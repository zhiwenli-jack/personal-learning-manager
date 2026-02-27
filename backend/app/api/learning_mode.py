"""学习模式 API 路由"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import LearningCourse, CourseStatus
from app.schemas.schemas import (
    CourseCreateRequest,
    KnowledgePointMasteryUpdate,
    LearningCourseListResponse,
    LearningCourseDetailResponse,
    MindMapResponse,
    LearningProgressResponse,
    RecommendationsResponse,
)
from app.services.learning_mode_service import learning_mode_service
from app.services import qwen_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/learning-mode", tags=["学习模式"])


@router.get("/courses", response_model=list[LearningCourseListResponse])
def get_courses(db: Session = Depends(get_db)):
    """获取学习课程列表"""
    courses = learning_mode_service.get_courses(db)
    result = []
    for c in courses:
        result.append(LearningCourseListResponse(
            id=c.id,
            title=c.title,
            description=c.description,
            direction_id=c.direction_id,
            status=c.status.value if hasattr(c.status, 'value') else c.status,
            total_points=c.total_points,
            mastered_points=c.mastered_points,
            progress_rate=float(c.progress_rate) if c.progress_rate else 0,
            material_count=len(c.material_ids) if c.material_ids else 0,
            created_at=c.created_at,
            updated_at=c.updated_at,
        ))
    return result


@router.post("/courses", response_model=LearningCourseListResponse)
def create_course(data: CourseCreateRequest, db: Session = Depends(get_db)):
    """创建学习课程"""
    if not data.material_ids:
        raise HTTPException(status_code=400, detail="至少需要选择一份资料")

    if not data.title.strip():
        raise HTTPException(status_code=400, detail="课程标题不能为空")

    try:
        course = learning_mode_service.create_course(
            title=data.title.strip(),
            material_ids=data.material_ids,
            db=db,
            description=data.description,
            direction_id=data.direction_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return LearningCourseListResponse(
        id=course.id,
        title=course.title,
        description=course.description,
        direction_id=course.direction_id,
        status=course.status.value if hasattr(course.status, 'value') else course.status,
        total_points=course.total_points,
        mastered_points=course.mastered_points,
        progress_rate=float(course.progress_rate) if course.progress_rate else 0,
        material_count=len(course.material_ids) if course.material_ids else 0,
        created_at=course.created_at,
        updated_at=course.updated_at,
    )


@router.post("/courses/{course_id}/generate", response_model=LearningCourseDetailResponse)
async def generate_course(course_id: int, db: Session = Depends(get_db)):
    """AI生成课程内容（分级知识点、关联关系、思维导图）"""
    course = db.query(LearningCourse).filter(LearningCourse.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")

    if course.status == CourseStatus.GENERATING:
        raise HTTPException(status_code=400, detail="课程正在生成中，请稍候")

    if not qwen_service.api_key:
        raise HTTPException(status_code=500, detail="API密钥未配置，请设置QWEN_API_KEY")

    try:
        await learning_mode_service.generate_course_content(course_id, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("生成课程失败: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"生成课程失败: {str(e)}")

    detail = learning_mode_service.get_course_detail(course_id, db)
    return detail


@router.get("/courses/{course_id}", response_model=LearningCourseDetailResponse)
def get_course_detail(course_id: int, db: Session = Depends(get_db)):
    """获取课程详情"""
    detail = learning_mode_service.get_course_detail(course_id, db)
    if not detail:
        raise HTTPException(status_code=404, detail="课程不存在")
    return detail


@router.get("/courses/{course_id}/mindmap", response_model=MindMapResponse)
def get_course_mindmap(course_id: int, db: Session = Depends(get_db)):
    """获取思维导图数据"""
    result = learning_mode_service.get_mindmap(course_id, db)
    if not result:
        raise HTTPException(status_code=404, detail="课程不存在")
    return result


@router.get("/courses/{course_id}/progress", response_model=LearningProgressResponse)
def get_course_progress(course_id: int, db: Session = Depends(get_db)):
    """获取学习进度"""
    result = learning_mode_service.get_learning_progress(course_id, db)
    if not result:
        raise HTTPException(status_code=404, detail="课程不存在")
    return result


@router.get("/courses/{course_id}/recommendations", response_model=RecommendationsResponse)
async def get_course_recommendations(course_id: int, db: Session = Depends(get_db)):
    """获取个性化学习推荐"""
    if not qwen_service.api_key:
        raise HTTPException(status_code=500, detail="API密钥未配置，请设置QWEN_API_KEY")

    try:
        result = await learning_mode_service.get_recommendations(course_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("获取推荐失败: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取推荐失败: {str(e)}")

    return result


@router.delete("/courses/{course_id}")
def delete_course(course_id: int, db: Session = Depends(get_db)):
    """删除课程"""
    success = learning_mode_service.delete_course(course_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="课程不存在")
    return {"message": "删除成功"}


@router.patch("/courses/{course_id}/points/{point_id}")
def update_point_mastery(
    course_id: int,
    point_id: int,
    data: KnowledgePointMasteryUpdate,
    db: Session = Depends(get_db),
):
    """更新知识点掌握度"""
    point = learning_mode_service.update_point_mastery(
        course_id, point_id, data.mastery_level, db
    )
    if not point:
        raise HTTPException(status_code=404, detail="知识点不存在")
    return {
        "id": point.id,
        "name": point.name,
        "mastery_level": float(point.mastery_level),
        "practice_count": point.practice_count,
        "correct_count": point.correct_count,
    }
