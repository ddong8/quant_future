/**
 * 响应式设计组合式函数
 * 提供设备检测、断点监听、移动端优化等功能
 */
import { ref, computed, onMounted, onUnmounted } from 'vue'

// 断点定义
export const breakpoints = {
  xs: 0,
  sm: 576,
  md: 768,
  lg: 992,
  xl: 1200,
  xxl: 1400
} as const

export type Breakpoint = keyof typeof breakpoints

// 设备类型
export interface DeviceInfo {
  isMobile: boolean
  isTablet: boolean
  isDesktop: boolean
  isTouch: boolean
  isRetina: boolean
  orientation: 'portrait' | 'landscape'
  platform: string
  userAgent: string
}

// 响应式状态
export interface ResponsiveState {
  windowWidth: number
  windowHeight: number
  currentBreakpoint: Breakpoint
  deviceInfo: DeviceInfo
  prefersReducedMotion: boolean
  prefersColorScheme: 'light' | 'dark' | 'no-preference'
}

let globalResponsive: ReturnType<typeof createResponsive> | null = null

function createResponsive() {
  // 响应式状态
  const windowWidth = ref(0)
  const windowHeight = ref(0)
  const currentBreakpoint = ref<Breakpoint>('xs')
  const prefersReducedMotion = ref(false)
  const prefersColorScheme = ref<'light' | 'dark' | 'no-preference'>('no-preference')

  // 设备信息
  const deviceInfo = ref<DeviceInfo>({
    isMobile: false,
    isTablet: false,
    isDesktop: true,
    isTouch: false,
    isRetina: false,
    orientation: 'landscape',
    platform: '',
    userAgent: ''
  })

  // 计算当前断点
  const getCurrentBreakpoint = (width: number): Breakpoint => {
    if (width >= breakpoints.xxl) return 'xxl'
    if (width >= breakpoints.xl) return 'xl'
    if (width >= breakpoints.lg) return 'lg'
    if (width >= breakpoints.md) return 'md'
    if (width >= breakpoints.sm) return 'sm'
    return 'xs'
  }

  // 检测设备信息
  const detectDevice = (): DeviceInfo => {
    if (typeof window === 'undefined') {
      return {
        isMobile: false,
        isTablet: false,
        isDesktop: true,
        isTouch: false,
        isRetina: false,
        orientation: 'landscape',
        platform: '',
        userAgent: ''
      }
    }

    const userAgent = navigator.userAgent.toLowerCase()
    const platform = navigator.platform.toLowerCase()
    
    // 检测移动设备
    const isMobile = /android|webos|iphone|ipad|ipod|blackberry|iemobile|opera mini/i.test(userAgent) ||
                     (window.innerWidth <= breakpoints.md && 'ontouchstart' in window)
    
    // 检测平板
    const isTablet = /ipad|android(?!.*mobile)|tablet/i.test(userAgent) ||
                     (window.innerWidth > breakpoints.md && window.innerWidth <= breakpoints.lg && 'ontouchstart' in window)
    
    // 检测桌面
    const isDesktop = !isMobile && !isTablet
    
    // 检测触摸支持
    const isTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0
    
    // 检测高DPI屏幕
    const isRetina = window.devicePixelRatio > 1
    
    // 检测屏幕方向
    const orientation = window.innerHeight > window.innerWidth ? 'portrait' : 'landscape'

    return {
      isMobile,
      isTablet,
      isDesktop,
      isTouch,
      isRetina,
      orientation,
      platform,
      userAgent
    }
  }

  // 检测用户偏好
  const detectPreferences = () => {
    if (typeof window === 'undefined') return

    // 检测动画偏好
    const reducedMotionQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
    prefersReducedMotion.value = reducedMotionQuery.matches

    // 检测颜色主题偏好
    const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)')
    const lightModeQuery = window.matchMedia('(prefers-color-scheme: light)')
    
    if (darkModeQuery.matches) {
      prefersColorScheme.value = 'dark'
    } else if (lightModeQuery.matches) {
      prefersColorScheme.value = 'light'
    } else {
      prefersColorScheme.value = 'no-preference'
    }

    // 监听偏好变化
    reducedMotionQuery.addEventListener('change', (e) => {
      prefersReducedMotion.value = e.matches
    })

    darkModeQuery.addEventListener('change', (e) => {
      if (e.matches) {
        prefersColorScheme.value = 'dark'
      } else if (lightModeQuery.matches) {
        prefersColorScheme.value = 'light'
      } else {
        prefersColorScheme.value = 'no-preference'
      }
    })
  }

  // 更新窗口尺寸
  const updateWindowSize = () => {
    if (typeof window === 'undefined') return

    windowWidth.value = window.innerWidth
    windowHeight.value = window.innerHeight
    currentBreakpoint.value = getCurrentBreakpoint(window.innerWidth)
    deviceInfo.value = detectDevice()
  }

  // 防抖函数
  const debounce = <T extends (...args: any[]) => void>(func: T, wait: number): T => {
    let timeout: NodeJS.Timeout
    return ((...args: any[]) => {
      clearTimeout(timeout)
      timeout = setTimeout(() => func.apply(null, args), wait)
    }) as T
  }

  // 防抖的窗口尺寸更新
  const debouncedUpdateWindowSize = debounce(updateWindowSize, 150)

  // 初始化
  const init = () => {
    if (typeof window === 'undefined') return

    updateWindowSize()
    detectPreferences()

    window.addEventListener('resize', debouncedUpdateWindowSize)
    window.addEventListener('orientationchange', () => {
      // 延迟更新以确保获取正确的尺寸
      setTimeout(updateWindowSize, 100)
    })
  }

  // 清理
  const cleanup = () => {
    if (typeof window === 'undefined') return

    window.removeEventListener('resize', debouncedUpdateWindowSize)
  }

  // 计算属性
  const isMobile = computed(() => deviceInfo.value.isMobile)
  const isTablet = computed(() => deviceInfo.value.isTablet)
  const isDesktop = computed(() => deviceInfo.value.isDesktop)
  const isTouch = computed(() => deviceInfo.value.isTouch)
  const isRetina = computed(() => deviceInfo.value.isRetina)

  // 断点检查函数
  const isBreakpoint = (bp: Breakpoint) => computed(() => currentBreakpoint.value === bp)
  const isBreakpointUp = (bp: Breakpoint) => computed(() => windowWidth.value >= breakpoints[bp])
  const isBreakpointDown = (bp: Breakpoint) => computed(() => windowWidth.value < breakpoints[bp])
  const isBreakpointBetween = (min: Breakpoint, max: Breakpoint) => 
    computed(() => windowWidth.value >= breakpoints[min] && windowWidth.value < breakpoints[max])

  // 响应式类名
  const responsiveClasses = computed(() => {
    const classes: string[] = []
    
    classes.push(`breakpoint-${currentBreakpoint.value}`)
    
    if (deviceInfo.value.isMobile) classes.push('is-mobile')
    if (deviceInfo.value.isTablet) classes.push('is-tablet')
    if (deviceInfo.value.isDesktop) classes.push('is-desktop')
    if (deviceInfo.value.isTouch) classes.push('is-touch')
    if (deviceInfo.value.isRetina) classes.push('is-retina')
    
    classes.push(`orientation-${deviceInfo.value.orientation}`)
    
    if (prefersReducedMotion.value) classes.push('prefers-reduced-motion')
    if (prefersColorScheme.value !== 'no-preference') {
      classes.push(`prefers-${prefersColorScheme.value}`)
    }
    
    return classes
  })

  // 获取优化的图片尺寸
  const getOptimizedImageSize = (baseWidth: number, baseHeight: number) => {
    const ratio = deviceInfo.value.isRetina ? 2 : 1
    const maxWidth = windowWidth.value
    
    let width = Math.min(baseWidth * ratio, maxWidth)
    let height = (width / baseWidth) * baseHeight
    
    return { width: Math.round(width), height: Math.round(height) }
  }

  // 获取适合的字体大小
  const getResponsiveFontSize = (baseSize: number) => {
    const bp = currentBreakpoint.value
    const multipliers = {
      xs: 0.875,
      sm: 0.9375,
      md: 1,
      lg: 1.0625,
      xl: 1.125,
      xxl: 1.1875
    }
    
    return Math.round(baseSize * multipliers[bp])
  }

  // 获取适合的间距
  const getResponsiveSpacing = (baseSpacing: number) => {
    const bp = currentBreakpoint.value
    const multipliers = {
      xs: 0.75,
      sm: 0.875,
      md: 1,
      lg: 1.125,
      xl: 1.25,
      xxl: 1.375
    }
    
    return Math.round(baseSpacing * multipliers[bp])
  }

  return {
    // 状态
    windowWidth,
    windowHeight,
    currentBreakpoint,
    deviceInfo,
    prefersReducedMotion,
    prefersColorScheme,
    
    // 计算属性
    isMobile,
    isTablet,
    isDesktop,
    isTouch,
    isRetina,
    responsiveClasses,
    
    // 方法
    init,
    cleanup,
    isBreakpoint,
    isBreakpointUp,
    isBreakpointDown,
    isBreakpointBetween,
    getOptimizedImageSize,
    getResponsiveFontSize,
    getResponsiveSpacing,
    updateWindowSize
  }
}

// 全局响应式实例
export function useGlobalResponsive() {
  if (!globalResponsive) {
    globalResponsive = createResponsive()
  }
  return globalResponsive
}

// 局部响应式实例
export function useResponsive() {
  const responsive = createResponsive()
  
  onMounted(() => {
    responsive.init()
  })
  
  onUnmounted(() => {
    responsive.cleanup()
  })
  
  return responsive
}

// 响应式工具函数
export const responsiveUtils = {
  // 根据设备类型选择值
  selectByDevice<T>(mobile: T, tablet: T, desktop: T): T {
    const { deviceInfo } = useGlobalResponsive()
    if (deviceInfo.value.isMobile) return mobile
    if (deviceInfo.value.isTablet) return tablet
    return desktop
  },
  
  // 根据断点选择值
  selectByBreakpoint<T>(values: Partial<Record<Breakpoint, T>>, fallback: T): T {
    const { currentBreakpoint } = useGlobalResponsive()
    return values[currentBreakpoint.value] ?? fallback
  },
  
  // 检查是否为移动端
  isMobileDevice(): boolean {
    const { deviceInfo } = useGlobalResponsive()
    return deviceInfo.value.isMobile
  },
  
  // 检查是否支持触摸
  isTouchDevice(): boolean {
    const { deviceInfo } = useGlobalResponsive()
    return deviceInfo.value.isTouch
  },
  
  // 获取当前断点
  getCurrentBreakpoint(): Breakpoint {
    const { currentBreakpoint } = useGlobalResponsive()
    return currentBreakpoint.value
  }
}

export default useResponsive