"""知识解析 API 路由"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Material, MaterialStatus, Direction, Question, QuestionType, ParseTask, TaskStatus
from app.schemas.schemas import ParseTextRequest, ParseUrlRequest, ParseTaskResponse, TaskListResponse, MaterialResponse
from app.services.parse_service import parse_service
from app.services import qwen_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/parse", tags=["知识解析"])


class UpdateDirectionRequest(BaseModel):
    """更新方向请求"""
    direction_id: Optional[int] = None


@router.post("/text", response_model=ParseTaskResponse)
async def parse_text(data: ParseTextRequest, db: Session = Depends(get_db)):
    """解析纯文本内容"""
    if not data.text.strip():
        raise HTTPException(status_code=400, detail="文本内容不能为空")
    task = await parse_service.parse_text(data.title, data.text, db, data.direction_id)
    return task


@router.post("/file", response_model=ParseTaskResponse)
async def parse_file(
    title: str = Form(...),
    direction_id: Optional[int] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """解析上传文件（支持 .pdf, .docx, .md, .txt）"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="未上传文件")
    task = await parse_service.parse_file(title, file, db, direction_id)
    return task


@router.post("/url", response_model=ParseTaskResponse)
async def parse_url(data: ParseUrlRequest, db: Session = Depends(get_db)):
    """解析 URL 网页内容"""
    if not data.url.strip():
        raise HTTPException(status_code=400, detail="URL 不能为空")
    task = await parse_service.parse_url(data.title, data.url, db, data.direction_id)
    return task


@router.get("/tasks", response_model=list[TaskListResponse])
def get_tasks(
    skip: int = 0,
    limit: int = 20,
    direction_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """获取解析任务列表"""
    tasks = parse_service.get_tasks(db, skip=skip, limit=limit, direction_id=direction_id)
    return tasks


@router.get("/tasks/{task_id}", response_model=ParseTaskResponse)
def get_task_detail(task_id: int, db: Session = Depends(get_db)):
    """获取任务详情（含知识点和最佳实践）"""
    task = parse_service.get_task_detail(task_id, db)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


@router.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """删除任务"""
    success = parse_service.delete_task(task_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="任务不存在")
    return {"message": "删除成功"}


@router.patch("/tasks/{task_id}", response_model=ParseTaskResponse)
def update_task_direction(task_id: int, data: UpdateDirectionRequest, db: Session = Depends(get_db)):
    """更新解析任务的学习方向"""
    task = db.query(ParseTask).filter(ParseTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 验证方向是否存在
    if data.direction_id is not None:
        direction = db.query(Direction).filter(Direction.id == data.direction_id).first()
        if not direction:
            raise HTTPException(status_code=404, detail="学习方向不存在")
    
    task.direction_id = data.direction_id
    db.commit()
    db.refresh(task)
    return task


@router.post("/tasks/{task_id}/generate-questions", response_model=MaterialResponse)
async def generate_questions_from_task(task_id: int, db: Session = Depends(get_db)):
    """将解析任务转换为资料并生成题目"""
    task = db.query(ParseTask).filter(ParseTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task.status != TaskStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="只有已完成的解析任务才能生成题目")
    
    if not task.raw_text:
        raise HTTPException(status_code=400, detail="解析任务没有原始文本内容")
    
    if not task.direction_id:
        raise HTTPException(status_code=400, detail="请先为解析任务指定学习方向")
    
    # 检查API密钥
    if not qwen_service.api_key:
        raise HTTPException(status_code=500, detail="API密钥未配置，请联系管理员设置QWEN_API_KEY")
    
    # 获取方向名称
    direction = db.query(Direction).filter(Direction.id == task.direction_id).first()
    direction_name = direction.name if direction else "通用"
    
    # 创建资料
    material = Material(
        direction_id=task.direction_id,
        title=task.title,
        content=task.raw_text,
        status=MaterialStatus.PENDING
    )
    db.add(material)
    db.commit()
    db.refresh(material)
    
    try:
        # 1. 提炼知识点
        key_points = await qwen_service.extract_key_points(material.content, direction_name)
        material.key_points = key_points
        
        # 2. 生成题目
        questions_data = await qwen_service.generate_questions(key_points, direction_name)
        
        # 3. 保存题目
        for q_data in questions_data:
            answer = q_data.get("answer", "")
            if isinstance(answer, list):
                answer = ",".join(answer)
            
            question = Question(
                material_id=material.id,
                type=QuestionType(q_data.get("type", "single_choice")),
                difficulty=q_data.get("difficulty", 3),
                content=q_data.get("content", ""),
                options=q_data.get("options"),
                answer=str(answer),
                explanation=q_data.get("explanation", ""),
            )
            db.add(question)
        
        material.status = MaterialStatus.PROCESSED
        db.commit()
        db.refresh(material)
        
    except Exception as e:
        logger.error(f"生成题目失败: {str(e)}", exc_info=True)
        material.status = MaterialStatus.FAILED
        db.commit()
        raise HTTPException(status_code=500, detail=f"生成题目失败: {str(e)}")
    
    return material
