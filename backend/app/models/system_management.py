"""
系统管理和数据导出数据模型
"""
import sqlalchemy as sa
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Enum, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from ..core.database import Base

class ExportStatus(PyEnum):
    """导出状态枚举"""
    PENDING = "pending"         # 待处理
    PROCESSING = "processing"   # 处理中
    COMPLETED = "completed"     # 已完成
    FAILED = "failed"          # 失败
    CANCELLED = "cancelled"     # 已取消

class ExportFormat(PyEnum):
    """导出格式枚举"""
    CSV = "csv"
    EXCEL = "excel"
    JSON = "json"
    PDF = "pdf"
    XML = "xml"

class LogLevel(PyEnum):
    """日志级别枚举"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class BackupType(PyEnum):
    """备份类型枚举"""
    FULL = "full"              # 全量备份
    INCREMENTAL = "incremental" # 增量备份
    DIFFERENTIAL = "differential" # 差异备份

class BackupStatus(PyEnum):
    """备份状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class DataExportTask(Base):
    """数据导出任务模型"""
    __tablename__ = "data_export_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 基本信息
    task_name = Column(String(200), nullable=False, comment="任务名称")
    task_id = Column(String(50), nullable=False, unique=True, comment="任务ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    
    # 导出配置
    export_type = Column(String(50), nullable=False, comment="导出类型")
    export_format = Column(Enum(ExportFormat), nullable=False, comment="导出格式")
    export_config = Column(JSON, comment="导出配置")
    
    # 过滤条件
    filters = Column(JSON, comment="过滤条件")
    date_range = Column(JSON, comment="日期范围")
    
    # 状态信息
    status = Column(Enum(ExportStatus), default=ExportStatus.PENDING, comment="导出状态")
    progress = Column(Integer, default=0, comment="进度百分比")
    
    # 结果信息
    file_path = Column(String(500), comment="文件路径")
    file_name = Column(String(200), comment="文件名")
    file_size = Column(Integer, comment="文件大小（字节）")
    download_url = Column(String(500), comment="下载链接")
    
    # 统计信息
    total_records = Column(Integer, comment="总记录数")
    exported_records = Column(Integer, comment="已导出记录数")
    
    # 时间信息
    started_at = Column(DateTime, comment="开始时间")
    completed_at = Column(DateTime, comment="完成时间")
    expires_at = Column(DateTime, comment="过期时间")
    
    # 错误信息
    error_message = Column(Text, comment="错误信息")
    error_details = Column(JSON, comment="错误详情")
    
    # 元数据
    model_metadata = Column(JSON, comment="元数据")
    
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    user = relationship("User")
    
    # 索引
    __table_args__ = (
        sa.Index('ix_data_export_tasks_user_status', 'user_id', 'status'),
        sa.Index('ix_data_export_tasks_created', 'created_at'),
        sa.Index('ix_data_export_tasks_expires', 'expires_at'),
    )

class SystemBackup(Base):
    """系统备份模型"""
    __tablename__ = "system_backups"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 基本信息
    backup_name = Column(String(200), nullable=False, comment="备份名称")
    backup_id = Column(String(50), nullable=False, unique=True, comment="备份ID")
    
    # 备份配置
    backup_type = Column(Enum(BackupType), nullable=False, comment="备份类型")
    backup_scope = Column(JSON, nullable=False, comment="备份范围")
    
    # 状态信息
    status = Column(Enum(BackupStatus), default=BackupStatus.PENDING, comment="备份状态")
    progress = Column(Integer, default=0, comment="进度百分比")
    
    # 文件信息
    file_path = Column(String(500), comment="备份文件路径")
    file_size = Column(Integer, comment="文件大小（字节）")
    compressed_size = Column(Integer, comment="压缩后大小（字节）")
    
    # 统计信息
    total_tables = Column(Integer, comment="总表数")
    backed_up_tables = Column(Integer, comment="已备份表数")
    total_records = Column(Integer, comment="总记录数")
    
    # 时间信息
    started_at = Column(DateTime, comment="开始时间")
    completed_at = Column(DateTime, comment="完成时间")
    
    # 验证信息
    checksum = Column(String(64), comment="校验和")
    is_verified = Column(Boolean, default=False, comment="是否已验证")
    
    # 错误信息
    error_message = Column(Text, comment="错误信息")
    
    # 元数据
    model_metadata = Column(JSON, comment="元数据")
    
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建者")
    
    # 关系
    creator = relationship("User")
    
    # 索引
    __table_args__ = (
        sa.Index('ix_system_backups_status', 'status'),
        sa.Index('ix_system_backups_created', 'created_at'),
        sa.Index('ix_system_backups_type', 'backup_type'),
    )

class SystemLog(Base):
    """系统日志模型"""
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 基本信息
    log_level = Column(Enum(LogLevel), nullable=False, comment="日志级别")
    logger_name = Column(String(100), nullable=False, comment="日志器名称")
    module = Column(String(100), comment="模块名称")
    
    # 日志内容
    message = Column(Text, nullable=False, comment="日志消息")
    exception = Column(Text, comment="异常信息")
    stack_trace = Column(Text, comment="堆栈跟踪")
    
    # 上下文信息
    user_id = Column(Integer, ForeignKey("users.id"), comment="用户ID")
    session_id = Column(String(100), comment="会话ID")
    request_id = Column(String(100), comment="请求ID")
    
    # 请求信息
    method = Column(String(10), comment="HTTP方法")
    url = Column(String(500), comment="请求URL")
    ip_address = Column(String(45), comment="IP地址")
    user_agent = Column(Text, comment="用户代理")
    
    # 性能信息
    duration_ms = Column(Integer, comment="执行时长（毫秒）")
    memory_usage = Column(Integer, comment="内存使用（字节）")
    
    # 额外数据
    extra_data = Column(JSON, comment="额外数据")
    
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    
    # 关系
    user = relationship("User")
    
    # 索引
    __table_args__ = (
        sa.Index('ix_system_logs_level_created', 'log_level', 'created_at'),
        sa.Index('ix_system_logs_module_created', 'module', 'created_at'),
        sa.Index('ix_system_logs_user_created', 'user_id', 'created_at'),
        sa.Index('ix_system_logs_request', 'request_id'),
    )

class SystemMetric(Base):
    """系统指标模型"""
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 基本信息
    metric_name = Column(String(100), nullable=False, comment="指标名称")
    metric_type = Column(String(50), nullable=False, comment="指标类型")
    
    # 指标值
    value = Column(Float, nullable=False, comment="指标值")
    unit = Column(String(20), comment="单位")
    
    # 标签和维度
    labels = Column(JSON, comment="标签")
    dimensions = Column(JSON, comment="维度")
    
    # 时间信息
    timestamp = Column(DateTime, nullable=False, comment="时间戳")
    
    # 元数据
    model_metadata = Column(JSON, comment="元数据")
    
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    
    # 索引
    __table_args__ = (
        sa.Index('ix_system_metrics_name_timestamp', 'metric_name', 'timestamp'),
        sa.Index('ix_system_metrics_type_timestamp', 'metric_type', 'timestamp'),
        sa.Index('ix_system_metrics_timestamp', 'timestamp'),
    )

class SystemAlert(Base):
    """系统告警模型"""
    __tablename__ = "system_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 基本信息
    alert_name = Column(String(100), nullable=False, comment="告警名称")
    alert_type = Column(String(50), nullable=False, comment="告警类型")
    severity = Column(String(20), nullable=False, comment="严重程度")
    
    # 告警内容
    title = Column(String(200), nullable=False, comment="告警标题")
    description = Column(Text, nullable=False, comment="告警描述")
    
    # 触发条件
    trigger_condition = Column(JSON, comment="触发条件")
    trigger_value = Column(Float, comment="触发值")
    threshold = Column(Float, comment="阈值")
    
    # 状态信息
    status = Column(String(20), default="active", comment="告警状态")
    is_acknowledged = Column(Boolean, default=False, comment="是否已确认")
    acknowledged_by = Column(Integer, ForeignKey("users.id"), comment="确认人")
    acknowledged_at = Column(DateTime, comment="确认时间")
    
    # 解决信息
    is_resolved = Column(Boolean, default=False, comment="是否已解决")
    resolved_by = Column(Integer, ForeignKey("users.id"), comment="解决人")
    resolved_at = Column(DateTime, comment="解决时间")
    resolution_notes = Column(Text, comment="解决备注")
    
    # 时间信息
    first_occurred_at = Column(DateTime, nullable=False, comment="首次发生时间")
    last_occurred_at = Column(DateTime, nullable=False, comment="最后发生时间")
    occurrence_count = Column(Integer, default=1, comment="发生次数")
    
    # 元数据
    model_metadata = Column(JSON, comment="元数据")
    
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    acknowledger = relationship("User", foreign_keys=[acknowledged_by])
    resolver = relationship("User", foreign_keys=[resolved_by])
    
    # 索引
    __table_args__ = (
        sa.Index('ix_system_alerts_status_severity', 'status', 'severity'),
        sa.Index('ix_system_alerts_type_created', 'alert_type', 'created_at'),
        sa.Index('ix_system_alerts_occurred', 'last_occurred_at'),
    )

class SystemConfiguration(Base):
    """系统配置模型"""
    __tablename__ = "system_configurations"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 基本信息
    config_key = Column(String(100), nullable=False, unique=True, comment="配置键")
    config_name = Column(String(200), nullable=False, comment="配置名称")
    config_group = Column(String(50), comment="配置分组")
    
    # 配置值
    config_value = Column(Text, comment="配置值")
    default_value = Column(Text, comment="默认值")
    data_type = Column(String(20), default="string", comment="数据类型")
    
    # 配置描述
    description = Column(Text, comment="配置描述")
    validation_rules = Column(JSON, comment="验证规则")
    
    # 状态信息
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_readonly = Column(Boolean, default=False, comment="是否只读")
    requires_restart = Column(Boolean, default=False, comment="是否需要重启")
    
    # 版本信息
    version = Column(Integer, default=1, comment="版本号")
    
    # 时间信息
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    updated_by = Column(Integer, ForeignKey("users.id"), comment="更新人")
    
    # 关系
    updater = relationship("User")
    
    # 索引
    __table_args__ = (
        sa.Index('ix_system_configurations_group', 'config_group'),
        sa.Index('ix_system_configurations_active', 'is_active'),
    )

class SystemMaintenanceWindow(Base):
    """系统维护窗口模型"""
    __tablename__ = "system_maintenance_windows"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 基本信息
    title = Column(String(200), nullable=False, comment="维护标题")
    description = Column(Text, comment="维护描述")
    maintenance_type = Column(String(50), nullable=False, comment="维护类型")
    
    # 时间安排
    scheduled_start = Column(DateTime, nullable=False, comment="计划开始时间")
    scheduled_end = Column(DateTime, nullable=False, comment="计划结束时间")
    actual_start = Column(DateTime, comment="实际开始时间")
    actual_end = Column(DateTime, comment="实际结束时间")
    
    # 状态信息
    status = Column(String(20), default="scheduled", comment="维护状态")
    
    # 影响范围
    affected_services = Column(JSON, comment="受影响的服务")
    impact_level = Column(String(20), comment="影响级别")
    
    # 通知设置
    notify_users = Column(Boolean, default=True, comment="是否通知用户")
    notification_sent = Column(Boolean, default=False, comment="是否已发送通知")
    
    # 执行信息
    executed_by = Column(Integer, ForeignKey("users.id"), comment="执行人")
    execution_notes = Column(Text, comment="执行备注")
    
    # 时间信息
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人")
    
    # 关系
    creator = relationship("User", foreign_keys=[created_by])
    executor = relationship("User", foreign_keys=[executed_by])
    
    # 索引
    __table_args__ = (
        sa.Index('ix_system_maintenance_windows_status', 'status'),
        sa.Index('ix_system_maintenance_windows_scheduled', 'scheduled_start', 'scheduled_end'),
    )