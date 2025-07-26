"""
用户管理相关的Pydantic模型
"""
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime

from ..models.enums import UserRole


class UserBase(BaseModel):
    """用户基础模型"""
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    phone: Optional[str] = None
    
    @validator('username')
    def validate_username(cls, v):
        if not v or len(v.strip()) < 3:
            raise ValueError('用户名至少需要3个字符')
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('用户名只能包含字母、数字、下划线和连字符')
        return v.strip().lower()
    
    @validator('phone')
    def validate_phone(cls, v):
        if v and not v.isdigit():
            raise ValueError('手机号只能包含数字')
        if v and len(v) != 11:
            raise ValueError('手机号必须是11位数字')
        return v


class UserCreate(UserBase):
    """创建用户模型"""
    password: str
    role: UserRole = UserRole.TRADER
    
    @validator('password')
    def validate_password(cls, v):
        if not v or len(v) < 6:
            raise ValueError('密码至少需要6个字符')
        
        # 检查密码强度
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        
        if not (has_upper and has_lower and has_digit):
            raise ValueError('密码必须包含大写字母、小写字母和数字')
        
        return v


class UserUpdate(BaseModel):
    """更新用户模型"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    
    @validator('phone')
    def validate_phone(cls, v):
        if v and not v.isdigit():
            raise ValueError('手机号只能包含数字')
        if v and len(v) != 11:
            raise ValueError('手机号必须是11位数字')
        return v


class UserAdminUpdate(UserUpdate):
    """管理员更新用户模型"""
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None


class UserResponse(BaseModel):
    """用户响应模型"""
    id: int
    username: str
    email: str
    full_name: Optional[str]
    phone: Optional[str]
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: Optional[datetime]
    last_login_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """用户列表响应模型"""
    id: int
    username: str
    email: str
    full_name: Optional[str]
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class UserStatsResponse(BaseModel):
    """用户统计响应模型"""
    total_users: int
    active_users: int
    verified_users: int
    admin_users: int
    trader_users: int
    viewer_users: int
    new_users_today: int
    new_users_this_week: int
    new_users_this_month: int


class UserSearchRequest(BaseModel):
    """用户搜索请求模型"""
    keyword: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None


class BatchUserOperation(BaseModel):
    """批量用户操作模型"""
    user_ids: List[int]
    operation: str  # activate, deactivate, delete, verify
    
    @validator('user_ids')
    def validate_user_ids(cls, v):
        if not v:
            raise ValueError('用户ID列表不能为空')
        if len(v) > 100:
            raise ValueError('批量操作最多支持100个用户')
        return v
    
    @validator('operation')
    def validate_operation(cls, v):
        allowed_operations = ['activate', 'deactivate', 'delete', 'verify']
        if v not in allowed_operations:
            raise ValueError(f'操作类型必须是: {", ".join(allowed_operations)}')
        return v


class UserActivityLog(BaseModel):
    """用户活动日志模型"""
    id: int
    user_id: int
    action: str
    description: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class PasswordPolicy(BaseModel):
    """密码策略模型"""
    min_length: int = 6
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_digits: bool = True
    require_special_chars: bool = False
    max_age_days: Optional[int] = None
    history_count: Optional[int] = None


class UserPreferences(BaseModel):
    """用户偏好设置模型"""
    language: str = "zh-CN"
    timezone: str = "Asia/Shanghai"
    theme: str = "light"
    notifications_email: bool = True
    notifications_sms: bool = False
    notifications_push: bool = True
    
    @validator('language')
    def validate_language(cls, v):
        allowed_languages = ['zh-CN', 'en-US']
        if v not in allowed_languages:
            raise ValueError(f'语言必须是: {", ".join(allowed_languages)}')
        return v
    
    @validator('theme')
    def validate_theme(cls, v):
        allowed_themes = ['light', 'dark', 'auto']
        if v not in allowed_themes:
            raise ValueError(f'主题必须是: {", ".join(allowed_themes)}')
        return v