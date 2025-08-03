"""
通知管理Schema
"""
from typing import Optional, Dict, List, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum

class NotificationType(str, Enum):
    """通知类型"""
    TRADE = "trade"
    RISK = "risk"
    SYSTEM = "system"
    MARKET = "market"
    ACCOUNT = "account"
    SECURITY = "security"

class NotificationChannel(str, Enum):
    """通知渠道"""
    IN_APP = "in_app"
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WEBHOOK = "webhook"

class NotificationPriority(str, Enum):
    """通知优先级"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class NotificationStatus(str, Enum):
    """通知状态"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    CANCELLED = "cancelled"

# ==================== 通知模板 ====================

class NotificationTemplateBase(BaseModel):
    """通知模板基础模型"""
    name: str = Field(..., description="模板名称")
    code: str = Field(..., description="模板代码")
    type: NotificationType = Field(..., description="通知类型")
    title_template: str = Field(..., description="标题模板")
    content_template: str = Field(..., description="内容模板")
    channels: List[NotificationChannel] = Field(..., description="支持的通知渠道")
    variables: Optional[Dict[str, Any]] = Field(default_factory=dict, description="模板变量定义")
    default_priority: NotificationPriority = Field(default=NotificationPriority.NORMAL, description="默认优先级")
    is_active: bool = Field(default=True, description="是否激活")

class NotificationTemplateCreate(NotificationTemplateBase):
    """创建通知模板"""
    pass

class NotificationTemplateUpdate(BaseModel):
    """更新通知模板"""
    name: Optional[str] = None
    title_template: Optional[str] = None
    content_template: Optional[str] = None
    channels: Optional[List[NotificationChannel]] = None
    variables: Optional[Dict[str, Any]] = None
    default_priority: Optional[NotificationPriority] = None
    is_active: Optional[bool] = None

class NotificationTemplateResponse(NotificationTemplateBase):
    """通知模板响应"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

# ==================== 通知消息 ====================

class NotificationBase(BaseModel):
    """通知消息基础模型"""
    type: NotificationType = Field(..., description="通知类型")
    title: str = Field(..., description="通知标题")
    content: str = Field(..., description="通知内容")
    channel: NotificationChannel = Field(..., description="通知渠道")
    priority: NotificationPriority = Field(default=NotificationPriority.NORMAL, description="优先级")
    recipient: Optional[str] = Field(None, description="接收者")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="元数据")
    expires_at: Optional[datetime] = Field(None, description="过期时间")

class NotificationCreate(NotificationBase):
    """创建通知消息"""
    user_id: int = Field(..., description="用户ID")
    template_id: Optional[int] = Field(None, description="模板ID")
    variables: Optional[Dict[str, Any]] = Field(default_factory=dict, description="模板变量值")

class NotificationUpdate(BaseModel):
    """更新通知消息"""
    status: Optional[NotificationStatus] = None
    read_at: Optional[datetime] = None

class NotificationResponse(NotificationBase):
    """通知消息响应"""
    id: int
    user_id: int
    template_id: Optional[int]
    status: NotificationStatus
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    read_at: Optional[datetime]
    error_message: Optional[str]
    retry_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class NotificationBatchCreate(BaseModel):
    """批量创建通知"""
    user_ids: List[int] = Field(..., description="用户ID列表")
    template_code: str = Field(..., description="模板代码")
    variables: Optional[Dict[str, Any]] = Field(default_factory=dict, description="模板变量")
    channels: List[NotificationChannel] = Field(..., description="通知渠道")
    priority: NotificationPriority = Field(default=NotificationPriority.NORMAL, description="优先级")
    scheduled_at: Optional[datetime] = Field(None, description="计划发送时间")

class NotificationBatchResponse(BaseModel):
    """批量通知响应"""
    total_count: int = Field(..., description="总数量")
    success_count: int = Field(..., description="成功数量")
    failed_count: int = Field(..., description="失败数量")
    notification_ids: List[int] = Field(..., description="通知ID列表")

# ==================== 通知偏好 ====================

class NotificationPreferenceBase(BaseModel):
    """通知偏好基础模型"""
    enabled: bool = Field(default=True, description="是否启用通知")
    quiet_hours_enabled: bool = Field(default=False, description="是否启用免打扰时间")
    quiet_hours_start: str = Field(default="22:00", description="免打扰开始时间")
    quiet_hours_end: str = Field(default="08:00", description="免打扰结束时间")
    email_enabled: bool = Field(default=True, description="邮件通知启用")
    sms_enabled: bool = Field(default=False, description="短信通知启用")
    push_enabled: bool = Field(default=True, description="推送通知启用")
    in_app_enabled: bool = Field(default=True, description="站内信启用")
    trade_notifications: Optional[Dict[str, bool]] = Field(default_factory=dict, description="交易通知偏好")
    risk_notifications: Optional[Dict[str, bool]] = Field(default_factory=dict, description="风险通知偏好")
    system_notifications: Optional[Dict[str, bool]] = Field(default_factory=dict, description="系统通知偏好")
    market_notifications: Optional[Dict[str, bool]] = Field(default_factory=dict, description="市场通知偏好")
    account_notifications: Optional[Dict[str, bool]] = Field(default_factory=dict, description="账户通知偏好")
    security_notifications: Optional[Dict[str, bool]] = Field(default_factory=dict, description="安全通知偏好")
    max_notifications_per_hour: int = Field(default=10, description="每小时最大通知数")
    digest_enabled: bool = Field(default=False, description="是否启用摘要通知")
    digest_frequency: str = Field(default="daily", description="摘要频率")
    digest_time: str = Field(default="09:00", description="摘要发送时间")

    @validator('quiet_hours_start', 'quiet_hours_end', 'digest_time')
    def validate_time_format(cls, v):
        """验证时间格式"""
        if v and not v.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$'):
            raise ValueError('时间格式必须为 HH:MM')
        return v

class NotificationPreferenceUpdate(NotificationPreferenceBase):
    """更新通知偏好"""
    pass

class NotificationPreferenceResponse(NotificationPreferenceBase):
    """通知偏好响应"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

# ==================== 通知规则 ====================

class NotificationRuleBase(BaseModel):
    """通知规则基础模型"""
    name: str = Field(..., description="规则名称")
    description: Optional[str] = Field(None, description="规则描述")
    event_type: str = Field(..., description="事件类型")
    conditions: Dict[str, Any] = Field(..., description="触发条件")
    template_code: Optional[str] = Field(None, description="模板代码")
    channels: List[NotificationChannel] = Field(..., description="通知渠道")
    priority: NotificationPriority = Field(default=NotificationPriority.NORMAL, description="优先级")
    rate_limit: Optional[int] = Field(None, description="频率限制（分钟）")
    max_per_day: Optional[int] = Field(None, description="每日最大次数")
    is_active: bool = Field(default=True, description="是否激活")

class NotificationRuleCreate(NotificationRuleBase):
    """创建通知规则"""
    pass

class NotificationRuleUpdate(BaseModel):
    """更新通知规则"""
    name: Optional[str] = None
    description: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None
    template_code: Optional[str] = None
    channels: Optional[List[NotificationChannel]] = None
    priority: Optional[NotificationPriority] = None
    rate_limit: Optional[int] = None
    max_per_day: Optional[int] = None
    is_active: Optional[bool] = None

class NotificationRuleResponse(NotificationRuleBase):
    """通知规则响应"""
    id: int
    user_id: int
    trigger_count: int
    last_triggered_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

# ==================== 通知统计 ====================

class NotificationStats(BaseModel):
    """通知统计"""
    total_notifications: int = Field(..., description="总通知数")
    unread_notifications: int = Field(..., description="未读通知数")
    notifications_by_type: Dict[str, int] = Field(..., description="按类型统计")
    notifications_by_channel: Dict[str, int] = Field(..., description="按渠道统计")
    notifications_by_status: Dict[str, int] = Field(..., description="按状态统计")
    recent_notifications: List[NotificationResponse] = Field(..., description="最近通知")

class NotificationDigestResponse(BaseModel):
    """通知摘要响应"""
    id: int
    user_id: int
    digest_type: str
    period_start: datetime
    period_end: datetime
    total_notifications: int
    unread_notifications: int
    notification_summary: Dict[str, Any]
    is_sent: bool
    sent_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        orm_mode = True

# ==================== 请求模型 ====================

class NotificationMarkReadRequest(BaseModel):
    """标记已读请求"""
    notification_ids: List[int] = Field(..., description="通知ID列表")

class NotificationBatchDeleteRequest(BaseModel):
    """批量删除请求"""
    notification_ids: List[int] = Field(..., description="通知ID列表")
    delete_type: str = Field(default="soft", description="删除类型: soft/hard")

class NotificationTestRequest(BaseModel):
    """测试通知请求"""
    template_code: str = Field(..., description="模板代码")
    channel: NotificationChannel = Field(..., description="通知渠道")
    variables: Optional[Dict[str, Any]] = Field(default_factory=dict, description="模板变量")
    recipient: Optional[str] = Field(None, description="接收者")

class NotificationSearchRequest(BaseModel):
    """通知搜索请求"""
    keyword: Optional[str] = Field(None, description="关键词")
    type: Optional[NotificationType] = Field(None, description="通知类型")
    channel: Optional[NotificationChannel] = Field(None, description="通知渠道")
    status: Optional[NotificationStatus] = Field(None, description="通知状态")
    priority: Optional[NotificationPriority] = Field(None, description="优先级")
    date_from: Optional[datetime] = Field(None, description="开始日期")
    date_to: Optional[datetime] = Field(None, description="结束日期")
    page: int = Field(default=1, description="页码")
    page_size: int = Field(default=20, description="每页数量")

class NotificationSearchResponse(BaseModel):
    """通知搜索响应"""
    notifications: List[NotificationResponse] = Field(..., description="通知列表")
    total_count: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    total_pages: int = Field(..., description="总页数")

# ==================== 通知设置 ====================

class NotificationChannelConfig(BaseModel):
    """通知渠道配置"""
    channel: NotificationChannel = Field(..., description="通知渠道")
    enabled: bool = Field(default=True, description="是否启用")
    config: Dict[str, Any] = Field(default_factory=dict, description="渠道配置")

class NotificationSystemConfig(BaseModel):
    """通知系统配置"""
    channels: List[NotificationChannelConfig] = Field(..., description="渠道配置")
    default_retry_count: int = Field(default=3, description="默认重试次数")
    retry_intervals: List[int] = Field(default=[60, 300, 900], description="重试间隔（秒）")
    cleanup_days: int = Field(default=30, description="清理天数")
    rate_limit_enabled: bool = Field(default=True, description="是否启用频率限制")
    batch_size: int = Field(default=100, description="批处理大小")

# ==================== 导出模型 ====================

class NotificationExportRequest(BaseModel):
    """通知导出请求"""
    export_type: str = Field(default="notifications", description="导出类型")
    filters: Optional[NotificationSearchRequest] = Field(None, description="过滤条件")
    format: str = Field(default="csv", description="导出格式")
    include_content: bool = Field(default=True, description="是否包含内容")

class NotificationExportResponse(BaseModel):
    """通知导出响应"""
    export_id: str = Field(..., description="导出ID")
    status: str = Field(..., description="导出状态")
    download_url: Optional[str] = Field(None, description="下载链接")
    file_size: Optional[int] = Field(None, description="文件大小")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    created_at: datetime = Field(..., description="创建时间")