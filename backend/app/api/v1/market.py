"""
市场数据API路由
"""
from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from typing import List, Optional
import json
import asyncio

from ...core.dependencies import get_current_user, require_trader_or_admin
from ...core.response import success_response
from ...services.market_service import market_service
from ...schemas.market import (
    InstrumentInfo,
    QuoteData,
    KlineData,
    KlineRequest,
    QuoteSubscription,
    MarketDataFilter,
    TradingTimeInfo,
    MarketStatus,
    ConnectionStatus,
    MarketDataStats,
)
from ...models import User

router = APIRouter()


@router.get("/status", response_model=ConnectionStatus)
async def get_connection_status():
    """获取市场数据连接状态"""
    status = await market_service.get_connection_status()
    
    return success_response(
        data=status.dict(),
        message="获取连接状态成功"
    )


@router.get("/instruments", response_model=List[InstrumentInfo])
async def get_instruments(
    exchange: Optional[str] = Query(None, description="交易所代码"),
    product_id: Optional[str] = Query(None, description="品种代码"),
    expired: Optional[bool] = Query(None, description="是否已过期"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    current_user: User = Depends(require_trader_or_admin),
):
    """获取合约信息列表"""
    filter_params = MarketDataFilter(
        exchange=exchange,
        product_id=product_id,
        expired=expired,
        keyword=keyword,
    )
    
    instruments = await market_service.get_instruments(filter_params)
    
    return success_response(
        data=[instrument.dict() for instrument in instruments],
        message=f"获取到{len(instruments)}个合约信息"
    )


@router.get("/instruments/{symbol}", response_model=InstrumentInfo)
async def get_instrument_by_symbol(
    symbol: str,
    current_user: User = Depends(require_trader_or_admin),
):
    """根据合约代码获取合约信息"""
    instrument = await market_service.get_instrument_by_symbol(symbol)
    
    if not instrument:
        return success_response(
            data=None,
            message="合约不存在"
        )
    
    return success_response(
        data=instrument.dict(),
        message="获取合约信息成功"
    )


@router.get("/quotes/{symbol}", response_model=QuoteData)
async def get_quote(
    symbol: str,
    current_user: User = Depends(require_trader_or_admin),
):
    """获取实时行情"""
    quote = await market_service.get_quote(symbol)
    
    if not quote:
        return success_response(
            data=None,
            message="获取行情失败"
        )
    
    return success_response(
        data=quote.dict(),
        message="获取行情成功"
    )


@router.post("/quotes/batch")
async def get_quotes_batch(
    symbols: List[str],
    current_user: User = Depends(require_trader_or_admin),
):
    """批量获取行情"""
    quotes = await market_service.get_quotes(symbols)
    
    return success_response(
        data={symbol: quote.dict() for symbol, quote in quotes.items()},
        message=f"获取{len(quotes)}个合约行情成功"
    )


@router.get("/klines/{symbol}", response_model=List[KlineData])
async def get_klines(
    symbol: str,
    duration: int = Query(60, description="K线周期（秒）"),
    data_length: int = Query(200, description="数据长度"),
    current_user: User = Depends(require_trader_or_admin),
):
    """获取K线数据"""
    request = KlineRequest(
        symbol=symbol,
        duration=duration,
        data_length=data_length,
    )
    
    klines = await market_service.get_klines(request)
    
    return success_response(
        data=[kline.dict() for kline in klines],
        message=f"获取K线数据成功，共{len(klines)}条"
    )


@router.post("/subscribe")
async def subscribe_quotes(
    subscription: QuoteSubscription,
    current_user: User = Depends(require_trader_or_admin),
):
    """订阅行情"""
    success = await market_service.subscribe_quotes(subscription)
    
    if success:
        return success_response(
            data={"symbols": subscription.symbols},
            message="订阅行情成功"
        )
    else:
        return success_response(
            data=None,
            message="订阅行情失败"
        )


@router.post("/unsubscribe")
async def unsubscribe_quotes(
    symbols: List[str],
    current_user: User = Depends(require_trader_or_admin),
):
    """取消订阅行情"""
    success = await market_service.unsubscribe_quotes(symbols)
    
    if success:
        return success_response(
            data={"symbols": symbols},
            message="取消订阅成功"
        )
    else:
        return success_response(
            data=None,
            message="取消订阅失败"
        )


@router.get("/subscriptions")
async def get_subscriptions(
    current_user: User = Depends(require_trader_or_admin),
):
    """获取已订阅的合约列表"""
    symbols = await market_service.get_subscribed_symbols()
    
    return success_response(
        data={"symbols": symbols},
        message=f"当前订阅{len(symbols)}个合约"
    )


@router.get("/trading-time/{symbol}", response_model=TradingTimeInfo)
async def get_trading_time_info(
    symbol: str,
    current_user: User = Depends(require_trader_or_admin),
):
    """获取交易时间信息"""
    trading_time_info = await market_service.get_trading_time_info(symbol)
    
    if not trading_time_info:
        return success_response(
            data=None,
            message="获取交易时间信息失败"
        )
    
    return success_response(
        data=trading_time_info.dict(),
        message="获取交易时间信息成功"
    )


@router.get("/market-status", response_model=MarketStatus)
async def get_market_status():
    """获取市场状态"""
    status = await market_service.get_market_status()
    
    return success_response(
        data=status.dict(),
        message="获取市场状态成功"
    )


@router.get("/stats", response_model=MarketDataStats)
async def get_market_stats(
    current_user: User = Depends(require_trader_or_admin),
):
    """获取市场数据统计"""
    stats = await market_service.get_market_stats()
    
    return success_response(
        data=stats.dict(),
        message="获取市场数据统计成功"
    )


# WebSocket连接管理
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # 连接已断开，移除
                self.disconnect(connection)


manager = ConnectionManager()


@router.websocket("/ws/quotes")
async def websocket_quotes(websocket: WebSocket):
    """WebSocket实时行情推送"""
    await manager.connect(websocket)
    
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("action") == "subscribe":
                symbols = message.get("symbols", [])
                if symbols:
                    subscription = QuoteSubscription(symbols=symbols)
                    await market_service.subscribe_quotes(subscription)
                    
                    # 发送订阅确认
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "subscription_confirmed",
                            "symbols": symbols
                        }),
                        websocket
                    )
                    
                    # 开始推送行情数据
                    asyncio.create_task(
                        push_quotes_to_client(websocket, symbols)
                    )
            
            elif message.get("action") == "unsubscribe":
                symbols = message.get("symbols", [])
                if symbols:
                    await market_service.unsubscribe_quotes(symbols)
                    
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "unsubscription_confirmed",
                            "symbols": symbols
                        }),
                        websocket
                    )
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket错误: {e}")
        manager.disconnect(websocket)


async def push_quotes_to_client(websocket: WebSocket, symbols: List[str]):
    """向客户端推送行情数据"""
    try:
        while websocket in manager.active_connections:
            quotes = await market_service.get_quotes(symbols)
            
            if quotes:
                message = {
                    "type": "quotes_update",
                    "data": {symbol: quote.dict() for symbol, quote in quotes.items()}
                }
                
                await manager.send_personal_message(
                    json.dumps(message, default=str),
                    websocket
                )
            
            await asyncio.sleep(1)  # 每秒推送一次
            
    except Exception as e:
        logger.error(f"推送行情数据失败: {e}")
        manager.disconnect(websocket)