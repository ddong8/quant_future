"""
交易系统适配器
用于对接不同的交易系统和券商接口
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
from decimal import Decimal
from enum import Enum

from ..models.order import Order, OrderFill, OrderStatus, OrderSide, OrderType

logger = logging.getLogger(__name__)


class TradingSystemType(Enum):
    """交易系统类型"""
    MOCK = "mock"           # 模拟交易系统
    IB = "interactive_brokers"  # 盈透证券
    ALPACA = "alpaca"       # Alpaca
    TD_AMERITRADE = "td_ameritrade"  # TD Ameritrade
    BINANCE = "binance"     # 币安
    CUSTOM = "custom"       # 自定义接口


class OrderSubmissionResult:
    """订单提交结果"""
    
    def __init__(self, success: bool, external_order_id: str = None, 
                 message: str = "", error_code: str = ""):
        self.success = success
        self.external_order_id = external_order_id
        self.message = message
        self.error_code = error_code


class TradingSystemAdapter(ABC):
    """交易系统适配器基类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.is_connected = False
        self.connection_info = {}
    
    @abstractmethod
    async def connect(self) -> bool:
        """连接到交易系统"""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """断开连接"""
        pass
    
    @abstractmethod
    async def submit_order(self, order: Order) -> OrderSubmissionResult:
        """提交订单"""
        pass
    
    @abstractmethod
    async def cancel_order(self, order: Order) -> bool:
        """取消订单"""
        pass
    
    @abstractmethod
    async def modify_order(self, order: Order, modifications: Dict[str, Any]) -> bool:
        """修改订单"""
        pass
    
    @abstractmethod
    async def get_order_status(self, external_order_id: str) -> Optional[Dict[str, Any]]:
        """获取订单状态"""
        pass
    
    @abstractmethod
    async def get_account_info(self) -> Dict[str, Any]:
        """获取账户信息"""
        pass
    
    @abstractmethod
    async def get_positions(self) -> List[Dict[str, Any]]:
        """获取持仓信息"""
        pass
    
    @abstractmethod
    async def get_market_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取市场数据"""
        pass


class MockTradingSystemAdapter(TradingSystemAdapter):
    """模拟交易系统适配器"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.orders: Dict[str, Dict[str, Any]] = {}
        self.positions: Dict[str, Dict[str, Any]] = {}
        self.account_balance = Decimal('1000000')  # 100万模拟资金
        
    async def connect(self) -> bool:
        """连接到模拟交易系统"""
        try:
            logger.info("连接到模拟交易系统")
            self.is_connected = True
            self.connection_info = {
                'system_type': 'mock',
                'connected_at': datetime.now().isoformat(),
                'account_id': 'MOCK_ACCOUNT_001'
            }
            return True
        except Exception as e:
            logger.error(f"连接模拟交易系统失败: {str(e)}")
            return False
    
    async def disconnect(self):
        """断开连接"""
        logger.info("断开模拟交易系统连接")
        self.is_connected = False
        self.connection_info = {}
    
    async def submit_order(self, order: Order) -> OrderSubmissionResult:
        """提交订单到模拟系统"""
        try:
            if not self.is_connected:
                return OrderSubmissionResult(
                    False, message="未连接到交易系统", error_code="NOT_CONNECTED"
                )
            
            # 生成外部订单ID
            external_order_id = f"MOCK_{order.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # 模拟订单验证
            validation_result = await self._validate_order(order)
            if not validation_result['valid']:
                return OrderSubmissionResult(
                    False, message=validation_result['message'], 
                    error_code=validation_result['error_code']
                )
            
            # 存储订单信息
            self.orders[external_order_id] = {
                'internal_order_id': order.id,
                'symbol': order.symbol,
                'side': order.side,
                'order_type': order.order_type,
                'quantity': float(order.quantity),
                'price': float(order.price) if order.price else None,
                'status': 'submitted',
                'filled_quantity': 0,
                'submitted_at': datetime.now().isoformat()
            }
            
            logger.info(f"模拟系统接受订单: {external_order_id}")
            
            return OrderSubmissionResult(
                True, external_order_id=external_order_id, 
                message="订单提交成功"
            )
            
        except Exception as e:
            logger.error(f"提交订单到模拟系统失败: {str(e)}")
            return OrderSubmissionResult(
                False, message=f"提交失败: {str(e)}", error_code="SUBMISSION_ERROR"
            )
    
    async def cancel_order(self, order: Order) -> bool:
        """取消模拟订单"""
        try:
            external_order_id = order.order_id_external
            if not external_order_id or external_order_id not in self.orders:
                logger.warning(f"未找到外部订单ID: {external_order_id}")
                return False
            
            order_info = self.orders[external_order_id]
            if order_info['status'] in ['filled', 'cancelled']:
                logger.warning(f"订单已结束，无法取消: {external_order_id}")
                return False
            
            # 更新订单状态
            order_info['status'] = 'cancelled'
            order_info['cancelled_at'] = datetime.now().isoformat()
            
            logger.info(f"模拟系统取消订单: {external_order_id}")
            return True
            
        except Exception as e:
            logger.error(f"取消模拟订单失败: {str(e)}")
            return False
    
    async def modify_order(self, order: Order, modifications: Dict[str, Any]) -> bool:
        """修改模拟订单"""
        try:
            external_order_id = order.order_id_external
            if not external_order_id or external_order_id not in self.orders:
                return False
            
            order_info = self.orders[external_order_id]
            if order_info['status'] not in ['submitted', 'accepted']:
                return False
            
            # 应用修改
            for field, value in modifications.items():
                if field in order_info:
                    order_info[field] = value
            
            order_info['modified_at'] = datetime.now().isoformat()
            
            logger.info(f"模拟系统修改订单: {external_order_id}")
            return True
            
        except Exception as e:
            logger.error(f"修改模拟订单失败: {str(e)}")
            return False
    
    async def get_order_status(self, external_order_id: str) -> Optional[Dict[str, Any]]:
        """获取模拟订单状态"""
        return self.orders.get(external_order_id)
    
    async def get_account_info(self) -> Dict[str, Any]:
        """获取模拟账户信息"""
        return {
            'account_id': 'MOCK_ACCOUNT_001',
            'account_type': 'demo',
            'currency': 'USD',
            'balance': float(self.account_balance),
            'available_funds': float(self.account_balance * Decimal('0.9')),
            'buying_power': float(self.account_balance * Decimal('2.0')),
            'positions_value': sum(
                pos['quantity'] * pos['current_price'] 
                for pos in self.positions.values()
            ),
            'unrealized_pnl': sum(
                pos['unrealized_pnl'] for pos in self.positions.values()
            ),
            'last_updated': datetime.now().isoformat()
        }
    
    async def get_positions(self) -> List[Dict[str, Any]]:
        """获取模拟持仓信息"""
        return list(self.positions.values())
    
    async def get_market_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取模拟市场数据"""
        # 模拟市场数据
        mock_prices = {
            'AAPL': 150.00,
            'TSLA': 200.00,
            'MSFT': 300.00,
            'GOOGL': 2500.00,
            'AMZN': 3000.00
        }
        
        base_price = mock_prices.get(symbol, 100.00)
        
        # 添加随机波动
        import random
        current_price = base_price * random.uniform(0.98, 1.02)
        
        return {
            'symbol': symbol,
            'price': current_price,
            'bid': current_price * 0.999,
            'ask': current_price * 1.001,
            'volume': random.randint(1000, 10000),
            'timestamp': datetime.now().isoformat()
        }
    
    async def _validate_order(self, order: Order) -> Dict[str, Any]:
        """验证订单"""
        try:
            # 检查标的是否支持
            supported_symbols = ['AAPL', 'TSLA', 'MSFT', 'GOOGL', 'AMZN']
            if order.symbol not in supported_symbols:
                return {
                    'valid': False,
                    'message': f'不支持的交易标的: {order.symbol}',
                    'error_code': 'UNSUPPORTED_SYMBOL'
                }
            
            # 检查数量
            if order.quantity <= 0:
                return {
                    'valid': False,
                    'message': '订单数量必须大于0',
                    'error_code': 'INVALID_QUANTITY'
                }
            
            # 检查价格
            if order.order_type in [OrderType.LIMIT, OrderType.STOP_LIMIT] and not order.price:
                return {
                    'valid': False,
                    'message': '限价单必须指定价格',
                    'error_code': 'MISSING_PRICE'
                }
            
            # 检查资金充足性（买单）
            if order.side == OrderSide.BUY and order.price:
                required_funds = order.quantity * order.price
                if required_funds > self.account_balance:
                    return {
                        'valid': False,
                        'message': '资金不足',
                        'error_code': 'INSUFFICIENT_FUNDS'
                    }
            
            return {'valid': True, 'message': '验证通过'}
            
        except Exception as e:
            return {
                'valid': False,
                'message': f'验证失败: {str(e)}',
                'error_code': 'VALIDATION_ERROR'
            }


class InteractiveBrokersAdapter(TradingSystemAdapter):
    """盈透证券适配器"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        # 这里可以初始化IB API连接
    
    async def connect(self) -> bool:
        """连接到IB"""
        # 实现IB连接逻辑
        logger.info("连接到Interactive Brokers")
        # 这里应该实现真实的IB API连接
        return False  # 暂未实现
    
    async def disconnect(self):
        """断开IB连接"""
        pass
    
    async def submit_order(self, order: Order) -> OrderSubmissionResult:
        """提交订单到IB"""
        # 实现IB订单提交逻辑
        return OrderSubmissionResult(False, message="IB适配器暂未实现")
    
    async def cancel_order(self, order: Order) -> bool:
        """取消IB订单"""
        return False
    
    async def modify_order(self, order: Order, modifications: Dict[str, Any]) -> bool:
        """修改IB订单"""
        return False
    
    async def get_order_status(self, external_order_id: str) -> Optional[Dict[str, Any]]:
        """获取IB订单状态"""
        return None
    
    async def get_account_info(self) -> Dict[str, Any]:
        """获取IB账户信息"""
        return {}
    
    async def get_positions(self) -> List[Dict[str, Any]]:
        """获取IB持仓信息"""
        return []
    
    async def get_market_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取IB市场数据"""
        return None


class TradingSystemManager:
    """交易系统管理器"""
    
    def __init__(self):
        self.adapters: Dict[str, TradingSystemAdapter] = {}
        self.default_adapter: Optional[TradingSystemAdapter] = None
    
    def register_adapter(self, system_type: TradingSystemType, 
                        adapter: TradingSystemAdapter, is_default: bool = False):
        """注册交易系统适配器"""
        self.adapters[system_type.value] = adapter
        if is_default:
            self.default_adapter = adapter
        logger.info(f"注册交易系统适配器: {system_type.value}")
    
    def get_adapter(self, system_type: str = None) -> Optional[TradingSystemAdapter]:
        """获取交易系统适配器"""
        if system_type:
            return self.adapters.get(system_type)
        return self.default_adapter
    
    async def connect_all(self):
        """连接所有交易系统"""
        for system_type, adapter in self.adapters.items():
            try:
                success = await adapter.connect()
                if success:
                    logger.info(f"成功连接到交易系统: {system_type}")
                else:
                    logger.warning(f"连接交易系统失败: {system_type}")
            except Exception as e:
                logger.error(f"连接交易系统异常: {system_type} - {str(e)}")
    
    async def disconnect_all(self):
        """断开所有交易系统连接"""
        for system_type, adapter in self.adapters.items():
            try:
                await adapter.disconnect()
                logger.info(f"断开交易系统连接: {system_type}")
            except Exception as e:
                logger.error(f"断开交易系统连接异常: {system_type} - {str(e)}")
    
    def get_connection_status(self) -> Dict[str, Any]:
        """获取所有交易系统连接状态"""
        status = {}
        for system_type, adapter in self.adapters.items():
            status[system_type] = {
                'connected': adapter.is_connected,
                'connection_info': adapter.connection_info
            }
        return status


# 全局交易系统管理器
trading_system_manager = TradingSystemManager()

# 注册默认的模拟交易系统
mock_adapter = MockTradingSystemAdapter({})
trading_system_manager.register_adapter(
    TradingSystemType.MOCK, mock_adapter, is_default=True
)