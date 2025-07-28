/**
 * 懒加载路由配置
 */
import { RouteRecordRaw } from 'vue-router'

// 懒加载组件函数
const lazyLoad = (view: string) => {
  return () => import(`@/views/${view}.vue`)
}

// 带加载状态的懒加载
const lazyLoadWithLoading = (view: string) => {
  return () => ({
    component: import(`@/views/${view}.vue`),
    loading: () => import('@/components/LoadingSpinner.vue'),
    error: () => import('@/components/ErrorFallback.vue'),
    delay: 200,
    timeout: 10000
  })
}

// 预加载关键路由
const preloadRoutes = [
  'dashboard/DashboardView',
  'strategies/StrategiesView',
  'trading/ManualTradingView'
]

// 预加载函数
export const preloadCriticalRoutes = () => {
  preloadRoutes.forEach(route => {
    import(`@/views/${route}.vue`).catch(() => {
      // 预加载失败时静默处理
    })
  })
}

// 路由配置
export const lazyRoutes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Home',
    redirect: '/dashboard'
  },
  
  // 认证相关路由
  {
    path: '/login',
    name: 'Login',
    component: lazyLoad('auth/LoginView'),
    meta: {
      requiresAuth: false,
      title: '登录',
      preload: false
    }
  },
  
  {
    path: '/register',
    name: 'Register',
    component: lazyLoad('auth/RegisterView'),
    meta: {
      requiresAuth: false,
      title: '注册',
      preload: false
    }
  },
  
  // 主要功能路由
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: lazyLoadWithLoading('dashboard/DashboardView'),
    meta: {
      requiresAuth: true,
      title: '仪表板',
      preload: true,
      keepAlive: true
    }
  },
  
  // 策略管理路由
  {
    path: '/strategies',
    name: 'Strategies',
    component: lazyLoadWithLoading('strategies/StrategiesView'),
    meta: {
      requiresAuth: true,
      title: '策略管理',
      preload: true,
      keepAlive: true
    }
  },
  
  {
    path: '/strategies/create',
    name: 'CreateStrategy',
    component: lazyLoad('strategies/CreateStrategyView'),
    meta: {
      requiresAuth: true,
      title: '创建策略',
      preload: false
    }
  },
  
  {
    path: '/strategies/:id/edit',
    name: 'EditStrategy',
    component: lazyLoad('strategies/StrategyEditorView'),
    meta: {
      requiresAuth: true,
      title: '编辑策略',
      preload: false
    }
  },
  
  {
    path: '/strategies/:id/test',
    name: 'TestStrategy',
    component: lazyLoad('strategies/StrategyTestView'),
    meta: {
      requiresAuth: true,
      title: '策略测试',
      preload: false
    }
  },
  
  // 回测相关路由
  {
    path: '/backtests',
    name: 'Backtests',
    component: lazyLoad('backtests/BacktestsView'),
    meta: {
      requiresAuth: true,
      title: '回测管理',
      preload: false,
      keepAlive: true
    }
  },
  
  {
    path: '/backtests/:id/results',
    name: 'BacktestResults',
    component: lazyLoad('backtests/BacktestResultView'),
    meta: {
      requiresAuth: true,
      title: '回测结果',
      preload: false
    }
  },
  
  // 交易相关路由
  {
    path: '/trading',
    name: 'Trading',
    component: lazyLoadWithLoading('trading/ManualTradingView'),
    meta: {
      requiresAuth: true,
      title: '手动交易',
      preload: true,
      keepAlive: true
    }
  },
  
  {
    path: '/trading/orders',
    name: 'Orders',
    component: lazyLoad('trading/OrdersView'),
    meta: {
      requiresAuth: true,
      title: '订单管理',
      preload: false,
      keepAlive: true
    }
  },
  
  {
    path: '/trading/positions',
    name: 'Positions',
    component: lazyLoad('trading/PositionsView'),
    meta: {
      requiresAuth: true,
      title: '持仓管理',
      preload: false,
      keepAlive: true
    }
  },
  
  // 风险控制路由
  {
    path: '/risk',
    name: 'Risk',
    component: lazyLoad('risk/RiskControlView'),
    meta: {
      requiresAuth: true,
      title: '风险控制',
      preload: false
    }
  },
  
  // 市场数据路由
  {
    path: '/market',
    name: 'Market',
    component: lazyLoad('market/MarketDataView'),
    meta: {
      requiresAuth: true,
      title: '市场数据',
      preload: false
    }
  },
  
  // 报告相关路由
  {
    path: '/reports',
    name: 'Reports',
    component: lazyLoad('reports/ReportsView'),
    meta: {
      requiresAuth: true,
      title: '报告中心',
      preload: false
    }
  },
  
  {
    path: '/reports/:id',
    name: 'ReportDetail',
    component: lazyLoad('reports/ReportDetailView'),
    meta: {
      requiresAuth: true,
      title: '报告详情',
      preload: false
    }
  },
  
  // 系统管理路由
  {
    path: '/system',
    name: 'System',
    component: lazyLoad('system/SystemView'),
    meta: {
      requiresAuth: true,
      requiresAdmin: true,
      title: '系统管理',
      preload: false
    }
  },
  
  {
    path: '/system/logs',
    name: 'SystemLogs',
    component: lazyLoad('system/LogsView'),
    meta: {
      requiresAuth: true,
      requiresAdmin: true,
      title: '系统日志',
      preload: false
    }
  },
  
  {
    path: '/system/monitoring',
    name: 'SystemMonitoring',
    component: lazyLoad('system/MonitoringView'),
    meta: {
      requiresAuth: true,
      requiresAdmin: true,
      title: '系统监控',
      preload: false
    }
  },
  
  // 用户相关路由
  {
    path: '/profile',
    name: 'Profile',
    component: lazyLoad('profile/ProfileView'),
    meta: {
      requiresAuth: true,
      title: '个人资料',
      preload: false
    }
  },
  
  {
    path: '/settings',
    name: 'Settings',
    component: lazyLoad('settings/SettingsView'),
    meta: {
      requiresAuth: true,
      title: '系统设置',
      preload: false
    }
  },
  
  // 帮助和文档路由
  {
    path: '/help',
    name: 'Help',
    component: lazyLoad('help/HelpView'),
    meta: {
      requiresAuth: false,
      title: '帮助中心',
      preload: false
    }
  },
  
  {
    path: '/docs',
    name: 'Documentation',
    component: lazyLoad('docs/DocumentationView'),
    meta: {
      requiresAuth: false,
      title: '文档中心',
      preload: false
    }
  },
  
  // 错误页面路由
  {
    path: '/403',
    name: 'Forbidden',
    component: lazyLoad('error/403View'),
    meta: {
      requiresAuth: false,
      title: '访问被拒绝',
      preload: false
    }
  },
  
  {
    path: '/404',
    name: 'NotFound',
    component: lazyLoad('error/404View'),
    meta: {
      requiresAuth: false,
      title: '页面未找到',
      preload: false
    }
  },
  
  {
    path: '/500',
    name: 'ServerError',
    component: lazyLoad('error/500View'),
    meta: {
      requiresAuth: false,
      title: '服务器错误',
      preload: false
    }
  },
  
  // 捕获所有未匹配的路由
  {
    path: '/:pathMatch(.*)*',
    redirect: '/404'
  }
]

// 路由预加载策略
export const routePreloadStrategy = {
  // 立即预加载关键路由
  immediate: [
    'dashboard/DashboardView',
    'strategies/StrategiesView',
    'trading/ManualTradingView'
  ],
  
  // 用户交互时预加载
  onHover: [
    'backtests/BacktestsView',
    'trading/OrdersView',
    'trading/PositionsView'
  ],
  
  // 空闲时预加载
  onIdle: [
    'risk/RiskControlView',
    'market/MarketDataView',
    'reports/ReportsView',
    'profile/ProfileView'
  ]
}

// 预加载管理器
export class RoutePreloader {
  private preloadedRoutes = new Set<string>()
  private preloadPromises = new Map<string, Promise<any>>()
  
  // 预加载单个路由
  async preloadRoute(routePath: string): Promise<void> {
    if (this.preloadedRoutes.has(routePath)) {
      return
    }
    
    if (this.preloadPromises.has(routePath)) {
      return this.preloadPromises.get(routePath)
    }
    
    const promise = import(`@/views/${routePath}.vue`)
      .then(() => {
        this.preloadedRoutes.add(routePath)
        this.preloadPromises.delete(routePath)
      })
      .catch((error) => {
        console.warn(`预加载路由失败: ${routePath}`, error)
        this.preloadPromises.delete(routePath)
      })
    
    this.preloadPromises.set(routePath, promise)
    return promise
  }
  
  // 批量预加载路由
  async preloadRoutes(routePaths: string[]): Promise<void> {
    const promises = routePaths.map(path => this.preloadRoute(path))
    await Promise.allSettled(promises)
  }
  
  // 预加载关键路由
  async preloadCriticalRoutes(): Promise<void> {
    await this.preloadRoutes(routePreloadStrategy.immediate)
  }
  
  // 空闲时预加载
  preloadOnIdle(): void {
    if ('requestIdleCallback' in window) {
      requestIdleCallback(() => {
        this.preloadRoutes(routePreloadStrategy.onIdle)
      })
    } else {
      // 降级方案
      setTimeout(() => {
        this.preloadRoutes(routePreloadStrategy.onIdle)
      }, 2000)
    }
  }
  
  // 获取预加载状态
  getPreloadStatus(): { loaded: string[], loading: string[] } {
    return {
      loaded: Array.from(this.preloadedRoutes),
      loading: Array.from(this.preloadPromises.keys())
    }
  }
}

// 全局预加载器实例
export const routePreloader = new RoutePreloader()