"""
应用配置模块
包含完整的环境变量配置和验证逻辑
"""
from typing import Optional, List, Union
from pydantic import validator, Field
from pydantic_settings import BaseSettings
import os
import secrets
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """应用配置类"""
    
    # ============================================================================
    # 应用基础配置
    # ============================================================================
    APP_NAME: str = "量化交易平台"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    SECRET_KEY: str = Field(
        default="default-secret-key-change-in-production",
        min_length=32,
        description="应用密钥，生产环境必须修改"
    )
    
    # ============================================================================
    # 数据库配置
    # ============================================================================
    DATABASE_URL: str = "postgresql://postgres:password@db:5432/trading_db"
    INFLUXDB_URL: str = "http://influxdb:8086"
    INFLUXDB_TOKEN: str = "my-super-secret-auth-token"
    INFLUXDB_ORG: str = "trading-org"
    INFLUXDB_BUCKET: str = "market-data"
    
    # Redis配置
    REDIS_URL: str = "redis://redis:6379/0"
    
    # 数据库连接池配置
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_RECYCLE: int = 300
    DB_POOL_PRE_PING: bool = True
    
    # ============================================================================
    # JWT 认证配置
    # ============================================================================
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    @property
    def JWT_SECRET_KEY(self) -> str:
        """JWT 密钥，使用应用密钥"""
        return self.SECRET_KEY
    
    # ============================================================================
    # 交易接口配置
    # ============================================================================
    TQSDK_AUTH: Optional[str] = None
    TQSDK_ACCOUNT: Optional[str] = None
    
    # ============================================================================
    # 邮件服务配置
    # ============================================================================
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    
    # ============================================================================
    # 日志配置
    # ============================================================================
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    
    # ============================================================================
    # 风险管理配置
    # ============================================================================
    MAX_DAILY_LOSS_PERCENT: float = 5.0
    MAX_POSITION_PERCENT: float = 20.0
    MAX_ORDERS_PER_MINUTE: int = 10
    
    # ============================================================================
    # Docker 和部署配置
    # ============================================================================
    # 数据库初始化配置
    DB_INIT_RETRY_COUNT: int = 5
    DB_INIT_RETRY_DELAY: int = 2
    DB_INIT_TIMEOUT: int = 30
    
    # 健康检查配置
    HEALTH_CHECK_INTERVAL: str = "30s"
    HEALTH_CHECK_TIMEOUT: str = "10s"
    HEALTH_CHECK_RETRIES: int = 3
    
    # 端口配置
    BACKEND_PORT: int = 8000
    FRONTEND_PORT: int = 3000
    POSTGRES_PORT: int = 5432
    INFLUXDB_PORT: int = 8086
    REDIS_PORT: int = 6379
    
    # ============================================================================
    # CORS 和安全配置
    # ============================================================================
    DEV_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    PROD_CORS_ORIGINS: List[str] = ["https://yourdomain.com"]
    PROD_SECURE_COOKIES: bool = True
    PROD_HTTPS_ONLY: bool = True
    
    @property
    def CORS_ORIGINS(self) -> List[str]:
        """根据环境返回 CORS 配置"""
        return self.DEV_CORS_ORIGINS if self.DEBUG else self.PROD_CORS_ORIGINS
    
    # ============================================================================
    # 监控配置
    # ============================================================================
    PROMETHEUS_ENABLED: bool = False
    PROMETHEUS_PORT: int = 9090
    GRAFANA_ENABLED: bool = False
    GRAFANA_PORT: int = 3001
    
    # ============================================================================
    # 性能配置
    # ============================================================================
    WORKER_PROCESSES: int = 4
    WORKER_CONNECTIONS: int = 1000
    KEEPALIVE_TIMEOUT: int = 65
    REDIS_MAX_CONNECTIONS: int = 50
    REDIS_CONNECTION_TIMEOUT: int = 5
    
    # ============================================================================
    # 验证器
    # ============================================================================
    @validator("DATABASE_URL", pre=True)
    def validate_database_url(cls, v: str) -> str:
        """验证数据库URL格式"""
        if not v.startswith(("postgresql://", "postgresql+psycopg2://")):
            raise ValueError("DATABASE_URL must be a PostgreSQL URL")
        return v
    
    @validator("SECRET_KEY", pre=True)
    def validate_secret_key(cls, v: str) -> str:
        """验证密钥安全性"""
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        
        # 在生产环境中检查是否使用了默认密钥
        import os
        debug_mode = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")
        if not debug_mode and v == "default-secret-key-change-in-production":
            raise ValueError("Must change SECRET_KEY in production environment")
        
        return v
    
    @validator("INFLUXDB_URL", pre=True)
    def validate_influxdb_url(cls, v: str) -> str:
        """验证 InfluxDB URL 格式"""
        if not v.startswith(("http://", "https://")):
            raise ValueError("INFLUXDB_URL must be a valid HTTP/HTTPS URL")
        return v
    
    @validator("REDIS_URL", pre=True)
    def validate_redis_url(cls, v: str) -> str:
        """验证 Redis URL 格式"""
        if not v.startswith("redis://"):
            raise ValueError("REDIS_URL must be a valid Redis URL")
        return v
    
    @validator("LOG_LEVEL", pre=True)
    def validate_log_level(cls, v: str) -> str:
        """验证日志级别"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v.upper()
    
    @validator("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", pre=True)
    def validate_jwt_expire_minutes(cls, v) -> int:
        """验证 JWT 过期时间"""
        # 转换为整数
        if isinstance(v, str):
            try:
                v = int(v)
            except ValueError:
                raise ValueError("JWT_ACCESS_TOKEN_EXPIRE_MINUTES must be a valid integer")
        
        if v <= 0:
            raise ValueError("JWT_ACCESS_TOKEN_EXPIRE_MINUTES must be positive")
        if v > 1440:  # 24小时
            logger.warning(f"JWT token expire time is very long: {v} minutes")
        return v
    
    @validator("MAX_DAILY_LOSS_PERCENT", pre=True)
    def validate_max_daily_loss(cls, v) -> float:
        """验证最大日损失百分比"""
        # 转换为浮点数
        if isinstance(v, str):
            try:
                v = float(v)
            except ValueError:
                raise ValueError("MAX_DAILY_LOSS_PERCENT must be a valid number")
        
        if v <= 0 or v > 100:
            raise ValueError("MAX_DAILY_LOSS_PERCENT must be between 0 and 100")
        return v
    
    @validator("MAX_POSITION_PERCENT", pre=True)
    def validate_max_position(cls, v) -> float:
        """验证最大持仓百分比"""
        # 转换为浮点数
        if isinstance(v, str):
            try:
                v = float(v)
            except ValueError:
                raise ValueError("MAX_POSITION_PERCENT must be a valid number")
        
        if v <= 0 or v > 100:
            raise ValueError("MAX_POSITION_PERCENT must be between 0 and 100")
        return v
    
    # ============================================================================
    # 配置验证方法
    # ============================================================================
    def validate_production_config(self) -> List[str]:
        """验证生产环境配置"""
        warnings = []
        
        # 检查关键配置
        if self.SECRET_KEY == "default-secret-key-change-in-production":
            warnings.append("SECRET_KEY is using default value")
        
        if self.INFLUXDB_TOKEN == "my-super-secret-auth-token":
            warnings.append("INFLUXDB_TOKEN is using default value")
        
        if "localhost" in self.DATABASE_URL:
            warnings.append("DATABASE_URL contains localhost, may not work in containers")
        
        if "localhost" in self.INFLUXDB_URL:
            warnings.append("INFLUXDB_URL contains localhost, may not work in containers")
        
        if "localhost" in self.REDIS_URL:
            warnings.append("REDIS_URL contains localhost, may not work in containers")
        
        # 检查邮件配置
        if not self.SMTP_HOST and not self.DEBUG:
            warnings.append("SMTP_HOST not configured, email notifications disabled")
        
        return warnings
    
    def get_database_config(self) -> dict:
        """获取数据库配置字典"""
        return {
            "url": self.DATABASE_URL,
            "pool_size": self.DB_POOL_SIZE,
            "max_overflow": self.DB_MAX_OVERFLOW,
            "pool_recycle": self.DB_POOL_RECYCLE,
            "pool_pre_ping": self.DB_POOL_PRE_PING,
        }
    
    def get_redis_config(self) -> dict:
        """获取 Redis 配置字典"""
        return {
            "url": self.REDIS_URL,
            "max_connections": self.REDIS_MAX_CONNECTIONS,
            "connection_timeout": self.REDIS_CONNECTION_TIMEOUT,
        }
    
    def get_jwt_config(self) -> dict:
        """获取 JWT 配置字典"""
        return {
            "secret_key": self.JWT_SECRET_KEY,
            "algorithm": self.JWT_ALGORITHM,
            "access_token_expire_minutes": self.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
            "refresh_token_expire_days": self.JWT_REFRESH_TOKEN_EXPIRE_DAYS,
        }
    
    # ============================================================================
    # Pydantic 配置
    # ============================================================================
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",  # 忽略额外的环境变量
        "validate_assignment": True,  # 验证赋值
    }


def create_settings() -> Settings:
    """创建配置实例并进行验证"""
    try:
        settings = Settings()
        
        # 在生产环境中验证配置
        if not settings.DEBUG:
            warnings = settings.validate_production_config()
            if warnings:
                logger.warning("Production configuration warnings:")
                for warning in warnings:
                    logger.warning(f"  - {warning}")
        
        logger.info(f"Configuration loaded successfully for {settings.APP_NAME} v{settings.APP_VERSION}")
        logger.info(f"Debug mode: {settings.DEBUG}")
        logger.info(f"Log level: {settings.LOG_LEVEL}")
        
        return settings
        
    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        raise


# 创建全局配置实例
settings = create_settings()