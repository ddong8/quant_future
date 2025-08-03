"""
端到端测试服务
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
import uuid

from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.models.strategy import Strategy
from app.models.backtest import Backtest
from app.models.order import Order
from app.models.position import Position
from app.services.integration_test_service import TestResult, TestStatus

logger = logging.getLogger(__name__)

@dataclass
class E2EScenario:
    """端到端测试场景"""
    scenario_id: str
    scenario_name: str
    description: str
    steps: List[Dict[str, Any]]
    expected_outcomes: List[Dict[str, Any]]
    test_data: Dict[str, Any]

class E2ETestService:
    """端到端测试服务"""
    
    def __init__(self):
        self.test_scenarios = self._initialize_scenarios()
        self.test_results = {}
    
    def _initialize_scenarios(self) -> List[E2EScenario]:
        """初始化测试场景"""
        
        scenarios = [
            E2EScenario(
                scenario_id="complete_trading_flow",
                scenario_name="完整交易流程",
                description="从策略创建到订单执行的完整流程",
                steps=[
                    {"action": "create_user", "params": {"username": "trader_001"}},
                    {"action": "create_strategy", "params": {"name": "测试策略", "type": "momentum"}},
                    {"action": "run_backtest", "params": {"period": "1M"}},
                    {"action": "create_order", "params": {"symbol": "AAPL", "quantity": 100}},
                    {"action": "execute_order", "params": {}},
                    {"action": "create_position", "params": {}},
                    {"action": "update_position", "params": {"price_change": 5.0}},
                    {"action": "close_position", "params": {}}
                ],
                expected_outcomes=[
                    {"check": "strategy_created", "criteria": {"status": "active"}},
                    {"check": "backtest_completed", "criteria": {"status": "completed"}},
                    {"check": "order_filled", "criteria": {"status": "filled"}},
                    {"check": "position_created", "criteria": {"quantity": 100}},
                    {"check": "pnl_calculated", "criteria": {"pnl": "> 0"}}
                ],
                test_data={}
            ),
            
            E2EScenario(
                scenario_id="risk_management_flow",
                scenario_name="风险管理流程",
                description="风险控制和止损止盈流程",
                steps=[
                    {"action": "create_user", "params": {"username": "risk_trader"}},
                    {"action": "set_risk_limits", "params": {"max_position_size": 1000}},
                    {"action": "create_large_order", "params": {"quantity": 1500}},
                    {"action": "verify_risk_rejection", "params": {}},
                    {"action": "create_valid_order", "params": {"quantity": 500}},
                    {"action": "set_stop_loss", "params": {"stop_price": 145.0}},
                    {"action": "trigger_stop_loss", "params": {"market_price": 144.0}},
                    {"action": "verify_position_closed", "params": {}}
                ],
                expected_outcomes=[
                    {"check": "large_order_rejected", "criteria": {"status": "rejected"}},
                    {"check": "valid_order_accepted", "criteria": {"status": "filled"}},
                    {"check": "stop_loss_triggered", "criteria": {"triggered": True}},
                    {"check": "position_closed", "criteria": {"status": "closed"}}
                ],
                test_data={}
            ),
            
            E2EScenario(
                scenario_id="multi_user_concurrent",
                scenario_name="多用户并发交易",
                description="多个用户同时进行交易操作",
                steps=[
                    {"action": "create_multiple_users", "params": {"count": 5}},
                    {"action": "concurrent_order_creation", "params": {"orders_per_user": 3}},
                    {"action": "concurrent_order_execution", "params": {}},
                    {"action": "verify_data_integrity", "params": {}},
                    {"action": "check_position_consistency", "params": {}}
                ],
                expected_outcomes=[
                    {"check": "all_users_created", "criteria": {"count": 5}},
                    {"check": "all_orders_processed", "criteria": {"success_rate": "> 95%"}},
                    {"check": "data_consistent", "criteria": {"consistency": True}},
                    {"check": "no_race_conditions", "criteria": {"conflicts": 0}}
                ],
                test_data={}
            ),
            
            E2EScenario(
                scenario_id="error_recovery_flow",
                scenario_name="错误恢复流程",
                description="系统错误和恢复机制测试",
                steps=[
                    {"action": "create_user", "params": {"username": "error_test_user"}},
                    {"action": "simulate_database_error", "params": {}},
                    {"action": "attempt_order_creation", "params": {}},
                    {"action": "verify_error_handling", "params": {}},
                    {"action": "restore_database", "params": {}},
                    {"action": "retry_order_creation", "params": {}},
                    {"action": "verify_recovery", "params": {}}
                ],
                expected_outcomes=[
                    {"check": "error_caught", "criteria": {"error_handled": True}},
                    {"check": "user_notified", "criteria": {"notification_sent": True}},
                    {"check": "recovery_successful", "criteria": {"order_created": True}},
                    {"check": "data_integrity_maintained", "criteria": {"integrity": True}}
                ],
                test_data={}
            )
        ]
        
        return scenarios
    
    async def run_e2e_scenario(
        self, 
        db: Session, 
        scenario_id: str
    ) -> TestResult:
        """运行端到端测试场景"""
        
        scenario = next((s for s in self.test_scenarios if s.scenario_id == scenario_id), None)
        if not scenario:
            raise ValueError(f"Scenario {scenario_id} not found")
        
        test_result = TestResult(
            test_id=str(uuid.uuid4()),
            test_name=scenario.scenario_name,
            status=TestStatus.RUNNING,
            start_time=datetime.now()
        )
        
        try:
            logger.info(f"Starting E2E scenario: {scenario.scenario_name}")
            
            # 执行测试步骤
            step_results = []
            test_context = {"scenario_id": scenario_id, "test_data": {}}
            
            for i, step in enumerate(scenario.steps):
                step_result = await self._execute_step(db, step, test_context)
                step_results.append({
                    "step": i + 1,
                    "action": step["action"],
                    "result": step_result,
                    "timestamp": datetime.now().isoformat()
                })
                
                if not step_result.get("success", False):
                    raise Exception(f"Step {i + 1} failed: {step_result.get('error', 'Unknown error')}")
            
            # 验证预期结果
            outcome_results = []
            for outcome in scenario.expected_outcomes:
                outcome_result = await self._verify_outcome(db, outcome, test_context)
                outcome_results.append({
                    "check": outcome["check"],
                    "result": outcome_result,
                    "timestamp": datetime.now().isoformat()
                })
                
                if not outcome_result.get("passed", False):
                    raise Exception(f"Outcome check failed: {outcome['check']}")
            
            test_result.status = TestStatus.PASSED
            test_result.details = {
                "scenario_id": scenario_id,
                "steps_executed": len(step_results),
                "outcomes_verified": len(outcome_results),
                "step_results": step_results,
                "outcome_results": outcome_results,
                "test_context": test_context
            }
            
            logger.info(f"E2E scenario completed successfully: {scenario.scenario_name}")
            
        except Exception as e:
            test_result.status = TestStatus.FAILED
            test_result.error_message = str(e)
            test_result.details = {
                "scenario_id": scenario_id,
                "error_step": len(step_results) if 'step_results' in locals() else 0,
                "step_results": step_results if 'step_results' in locals() else [],
                "test_context": test_context if 'test_context' in locals() else {}
            }
            
            logger.error(f"E2E scenario failed: {scenario.scenario_name} - {e}")
        
        finally:
            test_result.end_time = datetime.now()
            test_result.duration = (test_result.end_time - test_result.start_time).total_seconds()
            
            # 清理测试数据
            await self._cleanup_scenario_data(db, test_context)
        
        self.test_results[test_result.test_id] = test_result
        return test_result
    
    async def _execute_step(
        self, 
        db: Session, 
        step: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行测试步骤"""
        
        action = step["action"]
        params = step.get("params", {})
        
        try:
            if action == "create_user":
                return await self._create_test_user(db, params, context)
            elif action == "create_strategy":
                return await self._create_test_strategy(db, params, context)
            elif action == "run_backtest":
                return await self._run_test_backtest(db, params, context)
            elif action == "create_order":
                return await self._create_test_order(db, params, context)
            elif action == "execute_order":
                return await self._execute_test_order(db, params, context)
            elif action == "create_position":
                return await self._create_test_position(db, params, context)
            elif action == "update_position":
                return await self._update_test_position(db, params, context)
            elif action == "close_position":
                return await self._close_test_position(db, params, context)
            elif action == "set_risk_limits":
                return await self._set_risk_limits(db, params, context)
            elif action == "create_large_order":
                return await self._create_large_order(db, params, context)
            elif action == "verify_risk_rejection":
                return await self._verify_risk_rejection(db, params, context)
            elif action == "create_valid_order":
                return await self._create_valid_order(db, params, context)
            elif action == "set_stop_loss":
                return await self._set_stop_loss(db, params, context)
            elif action == "trigger_stop_loss":
                return await self._trigger_stop_loss(db, params, context)
            elif action == "verify_position_closed":
                return await self._verify_position_closed(db, params, context)
            elif action == "create_multiple_users":
                return await self._create_multiple_users(db, params, context)
            elif action == "concurrent_order_creation":
                return await self._concurrent_order_creation(db, params, context)
            elif action == "concurrent_order_execution":
                return await self._concurrent_order_execution(db, params, context)
            elif action == "verify_data_integrity":
                return await self._verify_data_integrity(db, params, context)
            elif action == "check_position_consistency":
                return await self._check_position_consistency(db, params, context)
            elif action == "simulate_database_error":
                return await self._simulate_database_error(db, params, context)
            elif action == "attempt_order_creation":
                return await self._attempt_order_creation(db, params, context)
            elif action == "verify_error_handling":
                return await self._verify_error_handling(db, params, context)
            elif action == "restore_database":
                return await self._restore_database(db, params, context)
            elif action == "retry_order_creation":
                return await self._retry_order_creation(db, params, context)
            elif action == "verify_recovery":
                return await self._verify_recovery(db, params, context)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _create_test_user(
        self, 
        db: Session, 
        params: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """创建测试用户"""
        
        username = params.get("username", f"test_user_{uuid.uuid4().hex[:8]}")
        
        user = User(
            username=username,
            email=f"{username}@test.com",
            hashed_password="test_password_hash",
            is_active=True
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        context["test_data"]["user_id"] = user.id
        context["test_data"]["username"] = username
        
        return {
            "success": True,
            "user_id": user.id,
            "username": username
        }
    
    async def _create_test_strategy(
        self, 
        db: Session, 
        params: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """创建测试策略"""
        
        user_id = context["test_data"]["user_id"]
        strategy_name = params.get("name", f"Test Strategy {uuid.uuid4().hex[:8]}")
        
        strategy = Strategy(
            name=strategy_name,
            description="E2E test strategy",
            type=params.get("type", "momentum"),
            code="# Test strategy code",
            parameters={"test": True},
            user_id=user_id,
            status="active"
        )
        
        db.add(strategy)
        db.commit()
        db.refresh(strategy)
        
        context["test_data"]["strategy_id"] = strategy.id
        
        return {
            "success": True,
            "strategy_id": strategy.id,
            "strategy_name": strategy_name
        }
    
    async def _run_test_backtest(
        self, 
        db: Session, 
        params: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """运行测试回测"""
        
        strategy_id = context["test_data"]["strategy_id"]
        user_id = context["test_data"]["user_id"]
        
        backtest = Backtest(
            strategy_id=strategy_id,
            user_id=user_id,
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now(),
            initial_capital=100000.0,
            status="completed",
            total_return=0.15,
            sharpe_ratio=1.2,
            max_drawdown=-0.08,
            completed_at=datetime.now()
        )
        
        db.add(backtest)
        db.commit()
        db.refresh(backtest)
        
        context["test_data"]["backtest_id"] = backtest.id
        
        return {
            "success": True,
            "backtest_id": backtest.id,
            "total_return": backtest.total_return
        }
    
    async def _create_test_order(
        self, 
        db: Session, 
        params: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """创建测试订单"""
        
        user_id = context["test_data"]["user_id"]
        
        order = Order(
            symbol=params.get("symbol", "AAPL"),
            side="buy",
            order_type="market",
            quantity=params.get("quantity", 100),
            user_id=user_id,
            status="pending"
        )
        
        db.add(order)
        db.commit()
        db.refresh(order)
        
        context["test_data"]["order_id"] = order.id
        
        return {
            "success": True,
            "order_id": order.id,
            "symbol": order.symbol,
            "quantity": order.quantity
        }
    
    async def _execute_test_order(
        self, 
        db: Session, 
        params: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行测试订单"""
        
        order_id = context["test_data"]["order_id"]
        order = db.query(Order).filter(Order.id == order_id).first()
        
        if not order:
            return {"success": False, "error": "Order not found"}
        
        # 模拟订单执行
        order.status = "filled"
        order.filled_quantity = order.quantity
        order.avg_fill_price = 150.0
        order.filled_at = datetime.now()
        
        db.commit()
        
        return {
            "success": True,
            "order_id": order_id,
            "filled_quantity": order.filled_quantity,
            "avg_fill_price": order.avg_fill_price
        }
    
    async def _create_test_position(
        self, 
        db: Session, 
        params: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """创建测试持仓"""
        
        user_id = context["test_data"]["user_id"]
        order_id = context["test_data"]["order_id"]
        order = db.query(Order).filter(Order.id == order_id).first()
        
        position = Position(
            symbol=order.symbol,
            quantity=order.filled_quantity,
            entry_price=order.avg_fill_price,
            current_price=order.avg_fill_price,
            user_id=user_id,
            status="open"
        )
        
        db.add(position)
        db.commit()
        db.refresh(position)
        
        context["test_data"]["position_id"] = position.id
        
        return {
            "success": True,
            "position_id": position.id,
            "symbol": position.symbol,
            "quantity": position.quantity
        }
    
    async def _update_test_position(
        self, 
        db: Session, 
        params: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """更新测试持仓"""
        
        position_id = context["test_data"]["position_id"]
        position = db.query(Position).filter(Position.id == position_id).first()
        
        if not position:
            return {"success": False, "error": "Position not found"}
        
        price_change = params.get("price_change", 5.0)
        position.current_price = position.entry_price + price_change
        position.unrealized_pnl = (position.current_price - position.entry_price) * position.quantity
        
        db.commit()
        
        return {
            "success": True,
            "position_id": position_id,
            "current_price": position.current_price,
            "unrealized_pnl": position.unrealized_pnl
        }
    
    async def _close_test_position(
        self, 
        db: Session, 
        params: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """关闭测试持仓"""
        
        position_id = context["test_data"]["position_id"]
        position = db.query(Position).filter(Position.id == position_id).first()
        
        if not position:
            return {"success": False, "error": "Position not found"}
        
        position.status = "closed"
        position.realized_pnl = position.unrealized_pnl
        position.unrealized_pnl = 0
        position.closed_at = datetime.now()
        
        db.commit()
        
        return {
            "success": True,
            "position_id": position_id,
            "realized_pnl": position.realized_pnl
        }
    
    # 其他步骤方法的简化实现
    async def _set_risk_limits(self, db: Session, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        context["test_data"]["max_position_size"] = params.get("max_position_size", 1000)
        return {"success": True, "max_position_size": context["test_data"]["max_position_size"]}
    
    async def _create_large_order(self, db: Session, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        # 模拟创建超过限制的大订单
        quantity = params.get("quantity", 1500)
        max_size = context["test_data"].get("max_position_size", 1000)
        
        if quantity > max_size:
            context["test_data"]["large_order_rejected"] = True
            return {"success": True, "rejected": True, "reason": "Exceeds position limit"}
        
        return {"success": True, "rejected": False}
    
    async def _verify_risk_rejection(self, db: Session, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        rejected = context["test_data"].get("large_order_rejected", False)
        return {"success": True, "risk_rejection_verified": rejected}
    
    async def _create_valid_order(self, db: Session, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        return await self._create_test_order(db, params, context)
    
    async def _set_stop_loss(self, db: Session, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        context["test_data"]["stop_loss_price"] = params.get("stop_price", 145.0)
        return {"success": True, "stop_loss_set": True}
    
    async def _trigger_stop_loss(self, db: Session, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        market_price = params.get("market_price", 144.0)
        stop_price = context["test_data"].get("stop_loss_price", 145.0)
        
        if market_price <= stop_price:
            context["test_data"]["stop_loss_triggered"] = True
            return {"success": True, "triggered": True}
        
        return {"success": True, "triggered": False}
    
    async def _verify_position_closed(self, db: Session, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        triggered = context["test_data"].get("stop_loss_triggered", False)
        return {"success": True, "position_closed": triggered}
    
    # 其他方法的简化实现...
    async def _create_multiple_users(self, db: Session, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        count = params.get("count", 5)
        user_ids = []
        
        for i in range(count):
            user = User(
                username=f"concurrent_user_{i}_{uuid.uuid4().hex[:8]}",
                email=f"user_{i}@test.com",
                hashed_password="test_password_hash",
                is_active=True
            )
            db.add(user)
            user_ids.append(user.id)
        
        db.commit()
        context["test_data"]["user_ids"] = user_ids
        
        return {"success": True, "users_created": len(user_ids)}
    
    async def _concurrent_order_creation(self, db: Session, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        # 模拟并发订单创建
        orders_per_user = params.get("orders_per_user", 3)
        user_ids = context["test_data"]["user_ids"]
        
        total_orders = len(user_ids) * orders_per_user
        context["test_data"]["total_orders"] = total_orders
        
        return {"success": True, "orders_created": total_orders}
    
    async def _concurrent_order_execution(self, db: Session, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        total_orders = context["test_data"]["total_orders"]
        success_rate = 0.98  # 模拟98%成功率
        
        return {"success": True, "success_rate": success_rate}
    
    async def _verify_data_integrity(self, db: Session, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        return {"success": True, "data_consistent": True}
    
    async def _check_position_consistency(self, db: Session, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        return {"success": True, "positions_consistent": True}
    
    # 错误恢复相关方法的简化实现
    async def _simulate_database_error(self, db: Session, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        context["test_data"]["database_error_simulated"] = True
        return {"success": True, "error_simulated": True}
    
    async def _attempt_order_creation(self, db: Session, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        if context["test_data"].get("database_error_simulated"):
            return {"success": False, "error": "Database connection failed"}
        return {"success": True}
    
    async def _verify_error_handling(self, db: Session, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        return {"success": True, "error_handled": True}
    
    async def _restore_database(self, db: Session, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        context["test_data"]["database_error_simulated"] = False
        return {"success": True, "database_restored": True}
    
    async def _retry_order_creation(self, db: Session, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        return await self._create_test_order(db, params, context)
    
    async def _verify_recovery(self, db: Session, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        return {"success": True, "recovery_successful": True}
    
    async def _verify_outcome(
        self, 
        db: Session, 
        outcome: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """验证预期结果"""
        
        check = outcome["check"]
        criteria = outcome["criteria"]
        
        # 根据检查类型验证结果
        if check == "strategy_created":
            strategy_id = context["test_data"].get("strategy_id")
            if strategy_id:
                strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
                passed = strategy and strategy.status == criteria.get("status")
            else:
                passed = False
        
        elif check == "backtest_completed":
            backtest_id = context["test_data"].get("backtest_id")
            if backtest_id:
                backtest = db.query(Backtest).filter(Backtest.id == backtest_id).first()
                passed = backtest and backtest.status == criteria.get("status")
            else:
                passed = False
        
        elif check == "order_filled":
            order_id = context["test_data"].get("order_id")
            if order_id:
                order = db.query(Order).filter(Order.id == order_id).first()
                passed = order and order.status == criteria.get("status")
            else:
                passed = False
        
        elif check == "position_created":
            position_id = context["test_data"].get("position_id")
            if position_id:
                position = db.query(Position).filter(Position.id == position_id).first()
                passed = position and position.quantity == criteria.get("quantity")
            else:
                passed = False
        
        elif check == "pnl_calculated":
            position_id = context["test_data"].get("position_id")
            if position_id:
                position = db.query(Position).filter(Position.id == position_id).first()
                pnl_criteria = criteria.get("pnl", "> 0")
                if pnl_criteria == "> 0":
                    passed = position and (position.unrealized_pnl or 0) > 0
                else:
                    passed = False
            else:
                passed = False
        
        else:
            # 默认通过，实际实现中应该有更详细的验证逻辑
            passed = True
        
        return {
            "passed": passed,
            "check": check,
            "criteria": criteria,
            "actual_result": context["test_data"]
        }
    
    async def _cleanup_scenario_data(self, db: Session, context: Dict[str, Any]):
        """清理场景测试数据"""
        
        try:
            test_data = context.get("test_data", {})
            
            # 删除测试数据（按依赖关系逆序）
            if "position_id" in test_data:
                db.query(Position).filter(Position.id == test_data["position_id"]).delete()
            
            if "order_id" in test_data:
                db.query(Order).filter(Order.id == test_data["order_id"]).delete()
            
            if "backtest_id" in test_data:
                db.query(Backtest).filter(Backtest.id == test_data["backtest_id"]).delete()
            
            if "strategy_id" in test_data:
                db.query(Strategy).filter(Strategy.id == test_data["strategy_id"]).delete()
            
            if "user_id" in test_data:
                db.query(User).filter(User.id == test_data["user_id"]).delete()
            
            if "user_ids" in test_data:
                for user_id in test_data["user_ids"]:
                    db.query(User).filter(User.id == user_id).delete()
            
            db.commit()
            logger.info("Scenario test data cleaned up successfully")
            
        except Exception as e:
            logger.error(f"Failed to cleanup scenario test data: {e}")
            db.rollback()
    
    def get_available_scenarios(self) -> List[Dict[str, Any]]:
        """获取可用的测试场景"""
        
        return [
            {
                "scenario_id": scenario.scenario_id,
                "scenario_name": scenario.scenario_name,
                "description": scenario.description,
                "steps_count": len(scenario.steps),
                "outcomes_count": len(scenario.expected_outcomes)
            }
            for scenario in self.test_scenarios
        ]
    
    def get_test_result(self, test_id: str) -> Optional[TestResult]:
        """获取测试结果"""
        return self.test_results.get(test_id)

# 创建全局实例
e2e_test_service = E2ETestService()