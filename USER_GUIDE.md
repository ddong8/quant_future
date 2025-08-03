# 量化交易平台用户指南

## 🚀 快速开始

### 1. 启动系统

```bash
# 一键启动所有服务
./start-project.sh

# 或者清理后重新启动
./start-project.sh --clean
```

### 2. 访问系统

- **前端界面**: http://localhost:3000
- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/api/v1/health/

## 👥 默认用户账户

系统已预置以下测试账户：

| 用户名 | 密码 | 角色 | 权限说明 |
|--------|------|------|----------|
| `admin` | `admin123` | 管理员 | 完全访问权限，可管理用户和系统设置 |
| `trader1` | `trader123` | 交易员 | 可创建策略、执行交易、查看报告 |
| `viewer1` | `viewer123` | 观察者 | 只读权限，可查看策略和报告 |

## 🔧 主要功能

### 策略管理
- 创建和编辑量化交易策略
- 策略代码编辑器（支持 Python 语法高亮）
- 策略版本管理和历史记录

### 回测系统
- 历史数据回测
- 回测报告和性能分析
- 风险指标计算

### 实盘交易
- 模拟交易环境
- 实时订单管理
- 持仓监控

### 风险管理
- 实时风险监控
- 止损止盈设置
- 资金管理规则

### 数据分析
- 实时市场数据
- 交易统计报告
- 性能图表展示

## 🛠️ 系统管理

### 停止系统

```bash
# 停止所有服务
./stop-project.sh

# 停止并清理容器
./stop-project.sh --clean

# 停止并删除所有数据（危险操作）
./stop-project.sh --clean --volumes
```

### 查看日志

```bash
# 查看后端日志
docker logs trading_backend_final

# 查看前端日志
docker logs trading_frontend

# 查看数据库日志
docker logs trading_postgres
```

### 服务状态检查

```bash
# 查看所有容器状态
docker ps

# 检查后端健康状态
curl http://localhost:8000/api/v1/health/

# 检查系统就绪状态
curl http://localhost:8000/api/v1/health/readiness
```

## 🔍 故障排除

### 常见问题

1. **前端无法访问**
   - 检查容器是否运行：`docker ps`
   - 查看前端日志：`docker logs trading_frontend`
   - 确认端口 3000 未被占用

2. **登录失败**
   - 确认使用正确的用户名和密码（见上方默认账户表格）
   - 检查后端服务是否正常：`curl http://localhost:8000/api/v1/health/`
   - 查看后端日志：`docker logs trading_backend_final`
   - 使用测试页面验证：打开 `test-login.html` 文件

3. **数据库连接问题**
   - 检查数据库容器状态：`docker ps | grep postgres`
   - 重新初始化数据库：`docker exec trading_backend_final python init_db.py`

4. **服务启动缓慢**
   - 前端首次启动需要安装依赖，可能需要几分钟
   - 检查网络连接，确保能访问 npm 镜像源

### 重置系统

如果遇到严重问题，可以完全重置系统：

```bash
# 停止并清理所有容器和数据
./stop-project.sh --clean --volumes

# 重新启动
./start-project.sh
```

## 📚 API 使用

### 认证

所有 API 请求都需要 JWT 令牌认证：

```bash
# 登录获取令牌
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# 使用令牌访问 API
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/users/me
```

### 主要 API 端点

- `POST /api/v1/auth/login` - 用户登录
- `GET /api/v1/users/me` - 获取当前用户信息
- `GET /api/v1/strategies/` - 获取策略列表
- `POST /api/v1/strategies/` - 创建新策略
- `GET /api/v1/backtests/` - 获取回测结果
- `POST /api/v1/orders/` - 创建交易订单

完整的 API 文档请访问：http://localhost:8000/docs

## 🔒 安全注意事项

1. **生产环境部署**
   - 修改默认密码
   - 更换 SECRET_KEY
   - 启用 HTTPS
   - 配置防火墙

2. **数据备份**
   - 定期备份数据库
   - 备份策略代码
   - 保存重要配置文件

3. **访问控制**
   - 定期审查用户权限
   - 监控异常登录
   - 启用日志审计

## 📞 技术支持

如果遇到问题，请：

1. 查看本指南的故障排除部分
2. 检查系统日志文件
3. 访问 API 文档了解详细信息
4. 提交 Issue 到项目仓库

---

**祝您使用愉快！** 🎉