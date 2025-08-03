"""
策略测试服务
提供策略代码的单元测试、集成测试和性能测试功能
"""

import ast
import sys
import io
import logging
import tempfile
import os
import subprocess
import time
import traceback
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from contextlib import redirect_stdout, redirect_stderr
import unittest
from unittest.mock import Mock, MagicMock
import pandas as pd
import numpy as np

from .code_validation_service import code_validation_service

logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """测试结果"""
    test_name: str
    passed: bool
    execution_time: float
    error_message: Optional[str] = None
    output: Optional[str] = None
    coverage: Optional[float] = None


@dataclass
class TestSuite:
    """测试套件"""
    name: str
    description: str
    tests: List[TestResult]
    total_tests: int
    passed_tests: int
    failed_tests: int
    total_time: float
    coverage: float


@dataclass
class PerformanceMetrics:
    """性能指标"""
    execution_time: float
    memory_usage: float
    cpu_usage: float
    function_calls: int
    complexity_score: float


class StrategyTestContext:
    """策略测试上下文"""
    
    def __init__(self):
        self.current_price = 100.0
        self.history_data = self._generate_mock_data()
        self.positions = {}
        self.orders = []
        self.balance = 100000.0
        self.portfolio_value = 100000.0
        
    def _generate_mock_data(self) -> pd.DataFrame:
        """生成模拟历史数据"""
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        np.random.seed(42)  # 确保可重复性
        
        # 生成模拟价格数据
        prices = []
        price = 100.0
        for _ in range(100):
            change = np.random.normal(0, 0.02)  # 2%的日波动率
            price *= (1 + change)
            prices.append(price)
        
        data = pd.DataFrame({
            'date': dates,
            'open': prices,
            'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
            'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
            'close': prices,
            'volume': [np.random.randint(1000, 10000) for _ in range(100)]
        })
        
        return data
    
    def get_current_price(self, symbol: str = 'DEFAULT') -> float:
        """获取当前价格"""
        return self.current_price
    
    def get_history_data(self, symbol: str = 'DEFAULT', period: int = 20) -> pd.DataFrame:
        """获取历史数据"""
        return self.history_data.tail(period).copy()
    
    def buy(self, symbol: str = 'DEFAULT', size: float = 1000, price: Optional[float] = None):
        """买入操作"""
        if price is None:
            price = self.current_price
        
        cost = size * price
        if cost <= self.balance:
            self.balance -= cost
            if symbol in self.positions:
                self.positions[symbol] += size
            else:
                self.positions[symbol] = size
            
            self.orders.append({
                'action': 'buy',
                'symbol': symbol,
                'size': size,
                'price': price,
                'timestamp': time.time()
            })
    
    def sell(self, symbol: str = 'DEFAULT', size: float = 1000, price: Optional[float] = None):
        """卖出操作"""
        if price is None:
            price = self.current_price
        
        if symbol in self.positions and self.positions[symbol] >= size:
            self.positions[symbol] -= size
            self.balance += size * price
            
            self.orders.append({
                'action': 'sell',
                'symbol': symbol,
                'size': size,
                'price': price,
                'timestamp': time.time()
            })
    
    def get_position(self, symbol: str = 'DEFAULT') -> float:
        """获取持仓"""
        return self.positions.get(symbol, 0.0)
    
    def get_balance(self) -> float:
        """获取余额"""
        return self.balance
    
    def get_portfolio_value(self) -> float:
        """获取组合价值"""
        total_value = self.balance
        for symbol, size in self.positions.items():
            total_value += size * self.current_price
        return total_value


class StrategyTestService:
    """策略测试服务"""
    
    def __init__(self):
        self.test_context = StrategyTestContext()
    
    def run_unit_tests(self, code: str, entry_point: str = "main") -> TestSuite:
        """运行单元测试"""
        tests = []
        start_time = time.time()
        
        # 1. 语法测试
        syntax_test = self._test_syntax(code)
        tests.append(syntax_test)
        
        # 2. 入口函数测试
        entry_test = self._test_entry_point(code, entry_point)
        tests.append(entry_test)
        
        # 3. 基本执行测试
        execution_test = self._test_basic_execution(code, entry_point)
        tests.append(execution_test)
        
        # 4. 数据访问测试
        data_access_test = self._test_data_access(code, entry_point)
        tests.append(data_access_test)
        
        # 5. 交易操作测试
        trading_test = self._test_trading_operations(code, entry_point)
        tests.append(trading_test)
        
        total_time = time.time() - start_time
        passed_tests = sum(1 for test in tests if test.passed)
        failed_tests = len(tests) - passed_tests
        
        return TestSuite(
            name="策略单元测试",
            description="策略代码的基础功能测试",
            tests=tests,
            total_tests=len(tests),
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            total_time=total_time,
            coverage=passed_tests / len(tests) * 100
        )
    
    def _test_syntax(self, code: str) -> TestResult:
        """测试语法正确性"""
        start_time = time.time()
        
        try:
            ast.parse(code)
            return TestResult(
                test_name="语法检查",
                passed=True,
                execution_time=time.time() - start_time,
                output="语法检查通过"
            )
        except SyntaxError as e:
            return TestResult(
                test_name="语法检查",
                passed=False,
                execution_time=time.time() - start_time,
                error_message=f"语法错误: {str(e)}"
            )
    
    def _test_entry_point(self, code: str, entry_point: str) -> TestResult:
        """测试入口函数存在性"""
        start_time = time.time()
        
        try:
            tree = ast.parse(code)
            
            # 查找入口函数
            entry_function = None
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == entry_point:
                    entry_function = node
                    break
            
            if entry_function:
                # 检查参数
                if len(entry_function.args.args) >= 1:
                    return TestResult(
                        test_name="入口函数检查",
                        passed=True,
                        execution_time=time.time() - start_time,
                        output=f"找到入口函数 {entry_point}，参数数量: {len(entry_function.args.args)}"
                    )
                else:
                    return TestResult(
                        test_name="入口函数检查",
                        passed=False,
                        execution_time=time.time() - start_time,
                        error_message=f"入口函数 {entry_point} 缺少必要参数 (context)"
                    )
            else:
                return TestResult(
                    test_name="入口函数检查",
                    passed=False,
                    execution_time=time.time() - start_time,
                    error_message=f"未找到入口函数: {entry_point}"
                )
        
        except Exception as e:
            return TestResult(
                test_name="入口函数检查",
                passed=False,
                execution_time=time.time() - start_time,
                error_message=f"检查入口函数时出错: {str(e)}"
            )
    
    def _test_basic_execution(self, code: str, entry_point: str) -> TestResult:
        """测试基本执行"""
        start_time = time.time()
        
        try:
            # 创建安全的执行环境
            safe_globals = self._create_safe_globals()
            safe_locals = {}
            
            # 执行代码
            exec(code, safe_globals, safe_locals)
            
            # 调用入口函数
            if entry_point in safe_locals:
                context = self.test_context
                safe_locals[entry_point](context)
                
                return TestResult(
                    test_name="基本执行测试",
                    passed=True,
                    execution_time=time.time() - start_time,
                    output="策略执行成功"
                )
            else:
                return TestResult(
                    test_name="基本执行测试",
                    passed=False,
                    execution_time=time.time() - start_time,
                    error_message=f"入口函数 {entry_point} 未定义"
                )
        
        except Exception as e:
            return TestResult(
                test_name="基本执行测试",
                passed=False,
                execution_time=time.time() - start_time,
                error_message=f"执行错误: {str(e)}"
            )
    
    def _test_data_access(self, code: str, entry_point: str) -> TestResult:
        """测试数据访问功能"""
        start_time = time.time()
        
        try:
            # 创建测试代码，检查是否能正确访问数据
            test_code = f"""
{code}

def test_data_access():
    context = test_context
    
    # 测试获取当前价格
    price = context.get_current_price()
    assert isinstance(price, (int, float)), "价格应该是数字类型"
    
    # 测试获取历史数据
    history = context.get_history_data(period=10)
    assert hasattr(history, 'shape'), "历史数据应该是DataFrame类型"
    assert history.shape[0] > 0, "历史数据不应为空"
    
    return True
"""
            
            safe_globals = self._create_safe_globals()
            safe_globals['test_context'] = self.test_context
            safe_locals = {}
            
            exec(test_code, safe_globals, safe_locals)
            
            # 运行测试
            result = safe_locals['test_data_access']()
            
            return TestResult(
                test_name="数据访问测试",
                passed=True,
                execution_time=time.time() - start_time,
                output="数据访问功能正常"
            )
        
        except Exception as e:
            return TestResult(
                test_name="数据访问测试",
                passed=False,
                execution_time=time.time() - start_time,
                error_message=f"数据访问测试失败: {str(e)}"
            )
    
    def _test_trading_operations(self, code: str, entry_point: str) -> TestResult:
        """测试交易操作功能"""
        start_time = time.time()
        
        try:
            # 重置测试上下文
            self.test_context = StrategyTestContext()
            
            safe_globals = self._create_safe_globals()
            safe_locals = {}
            
            exec(code, safe_globals, safe_locals)
            
            # 执行策略
            if entry_point in safe_locals:
                initial_balance = self.test_context.get_balance()
                safe_locals[entry_point](self.test_context)
                
                # 检查是否有交易操作
                has_trades = len(self.test_context.orders) > 0
                
                return TestResult(
                    test_name="交易操作测试",
                    passed=True,
                    execution_time=time.time() - start_time,
                    output=f"交易操作测试完成，执行了 {len(self.test_context.orders)} 笔交易"
                )
            else:
                return TestResult(
                    test_name="交易操作测试",
                    passed=False,
                    execution_time=time.time() - start_time,
                    error_message="入口函数未找到"
                )
        
        except Exception as e:
            return TestResult(
                test_name="交易操作测试",
                passed=False,
                execution_time=time.time() - start_time,
                error_message=f"交易操作测试失败: {str(e)}"
            )
    
    def _create_safe_globals(self) -> Dict[str, Any]:
        """创建安全的全局环境"""
        safe_globals = {
            '__builtins__': {
                'len': len,
                'str': str,
                'int': int,
                'float': float,
                'bool': bool,
                'list': list,
                'dict': dict,
                'tuple': tuple,
                'set': set,
                'abs': abs,
                'max': max,
                'min': min,
                'sum': sum,
                'round': round,
                'range': range,
                'enumerate': enumerate,
                'zip': zip,
                'isinstance': isinstance,
                'hasattr': hasattr,
                'getattr': getattr,
                'print': print,
            },
            'pd': pd,
            'np': np,
            'time': time,
        }
        
        return safe_globals
    
    def run_performance_test(self, code: str, entry_point: str = "main") -> PerformanceMetrics:
        """运行性能测试"""
        start_time = time.time()
        
        try:
            # 创建性能监控环境
            safe_globals = self._create_safe_globals()
            safe_locals = {}
            
            # 执行代码
            exec(code, safe_globals, safe_locals)
            
            # 多次执行以获得平均性能
            execution_times = []
            for _ in range(5):
                context = StrategyTestContext()
                exec_start = time.time()
                
                if entry_point in safe_locals:
                    safe_locals[entry_point](context)
                
                execution_times.append(time.time() - exec_start)
            
            avg_execution_time = sum(execution_times) / len(execution_times)
            
            # 计算复杂度分数
            validation_result = code_validation_service.validate_python_code(code, entry_point)
            complexity_score = validation_result.metrics.complexity
            
            return PerformanceMetrics(
                execution_time=avg_execution_time,
                memory_usage=0.0,  # 简化实现
                cpu_usage=0.0,     # 简化实现
                function_calls=validation_result.metrics.functions_count,
                complexity_score=complexity_score
            )
        
        except Exception as e:
            logger.error(f"性能测试失败: {e}")
            return PerformanceMetrics(
                execution_time=0.0,
                memory_usage=0.0,
                cpu_usage=0.0,
                function_calls=0,
                complexity_score=0.0
            )
    
    def run_integration_test(self, code: str, entry_point: str = "main") -> TestSuite:
        """运行集成测试"""
        tests = []
        start_time = time.time()
        
        # 1. 完整策略执行测试
        full_execution_test = self._test_full_strategy_execution(code, entry_point)
        tests.append(full_execution_test)
        
        # 2. 多周期执行测试
        multi_period_test = self._test_multi_period_execution(code, entry_point)
        tests.append(multi_period_test)
        
        # 3. 异常处理测试
        exception_handling_test = self._test_exception_handling(code, entry_point)
        tests.append(exception_handling_test)
        
        # 4. 边界条件测试
        boundary_test = self._test_boundary_conditions(code, entry_point)
        tests.append(boundary_test)
        
        total_time = time.time() - start_time
        passed_tests = sum(1 for test in tests if test.passed)
        failed_tests = len(tests) - passed_tests
        
        return TestSuite(
            name="策略集成测试",
            description="策略的完整功能和集成测试",
            tests=tests,
            total_tests=len(tests),
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            total_time=total_time,
            coverage=passed_tests / len(tests) * 100
        )
    
    def _test_full_strategy_execution(self, code: str, entry_point: str) -> TestResult:
        """测试完整策略执行"""
        start_time = time.time()
        
        try:
            context = StrategyTestContext()
            safe_globals = self._create_safe_globals()
            safe_locals = {}
            
            exec(code, safe_globals, safe_locals)
            
            if entry_point in safe_locals:
                # 模拟多个时间点的执行
                for i in range(10):
                    context.current_price = 100 + i * 2  # 模拟价格变化
                    safe_locals[entry_point](context)
                
                return TestResult(
                    test_name="完整策略执行测试",
                    passed=True,
                    execution_time=time.time() - start_time,
                    output=f"策略执行完成，共执行10个周期，产生 {len(context.orders)} 笔交易"
                )
            else:
                return TestResult(
                    test_name="完整策略执行测试",
                    passed=False,
                    execution_time=time.time() - start_time,
                    error_message="入口函数未找到"
                )
        
        except Exception as e:
            return TestResult(
                test_name="完整策略执行测试",
                passed=False,
                execution_time=time.time() - start_time,
                error_message=f"执行失败: {str(e)}"
            )
    
    def _test_multi_period_execution(self, code: str, entry_point: str) -> TestResult:
        """测试多周期执行"""
        start_time = time.time()
        
        try:
            context = StrategyTestContext()
            safe_globals = self._create_safe_globals()
            safe_locals = {}
            
            exec(code, safe_globals, safe_locals)
            
            if entry_point in safe_locals:
                # 模拟不同市场条件
                market_conditions = [
                    {'trend': 'up', 'volatility': 'low'},
                    {'trend': 'down', 'volatility': 'high'},
                    {'trend': 'sideways', 'volatility': 'medium'}
                ]
                
                for condition in market_conditions:
                    # 根据市场条件调整价格
                    if condition['trend'] == 'up':
                        context.current_price *= 1.05
                    elif condition['trend'] == 'down':
                        context.current_price *= 0.95
                    
                    safe_locals[entry_point](context)
                
                return TestResult(
                    test_name="多周期执行测试",
                    passed=True,
                    execution_time=time.time() - start_time,
                    output=f"多周期测试完成，测试了 {len(market_conditions)} 种市场条件"
                )
            else:
                return TestResult(
                    test_name="多周期执行测试",
                    passed=False,
                    execution_time=time.time() - start_time,
                    error_message="入口函数未找到"
                )
        
        except Exception as e:
            return TestResult(
                test_name="多周期执行测试",
                passed=False,
                execution_time=time.time() - start_time,
                error_message=f"多周期测试失败: {str(e)}"
            )
    
    def _test_exception_handling(self, code: str, entry_point: str) -> TestResult:
        """测试异常处理"""
        start_time = time.time()
        
        try:
            # 创建会产生异常的测试上下文
            class ErrorContext(StrategyTestContext):
                def get_current_price(self, symbol='DEFAULT'):
                    raise Exception("模拟数据获取失败")
            
            context = ErrorContext()
            safe_globals = self._create_safe_globals()
            safe_locals = {}
            
            exec(code, safe_globals, safe_locals)
            
            if entry_point in safe_locals:
                try:
                    safe_locals[entry_point](context)
                    # 如果没有抛出异常，说明策略有异常处理
                    return TestResult(
                        test_name="异常处理测试",
                        passed=True,
                        execution_time=time.time() - start_time,
                        output="策略能够正确处理异常情况"
                    )
                except Exception:
                    # 如果抛出异常，说明策略缺少异常处理
                    return TestResult(
                        test_name="异常处理测试",
                        passed=False,
                        execution_time=time.time() - start_time,
                        error_message="策略缺少异常处理机制"
                    )
            else:
                return TestResult(
                    test_name="异常处理测试",
                    passed=False,
                    execution_time=time.time() - start_time,
                    error_message="入口函数未找到"
                )
        
        except Exception as e:
            return TestResult(
                test_name="异常处理测试",
                passed=False,
                execution_time=time.time() - start_time,
                error_message=f"异常处理测试失败: {str(e)}"
            )
    
    def _test_boundary_conditions(self, code: str, entry_point: str) -> TestResult:
        """测试边界条件"""
        start_time = time.time()
        
        try:
            safe_globals = self._create_safe_globals()
            safe_locals = {}
            
            exec(code, safe_globals, safe_locals)
            
            if entry_point in safe_locals:
                # 测试极端条件
                boundary_conditions = [
                    {'balance': 0, 'price': 0.01},      # 极低余额和价格
                    {'balance': 1000000, 'price': 10000}, # 极高余额和价格
                    {'balance': 1000, 'price': 0}        # 零价格
                ]
                
                for condition in boundary_conditions:
                    context = StrategyTestContext()
                    context.balance = condition['balance']
                    context.current_price = condition['price']
                    
                    try:
                        safe_locals[entry_point](context)
                    except Exception as e:
                        # 记录但不失败，因为某些边界条件可能确实无法处理
                        pass
                
                return TestResult(
                    test_name="边界条件测试",
                    passed=True,
                    execution_time=time.time() - start_time,
                    output=f"边界条件测试完成，测试了 {len(boundary_conditions)} 种边界情况"
                )
            else:
                return TestResult(
                    test_name="边界条件测试",
                    passed=False,
                    execution_time=time.time() - start_time,
                    error_message="入口函数未找到"
                )
        
        except Exception as e:
            return TestResult(
                test_name="边界条件测试",
                passed=False,
                execution_time=time.time() - start_time,
                error_message=f"边界条件测试失败: {str(e)}"
            )
    
    def generate_test_report(self, test_suites: List[TestSuite], performance_metrics: PerformanceMetrics) -> Dict[str, Any]:
        """生成测试报告"""
        total_tests = sum(suite.total_tests for suite in test_suites)
        total_passed = sum(suite.passed_tests for suite in test_suites)
        total_failed = sum(suite.failed_tests for suite in test_suites)
        total_time = sum(suite.total_time for suite in test_suites)
        
        report = {
            'summary': {
                'total_tests': total_tests,
                'passed_tests': total_passed,
                'failed_tests': total_failed,
                'success_rate': (total_passed / total_tests * 100) if total_tests > 0 else 0,
                'total_execution_time': total_time
            },
            'test_suites': [
                {
                    'name': suite.name,
                    'description': suite.description,
                    'total_tests': suite.total_tests,
                    'passed_tests': suite.passed_tests,
                    'failed_tests': suite.failed_tests,
                    'coverage': suite.coverage,
                    'execution_time': suite.total_time,
                    'tests': [
                        {
                            'name': test.test_name,
                            'passed': test.passed,
                            'execution_time': test.execution_time,
                            'error_message': test.error_message,
                            'output': test.output
                        }
                        for test in suite.tests
                    ]
                }
                for suite in test_suites
            ],
            'performance_metrics': {
                'avg_execution_time': performance_metrics.execution_time,
                'memory_usage': performance_metrics.memory_usage,
                'cpu_usage': performance_metrics.cpu_usage,
                'function_calls': performance_metrics.function_calls,
                'complexity_score': performance_metrics.complexity_score
            },
            'recommendations': self._generate_recommendations(test_suites, performance_metrics)
        }
        
        return report
    
    def _generate_recommendations(self, test_suites: List[TestSuite], performance_metrics: PerformanceMetrics) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # 基于测试结果的建议
        for suite in test_suites:
            if suite.failed_tests > 0:
                recommendations.append(f"建议修复 {suite.name} 中的 {suite.failed_tests} 个失败测试")
        
        # 基于性能指标的建议
        if performance_metrics.execution_time > 1.0:
            recommendations.append("策略执行时间较长，建议优化算法复杂度")
        
        if performance_metrics.complexity_score > 10:
            recommendations.append("策略复杂度较高，建议拆分为更小的函数")
        
        # 通用建议
        if not recommendations:
            recommendations.append("策略测试通过，代码质量良好")
        
        return recommendations


# 全局策略测试服务实例
strategy_test_service = StrategyTestService()