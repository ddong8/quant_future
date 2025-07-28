# 量化交易平台系统管理员指南

## 目录

1. [系统概述](#系统概述)
2. [安装部署](#安装部署)
3. [系统配置](#系统配置)
4. [用户管理](#用户管理)
5. [数据库管理](#数据库管理)
6. [监控运维](#监控运维)
7. [安全管理](#安全管理)
8. [备份恢复](#备份恢复)
9. [故障排除](#故障排除)
10. [性能优化](#性能优化)

## 系统概述

### 架构组件

量化交易平台采用微服务架构，主要组件包括：

- **前端服务**: Vue.js单页应用
- **API网关**: Nginx反向代理
- **后端服务**: FastAPI应用服务器
- **数据库**: PostgreSQL + InfluxDB + Redis
- **消息队列**: Redis
- **监控系统**: Prometheus + Grafana

### 技术栈

- **操作系统**: Linux (Ubuntu 20.04+)
- **容器化**: Docker + Docker Compose
- **Web服务器**: Nginx
- **应用服务器**: Uvicorn
- **数据库**: PostgreSQL 13+, InfluxDB 2.0+, Redis 6+
- **监控**: Prometheus, Grafana
- **日志**: ELK Stack (可选)

### 系统要求

#### 最小配置
- **CPU**: 4核心
- **内存**: 8GB RAM
- **存储**: 100GB SSD
- **网络**: 100Mbps

#### 推荐配置
- **CPU**: 8核心
- **内存**: 16GB RAM
- **存储**: 500GB SSD
- **网络**: 1Gbps

## 安装部署

### 环境准备

#### 1. 系统更新

```bash
sudo apt update && sudo apt upgrade -y
```

#### 2. 安装Docker

```bash
# 安装Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 启动Docker服务
sudo systemctl enable docker
sudo systemctl start docker
```

#### 3. 创建用户

```bash
# 创建应用用户
sudo useradd -m -s /bin/bash trading
sudo usermod -aG docker trading

# 切换到应用用户
sudo su - trading
```

### 应用部署

#### 1. 获取代码

```bash
git clone https://github.com/your-org/quantitative-trading-platform.git
cd quantitative-trading-platform
```

#### 2. 环境配置

```bash
# 复制环境配置文件
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# 编辑配置文件
nano backend/.env
```

#### 3. 启动服务

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

#### 4. 初始化数据库

```bash
# 运行数据库迁移
docker-compose exec backend python -m alembic upgrade head

# 创建初始管理员用户
docker-compose exec backend python init_db.py
```

### 服务验证

#### 1. 健康检查

```bash
# 检查后端服务
curl http://localhost:8000/health

# 检查前端服务
curl http://localhost:3000

# 检查数据库连接
docker-compose exec backend python -c "from app.core.database import engine; print(engine.execute('SELECT 1').scalar())"
```

#### 2. 功能测试

- 访问前端界面: http://localhost:3000
- 访问API文档: http://localhost:8000/docs
- 登录管理员账户测试基本功能

## 系统配置

### 后端配置

#### 1. 环境变量配置 (backend/.env)

```bash
# 应用配置
APP_NAME=量化交易平台
APP_VERSION=1.0.0
DEBUG=false
LOG_LEVEL=INFO

# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/trading_db
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=your-influxdb-token
INFLUXDB_ORG=trading-org
INFLUXDB_BUCKET=market-data

# Redis配置
REDIS_URL=redis://localhost:6379/0

# JWT配置
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=1440
REFRESH_TOKEN_EXPIRE_DAYS=30

# tqsdk配置
TQSDK_USERNAME=your-tqsdk-username
TQSDK_PASSWORD=your-tqsdk-password

# 邮件配置
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# 监控配置
PROMETHEUS_ENABLED=true
GRAFANA_ENABLED=true
```

#### 2. 数据库配置

**PostgreSQL配置** (docker/postgresql.conf):
```ini
# 连接设置
max_connections = 200
shared_buffers = 256MB
effective_cache_size = 1GB

# 日志设置
log_statement = 'all'
log_duration = on
log_min_duration_statement = 1000

# 性能设置
checkpoint_completion_target = 0.9
wal_buffers = 16MB
```

**InfluxDB配置** (docker/influxdb.conf):
```toml
[http]
  enabled = true
  bind-address = ":8086"
  max-row-limit = 10000

[data]
  max-series-per-database = 1000000
  max-values-per-tag = 100000
```

### 前端配置

#### 1. 环境变量配置 (frontend/.env)

```bash
# API配置
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_WS_BASE_URL=ws://localhost:8000/api/v1/ws

# 应用配置
VITE_APP_TITLE=量化交易平台
VITE_APP_VERSION=1.0.0

# 功能开关
VITE_ENABLE_MOCK=false
VITE_ENABLE_DEBUG=false
```

#### 2. Nginx配置

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # 前端静态文件
    location / {
        root /var/www/html;
        try_files $uri $uri/ /index.html;
    }
    
    # API代理
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    # WebSocket代理
    location /api/v1/ws {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## 用户管理

### 用户角色

系统支持三种用户角色：

- **admin**: 系统管理员，拥有所有权限
- **trader**: 交易员，可以开发策略和执行交易
- **viewer**: 观察者，只能查看数据和报告

### 用户操作

#### 1. 创建用户

```bash
# 通过API创建用户
curl -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{
    "username": "trader1",
    "email": "trader1@example.com",
    "password": "secure_password",
    "role": "trader",
    "is_active": true
  }'

# 通过数据库直接创建
docker-compose exec backend python -c "
from app.services.user_service import user_service
user_service.create_user({
    'username': 'trader1',
    'email': 'trader1@example.com',
    'password': 'secure_password',
    'role': 'trader'
})
"
```

#### 2. 用户管理

```bash
# 查看所有用户
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  http://localhost:8000/api/v1/users

# 禁用用户
curl -X PUT http://localhost:8000/api/v1/users/1 \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"is_active": false}'

# 重置密码
curl -X POST http://localhost:8000/api/v1/users/1/reset-password \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### 权限管理

#### 1. 角色权限配置

编辑 `backend/app/core/security.py`:

```python
ROLE_PERMISSIONS = {
    "admin": [
        "user:create", "user:read", "user:update", "user:delete",
        "strategy:create", "strategy:read", "strategy:update", "strategy:delete",
        "trading:execute", "trading:read",
        "system:config", "system:monitor"
    ],
    "trader": [
        "strategy:create", "strategy:read", "strategy:update", "strategy:delete",
        "trading:execute", "trading:read",
        "backtest:create", "backtest:read"
    ],
    "viewer": [
        "strategy:read", "trading:read", "backtest:read"
    ]
}
```

#### 2. API权限检查

```python
from app.core.security import require_permission

@router.post("/strategies")
@require_permission("strategy:create")
async def create_strategy(strategy_data: StrategyCreate):
    # 创建策略逻辑
    pass
```

## 数据库管理

### PostgreSQL管理

#### 1. 数据库备份

```bash
# 创建备份
docker-compose exec postgres pg_dump -U postgres trading_db > backup_$(date +%Y%m%d_%H%M%S).sql

# 定时备份脚本
cat > /home/trading/backup_db.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/trading/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# PostgreSQL备份
docker-compose exec postgres pg_dump -U postgres trading_db > $BACKUP_DIR/postgres_$DATE.sql

# 保留最近7天的备份
find $BACKUP_DIR -name "postgres_*.sql" -mtime +7 -delete
EOF

chmod +x /home/trading/backup_db.sh

# 添加到crontab
echo "0 2 * * * /home/trading/backup_db.sh" | crontab -
```

#### 2. 数据库恢复

```bash
# 停止应用服务
docker-compose stop backend

# 恢复数据库
docker-compose exec postgres psql -U postgres -c "DROP DATABASE IF EXISTS trading_db;"
docker-compose exec postgres psql -U postgres -c "CREATE DATABASE trading_db;"
cat backup_20240101_020000.sql | docker-compose exec -T postgres psql -U postgres trading_db

# 重启服务
docker-compose start backend
```

#### 3. 数据库维护

```bash
# 查看数据库大小
docker-compose exec postgres psql -U postgres trading_db -c "
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"

# 重建索引
docker-compose exec postgres psql -U postgres trading_db -c "REINDEX DATABASE trading_db;"

# 清理统计信息
docker-compose exec postgres psql -U postgres trading_db -c "ANALYZE;"
```

### InfluxDB管理

#### 1. 数据保留策略

```bash
# 设置数据保留期
docker-compose exec influxdb influx bucket update \
  --name market-data \
  --retention 30d

# 查看存储使用情况
docker-compose exec influxdb influx bucket list
```

#### 2. 数据备份

```bash
# 备份InfluxDB数据
docker-compose exec influxdb influx backup /tmp/backup
docker cp $(docker-compose ps -q influxdb):/tmp/backup ./influxdb_backup_$(date +%Y%m%d)
```

### Redis管理

#### 1. 内存监控

```bash
# 查看内存使用
docker-compose exec redis redis-cli info memory

# 查看键统计
docker-compose exec redis redis-cli info keyspace

# 清理过期键
docker-compose exec redis redis-cli --scan --pattern "*" | xargs docker-compose exec redis redis-cli del
```

## 监控运维

### 系统监控

#### 1. Prometheus配置

创建 `docker/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'trading-platform'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
    
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
      
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
```

#### 2. Grafana仪表板

导入预配置的仪表板：

- 系统资源监控
- 应用性能监控
- 数据库性能监控
- 业务指标监控

#### 3. 告警规则

创建 `docker/alert.rules`:

```yaml
groups:
  - name: trading-platform
    rules:
      - alert: HighCPUUsage
        expr: cpu_usage_percent > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "CPU使用率过高"
          
      - alert: DatabaseConnectionFailed
        expr: database_connection_status == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "数据库连接失败"
```

### 日志管理

#### 1. 日志配置

编辑 `backend/app/core/logging.py`:

```python
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
        "json": {
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "/var/log/trading/app.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "formatter": "json",
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "file"],
    },
}
```

#### 2. 日志轮转

```bash
# 创建logrotate配置
cat > /etc/logrotate.d/trading-platform << 'EOF'
/var/log/trading/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 trading trading
    postrotate
        docker-compose restart backend
    endscript
}
EOF
```

### 性能监控

#### 1. 应用性能指标

监控以下关键指标：

- **响应时间**: API接口响应时间
- **吞吐量**: 每秒处理请求数
- **错误率**: 错误请求占比
- **并发数**: 同时处理的请求数

#### 2. 业务指标监控

- **活跃用户数**: 在线用户统计
- **策略执行数**: 运行中的策略数量
- **交易量**: 每日交易笔数和金额
- **系统稳定性**: 服务可用性

## 安全管理

### 网络安全

#### 1. 防火墙配置

```bash
# 安装ufw
sudo apt install ufw

# 基本规则
sudo ufw default deny incoming
sudo ufw default allow outgoing

# 允许SSH
sudo ufw allow ssh

# 允许HTTP/HTTPS
sudo ufw allow 80
sudo ufw allow 443

# 允许应用端口（仅内网）
sudo ufw allow from 192.168.1.0/24 to any port 8000
sudo ufw allow from 192.168.1.0/24 to any port 3000

# 启用防火墙
sudo ufw enable
```

#### 2. SSL证书配置

```bash
# 安装certbot
sudo apt install certbot python3-certbot-nginx

# 获取SSL证书
sudo certbot --nginx -d your-domain.com

# 自动续期
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -
```

### 应用安全

#### 1. JWT安全配置

```python
# 强密钥生成
import secrets
SECRET_KEY = secrets.token_urlsafe(32)

# 令牌配置
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1小时
REFRESH_TOKEN_EXPIRE_DAYS = 7     # 7天

# 安全头设置
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
}
```

#### 2. 数据库安全

```bash
# 创建专用数据库用户
docker-compose exec postgres psql -U postgres -c "
CREATE USER trading_app WITH PASSWORD 'strong_password';
GRANT CONNECT ON DATABASE trading_db TO trading_app;
GRANT USAGE ON SCHEMA public TO trading_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO trading_app;
"

# 限制数据库连接
# 在postgresql.conf中设置
listen_addresses = 'localhost'
max_connections = 100
```

### 审计日志

#### 1. 用户操作审计

```python
# 审计装饰器
def audit_log(action: str):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            user = get_current_user()
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                log_audit_event(
                    user_id=user.id,
                    action=action,
                    status="success",
                    duration=time.time() - start_time
                )
                return result
            except Exception as e:
                log_audit_event(
                    user_id=user.id,
                    action=action,
                    status="failed",
                    error=str(e),
                    duration=time.time() - start_time
                )
                raise
        return wrapper
    return decorator
```

#### 2. 系统事件审计

记录以下系统事件：

- 用户登录/登出
- 策略创建/修改/删除
- 交易执行
- 系统配置变更
- 安全事件

## 备份恢复

### 备份策略

#### 1. 全量备份

```bash
#!/bin/bash
# 全量备份脚本
BACKUP_DIR="/backup/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# 数据库备份
docker-compose exec postgres pg_dump -U postgres trading_db > $BACKUP_DIR/postgres.sql
docker-compose exec influxdb influx backup $BACKUP_DIR/influxdb

# 应用代码备份
tar -czf $BACKUP_DIR/application.tar.gz /home/trading/quantitative-trading-platform

# 配置文件备份
tar -czf $BACKUP_DIR/config.tar.gz /home/trading/quantitative-trading-platform/docker

# 上传到远程存储
aws s3 sync $BACKUP_DIR s3://your-backup-bucket/$(date +%Y%m%d)/
```

#### 2. 增量备份

```bash
#!/bin/bash
# 增量备份脚本（仅备份变更的数据）
BACKUP_DIR="/backup/incremental/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

# PostgreSQL增量备份（WAL文件）
docker-compose exec postgres pg_basebackup -D $BACKUP_DIR/postgres -Ft -z -P

# 应用日志备份
rsync -av --link-dest=/backup/incremental/latest /var/log/trading/ $BACKUP_DIR/logs/
ln -sfn $BACKUP_DIR /backup/incremental/latest
```

### 灾难恢复

#### 1. 恢复流程

```bash
#!/bin/bash
# 灾难恢复脚本
BACKUP_DATE=$1

if [ -z "$BACKUP_DATE" ]; then
    echo "Usage: $0 <backup_date>"
    exit 1
fi

BACKUP_DIR="/backup/$BACKUP_DATE"

# 停止所有服务
docker-compose down

# 恢复数据库
docker-compose up -d postgres
sleep 10
docker-compose exec postgres psql -U postgres -c "DROP DATABASE IF EXISTS trading_db;"
docker-compose exec postgres psql -U postgres -c "CREATE DATABASE trading_db;"
cat $BACKUP_DIR/postgres.sql | docker-compose exec -T postgres psql -U postgres trading_db

# 恢复InfluxDB
docker-compose up -d influxdb
sleep 10
docker-compose exec influxdb influx restore $BACKUP_DIR/influxdb

# 恢复应用代码
tar -xzf $BACKUP_DIR/application.tar.gz -C /

# 恢复配置文件
tar -xzf $BACKUP_DIR/config.tar.gz -C /

# 启动所有服务
docker-compose up -d

echo "恢复完成，请验证系统功能"
```

#### 2. 恢复验证

```bash
# 验证脚本
#!/bin/bash

# 检查服务状态
docker-compose ps

# 检查数据库连接
curl http://localhost:8000/health

# 检查前端服务
curl http://localhost:3000

# 检查用户登录
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'

echo "恢复验证完成"
```

## 故障排除

### 常见问题

#### 1. 服务启动失败

**问题**: Docker容器启动失败
```bash
# 查看容器日志
docker-compose logs backend

# 检查端口占用
netstat -tulpn | grep :8000

# 检查磁盘空间
df -h

# 检查内存使用
free -h
```

**解决方案**:
- 检查配置文件语法
- 确保端口未被占用
- 清理磁盘空间
- 重启Docker服务

#### 2. 数据库连接问题

**问题**: 应用无法连接数据库
```bash
# 检查数据库状态
docker-compose exec postgres pg_isready

# 检查连接配置
docker-compose exec backend python -c "
from app.core.database import engine
print(engine.url)
"

# 测试连接
docker-compose exec postgres psql -U postgres -d trading_db -c "SELECT 1;"
```

**解决方案**:
- 验证数据库凭据
- 检查网络连接
- 重启数据库服务
- 检查防火墙设置

#### 3. 性能问题

**问题**: 系统响应缓慢
```bash
# 检查系统资源
top
iostat -x 1
netstat -i

# 检查数据库性能
docker-compose exec postgres psql -U postgres -d trading_db -c "
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY total_time DESC 
LIMIT 10;
"

# 检查应用日志
docker-compose logs backend | grep -i "slow\|timeout\|error"
```

**解决方案**:
- 优化数据库查询
- 增加缓存
- 扩展硬件资源
- 优化应用代码

### 调试工具

#### 1. 日志分析

```bash
# 实时查看日志
docker-compose logs -f backend

# 搜索错误日志
docker-compose logs backend | grep -i error

# 分析访问日志
awk '{print $1}' /var/log/nginx/access.log | sort | uniq -c | sort -nr
```

#### 2. 性能分析

```bash
# 安装性能分析工具
sudo apt install htop iotop nethogs

# 监控系统资源
htop

# 监控磁盘I/O
iotop

# 监控网络使用
nethogs
```

#### 3. 数据库调试

```sql
-- 查看慢查询
SELECT query, calls, total_time, mean_time, rows
FROM pg_stat_statements 
WHERE mean_time > 1000
ORDER BY mean_time DESC;

-- 查看锁等待
SELECT * FROM pg_stat_activity WHERE wait_event IS NOT NULL;

-- 查看表大小
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## 性能优化

### 数据库优化

#### 1. PostgreSQL优化

```sql
-- 创建索引
CREATE INDEX CONCURRENTLY idx_orders_created_at ON orders(created_at);
CREATE INDEX CONCURRENTLY idx_orders_user_id ON orders(user_id);
CREATE INDEX CONCURRENTLY idx_strategies_status ON strategies(status);

-- 分区表（按时间分区）
CREATE TABLE orders_2024_01 PARTITION OF orders
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

-- 更新统计信息
ANALYZE;

-- 清理无用数据
VACUUM FULL;
```

#### 2. InfluxDB优化

```bash
# 设置合适的保留策略
docker-compose exec influxdb influx bucket update \
  --name market-data \
  --retention 90d

# 压缩数据
docker-compose exec influxdb influx task create \
  --file /path/to/compression-task.flux
```

### 应用优化

#### 1. 缓存策略

```python
# Redis缓存配置
CACHE_CONFIG = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

# 缓存装饰器
@cache_result(expire=300)  # 5分钟缓存
async def get_market_data(symbol: str):
    # 获取市场数据逻辑
    pass
```

#### 2. 连接池优化

```python
# 数据库连接池配置
DATABASE_CONFIG = {
    "pool_size": 20,
    "max_overflow": 30,
    "pool_timeout": 30,
    "pool_recycle": 3600,
}

# Redis连接池配置
REDIS_CONFIG = {
    "connection_pool_kwargs": {
        "max_connections": 50,
        "retry_on_timeout": True,
    }
}
```

### 系统优化

#### 1. 操作系统优化

```bash
# 内核参数优化
cat >> /etc/sysctl.conf << 'EOF'
# 网络优化
net.core.somaxconn = 65535
net.core.netdev_max_backlog = 5000
net.ipv4.tcp_max_syn_backlog = 65535

# 内存优化
vm.swappiness = 10
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5

# 文件系统优化
fs.file-max = 65535
EOF

sysctl -p
```

#### 2. Docker优化

```yaml
# docker-compose.yml优化
version: '3.8'
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
    ulimits:
      nofile:
        soft: 65535
        hard: 65535
```

---

*本指南会根据系统更新和运维经验持续完善。如有问题，请联系技术团队。*