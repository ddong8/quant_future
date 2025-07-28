"""
报告生成相关的Pydantic模型
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field


class ReportTemplateBase(BaseModel):
    """报告模板基础模型"""
    name: str = Field(..., description="模板名称")
    description: Optional[str] = Field(None, description="模板描述")
    template_type: str = Field("html", description="模板类型")
    content: str = Field(..., description="模板内容")
    variables: Optional[List[str]] = Field(None, description="模板变量")


class ReportTemplateCreate(ReportTemplateBase):
    """创建报告模板"""
    pass


class ReportTemplateUpdate(BaseModel):
    """更新报告模板"""
    name: Optional[str] = Field(None, description="模板名称")
    description: Optional[str] = Field(None, description="模板描述")
    content: Optional[str] = Field(None, description="模板内容")
    variables: Optional[List[str]] = Field(None, description="模板变量")


class ReportTemplate(ReportTemplateBase):
    """报告模板响应"""
    id: int
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ReportRequestBase(BaseModel):
    """报告请求基础模型"""
    report_type: str = Field(..., description="报告类型: trading, performance, risk, custom")
    start_date: datetime = Field(..., description="开始日期")
    end_date: datetime = Field(..., description="结束日期")
    template_name: Optional[str] = Field(None, description="模板名称")
    parameters: Optional[Dict[str, Any]] = Field(None, description="报告参数")


class ReportRequest(ReportRequestBase):
    """报告生成请求"""
    user_id: Optional[int] = Field(None, description="用户ID")
    format: str = Field("html", description="输出格式: html, pdf")
    delivery_method: Optional[str] = Field(None, description="交付方式: email, download")
    recipients: Optional[List[str]] = Field(None, description="接收者列表")


class ReportData(BaseModel):
    """报告数据"""
    user_id: int = Field(..., description="用户ID")
    report_type: str = Field(..., description="报告类型")
    data: Dict[str, Any] = Field(..., description="报告数据")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")
    generated_at: datetime = Field(..., description="生成时间")


class TradingStatistics(BaseModel):
    """交易统计"""
    total_orders: int = Field(..., description="总订单数")
    filled_orders: int = Field(..., description="成交订单数")
    buy_orders: int = Field(..., description="买入订单数")
    sell_orders: int = Field(..., description="卖出订单数")
    fill_rate: float = Field(..., description="成交率")
    total_volume: float = Field(..., description="总交易量")
    total_commission: float = Field(..., description="总手续费")
    total_pnl: float = Field(..., description="总盈亏")
    realized_pnl: float = Field(..., description="已实现盈亏")
    unrealized_pnl: float = Field(..., description="未实现盈亏")
    win_rate: float = Field(..., description="胜率")
    total_positions: int = Field(..., description="总持仓数")
    profitable_positions: int = Field(..., description="盈利持仓数")
    avg_position_size: float = Field(..., description="平均持仓大小")


class TradingReport(BaseModel):
    """交易报告"""
    user_id: int = Field(..., description="用户ID")
    period_start: datetime = Field(..., description="报告开始时间")
    period_end: datetime = Field(..., description="报告结束时间")
    statistics: TradingStatistics = Field(..., description="交易统计")
    orders: List[Dict[str, Any]] = Field(..., description="订单列表")
    positions: List[Dict[str, Any]] = Field(..., description="持仓列表")
    summary: str = Field(..., description="报告摘要")


class PerformanceMetrics(BaseModel):
    """绩效指标"""
    total_return: float = Field(..., description="总收益率")
    annualized_return: float = Field(..., description="年化收益率")
    sharpe_ratio: float = Field(..., description="夏普比率")
    max_drawdown: float = Field(..., description="最大回撤")
    volatility: float = Field(..., description="波动率")
    win_rate: float = Field(..., description="胜率")
    profit_factor: float = Field(..., description="盈利因子")
    avg_trade_return: float = Field(..., description="平均交易收益")


class PerformanceReport(BaseModel):
    """绩效报告"""
    user_id: int = Field(..., description="用户ID")
    period_start: datetime = Field(..., description="报告开始时间")
    period_end: datetime = Field(..., description="报告结束时间")
    metrics: PerformanceMetrics = Field(..., description="绩效指标")
    backtest_results: List[Dict[str, Any]] = Field(..., description="回测结果")
    trading_performance: Dict[str, Any] = Field(..., description="交易绩效")
    benchmark_comparison: Optional[Dict[str, Any]] = Field(None, description="基准比较")


class RiskMetrics(BaseModel):
    """风险指标"""
    var_95: float = Field(..., description="95% VaR")
    var_99: float = Field(..., description="99% VaR")
    expected_shortfall: float = Field(..., description="期望损失")
    max_drawdown: float = Field(..., description="最大回撤")
    concentration_risk: float = Field(..., description="集中度风险")
    leverage_ratio: float = Field(..., description="杠杆比率")
    beta: Optional[float] = Field(None, description="贝塔系数")
    correlation_risk: Optional[float] = Field(None, description="相关性风险")


class RiskReport(BaseModel):
    """风险报告"""
    user_id: int = Field(..., description="用户ID")
    period_start: datetime = Field(..., description="报告开始时间")
    period_end: datetime = Field(..., description="报告结束时间")
    risk_metrics: RiskMetrics = Field(..., description="风险指标")
    risk_events: List[Dict[str, Any]] = Field(..., description="风险事件")
    position_analysis: Dict[str, Any] = Field(..., description="持仓分析")
    stress_test_results: Optional[Dict[str, Any]] = Field(None, description="压力测试结果")


class ReportSchedule(BaseModel):
    """报告调度配置"""
    name: str = Field(..., description="调度名称")
    report_type: str = Field(..., description="报告类型")
    template_name: str = Field(..., description="模板名称")
    cron_expression: str = Field(..., description="Cron表达式")
    enabled: bool = Field(True, description="是否启用")
    recipients: List[str] = Field(..., description="接收者列表")
    parameters: Optional[Dict[str, Any]] = Field(None, description="报告参数")


class ReportScheduleCreate(ReportSchedule):
    """创建报告调度"""
    user_id: int = Field(..., description="用户ID")


class ReportScheduleResponse(ReportSchedule):
    """报告调度响应"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ReportExecution(BaseModel):
    """报告执行记录"""
    id: int = Field(..., description="执行ID")
    schedule_id: Optional[int] = Field(None, description="调度ID")
    user_id: int = Field(..., description="用户ID")
    report_type: str = Field(..., description="报告类型")
    status: str = Field(..., description="执行状态")
    start_time: datetime = Field(..., description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    output_path: Optional[str] = Field(None, description="输出路径")
    error_message: Optional[str] = Field(None, description="错误信息")
    
    class Config:
        from_attributes = True


class ReportDelivery(BaseModel):
    """报告交付配置"""
    method: str = Field(..., description="交付方式: email, ftp, webhook")
    config: Dict[str, Any] = Field(..., description="交付配置")
    enabled: bool = Field(True, description="是否启用")


class CustomReportRequest(BaseModel):
    """自定义报告请求"""
    template_name: str = Field(..., description="模板名称")
    data_sources: List[str] = Field(..., description="数据源列表")
    parameters: Dict[str, Any] = Field(..., description="报告参数")
    format: str = Field("html", description="输出格式")


class ReportAnalytics(BaseModel):
    """报告分析数据"""
    total_reports: int = Field(..., description="总报告数")
    reports_by_type: Dict[str, int] = Field(..., description="按类型分组")
    reports_by_user: Dict[str, int] = Field(..., description="按用户分组")
    avg_generation_time: float = Field(..., description="平均生成时间")
    success_rate: float = Field(..., description="成功率")
    popular_templates: List[Dict[str, Any]] = Field(..., description="热门模板")


class ReportConfiguration(BaseModel):
    """报告系统配置"""
    max_report_size_mb: int = Field(100, description="最大报告大小(MB)")
    retention_days: int = Field(30, description="报告保留天数")
    concurrent_generations: int = Field(5, description="并发生成数")
    default_template: str = Field("default.html", description="默认模板")
    supported_formats: List[str] = Field(["html", "pdf"], description="支持的格式")
    email_settings: Optional[Dict[str, Any]] = Field(None, description="邮件设置")


class ReportValidation(BaseModel):
    """报告验证结果"""
    is_valid: bool = Field(..., description="是否有效")
    errors: List[str] = Field(..., description="错误列表")
    warnings: List[str] = Field(..., description="警告列表")
    suggestions: List[str] = Field(..., description="建议列表")


class ReportPreview(BaseModel):
    """报告预览"""
    template_name: str = Field(..., description="模板名称")
    sample_data: Dict[str, Any] = Field(..., description="示例数据")
    preview_html: str = Field(..., description="预览HTML")
    variables_used: List[str] = Field(..., description="使用的变量")


class ReportExportRequest(BaseModel):
    """报告导出请求"""
    report_ids: List[int] = Field(..., description="报告ID列表")
    format: str = Field("zip", description="导出格式")
    include_data: bool = Field(False, description="是否包含原始数据")


class ReportImportRequest(BaseModel):
    """报告导入请求"""
    file_path: str = Field(..., description="文件路径")
    import_type: str = Field(..., description="导入类型: template, schedule, data")
    overwrite: bool = Field(False, description="是否覆盖")


class ReportDashboard(BaseModel):
    """报告仪表板数据"""
    recent_reports: List[ReportExecution] = Field(..., description="最近报告")
    scheduled_reports: List[ReportScheduleResponse] = Field(..., description="调度报告")
    analytics: ReportAnalytics = Field(..., description="分析数据")
    system_status: Dict[str, Any] = Field(..., description="系统状态")


class ReportNotification(BaseModel):
    """报告通知"""
    report_id: int = Field(..., description="报告ID")
    user_id: int = Field(..., description="用户ID")
    notification_type: str = Field(..., description="通知类型")
    message: str = Field(..., description="通知消息")
    sent_at: datetime = Field(..., description="发送时间")
    status: str = Field(..., description="发送状态")


class ReportAudit(BaseModel):
    """报告审计日志"""
    id: int = Field(..., description="审计ID")
    user_id: int = Field(..., description="用户ID")
    action: str = Field(..., description="操作类型")
    resource_type: str = Field(..., description="资源类型")
    resource_id: Optional[int] = Field(None, description="资源ID")
    details: Dict[str, Any] = Field(..., description="操作详情")
    timestamp: datetime = Field(..., description="时间戳")
    ip_address: Optional[str] = Field(None, description="IP地址")
    
    class Config:
        from_attributes = True