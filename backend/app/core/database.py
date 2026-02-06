"""数据库连接配置"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import get_settings

settings = get_settings()

# 根据数据库类型配置引擎参数
connect_args = {}
engine_kwargs = {"echo": settings.debug}

if settings.database_url.startswith("sqlite"):
    # SQLite 特殊配置
    connect_args = {"check_same_thread": False}
else:
    # MySQL/PostgreSQL 配置
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_recycle"] = 3600

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    **engine_kwargs
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """获取数据库会话依赖"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
