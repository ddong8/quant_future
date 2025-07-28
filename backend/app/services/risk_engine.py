"""
风险管理引擎
"""
from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
import logging
import asyncio
from dataclasses import dataclass

from ..models import User, TradingAccount, Position, Order, RiskRule, RiskEvent
from ..models.enums import OrderSide, OrderType, RiskRuleType, RiskEventType
from ..core.exceptions import RiskControlError
from .risk_service import RiskService
from .account_service import AccountService
from .position_service import PositionService

logger = logging.getLogger(__name__)


@dataclass
class RiskAction:
    """风险处理动作"""
    action_type: str
    parameters: Dict[str, Any]
    priority: int = 1
    auto_execute: bool = False


class RiskEngine:
    """风险管理引擎"""
    
    def __init__(self, db: Session):
        self.db = db
        self.risk_service = RiskService(db)
        self.account_service = AccountService(db)
        self.position_service = PositionService(db)
        
        # 风险检查器注册表
        self.risk_checkers = {
            RiskRuleType.POSITION_LIMIT: self._check_position_limit,
            RiskRuleType.ORDER_SIZE_LIMIT: self._check_order_size_limit,
            RiskRuleType.DAILY_LOSS_LIMIT: self._check_daily_loss_limit,
            RiskRuleType.CONCENTRATION_LIMIT: self._check_concentration_limit,
        }
        
        # 自动处理动作注册表
        self.auto_actions = {
            "cancel_orders": self._cancel_all_orders,
            "close_positions": self._close_all_positions,
            "freeze_account": self._freeze_account,
            "send_alert": self._send_alert,
        }
    
    async def check_pre_trade_risk(self, user_id: int, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """交易前风险检查"""
        try:
            logger.info(f"开始交易前风险检查: 用户{user_id}, 订单{order_data}")
            
            # 获取用户的风险规则
            risk_rules = self.risk_service.get_user_risk_rules(user_id)
            active_rules = [rule for rule in risk_rules if rule.is_active]
            
            # 执行各项风险检查
            check_results = []
            
            for rule in active_rules:
                if rule.rule_type in self.risk_checkers:
                    checker = self.risk_checkers[rule.rule_type]
                    result = await checker(user_id, order_data, rule)
                    check_results.append(result)
            
            # 汇总检查结果
            failed_checks = [result for result in check_results if not result['passed']]
            
            if failed_checks:
                # 记录风险事件
                await self._record_risk_event(
                    user_id=user_id,
                    event_type=RiskEventType.POSITION_LIMIT,  # 根据具体失败类型调整
                    title="交易前风险检查失败",
                    description="; ".join([check['message'] for check in failed_checks]),
                    event_data={"order_data": order_data, "failed_checks": failed_checks}
                )
                
                return {
                    'passed': False,
                    'message': '; '.join([check['message'] for check in failed_checks]),
                    'risk_level': max([check.get('risk_level', 'MEDIUM') for check in failed_checks]),
                    'failed_checks': failed_checks,
                    'suggested_actions': self._get_suggested_actions(failed_checks)
                }
            
            return {
                'passed': True,
                'message': '风险检查通过',
                'risk_level': 'LOW'
            }
            
        except Exception as e:
            logger.error(f"交易前风险检查失败: {e}")
            return {
                'passed': False,
                'message': f'风险检查异常: {str(e)}',
                'risk_level': 'HIGH'
            }
    
    async def monitor_real_time_risk(self, user_id: int) -> Dict[str, Any]:
        """实时风险监控"""
        try:
            # 获取账户信息
            account = self.account_service.get_account(user_id)
            if not account:
                return {'status': 'error', 'message': '账户不存在'}
            
            # 计算当前风险指标
            risk_metrics = self.account_service.calculate_account_metrics(user_id)
            
            # 检查风险阈值
            risk_alerts = []
            
            # 保证金比例检查
            margin_ratio = risk_metrics.get('margin_ratio', 0)
            if margin_ratio > 0.8:
                risk_alerts.append({
                    'type': 'MARGIN_CALL',
                    'severity': 'HIGH',
                    'message': f'保证金比例过高: {margin_ratio:.2%}',
                    'suggested_action': 'reduce_positions'
                })
            
            # 未实现盈亏检查
            unrealized_pnl = risk_metrics.get('unrealized_pnl', 0)
            total_balance = risk_metrics.get('total_balance', 1)
            pnl_ratio = unrealized_pnl / total_balance
            
            if pnl_ratio < -0.1:  # 未实现亏损超过10%
                risk_alerts.append({
                    'type': 'UNREALIZED_LOSS',
                    'severity': 'MEDIUM',
                    'message': f'未实现亏损过大: {pnl_ratio:.2%}',
                    'suggested_action': 'review_positions'
                })
            
            # 持仓集中度检查
            max_position_ratio = risk_metrics.get('max_single_position_ratio', 0)
            if max_position_ratio > 0.3:  # 单一持仓超过30%
                risk_alerts.append({
                    'type': 'CONCENTRATION_RISK',
                    'severity': 'MEDIUM',
                    'message': f'持仓过于集中: {max_position_ratio:.2%}',
                    'suggested_action': 'diversify_positions'
                })
            
            # 如果有高风险告警，执行自动处理
            high_risk_alerts = [alert for alert in risk_alerts if alert['severity'] == 'HIGH']
            if high_risk_alerts:
                await self._execute_auto_risk_actions(user_id, high_risk_alerts)
            
            return {
                'status': 'success',
                'risk_level': self._calculate_overall_risk_level(risk_alerts),
                'risk_metrics': risk_metrics,
                'risk_alerts': risk_alerts,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"实时风险监控失败: {e}")
            return {'status': 'error', 'message': str(e)}
    
    async def _check_position_limit(self, user_id: int, order_data: Dict[str, Any], rule: RiskRule) -> Dict[str, Any]:
        """检查持仓限制"""
        try:
            symbol = order_data['symbol']
            side = order_data['side']
            quantity = order_data['quantity']
            
            # 获取当前持仓
            position = self.position_service.get_position(user_id, symbol)
            current_quantity = float(position.quantity) if position else 0
            
            # 计算新的持仓数量
            if side == OrderSide.BUY.value:
                new_quantity = current_quantity + quantity
            else:
                new_quantity = current_quantity - quantity
            
            max_position = float(rule.rule_value)
            
            if abs(new_quantity) > max_position:
                return {
                    'passed': False,
                    'message': f'{symbol} 超过最大持仓限制 {max_position}，当前将达到 {abs(new_quantity)}',
                    'risk_level': 'HIGH',
                    'rule_type': rule.rule_type.value
                }
            
            return {'passed': True, 'message': '持仓限制检查通过'}
            
        except Exception as e:
            logger.error(f"持仓限制检查失败: {e}")
            return {
                'passed': False,
                'message': f'持仓限制检查异常: {str(e)}',
                'risk_level': 'HIGH'
            }
    
    async def _check_order_size_limit(self, user_id: int, order_data: Dict[str, Any], rule: RiskRule) -> Dict[str, Any]:
        """检查订单大小限制"""
        try:
            quantity = order_data['quantity']
            max_order_size = float(rule.rule_value)
            
            if quantity > max_order_size:
                return {
                    'passed': False,
                    'message': f'订单数量 {quantity} 超过单笔限制 {max_order_size}',
                    'risk_level': 'MEDIUM',
                    'rule_type': rule.rule_type.value
                }
            
            return {'passed': True, 'message': '订单大小检查通过'}
            
        except Exception as e:
            logger.error(f"订单大小检查失败: {e}")
            return {
                'passed': False,
                'message': f'订单大小检查异常: {str(e)}',
                'risk_level': 'MEDIUM'
            }
    
    async def _check_daily_loss_limit(self, user_id: int, order_data: Dict[str, Any], rule: RiskRule) -> Dict[str, Any]:
        """检查日亏损限制"""
        try:
            # 获取今日已实现盈亏
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            
            account = self.account_service.get_account(user_id)
            if not account:
                return {'passed': False, 'message': '账户不存在', 'risk_level': 'HIGH'}
            
            # 计算今日盈亏（简化实现）
            today_pnl = 0  # 这里需要从交易记录中计算
            
            daily_loss_limit = float(rule.rule_value)
            
            if today_pnl < -daily_loss_limit:
                return {
                    'passed': False,
                    'message': f'今日亏损 {abs(today_pnl)} 已达到限制 {daily_loss_limit}',
                    'risk_level': 'HIGH',
                    'rule_type': rule.rule_type.value
                }
            
            return {'passed': True, 'message': '日亏损限制检查通过'}
            
        except Exception as e:
            logger.error(f"日亏损限制检查失败: {e}")
            return {
                'passed': False,
                'message': f'日亏损限制检查异常: {str(e)}',
                'risk_level': 'HIGH'
            }
    
    async def _check_concentration_limit(self, user_id: int, order_data: Dict[str, Any], rule: RiskRule) -> Dict[str, Any]:
        """检查集中度限制"""
        try:
            symbol = order_data['symbol']
            quantity = order_data['quantity']
            price = order_data.get('price', 50000)  # 使用估算价格
            
            # 获取账户总资产
            metrics = self.account_service.calculate_account_metrics(user_id)
            total_assets = metrics.get('total_assets', 0)
            
            if total_assets <= 0:
                return {'passed': True, 'message': '无法计算集中度，跳过检查'}
            
            # 计算该品种的市值变化
            position_value_change = quantity * price
            
            # 获取当前该品种的持仓市值
            position = self.position_service.get_position(user_id, symbol)
            current_value = float(position.market_value or 0) if position else 0
            
            new_total_value = current_value + position_value_change
            concentration_ratio = new_total_value / total_assets
            
            max_concentration = float(rule.rule_value)
            
            if concentration_ratio > max_concentration:
                return {
                    'passed': False,
                    'message': f'{symbol} 集中度 {concentration_ratio:.2%} 超过限制 {max_concentration:.2%}',
                    'risk_level': 'MEDIUM',
                    'rule_type': rule.rule_type.value
                }
            
            return {'passed': True, 'message': '集中度限制检查通过'}
            
        except Exception as e:
            logger.error(f"集中度限制检查失败: {e}")
            return {
                'passed': False,
                'message': f'集中度限制检查异常: {str(e)}',
                'risk_level': 'MEDIUM'
            }
    
    async def _record_risk_event(self, user_id: int, event_type: RiskEventType, 
                                title: str, description: str, event_data: Dict[str, Any]):
        """记录风险事件"""
        try:
            risk_event = RiskEvent(
                user_id=user_id,
                event_type=event_type,
                severity="HIGH",
                title=title,
                description=description,
                event_data=event_data,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(risk_event)
            self.db.commit()
            
            logger.info(f"风险事件已记录: {title}")
            
        except Exception as e:
            logger.error(f"记录风险事件失败: {e}")
    
    def _get_suggested_actions(self, failed_checks: List[Dict[str, Any]]) -> List[str]:
        """获取建议的处理动作"""
        actions = []
        
        for check in failed_checks:
            rule_type = check.get('rule_type')
            
            if rule_type == RiskRuleType.POSITION_LIMIT.value:
                actions.append("减少持仓规模")
            elif rule_type == RiskRuleType.ORDER_SIZE_LIMIT.value:
                actions.append("减少订单数量")
            elif rule_type == RiskRuleType.DAILY_LOSS_LIMIT.value:
                actions.append("停止交易，等待明日")
            elif rule_type == RiskRuleType.CONCENTRATION_LIMIT.value:
                actions.append("分散投资，降低集中度")
        
        return list(set(actions))  # 去重
    
    def _calculate_overall_risk_level(self, risk_alerts: List[Dict[str, Any]]) -> str:
        """计算整体风险等级"""
        if not risk_alerts:
            return "LOW"
        
        severities = [alert['severity'] for alert in risk_alerts]
        
        if 'HIGH' in severities:
            return "HIGH"
        elif 'MEDIUM' in severities:
            return "MEDIUM"
        else:
            return "LOW"
    
    async def _execute_auto_risk_actions(self, user_id: int, high_risk_alerts: List[Dict[str, Any]]):
        """执行自动风险处理动作"""
        try:
            for alert in high_risk_alerts:
                suggested_action = alert.get('suggested_action')
                
                if suggested_action == 'reduce_positions':
                    # 这里可以实现自动减仓逻辑
                    logger.warning(f"用户 {user_id} 触发高风险告警，建议减仓")
                elif suggested_action == 'cancel_orders':
                    # 这里可以实现自动撤单逻辑
                    logger.warning(f"用户 {user_id} 触发高风险告警，建议撤单")
                
                # 记录风险事件
                await self._record_risk_event(
                    user_id=user_id,
                    event_type=RiskEventType.DAILY_LOSS_LIMIT,
                    title=f"高风险告警: {alert['type']}",
                    description=alert['message'],
                    event_data=alert
                )
                
        except Exception as e:
            logger.error(f"执行自动风险处理失败: {e}")
    
    async def _cancel_all_orders(self, user_id: int, parameters: Dict[str, Any]):
        """撤销所有订单"""
        # 这里需要调用订单服务来撤销订单
        logger.info(f"执行自动撤单: 用户 {user_id}")
    
    async def _close_all_positions(self, user_id: int, parameters: Dict[str, Any]):
        """平掉所有持仓"""
        # 这里需要调用持仓服务来平仓
        logger.info(f"执行自动平仓: 用户 {user_id}")
    
    async def _freeze_account(self, user_id: int, parameters: Dict[str, Any]):
        """冻结账户"""
        # 这里需要调用账户服务来冻结账户
        logger.info(f"执行账户冻结: 用户 {user_id}")
    
    async def _send_alert(self, user_id: int, parameters: Dict[str, Any]):
        """发送告警通知"""
        # 这里需要调用通知服务来发送告警
        logger.info(f"发送风险告警: 用户 {user_id}")


# 全局风险引擎实例
risk_engine = None

def get_risk_engine(db: Session) -> RiskEngine:
    """获取风险引擎实例"""
    global risk_engine
    if risk_engine is None:
        risk_engine = RiskEngine(db)
    return risk_engine