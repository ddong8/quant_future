# 回测引擎使用指南

## 概述

回测引擎是量化交易平台的核心组件之一，提供了完整的历史数据回放、模拟交易执行、持仓管理和性能分析功能。通过回测引擎，用户可以在历史数据上验证交易策略的有效性，评估策略的风险收益特征。

## 核心组件

### 1. 回测引擎 (BacktestEngine)

主要的回测执行引擎，协调各个组件完成回测任务。

#### 主要功能：
- 回测任务管理和执行
- 策略代码执行环境准备
- 回测结果计算和存储
- 进度跟踪和状态管理

#### 使用示例：
```python
from app.services.backtest_engine import BacktestEngine
from app.services.history_service import HistoryService

# 创建回测引擎
history_service = HistoryService(db)
backtest_engine = BacktestEngine(db, history_service)

# 运行回测
result = await backtest_engine.run_backtest(backtest_id)
```

### 2. 数据回放引擎 (BacktestDataReplay)

负责历史数据的加载和按时间顺序回放。

#### 主要功能：
- 历史K线数据加载和缓存
- 按时间顺序数据回放
- 多品种数据同步
- 数据查询和访问接口

#### 使用示例：
```python
from app.services.backtest_engine import BacktestDataReplay

data_replay = BacktestDataReplay(history_service)

# 加载历史数据
symbols = ["SHFE.cu2401", "SHFE.au2406"]
start_date = datetime(2024, 1, 1)
end_date = datetime(2024, 3, 31)

data = await data_replay.load_data(symbols, start_date, end_date)

# 获取指定时间的K线数据
bar_data = data_replay.get_bar_data("SHFE.cu2401", current_time)
```

### 3. 交易执行器 (BacktestTradeExecutor)

模拟真实的交易执行环境，处理订单的创建、成交和管理。

#### 主要功能：
- 订单创建和管理
- 市价单、限价单、止损单处理
- 滑点和手续费计算
- 订单成交逻辑模拟

#### 支持的订单类型：
- **市价单 (MARKET)**: 立即按市价成交
- **限价单 (LIMIT)**: 价格达到限价时成交
- **止损单 (STOP)**: 价格触及止损价时按市价成交

#### 使用示例：
```python
from app.services.backtest_engine import BacktestTradeExecutor, OrderType, OrderSide

executor = BacktestTradeExecutor(commission_rate=0.0003, slippage=0.0001)

# 创建市价买单
order = executor.create_order(
    symbol="SHFE.cu2401",
    side=OrderSide.BUY,
    order_type=OrderType.MARKET,
    quantity=10
)

# 处理订单
executor.process_orders(current_time, market_data)
```

### 4. 投资组合管理器 (BacktestPortfolioManager)

管理回测过程中的持仓、资金和盈亏计算。

#### 主要功能：
- 持仓数量和成本跟踪
- 实时市值和盈亏计算
- 资金使用情况管理
- 资金曲线记录

#### 使用示例：
```python
from app.services.backtest_engine import BacktestPortfolioManager

portfolio_manager = BacktestPortfolioManager(initial_capital=1000000)

# 更新持仓
portfolio_manager.update_position(filled_order)

# 更新市值
portfolio_manager.update_market_value(market_data)

# 获取账户信息
account = portfolio_manager.get_account_info()
print(f"总资产: {account.total_value}")
print(f"可用资金: {account.available_cash}")
```

### 5. 进度跟踪器 (BacktestProgressTracker)

跟踪回测执行进度和预估完成时间。

#### 主要功能：
- 实时进度计算
- 完成时间预估
- 进度回调通知

#### 使用示例：
```python
from app.services.backtest_engine import BacktestProgressTracker

def progress_callback(progress):
    print(f"回测进度: {progress:.1f}%")

tracker = BacktestProgressTracker(total_bars=10000, update_callback=progress_callback)
tracker.update_progress(5000)  # 50%完成
```

### 6. 回测上下文 (BacktestContext)

为策略代码提供回测环境的接口和数据访问。

#### 主要功能：
- K线数据查询接口
- 持仓信息查询
- 账户信息查询
- 交易下单接口

#### 策略接口：
```python
# 在策略代码中使用
def initialize(context):
    context.symbol = context.params.get("symbol", "SHFE.cu2401")
    context.period = context.params.get("period", 20)

def handle_bar(context, bar_dict):
    # 获取历史K线数据
    klines = context.get_klines(context.symbol, context.period)
    
    # 获取当前持仓
    position = context.get_position(context.symbol)
    
    # 获取账户信息
    account = context.get_account()
    
    # 下单交易
    if some_condition:
        context.order_target_percent(context.symbol, 0.5)  # 50%仓位
```

## 回测服务 (BacktestService)

高级回测管理服务，提供完整的回测生命周期管理。

### 主要功能：

#### 1. 回测管理
```python
from app.services.backtest_service import BacktestService

backtest_service = BacktestService(db, history_service)

# 创建回测
backtest_data = {
    'name': '双均线策略回测',
    'strategy_id': 1,
    'start_date': datetime(2024, 1, 1),
    'end_date': datetime(2024, 3, 31),
    'initial_capital': 1000000,
    'symbols': ['SHFE.cu2401'],
    'parameters': {'short_period': 5, 'long_period': 20}
}

backtest = backtest_service.create_backtest(backtest_data, user_id)
```

#### 2. 回测执行
```python
# 启动回测
result = await backtest_service.start_backtest(backtest.id, user_id)

# 获取进度
progress = backtest_service.get_backtest_progress(backtest.id, user_id)

# 停止回测
backtest_service.stop_backtest(backtest.id, user_id)
```

#### 3. 结果分析
```python
# 获取回测结果
results = backtest_service.get_backtest_results(backtest.id, user_id)

# 获取统计信息
stats = backtest_service.get_backtest_statistics(user_id)

# 比较多个回测
comparison = backtest_service.compare_backtests([1, 2, 3], user_id)
```

## API 接口

### 回测管理接口

#### POST /api/v1/backtests/
创建新的回测任务

**请求体:**
```json
{
    "name": "策略回测",
    "strategy_id": 1,
    "start_date": "2024-01-01T00:00:00",
    "end_date": "2024-03-31T23:59:59",
    "initial_capital": 1000000,
    "symbols": ["SHFE.cu2401"],
    "parameters": {"period": 20}
}
```

#### GET /api/v1/backtests/
获取回测列表

**查询参数:**
- `strategy_id`: 策略ID过滤
- `status`: 状态过滤
- `keyword`: 关键词搜索
- `page`: 页码
- `page_size`: 每页大小

#### GET /api/v1/backtests/{backtest_id}
获取回测详情

#### PUT /api/v1/backtests/{backtest_id}
更新回测配置

#### DELETE /api/v1/backtests/{backtest_id}
删除回测

### 回测执行接口

#### POST /api/v1/backtests/{backtest_id}/start
启动回测

#### POST /api/v1/backtests/{backtest_id}/stop
停止回测

#### GET /api/v1/backtests/{backtest_id}/progress
获取回测进度

#### GET /api/v1/backtests/{backtest_id}/results
获取回测结果

### 结果分析接口

#### GET /api/v1/backtests/{backtest_id}/equity-curve
获取资金曲线数据

#### GET /api/v1/backtests/{backtest_id}/trades
获取交易记录

#### GET /api/v1/backtests/{backtest_id}/daily-returns
获取日收益率数据

#### GET /api/v1/backtests/{backtest_id}/performance-metrics
获取详细性能指标

#### POST /api/v1/backtests/compare
比较多个回测结果

## 性能指标

### 收益指标
- **总收益率 (Total Return)**: (期末资产 - 期初资产) / 期初资产
- **年化收益率 (Annual Return)**: (1 + 总收益率)^(365/天数) - 1
- **最终资产 (Final Capital)**: 回测结束时的总资产

### 风险指标
- **最大回撤 (Max Drawdown)**: 从峰值到谷值的最大跌幅
- **波动率 (Volatility)**: 日收益率的标准差
- **VaR**: 在给定置信水平下的最大可能损失

### 风险调整收益指标
- **夏普比率 (Sharpe Ratio)**: (年化收益率 - 无风险利率) / 年化波动率
- **索提诺比率 (Sortino Ratio)**: (年化收益率 - 无风险利率) / 下行波动率
- **卡玛比率 (Calmar Ratio)**: 年化收益率 / 最大回撤

### 交易指标
- **总交易次数 (Total Trades)**: 完成的交易笔数
- **胜率 (Win Rate)**: 盈利交易次数 / 总交易次数
- **盈亏比 (Profit Factor)**: 总盈利 / 总亏损
- **平均盈利 (Average Win)**: 盈利交易的平均收益
- **平均亏损 (Average Loss)**: 亏损交易的平均损失

## 策略编写指南

### 策略结构

每个策略必须包含两个核心函数：

```python
def initialize(context):
    """
    策略初始化函数，在回测开始时调用一次
    
    Args:
        context: 策略上下文对象
    """
    # 设置策略参数
    context.symbol = context.params.get("symbol", "SHFE.cu2401")
    context.period = context.params.get("period", 20)
    
    # 初始化策略变量
    context.last_price = 0
    context.position_size = 0

def handle_bar(context, bar_dict):
    """
    K线处理函数，每个K线周期调用一次
    
    Args:
        context: 策略上下文对象
        bar_dict: 当前K线数据字典 {symbol: bar_data}
    """
    # 获取当前K线数据
    if context.symbol not in bar_dict:
        return
    
    current_bar = bar_dict[context.symbol]
    current_price = current_bar['close']
    
    # 策略逻辑
    # ...
```

### 数据访问接口

```python
# 获取历史K线数据
klines = context.get_klines(symbol, count=100)

# 获取持仓信息
position = context.get_position(symbol)
print(f"持仓数量: {position['quantity']}")
print(f"持仓成本: {position['avg_price']}")
print(f"未实现盈亏: {position['unrealized_pnl']}")

# 获取账户信息
account = context.get_account()
print(f"总资产: {account['total_value']}")
print(f"可用资金: {account['available_cash']}")
```

### 交易接口

```python
# 按百分比下单（推荐）
context.order_target_percent(symbol, 0.5)  # 50%仓位

# 按金额下单
context.order_target_value(symbol, 500000)  # 50万元仓位

# 直接买卖
context.buy(symbol, quantity=10)  # 买入10手
context.sell(symbol, quantity=5)   # 卖出5手

# 限价单
context.buy(symbol, quantity=10, price=70000)  # 限价买入
```

### 策略示例

#### 双均线策略
```python
def initialize(context):
    context.symbol = context.params.get("symbol", "SHFE.cu2401")
    context.short_period = context.params.get("short_period", 5)
    context.long_period = context.params.get("long_period", 20)

def handle_bar(context, bar_dict):
    if context.symbol not in bar_dict:
        return
    
    # 获取历史数据
    klines = context.get_klines(context.symbol, context.long_period + 1)
    
    if len(klines) < context.long_period:
        return
    
    # 计算移动平均
    short_prices = [k['close'] for k in klines[-context.short_period:]]
    long_prices = [k['close'] for k in klines[-context.long_period:]]
    
    short_ma = sum(short_prices) / len(short_prices)
    long_ma = sum(long_prices) / len(long_prices)
    
    # 交易信号
    if short_ma > long_ma:
        # 金叉，买入
        context.order_target_percent(context.symbol, 1.0)
    elif short_ma < long_ma:
        # 死叉，卖出
        context.order_target_percent(context.symbol, 0.0)
```

#### 均值回归策略
```python
import math

def initialize(context):
    context.symbol = context.params.get("symbol", "SHFE.cu2401")
    context.period = context.params.get("period", 20)
    context.threshold = context.params.get("threshold", 2.0)

def handle_bar(context, bar_dict):
    if context.symbol not in bar_dict:
        return
    
    # 获取历史数据
    klines = context.get_klines(context.symbol, context.period + 1)
    
    if len(klines) < context.period:
        return
    
    # 计算均值和标准差
    prices = [k['close'] for k in klines[-context.period:]]
    mean_price = sum(prices) / len(prices)
    
    variance = sum((p - mean_price) ** 2 for p in prices) / len(prices)
    std_price = math.sqrt(variance)
    
    current_price = klines[-1]['close']
    
    # 计算Z-score
    if std_price > 0:
        z_score = (current_price - mean_price) / std_price
        
        # 交易逻辑
        if z_score > context.threshold:
            # 价格过高，卖出
            context.order_target_percent(context.symbol, -0.5)
        elif z_score < -context.threshold:
            # 价格过低，买入
            context.order_target_percent(context.symbol, 0.5)
        elif abs(z_score) < 0.5:
            # 价格回归，平仓
            context.order_target_percent(context.symbol, 0.0)
```

## 最佳实践

### 1. 策略开发
- 保持策略逻辑简洁清晰
- 使用参数化设计，便于优化
- 添加适当的异常处理
- 记录关键的策略状态和决策

### 2. 回测配置
- 选择合适的回测时间范围
- 设置合理的初始资金
- 考虑交易成本和滑点
- 使用多个品种分散风险

### 3. 结果分析
- 关注风险调整后的收益指标
- 分析最大回撤的持续时间
- 检查交易频率和成本
- 进行样本外测试验证

### 4. 性能优化
- 避免在策略中进行复杂计算
- 合理使用历史数据查询
- 优化数据结构和算法
- 监控内存使用情况

## 故障排除

### 常见问题

1. **回测启动失败**
   - 检查策略代码语法
   - 验证回测参数设置
   - 确认历史数据可用性

2. **回测执行缓慢**
   - 减少历史数据查询频率
   - 优化策略计算逻辑
   - 调整回测时间范围

3. **结果异常**
   - 检查交易逻辑正确性
   - 验证数据质量
   - 确认成本设置合理

4. **内存不足**
   - 减少数据缓存大小
   - 优化数据结构
   - 分段执行长期回测

### 调试技巧

1. 使用日志记录关键信息
```python
def handle_bar(context, bar_dict):
    context.log(f"当前价格: {current_price}, 持仓: {position['quantity']}")
```

2. 分段测试策略逻辑
3. 使用小数据集快速验证
4. 检查中间计算结果

## 扩展开发

### 自定义指标
```python
def calculate_rsi(prices, period=14):
    """计算RSI指标"""
    gains = []
    losses = []
    
    for i in range(1, len(prices)):
        change = prices[i] - prices[i-1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(-change)
    
    if len(gains) < period:
        return None
    
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    
    if avg_loss == 0:
        return 100
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi
```

### 自定义订单类型
可以扩展交易执行器以支持更多订单类型，如条件单、冰山单等。

### 多品种策略
```python
def handle_bar(context, bar_dict):
    for symbol in context.symbols:
        if symbol in bar_dict:
            # 处理每个品种的逻辑
            process_symbol(context, symbol, bar_dict[symbol])
```

## 总结

回测引擎提供了完整的策略回测功能，支持多种订单类型、详细的性能分析和灵活的策略开发接口。通过合理使用回测引擎，可以有效验证交易策略的可行性，为实盘交易提供可靠的依据。

建议在使用过程中：
1. 从简单策略开始，逐步增加复杂度
2. 重视风险管理和资金管理
3. 进行充分的样本外测试
4. 持续监控和优化策略性能