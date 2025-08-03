"""
技术分析API接口
"""
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...models.user import User
from ...services.technical_analysis_service import TechnicalAnalysisService

router = APIRouter()

@router.get("/kline/{symbol_code}")
async def get_kline_data(
    symbol_code: str,
    interval: str = Query('1d', description="时间间隔"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    limit: int = Query(500, ge=1, le=2000, description="数量限制"),
    db: Session = Depends(get_db)
):
    """获取K线数据"""
    try:
        service = TechnicalAnalysisService(db)
        
        # 如果没有指定时间范围，默认获取最近的数据
        if not start_time and not end_time:
            end_time = datetime.now()
            if interval == '1m':
                start_time = end_time - timedelta(days=1)
            elif interval == '5m':
                start_time = end_time - timedelta(days=5)
            elif interval == '15m':
                start_time = end_time - timedelta(days=15)
            elif interval == '1h':
                start_time = end_time - timedelta(days=30)
            elif interval == '1d':
                start_time = end_time - timedelta(days=365)
            else:
                start_time = end_time - timedelta(days=90)
        
        kline_data = service.get_kline_data(
            symbol_code=symbol_code,
            interval=interval,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )
        
        return {
            'symbol': symbol_code,
            'interval': interval,
            'data': kline_data,
            'count': len(kline_data)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取K线数据失败: {str(e)}")

@router.get("/indicators/{symbol_code}")
async def get_technical_indicators(
    symbol_code: str,
    interval: str = Query('1d', description="时间间隔"),
    indicators: Optional[str] = Query(None, description="指标列表，逗号分隔"),
    limit: int = Query(500, ge=1, le=2000, description="数量限制"),
    db: Session = Depends(get_db)
):
    """获取技术指标数据"""
    try:
        service = TechnicalAnalysisService(db)
        
        # 解析指标列表
        indicator_list = None
        if indicators:
            indicator_list = [ind.strip() for ind in indicators.split(',')]
        
        result = service.get_technical_indicators(
            symbol_code=symbol_code,
            interval=interval,
            indicators=indicator_list,
            limit=limit
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="未找到数据")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取技术指标失败: {str(e)}")

@router.get("/indicators/ma/{symbol_code}")
async def get_moving_average(
    symbol_code: str,
    period: int = Query(20, ge=1, le=200, description="周期"),
    interval: str = Query('1d', description="时间间隔"),
    price_type: str = Query('close', description="价格类型"),
    limit: int = Query(500, ge=1, le=2000, description="数量限制"),
    db: Session = Depends(get_db)
):
    """获取移动平均线"""
    try:
        service = TechnicalAnalysisService(db)
        
        # 获取K线数据
        kline_data = service.get_kline_data(symbol_code, interval, limit=limit)
        if not kline_data:
            raise HTTPException(status_code=404, detail="未找到K线数据")
        
        # 计算移动平均线
        ma_values = service.calculate_ma(kline_data, period, price_type)
        
        return {
            'symbol': symbol_code,
            'indicator': 'MA',
            'period': period,
            'price_type': price_type,
            'data': ma_values
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"计算移动平均线失败: {str(e)}")

@router.get("/indicators/bollinger/{symbol_code}")
async def get_bollinger_bands(
    symbol_code: str,
    period: int = Query(20, ge=1, le=200, description="周期"),
    std_dev: float = Query(2.0, ge=0.1, le=5.0, description="标准差倍数"),
    interval: str = Query('1d', description="时间间隔"),
    price_type: str = Query('close', description="价格类型"),
    limit: int = Query(500, ge=1, le=2000, description="数量限制"),
    db: Session = Depends(get_db)
):
    """获取布林带"""
    try:
        service = TechnicalAnalysisService(db)
        
        # 获取K线数据
        kline_data = service.get_kline_data(symbol_code, interval, limit=limit)
        if not kline_data:
            raise HTTPException(status_code=404, detail="未找到K线数据")
        
        # 计算布林带
        bollinger_data = service.calculate_bollinger_bands(kline_data, period, std_dev, price_type)
        
        return {
            'symbol': symbol_code,
            'indicator': 'BOLLINGER',
            'period': period,
            'std_dev': std_dev,
            'price_type': price_type,
            'data': bollinger_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"计算布林带失败: {str(e)}")

@router.get("/indicators/rsi/{symbol_code}")
async def get_rsi(
    symbol_code: str,
    period: int = Query(14, ge=1, le=100, description="周期"),
    interval: str = Query('1d', description="时间间隔"),
    price_type: str = Query('close', description="价格类型"),
    limit: int = Query(500, ge=1, le=2000, description="数量限制"),
    db: Session = Depends(get_db)
):
    """获取RSI指标"""
    try:
        service = TechnicalAnalysisService(db)
        
        # 获取K线数据
        kline_data = service.get_kline_data(symbol_code, interval, limit=limit)
        if not kline_data:
            raise HTTPException(status_code=404, detail="未找到K线数据")
        
        # 计算RSI
        rsi_values = service.calculate_rsi(kline_data, period, price_type)
        
        return {
            'symbol': symbol_code,
            'indicator': 'RSI',
            'period': period,
            'price_type': price_type,
            'data': rsi_values
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"计算RSI失败: {str(e)}")

@router.get("/indicators/macd/{symbol_code}")
async def get_macd(
    symbol_code: str,
    fast_period: int = Query(12, ge=1, le=100, description="快线周期"),
    slow_period: int = Query(26, ge=1, le=200, description="慢线周期"),
    signal_period: int = Query(9, ge=1, le=50, description="信号线周期"),
    interval: str = Query('1d', description="时间间隔"),
    price_type: str = Query('close', description="价格类型"),
    limit: int = Query(500, ge=1, le=2000, description="数量限制"),
    db: Session = Depends(get_db)
):
    """获取MACD指标"""
    try:
        service = TechnicalAnalysisService(db)
        
        # 获取K线数据
        kline_data = service.get_kline_data(symbol_code, interval, limit=limit)
        if not kline_data:
            raise HTTPException(status_code=404, detail="未找到K线数据")
        
        # 计算MACD
        macd_data = service.calculate_macd(kline_data, fast_period, slow_period, signal_period, price_type)
        
        return {
            'symbol': symbol_code,
            'indicator': 'MACD',
            'fast_period': fast_period,
            'slow_period': slow_period,
            'signal_period': signal_period,
            'price_type': price_type,
            'data': macd_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"计算MACD失败: {str(e)}")

@router.post("/chart-config")
async def save_chart_config(
    config_name: str,
    config_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """保存图表配置"""
    try:
        service = TechnicalAnalysisService(db)
        
        success = service.save_chart_config(
            user_id=current_user.id,
            config_name=config_name,
            config_data=config_data
        )
        
        if success:
            return {"message": "图表配置保存成功"}
        else:
            raise HTTPException(status_code=500, detail="保存图表配置失败")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存图表配置失败: {str(e)}")

@router.get("/chart-configs")
async def get_chart_configs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户的图表配置"""
    try:
        service = TechnicalAnalysisService(db)
        
        configs = service.get_chart_configs(current_user.id)
        
        return {
            'configs': configs,
            'count': len(configs)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取图表配置失败: {str(e)}")