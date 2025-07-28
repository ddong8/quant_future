"""
订单管理服务
"""
import uuid
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
import logging

from ..models import Order, Position, Account, Strategy, User
from ..models.enums import OrderDirection, OrderOffset, OrderStatus, PositionDirection
from ..core.exceptions import (
    NotFoundError,
    ConflictError,
    ValidationError,
    AuthorizationError,
)
from ..core.dependencies import PaginationParams, SortParams
from .tqsdk_adapter import TQSDKAdapter
from .risk_service import RiskService

logger = logging.getLogger(__name__)


class OrderService:
    """订单管理服务类"""
    
    def __init__(self, db: Session, tqsdk_adapter: TQSDKAdapter, risk_service: RiskService):
        self.db = db
        self.tqsdk_adapter = tqsdk_adapter
        self.risk_service = risk_service
    
    def create_order(self, order_data: Dict[str, Any], user_id: int) -> Order:
        """创建订单"""
        try:
            # 验证策略权限
            strategy = self.db.query(Strategy).filter(
                and_(
                    Strategy.id == order_data['strategy_id'],
                    Strategy.user_id == user_id
                )
            ).first()
            
            if not strategy:
                raise NotFoundError("策略不存在或无权限访问")
            
            # 生成订单ID
            order_id = f"ORD_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
            
            # 风险检查
            risk_check_result = self.risk_service.check_order_risk(order_data, user_id)
            if not risk_check_result['passed']:
                raise ValidationError(f"风险检查未通过: {risk_check_result['reason']}")
            
            # 创建订单
            new_order = Order(
                id=order_id,
                strategy_id=order_data['strategy_id'],
                symbol=order_data['symbol'],
                direction=order_data['direction'],
                offset=order_data['offset'],
                volume=order_data['volume'],
                price=order_data['price'],
                status=OrderStatus.PENDING,
                notes=order_data.get('notes', '')
            )
            
            self.db.add(new_order)
            self.db.commit()
            self.db.refresh(new_order)
            
            # 提交到交易系统
            try:
                self._submit_order_to_broker(new_order)
            except Exception as e:
                # 如果提交失败，更新订单状态
                new_order.status = OrderStatus.REJECTED
                new_order.notes = f"提交失败: {str(e)}"
                self.db.commit()
                logger.error(f"订单提交失败: {order_id}, 错误: {e}")
            
            logger.info(f"订单创建成功: {order_id}")
            return new_order
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建订单失败: {e}")
            raise
    
    def modify_order(self, order_id: str, modify_data: Dict[str, Any], user_id: int) -> Order:
        """修改订单"""
        try:
            # 获取订单并验证权限
            order = self._get_order_with_permission(order_id, user_id)
            
            # 检查订单状态是否允许修改
            if order.status not in [OrderStatus.PENDING, OrderStatus.PARTIAL_FILLED]:
                raise ValidationError("订单状态不允许修改")
            
            # 风险检查
            modified_order_data = {
                'strategy_id': order.strategy_id,
                'symbol': order.symbol,
                'direction': order.direction,
                'offset': order.offset,
                'volume': modify_data.get('volume', order.volume),
                'price': modify_data.get('price', order.price),
            }
            
            risk_check_result = self.risk_service.check_order_risk(modified_order_data, user_id)
            if not risk_check_result['passed']:
                raise ValidationError(f"风险检查未通过: {risk_check_result['reason']}")
            
            # 更新订单信息
            old_volume = order.volume
            old_price = order.price
            
            if 'volume' in modify_data:
                order.volume = modify_data['volume']
            if 'price' in modify_data:
                order.price = modify_data['price']
            if 'notes' in modify_data:
                order.notes = modify_data['notes']
            
            order.updated_at = datetime.utcnow()
            
            # 提交修改到交易系统
            try:
                self._modify_order_in_broker(order, old_volume, old_price)
            except Exception as e:
                # 如果修改失败，回滚订单信息
                order.volume = old_volume
                order.price = old_price
                self.db.rollback()
                raise ValidationError(f"订单修改失败: {str(e)}")
            
            self.db.commit()
            self.db.refresh(order)
            
            logger.info(f"订单修改成功: {order_id}")
            return order
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"修改订单失败: {e}")
            raise
    
    def cancel_order(self, order_id: str, user_id: int) -> Order:
        """撤销订单"""
        try:
            # 获取订单并验证权限
            order = self._get_order_with_permission(order_id, user_id)
            
            # 检查订单状态是否允许撤销
            if order.status not in [OrderStatus.PENDING, OrderStatus.PARTIAL_FILLED]:
                raise ValidationError("订单状态不允许撤销")
            
            # 提交撤销到交易系统
            try:
                self._cancel_order_in_broker(order)
            except Exception as e:
                raise ValidationError(f"订单撤销失败: {str(e)}")
            
            # 更新订单状态
            order.status = OrderStatus.CANCELLED
            order.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(order)
            
            logger.info(f"订单撤销成功: {order_id}")
            return order
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"撤销订单失败: {e}")
            raise
    
    def get_order_by_id(self, order_id: str, user_id: int) -> Order:
        """根据ID获取订单"""
        return self._get_order_with_permission(order_id, user_id)
    
    def get_orders_list(self,
                       user_id: int,
                       strategy_id: Optional[int] = None,
                       symbol: Optional[str] = None,
                       status: Optional[OrderStatus] = None,
                       direction: Optional[OrderDirection] = None,
                       start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None,
                       pagination: Optional[PaginationParams] = None,
                       sort_params: Optional[SortParams] = None) -> Tuple[List[Order], int]:
        """获取订单列表"""
        # 构建查询
        query = self.db.query(Order).join(Strategy).filter(Strategy.user_id == user_id)
        
        # 应用过滤条件
        if strategy_id:
            query = query.filter(Order.strategy_id == strategy_id)
        
        if symbol:
            query = query.filter(Order.symbol == symbol)
        
        if status:
            query = query.filter(Order.status == status)
        
        if direction:
            query = query.filter(Order.direction == direction)
        
        if start_date:
            query = query.filter(Order.created_at >= start_date)
        
        if end_date:
            query = query.filter(Order.created_at <= end_date)
        
        # 获取总数
        total = query.count()
        
        # 应用排序
        if sort_params:
            if hasattr(Order, sort_params.sort_by):
                sort_column = getattr(Order, sort_params.sort_by)
                if sort_params.sort_order == "asc":
                    query = query.order_by(sort_column)
                else:
                    query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(desc(Order.created_at))
        
        # 应用分页
        if pagination:
            query = query.offset(pagination.offset).limit(pagination.page_size)
        
        orders = query.all()
        
        return orders, total
    
    def get_pending_orders(self, user_id: int, strategy_id: Optional[int] = None) -> List[Order]:
        """获取待成交订单"""
        query = self.db.query(Order).join(Strategy).filter(
            and_(
                Strategy.user_id == user_id,
                Order.status.in_([OrderStatus.PENDING, OrderStatus.PARTIAL_FILLED])
            )
        )
        
        if strategy_id:
            query = query.filter(Order.strategy_id == strategy_id)
        
        return query.order_by(Order.created_at).all()
    
    def batch_cancel_orders(self, order_ids: List[str], user_id: int) -> Dict[str, Any]:
        """批量撤销订单"""
        try:
            if len(order_ids) > 50:
                raise ValidationError("批量操作最多支持50个订单")
            
            results = []
            success_count = 0
            failed_count = 0
            
            for order_id in order_ids:
                try:
                    order = self.cancel_order(order_id, user_id)
                    results.append({
                        'order_id': order_id,
                        'success': True,
                        'message': '撤销成功'
                    })
                    success_count += 1
                except Exception as e:
                    results.append({
                        'order_id': order_id,
                        'success': False,
                        'message': str(e)
                    })
                    failed_count += 1
            
            logger.info(f"批量撤销订单完成: 成功 {success_count}, 失败 {failed_count}")
            
            return {
                'results': results,
                'success_count': success_count,
                'failed_count': failed_count
            }
            
        except Exception as e:
            logger.error(f"批量撤销订单失败: {e}")
            raise
    
    def update_order_status(self, order_id: str, status: OrderStatus, 
                           filled_volume: Optional[int] = None,
                           avg_fill_price: Optional[float] = None,
                           commission: Optional[float] = None) -> Order:
        """更新订单状态（由交易系统回调）"""
        try:
            order = self.db.query(Order).filter(Order.id == order_id).first()
            if not order:
                raise NotFoundError("订单不存在")
            
            old_status = order.status
            order.status = status
            order.updated_at = datetime.utcnow()
            
            if filled_volume is not None:
                order.filled_volume = filled_volume
            
            if avg_fill_price is not None:
                order.avg_fill_price = avg_fill_price
            
            if commission is not None:
                order.commission = commission
            
            if status == OrderStatus.FILLED:
                order.filled_at = datetime.utcnow()
                # 更新持仓
                self._update_position_from_order(order)
            
            self.db.commit()
            self.db.refresh(order)
            
            logger.info(f"订单状态更新: {order_id}, {old_status} -> {status}")
            return order
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新订单状态失败: {e}")
            raise
    
    def get_order_statistics(self, user_id: int, 
                           start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """获取订单统计信息"""
        query = self.db.query(Order).join(Strategy).filter(Strategy.user_id == user_id)
        
        if start_date:
            query = query.filter(Order.created_at >= start_date)
        
        if end_date:
            query = query.filter(Order.created_at <= end_date)
        
        # 基础统计
        total_orders = query.count()
        filled_orders = query.filter(Order.status == OrderStatus.FILLED).count()
        cancelled_orders = query.filter(Order.status == OrderStatus.CANCELLED).count()
        pending_orders = query.filter(Order.status.in_([OrderStatus.PENDING, OrderStatus.PARTIAL_FILLED])).count()
        
        # 按方向统计
        buy_orders = query.filter(Order.direction == OrderDirection.BUY).count()
        sell_orders = query.filter(Order.direction == OrderDirection.SELL).count()
        
        # 按品种统计
        symbol_stats = query.with_entities(
            Order.symbol,
            func.count(Order.id).label('count')
        ).group_by(Order.symbol).all()
        
        # 成交率
        fill_rate = filled_orders / total_orders if total_orders > 0 else 0
        
        # 平均成交时间（已成交订单）
        filled_orders_query = query.filter(
            and_(
                Order.status == OrderStatus.FILLED,
                Order.filled_at.isnot(None)
            )
        )
        
        avg_fill_time = None
        if filled_orders_query.count() > 0:
            fill_times = []
            for order in filled_orders_query.all():
                if order.filled_at and order.created_at:
                    fill_time = (order.filled_at - order.created_at).total_seconds()
                    fill_times.append(fill_time)
            
            if fill_times:
                avg_fill_time = sum(fill_times) / len(fill_times)
        
        return {
            'total_orders': total_orders,
            'filled_orders': filled_orders,
            'cancelled_orders': cancelled_orders,
            'pending_orders': pending_orders,
            'buy_orders': buy_orders,
            'sell_orders': sell_orders,
            'fill_rate': fill_rate,
            'avg_fill_time_seconds': avg_fill_time,
            'symbol_distribution': [
                {'symbol': symbol, 'count': count} 
                for symbol, count in symbol_stats
            ]
        }
    
    def _get_order_with_permission(self, order_id: str, user_id: int) -> Order:
        """获取订单并验证权限"""
        order = self.db.query(Order).join(Strategy).filter(
            and_(
                Order.id == order_id,
                Strategy.user_id == user_id
            )
        ).first()
        
        if not order:
            raise NotFoundError("订单不存在或无权限访问")
        
        return order
    
    def _submit_order_to_broker(self, order: Order):
        """提交订单到券商系统"""
        try:
            # 使用tqsdk适配器提交订单
            broker_order_id = self.tqsdk_adapter.submit_order(
                symbol=order.symbol,
                direction=order.direction,
                offset=order.offset,
                volume=order.volume,
                price=order.price
            )
            
            # 更新订单的券商订单ID
            order.notes = f"券商订单ID: {broker_order_id}"
            
        except Exception as e:
            logger.error(f"提交订单到券商失败: {order.id}, 错误: {e}")
            raise
    
    def _modify_order_in_broker(self, order: Order, old_volume: int, old_price: float):
        """在券商系统中修改订单"""
        try:
            # 使用tqsdk适配器修改订单
            self.tqsdk_adapter.modify_order(
                order_id=order.id,
                volume=order.volume,
                price=order.price
            )
            
        except Exception as e:
            logger.error(f"在券商系统修改订单失败: {order.id}, 错误: {e}")
            raise
    
    def _cancel_order_in_broker(self, order: Order):
        """在券商系统中撤销订单"""
        try:
            # 使用tqsdk适配器撤销订单
            self.tqsdk_adapter.cancel_order(order.id)
            
        except Exception as e:
            logger.error(f"在券商系统撤销订单失败: {order.id}, 错误: {e}")
            raise
    
    def _update_position_from_order(self, order: Order):
        """根据订单更新持仓"""
        try:
            # 查找现有持仓
            position = self.db.query(Position).filter(
                and_(
                    Position.strategy_id == order.strategy_id,
                    Position.symbol == order.symbol
                )
            ).first()
            
            if order.offset == OrderOffset.OPEN:
                # 开仓
                if position:
                    # 更新现有持仓
                    if order.direction == OrderDirection.BUY:
                        if position.direction == PositionDirection.LONG:
                            # 增加多头持仓
                            total_cost = position.volume * position.avg_price + order.filled_volume * order.avg_fill_price
                            total_volume = position.volume + order.filled_volume
                            position.avg_price = total_cost / total_volume
                            position.volume = total_volume
                        else:
                            # 减少空头持仓或转为多头
                            if order.filled_volume >= position.volume:
                                # 平空后开多
                                remaining_volume = order.filled_volume - position.volume
                                position.direction = PositionDirection.LONG
                                position.volume = remaining_volume
                                position.avg_price = order.avg_fill_price
                            else:
                                # 部分平空
                                position.volume -= order.filled_volume
                    else:  # SELL
                        if position.direction == PositionDirection.SHORT:
                            # 增加空头持仓
                            total_cost = position.volume * position.avg_price + order.filled_volume * order.avg_fill_price
                            total_volume = position.volume + order.filled_volume
                            position.avg_price = total_cost / total_volume
                            position.volume = total_volume
                        else:
                            # 减少多头持仓或转为空头
                            if order.filled_volume >= position.volume:
                                # 平多后开空
                                remaining_volume = order.filled_volume - position.volume
                                position.direction = PositionDirection.SHORT
                                position.volume = remaining_volume
                                position.avg_price = order.avg_fill_price
                            else:
                                # 部分平多
                                position.volume -= order.filled_volume
                else:
                    # 创建新持仓
                    direction = PositionDirection.LONG if order.direction == OrderDirection.BUY else PositionDirection.SHORT
                    position = Position(
                        strategy_id=order.strategy_id,
                        symbol=order.symbol,
                        direction=direction,
                        volume=order.filled_volume,
                        avg_price=order.avg_fill_price,
                        margin=order.filled_volume * order.avg_fill_price * 0.1,  # 假设保证金率10%
                        margin_rate=0.1
                    )
                    self.db.add(position)
            
            else:
                # 平仓
                if position:
                    if order.direction == OrderDirection.BUY and position.direction == PositionDirection.SHORT:
                        # 买入平空
                        position.volume = max(0, position.volume - order.filled_volume)
                    elif order.direction == OrderDirection.SELL and position.direction == PositionDirection.LONG:
                        # 卖出平多
                        position.volume = max(0, position.volume - order.filled_volume)
                    
                    # 如果持仓为0，删除持仓记录
                    if position.volume == 0:
                        self.db.delete(position)
            
            position.updated_at = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"更新持仓失败: {e}")
            raise