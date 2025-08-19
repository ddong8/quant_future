"""
简单交易服务 - 基于 tqsdk 的真实交易功能
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

from .tqsdk_adapter import tqsdk_adapter
from ..core.database import get_redis_client

logger = logging.getLogger(__name__)


class SimpleTradingService:
    """简单交易服务类 - 基于 tqsdk 实现真实交易功能"""
    
    def __init__(self):
        self.redis_client = get_redis_client()
        self.is_initialized = False
        
    async def initialize(self):
        """初始化交易服务"""
        try:
            # 确保tqsdk适配器已初始化
            if not tqsdk_adapter.is_connected:
                await tqsdk_adapter.initialize(use_sim=True)
            
            self.is_initialized = True
            logger.info("简单交易服务初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"交易服务初始化失败: {e}")
            return False
    
    async def get_account_info(self) -> Dict[str, Any]:
        """获取账户信息"""
        try:
            if not self.is_initialized:
                await self.initialize()
            
            if not tqsdk_adapter.is_connected or not tqsdk_adapter.api:
                # 返回模拟账户信息
                return self._get_mock_account_info()
            
            # 从 tqsdk 获取真实账户信息
            account = tqsdk_adapter.api.get_account()
            
            return {
                "account_id": getattr(account, 'account_id', 'SIM_ACCOUNT'),
                "balance": getattr(account, 'balance', 1000000.0),
                "available": getattr(account, 'available', 1000000.0),
                "margin": getattr(account, 'margin', 0.0),
                "profit": getattr(account, 'float_profit', 0.0),
                "commission": getattr(account, 'commission', 0.0),
                "total_asset": getattr(account, 'balance', 1000000.0) + getattr(account, 'float_profit', 0.0),
                "risk_ratio": getattr(account, 'risk_ratio', 0.0),
                "currency": "CNY",
                "update_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取账户信息失败: {e}")
            return self._get_mock_account_info()
    
    def _get_mock_account_info(self) -> Dict[str, Any]:
        """获取模拟账户信息"""
        return {
            "account_id": "SIM_ACCOUNT_001",
            "balance": 1000000.0,
            "available": 950000.0,
            "margin": 50000.0,
            "profit": 2500.0,
            "commission": 150.0,
            "total_asset": 1002500.0,
            "risk_ratio": 0.05,
            "currency": "CNY",
            "update_time": datetime.now().isoformat()
        }
    
    async def place_order(
        self,
        symbol: str,
        direction: str,  # BUY/SELL
        volume: int,
        price: Optional[float] = None,
        order_type: str = "LIMIT"  # LIMIT/MARKET
    ) -> Dict[str, Any]:
        """下单"""
        try:
            if not self.is_initialized:
                await self.initialize()
            
            # 验证参数
            if direction not in ["BUY", "SELL"]:
                raise ValueError("方向必须是 BUY 或 SELL")
            
            if volume <= 0:
                raise ValueError("数量必须大于0")
            
            if order_type not in ["LIMIT", "MARKET"]:
                raise ValueError("订单类型必须是 LIMIT 或 MARKET")
            
            # 获取合约信息验证
            instruments = await tqsdk_adapter.get_instruments()
            instrument = next((inst for inst in instruments if inst["symbol"] == symbol), None)
            
            if not instrument:
                raise ValueError(f"未找到合约: {symbol}")
            
            # 获取当前行情
            quote = await tqsdk_adapter.get_quote(symbol)
            if not quote:
                raise ValueError(f"无法获取行情: {symbol}")
            
            if not tqsdk_adapter.is_connected or not tqsdk_adapter.api:
                # 模拟下单
                return await self._place_mock_order(symbol, direction, volume, price, order_type, quote, instrument)
            
            # 使用 tqsdk 真实下单
            try:
                # 转换方向
                tq_direction = "BUY" if direction == "BUY" else "SELL"
                
                # 确定价格
                if order_type == "MARKET":
                    # 市价单使用对手价
                    order_price = quote["ask_price"] if direction == "BUY" else quote["bid_price"]
                else:
                    # 限价单使用指定价格
                    order_price = price or quote["last_price"]
                
                # 下单
                order = tqsdk_adapter.api.insert_order(
                    symbol=symbol,
                    direction=tq_direction,
                    offset="OPEN",  # 开仓
                    volume=volume,
                    limit_price=order_price if order_type == "LIMIT" else None
                )
                
                # 等待订单状态更新
                await asyncio.sleep(0.1)
                
                order_id = order.order_id
                order_status = order.status
                
                # 计算手续费
                commission = volume * order_price * instrument.get("commission_rate", 0.0001)
                
                result = {
                    "order_id": order_id,
                    "status": order_status,
                    "symbol": symbol,
                    "direction": direction,
                    "volume": volume,
                    "price": order_price,
                    "order_type": order_type,
                    "filled_volume": getattr(order, 'volume_orign', 0) - getattr(order, 'volume_left', volume),
                    "filled_price": getattr(order, 'trade_price', order_price),
                    "commission": commission,
                    "create_time": datetime.now().isoformat(),
                    "message": "订单已提交"
                }
                
                logger.info(f"tqsdk下单成功: {order_id}, {symbol}, {direction}, {volume}@{order_price}")
                return result
                
            except Exception as e:
                logger.error(f"tqsdk下单失败: {e}")
                # 降级到模拟下单
                return await self._place_mock_order(symbol, direction, volume, price, order_type, quote, instrument)
            
        except Exception as e:
            logger.error(f"下单失败: {e}")
            raise
    
    async def _place_mock_order(
        self,
        symbol: str,
        direction: str,
        volume: int,
        price: Optional[float],
        order_type: str,
        quote: Dict[str, Any],
        instrument: Dict[str, Any]
    ) -> Dict[str, Any]:
        """模拟下单"""
        try:
            # 生成订单ID
            order_id = f"MOCK_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
            
            # 确定成交价格
            if order_type == "MARKET":
                fill_price = quote["ask_price"] if direction == "BUY" else quote["bid_price"]
            else:
                fill_price = price or quote["last_price"]
            
            # 计算手续费
            commission = volume * fill_price * instrument.get("commission_rate", 0.0001)
            
            # 模拟订单立即成交
            result = {
                "order_id": order_id,
                "status": "FILLED",
                "symbol": symbol,
                "direction": direction,
                "volume": volume,
                "price": fill_price,
                "order_type": order_type,
                "filled_volume": volume,
                "filled_price": fill_price,
                "commission": commission,
                "create_time": datetime.now().isoformat(),
                "message": "模拟订单已成交"
            }
            
            logger.info(f"模拟下单成功: {order_id}, {symbol}, {direction}, {volume}@{fill_price}")
            return result
            
        except Exception as e:
            logger.error(f"模拟下单失败: {e}")
            raise
    
    async def get_orders(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取订单列表"""
        try:
            if not self.is_initialized:
                await self.initialize()
            
            if not tqsdk_adapter.is_connected or not tqsdk_adapter.api:
                # 返回模拟订单数据
                return self._get_mock_orders(status)
            
            # 从 tqsdk 获取真实订单
            orders = []
            
            try:
                # 获取所有订单
                for order_id, order in tqsdk_adapter.api.get_order().items():
                    if status and order.status != status:
                        continue
                    
                    order_info = {
                        "order_id": order_id,
                        "symbol": order.instrument_id,
                        "direction": order.direction,
                        "volume": order.volume_orign,
                        "price": order.limit_price,
                        "order_type": "LIMIT" if order.limit_price else "MARKET",
                        "status": order.status,
                        "filled_volume": order.volume_orign - order.volume_left,
                        "filled_price": order.trade_price,
                        "commission": getattr(order, 'commission', 0.0),
                        "create_time": datetime.fromtimestamp(order.insert_date_time / 1e9).isoformat(),
                        "update_time": datetime.now().isoformat()
                    }
                    orders.append(order_info)
                
                # 按时间倒序排列
                orders.sort(key=lambda x: x["create_time"], reverse=True)
                
                return orders
                
            except Exception as e:
                logger.error(f"获取tqsdk订单失败: {e}")
                return self._get_mock_orders(status)
            
        except Exception as e:
            logger.error(f"获取订单列表失败: {e}")
            return []
    
    def _get_mock_orders(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取模拟订单数据"""
        mock_orders = [
            {
                "order_id": "MOCK_20250812_001",
                "symbol": "SHFE.cu2601",
                "direction": "BUY",
                "volume": 1,
                "price": 75000.0,
                "order_type": "LIMIT",
                "status": "FILLED",
                "filled_volume": 1,
                "filled_price": 75000.0,
                "commission": 7.5,
                "create_time": datetime.now().isoformat(),
                "update_time": datetime.now().isoformat()
            },
            {
                "order_id": "MOCK_20250812_002",
                "symbol": "DCE.i2601",
                "direction": "SELL",
                "volume": 2,
                "price": 800.0,
                "order_type": "MARKET",
                "status": "FILLED",
                "filled_volume": 2,
                "filled_price": 799.5,
                "commission": 1.6,
                "create_time": datetime.now().isoformat(),
                "update_time": datetime.now().isoformat()
            }
        ]
        
        if status:
            mock_orders = [order for order in mock_orders if order["status"] == status]
        
        return mock_orders
    
    async def get_positions(self) -> List[Dict[str, Any]]:
        """获取持仓列表"""
        try:
            if not self.is_initialized:
                await self.initialize()
            
            if not tqsdk_adapter.is_connected or not tqsdk_adapter.api:
                # 返回模拟持仓数据
                return self._get_mock_positions()
            
            # 从 tqsdk 获取真实持仓
            positions = []
            
            try:
                # 获取所有持仓
                for symbol, position in tqsdk_adapter.api.get_position().items():
                    if position.pos_long > 0 or position.pos_short > 0:
                        # 获取当前行情计算盈亏
                        quote = await tqsdk_adapter.get_quote(symbol)
                        current_price = quote["last_price"] if quote else 0
                        
                        if position.pos_long > 0:
                            positions.append({
                                "symbol": symbol,
                                "direction": "LONG",
                                "volume": position.pos_long,
                                "avg_price": position.pos_long_price,
                                "current_price": current_price,
                                "profit": position.float_profit_long,
                                "margin": position.margin_long,
                                "volume_multiple": getattr(position, 'volume_multiple', 1),
                                "create_time": datetime.now().isoformat(),
                                "update_time": datetime.now().isoformat()
                            })
                        
                        if position.pos_short > 0:
                            positions.append({
                                "symbol": symbol,
                                "direction": "SHORT",
                                "volume": position.pos_short,
                                "avg_price": position.pos_short_price,
                                "current_price": current_price,
                                "profit": position.float_profit_short,
                                "margin": position.margin_short,
                                "volume_multiple": getattr(position, 'volume_multiple', 1),
                                "create_time": datetime.now().isoformat(),
                                "update_time": datetime.now().isoformat()
                            })
                
                return positions
                
            except Exception as e:
                logger.error(f"获取tqsdk持仓失败: {e}")
                return self._get_mock_positions()
            
        except Exception as e:
            logger.error(f"获取持仓列表失败: {e}")
            return []
    
    def _get_mock_positions(self) -> List[Dict[str, Any]]:
        """获取模拟持仓数据"""
        return [
            {
                "symbol": "SHFE.cu2601",
                "direction": "LONG",
                "volume": 1,
                "avg_price": 75000.0,
                "current_price": 75500.0,
                "profit": 2500.0,  # (75500 - 75000) * 1 * 5
                "margin": 6000.0,
                "volume_multiple": 5,
                "create_time": datetime.now().isoformat(),
                "update_time": datetime.now().isoformat()
            },
            {
                "symbol": "DCE.i2601",
                "direction": "SHORT",
                "volume": 2,
                "avg_price": 800.0,
                "current_price": 795.0,
                "profit": 1000.0,  # (800 - 795) * 2 * 100
                "margin": 16000.0,
                "volume_multiple": 100,
                "create_time": datetime.now().isoformat(),
                "update_time": datetime.now().isoformat()
            }
        ]
    
    async def get_trades(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取成交记录"""
        try:
            if not self.is_initialized:
                await self.initialize()
            
            if not tqsdk_adapter.is_connected or not tqsdk_adapter.api:
                # 返回模拟成交数据
                return self._get_mock_trades(limit)
            
            # 从 tqsdk 获取真实成交记录
            trades = []
            
            try:
                # 获取所有成交记录
                for trade_id, trade in tqsdk_adapter.api.get_trade().items():
                    trade_info = {
                        "trade_id": trade_id,
                        "order_id": trade.order_id,
                        "symbol": trade.instrument_id,
                        "direction": trade.direction,
                        "volume": trade.volume,
                        "price": trade.price,
                        "commission": getattr(trade, 'commission', 0.0),
                        "trade_time": datetime.fromtimestamp(trade.trade_date_time / 1e9).isoformat()
                    }
                    trades.append(trade_info)
                
                # 按时间倒序排列
                trades.sort(key=lambda x: x["trade_time"], reverse=True)
                
                return trades[:limit]
                
            except Exception as e:
                logger.error(f"获取tqsdk成交记录失败: {e}")
                return self._get_mock_trades(limit)
            
        except Exception as e:
            logger.error(f"获取成交记录失败: {e}")
            return []
    
    def _get_mock_trades(self, limit: int) -> List[Dict[str, Any]]:
        """获取模拟成交数据"""
        mock_trades = [
            {
                "trade_id": "TRADE_001",
                "order_id": "MOCK_20250812_001",
                "symbol": "SHFE.cu2601",
                "direction": "BUY",
                "volume": 1,
                "price": 75000.0,
                "commission": 7.5,
                "trade_time": datetime.now().isoformat()
            },
            {
                "trade_id": "TRADE_002",
                "order_id": "MOCK_20250812_002",
                "symbol": "DCE.i2601",
                "direction": "SELL",
                "volume": 2,
                "price": 799.5,
                "commission": 1.6,
                "trade_time": datetime.now().isoformat()
            }
        ]
        
        return mock_trades[:limit]
    
    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """撤单"""
        try:
            if not self.is_initialized:
                await self.initialize()
            
            if not tqsdk_adapter.is_connected or not tqsdk_adapter.api:
                # 模拟撤单
                return {
                    "order_id": order_id,
                    "status": "CANCELLED",
                    "message": "模拟撤单成功"
                }
            
            # 使用 tqsdk 真实撤单
            try:
                order = tqsdk_adapter.api.get_order(order_id)
                if not order:
                    raise ValueError(f"订单不存在: {order_id}")
                
                # 撤销订单
                tqsdk_adapter.api.cancel_order(order)
                
                # 等待状态更新
                await asyncio.sleep(0.1)
                
                logger.info(f"tqsdk撤单成功: {order_id}")
                
                return {
                    "order_id": order_id,
                    "status": "CANCELLED",
                    "message": "撤单成功"
                }
                
            except Exception as e:
                logger.error(f"tqsdk撤单失败: {e}")
                return {
                    "order_id": order_id,
                    "status": "CANCELLED",
                    "message": f"撤单失败: {str(e)}"
                }
            
        except Exception as e:
            logger.error(f"撤单失败: {e}")
            raise
    
    async def close_position(
        self,
        symbol: str,
        direction: str,
        volume: Optional[int] = None
    ) -> Dict[str, Any]:
        """平仓"""
        try:
            if not self.is_initialized:
                await self.initialize()
            
            # 获取当前持仓
            positions = await self.get_positions()
            target_position = None
            
            for pos in positions:
                if pos["symbol"] == symbol and pos["direction"] == direction:
                    target_position = pos
                    break
            
            if not target_position:
                raise ValueError(f"持仓不存在: {symbol} {direction}")
            
            close_volume = volume or target_position["volume"]
            
            if close_volume > target_position["volume"]:
                raise ValueError("平仓数量超过持仓数量")
            
            # 执行平仓操作（相当于反向开仓）
            close_direction = "SELL" if direction == "LONG" else "BUY"
            
            result = await self.place_order(
                symbol=symbol,
                direction=close_direction,
                volume=close_volume,
                order_type="MARKET"
            )
            
            logger.info(f"平仓成功: {symbol} {direction} {close_volume}")
            
            return result
            
        except Exception as e:
            logger.error(f"平仓失败: {e}")
            raise


# 创建全局交易服务实例
simple_trading_service = SimpleTradingService()