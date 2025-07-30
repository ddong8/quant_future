# 故障排除指南

本指南提供了量化交易平台常见问题的诊断和解决方案。

## 🔍 快速诊断

### 自动化诊断工具

在遇到问题时，首先运行我们提供的诊断工具：

```bash
# 全面配置验证
python3 validate_all_configs.py

# 启动状态验证
python3 test_startup_config.py

# 如果服务正在运行，检查运行状态
python3 validate_startup.py
```

### 基础检查清单

- [ ] Docker 和 Docker Compose 已安装且版本正确
- [ ] 端口 3000、8000、5432、6379、8086 未被占用
- [ ] 有足够的磁盘空间（至少 10GB）
- [ ] 有足够的内存（至少 4GB）
- [ ] `.env` 文件已正确配置

## 🚨 常见问题及解决方案

### 1. 容器启动问题

#### 问题：容器无法启动或立即退出

**症状**：
```bash
$ docker-compose ps
NAME                    COMMAND                  SERVICE             STATUS              PORTS
trading_backend         "python start_backen…"   backend             Exited (1)          
```

**诊断步骤**：
```bash
# 1. 查看容器日志
docker-compose logs backend

# 2. 检查容器状态
docker-compose ps

# 3. 尝试手动启动容器
docker-compose up backend
```

**常见原因和解决方案**：

1. **环境变量配置错误**
   ```bash
   # 检查环境变量文件
   cat .env
   
   # 从模板重新创建
   cp .env.template .env
   vim .env
   ```

2. **端口冲突**
   ```bash
   # 检查端口占用
   netstat -tulpn | grep :8000
   lsof -i :8000
   
   # 停止占用端口的进程或修改端口配置
   ```

3. **依赖服务未就绪**
   ```bash
   # 检查数据库服务状态
   docker-compose logs postgres
   
   # 重启依赖服务
   docker-compose restart postgres redis influxdb
   ```

4. **权限问题**
   ```bash
   # 检查文件权限
   ls -la backend/
   
   # 修复权限
   chmod +x backend/start_backend.py
   chmod +x start-trading-platform.sh
   ```

#### 问题：容器构建失败

**症状**：
```bash
ERROR: failed to solve: process "/bin/sh -c pip install -r requirements.txt" did not complete successfully
```

**解决方案**：
```bash
# 1. 清理Docker缓存
docker system prune -a

# 2. 重新构建镜像
docker-compose build --no-cache

# 3. 检查网络连接
ping pypi.org

# 4. 使用国内镜像源（如果在中国）
# 在 backend/Dockerfile 中添加：
# RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
```

### 2. 数据库连接问题

#### 问题：数据库连接失败

**症状**：
```
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) could not connect to server
```

**诊断步骤**：
```bash
# 1. 检查PostgreSQL容器状态
docker-compose logs postgres

# 2. 检查数据库健康状态
curl http://localhost:8000/api/v1/health/database

# 3. 尝试直接连接数据库
docker-compose exec postgres psql -U postgres -d trading_db
```

**解决方案**：

1. **PostgreSQL容器未启动**
   ```bash
   # 启动PostgreSQL
   docker-compose up -d postgres
   
   # 等待数据库就绪
   docker-compose exec postgres pg_isready -U postgres
   ```

2. **数据库初始化失败**
   ```bash
   # 查看初始化日志
   docker-compose logs db-init
   
   # 手动运行初始化
   docker-compose exec backend python init_db.py
   
   # 重新运行初始化容器
   docker-compose restart db-init
   ```

3. **连接配置错误**
   ```bash
   # 检查数据库URL配置
   grep DATABASE_URL .env
   
   # 确保使用容器名称而不是localhost
   DATABASE_URL=postgresql://postgres:password@postgres:5432/trading_db
   ```

#### 问题：数据库初始化失败

**症状**：
```
ERROR: relation "users" does not exist
```

**解决方案**：
```bash
# 1. 检查初始化容器日志
docker-compose logs db-init

# 2. 手动运行初始化脚本
docker-compose exec backend python init_db.py

# 3. 检查数据库表是否创建
docker-compose exec postgres psql -U postgres -d trading_db -c "\dt"

# 4. 如果需要重新初始化
docker-compose down -v  # 删除数据卷
docker-compose up -d    # 重新启动
```

### 3. 网络连接问题

#### 问题：前端无法访问后端API

**症状**：
- 前端页面显示网络错误
- API请求返回404或连接超时

**诊断步骤**：
```bash
# 1. 检查后端服务状态
curl http://localhost:8000/api/v1/health/

# 2. 检查前端代理配置
cat frontend/vite.config.ts | grep proxy

# 3. 检查容器网络
docker network ls
docker network inspect trading_network
```

**解决方案**：

1. **后端服务未启动**
   ```bash
   docker-compose restart backend
   docker-compose logs backend
   ```

2. **代理配置错误**
   ```bash
   # 检查vite.config.ts中的代理配置
   # 确保target指向正确的后端地址
   proxy: {
     '/api': {
       target: 'http://backend:8000',
       changeOrigin: true
     }
   }
   ```

3. **CORS配置问题**
   ```bash
   # 检查后端CORS配置
   grep -r CORS backend/app/
   
   # 确保前端域名在CORS允许列表中
   ```

#### 问题：WebSocket连接失败

**症状**：
```
WebSocket connection failed: Error during WebSocket handshake
```

**解决方案**：
```bash
# 1. 检查WebSocket代理配置
cat frontend/vite.config.ts | grep -A 5 "/ws"

# 2. 检查nginx配置（生产环境）
cat frontend/nginx.conf | grep -A 10 "location /api/v1/ws"

# 3. 测试WebSocket连接
# 使用浏览器开发者工具或WebSocket测试工具
```

### 4. 前端问题

#### 问题：前端页面无法加载

**症状**：
- 浏览器显示"无法访问此网站"
- 页面显示空白或错误信息

**诊断步骤**：
```bash
# 1. 检查前端容器状态
docker-compose logs frontend

# 2. 检查端口是否可访问
curl http://localhost:3000

# 3. 检查nginx配置
docker-compose exec frontend cat /etc/nginx/conf.d/default.conf
```

**解决方案**：

1. **前端容器启动失败**
   ```bash
   # 查看详细日志
   docker-compose logs frontend
   
   # 重新构建前端镜像
   docker-compose build --no-cache frontend
   
   # 检查Node.js依赖
   docker-compose exec frontend npm list
   ```

2. **Nginx配置错误**
   ```bash
   # 检查nginx配置语法
   docker-compose exec frontend nginx -t
   
   # 重新加载nginx配置
   docker-compose exec frontend nginx -s reload
   ```

#### 问题：图表组件无法显示

**症状**：
- 页面加载正常但图表区域空白
- 控制台显示ECharts相关错误

**解决方案**：
```bash
# 1. 运行图表组件验证
cd frontend && ./validate-charts.sh

# 2. 检查ECharts依赖
docker-compose exec frontend npm list echarts vue-echarts

# 3. 检查浏览器控制台错误
# 打开浏览器开发者工具查看JavaScript错误

# 4. 重新安装前端依赖
docker-compose exec frontend npm install
```

### 5. 性能问题

#### 问题：系统响应缓慢

**诊断步骤**：
```bash
# 1. 检查系统资源使用
docker stats

# 2. 检查数据库性能
docker-compose exec postgres psql -U postgres -d trading_db -c "
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY total_time DESC LIMIT 10;"

# 3. 检查Redis性能
docker-compose exec redis redis-cli info stats
```

**解决方案**：

1. **内存不足**
   ```bash
   # 增加Docker内存限制
   # 在docker-compose.yml中调整内存限制
   deploy:
     resources:
       limits:
         memory: 2G
   ```

2. **数据库查询慢**
   ```bash
   # 启用查询日志
   docker-compose exec postgres psql -U postgres -c "
   ALTER SYSTEM SET log_statement = 'all';
   SELECT pg_reload_conf();"
   
   # 分析慢查询
   docker-compose logs postgres | grep "duration:"
   ```

3. **磁盘I/O瓶颈**
   ```bash
   # 检查磁盘使用情况
   df -h
   iostat -x 1
   
   # 清理不必要的文件
   docker system prune -a
   ```

### 6. 安全问题

#### 问题：JWT令牌验证失败

**症状**：
```
HTTP 401: Invalid token
```

**解决方案**：
```bash
# 1. 检查JWT配置
grep JWT .env

# 2. 确保SECRET_KEY配置正确
# SECRET_KEY应该是一个强随机字符串

# 3. 检查令牌过期时间
grep TOKEN_EXPIRE .env

# 4. 重新生成SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### 问题：CORS错误

**症状**：
```
Access to fetch at 'http://localhost:8000/api/v1/...' from origin 'http://localhost:3000' has been blocked by CORS policy
```

**解决方案**：
```bash
# 1. 检查CORS配置
grep -r CORS backend/app/core/

# 2. 更新CORS设置
# 在backend/app/core/config.py中添加前端域名到允许列表

# 3. 重启后端服务
docker-compose restart backend
```

## 🔧 高级故障排除

### 日志分析

#### 收集所有日志
```bash
# 创建日志收集脚本
cat > collect_logs.sh << 'EOF'
#!/bin/bash
mkdir -p logs
docker-compose logs --no-color > logs/all_services.log
docker-compose logs --no-color backend > logs/backend.log
docker-compose logs --no-color frontend > logs/frontend.log
docker-compose logs --no-color postgres > logs/postgres.log
docker-compose logs --no-color redis > logs/redis.log
docker-compose logs --no-color influxdb > logs/influxdb.log
docker-compose logs --no-color db-init > logs/db-init.log
echo "日志已收集到 logs/ 目录"
EOF

chmod +x collect_logs.sh
./collect_logs.sh
```

#### 分析错误模式
```bash
# 查找错误关键词
grep -i error logs/all_services.log
grep -i exception logs/backend.log
grep -i failed logs/all_services.log

# 分析时间戳模式
awk '{print $1, $2}' logs/all_services.log | sort | uniq -c
```

### 网络诊断

#### 容器间网络连通性测试
```bash
# 测试后端到数据库连接
docker-compose exec backend ping postgres

# 测试前端到后端连接
docker-compose exec frontend wget -qO- http://backend:8000/api/v1/health/

# 检查DNS解析
docker-compose exec backend nslookup postgres
```

#### 端口连通性测试
```bash
# 测试外部端口访问
telnet localhost 8000
telnet localhost 3000

# 测试容器内部端口
docker-compose exec backend netstat -tulpn
```

### 数据库深度诊断

#### 检查数据库连接池
```bash
docker-compose exec postgres psql -U postgres -d trading_db -c "
SELECT 
    state,
    count(*) as connections
FROM pg_stat_activity 
WHERE datname = 'trading_db'
GROUP BY state;"
```

#### 检查数据库锁
```bash
docker-compose exec postgres psql -U postgres -d trading_db -c "
SELECT 
    blocked_locks.pid AS blocked_pid,
    blocked_activity.usename AS blocked_user,
    blocking_locks.pid AS blocking_pid,
    blocking_activity.usename AS blocking_user,
    blocked_activity.query AS blocked_statement,
    blocking_activity.query AS current_statement_in_blocking_process
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype
JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;"
```

### 性能分析

#### 系统资源监控
```bash
# 创建监控脚本
cat > monitor.sh << 'EOF'
#!/bin/bash
echo "=== Docker容器资源使用 ==="
docker stats --no-stream

echo -e "\n=== 系统内存使用 ==="
free -h

echo -e "\n=== 磁盘使用 ==="
df -h

echo -e "\n=== 网络连接 ==="
netstat -tulpn | grep -E ':(3000|8000|5432|6379|8086)'

echo -e "\n=== 进程状态 ==="
ps aux | grep -E '(docker|postgres|redis)' | head -10
EOF

chmod +x monitor.sh
./monitor.sh
```

#### 应用性能分析
```bash
# 后端API响应时间测试
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/api/v1/health/

# 创建curl格式文件
cat > curl-format.txt << 'EOF'
     time_namelookup:  %{time_namelookup}\n
        time_connect:  %{time_connect}\n
     time_appconnect:  %{time_appconnect}\n
    time_pretransfer:  %{time_pretransfer}\n
       time_redirect:  %{time_redirect}\n
  time_starttransfer:  %{time_starttransfer}\n
                     ----------\n
          time_total:  %{time_total}\n
EOF
```

## 📞 获取帮助

### 自助诊断清单

在寻求帮助之前，请完成以下检查：

- [ ] 运行了所有诊断工具
- [ ] 检查了相关日志文件
- [ ] 尝试了重启服务
- [ ] 验证了配置文件
- [ ] 检查了系统资源

### 提交问题报告

如果问题仍然存在，请提供以下信息：

1. **环境信息**
   ```bash
   # 系统信息
   uname -a
   docker --version
   docker-compose --version
   
   # 服务状态
   docker-compose ps
   ```

2. **错误日志**
   ```bash
   # 收集相关日志
   ./collect_logs.sh
   # 附加 logs/ 目录中的相关文件
   ```

3. **配置信息**
   ```bash
   # 配置验证结果
   python3 validate_all_configs.py > config_validation.txt
   ```

4. **重现步骤**
   - 详细描述问题出现的步骤
   - 预期行为和实际行为
   - 问题出现的频率

### 联系方式

- 📧 技术支持邮箱: support@trading-platform.com
- 🐛 GitHub Issues: https://github.com/your-org/quantitative-trading-platform/issues
- 📖 文档中心: https://docs.trading-platform.com
- 💬 社区论坛: https://community.trading-platform.com

---

**注意**: 在生产环境中遇到问题时，请优先联系技术支持团队，避免自行进行可能影响数据安全的操作。