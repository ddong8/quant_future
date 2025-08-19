"""
InfluxDB 相关API端点
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ...core.dependencies import get_current_user
from ...services.influxdb_market_service import influxdb_market_service
from ...core.influxdb import influx_manager
from ...schemas.base import BaseResponse

router = APIRouter()


class QuoteDataRequest(BaseModel):
    """行情数据请求"""
    symbol: str
    last_price: float
    bid_price: Optional[float] = None
    ask_price: Optional[float] = None
    volume: Optional[int] = None
    open_interest: Optional[int] = None
    datetime: Optional[datetime] = None


class KlineDataRequest(BaseModel):
    """K线数据请求"""
    symbol: str
    period: str = "1m"
    open: float
    high: float
    low: float
    close: float
    volume: Optional[int] = None
    datetime: Optional[datetime] = None


class QueryRequest(BaseModel):
    """查询请求"""
    symbol: str
    start_time: datetime
    end_time: Optional[datetime] = None
    limit: int = 1000


@router.get("/health", summary="InfluxDB健康检查")
async def influxdb_health():
    """检查InfluxDB连接状态"""
    try:
        # 尝试ping InfluxDB
        health = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: influx_manager.client.ping()
        )
        
        return BaseResponse(
            success=True,
            data={
                "status": "healthy",
                "message": "InfluxDB连接正常",
                "health": health
            }
        )
    except Exception as e:
        return BaseResponse(
            success=False,
            message=f"InfluxDB连接失败: {str(e)}"
        )


@router.post("/quotes", summary="存储行情数据")
async def store_quote(
    request: QuoteDataRequest,
    current_user = Depends(get_current_user)
):
    """存储单个行情数据到InfluxDB"""
    try:
        quote_data = {
            "last_price": request.last_price,
            "bid_price": request.bid_price or 0,
            "ask_price": request.ask_price or 0,
            "volume": request.volume or 0,
            "open_interest": request.open_interest or 0,
            "datetime": request.datetime or datetime.utcnow()
        }
        
        success = await influxdb_market_service.store_quote(
            request.symbol, 
            quote_data
        )
        
        if success:
            return BaseResponse(
                success=True,
                message=f"行情数据存储成功: {request.symbol}"
            )
        else:
            raise HTTPException(status_code=500, detail="行情数据存储失败")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"存储行情数据失败: {str(e)}")


@router.post("/klines", summary="存储K线数据")
async def store_kline(
    request: KlineDataRequest,
    current_user = Depends(get_current_user)
):
    """存储单个K线数据到InfluxDB"""
    try:
        kline_data = {
            "open": request.open,
            "high": request.high,
            "low": request.low,
            "close": request.close,
            "volume": request.volume or 0,
            "datetime": request.datetime or datetime.utcnow()
        }
        
        success = await influxdb_market_service.store_kline(
            request.symbol,
            kline_data,
            request.period
        )
        
        if success:
            return BaseResponse(
                success=True,
                message=f"K线数据存储成功: {request.symbol} {request.period}"
            )
        else:
            raise HTTPException(status_code=500, detail="K线数据存储失败")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"存储K线数据失败: {str(e)}")


@router.get("/quotes/{symbol}", summary="查询行情数据")
async def query_quotes(
    symbol: str,
    start_time: datetime = Query(..., description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    limit: int = Query(1000, description="限制条数"),
    current_user = Depends(get_current_user)
):
    """查询指定合约的行情数据"""
    try:
        quotes = await influxdb_market_service.query_quotes(
            symbol, start_time, end_time, limit
        )
        
        return BaseResponse(
            success=True,
            data={
                "symbol": symbol,
                "count": len(quotes),
                "quotes": quotes
            },
            message=f"查询到 {len(quotes)} 条行情数据"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询行情数据失败: {str(e)}")


@router.get("/klines/{symbol}", summary="查询K线数据")
async def query_klines(
    symbol: str,
    period: str = Query("1m", description="周期"),
    start_time: datetime = Query(..., description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    limit: int = Query(1000, description="限制条数"),
    current_user = Depends(get_current_user)
):
    """查询指定合约的K线数据"""
    try:
        klines = await influxdb_market_service.query_klines(
            symbol, period, start_time, end_time, limit
        )
        
        return BaseResponse(
            success=True,
            data={
                "symbol": symbol,
                "period": period,
                "count": len(klines),
                "klines": klines
            },
            message=f"查询到 {len(klines)} 条K线数据"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询K线数据失败: {str(e)}")


@router.get("/quotes/{symbol}/latest", summary="获取最新行情")
async def get_latest_quote(
    symbol: str,
    current_user = Depends(get_current_user)
):
    """获取指定合约的最新行情"""
    try:
        quote = await influxdb_market_service.get_latest_quote(symbol)
        
        if quote:
            return BaseResponse(
                success=True,
                data=quote,
                message=f"获取最新行情成功: {symbol}"
            )
        else:
            return BaseResponse(
                success=False,
                message=f"未找到行情数据: {symbol}"
            )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取最新行情失败: {str(e)}")


@router.post("/test-data", summary="生成测试数据")
async def generate_test_data(
    symbol: str = Query("SHFE.cu2601", description="合约代码"),
    count: int = Query(100, description="生成数量"),
    current_user = Depends(get_current_user)
):
    """生成测试数据到InfluxDB"""
    try:
        import random
        from datetime import timedelta
        
        # 生成测试行情数据
        base_price = 71500
        base_time = datetime.utcnow() - timedelta(hours=1)
        
        quotes = []
        for i in range(count):
            price = base_price + random.randint(-1000, 1000)
            quote_data = {
                "symbol": symbol,
                "data": {
                    "last_price": price,
                    "bid_price": price - random.randint(1, 10),
                    "ask_price": price + random.randint(1, 10),
                    "volume": random.randint(1000, 10000),
                    "open_interest": random.randint(5000, 50000),
                    "datetime": base_time + timedelta(seconds=i * 60)
                }
            }
            quotes.append(quote_data)
        
        # 批量存储
        success_count = await influxdb_market_service.store_quotes_batch(quotes)
        
        return BaseResponse(
            success=True,
            data={
                "symbol": symbol,
                "generated": count,
                "stored": success_count
            },
            message=f"测试数据生成完成: {success_count}/{count}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成测试数据失败: {str(e)}")


@router.delete("/data/{symbol}", summary="删除数据")
async def delete_data(
    symbol: str,
    measurement: str = Query("quotes", description="测量名称"),
    current_user = Depends(get_current_user)
):
    """删除指定合约的数据"""
    try:
        from ...core.config import settings
        
        # 构建删除查询
        delete_query = f'''
            from(bucket: "{settings.INFLUXDB_BUCKET}")
            |> range(start: 1970-01-01T00:00:00Z)
            |> filter(fn: (r) => r._measurement == "{measurement}")
            |> filter(fn: (r) => r.symbol == "{symbol}")
            |> drop()
        '''
        
        # 执行删除
        await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: influx_manager.client.delete_api().delete(
                start="1970-01-01T00:00:00Z",
                stop=datetime.utcnow(),
                predicate=f'_measurement="{measurement}" AND symbol="{symbol}"',
                bucket=settings.INFLUXDB_BUCKET
            )
        )
        
        return BaseResponse(
            success=True,
            message=f"数据删除成功: {symbol} {measurement}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除数据失败: {str(e)}")


@router.post("/flush", summary="刷新批处理")
async def flush_batches(
    current_user = Depends(get_current_user)
):
    """手动刷新所有批处理数据"""
    try:
        await influxdb_market_service.flush_all_batches()
        
        return BaseResponse(
            success=True,
            message="批处理数据刷新完成"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"刷新批处理失败: {str(e)}")


# 导入asyncio
import asyncio