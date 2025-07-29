"""
回测管理API路由
"""
from fastapi import APIRouter, Depends, Query, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional

from ...core.dependencies import (
    get_database,
    get_current_user,
    require_trader_or_admin,
    get_pagination_params,
    get_sort_params,
    PaginationParams,
    SortParams,
)
from ...core.response import (
    success_response,
    created_response,
    paginated_response,
    deleted_response,
)
from ...services.backtest_service import BacktestService
from ...services.history_service import HistoryService
from ...schemas.backtest import (
    BacktestCreate,
    BacktestUpdate,
    BacktestResponse,
    BacktestListResponse,
    BacktestProgressResponse,
    BacktestResultsResponse,
    BacktestStatsResponse,
    BacktestSearchRequest,
    BacktestCloneRequest,
    BacktestComparisonRequest,
    BacktestComparisonResponse,
)
from ...models import User
from ...models.enums import BacktestStatus

router = APIRouter()


@router.post("/", response_model=BacktestResponse, status_code=status.HTTP_201_CREATED)
async def create_backtest(
    backtest_data: BacktestCreate,
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_database),
):
    """创建回测"""
    history_service = HistoryService(db)
    backtest_service = BacktestService(db, history_service)
    
    backtest = backtest_service.create_backtest(
        backtest_data.dict(), 
        current_user.id
    )
    
    return created_response(
        data=BacktestResponse.from_orm(backtest).dict(),
        message="回测创建成功"
    )


@router.get("/", response_model=List[BacktestListResponse])
async def get_backtests_list(
    strategy_id: Optional[int] = Query(None, description="策略ID"),
    status: Optional[BacktestStatus] = Query(None, description="回测状态"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    pagination: PaginationParams = Depends(get_pagination_params),
    sort_params: SortParams = Depends(get_sort_params),
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_database),
):
    """获取回测列表"""
    history_service = HistoryService(db)
    backtest_service = BacktestService(db, history_service)
    
    backtests, total = backtest_service.get_backtests_list(
        user_id=current_user.id,
        strategy_id=strategy_id,
        status=status,
        keyword=keyword,
        pagination=pagination,
        sort_params=sort_params
    )
    
    backtest_list = [BacktestListResponse.from_orm(bt) for bt in backtests]
    
    return paginated_response(
        data=[bt.dict() for bt in backtest_list],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        message="获取回测列表成功"
    )


@router.get("/stats", response_model=BacktestStatsResponse)
async def get_backtest_stats(
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_database),
):
    """获取回测统计信息"""
    history_service = HistoryService(db)
    backtest_service = BacktestService(db, history_service)
    
    stats = backtest_service.get_backtest_statistics(current_user.id)
    
    return success_response(
        data=stats,
        message="获取回测统计成功"
    )


@router.get("/{backtest_id}", response_model=BacktestResponse)
async def get_backtest_by_id(
    backtest_id: int,
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_database),
):
    """根据ID获取回测详情"""
    history_service = HistoryService(db)
    backtest_service = BacktestService(db, history_service)
    
    backtest = backtest_service.get_backtest_by_id(backtest_id, current_user.id)
    
    return success_response(
        data=BacktestResponse.from_orm(backtest).dict(),
        message="获取回测详情成功"
    )


@router.put("/{backtest_id}", response_model=BacktestResponse)
async def update_backtest(
    backtest_id: int,
    backtest_data: BacktestUpdate,
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_database),
):
    """更新回测"""
    history_service = HistoryService(db)
    backtest_service = BacktestService(db, history_service)
    
    backtest = backtest_service.update_backtest(
        backtest_id, 
        backtest_data.dict(exclude_unset=True), 
        current_user.id
    )
    
    return success_response(
        data=BacktestResponse.from_orm(backtest).dict(),
        message="回测更新成功"
    )


@router.delete("/{backtest_id}")
async def delete_backtest(
    backtest_id: int,
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_database),
):
    """删除回测"""
    history_service = HistoryService(db)
    backtest_service = BacktestService(db, history_service)
    
    success = backtest_service.delete_backtest(backtest_id, current_user.id)
    
    if success:
        return deleted_response(message="回测删除成功")


@router.post("/{backtest_id}/start")
async def start_backtest(
    backtest_id: int,
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_database),
):
    """启动回测"""
    history_service = HistoryService(db)
    backtest_service = BacktestService(db, history_service)
    
    result = await backtest_service.start_backtest(backtest_id, current_user.id)
    
    return success_response(
        data=result,
        message="回测启动成功"
    )


@router.post("/{backtest_id}/stop")
async def stop_backtest(
    backtest_id: int,
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_database),
):
    """停止回测"""
    history_service = HistoryService(db)
    backtest_service = BacktestService(db, history_service)
    
    result = backtest_service.stop_backtest(backtest_id, current_user.id)
    
    return success_response(
        data=result,
        message="回测停止成功"
    )


@router.get("/{backtest_id}/progress", response_model=BacktestProgressResponse)
async def get_backtest_progress(
    backtest_id: int,
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_database),
):
    """获取回测进度"""
    history_service = HistoryService(db)
    backtest_service = BacktestService(db, history_service)
    
    progress = backtest_service.get_backtest_progress(backtest_id, current_user.id)
    
    return success_response(
        data=progress,
        message="获取回测进度成功"
    )


@router.get("/{backtest_id}/results", response_model=BacktestResultsResponse)
async def get_backtest_results(
    backtest_id: int,
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_database),
):
    """获取回测结果"""
    history_service = HistoryService(db)
    backtest_service = BacktestService(db, history_service)
    
    results = backtest_service.get_backtest_results(backtest_id, current_user.id)
    
    return success_response(
        data=results,
        message="获取回测结果成功"
    )


@router.post("/{backtest_id}/clone", response_model=BacktestResponse)
async def clone_backtest(
    backtest_id: int,
    clone_data: BacktestCloneRequest,
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_database),
):
    """克隆回测"""
    history_service = HistoryService(db)
    backtest_service = BacktestService(db, history_service)
    
    cloned_backtest = backtest_service.clone_backtest(
        backtest_id, 
        clone_data.name, 
        current_user.id
    )
    
    return created_response(
        data=BacktestResponse.from_orm(cloned_backtest).dict(),
        message="回测克隆成功"
    )


@router.post("/compare", response_model=BacktestComparisonResponse)
async def compare_backtests(
    comparison_request: BacktestComparisonRequest,
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_database),
):
    """比较多个回测结果"""
    history_service = HistoryService(db)
    backtest_service = BacktestService(db, history_service)
    
    comparison_data = backtest_service.compare_backtests(
        comparison_request.backtest_ids, 
        current_user.id
    )
    
    return success_response(
        data=comparison_data,
        message="回测比较完成"
    )


@router.get("/{backtest_id}/equity-curve")
async def get_equity_curve(
    backtest_id: int,
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_database),
):
    """获取资金曲线数据"""
    history_service = HistoryService(db)
    backtest_service = BacktestService(db, history_service)
    
    backtest = backtest_service.get_backtest_by_id(backtest_id, current_user.id)
    
    if backtest.status != BacktestStatus.COMPLETED:
        return success_response(
            data=[],
            message="回测尚未完成"
        )
    
    return success_response(
        data=backtest.equity_curve or [],
        message="获取资金曲线成功"
    )


@router.get("/{backtest_id}/trades")
async def get_trade_records(
    backtest_id: int,
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_database),
):
    """获取交易记录"""
    history_service = HistoryService(db)
    backtest_service = BacktestService(db, history_service)
    
    backtest = backtest_service.get_backtest_by_id(backtest_id, current_user.id)
    
    if backtest.status != BacktestStatus.COMPLETED:
        return success_response(
            data=[],
            message="回测尚未完成"
        )
    
    return success_response(
        data=backtest.trade_records or [],
        message="获取交易记录成功"
    )


@router.get("/{backtest_id}/daily-returns")
async def get_daily_returns(
    backtest_id: int,
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_database),
):
    """获取日收益率数据"""
    history_service = HistoryService(db)
    backtest_service = BacktestService(db, history_service)
    
    backtest = backtest_service.get_backtest_by_id(backtest_id, current_user.id)
    
    if backtest.status != BacktestStatus.COMPLETED:
        return success_response(
            data=[],
            message="回测尚未完成"
        )
    
    return success_response(
        data=backtest.daily_returns or [],
        message="获取日收益率成功"
    )


@router.get("/{backtest_id}/performance-metrics")
async def get_performance_metrics(
    backtest_id: int,
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_database),
):
    """获取详细性能指标"""
    history_service = HistoryService(db)
    backtest_service = BacktestService(db, history_service)
    
    backtest = backtest_service.get_backtest_by_id(backtest_id, current_user.id)
    
    if backtest.status != BacktestStatus.COMPLETED:
        return success_response(
            data={},
            message="回测尚未完成"
        )
    
    # 构建详细性能指标
    metrics = {
        # 收益指标
        'total_return': backtest.total_return,
        'annual_return': backtest.annual_return,
        'final_capital': backtest.final_capital,
        'initial_capital': backtest.initial_capital,
        
        # 风险指标
        'max_drawdown': backtest.max_drawdown,
        'sharpe_ratio': backtest.sharpe_ratio,
        'sortino_ratio': backtest.sortino_ratio,
        
        # 交易指标
        'total_trades': backtest.total_trades,
        'winning_trades': backtest.winning_trades,
        'losing_trades': backtest.losing_trades,
        'win_rate': backtest.win_rate,
        'avg_win': backtest.avg_win,
        'avg_loss': backtest.avg_loss,
        'profit_factor': backtest.profit_factor,
        
        # 时间信息
        'duration_days': (backtest.end_date - backtest.start_date).days,
        'trading_period': f"{backtest.start_date.strftime('%Y-%m-%d')} 至 {backtest.end_date.strftime('%Y-%m-%d')}",
        
        # 策略信息
        'strategy_id': backtest.strategy_id,
        'symbols': backtest.symbols,
        'parameters': backtest.parameters,
    }
    
    return success_response(
        data=metrics,
        message="获取性能指标成功"
    )


@router.post("/{backtest_id}/restart")
async def restart_backtest(
    backtest_id: int,
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_database),
):
    """重新启动回测"""
    history_service = HistoryService(db)
    backtest_service = BacktestService(db, history_service)
    
    # 先停止（如果正在运行）
    try:
        backtest_service.stop_backtest(backtest_id, current_user.id)
    except:
        pass  # 忽略停止失败的错误
    
    # 重新启动
    result = await backtest_service.start_backtest(backtest_id, current_user.id)
    
    return success_response(
        data=result,
        message="回测重新启动成功"
    )


@router.get("/running/list")
async def get_running_backtests(
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_database),
):
    """获取正在运行的回测列表"""
    history_service = HistoryService(db)
    backtest_service = BacktestService(db, history_service)
    
    running_backtests, _ = backtest_service.get_backtests_list(
        user_id=current_user.id,
        status=BacktestStatus.RUNNING
    )
    
    running_list = []
    for backtest in running_backtests:
        progress = backtest_service.get_backtest_progress(backtest.id, current_user.id)
        running_list.append({
            'id': backtest.id,
            'name': backtest.name,
            'strategy_id': backtest.strategy_id,
            'progress': progress['progress'],
            'started_at': progress['started_at'],
            'eta': progress['eta']
        })
    
    return success_response(
        data=running_list,
        message="获取运行中回测列表成功"
    )


@router.post("/batch-stop")
async def batch_stop_backtests(
    backtest_ids: List[int],
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_database),
):
    """批量停止回测"""
    if len(backtest_ids) > 20:
        return success_response(
            data={'error': '批量操作最多支持20个回测'},
            message="批量停止失败"
        )
    
    history_service = HistoryService(db)
    backtest_service = BacktestService(db, history_service)
    
    results = []
    for backtest_id in backtest_ids:
        try:
            result = backtest_service.stop_backtest(backtest_id, current_user.id)
            results.append({
                'backtest_id': backtest_id,
                'success': True,
                'message': '停止成功'
            })
        except Exception as e:
            results.append({
                'backtest_id': backtest_id,
                'success': False,
                'message': str(e)
            })
    
    success_count = len([r for r in results if r['success']])
    
    return success_response(
        data={
            'results': results,
            'success_count': success_count,
            'failed_count': len(results) - success_count
        },
        message=f"批量停止完成，成功: {success_count}, 失败: {len(results) - success_count}"
    )
# 回测分析和报告相关API

@router.get("/{backtest_id}/analysis")
async def analyze_backtest_results(
    backtest_id: int,
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_database),
):
    """分析回测结果"""
    history_service = HistoryService(db)
    backtest_service = BacktestService(db, history_service)
    
    analysis_result = backtest_service.analyze_backtest_results(backtest_id, current_user.id)
    
    return success_response(
        data=analysis_result,
        message="回测结果分析完成"
    )


@router.post("/{backtest_id}/report")
async def generate_backtest_report(
    backtest_id: int,
    report_type: str = Query("detailed", description="报告类型: summary/detailed"),
    format: str = Query("html", description="报告格式: html/pdf"),
    include_charts: bool = Query(True, description="是否包含图表"),
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_database),
):
    """生成回测报告"""
    history_service = HistoryService(db)
    backtest_service = BacktestService(db, history_service)
    
    report_result = backtest_service.generate_backtest_report(
        backtest_id, 
        current_user.id, 
        report_type, 
        format, 
        include_charts
    )
    
    return success_response(
        data=report_result,
        message="回测报告生成成功"
    )


@router.get("/{backtest_id}/charts/{chart_type}")
async def get_chart_data(
    backtest_id: int,
    chart_type: str,
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_database),
):
    """获取图表数据
    
    支持的图表类型:
    - equity_curve: 资金曲线
    - drawdown: 回撤分析
    - returns_distribution: 收益率分布
    - monthly_returns: 月度收益热力图
    - rolling_metrics: 滚动指标
    - trade_analysis: 交易分析
    - risk_metrics: 风险指标
    """
    history_service = HistoryService(db)
    backtest_service = BacktestService(db, history_service)
    
    chart_data = backtest_service.get_chart_data(backtest_id, current_user.id, chart_type)
    
    return success_response(
        data=chart_data,
        message=f"获取{chart_type}图表数据成功"
    )


@router.get("/{backtest_id}/attribution")
async def get_performance_attribution(
    backtest_id: int,
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_database),
):
    """获取业绩归因分析"""
    history_service = HistoryService(db)
    backtest_service = BacktestService(db, history_service)
    
    attribution_result = backtest_service.get_performance_attribution(backtest_id, current_user.id)
    
    return success_response(
        data=attribution_result,
        message="业绩归因分析完成"
    )


@router.post("/detailed-comparison")
async def detailed_backtest_comparison(
    backtest_ids: List[int],
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_database),
):
    """详细回测比较"""
    history_service = HistoryService(db)
    backtest_service = BacktestService(db, history_service)
    
    comparison_result = backtest_service.compare_backtests_detailed(backtest_ids, current_user.id)
    
    return success_response(
        data=comparison_result,
        message="详细回测比较完成"
    )


@router.get("/{backtest_id}/rolling-performance")
async def get_rolling_performance(
    backtest_id: int,
    window: int = Query(252, description="滚动窗口大小（交易日）"),
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_database),
):
    """获取滚动性能指标"""
    history_service = HistoryService(db)
    backtest_service = BacktestService(db, history_service)
    
    rolling_result = backtest_service.get_rolling_performance(backtest_id, current_user.id, window)
    
    return success_response(
        data=rolling_result,
        message="获取滚动性能指标成功"
    )


@router.get("/{backtest_id}/risk-analysis")
async def get_risk_analysis(
    backtest_id: int,
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_database),
):
    """获取风险分析"""
    history_service = HistoryService(db)
    backtest_service = BacktestService(db, history_service)
    
    # 获取风险指标数据
    risk_data = backtest_service.get_chart_data(backtest_id, current_user.id, "risk_metrics")
    
    return success_response(
        data=risk_data,
        message="风险分析完成"
    )


@router.get("/{backtest_id}/monthly-analysis")
async def get_monthly_analysis(
    backtest_id: int,
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_database),
):
    """获取月度分析"""
    history_service = HistoryService(db)
    backtest_service = BacktestService(db, history_service)
    
    backtest = backtest_service.get_backtest_by_id(backtest_id, current_user.id)
    
    if backtest.status != BacktestStatus.COMPLETED:
        return success_response(
            data={},
            message="回测尚未完成"
        )
    
    # 获取月度收益数据
    monthly_data = backtest_service.get_chart_data(backtest_id, current_user.id, "monthly_returns")
    
    return success_response(
        data=monthly_data,
        message="月度分析完成"
    )


@router.get("/{backtest_id}/trade-analysis")
async def get_trade_analysis(
    backtest_id: int,
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_database),
):
    """获取交易分析"""
    history_service = HistoryService(db)
    backtest_service = BacktestService(db, history_service)
    
    trade_data = backtest_service.get_chart_data(backtest_id, current_user.id, "trade_analysis")
    
    return success_response(
        data=trade_data,
        message="交易分析完成"
    )


@router.get("/{backtest_id}/summary-stats")
async def get_summary_statistics(
    backtest_id: int,
    current_user: User = Depends(require_trader_or_admin),
    db: Session = Depends(get_database),
):
    """获取汇总统计"""
    history_service = HistoryService(db)
    backtest_service = BacktestService(db, history_service)
    
    backtest = backtest_service.get_backtest_by_id(backtest_id, current_user.id)
    
    if backtest.status != BacktestStatus.COMPLETED:
        return success_response(
            data={},
            message="回测尚未完成"
        )
    
    # 构建汇总统计
    summary_stats = {
        "基本信息": {
            "回测名称": backtest.name,
            "策略ID": backtest.strategy_id,
            "回测期间": f"{backtest.start_date.strftime('%Y-%m-%d')} 至 {backtest.end_date.strftime('%Y-%m-%d')}",
            "交易天数": (backtest.end_date - backtest.start_date).days,
            "初始资金": backtest.initial_capital,
            "最终资金": backtest.final_capital,
            "交易品种": backtest.symbols,
        },
        "收益统计": {
            "总收益": backtest.final_capital - backtest.initial_capital,
            "总收益率": backtest.total_return,
            "年化收益率": backtest.annual_return,
            "最大回撤": backtest.max_drawdown,
            "夏普比率": backtest.sharpe_ratio,
            "索提诺比率": backtest.sortino_ratio,
        },
        "交易统计": {
            "总交易次数": backtest.total_trades,
            "盈利交易": backtest.winning_trades,
            "亏损交易": backtest.losing_trades,
            "胜率": backtest.win_rate,
            "平均盈利": backtest.avg_win,
            "平均亏损": backtest.avg_loss,
            "盈亏比": backtest.profit_factor,
        },
        "时间统计": {
            "创建时间": backtest.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            "开始时间": backtest.started_at.strftime('%Y-%m-%d %H:%M:%S') if backtest.started_at else None,
            "完成时间": backtest.completed_at.strftime('%Y-%m-%d %H:%M:%S') if backtest.completed_at else None,
            "执行耗时": str(backtest.completed_at - backtest.started_at) if backtest.started_at and backtest.completed_at else None,
        }
    }
    
    return success_response(
        data=summary_stats,
        message="获取汇总统计成功"
    )