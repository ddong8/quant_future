# 量化交易平台前端

基于 Vue 3 + TypeScript + Element Plus 构建的现代化量化交易平台前端应用。

## 技术栈

- **框架**: Vue 3 (Composition API)
- **语言**: TypeScript
- **构建工具**: Vite
- **UI 组件库**: Element Plus
- **状态管理**: Pinia
- **路由**: Vue Router 4
- **图表**: ECharts + Vue-ECharts
- **HTTP 客户端**: Axios
- **样式**: SCSS
- **代码规范**: ESLint + Prettier

## 功能特性

- 🔐 用户认证和权限管理
- 📊 实时数据仪表板
- 💹 交易执行界面
- 📋 订单和持仓管理
- 💰 账户资金管理
- 📈 策略管理和回测
- ⚠️ 风险监控和管理
- 📱 响应式设计
- 🌙 深色模式支持
- 🔄 实时数据更新

## 项目结构

```
frontend/
├── public/                 # 静态资源
├── src/
│   ├── api/               # API 接口
│   ├── components/        # 通用组件
│   ├── layouts/           # 布局组件
│   ├── router/            # 路由配置
│   ├── stores/            # Pinia 状态管理
│   ├── styles/            # 全局样式
│   ├── types/             # TypeScript 类型定义
│   ├── utils/             # 工具函数
│   ├── views/             # 页面组件
│   ├── App.vue            # 根组件
│   └── main.ts            # 应用入口
├── index.html             # HTML 模板
├── package.json           # 项目配置
├── tsconfig.json          # TypeScript 配置
├── vite.config.ts         # Vite 配置
└── README.md              # 项目说明
```

## 开发指南

### 环境要求

- Node.js >= 16
- npm >= 8

### 安装依赖

```bash
npm install
```

### 开发服务器

```bash
npm run dev
```

访问 http://localhost:3000

### 构建生产版本

```bash
npm run build
```

### 代码检查

```bash
npm run lint
```

### 代码格式化

```bash
npm run format
```

### 类型检查

```bash
npm run type-check
```

## 开发规范

### 组件命名

- 组件文件使用 PascalCase 命名，如 `UserProfile.vue`
- 组件名称使用多个单词，避免与 HTML 元素冲突

### 代码风格

- 使用 Composition API
- 优先使用 `<script setup>` 语法
- 使用 TypeScript 进行类型检查
- 遵循 ESLint 和 Prettier 配置

### 目录结构

- `views/` - 页面级组件
- `components/` - 可复用组件
- `stores/` - Pinia 状态管理
- `api/` - API 接口定义
- `types/` - TypeScript 类型定义

### 状态管理

使用 Pinia 进行状态管理：

```typescript
// stores/example.ts
import { defineStore } from 'pinia'

export const useExampleStore = defineStore('example', () => {
  const state = ref('')
  
  const action = () => {
    // 业务逻辑
  }
  
  return {
    state,
    action
  }
})
```

### API 调用

使用封装的 HTTP 客户端：

```typescript
// api/example.ts
import { http } from '@/utils/request'

export const exampleApi = {
  getData: () => http.get('/data'),
  postData: (data: any) => http.post('/data', data)
}
```

## 部署

### 构建

```bash
npm run build
```

构建产物在 `dist/` 目录中。

### 环境变量

创建 `.env.local` 文件配置环境变量：

```
VITE_API_BASE_URL=http://localhost:8000
```

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

MIT License