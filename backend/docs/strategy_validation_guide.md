# 策略代码验证和测试指南

## 概述

策略代码验证和测试系统提供了全面的策略代码质量检查、安全验证、沙盒执行和单元测试功能，确保策略代码的安全性、正确性和性能。

## 功能模块

### 1. 策略验证器 (StrategyValidator)

负责策略代码的静态分析和验证。

#### 主要功能：
- **语法检查**: 验证Python代码语法正确性
- **安全检查**: 检测危险函数和模块使用
- **结构检查**: 验证必需函数存在性和参数正确性
- **依赖检查**: 检查导入模块的可用性
- **代码分析**: 计算复杂度、可维护性等指标
- **安全报告**: 生成详细的安全风险报告

#### 使用示例：
```python
from app.services.strategy_validator import StrategyValidator
from app.schemas.strategy import StrategyValidationRequest

validator = StrategyValidator()

# 创建验证请求
request = StrategyValidationRequest(
    code=strategy_code,
    check_syntax=True,
    check_security=True,
    check_structure=True,
    check_dependencies=True
)

# 执行验证
result = validator.validate_strategy(request)

if result.valid:
    print("策略代码验证通过")
else:
    print(f"验证失败: {result.errors}")
```

### 2. 策略沙盒 (StrategySandbox)

提供安全的代码执行环境。

#### 主要功能：
- **安全执行**: 在受限环境中执行策略代码
- **资源限制**: 限制内存使用和执行时间
- **输出捕获**: 捕获代码执行输出和错误
- **模拟环境**: 提供模拟的交易上下文

#### 使用示例：
```python
from app.services.strategy_sandbox import StrategySandbox
from app.schemas.strategy import StrategySandboxRequest

sandbox = StrategySandbox()

# 创建沙盒请求
request = StrategySandboxRequest(
    code=strategy_code,
    test_data={
        'params': {'symbol': 'SHFE.cu2401'},
        'initial_capital': 1000000
    },
    timeout=30
)

# 执行代码
result = sandbox.execute(request)

if result.success:
    print(f"执行成功，输出: {result.output}")
    print(f"执行时间: {result.execution_time}秒")
    print(f"内存使用: {result.memory_usage}MB")
else:
    print(f"执行失败: {result.error}")
```

### 3. 策略测试器 (StrategyTester)

提供综合的策略测试功能。

#### 主要功能：
- **完整测试**: 结合验证、执行和性能评估
- **快速测试**: 提供快速的基础检查
- **性能评估**: 评估策略代码性能指标
- **测试报告**: 生成详细的测试报告

#### 使用示例：
```python
from app.services.strategy_tester import StrategyTester
from app.schemas.strategy import StrategyTestRequest

tester = StrategyTester(db)

# 创建测试请求
request = StrategyTestRequest(
    strategy_id=1,
    test_params={'symbol': 'SHFE.cu2401'},
    timeout=60
)

# 执行测试
result = tester.test_strategy(request, user_id)

print(f"测试结果: {result.overall_result}")
print(f"建议: {result.recommendations}")
```

### 4. 单元测试框架 (StrategyUnitTestFramework)

提供策略代码的单元测试功能。

#### 主要功能：
- **基础测试**: 检查必需函数存在性和调用
- **交易逻辑测试**: 测试买入卖出逻辑
- **自定义测试**: 支持添加自定义测试用例
- **测试报告**: 生成详细的测试结果

#### 使用示例：
```python
from app.services.strategy_unittest import run_strategy_unit_tests

# 运行单元测试
test_data = {
    'params': {'symbol': 'SHFE.cu2401'},
    'initial_capital': 1000000
}

results = run_strategy_unit_tests(strategy_code, test_data)

print(f"总测试: {results['total_tests']}")
print(f"通过: {results['passed_tests']}")
print(f"失败: {results['failed_tests']}")
print(f"整体结果: {'通过' if results['overall_success'] else '失败'}")
```

### 5. 综合验证服务 (StrategyValidationService)

整合所有验证和测试功能。

#### 主要功能：
- **综合验证**: 执行完整的验证流程
- **快速验证**: 提供快速的基础检查
- **评分系统**: 计算综合评分和等级
- **部署建议**: 提供部署准备状态评估

#### 使用示例：
```python
from app.services.strategy_validation_service import StrategyValidationService

service = StrategyValidationService(db)

# 综合验证
result = service.comprehensive_validation(strategy_id, user_id)

print(f"验证结果: {result['overall_result']}")
print(f"综合评分: {result['overall_score']}/10")
print(f"是否可部署: {result['ready_for_deployment']}")

# 快速验证
quick_result = service.quick_validation(strategy_code)
print(f"快速验证: {quick_result['validation_result']}")
```

## API 端点

### 策略验证相关

#### POST /api/v1/strategies/validate
验证策略代码

**请求体:**
```json
{
    "code": "策略代码",
    "check_syntax": true,
    "check_security": true,
    "check_structure": true,
    "check_dependencies": true
}
```

#### POST /api/v1/strategies/{strategy_id}/test
测试指定策略

**请求体:**
```json
{
    "strategy_id": 1,
    "test_params": {"symbol": "SHFE.cu2401"},
    "timeout": 60
}
```

#### POST /api/v1/strategies/sandbox
在沙盒中执行代码

**请求体:**
```json
{
    "code": "策略代码",
    "test_data": {"params": {}},
    "timeout": 30
}
```

#### POST /api/v1/strategies/quick-test
快速测试策略代码

**请求体:**
```json
{
    "code": "策略代码",
    "test_params": {"symbol": "SHFE.cu2401"}
}
```

#### POST /api/v1/strategies/{strategy_id}/unit-test
运行策略单元测试

#### GET /api/v1/strategies/{strategy_id}/analysis
分析策略代码

#### GET /api/v1/strategies/{strategy_id}/security-report
获取安全报告

#### GET /api/v1/strategies/{strategy_id}/dependencies
获取依赖信息

#### POST /api/v1/strategies/{strategy_id}/comprehensive-validation
综合策略验证

#### POST /api/v1/strategies/quick-validation
快速策略验证

## 安全机制

### 1. 代码安全检查

- **危险函数检测**: 检测 `eval`, `exec`, `open`, `__import__` 等危险函数
- **危险模块检测**: 检测 `os`, `sys`, `subprocess` 等危险模块
- **属性访问限制**: 限制访问私有属性和方法

### 2. 沙盒安全

- **受限全局环境**: 只提供安全的内置函数
- **模块白名单**: 只允许导入预定义的安全模块
- **资源限制**: 限制内存使用和执行时间
- **输出限制**: 限制输出内容大小

### 3. 执行隔离

- **线程隔离**: 使用独立线程执行代码
- **超时控制**: 强制终止超时执行
- **异常捕获**: 捕获并处理所有异常

## 性能指标

### 1. 代码质量指标

- **复杂度评分**: 基于代码复杂度计算 (0-10分)
- **可维护性评分**: 基于代码结构和长度 (0-10分)
- **安全性评分**: 基于安全检查结果 (0-10分)

### 2. 执行性能指标

- **执行时间**: 代码执行耗时
- **内存使用**: 代码执行内存占用
- **成功率**: 执行成功的比例

### 3. 综合评分

综合评分基于以下权重计算：
- 代码验证: 25%
- 安全检查: 20%
- 依赖检查: 15%
- 结构检查: 15%
- 单元测试: 15%
- 沙盒测试: 10%

## 最佳实践

### 1. 策略代码编写

```python
def initialize(context):
    """策略初始化函数 - 必需"""
    # 设置策略参数
    context.symbol = context.params.get("symbol", "SHFE.cu2401")
    context.period = context.params.get("period", 20)
    
    # 添加文档字符串
    context.log("策略初始化完成")

def handle_bar(context, bar_dict):
    """K线处理函数 - 必需"""
    try:
        # 获取数据
        klines = context.get_klines(context.symbol, context.period)
        
        if len(klines) < context.period:
            return
        
        # 计算指标
        prices = [k.close for k in klines]
        ma = sum(prices) / len(prices)
        
        # 交易逻辑
        current_price = klines[-1].close
        if current_price > ma:
            context.order_target_percent(context.symbol, 1.0)
        else:
            context.order_target_percent(context.symbol, 0.0)
            
    except Exception as e:
        context.log(f"处理K线数据时出错: {e}")
```

### 2. 验证流程建议

1. **开发阶段**: 使用快速验证检查基础问题
2. **测试阶段**: 使用综合验证进行全面检查
3. **部署前**: 确保综合评分 >= 7.0 且安全检查通过
4. **定期检查**: 定期运行单元测试确保代码质量

### 3. 错误处理

- 在策略代码中添加适当的异常处理
- 使用 `context.log()` 记录重要信息
- 避免使用可能导致程序崩溃的操作

## 故障排除

### 常见问题

1. **语法错误**: 检查Python语法，特别是缩进和冒号
2. **缺少必需函数**: 确保包含 `initialize` 和 `handle_bar` 函数
3. **安全检查失败**: 移除危险函数和模块的使用
4. **依赖缺失**: 安装缺失的Python包
5. **执行超时**: 优化代码逻辑，减少计算复杂度

### 调试技巧

1. 使用快速验证快速定位问题
2. 查看详细的错误信息和建议
3. 使用沙盒测试验证修复效果
4. 运行单元测试确保功能正确

## 扩展开发

### 添加自定义验证规则

```python
class CustomValidator(StrategyValidator):
    def _check_custom_rules(self, code: str) -> bool:
        # 添加自定义验证逻辑
        return True
```

### 添加自定义测试用例

```python
def create_custom_tests():
    framework = StrategyUnitTestFramework()
    
    def test_custom_logic(strategy_globals, context):
        # 自定义测试逻辑
        return True
    
    framework.add_test_case(
        "custom_test",
        "自定义测试描述",
        test_custom_logic,
        True
    )
    
    return framework
```

## 总结

策略代码验证和测试系统提供了完整的代码质量保障机制，通过多层次的检查和测试，确保策略代码的安全性、正确性和性能。建议在策略开发的各个阶段都使用相应的验证和测试功能，以提高策略质量和系统稳定性。