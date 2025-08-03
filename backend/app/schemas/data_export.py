"""
数据导出相关的Pydantic模式
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class ExportFormat(str, Enum):
    """导出格式枚举"""
    CSV = "csv"
    EXCEL = "excel"
    JSON = "json"
    PDF = "pdf"


class ExportType(str, Enum):
    """导出类型枚举"""
    ORDERS = "orders"
    POSITIONS = "positions"
    TRANSACTIONS = "transactions"
    STRATEGIES = "strategies"
    BACKTESTS = "backtests"
    RISK_REPORTS = "risk_reports"
    SYSTEM_LOGS = "system_logs"
    USER_DATA = "user_data"
    FULL_BACKUP = "full_backup"


class ExportStatus(str, Enum):
    """导出状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DataExportRequest(BaseModel):
    """数据导出请求"""
    export_type: ExportType = Field(..., description="导出类型")
    format: ExportFormat = Field(..., description="导出格式")
    start_date: Optional[datetime] = Field(None, description="开始日期")
    end_date: Optional[datetime] = Field(None, description="结束日期")
    filters: Optional[Dict[str, Any]] = Field(None, description="筛选条件")
    include_fields: Optional[List[str]] = Field(None, description="包含字段")
    exclude_fields: Optional[List[str]] = Field(None, description="排除字段")
    compress: bool = Field(False, description="是否压缩")
    password_protect: bool = Field(False, description="是否密码保护")
    password: Optional[str] = Field(None, description="保护密码")


class DataExportTask(BaseModel):
    """数据导出任务"""
    id: int
    user_id: int
    export_type: ExportType
    format: ExportFormat
    status: ExportStatus
    progress: int = Field(0, ge=0, le=100, description="进度百分比")
    file_path: Optional[str] = Field(None, description="文件路径")
    file_size: Optional[int] = Field(None, description="文件大小(字节)")
    download_url: Optional[str] = Field(None, description="下载链接")
    error_message: Optional[str] = Field(None, description="错误信息")
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    
    class Config:
        from_attributes = True


class DataExportTaskCreate(BaseModel):
    """创建数据导出任务"""
    export_type: ExportType
    format: ExportFormat
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    filters: Optional[Dict[str, Any]] = None
    include_fields: Optional[List[str]] = None
    exclude_fields: Optional[List[str]] = None
    compress: bool = False
    password_protect: bool = False
    password: Optional[str] = None


class DataExportTaskUpdate(BaseModel):
    """更新数据导出任务"""
    status: Optional[ExportStatus] = None
    progress: Optional[int] = Field(None, ge=0, le=100)
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    download_url: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class SystemBackupRequest(BaseModel):
    """系统备份请求"""
    include_user_data: bool = Field(True, description="包含用户数据")
    include_system_logs: bool = Field(False, description="包含系统日志")
    include_market_data: bool = Field(False, description="包含市场数据")
    compress: bool = Field(True, description="压缩备份文件")
    encrypt: bool = Field(True, description="加密备份文件")
    password: Optional[str] = Field(None, description="加密密码")


class SystemBackupInfo(BaseModel):
    """系统备份信息"""
    id: int
    backup_type: str
    file_path: str
    file_size: int
    created_at: datetime
    expires_at: Optional[datetime] = None
    checksum: str = Field(..., description="文件校验和")
    
    class Config:
        from_attributes = True


class LogLevel(str, Enum):
    """日志级别枚举"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class SystemLogQuery(BaseModel):
    """系统日志查询"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    level: Optional[LogLevel] = None
    module: Optional[str] = None
    user_id: Optional[int] = None
    message_contains: Optional[str] = None
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)


class SystemLogEntry(BaseModel):
    """系统日志条目"""
    id: int
    timestamp: datetime
    level: str
    module: str
    message: str
    user_id: Optional[int] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class SystemMetrics(BaseModel):
    """系统指标"""
    cpu_usage: float = Field(..., description="CPU使用率")
    memory_usage: float = Field(..., description="内存使用率")
    disk_usage: float = Field(..., description="磁盘使用率")
    active_connections: int = Field(..., description="活跃连接数")
    request_count: int = Field(..., description="请求总数")
    error_count: int = Field(..., description="错误总数")
    response_time_avg: float = Field(..., description="平均响应时间")
    timestamp: datetime


class PerformanceReport(BaseModel):
    """性能报告"""
    report_id: str
    generated_at: datetime
    time_range: Dict[str, datetime]
    metrics: SystemMetrics
    slow_queries: List[Dict[str, Any]]
    error_summary: Dict[str, int]
    recommendations: List[str]
    charts_data: Dict[str, Any]


class DataIntegrityCheck(BaseModel):
    """数据完整性检查"""
    check_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str
    total_tables: int
    checked_tables: int
    issues_found: int
    issues: List[Dict[str, Any]]
    recommendations: List[str]