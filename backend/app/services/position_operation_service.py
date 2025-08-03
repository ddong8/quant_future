"""
持仓操作服务
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from decimal import Decimal

from ..models.position import Position, PositionStatus, PositionHistory
from ..models.order import Order, OrderType, OrderSide, OrderStatus
from ..models.user import User
from ..services.order_service import OrderService
from ..services.risk_service import RiskService
from ..core.websocket import websocket_manager
from ..utils.position_calculator import PositionCalculator

logger = logging.getLogger(__name__)


class PositionOperationService:
    """持仓操作服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.order_service = OrderService(db)
        self.risk_service = RiskService(db)
        self.calculator = PositionCalculator()
    
    async def close_position(self, position_id: int, user_id: int, close_type: str = 'market', 
                      close_price: Optional[Decimal] = None, close_quantity: Optional[Decimal] = None) -> Dict[str, Any]:
        """平仓操作"""
        try:
            # 获取持仓
            position = self.db.query(Position).filter(
                and_(
                    Position.id == position_id,
                    Position.user_id == user_id,
                    Position.status == PositionStatus.OPEN
                )
            ).first()
            
            if not position:
                return {'success': False, 'error': '持仓不存在或已关闭'}
            
            # 确定平仓数量
            if close_quantity is None:
                close_quantity = position.available_quantity
            else:
                if close_quantity > position.available_quantity:
                    return {'success': False, 'error': '平仓数量超过可用数量'}
            
            # 风险检查
            risk_check = self._check_close_position_risk(position, close_quantity)
            if not risk_check['allowed']:
                return {'success': False, 'error': f'风险检查失败: {risk_check["reason"]}'}
            
            # 创建平仓订单
            close_order_data = self._create_close_order_data(position, close_type, close_price, close_quantity)
            
            # 提交订单
            order_result = self.order_service.create_order(close_order_data, user_id)
            
            if not order_result.get('success'):
                return {'success': False, 'error': f'创建平仓订单失败: {order_result.get("error")}'}
            
            order = order_result['order']
            
            # 更新持仓状态
            if close_quantity == position.quantity:
                # 全部平仓
                position.status = PositionStatus.CLOSING
            else:
                # 部分平仓，冻结相应数量
                position.frozen_quantity += close_quantity
                position.available_quantity -= close_quantity
            
            # 记录平仓操作
            self._record_position_operation(position, 'CLOSE', {
                'close_type': close_type,
                'close_quantity': float(close_quantity),
                'close_price': float(close_price) if close_price else None,
                'order_id': order.id
            })
            
            self.db.commit()
            
            # 发送WebSocket通知
            await self._notify_position_operation(position, 'CLOSE', {
                'order_id': order.id,
                'close_quantity': float(close_quantity)
            })
            
            logger.info(f"用户 {user_id} 平仓 {position.symbol}，数量: {close_quantity}")
            
            return {
                'success': True,
                'message': '平仓订单已提交',
                'order_id': order.id,
                'close_quantity': float(close_quantity),
                'estimated_pnl': self._calculate_estimated_close_pnl(position, close_price, close_quantity)
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"平仓操作失败: {e}")
            return {'success': False, 'error': str(e)}
    
    async def set_stop_loss(self, position_id: int, user_id: int, stop_price: Decimal, 
                     trigger_type: str = 'last_price') -> Dict[str, Any]:
        """设置止损"""
        try:
            position = self.db.query(Position).filter(
                and_(
                    Position.id == position_id,
                    Position.user_id == user_id,
                    Position.status == PositionStatus.OPEN
                )
            ).first()
            
            if not position:
                return {'success': False, 'error': '持仓不存在或已关闭'}
            
            # 验证止损价格
            validation_result = self._validate_stop_loss_price(position, stop_price)
            if not validation_result['valid']:
                return {'success': False, 'error': validation_result['error']}
            
            # 如果已有止损订单，先取消
            if position.stop_loss_order_id:
                cancel_result = self.order_service.cancel_order(position.stop_loss_order_id, user_id)
                if not cancel_result.get('success'):
                    logger.warning(f"取消原止损订单失败: {cancel_result.get('error')}")
            
            # 创建止损订单
            stop_order_data = {
                'symbol': position.symbol,
                'order_type': OrderType.STOP_LOSS,
                'side': OrderSide.SELL if position.position_type.value == 'LONG' else OrderSide.BUY,
                'quantity': position.available_quantity,
                'stop_price': stop_price,
                'trigger_type': trigger_type,
                'time_in_force': 'GTC',  # Good Till Cancelled
                'strategy_id': position.strategy_id,
                'source': 'stop_loss',
                'parent_position_id': position.id
            }
            
            order_result = self.order_service.create_order(stop_order_data, user_id)
            
            if not order_result.get('success'):
                return {'success': False, 'error': f'创建止损订单失败: {order_result.get("error")}'}
            
            order = order_result['order']
            
            # 更新持仓止损信息
            position.stop_loss_price = stop_price
            position.stop_loss_order_id = order.id
            
            # 记录操作
            self._record_position_operation(position, 'SET_STOP_LOSS', {
                'stop_price': float(stop_price),
                'trigger_type': trigger_type,
                'order_id': order.id
            })
            
            self.db.commit()
            
            # 发送通知
            await self._notify_position_operation(position, 'SET_STOP_LOSS', {
                'stop_price': float(stop_price),
                'order_id': order.id
            })
            
            logger.info(f"用户 {user_id} 为持仓 {position.symbol} 设置止损价格: {stop_price}")
            
            return {
                'success': True,
                'message': '止损设置成功',
                'stop_price': float(stop_price),
                'order_id': order.id,
                'estimated_loss': self._calculate_estimated_stop_loss(position, stop_price)
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"设置止损失败: {e}")
            return {'success': False, 'error': str(e)}
    
    async def set_take_profit(self, position_id: int, user_id: int, profit_price: Decimal,
                       trigger_type: str = 'last_price') -> Dict[str, Any]:
        """设置止盈"""
        try:
            position = self.db.query(Position).filter(
                and_(
                    Position.id == position_id,
                    Position.user_id == user_id,
                    Position.status == PositionStatus.OPEN
                )
            ).first()
            
            if not position:
                return {'success': False, 'error': '持仓不存在或已关闭'}
            
            # 验证止盈价格
            validation_result = self._validate_take_profit_price(position, profit_price)
            if not validation_result['valid']:
                return {'success': False, 'error': validation_result['error']}
            
            # 如果已有止盈订单，先取消
            if position.take_profit_order_id:
                cancel_result = self.order_service.cancel_order(position.take_profit_order_id, user_id)
                if not cancel_result.get('success'):
                    logger.warning(f"取消原止盈订单失败: {cancel_result.get('error')}")
            
            # 创建止盈订单
            profit_order_data = {
                'symbol': position.symbol,
                'order_type': OrderType.TAKE_PROFIT,
                'side': OrderSide.SELL if position.position_type.value == 'LONG' else OrderSide.BUY,
                'quantity': position.available_quantity,
                'stop_price': profit_price,
                'trigger_type': trigger_type,
                'time_in_force': 'GTC',
                'strategy_id': position.strategy_id,
                'source': 'take_profit',
                'parent_position_id': position.id
            }
            
            order_result = self.order_service.create_order(profit_order_data, user_id)
            
            if not order_result.get('success'):
                return {'success': False, 'error': f'创建止盈订单失败: {order_result.get("error")}'}
            
            order = order_result['order']
            
            # 更新持仓止盈信息
            position.take_profit_price = profit_price
            position.take_profit_order_id = order.id
            
            # 记录操作
            self._record_position_operation(position, 'SET_TAKE_PROFIT', {
                'profit_price': float(profit_price),
                'trigger_type': trigger_type,
                'order_id': order.id
            })
            
            self.db.commit()
            
            # 发送通知
            await self._notify_position_operation(position, 'SET_TAKE_PROFIT', {
                'profit_price': float(profit_price),
                'order_id': order.id
            })
            
            logger.info(f"用户 {user_id} 为持仓 {position.symbol} 设置止盈价格: {profit_price}")
            
            return {
                'success': True,
                'message': '止盈设置成功',
                'profit_price': float(profit_price),
                'order_id': order.id,
                'estimated_profit': self._calculate_estimated_take_profit(position, profit_price)
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"设置止盈失败: {e}")
            return {'success': False, 'error': str(e)}
    
    async def cancel_stop_loss(self, position_id: int, user_id: int) -> Dict[str, Any]:
        """取消止损"""
        try:
            position = self.db.query(Position).filter(
                and_(
                    Position.id == position_id,
                    Position.user_id == user_id,
                    Position.status == PositionStatus.OPEN
                )
            ).first()
            
            if not position:
                return {'success': False, 'error': '持仓不存在或已关闭'}
            
            if not position.stop_loss_order_id:
                return {'success': False, 'error': '没有设置止损'}
            
            # 取消止损订单
            cancel_result = self.order_service.cancel_order(position.stop_loss_order_id, user_id)
            
            if not cancel_result.get('success'):
                return {'success': False, 'error': f'取消止损订单失败: {cancel_result.get("error")}'}
            
            # 清除持仓止损信息
            position.stop_loss_price = None
            position.stop_loss_order_id = None
            
            # 记录操作
            self._record_position_operation(position, 'CANCEL_STOP_LOSS', {})
            
            self.db.commit()
            
            # 发送通知
            await self._notify_position_operation(position, 'CANCEL_STOP_LOSS', {})
            
            logger.info(f"用户 {user_id} 取消持仓 {position.symbol} 的止损")
            
            return {'success': True, 'message': '止损已取消'}
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"取消止损失败: {e}")
            return {'success': False, 'error': str(e)}
    
    async def cancel_take_profit(self, position_id: int, user_id: int) -> Dict[str, Any]:
        """取消止盈"""
        try:
            position = self.db.query(Position).filter(
                and_(
                    Position.id == position_id,
                    Position.user_id == user_id,
                    Position.status == PositionStatus.OPEN
                )
            ).first()
            
            if not position:
                return {'success': False, 'error': '持仓不存在或已关闭'}
            
            if not position.take_profit_order_id:
                return {'success': False, 'error': '没有设置止盈'}
            
            # 取消止盈订单
            cancel_result = self.order_service.cancel_order(position.take_profit_order_id, user_id)
            
            if not cancel_result.get('success'):
                return {'success': False, 'error': f'取消止盈订单失败: {cancel_result.get("error")}'}
            
            # 清除持仓止盈信息
            position.take_profit_price = None
            position.take_profit_order_id = None
            
            # 记录操作
            self._record_position_operation(position, 'CANCEL_TAKE_PROFIT', {})
            
            self.db.commit()
            
            # 发送通知
            await self._notify_position_operation(position, 'CANCEL_TAKE_PROFIT', {})
            
            logger.info(f"用户 {user_id} 取消持仓 {position.symbol} 的止盈")
            
            return {'success': True, 'message': '止盈已取消'}
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"取消止盈失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def check_position_concentration_risk(self, user_id: int) -> Dict[str, Any]:
        """检查持仓集中度风险"""
        try:
            # 获取用户所有持仓
            positions = self.db.query(Position).filter(
                and_(
                    Position.user_id == user_id,
                    Position.status == PositionStatus.OPEN
                )
            ).all()
            
            if not positions:
                return {'risk_level': 'LOW', 'warnings': [], 'recommendations': []}
            
            # 计算总市值
            total_market_value = sum(float(pos.market_value or 0) for pos in positions)
            
            if total_market_value == 0:
                return {'risk_level': 'LOW', 'warnings': [], 'recommendations': []}
            
            # 分析集中度风险
            concentration_analysis = self._analyze_concentration_risk(positions, total_market_value)
            
            # 分析行业集中度
            sector_analysis = self._analyze_sector_concentration(positions, total_market_value)
            
            # 综合风险评估
            overall_risk = self._assess_overall_concentration_risk(concentration_analysis, sector_analysis)
            
            return {
                'user_id': user_id,
                'total_market_value': total_market_value,
                'position_count': len(positions),
                'concentration_analysis': concentration_analysis,
                'sector_analysis': sector_analysis,
                'overall_risk': overall_risk,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"检查持仓集中度风险失败: {e}")
            return {'error': str(e)}
    
    def get_position_risk_alerts(self, user_id: int) -> List[Dict[str, Any]]:
        """获取持仓风险预警"""
        try:
            positions = self.db.query(Position).filter(
                and_(
                    Position.user_id == user_id,
                    Position.status == PositionStatus.OPEN
                )
            ).all()
            
            alerts = []
            
            for position in positions:
                # 检查各种风险
                position_alerts = self._check_position_risks(position)
                alerts.extend(position_alerts)
            
            # 检查组合级别风险
            portfolio_alerts = self._check_portfolio_risks(positions)
            alerts.extend(portfolio_alerts)
            
            # 按严重程度排序
            alerts.sort(key=lambda x: {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}.get(x['severity'], 0), reverse=True)
            
            return alerts
            
        except Exception as e:
            logger.error(f"获取持仓风险预警失败: {e}")
            return []
    
    def export_position_data(self, user_id: int, export_format: str = 'csv', 
                           start_date: Optional[datetime] = None, 
                           end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """导出持仓数据"""
        try:
            # 构建查询条件
            query = self.db.query(Position).filter(Position.user_id == user_id)
            
            if start_date:
                query = query.filter(Position.created_at >= start_date)
            if end_date:
                query = query.filter(Position.created_at <= end_date)
            
            positions = query.all()
            
            if not positions:
                return {'success': False, 'error': '没有数据可导出'}
            
            # 准备导出数据
            export_data = []
            for position in positions:
                export_data.append({
                    'symbol': position.symbol,
                    'position_type': position.position_type.value,
                    'quantity': float(position.quantity),
                    'average_cost': float(position.average_cost),
                    'current_price': float(position.current_price or 0),
                    'market_value': float(position.market_value or 0),
                    'unrealized_pnl': float(position.unrealized_pnl or 0),
                    'unrealized_pnl_percent': float(position.unrealized_pnl_percent or 0),
                    'daily_pnl': float(position.daily_pnl or 0),
                    'total_pnl': float(position.total_pnl or 0),
                    'return_rate': float(position.return_rate or 0),
                    'stop_loss_price': float(position.stop_loss_price) if position.stop_loss_price else None,
                    'take_profit_price': float(position.take_profit_price) if position.take_profit_price else None,
                    'status': position.status.value,
                    'created_at': position.created_at.isoformat() if position.created_at else None,
                    'updated_at': position.updated_at.isoformat() if position.updated_at else None
                })
            
            # 根据格式生成文件
            if export_format.lower() == 'csv':
                file_content = self._generate_csv_content(export_data)
                file_name = f"positions_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            elif export_format.lower() == 'json':
                import json
                file_content = json.dumps(export_data, indent=2, ensure_ascii=False)
                file_name = f"positions_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            else:
                return {'success': False, 'error': '不支持的导出格式'}
            
            return {
                'success': True,
                'file_name': file_name,
                'file_content': file_content,
                'record_count': len(export_data),
                'export_format': export_format
            }
            
        except Exception as e:
            logger.error(f"导出持仓数据失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_position_history(self, position_id: int, user_id: int, 
                           start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None,
                           limit: int = 100) -> Dict[str, Any]:
        """获取持仓历史记录"""
        try:
            # 验证持仓所有权
            position = self.db.query(Position).filter(
                and_(
                    Position.id == position_id,
                    Position.user_id == user_id
                )
            ).first()
            
            if not position:
                return {'error': '持仓不存在或无权限访问'}
            
            # 构建历史查询
            query = self.db.query(PositionHistory).filter(
                PositionHistory.position_id == position_id
            )
            
            if start_date:
                query = query.filter(PositionHistory.recorded_at >= start_date)
            if end_date:
                query = query.filter(PositionHistory.recorded_at <= end_date)
            
            history_records = query.order_by(PositionHistory.recorded_at.desc()).limit(limit).all()
            
            return {
                'position_id': position_id,
                'symbol': position.symbol,
                'history': [record.to_dict() for record in history_records],
                'total_records': len(history_records)
            }
            
        except Exception as e:
            logger.error(f"获取持仓历史失败: {e}")
            return {'error': str(e)}
    
    # ==================== 私有方法 ====================
    
    def _check_close_position_risk(self, position: Position, close_quantity: Decimal) -> Dict[str, Any]:
        """检查平仓风险"""
        try:
            # 基础检查
            if close_quantity <= 0:
                return {'allowed': False, 'reason': '平仓数量必须大于0'}
            
            if close_quantity > position.available_quantity:
                return {'allowed': False, 'reason': '平仓数量超过可用数量'}
            
            # 市场时间检查（简化）
            current_hour = datetime.now().hour
            if current_hour < 9 or current_hour > 15:
                return {'allowed': False, 'reason': '非交易时间'}
            
            # 风险规则检查
            risk_context = {
                'user_id': position.user_id,
                'position_id': position.id,
                'symbol': position.symbol,
                'action': 'close_position',
                'quantity': float(close_quantity)
            }
            
            risk_events = self.risk_service.check_risk_rules(risk_context)
            
            # 检查是否有阻止平仓的风险事件
            for event in risk_events:
                rule = self.risk_service.get_risk_rule(event.rule_id)
                if rule:
                    for action in rule.actions:
                        if action.get('type') == 'BLOCK_ORDER':
                            return {'allowed': False, 'reason': event.message}
            
            return {'allowed': True, 'reason': None}
            
        except Exception as e:
            logger.error(f"检查平仓风险失败: {e}")
            return {'allowed': False, 'reason': f'风险检查失败: {str(e)}'}
    
    def _create_close_order_data(self, position: Position, close_type: str, 
                               close_price: Optional[Decimal], close_quantity: Decimal) -> Dict[str, Any]:
        """创建平仓订单数据"""
        # 确定订单类型和价格
        if close_type == 'market':
            order_type = OrderType.MARKET
            price = None
        elif close_type == 'limit':
            order_type = OrderType.LIMIT
            price = close_price
        else:
            order_type = OrderType.MARKET
            price = None
        
        # 确定订单方向（平仓方向与开仓相反）
        if position.position_type.value == 'LONG':
            side = OrderSide.SELL
        else:
            side = OrderSide.BUY
        
        return {
            'symbol': position.symbol,
            'order_type': order_type,
            'side': side,
            'quantity': close_quantity,
            'price': price,
            'time_in_force': 'IOC' if close_type == 'market' else 'GTC',
            'strategy_id': position.strategy_id,
            'source': 'position_close',
            'parent_position_id': position.id
        }
    
    def _validate_stop_loss_price(self, position: Position, stop_price: Decimal) -> Dict[str, Any]:
        """验证止损价格"""
        try:
            current_price = position.current_price or position.average_cost
            
            if position.position_type.value == 'LONG':
                # 多头止损价格应该低于当前价格
                if stop_price >= current_price:
                    return {'valid': False, 'error': '多头止损价格应该低于当前价格'}
                
                # 检查止损幅度是否合理（不超过50%）
                stop_loss_ratio = (current_price - stop_price) / current_price
                if stop_loss_ratio > 0.5:
                    return {'valid': False, 'error': '止损幅度过大，不能超过50%'}
                    
            else:  # SHORT
                # 空头止损价格应该高于当前价格
                if stop_price <= current_price:
                    return {'valid': False, 'error': '空头止损价格应该高于当前价格'}
                
                # 检查止损幅度
                stop_loss_ratio = (stop_price - current_price) / current_price
                if stop_loss_ratio > 0.5:
                    return {'valid': False, 'error': '止损幅度过大，不能超过50%'}
            
            return {'valid': True, 'error': None}
            
        except Exception as e:
            return {'valid': False, 'error': f'价格验证失败: {str(e)}'}
    
    def _validate_take_profit_price(self, position: Position, profit_price: Decimal) -> Dict[str, Any]:
        """验证止盈价格"""
        try:
            current_price = position.current_price or position.average_cost
            
            if position.position_type.value == 'LONG':
                # 多头止盈价格应该高于当前价格
                if profit_price <= current_price:
                    return {'valid': False, 'error': '多头止盈价格应该高于当前价格'}
                    
            else:  # SHORT
                # 空头止盈价格应该低于当前价格
                if profit_price >= current_price:
                    return {'valid': False, 'error': '空头止盈价格应该低于当前价格'}
            
            return {'valid': True, 'error': None}
            
        except Exception as e:
            return {'valid': False, 'error': f'价格验证失败: {str(e)}'}
    
    def _calculate_estimated_close_pnl(self, position: Position, close_price: Optional[Decimal], 
                                     close_quantity: Decimal) -> float:
        """计算预估平仓盈亏"""
        try:
            if close_price is None:
                close_price = position.current_price or position.average_cost
            
            if position.position_type.value == 'LONG':
                pnl = float(close_quantity * (close_price - position.average_cost))
            else:
                pnl = float(close_quantity * (position.average_cost - close_price))
            
            return pnl
            
        except Exception as e:
            logger.error(f"计算预估平仓盈亏失败: {e}")
            return 0.0
    
    def _calculate_estimated_stop_loss(self, position: Position, stop_price: Decimal) -> float:
        """计算预估止损亏损"""
        try:
            if position.position_type.value == 'LONG':
                loss = float(position.available_quantity * (position.average_cost - stop_price))
            else:
                loss = float(position.available_quantity * (stop_price - position.average_cost))
            
            return loss
            
        except Exception as e:
            logger.error(f"计算预估止损亏损失败: {e}")
            return 0.0
    
    def _calculate_estimated_take_profit(self, position: Position, profit_price: Decimal) -> float:
        """计算预估止盈收益"""
        try:
            if position.position_type.value == 'LONG':
                profit = float(position.available_quantity * (profit_price - position.average_cost))
            else:
                profit = float(position.available_quantity * (position.average_cost - profit_price))
            
            return profit
            
        except Exception as e:
            logger.error(f"计算预估止盈收益失败: {e}")
            return 0.0
    
    def _record_position_operation(self, position: Position, operation_type: str, operation_data: Dict[str, Any]):
        """记录持仓操作"""
        try:
            # 这里可以记录到操作日志表
            logger.info(f"持仓操作记录: {position.symbol} - {operation_type} - {operation_data}")
            
        except Exception as e:
            logger.error(f"记录持仓操作失败: {e}")
    
    async def _notify_position_operation(self, position: Position, operation_type: str, operation_data: Dict[str, Any]):
        """发送持仓操作通知"""
        try:
            notification_data = {
                'type': 'position_operation',
                'operation_type': operation_type,
                'position_id': position.id,
                'symbol': position.symbol,
                'data': operation_data,
                'timestamp': datetime.now().isoformat()
            }
            
            await websocket_manager.send_to_user(position.user_id, notification_data)
            
        except Exception as e:
            logger.error(f"发送持仓操作通知失败: {e}")
    
    def _analyze_concentration_risk(self, positions: List[Position], total_market_value: float) -> Dict[str, Any]:
        """分析集中度风险"""
        try:
            # 计算各持仓占比
            position_weights = []
            for position in positions:
                weight = float(position.market_value or 0) / total_market_value
                position_weights.append({
                    'symbol': position.symbol,
                    'weight': weight,
                    'market_value': float(position.market_value or 0)
                })
            
            # 按权重排序
            position_weights.sort(key=lambda x: x['weight'], reverse=True)
            
            # 计算集中度指标
            max_weight = position_weights[0]['weight'] if position_weights else 0
            top_5_weight = sum(pos['weight'] for pos in position_weights[:5])
            
            # 赫芬达尔指数
            hhi = sum(pos['weight']**2 for pos in position_weights)
            
            # 风险评级
            if max_weight > 0.4:
                risk_level = 'HIGH'
                warnings = [f"单一持仓 {position_weights[0]['symbol']} 占比过高: {max_weight:.1%}"]
            elif max_weight > 0.2:
                risk_level = 'MEDIUM'
                warnings = [f"单一持仓 {position_weights[0]['symbol']} 占比较高: {max_weight:.1%}"]
            else:
                risk_level = 'LOW'
                warnings = []
            
            return {
                'risk_level': risk_level,
                'max_weight': max_weight,
                'top_5_weight': top_5_weight,
                'herfindahl_index': hhi,
                'effective_positions': 1/hhi if hhi > 0 else 0,
                'position_weights': position_weights,
                'warnings': warnings
            }
            
        except Exception as e:
            logger.error(f"分析集中度风险失败: {e}")
            return {'risk_level': 'UNKNOWN', 'warnings': []}
    
    def _analyze_sector_concentration(self, positions: List[Position], total_market_value: float) -> Dict[str, Any]:
        """分析行业集中度"""
        try:
            # 简化的行业分类
            sector_map = {
                'AAPL': 'Technology', 'GOOGL': 'Technology', 'MSFT': 'Technology',
                'AMZN': 'E-commerce', 'TSLA': 'Automotive', 'NVDA': 'Semiconductors'
            }
            
            # 计算行业分布
            sector_weights = {}
            for position in positions:
                sector = sector_map.get(position.symbol, 'Other')
                weight = float(position.market_value or 0) / total_market_value
                
                if sector not in sector_weights:
                    sector_weights[sector] = 0
                sector_weights[sector] += weight
            
            # 找出最大行业占比
            max_sector_weight = max(sector_weights.values()) if sector_weights else 0
            max_sector = max(sector_weights.items(), key=lambda x: x[1])[0] if sector_weights else None
            
            # 风险评级
            if max_sector_weight > 0.6:
                risk_level = 'HIGH'
                warnings = [f"行业 {max_sector} 占比过高: {max_sector_weight:.1%}"]
            elif max_sector_weight > 0.4:
                risk_level = 'MEDIUM'
                warnings = [f"行业 {max_sector} 占比较高: {max_sector_weight:.1%}"]
            else:
                risk_level = 'LOW'
                warnings = []
            
            return {
                'risk_level': risk_level,
                'max_sector_weight': max_sector_weight,
                'max_sector': max_sector,
                'sector_distribution': sector_weights,
                'sector_count': len(sector_weights),
                'warnings': warnings
            }
            
        except Exception as e:
            logger.error(f"分析行业集中度失败: {e}")
            return {'risk_level': 'UNKNOWN', 'warnings': []}
    
    def _assess_overall_concentration_risk(self, concentration_analysis: Dict[str, Any], 
                                         sector_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """评估整体集中度风险"""
        try:
            # 综合风险等级
            risk_levels = {'LOW': 1, 'MEDIUM': 2, 'HIGH': 3, 'UNKNOWN': 0}
            
            position_risk = risk_levels.get(concentration_analysis.get('risk_level', 'UNKNOWN'), 0)
            sector_risk = risk_levels.get(sector_analysis.get('risk_level', 'UNKNOWN'), 0)
            
            overall_risk_score = max(position_risk, sector_risk)
            overall_risk_level = {1: 'LOW', 2: 'MEDIUM', 3: 'HIGH'}.get(overall_risk_score, 'UNKNOWN')
            
            # 合并警告
            all_warnings = concentration_analysis.get('warnings', []) + sector_analysis.get('warnings', [])
            
            # 生成建议
            recommendations = []
            if overall_risk_level == 'HIGH':
                recommendations.extend([
                    '建议减少单一持仓或行业的权重',
                    '考虑增加不同行业的投资',
                    '设置适当的止损来控制风险'
                ])
            elif overall_risk_level == 'MEDIUM':
                recommendations.extend([
                    '注意监控大权重持仓的表现',
                    '考虑适度分散投资'
                ])
            
            return {
                'risk_level': overall_risk_level,
                'risk_score': overall_risk_score,
                'warnings': all_warnings,
                'recommendations': recommendations
            }
            
        except Exception as e:
            logger.error(f"评估整体集中度风险失败: {e}")
            return {'risk_level': 'UNKNOWN', 'warnings': [], 'recommendations': []}
    
    def _check_position_risks(self, position: Position) -> List[Dict[str, Any]]:
        """检查单个持仓风险"""
        alerts = []
        
        try:
            # 检查大幅亏损
            if position.unrealized_pnl_percent and float(position.unrealized_pnl_percent) < -10:
                alerts.append({
                    'type': 'large_loss',
                    'position_id': position.id,
                    'symbol': position.symbol,
                    'severity': 'HIGH',
                    'message': f'{position.symbol} 亏损超过10%，当前亏损 {float(position.unrealized_pnl_percent):.2f}%',
                    'value': float(position.unrealized_pnl_percent)
                })
            
            # 检查止损止盈触发
            if position.current_price:
                current_price = float(position.current_price)
                
                if position.stop_loss_price:
                    stop_price = float(position.stop_loss_price)
                    if ((position.position_type.value == 'LONG' and current_price <= stop_price) or
                        (position.position_type.value == 'SHORT' and current_price >= stop_price)):
                        alerts.append({
                            'type': 'stop_loss_triggered',
                            'position_id': position.id,
                            'symbol': position.symbol,
                            'severity': 'HIGH',
                            'message': f'{position.symbol} 触发止损价格 {stop_price}',
                            'value': stop_price
                        })
                
                if position.take_profit_price:
                    profit_price = float(position.take_profit_price)
                    if ((position.position_type.value == 'LONG' and current_price >= profit_price) or
                        (position.position_type.value == 'SHORT' and current_price <= profit_price)):
                        alerts.append({
                            'type': 'take_profit_triggered',
                            'position_id': position.id,
                            'symbol': position.symbol,
                            'severity': 'MEDIUM',
                            'message': f'{position.symbol} 触发止盈价格 {profit_price}',
                            'value': profit_price
                        })
            
            # 检查持仓时间
            if position.created_at:
                holding_days = (datetime.now() - position.created_at).days
                if holding_days > 90:  # 持仓超过3个月
                    alerts.append({
                        'type': 'long_holding',
                        'position_id': position.id,
                        'symbol': position.symbol,
                        'severity': 'LOW',
                        'message': f'{position.symbol} 持仓时间较长: {holding_days} 天',
                        'value': holding_days
                    })
            
        except Exception as e:
            logger.error(f"检查持仓风险失败: {e}")
        
        return alerts
    
    def _check_portfolio_risks(self, positions: List[Position]) -> List[Dict[str, Any]]:
        """检查组合级别风险"""
        alerts = []
        
        try:
            if not positions:
                return alerts
            
            # 计算总市值
            total_market_value = sum(float(pos.market_value or 0) for pos in positions)
            
            # 检查集中度风险
            max_position_value = max(float(pos.market_value or 0) for pos in positions)
            max_concentration = max_position_value / total_market_value if total_market_value > 0 else 0
            
            if max_concentration > 0.4:
                max_position = max(positions, key=lambda x: float(x.market_value or 0))
                alerts.append({
                    'type': 'high_concentration',
                    'severity': 'HIGH',
                    'message': f'持仓集中度过高，{max_position.symbol} 占比 {max_concentration:.1%}',
                    'value': max_concentration
                })
            
            # 检查总体盈亏
            total_unrealized_pnl = sum(float(pos.unrealized_pnl or 0) for pos in positions)
            total_cost = sum(float(pos.quantity * pos.average_cost) for pos in positions)
            
            if total_cost > 0:
                total_return_percent = total_unrealized_pnl / total_cost * 100
                if total_return_percent < -15:
                    alerts.append({
                        'type': 'portfolio_large_loss',
                        'severity': 'HIGH',
                        'message': f'组合总体亏损较大: {total_return_percent:.2f}%',
                        'value': total_return_percent
                    })
            
        except Exception as e:
            logger.error(f"检查组合风险失败: {e}")
        
        return alerts
    
    def _generate_csv_content(self, data: List[Dict[str, Any]]) -> str:
        """生成CSV内容"""
        try:
            import csv
            import io
            
            if not data:
                return ""
            
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"生成CSV内容失败: {e}")
            return ""