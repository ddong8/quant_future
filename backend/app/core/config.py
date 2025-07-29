"""
应用配置模块
"""
from typing import Optional
from pydantic import validator
from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    """应用配置类"""
    
    # 应用基础配置
    APP_NAME: str = "量化交易平台"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    SECRET_KEY: str = "default-secret-key-change-in-production"
    
    # 数据库配置
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/trading_db"
    INFLUXDB_URL: str = "http://localhost:8086"
    INFLUXDB_TOKEN: str = "my-super-secret-auth-token"
    INFLUXDB_ORG: str = "trading-org"
    INFLUXDB_BUCKET: str = "market-data"
    
    # Redis配置
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # tqsdk配置
    TQSDK_AUTH: Optional[str] = None
    TQSDK_ACCOUNT: Optional[str] = None
    
    # JWT配置
    @property
    def JWT_SECRET_KEY(self) -> str:
        return self.SECRET_KEY
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # 邮件配置
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    
    # 风险管理配置
    MAX_DAILY_LOSS_PERCENT: float = 5.0
    MAX_POSITION_PERCENT: float = 20.0
    MAX_ORDERS_PER_MINUTE: int = 10
    
    @validator("DATABASE_URL", pre=True)
    def validate_database_url(cls, v: str) -> str:
        """验证数据库URL格式"""
        if not v.startswith(("postgresql://", "postgresql+psycopg2://")):
            raise ValueError("DATABASE_URL must be a PostgreSQL URL")
        return v
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore"  # 忽略额外的环境变量
    }


# 创建全局配置实例
settings = Settings()