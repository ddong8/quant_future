"""
订单管理服务
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func
from datetime import datetime, timedelta
from decimal import Decimal
import uuid

from ..models.order import Order, OrderFill, OrderTemplate, OrderStatus, OrderType, OrderSide
from ..models.strategy import Strategy
from ..models.backtest import Backtest
from ..schemas.order import (
    OrderCreate, OrderUpdate, OrderSearchParams,
    OrderTemplateCreate, OrderTemplateUpdate,
    OrderActionRequest, OrderRiskCheckRequest
)
from ..core.exceptions import ValidationError, NotFoundError, PermissionError
from ..core.websocket import websocket_manager
from .order_notification_service import order_notification_service

logger = logging.getLogger(__name__)


class OrderService:
    """订单管理服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_order(self, order_data: OrderCreate, user_id: int) -> Order:
        """创建订单"""
        try:
            # 验证关联资源权限
            if order_data.strategy_id:
                strategy = self.db.query(Strategy).filter(
                    Strategy.id == order_data.strategy_id,
                    Strategy.user_id == user_id
                ).first()
                if not strategy:
                    raise NotFoundError("策略不存在或无权限访问")
            
            if order_data.backtest_id:
                backtest = self.db.query(Backtest).filter(
                    Backtest.id == order_data.backtest_id,
                    Backtest.user_id == user_id
                ).first()
                if not backtest:
                    raise NotFoundError("回测不存在或无权限访问")
            
            # 验证父订单
            if order_data.parent_order_id:
                parent_order = self.db.query(Order).filter(
                    Order.id == order_data.parent_order_id,
                    Order.user_id == user_id
                ).first()
                if not parent_order:
                    raise NotFoundError("父订单不存在或无权限访问")
            
            # 创建订单
            order = Order(
                uuid=str(uuid.uuid4()),
                symbol=order_data.symbol,
                order_type=order_data.order_type,
                side=order_data.side,
                quantity=order_data.quantity,
                price=order_data.price,
                stop_price=order_data.stop_price,
                time_in_force=order_data.time_in_force,
                priority=order_data.priority,
                iceberg_quantity=order_data.iceberg_quantity,
                trailing_amount=order_data.trailing_amount,
                trailing_percent=order_data.trailing_percent,
                expire_time=order_data.expire_time,
                max_position_size=order_data.max_position_size,
                strategy_id=order_data.strategy_id,
                backtest_id=order_data.backtest_id,
                parent_order_id=order_data.parent_order_id,
                broker=order_data.broker,
                account_id=order_data.account_id,
                tags=order_data.tags,
                notes=order_data.notes,
                metadata=order_data.metadata,
                user_id=user_id,
                source="manual"
            )
            
            # 计算剩余数量
            order.calculate_remaining_quantity()
            
            self.db.add(order)
            self.db.commit()
            self.db.refresh(order)
            
            # 发送WebSocket通知
            order_notification_service.notify_order_created(order)
            
            logger.info(f"创建订单成功: {order.id} - {order.symbol} {order.side} {order.quantity}")
            return order
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建订单失败: {str(e)}")
            raise
    
    def get_order(self, order_id: int, user_id: int) -> Optional[Order]:
        """获取订单详情"""
        order = self.db.query(Order).filter(
            Order.id == order_id,
            Order.user_id == user_id
        ).first()
        
        if not order:
            raise NotFoundError("订单不存在或无权限访问")
        
        return order
    
    def get_order_by_uuid(self, order_uuid: str, user_id: int) -> Optional[Order]:
        """通过UUID获取订单"""
        order = self.db.query(Order).filter(
            Order.uuid == order_uuid,
            Order.user_id == user_id
        ).first()
        
        if not order:
            raise NotFoundError("订单不存在或无权限访问")
        
        return order
    
    def update_order(self, order_id: int, order_data: OrderUpdate, user_id: int) -> Order:
        """更新订单"""
        try:
            order = self.db.query(Order).filter(
                Order.id == order_id,
                Order.user_id == user_id
            ).first()
            
            if not order:
                raise NotFoundError("订单不存在或无权限访问")
            
            # 检查订单是否可以修改
            if not order.is_active:
                raise ValidationError("只能修改活跃状态的订单")
            
            # 更新字段
            update_data = order_data.dict(exclude_unset=True)
            updated_fields = list(update_data.keys())
            
            for field, value in update_data.items():
                if hasattr(order, field):
                    setattr(order, field, value)
            
            # 重新计算剩余数量
            if 'quantity' in update_data:
                order.calculate_remaining_quantity()
            
            self.db.commit()
            self.db.refresh(order)
            
            # 发送WebSocket通知
            order_notification_service.notify_order_updated(order, updated_fields)
            
            logger.info(f"更新订单成功: {order.id}")
            return order
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新订单失败: {str(e)}")
            raise
    
    def cancel_order(self, order_id: int, user_id: int, reason: str = "") -> Order:
        """取消订单"""
        try:
            order = self.db.query(Order).filter(
                Order.id == order_id,
                Order.user_id == user_id
            ).first()
            
            if not order:
                raise NotFoundError("订单不存在或无权限访问")
            
            if not order.is_active:
                raise ValidationError("只能取消活跃状态的订单")
            
            # 保存旧状态
            old_status = order.status
            
            # 更新订单状态
            order.status = OrderStatus.CANCELLED
            order.cancelled_at = datetime.now()
            if reason:
                order.notes = f"{order.notes or ''}\n取消原因: {reason}".strip()
            
            self.db.commit()
            self.db.refresh(order)
            
            # 发送WebSocket通知
            order_notification_service.notify_order_cancelled(order, reason)
            order_notification_service.notify_order_status_change(order, old_status)
            
            logger.info(f"取消订单成功: {order.id}")
            return order
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"取消订单失败: {str(e)}")
            raise
    
    def search_orders(self, params: OrderSearchParams, user_id: int) -> Tuple[List[Order], int]:
        """搜索订单"""
        query = self.db.query(Order).filter(Order.user_id == user_id)
        
        # 交易标的筛选
        if params.symbol:
            query = query.filter(Order.symbol.ilike(f"%{params.symbol}%"))
        
        # 订单类型筛选
        if params.order_type:
            query = query.filter(Order.order_type == params.order_type)
        
        # 订单方向筛选
        if params.side:
            query = query.filter(Order.side == params.side)
        
        # 订单状态筛选
        if params.status:
            query = query.filter(Order.status == params.status)
        
        # 策略筛选
        if params.strategy_id:
            query = query.filter(Order.strategy_id == params.strategy_id)
        
        # 回测筛选
        if params.backtest_id:
            query = query.filter(Order.backtest_id == params.backtest_id)
        
        # 标签筛选
        if params.tags:
            for tag in params.tags:
                query = query.filter(Order.tags.contains([tag]))
        
        # 时间范围筛选
        if params.created_after:
            query = query.filter(Order.created_at >= params.created_after)
        
        if params.created_before:
            query = query.filter(Order.created_at <= params.created_before)
        
        # 数量范围筛选
        if params.min_quantity:
            query = query.filter(Order.quantity >= params.min_quantity)
        
        if params.max_quantity:
            query = query.filter(Order.quantity <= params.max_quantity)
        
        # 价格范围筛选
        if params.min_price:
            query = query.filter(Order.price >= params.min_price)
        
        if params.max_price:
            query = query.filter(Order.price <= params.max_price)
        
        # 获取总数
        total = query.count()
        
        # 排序
        sort_field = getattr(Order, params.sort_by)
        if params.sort_order == 'desc':
            query = query.order_by(desc(sort_field))
        else:
            query = query.order_by(asc(sort_field))
        
        # 分页
        offset = (params.page - 1) * params.page_size
        orders = query.offset(offset).limit(params.page_size).all()
        
        return orders, total
    
    def get_user_orders(self, user_id: int, status: Optional[OrderStatus] = None, 
                       limit: int = 50) -> List[Order]:
        """获取用户订单列表"""
        query = self.db.query(Order).filter(Order.user_id == user_id)
        
        if status:
            query = query.filter(Order.status == status)
        
        return query.order_by(desc(Order.created_at)).limit(limit).all()
    
    def get_active_orders(self, user_id: int) -> List[Order]:
        """获取活跃订单"""
        return self.db.query(Order).filter(
            Order.user_id == user_id,
            Order.status.in_([
                OrderStatus.PENDING,
                OrderStatus.SUBMITTED,
                OrderStatus.ACCEPTED,
                OrderStatus.PARTIALLY_FILLED
            ])
        ).order_by(desc(Order.created_at)).all()
    
    def get_order_stats(self, user_id: int) -> Dict[str, Any]:
        """获取订单统计信息"""
        # 基础统计
        total_orders = self.db.query(Order).filter(Order.user_id == user_id).count()
        
        active_orders = self.db.query(Order).filter(
            Order.user_id == user_id,
            Order.status.in_([
                OrderStatus.PENDING,
                OrderStatus.SUBMITTED,
                OrderStatus.ACCEPTED,
                OrderStatus.PARTIALLY_FILLED
            ])
        ).count()
        
        filled_orders = self.db.query(Order).filter(
            Order.user_id == user_id,
            Order.status == OrderStatus.FILLED
        ).count()
        
        cancelled_orders = self.db.query(Order).filter(
            Order.user_id == user_id,
            Order.status == OrderStatus.CANCELLED
        ).count()
        
        rejected_orders = self.db.query(Order).filter(
            Order.user_id == user_id,
            Order.status == OrderStatus.REJECTED
        ).count()
        
        # 成交统计
        filled_query = self.db.query(Order).filter(
            Order.user_id == user_id,
            Order.filled_quantity > 0
        )
        
        total_volume = filled_query.with_entities(
            func.sum(Order.filled_quantity)
        ).scalar() or Decimal('0')
        
        total_value = filled_query.with_entities(
            func.sum(Order.filled_quantity * Order.avg_fill_price)
        ).scalar() or Decimal('0')
        
        # 成交率统计
        orders_with_fills = self.db.query(Order).filter(
            Order.user_id == user_id,
            Order.quantity > 0
        ).all()
        
        if orders_with_fills:
            fill_ratios = [order.fill_ratio for order in orders_with_fills]
            avg_fill_ratio = sum(fill_ratios) / len(fill_ratios)
        else:
            avg_fill_ratio = 0.0
        
        # 成功率（完全成交的订单比例）
        success_rate = filled_orders / total_orders if total_orders > 0 else 0.0
        
        return {
            'total_orders': total_orders,
            'active_orders': active_orders,
            'filled_orders': filled_orders,
            'cancelled_orders': cancelled_orders,
            'rejected_orders': rejected_orders,
            'total_volume': float(total_volume),
            'total_value': float(total_value),
            'avg_fill_ratio': round(avg_fill_ratio, 4),
            'success_rate': round(success_rate, 4)
        }
    
    def add_order_fill(self, order_id: int, fill_data: Dict[str, Any]) -> OrderFill:
        """添加订单成交记录"""
        try:
            order = self.db.query(Order).filter(Order.id == order_id).first()
            if not order:
                raise NotFoundError("订单不存在")
            
            # 创建成交记录
            fill = OrderFill(
                uuid=str(uuid.uuid4()),
                order_id=order_id,
                fill_id_external=fill_data.get('fill_id_external'),
                quantity=Decimal(str(fill_data['quantity'])),
                price=Decimal(str(fill_data['price'])),
                value=Decimal(str(fill_data['quantity'])) * Decimal(str(fill_data['price'])),
                commission=Decimal(str(fill_data.get('commission', 0))),
                commission_asset=fill_data.get('commission_asset'),
                fill_time=fill_data.get('fill_time', datetime.now()),
                liquidity=fill_data.get('liquidity'),
                counterparty=fill_data.get('counterparty'),
                metadata=fill_data.get('metadata', {})
            )
            
            self.db.add(fill)
            
            # 更新订单状态
            order.filled_quantity += fill.quantity
            order.commission += fill.commission
            order.calculate_remaining_quantity()
            order.update_avg_fill_price()
            
            # 保存旧状态
            old_status = order.status
            
            # 更新订单状态
            if order.filled_quantity >= order.quantity:
                order.status = OrderStatus.FILLED
                order.filled_at = datetime.now()
            elif order.filled_quantity > 0:
                order.status = OrderStatus.PARTIALLY_FILLED
            
            self.db.commit()
            self.db.refresh(fill)
            self.db.refresh(order)
            
            # 发送WebSocket通知
            order_notification_service.notify_order_filled(order, fill)
            if old_status != order.status:
                order_notification_service.notify_order_status_change(order, old_status)
            
            logger.info(f"添加订单成交记录: {order_id}, 数量: {fill.quantity}, 价格: {fill.price}")
            return fill
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"添加订单成交记录失败: {str(e)}")
            raise
    
    def perform_risk_check(self, risk_data: OrderRiskCheckRequest, user_id: int) -> Dict[str, Any]:
        """执行订单风险检查"""
        try:
            warnings = []
            errors = []
            suggestions = []
            risk_score = 0.0
            
            # 基础风险检查
            # 1. 检查持仓限制
            current_position = self._get_current_position(risk_data.symbol, user_id)
            if risk_data.side == OrderSide.BUY:
                new_position = current_position + risk_data.quantity
            else:
                new_position = current_position - risk_data.quantity
            
            # 2. 检查资金充足性
            if risk_data.price and risk_data.side == OrderSide.BUY:
                required_funds = risk_data.quantity * risk_data.price
                available_funds = self._get_available_funds(user_id)
                
                if required_funds > available_funds:
                    errors.append("资金不足")
                    risk_score += 30
                elif required_funds > available_funds * Decimal('0.8'):
                    warnings.append("资金使用率较高")
                    risk_score += 15
            
            # 3. 检查价格合理性
            if risk_data.price:
                market_price = self._get_market_price(risk_data.symbol)
                if market_price:
                    price_diff = abs(risk_data.price - market_price) / market_price
                    if price_diff > 0.1:  # 价格偏离超过10%
                        warnings.append("订单价格偏离市价较大")
                        risk_score += 10
            
            # 4. 检查订单数量
            if risk_data.quantity > Decimal('1000000'):  # 大额订单
                warnings.append("订单数量较大，建议分批执行")
                risk_score += 5
            
            # 5. 检查策略风险
            if risk_data.strategy_id:
                strategy_risk = self._check_strategy_risk(risk_data.strategy_id, user_id)
                risk_score += strategy_risk
            
            # 确定风险等级
            if risk_score >= 50:
                risk_level = "high"
            elif risk_score >= 20:
                risk_level = "medium"
            else:
                risk_level = "low"
            
            # 生成建议
            if risk_level == "high":
                suggestions.append("建议降低订单数量或调整价格")
            elif risk_level == "medium":
                suggestions.append("建议谨慎执行，关注市场变化")
            
            # 计算最大允许数量
            max_allowed_quantity = self._calculate_max_allowed_quantity(
                risk_data.symbol, risk_data.side, user_id
            )
            
            # 估算保证金
            estimated_margin = self._estimate_margin_requirement(
                risk_data.symbol, risk_data.quantity, risk_data.price
            )
            
            return {
                'passed': len(errors) == 0,
                'risk_level': risk_level,
                'warnings': warnings,
                'errors': errors,
                'suggestions': suggestions,
                'risk_score': risk_score,
                'max_allowed_quantity': float(max_allowed_quantity) if max_allowed_quantity else None,
                'estimated_margin': float(estimated_margin) if estimated_margin else None
            }
            
        except Exception as e:
            logger.error(f"风险检查失败: {str(e)}")
            return {
                'passed': False,
                'risk_level': 'high',
                'warnings': [],
                'errors': [f"风险检查系统错误: {str(e)}"],
                'suggestions': ['请稍后重试或联系客服'],
                'risk_score': 100.0,
                'max_allowed_quantity': None,
                'estimated_margin': None
            }
    
    def batch_cancel_orders(self, order_ids: List[int], user_id: int) -> Dict[str, Any]:
        """批量取消订单"""
        try:
            results = {
                'success_count': 0,
                'failed_count': 0,
                'results': []
            }
            
            for order_id in order_ids:
                try:
                    order = self.cancel_order(order_id, user_id, "批量取消")
                    results['success_count'] += 1
                    results['results'].append({
                        'order_id': order_id,
                        'success': True,
                        'message': '取消成功'
                    })
                except Exception as e:
                    results['failed_count'] += 1
                    results['results'].append({
                        'order_id': order_id,
                        'success': False,
                        'message': str(e)
                    })
            
            # 发送批量操作结果通知
            order_notification_service.notify_batch_operation_result(
                user_id, "batch_cancel", results
            )
            
            return results
            
        except Exception as e:
            logger.error(f"批量取消订单失败: {str(e)}")
            raise
    
    # 私有辅助方法
    def _get_current_position(self, symbol: str, user_id: int) -> Decimal:
        """获取当前持仓"""
        # 这里应该查询持仓表，简化处理返回0
        return Decimal('0')
    
    def _get_available_funds(self, user_id: int) -> Decimal:
        """获取可用资金"""
        # 这里应该查询账户资金，简化处理返回大额
        return Decimal('1000000')
    
    def _get_market_price(self, symbol: str) -> Optional[Decimal]:
        """获取市场价格"""
        # 这里应该从市场数据源获取价格，简化处理返回None
        return None
    
    def _check_strategy_risk(self, strategy_id: int, user_id: int) -> float:
        """检查策略风险"""
        # 这里应该分析策略的历史表现，简化处理返回0
        return 0.0
    
    def _calculate_max_allowed_quantity(self, symbol: str, side: OrderSide, user_id: int) -> Optional[Decimal]:
        """计算最大允许数量"""
        # 这里应该根据风控规则计算，简化处理返回None
        return None
    
    def _estimate_margin_requirement(self, symbol: str, quantity: Decimal, price: Optional[Decimal]) -> Optional[Decimal]:
        """估算保证金需求"""
        # 这里应该根据产品类型计算保证金，简化处理返回None
        return None
    



class OrderTemplateService:
    """订单模板服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_template(self, template_data: OrderTemplateCreate, user_id: int) -> OrderTemplate:
        """创建订单模板"""
        try:
            template = OrderTemplate(
                uuid=str(uuid.uuid4()),
                name=template_data.name,
                description=template_data.description,
                category=template_data.category,
                template_config=template_data.template_config,
                default_parameters=template_data.default_parameters,
                tags=template_data.tags,
                author_id=user_id
            )
            
            self.db.add(template)
            self.db.commit()
            self.db.refresh(template)
            
            logger.info(f"创建订单模板成功: {template.id}")
            return template
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建订单模板失败: {str(e)}")
            raise
    
    def get_templates(self, category: Optional[str] = None, 
                     is_official: Optional[bool] = None,
                     user_id: Optional[int] = None) -> List[OrderTemplate]:
        """获取订单模板列表"""
        query = self.db.query(OrderTemplate).filter(
            OrderTemplate.is_active == True
        )
        
        if category:
            query = query.filter(OrderTemplate.category == category)
        
        if is_official is not None:
            query = query.filter(OrderTemplate.is_official == is_official)
        
        if user_id:
            query = query.filter(OrderTemplate.author_id == user_id)
        
        return query.order_by(desc(OrderTemplate.usage_count)).all()
    
    def get_template(self, template_id: int) -> Optional[OrderTemplate]:
        """获取订单模板详情"""
        template = self.db.query(OrderTemplate).filter(
            OrderTemplate.id == template_id,
            OrderTemplate.is_active == True
        ).first()
        
        if not template:
            raise NotFoundError("订单模板不存在")
        
        # 增加使用次数
        template.usage_count += 1
        self.db.commit()
        
        return template