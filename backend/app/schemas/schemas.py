"""Pydantic 数据模式定义"""
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.models import (
    MaterialStatus,
    QuestionType,
    QuestionRating,
    ExamMode,
    ExamStatus,
    ScoreType,
    ExpSourceType,
)


# ============ 学习方向 Schemas ============

class DirectionBase(BaseModel):
    """学习方向基础模式"""
    name: str
    description: Optional[str] = None


class DirectionCreate(DirectionBase):
    """创建学习方向"""
    pass


class DirectionResponse(DirectionBase):
    """学习方向响应"""
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============ 学习资料 Schemas ============

class MaterialBase(BaseModel):
    """学习资料基础模式"""
    title: str
    content: str


class MaterialCreate(MaterialBase):
    """创建学习资料"""
    direction_id: int


class MaterialResponse(MaterialBase):
    """学习资料响应"""
    id: int
    direction_id: int
    key_points: Optional[list] = None
    status: MaterialStatus
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============ 题目 Schemas ============

class QuestionBase(BaseModel):
    """题目基础模式"""
    type: QuestionType
    difficulty: int = 3
    content: str
    options: Optional[list] = None
    answer: str
    explanation: Optional[str] = None


class QuestionCreate(QuestionBase):
    """创建题目"""
    material_id: int


class QuestionResponse(QuestionBase):
    """题目响应"""
    id: int
    material_id: int
    rating: Optional[QuestionRating] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class QuestionRateRequest(BaseModel):
    """题目评价请求"""
    rating: QuestionRating


class QuestionUpdate(BaseModel):
    """更新题目"""
    content: Optional[str] = None
    options: Optional[list] = None
    answer: Optional[str] = None
    explanation: Optional[str] = None
    difficulty: Optional[int] = None


# ============ 测验 Schemas ============

class ExamCreate(BaseModel):
    """创建测验"""
    direction_id: int
    mode: ExamMode = ExamMode.UNTIMED
    time_limit: Optional[int] = None
    score_type: ScoreType = ScoreType.HUNDRED
    question_count: int = 10  # 题目数量
    material_ids: Optional[list[int]] = None  # 指定资料ID列表，不选则该方向全部资料


class ExamResponse(BaseModel):
    """测验响应"""
    id: int
    direction_id: int
    mode: ExamMode
    time_limit: Optional[int]
    score_type: ScoreType
    status: ExamStatus
    score: Optional[float] = None
    grade: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class ExamWithQuestions(ExamResponse):
    """测验详情(含题目)"""
    questions: list[QuestionResponse] = []


class ExamResult(BaseModel):
    """测验结果"""
    exam_id: int
    total_questions: int
    correct_count: int
    score: float
    grade: Optional[str] = None
    answers: list["AnswerResponse"] = []


# ============ 答题 Schemas ============

class AnswerCreate(BaseModel):
    """提交答案"""
    exam_id: int
    question_id: int
    user_answer: str


class AnswerResponse(BaseModel):
    """答案响应"""
    id: int
    exam_id: int
    question_id: int
    user_answer: str
    is_correct: Optional[bool] = None
    score: Optional[float] = None
    ai_feedback: Optional[str] = None
    answered_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ExamSubmit(BaseModel):
    """提交测验"""
    answers: list[AnswerCreate]


# ============ 错题 Schemas ============

class MistakeResponse(BaseModel):
    """错题响应"""
    id: int
    question_id: int
    answer_id: int
    error_count: int = 1
    error_prone: bool = False
    review_count: int
    mastered: bool
    created_at: datetime
    last_error_at: Optional[datetime] = None
    question: Optional[QuestionResponse] = None
    
    model_config = ConfigDict(from_attributes=True)


class MistakeUpdate(BaseModel):
    """更新错题"""
    mastered: Optional[bool] = None
    review_count: Optional[int] = None
    error_prone: Optional[bool] = None


# ============ 知识解析 Schemas ============

class ParseTextRequest(BaseModel):
    """解析纯文本请求"""
    title: str
    text: str
    direction_id: Optional[int] = None


class ParseUrlRequest(BaseModel):
    """解析 URL 请求"""
    title: str
    url: str
    direction_id: Optional[int] = None


class KnowledgePointResponse(BaseModel):
    """知识点响应"""
    id: int
    task_id: int
    name: str
    description: str
    importance: int
    category: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class BestPracticeResponse(BaseModel):
    """最佳实践响应"""
    id: int
    task_id: int
    title: str
    content: str
    scenario: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class TaskListResponse(BaseModel):
    """解析任务列表响应"""
    id: int
    direction_id: Optional[int] = None
    title: str
    source_type: str
    summary: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class ParseTaskResponse(BaseModel):
    """解析任务详情响应"""
    id: int
    direction_id: Optional[int] = None
    title: str
    source_type: str
    source_content: str
    raw_text: Optional[str] = None
    summary: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    knowledge_points: list[KnowledgePointResponse] = []
    best_practices: list[BestPracticeResponse] = []
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


# ============ 游戏化系统 Schemas ============

class UserProfileResponse(BaseModel):
    """用户档案响应"""
    user_id: int
    username: str
    level: int
    exp: int
    total_exp: int
    next_level_exp: int
    exp_to_next: int
    title: str
    streak_days: int
    last_login_date: Optional[date] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AchievementInfo(BaseModel):
    """成就信息"""
    achievement_id: str
    name: str
    description: str
    icon: str
    rarity: str
    exp_reward: int
    category: str


class UserAchievementResponse(BaseModel):
    """已解锁成就响应"""
    achievement_id: str
    name: str
    description: str
    icon: str
    rarity: str
    unlocked_at: datetime


class LockedAchievementResponse(BaseModel):
    """未解锁成就响应"""
    achievement_id: str
    name: str
    description: str
    icon: str
    rarity: str
    category: str


class AchievementsListResponse(BaseModel):
    """成就列表响应"""
    unlocked: list[UserAchievementResponse] = []
    locked: list[LockedAchievementResponse] = []


class DailyTaskResponse(BaseModel):
    """每日任务响应"""
    task_id: str
    name: str
    description: str
    icon: str
    target: int
    current: int
    completed: bool
    exp_reward: int
    date: date


class DirectionProgressResponse(BaseModel):
    """方向探索进度响应"""
    direction_id: int
    direction_name: str
    direction_description: Optional[str] = None
    total_questions: int
    answered_questions: int
    correct_questions: int
    mastered_count: int
    exploration_rate: float
    last_studied_at: Optional[datetime] = None


class ExpLogResponse(BaseModel):
    """经验日志响应"""
    id: int
    exp_amount: int
    source_type: ExpSourceType
    description: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GamificationReward(BaseModel):
    """游戏化奖励（嵌入到测验结果等响应中）"""
    exp_gained: int = 0
    level_up: bool = False
    old_level: Optional[int] = None
    new_level: Optional[int] = None
    new_title: Optional[str] = None
    achievements_unlocked: list[AchievementInfo] = []
    tasks_completed: list[str] = []


# ============ 学习模式 Schemas ============

class CourseCreateRequest(BaseModel):
    """创建学习课程请求"""
    title: str
    description: Optional[str] = None
    direction_id: Optional[int] = None
    material_ids: list[int]


class KnowledgePointMasteryUpdate(BaseModel):
    """更新知识点掌握度"""
    mastery_level: float


class CourseKnowledgePointResponse(BaseModel):
    """课程知识点响应"""
    id: int
    name: str
    description: str
    tier: str
    category: Optional[str] = None
    importance: int
    parent_id: Optional[int] = None
    order_index: int
    estimated_minutes: int
    mastery_level: float = 0
    practice_count: int = 0
    correct_count: int = 0
    children_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class KnowledgeRelationResponse(BaseModel):
    """知识关联响应"""
    id: int
    source_point_id: int
    source_point_name: str
    target_point_id: int
    target_point_name: str
    relation_type: str
    strength: int
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class LearningCourseListResponse(BaseModel):
    """学习课程列表响应"""
    id: int
    title: str
    description: Optional[str] = None
    direction_id: Optional[int] = None
    status: str
    total_points: int = 0
    mastered_points: int = 0
    progress_rate: float = 0
    material_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class LearningCourseDetailResponse(LearningCourseListResponse):
    """学习课程详情响应"""
    material_ids: list[int] = []
    knowledge_points: list[CourseKnowledgePointResponse] = []
    relations: list[KnowledgeRelationResponse] = []


class MindMapResponse(BaseModel):
    """思维导图响应"""
    course_id: int
    title: str
    mindmap_markdown: str


class LearningProgressResponse(BaseModel):
    """学习进度响应"""
    course_id: int
    total_points: int = 0
    mastered_points: int = 0
    progress_rate: float = 0
    beginner_total: int = 0
    beginner_mastered: int = 0
    intermediate_total: int = 0
    intermediate_mastered: int = 0
    advanced_total: int = 0
    advanced_mastered: int = 0
    weak_points: list[CourseKnowledgePointResponse] = []
    estimated_remaining_minutes: int = 0


class RecommendationItem(BaseModel):
    """推荐项"""
    knowledge_point_id: int
    knowledge_point_name: str
    tier: str
    reason: str
    priority: int = 3
    related_weak_points: list[str] = []


class RecommendationsResponse(BaseModel):
    """个性化推荐响应"""
    course_id: int
    recommendations: list[RecommendationItem] = []
