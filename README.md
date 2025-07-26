# 量化交易平台

基于tqsdk、FastAPI和Vue.js构建的量化交易平台，提供策略开发、回测、实盘交易和风险管理的完整解决方案。

## 项目结构

```
quantitative-trading-platform/
├── backend/                 # 后端服务 (FastAPI + Python)
│   ├── app/                # 应用代码
│   ├── requirements.txt    # Python依赖
│   └── pyproject.toml     # 项目配置
├── frontend/               # 前端应用 (Vue.js + TypeScript)
│   ├── src/               # 源代码
│   ├── package.json       # Node.js依赖
│   └── vite.config.ts     # Vite配置
├── docs/                  # 项目文档
└── README.md             # 项目说明
```

## 技术栈

### 后端
- **FastAPI** - 现代Python Web框架
- **tqsdk** - 天勤量化交易SDK
- **SQLAlchemy** - ORM框架
- **PostgreSQL** - 关系型数据库
- **InfluxDB** - 时序数据库
- **Redis** - 缓存和消息队列
- **Celery** - 异步任务队列

### 前端
- **Vue.js 3** - 渐进式JavaScript框架
- **TypeScript** - 类型安全
- **Element Plus** - UI组件库
- **ECharts** - 图表可视化
- **Vite** - 构建工具

## 快速开始

### 环境要求

- Python 3.9+
- Node.js 16+
- PostgreSQL 13+
- Redis 6+
- InfluxDB 2.0+

### 后端设置

1. 创建虚拟环境
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库连接等信息
```

4. 运行数据库迁移
```bash
alembic upgrade head
```

5. 启动开发服务器
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 前端设置

1. 安装依赖
```bash
cd frontend
npm install
```

2. 启动开发服务器
```bash
npm run dev
```

3. 构建生产版本
```bash
npm run build
```

## 开发指南

### 代码规范

- 后端使用 Black、isort、flake8 进行代码格式化和检查
- 前端使用 ESLint、Prettier 进行代码格式化和检查
- 提交前请运行相应的代码检查工具

### 测试

```bash
# 后端测试
cd backend
pytest

# 前端测试
cd frontend
npm run test
```

## 功能特性

- ✅ 用户认证和权限管理
- ✅ 实时市场数据获取
- ✅ 策略开发和管理
- ✅ 历史数据回测
- ✅ 实盘交易执行
- ✅ 风险管理和监控
- ✅ 交易报告和分析

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request来改进项目。