# 量化交易平台部署指南

## 系统要求

### 硬件要求
- **CPU**: 4核心以上
- **内存**: 8GB以上
- **存储**: 100GB以上SSD
- **网络**: 稳定的互联网连接

### 软件要求
- **操作系统**: Ubuntu 20.04+ / CentOS 8+ / macOS 10.15+
- **Python**: 3.9+
- **Node.js**: 16+
- **Docker**: 20.10+
- **Docker Compose**: 2.0+

## 快速部署

### 1. 克隆项目
```bash
git clone <repository-url>
cd quantitative-trading-platform
```

### 2. 环境配置
```bash
# 复制环境配置文件
cp .env.example .env

# 编辑配置文件
vim .env
```

### 3. 使用Docker Compose部署
```bash
# 构建和启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 4. 初始化数据库
```bash
# 运行数据库迁移
docker-compose exec backend alembic upgrade head

# 创建初始用户
docker-compose exec backend python init_db.py
```

### 5. 访问系统
- **前端界面**: http://localhost:3000
- **API文档**: http://localhost:8000/docs
- **管理后台**: http://localhost:8000/admin

## 详细部署步骤

### 1. 环境准备

#### 安装Docker和Docker Compose
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.12.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### 配置系统参数
```bash
# 增加文件描述符限制
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# 配置内核参数
echo "vm.max_map_count=262144" >> /etc/sysctl.conf
sysctl -p
```

### 2. 项目配置

#### 环境变量配置 (.env)
```bash
# 数据库配置
DATABASE_URL=postgresql://postgres:password@postgres:5432/trading_db
INFLUXDB_URL=http://influxdb:8086
INFLUXDB_TOKEN=your-influxdb-token
INFLUXDB_ORG=trading-org
INFLUXDB_BUCKET=trading-data

# Redis配置
REDIS_URL=redis://redis:6379/0

# JWT配置
SECRET_KEY=your-super-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# tqsdk配置
TQSDK_AUTH=your-tqsdk-auth-token

# 邮件配置
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# 系统配置
DEBUG=false
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

#### Docker Compose配置
```yaml
version: '3.8'

services:
  # PostgreSQL数据库
  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: trading_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

  # InfluxDB时序数据库
  influxdb:
    image: influxdb:2.6
    environment:
      DOCKER_INFLUXDB_INIT_MODE: setup
      DOCKER_INFLUXDB_INIT_USERNAME: admin
      DOCKER_INFLUXDB_INIT_PASSWORD: password
      DOCKER_INFLUXDB_INIT_ORG: trading-org
      DOCKER_INFLUXDB_INIT_BUCKET: trading-data
    volumes:
      - influxdb_data:/var/lib/influxdb2
    ports:
      - "8086:8086"
    restart: unless-stopped

  # Redis缓存
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    restart: unless-stopped

  # 后端API服务
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/trading_db
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ./backend:/app
      - ./logs:/app/logs
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
      - influxdb
    restart: unless-stopped

  # 前端Web服务
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    volumes:
      - ./frontend:/app
    ports:
      - "3000:3000"
    depends_on:
      - backend
    restart: unless-stopped

  # Nginx反向代理
  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - frontend
      - backend
    restart: unless-stopped

volumes:
  postgres_data:
  influxdb_data:
  redis_data:
```

### 3. 构建镜像

#### 后端Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 前端Dockerfile
```dockerfile
FROM node:16-alpine

WORKDIR /app

# 安装依赖
COPY package*.json ./
RUN npm ci --only=production

# 复制源代码
COPY . .

# 构建应用
RUN npm run build

# 使用nginx提供静态文件
FROM nginx:alpine
COPY --from=0 /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### 4. 数据库初始化

#### 运行数据库迁移
```bash
# 创建迁移文件
docker-compose exec backend alembic revision --autogenerate -m "Initial migration"

# 执行迁移
docker-compose exec backend alembic upgrade head
```

#### 初始化数据
```bash
# 创建管理员用户
docker-compose exec backend python -c "
from app.services.user_service import create_admin_user
create_admin_user('admin', 'admin@example.com', 'admin123')
"

# 导入基础数据
docker-compose exec backend python scripts/import_base_data.py
```

### 5. SSL证书配置

#### 使用Let's Encrypt
```bash
# 安装certbot
sudo apt-get install certbot python3-certbot-nginx

# 获取SSL证书
sudo certbot --nginx -d yourdomain.com

# 自动续期
sudo crontab -e
# 添加: 0 12 * * * /usr/bin/certbot renew --quiet
```

#### Nginx配置
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # 前端静态文件
    location / {
        proxy_pass http://frontend:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # API接口
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## 监控和维护

### 1. 健康检查
```bash
# 检查服务状态
docker-compose ps

# 检查服务健康
curl http://localhost:8000/health

# 查看资源使用
docker stats
```

### 2. 日志管理
```bash
# 查看实时日志
docker-compose logs -f backend

# 查看特定时间段日志
docker-compose logs --since="2023-01-01T00:00:00" backend

# 日志轮转配置
# 在docker-compose.yml中添加logging配置
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### 3. 备份策略
```bash
# 数据库备份
docker-compose exec postgres pg_dump -U postgres trading_db > backup_$(date +%Y%m%d).sql

# InfluxDB备份
docker-compose exec influxdb influx backup /tmp/backup
docker cp container_id:/tmp/backup ./influx_backup_$(date +%Y%m%d)

# 自动备份脚本
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec postgres pg_dump -U postgres trading_db | gzip > /backups/postgres_$DATE.sql.gz
find /backups -name "postgres_*.sql.gz" -mtime +7 -delete
```

### 4. 性能优化
```bash
# PostgreSQL优化
# 在postgresql.conf中调整参数
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB

# 连接池配置
max_connections = 100
```

## 故障排除

### 1. 常见问题

#### 服务无法启动
```bash
# 检查端口占用
netstat -tlnp | grep :8000

# 检查磁盘空间
df -h

# 检查内存使用
free -h
```

#### 数据库连接失败
```bash
# 检查数据库状态
docker-compose exec postgres pg_isready

# 检查连接配置
docker-compose exec backend python -c "
from app.core.database import engine
print(engine.url)
"
```

#### 前端无法访问
```bash
# 检查前端构建
docker-compose logs frontend

# 检查nginx配置
docker-compose exec nginx nginx -t
```

### 2. 性能问题

#### 数据库查询慢
```sql
-- 查看慢查询
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- 分析查询计划
EXPLAIN ANALYZE SELECT * FROM orders WHERE user_id = 1;
```

#### 内存使用过高
```bash
# 查看内存使用详情
docker stats --no-stream

# 调整JVM参数（如果使用Java组件）
-Xms512m -Xmx2g
```

## 安全配置

### 1. 防火墙设置
```bash
# 只开放必要端口
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

### 2. 数据库安全
```bash
# 修改默认密码
ALTER USER postgres PASSWORD 'new_strong_password';

# 限制连接来源
# 在pg_hba.conf中配置
host all all 172.18.0.0/16 md5
```

### 3. 应用安全
```bash
# 定期更新依赖
docker-compose exec backend pip list --outdated
docker-compose exec frontend npm audit

# 扫描安全漏洞
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image your-image:latest
```

## 扩展部署

### 1. 集群部署
```yaml
# docker-swarm.yml
version: '3.8'
services:
  backend:
    image: trading-backend:latest
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
```

### 2. Kubernetes部署
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: trading-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: trading-backend
  template:
    metadata:
      labels:
        app: trading-backend
    spec:
      containers:
      - name: backend
        image: trading-backend:latest
        ports:
        - containerPort: 8000
```

这个部署指南提供了从开发环境到生产环境的完整部署流程，包括环境配置、服务部署、监控维护和故障排除等各个方面。