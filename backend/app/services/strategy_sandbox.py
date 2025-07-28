"""
策略沙盒执行环境
"""
import ast
import sys
import io
import time
import threading
import traceback
import resource
import signal
import tempfile
import os
from contextlib import contextmanager
from typing import Dict, Any, Optional, Tuple
import logging

from ..schemas.strategy import (
    StrategySandboxRequest,
    StrategySandboxResponse,
)

logger = logging.getLogger(__name__)


class TimeoutError(Exception):
    """超时异常"""
    pass


class MemoryLimitError(Exception):
    """内存限制异常"""
    pass


class StrategySandbox:
    """策略沙盒执行环境"""
    
    def __init__(self, 
                 max_memory_mb: int = 100,
                 max_execution_time: int = 30,
                 max_output_size: int = 10000):
        self.max_memory_mb = max_memory_mb
        self.max_execution_time = max_execution_time
        self.max_output_size = max_output_size
        
        # 受限的内置函数
        self.restricted_builtins = {
            'abs', 'all', 'any', 'bin', 'bool', 'bytearray', 'bytes',
            'callable', 'chr', 'classmethod', 'complex', 'dict', 'divmod',
            'enumerate', 'filter', 'float', 'format', 'frozenset',
            'getattr', 'hasattr', 'hash', 'hex', 'id', 'int', 'isinstance',
            'issubclass', 'iter', 'len', 'list', 'map', 'max', 'min',
            'next', 'object', 'oct', 'ord', 'pow', 'print', 'property',
            'range', 'repr', 'reversed', 'round', 'set', 'setattr',
            'slice', 'sorted', 'staticmethod', 'str', 'sum', 'super',
            'tuple', 'type', 'vars', 'zip'
        }
        
        # 允许的模块
        self.allowed_modules = {
            'math', 'random', 'datetime', 'time', 'json', 'collections',
            'itertools', 'functools', 'operator', 'copy', 'decimal',
            'fractions', 'statistics', 'uuid', 're', 'string'
        }
    
    def execute(self, request: StrategySandboxRequest) -> StrategySandboxResponse:
        """执行策略代码"""
        start_time = time.time()
        
        try:
            # 验证代码安全性
            if not self._is_code_safe(request.code):
                return StrategySandboxResponse(
                    success=False,
                    output="",
                    error="代码包含不安全的操作",
                    execution_time=0.0,
                    memory_usage=0.0
                )
            
            # 在沙盒中执行代码
            output, error, memory_usage = self._execute_in_sandbox(
                request.code, 
                request.test_data or {},
                request.timeout
            )
            
            execution_time = time.time() - start_time
            
            return StrategySandboxResponse(
                success=error == "",
                output=output[:self.max_output_size],
                error=error,
                execution_time=execution_time,
                memory_usage=memory_usage
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"沙盒执行失败: {e}")
            
            return StrategySandboxResponse(
                success=False,
                output="",
                error=f"执行失败: {str(e)}",
                execution_time=execution_time,
                memory_usage=0.0
            )
    
    def _is_code_safe(self, code: str) -> bool:
        """检查代码是否安全"""
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                # 检查危险的函数调用
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in ['eval', 'exec', 'compile', '__import__', 'open', 'file']:
                            return False
                    elif isinstance(node.func, ast.Attribute):
                        if node.func.attr in ['system', 'popen', 'spawn']:
                            return False
                
                # 检查危险的模块导入
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        module_name = alias.name.split('.')[0]
                        if module_name not in self.allowed_modules:
                            return False
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        module_name = node.module.split('.')[0]
                        if module_name not in self.allowed_modules:
                            return False
                
                # 检查属性访问
                elif isinstance(node, ast.Attribute):
                    if node.attr.startswith('_'):
                        return False
            
            return True
            
        except SyntaxError:
            return False
    
    def _execute_in_sandbox(self, code: str, test_data: Dict[str, Any], timeout: int) -> Tuple[str, str, float]:
        """在沙盒中执行代码"""
        # 创建受限的全局环境
        restricted_globals = {
            '__builtins__': {name: getattr(__builtins__, name) for name in self.restricted_builtins if hasattr(__builtins__, name)},
            '__name__': '__main__',
            '__doc__': None,
        }
        
        # 添加允许的模块
        for module_name in self.allowed_modules:
            try:
                restricted_globals[module_name] = __import__(module_name)
            except ImportError:
                pass
        
        # 添加测试数据
        restricted_globals.update(test_data)
        
        # 创建模拟的策略上下文
        context = MockStrategyContext(test_data)
        restricted_globals['context'] = context
        
        # 捕获输出
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        output = ""
        error = ""
        memory_usage = 0.0
        
        try:
            sys.stdout = stdout_capture
            sys.stderr = stderr_capture
            
            # 设置内存限制
            if hasattr(resource, 'RLIMIT_AS'):
                resource.setrlimit(resource.RLIMIT_AS, (self.max_memory_mb * 1024 * 1024, -1))
            
            # 使用线程执行代码以支持超时
            result = {'exception': None}
            
            def execute_code():
                try:
                    exec(code, restricted_globals)
                except Exception as e:
                    result['exception'] = e
            
            thread = threading.Thread(target=execute_code)
            thread.daemon = True
            thread.start()
            thread.join(timeout)
            
            if thread.is_alive():
                # 超时处理
                error = f"执行超时 ({timeout}秒)"
            elif result['exception']:
                error = str(result['exception'])
            else:
                output = stdout_capture.getvalue()
                if stderr_capture.getvalue():
                    error = stderr_capture.getvalue()
            
            # 获取内存使用情况
            try:
                memory_usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024  # KB to MB
            except:
                memory_usage = 0.0
            
        except MemoryError:
            error = f"内存使用超过限制 ({self.max_memory_mb}MB)"
        except Exception as e:
            error = f"执行错误: {str(e)}"
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
        
        return output, error, memory_usage


class MockStrategyContext:
    """模拟策略上下文"""
    
    def __init__(self, test_data: Dict[str, Any]):
        self.test_data = test_data
        self.params = test_data.get('params', {})
        self.positions = {}
        self.orders = []
        self.portfolio_value = 1000000.0  # 初始资金100万
        self.current_bar = None
        
        # 模拟市场数据
        self.market_data = {
            'SHFE.cu2401': {
                'last_price': 70000.0,
                'bid_price': 69990.0,
                'ask_price': 70010.0,
                'volume': 1000,
                'open_interest': 50000
            }
        }
    
    def get_klines(self, symbol: str, count: int = 100):
        """获取K线数据（模拟）"""
        # 生成模拟K线数据
        import random
        base_price = 70000.0
        klines = []
        
        for i in range(count):
            # 简单的随机游走
            change = random.uniform(-0.02, 0.02)
            base_price *= (1 + change)
            
            kline = MockKline(
                open=base_price * random.uniform(0.998, 1.002),
                high=base_price * random.uniform(1.001, 1.005),
                low=base_price * random.uniform(0.995, 0.999),
                close=base_price,
                volume=random.randint(100, 1000),
                datetime=f"2024-01-{i+1:02d} 09:00:00"
            )
            klines.append(kline)
        
        return klines
    
    def get_quote(self, symbol: str):
        """获取行情数据（模拟）"""
        return self.market_data.get(symbol, {})
    
    def order_target_percent(self, symbol: str, percent: float):
        """按百分比下单（模拟）"""
        target_value = self.portfolio_value * percent
        current_price = self.market_data.get(symbol, {}).get('last_price', 70000.0)
        
        if current_price > 0:
            target_quantity = int(target_value / current_price)
            current_quantity = self.positions.get(symbol, 0)
            
            if target_quantity != current_quantity:
                order_quantity = target_quantity - current_quantity
                
                order = {
                    'symbol': symbol,
                    'quantity': order_quantity,
                    'price': current_price,
                    'type': 'market',
                    'status': 'filled'
                }
                
                self.orders.append(order)
                self.positions[symbol] = target_quantity
                
                print(f"下单: {symbol}, 数量: {order_quantity}, 价格: {current_price}")
    
    def order_target_value(self, symbol: str, value: float):
        """按金额下单（模拟）"""
        percent = value / self.portfolio_value
        self.order_target_percent(symbol, percent)
    
    def get_position(self, symbol: str):
        """获取持仓（模拟）"""
        return self.positions.get(symbol, 0)
    
    def get_portfolio_value(self):
        """获取组合价值（模拟）"""
        return self.portfolio_value
    
    def log(self, message: str):
        """记录日志"""
        print(f"[LOG] {message}")


class MockKline:
    """模拟K线数据"""
    
    def __init__(self, open, high, low, close, volume, datetime):
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume
        self.datetime = datetime
    
    def __repr__(self):
        return f"Kline(open={self.open}, high={self.high}, low={self.low}, close={self.close}, volume={self.volume})"


@contextmanager
def timeout_context(seconds):
    """超时上下文管理器"""
    def timeout_handler(signum, frame):
        raise TimeoutError(f"操作超时 ({seconds}秒)")
    
    # 设置信号处理器
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)