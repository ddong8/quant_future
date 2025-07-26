#!/usr/bin/env python3
"""
数据库初始化脚本
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.core.database_manager import db_manager
from app.core.config import settings
from app.models import User, UserRole
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_admin_user(db: Session):
    """创建管理员用户"""
    try:
        # 检查是否已存在管理员用户
        admin_user = db.query(User).filter(User.role == UserRole.ADMIN).first()
        if admin_user:
            logger.info("管理员用户已存在")
            return
        
        # 创建管理员用户
        hashed_password = pwd_context.hash("admin123")
        admin = User(
            username="admin",
            email="admin@trading.com",
            hashed_password=hashed_password,
            role=UserRole.ADMIN,
            full_name="系统管理员",
            is_active=True,
            is_verified=True
        )
        
        db.add(admin)
        db.commit()
        logger.info("管理员用户创建成功 - 用户名: admin, 密码: admin123")
        
    except Exception as e:
        logger.error(f"创建管理员用户失败: {e}")
        db.rollback()
        raise


def init_sample_data(db: Session):
    """初始化示例数据"""
    try:
        # 创建示例交易员用户
        trader_exists = db.query(User).filter(User.username == "trader1").first()
        if not trader_exists:
            hashed_password = pwd_context.hash("trader123")
            trader = User(
                username="trader1",
                email="trader1@trading.com",
                hashed_password=hashed_password,
                role=UserRole.TRADER,
                full_name="示例交易员",
                is_active=True,
                is_verified=True
            )
            db.add(trader)
            logger.info("示例交易员用户创建成功")
        
        # 创建示例观察者用户
        viewer_exists = db.query(User).filter(User.username == "viewer1").first()
        if not viewer_exists:
            hashed_password = pwd_context.hash("viewer123")
            viewer = User(
                username="viewer1",
                email="viewer1@trading.com",
                hashed_password=hashed_password,
                role=UserRole.VIEWER,
                full_name="示例观察者",
                is_active=True,
                is_verified=True
            )
            db.add(viewer)
            logger.info("示例观察者用户创建成功")
        
        db.commit()
        
    except Exception as e:
        logger.error(f"初始化示例数据失败: {e}")
        db.rollback()
        raise


def main():
    """主函数"""
    try:
        logger.info("开始初始化数据库...")
        logger.info(f"数据库URL: {settings.DATABASE_URL}")
        
        # 初始化数据库
        db_manager.init_database()
        
        # 创建初始数据
        with db_manager.get_db_session() as db:
            create_admin_user(db)
            init_sample_data(db)
        
        # 健康检查
        health = db_manager.health_check()
        logger.info(f"数据库健康状态: {health}")
        
        logger.info("数据库初始化完成！")
        logger.info("默认用户账号:")
        logger.info("  管理员 - 用户名: admin, 密码: admin123")
        logger.info("  交易员 - 用户名: trader1, 密码: trader123")
        logger.info("  观察者 - 用户名: viewer1, 密码: viewer123")
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()