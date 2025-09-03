from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """应用配置类"""
    
    # 服务配置
    environment: str = "development"
    host: str = "0.0.0.0"
    port: int = 8080
    debug: bool = True
    
    # 自塾API配置
    zishu_api_base: str = "https://zishu.co/api"
    zishu_timeout: int = 10
    use_mock_data: bool = False  # 是否使用模拟数据，设为False使用真实API
    
    # Redis配置
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""
    
    # 缓存配置
    cache_ttl: int = 7200  # 2小时
    cache_prefix: str = "what_to_do"
    
    # 算法权重配置
    algorithm_weights_urgency: float = 0.35
    algorithm_weights_importance: float = 0.30
    algorithm_weights_personal_fit: float = 0.25
    algorithm_weights_growth_value: float = 0.10
    
    # 紧急度阈值配置(小时)
    urgency_critical: int = 24
    urgency_high: int = 72
    urgency_medium: int = 168
    urgency_low: int = 720
    
    # 日志配置
    log_level: str = "INFO"
    log_format: str = "{time} | {level} | {message}"
    
    # CORS配置
    allowed_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080", 
        "https://zishu.co"
    ]
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False
    }


# 全局配置实例
settings = Settings()


def get_settings() -> Settings:
    """获取配置实例"""
    return settings