"""
回测引擎测试用例
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
import pandas as pd
import numpy as np

from app.services.backtest_engine import (
    BacktestEngine,
    BacktestDataReplay,
    BacktestTradeExecutor,
    BacktestPortfolioManager,
    BacktestProgressTracker,
    BacktestContext,
    OrderType,
    OrderSide,
    OrderStatus,
)
from app.services.history_service import HistoryService
from app.models import Backtest, Strategy
from app.models.enums import BacktestStatus


class TestBacktestDataReplay:
    """数据回放引擎测试"""
    
    def setup_method(self):
        self.history_service_mock = Mock(spec=HistoryService)
        self.data_replay = BacktestDataReplay(self.history_service_mock)
    
    @pytest.mark.asyncio
    async def test_load_data(self):
        """测试数据加载"""
        # 模拟历史数据
        mock_klines = [
            Mock(datetime=datetime(2024, 1, 1, 9, 0), open=70000, high=70100, low=69900, close=70050, volume=1000),
            Mock(datetime=datetime(2024, 1, 1, 9, 1), open=70050, high=70150, low=70000, close=70100, volume=1200),
        ]
        
        self.history_service_mock.get_klines = AsyncMock(return_value=mock_klines)
        
        symbols = ["SHFE.cu2401"]
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 2)
        
        data = await self.data_replay.load_data(symbols, start_date, end_date)
        
        assert "SHFE.cu2401" in data
        assert len(data["SHFE.cu2401"]) == 2
        assert data["SHFE.cu2401"].iloc[0]['open'] == 70000
    
    def test_get_bar_data(self):
        """测试获取K线数据"""
        # 准备测试数据
        df = pd.DataFrame({
            'open': [70000, 70050],
            'high': [70100, 70150],
            'low': [69900, 70000],
            'close': [70050, 70100],
            'volume': [1000, 1200],
            'open_interest': [50000, 50100]
        }, index=[
            datetime(2024, 1, 1, 9, 0),
            datetime(2024, 1, 1, 9, 1)
        ])
        
        self.data_replay.data_cache = {"SHFE.cu2401": df}
        
        # 测试获取数据
        bar_data = self.data_replay.get_bar_data("SHFE.cu2401", datetime(2024, 1, 1, 9, 1))
        
        assert bar_data is not None
        assert bar_data['symbol'] == "SHFE.cu2401"
        assert bar_data['close'] == 70100
    
    def test_get_historical_bars(self):
        """测试获取历史K线数据"""
        # 准备测试数据
        df = pd.DataFrame({
            'open': [70000, 70050, 70100],
            'high': [70100, 70150, 70200],
            'low': [69900, 70000, 70050],
            'close': [70050, 70100, 70150],
            'volume': [1000, 1200, 1100],
            'open_interest': [50000, 50100, 50200]
        }, index=[
            datetime(2024, 1, 1, 9, 0),
            datetime(2024, 1, 1, 9, 1),
            datetime(2024, 1, 1, 9, 2)
        ])
        
        self.data_replay.data_cache = {"SHFE.cu2401": df}
        
        # 测试获取历史数据
        bars = self.data_replay.get_historical_bars("SHFE.cu2401", datetime(2024, 1, 1, 9, 2), 2)
        
        assert len(bars) == 2
        assert bars[-1]['close'] == 70150


class TestBacktestTradeExecutor:
    """交易执行器测试"""
    
    def setup_method(self):
        self.executor = BacktestTradeExecutor()
    
    def test_create_order(self):
        """测试创建订单"""
        order = self.executor.create_order(
            symbol="SHFE.cu2401",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=10
        )
        
        assert order.symbol == "SHFE.cu2401"
        assert order.side == OrderSide.BUY
        assert order.order_type == OrderType.MARKET
        assert order.quantity == 10
        assert order.status == OrderStatus.PENDING
        assert len(self.executor.pending_orders) == 1
    
    def test_process_market_order(self):
        """测试处理市价单"""
        # 创建市价单
        order = self.executor.create_order(
            symbol="SHFE.cu2401",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=10
        )
        
        # 模拟市场数据
        market_data = {
            "SHFE.cu2401": {
                'open': 70000,
                'high': 70100,
                'low': 69900,
                'close': 70050,
                'volume': 1000
            }
        }
        
        # 处理订单
        self.executor.process_orders(datetime.utcnow(), market_data)
        
        # 验证订单已成交
        assert order.status == OrderStatus.FILLED
        assert order.filled_price is not None
        assert order.filled_quantity == 10
        assert len(self.executor.pending_orders) == 0
        assert len(self.executor.filled_orders) == 1
    
    def test_process_limit_order(self):
        """测试处理限价单"""
        # 创建限价买单
        order = self.executor.create_order(
            symbol="SHFE.cu2401",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=10,
            price=69950
        )
        
        # 模拟市场数据（价格未达到限价）
        market_data = {
            "SHFE.cu2401": {
                'open': 70000,
                'high': 70100,
                'low': 70000,  # 最低价高于限价
                'close': 70050,
                'volume': 1000
            }
        }
        
        # 处理订单
        self.executor.process_orders(datetime.utcnow(), market_data)
        
        # 验证订单未成交
        assert order.status == OrderStatus.PENDING
        assert len(self.executor.pending_orders) == 1
        
        # 模拟价格达到限价
        market_data["SHFE.cu2401"]['low'] = 69900  # 最低价低于限价
        
        # 再次处理订单
        self.executor.process_orders(datetime.utcnow(), market_data)
        
        # 验证订单已成交
        assert order.status == OrderStatus.FILLED
        assert order.filled_price == 69950
    
    def test_cancel_order(self):
        """测试撤销订单"""
        order = self.executor.create_order(
            symbol="SHFE.cu2401",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=10,
            price=69950
        )
        
        order_id = order.id
        
        # 撤销订单
        success = self.executor.cancel_order(order_id)
        
        assert success == True
        assert order.status == OrderStatus.CANCELLED
        assert len(self.executor.pending_orders) == 0


class TestBacktestPortfolioManager:
    """投资组合管理器测试"""
    
    def setup_method(self):
        self.portfolio_manager = BacktestPortfolioManager(1000000)  # 100万初始资金
    
    def test_initial_state(self):
        """测试初始状态"""
        account = self.portfolio_manager.get_account_info()
        
        assert account.initial_capital == 1000000
        assert account.available_cash == 1000000
        assert account.total_value == 1000000
        assert len(account.positions) == 0
    
    def test_update_position_buy(self):
        """测试买入更新持仓"""
        from app.services.backtest_engine import BacktestOrder
        
        # 创建买入订单
        order = BacktestOrder(
            id="order_1",
            symbol="SHFE.cu2401",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=10,
            filled_price=70000,
            filled_quantity=10,
            commission=210  # 手续费
        )
        order.status = OrderStatus.FILLED
        
        # 更新持仓
        self.portfolio_manager.update_position(order)
        
        # 验证持仓
        position = self.portfolio_manager.get_position("SHFE.cu2401")
        assert position.quantity == 10
        assert position.avg_price == 70000
        
        # 验证账户
        account = self.portfolio_manager.get_account_info()
        assert account.available_cash == 1000000 - 210  # 扣除手续费
        assert account.commission_paid == 210
    
    def test_update_position_sell(self):
        """测试卖出更新持仓"""
        from app.services.backtest_engine import BacktestOrder
        
        # 先买入建立持仓
        buy_order = BacktestOrder(
            id="order_1",
            symbol="SHFE.cu2401",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=10,
            filled_price=70000,
            filled_quantity=10,
            commission=210
        )
        buy_order.status = OrderStatus.FILLED
        self.portfolio_manager.update_position(buy_order)
        
        # 卖出部分持仓
        sell_order = BacktestOrder(
            id="order_2",
            symbol="SHFE.cu2401",
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            quantity=5,
            filled_price=70500,
            filled_quantity=5,
            commission=105.75
        )
        sell_order.status = OrderStatus.FILLED
        self.portfolio_manager.update_position(sell_order)
        
        # 验证持仓
        position = self.portfolio_manager.get_position("SHFE.cu2401")
        assert position.quantity == 5
        assert position.realized_pnl == (70500 - 70000) * 5  # 实现盈亏
    
    def test_update_market_value(self):
        """测试更新市值"""
        from app.services.backtest_engine import BacktestOrder
        
        # 建立持仓
        order = BacktestOrder(
            id="order_1",
            symbol="SHFE.cu2401",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=10,
            filled_price=70000,
            filled_quantity=10,
            commission=210
        )
        order.status = OrderStatus.FILLED
        self.portfolio_manager.update_position(order)
        
        # 更新市值
        market_data = {
            "SHFE.cu2401": {
                'close': 71000  # 价格上涨
            }
        }
        
        self.portfolio_manager.update_market_value(market_data)
        
        # 验证持仓和账户
        position = self.portfolio_manager.get_position("SHFE.cu2401")
        assert position.market_value == 10 * 71000
        assert position.unrealized_pnl == (71000 - 70000) * 10  # 未实现盈亏
        
        account = self.portfolio_manager.get_account_info()
        expected_total_value = 1000000 + (71000 - 70000) * 10 - 210
        assert account.total_value == expected_total_value


class TestBacktestProgressTracker:
    """进度跟踪器测试"""
    
    def test_progress_tracking(self):
        """测试进度跟踪"""
        callback_calls = []
        
        def progress_callback(progress):
            callback_calls.append(progress)
        
        tracker = BacktestProgressTracker(100, progress_callback)
        
        # 更新进度
        tracker.update_progress(25)
        assert tracker.get_progress() == 25.0
        assert callback_calls[-1] == 25.0
        
        tracker.update_progress(50)
        assert tracker.get_progress() == 50.0
        assert callback_calls[-1] == 50.0
        
        tracker.update_progress(100)
        assert tracker.get_progress() == 100.0
        assert callback_calls[-1] == 100.0
    
    def test_eta_calculation(self):
        """测试完成时间估算"""
        tracker = BacktestProgressTracker(100)
        
        # 初始状态没有ETA
        assert tracker.get_eta() is None
        
        # 更新进度后有ETA
        tracker.update_progress(50)
        eta = tracker.get_eta()
        assert eta is not None
        assert eta > datetime.utcnow()


class TestBacktestContext:
    """回测上下文测试"""
    
    def setup_method(self):
        self.backtest_engine_mock = Mock(spec=BacktestEngine)
        self.context = BacktestContext(
            backtest_engine=self.backtest_engine_mock,
            symbols=["SHFE.cu2401"],
            parameters={"period": 20}
        )
    
    def test_get_klines(self):
        """测试获取K线数据"""
        # 模拟数据回放器
        mock_data_replay = Mock()
        mock_data_replay.current_time = datetime(2024, 1, 1, 9, 30)
        mock_data_replay.get_historical_bars.return_value = [
            {'datetime': datetime(2024, 1, 1, 9, 0), 'close': 70000},
            {'datetime': datetime(2024, 1, 1, 9, 1), 'close': 70050},
        ]
        
        self.backtest_engine_mock.data_replay = mock_data_replay
        
        klines = self.context.get_klines("SHFE.cu2401", 100)
        
        assert len(klines) == 2
        assert klines[0]['close'] == 70000
        mock_data_replay.get_historical_bars.assert_called_once_with(
            "SHFE.cu2401", datetime(2024, 1, 1, 9, 30), 100
        )
    
    def test_get_position(self):
        """测试获取持仓"""
        from app.services.backtest_engine import BacktestPosition
        
        mock_position = BacktestPosition(
            symbol="SHFE.cu2401",
            quantity=10,
            avg_price=70000,
            market_value=700000,
            unrealized_pnl=5000,
            realized_pnl=2000
        )
        
        mock_portfolio_manager = Mock()
        mock_portfolio_manager.get_position.return_value = mock_position
        
        self.backtest_engine_mock.portfolio_manager = mock_portfolio_manager
        
        position = self.context.get_position("SHFE.cu2401")
        
        assert position['symbol'] == "SHFE.cu2401"
        assert position['quantity'] == 10
        assert position['avg_price'] == 70000
        assert position['unrealized_pnl'] == 5000
    
    def test_order_target_percent(self):
        """测试按百分比下单"""
        from app.services.backtest_engine import BacktestAccount, BacktestPosition
        
        # 模拟账户信息
        mock_account = BacktestAccount(
            initial_capital=1000000,
            available_cash=900000,
            total_value=1100000,
            positions={}
        )
        
        mock_portfolio_manager = Mock()
        mock_portfolio_manager.get_account_info.return_value = mock_account
        mock_portfolio_manager.get_position.return_value = BacktestPosition(symbol="SHFE.cu2401")
        
        # 模拟数据回放器
        mock_data_replay = Mock()
        mock_data_replay.current_time = datetime(2024, 1, 1, 9, 30)
        mock_data_replay.get_bar_data.return_value = {
            'close': 70000
        }
        
        # 模拟交易执行器
        mock_trade_executor = Mock()
        
        self.backtest_engine_mock.portfolio_manager = mock_portfolio_manager
        self.backtest_engine_mock.data_replay = mock_data_replay
        self.backtest_engine_mock.trade_executor = mock_trade_executor
        
        # 执行按百分比下单
        self.context.order_target_percent("SHFE.cu2401", 0.5)  # 50%仓位
        
        # 验证创建了订单
        mock_trade_executor.create_order.assert_called_once()
        call_args = mock_trade_executor.create_order.call_args
        
        assert call_args[1]['symbol'] == "SHFE.cu2401"
        assert call_args[1]['side'] == OrderSide.BUY
        assert call_args[1]['order_type'] == OrderType.MARKET


# 集成测试
class TestBacktestEngineIntegration:
    """回测引擎集成测试"""
    
    @pytest.mark.asyncio
    async def test_simple_backtest_workflow(self):
        """测试简单的回测工作流"""
        # 这是一个简化的集成测试示例
        # 实际测试需要更完整的数据和环境设置
        
        # 模拟策略代码
        strategy_code = '''
def initialize(context):
    context.symbol = "SHFE.cu2401"

def handle_bar(context, bar_dict):
    if context.symbol in bar_dict:
        current_price = bar_dict[context.symbol]['close']
        if current_price > 70000:
            context.order_target_percent(context.symbol, 0.5)
        else:
            context.order_target_percent(context.symbol, 0.0)
'''
        
        # 模拟数据库和服务
        db_mock = Mock()
        history_service_mock = Mock(spec=HistoryService)
        
        # 创建回测引擎
        engine = BacktestEngine(db_mock, history_service_mock)
        
        # 这里需要更多的模拟设置来完成完整的集成测试
        # 由于涉及异步操作和复杂的数据流，实际的集成测试会更复杂
        
        print("集成测试框架已建立，需要完整的测试环境来运行")


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])