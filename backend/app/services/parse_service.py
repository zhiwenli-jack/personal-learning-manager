"""核心解析服务 - 协调文本提取和大模型分析"""
import logging
from datetime import datetime

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.models import ParseTask, KnowledgePoint, BestPractice, SourceType, TaskStatus
from app.services.knowledge_service import knowledge_service
from app.services.extractor_service import extractor_service

logger = logging.getLogger(__name__)


class ParseService:
    """核心解析服务"""

    async def _do_analysis(self, task: ParseTask, raw_text: str, db: Session):
        """执行大模型分析并保存结果"""
        task.raw_text = raw_text
        task.status = TaskStatus.PROCESSING
        db.commit()

        # 调用千问分析
        result = await knowledge_service.extract_knowledge_and_practices(raw_text)

        # 保存摘要
        task.summary = result.get("summary", "")

        # 保存知识点
        for kp_data in result.get("knowledge_points", []):
            kp = KnowledgePoint(
                task_id=task.id,
                name=kp_data.get("name", "未命名知识点"),
                description=kp_data.get("description", ""),
                importance=kp_data.get("importance", 3),
                category=kp_data.get("category", ""),
            )
            db.add(kp)

        # 保存最佳实践
        for bp_data in result.get("best_practices", []):
            bp = BestPractice(
                task_id=task.id,
                title=bp_data.get("title", "未命名实践"),
                content=bp_data.get("content", ""),
                scenario=bp_data.get("scenario", ""),
                notes=bp_data.get("notes", ""),
            )
            db.add(bp)

        task.status = TaskStatus.COMPLETED
        task.updated_at = datetime.now()
        db.commit()
        db.refresh(task)

    async def parse_text(self, title: str, text: str, db: Session, direction_id: int | None = None) -> ParseTask:
        """解析纯文本"""
        task = ParseTask(
            title=title,
            direction_id=direction_id,
            source_type=SourceType.TEXT,
            source_content=text[:500],  # 保存前500字作为来源记录
            status=TaskStatus.PENDING,
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        try:
            await self._do_analysis(task, text, db)
        except Exception as e:
            logger.error("文本解析失败: %s", str(e))
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            task.updated_at = datetime.now()
            db.commit()
            db.refresh(task)

        return task

    async def parse_file(self, title: str, file: UploadFile, db: Session, direction_id: int | None = None) -> ParseTask:
        """解析上传文件"""
        task = ParseTask(
            title=title,
            direction_id=direction_id,
            source_type=SourceType.FILE,
            source_content=file.filename,
            status=TaskStatus.PENDING,
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        try:
            raw_text = await extractor_service.extract_from_file(file)
            await self._do_analysis(task, raw_text, db)
        except Exception as e:
            logger.error("文件解析失败: %s", str(e))
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            task.updated_at = datetime.now()
            db.commit()
            db.refresh(task)

        return task

    async def parse_url(self, title: str, url: str, db: Session, direction_id: int | None = None) -> ParseTask:
        """解析 URL 内容"""
        task = ParseTask(
            title=title,
            direction_id=direction_id,
            source_type=SourceType.URL,
            source_content=url,
            status=TaskStatus.PENDING,
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        try:
            raw_text = await extractor_service.extract_from_url(url)
            await self._do_analysis(task, raw_text, db)
        except Exception as e:
            logger.error("URL 解析失败: %s", str(e))
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            task.updated_at = datetime.now()
            db.commit()
            db.refresh(task)

        return task

    def get_tasks(self, db: Session, skip: int = 0, limit: int = 20, direction_id: int | None = None) -> list[ParseTask]:
        """获取任务列表"""
        query = db.query(ParseTask)
        if direction_id is not None:
            query = query.filter(ParseTask.direction_id == direction_id)
        return (
            query
            .order_by(ParseTask.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_task_detail(self, task_id: int, db: Session) -> ParseTask | None:
        """获取任务详情（含关联数据）"""
        return db.query(ParseTask).filter(ParseTask.id == task_id).first()

    def delete_task(self, task_id: int, db: Session) -> bool:
        """删除任务（级联删除关联数据）"""
        task = db.query(ParseTask).filter(ParseTask.id == task_id).first()
        if not task:
            return False
        db.delete(task)
        db.commit()
        return True


# 单例
parse_service = ParseService()
