"""
依赖注入容器
"""
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt
import redis

from .database import get_db, get_influx_client, get_redis_client
from .config import settings
from .exceptions import AuthenticationError, AuthorizationError
from ..models import User, UserRole
from .security import TokenBlacklist

# JWT认证
security = HTTPBearer()


# get_database 函数已被移除，请直接使用 get_db


def get_influxdb():
    """获取InfluxDB客户端依赖"""
    return get_influx_client()


def get_redis() -> redis.Redis:
    """获取Redis客户端依赖"""
    return get_redis_client()


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> int:
    """获取当前用户ID"""
    try:
        # 检查令牌是否在黑名单中
        redis_client = get_redis_client()
        token_blacklist = TokenBlacklist(redis_client)
        
        if token_blacklist.is_blacklisted(credentials.credentials):
            raise AuthenticationError("认证令牌已失效")
        
        # 解码JWT token
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        user_id_str = payload.get("sub")
        if user_id_str is None:
            raise AuthenticationError("无效的认证令牌")
        
        return int(user_id_str)
        
    except JWTError:
        raise AuthenticationError("认证令牌验证失败")


def get_current_user(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> User:
    """获取当前用户对象"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise AuthenticationError("用户不存在")
    
    if not user.is_active:
        raise AuthenticationError("用户账户已被禁用")
    
    return user


def get_current_user_dict(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> dict:
    """获取当前用户（字典格式，用于兼容性）"""
    from sqlalchemy import text
    
    result = db.execute(
        text('SELECT id, username, email, hashed_password, role, is_active, full_name, phone, created_at, last_login_at FROM users WHERE id = :user_id'),
        {'user_id': user_id}
    ).fetchone()
    
    if not result:
        raise AuthenticationError("用户不存在")
    
    user_data = {
        'id': result[0],
        'username': result[1],
        'email': result[2],
        'hashed_password': result[3],
        'role': result[4],
        'is_active': result[5],
        'full_name': result[6],
        'phone': result[7],
        'created_at': result[8],
        'last_login_at': result[9]
    }
    
    if not user_data['is_active']:
        raise AuthenticationError("用户账户已被禁用")
    
    return user_data


def get_current_active_user(
    current_user: dict = Depends(get_current_user_dict),
) -> dict:
    """获取当前活跃用户"""
    if not current_user["is_active"]:
        raise AuthenticationError("用户账户已被禁用")
    
    return current_user


def require_role(required_role: UserRole):
    """要求特定角色的依赖工厂"""
    def role_checker(current_user: dict = Depends(get_current_active_user)) -> dict:
        if current_user["role"] != required_role.value and current_user["role"] != UserRole.ADMIN.value:
            raise AuthorizationError(f"需要{required_role.value}角色权限")
        return current_user
    
    return role_checker


def require_admin(current_user: dict = Depends(get_current_active_user)) -> dict:
    """要求管理员权限"""
    if current_user["role"] != "admin":
        raise AuthorizationError("需要管理员权限")
    return current_user


def require_trader_or_admin(current_user: dict = Depends(get_current_active_user)) -> dict:
    """要求交易员或管理员权限"""
    if current_user["role"] not in ["trader", "admin"]:
        raise AuthorizationError("需要交易员或管理员权限")
    return current_user


def get_optional_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> Optional[dict]:
    """获取可选的当前用户（用于公开接口）"""
    try:
        from sqlalchemy import text
        
        # 尝试从Authorization头获取token
        authorization = request.headers.get("Authorization")
        if not authorization or not authorization.startswith("Bearer "):
            return None
        
        token = authorization.split(" ")[1]
        
        # 解码JWT token
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        user_id: int = payload.get("sub")
        if user_id is None:
            return None
        
        # 查询用户
        result = db.execute(
            text('SELECT id, username, email, role, is_active, full_name, phone FROM users WHERE id = :user_id AND is_active = true'),
            {'user_id': user_id}
        ).fetchone()
        
        if result:
            return {
                'id': result[0],
                'username': result[1],
                'email': result[2],
                'role': result[3],
                'is_active': result[4],
                'full_name': result[5],
                'phone': result[6]
            }
        
        return None
        
    except (JWTError, Exception):
        return None


class PaginationParams:
    """分页参数"""
    def __init__(self, page: int = 1, page_size: int = 20):
        self.page = max(1, page)
        self.page_size = min(100, max(1, page_size))  # 限制最大页面大小
        self.offset = (self.page - 1) * self.page_size


def get_pagination_params(page: int = 1, page_size: int = 20) -> PaginationParams:
    """获取分页参数依赖"""
    return PaginationParams(page=page, page_size=page_size)


class SortParams:
    """排序参数"""
    def __init__(self, sort_by: str = "id", sort_order: str = "desc"):
        self.sort_by = sort_by
        self.sort_order = sort_order.lower()
        if self.sort_order not in ["asc", "desc"]:
            self.sort_order = "desc"


def get_sort_params(sort_by: str = "id", sort_order: str = "desc") -> SortParams:
    """获取排序参数依赖"""
    return SortParams(sort_by=sort_by, sort_order=sort_order)


def get_request_info(request: Request) -> dict:
    """获取请求信息依赖"""
    return {
        "method": request.method,
        "url": str(request.url),
        "client_ip": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get("user-agent", "unknown"),
        "request_id": getattr(request.state, "request_id", "unknown"),
    }


# 缓存相关依赖
def get_cache_key(prefix: str, *args) -> str:
    """生成缓存键"""
    key_parts = [prefix] + [str(arg) for arg in args]
    return ":".join(key_parts)


async def get_cached_data(
    cache_key: str,
    redis_client: redis.Redis = Depends(get_redis),
) -> Optional[str]:
    """获取缓存数据"""
    try:
        return redis_client.get(cache_key)
    except Exception:
        return None


async def set_cached_data(
    cache_key: str,
    data: str,
    expire_seconds: int = 3600,
    redis_client: redis.Redis = Depends(get_redis),
) -> bool:
    """设置缓存数据"""
    try:
        return redis_client.setex(cache_key, expire_seconds, data)
    except Exception:
        return False