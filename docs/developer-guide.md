# 量化交易平台开发者指南

## 目录

1. [架构概述](#架构概述)
2. [开发环境搭建](#开发环境搭建)
3. [后端开发](#后端开发)
4. [前端开发](#前端开发)
5. [数据库设计](#数据库设计)
6. [API设计](#api设计)
7. [测试指南](#测试指南)
8. [部署指南](#部署指南)
9. [代码规范](#代码规范)
10. [最佳实践](#最佳实践)

## 架构概述

### 系统架构

量化交易平台采用前后端分离的微服务架构：

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   前端 (Vue.js)  │    │  API网关(Nginx) │    │ 后端(FastAPI)   │
│                 │◄──►│                 │◄──►│                 │
│ - 用户界面      │    │ - 反向代理      │    │ - 业务逻辑      │
│ - 状态管理      │    │ - 负载均衡      │    │ - API服务       │
│ - 路由管理      │    │ - SSL终止       │    │ - 认证授权      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                       ┌─────────────────────────────────┼─────────────────────────────────┐
                       │                                 │                                 │
                       ▼                                 ▼                                 ▼
            ┌─────────────────┐              ┌─────────────────┐              ┌─────────────────┐
            │ PostgreSQL      │              │ InfluxDB        │              │ Redis           │
            │                 │              │                 │              │                 │
            │ - 用户数据      │              │ - 时序数据      │              │ - 缓存          │
            │ - 策略信息      │              │ - 行情数据      │              │ - 会话存储      │
            │ - 交易记录      │              │ - 监控指标      │              │ - 消息队列      │
            └─────────────────┘              └─────────────────┘              └─────────────────┘
```

### 技术选型理由

- **FastAPI**: 高性能、自动API文档生成、类型提示支持
- **Vue.js 3**: 渐进式框架、Composition API、TypeScript支持
- **PostgreSQL**: ACID事务、复杂查询、JSON支持
- **InfluxDB**: 时序数据优化、高写入性能、数据压缩
- **Redis**: 高性能缓存、发布订阅、分布式锁

## 开发环境搭建

### 系统要求

- **操作系统**: Linux/macOS/Windows
- **Python**: 3.9+
- **Node.js**: 16+
- **Docker**: 20.10+
- **Git**: 2.30+

### 开发工具推荐

- **IDE**: VS Code / PyCharm / WebStorm
- **API测试**: Postman / Insomnia
- **数据库工具**: DBeaver / pgAdmin
- **版本控制**: Git + GitHub/GitLab### 
环境配置

#### 1. 克隆项目

```bash
git clone https://github.com/your-org/quantitative-trading-platform.git
cd quantitative-trading-platform
```

#### 2. 后端环境设置

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 安装开发依赖
pip install -r requirements-dev.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件
```

#### 3. 前端环境设置

```bash
cd frontend

# 安装依赖
npm install

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件
```

#### 4. 数据库设置

```bash
# 启动数据库服务
docker-compose up -d postgres influxdb redis

# 运行数据库迁移
cd backend
alembic upgrade head

# 初始化数据
python init_db.py
```

## 后端开发

### 项目结构

```
backend/
├── app/
│   ├── api/                # API路由
│   │   └── v1/            # API版本1
│   │       ├── auth.py    # 认证相关
│   │       ├── users.py   # 用户管理
│   │       └── ...
│   ├── core/              # 核心模块
│   │   ├── config.py      # 配置管理
│   │   ├── database.py    # 数据库连接
│   │   ├── security.py    # 安全认证
│   │   └── exceptions.py  # 异常处理
│   ├── models/            # SQLAlchemy模型
│   ├── schemas/           # Pydantic模式
│   ├── services/          # 业务逻辑层
│   └── main.py           # 应用入口
├── alembic/              # 数据库迁移
├── tests/                # 测试代码
└── requirements.txt      # 依赖管理
```

### 核心组件

#### 1. 配置管理 (core/config.py)

```python
from pydantic import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "量化交易平台"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # 数据库配置
    DATABASE_URL: str
    INFLUXDB_URL: str
    REDIS_URL: str
    
    # JWT配置
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    class Config:
        env_file = ".env"

settings = Settings()
```

#### 2. 数据库连接 (core/database.py)

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```#### 
3. 认证安全 (core/security.py)

```python
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt
```

### 数据模型设计

#### 1. 基础模型 (models/base.py)

```python
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class BaseModel(Base):
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

#### 2. 用户模型 (models/user.py)

```python
from sqlalchemy import Column, String, Boolean, Enum
from sqlalchemy.orm import relationship
from .base import BaseModel
from .enums import UserRole

class User(BaseModel):
    __tablename__ = "users"
    
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.TRADER)
    is_active = Column(Boolean, default=True)
    
    # 关系
    strategies = relationship("Strategy", back_populates="user")
    orders = relationship("Order", back_populates="user")
```

### 服务层设计

#### 1. 基础服务 (services/base.py)

```python
from typing import Generic, TypeVar, Type, Optional, List
from sqlalchemy.orm import Session
from app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")

class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model
    
    def get(self, db: Session, id: int) -> Optional[ModelType]:
        return db.query(self.model).filter(self.model.id == id).first()
    
    def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[ModelType]:
        return db.query(self.model).offset(skip).limit(limit).all()
    
    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        obj_data = obj_in.dict()
        db_obj = self.model(**obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
```

#### 2. 用户服务 (services/user_service.py)

```python
from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password
from .base import BaseService

class UserService(BaseService[User, UserCreate, UserUpdate]):
    def get_by_username(self, db: Session, *, username: str) -> Optional[User]:
        return db.query(User).filter(User.username == username).first()
    
    def authenticate(self, db: Session, *, username: str, password: str) -> Optional[User]:
        user = self.get_by_username(db, username=username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
    
    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        db_obj = User(
            username=obj_in.username,
            email=obj_in.email,
            hashed_password=get_password_hash(obj_in.password),
            role=obj_in.role,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

user_service = UserService(User)
```##
# API路由设计

#### 1. 路由结构

```python
# api/v1/__init__.py
from fastapi import APIRouter
from .auth import router as auth_router
from .users import router as users_router
from .strategies import router as strategies_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["认证"])
api_router.include_router(users_router, prefix="/users", tags=["用户管理"])
api_router.include_router(strategies_router, prefix="/strategies", tags=["策略管理"])
```

#### 2. 认证路由 (api/v1/auth.py)

```python
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token
from app.schemas.auth import Token
from app.services.user_service import user_service

router = APIRouter()

@router.post("/login", response_model=Token)
async def login(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    user = user_service.authenticate(
        db, username=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }
```

## 前端开发

### 项目结构

```
frontend/src/
├── api/                  # API客户端
├── components/           # 可复用组件
├── views/               # 页面视图
├── stores/              # Pinia状态管理
├── router/              # Vue Router配置
├── types/               # TypeScript类型定义
├── utils/               # 工具函数
├── styles/              # 全局样式
└── main.ts             # 应用入口
```

### 核心组件

#### 1. API客户端 (api/client.ts)

```typescript
import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import { useAuthStore } from '@/stores/auth'

class ApiClient {
  private instance: AxiosInstance

  constructor() {
    this.instance = axios.create({
      baseURL: import.meta.env.VITE_API_BASE_URL,
      timeout: 10000,
    })

    this.setupInterceptors()
  }

  private setupInterceptors() {
    // 请求拦截器
    this.instance.interceptors.request.use(
      (config) => {
        const authStore = useAuthStore()
        if (authStore.token) {
          config.headers.Authorization = `Bearer ${authStore.token}`
        }
        return config
      },
      (error) => Promise.reject(error)
    )

    // 响应拦截器
    this.instance.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          const authStore = useAuthStore()
          await authStore.logout()
        }
        return Promise.reject(error)
      }
    )
  }

  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<T> = await this.instance.get(url, config)
    return response.data
  }

  async post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<T> = await this.instance.post(url, data, config)
    return response.data
  }
}

export const apiClient = new ApiClient()
```

#### 2. 状态管理 (stores/auth.ts)

```typescript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User, LoginRequest, LoginResponse } from '@/types/auth'
import { authApi } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  // State
  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<User | null>(null)
  const loading = ref(false)

  // Getters
  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  // Actions
  const login = async (credentials: LoginRequest) => {
    loading.value = true
    try {
      const response = await authApi.login(credentials)
      token.value = response.access_token
      user.value = response.user
      localStorage.setItem('token', response.access_token)
      return response
    } finally {
      loading.value = false
    }
  }

  const logout = async () => {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
  }

  const fetchProfile = async () => {
    if (!token.value) return
    
    try {
      user.value = await authApi.getProfile()
    } catch (error) {
      await logout()
    }
  }

  return {
    token,
    user,
    loading,
    isAuthenticated,
    isAdmin,
    login,
    logout,
    fetchProfile
  }
})
```#### 
3. 路由配置 (router/index.ts)

```typescript
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/LoginView.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('@/views/dashboard/DashboardView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/strategies',
    name: 'Strategies',
    component: () => import('@/views/strategies/StrategiesView.vue'),
    meta: { requiresAuth: true, roles: ['admin', 'trader'] }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
    return
  }
  
  if (to.meta.roles && !to.meta.roles.includes(authStore.user?.role)) {
    next('/403')
    return
  }
  
  next()
})

export default router
```

### 组件开发规范

#### 1. 基础组件示例

```vue
<template>
  <div class="strategy-card" :class="{ active: strategy.status === 'active' }">
    <div class="strategy-header">
      <h3>{{ strategy.name }}</h3>
      <el-tag :type="statusType">{{ statusText }}</el-tag>
    </div>
    
    <div class="strategy-content">
      <p>{{ strategy.description }}</p>
      <div class="strategy-stats">
        <span>收益率: {{ formatPercent(strategy.return_rate) }}</span>
        <span>最大回撤: {{ formatPercent(strategy.max_drawdown) }}</span>
      </div>
    </div>
    
    <div class="strategy-actions">
      <el-button @click="handleEdit" size="small">编辑</el-button>
      <el-button 
        @click="handleToggle" 
        :type="strategy.status === 'active' ? 'danger' : 'success'"
        size="small"
      >
        {{ strategy.status === 'active' ? '停止' : '启动' }}
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Strategy } from '@/types/strategy'

interface Props {
  strategy: Strategy
}

interface Emits {
  (e: 'edit', strategy: Strategy): void
  (e: 'toggle', strategy: Strategy): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const statusType = computed(() => {
  switch (props.strategy.status) {
    case 'active': return 'success'
    case 'paused': return 'warning'
    case 'stopped': return 'danger'
    default: return 'info'
  }
})

const statusText = computed(() => {
  const statusMap = {
    active: '运行中',
    paused: '已暂停',
    stopped: '已停止',
    draft: '草稿'
  }
  return statusMap[props.strategy.status] || '未知'
})

const formatPercent = (value: number) => {
  return `${(value * 100).toFixed(2)}%`
}

const handleEdit = () => {
  emit('edit', props.strategy)
}

const handleToggle = () => {
  emit('toggle', props.strategy)
}
</script>

<style scoped>
.strategy-card {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  transition: all 0.3s;
}

.strategy-card:hover {
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.strategy-card.active {
  border-color: #67c23a;
}

.strategy-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.strategy-stats {
  display: flex;
  gap: 16px;
  font-size: 14px;
  color: #606266;
}

.strategy-actions {
  margin-top: 12px;
  display: flex;
  gap: 8px;
}
</style>
```

## 数据库设计

### 表结构设计

#### 1. 用户表 (users)

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'trader',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
```

#### 2. 策略表 (strategies)

```sql
CREATE TABLE strategies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    code TEXT NOT NULL,
    language VARCHAR(20) DEFAULT 'python',
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'draft',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_strategies_user_id ON strategies(user_id);
CREATE INDEX idx_strategies_status ON strategies(status);
CREATE INDEX idx_strategies_name ON strategies(name);
```

### 时序数据设计 (InfluxDB)

#### 1. 行情数据

```
measurement: quotes
tags:
  - symbol: 合约代码
  - exchange: 交易所
fields:
  - last_price: 最新价
  - bid_price: 买一价
  - ask_price: 卖一价
  - volume: 成交量
  - open_interest: 持仓量
timestamp: 时间戳
```

#### 2. 交易记录

```
measurement: trades
tags:
  - user_id: 用户ID
  - strategy_id: 策略ID
  - symbol: 合约代码
fields:
  - direction: 买卖方向
  - volume: 交易量
  - price: 成交价格
  - pnl: 盈亏
timestamp: 交易时间
```## 
API设计

### RESTful API设计原则

1. **资源导向**: URL表示资源，HTTP方法表示操作
2. **状态码**: 正确使用HTTP状态码
3. **版本控制**: 通过URL路径进行版本控制
4. **统一响应格式**: 所有API返回统一的响应格式

### API响应格式

```typescript
interface ApiResponse<T> {
  success: boolean
  data?: T
  message?: string
  error_code?: string
  error_message?: string
  timestamp: string
  request_id: string
}
```

### 分页响应格式

```typescript
interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}
```

### 错误处理

```python
# 自定义异常类
class BusinessLogicError(Exception):
    def __init__(self, error_code: str, message: str, status_code: int = 400):
        self.error_code = error_code
        self.message = message
        self.status_code = status_code

# 全局异常处理器
@app.exception_handler(BusinessLogicError)
async def business_logic_exception_handler(request: Request, exc: BusinessLogicError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error_code": exc.error_code,
            "error_message": exc.message,
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": str(uuid.uuid4())
        }
    )
```

## 测试指南

### 后端测试

#### 1. 单元测试

```python
# tests/test_user_service.py
import pytest
from sqlalchemy.orm import Session
from app.services.user_service import user_service
from app.schemas.user import UserCreate

def test_create_user(db: Session):
    user_data = UserCreate(
        username="testuser",
        email="test@example.com",
        password="testpassword",
        role="trader"
    )
    
    user = user_service.create(db, obj_in=user_data)
    
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.role == "trader"
    assert user.is_active is True

def test_authenticate_user(db: Session):
    # 创建测试用户
    user_data = UserCreate(
        username="testuser",
        email="test@example.com",
        password="testpassword"
    )
    user_service.create(db, obj_in=user_data)
    
    # 测试认证
    authenticated_user = user_service.authenticate(
        db, username="testuser", password="testpassword"
    )
    assert authenticated_user is not None
    assert authenticated_user.username == "testuser"
    
    # 测试错误密码
    wrong_auth = user_service.authenticate(
        db, username="testuser", password="wrongpassword"
    )
    assert wrong_auth is None
```

#### 2. 集成测试

```python
# tests/test_auth_api.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_login_success():
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "testuser", "password": "testpassword"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert data["data"]["token_type"] == "bearer"

def test_login_invalid_credentials():
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "testuser", "password": "wrongpassword"}
    )
    
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert "error_message" in data
```

### 前端测试

#### 1. 组件测试

```typescript
// tests/components/StrategyCard.test.ts
import { mount } from '@vue/test-utils'
import { describe, it, expect } from 'vitest'
import StrategyCard from '@/components/StrategyCard.vue'
import type { Strategy } from '@/types/strategy'

describe('StrategyCard', () => {
  const mockStrategy: Strategy = {
    id: 1,
    name: '测试策略',
    description: '这是一个测试策略',
    status: 'active',
    return_rate: 0.15,
    max_drawdown: 0.08
  }

  it('renders strategy information correctly', () => {
    const wrapper = mount(StrategyCard, {
      props: { strategy: mockStrategy }
    })

    expect(wrapper.find('h3').text()).toBe('测试策略')
    expect(wrapper.find('p').text()).toBe('这是一个测试策略')
    expect(wrapper.find('.strategy-stats').text()).toContain('15.00%')
  })

  it('emits edit event when edit button is clicked', async () => {
    const wrapper = mount(StrategyCard, {
      props: { strategy: mockStrategy }
    })

    await wrapper.find('.edit-button').trigger('click')
    expect(wrapper.emitted('edit')).toBeTruthy()
    expect(wrapper.emitted('edit')[0]).toEqual([mockStrategy])
  })
})
```

#### 2. E2E测试

```typescript
// tests/e2e/login.test.ts
import { test, expect } from '@playwright/test'

test('user can login successfully', async ({ page }) => {
  await page.goto('/login')
  
  await page.fill('[data-testid="username"]', 'testuser')
  await page.fill('[data-testid="password"]', 'testpassword')
  await page.click('[data-testid="login-button"]')
  
  await expect(page).toHaveURL('/dashboard')
  await expect(page.locator('[data-testid="user-menu"]')).toBeVisible()
})

test('shows error for invalid credentials', async ({ page }) => {
  await page.goto('/login')
  
  await page.fill('[data-testid="username"]', 'testuser')
  await page.fill('[data-testid="password"]', 'wrongpassword')
  await page.click('[data-testid="login-button"]')
  
  await expect(page.locator('[data-testid="error-message"]')).toBeVisible()
  await expect(page.locator('[data-testid="error-message"]')).toContainText('用户名或密码错误')
})
```

## 部署指南

### Docker部署

#### 1. Dockerfile

```dockerfile
# backend/Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```dockerfile
# frontend/Dockerfile
FROM node:16-alpine as build

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

#### 2. Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: trading_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"

  influxdb:
    image: influxdb:2.0
    environment:
      INFLUXDB_DB: trading
      INFLUXDB_ADMIN_USER: admin
      INFLUXDB_ADMIN_PASSWORD: password
    volumes:
      - influxdb_data:/var/lib/influxdb2
    ports:
      - "8086:8086"

  backend:
    build: ./backend
    environment:
      DATABASE_URL: postgresql://postgres:password@postgres:5432/trading_db
      REDIS_URL: redis://redis:6379/0
      INFLUXDB_URL: http://influxdb:8086
    depends_on:
      - postgres
      - redis
      - influxdb
    ports:
      - "8000:8000"

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend

volumes:
  postgres_data:
  influxdb_data:
```

### Kubernetes部署

#### 1. 部署配置

```yaml
# k8s/backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: trading-platform/backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
```

## 代码规范

### Python代码规范

#### 1. 代码格式化

```python
# pyproject.toml
[tool.black]
line-length = 88
target-version = ['py39']
include = '\.pyi?$'

[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88

[tool.flake8]
max-line-length = 88
extend-ignore = E203, W503
```

#### 2. 类型注解

```python
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class UserService:
    def __init__(self, db_session: Session) -> None:
        self.db = db_session
    
    async def get_user(self, user_id: int) -> Optional[User]:
        return await self.db.query(User).filter(User.id == user_id).first()
    
    async def get_users(
        self, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[User]:
        return await self.db.query(User).offset(skip).limit(limit).all()
```

### TypeScript代码规范

#### 1. ESLint配置

```json
{
  "extends": [
    "@vue/typescript/recommended",
    "@vue/prettier",
    "@vue/prettier/@typescript-eslint"
  ],
  "rules": {
    "@typescript-eslint/no-unused-vars": "error",
    "@typescript-eslint/explicit-function-return-type": "warn",
    "vue/component-name-in-template-casing": ["error", "PascalCase"]
  }
}
```

#### 2. 类型定义

```typescript
// types/api.ts
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  message?: string
  error_code?: string
  error_message?: string
  timestamp: string
  request_id: string
}

export interface PaginationParams {
  page?: number
  size?: number
  search?: string
}

export interface PaginatedData<T> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}
```

## 最佳实践

### 安全最佳实践

1. **输入验证**: 所有用户输入都必须验证
2. **SQL注入防护**: 使用ORM和参数化查询
3. **XSS防护**: 对输出进行转义
4. **CSRF防护**: 使用CSRF令牌
5. **密码安全**: 使用强哈希算法存储密码

### 性能最佳实践

1. **数据库优化**: 合理使用索引和查询优化
2. **缓存策略**: 使用Redis缓存热点数据
3. **异步处理**: 使用Celery处理耗时任务
4. **前端优化**: 代码分割和懒加载
5. **CDN使用**: 静态资源使用CDN加速

### 监控最佳实践

1. **日志记录**: 结构化日志记录
2. **指标监控**: 使用Prometheus收集指标
3. **告警设置**: 关键指标告警
4. **链路追踪**: 分布式链路追踪
5. **健康检查**: 服务健康检查端点

---

*本指南会根据项目发展持续更新，欢迎贡献改进建议。*