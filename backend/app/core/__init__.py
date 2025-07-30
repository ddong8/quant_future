"""
核心配置和工具模块
"""
from .config import settings
from .database import Base, engine, SessionLocal
from .database_manager import db_manager
from .exceptions import (
    BaseCustomException,
    BusinessLogicError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ConflictError,
    SystemError,
    ExternalServiceError,
    RateLimitError,
)
from .response import (
    SuccessResponse,
    ErrorResponse,
    PaginatedResponse,
    success_response,
    error_response,
    paginated_response,
    created_response,
    updated_response,
    deleted_response,
)
from .dependencies import (
    get_db,
    get_current_user,
    get_current_active_user,
    require_admin,
    require_trader_or_admin,
    get_pagination_params,
    PaginationParams,
)

__all__ = [
    # 配置
    "settings",
    # 数据库
    "Base",
    "engine", 
    "SessionLocal",
    "db_manager",
    # 异常
    "BaseCustomException",
    "BusinessLogicError",
    "ValidationError",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ConflictError",
    "SystemError",
    "ExternalServiceError",
    "RateLimitError",
    # 响应
    "SuccessResponse",
    "ErrorResponse",
    "PaginatedResponse",
    "success_response",
    "error_response",
    "paginated_response",
    "created_response",
    "updated_response",
    "deleted_response",
    # 依赖
    "get_db",
    "get_current_user",
    "get_current_active_user",
    "require_admin",
    "require_trader_or_admin",
    "get_pagination_params",
    "PaginationParams",
]