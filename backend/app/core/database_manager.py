"""
数据库管理工具类
"""
from typing import Generator, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
import logging

from .database import SessionLocal, engine, Base
from .influxdb import influx_manager

logger = logging.getLogger(__name__)


class DatabaseManager:
    """数据库管理器"""
    
    @staticmethod
    def create_tables():
        """创建所有数据表"""
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("数据表创建成功")
        except Exception as e:
            logger.error(f"数据表创建失败: {e}")
            raise
    
    @staticmethod
    def drop_tables():
        """删除所有数据表"""
        try:
            Base.metadata.drop_all(bind=engine)
            logger.info("数据表删除成功")
        except Exception as e:
            logger.error(f"数据表删除失败: {e}")
            raise
    
    @staticmethod
    @contextmanager
    def get_db_session() -> Generator[Session, None, None]:
        """获取数据库会话上下文管理器"""
        db = SessionLocal()
        try:
            yield db
            db.commit()
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"数据库操作失败: {e}")
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"未知错误: {e}")
            raise
        finally:
            db.close()
    
    @staticmethod
    def get_db() -> Generator[Session, None, None]:
        """获取数据库会话（用于FastAPI依赖注入）"""
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    @staticmethod
    def init_database():
        """初始化数据库"""
        try:
            # 创建PostgreSQL表
            DatabaseManager.create_tables()
            
            # 测试InfluxDB连接
            influx_manager.client.ping()
            logger.info("InfluxDB连接测试成功")
            
            logger.info("数据库初始化完成")
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise
    
    @staticmethod
    def health_check() -> dict:
        """数据库健康检查"""
        health_status = {
            "postgresql": False,
            "influxdb": False,
            "redis": False
        }
        
        # 检查PostgreSQL
        try:
            with DatabaseManager.get_db_session() as db:
                db.execute("SELECT 1")
            health_status["postgresql"] = True
        except Exception as e:
            logger.error(f"PostgreSQL健康检查失败: {e}")
        
        # 检查InfluxDB
        try:
            influx_manager.client.ping()
            health_status["influxdb"] = True
        except Exception as e:
            logger.error(f"InfluxDB健康检查失败: {e}")
        
        # 检查Redis
        try:
            from .database import redis_client
            redis_client.ping()
            health_status["redis"] = True
        except Exception as e:
            logger.error(f"Redis健康检查失败: {e}")
        
        return health_status


# 创建全局数据库管理器实例
db_manager = DatabaseManager()