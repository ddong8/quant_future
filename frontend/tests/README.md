# 前端集成测试

本目录包含量化交易平台前端的集成测试，用于验证组件集成、用户工作流、API调用和跨浏览器兼容性。

## 测试结构

```
tests/
├── README.md                          # 本文档
├── setup.ts                          # 测试环境设置
├── run-tests.ts                      # 测试运行脚本
├── integration/                      # 集成测试
│   ├── components/                   # 组件集成测试
│   │   ├── auth.test.ts             # 认证组件测试
│   │   ├── strategy.test.ts         # 策略组件测试
│   │   └── trading.test.ts          # 交易组件测试
│   └── api/                         # API集成测试
│       └── api-integration.test.ts   # API调用和状态管理测试
├── e2e/                             # E2E测试
│   └── user-workflows.test.ts       # 用户工作流测试
└── cross-browser/                   # 跨浏览器测试
    └── browser-compatibility.test.ts # 浏览器兼容性测试
```

## 测试覆盖范围

### 1. 组件集成测试

#### 认证组件测试 (`integration/components/auth.test.ts`)
- 登录表单验证和提交
- 注册表单验证和提交
- 认证状态管理
- 错误处理和用户反馈
- 完整认证流程测试

#### 策略组件测试 (`integration/components/strategy.test.ts`)
- 策略列表加载和显示
- 策略创建和编辑
- 策略代码验证
- 策略部署和管理
- 策略搜索和过滤

#### 交易组件测试 (`integration/components/trading.test.ts`)
- 交易表单验证和提交
- 订单管理和状态更新
- 持仓显示和管理
- 账户信息展示
- 实时数据更新

### 2. 用户工作流E2E测试

#### 新用户注册流程 (`e2e/user-workflows.test.ts`)
- 注册 → 登录 → 创建第一个策略
- 表单验证和错误处理
- 导航和页面跳转

#### 策略开发流程
- 策略创建 → 编辑 → 验证 → 回测 → 分析
- 代码编辑器集成
- 回测配置和结果查看

#### 实盘交易流程
- 策略部署 → 手动交易 → 订单管理 → 持仓监控
- 风险控制验证
- 实时数据处理

#### 多策略管理流程
- 多策略创建和比较
- 性能分析和优化
- 最佳策略选择

### 3. API调用和状态管理测试

#### 认证状态管理 (`integration/api/api-integration.test.ts`)
- 登录/登出流程
- Token管理和刷新
- 认证状态同步

#### 策略状态管理
- 策略CRUD操作
- 状态更新和同步
- 错误处理和重试

#### 交易状态管理
- 订单状态管理
- 持仓实时更新
- 账户信息同步

#### 跨Store状态同步
- 多个Store之间的状态协调
- 全局状态管理
- 状态持久化

### 4. 跨浏览器兼容性测试

#### 浏览器特性检测 (`cross-browser/browser-compatibility.test.ts`)
- Chrome、Firefox、Safari、Edge支持
- IE11降级方案
- 特性检测和polyfill

#### 响应式设计测试
- 移动端、平板、桌面适配
- 媒体查询测试
- 触摸事件支持

#### CSS兼容性测试
- Flexbox和Grid布局
- CSS变量和自定义属性
- 浏览器前缀处理

#### JavaScript兼容性测试
- ES6+特性支持
- Promise和async/await
- WebSocket和WebWorker

## 运行测试

### 前置要求

1. **Node.js环境**
   ```bash
   node >= 16.0.0
   npm >= 8.0.0
   ```

2. **安装依赖**
   ```bash
   npm install
   ```

3. **测试依赖**
   ```bash
   npm install --save-dev vitest @vue/test-utils jsdom
   ```

### 运行方式

#### 1. 使用npm脚本（推荐）

```bash
# 运行所有测试
npm run test

# 运行特定类型测试
npm run test:unit          # 单元测试
npm run test:integration   # 集成测试
npm run test:e2e          # E2E测试
npm run test:cross-browser # 跨浏览器测试

# 监听模式
npm run test:watch

# 生成覆盖率报告
npm run test:coverage

# 生成HTML报告
npm run test:report
```

#### 2. 使用测试脚本

```bash
# 运行所有测试
node tests/run-tests.ts

# 运行特定类型测试
node tests/run-tests.ts --type integration
node tests/run-tests.ts --type e2e
node tests/run-tests.ts --type cross-browser

# 指定浏览器
node tests/run-tests.ts --type cross-browser --browser chrome

# 指定视口尺寸
node tests/run-tests.ts --viewport mobile

# 监听模式
node tests/run-tests.ts --watch

# 生成覆盖率
node tests/run-tests.ts --coverage
```

#### 3. 直接使用Vitest

```bash
# 运行所有测试
npx vitest run

# 运行特定测试文件
npx vitest run tests/integration/components/auth.test.ts

# 监听模式
npx vitest watch

# 生成覆盖率
npx vitest run --coverage

# UI模式
npx vitest --ui
```

## 测试配置

### Vitest配置 (`vitest.config.ts`)

```typescript
export default defineConfig({
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./tests/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      thresholds: {
        global: {
          branches: 80,
          functions: 80,
          lines: 80,
          statements: 80
        }
      }
    }
  }
})
```

### 测试环境设置 (`setup.ts`)

- 全局测试配置
- Mock对象设置
- 浏览器API模拟
- 测试工具初始化

## 测试工具和库

### 核心测试库
- **Vitest**: 测试运行器和断言库
- **@vue/test-utils**: Vue组件测试工具
- **jsdom**: DOM环境模拟

### Mock和模拟
- **vi.mock()**: API模拟
- **MockWebSocket**: WebSocket模拟
- **MockLocalStorage**: 本地存储模拟

### 测试辅助
- **createPinia()**: 状态管理测试
- **createRouter()**: 路由测试
- **mount()**: 组件挂载

## 测试数据

### 模拟用户数据

```typescript
const mockUser = {
  id: '1',
  username: 'testuser',
  email: 'test@example.com'
}
```

### 模拟策略数据

```typescript
const mockStrategy = {
  id: '1',
  name: '测试策略',
  description: '用于测试的策略',
  code: 'def initialize(context): pass',
  status: 'draft'
}
```

### 模拟交易数据

```typescript
const mockOrder = {
  id: '1',
  symbol: 'SHFE.cu2401',
  side: 'buy',
  order_type: 'limit',
  quantity: 1,
  price: 70000,
  status: 'pending'
}
```

## 测试最佳实践

### 1. 测试隔离

- 每个测试独立运行
- 使用beforeEach清理状态
- Mock外部依赖

### 2. 测试命名

- 描述性测试名称
- 使用"应该"句式
- 明确测试意图

### 3. 断言策略

- 一个测试一个关注点
- 使用具体的断言
- 验证用户可见的行为

### 4. Mock策略

- Mock外部API调用
- 模拟异步操作
- 控制测试环境

### 5. 错误测试

- 测试错误情况
- 验证错误处理
- 测试边界条件

## 持续集成

### GitHub Actions配置

```yaml
name: Frontend Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        node-version: [16, 18, 20]
        browser: [chrome, firefox]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: ${{ matrix.node-version }}
    
    - name: Install dependencies
      run: npm ci
    
    - name: Run tests
      run: npm run test:ci
      env:
        TEST_BROWSER: ${{ matrix.browser }}
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

### 测试报告

- HTML覆盖率报告
- JSON测试结果
- 截图和视频记录
- 性能指标收集

## 调试和故障排除

### 常见问题

1. **组件挂载失败**
   ```bash
   # 检查依赖注入
   # 确保正确设置全局插件
   ```

2. **异步测试超时**
   ```bash
   # 增加超时时间
   # 正确处理Promise
   ```

3. **Mock不生效**
   ```bash
   # 检查Mock路径
   # 确保在正确位置调用vi.mock()
   ```

4. **跨浏览器测试失败**
   ```bash
   # 检查浏览器特性支持
   # 添加必要的polyfill
   ```

### 调试技巧

1. **使用调试器**
   ```typescript
   it('should debug test', () => {
     debugger // 在浏览器中调试
     // 测试代码
   })
   ```

2. **查看DOM结构**
   ```typescript
   console.log(wrapper.html())
   ```

3. **检查组件状态**
   ```typescript
   console.log(wrapper.vm.$data)
   ```

4. **监听事件**
   ```typescript
   console.log(wrapper.emitted())
   ```

## 性能优化

### 测试性能

- 并行运行测试
- 合理使用beforeEach/afterEach
- 避免不必要的DOM操作
- 优化Mock对象创建

### 内存管理

- 及时清理事件监听器
- 销毁组件实例
- 清理定时器和异步操作

## 扩展和自定义

### 自定义测试工具

```typescript
// 创建测试辅助函数
export function createTestWrapper(component: any, options = {}) {
  return mount(component, {
    global: {
      plugins: [createPinia(), router],
      ...options.global
    },
    ...options
  })
}
```

### 自定义断言

```typescript
// 扩展expect断言
expect.extend({
  toBeVisible(received) {
    const pass = received.style.display !== 'none'
    return {
      message: () => `expected element to be visible`,
      pass
    }
  }
})
```

---

更多信息请参考项目文档或联系开发团队。