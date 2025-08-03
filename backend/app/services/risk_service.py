"""
风险管理服务
"""
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from datetime import datetime, timedelta
from decimal import Decimal
import numpy as np
import pandas as pd
import logging

from ..models.risk import RiskRule, RiskEvent, RiskMetrics, RiskLimit
from ..models.enums import RiskLevel, RiskEventStatus, ActionType
from ..models.position import Position
from ..models.order import Order
from ..models.user import User
from ..models.strategy import Strategy
from ..core.database import get_db
from ..utils.risk_calculator import RiskCalculator
from ..services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class RiskService:
    """风险管理服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.risk_calculator = RiskCalculator()
        self.notification_service = NotificationService()
    
    # ==================== 风险规则管理 ====================
    
    def create_risk_rule(self, rule_data: Dict[str, Any], created_by: int) -> RiskRule:
        """创建风险规则"""
        try:
            rule = RiskRule(
                name=rule_data['name'],
                description=rule_data.get('description'),
                rule_type=rule_data['rule_type'],
                conditions=rule_data['conditions'],
                actions=rule_data['actions'],
                is_active=rule_data.get('is_active', True),
                priority=rule_data.get('priority', 0),
                risk_level=rule_data.get('risk_level', RiskLevel.MEDIUM),
                user_id=rule_data.get('user_id'),
                strategy_id=rule_data.get('strategy_id'),
                symbol_pattern=rule_data.get('symbol_pattern'),
                effective_from=rule_data.get('effective_from'),
                effective_to=rule_data.get('effective_to'),
                metadata=rule_data.get('metadata', {}),
                created_by=created_by
            )
            
            self.db.add(rule)
            self.db.commit()
            self.db.refresh(rule)
            
            logger.info(f"Created risk rule: {rule.name} (ID: {rule.id})")
            return rule
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating risk rule: {e}")
            raise
    
    def get_risk_rules(self, 
                      user_id: Optional[int] = None,
                      strategy_id: Optional[int] = None,
                      rule_type: Optional[str] = None,
                      is_active: Optional[bool] = None,
                      skip: int = 0,
                      limit: int = 100) -> List[RiskRule]:
        """获取风险规则列表"""
        query = self.db.query(RiskRule)
        
        if user_id is not None:
            query = query.filter(or_(RiskRule.user_id == user_id, RiskRule.user_id.is_(None)))
        
        if strategy_id is not None:
            query = query.filter(or_(RiskRule.strategy_id == strategy_id, RiskRule.strategy_id.is_(None)))
        
        if rule_type is not None:
            query = query.filter(RiskRule.rule_type == rule_type)
        
        if is_active is not None:
            query = query.filter(RiskRule.is_active == is_active)
        
        return query.order_by(desc(RiskRule.priority), RiskRule.created_at).offset(skip).limit(limit).all()
    
    def get_risk_rule(self, rule_id: int) -> Optional[RiskRule]:
        """获取单个风险规则"""
        return self.db.query(RiskRule).filter(RiskRule.id == rule_id).first()
    
    def update_risk_rule(self, rule_id: int, rule_data: Dict[str, Any]) -> Optional[RiskRule]:
        """更新风险规则"""
        try:
            rule = self.get_risk_rule(rule_id)
            if not rule:
                return None
            
            for key, value in rule_data.items():
                if hasattr(rule, key):
                    setattr(rule, key, value)
            
            self.db.commit()
            self.db.refresh(rule)
            
            logger.info(f"Updated risk rule: {rule.name} (ID: {rule.id})")
            return rule
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating risk rule {rule_id}: {e}")
            raise
    
    def delete_risk_rule(self, rule_id: int) -> bool:
        """删除风险规则"""
        try:
            rule = self.get_risk_rule(rule_id)
            if not rule:
                return False
            
            self.db.delete(rule)
            self.db.commit()
            
            logger.info(f"Deleted risk rule: {rule.name} (ID: {rule.id})")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting risk rule {rule_id}: {e}")
            raise
    
    # ==================== 风险监控 ====================
    
    def check_risk_rules(self, context: Dict[str, Any]) -> List[RiskEvent]:
        """检查风险规则并生成事件"""
        events = []
        
        try:
            # 获取适用的风险规则
            applicable_rules = self._get_applicable_rules(context)
            
            for rule in applicable_rules:
                if rule.evaluate_conditions(context):
                    # 创建风险事件
                    event = self._create_risk_event(rule, context)
                    events.append(event)
                    
                    # 执行风险处置动作
                    self._execute_risk_actions(rule, event, context)
                    
                    # 更新规则统计
                    rule.trigger_count += 1
                    rule.last_triggered_at = datetime.now()
            
            self.db.commit()
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error checking risk rules: {e}")
            raise
        
        return events
    
    def _get_applicable_rules(self, context: Dict[str, Any]) -> List[RiskRule]:
        """获取适用的风险规则"""
        query = self.db.query(RiskRule).filter(RiskRule.is_active == True)
        
        # 按优先级排序
        rules = query.order_by(desc(RiskRule.priority)).all()
        
        # 过滤适用的规则
        applicable_rules = []
        for rule in rules:
            if rule.is_applicable(context):
                applicable_rules.append(rule)
        
        return applicable_rules
    
    def _create_risk_event(self, rule: RiskRule, context: Dict[str, Any]) -> RiskEvent:
        """创建风险事件"""
        event = RiskEvent(
            rule_id=rule.id,
            event_type=rule.rule_type.value,
            severity=rule.risk_level,
            title=f"风险规则触发: {rule.name}",
            message=self._generate_event_message(rule, context),
            data=context.copy(),
            user_id=context.get('user_id'),
            strategy_id=context.get('strategy_id'),
            position_id=context.get('position_id'),
            order_id=context.get('order_id')
        )
        
        self.db.add(event)
        self.db.flush()  # 获取ID但不提交
        
        logger.warning(f"Risk event created: {event.title} (ID: {event.id})")
        return event
    
    def _generate_event_message(self, rule: RiskRule, context: Dict[str, Any]) -> str:
        """生成事件消息"""
        base_message = f"风险规则 '{rule.name}' 被触发"
        
        if rule.rule_type.value == "POSITION_LIMIT":
            position_value = context.get('position_value', 0)
            max_position = rule.conditions.get('max_position', 0)
            return f"{base_message}：持仓价值 {position_value} 超过限制 {max_position}"
        
        elif rule.rule_type.value == "CONCENTRATION":
            concentration = context.get('concentration', 0)
            max_concentration = rule.conditions.get('max_concentration', 0)
            return f"{base_message}：集中度 {concentration:.2%} 超过限制 {max_concentration:.2%}"
        
        elif rule.rule_type.value == "VAR_LIMIT":
            var_value = context.get('var_value', 0)
            max_var = rule.conditions.get('max_var', 0)
            return f"{base_message}：VaR值 {var_value} 超过限制 {max_var}"
        
        elif rule.rule_type.value == "DRAWDOWN_LIMIT":
            drawdown = context.get('drawdown', 0)
            max_drawdown = rule.conditions.get('max_drawdown', 0)
            return f"{base_message}：回撤 {abs(drawdown):.2%} 超过限制 {max_drawdown:.2%}"
        
        elif rule.rule_type.value == "LEVERAGE_LIMIT":
            leverage = context.get('leverage', 0)
            max_leverage = rule.conditions.get('max_leverage', 0)
            return f"{base_message}：杠杆率 {leverage:.2f} 超过限制 {max_leverage:.2f}"
        
        elif rule.rule_type.value == "LOSS_LIMIT":
            loss = context.get('loss', 0)
            max_loss = rule.conditions.get('max_loss', 0)
            return f"{base_message}：亏损 {abs(loss)} 超过限制 {max_loss}"
        
        else:
            return base_message
    
    def _execute_risk_actions(self, rule: RiskRule, event: RiskEvent, context: Dict[str, Any]):
        """执行风险处置动作"""
        actions = rule.actions
        if not actions:
            return
        
        for action in actions:
            action_type = action.get('type')
            action_params = action.get('params', {})
            
            try:
                if action_type == ActionType.ALERT.value:
                    self._send_alert(event, action_params)
                
                elif action_type == ActionType.BLOCK_ORDER.value:
                    self._block_order(context, action_params)
                
                elif action_type == ActionType.FORCE_CLOSE.value:
                    self._force_close_position(context, action_params)
                
                elif action_type == ActionType.REDUCE_POSITION.value:
                    self._reduce_position(context, action_params)
                
                elif action_type == ActionType.SUSPEND_TRADING.value:
                    self._suspend_trading(context, action_params)
                
                elif action_type == ActionType.NOTIFY_ADMIN.value:
                    self._notify_admin(event, action_params)
                
                logger.info(f"Executed risk action: {action_type} for event {event.id}")
                
            except Exception as e:
                logger.error(f"Error executing risk action {action_type}: {e}")
    
    def _send_alert(self, event: RiskEvent, params: Dict[str, Any]):
        """发送告警"""
        self.notification_service.send_risk_alert(
            user_id=event.user_id,
            title=event.title,
            message=event.message,
            severity=event.severity.value,
            data=event.data
        )
    
    def _block_order(self, context: Dict[str, Any], params: Dict[str, Any]):
        """阻止订单"""
        order_id = context.get('order_id')
        if order_id:
            # 这里应该调用订单服务来取消或阻止订单
            logger.info(f"Blocking order {order_id}")
    
    def _force_close_position(self, context: Dict[str, Any], params: Dict[str, Any]):
        """强制平仓"""
        position_id = context.get('position_id')
        if position_id:
            # 这里应该调用交易服务来强制平仓
            logger.info(f"Force closing position {position_id}")
    
    def _reduce_position(self, context: Dict[str, Any], params: Dict[str, Any]):
        """减仓"""
        position_id = context.get('position_id')
        reduce_ratio = params.get('reduce_ratio', 0.5)
        if position_id:
            # 这里应该调用交易服务来减仓
            logger.info(f"Reducing position {position_id} by {reduce_ratio:.2%}")
    
    def _suspend_trading(self, context: Dict[str, Any], params: Dict[str, Any]):
        """暂停交易"""
        user_id = context.get('user_id')
        strategy_id = context.get('strategy_id')
        duration = params.get('duration_minutes', 60)
        
        # 这里应该调用用户服务来暂停交易
        logger.info(f"Suspending trading for user {user_id}, strategy {strategy_id} for {duration} minutes")
    
    def _notify_admin(self, event: RiskEvent, params: Dict[str, Any]):
        """通知管理员"""
        self.notification_service.send_admin_notification(
            title=f"严重风险事件: {event.title}",
            message=event.message,
            severity=event.severity.value,
            data=event.data
        )
    
    # ==================== 风险事件管理 ====================
    
    def get_risk_events(self,
                       user_id: Optional[int] = None,
                       strategy_id: Optional[int] = None,
                       event_type: Optional[str] = None,
                       severity: Optional[str] = None,
                       status: Optional[str] = None,
                       start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None,
                       skip: int = 0,
                       limit: int = 100) -> List[RiskEvent]:
        """获取风险事件列表"""
        query = self.db.query(RiskEvent)
        
        if user_id is not None:
            query = query.filter(RiskEvent.user_id == user_id)
        
        if strategy_id is not None:
            query = query.filter(RiskEvent.strategy_id == strategy_id)
        
        if event_type is not None:
            query = query.filter(RiskEvent.event_type == event_type)
        
        if severity is not None:
            query = query.filter(RiskEvent.severity == severity)
        
        if status is not None:
            query = query.filter(RiskEvent.status == status)
        
        if start_date is not None:
            query = query.filter(RiskEvent.created_at >= start_date)
        
        if end_date is not None:
            query = query.filter(RiskEvent.created_at <= end_date)
        
        return query.order_by(desc(RiskEvent.created_at)).offset(skip).limit(limit).all()
    
    def get_risk_event(self, event_id: int) -> Optional[RiskEvent]:
        """获取单个风险事件"""
        return self.db.query(RiskEvent).filter(RiskEvent.id == event_id).first()
    
    def resolve_risk_event(self, event_id: int, resolved_by: int, notes: str = None) -> Optional[RiskEvent]:
        """解决风险事件"""
        try:
            event = self.get_risk_event(event_id)
            if not event:
                return None
            
            event.resolve(resolved_by, notes)
            self.db.commit()
            
            logger.info(f"Resolved risk event {event_id} by user {resolved_by}")
            return event
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error resolving risk event {event_id}: {e}")
            raise
    
    def escalate_risk_event(self, event_id: int) -> Optional[RiskEvent]:
        """升级风险事件"""
        try:
            event = self.get_risk_event(event_id)
            if not event:
                return None
            
            event.escalate()
            self.db.commit()
            
            # 发送升级通知
            self._notify_admin(event, {'escalated': True})
            
            logger.info(f"Escalated risk event {event_id}")
            return event
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error escalating risk event {event_id}: {e}")
            raise
    
    # ==================== 风险指标计算 ====================
    
    def calculate_risk_metrics(self, user_id: int, strategy_id: Optional[int] = None, 
                             date: Optional[datetime] = None) -> RiskMetrics:
        """计算风险指标"""
        if date is None:
            date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        try:
            # 获取用户持仓数据
            positions = self._get_user_positions(user_id, strategy_id)
            
            # 获取历史价格数据
            price_data = self._get_price_data(positions, date)
            
            # 计算基础指标
            portfolio_value = self.risk_calculator.calculate_portfolio_value(positions, price_data)
            cash_balance = self._get_cash_balance(user_id)
            total_exposure = self.risk_calculator.calculate_total_exposure(positions, price_data)
            net_exposure = self.risk_calculator.calculate_net_exposure(positions, price_data)
            
            # 计算收益指标
            daily_return = self.risk_calculator.calculate_daily_return(user_id, date)
            cumulative_return = self.risk_calculator.calculate_cumulative_return(user_id, date)
            
            # 计算风险指标
            volatility = self.risk_calculator.calculate_volatility(user_id, date)
            max_drawdown = self.risk_calculator.calculate_max_drawdown(user_id, date)
            current_drawdown = self.risk_calculator.calculate_current_drawdown(user_id, date)
            var_95 = self.risk_calculator.calculate_var(positions, price_data, confidence=0.95)
            var_99 = self.risk_calculator.calculate_var(positions, price_data, confidence=0.99)
            cvar_95 = self.risk_calculator.calculate_cvar(positions, price_data, confidence=0.95)
            
            # 计算杠杆和集中度
            leverage_ratio = self.risk_calculator.calculate_leverage_ratio(total_exposure, portfolio_value)
            concentration_ratio = self.risk_calculator.calculate_concentration_ratio(positions, price_data)
            
            # 计算流动性指标
            liquidity_ratio = self.risk_calculator.calculate_liquidity_ratio(positions)
            
            # 计算其他指标
            sharpe_ratio = self.risk_calculator.calculate_sharpe_ratio(user_id, date)
            sortino_ratio = self.risk_calculator.calculate_sortino_ratio(user_id, date)
            calmar_ratio = self.risk_calculator.calculate_calmar_ratio(user_id, date)
            
            # 创建或更新风险指标记录
            metrics = self.db.query(RiskMetrics).filter(
                and_(
                    RiskMetrics.user_id == user_id,
                    RiskMetrics.strategy_id == strategy_id,
                    RiskMetrics.date == date
                )
            ).first()
            
            if not metrics:
                metrics = RiskMetrics(
                    user_id=user_id,
                    strategy_id=strategy_id,
                    date=date
                )
                self.db.add(metrics)
            
            # 更新指标值
            metrics.portfolio_value = portfolio_value
            metrics.cash_balance = cash_balance
            metrics.total_exposure = total_exposure
            metrics.net_exposure = net_exposure
            metrics.daily_return = daily_return
            metrics.cumulative_return = cumulative_return
            metrics.volatility = volatility
            metrics.max_drawdown = max_drawdown
            metrics.current_drawdown = current_drawdown
            metrics.var_95 = var_95
            metrics.var_99 = var_99
            metrics.cvar_95 = cvar_95
            metrics.leverage_ratio = leverage_ratio
            metrics.concentration_ratio = concentration_ratio
            metrics.liquidity_ratio = liquidity_ratio
            metrics.sharpe_ratio = sharpe_ratio
            metrics.sortino_ratio = sortino_ratio
            metrics.calmar_ratio = calmar_ratio
            
            self.db.commit()
            self.db.refresh(metrics)
            
            logger.info(f"Calculated risk metrics for user {user_id}, strategy {strategy_id}")
            return metrics
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error calculating risk metrics: {e}")
            raise
    
    def get_risk_metrics(self,
                        user_id: int,
                        strategy_id: Optional[int] = None,
                        start_date: Optional[datetime] = None,
                        end_date: Optional[datetime] = None,
                        period_type: str = 'daily') -> List[RiskMetrics]:
        """获取风险指标历史数据"""
        query = self.db.query(RiskMetrics).filter(
            RiskMetrics.user_id == user_id,
            RiskMetrics.period_type == period_type
        )
        
        if strategy_id is not None:
            query = query.filter(RiskMetrics.strategy_id == strategy_id)
        
        if start_date is not None:
            query = query.filter(RiskMetrics.date >= start_date)
        
        if end_date is not None:
            query = query.filter(RiskMetrics.date <= end_date)
        
        return query.order_by(RiskMetrics.date).all()
    
    def _get_user_positions(self, user_id: int, strategy_id: Optional[int] = None) -> List[Position]:
        """获取用户持仓"""
        query = self.db.query(Position).filter(Position.user_id == user_id)
        
        if strategy_id is not None:
            query = query.filter(Position.strategy_id == strategy_id)
        
        return query.all()
    
    def _get_price_data(self, positions: List[Position], date: datetime) -> Dict[str, float]:
        """获取价格数据"""
        # 这里应该从市场数据服务获取价格数据
        # 暂时返回模拟数据
        price_data = {}
        for position in positions:
            price_data[position.symbol] = 100.0  # 模拟价格
        return price_data
    
    def _get_cash_balance(self, user_id: int) -> Decimal:
        """获取现金余额"""
        # 这里应该从账户服务获取现金余额
        # 暂时返回模拟数据
        return Decimal('10000.00')