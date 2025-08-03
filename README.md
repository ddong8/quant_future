# 🚀 量化交易平台

一个功能完整的量化交易平台，支持策略开发、回测分析、实盘交易、风险控制等全流程的量化交易需求。

## ✨ 主要功能

### 📊 核心功能模块
- **策略管理系统** - 策略开发、版本控制、代码编辑
- **回测系统** - 历史数据回测、性能分析、结果可视化
- **订单管理** - 订单创建、状态跟踪、执行管理
- **持仓管理** - 实时持仓、盈亏计算、风险监控
- **账户管理** - 资金管理、交易统计、绩效分析
- **市场数据** - 实时行情、技术分析、图表展示
- **风险控制** - 风险规则、实时监控、自动执行
- **系统管理** - 用户设置、数据导出、系统监控

### 🎯 技术特色
- **高性能优化** - 数据库索引、前端懒加载、WebSocket优化
- **实时数据处理** - WebSocket推送、实时计算、状态同步
- **完整的测试覆盖** - 单元测试、集成测试、端到端测试
- **优秀的用户体验** - 响应式设计、主题定制、错误处理
- **全面的风险控制** - 多层风险规则、实时监控、自动执行

## 🛠️ 技术栈

### 后端技术
- **FastAPI** - 现代化的 Python Web 框架
- **PostgreSQL** - 关系型数据库
- **SQLAlchemy** - ORM 框架
- **Alembic** - 数据库迁移工具
- **Redis** - 缓存和会话存储
- **WebSocket** - 实时数据推送

### 前端技术
- **Vue 3** - 渐进式 JavaScript 框架
- **TypeScript** - 类型安全的 JavaScript
- **Element Plus** - Vue 3 UI 组件库
- **ECharts** - 数据可视化图表库
- **Pinia** - Vue 状态管理
- **Vite** - 现代化构建工具

## 🚀 快速开始

### 1. 环境准备
```bash
# 克隆项目
git clone <repository-url>
cd trading-platform

# 设置环境
chmod +x setup.sh
./setup.sh
```

### 2. 配置数据库
```bash
# 安装 PostgreSQL (macOS)
brew install postgresql
brew services start postgresql

# 创建数据库
psql -U postgres -f init_db.sql
```

### 3. 配置环境变量
编辑配置文件：
- `backend/.env` - 后端配置
- `frontend/.env` - 前端配置

### 4. 启动服务
```bash
# 启动所有服务
./start.sh

# 或者分别启动
# 后端服务
cd backend
python -m uvicorn app.main:app --reload

# 前端服务
cd frontend
npm run dev
```

## 📱 访问应用

启动成功后，可以通过以下地址访问：

- **前端应用**: http://localhost:5173
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

### 默认管理员账户
- 用户名: `admin`
- 密码: `admin123`

## 🔧 管理命令

```bash
# 启动服务
./start.sh

# 停止服务
./stop.sh

# 重启服务
./restart.sh

# 查看日志
./logs.sh
```

## 📁 项目结构

```
trading-platform/
├── backend/                 # 后端代码
│   ├── app/                # 应用代码
│   │   ├── api/           # API 路由
│   │   ├── core/          # 核心模块
│   │   ├── models/        # 数据模型
│   │   ├── services/      # 业务逻辑
│   │   ├── schemas/       # 数据模式
│   │   └── utils/         # 工具函数
│   ├── alembic/           # 数据库迁移
│   ├── tests/             # 测试代码
│   └── requirements.txt   # Python 依赖
├── frontend/               # 前端代码
│   ├── src/               # 源代码
│   │   ├── api/          # API 客户端
│   │   ├── components/   # Vue 组件
│   │   ├── views/        # 页面视图
│   │   ├── stores/       # 状态管理
│   │   ├── utils/        # 工具函数
│   │   └── styles/       # 样式文件
│   ├── public/           # 静态资源
│   └── package.json      # Node.js 依赖
├── docs/                 # 文档
├── logs/                 # 日志文件
└── scripts/              # 脚本文件
```

## 🧪 测试

### 运行测试
```bash
# 后端测试
cd backend
pytest

# 前端测试
cd frontend
npm run test

# 集成测试
python -m pytest tests/integration/

# 端到端测试
npm run test:e2e
```

### 测试覆盖率
```bash
# 后端测试覆盖率
cd backend
pytest --cov=app --cov-report=html

# 前端测试覆盖率
cd frontend
npm run test:coverage
```

## 📊 性能监控

平台内置了完整的性能监控系统：

- **系统监控** - CPU、内存、磁盘、网络使用情况
- **应用监控** - 响应时间、错误率、连接数
- **数据库监控** - 查询性能、连接池状态
- **WebSocket监控** - 连接数、消息吞吐量

访问 `/system/monitoring` 查看实时监控数据。

## 🔒 安全特性

- **JWT 认证** - 安全的用户认证机制
- **角色权限** - 细粒度的权限控制
- **数据加密** - 敏感数据加密存储
- **API 限流** - 防止恶意请求
- **CORS 配置** - 跨域请求安全控制
- **SQL 注入防护** - ORM 层面的安全保护

## 📚 文档

- [用户指南](USER_GUIDE.md) - 详细的使用说明和故障排除
- [API 文档](http://localhost:8000/docs) - 完整的 API 接口文档
- [开发指南](DEVELOPMENT.md) - 开发环境搭建和贡献指南
- [部署指南](DEPLOYMENT.md) - 生产环境部署说明

## 🤝 贡献

欢迎贡献代码！请查看 [贡献指南](CONTRIBUTING.md) 了解详细信息。

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🆘 支持

如果遇到问题，可以通过以下方式获取帮助：

- 查看 [常见问题](FAQ.md)
- 提交 [Issue](https://github.com/your-repo/issues)
- 发送邮件至 support@example.com

---

**⚠️ 免责声明**: 本平台仅供学习和研究使用，不构成投资建议。量化交易存在风险，请谨慎使用。