"""测验 API"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.models import (
    Exam, ExamStatus, ExamMode, ScoreType,
    Question, Material, Answer, Mistake, QuestionType
)
from app.schemas import ExamCreate, ExamResponse, ExamWithQuestions, ExamResult, ExamSubmit
from app.services import qwen_service

router = APIRouter(prefix="/exams", tags=["测验"])


def _resolve_option_text(answer: str, options: list) -> str:
    """将选项字母(A/B/C/D)或带前缀的答案解析为实际选项文本"""
    answer = answer.strip()
    if not options:
        return answer

    # 已经是选项文本，直接返回
    for opt in options:
        if answer == opt.strip():
            return opt.strip()

    upper = answer.upper()

    # 单字母: "A", "B", "C", "D"
    if len(upper) == 1 and upper in "ABCDEFGH":
        idx = ord(upper) - 65
        if 0 <= idx < len(options):
            return options[idx].strip()

    # 带分隔符: "A." "A、" "A．" "A:" "A：" 或 "A. xxx"
    if len(answer) >= 2 and answer[0].upper() in "ABCDEFGH" and answer[1] in ".、．:：":
        idx = ord(answer[0].upper()) - 65
        if 0 <= idx < len(options):
            return options[idx].strip()

    return answer


def calculate_grade(score: float) -> str:
    """根据分数计算等级"""
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 60:
        return "C"
    else:
        return "D"


@router.get("", response_model=list[ExamResponse])
def get_exams(
    direction_id: int = None,
    status: str = None,
    db: Session = Depends(get_db)
):
    """获取测验列表"""
    query = db.query(Exam)
    
    if direction_id:
        query = query.filter(Exam.direction_id == direction_id)
    
    if status:
        query = query.filter(Exam.status == status)
    
    return query.order_by(Exam.created_at.desc()).all()


@router.post("", response_model=ExamWithQuestions)
def create_exam(data: ExamCreate, db: Session = Depends(get_db)):
    """创建测验"""
    # 获取该方向下的题目
    questions = (
        db.query(Question)
        .join(Material)
        .filter(Material.direction_id == data.direction_id)
        .order_by(func.random())
        .limit(data.question_count)
        .all()
    )
    
    if not questions:
        raise HTTPException(status_code=400, detail="该方向下没有可用题目，请先上传资料")
    
    # 创建测验
    exam = Exam(
        direction_id=data.direction_id,
        mode=data.mode,
        time_limit=data.time_limit if data.mode == ExamMode.TIMED else None,
        score_type=data.score_type,
    )
    db.add(exam)
    db.commit()
    db.refresh(exam)
    
    # 返回测验和题目
    return ExamWithQuestions(
        id=exam.id,
        direction_id=exam.direction_id,
        mode=exam.mode,
        time_limit=exam.time_limit,
        score_type=exam.score_type,
        status=exam.status,
        score=None,
        grade=None,
        created_at=exam.created_at,
        completed_at=None,
        questions=questions
    )


@router.get("/{exam_id}", response_model=ExamWithQuestions)
def get_exam(exam_id: int, db: Session = Depends(get_db)):
    """获取测验详情"""
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="测验不存在")
    
    # 获取该测验的题目(通过已有答案或重新查询)
    answered_question_ids = [a.question_id for a in exam.answers]
    
    if answered_question_ids:
        questions = db.query(Question).filter(Question.id.in_(answered_question_ids)).all()
    else:
        # 如果还没答题，重新查询题目
        questions = (
            db.query(Question)
            .join(Material)
            .filter(Material.direction_id == exam.direction_id)
            .limit(10)
            .all()
        )
    
    return ExamWithQuestions(
        id=exam.id,
        direction_id=exam.direction_id,
        mode=exam.mode,
        time_limit=exam.time_limit,
        score_type=exam.score_type,
        status=exam.status,
        score=float(exam.score) if exam.score else None,
        grade=exam.grade,
        created_at=exam.created_at,
        completed_at=exam.completed_at,
        questions=questions
    )


@router.post("/{exam_id}/submit", response_model=ExamResult)
async def submit_exam(
    exam_id: int,
    data: ExamSubmit,
    db: Session = Depends(get_db)
):
    """提交测验并评分"""
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="测验不存在")
    
    if exam.status == ExamStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="测验已完成")
    
    total_score = 0
    correct_count = 0
    answer_responses = []
    
    for answer_data in data.answers:
        question = db.query(Question).filter(Question.id == answer_data.question_id).first()
        if not question:
            continue
        
        is_correct = False
        score = 0.0
        ai_feedback = None
        
        # 根据题型评分
        if question.type in [QuestionType.SINGLE_CHOICE, QuestionType.MULTI_CHOICE, QuestionType.TRUE_FALSE]:
            # 客观题评分
            user_ans = answer_data.user_answer.strip()
            correct_ans = question.answer.strip()

            if question.type == QuestionType.MULTI_CHOICE:
                # 多选题：将双方都解析为选项文本集合后比较
                user_parts = [s.strip() for s in user_ans.split(",") if s.strip()]
                correct_parts = [s.strip() for s in correct_ans.split(",") if s.strip()]
                if question.options:
                    user_parts = [_resolve_option_text(p, question.options) for p in user_parts]
                    correct_parts = [_resolve_option_text(p, question.options) for p in correct_parts]
                is_correct = set(user_parts) == set(correct_parts)
            else:
                # 单选题 / 判断题：解析后比较
                resolved_user = _resolve_option_text(user_ans, question.options) if question.options else user_ans
                resolved_correct = _resolve_option_text(correct_ans, question.options) if question.options else correct_ans
                is_correct = resolved_user == resolved_correct

            score = 100.0 if is_correct else 0.0
        else:
            # 主观题：AI评分
            eval_result = await qwen_service.evaluate_answer(
                question.content,
                question.answer,
                answer_data.user_answer,
                question.type.value
            )
            score = eval_result.get("score", 0)
            ai_feedback = eval_result.get("feedback", "")
            is_correct = score >= 60
        
        # 保存答题记录
        answer = Answer(
            exam_id=exam_id,
            question_id=question.id,
            user_answer=answer_data.user_answer,
            is_correct=is_correct,
            score=score,
            ai_feedback=ai_feedback,
        )
        db.add(answer)
        db.flush()
        
        # 如果答错，添加到错题本
        if not is_correct:
            mistake = Mistake(
                question_id=question.id,
                answer_id=answer.id,
            )
            db.add(mistake)
        
        total_score += score
        if is_correct:
            correct_count += 1
        
        answer_responses.append(answer)
    
    # 计算最终得分
    question_count = len(data.answers)
    final_score = total_score / question_count if question_count > 0 else 0
    
    # 更新测验状态
    exam.status = ExamStatus.COMPLETED
    exam.score = final_score
    exam.grade = calculate_grade(final_score) if exam.score_type == ScoreType.GRADE else None
    exam.completed_at = datetime.now()
    
    db.commit()
    
    return ExamResult(
        exam_id=exam_id,
        total_questions=question_count,
        correct_count=correct_count,
        score=final_score,
        grade=exam.grade,
        answers=answer_responses
    )


@router.get("/{exam_id}/result", response_model=ExamResult)
def get_exam_result(exam_id: int, db: Session = Depends(get_db)):
    """获取测验结果"""
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="测验不存在")
    
    if exam.status != ExamStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="测验尚未完成")
    
    answers = db.query(Answer).filter(Answer.exam_id == exam_id).all()
    correct_count = sum(1 for a in answers if a.is_correct)
    
    return ExamResult(
        exam_id=exam_id,
        total_questions=len(answers),
        correct_count=correct_count,
        score=float(exam.score) if exam.score else 0,
        grade=exam.grade,
        answers=answers
    )
