"""
风险管理引擎
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from contextlib import contextmanager

from ..core.database import get_db
from ..services.risk_service import RiskService
from ..services.notification_service import NotificationService
from ..models.risk import RiskRule, RiskEvent, RiskMetrics, RiskLimit
from ..models.position import Position
from ..models.order import Order
from ..models.user import User

logger = logging.getLogger(__name__)


class RiskEngine:
    """风险管理引擎"""
    
    def __init__(self):
        self.is_running = False
        self.check_interval = 60  # 检查间隔（秒）
        self.notification_service = NotificationService()
        self._tasks = []
    
    @contextmanager
    def get_db_session(self):
        """获取数据库会话"""
        db = next(get_db())
        try:
            yield db
        finally:
            db.close()
    
    async def start(self):
        """启动风险引擎"""
        if self.is_running:
            logger.warning("Risk engine is already running")
            return
        
        self.is_running = True
        logger.info("Starting risk engine...")
        
        # 启动各种监控任务
        self._tasks = [
            asyncio.create_task(self._real_time_risk_monitor()),
            asyncio.create_task(self._periodic_risk_calculation()),
            asyncio.create_task(self._risk_limit_monitor()),
            asyncio.create_task(self._risk_event_processor())
        ]
        
        logger.info("Risk engine started successfully")
    
    async def stop(self):
        """停止风险引擎"""
        if not self.is_running:
            logger.warning("Risk engine is not running")
            return
        
        self.is_running = False
        logger.info("Stopping risk engine...")
        
        # 取消所有任务
        for task in self._tasks:
            task.cancel()
        
        # 等待任务完成
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        
        logger.info("Risk engine stopped successfully")
    
    async def _real_time_risk_monitor(self):
        """实时风险监控"""
        logger.info("Starting real-time risk monitor")
        
        while self.is_running:
            try:
                with self.get_db_session() as db:
                    risk_service = RiskService(db)
                    
                    # 获取所有活跃用户
                    active_users = self._get_active_users(db)
                    
                    for user in active_users:
                        await self._check_user_risk(risk_service, user.id)
                
                # 等待下一次检查
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                logger.info("Real-time risk monitor cancelled")
                break
            except Exception as e:
                logger.error(f"Error in real-time risk monitor: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def _periodic_risk_calculation(self):
        """定期风险指标计算"""
        logger.info("Starting periodic risk calculation")
        
        while self.is_running:
            try:
                # 每小时计算一次风险指标
                await asyncio.sleep(3600)
                
                if not self.is_running:
                    break
                
                with self.get_db_session() as db:
                    risk_service = RiskService(db)
                    
                    # 获取所有活跃用户
                    active_users = self._get_active_users(db)
                    
                    for user in active_users:
                        try:
                            # 计算用户的风险指标
                            metrics = risk_service.calculate_risk_metrics(user.id)
                            logger.info(f"Calculated risk metrics for user {user.id}")
                        except Exception as e:
                            logger.error(f"Error calculating risk metrics for user {user.id}: {e}")
                
            except asyncio.CancelledError:
                logger.info("Periodic risk calculation cancelled")
                break
            except Exception as e:
                logger.error(f"Error in periodic risk calculation: {e}")
    
    async def _risk_limit_monitor(self):
        """风险限额监控"""
        logger.info("Starting risk limit monitor")
        
        while self.is_running:
            try:
                with self.get_db_session() as db:
                    # 获取所有活跃的风险限额
                    active_limits = db.query(RiskLimit).filter(
                        RiskLimit.is_active == True
                    ).all()
                    
                    for limit in active_limits:
                        try:
                            # 重置限额（如果需要）
                            limit.reset_if_needed()
                            
                            # 检查限额使用情况
                            current_value = self._get_current_limit_value(db, limit)
                            is_breached = limit.check_breach(current_value)
                            
                            if is_breached and limit.is_hard_limit:
                                # 硬限制违反，需要立即处理
                                await self._handle_limit_breach(db, limit)
                            elif limit.is_warning_level():
                                # 达到预警水平
                                await self._handle_limit_warning(db, limit)
                        
                        except Exception as e:
                            logger.error(f"Error checking risk limit {limit.id}: {e}")
                    
                    db.commit()
                
                # 等待下一次检查
                await asyncio.sleep(300)  # 5分钟检查一次
                
            except asyncio.CancelledError:
                logger.info("Risk limit monitor cancelled")
                break
            except Exception as e:
                logger.error(f"Error in risk limit monitor: {e}")
                await asyncio.sleep(300)
    
    async def _risk_event_processor(self):
        """风险事件处理器"""
        logger.info("Starting risk event processor")
        
        while self.is_running:
            try:
                with self.get_db_session() as db:
                    # 获取未处理的高优先级风险事件
                    critical_events = db.query(RiskEvent).filter(
                        RiskEvent.status == 'ACTIVE',
                        RiskEvent.severity.in_(['HIGH', 'CRITICAL'])
                    ).order_by(RiskEvent.created_at).limit(10).all()
                    
                    for event in critical_events:
                        try:
                            await self._process_risk_event(db, event)
                        except Exception as e:
                            logger.error(f"Error processing risk event {event.id}: {e}")
                
                # 等待下一次处理
                await asyncio.sleep(30)  # 30秒检查一次
                
            except asyncio.CancelledError:
                logger.info("Risk event processor cancelled")
                break
            except Exception as e:
                logger.error(f"Error in risk event processor: {e}")
                await asyncio.sleep(30)
    
    async def _check_user_risk(self, risk_service: RiskService, user_id: int):
        """检查用户风险"""
        try:
            # 获取用户持仓
            positions = risk_service._get_user_positions(user_id)
            
            if not positions:
                return
            
            # 构建风险检查上下文
            context = await self._build_risk_context(risk_service, user_id, positions)
            
            # 检查风险规则
            events = risk_service.check_risk_rules(context)
            
            if events:
                logger.info(f"User {user_id} triggered {len(events)} risk events")
        
        except Exception as e:
            logger.error(f"Error checking risk for user {user_id}: {e}")
    
    async def _build_risk_context(self, risk_service: RiskService, user_id: int, 
                                positions: List[Position]) -> Dict[str, Any]:
        """构建风险检查上下文"""
        try:
            # 获取价格数据
            price_data = risk_service._get_price_data(positions, datetime.now())
            
            # 计算基础指标
            portfolio_value = float(risk_service.risk_calculator.calculate_portfolio_value(positions, price_data))
            total_exposure = float(risk_service.risk_calculator.calculate_total_exposure(positions, price_data))
            net_exposure = float(risk_service.risk_calculator.calculate_net_exposure(positions, price_data))
            leverage_ratio = float(risk_service.risk_calculator.calculate_leverage_ratio(
                total_exposure, portfolio_value
            ) or 0)
            concentration_ratio = float(risk_service.risk_calculator.calculate_concentration_ratio(
                positions, price_data
            ) or 0)
            
            # 获取最新的风险指标
            latest_metrics = risk_service.get_risk_metrics(user_id, limit=1)
            
            context = {
                'user_id': user_id,
                'portfolio_value': portfolio_value,
                'total_exposure': total_exposure,
                'net_exposure': net_exposure,
                'leverage': leverage_ratio,
                'concentration': concentration_ratio,
                'position_count': len(positions)
            }
            
            if latest_metrics:
                metrics = latest_metrics[0]
                context.update({
                    'drawdown': float(metrics.current_drawdown or 0),
                    'var_value': float(metrics.var_95 or 0),
                    'volatility': float(metrics.volatility or 0),
                    'liquidity_ratio': float(metrics.liquidity_ratio or 1.0)
                })
            
            return context
        
        except Exception as e:
            logger.error(f"Error building risk context for user {user_id}: {e}")
            return {'user_id': user_id}
    
    def _get_active_users(self, db: Session) -> List[User]:
        """获取活跃用户"""
        # 获取最近24小时内有活动的用户
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        return db.query(User).filter(
            User.is_active == True,
            User.last_login_at >= cutoff_time
        ).all()
    
    def _get_current_limit_value(self, db: Session, limit: RiskLimit) -> float:
        """获取当前限额使用值"""
        try:
            if limit.limit_type == "position_value":
                # 计算持仓价值
                positions = db.query(Position).filter(
                    Position.user_id == limit.user_id
                ).all()
                
                if limit.strategy_id:
                    positions = [p for p in positions if p.strategy_id == limit.strategy_id]
                
                total_value = sum(abs(float(p.quantity) * float(p.avg_cost)) for p in positions)
                return total_value
            
            elif limit.limit_type == "daily_loss":
                # 计算当日亏损
                today = datetime.now().date()
                # 这里应该从交易记录计算当日亏损
                return 0.0
            
            elif limit.limit_type == "order_count":
                # 计算订单数量
                today = datetime.now().date()
                order_count = db.query(Order).filter(
                    Order.user_id == limit.user_id,
                    Order.created_at >= today
                ).count()
                
                return float(order_count)
            
            else:
                return 0.0
        
        except Exception as e:
            logger.error(f"Error getting current limit value for limit {limit.id}: {e}")
            return 0.0
    
    async def _handle_limit_breach(self, db: Session, limit: RiskLimit):
        """处理限额违反"""
        try:
            # 创建风险事件
            event = RiskEvent(
                rule_id=None,  # 限额违反不关联具体规则
                event_type="LIMIT_BREACH",
                severity="HIGH",
                title=f"风险限额违反: {limit.limit_name}",
                message=f"用户 {limit.user_id} 的 {limit.limit_name} 超过限制 {limit.limit_value}，当前值 {limit.current_value}",
                data={
                    'limit_id': limit.id,
                    'limit_type': limit.limit_type,
                    'limit_value': float(limit.limit_value),
                    'current_value': float(limit.current_value),
                    'utilization_ratio': float(limit.utilization_ratio)
                },
                user_id=limit.user_id,
                strategy_id=limit.strategy_id
            )
            
            db.add(event)
            db.flush()
            
            # 发送通知
            await self.notification_service.send_risk_alert(
                user_id=limit.user_id,
                title=event.title,
                message=event.message,
                severity="HIGH",
                data=event.data
            )
            
            logger.warning(f"Risk limit breach: {limit.limit_name} for user {limit.user_id}")
        
        except Exception as e:
            logger.error(f"Error handling limit breach for limit {limit.id}: {e}")
    
    async def _handle_limit_warning(self, db: Session, limit: RiskLimit):
        """处理限额预警"""
        try:
            # 发送预警通知
            await self.notification_service.send_risk_alert(
                user_id=limit.user_id,
                title=f"风险限额预警: {limit.limit_name}",
                message=f"您的 {limit.limit_name} 已达到 {limit.utilization_ratio:.1%}，接近限制值",
                severity="MEDIUM",
                data={
                    'limit_id': limit.id,
                    'limit_type': limit.limit_type,
                    'utilization_ratio': float(limit.utilization_ratio),
                    'warning_threshold': float(limit.warning_threshold)
                }
            )
            
            logger.info(f"Risk limit warning: {limit.limit_name} for user {limit.user_id}")
        
        except Exception as e:
            logger.error(f"Error handling limit warning for limit {limit.id}: {e}")
    
    async def _process_risk_event(self, db: Session, event: RiskEvent):
        """处理风险事件"""
        try:
            # 检查事件是否需要自动升级
            if self._should_escalate_event(event):
                event.escalate()
                
                # 发送升级通知
                await self.notification_service.send_admin_notification(
                    title=f"风险事件升级: {event.title}",
                    message=f"风险事件 {event.id} 已升级为 {event.severity.value} 级别",
                    severity=event.severity.value,
                    data=event.data
                )
            
            # 检查事件是否可以自动解决
            if self._can_auto_resolve_event(event):
                event.resolve(resolved_by=None, notes="系统自动解决")
                logger.info(f"Auto-resolved risk event {event.id}")
            
            db.commit()
        
        except Exception as e:
            logger.error(f"Error processing risk event {event.id}: {e}")
            db.rollback()
    
    def _should_escalate_event(self, event: RiskEvent) -> bool:
        """判断事件是否应该升级"""
        # 如果事件创建超过1小时且未解决，则升级
        if event.status == 'ACTIVE':
            time_since_created = datetime.now() - event.created_at
            if time_since_created > timedelta(hours=1):
                return True
        
        return False
    
    def _can_auto_resolve_event(self, event: RiskEvent) -> bool:
        """判断事件是否可以自动解决"""
        # 这里可以实现自动解决的逻辑
        # 例如，如果触发条件已经不再满足，则可以自动解决
        return False
    
    # ==================== 外部接口 ====================
    
    async def check_order_risk(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """检查订单风险"""
        try:
            with self.get_db_session() as db:
                risk_service = RiskService(db)
                
                # 构建订单风险检查上下文
                context = {
                    'user_id': order_data['user_id'],
                    'symbol': order_data['symbol'],
                    'order_type': order_data['order_type'],
                    'side': order_data['side'],
                    'quantity': order_data['quantity'],
                    'price': order_data.get('price', 0),
                    'order_value': order_data['quantity'] * order_data.get('price', 0)
                }
                
                # 检查风险规则
                events = risk_service.check_risk_rules(context)
                
                # 判断是否允许下单
                allow_order = True
                block_reasons = []
                
                for event in events:
                    rule = risk_service.get_risk_rule(event.rule_id)
                    if rule:
                        for action in rule.actions:
                            if action.get('type') == 'BLOCK_ORDER':
                                allow_order = False
                                block_reasons.append(event.message)
                
                return {
                    'allow_order': allow_order,
                    'block_reasons': block_reasons,
                    'risk_events': [event.to_dict() for event in events]
                }
        
        except Exception as e:
            logger.error(f"Error checking order risk: {e}")
            return {
                'allow_order': False,
                'block_reasons': [f"风险检查失败: {str(e)}"],
                'risk_events': []
            }
    
    async def check_position_risk(self, user_id: int, strategy_id: Optional[int] = None) -> Dict[str, Any]:
        """检查持仓风险"""
        try:
            with self.get_db_session() as db:
                risk_service = RiskService(db)
                
                # 获取用户持仓
                positions = risk_service._get_user_positions(user_id, strategy_id)
                
                if not positions:
                    return {
                        'risk_level': 'LOW',
                        'risk_events': [],
                        'recommendations': []
                    }
                
                # 构建风险检查上下文
                context = await self._build_risk_context(risk_service, user_id, positions)
                
                # 检查风险规则
                events = risk_service.check_risk_rules(context)
                
                # 评估整体风险水平
                risk_level = self._evaluate_risk_level(events, context)
                
                # 生成风险建议
                recommendations = self._generate_risk_recommendations(events, context)
                
                return {
                    'risk_level': risk_level,
                    'risk_events': [event.to_dict() for event in events],
                    'recommendations': recommendations,
                    'context': context
                }
        
        except Exception as e:
            logger.error(f"Error checking position risk: {e}")
            return {
                'risk_level': 'UNKNOWN',
                'risk_events': [],
                'recommendations': [f"风险检查失败: {str(e)}"]
            }
    
    def _evaluate_risk_level(self, events: List[RiskEvent], context: Dict[str, Any]) -> str:
        """评估风险水平"""
        if not events:
            return 'LOW'
        
        # 根据事件严重程度评估
        max_severity = max(event.severity for event in events)
        
        if max_severity == 'CRITICAL':
            return 'CRITICAL'
        elif max_severity == 'HIGH':
            return 'HIGH'
        elif max_severity == 'MEDIUM':
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _generate_risk_recommendations(self, events: List[RiskEvent], context: Dict[str, Any]) -> List[str]:
        """生成风险建议"""
        recommendations = []
        
        # 根据风险事件生成建议
        for event in events:
            if event.event_type == 'POSITION_LIMIT':
                recommendations.append("建议减少单一标的持仓规模")
            elif event.event_type == 'CONCENTRATION':
                recommendations.append("建议分散投资，降低集中度风险")
            elif event.event_type == 'DRAWDOWN_LIMIT':
                recommendations.append("建议暂停交易，等待市场回调")
            elif event.event_type == 'LEVERAGE_LIMIT':
                recommendations.append("建议降低杠杆率，减少风险敞口")
            elif event.event_type == 'VAR_LIMIT':
                recommendations.append("建议调整持仓结构，降低VaR值")
        
        # 根据上下文生成通用建议
        leverage = context.get('leverage', 0)
        if leverage > 2.0:
            recommendations.append("当前杠杆率较高，建议谨慎操作")
        
        concentration = context.get('concentration', 0)
        if concentration > 0.3:
            recommendations.append("持仓集中度较高，建议适当分散")
        
        return list(set(recommendations))  # 去重


# 全局风险引擎实例
risk_engine = RiskEngine()