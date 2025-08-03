"""
订单通知服务
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from decimal import Decimal

from ..core.websocket import websocket_manager
from ..models.order import Order, OrderFill, OrderStatus

logger = logging.getLogger(__name__)


class OrderNotificationService:
    """订单通知服务"""
    
    @staticmethod
    def notify_order_status_change(order: Order, old_status: Optional[OrderStatus] = None):
        """通知订单状态变化"""
        try:
            message = {
                'type': 'order_status_changed',
                'order_id': order.id,
                'order_uuid': order.uuid,
                'symbol': order.symbol,
                'side': order.side,
                'order_type': order.order_type,
                'quantity': float(order.quantity),
                'price': float(order.price) if order.price else None,
                'filled_quantity': float(order.filled_quantity),
                'remaining_quantity': float(order.remaining_quantity) if order.remaining_quantity else None,
                'avg_fill_price': float(order.avg_fill_price) if order.avg_fill_price else None,
                'status': order.status,
                'old_status': old_status,
                'fill_ratio': order.fill_ratio,
                'is_active': order.is_active,
                'is_finished': order.is_finished,
                'timestamp': datetime.now().isoformat()
            }
            
            websocket_manager.send_to_user_sync(order.user_id, message)
            logger.info(f"发送订单状态变化通知: {order.id} {old_status} -> {order.status}")
            
        except Exception as e:
            logger.error(f"发送订单状态变化通知失败: {str(e)}")
    
    @staticmethod
    def notify_order_created(order: Order):
        """通知订单创建"""
        try:
            message = {
                'type': 'order_created',
                'order_id': order.id,
                'order_uuid': order.uuid,
                'symbol': order.symbol,
                'side': order.side,
                'order_type': order.order_type,
                'quantity': float(order.quantity),
                'price': float(order.price) if order.price else None,
                'status': order.status,
                'priority': order.priority,
                'time_in_force': order.time_in_force,
                'strategy_id': order.strategy_id,
                'backtest_id': order.backtest_id,
                'tags': order.tags,
                'timestamp': datetime.now().isoformat()
            }
            
            websocket_manager.send_to_user_sync(order.user_id, message)
            logger.info(f"发送订单创建通知: {order.id}")
            
        except Exception as e:
            logger.error(f"发送订单创建通知失败: {str(e)}")
    
    @staticmethod
    def notify_order_updated(order: Order, updated_fields: List[str]):
        """通知订单更新"""
        try:
            message = {
                'type': 'order_updated',
                'order_id': order.id,
                'order_uuid': order.uuid,
                'symbol': order.symbol,
                'updated_fields': updated_fields,
                'current_data': {
                    'quantity': float(order.quantity),
                    'price': float(order.price) if order.price else None,
                    'stop_price': float(order.stop_price) if order.stop_price else None,
                    'time_in_force': order.time_in_force,
                    'priority': order.priority,
                    'expire_time': order.expire_time.isoformat() if order.expire_time else None,
                    'tags': order.tags,
                    'notes': order.notes,
                    'status': order.status
                },
                'timestamp': datetime.now().isoformat()
            }
            
            websocket_manager.send_to_user_sync(order.user_id, message)
            logger.info(f"发送订单更新通知: {order.id}, 字段: {updated_fields}")
            
        except Exception as e:
            logger.error(f"发送订单更新通知失败: {str(e)}")
    
    @staticmethod
    def notify_order_cancelled(order: Order, reason: str = ""):
        """通知订单取消"""
        try:
            message = {
                'type': 'order_cancelled',
                'order_id': order.id,
                'order_uuid': order.uuid,
                'symbol': order.symbol,
                'side': order.side,
                'quantity': float(order.quantity),
                'filled_quantity': float(order.filled_quantity),
                'reason': reason,
                'cancelled_at': order.cancelled_at.isoformat() if order.cancelled_at else None,
                'timestamp': datetime.now().isoformat()
            }
            
            websocket_manager.send_to_user_sync(order.user_id, message)
            logger.info(f"发送订单取消通知: {order.id}")
            
        except Exception as e:
            logger.error(f"发送订单取消通知失败: {str(e)}")
    
    @staticmethod
    def notify_order_filled(order: Order, fill: OrderFill):
        """通知订单成交"""
        try:
            message = {
                'type': 'order_filled',
                'order_id': order.id,
                'order_uuid': order.uuid,
                'symbol': order.symbol,
                'side': order.side,
                'fill_data': {
                    'fill_id': fill.id,
                    'fill_uuid': fill.uuid,
                    'quantity': float(fill.quantity),
                    'price': float(fill.price),
                    'value': float(fill.value),
                    'commission': float(fill.commission),
                    'commission_asset': fill.commission_asset,
                    'fill_time': fill.fill_time.isoformat(),
                    'liquidity': fill.liquidity
                },
                'order_status': {
                    'filled_quantity': float(order.filled_quantity),
                    'remaining_quantity': float(order.remaining_quantity) if order.remaining_quantity else None,
                    'avg_fill_price': float(order.avg_fill_price) if order.avg_fill_price else None,
                    'status': order.status,
                    'fill_ratio': order.fill_ratio,
                    'total_commission': float(order.commission)
                },
                'timestamp': datetime.now().isoformat()
            }
            
            websocket_manager.send_to_user_sync(order.user_id, message)
            logger.info(f"发送订单成交通知: {order.id}, 成交数量: {fill.quantity}")
            
        except Exception as e:
            logger.error(f"发送订单成交通知失败: {str(e)}")
    
    @staticmethod
    def notify_order_rejected(order: Order, reason: str):
        """通知订单拒绝"""
        try:
            message = {
                'type': 'order_rejected',
                'order_id': order.id,
                'order_uuid': order.uuid,
                'symbol': order.symbol,
                'side': order.side,
                'quantity': float(order.quantity),
                'price': float(order.price) if order.price else None,
                'reason': reason,
                'timestamp': datetime.now().isoformat()
            }
            
            websocket_manager.send_to_user_sync(order.user_id, message)
            logger.info(f"发送订单拒绝通知: {order.id}, 原因: {reason}")
            
        except Exception as e:
            logger.error(f"发送订单拒绝通知失败: {str(e)}")
    
    @staticmethod
    def notify_order_expired(order: Order):
        """通知订单过期"""
        try:
            message = {
                'type': 'order_expired',
                'order_id': order.id,
                'order_uuid': order.uuid,
                'symbol': order.symbol,
                'side': order.side,
                'quantity': float(order.quantity),
                'filled_quantity': float(order.filled_quantity),
                'expire_time': order.expire_time.isoformat() if order.expire_time else None,
                'timestamp': datetime.now().isoformat()
            }
            
            websocket_manager.send_to_user_sync(order.user_id, message)
            logger.info(f"发送订单过期通知: {order.id}")
            
        except Exception as e:
            logger.error(f"发送订单过期通知失败: {str(e)}")
    
    @staticmethod
    def notify_order_error(order: Order, error_message: str, error_code: str = ""):
        """通知订单错误"""
        try:
            message = {
                'type': 'order_error',
                'order_id': order.id,
                'order_uuid': order.uuid,
                'symbol': order.symbol,
                'error_message': error_message,
                'error_code': error_code,
                'timestamp': datetime.now().isoformat()
            }
            
            websocket_manager.send_to_user_sync(order.user_id, message)
            logger.info(f"发送订单错误通知: {order.id}, 错误: {error_message}")
            
        except Exception as e:
            logger.error(f"发送订单错误通知失败: {str(e)}")
    
    @staticmethod
    def notify_batch_operation_result(user_id: int, operation: str, results: Dict[str, Any]):
        """通知批量操作结果"""
        try:
            message = {
                'type': 'batch_operation_result',
                'operation': operation,
                'success_count': results.get('success_count', 0),
                'failed_count': results.get('failed_count', 0),
                'total_count': results.get('success_count', 0) + results.get('failed_count', 0),
                'results': results.get('results', []),
                'timestamp': datetime.now().isoformat()
            }
            
            websocket_manager.send_to_user_sync(user_id, message)
            logger.info(f"发送批量操作结果通知: {operation}")
            
        except Exception as e:
            logger.error(f"发送批量操作结果通知失败: {str(e)}")
    
    @staticmethod
    def notify_risk_alert(user_id: int, order_id: int, alert_type: str, message: str, severity: str = "warning"):
        """通知风险警告"""
        try:
            alert_message = {
                'type': 'risk_alert',
                'order_id': order_id,
                'alert_type': alert_type,
                'message': message,
                'severity': severity,  # info, warning, error, critical
                'timestamp': datetime.now().isoformat()
            }
            
            websocket_manager.send_to_user_sync(user_id, alert_message)
            logger.info(f"发送风险警告通知: 订单 {order_id}, 类型: {alert_type}")
            
        except Exception as e:
            logger.error(f"发送风险警告通知失败: {str(e)}")
    
    @staticmethod
    def notify_order_execution_progress(order: Order, progress: float, message: str = ""):
        """通知订单执行进度"""
        try:
            progress_message = {
                'type': 'order_execution_progress',
                'order_id': order.id,
                'order_uuid': order.uuid,
                'symbol': order.symbol,
                'progress': progress,  # 0.0 - 1.0
                'message': message,
                'current_status': order.status,
                'filled_quantity': float(order.filled_quantity),
                'total_quantity': float(order.quantity),
                'timestamp': datetime.now().isoformat()
            }
            
            websocket_manager.send_to_user_sync(order.user_id, progress_message)
            logger.debug(f"发送订单执行进度通知: {order.id}, 进度: {progress:.2%}")
            
        except Exception as e:
            logger.error(f"发送订单执行进度通知失败: {str(e)}")


# 全局订单通知服务实例
order_notification_service = OrderNotificationService()