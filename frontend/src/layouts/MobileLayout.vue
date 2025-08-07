<template>
  <div class="mobile-layout" :class="layoutClasses">
    <!-- 移动端导航 -->
    <MobileNavigation
      :show-search="true"
      :show-notifications="true"
      :show-user-menu="true"
      :show-bottom-nav="showBottomNav"
    />

    <!-- 主要内容区域 -->
    <main class="mobile-main" :class="{ 'has-bottom-nav': showBottomNav }">
      <div class="mobile-content">
        <!-- 页面内容 -->
        <router-view v-slot="{ Component, route }">
          <transition
            :name="transitionName"
            mode="out-in"
            @before-enter="onBeforeEnter"
            @after-enter="onAfterEnter"
          >
            <keep-alive :include="keepAliveComponents">
              <component
                :is="Component"
                :key="route.fullPath"
                class="mobile-page"
              />
            </keep-alive>
          </transition>
        </router-view>
      </div>
    </main>

    <!-- 全局组件 -->
    <GlobalComponents />

    <!-- 性能监控 -->
    <PerformanceMonitor v-if="showPerformanceMonitor" />

    <!-- PWA 更新提示 -->
    <PWAUpdatePrompt />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useResponsive } from '@/composables/useResponsive'
import { usePerformanceOptimization } from '@/composables/usePerformanceOptimization'
import MobileNavigation from '@/components/navigation/MobileNavigation.vue'
import GlobalComponents from '@/components/common/GlobalComponents.vue'
import PerformanceMonitor from '@/components/common/PerformanceMonitor.vue'
import PWAUpdatePrompt from '@/components/common/PWAUpdatePrompt.vue'

const route = useRoute()
const router = useRouter()

// 响应式功能
const {
  isMobile,
  deviceInfo,
  currentBreakpoint,
  prefersReducedMotion,
  responsiveClasses
} = useResponsive()

// 性能优化
const { startMonitoring, stopMonitoring } = usePerformanceOptimization()

// 状态
const transitionName = ref('slide-left')
const routeHistory = ref<string[]>([])
const showPerformanceMonitor = ref(process.env.NODE_ENV === 'development')

// 计算属性
const layoutClasses = computed(() => [
  ...responsiveClasses.value,
  {
    'mobile-optimized': isMobile.value,
    'touch-optimized': deviceInfo.value.isTouch,
    'high-dpi-optimized': deviceInfo.value.isRetina,
    'landscape-optimized': deviceInfo.value.orientation === 'landscape',
    'portrait-optimized': deviceInfo.value.orientation === 'portrait',
    'accessibility-optimized': prefersReducedMotion.value
  }
])

// 是否显示底部导航
const showBottomNav = computed(() => {
  const path = route.path
  // 在某些页面隐藏底部导航
  const hiddenPaths = ['/login', '/register', '/profile']
  return !hiddenPaths.some(hiddenPath => path.startsWith(hiddenPath))
})

// 需要缓存的组件
const keepAliveComponents = computed(() => [
  'DashboardView',
  'TradingView',
  'StrategiesView',
  'MarketQuotes'
])

// 路由转场动画
const getTransitionName = (to: string, from: string) => {
  if (prefersReducedMotion.value) return 'fade'
  
  const toIndex = routeHistory.value.indexOf(to)
  const fromIndex = routeHistory.value.indexOf(from)
  
  if (toIndex > fromIndex) {
    return 'slide-left'
  } else if (toIndex < fromIndex) {
    return 'slide-right'
  } else {
    return 'fade'
  }
}

// 监听路由变化
watch(() => route.path, (to, from) => {
  // 更新路由历史
  if (!routeHistory.value.includes(to)) {
    routeHistory.value.push(to)
  }
  
  // 设置转场动画
  transitionName.value = getTransitionName(to, from)
  
  // 滚动到顶部
  setTimeout(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }, 100)
})

// 转场动画事件
const onBeforeEnter = () => {
  // 转场开始前的处理
  document.body.style.overflow = 'hidden'
}

const onAfterEnter = () => {
  // 转场完成后的处理
  document.body.style.overflow = ''
}

// 处理返回按钮
const handleBackButton = (event: PopStateEvent) => {
  event.preventDefault()
  
  // 如果有历史记录，则返回上一页
  if (routeHistory.value.length > 1) {
    routeHistory.value.pop()
    const previousRoute = routeHistory.value[routeHistory.value.length - 1]
    router.push(previousRoute)
  } else {
    // 否则返回首页
    router.push('/')
  }
}

// 处理屏幕方向变化
const handleOrientationChange = () => {
  // 延迟处理以确保获取正确的尺寸
  setTimeout(() => {
    // 重新计算布局
    window.dispatchEvent(new Event('resize'))
  }, 100)
}

// 处理可见性变化
const handleVisibilityChange = () => {
  if (document.hidden) {
    // 页面隐藏时暂停性能监控
    stopMonitoring()
  } else {
    // 页面显示时恢复性能监控
    startMonitoring()
  }
}

// 生命周期
onMounted(() => {
  // 启动性能监控
  startMonitoring()
  
  // 添加事件监听
  window.addEventListener('popstate', handleBackButton)
  window.addEventListener('orientationchange', handleOrientationChange)
  document.addEventListener('visibilitychange', handleVisibilityChange)
  
  // 设置初始路由历史
  routeHistory.value = [route.path]
  
  // 设置视口元标签
  const viewport = document.querySelector('meta[name="viewport"]')
  if (viewport) {
    viewport.setAttribute('content', 
      'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover'
    )
  }
  
  // 设置状态栏样式
  const statusBarStyle = document.createElement('meta')
  statusBarStyle.name = 'apple-mobile-web-app-status-bar-style'
  statusBarStyle.content = 'default'
  document.head.appendChild(statusBarStyle)
  
  // 设置全屏模式
  const webAppCapable = document.createElement('meta')
  webAppCapable.name = 'apple-mobile-web-app-capable'
  webAppCapable.content = 'yes'
  document.head.appendChild(webAppCapable)
})

onUnmounted(() => {
  // 停止性能监控
  stopMonitoring()
  
  // 移除事件监听
  window.removeEventListener('popstate', handleBackButton)
  window.removeEventListener('orientationchange', handleOrientationChange)
  document.removeEventListener('visibilitychange', handleVisibilityChange)
})
</script>

<style lang="scss" scoped>
.mobile-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  
  // 启用硬件加速
  transform: translateZ(0);
  // 优化渲染性能
  contain: layout style paint;
}

.mobile-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  margin-top: 56px; // 为顶部导航留出空间
  
  &.has-bottom-nav {
    margin-bottom: 60px; // 为底部导航留出空间
  }
}

.mobile-content {
  flex: 1;
  overflow: hidden;
  position: relative;
}

.mobile-page {
  height: 100%;
  overflow-y: auto;
  overflow-x: hidden;
  
  // 优化滚动性能
  -webkit-overflow-scrolling: touch;
  scroll-behavior: smooth;
  
  // 减少重绘
  contain: layout style paint;
}

// 转场动画
.slide-left-enter-active,
.slide-left-leave-active,
.slide-right-enter-active,
.slide-right-leave-active {
  transition: transform 0.3s ease-out;
}

.slide-left-enter-from {
  transform: translateX(100%);
}

.slide-left-leave-to {
  transform: translateX(-100%);
}

.slide-right-enter-from {
  transform: translateX(-100%);
}

.slide-right-leave-to {
  transform: translateX(100%);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

// 移动端优化
.mobile-optimized {
  // 减少复杂样式以提高性能
  * {
    box-shadow: none;
    border-radius: 4px;
  }
  
  // 简化动画
  .slide-left-enter-active,
  .slide-left-leave-active,
  .slide-right-enter-active,
  .slide-right-leave-active {
    transition-duration: 0.2s;
  }
}

// 触摸优化
.touch-optimized {
  // 优化触摸滚动
  .mobile-page {
    -webkit-overflow-scrolling: touch;
    overscroll-behavior: contain;
  }
  
  // 防止双击缩放
  * {
    touch-action: manipulation;
  }
}

// 高DPI优化
.high-dpi-optimized {
  // 优化图标和文字渲染
  * {
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }
}

// 横屏优化
.landscape-optimized {
  .mobile-main {
    margin-top: 48px; // 减少顶部间距
    
    &.has-bottom-nav {
      margin-bottom: 50px; // 减少底部间距
    }
  }
}

// 竖屏优化
.portrait-optimized {
  .mobile-main {
    margin-top: 56px;
    
    &.has-bottom-nav {
      margin-bottom: 60px;
    }
  }
}

// 可访问性优化
.accessibility-optimized {
  // 禁用动画
  .slide-left-enter-active,
  .slide-left-leave-active,
  .slide-right-enter-active,
  .slide-right-leave-active,
  .fade-enter-active,
  .fade-leave-active {
    transition: none !important;
  }
  
  // 增强对比度
  * {
    border-width: 2px;
  }
}

// 响应式断点优化
@media (max-width: 480px) {
  .mobile-main {
    margin-top: 52px;
    
    &.has-bottom-nav {
      margin-bottom: 56px;
    }
  }
}

// 横屏小屏幕优化
@media (orientation: landscape) and (max-height: 500px) {
  .mobile-main {
    margin-top: 44px;
    
    &.has-bottom-nav {
      margin-bottom: 48px;
    }
  }
}

// 暗色主题优化
.dark {
  .mobile-layout {
    background-color: var(--el-bg-color-page);
  }
  
  .mobile-page {
    background-color: var(--el-bg-color-page);
  }
}

// 打印优化
@media print {
  .mobile-layout {
    height: auto;
    overflow: visible;
  }
  
  .mobile-main {
    margin: 0;
    overflow: visible;
  }
  
  .mobile-page {
    height: auto;
    overflow: visible;
  }
}
</style>