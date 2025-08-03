"""
集成测试服务
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json
import uuid

from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.strategy import Strategy
from app.models.backtest import Backtest
from app.models.order import Order
from app.models.position import Position
from app.models.transaction import Transaction
from app.models.user import User
from app.services.strategy_service import strategy_service
from app.services.backtest_service import backtest_service
from app.services.order_service import order_service
from app.services.position_service import position_service
from app.services.transaction_service import transaction_service

logger = logging.getLogger(__name__)

class TestStatus(Enum):
    """测试状态"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class TestResult:
    """测试结果"""
    test_id: str
    test_name: str
    status: TestStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    error_message: Optional[str] = None
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['status'] = self.status.value
        data['start_time'] = self.start_time.isoformat()
        if self.end_time:
            data['end_time'] = self.end_time.isoformat()
        return data

@dataclass
class IntegrationTestSuite:
    """集成测试套件"""
    suite_id: str
    suite_name: str
    tests: List[TestResult]
    start_time: datetime
    end_time: Optional[datetime] = None
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    skipped_tests: int = 0
    
    def __post_init__(self):
        self.total_tests = len(self.tests)
    
    def update_stats(self):
        """更新统计信息"""
        self.passed_tests = sum(1 for t in self.tests if t.status == TestStatus.PASSED)
        self.failed_tests = sum(1 for t in self.tests if t.status == TestStatus.FAILED)
        self.skipped_tests = sum(1 for t in self.tests if t.status == TestStatus.SKIPPED)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        self.update_stats()
        return {
            "suite_id": self.suite_id,
            "suite_name": self.suite_name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "skipped_tests": self.skipped_tests,
            "success_rate": (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0,
            "tests": [test.to_dict() for test in self.tests]
        }

class IntegrationTestService:
    """集成测试服务"""
    
    def __init__(self):
        self.test_suites: Dict[str, IntegrationTestSuite] = {}
        self.test_user_id = None
        self.test_data_cleanup = []
    
    async def run_full_integration_test(self, db: Session) -> IntegrationTestSuite:
        """运行完整的集成测试"""
        
        suite_id = str(uuid.uuid4())
        suite = IntegrationTestSuite(
            suite_id=suite_id,
            suite_name="完整集成测试",
            tests=[],
            start_time=datetime.now()
        )
        
        try:
            # 准备测试环境
            await self._setup_test_environment(db)
            
            # 执行测试用例
            test_cases = [
                ("策略创建测试", self._test_strategy_creation),
                ("回测执行测试", self._test_backtest_execution),
                ("订单创建测试", self._test_order_creation),
                ("持仓管理测试", self._test_position_management),
                ("交易流程测试", self._test_trading_workflow),
                ("数据一致性测试", self._test_data_consistency),
                ("异常处理测试", self._test_exception_handling),
                ("并发操作测试", self._test_concurrent_operations)
            ]
            
            for test_name, test_func in test_cases:
                test_result = await self._run_single_test(test_name, test_func, db)
                suite.tests.append(test_result)
            
            suite.end_time = datetime.now()
            self.test_suites[suite_id] = suite
            
            # 清理测试数据
            await self._cleanup_test_environment(db)
            
            logger.info(f"Integration test suite completed: {suite.passed_tests}/{suite.total_tests} passed")
            
        except Exception as e:
            logger.error(f"Integration test suite failed: {e}")
            suite.end_time = datetime.now()
            # 添加失败的测试结果
            if not suite.tests:
                suite.tests.append(TestResult(
                    test_id=str(uuid.uuid4()),
                    test_name="测试套件初始化",
                    status=TestStatus.FAILED,
                    start_time=suite.start_time,
                    end_time=datetime.now(),
                    error_message=str(e)
                ))
        
        return suite
    
    async def _setup_test_environment(self, db: Session):
        """设置测试环境"""
        
        # 创建测试用户
        test_user = User(
            username=f"test_user_{uuid.uuid4().hex[:8]}",
            email=f"test_{uuid.uuid4().hex[:8]}@example.com",
            hashed_password="test_password_hash",
            is_active=True
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        self.test_user_id = test_user.id
        self.test_data_cleanup.append(("user", test_user.id))
        
        logger.info(f"Test environment setup completed, test user ID: {self.test_user_id}")
    
    async def _cleanup_test_environment(self, db: Session):
        """清理测试环境"""
        
        try:
            # 按依赖关系逆序删除测试数据
            for data_type, data_id in reversed(self.test_data_cleanup):
                if data_type == "transaction":
                    db.query(Transaction).filter(Transaction.id == data_id).delete()
                elif data_type == "position":
                    db.query(Position).filter(Position.id == data_id).delete()
                elif data_type == "order":
                    db.query(Order).filter(Order.id == data_id).delete()
                elif data_type == "backtest":
                    db.query(Backtest).filter(Backtest.id == data_id).delete()
                elif data_type == "strategy":
                    db.query(Strategy).filter(Strategy.id == data_id).delete()
                elif data_type == "user":
                    db.query(User).filter(User.id == data_id).delete()
            
            db.commit()
            self.test_data_cleanup.clear()
            logger.info("Test environment cleanup completed")
            
        except Exception as e:
            logger.error(f"Test environment cleanup failed: {e}")
            db.rollback()
    
    async def _run_single_test(
        self, 
        test_name: str, 
        test_func, 
        db: Session
    ) -> TestResult:
        """运行单个测试"""
        
        test_id = str(uuid.uuid4())
        test_result = TestResult(
            test_id=test_id,
            test_name=test_name,
            status=TestStatus.RUNNING,
            start_time=datetime.now()
        )
        
        try:
            logger.info(f"Running test: {test_name}")
            
            # 执行测试
            result_details = await test_func(db)
            
            test_result.status = TestStatus.PASSED
            test_result.details = result_details
            test_result.end_time = datetime.now()
            test_result.duration = (test_result.end_time - test_result.start_time).total_seconds()
            
            logger.info(f"Test passed: {test_name}")
            
        except Exception as e:
            test_result.status = TestStatus.FAILED
            test_result.error_message = str(e)
            test_result.end_time = datetime.now()
            test_result.duration = (test_result.end_time - test_result.start_time).total_seconds()
            
            logger.error(f"Test failed: {test_name} - {e}")
        
        return test_result
    
    async def _test_strategy_creation(self, db: Session) -> Dict[str, Any]:
        """测试策略创建"""
        
        strategy_data = {
            "name": f"测试策略_{uuid.uuid4().hex[:8]}",
            "description": "集成测试策略",
            "type": "momentum",
            "code": """
def initialize(context):
    context.symbol = 'AAPL'
    
def handle_data(context, data):
    current_price = data.current(context.symbol, 'price')
    if current_price > 150:
        order_target_percent(context.symbol, 0.5)
    else:
        order_target_percent(context.symbol, 0)
""",
            "parameters": {"lookback_period": 20, "threshold": 0.02},
            "user_id": self.test_user_id
        }
        
        # 创建策略
        strategy = await strategy_service.create_strategy(db, strategy_data)
        self.test_data_cleanup.append(("strategy", strategy.id))
        
        # 验证策略创建
        assert strategy.id is not None
        assert strategy.name == strategy_data["name"]
        assert strategy.user_id == self.test_user_id
        assert strategy.status == "draft"
        
        # 验证策略代码解析
        assert strategy.code == strategy_data["code"]
        assert strategy.parameters == strategy_data["parameters"]
        
        return {
            "strategy_id": strategy.id,
            "strategy_name": strategy.name,
            "created_at": strategy.created_at.isoformat()
        }
    
    async def _test_backtest_execution(self, db: Session) -> Dict[str, Any]:
        """测试回测执行"""
        
        # 首先创建一个策略
        strategy_result = await self._test_strategy_creation(db)
        strategy_id = strategy_result["strategy_id"]
        
        backtest_config = {
            "strategy_id": strategy_id,
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "initial_capital": 100000.0,
            "symbols": ["AAPL", "GOOGL"],
            "benchmark": "SPY",
            "user_id": self.test_user_id
        }
        
        # 创建回测
        backtest = await backtest_service.create_backtest(db, backtest_config)
        self.test_data_cleanup.append(("backtest", backtest.id))
        
        # 验证回测创建
        assert backtest.id is not None
        assert backtest.strategy_id == strategy_id
        assert backtest.user_id == self.test_user_id
        assert backtest.status == "pending"
        
        # 模拟回测执行（实际环境中会异步执行）
        backtest.status = "running"
        db.commit()
        
        # 模拟回测完成
        backtest.status = "completed"
        backtest.total_return = 0.15
        backtest.sharpe_ratio = 1.2
        backtest.max_drawdown = -0.08
        backtest.completed_at = datetime.now()
        db.commit()
        
        return {
            "backtest_id": backtest.id,
            "strategy_id": strategy_id,
            "status": backtest.status,
            "total_return": backtest.total_return,
            "sharpe_ratio": backtest.sharpe_ratio
        }
    
    async def _test_order_creation(self, db: Session) -> Dict[str, Any]:
        """测试订单创建"""
        
        order_data = {
            "symbol": "AAPL",
            "side": "buy",
            "order_type": "market",
            "quantity": 100,
            "user_id": self.test_user_id
        }
        
        # 创建订单
        order = await order_service.create_order(db, order_data)
        self.test_data_cleanup.append(("order", order.id))
        
        # 验证订单创建
        assert order.id is not None
        assert order.symbol == order_data["symbol"]
        assert order.side == order_data["side"]
        assert order.quantity == order_data["quantity"]
        assert order.user_id == self.test_user_id
        assert order.status == "pending"
        
        # 模拟订单执行
        order.status = "filled"
        order.filled_quantity = order.quantity
        order.avg_fill_price = 150.0
        order.filled_at = datetime.now()
        db.commit()
        
        return {
            "order_id": order.id,
            "symbol": order.symbol,
            "status": order.status,
            "filled_quantity": order.filled_quantity,
            "avg_fill_price": order.avg_fill_price
        }
    
    async def _test_position_management(self, db: Session) -> Dict[str, Any]:
        """测试持仓管理"""
        
        # 首先创建一个订单
        order_result = await self._test_order_creation(db)
        
        position_data = {
            "symbol": "AAPL",
            "quantity": 100,
            "entry_price": 150.0,
            "current_price": 155.0,
            "user_id": self.test_user_id
        }
        
        # 创建持仓
        position = await position_service.create_position(db, position_data)
        self.test_data_cleanup.append(("position", position.id))
        
        # 验证持仓创建
        assert position.id is not None
        assert position.symbol == position_data["symbol"]
        assert position.quantity == position_data["quantity"]
        assert position.entry_price == position_data["entry_price"]
        assert position.user_id == self.test_user_id
        
        # 测试持仓更新
        position.current_price = 160.0
        position.unrealized_pnl = (160.0 - 150.0) * 100
        db.commit()
        
        # 验证盈亏计算
        expected_pnl = (160.0 - 150.0) * 100
        assert abs(position.unrealized_pnl - expected_pnl) < 0.01
        
        return {
            "position_id": position.id,
            "symbol": position.symbol,
            "quantity": position.quantity,
            "entry_price": position.entry_price,
            "current_price": position.current_price,
            "unrealized_pnl": position.unrealized_pnl
        }
    
    async def _test_trading_workflow(self, db: Session) -> Dict[str, Any]:
        """测试完整交易流程"""
        
        workflow_results = {}
        
        # 1. 创建策略
        strategy_result = await self._test_strategy_creation(db)
        workflow_results["strategy"] = strategy_result
        
        # 2. 执行回测
        backtest_result = await self._test_backtest_execution(db)
        workflow_results["backtest"] = backtest_result
        
        # 3. 基于回测结果创建订单
        order_result = await self._test_order_creation(db)
        workflow_results["order"] = order_result
        
        # 4. 订单成交后创建持仓
        position_result = await self._test_position_management(db)
        workflow_results["position"] = position_result
        
        # 5. 创建交易记录
        transaction_data = {
            "type": "trade",
            "amount": order_result["filled_quantity"] * order_result["avg_fill_price"],
            "description": f"买入 {order_result['symbol']} {order_result['filled_quantity']} 股",
            "reference_id": order_result["order_id"],
            "user_id": self.test_user_id
        }
        
        transaction = await transaction_service.create_transaction(db, transaction_data)
        self.test_data_cleanup.append(("transaction", transaction.id))
        
        workflow_results["transaction"] = {
            "transaction_id": transaction.id,
            "type": transaction.type,
            "amount": transaction.amount,
            "reference_id": transaction.reference_id
        }
        
        # 验证数据关联性
        assert backtest_result["strategy_id"] == strategy_result["strategy_id"]
        assert transaction.reference_id == order_result["order_id"]
        
        return workflow_results
    
    async def _test_data_consistency(self, db: Session) -> Dict[str, Any]:
        """测试数据一致性"""
        
        consistency_checks = {}
        
        # 检查用户数据一致性
        user_orders = db.query(Order).filter(Order.user_id == self.test_user_id).all()
        user_positions = db.query(Position).filter(Position.user_id == self.test_user_id).all()
        user_transactions = db.query(Transaction).filter(Transaction.user_id == self.test_user_id).all()
        
        consistency_checks["user_data"] = {
            "orders_count": len(user_orders),
            "positions_count": len(user_positions),
            "transactions_count": len(user_transactions)
        }
        
        # 检查订单-持仓一致性
        filled_orders = [o for o in user_orders if o.status == "filled"]
        position_symbols = {p.symbol for p in user_positions}
        order_symbols = {o.symbol for o in filled_orders}
        
        consistency_checks["order_position_consistency"] = {
            "filled_orders": len(filled_orders),
            "position_symbols": list(position_symbols),
            "order_symbols": list(order_symbols),
            "symbols_match": position_symbols == order_symbols
        }
        
        # 检查交易记录一致性
        order_ids = {o.id for o in user_orders}
        transaction_refs = {t.reference_id for t in user_transactions if t.reference_id}
        
        consistency_checks["transaction_consistency"] = {
            "order_ids": len(order_ids),
            "transaction_refs": len(transaction_refs),
            "refs_valid": all(ref in order_ids for ref in transaction_refs if ref)
        }
        
        # 检查金额计算一致性
        total_trade_amount = sum(
            o.filled_quantity * o.avg_fill_price 
            for o in filled_orders 
            if o.avg_fill_price
        )
        total_transaction_amount = sum(
            t.amount for t in user_transactions 
            if t.type == "trade"
        )
        
        consistency_checks["amount_consistency"] = {
            "total_trade_amount": total_trade_amount,
            "total_transaction_amount": total_transaction_amount,
            "amounts_match": abs(total_trade_amount - total_transaction_amount) < 0.01
        }
        
        return consistency_checks
    
    async def _test_exception_handling(self, db: Session) -> Dict[str, Any]:
        """测试异常处理"""
        
        exception_tests = {}
        
        # 测试无效数据处理
        try:
            invalid_order = {
                "symbol": "",  # 无效符号
                "side": "invalid_side",  # 无效方向
                "quantity": -100,  # 无效数量
                "user_id": self.test_user_id
            }
            await order_service.create_order(db, invalid_order)
            exception_tests["invalid_order"] = {"handled": False, "error": "No exception raised"}
        except Exception as e:
            exception_tests["invalid_order"] = {"handled": True, "error": str(e)}
        
        # 测试不存在的用户
        try:
            invalid_user_order = {
                "symbol": "AAPL",
                "side": "buy",
                "quantity": 100,
                "user_id": 99999  # 不存在的用户ID
            }
            await order_service.create_order(db, invalid_user_order)
            exception_tests["invalid_user"] = {"handled": False, "error": "No exception raised"}
        except Exception as e:
            exception_tests["invalid_user"] = {"handled": True, "error": str(e)}
        
        # 测试数据库约束违反
        try:
            # 尝试创建重复的策略名称
            duplicate_strategy = {
                "name": "重复策略名称",
                "description": "测试重复",
                "type": "momentum",
                "code": "# 测试代码",
                "user_id": self.test_user_id
            }
            strategy1 = await strategy_service.create_strategy(db, duplicate_strategy)
            self.test_data_cleanup.append(("strategy", strategy1.id))
            
            strategy2 = await strategy_service.create_strategy(db, duplicate_strategy)
            self.test_data_cleanup.append(("strategy", strategy2.id))
            
            exception_tests["duplicate_strategy"] = {"handled": False, "error": "No exception raised"}
        except Exception as e:
            exception_tests["duplicate_strategy"] = {"handled": True, "error": str(e)}
        
        return exception_tests
    
    async def _test_concurrent_operations(self, db: Session) -> Dict[str, Any]:
        """测试并发操作"""
        
        concurrent_results = {}
        
        # 创建多个并发订单
        async def create_concurrent_order(symbol: str, quantity: int):
            try:
                order_data = {
                    "symbol": symbol,
                    "side": "buy",
                    "order_type": "market",
                    "quantity": quantity,
                    "user_id": self.test_user_id
                }
                order = await order_service.create_order(db, order_data)
                self.test_data_cleanup.append(("order", order.id))
                return {"success": True, "order_id": order.id}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        # 并发创建订单
        concurrent_tasks = [
            create_concurrent_order("AAPL", 50),
            create_concurrent_order("GOOGL", 25),
            create_concurrent_order("MSFT", 75),
            create_concurrent_order("TSLA", 30)
        ]
        
        results = await asyncio.gather(*concurrent_tasks, return_exceptions=True)
        
        successful_orders = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
        failed_orders = len(results) - successful_orders
        
        concurrent_results["concurrent_orders"] = {
            "total_attempts": len(concurrent_tasks),
            "successful": successful_orders,
            "failed": failed_orders,
            "success_rate": successful_orders / len(concurrent_tasks) * 100
        }
        
        return concurrent_results
    
    def get_test_suite(self, suite_id: str) -> Optional[IntegrationTestSuite]:
        """获取测试套件"""
        return self.test_suites.get(suite_id)
    
    def get_all_test_suites(self) -> List[Dict[str, Any]]:
        """获取所有测试套件"""
        return [suite.to_dict() for suite in self.test_suites.values()]
    
    def get_test_summary(self) -> Dict[str, Any]:
        """获取测试摘要"""
        if not self.test_suites:
            return {"total_suites": 0, "total_tests": 0, "overall_success_rate": 0}
        
        total_tests = sum(suite.total_tests for suite in self.test_suites.values())
        total_passed = sum(suite.passed_tests for suite in self.test_suites.values())
        
        return {
            "total_suites": len(self.test_suites),
            "total_tests": total_tests,
            "total_passed": total_passed,
            "total_failed": total_tests - total_passed,
            "overall_success_rate": (total_passed / total_tests * 100) if total_tests > 0 else 0,
            "latest_suite": max(self.test_suites.values(), key=lambda s: s.start_time).to_dict() if self.test_suites else None
        }

# 创建全局实例
integration_test_service = IntegrationTestService()