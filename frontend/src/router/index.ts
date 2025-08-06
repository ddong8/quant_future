import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { createRoutePreloader } from '@/utils/routePreloader'
import { ElMessage } from 'element-plus'
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'

// 配置NProgress
NProgress.configure({ showSpinner: false })

// 路由懒加载辅助函数
const lazyLoad = (view: string, chunk?: string) => {
  const chunkName = chunk || view.toLowerCase()
  return () => import(/* webpackChunkName: "[request]" */ `@/views/${view}.vue`)
}

// 带错误处理的懒加载
const lazyLoadWithErrorHandling = (importFunc: () => Promise<any>, retries = 3) => {
  return async () => {
    for (let i = 0; i < retries; i++) {
      try {
        return await importFunc()
      } catch (error) {
        console.error(`Failed to load component (attempt ${i + 1}):`, error)
        if (i === retries - 1) {
          ElMessage.error('页面加载失败，请刷新重试')
          throw error
        }
        // 等待一段时间后重试
        await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)))
      }
    }
  }
}

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: lazyLoadWithErrorHandling(() => import(/* webpackChunkName: "auth" */ '@/views/auth/LoginView.vue')),
    meta: {
      title: '登录',
      requiresAuth: false
    }
  },
  {
    path: '/register',
    name: 'Register',
    component: lazyLoadWithErrorHandling(() => import(/* webpackChunkName: "auth" */ '@/views/auth/RegisterView.vue')),
    meta: {
      title: '注册',
      requiresAuth: false
    }
  },
  {
    path: '/',
    component: lazyLoadWithErrorHandling(() => import(/* webpackChunkName: "layout" */ '@/layouts/MainLayout.vue')),
    meta: {
      requiresAuth: true
    },
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: lazyLoadWithErrorHandling(() => import(/* webpackChunkName: "dashboard" */ '@/views/dashboard/DashboardView.vue')),
        meta: {
          title: '仪表板',
          icon: 'Dashboard',
          preload: true
        }
      },
      {
        path: 'trading',
        name: 'TradingOverview',
        component: lazyLoadWithErrorHandling(() => import(/* webpackChunkName: "trading" */ '@/views/trading/TradingView.vue')),
        meta: {
          title: '交易面板',
          icon: 'Monitor',
          parent: 'trading'
        }
      },
      {
        path: 'trading/manual',
        name: 'ManualTrading',
        component: () => import('@/views/trading/ManualTradingView.vue'),
        meta: {
          title: '手动交易',
          icon: 'Edit',
          parent: 'trading'
        }
      },
      {
        path: 'trading/quick',
        name: 'QuickTrading',
        component: () => import('@/views/trading/QuickTradingView.vue'),
        meta: {
          title: '快速交易',
          icon: 'Lightning',
          parent: 'trading'
        }
      },
      {
        path: 'orders',
        name: 'OrdersList',
        component: () => import('@/views/orders/OrdersView.vue'),
        meta: {
          title: '订单列表',
          icon: 'Document',
          parent: 'orders'
        }
      },
      {
        path: 'orders/history',
        name: 'OrderHistory',
        component: () => import('@/views/orders/OrderHistoryView.vue'),
        meta: {
          title: '历史订单',
          icon: 'Clock',
          parent: 'orders'
        }
      },
      {
        path: 'orders/templates',
        name: 'OrderTemplates',
        component: () => import('@/views/orders/OrderTemplatesView.vue'),
        meta: {
          title: '订单模板',
          icon: 'Collection',
          parent: 'orders'
        }
      },
      {
        path: 'positions',
        name: 'PositionsList',
        component: () => import('@/views/positions/PositionsView.vue'),
        meta: {
          title: '当前持仓',
          icon: 'Wallet',
          parent: 'positions'
        }
      },
      {
        path: 'positions/history',
        name: 'PositionHistory',
        component: () => import('@/views/positions/PositionHistoryView.vue'),
        meta: {
          title: '持仓历史',
          icon: 'Clock',
          parent: 'positions'
        }
      },
      {
        path: 'positions/analysis',
        name: 'PositionAnalysis',
        component: () => import('@/views/positions/PositionAnalysisView.vue'),
        meta: {
          title: '持仓分析',
          icon: 'DataAnalysis',
          parent: 'positions'
        }
      },
      {
        path: '/accounts',
        name: 'Accounts',
        component: () => import('@/views/accounts/AccountsView.vue'),
        meta: {
          title: '账户管理',
          icon: 'Wallet'
        }
      },
      {
        path: '/account',
        name: 'AccountOverview',
        component: () => import('@/views/account/AccountOverview.vue'),
        meta: {
          title: '账户概览',
          hidden: true
        }
      },
      {
        path: '/account/transactions',
        name: 'TransactionHistory',
        component: () => import('@/views/account/TransactionHistory.vue'),
        meta: {
          title: '交易流水',
          hidden: true
        }
      },
      {
        path: 'strategies',
        name: 'StrategiesList',
        component: () => import('@/views/strategies/StrategiesView.vue'),
        meta: {
          title: '策略列表',
          icon: 'List',
          parent: 'strategies'
        }
      },
      {
        path: 'strategies/create',
        name: 'StrategyCreate',
        component: () => import('@/views/strategies/StrategyCreateView.vue'),
        meta: {
          title: '创建策略',
          icon: 'Plus',
          parent: 'strategies'
        }
      },
      {
        path: 'strategies/templates',
        name: 'StrategyTemplates',
        component: () => import('@/views/strategies/StrategyTemplatesView.vue'),
        meta: {
          title: '策略模板',
          icon: 'Collection',
          parent: 'strategies'
        }
      },
      {
        path: 'strategies/performance',
        name: 'StrategyPerformance',
        component: () => import('@/views/strategies/StrategyPerformanceView.vue'),
        meta: {
          title: '策略绩效',
          icon: 'TrendCharts',
          parent: 'strategies'
        }
      },
      {
        path: '/strategies/:id',
        name: 'StrategyDetail',
        component: () => import('@/views/strategies/StrategyDetailView.vue'),
        meta: {
          title: '策略详情',
          hidden: true
        }
      },
      {
        path: '/strategies/:id/edit',
        name: 'StrategyEditor',
        component: () => import('@/views/strategies/StrategyEditorView.vue'),
        meta: {
          title: '策略编辑器',
          hidden: true
        }
      },
      {
        path: '/strategies/:id/test',
        name: 'StrategyTest',
        component: () => import('@/views/strategies/StrategyTestView.vue'),
        meta: {
          title: '策略测试',
          hidden: true
        }
      },
      {
        path: '/backtests',
        name: 'Backtests',
        meta: {
          title: '回测系统',
          icon: 'DataAnalysis'
        },
        children: [
          {
            path: '',
            name: 'BacktestsList',
            component: () => import('@/views/backtests/BacktestsView.vue'),
            meta: {
              title: '回测列表',
              icon: 'List'
            }
          },
          {
            path: 'create',
            name: 'BacktestCreate',
            component: () => import('@/views/backtests/BacktestCreateView.vue'),
            meta: {
              title: '创建回测',
              icon: 'Plus'
            }
          },
          {
            path: 'comparison',
            name: 'BacktestComparison',
            component: () => import('@/views/backtests/BacktestComparisonView.vue'),
            meta: {
              title: '回测对比',
              icon: 'DataBoard'
            }
          },
          {
            path: 'reports',
            name: 'BacktestReports',
            component: () => import('@/views/backtests/BacktestReportsView.vue'),
            meta: {
              title: '回测报告',
              icon: 'Document'
            }
          }
        ]
      },
      {
        path: '/backtests/:id',
        name: 'BacktestDetail',
        component: () => import('@/views/backtests/BacktestDetailView.vue'),
        meta: {
          title: '回测详情',
          hidden: true
        }
      },
      {
        path: '/backtests/:id/result',
        name: 'BacktestResult',
        component: () => import('@/views/backtests/BacktestResultView.vue'),
        meta: {
          title: '回测结果',
          hidden: true
        }
      },
      {
        path: '/risk',
        name: 'Risk',
        component: () => import('@/views/risk/RiskControlView.vue'),
        meta: {
          title: '风险控制',
          icon: 'Warning'
        }
      },
      {
        path: '/market',
        name: 'Market',
        meta: {
          title: '市场行情',
          icon: 'Monitor'
        },
        children: [
          {
            path: '',
            name: 'MarketQuotes',
            component: () => import('@/views/market/MarketQuotes.vue'),
            meta: {
              title: '实时行情',
              icon: 'TrendCharts'
            }
          },
          {
            path: 'technical',
            name: 'TechnicalAnalysis',
            component: () => import('@/views/market/TechnicalAnalysisView.vue'),
            meta: {
              title: '技术分析',
              icon: 'DataAnalysis'
            }
          },
          {
            path: 'news',
            name: 'MarketNews',
            component: () => import('@/views/market/MarketNewsView.vue'),
            meta: {
              title: '市场资讯',
              icon: 'ChatDotRound'
            }
          },
          {
            path: 'calendar',
            name: 'EconomicCalendar',
            component: () => import('@/views/market/EconomicCalendarView.vue'),
            meta: {
              title: '财经日历',
              icon: 'Calendar'
            }
          }
        ]
      },
      {
        path: '/profile',
        name: 'Profile',
        component: () => import('@/views/profile/ProfileView.vue'),
        meta: {
          title: '个人中心',
          icon: 'User',
          hidden: true
        }
      },
      {
        path: 'settings',
        name: 'GeneralSettings',
        component: () => import('@/views/settings/SettingsView.vue'),
        meta: {
          title: '通用设置',
          icon: 'Setting',
          parent: 'settings',
          roles: ['admin']
        }
      },
      {
        path: 'settings/account',
        name: 'AccountSettings',
        component: () => import('@/views/settings/AccountSettingsView.vue'),
        meta: {
          title: '账户设置',
          icon: 'User',
          parent: 'settings'
        }
      },
      {
        path: 'settings/trading',
        name: 'TradingSettings',
        component: () => import('@/views/settings/TradingSettingsView.vue'),
        meta: {
          title: '交易设置',
          icon: 'TrendCharts',
          parent: 'settings'
        }
      },
      {
        path: 'settings/notifications',
        name: 'NotificationSettings',
        component: () => import('@/views/settings/NotificationSettingsView.vue'),
        meta: {
          title: '通知设置',
          icon: 'Bell',
          parent: 'settings'
        }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/error/NotFoundView.vue'),
    meta: {
      title: '页面不存在'
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  }
})

// 创建路由预加载器
const routePreloader = createRoutePreloader(router)

// 初始化预加载功能
router.onReady?.(() => {
  // 预加载标记的路由
  routePreloader.preloadMarkedRoutes()
  
  // 设置悬停预加载
  routePreloader.setupHoverPreload()
  
  // 在空闲时间预加载
  routePreloader.preloadOnIdle()
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  NProgress.start()
  
  const authStore = useAuthStore()
  
  // 设置页面标题
  if (to.meta.title) {
    document.title = `${to.meta.title} - 量化交易平台`
  }
  
  // 检查是否需要认证
  if (to.meta.requiresAuth !== false) {
    if (!authStore.isAuthenticated) {
      // 尝试从本地存储恢复认证状态
      await authStore.initAuth()
      
      if (!authStore.isAuthenticated) {
        next({
          name: 'Login',
          query: { redirect: to.fullPath }
        })
        return
      }
    }
    
    // 检查角色权限
    if (to.meta.roles && Array.isArray(to.meta.roles)) {
      const userRole = authStore.user?.role
      if (!userRole || !to.meta.roles.includes(userRole)) {
        next({ name: 'Dashboard' })
        return
      }
    }
  }
  
  // 如果已登录用户访问登录页，重定向到仪表板
  if (authStore.isAuthenticated && (to.name === 'Login' || to.name === 'Register')) {
    next({ name: 'Dashboard' })
    return
  }
  
  next()
})

router.afterEach((to) => {
  NProgress.done()
  
  // 智能预加载下一个可能访问的路由
  if (routePreloader) {
    routePreloader.intelligentPreload()
  }
  
  // 记录页面访问性能
  if ('performance' in window) {
    setTimeout(() => {
      const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming
      if (navigation) {
        const loadTime = navigation.loadEventEnd - navigation.loadEventStart
        console.log(`Page ${to.name} loaded in ${loadTime}ms`)
      }
    }, 0)
  }
})

export default router