"""游戏化 API 路由"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import UserProfile, UserAchievement, ExpLog
from app.core.achievements import ACHIEVEMENTS
from app.core.daily_tasks import DAILY_TASKS
from app.core.level_config import get_next_level_exp
from app.schemas.schemas import (
    UserProfileResponse,
    AchievementsListResponse,
    UserAchievementResponse,
    LockedAchievementResponse,
    DailyTaskResponse,
    DirectionProgressResponse,
    ExpLogResponse,
)
from app.services import gamification_service as gs

router = APIRouter(prefix="/gamification", tags=["游戏化"])


@router.get("/profile", response_model=UserProfileResponse)
def get_profile(db: Session = Depends(get_db)):
    """获取用户游戏化档案"""
    profile = gs.get_or_create_profile(db)
    # 更新连续登录
    gs.update_streak(db)
    db.refresh(profile)

    next_exp = get_next_level_exp(profile.level)
    return UserProfileResponse(
        user_id=profile.user_id,
        username=profile.username,
        level=profile.level,
        exp=profile.total_exp,
        total_exp=profile.total_exp,
        next_level_exp=next_exp,
        exp_to_next=max(0, next_exp - profile.total_exp),
        title=profile.title,
        streak_days=profile.streak_days,
        last_login_date=profile.last_login_date,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


@router.get("/achievements", response_model=AchievementsListResponse)
def get_achievements(db: Session = Depends(get_db)):
    """获取成就列表（已解锁 + 未解锁）"""
    unlocked_records = db.query(UserAchievement).filter(
        UserAchievement.user_id == 1
    ).all()
    unlocked_ids = {ua.achievement_id for ua in unlocked_records}
    unlocked_map = {ua.achievement_id: ua for ua in unlocked_records}

    unlocked = []
    locked = []

    for ach_id, ach in ACHIEVEMENTS.items():
        if ach_id in unlocked_ids:
            ua = unlocked_map[ach_id]
            unlocked.append(UserAchievementResponse(
                achievement_id=ach_id,
                name=ach["name"],
                description=ach["description"],
                icon=ach["icon"],
                rarity=ach["rarity"],
                unlocked_at=ua.unlocked_at,
            ))
        else:
            locked.append(LockedAchievementResponse(
                achievement_id=ach_id,
                name=ach["name"],
                description=ach["description"],
                icon=ach["icon"],
                rarity=ach["rarity"],
                category=ach["category"],
            ))

    return AchievementsListResponse(unlocked=unlocked, locked=locked)


@router.get("/daily-tasks", response_model=list[DailyTaskResponse])
def get_daily_tasks(db: Session = Depends(get_db)):
    """获取今日任务列表（自动生成）"""
    tasks = gs.generate_daily_tasks(db)
    result = []
    for task in tasks:
        task_def = DAILY_TASKS.get(task.task_id, {})
        result.append(DailyTaskResponse(
            task_id=task.task_id,
            name=task_def.get("name", task.task_id),
            description=task_def.get("description", ""),
            icon=task_def.get("icon", ""),
            target=task.target,
            current=task.current,
            completed=task.completed,
            exp_reward=task.exp_reward,
            date=task.date,
        ))
    return result


@router.get("/direction-progress", response_model=list[DirectionProgressResponse])
def get_direction_progress(
    direction_id: int = Query(None, description="指定方向ID"),
    db: Session = Depends(get_db),
):
    """获取方向探索进度"""
    all_progress = gs.get_all_direction_progress(db)
    if direction_id:
        all_progress = [p for p in all_progress if p["direction_id"] == direction_id]
    return [DirectionProgressResponse(**p) for p in all_progress]


@router.get("/exp-logs", response_model=list[ExpLogResponse])
def get_exp_logs(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """获取经验获取日志"""
    logs = db.query(ExpLog).filter(
        ExpLog.user_id == 1
    ).order_by(ExpLog.created_at.desc()).offset(offset).limit(limit).all()
    return logs
