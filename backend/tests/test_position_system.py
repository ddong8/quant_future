"""
持仓系统测试
"""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.position import Position, PositionHistory, PositionType, PositionStatus
from app.models.user import User
from app.models.order import Order, OrderFill, OrderSide, OrderType, OrderStatus
from app.services.position_service import PositionService, PositionCalculationService
from app.utils.position_calculator import PositionCalculator, PositionRiskAnalyzer
from app.core.security import get_password_hash

class TestPositionModel:
    """持仓模型测试"""
    
    def test_position_creation(self, db: Session):
        """测试持仓创建"""
        # 创建用户
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=get_password_hash("password"),
            full_name="Test User"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # 创建持仓
        position = Position(
            symbol="AAPL",
            position_type=PositionType.LONG,
            quantity=Decimal('100'),
            average_cost=Decimal('150.00'),
            user_id=user.id
        )
        db.add(position)
        db.commit()
        db.refresh(position)
        
        assert position.symbol == "AAPL"
        assert position.position_type == PositionType.LONG
        assert position.quantity == Decimal('100')
        assert position.average_cost == Decimal('150.00')
        assert position.is_long == True
        assert position.is_open == True
    
    def test_position_add_trade(self, db: Session):
        """测试添加交易到持仓"""
        # 创建用户
        user = User(
            username="testuser2",
            email="test2@example.com",
            hashed_password=get_password_hash("password"),
            full_name="Test User 2"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # 创建空持仓
        position = Position(
            symbol="TSLA",
            user_id=user.id
        )
        db.add(position)
        db.commit()
        db.refresh(position)
        
        # 添加买入交易
        position.add_trade(Decimal('50'), Decimal('200.00'), Decimal('5.00'))
        
        assert position.quantity == Decimal('50')
        assert position.average_cost == Decimal('200.10')  # (50*200+5)/50
        assert position.position_type == PositionType.LONG
        assert position.status == PositionStatus.OPEN
        
        # 添加加仓交易
        position.add_trade(Decimal('50'), Decimal('180.00'), Decimal('5.00'))
        
        assert position.quantity == Decimal('100')
        # 新平均成本 = (50*200.10 + 50*180 + 5) / 100
        expected_cost = (Decimal('50') * Decimal('200.10') + Decimal('50') * Decimal('180.00') + Decimal('5.00')) / Decimal('100')
        assert abs(position.average_cost - expected_cost) < Decimal('0.01')
    
    def test_position_partial_close(self, db: Session):
        """测试部分平仓"""
        # 创建用户
        user = User(
            username="testuser3",
            email="test3@example.com",
            hashed_password=get_password_hash("password"),
            full_name="Test User 3"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # 创建持仓
        position = Position(
            symbol="GOOGL",
            position_type=PositionType.LONG,
            quantity=Decimal('100'),
            average_cost=Decimal('2500.00'),
            total_cost=Decimal('250000.00'),
            user_id=user.id,
            status=PositionStatus.OPEN
        )
        db.add(position)
        db.commit()
        db.refresh(position)
        
        # 部分平仓（卖出30股，价格2600）
        position.add_trade(Decimal('-30'), Decimal('2600.00'), Decimal('10.00'))
        
        assert position.quantity == Decimal('70')
        assert position.status == PositionStatus.OPEN
        # 已实现盈亏 = 30 * (2600 - 2500) - 10 = 2990
        assert position.realized_pnl == Decimal('2990.00')
    
    def test_position_market_price_update(self, db: Session):
        """测试市场价格更新"""
        # 创建用户
        user = User(
            username="testuser4",
            email="test4@example.com",
            hashed_password=get_password_hash("password"),
            full_name="Test User 4"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # 创建持仓
        position = Position(
            symbol="MSFT",
            position_type=PositionType.LONG,
            quantity=Decimal('100'),
            average_cost=Decimal('300.00'),
            user_id=user.id
        )
        db.add(position)
        db.commit()
        db.refresh(position)
        
        # 更新市场价格
        position.update_market_price(Decimal('320.00'))
        
        assert position.current_price == Decimal('320.00')
        assert position.market_value == Decimal('32000.00')  # 100 * 320
        assert position.unrealized_pnl == Decimal('2000.00')  # 100 * (320 - 300)
    
    def test_stop_loss_trigger(self, db: Session):
        """测试止损触发"""
        # 创建用户
        user = User(
            username="testuser5",
            email="test5@example.com",
            hashed_password=get_password_hash("password"),
            full_name="Test User 5"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # 创建多头持仓
        position = Position(
            symbol="AMZN",
            position_type=PositionType.LONG,
            quantity=Decimal('10'),
            average_cost=Decimal('3000.00'),
            current_price=Decimal('3100.00'),
            stop_loss_price=Decimal('2900.00'),
            user_id=user.id
        )
        db.add(position)
        db.commit()
        db.refresh(position)
        
        # 价格下跌，未触发止损
        position.update_market_price(Decimal('2950.00'))
        assert position.check_stop_loss_trigger() == False
        
        # 价格继续下跌，触发止损
        position.update_market_price(Decimal('2890.00'))
        assert position.check_stop_loss_trigger() == True

class TestPositionService:
    """持仓服务测试"""
    
    def test_position_calculation_from_trades(self, db: Session):
        """测试从交易记录计算持仓"""
        # 创建用户
        user = User(
            username="trader1",
            email="trader1@example.com",
            hashed_password=get_password_hash("password"),
            full_name="Trader 1"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # 创建订单和成交记录
        order1 = Order(
            symbol="NVDA",
            side=OrderSide.BUY,
            type=OrderType.MARKET,
            quantity=Decimal('100'),
            status=OrderStatus.FILLED,
            user_id=user.id
        )
        db.add(order1)
        db.commit()
        db.refresh(order1)
        
        fill1 = OrderFill(
            order_id=order1.id,
            quantity=Decimal('100'),
            price=Decimal('400.00'),
            commission=Decimal('5.00')
        )
        db.add(fill1)
        
        order2 = Order(
            symbol="NVDA",
            side=OrderSide.BUY,
            type=OrderType.MARKET,
            quantity=Decimal('50'),
            status=OrderStatus.FILLED,
            user_id=user.id
        )
        db.add(order2)
        db.commit()
        db.refresh(order2)
        
        fill2 = OrderFill(
            order_id=order2.id,
            quantity=Decimal('50'),
            price=Decimal('420.00'),
            commission=Decimal('2.50')
        )
        db.add(fill2)
        db.commit()
        
        # 计算持仓
        calc_service = PositionCalculationService(db)
        position = calc_service.calculate_position_from_trades(user.id, "NVDA")
        
        assert position is not None
        assert position.symbol == "NVDA"
        assert position.quantity == Decimal('150')
        assert position.position_type == PositionType.LONG
        # 平均成本 = (100*400 + 5 + 50*420 + 2.5) / 150
        expected_cost = (Decimal('40000') + Decimal('5') + Decimal('21000') + Decimal('2.5')) / Decimal('150')
        assert abs(position.average_cost - expected_cost) < Decimal('0.01')
    
    def test_portfolio_metrics_calculation(self, db: Session):
        """测试投资组合指标计算"""
        # 创建用户
        user = User(
            username="portfolio_user",
            email="portfolio@example.com",
            hashed_password=get_password_hash("password"),
            full_name="Portfolio User"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # 创建多个持仓
        positions = [
            Position(
                symbol="AAPL",
                position_type=PositionType.LONG,
                quantity=Decimal('100'),
                average_cost=Decimal('150.00'),
                current_price=Decimal('160.00'),
                total_cost=Decimal('15000.00'),
                user_id=user.id,
                status=PositionStatus.OPEN
            ),
            Position(
                symbol="GOOGL",
                position_type=PositionType.LONG,
                quantity=Decimal('10'),
                average_cost=Decimal('2500.00'),
                current_price=Decimal('2600.00'),
                total_cost=Decimal('25000.00'),
                user_id=user.id,
                status=PositionStatus.OPEN
            )
        ]
        
        for pos in positions:
            pos.update_market_price(pos.current_price)
            db.add(pos)
        
        db.commit()
        
        # 计算投资组合指标
        calc_service = PositionCalculationService(db)
        metrics = calc_service.calculate_portfolio_metrics(user.id)
        
        assert metrics['total_positions'] == 2
        assert metrics['total_market_value'] == 42000.0  # 100*160 + 10*2600
        assert metrics['total_cost'] == 40000.0  # 15000 + 25000
        assert metrics['total_unrealized_pnl'] == 2000.0  # 100*10 + 10*100

class TestPositionCalculator:
    """持仓计算器测试"""
    
    def test_average_cost_calculation(self):
        """测试平均成本计算"""
        trades = [
            {'quantity': 100, 'price': 50.0, 'commission': 5.0},
            {'quantity': 50, 'price': 60.0, 'commission': 2.5},
            {'quantity': -30, 'price': 55.0, 'commission': 1.5}
        ]
        
        avg_cost, total_cost = PositionCalculator.calculate_average_cost(trades)
        
        # 买入150股，成本 = 100*50 + 5 + 50*60 + 2.5 = 8007.5
        # 卖出30股，平均成本 = 8007.5/150 = 53.383
        # 剩余120股，成本 = 120 * 53.383 = 6406
        # 扣除卖出手续费1.5，最终成本 = 6404.5
        # 平均成本 = 6404.5 / 120 = 53.371
        
        assert abs(float(avg_cost) - 53.371) < 0.01
        assert abs(float(total_cost) - 6404.5) < 0.1
    
    def test_pnl_calculation(self):
        """测试盈亏计算"""
        # 多头持仓
        unrealized_pnl, market_value = PositionCalculator.calculate_pnl(
            Decimal('100'), Decimal('50.0'), Decimal('55.0'), 'LONG'
        )
        
        assert unrealized_pnl == Decimal('500.0')  # 100 * (55 - 50)
        assert market_value == Decimal('5500.0')  # 100 * 55
        
        # 空头持仓
        unrealized_pnl, market_value = PositionCalculator.calculate_pnl(
            Decimal('100'), Decimal('50.0'), Decimal('45.0'), 'SHORT'
        )
        
        assert unrealized_pnl == Decimal('500.0')  # 100 * (50 - 45)
        assert market_value == Decimal('4500.0')  # 100 * 45
    
    def test_risk_metrics_calculation(self):
        """测试风险指标计算"""
        # 模拟价格历史
        price_history = [100, 102, 98, 105, 95, 110, 90, 115, 85, 120]
        
        metrics = PositionCalculator.calculate_risk_metrics(
            price_history, 100, 10000
        )
        
        assert 'volatility' in metrics
        assert 'var_95' in metrics
        assert 'var_99' in metrics
        assert 'max_drawdown' in metrics
        assert 'sharpe_ratio' in metrics
        
        # 检查指标合理性
        assert metrics['volatility'] >= 0
        assert metrics['max_drawdown'] <= 0  # 回撤应该是负数或0
    
    def test_position_concentration(self):
        """测试持仓集中度计算"""
        positions = [
            {'symbol': 'AAPL', 'market_value': 50000},
            {'symbol': 'GOOGL', 'market_value': 30000},
            {'symbol': 'MSFT', 'market_value': 20000}
        ]
        
        concentration = PositionCalculator.calculate_position_concentration(positions)
        
        assert 'herfindahl_index' in concentration
        assert 'top_5_concentration' in concentration
        assert 'max_position_weight' in concentration
        
        # 最大持仓权重应该是50%
        assert abs(concentration['max_position_weight'] - 0.5) < 0.01
        
        # 前5大集中度应该是100%（只有3个持仓）
        assert concentration['top_5_concentration'] == 1.0
    
    def test_optimal_position_size(self):
        """测试最优持仓规模计算"""
        position_size = PositionCalculator.calculate_optimal_position_size(
            account_balance=100000,
            risk_per_trade=0.02,  # 2%风险
            entry_price=100,
            stop_loss_price=95
        )
        
        # 风险金额 = 100000 * 0.02 = 2000
        # 每股风险 = 100 - 95 = 5
        # 持仓数量 = 2000 / 5 = 400
        assert position_size == 400.0
    
    def test_kelly_criterion(self):
        """测试凯利公式计算"""
        kelly_fraction = PositionCalculator.calculate_kelly_criterion(
            win_rate=0.6,
            avg_win=15.0,
            avg_loss=10.0
        )
        
        # 凯利公式: f = (bp - q) / b
        # b = 15/10 = 1.5, p = 0.6, q = 0.4
        # f = (1.5*0.6 - 0.4) / 1.5 = (0.9 - 0.4) / 1.5 = 0.333
        assert abs(kelly_fraction - 0.333) < 0.01

class TestPositionRiskAnalyzer:
    """持仓风险分析器测试"""
    
    def test_position_risk_analysis(self):
        """测试持仓风险分析"""
        analyzer = PositionRiskAnalyzer()
        
        position_data = {
            'id': 1,
            'symbol': 'AAPL',
            'quantity': 100,
            'total_cost': 15000,
            'market_value': 16000,
            'stop_loss_price': None,
            'opened_at': '2023-01-01T00:00:00'
        }
        
        price_history = [150, 152, 148, 155, 145, 160, 140, 165, 135, 170]
        
        risk_analysis = analyzer.analyze_position_risk(position_data, price_history)
        
        assert 'risk_level' in risk_analysis
        assert 'risk_score' in risk_analysis
        assert 'risk_factors' in risk_analysis
        assert 'recommendations' in risk_analysis
        assert 'risk_metrics' in risk_analysis
        
        # 应该检测到未设置止损的风险
        assert '未设置止损' in risk_analysis['risk_factors']
        assert '建议设置止损价格' in risk_analysis['recommendations']
    
    def test_risk_report_generation(self):
        """测试风险报告生成"""
        analyzer = PositionRiskAnalyzer()
        
        positions = [
            {
                'id': 1,
                'symbol': 'AAPL',
                'market_value': 50000,
                'total_pnl': 5000,
                'stop_loss_price': 145
            },
            {
                'id': 2,
                'symbol': 'GOOGL',
                'market_value': 30000,
                'total_pnl': -2000,
                'stop_loss_price': None
            }
        ]
        
        market_data = {
            'price_history': {
                'AAPL': [150, 152, 148, 155, 160],
                'GOOGL': [2500, 2520, 2480, 2460, 2400]
            }
        }
        
        report = analyzer.generate_risk_report(positions, market_data)
        
        assert 'report_date' in report
        assert 'portfolio_summary' in report
        assert 'risk_analysis' in report
        assert 'position_risks' in report
        assert 'recommendations' in report
        
        # 检查投资组合摘要
        assert report['portfolio_summary']['total_positions'] == 2
        assert report['portfolio_summary']['total_value'] == 80000
        assert report['portfolio_summary']['total_pnl'] == 3000

@pytest.fixture
def db():
    """数据库会话fixture"""
    from app.core.database import SessionLocal, engine
    from app.models import Base
    
    # 创建测试数据库表
    Base.metadata.create_all(bind=engine)
    
    # 创建会话
    session = SessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        # 清理测试数据
        Base.metadata.drop_all(bind=engine)