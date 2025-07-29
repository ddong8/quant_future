"""
持仓管理服务
"""
from typing import List, Optional, Dict, Any, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
import logging

from ..models import Position, Order, Account, User
from ..models.enums import PositionSide, OrderSide, OrderStatus
from ..core.exceptions import NotFoundError, ValidationError
from ..core.dependencies import PaginationParams, SortParams

logger = logging.getLogger(__name__)


class PositionService:
    """持仓管理服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_position(self, user_id: int, symbol: str) -> Optional[Position]:
        """获取指定品种的持仓"""
        return self.db.query(Position).filter(
            and_(
                Position.user_id == user_id,
                Position.symbol == symbol
            )
        ).first()
    
    def get_positions_list(self,
                          user_id: Optional[int] = None,
                          symbol: Optional[str] = None,
                          side: Optional[PositionSide] = None,
                          only_active: bool = True,
                          pagination: Optional[PaginationParams] = None,
                          sort_params: Optional[SortParams] = None) -> Tuple[List[Position], int]:
        """获取持仓列表"""
        query = self.db.query(Position)
        
        # 用户过滤
        if user_id:
            query = query.filter(Position.user_id == user_id)
        
        # 品种过滤
        if symbol:
            query = query.filter(Position.symbol == symbol)
        
        # 方向过滤
        if side:
            query = query.filter(Position.side == side)
        
        # 只显示有持仓的
        if only_active:
            query = query.filter(Position.quantity != 0)
        
        # 获取总数
        total = query.count()
        
        # 应用排序
        if sort_params:
            if hasattr(Position, sort_params.sort_by):
                sort_column = getattr(Position, sort_params.sort_by)
                if sort_params.sort_order == "asc":
                    query = query.order_by(sort_column)
                else:
                    query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(desc(Position.updated_at))
        
        # 应用分页
        if pagination:
            query = query.offset(pagination.offset).limit(pagination.page_size)
        
        positions = query.all()
        
        return positions, total
    
    def update_position_from_order(self, order: Order):
        """根据订单更新持仓"""
        try:
            # 获取或创建持仓记录
            position = self.get_position(order.user_id, order.symbol)
            
            if not position:
                position = Position(
                    user_id=order.user_id,
                    symbol=order.symbol,
                    side=PositionSide.LONG if order.side == OrderSide.BUY else PositionSide.SHORT,
                    quantity=Decimal('0'),
                    average_price=Decimal('0'),
                    market_value=Decimal('0'),
                    unrealized_pnl=Decimal('0'),
                    realized_pnl=Decimal('0'),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                self.db.add(position)
            
            # 计算持仓变化
            fill_quantity = order.filled_quantity or Decimal('0')
            fill_price = order.average_price or Decimal('0')
            
            if order.side == OrderSide.BUY:
                self._process_buy_order(position, fill_quantity, fill_price)
            else:
                self._process_sell_order(position, fill_quantity, fill_price)
            
            # 更新时间戳
            position.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"持仓更新成功: {order.symbol}, 数量: {position.quantity}")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新持仓失败: {e}")
            raise
    
    def _process_buy_order(self, position: Position, quantity: Decimal, price: Decimal):
        """处理买入订单"""
        current_quantity = position.quantity
        current_avg_price = position.average_price
        
        if current_quantity >= 0:
            # 增加多头持仓或建立多头持仓
            if current_quantity == 0:
                # 新建持仓
                position.quantity = quantity
                position.average_price = price
                position.side = PositionSide.LONG
            else:
                # 增加持仓
                total_cost = current_quantity * current_avg_price + quantity * price
                total_quantity = current_quantity + quantity
                position.quantity = total_quantity
                position.average_price = total_cost / total_quantity
        else:
            # 当前是空头持仓，买入是平仓或反向开仓
            abs_current_quantity = abs(current_quantity)
            
            if quantity <= abs_current_quantity:
                # 部分或全部平空
                realized_pnl = (current_avg_price - price) * quantity
                position.realized_pnl += realized_pnl
                position.quantity = current_quantity + quantity
                
                if position.quantity == 0:
                    position.average_price = Decimal('0')
                    position.side = PositionSide.LONG  # 重置为多头方向
            else:
                # 平空后反向开多
                close_quantity = abs_current_quantity
                open_quantity = quantity - close_quantity
                
                # 平仓盈亏
                realized_pnl = (current_avg_price - price) * close_quantity
                position.realized_pnl += realized_pnl
                
                # 新开多头
                position.quantity = open_quantity
                position.average_price = price
                position.side = PositionSide.LONG
    
    def _process_sell_order(self, position: Position, quantity: Decimal, price: Decimal):
        """处理卖出订单"""
        current_quantity = position.quantity
        current_avg_price = position.average_price
        
        if current_quantity <= 0:
            # 增加空头持仓或建立空头持仓
            abs_current_quantity = abs(current_quantity)
            
            if current_quantity == 0:
                # 新建空头持仓
                position.quantity = -quantity
                position.average_price = price
                position.side = PositionSide.SHORT
            else:
                # 增加空头持仓
                total_cost = abs_current_quantity * current_avg_price + quantity * price
                total_quantity = abs_current_quantity + quantity
                position.quantity = -total_quantity
                position.average_price = total_cost / total_quantity
        else:
            # 当前是多头持仓，卖出是平仓或反向开仓
            if quantity <= current_quantity:
                # 部分或全部平多
                realized_pnl = (price - current_avg_price) * quantity
                position.realized_pnl += realized_pnl
                position.quantity = current_quantity - quantity
                
                if position.quantity == 0:
                    position.average_price = Decimal('0')
                    position.side = PositionSide.SHORT  # 重置为空头方向
            else:
                # 平多后反向开空
                close_quantity = current_quantity
                open_quantity = quantity - close_quantity
                
                # 平仓盈亏
                realized_pnl = (price - current_avg_price) * close_quantity
                position.realized_pnl += realized_pnl
                
                # 新开空头
                position.quantity = -open_quantity
                position.average_price = price
                position.side = PositionSide.SHORT
    
    def update_market_value(self, user_id: int, symbol: str, current_price: float):
        """更新持仓市值和未实现盈亏"""
        try:
            position = self.get_position(user_id, symbol)
            
            if not position or position.quantity == 0:
                return
            
            # 计算市值
            abs_quantity = abs(position.quantity)
            position.market_value = abs_quantity * Decimal(str(current_price))
            
            # 计算未实现盈亏
            if position.quantity > 0:
                # 多头持仓
                position.unrealized_pnl = (Decimal(str(current_price)) - position.average_price) * position.quantity
            else:
                # 空头持仓
                position.unrealized_pnl = (position.average_price - Decimal(str(current_price))) * abs(position.quantity)
            
            position.updated_at = datetime.utcnow()
            
            self.db.commit()
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新持仓市值失败: {e}")
    
    def batch_update_market_values(self, market_data: Dict[str, float]):
        """批量更新持仓市值"""
        try:
            for symbol, current_price in market_data.items():
                positions = self.db.query(Position).filter(
                    and_(
                        Position.symbol == symbol,
                        Position.quantity != 0
                    )
                ).all()
                
                for position in positions:
                    # 计算市值
                    abs_quantity = abs(position.quantity)
                    position.market_value = abs_quantity * Decimal(str(current_price))
                    
                    # 计算未实现盈亏
                    if position.quantity > 0:
                        # 多头持仓
                        position.unrealized_pnl = (Decimal(str(current_price)) - position.average_price) * position.quantity
                    else:
                        # 空头持仓
                        position.unrealized_pnl = (position.average_price - Decimal(str(current_price))) * abs(position.quantity)
                    
                    position.updated_at = datetime.utcnow()
            
            self.db.commit()
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"批量更新持仓市值失败: {e}")
    
    def close_position(self, user_id: int, symbol: str, quantity: Optional[float] = None) -> Dict[str, Any]:
        """平仓"""
        try:
            position = self.get_position(user_id, symbol)
            
            if not position or position.quantity == 0:
                raise NotFoundError("没有持仓可平")
            
            # 确定平仓数量
            close_quantity = quantity or abs(float(position.quantity))
            max_close_quantity = abs(float(position.quantity))
            
            if close_quantity > max_close_quantity:
                raise ValidationError(f"平仓数量不能超过持仓数量 {max_close_quantity}")
            
            # 确定平仓方向
            if position.quantity > 0:
                # 多头持仓，卖出平仓
                close_side = OrderSide.SELL
            else:
                # 空头持仓，买入平仓
                close_side = OrderSide.BUY
            
            return {
                'symbol': symbol,
                'side': close_side.value,
                'quantity': close_quantity,
                'order_type': 'MARKET',
                'position_quantity': float(position.quantity),
                'average_price': float(position.average_price)
            }
            
        except Exception as e:
            logger.error(f"平仓失败: {e}")
            raise
    
    def get_position_summary(self, user_id: int) -> Dict[str, Any]:
        """获取持仓汇总"""
        try:
            positions = self.db.query(Position).filter(
                and_(
                    Position.user_id == user_id,
                    Position.quantity != 0
                )
            ).all()
            
            total_market_value = Decimal('0')
            total_unrealized_pnl = Decimal('0')
            total_realized_pnl = Decimal('0')
            long_positions = 0
            short_positions = 0
            
            position_details = []
            
            for position in positions:
                total_market_value += position.market_value or Decimal('0')
                total_unrealized_pnl += position.unrealized_pnl or Decimal('0')
                total_realized_pnl += position.realized_pnl or Decimal('0')
                
                if position.quantity > 0:
                    long_positions += 1
                else:
                    short_positions += 1
                
                position_details.append({
                    'symbol': position.symbol,
                    'side': position.side.value,
                    'quantity': float(position.quantity),
                    'average_price': float(position.average_price),
                    'market_value': float(position.market_value or 0),
                    'unrealized_pnl': float(position.unrealized_pnl or 0),
                    'realized_pnl': float(position.realized_pnl or 0),
                    'pnl_ratio': float((position.unrealized_pnl or Decimal('0')) / (position.market_value or Decimal('1')) * 100)
                })
            
            return {
                'total_positions': len(positions),
                'long_positions': long_positions,
                'short_positions': short_positions,
                'total_market_value': float(total_market_value),
                'total_unrealized_pnl': float(total_unrealized_pnl),
                'total_realized_pnl': float(total_realized_pnl),
                'total_pnl_ratio': float(total_unrealized_pnl / total_market_value * 100) if total_market_value > 0 else 0,
                'positions': position_details
            }
            
        except Exception as e:
            logger.error(f"获取持仓汇总失败: {e}")
            return {}
    
    def get_available_quantity(self, user_id: int, symbol: str) -> float:
        """获取可用持仓数量"""
        position = self.get_position(user_id, symbol)
        
        if not position:
            return 0.0
        
        total_quantity = abs(float(position.quantity))
        frozen_quantity = float(position.frozen_quantity or 0)
        
        return max(0.0, total_quantity - frozen_quantity)