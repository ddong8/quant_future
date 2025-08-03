"""
风险控制自动化执行服务
"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from enum import Enum

from app.models.risk import RiskRule, RiskEvent
from app.models.order import Order, OrderStatus, OrderSide
from app.models.position import Position
from app.models.account import Account
from app.models.user import User
from app.schemas.risk import RiskCheckResult, RiskAction, RiskActionType
from app.services.order_service import OrderService
from app.services.position_service import PositionService
from app.services.account_service import AccountService
from app.services.notification_service import NotificationService
from app.core.websocket import WebSocketManager
from app.utils.risk_calculator import RiskCalculator
from app.core.logging import get_logger

logger = get_logger(__name__)


class RiskControlAction(str, Enum):
    """风险控制动作枚举"""
    REJECT_ORDER = "reject_order"
    REDUCE_ORDER_SIZE = "reduce_order_size"
    FORCE_CLOSE_POSITION = "force_close_position"
    SUSPEND_TRADING = "suspend_trading"
    MARGIN_CALL = "margin_call"
    LIQUIDATION = "liquidation"


class RiskControlSeverity(str, Enum):
    """风险控制严重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskControlService:
    """风险控制自动化执行服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.order_service = OrderService(db)
        self.position_service = PositionService(db)
        self.account_service = AccountService(db)
        self.notification_service = NotificationService(db)
        self.websocket_manager = WebSocketManager()
        self.risk_calculator = RiskCalculator()
        
        # 风险控制配置
        self.config = {
            "max_position_size_ratio": 0.1,  # 单个持仓最大占比
            "max_daily_loss_ratio": 0.05,    # 日最大亏损比例
            "margin_call_ratio": 0.3,        # 保证金追缴比例
            "liquidation_ratio": 0.2,        # 强制平仓比例
            "max_order_value_ratio": 0.2,    # 单笔订单最大价值比例
        }
    
    async def check_order_risk(self, user_id: int, order_data: Dict[str, Any]) -> RiskCheckResult:
        """订单提交前风险检查"""
        try:
            logger.info(f"开始订单风险检查 - 用户: {user_id}, 订单: {order_data}")
            
            # 获取用户账户信息
            account = self.account_service.get_account_by_user_id(user_id)
            if not account:
                return RiskCheckResult(
                    passed=False,
                    risk_level="critical",
                    message="账户不存在",
                    actions=[]
                )
            
            # 获取活跃风险规则
            risk_rules = self._get_active_risk_rules(user_id)
            
            # 执行各项风险检查
            check_results = []
            
            # 1. 资金充足性检查
            funding_result = await self._check_funding_adequacy(account, order_data)
            check_results.append(funding_result)
            
            # 2. 持仓集中度检查
            concentration_result = await self._check_position_concentration(user_id, order_data)
            check_results.append(concentration_result)
            
            # 3. 单笔订单限额检查
            order_limit_result = await self._check_order_limits(account, order_data)
            check_results.append(order_limit_result)
            
            # 4. 日内交易限制检查
            daily_limit_result = await self._check_daily_limits(user_id, order_data)
            check_results.append(daily_limit_result)
            
            # 5. 自定义风险规则检查
            custom_rules_result = await self._check_custom_risk_rules(user_id, risk_rules, order_data)
            check_results.append(custom_rules_result)
            
            # 综合评估风险检查结果
            final_result = self._evaluate_risk_results(check_results)
            
            # 记录风险检查事件
            await self._log_risk_check_event(user_id, order_data, final_result)
            
            return final_result
            
        except Exception as e:
            logger.error(f"订单风险检查失败: {str(e)}")
            return RiskCheckResult(
                passed=False,
                risk_level="critical",
                message=f"风险检查系统错误: {str(e)}",
                actions=[]
            )
    
    async def execute_risk_action(self, user_id: int, action: RiskControlAction, 
                                context: Dict[str, Any]) -> bool:
        """执行风险控制动作"""
        try:
            logger.info(f"执行风险控制动作 - 用户: {user_id}, 动作: {action.value}")
            
            success = False
            
            if action == RiskControlAction.REJECT_ORDER:
                success = await self._reject_order(user_id, context)
            elif action == RiskControlAction.REDUCE_ORDER_SIZE:
                success = await self._reduce_order_size(user_id, context)
            elif action == RiskControlAction.FORCE_CLOSE_POSITION:
                success = await self._force_close_position(user_id, context)
            elif action == RiskControlAction.SUSPEND_TRADING:
                success = await self._suspend_trading(user_id, context)
            elif action == RiskControlAction.MARGIN_CALL:
                success = await self._trigger_margin_call(user_id, context)
            elif action == RiskControlAction.LIQUIDATION:
                success = await self._trigger_liquidation(user_id, context)
            
            # 记录风险控制动作
            await self._log_risk_action(user_id, action, context, success)
            
            # 发送通知
            await self._send_risk_notification(user_id, action, context, success)
            
            return success
            
        except Exception as e:
            logger.error(f"执行风险控制动作失败: {str(e)}")
            await self._log_risk_action(user_id, action, context, False, str(e))
            return False
    
    async def monitor_real_time_risk(self, user_id: int) -> None:
        """实时风险监控"""
        try:
            logger.info(f"开始实时风险监控 - 用户: {user_id}")
            
            # 获取用户账户和持仓信息
            account = self.account_service.get_account_by_user_id(user_id)
            positions = self.position_service.get_user_positions(user_id)
            
            if not account:
                return
            
            # 计算当前风险指标
            risk_metrics = await self._calculate_real_time_risk_metrics(account, positions)
            
            # 检查是否触发风险阈值
            triggered_actions = await self._check_risk_thresholds(user_id, risk_metrics)
            
            # 执行触发的风险控制动作
            for action_info in triggered_actions:
                await self.execute_risk_action(
                    user_id, 
                    action_info["action"], 
                    action_info["context"]
                )
            
        except Exception as e:
            logger.error(f"实时风险监控失败: {str(e)}")
    
    async def emergency_risk_control(self, user_id: int, reason: str) -> bool:
        """紧急风险控制"""
        try:
            logger.warning(f"触发紧急风险控制 - 用户: {user_id}, 原因: {reason}")
            
            # 1. 立即暂停交易
            await self.execute_risk_action(
                user_id, 
                RiskControlAction.SUSPEND_TRADING,
                {"reason": reason, "emergency": True}
            )
            
            # 2. 取消所有未成交订单
            await self._cancel_all_pending_orders(user_id)
            
            # 3. 评估是否需要强制平仓
            account = self.account_service.get_account_by_user_id(user_id)
            if account and account.margin_ratio < self.config["liquidation_ratio"]:
                await self.execute_risk_action(
                    user_id,
                    RiskControlAction.LIQUIDATION,
                    {"reason": reason, "emergency": True}
                )
            
            # 4. 发送紧急通知
            await self._send_emergency_notification(user_id, reason)
            
            return True
            
        except Exception as e:
            logger.error(f"紧急风险控制失败: {str(e)}")
            return False
    
    def _get_active_risk_rules(self, user_id: int) -> List[RiskRule]:
        """获取活跃的风险规则"""
        return self.db.query(RiskRule).filter(
            and_(
                RiskRule.user_id == user_id,
                RiskRule.is_active == True
            )
        ).all()
    
    async def _check_funding_adequacy(self, account: Account, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """检查资金充足性"""
        try:
            order_value = float(order_data.get("quantity", 0)) * float(order_data.get("price", 0))
            available_balance = account.available_balance
            
            if order_value > available_balance:
                return {
                    "passed": False,
                    "risk_level": "high",
                    "message": f"资金不足，需要 {order_value}，可用 {available_balance}",
                    "action": RiskControlAction.REJECT_ORDER
                }
            
            # 检查是否超过单笔订单限额
            max_order_value = account.total_balance * self.config["max_order_value_ratio"]
            if order_value > max_order_value:
                return {
                    "passed": False,
                    "risk_level": "medium",
                    "message": f"单笔订单金额过大，限额 {max_order_value}",
                    "action": RiskControlAction.REDUCE_ORDER_SIZE,
                    "suggested_size": max_order_value / float(order_data.get("price", 1))
                }
            
            return {
                "passed": True,
                "risk_level": "low",
                "message": "资金充足性检查通过"
            }
            
        except Exception as e:
            return {
                "passed": False,
                "risk_level": "critical",
                "message": f"资金检查错误: {str(e)}"
            }
    
    async def _check_position_concentration(self, user_id: int, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """检查持仓集中度"""
        try:
            symbol = order_data.get("symbol")
            order_quantity = float(order_data.get("quantity", 0))
            
            # 获取当前持仓
            current_position = self.position_service.get_position_by_symbol(user_id, symbol)
            current_quantity = current_position.quantity if current_position else 0
            
            # 计算新的持仓数量
            if order_data.get("side") == OrderSide.BUY:
                new_quantity = current_quantity + order_quantity
            else:
                new_quantity = current_quantity - order_quantity
            
            # 获取账户总价值
            account = self.account_service.get_account_by_user_id(user_id)
            total_value = account.total_balance if account else 0
            
            # 计算持仓价值占比
            position_value = abs(new_quantity) * float(order_data.get("price", 0))
            concentration_ratio = position_value / total_value if total_value > 0 else 0
            
            max_concentration = self.config["max_position_size_ratio"]
            
            if concentration_ratio > max_concentration:
                return {
                    "passed": False,
                    "risk_level": "high",
                    "message": f"持仓集中度过高 {concentration_ratio:.2%}，限制 {max_concentration:.2%}",
                    "action": RiskControlAction.REDUCE_ORDER_SIZE,
                    "suggested_size": (max_concentration * total_value) / float(order_data.get("price", 1))
                }
            
            return {
                "passed": True,
                "risk_level": "low",
                "message": "持仓集中度检查通过"
            }
            
        except Exception as e:
            return {
                "passed": False,
                "risk_level": "critical",
                "message": f"持仓集中度检查错误: {str(e)}"
            }
    
    async def _check_order_limits(self, account: Account, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """检查订单限额"""
        try:
            order_value = float(order_data.get("quantity", 0)) * float(order_data.get("price", 0))
            max_order_value = account.total_balance * self.config["max_order_value_ratio"]
            
            if order_value > max_order_value:
                return {
                    "passed": False,
                    "risk_level": "medium",
                    "message": f"订单金额超限，当前 {order_value}，限额 {max_order_value}",
                    "action": RiskControlAction.REDUCE_ORDER_SIZE
                }
            
            return {
                "passed": True,
                "risk_level": "low",
                "message": "订单限额检查通过"
            }
            
        except Exception as e:
            return {
                "passed": False,
                "risk_level": "critical",
                "message": f"订单限额检查错误: {str(e)}"
            }
    
    async def _check_daily_limits(self, user_id: int, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """检查日内交易限制"""
        try:
            today = datetime.now().date()
            
            # 获取今日订单
            today_orders = self.db.query(Order).filter(
                and_(
                    Order.user_id == user_id,
                    Order.created_at >= today,
                    Order.status.in_([OrderStatus.FILLED, OrderStatus.PARTIALLY_FILLED])
                )
            ).all()
            
            # 计算今日交易金额
            today_volume = sum(
                order.filled_quantity * order.avg_price 
                for order in today_orders 
                if order.filled_quantity and order.avg_price
            )
            
            # 获取账户信息计算限额
            account = self.account_service.get_account_by_user_id(user_id)
            daily_limit = account.total_balance * 2.0  # 日交易限额为账户总额的2倍
            
            order_value = float(order_data.get("quantity", 0)) * float(order_data.get("price", 0))
            
            if today_volume + order_value > daily_limit:
                return {
                    "passed": False,
                    "risk_level": "medium",
                    "message": f"超过日交易限额，今日已交易 {today_volume}，限额 {daily_limit}",
                    "action": RiskControlAction.REJECT_ORDER
                }
            
            return {
                "passed": True,
                "risk_level": "low",
                "message": "日内交易限制检查通过"
            }
            
        except Exception as e:
            return {
                "passed": False,
                "risk_level": "critical",
                "message": f"日内交易限制检查错误: {str(e)}"
            }
    
    async def _check_custom_risk_rules(self, user_id: int, risk_rules: List[RiskRule], 
                                     order_data: Dict[str, Any]) -> Dict[str, Any]:
        """检查自定义风险规则"""
        try:
            for rule in risk_rules:
                # 根据规则类型执行检查
                if rule.rule_type == "max_position_value":
                    result = await self._check_max_position_value_rule(rule, order_data)
                elif rule.rule_type == "max_daily_loss":
                    result = await self._check_max_daily_loss_rule(user_id, rule, order_data)
                elif rule.rule_type == "symbol_blacklist":
                    result = await self._check_symbol_blacklist_rule(rule, order_data)
                else:
                    continue
                
                if not result["passed"]:
                    return result
            
            return {
                "passed": True,
                "risk_level": "low",
                "message": "自定义风险规则检查通过"
            }
            
        except Exception as e:
            return {
                "passed": False,
                "risk_level": "critical",
                "message": f"自定义风险规则检查错误: {str(e)}"
            }
    
    async def _check_max_position_value_rule(self, rule: RiskRule, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """检查最大持仓价值规则"""
        max_value = rule.parameters.get("max_value", 0)
        order_value = float(order_data.get("quantity", 0)) * float(order_data.get("price", 0))
        
        if order_value > max_value:
            return {
                "passed": False,
                "risk_level": rule.severity,
                "message": f"违反最大持仓价值规则，当前 {order_value}，限制 {max_value}",
                "action": RiskControlAction.REDUCE_ORDER_SIZE
            }
        
        return {"passed": True, "risk_level": "low", "message": "最大持仓价值规则检查通过"}
    
    async def _check_max_daily_loss_rule(self, user_id: int, rule: RiskRule, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """检查最大日亏损规则"""
        max_loss = rule.parameters.get("max_loss", 0)
        
        # 计算今日盈亏
        today_pnl = await self._calculate_daily_pnl(user_id)
        
        if today_pnl < -max_loss:
            return {
                "passed": False,
                "risk_level": rule.severity,
                "message": f"违反最大日亏损规则，当前亏损 {abs(today_pnl)}，限制 {max_loss}",
                "action": RiskControlAction.SUSPEND_TRADING
            }
        
        return {"passed": True, "risk_level": "low", "message": "最大日亏损规则检查通过"}
    
    async def _check_symbol_blacklist_rule(self, rule: RiskRule, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """检查标的黑名单规则"""
        blacklist = rule.parameters.get("symbols", [])
        symbol = order_data.get("symbol")
        
        if symbol in blacklist:
            return {
                "passed": False,
                "risk_level": rule.severity,
                "message": f"标的 {symbol} 在黑名单中",
                "action": RiskControlAction.REJECT_ORDER
            }
        
        return {"passed": True, "risk_level": "low", "message": "标的黑名单规则检查通过"}
    
    def _evaluate_risk_results(self, check_results: List[Dict[str, Any]]) -> RiskCheckResult:
        """综合评估风险检查结果"""
        failed_checks = [result for result in check_results if not result.get("passed", True)]
        
        if not failed_checks:
            return RiskCheckResult(
                passed=True,
                risk_level="low",
                message="所有风险检查通过",
                actions=[]
            )
        
        # 找出最高风险级别
        risk_levels = ["low", "medium", "high", "critical"]
        max_risk_level = max(
            (result.get("risk_level", "low") for result in failed_checks),
            key=lambda x: risk_levels.index(x)
        )
        
        # 收集所有建议的动作
        actions = []
        messages = []
        
        for result in failed_checks:
            messages.append(result.get("message", ""))
            if "action" in result:
                actions.append(RiskAction(
                    action_type=result["action"],
                    parameters=result.get("parameters", {}),
                    reason=result.get("message", "")
                ))
        
        return RiskCheckResult(
            passed=False,
            risk_level=max_risk_level,
            message="; ".join(messages),
            actions=actions
        )
    
    async def _reject_order(self, user_id: int, context: Dict[str, Any]) -> bool:
        """拒绝订单"""
        try:
            order_id = context.get("order_id")
            if order_id:
                # 更新订单状态为拒绝
                order = self.db.query(Order).filter(Order.id == order_id).first()
                if order:
                    order.status = OrderStatus.REJECTED
                    order.reject_reason = context.get("reason", "风险控制拒绝")
                    self.db.commit()
            
            return True
        except Exception as e:
            logger.error(f"拒绝订单失败: {str(e)}")
            return False
    
    async def _reduce_order_size(self, user_id: int, context: Dict[str, Any]) -> bool:
        """减少订单数量"""
        try:
            order_id = context.get("order_id")
            suggested_size = context.get("suggested_size")
            
            if order_id and suggested_size:
                order = self.db.query(Order).filter(Order.id == order_id).first()
                if order and order.status == OrderStatus.PENDING:
                    order.quantity = suggested_size
                    self.db.commit()
                    return True
            
            return False
        except Exception as e:
            logger.error(f"减少订单数量失败: {str(e)}")
            return False
    
    async def _force_close_position(self, user_id: int, context: Dict[str, Any]) -> bool:
        """强制平仓"""
        try:
            symbol = context.get("symbol")
            if not symbol:
                return False
            
            position = self.position_service.get_position_by_symbol(user_id, symbol)
            if not position or position.quantity == 0:
                return True  # 没有持仓，认为成功
            
            # 创建平仓订单
            close_order_data = {
                "symbol": symbol,
                "side": OrderSide.SELL if position.quantity > 0 else OrderSide.BUY,
                "quantity": abs(position.quantity),
                "order_type": "market",
                "force_close": True,
                "reason": context.get("reason", "风险控制强制平仓")
            }
            
            # 提交平仓订单
            close_order = await self.order_service.create_order(user_id, close_order_data)
            return close_order is not None
            
        except Exception as e:
            logger.error(f"强制平仓失败: {str(e)}")
            return False
    
    async def _suspend_trading(self, user_id: int, context: Dict[str, Any]) -> bool:
        """暂停交易"""
        try:
            # 更新用户交易状态
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                user.trading_suspended = True
                user.suspension_reason = context.get("reason", "风险控制暂停交易")
                user.suspended_at = datetime.utcnow()
                self.db.commit()
                return True
            
            return False
        except Exception as e:
            logger.error(f"暂停交易失败: {str(e)}")
            return False
    
    async def _trigger_margin_call(self, user_id: int, context: Dict[str, Any]) -> bool:
        """触发保证金追缴"""
        try:
            # 发送保证金追缴通知
            await self.notification_service.send_notification(
                user_id=user_id,
                title="保证金追缴通知",
                content=f"您的账户保证金不足，请及时补充资金。原因：{context.get('reason', '未知')}",
                notification_type="margin_call",
                priority="high"
            )
            
            # 记录保证金追缴事件
            risk_event = RiskEvent(
                user_id=user_id,
                event_type="margin_call",
                severity="high",
                description=context.get("reason", "保证金追缴"),
                data=context
            )
            self.db.add(risk_event)
            self.db.commit()
            
            return True
        except Exception as e:
            logger.error(f"触发保证金追缴失败: {str(e)}")
            return False
    
    async def _trigger_liquidation(self, user_id: int, context: Dict[str, Any]) -> bool:
        """触发强制清算"""
        try:
            # 获取所有持仓
            positions = self.position_service.get_user_positions(user_id)
            
            # 按风险程度排序，优先平仓高风险持仓
            sorted_positions = sorted(
                positions, 
                key=lambda p: abs(p.unrealized_pnl / p.market_value) if p.market_value > 0 else 0,
                reverse=True
            )
            
            # 逐个强制平仓
            for position in sorted_positions:
                if position.quantity != 0:
                    await self._force_close_position(user_id, {
                        "symbol": position.symbol,
                        "reason": f"强制清算 - {context.get('reason', '未知原因')}"
                    })
            
            # 暂停交易
            await self._suspend_trading(user_id, context)
            
            return True
        except Exception as e:
            logger.error(f"触发强制清算失败: {str(e)}")
            return False
    
    async def _cancel_all_pending_orders(self, user_id: int) -> bool:
        """取消所有未成交订单"""
        try:
            pending_orders = self.db.query(Order).filter(
                and_(
                    Order.user_id == user_id,
                    Order.status == OrderStatus.PENDING
                )
            ).all()
            
            for order in pending_orders:
                order.status = OrderStatus.CANCELLED
                order.cancel_reason = "紧急风险控制"
                order.cancelled_at = datetime.utcnow()
            
            self.db.commit()
            return True
        except Exception as e:
            logger.error(f"取消所有未成交订单失败: {str(e)}")
            return False
    
    async def _calculate_real_time_risk_metrics(self, account: Account, positions: List[Position]) -> Dict[str, float]:
        """计算实时风险指标"""
        try:
            total_value = account.total_balance
            total_pnl = sum(pos.unrealized_pnl for pos in positions if pos.unrealized_pnl)
            
            # 计算各种风险指标
            metrics = {
                "total_value": total_value,
                "total_pnl": total_pnl,
                "pnl_ratio": total_pnl / total_value if total_value > 0 else 0,
                "margin_ratio": account.margin_ratio if hasattr(account, 'margin_ratio') else 1.0,
                "max_position_ratio": 0,
                "position_count": len([p for p in positions if p.quantity != 0])
            }
            
            # 计算最大持仓占比
            if positions and total_value > 0:
                max_position_value = max(
                    abs(pos.market_value) for pos in positions if pos.market_value
                )
                metrics["max_position_ratio"] = max_position_value / total_value
            
            return metrics
        except Exception as e:
            logger.error(f"计算实时风险指标失败: {str(e)}")
            return {}
    
    async def _check_risk_thresholds(self, user_id: int, risk_metrics: Dict[str, float]) -> List[Dict[str, Any]]:
        """检查风险阈值"""
        triggered_actions = []
        
        try:
            # 检查保证金比例
            margin_ratio = risk_metrics.get("margin_ratio", 1.0)
            if margin_ratio < self.config["liquidation_ratio"]:
                triggered_actions.append({
                    "action": RiskControlAction.LIQUIDATION,
                    "context": {
                        "reason": f"保证金比例过低: {margin_ratio:.2%}",
                        "margin_ratio": margin_ratio
                    }
                })
            elif margin_ratio < self.config["margin_call_ratio"]:
                triggered_actions.append({
                    "action": RiskControlAction.MARGIN_CALL,
                    "context": {
                        "reason": f"保证金比例不足: {margin_ratio:.2%}",
                        "margin_ratio": margin_ratio
                    }
                })
            
            # 检查日亏损比例
            pnl_ratio = risk_metrics.get("pnl_ratio", 0)
            if pnl_ratio < -self.config["max_daily_loss_ratio"]:
                triggered_actions.append({
                    "action": RiskControlAction.SUSPEND_TRADING,
                    "context": {
                        "reason": f"日亏损过大: {pnl_ratio:.2%}",
                        "pnl_ratio": pnl_ratio
                    }
                })
            
            # 检查持仓集中度
            max_position_ratio = risk_metrics.get("max_position_ratio", 0)
            if max_position_ratio > self.config["max_position_size_ratio"]:
                triggered_actions.append({
                    "action": RiskControlAction.FORCE_CLOSE_POSITION,
                    "context": {
                        "reason": f"持仓集中度过高: {max_position_ratio:.2%}",
                        "position_ratio": max_position_ratio
                    }
                })
            
            return triggered_actions
        except Exception as e:
            logger.error(f"检查风险阈值失败: {str(e)}")
            return []
    
    async def _calculate_daily_pnl(self, user_id: int) -> float:
        """计算日盈亏"""
        try:
            today = datetime.now().date()
            
            # 获取今日交易记录
            today_orders = self.db.query(Order).filter(
                and_(
                    Order.user_id == user_id,
                    Order.created_at >= today,
                    Order.status == OrderStatus.FILLED
                )
            ).all()
            
            # 计算已实现盈亏
            realized_pnl = sum(
                order.realized_pnl for order in today_orders 
                if order.realized_pnl
            )
            
            # 获取当前持仓的未实现盈亏
            positions = self.position_service.get_user_positions(user_id)
            unrealized_pnl = sum(
                pos.unrealized_pnl for pos in positions 
                if pos.unrealized_pnl
            )
            
            return realized_pnl + unrealized_pnl
        except Exception as e:
            logger.error(f"计算日盈亏失败: {str(e)}")
            return 0.0
    
    async def _log_risk_check_event(self, user_id: int, order_data: Dict[str, Any], 
                                  result: RiskCheckResult) -> None:
        """记录风险检查事件"""
        try:
            risk_event = RiskEvent(
                user_id=user_id,
                event_type="risk_check",
                severity=result.risk_level,
                description=f"订单风险检查 - {result.message}",
                data={
                    "order_data": order_data,
                    "check_result": {
                        "passed": result.passed,
                        "risk_level": result.risk_level,
                        "message": result.message,
                        "actions": [action.dict() for action in result.actions]
                    }
                }
            )
            self.db.add(risk_event)
            self.db.commit()
        except Exception as e:
            logger.error(f"记录风险检查事件失败: {str(e)}")
    
    async def _log_risk_action(self, user_id: int, action: RiskControlAction, 
                             context: Dict[str, Any], success: bool, error: str = None) -> None:
        """记录风险控制动作"""
        try:
            risk_event = RiskEvent(
                user_id=user_id,
                event_type="risk_action",
                severity="high" if not success else "medium",
                description=f"风险控制动作: {action.value} - {'成功' if success else '失败'}",
                data={
                    "action": action.value,
                    "context": context,
                    "success": success,
                    "error": error
                }
            )
            self.db.add(risk_event)
            self.db.commit()
        except Exception as e:
            logger.error(f"记录风险控制动作失败: {str(e)}")
    
    async def _send_risk_notification(self, user_id: int, action: RiskControlAction, 
                                    context: Dict[str, Any], success: bool) -> None:
        """发送风险通知"""
        try:
            action_names = {
                RiskControlAction.REJECT_ORDER: "订单拒绝",
                RiskControlAction.REDUCE_ORDER_SIZE: "订单数量调整",
                RiskControlAction.FORCE_CLOSE_POSITION: "强制平仓",
                RiskControlAction.SUSPEND_TRADING: "交易暂停",
                RiskControlAction.MARGIN_CALL: "保证金追缴",
                RiskControlAction.LIQUIDATION: "强制清算"
            }
            
            title = f"风险控制通知 - {action_names.get(action, action.value)}"
            content = f"系统已执行风险控制措施：{action_names.get(action, action.value)}\n"
            content += f"原因：{context.get('reason', '未知')}\n"
            content += f"状态：{'成功' if success else '失败'}"
            
            await self.notification_service.send_notification(
                user_id=user_id,
                title=title,
                content=content,
                notification_type="risk_control",
                priority="high"
            )
            
            # 发送WebSocket实时通知
            await self.websocket_manager.send_to_user(user_id, {
                "type": "risk_control",
                "action": action.value,
                "success": success,
                "context": context
            })
            
        except Exception as e:
            logger.error(f"发送风险通知失败: {str(e)}")
    
    async def _send_emergency_notification(self, user_id: int, reason: str) -> None:
        """发送紧急通知"""
        try:
            await self.notification_service.send_notification(
                user_id=user_id,
                title="紧急风险控制通知",
                content=f"系统已触发紧急风险控制措施，您的交易已被暂停。原因：{reason}",
                notification_type="emergency",
                priority="critical"
            )
            
            # 发送WebSocket紧急通知
            await self.websocket_manager.send_to_user(user_id, {
                "type": "emergency_risk_control",
                "reason": reason,
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"发送紧急通知失败: {str(e)}")