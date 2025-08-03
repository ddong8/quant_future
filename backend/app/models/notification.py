"""
通知和消息管理数据模型
"""
import sqlalchemy as sa
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from ..core.database import Base

class NotificationType(PyEnum):
    """通知类型枚举"""
    TRADE = "trade"              # 交易通知
    RISK = "risk"                # 风险通知
    SYSTEM = "system"            # 系统通知
    MARKET = "market"            # 市场通知
    ACCOUNT = "account"          # 账户通知
    SECURITY = "security"        # 安全通知

class NotificationChannel(PyEnum):
    """通知渠道枚举"""
    IN_APP = "in_app"           # 站内信
    EMAIL = "email"             # 邮件
    SMS = "sms"                 # 短信
    PUSH = "push"               # 推送通知
    WEBHOOK = "webhook"         # Webhook

class NotificationPriority(PyEnum):
    """通知优先级枚举"""
    LOW = "low"                 # 低优先级
    NORMAL = "normal"           # 普通优先级
    HIGH = "high"               # 高优先级
    URGENT = "urgent"           # 紧急

class NotificationStatus(PyEnum):
    """通知状态枚举"""
    PENDING = "pending"         # 待发送
    SENT = "sent"               # 已发送
    DELIVERED = "delivered"     # 已送达
    READ = "read"               # 已读
    FAILED = "failed"           # 发送失败
    CANCELLED = "cancelled"     # 已取消

class NotificationTemplate(Base):
    """通知模板模型"""
    __tablename__ = "notification_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 基本信息
    name = Column(String(100), nullable=False, comment="模板名称")
    code = Column(String(50), nullable=False, unique=True, comment="模板代码")
    type = Column(Enum(NotificationType), nullable=False, comment="通知类型")
    
    # 模板内容
    title_template = Column(String(200), nullable=False, comment="标题模板")
    content_template = Column(Text, nullable=False, comment="内容模板")
    
    # 渠道配置
    channels = Column(JSON, nullable=False, comment="支持的通知渠道")
    
    # 模板配置
    variables = Column(JSON, comment="模板变量定义")
    default_priority = Column(Enum(NotificationPriority), default=NotificationPriority.NORMAL, comment="默认优先级")
    
    # 状态
    is_active = Column(Boolean, default=True, comment="是否激活")
    
    # 时间信息
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    notifications = relationship("Notification", back_populates="template")

class Notification(Base):
    """通知消息模型"""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 基本信息
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    template_id = Column(Integer, ForeignKey("notification_templates.id"), comment="模板ID")
    
    # 通知内容
    type = Column(Enum(NotificationType), nullable=False, comment="通知类型")
    title = Column(String(200), nullable=False, comment="通知标题")
    content = Column(Text, nullable=False, comment="通知内容")
    
    # 通知配置
    channel = Column(Enum(NotificationChannel), nullable=False, comment="通知渠道")
    priority = Column(Enum(NotificationPriority), default=NotificationPriority.NORMAL, comment="优先级")
    
    # 状态信息
    status = Column(Enum(NotificationStatus), default=NotificationStatus.PENDING, comment="通知状态")
    
    # 发送信息
    recipient = Column(String(200), comment="接收者（邮箱/手机号等）")
    sent_at = Column(DateTime, comment="发送时间")
    delivered_at = Column(DateTime, comment="送达时间")
    read_at = Column(DateTime, comment="阅读时间")
    
    # 失败信息
    error_message = Column(Text, comment="错误信息")
    retry_count = Column(Integer, default=0, comment="重试次数")
    max_retries = Column(Integer, default=3, comment="最大重试次数")
    
    # 元数据
    model_metadata = Column(JSON, comment="元数据")
    variables = Column(JSON, comment="模板变量值")
    
    # 过期时间
    expires_at = Column(DateTime, comment="过期时间")
    
    # 时间信息
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    user = relationship("User")
    template = relationship("NotificationTemplate", back_populates="notifications")
    
    # 索引
    __table_args__ = (
        sa.Index('ix_notifications_user_status', 'user_id', 'status'),
        sa.Index('ix_notifications_type_created', 'type', 'created_at'),
        sa.Index('ix_notifications_channel_status', 'channel', 'status'),
    )

class NotificationPreference(Base):
    """用户通知偏好模型"""
    __tablename__ = "notification_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, comment="用户ID")
    
    # 全局设置
    enabled = Column(Boolean, default=True, comment="是否启用通知")
    quiet_hours_enabled = Column(Boolean, default=False, comment="是否启用免打扰时间")
    quiet_hours_start = Column(String(5), default="22:00", comment="免打扰开始时间")
    quiet_hours_end = Column(String(5), default="08:00", comment="免打扰结束时间")
    
    # 渠道偏好
    email_enabled = Column(Boolean, default=True, comment="邮件通知启用")
    sms_enabled = Column(Boolean, default=False, comment="短信通知启用")
    push_enabled = Column(Boolean, default=True, comment="推送通知启用")
    in_app_enabled = Column(Boolean, default=True, comment="站内信启用")
    
    # 类型偏好
    trade_notifications = Column(JSON, comment="交易通知偏好")
    risk_notifications = Column(JSON, comment="风险通知偏好")
    system_notifications = Column(JSON, comment="系统通知偏好")
    market_notifications = Column(JSON, comment="市场通知偏好")
    account_notifications = Column(JSON, comment="账户通知偏好")
    security_notifications = Column(JSON, comment="安全通知偏好")
    
    # 频率控制
    max_notifications_per_hour = Column(Integer, default=10, comment="每小时最大通知数")
    digest_enabled = Column(Boolean, default=False, comment="是否启用摘要通知")
    digest_frequency = Column(String(20), default="daily", comment="摘要频率")
    digest_time = Column(String(5), default="09:00", comment="摘要发送时间")
    
    # 时间信息
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    user = relationship("User")

class NotificationRule(Base):
    """通知规则模型"""
    __tablename__ = "notification_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    
    # 规则信息
    name = Column(String(100), nullable=False, comment="规则名称")
    description = Column(Text, comment="规则描述")
    
    # 触发条件
    event_type = Column(String(50), nullable=False, comment="事件类型")
    conditions = Column(JSON, nullable=False, comment="触发条件")
    
    # 通知配置
    template_code = Column(String(50), comment="模板代码")
    channels = Column(JSON, nullable=False, comment="通知渠道")
    priority = Column(Enum(NotificationPriority), default=NotificationPriority.NORMAL, comment="优先级")
    
    # 频率控制
    rate_limit = Column(Integer, comment="频率限制（分钟）")
    max_per_day = Column(Integer, comment="每日最大次数")
    
    # 状态
    is_active = Column(Boolean, default=True, comment="是否激活")
    
    # 统计
    trigger_count = Column(Integer, default=0, comment="触发次数")
    last_triggered_at = Column(DateTime, comment="最后触发时间")
    
    # 时间信息
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    user = relationship("User")

class NotificationQueue(Base):
    """通知队列模型"""
    __tablename__ = "notification_queue"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 队列信息
    notification_id = Column(Integer, ForeignKey("notifications.id"), nullable=False, comment="通知ID")
    queue_name = Column(String(50), nullable=False, comment="队列名称")
    
    # 调度信息
    scheduled_at = Column(DateTime, nullable=False, comment="计划发送时间")
    priority = Column(Integer, default=0, comment="队列优先级")
    
    # 状态
    status = Column(String(20), default="queued", comment="队列状态")
    processed_at = Column(DateTime, comment="处理时间")
    
    # 重试信息
    retry_count = Column(Integer, default=0, comment="重试次数")
    next_retry_at = Column(DateTime, comment="下次重试时间")
    
    # 时间信息
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    notification = relationship("Notification")
    
    # 索引
    __table_args__ = (
        sa.Index('ix_notification_queue_scheduled', 'scheduled_at', 'status'),
        sa.Index('ix_notification_queue_priority', 'priority', 'created_at'),
    )

class NotificationLog(Base):
    """通知日志模型"""
    __tablename__ = "notification_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 关联信息
    notification_id = Column(Integer, ForeignKey("notifications.id"), nullable=False, comment="通知ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    
    # 日志信息
    action = Column(String(50), nullable=False, comment="操作类型")
    status = Column(String(20), nullable=False, comment="状态")
    message = Column(Text, comment="日志消息")
    
    # 渠道信息
    channel = Column(String(20), comment="通知渠道")
    provider = Column(String(50), comment="服务提供商")
    
    # 响应信息
    response_code = Column(String(20), comment="响应代码")
    response_message = Column(Text, comment="响应消息")
    response_data = Column(JSON, comment="响应数据")
    
    # 性能信息
    duration_ms = Column(Integer, comment="处理时长（毫秒）")
    
    # 时间信息
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    
    # 关系
    notification = relationship("Notification")
    user = relationship("User")
    
    # 索引
    __table_args__ = (
        sa.Index('ix_notification_logs_notification', 'notification_id'),
        sa.Index('ix_notification_logs_user_action', 'user_id', 'action'),
        sa.Index('ix_notification_logs_created', 'created_at'),
    )

class NotificationDigest(Base):
    """通知摘要模型"""
    __tablename__ = "notification_digests"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    
    # 摘要信息
    digest_type = Column(String(20), nullable=False, comment="摘要类型")
    period_start = Column(DateTime, nullable=False, comment="统计开始时间")
    period_end = Column(DateTime, nullable=False, comment="统计结束时间")
    
    # 统计数据
    total_notifications = Column(Integer, default=0, comment="总通知数")
    unread_notifications = Column(Integer, default=0, comment="未读通知数")
    notification_summary = Column(JSON, comment="通知摘要")
    
    # 发送状态
    is_sent = Column(Boolean, default=False, comment="是否已发送")
    sent_at = Column(DateTime, comment="发送时间")
    
    # 时间信息
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    user = relationship("User")
    
    # 索引
    __table_args__ = (
        sa.Index('ix_notification_digests_user_period', 'user_id', 'period_start', 'period_end'),
        sa.UniqueConstraint('user_id', 'digest_type', 'period_start', name='uq_user_digest_period'),
    )