"""
订单执行服务
整合订单执行引擎和交易系统适配器，提供完整的订单执行功能
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from decimal import Decimal

from ..models.order import Order, OrderStatus, OrderSide
from ..core.order_execution_engine import order_execution_engine, ExecutionResult
from ..adapters.trading_system_adapter import trading_system_manager, TradingSystemType
from ..services.order_notification_service import order_notification_service
from ..core.database import SessionLocal

logger = logging.getLogger(__name__)


class OrderExecutionService:
    """订单执行服务"""
    
    def __init__(self):
        self.is_running = False
        self.execution_tasks: Dict[int, asyncio.Task] = {}
        self.execution_stats = {
            'total_submitted': 0,
            'total_executed': 0,
            'total_cancelled': 0,
            'total_rejected': 0,
            'execution_errors': 0
        }
    
    async def start_service(self):
        """启动订单执行服务"""
        if self.is_running:
            logger.warning("订单执行服务已在运行")
            return
        
        try:
            logger.info("启动订单执行服务")
            
            # 连接交易系统
            await trading_system_manager.connect_all()
            
            # 启动执行引擎工作线程
            asyncio.create_task(order_execution_engine.start_execution_worker())
            
            # 启动订单状态监控
            asyncio.create_task(self._start_order_status_monitor())
            
            # 启动执行统计更新
            asyncio.create_task(self._start_stats_updater())
            
            self.is_running = True
            logger.info("订单执行服务启动成功")
            
        except Exception as e:
            logger.error(f"启动订单执行服务失败: {str(e)}")
            raise
    
    async def stop_service(self):
        """停止订单执行服务"""
        if not self.is_running:
            return
        
        try:
            logger.info("停止订单执行服务")
            
            # 取消所有执行任务
            for order_id, task in self.execution_tasks.items():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            self.execution_tasks.clear()
            
            # 断开交易系统连接
            await trading_system_manager.disconnect_all()
            
            self.is_running = False
            logger.info("订单执行服务已停止")
            
        except Exception as e:
            logger.error(f"停止订单执行服务失败: {str(e)}")
    
    async def submit_order_for_execution(self, order: Order, 
                                       trading_system: str = None) -> ExecutionResult:
        """提交订单执行"""
        try:
            logger.info(f"提交订单执行: {order.id} - {order.symbol} {order.side} {order.quantity}")
            
            # 获取交易系统适配器
            adapter = trading_system_manager.get_adapter(trading_system)
            if not adapter:
                logger.error(f"未找到交易系统适配器: {trading_system}")
                return ExecutionResult.FAILED
            
            if not adapter.is_connected:
                logger.error(f"交易系统未连接: {trading_system}")
                return ExecutionResult.FAILED
            
            # 提交订单到交易系统
            submission_result = await adapter.submit_order(order)
            
            if not submission_result.success:
                logger.error(f"订单提交失败: {order.id} - {submission_result.message}")
                await self._handle_submission_failure(order, submission_result)
                return ExecutionResult.REJECTED
            
            # 更新订单的外部ID
            await self._update_order_external_id(order, submission_result.external_order_id)
            
            # 提交到执行引擎
            execution_result = await order_execution_engine.submit_order(order)
            
            # 更新统计
            self.execution_stats['total_submitted'] += 1
            
            # 启动订单监控任务
            monitor_task = asyncio.create_task(
                self._monitor_order_execution(order, adapter)
            )
            self.execution_tasks[order.id] = monitor_task
            
            logger.info(f"订单提交成功: {order.id} - 外部ID: {submission_result.external_order_id}")
            return execution_result
            
        except Exception as e:
            logger.error(f"提交订单执行失败: {order.id} - {str(e)}")
            self.execution_stats['execution_errors'] += 1
            return ExecutionResult.FAILED
    
    async def cancel_order_execution(self, order: Order) -> bool:
        """取消订单执行"""
        try:
            logger.info(f"取消订单执行: {order.id}")
            
            # 从执行引擎取消
            engine_result = await order_execution_engine.cancel_order(order)
            
            # 从交易系统取消
            adapter = trading_system_manager.get_adapter()
            if adapter and adapter.is_connected and order.order_id_external:
                system_result = await adapter.cancel_order(order)
                if not system_result:
                    logger.warning(f"交易系统取消订单失败: {order.id}")
            
            # 停止监控任务
            if order.id in self.execution_tasks:
                task = self.execution_tasks[order.id]
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                del self.execution_tasks[order.id]
            
            # 更新统计
            if engine_result == ExecutionResult.CANCELLED:
                self.execution_stats['total_cancelled'] += 1
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"取消订单执行失败: {order.id} - {str(e)}")
            return False
    
    async def modify_order_execution(self, order: Order, 
                                   modifications: Dict[str, Any]) -> bool:
        """修改订单执行"""
        try:
            logger.info(f"修改订单执行: {order.id} - {modifications}")
            
            # 在执行引擎中修改
            engine_result = await order_execution_engine.modify_order(order, modifications)
            
            # 在交易系统中修改
            adapter = trading_system_manager.get_adapter()
            if adapter and adapter.is_connected and order.order_id_external:
                system_result = await adapter.modify_order(order, modifications)
                if not system_result:
                    logger.warning(f"交易系统修改订单失败: {order.id}")
            
            return engine_result == ExecutionResult.SUCCESS
            
        except Exception as e:
            logger.error(f"修改订单执行失败: {order.id} - {str(e)}")
            return False
    
    async def get_order_execution_status(self, order: Order) -> Optional[Dict[str, Any]]:
        """获取订单执行状态"""
        try:
            status = {
                'order_id': order.id,
                'internal_status': order.status,
                'is_active': order.is_active,
                'filled_quantity': float(order.filled_quantity),
                'remaining_quantity': float(order.remaining_quantity) if order.remaining_quantity else 0,
                'fill_ratio': order.fill_ratio
            }
            
            # 获取交易系统状态
            if order.order_id_external:
                adapter = trading_system_manager.get_adapter()
                if adapter and adapter.is_connected:
                    external_status = await adapter.get_order_status(order.order_id_external)
                    if external_status:
                        status['external_status'] = external_status
            
            return status
            
        except Exception as e:
            logger.error(f"获取订单执行状态失败: {order.id} - {str(e)}")
            return None
    
    async def _monitor_order_execution(self, order: Order, adapter):
        """监控订单执行过程"""
        try:
            logger.info(f"开始监控订单执行: {order.id}")
            
            while order.is_active and order.order_id_external:
                try:
                    # 获取交易系统中的订单状态
                    external_status = await adapter.get_order_status(order.order_id_external)
                    
                    if external_status:
                        await self._process_external_status_update(order, external_status)
                    
                    # 等待一段时间后再次检查
                    await asyncio.sleep(5)
                    
                    # 刷新订单状态
                    db = SessionLocal()
                    try:
                        db.refresh(order)
                    finally:
                        db.close()
                    
                except asyncio.CancelledError:
                    logger.info(f"订单监控被取消: {order.id}")
                    break
                except Exception as e:
                    logger.error(f"监控订单执行异常: {order.id} - {str(e)}")
                    await asyncio.sleep(10)  # 出错时等待更长时间
            
            logger.info(f"订单监控结束: {order.id}")
            
        except Exception as e:
            logger.error(f"监控订单执行失败: {order.id} - {str(e)}")
        finally:
            # 清理监控任务
            self.execution_tasks.pop(order.id, None)
    
    async def _process_external_status_update(self, order: Order, external_status: Dict[str, Any]):
        """处理外部状态更新"""
        try:
            external_order_status = external_status.get('status')
            external_filled_qty = external_status.get('filled_quantity', 0)
            
            # 检查是否有新的成交
            if external_filled_qty > order.filled_quantity:
                # 计算新成交数量
                new_fill_qty = Decimal(str(external_filled_qty)) - order.filled_quantity
                
                # 创建成交记录
                fill_data = {
                    'quantity': float(new_fill_qty),
                    'price': external_status.get('last_fill_price', 0),
                    'commission': external_status.get('commission', 0),
                    'fill_time': datetime.now(),
                    'liquidity': external_status.get('liquidity', 'unknown')
                }
                
                # 添加成交记录
                db = SessionLocal()
                try:
                    from .order_service import OrderService
                    order_service = OrderService(db)
                    order_service.add_order_fill(order.id, fill_data)
                    db.refresh(order)
                finally:
                    db.close()
            
            # 检查订单状态变化
            if external_order_status == 'cancelled' and order.status != OrderStatus.CANCELLED:
                await self._update_order_status(order, OrderStatus.CANCELLED)
            elif external_order_status == 'rejected' and order.status != OrderStatus.REJECTED:
                await self._update_order_status(order, OrderStatus.REJECTED)
            
        except Exception as e:
            logger.error(f"处理外部状态更新失败: {order.id} - {str(e)}")
    
    async def _update_order_external_id(self, order: Order, external_id: str):
        """更新订单外部ID"""
        db = SessionLocal()
        try:
            order.order_id_external = external_id
            db.commit()
            db.refresh(order)
        finally:
            db.close()
    
    async def _update_order_status(self, order: Order, new_status: OrderStatus):
        """更新订单状态"""
        db = SessionLocal()
        try:
            old_status = order.status
            order.status = new_status
            
            if new_status == OrderStatus.CANCELLED:
                order.cancelled_at = datetime.now()
            
            db.commit()
            db.refresh(order)
            
            # 发送状态变化通知
            order_notification_service.notify_order_status_change(order, old_status)
            
        finally:
            db.close()
    
    async def _handle_submission_failure(self, order: Order, submission_result):
        """处理订单提交失败"""
        try:
            # 更新订单状态为拒绝
            await self._update_order_status(order, OrderStatus.REJECTED)
            
            # 发送拒绝通知
            order_notification_service.notify_order_rejected(
                order, submission_result.message
            )
            
            # 更新统计
            self.execution_stats['total_rejected'] += 1
            
        except Exception as e:
            logger.error(f"处理订单提交失败异常: {order.id} - {str(e)}")
    
    async def _start_order_status_monitor(self):
        """启动订单状态监控"""
        logger.info("启动订单状态监控")
        
        while self.is_running:
            try:
                # 检查所有活跃订单的状态
                db = SessionLocal()
                try:
                    active_orders = db.query(Order).filter(
                        Order.status.in_([
                            OrderStatus.PENDING,
                            OrderStatus.SUBMITTED,
                            OrderStatus.ACCEPTED,
                            OrderStatus.PARTIALLY_FILLED
                        ])
                    ).all()
                    
                    for order in active_orders:
                        if order.id not in self.execution_tasks:
                            # 为没有监控任务的活跃订单创建监控
                            adapter = trading_system_manager.get_adapter()
                            if adapter and adapter.is_connected:
                                monitor_task = asyncio.create_task(
                                    self._monitor_order_execution(order, adapter)
                                )
                                self.execution_tasks[order.id] = monitor_task
                
                finally:
                    db.close()
                
                # 每分钟检查一次
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"订单状态监控异常: {str(e)}")
                await asyncio.sleep(60)
    
    async def _start_stats_updater(self):
        """启动执行统计更新"""
        logger.info("启动执行统计更新")
        
        while self.is_running:
            try:
                # 更新执行统计
                db = SessionLocal()
                try:
                    # 统计各种状态的订单数量
                    total_executed = db.query(Order).filter(
                        Order.status == OrderStatus.FILLED
                    ).count()
                    
                    total_cancelled = db.query(Order).filter(
                        Order.status == OrderStatus.CANCELLED
                    ).count()
                    
                    total_rejected = db.query(Order).filter(
                        Order.status == OrderStatus.REJECTED
                    ).count()
                    
                    self.execution_stats.update({
                        'total_executed': total_executed,
                        'total_cancelled': total_cancelled,
                        'total_rejected': total_rejected,
                        'last_updated': datetime.now().isoformat()
                    })
                
                finally:
                    db.close()
                
                # 每5分钟更新一次
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error(f"执行统计更新异常: {str(e)}")
                await asyncio.sleep(300)
    
    def get_service_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {
            'is_running': self.is_running,
            'active_executions': len(self.execution_tasks),
            'execution_stats': self.execution_stats,
            'trading_systems': trading_system_manager.get_connection_status(),
            'engine_stats': order_execution_engine.get_execution_stats(),
            'timestamp': datetime.now().isoformat()
        }
    
    def get_execution_statistics(self) -> Dict[str, Any]:
        """获取执行统计信息"""
        return {
            **self.execution_stats,
            'success_rate': (
                self.execution_stats['total_executed'] / 
                max(self.execution_stats['total_submitted'], 1)
            ),
            'active_orders': len(self.execution_tasks),
            'timestamp': datetime.now().isoformat()
        }


# 全局订单执行服务实例
order_execution_service = OrderExecutionService()