"""应用配置模块"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置类"""
    
    # 应用配置
    app_name: str = "个人学习管理软件"
    debug: bool = True
    
    # 数据库配置
    database_url: str = "sqlite:///./personal_study.db"
    
    # 通义千问 API 配置
    qwen_api_key: str = ""
    qwen_model: str = "qwen-plus"
    qwen_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    
    # 知识解析配置
    upload_dir: str = "./uploads"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()
