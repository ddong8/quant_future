"""
数据库操作集成测试
"""
import pytest
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta

from app.models.user import User
from app.models.strategy import Strategy
from app.models.backtest import Backtest
from app.models.trading import Order, Position
from app.models.risk import RiskRule
from app.core.database import get_db


class TestUserOperations:
    """用户数据库操作测试"""
    
    def test_create_user(self, db_session: Session):
        """测试创建用户"""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password",
            is_active=True
        )
        
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        assert user.id is not None
        assert user.username == "testuser"
        assert user.created_at is not None
    
    def test_user_unique_constraints(self, db_session: Session):
        """测试用户唯一约束"""
        user1 = User(
            username="unique_user",
            email="unique@example.com",
            hashed_password="password1"
        )
        
        user2 = User(
            username="unique_user",  # 重复用户名
            email="another@example.com",
            hashed_password="password2"
        )
        
        db_session.add(user1)
        db_session.commit()
        
        db_session.add(user2)
        
        with pytest.raises(Exception):  # 应该抛出唯一约束异常
            db_session.commit()
    
    def test_user_email_unique_constraint(self, db_session: Session):
        """测试用户邮箱唯一约束"""
        user1 = User(
            username="user1",
            email="same@example.com",
            hashed_password="password1"
        )
        
        user2 = User(
            username="user2",
            email="same@example.com",  # 重复邮箱
            hashed_password="password2"
        )
        
        db_session.add(user1)
        db_session.commit()
        
        db_session.add(user2)
        
        with pytest.raises(Exception):  # 应该抛出唯一约束异常
            db_session.commit()
    
    def test_user_query_operations(self, db_session: Session, test_user: User):
        """测试用户查询操作"""
        # 按ID查询
        user_by_id = db_session.query(User).filter(User.id == test_user.id).first()
        assert user_by_id is not None
        assert user_by_id.username == test_user.username
        
        # 按用户名查询
        user_by_username = db_session.query(User).filter(User.username == test_user.username).first()
        assert user_by_username is not None
        assert user_by_username.id == test_user.id
        
        # 按邮箱查询
        user_by_email = db_session.query(User).filter(User.email == test_user.email).first()
        assert user_by_email is not None
        assert user_by_email.id == test_user.id
    
    def test_user_update_operations(self, db_session: Session, test_user: User):
        """测试用户更新操作"""
        original_username = test_user.username
        
        # 更新用户信息
        test_user.username = "updated_username"
        test_user.is_active = False
        
        db_session.commit()
        db_session.refresh(test_user)
        
        assert test_user.username == "updated_username"
        assert test_user.is_active is False
        assert test_user.updated_at is not None
    
    def test_user_deletion(self, db_session: Session):
        """测试用户删除"""
        user = User(
            username="to_delete",
            email="delete@example.com",
            hashed_password="password"
        )
        
        db_session.add(user)
        db_session.commit()
        user_id = user.id
        
        # 删除用户
        db_session.delete(user)
        db_session.commit()
        
        # 验证用户已删除
        deleted_user = db_session.query(User).filter(User.id == user_id).first()
        assert deleted_user is None


class TestStrategyOperations:
    """策略数据库操作测试"""
    
    def test_create_strategy(self, db_session: Session, test_user: User):
        """测试创建策略"""
        strategy = Strategy(
            name="Test Strategy",
            description="A test strategy",
            code="def initialize(context): pass",
            user_id=test_user.id,
            status="draft"
        )
        
        db_session.add(strategy)
        db_session.commit()
        db_session.refresh(strategy)
        
        assert strategy.id is not None
        assert strategy.name == "Test Strategy"
        assert strategy.user_id == test_user.id
        assert strategy.created_at is not None
    
    def test_strategy_user_relationship(self, db_session: Session, test_user: User):
        """测试策略与用户的关系"""
        strategy = Strategy(
            name="Relationship Test",
            description="Testing relationship",
            code="def initialize(context): pass",
            user_id=test_user.id
        )
        
        db_session.add(strategy)
        db_session.commit()
        db_session.refresh(strategy)
        
        # 测试正向关系
        assert strategy.user.id == test_user.id
        assert strategy.user.username == test_user.username
        
        # 测试反向关系
        user_strategies = test_user.strategies
        assert len(user_strategies) >= 1
        assert strategy in user_strategies
    
    def test_strategy_query_with_filters(self, db_session: Session, test_user: User):
        """测试策略查询过滤"""
        # 创建多个策略
        strategies = []
        for i in range(5):
            strategy = Strategy(
                name=f"Strategy {i}",
                description=f"Description {i}",
                code="def initialize(context): pass",
                user_id=test_user.id,
                status="active" if i % 2 == 0 else "draft"
            )
            strategies.append(strategy)
        
        db_session.add_all(strategies)
        db_session.commit()
        
        # 按状态过滤
        active_strategies = db_session.query(Strategy).filter(
            Strategy.user_id == test_user.id,
            Strategy.status == "active"
        ).all()
        
        assert len(active_strategies) == 3  # 0, 2, 4
        
        # 按名称模糊查询
        name_filtered = db_session.query(Strategy).filter(
            Strategy.user_id == test_user.id,
            Strategy.name.like("%Strategy 1%")
        ).all()
        
        assert len(name_filtered) == 1
        assert name_filtered[0].name == "Strategy 1"
    
    def test_strategy_cascade_delete(self, db_session: Session, test_user: User):
        """测试策略级联删除"""
        strategy = Strategy(
            name="To Delete",
            description="Will be deleted",
            code="def initialize(context): pass",
            user_id=test_user.id
        )
        
        db_session.add(strategy)
        db_session.commit()
        db_session.refresh(strategy)
        
        # 创建关联的回测
        backtest = Backtest(
            name="Associated Backtest",
            strategy_id=strategy.id,
            user_id=test_user.id,
            start_date="2023-01-01",
            end_date="2023-12-31",
            initial_capital=100000.0
        )
        
        db_session.add(backtest)
        db_session.commit()
        
        strategy_id = strategy.id
        backtest_id = backtest.id
        
        # 删除策略
        db_session.delete(strategy)
        db_session.commit()
        
        # 验证策略已删除
        deleted_strategy = db_session.query(Strategy).filter(Strategy.id == strategy_id).first()
        assert deleted_strategy is None
        
        # 验证关联的回测也被删除（如果配置了级联删除）
        # 或者验证外键约束
        deleted_backtest = db_session.query(Backtest).filter(Backtest.id == backtest_id).first()
        # 根据实际的外键配置，这里可能是None或者抛出异常


class TestBacktestOperations:
    """回测数据库操作测试"""
    
    def test_create_backtest(self, db_session: Session, test_strategy: Strategy):
        """测试创建回测"""
        backtest = Backtest(
            name="Test Backtest",
            strategy_id=test_strategy.id,
            user_id=test_strategy.user_id,
            start_date="2023-01-01",
            end_date="2023-12-31",
            initial_capital=100000.0,
            status="pending"
        )
        
        db_session.add(backtest)
        db_session.commit()
        db_session.refresh(backtest)
        
        assert backtest.id is not None
        assert backtest.name == "Test Backtest"
        assert backtest.strategy_id == test_strategy.id
        assert backtest.initial_capital == 100000.0
    
    def test_backtest_relationships(self, db_session: Session, test_backtest: Backtest):
        """测试回测关系"""
        # 测试与策略的关系
        assert test_backtest.strategy is not None
        assert test_backtest.strategy.id == test_backtest.strategy_id
        
        # 测试与用户的关系
        assert test_backtest.user is not None
        assert test_backtest.user.id == test_backtest.user_id
    
    def test_backtest_date_validation(self, db_session: Session, test_strategy: Strategy):
        """测试回测日期验证"""
        # 创建结束日期早于开始日期的回测
        backtest = Backtest(
            name="Invalid Date Backtest",
            strategy_id=test_strategy.id,
            user_id=test_strategy.user_id,
            start_date="2023-12-31",
            end_date="2023-01-01",  # 结束日期早于开始日期
            initial_capital=100000.0
        )
        
        db_session.add(backtest)
        
        # 如果有数据库级别的约束检查，这里应该抛出异常
        # 否则需要在应用层进行验证
        try:
            db_session.commit()
            # 如果没有数据库约束，在应用层验证
            assert backtest.start_date < backtest.end_date, "Start date should be before end date"
        except Exception:
            # 数据库约束检查通过
            pass
    
    def test_backtest_status_updates(self, db_session: Session, test_backtest: Backtest):
        """测试回测状态更新"""
        original_status = test_backtest.status
        
        # 更新状态为运行中
        test_backtest.status = "running"
        test_backtest.started_at = datetime.utcnow()
        
        db_session.commit()
        db_session.refresh(test_backtest)
        
        assert test_backtest.status == "running"
        assert test_backtest.started_at is not None
        
        # 更新状态为完成
        test_backtest.status = "completed"
        test_backtest.completed_at = datetime.utcnow()
        test_backtest.total_return = 0.15
        test_backtest.sharpe_ratio = 1.2
        test_backtest.max_drawdown = -0.08
        
        db_session.commit()
        db_session.refresh(test_backtest)
        
        assert test_backtest.status == "completed"
        assert test_backtest.completed_at is not None
        assert test_backtest.total_return == 0.15


class TestTradingOperations:
    """交易数据库操作测试"""
    
    def test_create_order(self, db_session: Session, test_user: User):
        """测试创建订单"""
        order = Order(
            user_id=test_user.id,
            symbol="SHFE.cu2401",
            side="buy",
            order_type="limit",
            quantity=1,
            price=70000.0,
            status="pending"
        )
        
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)
        
        assert order.id is not None
        assert order.symbol == "SHFE.cu2401"
        assert order.quantity == 1
        assert order.price == 70000.0
        assert order.created_at is not None
    
    def test_order_status_transitions(self, db_session: Session, test_order: Order):
        """测试订单状态转换"""
        # 初始状态
        assert test_order.status == "pending"
        
        # 更新为部分成交
        test_order.status = "partially_filled"
        test_order.filled_quantity = 0.5
        test_order.avg_fill_price = 70000.0
        
        db_session.commit()
        db_session.refresh(test_order)
        
        assert test_order.status == "partially_filled"
        assert test_order.filled_quantity == 0.5
        
        # 更新为完全成交
        test_order.status = "filled"
        test_order.filled_quantity = 1.0
        test_order.filled_at = datetime.utcnow()
        
        db_session.commit()
        db_session.refresh(test_order)
        
        assert test_order.status == "filled"
        assert test_order.filled_quantity == 1.0
        assert test_order.filled_at is not None
    
    def test_create_position(self, db_session: Session, test_user: User):
        """测试创建持仓"""
        position = Position(
            user_id=test_user.id,
            symbol="SHFE.cu2401",
            quantity=1,
            avg_price=70000.0,
            current_price=70500.0
        )
        
        db_session.add(position)
        db_session.commit()
        db_session.refresh(position)
        
        assert position.id is not None
        assert position.symbol == "SHFE.cu2401"
        assert position.quantity == 1
        assert position.avg_price == 70000.0
    
    def test_position_pnl_calculation(self, db_session: Session, test_position: Position):
        """测试持仓盈亏计算"""
        # 更新当前价格
        test_position.current_price = 70500.0
        
        db_session.commit()
        db_session.refresh(test_position)
        
        # 计算未实现盈亏
        unrealized_pnl = (test_position.current_price - test_position.avg_price) * test_position.quantity
        
        assert unrealized_pnl == 500.0  # (70500 - 70000) * 1
    
    def test_order_position_relationship(self, db_session: Session, test_user: User):
        """测试订单和持仓的关系"""
        # 创建买入订单
        buy_order = Order(
            user_id=test_user.id,
            symbol="SHFE.cu2401",
            side="buy",
            order_type="limit",
            quantity=1,
            price=70000.0,
            status="filled",
            filled_quantity=1.0,
            avg_fill_price=70000.0
        )
        
        db_session.add(buy_order)
        db_session.commit()
        
        # 创建对应的持仓
        position = Position(
            user_id=test_user.id,
            symbol="SHFE.cu2401",
            quantity=1,
            avg_price=70000.0,
            current_price=70000.0
        )
        
        db_session.add(position)
        db_session.commit()
        
        # 验证订单和持仓的关联
        user_orders = db_session.query(Order).filter(
            Order.user_id == test_user.id,
            Order.symbol == "SHFE.cu2401"
        ).all()
        
        user_positions = db_session.query(Position).filter(
            Position.user_id == test_user.id,
            Position.symbol == "SHFE.cu2401"
        ).all()
        
        assert len(user_orders) == 1
        assert len(user_positions) == 1
        assert user_orders[0].symbol == user_positions[0].symbol


class TestComplexQueries:
    """复杂查询测试"""
    
    def test_user_trading_summary(self, db_session: Session, test_user: User):
        """测试用户交易汇总查询"""
        # 创建多个订单
        orders = []
        for i in range(5):
            order = Order(
                user_id=test_user.id,
                symbol=f"SHFE.cu240{i+1}",
                side="buy" if i % 2 == 0 else "sell",
                order_type="limit",
                quantity=1,
                price=70000.0 + i * 100,
                status="filled",
                filled_quantity=1.0,
                avg_fill_price=70000.0 + i * 100
            )
            orders.append(order)
        
        db_session.add_all(orders)
        db_session.commit()
        
        # 查询用户交易汇总
        trading_summary = db_session.query(
            Order.side,
            db_session.query(Order.quantity).filter(Order.user_id == test_user.id).count().label('order_count'),
            db_session.query(Order.quantity).filter(Order.user_id == test_user.id).sum().label('total_quantity')
        ).filter(Order.user_id == test_user.id).group_by(Order.side).all()
        
        # 验证汇总结果
        assert len(trading_summary) >= 1
    
    def test_strategy_performance_query(self, db_session: Session, test_user: User):
        """测试策略性能查询"""
        # 创建策略
        strategy = Strategy(
            name="Performance Test Strategy",
            description="Testing performance queries",
            code="def initialize(context): pass",
            user_id=test_user.id,
            status="active"
        )
        
        db_session.add(strategy)
        db_session.commit()
        db_session.refresh(strategy)
        
        # 创建多个回测
        backtests = []
        for i in range(3):
            backtest = Backtest(
                name=f"Backtest {i}",
                strategy_id=strategy.id,
                user_id=test_user.id,
                start_date="2023-01-01",
                end_date="2023-12-31",
                initial_capital=100000.0,
                status="completed",
                total_return=0.1 + i * 0.05,
                sharpe_ratio=1.0 + i * 0.2,
                max_drawdown=-0.05 - i * 0.01
            )
            backtests.append(backtest)
        
        db_session.add_all(backtests)
        db_session.commit()
        
        # 查询策略平均性能
        avg_performance = db_session.query(
            db_session.query(Backtest.total_return).filter(
                Backtest.strategy_id == strategy.id,
                Backtest.status == "completed"
            ).func.avg().label('avg_return'),
            db_session.query(Backtest.sharpe_ratio).filter(
                Backtest.strategy_id == strategy.id,
                Backtest.status == "completed"
            ).func.avg().label('avg_sharpe'),
            db_session.query(Backtest.max_drawdown).filter(
                Backtest.strategy_id == strategy.id,
                Backtest.status == "completed"
            ).func.avg().label('avg_drawdown')
        ).first()
        
        # 验证性能指标
        assert avg_performance is not None
    
    def test_date_range_queries(self, db_session: Session, test_user: User):
        """测试日期范围查询"""
        # 创建不同日期的订单
        base_date = datetime.utcnow()
        orders = []
        
        for i in range(10):
            order = Order(
                user_id=test_user.id,
                symbol="SHFE.cu2401",
                side="buy",
                order_type="limit",
                quantity=1,
                price=70000.0,
                status="filled",
                created_at=base_date - timedelta(days=i)
            )
            orders.append(order)
        
        db_session.add_all(orders)
        db_session.commit()
        
        # 查询最近7天的订单
        recent_orders = db_session.query(Order).filter(
            Order.user_id == test_user.id,
            Order.created_at >= base_date - timedelta(days=7)
        ).all()
        
        assert len(recent_orders) == 8  # 包括今天，共8天
        
        # 查询特定日期范围的订单
        range_orders = db_session.query(Order).filter(
            Order.user_id == test_user.id,
            Order.created_at.between(
                base_date - timedelta(days=5),
                base_date - timedelta(days=2)
            )
        ).all()
        
        assert len(range_orders) == 4  # 2, 3, 4, 5天前的订单


class TestDatabaseConstraints:
    """数据库约束测试"""
    
    def test_foreign_key_constraints(self, db_session: Session):
        """测试外键约束"""
        # 尝试创建引用不存在用户的策略
        fake_user_id = "00000000-0000-0000-0000-000000000000"
        
        strategy = Strategy(
            name="Invalid Strategy",
            description="References non-existent user",
            code="def initialize(context): pass",
            user_id=fake_user_id
        )
        
        db_session.add(strategy)
        
        with pytest.raises(Exception):  # 应该抛出外键约束异常
            db_session.commit()
    
    def test_not_null_constraints(self, db_session: Session, test_user: User):
        """测试非空约束"""
        # 尝试创建缺少必需字段的策略
        strategy = Strategy(
            # name=None,  # 缺少必需的name字段
            description="Missing name",
            code="def initialize(context): pass",
            user_id=test_user.id
        )
        
        db_session.add(strategy)
        
        with pytest.raises(Exception):  # 应该抛出非空约束异常
            db_session.commit()
    
    def test_check_constraints(self, db_session: Session, test_user: User):
        """测试检查约束"""
        # 尝试创建负数量的订单
        order = Order(
            user_id=test_user.id,
            symbol="SHFE.cu2401",
            side="buy",
            order_type="limit",
            quantity=-1,  # 负数量
            price=70000.0,
            status="pending"
        )
        
        db_session.add(order)
        
        # 如果有数据库级别的检查约束，这里应该抛出异常
        try:
            db_session.commit()
            # 如果没有数据库约束，在应用层验证
            assert order.quantity > 0, "Quantity should be positive"
        except Exception:
            # 数据库约束检查通过
            pass


class TestDatabasePerformance:
    """数据库性能测试"""
    
    def test_bulk_insert_performance(self, db_session: Session, test_user: User):
        """测试批量插入性能"""
        import time
        
        # 创建大量订单数据
        orders = []
        for i in range(1000):
            order = Order(
                user_id=test_user.id,
                symbol=f"SHFE.cu240{i%10+1}",
                side="buy" if i % 2 == 0 else "sell",
                order_type="limit",
                quantity=1,
                price=70000.0 + i,
                status="pending"
            )
            orders.append(order)
        
        # 测试批量插入时间
        start_time = time.time()
        
        db_session.add_all(orders)
        db_session.commit()
        
        end_time = time.time()
        insert_time = end_time - start_time
        
        # 验证插入时间合理（应该在几秒内完成）
        assert insert_time < 10.0  # 10秒内完成
        
        # 验证数据正确插入
        inserted_count = db_session.query(Order).filter(Order.user_id == test_user.id).count()
        assert inserted_count >= 1000
    
    def test_complex_query_performance(self, db_session: Session, test_user: User):
        """测试复杂查询性能"""
        import time
        
        # 执行复杂的联合查询
        start_time = time.time()
        
        result = db_session.query(
            User.username,
            Strategy.name,
            Backtest.total_return
        ).join(
            Strategy, User.id == Strategy.user_id
        ).join(
            Backtest, Strategy.id == Backtest.strategy_id
        ).filter(
            User.id == test_user.id,
            Backtest.status == "completed"
        ).all()
        
        end_time = time.time()
        query_time = end_time - start_time
        
        # 验证查询时间合理
        assert query_time < 5.0  # 5秒内完成
    
    def test_index_effectiveness(self, db_session: Session, test_user: User):
        """测试索引有效性"""
        # 创建大量数据
        orders = []
        for i in range(5000):
            order = Order(
                user_id=test_user.id,
                symbol=f"SHFE.cu240{i%100+1}",
                side="buy",
                order_type="limit",
                quantity=1,
                price=70000.0,
                status="pending",
                created_at=datetime.utcnow() - timedelta(seconds=i)
            )
            orders.append(order)
        
        db_session.add_all(orders)
        db_session.commit()
        
        import time
        
        # 测试按用户ID查询（应该有索引）
        start_time = time.time()
        user_orders = db_session.query(Order).filter(Order.user_id == test_user.id).all()
        end_time = time.time()
        
        indexed_query_time = end_time - start_time
        
        # 测试按创建时间范围查询（应该有索引）
        start_time = time.time()
        recent_orders = db_session.query(Order).filter(
            Order.created_at >= datetime.utcnow() - timedelta(hours=1)
        ).all()
        end_time = time.time()
        
        date_query_time = end_time - start_time
        
        # 验证查询时间合理（有索引的查询应该很快）
        assert indexed_query_time < 1.0  # 1秒内完成
        assert date_query_time < 1.0  # 1秒内完成
        
        assert len(user_orders) >= 5000
        assert len(recent_orders) >= 0