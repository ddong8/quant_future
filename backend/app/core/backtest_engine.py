"""
回测引擎核心模块
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from decimal import Decimal
import pandas as pd
import numpy as np
from dataclasses import dataclass
from enum import Enum

from ..models.backtest import Backtest, BacktestStatus
from ..models.strategy import Strategy, StrategyVersion
from ..services.backtest_service import BacktestService

logger = logging.getLogger(__name__)


class SignalType(Enum):
    """信号类型"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


@dataclass
class TradingSignal:
    """交易信号"""
    timestamp: datetime
    symbol: str
    signal_type: SignalType
    price: float
    quantity: int
    confidence: float = 1.0
    metadata: Dict[str, Any] = None


@dataclass
class Position:
    """持仓信息"""
    symbol: str
    quantity: int
    avg_price: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float
    entry_time: datetime
    last_update: datetime


@dataclass
class Trade:
    """交易记录"""
    id: str
    timestamp: datetime
    symbol: str
    side: str  # buy/sell
    quantity: int
    price: float
    commission: float
    pnl: float
    position_before: int
    position_after: int


class BacktestEngine:
    """回测引擎"""
    
    def __init__(self, backtest: Backtest, db_session):
        self.backtest = backtest
        self.db_session = db_session
        self.service = BacktestService(db_session)
        
        # 回测状态
        self.is_running = False
        self.is_paused = False
        self.current_date = None
        self.progress = 0.0
        
        # 资金管理
        self.initial_capital = float(backtest.initial_capital)
        self.current_capital = self.initial_capital
        self.available_cash = self.initial_capital
        
        # 持仓管理
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        
        # 性能统计
        self.equity_curve = []
        self.drawdown_curve = []
        self.daily_returns = []
        
        # 策略相关
        self.strategy_code = None
        self.strategy_function = None
        
        # 数据相关
        self.market_data: Dict[str, pd.DataFrame] = {}
        self.current_data: Dict[str, Dict] = {}
        
        # 回调函数
        self.progress_callback: Optional[Callable] = None
        self.signal_callback: Optional[Callable] = None
    
    async def initialize(self):
        """初始化回测引擎"""
        try:
            logger.info(f"初始化回测引擎: {self.backtest.id}")
            
            # 加载策略代码
            await self._load_strategy()
            
            # 加载历史数据
            await self._load_market_data()
            
            # 初始化状态
            self.current_date = self.backtest.start_date
            self.progress = 0.0
            
            # 更新回测状态
            await self._update_status(BacktestStatus.RUNNING, 0.0)
            
            logger.info("回测引擎初始化完成")
            
        except Exception as e:
            logger.error(f"初始化回测引擎失败: {str(e)}")
            await self._update_status(BacktestStatus.FAILED, error_message=str(e))
            raise
    
    async def run(self):
        """运行回测"""
        try:
            self.is_running = True
            logger.info(f"开始运行回测: {self.backtest.id}")
            
            # 计算总天数
            total_days = (self.backtest.end_date - self.backtest.start_date).days
            current_day = 0
            
            # 按日期遍历
            current_date = self.backtest.start_date
            while current_date <= self.backtest.end_date and self.is_running:
                
                # 检查是否暂停
                if self.is_paused:
                    await asyncio.sleep(1)
                    continue
                
                # 更新当前日期
                self.current_date = current_date
                
                # 获取当日数据
                await self._update_current_data(current_date)
                
                # 生成交易信号
                signals = await self._generate_signals(current_date)
                
                # 执行交易
                for signal in signals:
                    await self._execute_signal(signal)
                
                # 更新持仓和资金
                await self._update_portfolio(current_date)
                
                # 记录每日数据
                await self._record_daily_data(current_date)
                
                # 更新进度
                current_day += 1
                self.progress = (current_day / total_days) * 100
                
                if current_day % 10 == 0:  # 每10天更新一次进度
                    await self._update_status(BacktestStatus.RUNNING, self.progress)
                
                # 调用进度回调
                if self.progress_callback:
                    await self.progress_callback(self.progress, current_date)
                
                # 移动到下一天
                current_date += timedelta(days=1)
            
            # 完成回测
            if self.is_running:
                await self._finalize_backtest()
                await self._update_status(BacktestStatus.COMPLETED, 100.0)
                logger.info(f"回测完成: {self.backtest.id}")
            
        except Exception as e:
            logger.error(f"运行回测失败: {str(e)}")
            await self._update_status(BacktestStatus.FAILED, error_message=str(e))
            raise
        finally:
            self.is_running = False
    
    async def pause(self):
        """暂停回测"""
        self.is_paused = True
        await self._update_status(BacktestStatus.PAUSED, self.progress)
        logger.info(f"回测已暂停: {self.backtest.id}")
    
    async def resume(self):
        """恢复回测"""
        self.is_paused = False
        await self._update_status(BacktestStatus.RUNNING, self.progress)
        logger.info(f"回测已恢复: {self.backtest.id}")
    
    async def stop(self):
        """停止回测"""
        self.is_running = False
        self.is_paused = False
        await self._update_status(BacktestStatus.CANCELLED, self.progress)
        logger.info(f"回测已停止: {self.backtest.id}")
    
    async def _load_strategy(self):
        """加载策略代码"""
        try:
            # 获取策略代码
            if self.backtest.strategy_version_id:
                # 使用指定版本
                strategy_version = self.db_session.query(StrategyVersion).filter(
                    StrategyVersion.id == self.backtest.strategy_version_id
                ).first()
                self.strategy_code = strategy_version.code
            else:
                # 使用当前版本
                strategy = self.db_session.query(Strategy).filter(
                    Strategy.id == self.backtest.strategy_id
                ).first()
                self.strategy_code = strategy.code
            
            # 编译策略函数（简化版本，实际需要更复杂的沙箱环境）
            # 这里只是示例，实际应该使用安全的代码执行环境
            logger.info("策略代码加载完成")
            
        except Exception as e:
            logger.error(f"加载策略代码失败: {str(e)}")
            raise
    
    async def _load_market_data(self):
        """加载历史数据"""
        try:
            # 这里应该从数据源加载历史数据
            # 简化版本，实际需要连接到数据提供商
            for symbol in self.backtest.symbols:
                # 模拟数据加载
                date_range = pd.date_range(
                    start=self.backtest.start_date,
                    end=self.backtest.end_date,
                    freq='D'
                )
                
                # 生成模拟数据（实际应该从真实数据源获取）
                np.random.seed(42)  # 确保可重复性
                prices = 100 * np.exp(np.cumsum(np.random.randn(len(date_range)) * 0.02))
                
                self.market_data[symbol] = pd.DataFrame({
                    'date': date_range,
                    'open': prices * (1 + np.random.randn(len(date_range)) * 0.01),
                    'high': prices * (1 + np.abs(np.random.randn(len(date_range))) * 0.02),
                    'low': prices * (1 - np.abs(np.random.randn(len(date_range))) * 0.02),
                    'close': prices,
                    'volume': np.random.randint(1000, 10000, len(date_range))
                }).set_index('date')
            
            logger.info(f"历史数据加载完成，共{len(self.backtest.symbols)}个标的")
            
        except Exception as e:
            logger.error(f"加载历史数据失败: {str(e)}")
            raise
    
    async def _update_current_data(self, date: datetime):
        """更新当前日期的数据"""
        self.current_data = {}
        for symbol in self.backtest.symbols:
            if date in self.market_data[symbol].index:
                self.current_data[symbol] = self.market_data[symbol].loc[date].to_dict()
    
    async def _generate_signals(self, date: datetime) -> List[TradingSignal]:
        """生成交易信号"""
        signals = []
        
        # 简化的信号生成逻辑（实际应该执行策略代码）
        for symbol in self.backtest.symbols:
            if symbol in self.current_data:
                data = self.current_data[symbol]
                
                # 简单的移动平均策略示例
                if len(self.equity_curve) > 20:
                    recent_prices = [self.market_data[symbol].loc[d]['close'] 
                                   for d in self.market_data[symbol].index[-20:]]
                    ma_short = np.mean(recent_prices[-5:])
                    ma_long = np.mean(recent_prices[-20:])
                    
                    if ma_short > ma_long and symbol not in self.positions:
                        # 买入信号
                        signals.append(TradingSignal(
                            timestamp=date,
                            symbol=symbol,
                            signal_type=SignalType.BUY,
                            price=data['close'],
                            quantity=100
                        ))
                    elif ma_short < ma_long and symbol in self.positions:
                        # 卖出信号
                        signals.append(TradingSignal(
                            timestamp=date,
                            symbol=symbol,
                            signal_type=SignalType.SELL,
                            price=data['close'],
                            quantity=self.positions[symbol].quantity
                        ))
        
        return signals
    
    async def _execute_signal(self, signal: TradingSignal):
        """执行交易信号"""
        try:
            # 计算手续费
            commission = max(
                signal.price * signal.quantity * self.backtest.commission_rate,
                self.backtest.min_commission
            )
            
            # 计算滑点
            slippage = signal.price * self.backtest.slippage_rate
            actual_price = signal.price + (slippage if signal.signal_type == SignalType.BUY else -slippage)
            
            if signal.signal_type == SignalType.BUY:
                # 买入
                total_cost = actual_price * signal.quantity + commission
                
                if total_cost <= self.available_cash:
                    # 执行买入
                    if signal.symbol in self.positions:
                        # 加仓
                        pos = self.positions[signal.symbol]
                        new_quantity = pos.quantity + signal.quantity
                        new_avg_price = ((pos.avg_price * pos.quantity) + (actual_price * signal.quantity)) / new_quantity
                        pos.quantity = new_quantity
                        pos.avg_price = new_avg_price
                    else:
                        # 开仓
                        self.positions[signal.symbol] = Position(
                            symbol=signal.symbol,
                            quantity=signal.quantity,
                            avg_price=actual_price,
                            current_price=actual_price,
                            unrealized_pnl=0.0,
                            realized_pnl=0.0,
                            entry_time=signal.timestamp,
                            last_update=signal.timestamp
                        )
                    
                    self.available_cash -= total_cost
                    
                    # 记录交易
                    trade = Trade(
                        id=f"trade_{len(self.trades) + 1}",
                        timestamp=signal.timestamp,
                        symbol=signal.symbol,
                        side="buy",
                        quantity=signal.quantity,
                        price=actual_price,
                        commission=commission,
                        pnl=0.0,
                        position_before=self.positions[signal.symbol].quantity - signal.quantity,
                        position_after=self.positions[signal.symbol].quantity
                    )
                    self.trades.append(trade)
            
            elif signal.signal_type == SignalType.SELL:
                # 卖出
                if signal.symbol in self.positions:
                    pos = self.positions[signal.symbol]
                    sell_quantity = min(signal.quantity, pos.quantity)
                    
                    if sell_quantity > 0:
                        # 执行卖出
                        total_proceeds = actual_price * sell_quantity - commission
                        pnl = (actual_price - pos.avg_price) * sell_quantity - commission
                        
                        pos.quantity -= sell_quantity
                        pos.realized_pnl += pnl
                        self.available_cash += total_proceeds
                        
                        # 如果全部卖出，移除持仓
                        if pos.quantity == 0:
                            del self.positions[signal.symbol]
                        
                        # 记录交易
                        trade = Trade(
                            id=f"trade_{len(self.trades) + 1}",
                            timestamp=signal.timestamp,
                            symbol=signal.symbol,
                            side="sell",
                            quantity=sell_quantity,
                            price=actual_price,
                            commission=commission,
                            pnl=pnl,
                            position_before=pos.quantity + sell_quantity,
                            position_after=pos.quantity
                        )
                        self.trades.append(trade)
            
        except Exception as e:
            logger.error(f"执行交易信号失败: {str(e)}")
    
    async def _update_portfolio(self, date: datetime):
        """更新投资组合"""
        # 更新持仓市值
        total_market_value = self.available_cash
        
        for symbol, position in self.positions.items():
            if symbol in self.current_data:
                current_price = self.current_data[symbol]['close']
                position.current_price = current_price
                position.unrealized_pnl = (current_price - position.avg_price) * position.quantity
                position.last_update = date
                
                total_market_value += current_price * position.quantity
        
        self.current_capital = total_market_value
    
    async def _record_daily_data(self, date: datetime):
        """记录每日数据"""
        # 记录净值曲线
        self.equity_curve.append({
            'date': date.isoformat(),
            'equity': self.current_capital,
            'cash': self.available_cash,
            'return': (self.current_capital - self.initial_capital) / self.initial_capital
        })
        
        # 计算回撤
        if len(self.equity_curve) > 1:
            peak = max([point['equity'] for point in self.equity_curve])
            drawdown = (self.current_capital - peak) / peak
            self.drawdown_curve.append({
                'date': date.isoformat(),
                'drawdown': drawdown
            })
        
        # 计算日收益率
        if len(self.equity_curve) > 1:
            prev_equity = self.equity_curve[-2]['equity']
            daily_return = (self.current_capital - prev_equity) / prev_equity
            self.daily_returns.append({
                'date': date.isoformat(),
                'return': daily_return
            })
    
    async def _finalize_backtest(self):
        """完成回测，计算最终统计"""
        try:
            # 计算性能指标
            results = self._calculate_performance_metrics()
            
            # 保存结果到数据库
            await self.service.update_backtest_results(self.backtest.id, results)
            
            logger.info("回测结果计算完成")
            
        except Exception as e:
            logger.error(f"完成回测失败: {str(e)}")
            raise
    
    def _calculate_performance_metrics(self) -> Dict[str, Any]:
        """计算性能指标"""
        if not self.equity_curve:
            return {}
        
        # 基础统计
        total_return = (self.current_capital - self.initial_capital) / self.initial_capital
        
        # 年化收益率
        days = len(self.equity_curve)
        annual_return = (1 + total_return) ** (365 / days) - 1 if days > 0 else 0
        
        # 最大回撤
        max_drawdown = min([point['drawdown'] for point in self.drawdown_curve]) if self.drawdown_curve else 0
        
        # 夏普比率
        if self.daily_returns:
            returns = [point['return'] for point in self.daily_returns]
            sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
        else:
            sharpe_ratio = 0
        
        # 交易统计
        winning_trades = len([t for t in self.trades if t.pnl > 0])
        losing_trades = len([t for t in self.trades if t.pnl < 0])
        win_rate = winning_trades / len(self.trades) if self.trades else 0
        
        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'max_drawdown': abs(max_drawdown),
            'sharpe_ratio': sharpe_ratio,
            'total_trades': len(self.trades),
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'equity_curve': self.equity_curve,
            'drawdown_curve': self.drawdown_curve,
            'trades_detail': [
                {
                    'id': t.id,
                    'timestamp': t.timestamp.isoformat(),
                    'symbol': t.symbol,
                    'side': t.side,
                    'quantity': t.quantity,
                    'price': t.price,
                    'commission': t.commission,
                    'pnl': t.pnl
                } for t in self.trades
            ],
            'daily_returns': self.daily_returns,
            'positions': [
                {
                    'symbol': pos.symbol,
                    'quantity': pos.quantity,
                    'avg_price': pos.avg_price,
                    'current_price': pos.current_price,
                    'unrealized_pnl': pos.unrealized_pnl,
                    'realized_pnl': pos.realized_pnl
                } for pos in self.positions.values()
            ]
        }
    
    async def _update_status(self, status: BacktestStatus, progress: Optional[float] = None, 
                           error_message: Optional[str] = None):
        """更新回测状态"""
        try:
            self.service.update_backtest_status(
                self.backtest.id, 
                status, 
                progress, 
                error_message
            )
        except Exception as e:
            logger.error(f"更新回测状态失败: {str(e)}")


# 回测任务管理器
class BacktestTaskManager:
    """回测任务管理器"""
    
    def __init__(self):
        self.running_tasks: Dict[int, BacktestEngine] = {}
    
    async def start_backtest(self, backtest: Backtest, db_session) -> BacktestEngine:
        """启动回测任务"""
        if backtest.id in self.running_tasks:
            raise ValueError("回测任务已在运行中")
        
        engine = BacktestEngine(backtest, db_session)
        self.running_tasks[backtest.id] = engine
        
        try:
            await engine.initialize()
            # 在后台运行回测
            asyncio.create_task(self._run_backtest_task(engine))
            return engine
        except Exception as e:
            if backtest.id in self.running_tasks:
                del self.running_tasks[backtest.id]
            raise
    
    async def _run_backtest_task(self, engine: BacktestEngine):
        """运行回测任务"""
        try:
            await engine.run()
        except Exception as e:
            logger.error(f"回测任务执行失败: {str(e)}")
        finally:
            # 清理任务
            if engine.backtest.id in self.running_tasks:
                del self.running_tasks[engine.backtest.id]
    
    async def pause_backtest(self, backtest_id: int):
        """暂停回测"""
        if backtest_id in self.running_tasks:
            await self.running_tasks[backtest_id].pause()
    
    async def resume_backtest(self, backtest_id: int):
        """恢复回测"""
        if backtest_id in self.running_tasks:
            await self.running_tasks[backtest_id].resume()
    
    async def stop_backtest(self, backtest_id: int):
        """停止回测"""
        if backtest_id in self.running_tasks:
            await self.running_tasks[backtest_id].stop()
    
    def get_running_backtests(self) -> List[int]:
        """获取运行中的回测列表"""
        return list(self.running_tasks.keys())


# 全局任务管理器实例
backtest_task_manager = BacktestTaskManager()