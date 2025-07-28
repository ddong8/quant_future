# 量化交易平台 API 文档

## 概述

本文档描述了量化交易平台的RESTful API接口。平台基于FastAPI构建，提供完整的量化交易功能，包括用户认证、策略管理、市场数据、交易执行、风险管理等。

## 基础信息

- **基础URL**: `http://localhost:8000/api/v1`
- **API版本**: v1
- **认证方式**: JWT Bearer Token
- **数据格式**: JSON
- **字符编码**: UTF-8

## 认证

### 获取访问令牌

所有API请求都需要在请求头中包含有效的JWT令牌：

```http
Authorization: Bearer <your-jwt-token>
```

### 令牌刷新

访问令牌有效期为24小时，可通过刷新令牌获取新的访问令牌。

## 通用响应格式

### 成功响应

```json
{
  "success": true,
  "data": {
    // 响应数据
  },
  "message": "操作成功",
  "timestamp": "2024-01-01T10:00:00Z",
  "request_id": "uuid-string"
}
```

### 错误响应

```json
{
  "success": false,
  "error_code": "ERROR_CODE",
  "error_message": "错误描述",
  "details": {
    // 错误详情
  },
  "timestamp": "2024-01-01T10:00:00Z",
  "request_id": "uuid-string"
}
```

## API 端点

### 1. 认证接口 (/auth)

#### 1.1 用户登录

**POST** `/auth/login`

用户登录获取访问令牌。

**请求参数:**
```json
{
  "username": "string",
  "password": "string"
}
```

**响应示例:**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "expires_in": 86400,
    "user": {
      "id": 1,
      "username": "trader1",
      "email": "trader1@example.com",
      "role": "trader"
    }
  }
}
```

#### 1.2 用户登出

**POST** `/auth/logout`

用户登出，使当前令牌失效。

**请求头:**
```http
Authorization: Bearer <access-token>
```

#### 1.3 刷新令牌

**POST** `/auth/refresh`

使用刷新令牌获取新的访问令牌。

**请求参数:**
```json
{
  "refresh_token": "string"
}
```

#### 1.4 获取用户信息

**GET** `/auth/profile`

获取当前登录用户的详细信息。

**请求头:**
```http
Authorization: Bearer <access-token>
```

### 2. 用户管理接口 (/users)

#### 2.1 获取用户列表

**GET** `/users`

获取系统中所有用户的列表（需要管理员权限）。

**查询参数:**
- `page`: 页码（默认: 1）
- `size`: 每页数量（默认: 20）
- `role`: 用户角色过滤
- `active`: 激活状态过滤

#### 2.2 创建用户

**POST** `/users`

创建新用户（需要管理员权限）。

**请求参数:**
```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "role": "trader|admin|viewer",
  "is_active": true
}
```

#### 2.3 获取用户详情

**GET** `/users/{user_id}`

获取指定用户的详细信息。

#### 2.4 更新用户信息

**PUT** `/users/{user_id}`

更新用户信息。

#### 2.5 删除用户

**DELETE** `/users/{user_id}`

删除指定用户（需要管理员权限）。

### 3. 策略管理接口 (/strategies)

#### 3.1 获取策略列表

**GET** `/strategies`

获取当前用户的策略列表。

**查询参数:**
- `page`: 页码
- `size`: 每页数量
- `status`: 策略状态过滤
- `search`: 策略名称搜索

**响应示例:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 1,
        "name": "均线策略",
        "description": "基于移动平均线的交易策略",
        "status": "active",
        "created_at": "2024-01-01T10:00:00Z",
        "updated_at": "2024-01-01T12:00:00Z"
      }
    ],
    "total": 10,
    "page": 1,
    "size": 20
  }
}
```

#### 3.2 创建策略

**POST** `/strategies`

创建新的交易策略。

**请求参数:**
```json
{
  "name": "string",
  "description": "string",
  "code": "string",
  "language": "python"
}
```

#### 3.3 获取策略详情

**GET** `/strategies/{strategy_id}`

获取指定策略的详细信息。

#### 3.4 更新策略

**PUT** `/strategies/{strategy_id}`

更新策略信息和代码。

#### 3.5 删除策略

**DELETE** `/strategies/{strategy_id}`

删除指定策略。

#### 3.6 验证策略代码

**POST** `/strategies/{strategy_id}/validate`

验证策略代码的语法和安全性。

**响应示例:**
```json
{
  "success": true,
  "data": {
    "valid": true,
    "errors": [],
    "warnings": [
      "建议添加风险控制逻辑"
    ]
  }
}
```

#### 3.7 部署策略

**POST** `/strategies/{strategy_id}/deploy`

将策略部署到实盘交易环境。

#### 3.8 停止策略

**POST** `/strategies/{strategy_id}/stop`

停止正在运行的策略。

### 4. 市场数据接口 (/market)

#### 4.1 获取合约列表

**GET** `/market/instruments`

获取可交易的合约列表。

**查询参数:**
- `exchange`: 交易所过滤
- `product_class`: 产品类型过滤
- `search`: 合约代码搜索

#### 4.2 获取实时行情

**GET** `/market/quotes/{symbol}`

获取指定合约的实时行情数据。

**响应示例:**
```json
{
  "success": true,
  "data": {
    "symbol": "SHFE.cu2401",
    "last_price": 68500.0,
    "bid_price": 68490.0,
    "ask_price": 68510.0,
    "volume": 12345,
    "open_interest": 54321,
    "timestamp": "2024-01-01T10:00:00Z"
  }
}
```

#### 4.3 获取K线数据

**GET** `/market/klines/{symbol}`

获取指定合约的K线数据。

**查询参数:**
- `duration`: K线周期（1m, 5m, 15m, 1h, 1d等）
- `start_time`: 开始时间
- `end_time`: 结束时间
- `limit`: 数据条数限制

**响应示例:**
```json
{
  "success": true,
  "data": [
    {
      "datetime": "2024-01-01T10:00:00Z",
      "open": 68400.0,
      "high": 68600.0,
      "low": 68300.0,
      "close": 68500.0,
      "volume": 1000
    }
  ]
}
```

### 5. 订单管理接口 (/orders)

#### 5.1 下单

**POST** `/orders`

创建新的交易订单。

**请求参数:**
```json
{
  "symbol": "SHFE.cu2401",
  "direction": "BUY|SELL",
  "offset": "OPEN|CLOSE",
  "volume": 1,
  "price": 68500.0,
  "order_type": "LIMIT|MARKET",
  "strategy_id": 1
}
```

#### 5.2 获取订单列表

**GET** `/orders`

获取订单列表。

**查询参数:**
- `status`: 订单状态过滤
- `symbol`: 合约过滤
- `start_time`: 开始时间
- `end_time`: 结束时间

#### 5.3 获取订单详情

**GET** `/orders/{order_id}`

获取指定订单的详细信息。

#### 5.4 撤销订单

**DELETE** `/orders/{order_id}`

撤销指定订单。

### 6. 持仓管理接口 (/positions)

#### 6.1 获取持仓列表

**GET** `/positions`

获取当前持仓信息。

**响应示例:**
```json
{
  "success": true,
  "data": [
    {
      "symbol": "SHFE.cu2401",
      "direction": "LONG",
      "volume": 2,
      "price": 68400.0,
      "unrealized_pnl": 200.0,
      "margin": 13680.0,
      "updated_at": "2024-01-01T10:00:00Z"
    }
  ]
}
```

#### 6.2 获取持仓详情

**GET** `/positions/{symbol}`

获取指定合约的持仓详情。

### 7. 账户管理接口 (/accounts)

#### 7.1 获取账户信息

**GET** `/accounts`

获取交易账户信息。

**响应示例:**
```json
{
  "success": true,
  "data": {
    "account_id": "123456789",
    "balance": 100000.0,
    "available": 86320.0,
    "margin": 13680.0,
    "frozen_margin": 0.0,
    "realized_pnl": 500.0,
    "unrealized_pnl": 200.0,
    "updated_at": "2024-01-01T10:00:00Z"
  }
}
```

#### 7.2 获取资金流水

**GET** `/accounts/transactions`

获取资金变动流水记录。

### 8. 风险管理接口 (/risk)

#### 8.1 获取风险配置

**GET** `/risk/config`

获取当前的风险控制配置。

#### 8.2 更新风险配置

**PUT** `/risk/config`

更新风险控制参数。

**请求参数:**
```json
{
  "max_daily_loss": 5000.0,
  "max_position_ratio": 0.3,
  "max_single_order_amount": 10000.0,
  "stop_loss_ratio": 0.05
}
```

#### 8.3 获取风险监控状态

**GET** `/risk/status`

获取当前的风险监控状态。

### 9. 回测系统接口 (/backtests)

#### 9.1 创建回测任务

**POST** `/backtests`

创建新的回测任务。

**请求参数:**
```json
{
  "strategy_id": 1,
  "symbol": "SHFE.cu2401",
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "initial_capital": 100000.0,
  "commission_rate": 0.0001
}
```

#### 9.2 获取回测列表

**GET** `/backtests`

获取回测任务列表。

#### 9.3 获取回测结果

**GET** `/backtests/{backtest_id}`

获取指定回测任务的结果。

**响应示例:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "status": "completed",
    "results": {
      "total_return": 0.15,
      "sharpe_ratio": 1.2,
      "max_drawdown": 0.08,
      "win_rate": 0.65,
      "total_trades": 50
    },
    "equity_curve": [
      {"date": "2024-01-01", "equity": 100000.0},
      {"date": "2024-01-02", "equity": 101000.0}
    ]
  }
}
```

### 10. 系统监控接口 (/monitoring)

#### 10.1 获取系统状态

**GET** `/monitoring/status`

获取系统运行状态。

#### 10.2 获取性能指标

**GET** `/monitoring/metrics`

获取系统性能指标。

### 11. 日志管理接口 (/logs)

#### 11.1 获取日志列表

**GET** `/logs`

获取系统日志列表。

**查询参数:**
- `level`: 日志级别过滤
- `module`: 模块过滤
- `start_time`: 开始时间
- `end_time`: 结束时间

### 12. 报告生成接口 (/reports)

#### 12.1 生成交易报告

**POST** `/reports/trading`

生成交易报告。

#### 12.2 获取报告列表

**GET** `/reports`

获取已生成的报告列表。

## WebSocket 接口

### 连接地址

`ws://localhost:8000/api/v1/ws`

### 认证

WebSocket连接需要在连接时传递JWT令牌：

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws?token=your-jwt-token');
```

### 消息格式

#### 订阅消息

```json
{
  "type": "subscribe",
  "channel": "quotes",
  "symbol": "SHFE.cu2401"
}
```

#### 数据推送

```json
{
  "type": "data",
  "channel": "quotes",
  "data": {
    "symbol": "SHFE.cu2401",
    "last_price": 68500.0,
    "timestamp": "2024-01-01T10:00:00Z"
  }
}
```

### 支持的频道

- `quotes`: 实时行情数据
- `orders`: 订单状态更新
- `positions`: 持仓变化
- `account`: 账户资金变化
- `alerts`: 系统告警

## 错误代码

| 错误代码 | 描述 | HTTP状态码 |
|---------|------|-----------|
| VALIDATION_ERROR | 参数验证失败 | 422 |
| AUTHENTICATION_FAILED | 认证失败 | 401 |
| PERMISSION_DENIED | 权限不足 | 403 |
| RESOURCE_NOT_FOUND | 资源不存在 | 404 |
| STRATEGY_VALIDATION_FAILED | 策略验证失败 | 400 |
| INSUFFICIENT_BALANCE | 余额不足 | 400 |
| RISK_CHECK_FAILED | 风险检查失败 | 400 |
| MARKET_CLOSED | 市场已关闭 | 400 |
| SYSTEM_MAINTENANCE | 系统维护中 | 503 |
| INTERNAL_SERVER_ERROR | 服务器内部错误 | 500 |

## 限流规则

- 普通用户：每分钟最多100个请求
- 高级用户：每分钟最多500个请求
- 管理员：无限制

## 版本更新

### v1.0.0 (当前版本)
- 初始版本发布
- 支持基础的交易功能
- 完整的用户认证和权限管理
- 策略开发和回测功能

## 联系方式

如有API使用问题，请联系：
- 技术支持：support@trading-platform.com
- 开发者文档：https://docs.trading-platform.com