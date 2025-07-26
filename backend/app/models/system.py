"""
系统监控和通知相关数据模型
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON, Boolean
from sqlalchemy.sql import func

from ..core.database import Base
from .enums import NotificationType


class SystemLog(Base):
    """系统日志模型"""
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 日志基本信息
    level = Column(String(20), nullable=False, index=True)  # DEBUG/INFO/WARNING/ERROR/CRITICAL
    module = Column(String(100), nullable=False, index=True)  # 模块名称
    function = Column(String(100))  # 函数名称
    message = Column(Text, nullable=False)
    
    # 关联信息
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), index=True)
    
    # 额外数据
    extra_data = Column(JSON)  # 额外的日志数据
    
    # 请求信息
    request_id = Column(String(100), index=True)  # 请求ID
    ip_address = Column(String(45))  # IP地址
    user_agent = Column(Text)  # 用户代理
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<SystemLog(id={self.id}, level='{self.level}', module='{self.module}')>"


class SystemMetric(Base):
    """系统指标模型"""
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 指标信息
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(20))  # percent/bytes/count/ms等
    
    # 服务信息
    service_name = Column(String(50), nullable=False, index=True)  # api/worker/scheduler等
    instance_id = Column(String(100))  # 实例ID
    
    # 标签
    tags = Column(JSON)  # 指标标签
    
    # 时间戳
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    def __repr__(self):
        return f"<SystemMetric(id={self.id}, name='{self.metric_name}', value={self.metric_value})>"


class Notification(Base):
    """通知模型"""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 通知基本信息
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    notification_type = Column(String(20), nullable=False)  # email/sms/webhook/in_app
    
    # 接收者信息
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    recipient = Column(String(200), nullable=False)  # 邮箱/手机号/webhook URL等
    
    # 关联信息
    related_type = Column(String(50))  # strategy/backtest/risk_event/system等
    related_id = Column(Integer)  # 关联对象ID
    
    # 发送状态
    is_sent = Column(Boolean, default=False)
    sent_at = Column(DateTime(timezone=True))
    delivery_status = Column(String(20))  # pending/sent/delivered/failed
    error_message = Column(Text)
    
    # 优先级
    priority = Column(String(20), default="normal")  # low/normal/high/urgent
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Notification(id={self.id}, type='{self.notification_type}', title='{self.title}')>"


class ScheduledTask(Base):
    """定时任务模型"""
    __tablename__ = "scheduled_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 任务基本信息
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    task_type = Column(String(50), nullable=False)  # report/cleanup/backup/sync等
    
    # 调度配置
    cron_expression = Column(String(100), nullable=False)  # Cron表达式
    timezone = Column(String(50), default="UTC")
    
    # 任务配置
    parameters = Column(JSON)  # 任务参数
    
    # 状态
    is_active = Column(Boolean, default=True)
    last_run_at = Column(DateTime(timezone=True))
    next_run_at = Column(DateTime(timezone=True))
    last_status = Column(String(20))  # success/failed/running
    last_error = Column(Text)
    
    # 统计
    total_runs = Column(Integer, default=0)
    success_runs = Column(Integer, default=0)
    failed_runs = Column(Integer, default=0)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<ScheduledTask(id={self.id}, name='{self.name}', type='{self.task_type}')>"