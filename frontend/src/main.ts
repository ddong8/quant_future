import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import zhCn from 'element-plus/es/locale/lang/zh-cn'

import App from './App.vue'
import router from './router'
import { useAuthStore } from '@/stores/auth'
import { createGlobalResponsive } from '@/composables/useResponsive'
import './styles/index.scss'

// 性能监控
if ('performance' in window) {
  // 监控首屏加载时间
  window.addEventListener('load', () => {
    const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming
    if (navigation) {
      const loadTime = navigation.loadEventEnd - navigation.loadEventStart
      console.log(`App loaded in ${loadTime}ms`)
      
      // 记录性能指标
      const metrics = {
        loadTime,
        domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
        firstPaint: performance.getEntriesByName('first-paint')[0]?.startTime || 0,
        firstContentfulPaint: performance.getEntriesByName('first-contentful-paint')[0]?.startTime || 0
      }
      
      console.log('Performance metrics:', metrics)
    }
  })
}

const app = createApp(App)

// 注册Element Plus图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

const pinia = createPinia()
app.use(pinia)
app.use(router)
app.use(ElementPlus, {
  locale: zhCn,
})

// 初始化全局响应式实例
createGlobalResponsive()

// 初始化认证状态
const authStore = useAuthStore()

// 性能优化初始化
const initPerformanceOptimization = () => {
  // 预加载关键资源
  const criticalResources = [
    '/api/user/profile',
    '/api/dashboard/summary'
  ]
  
  criticalResources.forEach(resource => {
    const link = document.createElement('link')
    link.rel = 'prefetch'
    link.href = resource
    document.head.appendChild(link)
  })
  
  // 启用性能监控（仅在开发环境）
  if (process.env.NODE_ENV === 'development') {
    try {
      import('@/composables/usePerformanceOptimization').then(({ usePerformanceOptimization }) => {
        const { autoOptimize } = usePerformanceOptimization()
        setTimeout(autoOptimize, 2000) // 延迟2秒后自动优化
      }).catch(() => {
        console.log('Performance optimization not available')
      })
    } catch (error) {
      console.log('Performance optimization not available')
    }
  }
}

authStore.initAuth().then(() => {
  app.mount('#app')
  initPerformanceOptimization()
}).catch(() => {
  // 即使初始化失败也要挂载应用
  app.mount('#app')
  initPerformanceOptimization()
})