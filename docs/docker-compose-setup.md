# Docker Compose 部署指南

本文档介绍如何使用 Docker Compose 部署量化交易平台，包括自动化数据库初始化和完整的服务配置。

## 🚀 快速开始

### 1. 环境准备

确保系统已安装以下软件：

- Docker (版本 20.10+)
- Docker Compose (版本 2.0+)
- curl (用于健康检查)

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.template .env

# 根据需要修改配置
vim .env
```

### 3. 启动服务

使用提供的启动脚本：

```bash
# 启动所有服务
./start-trading-platform.sh

# 或者清理后启动
./start-trading-platform.sh start --clean

# 查看帮助
./start-trading-platform.sh help
```

或者直接使用 docker-compose：

```bash
# 构建并启动服务
docker-compose up -d --build

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

## 📋 服务架构

### 服务列表

| 服务名 | 容器名 | 端口 | 描述 |
|--------|--------|------|------|
| postgres | trading_postgres | 5432 | PostgreSQL 数据库 |
| redis | trading_redis | 6379 | Redis 缓存 |
| influxdb | trading_influxdb | 8086 | InfluxDB 时序数据库 |
| db-init | trading_db_init | - | 数据库初始化容器 |
| backend | trading_backend | 8000 | FastAPI 后端服务 |
| frontend | trading_frontend | 3000 | Vue.js 前端应用 |

### 启动顺序

```mermaid
graph TD
    A[PostgreSQL] --> D[db-init]
    B[Redis] --> D
    C[InfluxDB] --> D
    D --> E[Backend]
    E --> F[Frontend]
```

## 🔧 配置详解

### 环境变量配置

主要的环境变量配置项：

#### 数据库配置
```bash
# PostgreSQL
POSTGRES_DB=trading_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
DATABASE_URL=postgresql://postgres:password@postgres:5432/trading_db

# Redis
REDIS_URL=redis://redis:6379/0

# InfluxDB
INFLUXDB_URL=http://influxdb:8086
INFLUXDB_ADMIN_TOKEN=my-super-secret-auth-token
```

#### 应用配置
```bash
# 基础配置
APP_NAME=量化交易平台
SECRET_KEY=your-super-secret-key-change-this-in-production
DEBUG=true

# JWT 配置
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 数据库初始化

系统会自动执行以下初始化步骤：

1. **等待数据库就绪**：确保 PostgreSQL、Redis、InfluxDB 都正常运行
2. **健康检查**：验证所有数据库连接正常
3. **创建表结构**：执行数据库迁移，创建所有必需的表
4. **创建默认用户**：创建管理员、交易员、观察者账户
5. **验证初始化**：确认所有步骤成功完成

#### 默认用户账户

| 用户名 | 密码 | 角色 | 邮箱 |
|--------|------|------|------|
| admin | admin123 | 管理员 | admin@trading.com |
| trader | trader123 | 交易员 | trader@trading.com |
| observer | observer123 | 观察者 | observer@trading.com |

## 🔍 监控和调试

### 健康检查

所有服务都配置了健康检查：

```bash
# 检查后端服务健康状态
curl http://localhost:8000/api/v1/health/

# 检查前端服务
curl http://localhost:3000/

# 检查数据库连接
docker-compose exec backend python -c "
from app.services.health_check_service import health_checker
import asyncio
result = asyncio.run(health_checker.check_database_connection())
print(f'Database: {result[\"status\"]}')
"
```

### 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f db-init

# 查看初始化日志
docker-compose exec backend cat /var/log/trading/init.log
```

### 服务状态

```bash
# 查看容器状态
docker-compose ps

# 查看资源使用情况
docker stats

# 进入容器调试
docker-compose exec backend bash
docker-compose exec postgres psql -U postgres -d trading_db
```

## 🛠️ 常见问题

### 1. 数据库初始化失败

**症状**：backend 服务无法启动，提示数据库连接错误

**解决方案**：
```bash
# 查看初始化日志
docker-compose logs db-init

# 重新运行初始化
docker-compose restart db-init

# 手动运行初始化
docker-compose exec backend python init_db.py
```

### 2. 前端无法访问后端 API

**症状**：前端页面显示网络错误

**解决方案**：
```bash
# 检查后端服务状态
curl http://localhost:8000/api/v1/health/

# 检查网络配置
docker network ls
docker network inspect trading_network

# 重启服务
docker-compose restart backend frontend
```

### 3. 容器启动缓慢

**症状**：服务启动时间过长

**解决方案**：
```bash
# 检查资源使用情况
docker stats

# 调整资源限制（在 docker-compose.yml 中）
deploy:
  resources:
    limits:
      memory: 2G
      cpus: '1.0'
```

### 4. 数据持久化问题

**症状**：容器重启后数据丢失

**解决方案**：
```bash
# 检查卷挂载
docker volume ls
docker volume inspect trading_postgres_data

# 备份数据
docker-compose exec postgres pg_dump -U postgres trading_db > backup.sql

# 恢复数据
docker-compose exec -T postgres psql -U postgres trading_db < backup.sql
```

## 🔒 安全配置

### 生产环境配置

在生产环境中，请务必修改以下配置：

1. **更改默认密码**：
   ```bash
   # 数据库密码
   POSTGRES_PASSWORD=your-secure-password
   
   # JWT 密钥
   SECRET_KEY=your-super-secure-secret-key
   
   # InfluxDB 令牌
   INFLUXDB_ADMIN_TOKEN=your-secure-token
   ```

2. **禁用调试模式**：
   ```bash
   DEBUG=false
   LOG_LEVEL=WARNING
   ```

3. **配置 HTTPS**：
   ```bash
   # 使用反向代理（如 Nginx）配置 SSL
   # 更新 CORS 配置
   DEV_CORS_ORIGINS=["https://yourdomain.com"]
   ```

### 网络安全

```bash
# 限制端口暴露（仅在生产环境）
# 移除不必要的端口映射
ports:
  # - "5432:5432"  # 不要在生产环境暴露数据库端口
  # - "6379:6379"  # 不要暴露 Redis 端口
```

## 📊 性能优化

### 数据库优化

```bash
# PostgreSQL 配置优化
environment:
  - POSTGRES_SHARED_BUFFERS=256MB
  - POSTGRES_EFFECTIVE_CACHE_SIZE=1GB
  - POSTGRES_WORK_MEM=4MB
```

### 应用优化

```bash
# 后端性能配置
environment:
  - WORKER_PROCESSES=4
  - WORKER_CONNECTIONS=1000
  - DB_POOL_SIZE=20
  - DB_MAX_OVERFLOW=40
```

## 🔄 更新和维护

### 更新服务

```bash
# 拉取最新镜像
docker-compose pull

# 重新构建并启动
docker-compose up -d --build

# 清理旧镜像
docker image prune -f
```

### 备份和恢复

```bash
# 数据库备份
./scripts/backup-database.sh

# 完整备份
docker-compose exec postgres pg_dumpall -U postgres > full-backup.sql

# 恢复备份
docker-compose exec -T postgres psql -U postgres < full-backup.sql
```

## 📞 支持

如果遇到问题，请：

1. 查看日志文件
2. 运行配置验证脚本：`python3 validate_compose_config.py`
3. 检查服务健康状态
4. 参考故障排除指南

---

**注意**：本指南假设你已经熟悉 Docker 和 Docker Compose 的基本概念。如果需要更多帮助，请参考官方文档或联系技术支持。