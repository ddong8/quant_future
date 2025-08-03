"""
系统管理Schema
"""
from typing import Optional, Dict, List, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum

class ExportStatus(str, Enum):
    """导出状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ExportFormat(str, Enum):
    """导出格式"""
    CSV = "csv"
    EXCEL = "excel"
    JSON = "json"
    PDF = "pdf"
    XML = "xml"

class LogLevel(str, Enum):
    """日志级别"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class BackupType(str, Enum):
    """备份类型"""
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"

class BackupStatus(str, Enum):
    """备份状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

# ==================== 数据导出 ====================

class DataExportRequest(BaseModel):
    """数据导出请求"""
    task_name: str = Field(..., description="任务名称")
    export_type: str = Field(..., description="导出类型")
    export_format: ExportFormat = Field(..., description="导出格式")
    export_config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="导出配置")
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="过滤条件")
    date_range: Optional[Dict[str, str]] = Field(None, description="日期范围")

class DataExportTaskResponse(BaseModel):
    """数据导出任务响应"""
    id: int
    task_name: str
    task_id: str
    user_id: int
    export_type: str
    export_format: ExportFormat
    export_config: Optional[Dict[str, Any]]
    filters: Optional[Dict[str, Any]]
    date_range: Optional[Dict[str, str]]
    status: ExportStatus
    progress: int
    file_path: Optional[str]
    file_name: Optional[str]
    file_size: Optional[int]
    download_url: Optional[str]
    total_records: Optional[int]
    exported_records: Optional[int]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    expires_at: Optional[datetime]
    error_message: Optional[str]
    error_details: Optional[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class DataExportListResponse(BaseModel):
    """数据导出列表响应"""
    tasks: List[DataExportTaskResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int

# ==================== 系统备份 ====================

class SystemBackupRequest(BaseModel):
    """系统备份请求"""
    backup_name: str = Field(..., description="备份名称")
    backup_type: BackupType = Field(..., description="备份类型")
    backup_scope: Dict[str, Any] = Field(..., description="备份范围")

class SystemBackupResponse(BaseModel):
    """系统备份响应"""
    id: int
    backup_name: str
    backup_id: str
    backup_type: BackupType
    backup_scope: Dict[str, Any]
    status: BackupStatus
    progress: int
    file_path: Optional[str]
    file_size: Optional[int]
    compressed_size: Optional[int]
    total_tables: Optional[int]
    backed_up_tables: Optional[int]
    total_records: Optional[int]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    checksum: Optional[str]
    is_verified: bool
    error_message: Optional[str]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int]
    
    class Config:
        orm_mode = True

# ==================== 系统日志 ====================

class SystemLogQuery(BaseModel):
    """系统日志查询"""
    log_level: Optional[LogLevel] = Field(None, description="日志级别")
    logger_name: Optional[str] = Field(None, description="日志器名称")
    module: Optional[str] = Field(None, description="模块名称")
    user_id: Optional[int] = Field(None, description="用户ID")
    keyword: Optional[str] = Field(None, description="关键词")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=50, ge=1, le=1000, description="每页数量")

class SystemLogResponse(BaseModel):
    """系统日志响应"""
    id: int
    log_level: LogLevel
    logger_name: str
    module: Optional[str]
    message: str
    exception: Optional[str]
    stack_trace: Optional[str]
    user_id: Optional[int]
    session_id: Optional[str]
    request_id: Optional[str]
    method: Optional[str]
    url: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    duration_ms: Optional[int]
    memory_usage: Optional[int]
    extra_data: Optional[Dict[str, Any]]
    created_at: datetime
    
    class Config:
        orm_mode = True

class SystemLogListResponse(BaseModel):
    """系统日志列表响应"""
    logs: List[SystemLogResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int

class SystemLogStats(BaseModel):
    """系统日志统计"""
    total_logs: int
    logs_by_level: Dict[str, int]
    logs_by_module: Dict[str, int]
    error_rate: float
    recent_errors: List[SystemLogResponse]

# ==================== 系统指标 ====================

class SystemMetricQuery(BaseModel):
    """系统指标查询"""
    metric_name: Optional[str] = Field(None, description="指标名称")
    metric_type: Optional[str] = Field(None, description="指标类型")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    labels: Optional[Dict[str, str]] = Field(None, description="标签过滤")
    aggregation: Optional[str] = Field("avg", description="聚合方式")
    interval: Optional[str] = Field("1h", description="时间间隔")

class SystemMetricResponse(BaseModel):
    """系统指标响应"""
    id: int
    metric_name: str
    metric_type: str
    value: float
    unit: Optional[str]
    labels: Optional[Dict[str, Any]]
    dimensions: Optional[Dict[str, Any]]
    timestamp: datetime
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    
    class Config:
        orm_mode = True

class SystemMetricSeries(BaseModel):
    """系统指标时间序列"""
    metric_name: str
    metric_type: str
    unit: Optional[str]
    data_points: List[Dict[str, Any]]  # [{"timestamp": "...", "value": 123}]
    labels: Optional[Dict[str, str]]

# ==================== 系统告警 ====================

class SystemAlertResponse(BaseModel):
    """系统告警响应"""
    id: int
    alert_name: str
    alert_type: str
    severity: str
    title: str
    description: str
    trigger_condition: Optional[Dict[str, Any]]
    trigger_value: Optional[float]
    threshold: Optional[float]
    status: str
    is_acknowledged: bool
    acknowledged_by: Optional[int]
    acknowledged_at: Optional[datetime]
    is_resolved: bool
    resolved_by: Optional[int]
    resolved_at: Optional[datetime]
    resolution_notes: Optional[str]
    first_occurred_at: datetime
    last_occurred_at: datetime
    occurrence_count: int
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class SystemAlertAcknowledge(BaseModel):
    """系统告警确认"""
    alert_ids: List[int] = Field(..., description="告警ID列表")
    notes: Optional[str] = Field(None, description="确认备注")

class SystemAlertResolve(BaseModel):
    """系统告警解决"""
    alert_ids: List[int] = Field(..., description="告警ID列表")
    resolution_notes: str = Field(..., description="解决备注")

# ==================== 系统配置 ====================

class SystemConfigurationResponse(BaseModel):
    """系统配置响应"""
    id: int
    config_key: str
    config_name: str
    config_group: Optional[str]
    config_value: Optional[str]
    default_value: Optional[str]
    data_type: str
    description: Optional[str]
    validation_rules: Optional[Dict[str, Any]]
    is_active: bool
    is_readonly: bool
    requires_restart: bool
    version: int
    created_at: datetime
    updated_at: datetime
    updated_by: Optional[int]
    
    class Config:
        orm_mode = True

class SystemConfigurationUpdate(BaseModel):
    """系统配置更新"""
    config_value: str = Field(..., description="配置值")
    notes: Optional[str] = Field(None, description="更新备注")

# ==================== 系统维护 ====================

class SystemMaintenanceWindowRequest(BaseModel):
    """系统维护窗口请求"""
    title: str = Field(..., description="维护标题")
    description: Optional[str] = Field(None, description="维护描述")
    maintenance_type: str = Field(..., description="维护类型")
    scheduled_start: datetime = Field(..., description="计划开始时间")
    scheduled_end: datetime = Field(..., description="计划结束时间")
    affected_services: Optional[List[str]] = Field(default_factory=list, description="受影响的服务")
    impact_level: str = Field(default="medium", description="影响级别")
    notify_users: bool = Field(default=True, description="是否通知用户")

class SystemMaintenanceWindowResponse(BaseModel):
    """系统维护窗口响应"""
    id: int
    title: str
    description: Optional[str]
    maintenance_type: str
    scheduled_start: datetime
    scheduled_end: datetime
    actual_start: Optional[datetime]
    actual_end: Optional[datetime]
    status: str
    affected_services: Optional[List[str]]
    impact_level: Optional[str]
    notify_users: bool
    notification_sent: bool
    executed_by: Optional[int]
    execution_notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int]
    
    class Config:
        orm_mode = True

# ==================== 系统状态 ====================

class SystemHealthCheck(BaseModel):
    """系统健康检查"""
    overall_status: str = Field(..., description="总体状态")
    components: Dict[str, Dict[str, Any]] = Field(..., description="组件状态")
    timestamp: datetime = Field(..., description="检查时间")

class SystemPerformanceReport(BaseModel):
    """系统性能报告"""
    cpu_usage: float = Field(..., description="CPU使用率")
    memory_usage: float = Field(..., description="内存使用率")
    disk_usage: float = Field(..., description="磁盘使用率")
    network_io: Dict[str, float] = Field(..., description="网络IO")
    database_performance: Dict[str, Any] = Field(..., description="数据库性能")
    response_times: Dict[str, float] = Field(..., description="响应时间")
    error_rates: Dict[str, float] = Field(..., description="错误率")
    active_users: int = Field(..., description="活跃用户数")
    timestamp: datetime = Field(..., description="报告时间")

class SystemOptimizationSuggestion(BaseModel):
    """系统优化建议"""
    category: str = Field(..., description="建议分类")
    priority: str = Field(..., description="优先级")
    title: str = Field(..., description="建议标题")
    description: str = Field(..., description="建议描述")
    impact: str = Field(..., description="预期影响")
    effort: str = Field(..., description="实施难度")
    resources: List[str] = Field(default_factory=list, description="相关资源")

class SystemOptimizationReport(BaseModel):
    """系统优化报告"""
    report_id: str = Field(..., description="报告ID")
    generated_at: datetime = Field(..., description="生成时间")
    performance_score: float = Field(..., description="性能评分")
    suggestions: List[SystemOptimizationSuggestion] = Field(..., description="优化建议")
    metrics_summary: Dict[str, Any] = Field(..., description="指标摘要")

# ==================== 数据清理 ====================

class DataCleanupRequest(BaseModel):
    """数据清理请求"""
    cleanup_type: str = Field(..., description="清理类型")
    target_tables: List[str] = Field(..., description="目标表")
    retention_days: int = Field(..., ge=1, description="保留天数")
    dry_run: bool = Field(default=True, description="是否为试运行")
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="过滤条件")

class DataCleanupResponse(BaseModel):
    """数据清理响应"""
    cleanup_id: str = Field(..., description="清理ID")
    status: str = Field(..., description="清理状态")
    total_records: int = Field(..., description="总记录数")
    cleaned_records: int = Field(..., description="已清理记录数")
    freed_space: int = Field(..., description="释放空间（字节）")
    started_at: datetime = Field(..., description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    error_message: Optional[str] = Field(None, description="错误信息")

# ==================== 系统统计 ====================

class SystemStatistics(BaseModel):
    """系统统计"""
    users: Dict[str, int] = Field(..., description="用户统计")
    orders: Dict[str, int] = Field(..., description="订单统计")
    positions: Dict[str, int] = Field(..., description="持仓统计")
    transactions: Dict[str, int] = Field(..., description="交易统计")
    notifications: Dict[str, int] = Field(..., description="通知统计")
    system_resources: Dict[str, float] = Field(..., description="系统资源")
    database_stats: Dict[str, Any] = Field(..., description="数据库统计")
    generated_at: datetime = Field(..., description="生成时间")