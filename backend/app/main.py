"""FastAPI 应用入口"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.core.database import engine, Base
from app.api import (
    directions_router,
    materials_router,
    questions_router,
    exams_router,
    mistakes_router,
    parse_router,
)

settings = get_settings()

# 创建应用
app = FastAPI(
    title=settings.app_name,
    description="个人学习管理软件 API - 支持资料上传、题目生成、智能评分",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发环境允许所有来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(directions_router, prefix="/api")
app.include_router(materials_router, prefix="/api")
app.include_router(questions_router, prefix="/api")
app.include_router(exams_router, prefix="/api")
app.include_router(mistakes_router, prefix="/api")
app.include_router(parse_router, prefix="/api")


@app.on_event("startup")
def startup():
    """应用启动时创建数据表和上传目录"""
    Base.metadata.create_all(bind=engine)
    os.makedirs(settings.upload_dir, exist_ok=True)


@app.get("/")
def root():
    """根路由"""
    return {
        "name": settings.app_name,
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    """健康检查"""
    return {"status": "ok"}
