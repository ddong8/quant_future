"""
监控系统相关的Pydantic模型
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class SystemMetricsBase(BaseModel):
    """系统指标基础模型"""
    cpu_percent: float = Field(..., description="CPU使用率")
    memory_percent: float = Field(..., description="内存使用率")
    disk_percent: float = Field(..., description="磁盘使用率")
    network_bytes_sent: int = Field(..., description="网络发送字节数")
    network_bytes_recv: int = Field(..., description="网络接收字节数")
    db_active_connections: int = Field(..., description="数据库活跃连接数")
    db_cache_hit_ratio: float = Field(..., description="数据库缓存命中率")
    app_user_count: int = Field(..., description="应用用户数量")
    app_running_strategies: int = Field(..., description="运行中的策略数量")


class SystemMetricsCreate(SystemMetricsBase):
    """创建系统指标"""
    timestamp: datetime = Field(..., description="时间戳")


class SystemMetricsResponse(SystemMetricsBase):
    """系统指标响应"""
    id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True


class HealthCheckBase(BaseModel):
    """健康检查基础模型"""
    check_name: str = Field(..., description="检查名称")
    status: str = Field(..., description="状态: healthy, warning, critical")
    message: str = Field(..., description="检查消息")
    response_time: Optional[float] = Field(None, description="响应时间(毫秒)")
    value: Optional[float] = Field(None, description="检查值")


class HealthCheckCreate(HealthCheckBase):
    """创建健康检查"""
    timestamp: datetime = Field(..., description="时间戳")


class HealthCheckResponse(HealthCheckBase):
    """健康检查响应"""
    id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True


class AlertRuleBase(BaseModel):
    """告警规则基础模型"""
    name: str = Field(..., description="规则名称")
    description: Optional[str] = Field(None, description="规则描述")
    metric_name: str = Field(..., description="监控指标名称")
    operator: str = Field(..., description="比较操作符: gt, lt, eq, gte, lte")
    threshold: float = Field(..., description="阈值")
    severity: str = Field(..., description="严重程度: info, warning, error, critical")
    enabled: bool = Field(True, description="是否启用")
    notification_channels: List[str] = Field(default=[], description="通知渠道")
    silence_duration: int = Field(60, description="静默时间(分钟)")


class AlertRuleCreate(AlertRuleBase):
    """创建告警规则"""
    pass


class AlertRuleUpdate(BaseModel):
    """更新告警规则"""
    name: Optional[str] = Field(None, description="规则名称")
    description: Optional[str] = Field(None, description="规则描述")
    metric_name: Optional[str] = Field(None, description="监控指标名称")
    operator: Optional[str] = Field(None, description="比较操作符")
    threshold: Optional[float] = Field(None, description="阈值")
    severity: Optional[str] = Field(None, description="严重程度")
    enabled: Optional[bool] = Field(None, description="是否启用")
    notification_channels: Optional[List[str]] = Field(None, description="通知渠道")
    silence_duration: Optional[int] = Field(None, description="静默时间(分钟)")


class AlertRuleResponse(AlertRuleBase):
    """告警规则响应"""
    id: int
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class AlertHistoryBase(BaseModel):
    """告警历史基础模型"""
    rule_id: int = Field(..., description="规则ID")
    metric_name: str = Field(..., description="指标名称")
    current_value: float = Field(..., description="当前值")
    threshold: float = Field(..., description="阈值")
    operator: str = Field(..., description="操作符")
    severity: str = Field(..., description="严重程度")
    message: str = Field(..., description="告警消息")


class AlertHistoryCreate(AlertHistoryBase):
    """创建告警历史"""
    created_at: datetime = Field(..., description="创建时间")


class AlertHistoryResponse(AlertHistoryBase):
    """告警历史响应"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class SystemStatusResponse(BaseModel):
    """系统状态响应"""
    overall_status: str = Field(..., description="总体状态")
    last_update: Optional[datetime] = Field(None, description="最后更新时间")
    system_metrics: Dict[str, Any] = Field(..., description="系统指标")
    health_checks: Dict[str, int] = Field(..., description="健康检查统计")
    monitoring_status: str = Field(..., description="监控状态")


class MetricsQueryParams(BaseModel):
    """指标查询参数"""
    metric_names: List[str] = Field(..., description="指标名称列表")
    start_time: datetime = Field(..., description="开始时间")
    end_time: datetime = Field(..., description="结束时间")
    aggregation: Optional[str] = Field("avg", description="聚合方式")
    interval: Optional[str] = Field("1h", description="时间间隔")


class MetricsDataPoint(BaseModel):
    """指标数据点"""
    timestamp: datetime = Field(..., description="时间戳")
    value: float = Field(..., description="值")


class AggregatedMetricsResponse(BaseModel):
    """聚合指标响应"""
    metric_name: str = Field(..., description="指标名称")
    aggregation: str = Field(..., description="聚合方式")
    interval: str = Field(..., description="时间间隔")
    data_points: List[Dict[str, Any]] = Field(..., description="数据点")


class HealthSummaryResponse(BaseModel):
    """健康检查摘要响应"""
    summary: List[Dict[str, Any]] = Field(..., description="检查摘要")
    status_counts: Dict[str, int] = Field(..., description="状态统计")
    total_checks: int = Field(..., description="总检查数")
    last_update: Optional[datetime] = Field(None, description="最后更新时间")


class MonitoringDashboardResponse(BaseModel):
    """监控仪表板响应"""
    system_status: Dict[str, Any] = Field(..., description="系统状态")
    metrics_trend: List[Dict[str, Any]] = Field(..., description="指标趋势")
    health_summary: Dict[str, Any] = Field(..., description="健康检查摘要")
    recent_alerts: List[Dict[str, Any]] = Field(..., description="最近告警")
    statistics: Dict[str, Any] = Field(..., description="统计信息")


class NotificationChannelConfig(BaseModel):
    """通知渠道配置"""
    channel_type: str = Field(..., description="渠道类型: email, sms, wechat, webhook")
    enabled: bool = Field(True, description="是否启用")
    config: Dict[str, Any] = Field(..., description="渠道配置")


class NotificationTest(BaseModel):
    """通知测试"""
    channel_type: str = Field(..., description="渠道类型")
    recipients: List[str] = Field(..., description="接收者列表")
    test_message: str = Field("这是一条测试消息", description="测试消息")


class MonitoringConfig(BaseModel):
    """监控配置"""
    collection_interval: int = Field(30, description="收集间隔(秒)")
    health_check_interval: int = Field(60, description="健康检查间隔(秒)")
    alert_check_interval: int = Field(60, description="告警检查间隔(秒)")
    metrics_retention_days: int = Field(30, description="指标保留天数")
    health_check_retention_days: int = Field(7, description="健康检查保留天数")
    alert_history_retention_days: int = Field(90, description="告警历史保留天数")
    notification_channels: List[NotificationChannelConfig] = Field(default=[], description="通知渠道配置")


class SystemResourceUsage(BaseModel):
    """系统资源使用情况"""
    cpu: Dict[str, Any] = Field(..., description="CPU信息")
    memory: Dict[str, Any] = Field(..., description="内存信息")
    disk: Dict[str, Any] = Field(..., description="磁盘信息")
    network: Dict[str, Any] = Field(..., description="网络信息")
    processes: Dict[str, Any] = Field(..., description="进程信息")


class DatabaseMetrics(BaseModel):
    """数据库指标"""
    active_connections: int = Field(..., description="活跃连接数")
    total_connections: int = Field(..., description="总连接数")
    max_connections: int = Field(..., description="最大连接数")
    cache_hit_ratio: float = Field(..., description="缓存命中率")
    transactions_per_second: float = Field(..., description="每秒事务数")
    query_duration_avg: float = Field(..., description="平均查询时间")
    slow_queries: int = Field(..., description="慢查询数量")


class ApplicationMetrics(BaseModel):
    """应用指标"""
    user_count: int = Field(..., description="用户数量")
    active_users: int = Field(..., description="活跃用户数")
    strategy_count: int = Field(..., description="策略数量")
    running_strategies: int = Field(..., description="运行中策略数")
    today_orders: int = Field(..., description="今日订单数")
    today_trades: int = Field(..., description="今日成交数")
    trade_success_rate: float = Field(..., description="交易成功率")
    api_requests_per_minute: float = Field(..., description="每分钟API请求数")
    error_rate: float = Field(..., description="错误率")


class PerformanceMetrics(BaseModel):
    """性能指标"""
    response_time_avg: float = Field(..., description="平均响应时间")
    response_time_p95: float = Field(..., description="95%响应时间")
    response_time_p99: float = Field(..., description="99%响应时间")
    throughput: float = Field(..., description="吞吐量")
    error_count: int = Field(..., description="错误数量")
    concurrent_users: int = Field(..., description="并发用户数")


class MonitoringAlert(BaseModel):
    """监控告警"""
    id: int = Field(..., description="告警ID")
    rule_name: str = Field(..., description="规则名称")
    metric_name: str = Field(..., description="指标名称")
    current_value: float = Field(..., description="当前值")
    threshold: float = Field(..., description="阈值")
    severity: str = Field(..., description="严重程度")
    status: str = Field(..., description="状态: active, resolved")
    message: str = Field(..., description="告警消息")
    first_triggered: datetime = Field(..., description="首次触发时间")
    last_triggered: datetime = Field(..., description="最后触发时间")
    resolved_at: Optional[datetime] = Field(None, description="解决时间")


class AlertStatistics(BaseModel):
    """告警统计"""
    total_alerts: int = Field(..., description="总告警数")
    active_alerts: int = Field(..., description="活跃告警数")
    resolved_alerts: int = Field(..., description="已解决告警数")
    alerts_by_severity: Dict[str, int] = Field(..., description="按严重程度分组")
    alerts_by_metric: Dict[str, int] = Field(..., description="按指标分组")
    avg_resolution_time: float = Field(..., description="平均解决时间(分钟)")


class MonitoringReport(BaseModel):
    """监控报告"""
    report_id: str = Field(..., description="报告ID")
    report_type: str = Field(..., description="报告类型: daily, weekly, monthly")
    start_time: datetime = Field(..., description="开始时间")
    end_time: datetime = Field(..., description="结束时间")
    system_summary: Dict[str, Any] = Field(..., description="系统摘要")
    performance_summary: Dict[str, Any] = Field(..., description="性能摘要")
    alert_summary: AlertStatistics = Field(..., description="告警摘要")
    recommendations: List[str] = Field(..., description="建议")
    generated_at: datetime = Field(..., description="生成时间")