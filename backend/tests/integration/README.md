# 后端集成测试

本目录包含量化交易平台后端的集成测试，用于验证各个组件之间的协作和整体系统功能。

## 测试结构

```
tests/integration/
├── README.md                      # 本文档
├── test_auth_api.py              # 认证API集成测试
├── test_strategy_api.py          # 策略API集成测试
├── test_backtest_api.py          # 回测API集成测试
├── test_trading_api.py           # 交易API集成测试
├── test_websocket.py             # WebSocket集成测试
├── test_tqsdk_integration.py     # TQSDK集成测试
└── test_database_operations.py   # 数据库操作集成测试
```

## 测试覆盖范围

### 1. 认证API测试 (`test_auth_api.py`)
- 用户注册、登录、登出
- JWT令牌生成和验证
- 密码修改和重置
- 权限控制和访问验证
- 完整认证流程测试

### 2. 策略API测试 (`test_strategy_api.py`)
- 策略CRUD操作
- 策略代码验证和测试
- 策略部署和停止
- 策略性能监控
- 策略权限控制

### 3. 回测API测试 (`test_backtest_api.py`)
- 回测创建和配置
- 回测执行和状态管理
- 回测结果分析
- 回测比较和导出
- 回测权限验证

### 4. 交易API测试 (`test_trading_api.py`)
- 订单创建、修改、取消
- 持仓管理和查询
- 账户信息获取
- 风险控制验证
- 交易流程测试

### 5. WebSocket测试 (`test_websocket.py`)
- WebSocket连接和认证
- 实时数据订阅
- 消息推送和接收
- 错误处理和重连
- 并发连接测试

### 6. TQSDK集成测试 (`test_tqsdk_integration.py`)
- TQSDK适配器功能
- 市场数据获取
- 历史数据查询
- 订单执行接口
- 错误处理和性能测试

### 7. 数据库操作测试 (`test_database_operations.py`)
- 数据模型CRUD操作
- 数据关系和约束
- 复杂查询和聚合
- 事务处理
- 性能和索引测试

## 运行测试

### 前置要求

1. **Python环境**
   ```bash
   python >= 3.8
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   pip install pytest pytest-asyncio httpx
   ```

3. **数据库设置**
   - 测试使用SQLite内存数据库
   - 无需额外配置

4. **Redis设置**（可选）
   - 用于缓存测试
   - 可使用模拟Redis

### 运行方式

#### 1. 使用测试脚本（推荐）

```bash
# 运行所有集成测试
python tests/run_integration_tests.py

# 运行特定测试套件
python tests/run_integration_tests.py --suite auth
python tests/run_integration_tests.py --suite strategy
python tests/run_integration_tests.py --suite trading

# 详细输出
python tests/run_integration_tests.py --verbose

# 生成覆盖率报告
python tests/run_integration_tests.py --coverage

# 生成HTML测试报告
python tests/run_integration_tests.py --report

# 检查测试依赖
python tests/run_integration_tests.py --check-deps

# 清理测试数据
python tests/run_integration_tests.py --cleanup
```

#### 2. 直接使用pytest

```bash
# 运行所有集成测试
pytest tests/integration/

# 运行特定测试文件
pytest tests/integration/test_auth_api.py

# 运行特定测试类
pytest tests/integration/test_auth_api.py::TestAuthAPI

# 运行特定测试方法
pytest tests/integration/test_auth_api.py::TestAuthAPI::test_login_success

# 详细输出
pytest tests/integration/ -v

# 生成覆盖率报告
pytest tests/integration/ --cov=app --cov-report=html

# 并行运行测试
pytest tests/integration/ -n auto
```

#### 3. 按标记运行测试

```bash
# 运行认证相关测试
pytest -m auth

# 运行慢速测试
pytest -m slow

# 排除慢速测试
pytest -m "not slow"

# 运行多个标记
pytest -m "auth or strategy"
```

## 测试配置

### 环境变量

测试使用以下环境变量：

```bash
TESTING=1                          # 启用测试模式
DATABASE_URL=sqlite:///./test.db   # 测试数据库URL
REDIS_URL=redis://localhost:6379/1 # 测试Redis URL
SECRET_KEY=test_secret_key         # 测试密钥
```

### 测试夹具

主要测试夹具定义在 `conftest.py` 中：

- `db_session`: 数据库会话
- `client`: 测试客户端
- `async_client`: 异步测试客户端
- `test_user`: 测试用户
- `admin_user`: 管理员用户
- `auth_headers`: 认证头
- `test_strategy`: 测试策略
- `test_backtest`: 测试回测
- `mock_tqsdk`: 模拟TQSDK
- `mock_redis`: 模拟Redis
- `mock_influxdb`: 模拟InfluxDB

## 测试数据

### 测试用户

```python
# 普通用户
username: testuser
email: test@example.com
password: testpass123

# 管理员用户
username: admin
email: admin@example.com
password: admin123
```

### 测试合约

```python
TEST_SYMBOLS = [
    "SHFE.cu2401",  # 铜期货
    "DCE.i2401",    # 铁矿石期货
    "CZCE.MA401"    # 甲醇期货
]
```

### 测试数据

```python
# K线数据
TEST_KLINE_DATA = [
    {
        "datetime": "2023-01-01 09:00:00",
        "open": 69900.0,
        "high": 70100.0,
        "low": 69800.0,
        "close": 70000.0,
        "volume": 100
    }
]

# 行情数据
TEST_QUOTE_DATA = {
    "symbol": "SHFE.cu2401",
    "last_price": 70000.0,
    "bid_price1": 69990.0,
    "ask_price1": 70010.0,
    "volume": 1000
}
```

## 模拟服务

### TQSDK模拟

```python
class MockTQSDK:
    def get_quote(self, symbol):
        return mock_quote_data
    
    def get_kline_serial(self, symbol, duration):
        return mock_kline_data
    
    def insert_order(self, **kwargs):
        return mock_order_result
```

### Redis模拟

```python
class MockRedis:
    def __init__(self):
        self.data = {}
    
    def get(self, key):
        return self.data.get(key)
    
    def set(self, key, value, ex=None):
        self.data[key] = value
```

### InfluxDB模拟

```python
class MockInfluxDB:
    def __init__(self):
        self.data = []
    
    def write(self, bucket, org, record):
        self.data.append(record)
    
    def query(self, query):
        return mock_query_result
```

## 测试最佳实践

### 1. 测试隔离

- 每个测试使用独立的数据库会话
- 测试结束后自动清理数据
- 使用事务回滚确保数据隔离

### 2. 模拟外部依赖

- 使用mock对象模拟TQSDK、Redis、InfluxDB
- 避免依赖外部服务的可用性
- 提高测试执行速度

### 3. 异步测试

- 使用`pytest-asyncio`支持异步测试
- WebSocket测试使用异步客户端
- 正确处理异步上下文

### 4. 错误测试

- 测试各种错误情况和边界条件
- 验证错误处理和异常响应
- 确保系统的健壮性

### 5. 性能测试

- 包含基本的性能测试
- 验证数据库查询效率
- 测试并发处理能力

## 持续集成

### GitHub Actions

```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-asyncio httpx
    
    - name: Run integration tests
      run: |
        python tests/run_integration_tests.py --coverage
    
    - name: Upload coverage
      uses: codecov/codecov-action@v1
```

### 本地钩子

```bash
# .git/hooks/pre-commit
#!/bin/bash
echo "运行集成测试..."
python tests/run_integration_tests.py --suite auth
if [ $? -ne 0 ]; then
    echo "集成测试失败，提交被阻止"
    exit 1
fi
```

## 故障排除

### 常见问题

1. **数据库连接错误**
   ```bash
   # 检查数据库配置
   echo $DATABASE_URL
   
   # 重新创建测试数据库
   python tests/run_integration_tests.py --cleanup
   ```

2. **依赖包缺失**
   ```bash
   # 检查依赖
   python tests/run_integration_tests.py --check-deps
   
   # 安装缺失依赖
   pip install pytest pytest-asyncio httpx
   ```

3. **异步测试失败**
   ```bash
   # 确保安装了pytest-asyncio
   pip install pytest-asyncio
   
   # 检查pytest配置
   cat pytest.ini
   ```

4. **WebSocket测试超时**
   ```bash
   # 增加超时时间
   pytest tests/integration/test_websocket.py --timeout=60
   ```

### 调试技巧

1. **详细输出**
   ```bash
   pytest tests/integration/ -v -s
   ```

2. **停在第一个失败**
   ```bash
   pytest tests/integration/ -x
   ```

3. **运行特定测试**
   ```bash
   pytest tests/integration/test_auth_api.py::TestAuthAPI::test_login_success -v
   ```

4. **查看测试覆盖率**
   ```bash
   pytest tests/integration/ --cov=app --cov-report=term-missing
   ```

## 贡献指南

### 添加新测试

1. 在相应的测试文件中添加测试方法
2. 使用适当的测试夹具
3. 添加必要的模拟对象
4. 确保测试隔离和清理
5. 添加适当的测试标记

### 测试命名规范

- 测试文件：`test_*.py`
- 测试类：`Test*`
- 测试方法：`test_*`
- 描述性命名，清楚表达测试目的

### 代码风格

- 遵循PEP 8代码风格
- 使用类型提示
- 添加适当的文档字符串
- 保持测试简洁和可读

---

更多信息请参考项目文档或联系开发团队。