"""
Pydantic模型定义
"""
from .auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    RefreshTokenRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
    ChangePasswordRequest,
    EmailVerificationRequest,
    UserProfile,
    SessionInfo,
    LogoutRequest,
)
from .user import (
    UserCreate,
    UserUpdate,
    UserAdminUpdate,
    UserResponse,
    UserListResponse,
    UserStatsResponse,
    UserSearchRequest,
    BatchUserOperation,
    UserPreferences,
)
from .market import (
    InstrumentInfo,
    QuoteData,
    KlineData,
    KlineRequest,
    QuoteSubscription,
    MarketDataFilter,
    TradingTimeInfo,
    MarketStatus,
    ConnectionStatus,
    MarketDataStats,
)

__all__ = [
    # 认证相关
    "LoginRequest",
    "RegisterRequest", 
    "TokenResponse",
    "RefreshTokenRequest",
    "PasswordResetRequest",
    "PasswordResetConfirm",
    "ChangePasswordRequest",
    "EmailVerificationRequest",
    "UserProfile",
    "SessionInfo",
    "LogoutRequest",
    # 用户管理相关
    "UserCreate",
    "UserUpdate",
    "UserAdminUpdate",
    "UserResponse",
    "UserListResponse",
    "UserStatsResponse",
    "UserSearchRequest",
    "BatchUserOperation",
    "UserPreferences",
    # 市场数据相关
    "InstrumentInfo",
    "QuoteData",
    "KlineData",
    "KlineRequest",
    "QuoteSubscription",
    "MarketDataFilter",
    "TradingTimeInfo",
    "MarketStatus",
    "ConnectionStatus",
    "MarketDataStats",
]