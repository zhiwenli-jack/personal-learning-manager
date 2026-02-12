"""知识解析 API 路由"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.schemas import ParseTextRequest, ParseUrlRequest, ParseTaskResponse, TaskListResponse
from app.services.parse_service import parse_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/parse", tags=["知识解析"])


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
