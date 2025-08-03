"""
订单执行引擎
负责订单的提交、执行、成交处理等核心逻辑
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
import uuid

from ..models.order import Order, OrderFill, OrderStatus, OrderType, OrderSide
from ..services.order_notification_service import order_notification_service
from ..core.database import SessionLocal

logger = logging.getLogger(__name__)


class ExecutionResult(Enum):
    """执行结果枚举"""
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class OrderExecutionEngine:
    """订单执行引擎"""
    
    def __init__(self):
        self.execution_handlers: Dict[str, Callable] = {}
        self.market_data_provider = None
        self.risk_manager = None
        self.position_manager = None
        self.account_manager = None
        
        # 执行队列和状态
        self.execution_queue = asyncio.Queue()
        self.active_executions: Dict[int, asyncio.Task] = {}
        self.execution_stats = {
            'total_orders': 0,
            'successful_orders': 0,
            'failed_orders': 0,
            'cancelled_orders': 0,
            'average_execution_time': 0.0
        }
    
    def register_execution_handler(self, order_type: str, handler: Callable):
        """注册订单类型的执行处理器"""
        self.execution_handlers[order_type] = handler
        logger.info(f"注册订单执行处理器: {order_type}")
    
    async def submit_order(self, order: Order) -> ExecutionResult:
        """提交订单到执行引擎"""
        try:
            logger.info(f"提交订单到执行引擎: {order.id} - {order.symbol} {order.side} {order.quantity}")
            
            # 预执行检查
            pre_check_result = await self._pre_execution_check(order)
            if not pre_check_result.success:
                await self._handle_order_rejection(order, pre_check_result.message)
                return ExecutionResult.REJECTED
            
            # 更新订单状态为已提交
            await self._update_order_status(order, OrderStatus.SUBMITTED)
            
            # 添加到执行队列
            await self.execution_queue.put(order)
            
            # 启动异步执行任务
            execution_task = asyncio.create_task(self._execute_order(order))
            self.active_executions[order.id] = execution_task
            
            return ExecutionResult.SUCCESS
            
        except Exception as e:
            logger.error(f"提交订单失败: {order.id} - {str(e)}")
            await self._handle_order_error(order, str(e))
            return ExecutionResult.FAILED
    
    async def cancel_order(self, order: Order, reason: str = "") -> ExecutionResult:
        """取消订单执行"""
        try:
            logger.info(f"取消订单执行: {order.id} - {reason}")
            
            # 检查订单是否可以取消
            if not order.is_active:
                raise ValueError("订单不是活跃状态，无法取消")
            
            # 如果订单正在执行，停止执行任务
            if order.id in self.active_executions:
                execution_task = self.active_executions[order.id]
                execution_task.cancel()
                
                try:
                    await execution_task
                except asyncio.CancelledError:
                    pass
                
                del self.active_executions[order.id]
            
            # 更新订单状态
            await self._update_order_status(order, OrderStatus.CANCELLED)
            
            # 发送取消通知
            order_notification_service.notify_order_cancelled(order, reason)
            
            self.execution_stats['cancelled_orders'] += 1
            
            return ExecutionResult.CANCELLED
            
        except Exception as e:
            logger.error(f"取消订单失败: {order.id} - {str(e)}")
            return ExecutionResult.FAILED
    
    async def modify_order(self, order: Order, modifications: Dict[str, Any]) -> ExecutionResult:
        """修改订单"""
        try:
            logger.info(f"修改订单: {order.id} - {modifications}")
            
            # 检查订单是否可以修改
            if not order.is_active:
                raise ValueError("订单不是活跃状态，无法修改")
            
            # 如果订单正在执行，需要先暂停执行
            execution_paused = False
            if order.id in self.active_executions:
                # 这里可以实现更复杂的暂停逻辑
                execution_paused = True
            
            # 应用修改
            db = SessionLocal()
            try:
                for field, value in modifications.items():
                    if hasattr(order, field):
                        setattr(order, field, value)
                
                # 重新计算剩余数量等
                if 'quantity' in modifications:
                    order.calculate_remaining_quantity()
                
                db.commit()
                db.refresh(order)
                
                # 发送修改通知
                order_notification_service.notify_order_updated(
                    order, list(modifications.keys())
                )
                
                # 如果暂停了执行，重新启动
                if execution_paused:
                    # 重新提交到执行队列
                    await self.execution_queue.put(order)
                
                return ExecutionResult.SUCCESS
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"修改订单失败: {order.id} - {str(e)}")
            return ExecutionResult.FAILED
    
    async def _execute_order(self, order: Order):
        """执行订单的核心逻辑"""
        execution_start_time = datetime.now()
        
        try:
            logger.info(f"开始执行订单: {order.id}")
            
            # 更新订单状态为已接受
            await self._update_order_status(order, OrderStatus.ACCEPTED)
            
            # 根据订单类型选择执行策略
            handler = self.execution_handlers.get(order.order_type)
            if not handler:
                # 使用默认执行逻辑
                await self._default_execution_logic(order)
            else:
                await handler(order)
            
            # 计算执行时间
            execution_time = (datetime.now() - execution_start_time).total_seconds()
            self._update_execution_stats(execution_time, True)
            
            logger.info(f"订单执行完成: {order.id}, 耗时: {execution_time:.2f}秒")
            
        except asyncio.CancelledError:
            logger.info(f"订单执行被取消: {order.id}")
            raise
        except Exception as e:
            logger.error(f"订单执行失败: {order.id} - {str(e)}")
            await self._handle_order_error(order, str(e))
            
            execution_time = (datetime.now() - execution_start_time).total_seconds()
            self._update_execution_stats(execution_time, False)
        finally:
            # 清理执行任务
            self.active_executions.pop(order.id, None)
    
    async def _default_execution_logic(self, order: Order):
        """默认订单执行逻辑"""
        try:
            # 获取市场价格
            market_price = await self._get_market_price(order.symbol)
            if not market_price:
                raise ValueError(f"无法获取 {order.symbol} 的市场价格")
            
            # 确定执行价格
            execution_price = await self._determine_execution_price(order, market_price)
            if not execution_price:
                # 价格不满足条件，等待
                await self._wait_for_price_condition(order, market_price)
                return
            
            # 执行成交
            await self._execute_fill(order, execution_price)
            
        except Exception as e:
            logger.error(f"默认执行逻辑失败: {order.id} - {str(e)}")
            raise
    
    async def _determine_execution_price(self, order: Order, market_price: Decimal) -> Optional[Decimal]:
        """确定订单执行价格"""
        if order.order_type == OrderType.MARKET:
            return market_price
        
        elif order.order_type == OrderType.LIMIT:
            if order.side == OrderSide.BUY:
                # 买单：市价 <= 限价时可以成交
                if market_price <= order.price:
                    return min(order.price, market_price)
            else:  # SELL
                # 卖单：市价 >= 限价时可以成交
                if market_price >= order.price:
                    return max(order.price, market_price)
            return None
        
        elif order.order_type == OrderType.STOP:
            if order.side == OrderSide.BUY:
                # 买入止损：市价 >= 止损价时触发
                if market_price >= order.stop_price:
                    return market_price
            else:  # SELL
                # 卖出止损：市价 <= 止损价时触发
                if market_price <= order.stop_price:
                    return market_price
            return None
        
        elif order.order_type == OrderType.STOP_LIMIT:
            # 先检查是否触发止损条件
            triggered = False
            if order.side == OrderSide.BUY and market_price >= order.stop_price:
                triggered = True
            elif order.side == OrderSide.SELL and market_price <= order.stop_price:
                triggered = True
            
            if triggered:
                # 触发后按限价单逻辑执行
                if order.side == OrderSide.BUY:
                    if market_price <= order.price:
                        return min(order.price, market_price)
                else:  # SELL
                    if market_price >= order.price:
                        return max(order.price, market_price)
            return None
        
        else:
            # 其他订单类型使用市价
            return market_price
    
    async def _execute_fill(self, order: Order, price: Decimal):
        """执行订单成交"""
        try:
            remaining_quantity = order.quantity - order.filled_quantity
            
            # 模拟分批成交（可以根据市场深度等因素调整）
            fill_quantity = await self._calculate_fill_quantity(order, remaining_quantity)
            
            # 创建成交记录
            fill_data = {
                'quantity': float(fill_quantity),
                'price': float(price),
                'commission': float(fill_quantity * price * Decimal('0.001')),  # 0.1%手续费
                'commission_asset': 'USD',
                'fill_time': datetime.now(),
                'liquidity': 'taker',  # 简化处理
                'counterparty': f'MM_{uuid.uuid4().hex[:8]}'
            }
            
            # 添加成交记录到数据库
            db = SessionLocal()
            try:
                from ..services.order_service import OrderService
                order_service = OrderService(db)
                fill = order_service.add_order_fill(order.id, fill_data)
                
                # 刷新订单状态
                db.refresh(order)
                
                logger.info(f"订单成交: {order.id}, 数量: {fill_quantity}, 价格: {price}")
                
                # 如果还有剩余数量，继续执行
                if order.remaining_quantity > 0 and order.status == OrderStatus.PARTIALLY_FILLED:
                    # 等待一段时间后继续执行
                    await asyncio.sleep(1)
                    await self._execute_fill(order, price)
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"执行成交失败: {order.id} - {str(e)}")
            raise
    
    async def _calculate_fill_quantity(self, order: Order, remaining_quantity: Decimal) -> Decimal:
        """计算本次成交数量"""
        # 简化逻辑：随机成交10%-100%的剩余数量
        import random
        fill_ratio = random.uniform(0.1, 1.0)
        return remaining_quantity * Decimal(str(fill_ratio))
    
    async def _wait_for_price_condition(self, order: Order, current_price: Decimal):
        """等待价格条件满足"""
        logger.info(f"订单 {order.id} 等待价格条件满足，当前价格: {current_price}")
        
        # 等待一段时间后重新检查
        await asyncio.sleep(5)
        
        # 重新获取价格并检查
        new_price = await self._get_market_price(order.symbol)
        if new_price:
            execution_price = await self._determine_execution_price(order, new_price)
            if execution_price:
                await self._execute_fill(order, execution_price)
            else:
                # 继续等待
                await self._wait_for_price_condition(order, new_price)
    
    async def _get_market_price(self, symbol: str) -> Optional[Decimal]:
        """获取市场价格"""
        # 这里应该从市场数据提供商获取实时价格
        # 简化处理：使用模拟价格
        mock_prices = {
            'AAPL': Decimal('150.00'),
            'TSLA': Decimal('200.00'),
            'MSFT': Decimal('300.00'),
            'GOOGL': Decimal('2500.00'),
            'AMZN': Decimal('3000.00')
        }
        
        base_price = mock_prices.get(symbol, Decimal('100.00'))
        
        # 添加随机波动
        import random
        volatility = random.uniform(0.95, 1.05)
        return base_price * Decimal(str(volatility))
    
    async def _pre_execution_check(self, order: Order) -> 'CheckResult':
        """执行前检查"""
        try:
            # 检查订单状态
            if not order.is_active:
                return CheckResult(False, "订单不是活跃状态")
            
            # 检查资金充足性
            if order.side == OrderSide.BUY and order.price:
                required_funds = order.quantity * order.price
                # 这里应该检查实际账户余额
                # 简化处理：假设资金充足
                pass
            
            # 检查持仓限制
            # 这里应该检查实际持仓情况
            # 简化处理：假设没有限制
            
            # 检查风险规则
            # 这里应该调用风险管理模块
            # 简化处理：假设通过风险检查
            
            return CheckResult(True, "检查通过")
            
        except Exception as e:
            logger.error(f"执行前检查失败: {order.id} - {str(e)}")
            return CheckResult(False, f"检查失败: {str(e)}")
    
    async def _update_order_status(self, order: Order, new_status: OrderStatus):
        """更新订单状态"""
        db = SessionLocal()
        try:
            old_status = order.status
            order.status = new_status
            
            # 更新相关时间戳
            if new_status == OrderStatus.SUBMITTED:
                order.submitted_at = datetime.now()
            elif new_status == OrderStatus.ACCEPTED:
                order.accepted_at = datetime.now()
            elif new_status == OrderStatus.FILLED:
                order.filled_at = datetime.now()
            elif new_status == OrderStatus.CANCELLED:
                order.cancelled_at = datetime.now()
            
            db.commit()
            db.refresh(order)
            
            # 发送状态变化通知
            order_notification_service.notify_order_status_change(order, old_status)
            
        finally:
            db.close()
    
    async def _handle_order_rejection(self, order: Order, reason: str):
        """处理订单拒绝"""
        await self._update_order_status(order, OrderStatus.REJECTED)
        order_notification_service.notify_order_rejected(order, reason)
        self.execution_stats['failed_orders'] += 1
    
    async def _handle_order_error(self, order: Order, error_message: str):
        """处理订单错误"""
        order_notification_service.notify_order_error(order, error_message, "EXECUTION_ERROR")
        self.execution_stats['failed_orders'] += 1
    
    def _update_execution_stats(self, execution_time: float, success: bool):
        """更新执行统计"""
        self.execution_stats['total_orders'] += 1
        
        if success:
            self.execution_stats['successful_orders'] += 1
        else:
            self.execution_stats['failed_orders'] += 1
        
        # 更新平均执行时间
        total_orders = self.execution_stats['total_orders']
        current_avg = self.execution_stats['average_execution_time']
        self.execution_stats['average_execution_time'] = (
            (current_avg * (total_orders - 1) + execution_time) / total_orders
        )
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """获取执行统计信息"""
        return {
            **self.execution_stats,
            'active_executions': len(self.active_executions),
            'queue_size': self.execution_queue.qsize(),
            'timestamp': datetime.now().isoformat()
        }
    
    async def start_execution_worker(self):
        """启动执行工作线程"""
        logger.info("启动订单执行工作线程")
        
        while True:
            try:
                # 从队列获取订单
                order = await self.execution_queue.get()
                
                # 检查订单是否仍然有效
                if order.is_active:
                    # 启动执行任务
                    execution_task = asyncio.create_task(self._execute_order(order))
                    self.active_executions[order.id] = execution_task
                
                # 标记任务完成
                self.execution_queue.task_done()
                
            except Exception as e:
                logger.error(f"执行工作线程错误: {str(e)}")
                await asyncio.sleep(1)


class CheckResult:
    """检查结果类"""
    
    def __init__(self, success: bool, message: str = ""):
        self.success = success
        self.message = message


# 全局订单执行引擎实例
order_execution_engine = OrderExecutionEngine()