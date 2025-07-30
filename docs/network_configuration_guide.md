# 容器间网络通信配置指南

## 概述

本文档详细说明了量化交易平台中容器间网络通信的配置，包括服务发现、代理配置、网络安全和故障排除。

## 网络架构

### 服务拓扑

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Browser   │───▶│  Frontend   │───▶│   Backend   │
│             │    │   (3000)    │    │   (8000)    │
└─────────────┘    └─────────────┘    └─────────────┘
                           │                   │
                           │                   ▼
                           │          ┌─────────────┐
                           │          │ PostgreSQL  │
                           │          │   (5432)    │
                           │          └─────────────┘
                           │                   │
                           │                   ▼
                           │          ┌─────────────┐
                           │          │    Redis    │
                           │          │   (6379)    │
                           │          └─────────────┘
                           │                   │
                           │                   ▼
                           │          ┌─────────────┐
                           └─────────▶│  InfluxDB   │
                                      │   (8086)    │
                                      └─────────────┘
```

### 网络配置

#### Docker 网络
```yaml
networks:
  default:
    name: trading_network
```

所有服务运行在同一个 Docker 网络中，可以通过服务名进行通信。

## 服务间通信配置

### 1. 前端到后端通信

#### 开发环境 (Vite 代理)

```typescript
// vite.config.ts
server: {
  proxy: {
    '/api': {
      target: 'http://backend:8000',  // 使用容器名
      changeOrigin: true,
      secure: false,
      timeout: 30000
    },
    '/ws': {
      target: 'ws://backend:8000',    // WebSocket 代理
      ws: true,
      changeOrigin: true
    }
  }
}
```

#### 生产环境 (Nginx 代理)

```nginx
# nginx.conf
location /api/ {
    proxy_pass http://backend:8000;  # 使用容器名
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}

location /api/v1/ws {
    proxy_pass http://backend:8000;  # WebSocket 代理
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

### 2. 后端到数据库通信

#### 数据库连接配置

```yaml
# docker-compose.yml
environment:
  - DATABASE_URL=postgresql://postgres:password@postgres:5432/trading_db
  - REDIS_URL=redis://redis:6379/0
  - INFLUXDB_URL=http://influxdb:8086
```

#### 连接池配置

```yaml
environment:
  - DB_POOL_SIZE=10
  - DB_MAX_OVERFLOW=20
  - DB_POOL_RECYCLE=300
  - REDIS_MAX_CONNECTIONS=50
```

## 环境变量配置

### 前端环境变量

#### 开发环境
```bash
# 浏览器访问的API地址
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_WS_BASE_URL=ws://localhost:8000/api/v1/ws

# 开发服务器代理目标（容器内部通信）
VITE_API_PROXY_TARGET=http://backend:8000
VITE_WS_PROXY_TARGET=ws://backend:8000
```

#### 生产环境
```bash
# 生产环境API地址
VITE_API_BASE_URL=https://yourdomain.com/api/v1
VITE_WS_BASE_URL=wss://yourdomain.com/api/v1/ws

# Nginx后端配置
NGINX_BACKEND_HOST=backend
NGINX_BACKEND_PORT=8000
```

### 后端环境变量

```bash
# 数据库连接（使用容器名）
DATABASE_URL=postgresql://postgres:password@postgres:5432/trading_db
REDIS_URL=redis://redis:6379/0
INFLUXDB_URL=http://influxdb:8086

# CORS配置
DEV_CORS_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]
PROD_CORS_ORIGINS=["https://yourdomain.com"]
```

## 服务依赖配置

### 启动顺序控制

```yaml
# docker-compose.yml
services:
  backend:
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      influxdb:
        condition: service_healthy
      db-init:
        condition: service_completed_successfully

  frontend:
    depends_on:
      backend:
        condition: service_healthy
```

### 健康检查配置

#### 数据库服务
```yaml
postgres:
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U postgres"]
    interval: 10s
    timeout: 5s
    retries: 5

redis:
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
    interval: 10s
    timeout: 3s
    retries: 3

influxdb:
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8086/health"]
    interval: 30s
    timeout: 10s
    retries: 3
```

#### 应用服务
```yaml
backend:
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health/readiness"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 40s

frontend:
  healthcheck:
    test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:3000/"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 60s
```

## 网络安全配置

### 1. 端口暴露控制

```yaml
# 只暴露必要的端口到主机
ports:
  - "3000:3000"  # 前端服务
  - "8000:8000"  # 后端API
  # 数据库端口不暴露到主机，仅容器内部访问
```

### 2. 网络隔离

```yaml
# 使用自定义网络
networks:
  default:
    name: trading_network
    driver: bridge
```

### 3. 防火墙配置

```bash
# 主机防火墙规则示例
iptables -A INPUT -p tcp --dport 3000 -j ACCEPT  # 前端
iptables -A INPUT -p tcp --dport 8000 -j ACCEPT  # 后端API
iptables -A INPUT -p tcp --dport 5432 -j DROP    # 阻止外部访问数据库
```

## 开发环境配置

### 热重载支持

```yaml
# docker-compose.dev.yml
frontend:
  volumes:
    - ./frontend:/app
    - /app/node_modules
  environment:
    - VITE_API_PROXY_TARGET=http://backend:8000
  command: npm run dev -- --host 0.0.0.0

backend:
  volumes:
    - ./backend:/app
  environment:
    - DEBUG=true
  command: uvicorn app.main:app --host 0.0.0.0 --reload
```

### 开发工具访问

```bash
# 访问开发工具容器
docker-compose -f docker-compose.yml -f docker-compose.dev.yml --profile tools up

# 进入容器调试
docker-compose exec backend bash
docker-compose exec frontend sh
```

## 生产环境配置

### 负载均衡

```yaml
# docker-compose.prod.yml
backend:
  deploy:
    replicas: 3
  environment:
    - WORKER_PROCESSES=4

nginx:
  image: nginx:alpine
  volumes:
    - ./nginx/nginx.conf:/etc/nginx/nginx.conf
  ports:
    - "80:80"
    - "443:443"
```

### SSL/TLS 配置

```nginx
# nginx.conf for production
server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header X-Forwarded-Proto https;
    }
}
```

## 网络监控

### 连通性检查

```bash
# 使用验证脚本
python validate_network_connectivity.py

# 手动测试
docker-compose exec frontend wget -q --spider http://backend:8000/api/v1/health/
docker-compose exec backend nc -z postgres 5432
```

### 网络流量监控

```bash
# 查看网络统计
docker stats

# 查看网络连接
docker-compose exec backend netstat -an

# 查看DNS解析
docker-compose exec backend nslookup postgres
```

## 故障排除

### 常见问题

#### 1. 服务无法解析

**症状**: `Name or service not known`

**解决方案**:
```bash
# 检查网络配置
docker network ls
docker network inspect trading_network

# 检查服务状态
docker-compose ps

# 重启网络
docker-compose down
docker-compose up -d
```

#### 2. 连接超时

**症状**: `Connection timed out`

**解决方案**:
```bash
# 检查服务健康状态
docker-compose ps

# 查看服务日志
docker-compose logs backend
docker-compose logs frontend

# 测试端口连通性
docker-compose exec frontend nc -z backend 8000
```

#### 3. 代理配置错误

**症状**: 前端无法访问后端API

**解决方案**:
```bash
# 检查Vite配置
cat frontend/vite.config.ts

# 检查环境变量
docker-compose exec frontend env | grep VITE

# 重启前端服务
docker-compose restart frontend
```

#### 4. CORS错误

**症状**: `Access-Control-Allow-Origin` 错误

**解决方案**:
```bash
# 检查后端CORS配置
docker-compose exec backend env | grep CORS

# 更新CORS配置
# 在docker-compose.yml中添加正确的CORS域名
```

### 调试工具

#### 网络诊断命令

```bash
# 在容器内执行网络诊断
docker-compose exec backend sh -c "
  echo '=== 网络接口 ===' &&
  ip addr show &&
  echo '=== 路由表 ===' &&
  ip route show &&
  echo '=== DNS配置 ===' &&
  cat /etc/resolv.conf &&
  echo '=== 端口监听 ===' &&
  netstat -tlnp
"
```

#### 连通性测试

```bash
# 测试所有服务连通性
services=(postgres redis influxdb backend frontend)
for service in "${services[@]}"; do
  echo "测试连接到 $service..."
  docker-compose exec backend nc -z $service $(docker-compose port $service | cut -d: -f2) && echo "✅ $service 连接成功" || echo "❌ $service 连接失败"
done
```

## 性能优化

### 网络性能调优

```yaml
# docker-compose.yml
services:
  backend:
    sysctls:
      - net.core.somaxconn=65535
      - net.ipv4.tcp_max_syn_backlog=65535
    ulimits:
      nofile:
        soft: 65535
        hard: 65535
```

### 连接池优化

```yaml
environment:
  # PostgreSQL连接池
  - DB_POOL_SIZE=20
  - DB_MAX_OVERFLOW=40
  - DB_POOL_RECYCLE=3600
  
  # Redis连接池
  - REDIS_MAX_CONNECTIONS=100
  - REDIS_CONNECTION_TIMEOUT=5
```

## 最佳实践

### 1. 使用容器名进行通信
- ✅ `http://backend:8000`
- ❌ `http://localhost:8000`

### 2. 配置适当的超时时间
- 开发环境：较短超时，快速反馈
- 生产环境：较长超时，提高稳定性

### 3. 实现健康检查
- 所有服务都应配置健康检查
- 使用健康检查控制启动顺序

### 4. 监控网络状态
- 定期检查连通性
- 监控网络延迟和吞吐量

### 5. 安全配置
- 最小化端口暴露
- 使用网络隔离
- 配置适当的防火墙规则

这个网络配置确保了容器间的可靠通信和高性能的服务交互。