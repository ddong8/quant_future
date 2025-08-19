"""
简化回测引擎 - 基于tqsdk的策略回测功能
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
import numpy as np
import uuid

from .tqsdk_adapter import tqsdk_adapter
from ..core.database import get_redis_client
from ..core.exceptions import ValidationError, BusinessLogicError

logger = logging.getLogger(__name__)


class OrderSide(Enum):
    """订单方向"""
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(Enum):
    """订单状态"""
    PENDING = "PENDING"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"


@dataclass
class BacktestOrder:
    """回测订单"""
    id: str
    symbol: str
    side: OrderSide
    quantity: int
    price: float
    status: OrderStatus = OrderStatus.PENDING
    created_time: datetime = field(default_factory=datetime.now)
    filled_time: Optional[datetime] = None
    filled_price: Optional[float] = None
    commission: float = 0.0


@dataclass
class BacktestPosition:
    """回测持仓"""
    symbol: str
    quantity: int = 0
    avg_price: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    
    def update_unrealized_pnl(self, current_price: float):
        """更新未实现盈亏"""
        if self.quantity != 0:
            self.unrealized_pnl = self.quantity * (current_price - self.avg_price)
        else:
            self.unrealized_pnl = 0.0


@dataclass
class BacktestAccount:
    """回测账户"""
    initial_capital: float
    available_cash: float
    total_value: float
    positions: Dict[str, BacktestPosition] = field(default_factory=dict)
    commission_paid: float = 0.0
    
    def get_position(self, symbol: str) -> BacktestPosition:
        """获取持仓"""
        if symbol not in self.positions:
            self.positions[symbol] = BacktestPosition(symbol=symbol)
        return self.positions[symbol]
    
    def update_total_value(self, market_prices: Dict[str, float]):
        """更新总资产"""
        position_value = 0.0
        for symbol, position in self.positions.items():
            if symbol in market_prices:
                position.update_unrealized_pnl(market_prices[symbol])
                position_value += position.quantity * market_prices[symbol]
        
        self.total_value = self.available_cash + position_value


class SimpleBacktestEngine:
    """简化回测引擎"""
    
    def __init__(self):
        self.redis_client = get_redis_client()
        self.running_backtests: Dict[str, Dict] = {}
    
    async def create_backtest(
        self,
        strategy_code: str,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        initial_capital: float = 1000000.0,
        commission_rate: float = 0.0001
    ) -> str:
        """创建回测任务"""
        try:
            # 生成回测ID
            backtest_id = f"BT_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
            
            # 验证参数
            if start_date >= end_date:
                raise ValidationError("开始时间必须早于结束时间")
            
            if initial_capital <= 0:
                raise ValidationError("初始资金必须大于0")
            
            if not symbols:
                raise ValidationError("必须指定至少一个交易标的")
            
            # 创建回测配置
            backtest_config = {
                "backtest_id": backtest_id,
                "strategy_code": strategy_code,
                "symbols": symbols,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "initial_capital": initial_capital,
                "commission_rate": commission_rate,
                "status": "CREATED",
                "created_time": datetime.now().isoformat(),
                "progress": 0.0,
                "results": None
            }
            
            # 保存配置
            self.running_backtests[backtest_id] = backtest_config
            
            # 缓存到Redis
            self.redis_client.setex(
                f"backtest:{backtest_id}",
                3600,  # 1小时过期
                str(backtest_config)
            )
            
            logger.info(f"回测任务创建成功: {backtest_id}")
            return backtest_id
            
        except Exception as e:
            logger.error(f"创建回测任务失败: {e}")
            raise BusinessLogicError(f"创建回测任务失败: {str(e)}")
    
    async def run_backtest(self, backtest_id: str) -> Dict[str, Any]:
        """运行回测"""
        try:
            if backtest_id not in self.running_backtests:
                raise ValidationError("回测任务不存在")
            
            config = self.running_backtests[backtest_id]
            config["status"] = "RUNNING"
            config["start_time"] = datetime.now().isoformat()
            
            # 解析参数
            symbols = config["symbols"]
            start_date = datetime.fromisoformat(config["start_date"])
            end_date = datetime.fromisoformat(config["end_date"])
            initial_capital = config["initial_capital"]
            commission_rate = config["commission_rate"]
            strategy_code = config["strategy_code"]
            
            # 初始化回测账户
            account = BacktestAccount(
                initial_capital=initial_capital,
                available_cash=initial_capital,
                total_value=initial_capital
            )
            
            # 获取历史数据
            logger.info(f"开始获取历史数据: {symbols}")
            historical_data = await self._load_historical_data(symbols, start_date, end_date)
            
            if not historical_data:
                raise BusinessLogicError("无法获取历史数据")
            
            # 执行回测
            results = await self._execute_backtest(
                backtest_id, account, historical_data, strategy_code, commission_rate
            )
            
            # 更新状态
            config["status"] = "COMPLETED"
            config["end_time"] = datetime.now().isoformat()
            config["results"] = results
            config["progress"] = 100.0
            
            logger.info(f"回测完成: {backtest_id}")
            return results
            
        except Exception as e:
            logger.error(f"回测执行失败: {e}")
            if backtest_id in self.running_backtests:
                self.running_backtests[backtest_id]["status"] = "FAILED"
                self.running_backtests[backtest_id]["error"] = str(e)
            raise BusinessLogicError(f"回测执行失败: {str(e)}")
    
    async def _load_historical_data(
        self, 
        symbols: List[str], 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, List[Dict]]:
        """加载历史数据"""
        try:
            historical_data = {}
            
            for symbol in symbols:
                # 计算需要的数据长度（按分钟计算）
                total_minutes = int((end_date - start_date).total_seconds() / 60)
                data_length = min(total_minutes, 8000)  # tqsdk限制
                
                # 获取K线数据
                klines = await tqsdk_adapter.get_klines(symbol, 60, data_length)
                
                if klines:
                    # 过滤时间范围内的数据
                    filtered_klines = []
                    for kline in klines:
                        kline_time = datetime.fromisoformat(kline["datetime"])
                        if start_date <= kline_time <= end_date:
                            filtered_klines.append(kline)
                    
                    historical_data[symbol] = filtered_klines
                    logger.info(f"获取 {symbol} 历史数据: {len(filtered_klines)} 条")
                else:
                    logger.warning(f"无法获取 {symbol} 的历史数据")
            
            return historical_data
            
        except Exception as e:
            logger.error(f"加载历史数据失败: {e}")
            return {}
    
    async def _execute_backtest(
        self,
        backtest_id: str,
        account: BacktestAccount,
        historical_data: Dict[str, List[Dict]],
        strategy_code: str,
        commission_rate: float
    ) -> Dict[str, Any]:
        """执行回测逻辑"""
        try:
            orders = []
            equity_curve = []
            trades = []
            
            # 获取所有时间点
            all_times = set()
            for symbol_data in historical_data.values():
                for kline in symbol_data:
                    all_times.add(datetime.fromisoformat(kline["datetime"]))
            
            sorted_times = sorted(all_times)
            total_steps = len(sorted_times)
            
            # 简单的移动平均策略示例
            ma_periods = {"short": 5, "long": 20}
            ma_data = {symbol: {"short": [], "long": [], "prices": []} for symbol in historical_data.keys()}
            
            for i, current_time in enumerate(sorted_times):
                # 更新进度
                progress = (i / total_steps) * 100
                self.running_backtests[backtest_id]["progress"] = progress
                
                # 获取当前时刻的价格数据
                current_prices = {}
                for symbol, symbol_data in historical_data.items():
                    for kline in symbol_data:
                        if datetime.fromisoformat(kline["datetime"]) == current_time:
                            current_prices[symbol] = kline["close"]
                            ma_data[symbol]["prices"].append(kline["close"])
                            break
                
                # 计算移动平均线
                for symbol in current_prices.keys():
                    prices = ma_data[symbol]["prices"]
                    if len(prices) >= ma_periods["short"]:
                        short_ma = np.mean(prices[-ma_periods["short"]:])
                        ma_data[symbol]["short"].append(short_ma)
                    
                    if len(prices) >= ma_periods["long"]:
                        long_ma = np.mean(prices[-ma_periods["long"]:])
                        ma_data[symbol]["long"].append(long_ma)
                
                # 执行交易策略（简单的双均线策略）
                for symbol in current_prices.keys():
                    if (len(ma_data[symbol]["short"]) >= 2 and 
                        len(ma_data[symbol]["long"]) >= 2):
                        
                        short_ma_current = ma_data[symbol]["short"][-1]
                        short_ma_prev = ma_data[symbol]["short"][-2]
                        long_ma_current = ma_data[symbol]["long"][-1]
                        long_ma_prev = ma_data[symbol]["long"][-2]
                        
                        position = account.get_position(symbol)
                        current_price = current_prices[symbol]
                        
                        # 金叉买入信号
                        if (short_ma_prev <= long_ma_prev and 
                            short_ma_current > long_ma_current and 
                            position.quantity <= 0):
                            
                            # 计算买入数量（使用可用资金的10%）
                            trade_value = account.available_cash * 0.1
                            quantity = int(trade_value / current_price)
                            
                            if quantity > 0:
                                order = await self._place_backtest_order(
                                    account, symbol, OrderSide.BUY, quantity, 
                                    current_price, current_time, commission_rate
                                )
                                orders.append(order)
                                trades.append({
                                    "time": current_time.isoformat(),
                                    "symbol": symbol,
                                    "side": "BUY",
                                    "quantity": quantity,
                                    "price": current_price,
                                    "signal": "MA_CROSS_UP"
                                })
                        
                        # 死叉卖出信号
                        elif (short_ma_prev >= long_ma_prev and 
                              short_ma_current < long_ma_current and 
                              position.quantity > 0):
                            
                            quantity = position.quantity
                            order = await self._place_backtest_order(
                                account, symbol, OrderSide.SELL, quantity,
                                current_price, current_time, commission_rate
                            )
                            orders.append(order)
                            trades.append({
                                "time": current_time.isoformat(),
                                "symbol": symbol,
                                "side": "SELL",
                                "quantity": quantity,
                                "price": current_price,
                                "signal": "MA_CROSS_DOWN"
                            })
                
                # 更新账户价值
                account.update_total_value(current_prices)
                
                # 记录权益曲线
                equity_curve.append({
                    "time": current_time.isoformat(),
                    "total_value": account.total_value,
                    "available_cash": account.available_cash,
                    "unrealized_pnl": sum(pos.unrealized_pnl for pos in account.positions.values()),
                    "realized_pnl": sum(pos.realized_pnl for pos in account.positions.values())
                })
            
            # 计算回测结果
            results = self._calculate_backtest_results(account, equity_curve, trades)
            
            return results
            
        except Exception as e:
            logger.error(f"执行回测失败: {e}")
            raise
    
    async def _place_backtest_order(
        self,
        account: BacktestAccount,
        symbol: str,
        side: OrderSide,
        quantity: int,
        price: float,
        current_time: datetime,
        commission_rate: float
    ) -> BacktestOrder:
        """在回测中下单"""
        try:
            order_id = f"ORDER_{current_time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
            
            # 创建订单
            order = BacktestOrder(
                id=order_id,
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price,
                created_time=current_time,
                filled_time=current_time,
                filled_price=price,
                status=OrderStatus.FILLED
            )
            
            # 计算手续费
            order.commission = quantity * price * commission_rate
            account.commission_paid += order.commission
            
            # 更新持仓
            position = account.get_position(symbol)
            
            if side == OrderSide.BUY:
                # 买入
                if position.quantity >= 0:
                    # 开多仓或加仓
                    new_quantity = position.quantity + quantity
                    new_avg_price = ((position.quantity * position.avg_price + 
                                    quantity * price) / new_quantity) if new_quantity > 0 else 0
                    position.quantity = new_quantity
                    position.avg_price = new_avg_price
                else:
                    # 平空仓
                    if quantity <= abs(position.quantity):
                        # 部分或全部平仓
                        realized_pnl = quantity * (position.avg_price - price)
                        position.realized_pnl += realized_pnl
                        position.quantity += quantity
                        if position.quantity == 0:
                            position.avg_price = 0
                    else:
                        # 平仓后反向开仓
                        close_quantity = abs(position.quantity)
                        open_quantity = quantity - close_quantity
                        
                        # 平仓盈亏
                        realized_pnl = close_quantity * (position.avg_price - price)
                        position.realized_pnl += realized_pnl
                        
                        # 开新仓
                        position.quantity = open_quantity
                        position.avg_price = price
                
                # 更新可用资金
                account.available_cash -= quantity * price + order.commission
            
            else:  # SELL
                # 卖出
                if position.quantity <= 0:
                    # 开空仓或加仓
                    new_quantity = position.quantity - quantity
                    new_avg_price = ((abs(position.quantity) * position.avg_price + 
                                    quantity * price) / abs(new_quantity)) if new_quantity != 0 else 0
                    position.quantity = new_quantity
                    position.avg_price = new_avg_price
                else:
                    # 平多仓
                    if quantity <= position.quantity:
                        # 部分或全部平仓
                        realized_pnl = quantity * (price - position.avg_price)
                        position.realized_pnl += realized_pnl
                        position.quantity -= quantity
                        if position.quantity == 0:
                            position.avg_price = 0
                    else:
                        # 平仓后反向开仓
                        close_quantity = position.quantity
                        open_quantity = quantity - close_quantity
                        
                        # 平仓盈亏
                        realized_pnl = close_quantity * (price - position.avg_price)
                        position.realized_pnl += realized_pnl
                        
                        # 开新仓
                        position.quantity = -open_quantity
                        position.avg_price = price
                
                # 更新可用资金
                account.available_cash += quantity * price - order.commission
            
            return order
            
        except Exception as e:
            logger.error(f"回测下单失败: {e}")
            raise
    
    def _calculate_backtest_results(
        self, 
        account: BacktestAccount, 
        equity_curve: List[Dict], 
        trades: List[Dict]
    ) -> Dict[str, Any]:
        """计算回测结果"""
        try:
            if not equity_curve:
                return {"error": "无权益曲线数据"}
            
            # 基本统计
            initial_value = account.initial_capital
            final_value = account.total_value
            total_return = (final_value - initial_value) / initial_value
            
            # 计算最大回撤
            peak = initial_value
            max_drawdown = 0.0
            drawdown_series = []
            
            for point in equity_curve:
                value = point["total_value"]
                if value > peak:
                    peak = value
                drawdown = (peak - value) / peak
                drawdown_series.append(drawdown)
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
            
            # 计算夏普比率（简化版）
            returns = []
            for i in range(1, len(equity_curve)):
                prev_value = equity_curve[i-1]["total_value"]
                curr_value = equity_curve[i]["total_value"]
                returns.append((curr_value - prev_value) / prev_value)
            
            if returns:
                avg_return = np.mean(returns)
                std_return = np.std(returns)
                sharpe_ratio = avg_return / std_return if std_return > 0 else 0
            else:
                sharpe_ratio = 0
            
            # 交易统计
            total_trades = len(trades)
            winning_trades = 0
            losing_trades = 0
            
            # 简化的盈亏计算
            total_realized_pnl = sum(pos.realized_pnl for pos in account.positions.values())
            
            results = {
                "summary": {
                    "initial_capital": initial_value,
                    "final_value": final_value,
                    "total_return": total_return,
                    "total_return_pct": total_return * 100,
                    "max_drawdown": max_drawdown,
                    "max_drawdown_pct": max_drawdown * 100,
                    "sharpe_ratio": sharpe_ratio,
                    "total_trades": total_trades,
                    "commission_paid": account.commission_paid,
                    "realized_pnl": total_realized_pnl
                },
                "equity_curve": equity_curve[-100:],  # 只返回最后100个点
                "trades": trades,
                "positions": {
                    symbol: {
                        "quantity": pos.quantity,
                        "avg_price": pos.avg_price,
                        "unrealized_pnl": pos.unrealized_pnl,
                        "realized_pnl": pos.realized_pnl
                    }
                    for symbol, pos in account.positions.items()
                    if pos.quantity != 0 or pos.realized_pnl != 0
                }
            }
            
            return results
            
        except Exception as e:
            logger.error(f"计算回测结果失败: {e}")
            return {"error": f"计算失败: {str(e)}"}
    
    async def get_backtest_status(self, backtest_id: str) -> Dict[str, Any]:
        """获取回测状态"""
        try:
            if backtest_id not in self.running_backtests:
                raise ValidationError("回测任务不存在")
            
            return self.running_backtests[backtest_id]
            
        except Exception as e:
            logger.error(f"获取回测状态失败: {e}")
            raise BusinessLogicError(f"获取回测状态失败: {str(e)}")
    
    async def list_backtests(self) -> List[Dict[str, Any]]:
        """获取回测列表"""
        try:
            backtests = []
            for backtest_id, config in self.running_backtests.items():
                backtests.append({
                    "backtest_id": backtest_id,
                    "status": config["status"],
                    "created_time": config["created_time"],
                    "progress": config.get("progress", 0.0),
                    "symbols": config["symbols"],
                    "initial_capital": config["initial_capital"]
                })
            
            # 按创建时间倒序排列
            backtests.sort(key=lambda x: x["created_time"], reverse=True)
            
            return backtests
            
        except Exception as e:
            logger.error(f"获取回测列表失败: {e}")
            raise BusinessLogicError(f"获取回测列表失败: {str(e)}")


# 创建全局回测引擎实例
simple_backtest_engine = SimpleBacktestEngine()