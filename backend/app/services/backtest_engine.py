"""
回测引擎核心逻辑
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session

from ..models import Backtest, Strategy, User
from ..models.enums import BacktestStatus
from ..core.exceptions import ValidationError, NotFoundError
from .history_service import HistoryService
from .tqsdk_adapter import TQSDKAdapter

logger = logging.getLogger(__name__)


class OrderType(Enum):
    """订单类型"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"


class OrderSide(Enum):
    """订单方向"""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    """订单状态"""
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass
class BacktestOrder:
    """回测订单"""
    id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    status: OrderStatus = OrderStatus.PENDING
    created_time: Optional[datetime] = None
    filled_time: Optional[datetime] = None
    filled_price: Optional[float] = None
    filled_quantity: float = 0.0
    commission: float = 0.0


@dataclass
class BacktestPosition:
    """回测持仓"""
    symbol: str
    quantity: float = 0.0
    avg_price: float = 0.0
    market_value: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0


@dataclass
class BacktestAccount:
    """回测账户"""
    initial_capital: float
    available_cash: float
    total_value: float
    positions: Dict[str, BacktestPosition]
    margin_used: float = 0.0
    commission_paid: float = 0.0


class BacktestDataReplay:
    """历史数据回放引擎"""
    
    def __init__(self, history_service: HistoryService):
        self.history_service = history_service
        self.current_time = None
        self.data_cache = {}
        
    async def load_data(self, symbols: List[str], start_date: datetime, end_date: datetime, 
                       frequency: str = "1m") -> Dict[str, pd.DataFrame]:
        """加载历史数据"""
        data = {}
        
        for symbol in symbols:
            try:
                # 获取历史K线数据
                klines = await self.history_service.get_klines(
                    symbol=symbol,
                    start_time=start_date,
                    end_time=end_date,
                    frequency=frequency,
                    limit=None  # 获取所有数据
                )
                
                # 转换为DataFrame
                df_data = []
                for kline in klines:
                    df_data.append({
                        'datetime': kline.datetime,
                        'open': kline.open,
                        'high': kline.high,
                        'low': kline.low,
                        'close': kline.close,
                        'volume': kline.volume,
                        'open_interest': getattr(kline, 'open_interest', 0)
                    })
                
                if df_data:
                    df = pd.DataFrame(df_data)
                    df['datetime'] = pd.to_datetime(df['datetime'])
                    df.set_index('datetime', inplace=True)
                    df.sort_index(inplace=True)
                    data[symbol] = df
                else:
                    logger.warning(f"没有获取到 {symbol} 的历史数据")
                    
            except Exception as e:
                logger.error(f"加载 {symbol} 历史数据失败: {e}")
                
        return data
    
    def get_bar_data(self, symbol: str, current_time: datetime) -> Optional[Dict[str, Any]]:
        """获取指定时间的K线数据"""
        if symbol not in self.data_cache:
            return None
            
        df = self.data_cache[symbol]
        
        # 查找最接近当前时间的数据
        try:
            # 获取当前时间或之前最近的数据
            available_data = df[df.index <= current_time]
            if available_data.empty:
                return None
                
            latest_bar = available_data.iloc[-1]
            
            return {
                'symbol': symbol,
                'datetime': latest_bar.name,
                'open': float(latest_bar['open']),
                'high': float(latest_bar['high']),
                'low': float(latest_bar['low']),
                'close': float(latest_bar['close']),
                'volume': float(latest_bar['volume']),
                'open_interest': float(latest_bar.get('open_interest', 0))
            }
            
        except Exception as e:
            logger.error(f"获取 {symbol} 在 {current_time} 的K线数据失败: {e}")
            return None
    
    def get_historical_bars(self, symbol: str, current_time: datetime, 
                           count: int = 100) -> List[Dict[str, Any]]:
        """获取历史K线数据"""
        if symbol not in self.data_cache:
            return []
            
        df = self.data_cache[symbol]
        
        try:
            # 获取当前时间或之前的数据
            available_data = df[df.index <= current_time]
            if available_data.empty:
                return []
            
            # 获取最近count条数据
            recent_data = available_data.tail(count)
            
            bars = []
            for idx, row in recent_data.iterrows():
                bars.append({
                    'symbol': symbol,
                    'datetime': idx,
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'volume': float(row['volume']),
                    'open_interest': float(row.get('open_interest', 0))
                })
            
            return bars
            
        except Exception as e:
            logger.error(f"获取 {symbol} 历史K线数据失败: {e}")
            return []


class BacktestTradeExecutor:
    """模拟交易执行器"""
    
    def __init__(self, commission_rate: float = 0.0003, slippage: float = 0.0001):
        self.commission_rate = commission_rate  # 手续费率
        self.slippage = slippage  # 滑点
        self.pending_orders: List[BacktestOrder] = []
        self.filled_orders: List[BacktestOrder] = []
        self.order_id_counter = 0
    
    def create_order(self, symbol: str, side: OrderSide, order_type: OrderType,
                    quantity: float, price: Optional[float] = None,
                    stop_price: Optional[float] = None) -> BacktestOrder:
        """创建订单"""
        self.order_id_counter += 1
        
        order = BacktestOrder(
            id=f"order_{self.order_id_counter}",
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
            created_time=datetime.utcnow()
        )
        
        self.pending_orders.append(order)
        return order
    
    def process_orders(self, current_time: datetime, market_data: Dict[str, Dict[str, Any]]):
        """处理待成交订单"""
        orders_to_remove = []
        
        for order in self.pending_orders:
            if order.symbol not in market_data:
                continue
                
            bar_data = market_data[order.symbol]
            
            # 检查订单是否可以成交
            if self._can_fill_order(order, bar_data):
                fill_price = self._calculate_fill_price(order, bar_data)
                self._fill_order(order, fill_price, current_time)
                orders_to_remove.append(order)
        
        # 移除已成交的订单
        for order in orders_to_remove:
            self.pending_orders.remove(order)
            self.filled_orders.append(order)
    
    def _can_fill_order(self, order: BacktestOrder, bar_data: Dict[str, Any]) -> bool:
        """检查订单是否可以成交"""
        if order.order_type == OrderType.MARKET:
            return True
        
        elif order.order_type == OrderType.LIMIT:
            if order.side == OrderSide.BUY:
                return bar_data['low'] <= order.price
            else:
                return bar_data['high'] >= order.price
        
        elif order.order_type == OrderType.STOP:
            if order.side == OrderSide.BUY:
                return bar_data['high'] >= order.stop_price
            else:
                return bar_data['low'] <= order.stop_price
        
        return False
    
    def _calculate_fill_price(self, order: BacktestOrder, bar_data: Dict[str, Any]) -> float:
        """计算成交价格"""
        if order.order_type == OrderType.MARKET:
            # 市价单使用开盘价加滑点
            base_price = bar_data['open']
            if order.side == OrderSide.BUY:
                return base_price * (1 + self.slippage)
            else:
                return base_price * (1 - self.slippage)
        
        elif order.order_type == OrderType.LIMIT:
            # 限价单使用限价
            return order.price
        
        elif order.order_type == OrderType.STOP:
            # 止损单使用止损价加滑点
            if order.side == OrderSide.BUY:
                return order.stop_price * (1 + self.slippage)
            else:
                return order.stop_price * (1 - self.slippage)
        
        return bar_data['close']
    
    def _fill_order(self, order: BacktestOrder, fill_price: float, fill_time: datetime):
        """成交订单"""
        order.status = OrderStatus.FILLED
        order.filled_time = fill_time
        order.filled_price = fill_price
        order.filled_quantity = order.quantity
        
        # 计算手续费
        order.commission = abs(order.quantity * fill_price * self.commission_rate)
    
    def cancel_order(self, order_id: str) -> bool:
        """撤销订单"""
        for order in self.pending_orders:
            if order.id == order_id:
                order.status = OrderStatus.CANCELLED
                self.pending_orders.remove(order)
                return True
        return False
    
    def get_pending_orders(self, symbol: Optional[str] = None) -> List[BacktestOrder]:
        """获取待成交订单"""
        if symbol:
            return [order for order in self.pending_orders if order.symbol == symbol]
        return self.pending_orders.copy()
    
    def get_filled_orders(self, symbol: Optional[str] = None) -> List[BacktestOrder]:
        """获取已成交订单"""
        if symbol:
            return [order for order in self.filled_orders if order.symbol == symbol]
        return self.filled_orders.copy()


class BacktestPortfolioManager:
    """持仓和资金管理模拟器"""
    
    def __init__(self, initial_capital: float):
        self.account = BacktestAccount(
            initial_capital=initial_capital,
            available_cash=initial_capital,
            total_value=initial_capital,
            positions={}
        )
        self.equity_curve = []
        self.daily_returns = []
        
    def update_position(self, order: BacktestOrder):
        """更新持仓"""
        symbol = order.symbol
        
        # 初始化持仓
        if symbol not in self.account.positions:
            self.account.positions[symbol] = BacktestPosition(symbol=symbol)
        
        position = self.account.positions[symbol]
        
        # 计算新的持仓数量和平均价格
        if order.side == OrderSide.BUY:
            # 买入
            if position.quantity >= 0:
                # 增加多头持仓
                total_cost = position.quantity * position.avg_price + order.filled_quantity * order.filled_price
                total_quantity = position.quantity + order.filled_quantity
                position.avg_price = total_cost / total_quantity if total_quantity > 0 else 0
                position.quantity = total_quantity
            else:
                # 平空头持仓
                if order.filled_quantity <= abs(position.quantity):
                    # 部分或全部平仓
                    realized_pnl = (position.avg_price - order.filled_price) * order.filled_quantity
                    position.realized_pnl += realized_pnl
                    position.quantity += order.filled_quantity
                    
                    if position.quantity == 0:
                        position.avg_price = 0
                else:
                    # 平仓后反向开仓
                    close_quantity = abs(position.quantity)
                    open_quantity = order.filled_quantity - close_quantity
                    
                    # 平仓盈亏
                    realized_pnl = (position.avg_price - order.filled_price) * close_quantity
                    position.realized_pnl += realized_pnl
                    
                    # 新开仓
                    position.quantity = open_quantity
                    position.avg_price = order.filled_price
        
        else:  # SELL
            # 卖出
            if position.quantity <= 0:
                # 增加空头持仓
                total_cost = abs(position.quantity) * position.avg_price + order.filled_quantity * order.filled_price
                total_quantity = abs(position.quantity) + order.filled_quantity
                position.avg_price = total_cost / total_quantity if total_quantity > 0 else 0
                position.quantity = -total_quantity
            else:
                # 平多头持仓
                if order.filled_quantity <= position.quantity:
                    # 部分或全部平仓
                    realized_pnl = (order.filled_price - position.avg_price) * order.filled_quantity
                    position.realized_pnl += realized_pnl
                    position.quantity -= order.filled_quantity
                    
                    if position.quantity == 0:
                        position.avg_price = 0
                else:
                    # 平仓后反向开仓
                    close_quantity = position.quantity
                    open_quantity = order.filled_quantity - close_quantity
                    
                    # 平仓盈亏
                    realized_pnl = (order.filled_price - position.avg_price) * close_quantity
                    position.realized_pnl += realized_pnl
                    
                    # 新开仓
                    position.quantity = -open_quantity
                    position.avg_price = order.filled_price
        
        # 更新可用资金
        self.account.available_cash -= order.commission
        self.account.commission_paid += order.commission
    
    def update_market_value(self, market_data: Dict[str, Dict[str, Any]]):
        """更新市值和未实现盈亏"""
        total_market_value = 0
        
        for symbol, position in self.account.positions.items():
            if position.quantity == 0:
                position.market_value = 0
                position.unrealized_pnl = 0
                continue
            
            if symbol in market_data:
                current_price = market_data[symbol]['close']
                position.market_value = abs(position.quantity) * current_price
                
                # 计算未实现盈亏
                if position.quantity > 0:
                    # 多头
                    position.unrealized_pnl = (current_price - position.avg_price) * position.quantity
                else:
                    # 空头
                    position.unrealized_pnl = (position.avg_price - current_price) * abs(position.quantity)
                
                total_market_value += position.market_value
        
        # 更新账户总价值
        total_unrealized_pnl = sum(pos.unrealized_pnl for pos in self.account.positions.values())
        total_realized_pnl = sum(pos.realized_pnl for pos in self.account.positions.values())
        
        self.account.total_value = (
            self.account.initial_capital + 
            total_realized_pnl + 
            total_unrealized_pnl - 
            self.account.commission_paid
        )
    
    def record_equity_point(self, timestamp: datetime):
        """记录资金曲线点"""
        self.equity_curve.append({
            'timestamp': timestamp,
            'total_value': self.account.total_value,
            'available_cash': self.account.available_cash,
            'market_value': sum(pos.market_value for pos in self.account.positions.values()),
            'unrealized_pnl': sum(pos.unrealized_pnl for pos in self.account.positions.values()),
            'realized_pnl': sum(pos.realized_pnl for pos in self.account.positions.values())
        })
    
    def calculate_daily_return(self, previous_value: float) -> float:
        """计算日收益率"""
        if previous_value <= 0:
            return 0.0
        return (self.account.total_value - previous_value) / previous_value
    
    def get_position(self, symbol: str) -> BacktestPosition:
        """获取持仓"""
        return self.account.positions.get(symbol, BacktestPosition(symbol=symbol))
    
    def get_account_info(self) -> BacktestAccount:
        """获取账户信息"""
        return self.account


class BacktestProgressTracker:
    """回测进度跟踪器"""
    
    def __init__(self, total_bars: int, update_callback: Optional[Callable] = None):
        self.total_bars = total_bars
        self.processed_bars = 0
        self.start_time = datetime.utcnow()
        self.update_callback = update_callback
        
    def update_progress(self, processed_bars: int):
        """更新进度"""
        self.processed_bars = processed_bars
        progress = (processed_bars / self.total_bars) * 100 if self.total_bars > 0 else 0
        
        if self.update_callback:
            self.update_callback(progress)
    
    def get_progress(self) -> float:
        """获取当前进度"""
        return (self.processed_bars / self.total_bars) * 100 if self.total_bars > 0 else 0
    
    def get_eta(self) -> Optional[datetime]:
        """估算完成时间"""
        if self.processed_bars == 0:
            return None
        
        elapsed_time = datetime.utcnow() - self.start_time
        avg_time_per_bar = elapsed_time.total_seconds() / self.processed_bars
        remaining_bars = self.total_bars - self.processed_bars
        
        if remaining_bars <= 0:
            return datetime.utcnow()
        
        eta_seconds = remaining_bars * avg_time_per_bar
        return datetime.utcnow() + timedelta(seconds=eta_seconds)


class BacktestEngine:
    """回测引擎主类"""
    
    def __init__(self, db: Session, history_service: HistoryService):
        self.db = db
        self.history_service = history_service
        self.data_replay = BacktestDataReplay(history_service)
        self.trade_executor = None
        self.portfolio_manager = None
        self.progress_tracker = None
        self.strategy_globals = {}
        
    async def run_backtest(self, backtest_id: int) -> Dict[str, Any]:
        """运行回测"""
        try:
            # 获取回测配置
            backtest = self.db.query(Backtest).filter(Backtest.id == backtest_id).first()
            if not backtest:
                raise NotFoundError("回测不存在")
            
            # 获取策略
            strategy = self.db.query(Strategy).filter(Strategy.id == backtest.strategy_id).first()
            if not strategy:
                raise NotFoundError("策略不存在")
            
            # 更新回测状态
            backtest.status = BacktestStatus.RUNNING
            backtest.started_at = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"开始运行回测: {backtest.name}")
            
            # 初始化组件
            self.trade_executor = BacktestTradeExecutor()
            self.portfolio_manager = BacktestPortfolioManager(backtest.initial_capital)
            
            # 加载历史数据
            symbols = backtest.symbols or []
            data = await self.data_replay.load_data(
                symbols=symbols,
                start_date=backtest.start_date,
                end_date=backtest.end_date
            )
            
            if not data:
                raise ValidationError("没有可用的历史数据")
            
            self.data_replay.data_cache = data
            
            # 计算总的K线数量用于进度跟踪
            total_bars = max(len(df) for df in data.values()) if data else 0
            self.progress_tracker = BacktestProgressTracker(
                total_bars=total_bars,
                update_callback=lambda progress: self._update_backtest_progress(backtest_id, progress)
            )
            
            # 准备策略执行环境
            self._prepare_strategy_environment(strategy, backtest)
            
            # 执行回测
            result = await self._execute_backtest(backtest, data)
            
            # 更新回测结果
            self._update_backtest_results(backtest, result)
            
            # 更新状态为完成
            backtest.status = BacktestStatus.COMPLETED
            backtest.completed_at = datetime.utcnow()
            backtest.progress = 100.0
            self.db.commit()
            
            logger.info(f"回测完成: {backtest.name}")
            
            return result
            
        except Exception as e:
            logger.error(f"回测执行失败: {e}")
            
            # 更新回测状态为失败
            backtest.status = BacktestStatus.FAILED
            backtest.error_message = str(e)
            backtest.completed_at = datetime.utcnow()
            self.db.commit()
            
            raise
    
    def _prepare_strategy_environment(self, strategy: Strategy, backtest: Backtest):
        """准备策略执行环境"""
        # 创建策略上下文
        context = BacktestContext(
            backtest_engine=self,
            symbols=backtest.symbols,
            parameters=backtest.parameters or {}
        )
        
        # 准备全局环境
        self.strategy_globals = {
            '__builtins__': __builtins__,
            '__name__': '__main__',
            'context': context,
        }
        
        # 添加常用模块
        import math
        import numpy as np
        import pandas as pd
        
        self.strategy_globals.update({
            'math': math,
            'np': np,
            'pd': pd,
        })
        
        # 执行策略代码
        exec(strategy.code, self.strategy_globals)
    
    async def _execute_backtest(self, backtest: Backtest, data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """执行回测逻辑"""
        # 获取所有时间点
        all_timestamps = set()
        for df in data.values():
            all_timestamps.update(df.index)
        
        timestamps = sorted(all_timestamps)
        
        if not timestamps:
            raise ValidationError("没有有效的时间数据")
        
        # 初始化策略
        if 'initialize' in self.strategy_globals:
            self.strategy_globals['initialize'](self.strategy_globals['context'])
        
        # 逐个时间点回放
        previous_day_value = backtest.initial_capital
        
        for i, current_time in enumerate(timestamps):
            # 更新当前时间
            self.data_replay.current_time = current_time
            
            # 获取当前时间的市场数据
            market_data = {}
            for symbol in backtest.symbols:
                bar_data = self.data_replay.get_bar_data(symbol, current_time)
                if bar_data:
                    market_data[symbol] = bar_data
            
            if not market_data:
                continue
            
            # 处理待成交订单
            self.trade_executor.process_orders(current_time, market_data)
            
            # 更新持仓市值
            self.portfolio_manager.update_market_value(market_data)
            
            # 调用策略的handle_bar函数
            if 'handle_bar' in self.strategy_globals:
                try:
                    self.strategy_globals['handle_bar'](
                        self.strategy_globals['context'], 
                        market_data
                    )
                except Exception as e:
                    logger.error(f"策略执行错误 at {current_time}: {e}")
            
            # 处理新产生的订单
            for order in self.trade_executor.pending_orders:
                if order.created_time and order.created_time >= current_time:
                    # 立即尝试成交市价单
                    if order.order_type == OrderType.MARKET:
                        if order.symbol in market_data:
                            fill_price = self.trade_executor._calculate_fill_price(order, market_data[order.symbol])
                            self.trade_executor._fill_order(order, fill_price, current_time)
                            self.portfolio_manager.update_position(order)
            
            # 记录资金曲线
            self.portfolio_manager.record_equity_point(current_time)
            
            # 计算日收益率（每日收盘时）
            if current_time.hour == 15:  # 假设15点为收盘时间
                daily_return = self.portfolio_manager.calculate_daily_return(previous_day_value)
                self.portfolio_manager.daily_returns.append({
                    'date': current_time.date(),
                    'return': daily_return
                })
                previous_day_value = self.portfolio_manager.account.total_value
            
            # 更新进度
            self.progress_tracker.update_progress(i + 1)
        
        # 生成回测结果
        return self._generate_backtest_result()
    
    def _generate_backtest_result(self) -> Dict[str, Any]:
        """生成回测结果"""
        account = self.portfolio_manager.account
        equity_curve = self.portfolio_manager.equity_curve
        daily_returns = self.portfolio_manager.daily_returns
        filled_orders = self.trade_executor.filled_orders
        
        # 基础指标
        final_capital = account.total_value
        total_return = (final_capital - account.initial_capital) / account.initial_capital
        
        # 计算年化收益率
        if equity_curve:
            days = (equity_curve[-1]['timestamp'] - equity_curve[0]['timestamp']).days
            annual_return = (1 + total_return) ** (365 / max(days, 1)) - 1 if days > 0 else 0
        else:
            annual_return = 0
        
        # 计算最大回撤
        max_drawdown = self._calculate_max_drawdown(equity_curve)
        
        # 计算夏普比率
        sharpe_ratio = self._calculate_sharpe_ratio(daily_returns)
        
        # 计算索提诺比率
        sortino_ratio = self._calculate_sortino_ratio(daily_returns)
        
        # 交易统计
        trade_stats = self._calculate_trade_statistics(filled_orders)
        
        return {
            'final_capital': final_capital,
            'total_return': total_return,
            'annual_return': annual_return,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'equity_curve': equity_curve,
            'daily_returns': daily_returns,
            'trade_records': [self._order_to_dict(order) for order in filled_orders],
            **trade_stats
        }
    
    def _calculate_max_drawdown(self, equity_curve: List[Dict]) -> float:
        """计算最大回撤"""
        if not equity_curve:
            return 0.0
        
        peak = equity_curve[0]['total_value']
        max_dd = 0.0
        
        for point in equity_curve:
            value = point['total_value']
            if value > peak:
                peak = value
            
            drawdown = (peak - value) / peak
            max_dd = max(max_dd, drawdown)
        
        return max_dd
    
    def _calculate_sharpe_ratio(self, daily_returns: List[Dict], risk_free_rate: float = 0.03) -> float:
        """计算夏普比率"""
        if not daily_returns:
            return 0.0
        
        returns = [r['return'] for r in daily_returns]
        
        if not returns:
            return 0.0
        
        avg_return = np.mean(returns)
        std_return = np.std(returns)
        
        if std_return == 0:
            return 0.0
        
        # 年化
        daily_risk_free = risk_free_rate / 252
        return (avg_return - daily_risk_free) / std_return * np.sqrt(252)
    
    def _calculate_sortino_ratio(self, daily_returns: List[Dict], risk_free_rate: float = 0.03) -> float:
        """计算索提诺比率"""
        if not daily_returns:
            return 0.0
        
        returns = [r['return'] for r in daily_returns]
        
        if not returns:
            return 0.0
        
        avg_return = np.mean(returns)
        negative_returns = [r for r in returns if r < 0]
        
        if not negative_returns:
            return float('inf') if avg_return > risk_free_rate / 252 else 0.0
        
        downside_std = np.std(negative_returns)
        
        if downside_std == 0:
            return 0.0
        
        # 年化
        daily_risk_free = risk_free_rate / 252
        return (avg_return - daily_risk_free) / downside_std * np.sqrt(252)
    
    def _calculate_trade_statistics(self, filled_orders: List[BacktestOrder]) -> Dict[str, Any]:
        """计算交易统计"""
        if not filled_orders:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'profit_factor': 0.0
            }
        
        # 按品种分组计算盈亏
        symbol_pnl = {}
        
        for order in filled_orders:
            symbol = order.symbol
            if symbol not in symbol_pnl:
                symbol_pnl[symbol] = []
            
            # 简化的盈亏计算（实际应该配对买卖单）
            pnl = 0  # 这里需要更复杂的逻辑来计算每笔交易的盈亏
            symbol_pnl[symbol].append(pnl)
        
        # 统计所有交易
        all_trades = []
        for trades in symbol_pnl.values():
            all_trades.extend(trades)
        
        total_trades = len(all_trades)
        winning_trades = len([t for t in all_trades if t > 0])
        losing_trades = len([t for t in all_trades if t < 0])
        
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        wins = [t for t in all_trades if t > 0]
        losses = [t for t in all_trades if t < 0]
        
        avg_win = np.mean(wins) if wins else 0
        avg_loss = abs(np.mean(losses)) if losses else 0
        
        profit_factor = sum(wins) / abs(sum(losses)) if losses else float('inf') if wins else 0
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor
        }
    
    def _order_to_dict(self, order: BacktestOrder) -> Dict[str, Any]:
        """将订单转换为字典"""
        return {
            'id': order.id,
            'symbol': order.symbol,
            'side': order.side.value,
            'type': order.order_type.value,
            'quantity': order.quantity,
            'price': order.price,
            'filled_price': order.filled_price,
            'filled_quantity': order.filled_quantity,
            'commission': order.commission,
            'created_time': order.created_time.isoformat() if order.created_time else None,
            'filled_time': order.filled_time.isoformat() if order.filled_time else None,
            'status': order.status.value
        }
    
    def _update_backtest_progress(self, backtest_id: int, progress: float):
        """更新回测进度"""
        try:
            backtest = self.db.query(Backtest).filter(Backtest.id == backtest_id).first()
            if backtest:
                backtest.progress = progress
                self.db.commit()
        except Exception as e:
            logger.error(f"更新回测进度失败: {e}")
    
    def _update_backtest_results(self, backtest: Backtest, result: Dict[str, Any]):
        """更新回测结果"""
        backtest.final_capital = result['final_capital']
        backtest.total_return = result['total_return']
        backtest.annual_return = result['annual_return']
        backtest.max_drawdown = result['max_drawdown']
        backtest.sharpe_ratio = result['sharpe_ratio']
        backtest.sortino_ratio = result['sortino_ratio']
        
        backtest.total_trades = result['total_trades']
        backtest.winning_trades = result['winning_trades']
        backtest.losing_trades = result['losing_trades']
        backtest.win_rate = result['win_rate']
        backtest.avg_win = result['avg_win']
        backtest.avg_loss = result['avg_loss']
        backtest.profit_factor = result['profit_factor']
        
        backtest.equity_curve = result['equity_curve']
        backtest.trade_records = result['trade_records']
        backtest.daily_returns = result['daily_returns']


class BacktestContext:
    """回测策略上下文"""
    
    def __init__(self, backtest_engine: BacktestEngine, symbols: List[str], parameters: Dict[str, Any]):
        self.backtest_engine = backtest_engine
        self.symbols = symbols
        self.params = parameters
        self.current_time = None
        
    def get_klines(self, symbol: str, count: int = 100) -> List[Dict[str, Any]]:
        """获取K线数据"""
        if not self.backtest_engine.data_replay.current_time:
            return []
        
        return self.backtest_engine.data_replay.get_historical_bars(
            symbol, self.backtest_engine.data_replay.current_time, count
        )
    
    def get_position(self, symbol: str) -> Dict[str, Any]:
        """获取持仓信息"""
        position = self.backtest_engine.portfolio_manager.get_position(symbol)
        return {
            'symbol': symbol,
            'quantity': position.quantity,
            'avg_price': position.avg_price,
            'market_value': position.market_value,
            'unrealized_pnl': position.unrealized_pnl,
            'realized_pnl': position.realized_pnl
        }
    
    def get_account(self) -> Dict[str, Any]:
        """获取账户信息"""
        account = self.backtest_engine.portfolio_manager.get_account_info()
        return {
            'initial_capital': account.initial_capital,
            'available_cash': account.available_cash,
            'total_value': account.total_value,
            'margin_used': account.margin_used,
            'commission_paid': account.commission_paid
        }
    
    def order_target_percent(self, symbol: str, percent: float):
        """按百分比下单"""
        account = self.backtest_engine.portfolio_manager.get_account_info()
        target_value = account.total_value * percent
        
        # 获取当前价格
        current_bar = self.backtest_engine.data_replay.get_bar_data(
            symbol, self.backtest_engine.data_replay.current_time
        )
        
        if not current_bar:
            return
        
        current_price = current_bar['close']
        target_quantity = target_value / current_price
        
        # 获取当前持仓
        current_position = self.backtest_engine.portfolio_manager.get_position(symbol)
        quantity_diff = target_quantity - current_position.quantity
        
        if abs(quantity_diff) > 0.01:  # 最小交易单位
            side = OrderSide.BUY if quantity_diff > 0 else OrderSide.SELL
            order = self.backtest_engine.trade_executor.create_order(
                symbol=symbol,
                side=side,
                order_type=OrderType.MARKET,
                quantity=abs(quantity_diff)
            )
            
            # 立即成交市价单
            fill_price = self.backtest_engine.trade_executor._calculate_fill_price(order, current_bar)
            self.backtest_engine.trade_executor._fill_order(
                order, fill_price, self.backtest_engine.data_replay.current_time
            )
            self.backtest_engine.portfolio_manager.update_position(order)
    
    def order_target_value(self, symbol: str, value: float):
        """按金额下单"""
        account = self.backtest_engine.portfolio_manager.get_account_info()
        percent = value / account.total_value
        self.order_target_percent(symbol, percent)
    
    def buy(self, symbol: str, quantity: float, price: Optional[float] = None):
        """买入"""
        order_type = OrderType.LIMIT if price else OrderType.MARKET
        self.backtest_engine.trade_executor.create_order(
            symbol=symbol,
            side=OrderSide.BUY,
            order_type=order_type,
            quantity=quantity,
            price=price
        )
    
    def sell(self, symbol: str, quantity: float, price: Optional[float] = None):
        """卖出"""
        order_type = OrderType.LIMIT if price else OrderType.MARKET
        self.backtest_engine.trade_executor.create_order(
            symbol=symbol,
            side=OrderSide.SELL,
            order_type=order_type,
            quantity=quantity,
            price=price
        )
    
    def log(self, message: str):
        """记录日志"""
        logger.info(f"[Strategy] {message}")