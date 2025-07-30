# 后端容器优化指南

## 概述

本文档详细说明了后端容器的优化配置，包括 Dockerfile 改进、环境变量管理、启动流程优化和性能调优。

## Dockerfile 优化

### 多阶段构建

使用多阶段构建减少最终镜像大小：

```dockerfile
# 构建阶段
FROM python:3.11-slim as builder
# 安装构建依赖和Python包

# 运行阶段  
FROM python:3.11-slim as runtime
# 只复制必要的运行时文件
```

### 安全改进

1. **非 root 用户运行**
   ```dockerfile
   RUN groupadd -r appuser && useradd -r -g appuser appuser
   USER appuser
   ```

2. **最小化系统依赖**
   - 只安装必要的系统包
   - 清理 apt 缓存

3. **健康检查集成**
   ```dockerfile
   HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
       CMD curl -f http://localhost:8000/api/v1/health/ || exit 1
   ```

## 环境变量配置

### 分类管理

环境变量按功能分类管理：

#### 数据库连接配置
- `DATABASE_URL` - PostgreSQL 连接字符串
- `REDIS_URL` - Redis 连接字符串  
- `INFLUXDB_URL` - InfluxDB 连接字符串

#### 应用配置
- `SECRET_KEY` - 应用密钥
- `DEBUG` - 调试模式
- `LOG_LEVEL` - 日志级别
- `APP_NAME` - 应用名称

#### 性能配置
- `WORKER_PROCESSES` - 工作进程数
- `DB_POOL_SIZE` - 数据库连接池大小
- `REDIS_MAX_CONNECTIONS` - Redis 最大连接数

#### 健康检查配置
- `HEALTH_CHECK_INTERVAL` - 检查间隔
- `HEALTH_CHECK_TIMEOUT` - 检查超时
- `HEALTH_CHECK_RETRIES` - 重试次数

### 环境特定配置

#### 开发环境
```yaml
environment:
  - DEBUG=true
  - LOG_LEVEL=DEBUG
  - WORKER_PROCESSES=1
  - DB_POOL_SIZE=5
```

#### 生产环境
```yaml
environment:
  - DEBUG=false
  - LOG_LEVEL=INFO
  - WORKER_PROCESSES=4
  - DB_POOL_SIZE=20
```

## 启动流程优化

### 启动脚本 (start_backend.py)

提供完整的启动流程管理：

1. **环境验证**
   - 检查必需的环境变量
   - 验证配置格式

2. **依赖等待**
   - 等待数据库初始化完成
   - 执行启动前健康检查

3. **服务启动**
   - 根据环境选择启动模式
   - 配置 Uvicorn 参数

### 启动流程

```
环境验证 → 等待初始化 → 健康检查 → 启动服务器
```

## 健康检查配置

### 多层次健康检查

1. **容器级健康检查**
   ```yaml
   healthcheck:
     test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health/readiness"]
     interval: 30s
     timeout: 10s
     retries: 3
     start_period: 40s
   ```

2. **应用级健康检查**
   - `/api/v1/health/` - 基础健康检查
   - `/api/v1/health/readiness` - 就绪检查
   - `/api/v1/health/liveness` - 存活检查

### 健康检查端点

- **基础检查**: 验证应用基本功能
- **就绪检查**: 验证应用是否准备好接收流量
- **存活检查**: 验证应用是否仍在运行

## 性能优化

### 资源限制

```yaml
deploy:
  resources:
    limits:
      memory: 1G
      cpus: '0.5'
    reservations:
      memory: 512M
      cpus: '0.25'
```

### 连接池优化

#### PostgreSQL 连接池
```yaml
environment:
  - DB_POOL_SIZE=10          # 连接池大小
  - DB_MAX_OVERFLOW=20       # 最大溢出连接
  - DB_POOL_RECYCLE=300      # 连接回收时间
  - DB_POOL_PRE_PING=true    # 连接预检查
```

#### Redis 连接池
```yaml
environment:
  - REDIS_MAX_CONNECTIONS=50    # 最大连接数
  - REDIS_CONNECTION_TIMEOUT=5  # 连接超时
```

### 工作进程配置

#### 开发环境
- 单进程 + 热重载
- 较小的连接池

#### 生产环境
- 多进程 (CPU 核心数)
- 较大的连接池
- 无热重载

## 日志管理

### 日志配置

```yaml
environment:
  - LOG_LEVEL=INFO
  - LOG_FILE=/var/log/trading/backend.log
```

### 日志目录

- 容器内路径: `/var/log/trading/`
- 主机挂载: `./logs:/var/log/trading`

### 日志文件

- `backend_startup.log` - 启动日志
- `backend.log` - 应用日志
- `init.log` - 初始化日志

## 网络配置

### 容器网络

```yaml
networks:
  - default  # 使用默认网络
```

### 端口映射

```yaml
ports:
  - "8000:8000"  # HTTP API 端口
```

### 服务发现

容器间通过服务名通信：
- `postgres` - 数据库服务
- `redis` - 缓存服务
- `influxdb` - 时序数据库服务

## 依赖管理

### 服务依赖

```yaml
depends_on:
  postgres:
    condition: service_healthy
  redis:
    condition: service_healthy
  influxdb:
    condition: service_healthy
  db-init:
    condition: service_completed_successfully
```

### 启动顺序

1. 数据库服务启动并健康
2. 初始化容器运行并完成
3. 后端服务启动

## 数据卷配置

### 开发环境

```yaml
volumes:
  - ./backend:/app              # 代码热重载
  - ./logs:/var/log/trading     # 日志持久化
  - db_init_status:/var/lib/db-init  # 初始化状态
```

### 生产环境

```yaml
volumes:
  - ./logs:/var/log/trading     # 仅日志持久化
  - db_init_status:/var/lib/db-init  # 初始化状态
```

## 安全配置

### 密钥管理

1. **强密钥要求**
   - SECRET_KEY 至少 32 字符
   - 生产环境必须修改默认值

2. **环境变量保护**
   - 敏感信息通过环境变量传递
   - 不在代码中硬编码

### 用户权限

- 使用非 root 用户运行
- 最小权限原则

## 监控和调试

### 配置验证

使用 `validate_backend_config.py` 验证配置：

```bash
python validate_backend_config.py
```

### 启动调试

查看启动日志：

```bash
docker-compose logs backend
```

### 健康状态检查

```bash
curl http://localhost:8000/api/v1/health/detailed
```

## 故障排除

### 常见问题

#### 1. 启动超时

**症状**: 容器启动后长时间无响应

**解决方案**:
- 检查数据库初始化状态
- 增加启动超时时间
- 查看启动日志

#### 2. 健康检查失败

**症状**: 健康检查持续失败

**解决方案**:
- 检查健康检查端点
- 验证网络连接
- 查看应用日志

#### 3. 内存不足

**症状**: 容器被 OOM Killer 终止

**解决方案**:
- 增加内存限制
- 优化连接池配置
- 减少工作进程数

#### 4. 数据库连接失败

**症状**: 无法连接到数据库

**解决方案**:
- 检查数据库服务状态
- 验证连接字符串
- 检查网络连接

### 调试命令

```bash
# 进入容器调试
docker-compose exec backend bash

# 查看环境变量
docker-compose exec backend env

# 测试数据库连接
docker-compose exec backend python check_db_status.py

# 验证配置
docker-compose exec backend python validate_backend_config.py
```

## 最佳实践

### 开发环境

1. **启用热重载**
   - 代码变更自动重启
   - 快速开发迭代

2. **详细日志**
   - DEBUG 级别日志
   - 详细错误信息

3. **快速启动**
   - 较短的健康检查间隔
   - 较小的资源配置

### 生产环境

1. **性能优化**
   - 多进程配置
   - 连接池优化
   - 资源限制

2. **安全加固**
   - 禁用调试模式
   - 强密钥配置
   - 最小权限运行

3. **监控告警**
   - 健康检查监控
   - 资源使用监控
   - 错误日志告警

### 配置管理

1. **环境分离**
   - 不同环境使用不同配置
   - 敏感信息环境变量化

2. **配置验证**
   - 启动前验证配置
   - 自动化配置检查

3. **文档维护**
   - 配置变更文档化
   - 故障排除指南更新

这个优化配置确保了后端容器的高性能、高可用性和易维护性。