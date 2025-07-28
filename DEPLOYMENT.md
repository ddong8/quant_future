# 量化交易平台部署指南

本文档详细介绍了量化交易平台的部署方法，支持Docker和Kubernetes两种部署方式。

## 目录结构

```
├── docker/                 # Docker相关配置
│   ├── nginx.conf          # Nginx配置
│   ├── supervisord.conf    # Supervisor配置
│   ├── start.sh           # 启动脚本
│   ├── init-db.sql        # 数据库初始化脚本
│   ├── prometheus.yml     # Prometheus配置
│   └── grafana/           # Grafana配置
├── k8s/                   # Kubernetes配置
│   ├── namespace.yaml     # 命名空间和配置
│   ├── postgres.yaml      # PostgreSQL部署
│   ├── redis.yaml         # Redis部署
│   ├── influxdb.yaml      # InfluxDB部署
│   ├── app.yaml           # 应用部署
│   └── monitoring.yaml    # 监控组件
├── scripts/               # 部署脚本
│   ├── deploy.sh          # 部署脚本
│   ├── backup.sh          # 备份脚本
│   └── monitor.sh         # 监控脚本
├── Dockerfile             # Docker镜像构建
└── docker-compose.yml     # Docker Compose配置
```

## 快速开始

### 1. Docker部署（推荐用于开发和测试）

#### 前置要求
- Docker 20.10+
- Docker Compose 2.0+
- Git

#### 部署步骤

1. **克隆代码并进入目录**
```bash
git clone <repository-url>
cd quantitative-trading-platform
```

2. **配置环境变量**
```bash
# 创建环境变量文件
cp .env.example .env
# 编辑配置（可选，脚本会自动生成默认配置）
vim .env
```

3. **执行部署**
```bash
# 使用部署脚本
./scripts/deploy.sh -t docker deploy

# 或者手动部署
docker-compose up -d
```

4. **验证部署**
```bash
# 检查服务状态
docker-compose ps

# 健康检查
./scripts/deploy.sh health-check
```

#### 访问地址
- 主应用: http://localhost
- API文档: http://localhost:8000/docs
- Grafana监控: http://localhost:3000 (admin/admin123)
- Prometheus: http://localhost:9090

### 2. Kubernetes部署（推荐用于生产环境）

#### 前置要求
- Kubernetes 1.20+
- kubectl配置正确
- 足够的集群资源

#### 部署步骤

1. **准备Kubernetes集群**
```bash
# 确认集群连接
kubectl cluster-info
```

2. **配置密钥**
```bash
# 生成密钥
SECRET_KEY=$(openssl rand -hex 32)
INFLUXDB_TOKEN=$(openssl rand -hex 32)

# 更新k8s/namespace.yaml中的密钥
echo -n "$SECRET_KEY" | base64
echo -n "$INFLUXDB_TOKEN" | base64
```

3. **执行部署**
```bash
# 使用部署脚本
./scripts/deploy.sh -t k8s deploy

# 或者手动部署
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/influxdb.yaml
kubectl apply -f k8s/app.yaml
kubectl apply -f k8s/monitoring.yaml
```

4. **验证部署**
```bash
# 检查Pod状态
kubectl get pods -n quant-trading

# 检查服务
kubectl get services -n quant-trading

# 健康检查
./scripts/deploy.sh -t k8s health-check
```

#### 访问应用
```bash
# 获取LoadBalancer IP
kubectl get service quant-trading-service -n quant-trading

# 或使用端口转发
kubectl port-forward service/quant-trading-service 8080:80 -n quant-trading
```

## 配置说明

### 环境变量

| 变量名 | 描述 | 默认值 |
|--------|------|--------|
| SECRET_KEY | 应用密钥 | 自动生成 |
| DATABASE_URL | 数据库连接 | postgresql://... |
| REDIS_URL | Redis连接 | redis://... |
| INFLUXDB_URL | InfluxDB连接 | http://... |
| INFLUXDB_TOKEN | InfluxDB令牌 | 自动生成 |
| ENVIRONMENT | 运行环境 | production |

### 资源要求

#### 最小配置
- CPU: 4核
- 内存: 8GB
- 存储: 50GB

#### 推荐配置
- CPU: 8核
- 内存: 16GB
- 存储: 200GB SSD

### 端口说明

| 服务 | 端口 | 描述 |
|------|------|------|
| Nginx | 80 | Web前端 |
| FastAPI | 8000 | API服务 |
| PostgreSQL | 5432 | 数据库 |
| Redis | 6379 | 缓存 |
| InfluxDB | 8086 | 时序数据库 |
| Prometheus | 9090 | 监控 |
| Grafana | 3000 | 可视化 |

## 运维管理

### 监控

#### 启动监控
```bash
# 一次性检查
./scripts/monitor.sh check

# 持续监控
./scripts/monitor.sh -t docker monitor

# 生成报告
./scripts/monitor.sh report
```

#### 监控指标
- 应用健康状态
- 数据库连接状态
- 系统资源使用
- 错误日志统计

### 备份

#### 执行备份
```bash
# 完整备份
./scripts/backup.sh -t docker

# 指定备份目录
./scripts/backup.sh -d /backup/path

# 上传到云存储
CLOUD_STORAGE_ENABLED=true ./scripts/backup.sh --upload
```

#### 备份内容
- PostgreSQL数据库
- Redis数据
- InfluxDB数据
- 应用日志和报告
- 配置文件

### 日志管理

#### 查看日志
```bash
# Docker环境
docker-compose logs -f app
docker-compose logs -f db

# Kubernetes环境
kubectl logs -f deployment/quant-trading-app -n quant-trading
kubectl logs -f statefulset/postgres -n quant-trading
```

#### 日志轮转
日志文件会自动轮转，保留最近30天的日志。

### 扩容

#### Docker环境扩容
```bash
# 增加应用实例
docker-compose up -d --scale app=3
```

#### Kubernetes环境扩容
```bash
# 水平扩容
kubectl scale deployment quant-trading-app --replicas=5 -n quant-trading

# 垂直扩容（修改资源限制）
kubectl patch deployment quant-trading-app -n quant-trading -p '{"spec":{"template":{"spec":{"containers":[{"name":"app","resources":{"limits":{"memory":"2Gi","cpu":"1000m"}}}]}}}}'
```

## 故障排除

### 常见问题

#### 1. 服务启动失败
```bash
# 检查日志
docker-compose logs app
# 或
kubectl logs deployment/quant-trading-app -n quant-trading

# 检查配置
docker-compose config
```

#### 2. 数据库连接失败
```bash
# 检查数据库状态
docker-compose exec db pg_isready -U postgres
# 或
kubectl exec statefulset/postgres -n quant-trading -- pg_isready -U postgres

# 检查网络连接
docker-compose exec app ping db
```

#### 3. 内存不足
```bash
# 检查资源使用
docker stats
# 或
kubectl top pods -n quant-trading

# 增加内存限制
# 修改docker-compose.yml或k8s配置文件
```

#### 4. 磁盘空间不足
```bash
# 清理Docker
docker system prune -a

# 清理日志
docker-compose exec app find /app/logs -name "*.log" -mtime +7 -delete

# 清理备份
find ./backups -name "*.tar.gz" -mtime +30 -delete
```

### 性能优化

#### 1. 数据库优化
```sql
-- 创建索引
CREATE INDEX CONCURRENTLY idx_orders_created_at ON orders(created_at);
CREATE INDEX CONCURRENTLY idx_trades_symbol_time ON trades(symbol, created_at);

-- 分析表统计信息
ANALYZE;

-- 清理无用数据
VACUUM FULL;
```

#### 2. Redis优化
```bash
# 配置内存策略
docker-compose exec redis redis-cli CONFIG SET maxmemory-policy allkeys-lru

# 启用持久化
docker-compose exec redis redis-cli CONFIG SET save "900 1 300 10 60 10000"
```

#### 3. 应用优化
- 启用Gzip压缩
- 配置CDN加速
- 使用连接池
- 启用缓存

## 安全配置

### 1. 网络安全
```bash
# 配置防火墙
ufw allow 80/tcp
ufw allow 443/tcp
ufw deny 5432/tcp  # 禁止外部访问数据库

# 使用TLS证书
# 配置nginx SSL
```

### 2. 访问控制
```yaml
# 配置RBAC（Kubernetes）
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: quant-trading-role
  namespace: quant-trading
rules:
- apiGroups: [""]
  resources: ["pods", "services"]
  verbs: ["get", "list", "watch"]
```

### 3. 密钥管理
```bash
# 使用Kubernetes Secrets
kubectl create secret generic app-secrets \
  --from-literal=SECRET_KEY="your-secret-key" \
  --from-literal=DATABASE_PASSWORD="your-db-password" \
  -n quant-trading
```

## 升级指南

### 1. 应用升级
```bash
# 构建新版本
docker build -t quant-trading:v2.0.0 .

# 更新部署
docker-compose down
docker-compose up -d

# 或Kubernetes滚动更新
kubectl set image deployment/quant-trading-app app=quant-trading:v2.0.0 -n quant-trading
```

### 2. 数据库迁移
```bash
# 执行迁移
./scripts/deploy.sh migrate

# 或手动执行
docker-compose exec app python -m alembic upgrade head
```

### 3. 回滚
```bash
# Docker回滚
docker-compose down
# 恢复旧版本配置
docker-compose up -d

# Kubernetes回滚
kubectl rollout undo deployment/quant-trading-app -n quant-trading
```

## 支持与联系

如果在部署过程中遇到问题，请：

1. 查看日志文件
2. 检查系统资源
3. 参考故障排除章节
4. 提交Issue到项目仓库

---

更多详细信息请参考项目文档或联系技术支持团队。