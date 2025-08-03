"""
持仓管理API路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime

from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...core.permissions import require_permission
from ...models.user import User
from ...models.role import PermissionConstants
from ...models.position import PositionStatus, PositionType
from ...services.position_service import PositionService
from ...services.position_operation_service import PositionOperationService
from ...schemas.position import (
    PositionResponse, PositionCreate, PositionUpdate,
    PositionHistoryResponse, PositionSummaryResponse,
    StopLossRequest, TakeProfitRequest, ClosePositionRequest,
    MarketDataUpdate, BatchMarketDataUpdate,
    PositionFilter, PortfolioMetrics, PositionStatistics,
    StopTrigger, PositionConsistencyCheck, PositionRepairResult,
    PositionListResponse, PositionHistoryListResponse,
    FreezeQuantityRequest, UnfreezeQuantityRequest,
    PositionRiskMetrics, PositionAlert
)
from ...core.response import success_response, error_response

router = APIRouter(prefix="/positions", tags=["持仓管理"])

@router.get("/", response_model=Dict[str, Any])
@require_permission(PermissionConstants.POSITION_VIEW)
async def get_positions(
    status: Optional[PositionStatus] = Query(None, description="持仓状态"),
    symbol: Optional[str] = Query(None, description="交易标的"),
    position_type: Optional[PositionType] = Query(None, description="持仓类型"),
    strategy_id: Optional[int] = Query(None, description="策略ID"),
    backtest_id: Optional[int] = Query(None, description="回测ID"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取持仓列表"""
    try:
        position_service = PositionService(db)
        
        # 获取持仓列表
        positions = position_service.get_user_positions(
            user_id=current_user.id,
            status=status,
            symbol=symbol
        )
        
        # 应用其他筛选条件
        if position_type:
            positions = [p for p in positions if p.position_type == position_type]
        if strategy_id:
            positions = [p for p in positions if p.strategy_id == strategy_id]
        if backtest_id:
            positions = [p for p in positions if p.backtest_id == backtest_id]
        
        # 分页
        total = len(positions)
        start = (page - 1) * size
        end = start + size
        page_positions = positions[start:end]
        
        return success_response(
            data={
                "items": [pos.to_dict() for pos in page_positions],
                "total": total,
                "page": page,
                "size": size,
                "has_next": end < total
            },
            message="获取持仓列表成功"
        )
    except Exception as e:
        return error_response(message=str(e))

@router.get("/{position_id}", response_model=Dict[str, Any])
@require_permission(PermissionConstants.POSITION_VIEW)
async def get_position(
    position_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取持仓详情"""
    try:
        position_service = PositionService(db)
        position = position_service.get_position(position_id, current_user.id)
        
        return success_response(
            data=position.to_dict(),
            message="获取持仓详情成功"
        )
    except Exception as e:
        return error_response(message=str(e))

@router.put("/{position_id}", response_model=Dict[str, Any])
@require_permission(PermissionConstants.POSITION_MANAGE)
async def update_position(
    position_id: int,
    position_data: PositionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新持仓信息"""
    try:
        position_service = PositionService(db)
        position = position_service.get_position(position_id, current_user.id)
        
        # 更新字段
        if position_data.stop_loss_price is not None:
            position.stop_loss_price = position_data.stop_loss_price
        if position_data.take_profit_price is not None:
            position.take_profit_price = position_data.take_profit_price
        if position_data.notes is not None:
            position.notes = position_data.notes
        if position_data.tags is not None:
            position.tags = position_data.tags
        
        db.commit()
        db.refresh(position)
        
        return success_response(
            data=position.to_dict(),
            message="更新持仓成功"
        )
    except Exception as e:
        return error_response(message=str(e))

@router.post("/{position_id}/stop-loss", response_model=Dict[str, Any])
@require_permission(PermissionConstants.POSITION_MANAGE)
async def set_stop_loss(
    position_id: int,
    request: StopLossRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """设置止损"""
    try:
        position_service = PositionService(db)
        position = position_service.set_stop_loss(
            position_id=position_id,
            user_id=current_user.id,
            stop_price=request.stop_price,
            order_id=request.order_id
        )
        
        return success_response(
            data=position.to_dict(),
            message="设置止损成功"
        )
    except Exception as e:
        return error_response(message=str(e))

@router.post("/{position_id}/take-profit", response_model=Dict[str, Any])
@require_permission(PermissionConstants.POSITION_MANAGE)
async def set_take_profit(
    position_id: int,
    request: TakeProfitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """设置止盈"""
    try:
        position_service = PositionService(db)
        position = position_service.set_take_profit(
            position_id=position_id,
            user_id=current_user.id,
            profit_price=request.profit_price,
            order_id=request.order_id
        )
        
        return success_response(
            data=position.to_dict(),
            message="设置止盈成功"
        )
    except Exception as e:
        return error_response(message=str(e))

@router.post("/{position_id}/close", response_model=Dict[str, Any])
@require_permission(PermissionConstants.POSITION_MANAGE)
async def close_position(
    position_id: int,
    request: ClosePositionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """平仓"""
    try:
        position_service = PositionService(db)
        position = position_service.close_position(
            position_id=position_id,
            user_id=current_user.id,
            close_price=request.close_price,
            reason=request.reason
        )
        
        return success_response(
            data=position.to_dict(),
            message="平仓成功"
        )
    except Exception as e:
        return error_response(message=str(e))

@router.post("/{position_id}/freeze", response_model=Dict[str, Any])
@require_permission(PermissionConstants.POSITION_MANAGE)
async def freeze_quantity(
    position_id: int,
    request: FreezeQuantityRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """冻结持仓数量"""
    try:
        position_service = PositionService(db)
        position = position_service.get_position(position_id, current_user.id)
        
        success = position.freeze_quantity(request.quantity)
        if not success:
            return error_response(message="冻结失败，可用数量不足")
        
        db.commit()
        db.refresh(position)
        
        return success_response(
            data=position.to_dict(),
            message="冻结数量成功"
        )
    except Exception as e:
        return error_response(message=str(e))

@router.post("/{position_id}/unfreeze", response_model=Dict[str, Any])
@require_permission(PermissionConstants.POSITION_MANAGE)
async def unfreeze_quantity(
    position_id: int,
    request: UnfreezeQuantityRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """解冻持仓数量"""
    try:
        position_service = PositionService(db)
        position = position_service.get_position(position_id, current_user.id)
        
        success = position.unfreeze_quantity(request.quantity)
        if not success:
            return error_response(message="解冻失败，冻结数量不足")
        
        db.commit()
        db.refresh(position)
        
        return success_response(
            data=position.to_dict(),
            message="解冻数量成功"
        )
    except Exception as e:
        return error_response(message=str(e))

@router.get("/{position_id}/history", response_model=Dict[str, Any])
@require_permission(PermissionConstants.POSITION_VIEW)
async def get_position_history(
    position_id: int,
    action: Optional[str] = Query(None, description="操作类型"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取持仓历史记录"""
    try:
        position_service = PositionService(db)
        history_records = position_service.get_position_history(
            position_id=position_id,
            user_id=current_user.id,
            action=action
        )
        
        # 分页
        total = len(history_records)
        start = (page - 1) * size
        end = start + size
        page_records = history_records[start:end]
        
        return success_response(
            data={
                "items": [record.to_dict() for record in page_records],
                "total": total,
                "page": page,
                "size": size,
                "has_next": end < total
            },
            message="获取持仓历史成功"
        )
    except Exception as e:
        return error_response(message=str(e))

@router.get("/portfolio/summary", response_model=Dict[str, Any])
@require_permission(PermissionConstants.POSITION_VIEW)
async def get_portfolio_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取投资组合摘要"""
    try:
        position_service = PositionService(db)
        summary = position_service.get_portfolio_summary(current_user.id)
        
        return success_response(
            data=summary,
            message="获取投资组合摘要成功"
        )
    except Exception as e:
        return error_response(message=str(e))

@router.get("/portfolio/statistics", response_model=Dict[str, Any])
@require_permission(PermissionConstants.POSITION_VIEW)
async def get_position_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取持仓统计信息"""
    try:
        position_service = PositionService(db)
        statistics = position_service.get_position_statistics(current_user.id)
        
        return success_response(
            data=statistics,
            message="获取持仓统计成功"
        )
    except Exception as e:
        return error_response(message=str(e))

@router.post("/market-data/update", response_model=Dict[str, Any])
@require_permission(PermissionConstants.DATA_MANAGE)
async def update_market_data(
    request: BatchMarketDataUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量更新市场数据"""
    try:
        position_service = PositionService(db)
        position_service.update_market_prices(request.price_data)
        
        return success_response(
            message=f"成功更新 {len(request.price_data)} 个标的的市场数据"
        )
    except Exception as e:
        return error_response(message=str(e))

@router.get("/stop-triggers/check", response_model=Dict[str, Any])
@require_permission(PermissionConstants.POSITION_VIEW)
async def check_stop_triggers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """检查止损止盈触发"""
    try:
        position_service = PositionService(db)
        triggers = position_service.check_stop_triggers(current_user.id)
        
        return success_response(
            data=triggers,
            message=f"检查完成，发现 {len(triggers)} 个触发条件"
        )
    except Exception as e:
        return error_response(message=str(e))

@router.post("/consistency/check", response_model=Dict[str, Any])
@require_permission(PermissionConstants.POSITION_MANAGE)
async def check_position_consistency(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """检查持仓数据一致性"""
    try:
        position_service = PositionService(db)
        result = position_service.calculation_service.check_position_consistency(current_user.id)
        
        return success_response(
            data=result,
            message="持仓一致性检查完成"
        )
    except Exception as e:
        return error_response(message=str(e))

@router.post("/consistency/repair", response_model=Dict[str, Any])
@require_permission(PermissionConstants.POSITION_MANAGE)
async def repair_position_data(
    position_id: Optional[int] = Query(None, description="指定持仓ID，不指定则修复所有"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """修复持仓数据"""
    try:
        position_service = PositionService(db)
        result = position_service.calculation_service.repair_position_data(
            user_id=current_user.id,
            position_id=position_id
        )
        
        return success_response(
            data=result,
            message="持仓数据修复完成"
        )
    except Exception as e:
        return error_response(message=str(e))

@router.get("/symbols/{symbol}", response_model=Dict[str, Any])
@require_permission(PermissionConstants.POSITION_VIEW)
async def get_position_by_symbol(
    symbol: str,
    strategy_id: Optional[int] = Query(None, description="策略ID"),
    backtest_id: Optional[int] = Query(None, description="回测ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """根据标的获取持仓"""
    try:
        position_service = PositionService(db)
        position = position_service.get_position_by_symbol(
            user_id=current_user.id,
            symbol=symbol,
            strategy_id=strategy_id,
            backtest_id=backtest_id
        )
        
        if not position:
            return success_response(
                data=None,
                message="未找到对应持仓"
            )
        
        return success_response(
            data=position.to_dict(),
            message="获取持仓成功"
        )
    except Exception as e:
        return error_response(message=str(e))

@router.get("/export/csv", response_model=Dict[str, Any])
@require_permission(PermissionConstants.DATA_EXPORT)
async def export_positions_csv(
    status: Optional[PositionStatus] = Query(None, description="持仓状态"),
    symbol: Optional[str] = Query(None, description="交易标的"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """导出持仓数据为CSV"""
    try:
        position_service = PositionService(db)
        positions = position_service.get_user_positions(
            user_id=current_user.id,
            status=status,
            symbol=symbol
        )
        
        # 生成CSV数据
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 写入表头
        headers = [
            'ID', '标的', '持仓类型', '状态', '数量', '可用数量', '冻结数量',
            '平均成本', '总成本', '当前价格', '市值', '已实现盈亏', '未实现盈亏',
            '总盈亏', '收益率', '开仓时间', '平仓时间'
        ]
        writer.writerow(headers)
        
        # 写入数据
        for pos in positions:
            row = [
                pos.id,
                pos.symbol,
                '多头' if pos.is_long else '空头',
                '持仓中' if pos.is_open else '已平仓',
                float(pos.quantity),
                float(pos.available_quantity),
                float(pos.frozen_quantity),
                float(pos.average_cost),
                float(pos.total_cost),
                float(pos.current_price) if pos.current_price else '',
                float(pos.market_value) if pos.market_value else '',
                float(pos.realized_pnl),
                float(pos.unrealized_pnl),
                float(pos.total_pnl),
                f"{pos.return_rate:.2%}",
                pos.opened_at.strftime('%Y-%m-%d %H:%M:%S') if pos.opened_at else '',
                pos.closed_at.strftime('%Y-%m-%d %H:%M:%S') if pos.closed_at else ''
            ]
            writer.writerow(row)
        
        csv_content = output.getvalue()
        output.close()
        
        return success_response(
            data={
                'csv_content': csv_content,
                'filename': f'positions_{current_user.username}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                'record_count': len(positions)
            },
            message="导出持仓数据成功"
        )
    except Exception as e:
        return error_response(message=str(e))

# 实时更新相关接口
@router.post("/realtime/subscribe", response_model=Dict[str, Any])
@require_permission(PermissionConstants.POSITION_VIEW)
async def subscribe_realtime_updates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """订阅持仓实时更新"""
    try:
        from ...services.position_realtime_service import realtime_service
        await realtime_service.subscribe_user_positions(current_user.id)
        
        return success_response(message="订阅持仓实时更新成功")
    except Exception as e:
        return error_response(message=str(e))

@router.post("/realtime/unsubscribe", response_model=Dict[str, Any])
@require_permission(PermissionConstants.POSITION_VIEW)
async def unsubscribe_realtime_updates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """取消订阅持仓实时更新"""
    try:
        from ...services.position_realtime_service import realtime_service
        await realtime_service.unsubscribe_user_positions(current_user.id)
        
        return success_response(message="取消订阅持仓实时更新成功")
    except Exception as e:
        return error_response(message=str(e))

@router.get("/realtime/metrics", response_model=Dict[str, Any])
@require_permission(PermissionConstants.POSITION_VIEW)
async def get_realtime_portfolio_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取实时投资组合指标"""
    try:
        from ...services.position_realtime_service import realtime_service
        metrics = await realtime_service.calculate_portfolio_metrics(current_user.id)
        
        return success_response(
            data=metrics,
            message="获取实时投资组合指标成功"
        )
    except Exception as e:
        return error_response(message=str(e))

@router.get("/realtime/alerts", response_model=Dict[str, Any])
@require_permission(PermissionConstants.POSITION_VIEW)
async def get_risk_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取风险预警"""
    try:
        from ...services.position_realtime_service import realtime_service
        alerts = await realtime_service.check_risk_alerts(current_user.id)
        
        return success_response(
            data=alerts,
            message=f"获取风险预警成功，发现 {len(alerts)} 个预警"
        )
    except Exception as e:
        return error_response(message=str(e))

# 图表分析相关接口
@router.get("/{position_id}/chart/pnl", response_model=Dict[str, Any])
@require_permission(PermissionConstants.POSITION_VIEW)
async def get_position_pnl_chart(
    position_id: int,
    period: str = Query('1d', description="时间周期: 1d, 1w, 1m, 3m"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取持仓盈亏图表"""
    try:
        from ...services.position_chart_service import PositionChartService
        
        # 验证持仓权限
        position_service = PositionService(db)
        position_service.get_position(position_id, current_user.id)
        
        chart_service = PositionChartService(db)
        chart_data = chart_service.get_position_pnl_chart(position_id, period)
        
        return success_response(
            data=chart_data,
            message="获取持仓盈亏图表成功"
        )
    except Exception as e:
        return error_response(message=str(e))

@router.get("/{position_id}/chart/return", response_model=Dict[str, Any])
@require_permission(PermissionConstants.POSITION_VIEW)
async def get_position_return_chart(
    position_id: int,
    period: str = Query('1d', description="时间周期: 1d, 1w, 1m, 3m"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取持仓收益率图表"""
    try:
        from ...services.position_chart_service import PositionChartService
        
        # 验证持仓权限
        position_service = PositionService(db)
        position_service.get_position(position_id, current_user.id)
        
        chart_service = PositionChartService(db)
        chart_data = chart_service.get_position_return_chart(position_id, period)
        
        return success_response(
            data=chart_data,
            message="获取持仓收益率图表成功"
        )
    except Exception as e:
        return error_response(message=str(e))

@router.get("/portfolio/chart/allocation", response_model=Dict[str, Any])
@require_permission(PermissionConstants.POSITION_VIEW)
async def get_portfolio_allocation_chart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取投资组合配置图表"""
    try:
        from ...services.position_chart_service import PositionChartService
        
        chart_service = PositionChartService(db)
        chart_data = chart_service.get_portfolio_allocation_chart(current_user.id)
        
        return success_response(
            data=chart_data,
            message="获取投资组合配置图表成功"
        )
    except Exception as e:
        return error_response(message=str(e))

@router.get("/portfolio/chart/performance", response_model=Dict[str, Any])
@require_permission(PermissionConstants.POSITION_VIEW)
async def get_portfolio_performance_chart(
    period: str = Query('1m', description="时间周期: 1d, 1w, 1m, 3m"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取投资组合表现图表"""
    try:
        from ...services.position_chart_service import PositionChartService
        
        chart_service = PositionChartService(db)
        chart_data = chart_service.get_portfolio_performance_chart(current_user.id, period)
        
        return success_response(
            data=chart_data,
            message="获取投资组合表现图表成功"
        )
    except Exception as e:
        return error_response(message=str(e))

@router.get("/portfolio/chart/risk", response_model=Dict[str, Any])
@require_permission(PermissionConstants.POSITION_VIEW)
async def get_risk_metrics_chart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取风险指标图表"""
    try:
        from ...services.position_chart_service import PositionChartService
        
        chart_service = PositionChartService(db)
        chart_data = chart_service.get_risk_metrics_chart(current_user.id)
        
        return success_response(
            data=chart_data,
            message="获取风险指标图表成功"
        )
    except Exception as e:
        return error_response(message=str(e))

@router.get("/portfolio/chart/sector", response_model=Dict[str, Any])
@require_permission(PermissionConstants.POSITION_VIEW)
async def get_sector_distribution_chart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取行业分布图表"""
    try:
        from ...services.position_chart_service import PositionChartService
        
        chart_service = PositionChartService(db)
        chart_data = chart_service.get_sector_distribution_chart(current_user.id)
        
        return success_response(
            data=chart_data,
            message="获取行业分布图表成功"
        )
    except Exception as e:
        return error_response(message=str(e))

@router.get("/{position_id}/trend", response_model=Dict[str, Any])
@require_permission(PermissionConstants.POSITION_VIEW)
async def get_position_trend_data(
    position_id: int,
    period: str = Query('1d', description="时间周期: 1d, 1w, 1m"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取持仓趋势数据"""
    try:
        from ...services.position_realtime_service import realtime_service
        
        # 验证持仓权限
        position_service = PositionService(db)
        position_service.get_position(position_id, current_user.id)
        
        trend_data = await realtime_service.get_position_trend_data(position_id, period)
        
        return success_response(
            data=trend_data,
            message="获取持仓趋势数据成功"
        )
    except Exception as e:
        return error_response(message=str(e))

# ==================== 持仓操作端点 ====================

@router.post("/{position_id}/close")
@require_permission(PermissionConstants.POSITION_MANAGE)
async def close_position(
    position_id: int,
    request: ClosePositionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """平仓操作"""
    operation_service = PositionOperationService(db)
    
    result = operation_service.close_position(
        position_id=position_id,
        user_id=current_user.id,
        close_type=request.close_type,
        close_price=request.close_price,
        close_quantity=request.close_quantity
    )
    
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('error'))
    
    return result


@router.post("/{position_id}/stop-loss")
@require_permission(PermissionConstants.POSITION_MANAGE)
async def set_stop_loss(
    position_id: int,
    request: StopLossRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """设置止损"""
    operation_service = PositionOperationService(db)
    
    result = operation_service.set_stop_loss(
        position_id=position_id,
        user_id=current_user.id,
        stop_price=request.stop_price,
        trigger_type=request.trigger_type
    )
    
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('error'))
    
    return result


@router.post("/{position_id}/take-profit")
@require_permission(PermissionConstants.POSITION_MANAGE)
async def set_take_profit(
    position_id: int,
    request: TakeProfitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """设置止盈"""
    operation_service = PositionOperationService(db)
    
    result = operation_service.set_take_profit(
        position_id=position_id,
        user_id=current_user.id,
        profit_price=request.profit_price,
        trigger_type=request.trigger_type
    )
    
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('error'))
    
    return result


@router.delete("/{position_id}/stop-loss")
@require_permission(PermissionConstants.POSITION_MANAGE)
async def cancel_stop_loss(
    position_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """取消止损"""
    operation_service = PositionOperationService(db)
    
    result = operation_service.cancel_stop_loss(
        position_id=position_id,
        user_id=current_user.id
    )
    
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('error'))
    
    return result


@router.delete("/{position_id}/take-profit")
@require_permission(PermissionConstants.POSITION_MANAGE)
async def cancel_take_profit(
    position_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """取消止盈"""
    operation_service = PositionOperationService(db)
    
    result = operation_service.cancel_take_profit(
        position_id=position_id,
        user_id=current_user.id
    )
    
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('error'))
    
    return result


# ==================== 风险管理端点 ====================

@router.get("/risk/concentration")
@require_permission(PermissionConstants.POSITION_READ)
async def check_concentration_risk(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """检查持仓集中度风险"""
    operation_service = PositionOperationService(db)
    
    result = operation_service.check_position_concentration_risk(current_user.id)
    
    if 'error' in result:
        raise HTTPException(status_code=400, detail=result['error'])
    
    return result


@router.get("/risk/alerts")
@require_permission(PermissionConstants.POSITION_READ)
async def get_risk_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取持仓风险预警"""
    operation_service = PositionOperationService(db)
    
    alerts = operation_service.get_position_risk_alerts(current_user.id)
    
    return {
        'alerts': alerts,
        'alert_count': len(alerts),
        'high_severity_count': len([a for a in alerts if a.get('severity') == 'HIGH']),
        'generated_at': datetime.now().isoformat()
    }


# ==================== 数据导出端点 ====================

@router.get("/export")
@require_permission(PermissionConstants.POSITION_READ)
async def export_positions(
    format: str = Query('csv', description="导出格式: csv, json"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """导出持仓数据"""
    operation_service = PositionOperationService(db)
    
    result = operation_service.export_position_data(
        user_id=current_user.id,
        export_format=format,
        start_date=start_date,
        end_date=end_date
    )
    
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('error'))
    
    from fastapi.responses import Response
    
    if format.lower() == 'csv':
        media_type = 'text/csv'
    elif format.lower() == 'json':
        media_type = 'application/json'
    else:
        media_type = 'text/plain'
    
    return Response(
        content=result['file_content'],
        media_type=media_type,
        headers={
            'Content-Disposition': f'attachment; filename="{result["file_name"]}"'
        }
    )


@router.get("/{position_id}/history")
@require_permission(PermissionConstants.POSITION_READ)
async def get_position_history(
    position_id: int,
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取持仓历史记录"""
    operation_service = PositionOperationService(db)
    
    result = operation_service.get_position_history(
        position_id=position_id,
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )
    
    if 'error' in result:
        raise HTTPException(status_code=400, detail=result['error'])
    
    return result