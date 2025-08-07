<template>
  <div 
    class="responsive-layout"
    :class="[
      ...responsiveClasses,
      {
        'mobile-optimized': isMobile,
        'tablet-optimized': isTablet,
        'desktop-optimized': isDesktop,
        'touch-optimized': isTouch,
        'high-dpi-optimized': isRetina,
        'landscape-optimized': deviceInfo.orientation === 'landscape',
        'portrait-optimized': deviceInfo.orientation === 'portrait',
        'accessibility-optimized': prefersReducedMotion
      }
    ]"
  >
    <!-- 移动端顶部导航栏 -->
    <div v-if="isMobile" class="mobile-header">
      <div class="mobile-header-content">
        <el-button
          v-if="showMenuButton"
          type="text"
          class="mobile-menu-button"
          @click="toggleMobileMenu"
        >
          <el-icon><Menu /></el-icon>
        </el-button>
        
        <div class="mobile-title">
          <slot name="mobile-title">{{ title }}</slot>
        </div>
        
        <div class="mobile-actions">
          <slot name="mobile-actions"></slot>
        </div>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="layout-main" :class="{ 'has-mobile-header': isMobile && showMobileHeader }">
      <!-- 侧边栏 -->
      <div 
        v-if="showSidebar"
        class="layout-sidebar"
        :class="{
          'sidebar-collapsed': sidebarCollapsed,
          'sidebar-mobile': isMobile,
          'sidebar-overlay': isMobile && mobileMenuVisible
        }"
      >
        <!-- 移动端遮罩 -->
        <div 
          v-if="isMobile && mobileMenuVisible"
          class="sidebar-overlay-mask"
          @click="closeMobileMenu"
        ></div>
        
        <div class="sidebar-content">
          <slot name="sidebar"></slot>
        </div>
      </div>

      <!-- 内容区域 -->
      <div 
        class="layout-content"
        :class="{
          'content-full': !showSidebar,
          'content-with-sidebar': showSidebar && !sidebarCollapsed,
          'content-with-collapsed-sidebar': showSidebar && sidebarCollapsed
        }"
      >
        <!-- 桌面端头部 -->
        <div v-if="!isMobile && showHeader" class="desktop-header">
          <slot name="header"></slot>
        </div>

        <!-- 主要内容 -->
        <div class="content-main">
          <slot></slot>
        </div>

        <!-- 底部 -->
        <div v-if="showFooter" class="layout-footer">
          <slot name="footer"></slot>
        </div>
      </div>
    </div>

    <!-- 移动端底部导航 -->
    <div v-if="isMobile && showBottomNav" class="mobile-bottom-nav">
      <slot name="bottom-nav"></slot>
    </div>

    <!-- 回到顶部按钮 -->
    <el-backtop
      v-if="showBackTop"
      :right="backTopPosition.right"
      :bottom="backTopPosition.bottom"
      :visibility-height="200"
    />

    <!-- 性能监控 -->
    <div v-if="showPerformanceMonitor && isDevelopment" class="performance-monitor">
      <div class="performance-item">
        <span>FPS: {{ performanceMetrics.fps }}</span>
      </div>
      <div class="performance-item">
        <span>Memory: {{ Math.round(performanceMetrics.memoryUsage) }}MB</span>
      </div>
      <div class="performance-item">
        <span>{{ currentBreakpoint.toUpperCase() }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { Menu } from '@element-plus/icons-vue'
import { useResponsive } from '@/composables/useResponsive'
import { usePerformanceOptimization } from '@/composables/usePerformanceOptimization'

interface Props {
  title?: string
  showSidebar?: boolean
  showHeader?: boolean
  showFooter?: boolean
  showMobileHeader?: boolean
  showBottomNav?: boolean
  showMenuButton?: boolean
  showBackTop?: boolean
  showPerformanceMonitor?: boolean
  sidebarCollapsed?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  title: '量化交易平台',
  showSidebar: true,
  showHeader: true,
  showFooter: false,
  showMobileHeader: true,
  showBottomNav: false,
  showMenuButton: true,
  showBackTop: true,
  showPerformanceMonitor: false,
  sidebarCollapsed: false
})

const emit = defineEmits<{
  'toggle-sidebar': []
  'mobile-menu-toggle': [visible: boolean]
}>()

// 响应式功能
const {
  windowWidth,
  windowHeight,
  currentBreakpoint,
  deviceInfo,
  isMobile,
  isTablet,
  isDesktop,
  isTouch,
  isRetina,
  prefersReducedMotion,
  responsiveClasses
} = useResponsive()

// 性能监控
const { metrics: performanceMetrics } = usePerformanceOptimization()

// 移动端菜单状态
const mobileMenuVisible = ref(false)

// 开发环境检测
const isDevelopment = computed(() => process.env.NODE_ENV === 'development')

// 回到顶部按钮位置
const backTopPosition = computed(() => {
  if (isMobile.value) {
    return {
      right: 20,
      bottom: props.showBottomNav ? 80 : 20
    }
  }
  return {
    right: 40,
    bottom: 40
  }
})

// 切换移动端菜单
const toggleMobileMenu = () => {
  mobileMenuVisible.value = !mobileMenuVisible.value
  emit('mobile-menu-toggle', mobileMenuVisible.value)
}

// 关闭移动端菜单
const closeMobileMenu = () => {
  mobileMenuVisible.value = false
  emit('mobile-menu-toggle', false)
}

// 监听窗口大小变化，自动关闭移动端菜单
watch([windowWidth, isMobile], ([newWidth, newIsMobile]) => {
  if (!newIsMobile && mobileMenuVisible.value) {
    closeMobileMenu()
  }
})

// 监听路由变化，关闭移动端菜单
watch(() => window.location.pathname, () => {
  if (mobileMenuVisible.value) {
    closeMobileMenu()
  }
})

// 处理键盘事件
const handleKeydown = (event: KeyboardEvent) => {
  // ESC键关闭移动端菜单
  if (event.key === 'Escape' && mobileMenuVisible.value) {
    closeMobileMenu()
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
  
  // 设置CSS自定义属性
  document.documentElement.style.setProperty('--window-width', `${windowWidth.value}px`)
  document.documentElement.style.setProperty('--window-height', `${windowHeight.value}px`)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})

// 监听窗口尺寸变化，更新CSS变量
watch([windowWidth, windowHeight], ([width, height]) => {
  document.documentElement.style.setProperty('--window-width', `${width}px`)
  document.documentElement.style.setProperty('--window-height', `${height}px`)
})
</script>

<style lang="scss" scoped>
.responsive-layout {
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

// 移动端头部
.mobile-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 56px;
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color-lighter);
  z-index: 1000;
  
  .mobile-header-content {
    display: flex;
    align-items: center;
    height: 100%;
    padding: 0 16px;
  }
  
  .mobile-menu-button {
    margin-right: 12px;
    font-size: 20px;
  }
  
  .mobile-title {
    flex: 1;
    font-size: 18px;
    font-weight: 600;
    color: var(--el-text-color-primary);
  }
  
  .mobile-actions {
    display: flex;
    align-items: center;
    gap: 8px;
  }
}

// 主要布局
.layout-main {
  display: flex;
  flex: 1;
  overflow: hidden;
  
  &.has-mobile-header {
    margin-top: 56px;
  }
}

// 侧边栏
.layout-sidebar {
  position: relative;
  width: 240px;
  background: var(--el-bg-color);
  border-right: 1px solid var(--el-border-color-lighter);
  transition: width 0.3s ease;
  
  &.sidebar-collapsed {
    width: 64px;
  }
  
  &.sidebar-mobile {
    position: fixed;
    top: 56px;
    left: 0;
    bottom: 0;
    width: 280px;
    z-index: 1001;
    transform: translateX(-100%);
    transition: transform 0.3s ease;
    
    &.sidebar-overlay {
      transform: translateX(0);
    }
  }
  
  .sidebar-content {
    height: 100%;
    overflow-y: auto;
    overflow-x: hidden;
    
    // 优化滚动性能
    -webkit-overflow-scrolling: touch;
    scrollbar-width: thin;
  }
}

.sidebar-overlay-mask {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: -1;
}

// 内容区域
.layout-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  
  &.content-full {
    width: 100%;
  }
  
  &.content-with-sidebar {
    width: calc(100% - 240px);
  }
  
  &.content-with-collapsed-sidebar {
    width: calc(100% - 64px);
  }
}

// 桌面端头部
.desktop-header {
  height: 60px;
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color-lighter);
  display: flex;
  align-items: center;
  padding: 0 24px;
}

// 主要内容
.content-main {
  flex: 1;
  overflow: auto;
  
  // 优化滚动性能
  -webkit-overflow-scrolling: touch;
  scroll-behavior: smooth;
}

// 底部
.layout-footer {
  height: 60px;
  background: var(--el-bg-color);
  border-top: 1px solid var(--el-border-color-lighter);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 24px;
}

// 移动端底部导航
.mobile-bottom-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 60px;
  background: var(--el-bg-color);
  border-top: 1px solid var(--el-border-color-lighter);
  z-index: 1000;
}

// 性能监控
.performance-monitor {
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
  
  .performance-item {
    margin-bottom: 4px;
    
    &:last-child {
      margin-bottom: 0;
    }
  }
}

// 移动端优化
.mobile-optimized {
  .layout-sidebar {
    .sidebar-content {
      padding: 8px;
    }
  }
  
  .content-main {
    padding: 12px;
  }
  
  .desktop-header {
    height: 50px;
    padding: 0 16px;
  }
}

// 平板优化
.tablet-optimized {
  .layout-sidebar {
    width: 200px;
    
    &.sidebar-collapsed {
      width: 60px;
    }
  }
  
  .content-with-sidebar {
    width: calc(100% - 200px);
  }
  
  .content-with-collapsed-sidebar {
    width: calc(100% - 60px);
  }
}

// 触摸优化
.touch-optimized {
  .mobile-menu-button {
    min-height: 44px;
    min-width: 44px;
  }
  
  .mobile-actions :deep(.el-button) {
    min-height: 44px;
  }
}

// 高DPI优化
.high-dpi-optimized {
  .mobile-header,
  .layout-sidebar,
  .desktop-header {
    border-width: 0.5px;
  }
}

// 横屏优化
.landscape-optimized {
  &.mobile-optimized {
    .mobile-header {
      height: 48px;
    }
    
    .layout-main.has-mobile-header {
      margin-top: 48px;
    }
    
    .content-main {
      padding: 8px 12px;
    }
  }
}

// 竖屏优化
.portrait-optimized {
  &.mobile-optimized {
    .mobile-header {
      height: 56px;
    }
    
    .content-main {
      padding: 16px;
    }
  }
}

// 可访问性优化
.accessibility-optimized {
  * {
    transition-duration: 0.01ms !important;
  }
  
  .sidebar-mobile {
    transition: none;
  }
}

// 响应式断点样式
@media (max-width: 767px) {
  .layout-content {
    &.content-with-sidebar,
    &.content-with-collapsed-sidebar {
      width: 100%;
    }
  }
}

@media (max-width: 480px) {
  .mobile-header {
    .mobile-header-content {
      padding: 0 12px;
    }
    
    .mobile-title {
      font-size: 16px;
    }
  }
  
  .content-main {
    padding: 8px;
  }
}

// 打印样式
@media print {
  .mobile-header,
  .layout-sidebar,
  .mobile-bottom-nav,
  .performance-monitor {
    display: none !important;
  }
  
  .layout-content {
    width: 100% !important;
  }
}
</style>