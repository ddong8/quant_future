"""
策略验证和测试功能的测试用例
"""
import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.services.strategy_validator import StrategyValidator
from app.services.strategy_sandbox import StrategySandbox
from app.services.strategy_tester import StrategyTester
from app.services.strategy_validation_service import StrategyValidationService
from app.schemas.strategy import (
    StrategyValidationRequest,
    StrategySandboxRequest,
    StrategyTestRequest,
)


class TestStrategyValidator:
    """策略验证器测试"""
    
    def setup_method(self):
        self.validator = StrategyValidator()
    
    def test_valid_strategy_code(self):
        """测试有效的策略代码"""
        code = '''
def initialize(context):
    context.symbol = "SHFE.cu2401"

def handle_bar(context, bar_dict):
    print("处理K线数据")
'''
        
        request = StrategyValidationRequest(
            code=code,
            check_syntax=True,
            check_security=True,
            check_structure=True,
            check_dependencies=True
        )
        
        result = self.validator.validate_strategy(request)
        
        assert result.valid == True
        assert len(result.errors) == 0
        assert result.checks['syntax'] == True
        assert result.checks['structure'] == True
    
    def test_invalid_syntax(self):
        """测试语法错误的代码"""
        code = '''
def initialize(context):
    context.symbol = "SHFE.cu2401"
    # 语法错误：缺少冒号
def handle_bar(context, bar_dict)
    print("处理K线数据")
'''
        
        request = StrategyValidationRequest(
            code=code,
            check_syntax=True
        )
        
        result = self.validator.validate_strategy(request)
        
        assert result.valid == False
        assert len(result.errors) > 0
        assert result.checks['syntax'] == False
    
    def test_security_violation(self):
        """测试安全违规代码"""
        code = '''
import os

def initialize(context):
    # 安全违规：使用危险函数
    os.system("rm -rf /")

def handle_bar(context, bar_dict):
    pass
'''
        
        request = StrategyValidationRequest(
            code=code,
            check_security=True
        )
        
        result = self.validator.validate_strategy(request)
        
        assert result.valid == False
        assert len(result.errors) > 0
        assert result.checks['security'] == False
    
    def test_missing_required_functions(self):
        """测试缺少必需函数"""
        code = '''
def some_other_function():
    pass
'''
        
        request = StrategyValidationRequest(
            code=code,
            check_structure=True
        )
        
        result = self.validator.validate_strategy(request)
        
        assert result.valid == False
        assert len(result.errors) > 0
        assert result.checks['structure'] == False
    
    def test_code_analysis(self):
        """测试代码分析"""
        code = '''
def initialize(context):
    context.symbol = "SHFE.cu2401"
    context.period = 20

def handle_bar(context, bar_dict):
    if context.symbol in bar_dict:
        price = bar_dict[context.symbol]['close']
        if price > 70000:
            print("价格较高")
        else:
            print("价格较低")
'''
        
        analysis = self.validator.analyze_code(code)
        
        assert analysis.lines_of_code > 0
        assert analysis.functions_count == 2
        assert analysis.complexity_score > 0
        assert analysis.security_score > 0
        assert analysis.maintainability_score > 0
    
    def test_dependency_info(self):
        """测试依赖信息获取"""
        code = '''
import math
import numpy as np
import pandas as pd

def initialize(context):
    pass

def handle_bar(context, bar_dict):
    pass
'''
        
        dependencies = self.validator.get_dependency_info(code)
        
        assert len(dependencies) >= 3
        module_names = [dep.module_name for dep in dependencies]
        assert 'math' in module_names
        assert 'numpy' in module_names
        assert 'pandas' in module_names
    
    def test_security_report(self):
        """测试安全报告生成"""
        code = '''
def initialize(context):
    context.symbol = "SHFE.cu2401"

def handle_bar(context, bar_dict):
    print("安全的策略代码")
'''
        
        security_report = self.validator.generate_security_report(code)
        
        assert security_report.security_level in ['HIGH', 'MEDIUM', 'LOW']
        assert isinstance(security_report.safe_to_execute, bool)
        assert isinstance(security_report.issues, list)
        assert isinstance(security_report.recommendations, list)


class TestStrategySandbox:
    """策略沙盒测试"""
    
    def setup_method(self):
        self.sandbox = StrategySandbox()
    
    def test_safe_code_execution(self):
        """测试安全代码执行"""
        code = '''
def initialize(context):
    context.symbol = "SHFE.cu2401"
    print(f"初始化策略，交易品种: {context.symbol}")

def handle_bar(context, bar_dict):
    print("处理K线数据")

# 执行测试
initialize(context)
handle_bar(context, {})
'''
        
        request = StrategySandboxRequest(
            code=code,
            test_data={'params': {'symbol': 'SHFE.cu2401'}},
            timeout=10
        )
        
        result = self.sandbox.execute(request)
        
        assert result.success == True
        assert result.execution_time > 0
        assert len(result.output) > 0
        assert result.error == ""
    
    def test_unsafe_code_rejection(self):
        """测试不安全代码被拒绝"""
        code = '''
import os
os.system("echo 'dangerous command'")
'''
        
        request = StrategySandboxRequest(
            code=code,
            test_data={},
            timeout=10
        )
        
        result = self.sandbox.execute(request)
        
        assert result.success == False
        assert "不安全" in result.error
    
    def test_timeout_handling(self):
        """测试超时处理"""
        code = '''
import time
time.sleep(20)  # 超过超时限制
'''
        
        request = StrategySandboxRequest(
            code=code,
            test_data={},
            timeout=5
        )
        
        result = self.sandbox.execute(request)
        
        assert result.success == False
        assert "超时" in result.error


class TestStrategyTester:
    """策略测试器测试"""
    
    def setup_method(self):
        self.db_mock = Mock(spec=Session)
        self.tester = StrategyTester(self.db_mock)
    
    def test_quick_test_valid_strategy(self):
        """测试快速测试有效策略"""
        code = '''
def initialize(context):
    context.symbol = "SHFE.cu2401"

def handle_bar(context, bar_dict):
    print("处理K线数据")
'''
        
        result = self.tester.run_quick_test(code)
        
        assert result['success'] == True
        assert result['result'] == 'PASS'
        assert result['execution_time'] > 0
    
    def test_quick_test_invalid_strategy(self):
        """测试快速测试无效策略"""
        code = '''
def invalid_function():
    pass
# 缺少必需的函数
'''
        
        result = self.tester.run_quick_test(code)
        
        assert result['success'] == False
        assert result['result'] == 'VALIDATION_FAILED'
        assert len(result['errors']) > 0


class TestStrategyValidationService:
    """策略验证服务测试"""
    
    def setup_method(self):
        self.db_mock = Mock(spec=Session)
        self.service = StrategyValidationService(self.db_mock)
    
    def test_quick_validation_valid_code(self):
        """测试快速验证有效代码"""
        code = '''
def initialize(context):
    context.symbol = "SHFE.cu2401"

def handle_bar(context, bar_dict):
    print("处理K线数据")
'''
        
        result = self.service.quick_validation(code)
        
        assert result['validation_result'] == 'PASS'
        assert result['quick_score'] >= 7.0
        assert result['code_valid'] == True
        assert result['structure_ok'] == True
    
    def test_quick_validation_invalid_code(self):
        """测试快速验证无效代码"""
        code = '''
def some_function():
    pass
# 缺少必需函数
'''
        
        result = self.service.quick_validation(code)
        
        assert result['validation_result'] == 'FAIL'
        assert result['quick_score'] < 7.0
        assert result['structure_ok'] == False


# 集成测试
class TestStrategyValidationIntegration:
    """策略验证集成测试"""
    
    def test_complete_validation_workflow(self):
        """测试完整的验证工作流"""
        # 准备测试策略代码
        strategy_code = '''
import math

def initialize(context):
    """策略初始化"""
    context.symbol = context.params.get("symbol", "SHFE.cu2401")
    context.short_period = context.params.get("short_period", 5)
    context.long_period = context.params.get("long_period", 20)
    print(f"策略初始化完成，交易品种: {context.symbol}")

def handle_bar(context, bar_dict):
    """处理K线数据"""
    # 获取K线数据
    klines = context.get_klines(context.symbol, context.long_period + 1)
    
    if len(klines) < context.long_period:
        return
    
    # 计算移动平均
    short_prices = [k.close for k in klines[-context.short_period:]]
    long_prices = [k.close for k in klines[-context.long_period:]]
    
    short_ma = sum(short_prices) / len(short_prices)
    long_ma = sum(long_prices) / len(long_prices)
    
    # 交易逻辑
    if short_ma > long_ma:
        context.order_target_percent(context.symbol, 1.0)
        print("金叉信号，买入")
    elif short_ma < long_ma:
        context.order_target_percent(context.symbol, 0.0)
        print("死叉信号，卖出")
'''
        
        # 1. 代码验证
        validator = StrategyValidator()
        validation_request = StrategyValidationRequest(
            code=strategy_code,
            check_syntax=True,
            check_security=True,
            check_structure=True,
            check_dependencies=True
        )
        
        validation_result = validator.validate_strategy(validation_request)
        assert validation_result.valid == True
        
        # 2. 沙盒执行
        sandbox = StrategySandbox()
        sandbox_request = StrategySandboxRequest(
            code=strategy_code,
            test_data={
                'params': {
                    'symbol': 'SHFE.cu2401',
                    'short_period': 5,
                    'long_period': 20
                }
            },
            timeout=30
        )
        
        sandbox_result = sandbox.execute(sandbox_request)
        assert sandbox_result.success == True
        
        # 3. 单元测试
        from app.services.strategy_unittest import run_strategy_unit_tests
        
        unit_test_results = run_strategy_unit_tests(strategy_code, {
            'params': {'symbol': 'SHFE.cu2401'},
            'initial_capital': 1000000
        })
        
        assert unit_test_results['overall_success'] == True
        assert unit_test_results['passed_tests'] > 0
        
        print("完整验证工作流测试通过！")


if __name__ == "__main__":
    # 运行集成测试
    integration_test = TestStrategyValidationIntegration()
    integration_test.test_complete_validation_workflow()
    print("所有测试通过！")