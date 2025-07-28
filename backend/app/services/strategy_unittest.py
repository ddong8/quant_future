"""
策略单元测试框架
"""
import unittest
import sys
import io
import traceback
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
import logging

from ..schemas.strategy import StrategyTestResponse

logger = logging.getLogger(__name__)


class StrategyTestCase:
    """策略测试用例"""
    
    def __init__(self, name: str, description: str, test_func: Callable, expected_result: Any = None):
        self.name = name
        self.description = description
        self.test_func = test_func
        self.expected_result = expected_result
        self.result = None
        self.success = False
        self.error = None
        self.execution_time = 0.0


class StrategyUnitTestFramework:
    """策略单元测试框架"""
    
    def __init__(self):
        self.test_cases = []
        self.setup_func = None
        self.teardown_func = None
        self.context = None
    
    def add_test_case(self, name: str, description: str, test_func: Callable, expected_result: Any = None):
        """添加测试用例"""
        test_case = StrategyTestCase(name, description, test_func, expected_result)
        self.test_cases.append(test_case)
    
    def set_setup(self, setup_func: Callable):
        """设置测试前置函数"""
        self.setup_func = setup_func
    
    def set_teardown(self, teardown_func: Callable):
        """设置测试后置函数"""
        self.teardown_func = teardown_func
    
    def run_tests(self, strategy_code: str, test_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """运行所有测试用例"""
        results = {
            'total_tests': len(self.test_cases),
            'passed_tests': 0,
            'failed_tests': 0,
            'test_results': [],
            'overall_success': False,
            'execution_time': 0.0,
            'summary': ''
        }
        
        start_time = datetime.utcnow()
        
        try:
            # 执行策略代码以获取函数定义
            strategy_globals = self._execute_strategy_code(strategy_code, test_data or {})
            
            # 运行每个测试用例
            for test_case in self.test_cases:
                test_result = self._run_single_test(test_case, strategy_globals)
                results['test_results'].append(test_result)
                
                if test_result['success']:
                    results['passed_tests'] += 1
                else:
                    results['failed_tests'] += 1
            
            # 计算总体结果
            results['overall_success'] = results['failed_tests'] == 0
            results['execution_time'] = (datetime.utcnow() - start_time).total_seconds()
            
            # 生成摘要
            results['summary'] = self._generate_test_summary(results)
            
        except Exception as e:
            logger.error(f"测试框架执行失败: {e}")
            results['summary'] = f"测试框架执行失败: {str(e)}"
        
        return results
    
    def _execute_strategy_code(self, strategy_code: str, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行策略代码获取函数定义"""
        strategy_globals = {
            '__builtins__': __builtins__,
            '__name__': '__main__',
            'test_data': test_data,
        }
        
        # 添加常用模块
        import math
        import random
        import datetime
        import json
        
        strategy_globals.update({
            'math': math,
            'random': random,
            'datetime': datetime,
            'json': json,
        })
        
        # 创建模拟上下文
        context = MockTestContext(test_data)
        strategy_globals['context'] = context
        self.context = context
        
        try:
            exec(strategy_code, strategy_globals)
        except Exception as e:
            raise Exception(f"策略代码执行失败: {str(e)}")
        
        return strategy_globals
    
    def _run_single_test(self, test_case: StrategyTestCase, strategy_globals: Dict[str, Any]) -> Dict[str, Any]:
        """运行单个测试用例"""
        start_time = datetime.utcnow()
        
        result = {
            'name': test_case.name,
            'description': test_case.description,
            'success': False,
            'result': None,
            'expected': test_case.expected_result,
            'error': None,
            'execution_time': 0.0,
            'output': ''
        }
        
        # 捕获输出
        old_stdout = sys.stdout
        stdout_capture = io.StringIO()
        
        try:
            sys.stdout = stdout_capture
            
            # 执行前置函数
            if self.setup_func:
                self.setup_func(self.context)
            
            # 执行测试函数
            test_result = test_case.test_func(strategy_globals, self.context)
            
            # 执行后置函数
            if self.teardown_func:
                self.teardown_func(self.context)
            
            result['result'] = test_result
            result['output'] = stdout_capture.getvalue()
            
            # 检查结果
            if test_case.expected_result is not None:
                result['success'] = test_result == test_case.expected_result
            else:
                result['success'] = test_result is not None and test_result != False
            
        except Exception as e:
            result['error'] = str(e)
            result['success'] = False
            
        finally:
            sys.stdout = old_stdout
            result['execution_time'] = (datetime.utcnow() - start_time).total_seconds()
        
        return result
    
    def _generate_test_summary(self, results: Dict[str, Any]) -> str:
        """生成测试摘要"""
        total = results['total_tests']
        passed = results['passed_tests']
        failed = results['failed_tests']
        
        summary = f"测试完成: 总计 {total} 个测试用例, 通过 {passed} 个, 失败 {failed} 个"
        
        if failed > 0:
            summary += f"\n失败的测试用例:"
            for test_result in results['test_results']:
                if not test_result['success']:
                    summary += f"\n- {test_result['name']}: {test_result['error'] or '结果不匹配'}"
        
        return summary


class MockTestContext:
    """模拟测试上下文"""
    
    def __init__(self, test_data: Dict[str, Any]):
        self.test_data = test_data
        self.params = test_data.get('params', {})
        self.positions = {}
        self.orders = []
        self.portfolio_value = test_data.get('initial_capital', 1000000.0)
        self.current_bar = None
        self.bars_data = []
        
        # 模拟市场数据
        self.market_data = test_data.get('market_data', {
            'SHFE.cu2401': {
                'last_price': 70000.0,
                'bid_price': 69990.0,
                'ask_price': 70010.0,
                'volume': 1000,
                'open_interest': 50000
            }
        })
    
    def get_klines(self, symbol: str, count: int = 100):
        """获取K线数据（模拟）"""
        if 'klines_data' in self.test_data:
            return self.test_data['klines_data'][:count]
        
        # 生成模拟数据
        import random
        base_price = 70000.0
        klines = []
        
        for i in range(count):
            change = random.uniform(-0.02, 0.02)
            base_price *= (1 + change)
            
            kline = {
                'open': base_price * random.uniform(0.998, 1.002),
                'high': base_price * random.uniform(1.001, 1.005),
                'low': base_price * random.uniform(0.995, 0.999),
                'close': base_price,
                'volume': random.randint(100, 1000),
                'datetime': f"2024-01-{i+1:02d} 09:00:00"
            }
            klines.append(kline)
        
        return klines
    
    def order_target_percent(self, symbol: str, percent: float):
        """按百分比下单"""
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
                
                return order
        
        return None
    
    def get_position(self, symbol: str):
        """获取持仓"""
        return self.positions.get(symbol, 0)
    
    def get_portfolio_value(self):
        """获取组合价值"""
        return self.portfolio_value
    
    def reset(self):
        """重置上下文"""
        self.positions = {}
        self.orders = []
        self.portfolio_value = self.test_data.get('initial_capital', 1000000.0)


def create_basic_strategy_tests() -> StrategyUnitTestFramework:
    """创建基础策略测试用例"""
    framework = StrategyUnitTestFramework()
    
    # 测试用例1: 检查initialize函数是否存在
    def test_initialize_exists(strategy_globals, context):
        return 'initialize' in strategy_globals and callable(strategy_globals['initialize'])
    
    framework.add_test_case(
        "initialize_function_exists",
        "检查initialize函数是否存在",
        test_initialize_exists,
        True
    )
    
    # 测试用例2: 检查handle_bar函数是否存在
    def test_handle_bar_exists(strategy_globals, context):
        return 'handle_bar' in strategy_globals and callable(strategy_globals['handle_bar'])
    
    framework.add_test_case(
        "handle_bar_function_exists",
        "检查handle_bar函数是否存在",
        test_handle_bar_exists,
        True
    )
    
    # 测试用例3: 测试initialize函数调用
    def test_initialize_call(strategy_globals, context):
        if 'initialize' in strategy_globals:
            try:
                strategy_globals['initialize'](context)
                return True
            except Exception as e:
                raise Exception(f"initialize函数调用失败: {str(e)}")
        return False
    
    framework.add_test_case(
        "initialize_function_call",
        "测试initialize函数调用",
        test_initialize_call,
        True
    )
    
    # 测试用例4: 测试handle_bar函数调用
    def test_handle_bar_call(strategy_globals, context):
        if 'handle_bar' in strategy_globals:
            try:
                # 模拟bar数据
                bar_dict = {
                    'SHFE.cu2401': {
                        'open': 70000.0,
                        'high': 70100.0,
                        'low': 69900.0,
                        'close': 70050.0,
                        'volume': 1000
                    }
                }
                strategy_globals['handle_bar'](context, bar_dict)
                return True
            except Exception as e:
                raise Exception(f"handle_bar函数调用失败: {str(e)}")
        return False
    
    framework.add_test_case(
        "handle_bar_function_call",
        "测试handle_bar函数调用",
        test_handle_bar_call,
        True
    )
    
    # 测试用例5: 测试策略参数访问
    def test_params_access(strategy_globals, context):
        if 'initialize' in strategy_globals:
            try:
                strategy_globals['initialize'](context)
                # 检查是否能访问参数
                return hasattr(context, 'params')
            except:
                return False
        return False
    
    framework.add_test_case(
        "params_access",
        "测试策略参数访问",
        test_params_access,
        True
    )
    
    return framework


def create_trading_logic_tests() -> StrategyUnitTestFramework:
    """创建交易逻辑测试用例"""
    framework = StrategyUnitTestFramework()
    
    # 测试用例1: 测试买入逻辑
    def test_buy_logic(strategy_globals, context):
        if 'initialize' in strategy_globals and 'handle_bar' in strategy_globals:
            try:
                # 初始化
                strategy_globals['initialize'](context)
                
                # 模拟上涨行情
                bar_dict = {
                    'SHFE.cu2401': {
                        'open': 70000.0,
                        'high': 71000.0,
                        'low': 70000.0,
                        'close': 70800.0,
                        'volume': 1000
                    }
                }
                
                initial_position = context.get_position('SHFE.cu2401')
                strategy_globals['handle_bar'](context, bar_dict)
                final_position = context.get_position('SHFE.cu2401')
                
                # 检查是否有买入行为
                return final_position > initial_position
                
            except Exception as e:
                raise Exception(f"买入逻辑测试失败: {str(e)}")
        return False
    
    framework.add_test_case(
        "buy_logic_test",
        "测试买入逻辑",
        test_buy_logic
    )
    
    # 测试用例2: 测试卖出逻辑
    def test_sell_logic(strategy_globals, context):
        if 'initialize' in strategy_globals and 'handle_bar' in strategy_globals:
            try:
                # 初始化
                strategy_globals['initialize'](context)
                
                # 先建立多头仓位
                context.order_target_percent('SHFE.cu2401', 0.5)
                
                # 模拟下跌行情
                bar_dict = {
                    'SHFE.cu2401': {
                        'open': 70000.0,
                        'high': 70000.0,
                        'low': 69000.0,
                        'close': 69200.0,
                        'volume': 1000
                    }
                }
                
                initial_position = context.get_position('SHFE.cu2401')
                strategy_globals['handle_bar'](context, bar_dict)
                final_position = context.get_position('SHFE.cu2401')
                
                # 检查是否有卖出行为
                return final_position < initial_position
                
            except Exception as e:
                raise Exception(f"卖出逻辑测试失败: {str(e)}")
        return False
    
    framework.add_test_case(
        "sell_logic_test",
        "测试卖出逻辑",
        test_sell_logic
    )
    
    return framework


def run_strategy_unit_tests(strategy_code: str, test_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """运行策略单元测试"""
    all_results = {
        'basic_tests': {},
        'trading_tests': {},
        'overall_success': False,
        'total_tests': 0,
        'passed_tests': 0,
        'failed_tests': 0,
        'summary': ''
    }
    
    try:
        # 运行基础测试
        basic_framework = create_basic_strategy_tests()
        basic_results = basic_framework.run_tests(strategy_code, test_data)
        all_results['basic_tests'] = basic_results
        
        # 运行交易逻辑测试
        trading_framework = create_trading_logic_tests()
        trading_results = trading_framework.run_tests(strategy_code, test_data)
        all_results['trading_tests'] = trading_results
        
        # 汇总结果
        all_results['total_tests'] = basic_results['total_tests'] + trading_results['total_tests']
        all_results['passed_tests'] = basic_results['passed_tests'] + trading_results['passed_tests']
        all_results['failed_tests'] = basic_results['failed_tests'] + trading_results['failed_tests']
        all_results['overall_success'] = all_results['failed_tests'] == 0
        
        # 生成总体摘要
        all_results['summary'] = f"""
单元测试完成:
- 基础测试: {basic_results['passed_tests']}/{basic_results['total_tests']} 通过
- 交易测试: {trading_results['passed_tests']}/{trading_results['total_tests']} 通过
- 总体结果: {'通过' if all_results['overall_success'] else '失败'}
"""
        
    except Exception as e:
        logger.error(f"单元测试执行失败: {e}")
        all_results['summary'] = f"单元测试执行失败: {str(e)}"
    
    return all_results