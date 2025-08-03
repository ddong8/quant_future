"""
认证相关的Pydantic模型
"""
from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime


class LoginRequest(BaseModel):
    """登录请求模型"""
    username: str
    password: str
    
    @validator('username')
    def validate_username(cls, v):
        if not v or len(v.strip()) < 3:
            raise ValueError('用户名至少需要3个字符')
        return v.strip()
    
    @validator('password')
    def validate_password(cls, v):
        if not v or len(v) < 6:
            raise ValueError('密码至少需要6个字符')
        return v


class RegisterRequest(BaseModel):
    """注册请求模型"""
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    
    @validator('username')
    def validate_username(cls, v):
        if not v or len(v.strip()) < 3:
            raise ValueError('用户名至少需要3个字符')
        if not v.isalnum():
            raise ValueError('用户名只能包含字母和数字')
        return v.strip().lower()
    
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
    
    @validator('phone')
    def validate_phone(cls, v):
        if v and not v.isdigit():
            raise ValueError('手机号只能包含数字')
        return v


class TokenResponse(BaseModel):
    """令牌响应模型"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # 秒
    user_id: int
    username: str
    role: str


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求模型"""
    refresh_token: str


class PasswordResetRequest(BaseModel):
    """密码重置请求模型"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """密码重置确认模型"""
    token: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if not v or len(v) < 6:
            raise ValueError('密码至少需要6个字符')
        
        # 检查密码强度
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        
        if not (has_upper and has_lower and has_digit):
            raise ValueError('密码必须包含大写字母、小写字母和数字')
        
        return v


class ChangePasswordRequest(BaseModel):
    """修改密码请求模型"""
    current_password: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if not v or len(v) < 6:
            raise ValueError('密码至少需要6个字符')
        
        # 检查密码强度
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        
        if not (has_upper and has_lower and has_digit):
            raise ValueError('密码必须包含大写字母、小写字母和数字')
        
        return v


class EmailVerificationRequest(BaseModel):
    """邮箱验证请求模型"""
    token: str


class UserProfile(BaseModel):
    """用户资料模型"""
    id: int
    username: str
    email: str
    full_name: Optional[str]
    phone: Optional[str]
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login_at: Optional[datetime]
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class SessionInfo(BaseModel):
    """会话信息模型"""
    session_id: int
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime
    last_accessed_at: datetime
    expires_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True


class LogoutRequest(BaseModel):
    """登出请求模型"""
    all_sessions: bool = False  # 是否登出所有会话