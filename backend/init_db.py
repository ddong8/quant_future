#!/usr/bin/env python3
"""
增强的数据库初始化脚本
包含重试机制、健康检查和详细错误日志记录
"""
import sys
import os
import time
from pathlib import Path
from typing import Optional, Dict, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.core.database_manager import db_manager
from app.core.config import settings
from app.models import User, UserRole
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from sqlalchemy import text
from passlib.context import CryptContext
import logging
from contextlib import contextmanager

# 配置详细日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/init_db.log', mode='a', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 重试配置
MAX_RETRIES = 5
RETRY_DELAY = 2  # 秒
CONNECTION_TIMEOUT = 30  # 秒


@contextmanager
def database_session_with_retry():
    """带重试机制的数据库会话上下文管理器"""
    for attempt in range(MAX_RETRIES):
        try:
            with db_manager.get_db_session() as db:
                yield db
                return
        except (OperationalError, SQLAlchemyError) as e:
            logger.warning(f"数据库连接尝试 {attempt + 1}/{MAX_RETRIES} 失败: {e}")
            if attempt == MAX_RETRIES - 1:
                logger.error("数据库连接重试次数已用完")
                raise
            time.sleep(RETRY_DELAY * (2 ** attempt))  # 指数退避


def wait_for_database_ready(max_wait_time: int = CONNECTION_TIMEOUT) -> bool:
    """等待数据库就绪"""
    logger.info("等待数据库连接就绪...")
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        try:
            with db_manager.get_db_session() as db:
                # 执行简单查询测试连接
                db.execute(text("SELECT 1"))
                logger.info("数据库连接就绪")
                return True
        except Exception as e:
            logger.debug(f"数据库连接测试失败: {e}")
            time.sleep(1)
    
    logger.error(f"数据库在 {max_wait_time} 秒内未就绪")
    return False


def verify_database_schema() -> bool:
    """验证数据库模式完整性"""
    logger.info("验证数据库模式...")
    try:
        with database_session_with_retry() as db:
            # 检查关键表是否存在
            required_tables = ['users', 'strategies', 'orders', 'positions', 'backtests']
            for table in required_tables:
                result = db.execute(text(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = '{table}'
                    )
                """)).scalar()
                
                if not result:
                    logger.error(f"必需的表 '{table}' 不存在")
                    return False
            
            logger.info("数据库模式验证通过")
            return True
    except Exception as e:
        logger.error(f"数据库模式验证失败: {e}")
        return False


def create_admin_user(db: Session):
    """创建管理员用户"""
    try:
        # 检查是否已存在管理员用户
        admin_user = db.query(User).filter(User.role == UserRole.ADMIN).first()
        if admin_user:
            logger.info(f"管理员用户已存在: {admin_user.username}")
            return admin_user
        
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
        db.flush()  # 获取ID但不提交
        logger.info(f"管理员用户创建成功 - ID: {admin.id}, 用户名: admin")
        return admin
        
    except Exception as e:
        logger.error(f"创建管理员用户失败: {e}")
        db.rollback()
        raise


def create_default_users(db: Session) -> Dict[str, User]:
    """创建默认用户"""
    created_users = {}
    
    try:
        # 定义默认用户配置
        default_users_config = [
            {
                "username": "trader1",
                "email": "trader1@trading.com",
                "password": "trader123",
                "role": UserRole.TRADER,
                "full_name": "示例交易员"
            },
            {
                "username": "viewer1", 
                "email": "viewer1@trading.com",
                "password": "viewer123",
                "role": UserRole.VIEWER,
                "full_name": "示例观察者"
            }
        ]
        
        for user_config in default_users_config:
            # 检查用户是否已存在
            existing_user = db.query(User).filter(User.username == user_config["username"]).first()
            if existing_user:
                logger.info(f"用户 {user_config['username']} 已存在")
                created_users[user_config["username"]] = existing_user
                continue
            
            # 创建新用户
            hashed_password = pwd_context.hash(user_config["password"])
            user = User(
                username=user_config["username"],
                email=user_config["email"],
                hashed_password=hashed_password,
                role=user_config["role"],
                full_name=user_config["full_name"],
                is_active=True,
                is_verified=True
            )
            
            db.add(user)
            db.flush()  # 获取ID但不提交
            created_users[user_config["username"]] = user
            logger.info(f"用户 {user_config['username']} 创建成功 - ID: {user.id}")
        
        return created_users
        
    except Exception as e:
        logger.error(f"创建默认用户失败: {e}")
        db.rollback()
        raise


def validate_user_creation(db: Session, users: Dict[str, User]) -> bool:
    """验证用户创建结果"""
    try:
        for username, user in users.items():
            # 验证用户是否正确保存到数据库
            db_user = db.query(User).filter(User.id == user.id).first()
            if not db_user:
                logger.error(f"用户 {username} 验证失败: 数据库中未找到")
                return False
            
            # 验证用户属性
            if db_user.username != user.username or db_user.role != user.role:
                logger.error(f"用户 {username} 验证失败: 属性不匹配")
                return False
        
        logger.info("用户创建验证通过")
        return True
        
    except Exception as e:
        logger.error(f"用户创建验证失败: {e}")
        return False


def perform_comprehensive_health_check() -> Dict[str, Any]:
    """执行全面的健康检查"""
    logger.info("执行全面健康检查...")
    health_status = {
        "overall": False,
        "components": {},
        "timestamp": time.time()
    }
    
    try:
        # 基础健康检查
        basic_health = db_manager.health_check()
        health_status["components"].update(basic_health)
        
        # 数据库连接池状态检查
        try:
            from app.core.database import engine
            pool_status = {
                "pool_size": engine.pool.size(),
                "checked_in": engine.pool.checkedin(),
                "checked_out": engine.pool.checkedout(),
                "overflow": engine.pool.overflow(),
                "invalid": engine.pool.invalid()
            }
            health_status["components"]["connection_pool"] = pool_status
            logger.info(f"连接池状态: {pool_status}")
        except Exception as e:
            logger.warning(f"连接池状态检查失败: {e}")
            health_status["components"]["connection_pool"] = {"error": str(e)}
        
        # 检查是否所有关键组件都健康
        critical_components = ["postgresql", "influxdb", "redis"]
        all_healthy = all(health_status["components"].get(comp, False) for comp in critical_components)
        health_status["overall"] = all_healthy
        
        if all_healthy:
            logger.info("所有组件健康检查通过")
        else:
            logger.warning("部分组件健康检查失败")
        
        return health_status
        
    except Exception as e:
        logger.error(f"健康检查执行失败: {e}")
        health_status["components"]["health_check_error"] = str(e)
        return health_status


def log_initialization_summary(admin_user: User, default_users: Dict[str, User], health_status: Dict[str, Any]):
    """记录初始化摘要"""
    logger.info("=" * 60)
    logger.info("数据库初始化完成摘要")
    logger.info("=" * 60)
    
    # 用户信息
    logger.info("创建的用户账号:")
    logger.info(f"  管理员 - ID: {admin_user.id}, 用户名: admin, 密码: admin123")
    
    for username, user in default_users.items():
        password = "trader123" if user.role == UserRole.TRADER else "viewer123"
        logger.info(f"  {user.role.value} - ID: {user.id}, 用户名: {username}, 密码: {password}")
    
    # 健康状态
    logger.info("\n系统健康状态:")
    for component, status in health_status["components"].items():
        if isinstance(status, bool):
            status_text = "✓ 正常" if status else "✗ 异常"
            logger.info(f"  {component}: {status_text}")
        elif isinstance(status, dict) and "error" not in status:
            logger.info(f"  {component}: ✓ 正常")
    
    overall_status = "✓ 正常" if health_status["overall"] else "✗ 部分异常"
    logger.info(f"  整体状态: {overall_status}")
    
    logger.info("=" * 60)


def main():
    """主函数"""
    start_time = time.time()
    
    try:
        logger.info("开始增强的数据库初始化流程...")
        logger.info(f"数据库URL: {settings.DATABASE_URL}")
        logger.info(f"最大重试次数: {MAX_RETRIES}")
        logger.info(f"连接超时时间: {CONNECTION_TIMEOUT}秒")
        
        # 步骤1: 等待数据库就绪
        if not wait_for_database_ready():
            logger.error("数据库连接超时，初始化失败")
            sys.exit(1)
        
        # 步骤2: 初始化数据库结构
        logger.info("初始化数据库结构...")
        db_manager.init_database()
        
        # 步骤3: 验证数据库模式
        if not verify_database_schema():
            logger.error("数据库模式验证失败，初始化终止")
            sys.exit(1)
        
        # 步骤4: 创建用户数据
        logger.info("创建默认用户数据...")
        with database_session_with_retry() as db:
            # 创建管理员用户
            admin_user = create_admin_user(db)
            
            # 创建默认用户
            default_users = create_default_users(db)
            
            # 验证用户创建
            all_users = {"admin": admin_user, **default_users}
            if not validate_user_creation(db, all_users):
                logger.error("用户创建验证失败，回滚事务")
                raise Exception("用户创建验证失败")
            
            # 提交事务
            db.commit()
            logger.info("所有用户数据创建并验证成功")
        
        # 步骤5: 执行全面健康检查
        health_status = perform_comprehensive_health_check()
        
        # 步骤6: 记录初始化摘要
        elapsed_time = time.time() - start_time
        logger.info(f"初始化耗时: {elapsed_time:.2f}秒")
        
        log_initialization_summary(admin_user, default_users, health_status)
        
        if not health_status["overall"]:
            logger.warning("初始化完成，但部分组件存在问题，请检查日志")
            sys.exit(2)  # 部分成功退出码
        
        logger.info("数据库初始化完全成功！")
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"数据库初始化失败 (耗时: {elapsed_time:.2f}秒): {e}")
        logger.exception("详细错误信息:")
        sys.exit(1)


if __name__ == "__main__":
    main()