"""游戏化服务 - 经验值、等级、成就、每日任务"""
import random
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct

from app.models import (
    UserProfile, UserAchievement, UserDailyTask, ExpLog, DirectionProgress,
    ExpSourceType, Exam, ExamStatus, Answer, Mistake, Material, MaterialStatus,
    Question, Direction,
)
from app.core.level_config import (
    get_level_for_exp, get_title_for_level, get_next_level_exp, LEVEL_THRESHOLDS, MAX_LEVEL,
)
from app.core.achievements import ACHIEVEMENTS
from app.core.daily_tasks import DAILY_TASKS, DAILY_TASK_COUNT


# ============ 用户档案 ============

def get_or_create_profile(db: Session) -> UserProfile:
    """获取或创建默认用户档案"""
    profile = db.query(UserProfile).filter(UserProfile.user_id == 1).first()
    if not profile:
        profile = UserProfile(
            user_id=1,
            username="探险家",
            level=1,
            exp=0,
            total_exp=0,
            title="见习探险家",
            streak_days=0,
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


# ============ 经验值系统 ============

def award_exp(
    db: Session,
    amount: int,
    source_type: ExpSourceType,
    source_id: int = None,
    description: str = None,
) -> dict:
    """发放经验值，记录日志，检测升级"""
    profile = get_or_create_profile(db)
    old_level = profile.level
    old_title = profile.title

    profile.exp += amount
    profile.total_exp += amount

    # 记录日志
    log = ExpLog(
        user_id=1,
        exp_amount=amount,
        source_type=source_type,
        source_id=source_id,
        description=description,
    )
    db.add(log)

    # 检测升级
    level_result = _check_level_up(db, profile)

    db.commit()

    result = {
        "exp_gained": amount,
        "total_exp": profile.total_exp,
        "current_exp": profile.exp,
    }
    result.update(level_result)
    return result


def _check_level_up(db: Session, profile: UserProfile) -> dict:
    """检测并执行升级"""
    old_level = profile.level
    old_title = profile.title

    new_level = get_level_for_exp(profile.total_exp)
    if new_level > old_level:
        profile.level = new_level
        profile.title = get_title_for_level(new_level)
        return {
            "level_up": True,
            "old_level": old_level,
            "new_level": new_level,
            "old_title": old_title,
            "new_title": profile.title,
        }
    return {"level_up": False}


def calculate_exam_exp(exam_score: float, streak_days: int) -> int:
    """计算测验经验值"""
    base_exp = 50
    score_bonus = int((exam_score or 0) * 0.5)
    streak_bonus = min(streak_days * 5, 50)
    return base_exp + score_bonus + streak_bonus


# ============ 连续登录 ============

def update_streak(db: Session) -> int:
    """更新连续登录天数，返回连击奖励EXP（0表示无奖励）"""
    profile = get_or_create_profile(db)
    today = date.today()
    last_login = profile.last_login_date

    if last_login is None:
        profile.streak_days = 1
        profile.last_login_date = today
    elif last_login == today:
        pass  # 今天已更新
    elif last_login == today - timedelta(days=1):
        profile.streak_days += 1
        profile.last_login_date = today
    else:
        profile.streak_days = 1
        profile.last_login_date = today

    db.commit()

    bonus_map = {3: 20, 7: 50, 14: 100, 30: 200}
    bonus = bonus_map.get(profile.streak_days, 0)
    if bonus > 0:
        award_exp(
            db, bonus, ExpSourceType.STREAK_BONUS,
            description=f"连续学习{profile.streak_days}天奖励",
        )
    return bonus


# ============ 成就系统 ============

def get_user_stats(db: Session) -> dict:
    """聚合用户统计数据，供成就检测使用"""
    exam_count = db.query(Exam).filter(Exam.status == ExamStatus.COMPLETED).count()
    mastered_mistakes = db.query(Mistake).filter(Mistake.mastered == True).count()
    material_count = db.query(Material).filter(Material.status == MaterialStatus.PROCESSED).count()

    # 最高分
    max_score = db.query(func.max(Exam.score)).filter(
        Exam.status == ExamStatus.COMPLETED
    ).scalar()
    has_perfect_score = max_score is not None and float(max_score) >= 100

    # 探索方向数（有已完成测验的方向）
    direction_count = db.query(distinct(Exam.direction_id)).filter(
        Exam.status == ExamStatus.COMPLETED
    ).count()

    # 所有方向是否都达到90%探索率
    all_directions = db.query(Direction).count()
    if all_directions > 0:
        high_explore = db.query(DirectionProgress).filter(
            DirectionProgress.exploration_rate >= 90
        ).count()
        all_directions_90 = high_explore >= all_directions and all_directions > 0
    else:
        all_directions_90 = False

    profile = get_or_create_profile(db)

    return {
        "exam_count": exam_count,
        "mastered_mistakes": mastered_mistakes,
        "material_count": material_count,
        "has_perfect_score": has_perfect_score,
        "direction_count": direction_count,
        "all_directions_90": all_directions_90,
        "streak_days": profile.streak_days,
    }


def check_achievements(db: Session) -> list:
    """检测并解锁所有满足条件的成就，返回新解锁列表"""
    stats = get_user_stats(db)
    unlocked_ids = {
        ua.achievement_id
        for ua in db.query(UserAchievement).filter(UserAchievement.user_id == 1).all()
    }

    newly_unlocked = []
    for ach_id, ach in ACHIEVEMENTS.items():
        if ach_id in unlocked_ids:
            continue
        if _check_achievement_condition(ach_id, stats):
            ua = UserAchievement(user_id=1, achievement_id=ach_id)
            db.add(ua)
            # 成就经验奖励
            award_exp(
                db, ach["exp_reward"], ExpSourceType.ACHIEVEMENT,
                description=f"解锁成就：{ach['name']}",
            )
            newly_unlocked.append(ach)

    if newly_unlocked:
        db.commit()
    return newly_unlocked


def _check_achievement_condition(ach_id: str, stats: dict) -> bool:
    """检查单个成就是否满足条件"""
    conditions = {
        "first_exam": stats["exam_count"] >= 1,
        "exam_master_10": stats["exam_count"] >= 10,
        "exam_master_50": stats["exam_count"] >= 50,
        "perfect_score": stats.get("has_perfect_score", False),
        "first_master": stats["mastered_mistakes"] >= 1,
        "mistake_hunter_50": stats["mastered_mistakes"] >= 50,
        "first_upload": stats["material_count"] >= 1,
        "explorer_3_directions": stats["direction_count"] >= 3,
        "full_exploration": stats.get("all_directions_90", False),
        "streak_7": stats["streak_days"] >= 7,
        "streak_30": stats["streak_days"] >= 30,
    }
    return conditions.get(ach_id, False)


# ============ 每日任务 ============

def generate_daily_tasks(db: Session) -> list:
    """获取今日任务，不存在则自动生成"""
    today = date.today()
    existing = db.query(UserDailyTask).filter(
        UserDailyTask.user_id == 1,
        UserDailyTask.date == today,
    ).all()

    if existing:
        return existing

    # 从任务池随机选取
    task_ids = list(DAILY_TASKS.keys())
    selected = random.sample(task_ids, min(DAILY_TASK_COUNT, len(task_ids)))

    tasks = []
    for task_id in selected:
        task_def = DAILY_TASKS[task_id]
        dt = UserDailyTask(
            user_id=1,
            task_id=task_id,
            date=today,
            target=task_def["target"],
            current=0,
            completed=False,
            exp_reward=task_def["exp_reward"],
        )
        db.add(dt)
        tasks.append(dt)

    db.commit()
    for t in tasks:
        db.refresh(t)
    return tasks


def update_task_progress(db: Session, task_type: str, increment: int = 1) -> list:
    """更新匹配类型的每日任务进度，返回新完成的任务名称列表"""
    today = date.today()
    tasks = db.query(UserDailyTask).filter(
        UserDailyTask.user_id == 1,
        UserDailyTask.date == today,
        UserDailyTask.completed == False,
    ).all()

    completed_names = []
    for task in tasks:
        task_def = DAILY_TASKS.get(task.task_id)
        if not task_def or task_def["task_type"] != task_type:
            continue
        task.current = min(task.current + increment, task.target)
        if task.current >= task.target and not task.completed:
            task.completed = True
            task.completed_at = datetime.now()
            # 发放任务奖励
            award_exp(
                db, task.exp_reward, ExpSourceType.DAILY_TASK,
                description=f"完成每日任务：{task_def['name']}",
            )
            completed_names.append(task_def["name"])

    db.commit()
    return completed_names


# ============ 方向探索进度 ============

def update_direction_progress(db: Session, direction_id: int):
    """更新指定方向的探索进度"""
    # 该方向总题数
    total_questions = db.query(Question).join(Material).filter(
        Material.direction_id == direction_id
    ).count()

    # 已答题目（去重，只统计已完成测验中的题目）
    answered_qids = db.query(distinct(Answer.question_id)).join(Exam).filter(
        Exam.status == ExamStatus.COMPLETED,
        Exam.direction_id == direction_id,
    ).all()
    answered_count = len(answered_qids)

    # 答对的题目数（去重）
    correct_qids = db.query(distinct(Answer.question_id)).join(Exam).filter(
        Exam.status == ExamStatus.COMPLETED,
        Exam.direction_id == direction_id,
        Answer.is_correct == True,
    ).all()
    correct_count = len(correct_qids)

    # 已掌握错题数
    mastered_count = db.query(Mistake).join(Question).join(Material).filter(
        Material.direction_id == direction_id,
        Mistake.mastered == True,
    ).count()

    exploration_rate = (answered_count / total_questions * 100) if total_questions > 0 else 0

    progress = db.query(DirectionProgress).filter(
        DirectionProgress.user_id == 1,
        DirectionProgress.direction_id == direction_id,
    ).first()

    if not progress:
        progress = DirectionProgress(user_id=1, direction_id=direction_id)
        db.add(progress)

    progress.total_questions = total_questions
    progress.answered_questions = answered_count
    progress.correct_questions = correct_count
    progress.mastered_count = mastered_count
    progress.exploration_rate = min(exploration_rate, 100)
    progress.last_studied_at = datetime.now()

    db.commit()


def get_all_direction_progress(db: Session) -> list:
    """获取所有方向的探索进度"""
    directions = db.query(Direction).all()
    result = []
    for d in directions:
        progress = db.query(DirectionProgress).filter(
            DirectionProgress.user_id == 1,
            DirectionProgress.direction_id == d.id,
        ).first()

        if progress:
            result.append({
                "direction_id": d.id,
                "direction_name": d.name,
                "direction_description": d.description,
                "total_questions": progress.total_questions,
                "answered_questions": progress.answered_questions,
                "correct_questions": progress.correct_questions,
                "mastered_count": progress.mastered_count,
                "exploration_rate": float(progress.exploration_rate),
                "last_studied_at": progress.last_studied_at,
            })
        else:
            # 计算实时数据
            total = db.query(Question).join(Material).filter(
                Material.direction_id == d.id
            ).count()
            result.append({
                "direction_id": d.id,
                "direction_name": d.name,
                "direction_description": d.description,
                "total_questions": total,
                "answered_questions": 0,
                "correct_questions": 0,
                "mastered_count": 0,
                "exploration_rate": 0.0,
                "last_studied_at": None,
            })
    return result


# ============ 事件处理器 ============

def on_exam_complete(db: Session, exam, correct_count: int, total_count: int) -> dict:
    """测验完成后的游戏化处理"""
    profile = get_or_create_profile(db)

    # 更新连续登录
    update_streak(db)

    # 计算并发放经验
    exp = calculate_exam_exp(float(exam.score or 0), profile.streak_days)
    exp_result = award_exp(
        db, exp, ExpSourceType.EXAM_COMPLETE, source_id=exam.id,
        description=f"完成测验 - {float(exam.score or 0):.0f}分",
    )

    # 更新方向进度
    update_direction_progress(db, exam.direction_id)

    # 更新每日任务
    generate_daily_tasks(db)  # 确保今日任务已生成
    completed_tasks = update_task_progress(db, "exam", 1)

    # 高分任务
    if exam.score and float(exam.score) >= 80:
        completed_tasks += update_task_progress(db, "exam_score", 1)

    # 答对题目任务
    if correct_count > 0:
        completed_tasks += update_task_progress(db, "questions", correct_count)

    # 检测成就
    unlocked = check_achievements(db)

    return {
        "exp_gained": exp,
        "level_up": exp_result.get("level_up", False),
        "old_level": exp_result.get("old_level"),
        "new_level": exp_result.get("new_level"),
        "new_title": exp_result.get("new_title"),
        "achievements_unlocked": unlocked,
        "tasks_completed": completed_tasks,
    }


def on_mistake_mastered(db: Session, mistake) -> dict:
    """掌握错题后的游戏化处理"""
    profile = get_or_create_profile(db)
    update_streak(db)

    exp_result = award_exp(
        db, 20, ExpSourceType.MISTAKE_MASTER, source_id=mistake.id,
        description="掌握错题",
    )

    # 更新方向进度（通过question -> material -> direction）
    question = mistake.question
    if question and question.material:
        update_direction_progress(db, question.material.direction_id)

    generate_daily_tasks(db)
    completed_tasks = update_task_progress(db, "mistake", 1)
    unlocked = check_achievements(db)

    return {
        "exp_gained": 20,
        "level_up": exp_result.get("level_up", False),
        "achievements_unlocked": unlocked,
        "tasks_completed": completed_tasks,
    }


def on_material_uploaded(db: Session, material) -> dict:
    """上传资料后的游戏化处理"""
    profile = get_or_create_profile(db)
    update_streak(db)

    exp = 30
    if material.status == MaterialStatus.PROCESSED:
        exp += 20  # 成功生成题目额外奖励

    exp_result = award_exp(
        db, exp, ExpSourceType.MATERIAL_UPLOAD, source_id=material.id,
        description=f"上传资料：{material.title[:30]}",
    )

    generate_daily_tasks(db)
    completed_tasks = update_task_progress(db, "material", 1)
    unlocked = check_achievements(db)

    return {
        "exp_gained": exp,
        "level_up": exp_result.get("level_up", False),
        "achievements_unlocked": unlocked,
        "tasks_completed": completed_tasks,
    }
