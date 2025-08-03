<template>
  <div id="app" :class="appClasses">
    <ErrorBoundary>
      <router-view />
    </ErrorBoundary>
    
    <!-- 全局加载组件 -->
    <GlobalLoading />
    
    <!-- 性能监控指示器 (仅开发环境) -->
    <div 
      v-if="showPerformanceIndicator" 
      class="performance-indicator"
      :class="performanceStatus"
    >
      FPS: {{ performanceMetrics.fps }} | 
      Memory: {{ Math.round(performanceMetrics.memoryUsage) }}MB
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'
import { useGlobalResponsive } from '@/composables/useResponsive'
import { usePerformanceOptimization } from '@/composables/usePerformanceOptimization'
import ErrorBoundary from '@/components/common/ErrorBoundary.vue'
import GlobalLoading from '@/components/common/GlobalLoading.vue'

const authStore = useAuthStore()
const themeStore = useThemeStore()
const responsive = useGlobalResponsive()
const { metrics: performanceMetrics } = usePerformanceOptimization()

// 应用样式类
const appClasses = computed(() => {
  const classes = []
  
  if (responsive.deviceInfo.value.isMobile) {
    classes.push('mobile-optimized')
  }
  
  if (responsive.windowWidth.value < 480) {
    classes.push('low-end-optimized')
  }
  
  if (responsive.prefersReducedMotion.value) {
    classes.push('reduce-motion')
  }
  
  return classes
})

// 性能指示器
const showPerformanceIndicator = computed(() => {
  return process.env.NODE_ENV === 'development' && performanceMetrics.value.fps > 0
})

const performanceStatus = computed(() => {
  const fps = performanceMetrics.value.fps
  const memory = performanceMetrics.value.memoryUsage
  
  if (fps < 30 || memory > 100) return 'error'
  if (fps < 45 || memory > 50) return 'warning'
  return 'good'
})

onMounted(() => {
  // 初始化主题
  themeStore.initTheme()
  
  // 添加性能监控类
  if (process.env.NODE_ENV === 'development') {
    document.documentElement.classList.add('debug-performance')
  }
})
</script>

<style lang="scss">
#app {
  height: 100vh;
  width: 100vw;
  /* 启用硬件加速 */
  transform: translateZ(0);
  /* 优化渲染性能 */
  contain: layout style paint;
}

/* 性能指示器样式 */
.performance-indicator {
  position: fixed;
  top: 10px;
  right: 10px;
  z-index: 9999;
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 8px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-family: monospace;
  pointer-events: none;
  transition: opacity 0.3s ease;
  
  &.good {
    background: rgba(0, 128, 0, 0.8);
  }
  
  &.warning {
    background: rgba(255, 165, 0, 0.8);
  }
  
  &.error {
    background: rgba(255, 0, 0, 0.8);
  }
}

/* 移动端优化 */
.mobile-optimized {
  /* 减少复杂样式以提高性能 */
  .el-card,
  .el-dialog,
  .el-drawer {
    box-shadow: none;
    border-radius: 4px;
  }
  
  /* 简化动画 */
  * {
    transition-duration: 0.2s !important;
  }
}

/* 低端设备优化 */
.low-end-optimized {
  /* 禁用复杂动画和效果 */
  * {
    animation: none !important;
    transition: none !important;
    box-shadow: none !important;
    background-image: none !important;
  }
}

/* 减少动画偏好 */
.reduce-motion {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
</style>