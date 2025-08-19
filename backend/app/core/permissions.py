"""
权限检查核心模块
"""
import logging
from typing import List, Dict, Any, Optional
from ..models.user import User

logger = logging.getLogger(__name__)

# 权限常量定义
class Permissions:
    """权限常量"""
    
    # 基础权限
    READ_PROFILE = "read_profile"
    WRITE_PROFILE = "write_profile"
    
    # 设置权限
    READ_SETTINGS = "read_settings"
    WRITE_SETTINGS = "write_settings"
    MANAGE_SETTINGS = "manage_settings"
    
    # 交易权限
    VIEW_ORDERS = "view_orders"
    CREATE_ORDERS = "create_orders"
    CANCEL_ORDERS = "cancel_orders"
    VIEW_POSITIONS = "view_positions"
    CLOSE_POSITIONS = "close_positions"
    
    # 账户权限
    VIEW_ACCOUNT = "view_account"
    MANAGE_ACCOUNT = "manage_account"
    VIEW_TRANSACTIONS = "view_transactions"
    
    # 风险管理权限
    VIEW_RISK = "view_risk"
    MANAGE_RISK = "manage_risk"
    
    # 系统权限
    VIEW_SYSTEM_LOGS = "view_system_logs"
    MANAGE_SYSTEM = "manage_system"
    
    # 高级功能权限
    USE_ADVANCED_FEATURES = "use_advanced_features"
    API_ACCESS = "api_access"
    EXPORT_DATA = "export_data"

# 用户等级定义
class UserLevels:
    """用户等级"""
    GUEST = 0
    BASIC = 1
    STANDARD = 2
    PREMIUM = 3
    VIP = 4
    ADMIN = 9

# 默认权限映射
DEFAULT_PERMISSIONS = {
    UserLevels.GUEST: [
        Permissions.READ_PROFILE,
    ],
    UserLevels.BASIC: [
        Permissions.READ_PROFILE,
        Permissions.WRITE_PROFILE,
        Permissions.READ_SETTINGS,
        Permissions.WRITE_SETTINGS,
        Permissions.VIEW_ACCOUNT,
    ],
    UserLevels.STANDARD: [
        Permissions.READ_PROFILE,
        Permissions.WRITE_PROFILE,
        Permissions.READ_SETTINGS,
        Permissions.WRITE_SETTINGS,
        Permissions.VIEW_ACCOUNT,
        Permissions.MANAGE_ACCOUNT,
        Permissions.VIEW_ORDERS,
        Permissions.CREATE_ORDERS,
        Permissions.CANCEL_ORDERS,
        Permissions.VIEW_POSITIONS,
        Permissions.VIEW_TRANSACTIONS,
        Permissions.VIEW_RISK,
    ],
    UserLevels.PREMIUM: [
        Permissions.READ_PROFILE,
        Permissions.WRITE_PROFILE,
        Permissions.READ_SETTINGS,
        Permissions.WRITE_SETTINGS,
        Permissions.MANAGE_SETTINGS,
        Permissions.VIEW_ACCOUNT,
        Permissions.MANAGE_ACCOUNT,
        Permissions.VIEW_ORDERS,
        Permissions.CREATE_ORDERS,
        Permissions.CANCEL_ORDERS,
        Permissions.VIEW_POSITIONS,
        Permissions.CLOSE_POSITIONS,
        Permissions.VIEW_TRANSACTIONS,
        Permissions.VIEW_RISK,
        Permissions.MANAGE_RISK,
        Permissions.USE_ADVANCED_FEATURES,
        Permissions.API_ACCESS,
        Permissions.EXPORT_DATA,
    ],
    UserLevels.VIP: [
        Permissions.READ_PROFILE,
        Permissions.WRITE_PROFILE,
        Permissions.READ_SETTINGS,
        Permissions.WRITE_SETTINGS,
        Permissions.MANAGE_SETTINGS,
        Permissions.VIEW_ACCOUNT,
        Permissions.MANAGE_ACCOUNT,
        Permissions.VIEW_ORDERS,
        Permissions.CREATE_ORDERS,
        Permissions.CANCEL_ORDERS,
        Permissions.VIEW_POSITIONS,
        Permissions.CLOSE_POSITIONS,
        Permissions.VIEW_TRANSACTIONS,
        Permissions.VIEW_RISK,
        Permissions.MANAGE_RISK,
        Permissions.USE_ADVANCED_FEATURES,
        Permissions.API_ACCESS,
        Permissions.EXPORT_DATA,
    ],
    UserLevels.ADMIN: [
        # 管理员拥有所有权限
        Permissions.READ_PROFILE,
        Permissions.WRITE_PROFILE,
        Permissions.READ_SETTINGS,
        Permissions.WRITE_SETTINGS,
        Permissions.MANAGE_SETTINGS,
        Permissions.VIEW_ACCOUNT,
        Permissions.MANAGE_ACCOUNT,
        Permissions.VIEW_ORDERS,
        Permissions.CREATE_ORDERS,
        Permissions.CANCEL_ORDERS,
        Permissions.VIEW_POSITIONS,
        Permissions.CLOSE_POSITIONS,
        Permissions.VIEW_TRANSACTIONS,
        Permissions.VIEW_RISK,
        Permissions.MANAGE_RISK,
        Permissions.USE_ADVANCED_FEATURES,
        Permissions.API_ACCESS,
        Permissions.EXPORT_DATA,
        Permissions.VIEW_SYSTEM_LOGS,
        Permissions.MANAGE_SYSTEM,
    ]
}

def get_user_level(user: User) -> int:
    """获取用户等级"""
    if hasattr(user, 'level') and user.level is not None:
        return user.level
    
    # 如果没有设置等级，根据用户类型推断
    if hasattr(user, 'user_type'):
        if user.user_type == 'admin':
            return UserLevels.ADMIN
        elif user.user_type == 'vip':
            return UserLevels.VIP
        elif user.user_type == 'premium':
            return UserLevels.PREMIUM
        elif user.user_type == 'standard':
            return UserLevels.STANDARD
        elif user.user_type == 'basic':
            return UserLevels.BASIC
    
    # 默认为基础用户
    return UserLevels.BASIC

def get_user_permissions(user: User) -> List[str]:
    """获取用户权限列表"""
    try:
        user_level = get_user_level(user)
        
        # 获取基于等级的默认权限
        permissions = DEFAULT_PERMISSIONS.get(user_level, []).copy()
        
        # 如果用户有自定义权限，合并权限
        if hasattr(user, 'custom_permissions') and user.custom_permissions:
            if isinstance(user.custom_permissions, list):
                permissions.extend(user.custom_permissions)
            elif isinstance(user.custom_permissions, dict):
                # 处理权限对象格式
                for perm, enabled in user.custom_permissions.items():
                    if enabled and perm not in permissions:
                        permissions.append(perm)
                    elif not enabled and perm in permissions:
                        permissions.remove(perm)
        
        # 去重并返回
        return list(set(permissions))
        
    except Exception as e:
        logger.error(f"获取用户权限失败: {e}")
        return DEFAULT_PERMISSIONS.get(UserLevels.BASIC, [])

def check_user_permission(user: User, permission: str) -> bool:
    """检查用户是否有指定权限"""
    try:
        user_permissions = get_user_permissions(user)
        return permission in user_permissions
        
    except Exception as e:
        logger.error(f"检查用户权限失败: {e}")
        return False

def check_user_permissions(user: User, permissions: List[str], require_all: bool = True) -> bool:
    """检查用户是否有指定的多个权限"""
    try:
        user_permissions = get_user_permissions(user)
        
        if require_all:
            # 需要所有权限
            return all(perm in user_permissions for perm in permissions)
        else:
            # 只需要任一权限
            return any(perm in user_permissions for perm in permissions)
            
    except Exception as e:
        logger.error(f"检查用户权限失败: {e}")
        return False

def check_user_level(user: User, min_level: int) -> bool:
    """检查用户等级是否满足最低要求"""
    try:
        user_level = get_user_level(user)
        return user_level >= min_level
        
    except Exception as e:
        logger.error(f"检查用户等级失败: {e}")
        return False

def get_permission_description(permission: str) -> str:
    """获取权限描述"""
    descriptions = {
        Permissions.READ_PROFILE: "查看个人资料",
        Permissions.WRITE_PROFILE: "修改个人资料",
        Permissions.READ_SETTINGS: "查看设置",
        Permissions.WRITE_SETTINGS: "修改设置",
        Permissions.MANAGE_SETTINGS: "管理设置",
        Permissions.VIEW_ORDERS: "查看订单",
        Permissions.CREATE_ORDERS: "创建订单",
        Permissions.CANCEL_ORDERS: "取消订单",
        Permissions.VIEW_POSITIONS: "查看持仓",
        Permissions.CLOSE_POSITIONS: "平仓",
        Permissions.VIEW_ACCOUNT: "查看账户",
        Permissions.MANAGE_ACCOUNT: "管理账户",
        Permissions.VIEW_TRANSACTIONS: "查看交易记录",
        Permissions.VIEW_RISK: "查看风险信息",
        Permissions.MANAGE_RISK: "管理风险设置",
        Permissions.VIEW_SYSTEM_LOGS: "查看系统日志",
        Permissions.MANAGE_SYSTEM: "系统管理",
        Permissions.USE_ADVANCED_FEATURES: "使用高级功能",
        Permissions.API_ACCESS: "API访问",
        Permissions.EXPORT_DATA: "导出数据",
    }
    
    return descriptions.get(permission, permission)

def get_level_description(level: int) -> str:
    """获取用户等级描述"""
    descriptions = {
        UserLevels.GUEST: "访客",
        UserLevels.BASIC: "基础用户",
        UserLevels.STANDARD: "标准用户",
        UserLevels.PREMIUM: "高级用户",
        UserLevels.VIP: "VIP用户",
        UserLevels.ADMIN: "管理员",
    }
    
    return descriptions.get(level, f"等级{level}")

class PermissionChecker:
    """权限检查器类"""
    
    def __init__(self, user: User):
        self.user = user
        self.user_level = get_user_level(user)
        self.user_permissions = get_user_permissions(user)
    
    def has_permission(self, permission: str) -> bool:
        """检查是否有指定权限"""
        return permission in self.user_permissions
    
    def has_permissions(self, permissions: List[str], require_all: bool = True) -> bool:
        """检查是否有指定的多个权限"""
        if require_all:
            return all(perm in self.user_permissions for perm in permissions)
        else:
            return any(perm in self.user_permissions for perm in permissions)
    
    def has_level(self, min_level: int) -> bool:
        """检查是否满足最低等级要求"""
        return self.user_level >= min_level
    
    def can_access_feature(self, feature_config: Dict[str, Any]) -> bool:
        """检查是否可以访问某个功能"""
        # 检查等级要求
        if 'min_level' in feature_config:
            if not self.has_level(feature_config['min_level']):
                return False
        
        # 检查权限要求
        if 'required_permissions' in feature_config:
            permissions = feature_config['required_permissions']
            require_all = feature_config.get('require_all_permissions', True)
            if not self.has_permissions(permissions, require_all):
                return False
        
        # 检查用户类型要求
        if 'allowed_user_types' in feature_config:
            user_type = getattr(self.user, 'user_type', 'basic')
            if user_type not in feature_config['allowed_user_types']:
                return False
        
        return True
    
    def get_accessible_features(self, features_config: Dict[str, Dict[str, Any]]) -> List[str]:
        """获取用户可访问的功能列表"""
        accessible_features = []
        
        for feature_name, feature_config in features_config.items():
            if self.can_access_feature(feature_config):
                accessible_features.append(feature_name)
        
        return accessible_features

# 权限映射 - 将API权限映射到系统权限
PERMISSION_MAPPING = {
    "account:read": Permissions.VIEW_ACCOUNT,
    "account:create": Permissions.MANAGE_ACCOUNT,
    "account:update": Permissions.MANAGE_ACCOUNT,
    "account:delete": Permissions.MANAGE_ACCOUNT,
    "account:deposit": Permissions.MANAGE_ACCOUNT,
    "account:withdraw": Permissions.MANAGE_ACCOUNT,
    "account:manage": Permissions.MANAGE_ACCOUNT,
    "order:read": Permissions.VIEW_ORDERS,
    "order:create": Permissions.CREATE_ORDERS,
    "order:cancel": Permissions.CANCEL_ORDERS,
    "position:read": Permissions.VIEW_POSITIONS,
    "position:close": Permissions.CLOSE_POSITIONS,
    "transaction:read": Permissions.VIEW_TRANSACTIONS,
    "risk:read": Permissions.VIEW_RISK,
    "risk:manage": Permissions.MANAGE_RISK,
}

# 权限装饰器
def require_permission(permission: str):
    """权限检查装饰器 - 支持FastAPI"""
    from functools import wraps
    from fastapi import HTTPException, status
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从kwargs中获取current_user
            user = kwargs.get('current_user')
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="未认证用户"
                )
            
            # 映射API权限到系统权限
            system_permission = PERMISSION_MAPPING.get(permission, permission)
            
            if not check_user_permission(user, system_permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"权限不足，需要权限: {get_permission_description(system_permission)}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_level(min_level: int):
    """等级检查装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            user = kwargs.get('current_user') or args[0] if args else None
            
            if not user or not check_user_level(user, min_level):
                raise PermissionError(f"需要用户等级: {get_level_description(min_level)}")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator