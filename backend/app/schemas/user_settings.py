"""
用户设置数据模型Schema
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, validator, EmailStr

class UserProfileBase(BaseModel):
    """用户个人资料基础模型"""
    full_name: Optional[str] = Field(None, description="全名")
    phone: Optional[str] = Field(None, description="手机号")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    avatar: Optional[str] = Field(None, description="头像URL")
    timezone: Optional[str] = Field(default="Asia/Shanghai", description="时区")
    language: Optional[str] = Field(default="zh-CN", description="语言")
    date_format: Optional[str] = Field(default="YYYY-MM-DD", description="日期格式")
    currency_display: Optional[str] = Field(default="USD", description="显示货币")

class UserProfileUpdate(UserProfileBase):
    """更新用户个人资料"""
    pass

class UserProfileResponse(UserProfileBase):
    """用户个人资料响应"""
    id: int
    username: str
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime]
    
    class Config:
        orm_mode = True

class UserSettingsBase(BaseModel):
    """用户设置基础模型"""
    theme: Optional[str] = Field(default="light", description="主题")
    sidebar_collapsed: Optional[bool] = Field(default=False, description="侧边栏折叠")
    auto_refresh: Optional[bool] = Field(default=True, description="自动刷新")
    refresh_interval: Optional[int] = Field(default=30, description="刷新间隔(秒)")
    default_chart_period: Optional[str] = Field(default="1d", description="默认图表周期")
    show_advanced_features: Optional[bool] = Field(default=False, description="显示高级功能")

class UserSettingsUpdate(UserSettingsBase):
    """更新用户设置"""
    pass

class UserSettingsResponse(UserSettingsBase):
    """用户设置响应"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class SecuritySettingsBase(BaseModel):
    """安全设置基础模型"""
    two_factor_enabled: Optional[bool] = Field(default=False, description="双因子认证启用")
    login_notifications: Optional[bool] = Field(default=True, description="登录通知")
    session_timeout: Optional[int] = Field(default=3600, description="会话超时(秒)")
    ip_whitelist: Optional[List[str]] = Field(default_factory=list, description="IP白名单")
    allowed_devices: Optional[int] = Field(default=5, description="允许设备数量")

class SecuritySettingsUpdate(SecuritySettingsBase):
    """更新安全设置"""
    pass

class SecuritySettingsResponse(SecuritySettingsBase):
    """安全设置响应"""
    id: int
    user_id: int
    two_factor_secret: Optional[str] = Field(None, description="双因子认证密钥")
    backup_codes: Optional[List[str]] = Field(default_factory=list, description="备用码")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class PasswordChangeRequest(BaseModel):
    """修改密码请求"""
    current_password: str = Field(..., description="当前密码")
    new_password: str = Field(..., min_length=8, description="新密码")
    
    @validator('new_password')
    def validate_password_strength(cls, v):
        """验证密码强度"""
        if len(v) < 8:
            raise ValueError('密码长度至少8位')
        
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in v)
        
        if not all([has_upper, has_lower, has_digit, has_special]):
            raise ValueError('密码必须包含大小写字母、数字和特殊字符')
        
        return v

class TwoFactorToggleRequest(BaseModel):
    """双因子认证切换请求"""
    enabled: bool = Field(..., description="是否启用")
    verification_code: Optional[str] = Field(None, description="验证码")

class TwoFactorQRCodeResponse(BaseModel):
    """双因子认证二维码响应"""
    qr_code_url: str = Field(..., description="二维码URL")
    secret_key: str = Field(..., description="密钥")
    backup_codes: List[str] = Field(..., description="备用码")

class NotificationSettingsBase(BaseModel):
    """通知设置基础模型"""
    email_enabled: Optional[bool] = Field(default=True, description="邮件通知启用")
    sms_enabled: Optional[bool] = Field(default=False, description="短信通知启用")
    push_enabled: Optional[bool] = Field(default=True, description="推送通知启用")
    trade_notifications: Optional[List[str]] = Field(
        default_factory=lambda: ["order_filled", "position_closed"],
        description="交易通知类型"
    )
    risk_notifications: Optional[List[str]] = Field(
        default_factory=lambda: ["margin_call", "large_loss"],
        description="风险通知类型"
    )
    system_notifications: Optional[List[str]] = Field(
        default_factory=lambda: ["maintenance", "security_alert"],
        description="系统通知类型"
    )
    notification_hours: Optional[Dict[str, Any]] = Field(
        default_factory=lambda: {"start": "09:00", "end": "21:00"},
        description="通知时间段"
    )

class NotificationSettingsUpdate(NotificationSettingsBase):
    """更新通知设置"""
    pass

class NotificationSettingsResponse(NotificationSettingsBase):
    """通知设置响应"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class LoginDeviceBase(BaseModel):
    """登录设备基础模型"""
    device_name: str = Field(..., description="设备名称")
    device_type: str = Field(..., description="设备类型")
    browser: Optional[str] = Field(None, description="浏览器")
    os: Optional[str] = Field(None, description="操作系统")
    ip_address: str = Field(..., description="IP地址")
    location: Optional[str] = Field(None, description="位置")
    user_agent: Optional[str] = Field(None, description="用户代理")

class LoginDeviceResponse(LoginDeviceBase):
    """登录设备响应"""
    id: int
    user_id: int
    is_current: bool = Field(..., description="是否当前设备")
    last_login_at: datetime = Field(..., description="最后登录时间")
    created_at: datetime
    
    class Config:
        orm_mode = True

class UserActivityLog(BaseModel):
    """用户活动日志"""
    id: int
    user_id: int
    action: str = Field(..., description="操作类型")
    description: str = Field(..., description="操作描述")
    ip_address: Optional[str] = Field(None, description="IP地址")
    user_agent: Optional[str] = Field(None, description="用户代理")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="元数据")
    created_at: datetime
    
    class Config:
        orm_mode = True

class UserDataExportRequest(BaseModel):
    """用户数据导出请求"""
    export_type: str = Field(default="all", description="导出类型")
    include_transactions: Optional[bool] = Field(default=True, description="包含交易记录")
    include_orders: Optional[bool] = Field(default=True, description="包含订单记录")
    include_positions: Optional[bool] = Field(default=True, description="包含持仓记录")
    date_range: Optional[Dict[str, str]] = Field(None, description="日期范围")

class UserDataExportResponse(BaseModel):
    """用户数据导出响应"""
    export_id: str = Field(..., description="导出ID")
    status: str = Field(..., description="导出状态")
    download_url: Optional[str] = Field(None, description="下载链接")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    file_size: Optional[int] = Field(None, description="文件大小")
    created_at: datetime

class AccountDeletionRequest(BaseModel):
    """账户删除请求"""
    password: str = Field(..., description="密码确认")
    reason: Optional[str] = Field(None, description="删除原因")
    feedback: Optional[str] = Field(None, description="反馈意见")

class UserPreferences(BaseModel):
    """用户偏好设置"""
    dashboard_layout: Optional[Dict[str, Any]] = Field(default_factory=dict, description="仪表板布局")
    favorite_symbols: Optional[List[str]] = Field(default_factory=list, description="收藏标的")
    watchlists: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="自选列表")
    quick_actions: Optional[List[str]] = Field(default_factory=list, description="快捷操作")
    chart_settings: Optional[Dict[str, Any]] = Field(default_factory=dict, description="图表设置")

class APIKeyBase(BaseModel):
    """API密钥基础模型"""
    name: str = Field(..., description="密钥名称")
    permissions: List[str] = Field(..., description="权限列表")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    ip_whitelist: Optional[List[str]] = Field(default_factory=list, description="IP白名单")

class APIKeyCreate(APIKeyBase):
    """创建API密钥"""
    pass

class APIKeyResponse(APIKeyBase):
    """API密钥响应"""
    id: int
    user_id: int
    key_id: str = Field(..., description="密钥ID")
    key_secret: Optional[str] = Field(None, description="密钥(仅创建时返回)")
    is_active: bool = Field(..., description="是否激活")
    last_used_at: Optional[datetime] = Field(None, description="最后使用时间")
    created_at: datetime
    
    class Config:
        orm_mode = True

class UserSettingsValidation(BaseModel):
    """用户设置验证"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    
    @validator('errors', 'warnings', pre=True)
    def ensure_list(cls, v):
        if v is None:
            return []
        return v if isinstance(v, list) else [v]