"""
持仓管理服务
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func
from datetime import datetime, timedelta
from decimal import Decimal
import uuid

from ..models.position import Position, PositionHistory, PositionSummary, PositionStatus, PositionType
from ..models.order import Order, OrderFill, OrderSide
from ..models.strategy import Strategy
from ..models.backtest import Backtest
from ..core.exceptions import ValidationError, NotFoundError, PermissionError

logger = logging.getLogger(__name__)


class PositionCalculationService:
    """持仓计算服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_position_from_trades(self, user_id: int, symbol: str, 
                                     strategy_id: Optional[int] = None,
                                     backtest_id: Optional[int] = None) -> Optional[Position]:
        """从交易记录计算持仓"""
        try:
            # 获取相关的成交记录
            query = self.db.query(OrderFill).join(Order).filter(
                Order.user_id == user_id,
                Order.symbol == symbol
            )
            
            if strategy_id:
                query = query.filter(Order.strategy_id == strategy_id)
            if backtest_id:
                query = query.filter(Order.backtest_id == backtest_id)
            
            fills = query.order_by(OrderFill.fill_time).all()
            
            if not fills:
                return None
            
            # 查找或创建持仓记录
            position = self.db.query(Position).filter(
                Position.user_id == user_id,
                Position.symbol == symbol,
                Position.strategy_id == strategy_id,
                Position.backtest_id == backtest_id,
                Position.status == PositionStatus.OPEN
            ).first()
            
            if not position:
                position = Position(
                    uuid=str(uuid.uuid4()),
                    symbol=symbol,
                    user_id=user_id,
                    strategy_id=strategy_id,
                    backtest_id=backtest_id,
                    status=PositionStatus.OPEN
                )
                self.db.add(position)
            
            # 重新计算持仓
            self._recalculate_position_from_fills(position, fills)
            
            self.db.commit()
            self.db.refresh(position)
            
            logger.info(f"计算持仓完成: {symbol}, 数量: {position.quantity}")
            return position
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"计算持仓失败: {str(e)}")
            raise
    
    def _recalculate_position_from_fills(self, position: Position, fills: List[OrderFill]):
        """从成交记录重新计算持仓"""
        # 重置持仓数据
        position.quantity = Decimal('0')
        position.average_cost = Decimal('0')
        position.total_cost = Decimal('0')
        position.realized_pnl = Decimal('0')
        
        for fill in fills:
            order = fill.order
            
            # 确定交易数量和方向
            if order.side == OrderSide.BUY:
                trade_quantity = fill.quantity
            else:  # SELL
                trade_quantity = -fill.quantity
            
            # 添加交易到持仓
            position.add_trade(trade_quantity, fill.price, fill.commission)
        
        # 设置持仓类型
        if position.quantity > 0:
            position.position_type = PositionType.LONG
        elif position.quantity < 0:
            position.position_type = PositionType.SHORT
            position.quantity = abs(position.quantity)  # 持仓数量始终为正
        
        # 如果持仓为0，标记为已关闭
        if position.quantity == 0:
            position.status = PositionStatus.CLOSED
            position.closed_at = datetime.now()
    
    def update_position_market_data(self, position: Position, current_price: Decimal):
        """更新持仓的市场数据"""
        try:
            position.update_market_price(current_price)
            self.db.commit()
            
            logger.debug(f"更新持仓市场数据: {position.symbol}, 价格: {current_price}")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新持仓市场数据失败: {str(e)}")
            raise
    
    def batch_update_market_data(self, price_data: Dict[str, Decimal]):
        """批量更新市场数据"""
        try:
            updated_count = 0
            
            for symbol, price in price_data.items():
                positions = self.db.query(Position).filter(
                    Position.symbol == symbol,
                    Position.status == PositionStatus.OPEN
                ).all()
                
                for position in positions:
                    position.update_market_price(price)
                    updated_count += 1
            
            self.db.commit()
            logger.info(f"批量更新市场数据完成，更新 {updated_count} 个持仓")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"批量更新市场数据失败: {str(e)}")
            raise
    
    def calculate_portfolio_metrics(self, user_id: int) -> Dict[str, Any]:
        """计算投资组合指标"""
        try:
            positions = self.db.query(Position).filter(
                Position.user_id == user_id,
                Position.status == PositionStatus.OPEN
            ).all()
            
            if not positions:
                return {
                    'total_positions': 0,
                    'total_market_value': 0.0,
                    'total_cost': 0.0,
                    'total_pnl': 0.0,
                    'total_realized_pnl': 0.0,
                    'total_unrealized_pnl': 0.0,
                    'return_rate': 0.0,
                    'positions_by_symbol': {}
                }
            
            total_market_value = sum(pos.market_value or Decimal('0') for pos in positions)
            total_cost = sum(pos.total_cost for pos in positions)
            total_pnl = sum(pos.total_pnl for pos in positions)
            total_realized_pnl = sum(pos.realized_pnl for pos in positions)
            total_unrealized_pnl = sum(pos.unrealized_pnl for pos in positions)
            
            return_rate = float(total_pnl / total_cost) if total_cost > 0 else 0.0
            
            # 按标的分组统计
            positions_by_symbol = {}
            for pos in positions:
                symbol = pos.symbol
                if symbol not in positions_by_symbol:
                    positions_by_symbol[symbol] = {
                        'positions': [],
                        'total_quantity': 0.0,
                        'total_market_value': 0.0,
                        'total_pnl': 0.0
                    }
                
                positions_by_symbol[symbol]['positions'].append(pos.to_dict())
                positions_by_symbol[symbol]['total_quantity'] += float(pos.quantity)
                positions_by_symbol[symbol]['total_market_value'] += float(pos.market_value or 0)
                positions_by_symbol[symbol]['total_pnl'] += float(pos.total_pnl)
            
            return {
                'total_positions': len(positions),
                'total_market_value': float(total_market_value),
                'total_cost': float(total_cost),
                'total_pnl': float(total_pnl),
                'total_realized_pnl': float(total_realized_pnl),
                'total_unrealized_pnl': float(total_unrealized_pnl),
                'return_rate': return_rate,
                'positions_by_symbol': positions_by_symbol
            }
            
        except Exception as e:
            logger.error(f"计算投资组合指标失败: {str(e)}")
            raise
    
    def check_position_consistency(self, user_id: int) -> Dict[str, Any]:
        """检查持仓数据一致性"""
        try:
            inconsistencies = []
            
            # 获取所有持仓
            positions = self.db.query(Position).filter(
                Position.user_id == user_id
            ).all()
            
            for position in positions:
                # 重新计算持仓并比较
                fills = self.db.query(OrderFill).join(Order).filter(
                    Order.user_id == user_id,
                    Order.symbol == position.symbol,
                    Order.strategy_id == position.strategy_id,
                    Order.backtest_id == position.backtest_id
                ).order_by(OrderFill.fill_time).all()
                
                # 创建临时持仓对象进行计算
                temp_position = Position(
                    symbol=position.symbol,
                    user_id=user_id,
                    strategy_id=position.strategy_id,
                    backtest_id=position.backtest_id
                )
                
                self._recalculate_position_from_fills(temp_position, fills)
                
                # 比较计算结果
                tolerance = Decimal('0.01')  # 容差
                
                if abs(position.quantity - temp_position.quantity) > tolerance:
                    inconsistencies.append({
                        'position_id': position.id,
                        'symbol': position.symbol,
                        'field': 'quantity',
                        'current_value': float(position.quantity),
                        'calculated_value': float(temp_position.quantity),
                        'difference': float(position.quantity - temp_position.quantity)
                    })
                
                if abs(position.average_cost - temp_position.average_cost) > tolerance:
                    inconsistencies.append({
                        'position_id': position.id,
                        'symbol': position.symbol,
                        'field': 'average_cost',
                        'current_value': float(position.average_cost),
                        'calculated_value': float(temp_position.average_cost),
                        'difference': float(position.average_cost - temp_position.average_cost)
                    })
            
            return {
                'total_positions_checked': len(positions),
                'inconsistencies_found': len(inconsistencies),
                'inconsistencies': inconsistencies,
                'is_consistent': len(inconsistencies) == 0
            }
            
        except Exception as e:
            logger.error(f"检查持仓一致性失败: {str(e)}")
            raise
    
    def repair_position_data(self, user_id: int, position_id: Optional[int] = None) -> Dict[str, Any]:
        """修复持仓数据"""
        try:
            repaired_count = 0
            
            query = self.db.query(Position).filter(Position.user_id == user_id)
            if position_id:
                query = query.filter(Position.id == position_id)
            
            positions = query.all()
            
            for position in positions:
                # 重新计算持仓
                result = self.calculate_position_from_trades(
                    user_id=position.user_id,
                    symbol=position.symbol,
                    strategy_id=position.strategy_id,
                    backtest_id=position.backtest_id
                )
                
                if result:
                    repaired_count += 1
            
            return {
                'repaired_positions': repaired_count,
                'message': f'成功修复 {repaired_count} 个持仓记录'
            }
            
        except Exception as e:
            logger.error(f"修复持仓数据失败: {str(e)}")
            raise


class PositionService:
    """持仓管理服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.calculation_service = PositionCalculationService(db)
    
    def get_user_positions(self, user_id: int, status: Optional[PositionStatus] = None,
                          symbol: Optional[str] = None) -> List[Position]:
        """获取用户持仓列表"""
        query = self.db.query(Position).filter(Position.user_id == user_id)
        
        if status:
            query = query.filter(Position.status == status)
        if symbol:
            query = query.filter(Position.symbol == symbol)
        
        return query.order_by(desc(Position.updated_at)).all()
    
    def get_position(self, position_id: int, user_id: int) -> Position:
        """获取持仓详情"""
        position = self.db.query(Position).filter(
            Position.id == position_id,
            Position.user_id == user_id
        ).first()
        
        if not position:
            raise NotFoundError("持仓不存在或无权限访问")
        
        return position
    
    def get_position_by_symbol(self, user_id: int, symbol: str, 
                              strategy_id: Optional[int] = None,
                              backtest_id: Optional[int] = None) -> Optional[Position]:
        """根据标的获取持仓"""
        query = self.db.query(Position).filter(
            Position.user_id == user_id,
            Position.symbol == symbol,
            Position.status == PositionStatus.OPEN
        )
        
        if strategy_id:
            query = query.filter(Position.strategy_id == strategy_id)
        if backtest_id:
            query = query.filter(Position.backtest_id == backtest_id)
        
        return query.first()
    
    def update_position_from_fill(self, fill: OrderFill):
        """从成交记录更新持仓"""
        try:
            order = fill.order
            
            # 查找或创建持仓
            position = self.get_position_by_symbol(
                user_id=order.user_id,
                symbol=order.symbol,
                strategy_id=order.strategy_id,
                backtest_id=order.backtest_id
            )
            
            if not position:
                position = Position(
                    uuid=str(uuid.uuid4()),
                    symbol=order.symbol,
                    user_id=order.user_id,
                    strategy_id=order.strategy_id,
                    backtest_id=order.backtest_id,
                    source=order.source,
                    source_id=order.source_id,
                    status=PositionStatus.OPEN
                )
                self.db.add(position)
            
            # 确定交易数量和方向
            if order.side == OrderSide.BUY:
                trade_quantity = fill.quantity
            else:  # SELL
                trade_quantity = -fill.quantity
            
            # 更新持仓
            position.add_trade(trade_quantity, fill.price, fill.commission)
            
            self.db.commit()
            self.db.refresh(position)
            
            logger.info(f"从成交更新持仓: {order.symbol}, 成交数量: {fill.quantity}")
            return position
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"从成交更新持仓失败: {str(e)}")
            raise
    
    def set_stop_loss(self, position_id: int, user_id: int, stop_price: Decimal,
                     order_id: Optional[int] = None) -> Position:
        """设置止损"""
        try:
            position = self.get_position(position_id, user_id)
            
            if not position.is_open:
                raise ValidationError("只能为开放状态的持仓设置止损")
            
            position.set_stop_loss(stop_price, order_id)
            
            self.db.commit()
            self.db.refresh(position)
            
            logger.info(f"设置止损: {position.symbol}, 止损价: {stop_price}")
            return position
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"设置止损失败: {str(e)}")
            raise
    
    def set_take_profit(self, position_id: int, user_id: int, profit_price: Decimal,
                       order_id: Optional[int] = None) -> Position:
        """设置止盈"""
        try:
            position = self.get_position(position_id, user_id)
            
            if not position.is_open:
                raise ValidationError("只能为开放状态的持仓设置止盈")
            
            position.set_take_profit(profit_price, order_id)
            
            self.db.commit()
            self.db.refresh(position)
            
            logger.info(f"设置止盈: {position.symbol}, 止盈价: {profit_price}")
            return position
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"设置止盈失败: {str(e)}")
            raise
    
    def close_position(self, position_id: int, user_id: int, close_price: Decimal,
                      reason: str = "") -> Position:
        """平仓"""
        try:
            position = self.get_position(position_id, user_id)
            
            if not position.is_open:
                raise ValidationError("持仓已关闭")
            
            # 计算平仓盈亏
            if position.is_long:
                close_pnl = position.quantity * (close_price - position.average_cost)
            else:
                close_pnl = position.quantity * (position.average_cost - close_price)
            
            # 更新持仓状态
            position.realized_pnl += close_pnl
            position.quantity = Decimal('0')
            position.available_quantity = Decimal('0')
            position.frozen_quantity = Decimal('0')
            position.status = PositionStatus.CLOSED
            position.closed_at = datetime.now()
            position.current_price = close_price
            position.market_value = Decimal('0')
            position.unrealized_pnl = Decimal('0')
            position.total_pnl = position.realized_pnl
            
            if reason:
                position.notes = f"{position.notes or ''}\n平仓原因: {reason}".strip()
            
            self.db.commit()
            self.db.refresh(position)
            
            logger.info(f"平仓完成: {position.symbol}, 平仓价: {close_price}, 盈亏: {close_pnl}")
            return position
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"平仓失败: {str(e)}")
            raise
    
    def get_position_history(self, position_id: int, user_id: int,
                           action: Optional[str] = None) -> List[PositionHistory]:
        """获取持仓历史记录"""
        # 验证持仓权限
        position = self.get_position(position_id, user_id)
        
        query = self.db.query(PositionHistory).filter(
            PositionHistory.position_id == position_id
        )
        
        if action:
            query = query.filter(PositionHistory.action == action)
        
        return query.order_by(desc(PositionHistory.created_at)).all()
    
    def get_portfolio_summary(self, user_id: int) -> Dict[str, Any]:
        """获取投资组合摘要"""
        return self.calculation_service.calculate_portfolio_metrics(user_id)
    
    def update_market_prices(self, price_data: Dict[str, Decimal]):
        """更新市场价格"""
        self.calculation_service.batch_update_market_data(price_data)
    
    def check_stop_triggers(self, user_id: int) -> List[Dict[str, Any]]:
        """检查止损止盈触发"""
        positions = self.get_user_positions(user_id, PositionStatus.OPEN)
        triggers = []
        
        for position in positions:
            if position.check_stop_loss_trigger():
                triggers.append({
                    'position_id': position.id,
                    'symbol': position.symbol,
                    'trigger_type': 'stop_loss',
                    'trigger_price': float(position.stop_loss_price),
                    'current_price': float(position.current_price),
                    'order_id': position.stop_loss_order_id
                })
            
            if position.check_take_profit_trigger():
                triggers.append({
                    'position_id': position.id,
                    'symbol': position.symbol,
                    'trigger_type': 'take_profit',
                    'trigger_price': float(position.take_profit_price),
                    'current_price': float(position.current_price),
                    'order_id': position.take_profit_order_id
                })
        
        return triggers
    
    def get_position_statistics(self, user_id: int) -> Dict[str, Any]:
        """获取持仓统计信息"""
        try:
            # 基础统计
            total_positions = self.db.query(Position).filter(
                Position.user_id == user_id
            ).count()
            
            open_positions = self.db.query(Position).filter(
                Position.user_id == user_id,
                Position.status == PositionStatus.OPEN
            ).count()
            
            closed_positions = self.db.query(Position).filter(
                Position.user_id == user_id,
                Position.status == PositionStatus.CLOSED
            ).count()
            
            # 盈亏统计
            profit_positions = self.db.query(Position).filter(
                Position.user_id == user_id,
                Position.total_pnl > 0
            ).count()
            
            loss_positions = self.db.query(Position).filter(
                Position.user_id == user_id,
                Position.total_pnl < 0
            ).count()
            
            # 投资组合指标
            portfolio_metrics = self.get_portfolio_summary(user_id)
            
            return {
                'total_positions': total_positions,
                'open_positions': open_positions,
                'closed_positions': closed_positions,
                'profit_positions': profit_positions,
                'loss_positions': loss_positions,
                'win_rate': profit_positions / max(total_positions, 1),
                'portfolio_metrics': portfolio_metrics
            }
            
        except Exception as e:
            logger.error(f"获取持仓统计失败: {str(e)}")
            raise