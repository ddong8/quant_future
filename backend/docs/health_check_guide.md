# 数据库健康检查机制指南

## 概述

数据库健康检查机制提供了全面的数据库连接状态监控、初始化状态验证和系统就绪检查功能，确保应用在容器环境中的可靠启动和运行。

## 核心组件

### 1. DatabaseHealthChecker 服务

位置：`app/services/health_check_service.py`

主要功能：
- PostgreSQL 数据库健康检查
- InfluxDB 时序数据库健康检查  
- Redis 缓存数据库健康检查
- 数据库初始化状态验证
- 系统就绪等待逻辑

### 2. 健康检查 API 端点

位置：`app/api/v1/health.py`

提供的端点：
- `GET /api/v1/health/` - 基础健康检查
- `GET /api/v1/health/detailed` - 详细健康检查
- `GET /api/v1/health/database` - 数据库健康检查
- `GET /api/v1/health/initialization` - 初始化状态检查
- `GET /api/v1/health/readiness` - 就绪检查
- `GET /api/v1/health/liveness` - 存活检查

### 3. 命令行工具

- `check_db_status.py` - 数据库状态检查脚本
- `wait_for_db.py` - 等待数据库就绪脚本

## 健康检查类型

### 基础健康检查

最简单的健康检查，仅验证 PostgreSQL 连接：

```bash
curl http://localhost:8000/api/v1/health/
```

响应示例：
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00.000Z",
  "service": "trading-platform",
  "version": "0.1.0"
}
```

### 详细健康检查

全面的健康检查，包含所有数据库服务：

```bash
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/health/detailed
```

响应示例：
```json
{
  "success": true,
  "data": {
    "overall_status": "healthy",
    "total_response_time_ms": 45.67,
    "timestamp": "2024-01-01T12:00:00.000Z",
    "checks": {
      "postgresql": {
        "service": "postgresql",
        "status": "healthy",
        "response_time_ms": 12.34,
        "connection_count": 5,
        "database_size": "10 MB",
        "version": "13.8"
      },
      "influxdb": {
        "service": "influxdb",
        "status": "healthy",
        "response_time_ms": 23.45,
        "health_status": "pass",
        "organization": "trading-org",
        "bucket": "market-data"
      },
      "redis": {
        "service": "redis",
        "status": "healthy",
        "response_time_ms": 8.90,
        "version": "6.2.6",
        "connected_clients": 3,
        "used_memory": "2.1M"
      }
    },
    "summary": {
      "total_checks": 3,
      "healthy": 3,
      "warning": 0,
      "critical": 0
    }
  }
}
```

### 就绪检查 (Readiness Probe)

用于容器编排，检查应用是否准备好接收流量：

```bash
curl http://localhost:8000/api/v1/health/readiness
```

响应示例：
```json
{
  "ready": true,
  "timestamp": "2024-01-01T12:00:00.000Z",
  "checks": {
    "database": "healthy",
    "initialization": "healthy"
  }
}
```

### 存活检查 (Liveness Probe)

用于容器编排，检查应用是否仍在运行：

```bash
curl http://localhost:8000/api/v1/health/liveness
```

响应示例：
```json
{
  "alive": true,
  "timestamp": "2024-01-01T12:00:00.000Z",
  "service": "trading-platform"
}
```

## 状态级别

### healthy (健康)
- 所有检查项正常
- 响应时间在正常范围内
- 服务完全可用

### warning (警告)
- 服务可用但性能下降
- 响应时间超过警告阈值（1秒）
- 需要关注但不影响基本功能

### critical (严重)
- 服务不可用或严重异常
- 响应时间超过严重阈值（5秒）
- 需要立即处理

## 使用场景

### 1. 应用启动时的依赖检查

在应用启动时等待数据库就绪：

```python
from app.services.health_check_service import health_checker

# 等待数据库就绪
db_ready = await health_checker.wait_for_database_ready(
    max_wait_time=60,
    check_interval=2
)

if not db_ready:
    raise SystemError("数据库未在指定时间内就绪")
```

### 2. Docker Compose 健康检查

在 `docker-compose.yml` 中配置健康检查：

```yaml
services:
  backend:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### 3. Kubernetes 探针配置

```yaml
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: backend
    livenessProbe:
      httpGet:
        path: /api/v1/health/liveness
        port: 8000
      initialDelaySeconds: 30
      periodSeconds: 10
    readinessProbe:
      httpGet:
        path: /api/v1/health/readiness
        port: 8000
      initialDelaySeconds: 5
      periodSeconds: 5
```

### 4. 命令行检查

使用提供的脚本进行检查：

```bash
# 检查数据库状态
python check_db_status.py

# 等待数据库就绪
python wait_for_db.py --timeout 60 --interval 2

# 静默模式等待
python wait_for_db.py --quiet --timeout 30

# 同时检查初始化状态
python wait_for_db.py --check-init
```

## 配置参数

### 环境变量配置

```bash
# 数据库初始化配置
DB_INIT_TIMEOUT=30          # 初始化超时时间（秒）
DB_INIT_RETRY_COUNT=5       # 重试次数
DB_INIT_RETRY_DELAY=2       # 重试延迟（秒）

# 健康检查配置
HEALTH_CHECK_INTERVAL=30s   # 检查间隔
HEALTH_CHECK_TIMEOUT=10s    # 检查超时
HEALTH_CHECK_RETRIES=3      # 重试次数
```

### 代码配置

```python
class DatabaseHealthChecker:
    def __init__(self):
        self.check_timeout = 10         # 检查超时时间（秒）
        self.warning_threshold = 1000   # 警告阈值（毫秒）
        self.critical_threshold = 5000  # 严重阈值（毫秒）
```

## 监控和告警

### 1. 响应时间监控

- 警告阈值：1000ms
- 严重阈值：5000ms
- 建议设置监控告警

### 2. 连接数监控

监控数据库连接数，防止连接池耗尽：

```sql
SELECT count(*) FROM pg_stat_activity WHERE state = 'active';
```

### 3. 磁盘空间监控

监控数据库磁盘使用情况：

```sql
SELECT pg_size_pretty(pg_database_size(current_database()));
```

## 故障排除

### 常见问题

#### 1. PostgreSQL 连接失败

**症状**：
```json
{
  "service": "postgresql",
  "status": "critical",
  "error": "connection refused"
}
```

**解决方案**：
- 检查数据库服务是否启动
- 验证连接字符串配置
- 检查网络连接和防火墙设置
- 确认数据库用户权限

#### 2. InfluxDB 连接超时

**症状**：
```json
{
  "service": "influxdb",
  "status": "critical",
  "error": "timeout"
}
```

**解决方案**：
- 检查 InfluxDB 服务状态
- 验证认证令牌
- 检查组织和存储桶配置
- 确认网络连接

#### 3. Redis 连接异常

**症状**：
```json
{
  "service": "redis",
  "status": "critical",
  "error": "connection error"
}
```

**解决方案**：
- 检查 Redis 服务状态
- 验证连接URL配置
- 检查内存使用情况
- 确认网络连接

#### 4. 初始化状态异常

**症状**：
```json
{
  "service": "database_initialization",
  "status": "critical",
  "missing_tables": ["users", "strategies"]
}
```

**解决方案**：
- 运行数据库初始化脚本
- 检查数据库权限
- 验证模型定义
- 重新创建缺失的表

### 调试技巧

#### 1. 启用详细日志

```bash
export LOG_LEVEL=DEBUG
python check_db_status.py
```

#### 2. 单独测试各个服务

```bash
# 测试 PostgreSQL
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/health/services/postgresql

# 测试 InfluxDB
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/health/services/influxdb

# 测试 Redis
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/health/services/redis
```

#### 3. 检查应用启动日志

```bash
docker logs backend-container
```

查找健康检查相关的日志信息。

## 最佳实践

### 1. 容器启动顺序

使用 `depends_on` 和健康检查确保正确的启动顺序：

```yaml
services:
  backend:
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
      influxdb:
        condition: service_healthy
```

### 2. 优雅启动

在应用启动时实现优雅的等待逻辑：

```python
# 等待数据库就绪
await health_checker.wait_for_database_ready()

# 执行健康检查
health_result = await health_checker.perform_comprehensive_health_check()

# 根据结果决定是否继续启动
if health_result["overall_status"] == "critical":
    raise SystemError("关键服务不可用")
```

### 3. 监控集成

将健康检查结果集成到监控系统：

```python
# 定期执行健康检查并上报结果
async def periodic_health_check():
    result = await health_checker.perform_comprehensive_health_check()
    # 上报到监控系统
    monitoring_service.report_health_status(result)
```

### 4. 告警配置

设置合适的告警规则：

- 连续3次健康检查失败时告警
- 响应时间超过阈值时告警
- 关键服务不可用时立即告警

## API 参考

### 端点列表

| 端点 | 方法 | 认证 | 描述 |
|------|------|------|------|
| `/api/v1/health/` | GET | 否 | 基础健康检查 |
| `/api/v1/health/detailed` | GET | 是 | 详细健康检查 |
| `/api/v1/health/database` | GET | 是 | 数据库健康检查 |
| `/api/v1/health/initialization` | GET | 是 | 初始化状态检查 |
| `/api/v1/health/readiness` | GET | 否 | 就绪检查 |
| `/api/v1/health/liveness` | GET | 否 | 存活检查 |
| `/api/v1/health/services/{service}` | GET | 是 | 特定服务检查 |
| `/api/v1/health/summary` | GET | 是 | 健康检查摘要 |

### 响应格式

#### 成功响应

```json
{
  "success": true,
  "data": {
    // 健康检查数据
  },
  "message": "操作成功"
}
```

#### 错误响应

```json
{
  "success": false,
  "error": {
    "code": "HEALTH_CHECK_FAILED",
    "message": "健康检查失败",
    "details": "具体错误信息"
  }
}
```

## 扩展和定制

### 添加自定义检查

```python
class CustomHealthChecker(DatabaseHealthChecker):
    async def check_custom_service(self) -> Dict[str, Any]:
        """自定义服务健康检查"""
        # 实现自定义检查逻辑
        pass
    
    async def perform_comprehensive_health_check(self) -> Dict[str, Any]:
        # 调用父类方法
        result = await super().perform_comprehensive_health_check()
        
        # 添加自定义检查
        custom_check = await self.check_custom_service()
        result["checks"]["custom_service"] = custom_check
        
        return result
```

### 自定义阈值

```python
# 在配置中定义自定义阈值
HEALTH_CHECK_WARNING_THRESHOLD = 2000  # 2秒
HEALTH_CHECK_CRITICAL_THRESHOLD = 10000  # 10秒

# 在健康检查器中使用
health_checker.warning_threshold = HEALTH_CHECK_WARNING_THRESHOLD
health_checker.critical_threshold = HEALTH_CHECK_CRITICAL_THRESHOLD
```

这个健康检查机制为量化交易平台提供了全面的数据库状态监控和系统就绪验证功能，确保在容器环境中的可靠部署和运行。