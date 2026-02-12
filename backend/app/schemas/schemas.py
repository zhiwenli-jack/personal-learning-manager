"""Pydantic 数据模式定义"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.models import (
    MaterialStatus,
    QuestionType,
    QuestionRating,
    ExamMode,
    ExamStatus,
    ScoreType,
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
    review_count: int
    mastered: bool
    created_at: datetime
    question: Optional[QuestionResponse] = None
    
    model_config = ConfigDict(from_attributes=True)


class MistakeUpdate(BaseModel):
    """更新错题"""
    mastered: Optional[bool] = None
    review_count: Optional[int] = None


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
