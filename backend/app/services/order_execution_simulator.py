"""
订单执行模拟器
用于测试和演示订单状态实时更新功能
"""

import asyncio
import logging
import random
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal

from ..models.order import Order, OrderStatus, OrderSide
from ..services.order_service import OrderService
from ..services.order_notification_service import order_notification_service
from ..core.database import SessionLocal

logger = logging.getLogger(__name__)


class OrderExecutionSimulator:
    """订单执行模拟器"""
    
    def __init__(self):
        self.running_simulations: Dict[int, asyncio.Task] = {}
        self.market_prices: Dict[str, Decimal] = {
            'AAPL': Decimal('150.00'),
            'TSLA': Decimal('200.00'),
            'MSFT': Decimal('300.00'),
            'GOOGL': Decimal('2500.00'),
            'AMZN': Decimal('3000.00')
        }
    
    async def start_order_simulation(self, order_id: int):
        """开始订单执行模拟"""
        if order_id in self.running_simulations:
            logger.warning(f"订单 {order_id} 的模拟已在运行")
            return
        
        task = asyncio.create_task(self._simulate_order_execution(order_id))
        self.running_simulations[order_id] = task
        
        try:
            await task
        except asyncio.CancelledError:
            logger.info(f"订单 {order_id} 的模拟被取消")
        except Exception as e:
            logger.error(f"订单 {order_id} 模拟执行失败: {str(e)}")
        finally:
            self.running_simulations.pop(order_id, None)
    
    async def stop_order_simulation(self, order_id: int):
        """停止订单执行模拟"""
        task = self.running_simulations.get(order_id)
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
    
    async def _simulate_order_execution(self, order_id: int):
        """模拟订单执行过程"""
        db = SessionLocal()
        try:
            order_service = OrderService(db)
            order = db.query(Order).filter(Order.id == order_id).first()
            
            if not order or not order.is_active:
                logger.warning(f"订单 {order_id} 不存在或不是活跃状态")
                return
            
            logger.info(f"开始模拟订单执行: {order_id}")
            
            # 模拟订单提交过程
            await self._simulate_order_submission(order, order_service)
            
            # 模拟订单执行过程
            if order.status in [OrderStatus.SUBMITTED, OrderStatus.ACCEPTED]:
                await self._simulate_order_filling(order, order_service)
            
        except Exception as e:
            logger.error(f"模拟订单执行失败: {str(e)}")
            # 发送错误通知
            if 'order' in locals():
                order_notification_service.notify_order_error(
                    order, f"模拟执行失败: {str(e)}", "SIMULATION_ERROR"
                )
        finally:
            db.close()
    
    async def _simulate_order_submission(self, order: Order, order_service: OrderService):
        """模拟订单提交过程"""
        # 等待1-3秒模拟网络延迟
        await asyncio.sleep(random.uniform(1, 3))
        
        # 更新订单状态为已提交
        old_status = order.status
        order.status = OrderStatus.SUBMITTED
        order.submitted_at = datetime.now()
        
        order_service.db.commit()
        order_service.db.refresh(order)
        
        # 发送状态变化通知
        order_notification_service.notify_order_status_change(order, old_status)
        
        # 等待1-2秒
        await asyncio.sleep(random.uniform(1, 2))
        
        # 模拟风险检查和订单接受
        risk_check_passed = random.random() > 0.1  # 90%概率通过风险检查
        
        if risk_check_passed:
            old_status = order.status
            order.status = OrderStatus.ACCEPTED
            order.accepted_at = datetime.now()
            order.risk_check_passed = True
            
            order_service.db.commit()
            order_service.db.refresh(order)
            
            order_notification_service.notify_order_status_change(order, old_status)
        else:
            # 订单被拒绝
            old_status = order.status
            order.status = OrderStatus.REJECTED
            order.risk_check_passed = False
            order.risk_check_message = "风险检查未通过"
            
            order_service.db.commit()
            order_service.db.refresh(order)
            
            order_notification_service.notify_order_rejected(order, "风险检查未通过")
            order_notification_service.notify_order_status_change(order, old_status)
    
    async def _simulate_order_filling(self, order: Order, order_service: OrderService):
        """模拟订单成交过程"""
        if order.status != OrderStatus.ACCEPTED:
            return
        
        # 获取市场价格
        market_price = self.market_prices.get(order.symbol, Decimal('100.00'))
        
        # 模拟价格波动
        price_volatility = Decimal(str(random.uniform(0.95, 1.05)))
        current_price = market_price * price_volatility
        
        # 确定成交价格
        if order.order_type == 'market':
            fill_price = current_price
        elif order.order_type == 'limit':
            if order.side == OrderSide.BUY:
                if current_price <= order.price:
                    fill_price = min(order.price, current_price)
                else:
                    # 价格不满足，等待
                    await asyncio.sleep(random.uniform(5, 15))
                    return await self._simulate_order_filling(order, order_service)
            else:  # SELL
                if current_price >= order.price:
                    fill_price = max(order.price, current_price)
                else:
                    # 价格不满足，等待
                    await asyncio.sleep(random.uniform(5, 15))
                    return await self._simulate_order_filling(order, order_service)
        else:
            fill_price = current_price
        
        # 模拟分批成交
        remaining_quantity = order.quantity - order.filled_quantity
        
        while remaining_quantity > 0 and order.status in [OrderStatus.ACCEPTED, OrderStatus.PARTIALLY_FILLED]:
            # 随机成交数量（10%-100%的剩余数量）
            fill_ratio = random.uniform(0.1, 1.0)
            fill_quantity = min(remaining_quantity, remaining_quantity * Decimal(str(fill_ratio)))
            
            # 创建成交记录
            fill_data = {
                'quantity': float(fill_quantity),
                'price': float(fill_price),
                'commission': float(fill_quantity * fill_price * Decimal('0.001')),  # 0.1%手续费
                'commission_asset': 'USD',
                'fill_time': datetime.now(),
                'liquidity': random.choice(['maker', 'taker']),
                'counterparty': f'MM_{random.randint(1, 10)}'
            }
            
            # 添加成交记录
            fill = order_service.add_order_fill(order.id, fill_data)
            
            # 更新剩余数量
            remaining_quantity = order.quantity - order.filled_quantity
            
            # 发送执行进度通知
            progress = float(order.filled_quantity / order.quantity)
            order_notification_service.notify_order_execution_progress(
                order, progress, f"已成交 {order.filled_quantity}/{order.quantity}"
            )
            
            # 如果还有剩余数量，等待一段时间再继续成交
            if remaining_quantity > 0:
                await asyncio.sleep(random.uniform(2, 8))
                
                # 模拟价格变化
                price_change = Decimal(str(random.uniform(0.98, 1.02)))
                fill_price = fill_price * price_change
        
        logger.info(f"订单 {order.id} 模拟执行完成")
    
    def update_market_price(self, symbol: str, price: Decimal):
        """更新市场价格"""
        self.market_prices[symbol] = price
        logger.info(f"更新 {symbol} 市场价格为 {price}")
    
    def get_market_price(self, symbol: str) -> Optional[Decimal]:
        """获取市场价格"""
        return self.market_prices.get(symbol)
    
    async def simulate_market_movement(self):
        """模拟市场价格波动"""
        while True:
            try:
                for symbol in self.market_prices:
                    # 随机价格变化 (-2% 到 +2%)
                    change_ratio = Decimal(str(random.uniform(0.98, 1.02)))
                    self.market_prices[symbol] *= change_ratio
                
                # 每30秒更新一次价格
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"模拟市场波动失败: {str(e)}")
                await asyncio.sleep(60)
    
    def get_simulation_status(self) -> Dict[str, Any]:
        """获取模拟器状态"""
        return {
            'running_simulations': list(self.running_simulations.keys()),
            'simulation_count': len(self.running_simulations),
            'market_prices': {k: float(v) for k, v in self.market_prices.items()},
            'timestamp': datetime.now().isoformat()
        }


# 全局订单执行模拟器实例
order_execution_simulator = OrderExecutionSimulator()


async def start_market_simulation():
    """启动市场模拟"""
    await order_execution_simulator.simulate_market_movement()


# 为OrderService添加模拟执行方法
def add_simulation_methods_to_order_service():
    """为OrderService添加模拟执行方法"""
    
    def start_simulation(self, order_id: int):
        """启动订单执行模拟"""
        asyncio.create_task(order_execution_simulator.start_order_simulation(order_id))
    
    def stop_simulation(self, order_id: int):
        """停止订单执行模拟"""
        asyncio.create_task(order_execution_simulator.stop_order_simulation(order_id))
    
    # 动态添加方法到OrderService类
    OrderService.start_simulation = start_simulation
    OrderService.stop_simulation = stop_simulation


# 初始化时添加模拟方法
add_simulation_methods_to_order_service()