"""数据库模型定义"""
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Enum, JSON, Numeric
from sqlalchemy.orm import relationship
from app.core.database import Base


class MaterialStatus(str, PyEnum):
    """资料处理状态"""
    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"


class QuestionType(str, PyEnum):
    """题目类型"""
    SINGLE_CHOICE = "single_choice"
    MULTI_CHOICE = "multi_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"


class QuestionRating(str, PyEnum):
    """题目评价"""
    GOOD = "good"
    BAD = "bad"


class ExamMode(str, PyEnum):
    """测验模式"""
    TIMED = "timed"
    UNTIMED = "untimed"


class ScoreType(str, PyEnum):
    """评分类型"""
    HUNDRED = "hundred"
    GRADE = "grade"


class ExamStatus(str, PyEnum):
    """测验状态"""
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class SourceType(str, PyEnum):
    """解析来源类型"""
    TEXT = "text"
    FILE = "file"
    URL = "url"


class TaskStatus(str, PyEnum):
    """解析任务状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Direction(Base):
    """学习方向表"""
    __tablename__ = "directions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True, comment="方向名称")
    description = Column(Text, comment="方向描述")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    
    # 关联
    materials = relationship("Material", back_populates="direction")
    exams = relationship("Exam", back_populates="direction")
    parse_tasks = relationship("ParseTask", back_populates="direction")


class Material(Base):
    """学习资料表"""
    __tablename__ = "materials"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    direction_id = Column(Integer, ForeignKey("directions.id"), nullable=False, comment="学习方向ID")
    title = Column(String(200), nullable=False, comment="资料标题")
    content = Column(Text, nullable=False, comment="原始资料内容")
    key_points = Column(JSON, comment="AI提炼的核心知识点")
    status = Column(Enum(MaterialStatus), default=MaterialStatus.PENDING, comment="处理状态")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    
    # 关联
    direction = relationship("Direction", back_populates="materials")
    questions = relationship("Question", back_populates="material")


class Question(Base):
    """题目表"""
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False, comment="来源资料ID")
    type = Column(Enum(QuestionType), nullable=False, comment="题目类型")
    difficulty = Column(Integer, default=3, comment="难度1-5")
    content = Column(Text, nullable=False, comment="题目内容")
    options = Column(JSON, comment="选项(选择题用)")
    answer = Column(Text, nullable=False, comment="标准答案")
    explanation = Column(Text, comment="答案解析")
    rating = Column(Enum(QuestionRating), nullable=True, comment="用户评价")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    
    # 关联
    material = relationship("Material", back_populates="questions")
    answers = relationship("Answer", back_populates="question")
    mistakes = relationship("Mistake", back_populates="question")


class Exam(Base):
    """测验表"""
    __tablename__ = "exams"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    direction_id = Column(Integer, ForeignKey("directions.id"), nullable=False, comment="学习方向ID")
    mode = Column(Enum(ExamMode), default=ExamMode.UNTIMED, comment="测验模式")
    time_limit = Column(Integer, nullable=True, comment="限时分钟数")
    score_type = Column(Enum(ScoreType), default=ScoreType.HUNDRED, comment="评分类型")
    status = Column(Enum(ExamStatus), default=ExamStatus.IN_PROGRESS, comment="测验状态")
    score = Column(Numeric(5, 2), nullable=True, comment="最终得分")
    grade = Column(String(1), nullable=True, comment="等级A/B/C/D")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    completed_at = Column(DateTime, nullable=True, comment="完成时间")
    
    # 关联
    direction = relationship("Direction", back_populates="exams")
    answers = relationship("Answer", back_populates="exam")


class Answer(Base):
    """答题记录表"""
    __tablename__ = "answers"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False, comment="测验ID")
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False, comment="题目ID")
    user_answer = Column(Text, nullable=False, comment="用户答案")
    is_correct = Column(Boolean, nullable=True, comment="是否正确")
    score = Column(Numeric(5, 2), nullable=True, comment="单题得分")
    ai_feedback = Column(Text, nullable=True, comment="AI评分反馈")
    answered_at = Column(DateTime, default=datetime.now, comment="答题时间")
    
    # 关联
    exam = relationship("Exam", back_populates="answers")
    question = relationship("Question", back_populates="answers")
    mistake = relationship("Mistake", back_populates="answer", uselist=False)


class Mistake(Base):
    """错题表"""
    __tablename__ = "mistakes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False, comment="题目ID")
    answer_id = Column(Integer, ForeignKey("answers.id"), nullable=False, comment="答题记录ID")
    review_count = Column(Integer, default=0, comment="复习次数")
    mastered = Column(Boolean, default=False, comment="是否已掌握")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    
    # 关联
    question = relationship("Question", back_populates="mistakes")
    answer = relationship("Answer", back_populates="mistake")


class ParseTask(Base):
    """知识解析任务表"""
    __tablename__ = "parse_tasks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    direction_id = Column(Integer, ForeignKey("directions.id", ondelete="SET NULL"), nullable=True, comment="学习方向ID")
    title = Column(String(200), nullable=False, comment="任务标题")
    source_type = Column(Enum(SourceType), nullable=False, comment="来源类型")
    source_content = Column(Text, nullable=False, comment="来源内容")
    raw_text = Column(Text, nullable=True, comment="提取的原始文本")
    summary = Column(Text, nullable=True, comment="内容摘要")
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, comment="任务状态")
    error_message = Column(Text, nullable=True, comment="错误信息")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    
    # 关联
    direction = relationship("Direction", back_populates="parse_tasks")
    knowledge_points = relationship("KnowledgePoint", back_populates="task", cascade="all, delete-orphan")
    best_practices = relationship("BestPractice", back_populates="task", cascade="all, delete-orphan")


class KnowledgePoint(Base):
    """知识点表"""
    __tablename__ = "knowledge_points"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("parse_tasks.id"), nullable=False, comment="解析任务ID")
    name = Column(String(200), nullable=False, comment="知识点名称")
    description = Column(Text, nullable=False, comment="详细描述")
    importance = Column(Integer, default=3, comment="重要程度1-5")
    category = Column(String(100), nullable=True, comment="分类标签")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    
    # 关联
    task = relationship("ParseTask", back_populates="knowledge_points")


class BestPractice(Base):
    """最佳实践表"""
    __tablename__ = "best_practices"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("parse_tasks.id"), nullable=False, comment="解析任务ID")
    title = Column(String(200), nullable=False, comment="实践标题")
    content = Column(Text, nullable=False, comment="具体内容")
    scenario = Column(Text, nullable=True, comment="适用场景")
    notes = Column(Text, nullable=True, comment="注意事项")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    
    # 关联
    task = relationship("ParseTask", back_populates="best_practices")
