/**
 * 响应式设计组合式函数
 */
import { ref, onMounted, onUnmounted, computed } from 'vue'

export interface BreakpointConfig {
  xs: number
  sm: number
  md: number
  lg: number
  xl: number
  xxl: number
}

export interface DeviceInfo {
  isMobile: boolean
  isTablet: boolean
  isDesktop: boolean
  isLargeScreen: boolean
  orientation: 'portrait' | 'landscape'
  pixelRatio: number
}

export function useResponsive() {
  const windowWidth = ref(0)
  const windowHeight = ref(0)
  
  // 默认断点配置
  const breakpoints: BreakpointConfig = {
    xs: 480,
    sm: 576,
    md: 768,
    lg: 992,
    xl: 1200,
    xxl: 1600
  }

  // 更新窗口尺寸
  const updateWindowSize = () => {
    windowWidth.value = window.innerWidth
    windowHeight.value = window.innerHeight
  }

  // 设备信息
  const deviceInfo = computed<DeviceInfo>(() => {
    const width = windowWidth.value
    const height = windowHeight.value
    
    return {
      isMobile: width < breakpoints.md,
      isTablet: width >= breakpoints.md && width < breakpoints.lg,
      isDesktop: width >= breakpoints.lg,
      isLargeScreen: width >= breakpoints.xl,
      orientation: width > height ? 'landscape' : 'portrait',
      pixelRatio: window.devicePixelRatio || 1
    }
  })

  // 当前断点
  const currentBreakpoint = computed(() => {
    const width = windowWidth.value
    if (width < breakpoints.xs) return 'xs'
    if (width < breakpoints.sm) return 'sm'
    if (width < breakpoints.md) return 'md'
    if (width < breakpoints.lg) return 'lg'
    if (width < breakpoints.xl) return 'xl'
    return 'xxl'
  })

  // 断点匹配函数
  const isBreakpoint = (breakpoint: keyof BreakpointConfig) => {
    return windowWidth.value >= breakpoints[breakpoint]
  }

  // 断点范围匹配
  const isBetween = (min: keyof BreakpointConfig, max: keyof BreakpointConfig) => {
    const width = windowWidth.value
    return width >= breakpoints[min] && width < breakpoints[max]
  }

  // 获取响应式列数
  const getResponsiveColumns = (config: Partial<Record<keyof BreakpointConfig, number>>) => {
    const width = windowWidth.value
    
    if (width >= breakpoints.xxl && config.xxl) return config.xxl
    if (width >= breakpoints.xl && config.xl) return config.xl
    if (width >= breakpoints.lg && config.lg) return config.lg
    if (width >= breakpoints.md && config.md) return config.md
    if (width >= breakpoints.sm && config.sm) return config.sm
    if (width >= breakpoints.xs && config.xs) return config.xs
    
    return config.xs || 1
  }

  // 获取响应式间距
  const getResponsiveSpacing = (config: Partial<Record<keyof BreakpointConfig, number>>) => {
    return getResponsiveColumns(config)
  }

  // 媒体查询匹配
  const matchMedia = (query: string) => {
    const mediaQuery = ref(false)
    
    if (typeof window !== 'undefined') {
      const mediaQueryList = window.matchMedia(query)
      mediaQuery.value = mediaQueryList.matches
      
      const handler = (e: MediaQueryListEvent) => {
        mediaQuery.value = e.matches
      }
      
      mediaQueryList.addEventListener('change', handler)
      
      onUnmounted(() => {
        mediaQueryList.removeEventListener('change', handler)
      })
    }
    
    return mediaQuery
  }

  // 检测触摸设备
  const isTouchDevice = computed(() => {
    return 'ontouchstart' in window || navigator.maxTouchPoints > 0
  })

  // 检测暗色模式偏好
  const prefersDarkMode = matchMedia('(prefers-color-scheme: dark)')

  // 检测减少动画偏好
  const prefersReducedMotion = matchMedia('(prefers-reduced-motion: reduce)')

  // 检测高对比度偏好
  const prefersHighContrast = matchMedia('(prefers-contrast: high)')

  // 获取安全区域
  const getSafeAreaInsets = () => {
    const style = getComputedStyle(document.documentElement)
    return {
      top: parseInt(style.getPropertyValue('--safe-area-inset-top') || '0'),
      right: parseInt(style.getPropertyValue('--safe-area-inset-right') || '0'),
      bottom: parseInt(style.getPropertyValue('--safe-area-inset-bottom') || '0'),
      left: parseInt(style.getPropertyValue('--safe-area-inset-left') || '0')
    }
  }

  // 响应式字体大小
  const getResponsiveFontSize = (baseSize: number, scaleFactor = 0.1) => {
    const width = windowWidth.value
    const scale = Math.max(0.8, Math.min(1.2, width / 1200))
    return Math.round(baseSize * scale)
  }

  // 响应式容器宽度
  const getContainerWidth = () => {
    const width = windowWidth.value
    if (width >= breakpoints.xxl) return Math.min(width * 0.9, 1400)
    if (width >= breakpoints.xl) return Math.min(width * 0.92, 1200)
    if (width >= breakpoints.lg) return Math.min(width * 0.95, 992)
    if (width >= breakpoints.md) return width * 0.98
    return width - 32 // 移动端留出边距
  }

  // 响应式网格配置
  const getGridConfig = () => {
    const { isMobile, isTablet, isDesktop } = deviceInfo.value
    
    if (isMobile) {
      return {
        columns: 1,
        gap: 16,
        padding: 16
      }
    }
    
    if (isTablet) {
      return {
        columns: 2,
        gap: 20,
        padding: 24
      }
    }
    
    return {
      columns: 3,
      gap: 24,
      padding: 32
    }
  }

  // 响应式表格配置
  const getTableConfig = () => {
    const { isMobile, isTablet } = deviceInfo.value
    
    if (isMobile) {
      return {
        size: 'small',
        showHeader: false,
        cardMode: true,
        maxColumns: 2
      }
    }
    
    if (isTablet) {
      return {
        size: 'default',
        showHeader: true,
        cardMode: false,
        maxColumns: 4
      }
    }
    
    return {
      size: 'default',
      showHeader: true,
      cardMode: false,
      maxColumns: -1 // 无限制
    }
  }

  // 响应式导航配置
  const getNavigationConfig = () => {
    const { isMobile, isTablet } = deviceInfo.value
    
    if (isMobile) {
      return {
        mode: 'bottom-tabs',
        collapsed: true,
        showLabels: false
      }
    }
    
    if (isTablet) {
      return {
        mode: 'drawer',
        collapsed: false,
        showLabels: true
      }
    }
    
    return {
      mode: 'sidebar',
      collapsed: false,
      showLabels: true
    }
  }

  // 防抖的窗口大小更新
  let resizeTimer: NodeJS.Timeout
  const debouncedUpdateWindowSize = () => {
    clearTimeout(resizeTimer)
    resizeTimer = setTimeout(updateWindowSize, 100)
  }

  onMounted(() => {
    updateWindowSize()
    window.addEventListener('resize', debouncedUpdateWindowSize, { passive: true })
    window.addEventListener('orientationchange', updateWindowSize, { passive: true })
  })

  onUnmounted(() => {
    window.removeEventListener('resize', debouncedUpdateWindowSize)
    window.removeEventListener('orientationchange', updateWindowSize)
    clearTimeout(resizeTimer)
  })

  return {
    // 基础响应式数据
    windowWidth,
    windowHeight,
    deviceInfo,
    currentBreakpoint,
    breakpoints,
    
    // 断点匹配函数
    isBreakpoint,
    isBetween,
    
    // 响应式配置获取
    getResponsiveColumns,
    getResponsiveSpacing,
    getResponsiveFontSize,
    getContainerWidth,
    getGridConfig,
    getTableConfig,
    getNavigationConfig,
    
    // 媒体查询
    matchMedia,
    isTouchDevice,
    prefersDarkMode,
    prefersReducedMotion,
    prefersHighContrast,
    
    // 工具函数
    getSafeAreaInsets,
    updateWindowSize
  }
}

// 全局响应式实例
let globalResponsive: ReturnType<typeof useResponsive> | null = null

export function createGlobalResponsive() {
  if (!globalResponsive) {
    globalResponsive = useResponsive()
  }
  return globalResponsive
}

export function useGlobalResponsive() {
  if (!globalResponsive) {
    throw new Error('Global responsive instance not created. Call createGlobalResponsive() first.')
  }
  return globalResponsive
}