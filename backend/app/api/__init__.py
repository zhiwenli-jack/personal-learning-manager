"""API 路由模块"""
from app.api.directions import router as directions_router
from app.api.materials import router as materials_router
from app.api.questions import router as questions_router
from app.api.exams import router as exams_router
from app.api.mistakes import router as mistakes_router

__all__ = [
    "directions_router",
    "materials_router",
    "questions_router",
    "exams_router",
    "mistakes_router",
]
