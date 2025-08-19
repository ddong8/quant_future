"""
技术分析 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
import logging

from ...services.technical_analysis_service import technical_analysis_service
from ...core.dependencies import get_current_user
from ...models import User

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/indicators/{symbol}")
async def get_technical_indicators(
    symbol: str,
    period: str = Query("1d", description="时间周期"),
    limit: int = Query(100, description="数据长度"),
    current_user: User = Depends(get_current_user)
):
    """获取技术指标"""
    try:
        result = await technical_analysis_service.get_technical_indicators(
            symbol=symbol,
            period=period,
            limit=limit
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "success": True,
            "data": result,
            "message": "获取技术指标成功"
        }
        
    except Exception as e:
        logger.error(f"获取技术指标失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/multi-timeframe/{symbol}")
async def get_multi_timeframe_analysis(
    symbol: str,
    current_user: User = Depends(get_current_user)
):
    """获取多周期技术分析"""
    try:
        result = await technical_analysis_service.get_multi_timeframe_analysis(symbol)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "success": True,
            "data": result,
            "message": "获取多周期分析成功"
        }
        
    except Exception as e:
        logger.error(f"获取多周期分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/signals/{symbol}")
async def get_trading_signals(
    symbol: str,
    period: str = Query("1d", description="时间周期"),
    current_user: User = Depends(get_current_user)
):
    """获取交易信号"""
    try:
        indicators = await technical_analysis_service.get_technical_indicators(
            symbol=symbol,
            period=period,
            limit=50
        )
        
        if "error" in indicators:
            raise HTTPException(status_code=400, detail=indicators["error"])
        
        return {
            "success": True,
            "data": {
                "symbol": symbol,
                "period": period,
                "signals": indicators.get("signals", {}),
                "latest_values": indicators.get("latest_values", {}),
                "timestamp": indicators.get("timestamp")
            },
            "message": "获取交易信号成功"
        }
        
    except Exception as e:
        logger.error(f"获取交易信号失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))