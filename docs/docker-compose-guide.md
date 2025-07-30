# Docker Compose 部署指南

## 概述

本项目提供了多个 Docker Compose 配置文件，支持不同的部署环境和使用场景。

## 配置文件说明

### 基础配置文件

- `docker-compose.yml` - 基础配置，包含所有核心服务
- `docker-compose.dev.yml` - 开发环境扩展配置
- `docker-compose.prod.yml` - 生产环境扩展配置

### 服务组件

#### 数据库服务
- **postgres** - PostgreSQL 主数据库
- **redis** - Redis 缓存数据库
- **influxdb** - InfluxDB 时序数据库

#### 应用服务
- **db-init** - 数据库初始化容器
- **backend** - FastAPI 后端服务
- **frontend** - Vue.js 前端服务

#### 辅助服务
- **dev-tools** - 开发工具容器（仅开发环境）
- **nginx** - 反向代理服务器（仅生产环境）

## 使用方法

### 开发环境

```bash
# 启动开发环境
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# 后台运行
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# 启动开发工具容器
docker-compose -f docker-compose.yml -f docker-compose.dev.yml --profile tools up

# 查看日志
docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs -f

# 停止服务
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down
```

### 生产环境

```bash
# 设置环境变量
export POSTGRES_PASSWORD=your-secure-password
export SECRET_KEY=your-super-secret-key
export INFLUXDB_ADMIN_TOKEN=your-influxdb-token

# 启动生产环境
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 启动包含 Nginx 的完整生产环境
docker-compose -f docker-compose.yml -f docker-compose.prod.yml --profile nginx up -d

# 查看服务状态
docker-compose -f docker-compose.yml -f docker-compose.prod.yml ps

# 查看日志
docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f backend
```

### 仅启动数据库服务

```bash
# 仅启动数据库相关服务
docker-compose up postgres redis influxdb

# 运行数据库初始化
docker-compose up db-init
```

## 数据库初始化流程

### 初始化容器工作流程

1. **等待数据库就绪** - 检查所有数据库服务是否可用
2. **执行健康检查** - 验证数据库连接和基本功能
3. **运行初始化脚本** - 创建表结构和初始数据
4. **验证初始化结果** - 确认初始化是否成功完成
5. **创建完成标记** - 标记初始化已完成

### 初始化状态检查

```bash
# 检查初始化状态
docker-compose exec backend python check_init_status.py

# 等待初始化完成
docker-compose exec backend python check_init_status.py --wait

# 手动运行初始化
docker-compose exec backend python run_init.py
```

## 环境变量配置

### 必需的环境变量（生产环境）

```bash
# 数据库密码
POSTGRES_PASSWORD=your-secure-password

# 应用密钥
SECRET_KEY=your-super-secret-key-at-least-32-characters

# InfluxDB 配置
INFLUXDB_ADMIN_TOKEN=your-influxdb-admin-token
```

### 可选的环境变量

```bash
# 数据库配置
POSTGRES_DB=trading_db
POSTGRES_USER=postgres

# Redis 配置
REDIS_PASSWORD=your-redis-password

# InfluxDB 配置
INFLUXDB_ORG=trading-org
INFLUXDB_BUCKET=market-data

# 应用配置
LOG_LEVEL=INFO
BACKEND_WORKERS=4

# 前端配置
FRONTEND_API_URL=http://localhost:8000/api/v1
FRONTEND_WS_URL=ws://localhost:8000/api/v1/ws

# 数据目录
DATA_DIR=./data
```

## 健康检查

### 服务健康检查

所有服务都配置了健康检查，可以通过以下方式查看：

```bash
# 查看所有服务健康状态
docker-compose ps

# 查看特定服务健康状态
docker-compose ps backend

# 手动执行健康检查
curl http://localhost:8000/api/v1/health/
```

### 健康检查端点

- `GET /api/v1/health/` - 基础健康检查
- `GET /api/v1/health/readiness` - 就绪检查
- `GET /api/v1/health/liveness` - 存活检查
- `GET /api/v1/health/detailed` - 详细健康检查

## 数据持久化

### 数据卷

- `postgres_data` - PostgreSQL 数据
- `redis_data` - Redis 数据
- `influxdb_data` - InfluxDB 数据
- `db_init_status` - 初始化状态标记

### 备份和恢复

```bash
# 备份 PostgreSQL 数据
docker-compose exec postgres pg_dump -U postgres trading_db > backup.sql

# 恢复 PostgreSQL 数据
docker-compose exec -T postgres psql -U postgres trading_db < backup.sql

# 备份所有数据卷
docker run --rm -v trading_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz -C /data .
```

## 日志管理

### 日志位置

- 应用日志：`./logs/`
- 容器日志：通过 `docker-compose logs` 查看

### 日志查看

```bash
# 查看所有服务日志
docker-compose logs

# 查看特定服务日志
docker-compose logs backend

# 实时跟踪日志
docker-compose logs -f backend

# 查看最近的日志
docker-compose logs --tail=100 backend
```

## 网络配置

### 默认网络

所有服务运行在 `trading_network` 网络中，服务间可以通过服务名进行通信。

### 端口映射

- **3000** - 前端服务
- **8000** - 后端 API 服务
- **5432** - PostgreSQL 数据库
- **6379** - Redis 缓存
- **8086** - InfluxDB 数据库

## 故障排除

### 常见问题

#### 1. 数据库连接失败

```bash
# 检查数据库服务状态
docker-compose ps postgres

# 查看数据库日志
docker-compose logs postgres

# 测试数据库连接
docker-compose exec backend python wait_for_db.py
```

#### 2. 初始化容器失败

```bash
# 查看初始化日志
docker-compose logs db-init

# 检查初始化状态
docker-compose exec backend python check_init_status.py

# 手动重新初始化
docker-compose run --rm db-init python run_init.py
```

#### 3. 后端服务启动失败

```bash
# 查看后端日志
docker-compose logs backend

# 检查健康状态
curl http://localhost:8000/api/v1/health/

# 进入容器调试
docker-compose exec backend bash
```

#### 4. 前端服务无法访问后端

```bash
# 检查网络连接
docker-compose exec frontend curl http://backend:8000/api/v1/health/

# 检查环境变量
docker-compose exec frontend env | grep VITE
```

### 调试技巧

#### 1. 进入容器调试

```bash
# 进入后端容器
docker-compose exec backend bash

# 进入数据库容器
docker-compose exec postgres psql -U postgres trading_db
```

#### 2. 查看容器资源使用

```bash
# 查看资源使用情况
docker stats

# 查看特定容器资源使用
docker stats trading_backend
```

#### 3. 重建服务

```bash
# 重建特定服务
docker-compose build backend

# 强制重建所有服务
docker-compose build --no-cache

# 重建并重启服务
docker-compose up --build backend
```

## 性能优化

### 生产环境优化

1. **使用多个 Worker 进程**
   ```bash
   export BACKEND_WORKERS=4
   ```

2. **配置资源限制**
   ```yaml
   services:
     backend:
       deploy:
         resources:
           limits:
             memory: 1G
             cpus: '0.5'
   ```

3. **启用 Nginx 反向代理**
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml --profile nginx up -d
   ```

### 监控和告警

1. **启用健康检查**
   - 所有服务都配置了健康检查
   - 可以集成到监控系统中

2. **日志聚合**
   - 配置日志收集和分析
   - 设置告警规则

## 安全考虑

### 生产环境安全

1. **使用强密码**
   - 为所有数据库设置强密码
   - 定期轮换密钥

2. **网络安全**
   - 限制端口暴露
   - 使用防火墙规则

3. **数据加密**
   - 启用数据库连接加密
   - 使用 HTTPS

4. **访问控制**
   - 限制容器权限
   - 使用非 root 用户运行服务

## 扩展和定制

### 添加新服务

1. 在 `docker-compose.yml` 中定义新服务
2. 配置依赖关系和网络
3. 添加健康检查
4. 更新文档

### 自定义配置

1. 创建自定义的 override 文件
2. 使用环境变量覆盖默认配置
3. 挂载自定义配置文件

这个指南提供了完整的 Docker Compose 部署和管理说明，涵盖了从开发到生产的各种场景。