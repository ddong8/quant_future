# 环境变量配置指南

## 概述

本指南详细说明了量化交易平台的环境变量配置，包括配置文件的创建、验证和管理。

## 快速开始

### 1. 生成配置文件

使用配置生成脚本快速创建适合您环境的配置文件：

```bash
# 开发环境配置
python generate_config.py --environment development

# Docker 环境配置  
python generate_config.py --environment docker

# 生产环境配置
python generate_config.py --environment production

# 交互式配置
python generate_config.py --interactive
```

### 2. 验证配置

生成配置后，使用验证脚本检查配置的正确性：

```bash
# 验证配置
python validate_config.py

# 严格模式验证（警告也视为错误）
python validate_config.py --strict
```

## 配置文件结构

### .env.example
示例配置文件，包含所有可用的环境变量及其说明。这个文件应该提交到版本控制系统。

### .env
实际的环境变量配置文件，包含敏感信息，不应提交到版本控制系统。

## 配置分类

### 应用基础配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| APP_NAME | 量化交易平台 | 应用名称 |
| APP_VERSION | 0.1.0 | 应用版本 |
| DEBUG | false | 调试模式 |
| SECRET_KEY | (自动生成) | 应用密钥，至少32字符 |

### 数据库配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| DATABASE_URL | postgresql://postgres:password@db:5432/trading_db | PostgreSQL 连接URL |
| INFLUXDB_URL | http://influxdb:8086 | InfluxDB 连接URL |
| INFLUXDB_TOKEN | (自动生成) | InfluxDB 认证令牌 |
| INFLUXDB_ORG | trading-org | InfluxDB 组织名 |
| INFLUXDB_BUCKET | market-data | InfluxDB 存储桶名 |
| REDIS_URL | redis://redis:6379/0 | Redis 连接URL |

### JWT 认证配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| JWT_ALGORITHM | HS256 | JWT 签名算法 |
| JWT_ACCESS_TOKEN_EXPIRE_MINUTES | 30 | 访问令牌过期时间（分钟） |
| JWT_REFRESH_TOKEN_EXPIRE_DAYS | 7 | 刷新令牌过期时间（天） |

### 交易接口配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| TQSDK_AUTH | (可选) | 天勤量化认证令牌 |
| TQSDK_ACCOUNT | (可选) | 天勤量化交易账户 |

### 风险管理配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| MAX_DAILY_LOSS_PERCENT | 5.0 | 最大日损失百分比 |
| MAX_POSITION_PERCENT | 20.0 | 最大持仓百分比 |
| MAX_ORDERS_PER_MINUTE | 10 | 每分钟最大订单数 |

### Docker 部署配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| DB_INIT_RETRY_COUNT | 5 | 数据库初始化重试次数 |
| DB_INIT_RETRY_DELAY | 2 | 重试延迟（秒） |
| DB_INIT_TIMEOUT | 30 | 初始化超时时间（秒） |
| HEALTH_CHECK_INTERVAL | 30s | 健康检查间隔 |
| HEALTH_CHECK_TIMEOUT | 10s | 健康检查超时 |
| HEALTH_CHECK_RETRIES | 3 | 健康检查重试次数 |

### 端口配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| BACKEND_PORT | 8000 | 后端服务端口 |
| FRONTEND_PORT | 3000 | 前端服务端口 |
| POSTGRES_PORT | 5432 | PostgreSQL 端口 |
| INFLUXDB_PORT | 8086 | InfluxDB 端口 |
| REDIS_PORT | 6379 | Redis 端口 |

## 环境特定配置

### 开发环境 (development)

```bash
DEBUG=true
DATABASE_URL=postgresql://postgres:postgres123@localhost:5432/trading_db
INFLUXDB_URL=http://localhost:8086
REDIS_URL=redis://localhost:6379/0
DEV_CORS_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]
```

### Docker 环境 (docker)

```bash
DEBUG=false
DATABASE_URL=postgresql://postgres:postgres123@db:5432/trading_db
INFLUXDB_URL=http://influxdb:8086
REDIS_URL=redis://redis:6379/0
```

### 生产环境 (production)

```bash
DEBUG=false
DATABASE_URL=postgresql://postgres:CHANGE_ME@db:5432/trading_db
PROD_CORS_ORIGINS=["https://yourdomain.com"]
PROD_SECURE_COOKIES=true
PROD_HTTPS_ONLY=true
PROMETHEUS_ENABLED=true
GRAFANA_ENABLED=true
```

## 配置验证

### 自动验证

配置验证脚本会自动检查以下内容：

1. **必需变量检查**: 确保所有必需的环境变量都已设置
2. **格式验证**: 验证URL、数值等格式的正确性
3. **安全检查**: 检查密钥强度和默认值使用情况
4. **Docker兼容性**: 检查配置是否适合容器环境
5. **完整性检查**: 与示例文件比较，发现缺失的配置

### 验证结果

- ✅ **通过**: 配置完全正确
- ⚠️ **警告**: 配置可用但有改进建议
- ❌ **错误**: 配置有问题，需要修复

## 安全最佳实践

### 1. 密钥管理

- 使用强密钥（至少32字符）
- 定期轮换密钥
- 不要在代码中硬编码密钥
- 生产环境必须更改所有默认密钥

### 2. 数据库安全

- 使用强密码
- 限制数据库访问权限
- 启用SSL连接（生产环境）
- 定期备份数据

### 3. 网络安全

- 配置正确的CORS域名
- 使用HTTPS（生产环境）
- 启用安全Cookie
- 限制网络访问

### 4. 监控和日志

- 启用访问日志
- 监控异常活动
- 设置告警机制
- 定期审计配置

## 故障排除

### 常见问题

#### 1. 数据库连接失败

**症状**: 应用启动时数据库连接错误

**解决方案**:
- 检查 `DATABASE_URL` 格式
- 确认数据库服务已启动
- 验证用户名和密码
- 检查网络连接

#### 2. JWT 认证失败

**症状**: 用户登录后立即失效

**解决方案**:
- 检查 `SECRET_KEY` 是否正确设置
- 确认 JWT 过期时间配置
- 验证时钟同步

#### 3. CORS 错误

**症状**: 前端无法访问后端API

**解决方案**:
- 检查 `CORS_ORIGINS` 配置
- 确认前端域名正确
- 验证协议（HTTP/HTTPS）匹配

#### 4. 容器间通信失败

**症状**: Docker 容器无法相互访问

**解决方案**:
- 使用容器名而不是 localhost
- 检查 Docker 网络配置
- 验证端口映射

### 调试技巧

#### 1. 启用调试模式

```bash
DEBUG=true
LOG_LEVEL=DEBUG
```

#### 2. 检查配置加载

```python
from app.core.config import settings
print(settings.dict())
```

#### 3. 验证数据库连接

```bash
python -c "from app.core.database import engine; print(engine.execute('SELECT 1').scalar())"
```

#### 4. 测试Redis连接

```bash
python -c "from app.core.database import redis_client; print(redis_client.ping())"
```

## 配置模板

### 最小配置模板

```bash
# 基础配置
APP_NAME=量化交易平台
SECRET_KEY=your-32-character-secret-key-here
DEBUG=false

# 数据库
DATABASE_URL=postgresql://user:pass@host:5432/db
INFLUXDB_URL=http://influxdb:8086
INFLUXDB_TOKEN=your-influxdb-token
REDIS_URL=redis://redis:6379/0

# JWT
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 完整配置模板

参考 `.env.example` 文件获取完整的配置模板。

## 配置管理工具

### generate_config.py

配置生成脚本，支持：
- 多环境配置生成
- 交互式配置
- 安全密钥生成
- 配置合并

### validate_config.py

配置验证脚本，支持：
- 格式验证
- 安全检查
- 完整性验证
- 详细错误报告

## 更新和维护

### 配置更新流程

1. 备份现有配置
2. 更新配置文件
3. 运行验证脚本
4. 重启应用服务
5. 验证功能正常

### 版本兼容性

- 向后兼容：新版本支持旧配置
- 废弃通知：提前通知配置变更
- 迁移脚本：提供自动迁移工具

### 配置审计

定期审计配置：
- 检查安全设置
- 验证性能参数
- 更新过期配置
- 清理无用配置

## 参考资料

- [Pydantic Settings 文档](https://pydantic-docs.helpmanual.io/usage/settings/)
- [Docker Compose 环境变量](https://docs.docker.com/compose/environment-variables/)
- [PostgreSQL 连接字符串](https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNSTRING)
- [Redis 连接URL](https://redis.io/topics/clients#redis-uri-scheme)