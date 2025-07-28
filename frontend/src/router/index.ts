import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'

// 配置NProgress
NProgress.configure({ showSpinner: false })

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/LoginView.vue'),
    meta: {
      title: '登录',
      requiresAuth: false
    }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/auth/RegisterView.vue'),
    meta: {
      title: '注册',
      requiresAuth: false
    }
  },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    meta: {
      requiresAuth: true
    },
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/DashboardView.vue'),
        meta: {
          title: '仪表板',
          icon: 'Dashboard'
        }
      },
      {
        path: '/trading',
        name: 'Trading',
        component: () => import('@/views/trading/TradingView.vue'),
        meta: {
          title: '交易',
          icon: 'TrendCharts'
        }
      },
      {
        path: '/trading/manual',
        name: 'ManualTrading',
        component: () => import('@/views/trading/ManualTradingView.vue'),
        meta: {
          title: '手动交易',
          hidden: true
        }
      },
      {
        path: '/orders',
        name: 'Orders',
        component: () => import('@/views/orders/OrdersView.vue'),
        meta: {
          title: '订单管理',
          icon: 'List'
        }
      },
      {
        path: '/positions',
        name: 'Positions',
        component: () => import('@/views/positions/PositionsView.vue'),
        meta: {
          title: '持仓管理',
          icon: 'PieChart'
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
        path: '/strategies',
        name: 'Strategies',
        component: () => import('@/views/strategies/StrategiesView.vue'),
        meta: {
          title: '策略管理',
          icon: 'Document'
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
        component: () => import('@/views/backtests/BacktestsView.vue'),
        meta: {
          title: '回测系统',
          icon: 'DataAnalysis'
        }
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
        component: () => import('@/views/market/MarketView.vue'),
        meta: {
          title: '市场数据',
          icon: 'Monitor'
        }
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
        path: '/settings',
        name: 'Settings',
        component: () => import('@/views/settings/SettingsView.vue'),
        meta: {
          title: '系统设置',
          icon: 'Setting',
          roles: ['admin']
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

router.afterEach(() => {
  NProgress.done()
})

export default router