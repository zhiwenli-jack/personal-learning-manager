"""题目 API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import Question, Material
from app.schemas import QuestionResponse, QuestionRateRequest, QuestionUpdate

router = APIRouter(prefix="/questions", tags=["题目"])


@router.get("", response_model=list[QuestionResponse])
def get_questions(
    material_id: int = None,
    direction_id: int = None,
    question_type: str = None,
    db: Session = Depends(get_db)
):
    """获取题目列表"""
    query = db.query(Question)
    
    if material_id:
        query = query.filter(Question.material_id == material_id)
    
    if direction_id:
        query = query.join(Material).filter(Material.direction_id == direction_id)
    
    if question_type:
        query = query.filter(Question.type == question_type)
    
    return query.order_by(Question.created_at.desc()).all()


@router.get("/{question_id}", response_model=QuestionResponse)
def get_question(question_id: int, db: Session = Depends(get_db)):
    """获取题目详情"""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")
    return question


@router.patch("/{question_id}", response_model=QuestionResponse)
def update_question(
    question_id: int,
    data: QuestionUpdate,
    db: Session = Depends(get_db)
):
    """更新题目"""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")
    
    # 只更新提供的字段
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(question, field, value)
    
    db.commit()
    db.refresh(question)
    return question


@router.patch("/{question_id}/rate", response_model=QuestionResponse)
def rate_question(
    question_id: int,
    data: QuestionRateRequest,
    db: Session = Depends(get_db)
):
    """评价题目(好/不好)"""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")
    
    question.rating = data.rating
    db.commit()
    db.refresh(question)
    return question


@router.delete("/{question_id}")
def delete_question(question_id: int, db: Session = Depends(get_db)):
    """删除题目"""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")
    
    db.delete(question)
    db.commit()
    return {"message": "删除成功"}
