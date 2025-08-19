"""
简化回测API路由
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from ...core.dependencies import get_current_user, require_trader_or_admin
from ...core.response import success_response, error_response
from ...services.simple_backtest_engine import simple_backtest_engine
from ...models import User

router = APIRouter()


class BacktestCreateRequest(BaseModel):
    """创建回测请求"""
    strategy_name: str
    strategy_code: str
    symbols: List[str]
    start_date: datetime
    end_date: datetime
    initial_capital: float = 1000000.0
    commission_rate: float = 0.0001


class BacktestRunRequest(BaseModel):
    """运行回测请求"""
    backtest_id: str


@router.post("/create")
async def create_backtest(
    request: BacktestCreateRequest,
    current_user: User = Depends(require_trader_or_admin),
):
    """创建回测任务"""
    try:
        backtest_id = await simple_backtest_engine.create_backtest(
            strategy_code=request.strategy_code,
            symbols=request.symbols,
            start_date=request.start_date,
            end_date=request.end_date,
            initial_capital=request.initial_capital,
            commission_rate=request.commission_rate
        )
        
        return success_response(
            data={
                "backtest_id": backtest_id,
                "strategy_name": request.strategy_name,
                "symbols": request.symbols,
                "start_date": request.start_date.isoformat(),
                "end_date": request.end_date.isoformat(),
                "initial_capital": request.initial_capital
            },
            message="回测任务创建成功"
        )
        
    except Exception as e:
        return error_response(
            error_code="BACKTEST_CREATE_ERROR",
            message=f"创建回测任务失败: {str(e)}"
        )


@router.post("/run")
async def run_backtest(
    request: BacktestRunRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_trader_or_admin),
):
    """运行回测（异步）"""
    try:
        # 在后台任务中运行回测
        background_tasks.add_task(
            simple_backtest_engine.run_backtest,
            request.backtest_id
        )
        
        return success_response(
            data={"backtest_id": request.backtest_id},
            message="回测任务已启动，正在后台运行"
        )
        
    except Exception as e:
        return error_response(
            error_code="BACKTEST_RUN_ERROR",
            message=f"启动回测失败: {str(e)}"
        )


@router.post("/quick-run")
async def quick_run_backtest(
    request: BacktestCreateRequest,
    current_user: User = Depends(require_trader_or_admin),
):
    """快速回测（创建并立即运行）"""
    try:
        # 创建回测任务
        backtest_id = await simple_backtest_engine.create_backtest(
            strategy_code=request.strategy_code,
            symbols=request.symbols,
            start_date=request.start_date,
            end_date=request.end_date,
            initial_capital=request.initial_capital,
            commission_rate=request.commission_rate
        )
        
        # 立即运行回测
        results = await simple_backtest_engine.run_backtest(backtest_id)
        
        return success_response(
            data={
                "backtest_id": backtest_id,
                "results": results
            },
            message="快速回测完成"
        )
        
    except Exception as e:
        return error_response(
            error_code="QUICK_BACKTEST_ERROR",
            message=f"快速回测失败: {str(e)}"
        )


@router.get("/status/{backtest_id}")
async def get_backtest_status(
    backtest_id: str,
    current_user: User = Depends(require_trader_or_admin),
):
    """获取回测状态"""
    try:
        status = await simple_backtest_engine.get_backtest_status(backtest_id)
        
        return success_response(
            data=status,
            message="获取回测状态成功"
        )
        
    except Exception as e:
        return error_response(
            error_code="BACKTEST_STATUS_ERROR",
            message=f"获取回测状态失败: {str(e)}"
        )


@router.get("/list")
async def list_backtests(
    current_user: User = Depends(require_trader_or_admin),
):
    """获取回测列表"""
    try:
        backtests = await simple_backtest_engine.list_backtests()
        
        return success_response(
            data=backtests,
            message=f"获取到{len(backtests)}个回测任务"
        )
        
    except Exception as e:
        return error_response(
            error_code="BACKTEST_LIST_ERROR",
            message=f"获取回测列表失败: {str(e)}"
        )


@router.get("/results/{backtest_id}")
async def get_backtest_results(
    backtest_id: str,
    current_user: User = Depends(require_trader_or_admin),
):
    """获取回测结果"""
    try:
        status = await simple_backtest_engine.get_backtest_status(backtest_id)
        
        if status["status"] != "COMPLETED":
            return success_response(
                data={"status": status["status"], "progress": status.get("progress", 0)},
                message=f"回测尚未完成，当前状态: {status['status']}"
            )
        
        return success_response(
            data=status["results"],
            message="获取回测结果成功"
        )
        
    except Exception as e:
        return error_response(
            error_code="BACKTEST_RESULTS_ERROR",
            message=f"获取回测结果失败: {str(e)}"
        )


@router.post("/demo")
async def demo_backtest(
    current_user: User = Depends(require_trader_or_admin),
):
    """演示回测（使用预设参数）"""
    try:
        # 使用预设参数进行演示回测
        demo_request = BacktestCreateRequest(
            strategy_name="双均线策略演示",
            strategy_code="# 双均线策略\n# 短期均线上穿长期均线时买入\n# 短期均线下穿长期均线时卖出",
            symbols=["SHFE.cu2401", "DCE.i2401"],
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 6, 30),
            initial_capital=1000000.0,
            commission_rate=0.0001
        )
        
        # 创建并运行回测
        backtest_id = await simple_backtest_engine.create_backtest(
            strategy_code=demo_request.strategy_code,
            symbols=demo_request.symbols,
            start_date=demo_request.start_date,
            end_date=demo_request.end_date,
            initial_capital=demo_request.initial_capital,
            commission_rate=demo_request.commission_rate
        )
        
        # 运行回测
        results = await simple_backtest_engine.run_backtest(backtest_id)
        
        return success_response(
            data={
                "backtest_id": backtest_id,
                "strategy_name": demo_request.strategy_name,
                "results": results
            },
            message="演示回测完成"
        )
        
    except Exception as e:
        return error_response(
            error_code="DEMO_BACKTEST_ERROR",
            message=f"演示回测失败: {str(e)}"
        )