"""
日志管理相关的Pydantic模型
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class LogEntryBase(BaseModel):
    """日志条目基础模型"""
    level: str = Field(..., description="日志级别")
    message: str = Field(..., description="日志消息")
    logger: Optional[str] = Field(None, description="日志记录器")
    module: Optional[str] = Field(None, description="模块名称")
    function: Optional[str] = Field(None, description="函数名称")
    line_number: Optional[int] = Field(None, description="行号")
    user_id: Optional[int] = Field(None, description="用户ID")
    request_id: Optional[str] = Field(None, description="请求ID")
    extra_data: Optional[Dict[str, Any]] = Field(None, description="额外数据")


class LogEntryCreate(LogEntryBase):
    """创建日志条目"""
    pass


class LogEntry(LogEntryBase):
    """日志条目响应"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class LogQuery(BaseModel):
    """日志查询参数"""
    level: Optional[str] = Field(None, description="日志级别过滤")
    logger: Optional[str] = Field(None, description="日志记录器过滤")
    module: Optional[str] = Field(None, description="模块过滤")
    message: Optional[str] = Field(None, description="消息内容过滤")
    user_id: Optional[int] = Field(None, description="用户ID过滤")
    request_id: Optional[str] = Field(None, description="请求ID过滤")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")


class LogStatistics(BaseModel):
    """日志统计信息"""
    total_logs: int = Field(..., description="总日志数")
    level_counts: Dict[str, int] = Field(..., description="按级别统计")
    module_counts: Dict[str, int] = Field(..., description="按模块统计")
    user_counts: Dict[str, int] = Field(..., description="按用户统计")
    hourly_counts: Dict[str, int] = Field(..., description="按小时统计")
    error_rate: float = Field(..., description="错误率")
    start_time: datetime = Field(..., description="统计开始时间")
    end_time: datetime = Field(..., description="统计结束时间")


class ErrorPattern(BaseModel):
    """错误模式"""
    pattern: str = Field(..., description="错误模式")
    count: int = Field(..., description="出现次数")
    first_occurrence: str = Field(..., description="首次出现时间")
    last_occurrence: str = Field(..., description="最后出现时间")
    sample_message: str = Field(..., description="示例消息")
    affected_users_count: int = Field(..., description="影响用户数")
    unique_requests_count: int = Field(..., description="唯一请求数")
    frequency: float = Field(..., description="每小时频率")


class LogExportRequest(BaseModel):
    """日志导出请求"""
    query: LogQuery = Field(..., description="查询条件")
    format: str = Field("json", description="导出格式: json, csv")
    max_records: int = Field(10000, description="最大记录数")


class LogHealthStatus(BaseModel):
    """日志系统健康状态"""
    status: str = Field(..., description="状态: healthy, warning, error")
    recent_logs_count: int = Field(..., description="最近日志数量")
    recent_error_count: int = Field(..., description="最近错误数量")
    error_rate: float = Field(..., description="错误率")
    database_size: str = Field(..., description="数据库大小")
    oldest_log_date: Optional[str] = Field(None, description="最老日志日期")
    disk_free_gb: float = Field(..., description="磁盘剩余空间(GB)")
    log_retention_days: int = Field(..., description="日志保留天数")
    last_rotation: Optional[str] = Field(None, description="最后轮转时间")


class LogSearchRequest(BaseModel):
    """日志搜索请求"""
    search_text: str = Field(..., description="搜索文本")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    limit: int = Field(100, description="结果限制")


class LogTrendRequest(BaseModel):
    """日志趋势请求"""
    days: int = Field(7, description="天数")
    interval: str = Field("hour", description="间隔: hour, day")


class LogTrendData(BaseModel):
    """日志趋势数据点"""
    time: str = Field(..., description="时间")
    count: int = Field(..., description="数量")


class LogTrendResponse(BaseModel):
    """日志趋势响应"""
    overall_trend: List[LogTrendData] = Field(..., description="总体趋势")
    level_trends: Dict[str, List[LogTrendData]] = Field(..., description="按级别趋势")
    start_time: str = Field(..., description="开始时间")
    end_time: str = Field(..., description="结束时间")
    interval: str = Field(..., description="时间间隔")


class LogRotationConfig(BaseModel):
    """日志轮转配置"""
    retention_days: int = Field(30, description="保留天数")
    rotation_size_mb: int = Field(100, description="轮转大小(MB)")
    auto_rotation: bool = Field(True, description="自动轮转")
    compression: bool = Field(True, description="压缩归档")


class LogRotationStatus(BaseModel):
    """日志轮转状态"""
    last_rotation: Optional[datetime] = Field(None, description="最后轮转时间")
    next_rotation: Optional[datetime] = Field(None, description="下次轮转时间")
    rotated_files: List[str] = Field(..., description="已轮转文件")
    total_size_mb: float = Field(..., description="总大小(MB)")
    archived_size_mb: float = Field(..., description="归档大小(MB)")


class LogAnalysisRequest(BaseModel):
    """日志分析请求"""
    analysis_type: str = Field(..., description="分析类型: error_patterns, performance, user_activity")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    parameters: Optional[Dict[str, Any]] = Field(None, description="分析参数")


class LogAnalysisResult(BaseModel):
    """日志分析结果"""
    analysis_type: str = Field(..., description="分析类型")
    results: Dict[str, Any] = Field(..., description="分析结果")
    summary: str = Field(..., description="结果摘要")
    recommendations: List[str] = Field(..., description="建议")
    generated_at: datetime = Field(..., description="生成时间")


class LogAlert(BaseModel):
    """日志告警"""
    id: int = Field(..., description="告警ID")
    rule_name: str = Field(..., description="规则名称")
    condition: str = Field(..., description="触发条件")
    message: str = Field(..., description="告警消息")
    severity: str = Field(..., description="严重程度")
    triggered_at: datetime = Field(..., description="触发时间")
    resolved_at: Optional[datetime] = Field(None, description="解决时间")
    status: str = Field(..., description="状态: active, resolved")


class LogAlertRule(BaseModel):
    """日志告警规则"""
    name: str = Field(..., description="规则名称")
    description: Optional[str] = Field(None, description="规则描述")
    condition: str = Field(..., description="触发条件")
    severity: str = Field(..., description="严重程度")
    enabled: bool = Field(True, description="是否启用")
    notification_channels: List[str] = Field(..., description="通知渠道")
    cooldown_minutes: int = Field(60, description="冷却时间(分钟)")


class LogMetrics(BaseModel):
    """日志指标"""
    timestamp: datetime = Field(..., description="时间戳")
    logs_per_second: float = Field(..., description="每秒日志数")
    error_rate: float = Field(..., description="错误率")
    response_time_avg: float = Field(..., description="平均响应时间")
    active_users: int = Field(..., description="活跃用户数")
    top_errors: List[str] = Field(..., description="主要错误")


class LogDashboardData(BaseModel):
    """日志仪表板数据"""
    current_metrics: LogMetrics = Field(..., description="当前指标")
    statistics: LogStatistics = Field(..., description="统计信息")
    error_patterns: List[ErrorPattern] = Field(..., description="错误模式")
    health_status: LogHealthStatus = Field(..., description="健康状态")
    recent_alerts: List[LogAlert] = Field(..., description="最近告警")
    trends: LogTrendResponse = Field(..., description="趋势数据")


class LogConfigUpdate(BaseModel):
    """日志配置更新"""
    log_level: Optional[str] = Field(None, description="日志级别")
    retention_days: Optional[int] = Field(None, description="保留天数")
    rotation_size_mb: Optional[int] = Field(None, description="轮转大小")
    enable_compression: Optional[bool] = Field(None, description="启用压缩")
    enable_auto_rotation: Optional[bool] = Field(None, description="启用自动轮转")


class LogQueryResponse(BaseModel):
    """日志查询响应"""
    logs: List[LogEntry] = Field(..., description="日志列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="页码")
    page_size: int = Field(..., description="页大小")
    has_more: bool = Field(..., description="是否有更多")


class LogBatchOperation(BaseModel):
    """日志批量操作"""
    operation: str = Field(..., description="操作类型: delete, export, archive")
    log_ids: List[int] = Field(..., description="日志ID列表")
    parameters: Optional[Dict[str, Any]] = Field(None, description="操作参数")


class LogBatchResult(BaseModel):
    """日志批量操作结果"""
    operation: str = Field(..., description="操作类型")
    success_count: int = Field(..., description="成功数量")
    failed_count: int = Field(..., description="失败数量")
    errors: List[str] = Field(..., description="错误信息")
    result_data: Optional[Dict[str, Any]] = Field(None, description="结果数据")