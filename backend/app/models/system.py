"""
系统监控和通知相关数据模型
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON, Boolean
from sqlalchemy.orm import relationship
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

class SystemMetrics(Base):
    """系统性能指标表"""
    __tablename__ = "system_metrics_detailed"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True, comment="时间戳")
    
    # CPU指标
    cpu_percent = Column(Float, comment="CPU使用率")
    cpu_count = Column(Integer, comment="CPU核心数")
    cpu_freq_current = Column(Float, comment="当前CPU频率")
    
    # 内存指标
    memory_total = Column(Integer, comment="总内存")
    memory_available = Column(Integer, comment="可用内存")
    memory_percent = Column(Float, comment="内存使用率")
    memory_used = Column(Integer, comment="已用内存")
    
    # 磁盘指标
    disk_total = Column(Integer, comment="总磁盘空间")
    disk_used = Column(Integer, comment="已用磁盘空间")
    disk_percent = Column(Float, comment="磁盘使用率")
    
    # 网络指标
    network_bytes_sent = Column(Integer, comment="网络发送字节数")
    network_bytes_recv = Column(Integer, comment="网络接收字节数")
    
    # 数据库指标
    db_active_connections = Column(Integer, comment="数据库活跃连接数")
    db_total_connections = Column(Integer, comment="数据库总连接数")
    db_cache_hit_ratio = Column(Float, comment="数据库缓存命中率")
    
    # 应用指标
    app_user_count = Column(Integer, comment="应用用户数量")
    app_active_users = Column(Integer, comment="活跃用户数量")
    app_running_strategies = Column(Integer, comment="运行中的策略数量")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class HealthCheck(Base):
    """健康检查表"""
    __tablename__ = "health_checks"
    
    id = Column(Integer, primary_key=True, index=True)
    check_name = Column(String(100), nullable=False, index=True, comment="检查名称")
    status = Column(String(20), nullable=False, comment="状态: healthy, warning, critical")
    message = Column(Text, comment="检查消息")
    response_time = Column(Float, comment="响应时间(毫秒)")
    value = Column(Float, comment="检查值")
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True, comment="检查时间")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AlertRule(Base):
    """告警规则表"""
    __tablename__ = "alert_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, comment="规则名称")
    description = Column(Text, comment="规则描述")
    metric_name = Column(String(100), nullable=False, comment="监控指标名称")
    operator = Column(String(10), nullable=False, comment="比较操作符: gt, lt, eq, gte, lte")
    threshold = Column(Float, nullable=False, comment="阈值")
    severity = Column(String(20), nullable=False, comment="严重程度: info, warning, error, critical")
    enabled = Column(Boolean, default=True, comment="是否启用")
    notification_channels = Column(JSON, comment="通知渠道列表")
    silence_duration = Column(Integer, default=60, comment="静默时间(分钟)")
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建者ID")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    creator = relationship("User", back_populates="alert_rules", foreign_keys=[created_by])
    history = relationship("AlertHistory", foreign_keys="AlertHistory.rule_id", cascade="all, delete-orphan")


class AlertHistory(Base):
    """告警历史表"""
    __tablename__ = "alert_history"
    
    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, ForeignKey("alert_rules.id"), nullable=False, comment="规则ID")
    metric_name = Column(String(100), nullable=False, comment="指标名称")
    current_value = Column(Float, nullable=False, comment="当前值")
    threshold = Column(Float, nullable=False, comment="阈值")
    operator = Column(String(10), nullable=False, comment="操作符")
    severity = Column(String(20), nullable=False, comment="严重程度")
    message = Column(Text, comment="告警消息")
    status = Column(String(20), default='active', comment="状态: active, resolved")
    resolved_at = Column(DateTime(timezone=True), comment="解决时间")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # 关系
    rule = relationship("AlertRule", foreign_keys=[rule_id])


class MonitoringConfig(Base):
    """监控配置表"""
    __tablename__ = "monitoring_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    config_key = Column(String(100), nullable=False, unique=True, comment="配置键")
    config_value = Column(JSON, comment="配置值")
    description = Column(Text, comment="配置描述")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class NotificationChannel(Base):
    """通知渠道表"""
    __tablename__ = "notification_channels"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="渠道名称")
    channel_type = Column(String(50), nullable=False, comment="渠道类型: email, sms, wechat, webhook")
    config = Column(JSON, comment="渠道配置")
    enabled = Column(Boolean, default=True, comment="是否启用")
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建者ID")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class SystemEvent(Base):
    """系统事件表"""
    __tablename__ = "system_events"
    
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(50), nullable=False, comment="事件类型")
    event_name = Column(String(100), nullable=False, comment="事件名称")
    description = Column(Text, comment="事件描述")
    severity = Column(String(20), comment="严重程度")
    source = Column(String(100), comment="事件源")
    user_id = Column(Integer, ForeignKey("users.id"), comment="相关用户ID")
    event_model_metadata = Column(JSON, comment="事件元数据")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)