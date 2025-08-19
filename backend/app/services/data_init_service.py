"""
数据初始化服务
"""
import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
from decimal import Decimal

from ..core.database import get_db
from ..models.user import User
from ..models.account import Account, AccountType, AccountStatus
from ..services.account_service import AccountService

logger = logging.getLogger(__name__)


class DataInitService:
    """数据初始化服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.account_service = AccountService(db)
    
    def create_default_accounts_for_user(self, user: User) -> list[Account]:
        """为用户创建默认账户"""
        try:
            # 检查用户是否已有账户
            existing_accounts = self.account_service.get_user_accounts(user.id)
            if existing_accounts:
                logger.info(f"用户 {user.username} 已有 {len(existing_accounts)} 个账户")
                return existing_accounts
            
            # 创建默认账户
            default_accounts = []
            
            # 1. 主现金账户
            main_account_data = {
                'account_name': '主账户',
                'account_type': 'CASH',
                'base_currency': 'CNY',
                'risk_level': 'MEDIUM',
                'settings': {
                    'auto_transfer': True,
                    'risk_alert_threshold': 0.8,
                    'notification_preferences': {
                        'email': True,
                        'sms': False,
                        'push': True
                    }
                }
            }
            
            main_account = self.account_service.create_account(
                user_id=user.id,
                account_data=main_account_data
            )
            
            # 初始化资金（模拟入金）
            if main_account:
                self.account_service.deposit(
                    account_id=main_account.id,
                    amount=Decimal('1000000'),  # 100万初始资金
                    description="系统初始化资金"
                )
                default_accounts.append(main_account)
            
            # 2. 期货账户（如果是高级用户）
            if hasattr(user, 'user_type') and user.user_type in ['premium', 'vip', 'admin']:
                futures_account_data = {
                    'account_name': '期货账户',
                    'account_type': 'FUTURES',
                    'base_currency': 'CNY',
                    'risk_level': 'HIGH',
                    'settings': {
                        'auto_transfer': False,
                        'risk_alert_threshold': 0.9,
                        'margin_call_threshold': 0.7,
                        'notification_preferences': {
                            'email': True,
                            'sms': True,
                            'push': True
                        }
                    }
                }
                
                futures_account = self.account_service.create_account(
                    user_id=user.id,
                    account_data=futures_account_data
                )
                
                if futures_account:
                    self.account_service.deposit(
                        account_id=futures_account.id,
                        amount=Decimal('500000'),  # 50万期货资金
                        description="系统初始化期货资金"
                    )
                    default_accounts.append(futures_account)
            
            logger.info(f"为用户 {user.username} 创建了 {len(default_accounts)} 个默认账户")
            return default_accounts
            
        except Exception as e:
            logger.error(f"为用户 {user.username} 创建默认账户失败: {e}")
            self.db.rollback()
            return []
    
    def initialize_all_users_accounts(self):
        """为所有用户初始化账户"""
        try:
            users = self.db.query(User).filter(User.is_active == True).all()
            
            total_created = 0
            for user in users:
                accounts = self.create_default_accounts_for_user(user)
                total_created += len(accounts)
            
            logger.info(f"为 {len(users)} 个用户总共创建了 {total_created} 个账户")
            return total_created
            
        except Exception as e:
            logger.error(f"批量初始化用户账户失败: {e}")
            return 0
    
    def create_sample_market_data(self):
        """创建示例市场数据"""
        # 这里可以添加创建示例市场数据的逻辑
        pass
    
    def create_sample_strategies(self):
        """创建示例策略"""
        # 这里可以添加创建示例策略的逻辑
        pass


def init_user_data(user: User, db: Session = None):
    """为单个用户初始化数据"""
    if not db:
        db = next(get_db())
    
    try:
        init_service = DataInitService(db)
        accounts = init_service.create_default_accounts_for_user(user)
        return accounts
    except Exception as e:
        logger.error(f"初始化用户数据失败: {e}")
        return []


def init_all_data(db: Session = None):
    """初始化所有数据"""
    if not db:
        db = next(get_db())
    
    try:
        init_service = DataInitService(db)
        
        # 初始化所有用户账户
        accounts_created = init_service.initialize_all_users_accounts()
        
        # 创建示例数据
        init_service.create_sample_market_data()
        init_service.create_sample_strategies()
        
        logger.info(f"数据初始化完成，创建了 {accounts_created} 个账户")
        return True
        
    except Exception as e:
        logger.error(f"数据初始化失败: {e}")
        return False