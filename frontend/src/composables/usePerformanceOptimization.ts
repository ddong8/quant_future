/**
 * 性能优化组合式函数
 * 提供FPS监控、内存监控、懒加载、虚拟滚动等性能优化功能
 */
import { ref, computed, onMounted, onUnmounted } from 'vue'

// 性能指标接口
export interface PerformanceMetrics {
  fps: number
  memoryUsage: number
  loadTime: number
  renderTime: number
  networkLatency: number
}

// 懒加载配置
export interface LazyLoadOptions {
  root?: Element | null
  rootMargin?: string
  threshold?: number | number[]
  loadingClass?: string
  errorClass?: string
  successClass?: string
}

// 虚拟滚动配置
export interface VirtualScrollOptions {
  itemHeight: number
  containerHeight: number
  buffer?: number
  threshold?: number
}

let globalPerformanceMonitor: ReturnType<typeof createPerformanceMonitor> | null = null

function createPerformanceMonitor() {
  // 性能指标
  const metrics = ref<PerformanceMetrics>({
    fps: 0,
    memoryUsage: 0,
    loadTime: 0,
    renderTime: 0,
    networkLatency: 0
  })

  // 监控状态
  const isMonitoring = ref(false)
  const performanceObserver = ref<PerformanceObserver | null>(null)
  const fpsCounter = ref<number>(0)
  const lastTime = ref<number>(0)
  const frameCount = ref<number>(0)

  // FPS监控
  const measureFPS = () => {
    const now = performance.now()
    frameCount.value++

    if (now - lastTime.value >= 1000) {
      metrics.value.fps = Math.round((frameCount.value * 1000) / (now - lastTime.value))
      frameCount.value = 0
      lastTime.value = now
    }

    if (isMonitoring.value) {
      requestAnimationFrame(measureFPS)
    }
  }

  // 内存使用监控
  const measureMemory = () => {
    if ('memory' in performance) {
      const memory = (performance as any).memory
      metrics.value.memoryUsage = memory.usedJSHeapSize / 1024 / 1024 // MB
    }
  }

  // 网络延迟监控
  const measureNetworkLatency = async () => {
    try {
      const start = performance.now()
      await fetch('/health', { method: 'HEAD' })
      const end = performance.now()
      metrics.value.networkLatency = end - start
    } catch (error) {
      console.warn('Network latency measurement failed:', error)
    }
  }

  // 页面加载时间监控
  const measureLoadTime = () => {
    if ('navigation' in performance) {
      const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming
      if (navigation) {
        metrics.value.loadTime = navigation.loadEventEnd - navigation.loadEventStart
      }
    }
  }

  // 渲染时间监控
  const measureRenderTime = () => {
    if (performanceObserver.value) {
      performanceObserver.value.disconnect()
    }

    performanceObserver.value = new PerformanceObserver((list) => {
      const entries = list.getEntries()
      for (const entry of entries) {
        if (entry.entryType === 'measure') {
          metrics.value.renderTime = entry.duration
        }
      }
    })

    performanceObserver.value.observe({ entryTypes: ['measure'] })
  }

  // 开始监控
  const startMonitoring = () => {
    if (isMonitoring.value) return

    isMonitoring.value = true
    lastTime.value = performance.now()
    
    // 启动FPS监控
    requestAnimationFrame(measureFPS)
    
    // 启动其他监控
    measureLoadTime()
    measureRenderTime()
    
    // 定期更新内存和网络延迟
    const interval = setInterval(() => {
      if (!isMonitoring.value) {
        clearInterval(interval)
        return
      }
      
      measureMemory()
      measureNetworkLatency()
    }, 5000)
  }

  // 停止监控
  const stopMonitoring = () => {
    isMonitoring.value = false
    
    if (performanceObserver.value) {
      performanceObserver.value.disconnect()
      performanceObserver.value = null
    }
  }

  // 性能评分
  const performanceScore = computed(() => {
    const { fps, memoryUsage, loadTime, networkLatency } = metrics.value
    
    let score = 100
    
    // FPS评分 (60fps为满分)
    if (fps < 30) score -= 30
    else if (fps < 45) score -= 15
    else if (fps < 55) score -= 5
    
    // 内存使用评分 (50MB以下为满分)
    if (memoryUsage > 200) score -= 30
    else if (memoryUsage > 100) score -= 15
    else if (memoryUsage > 50) score -= 5
    
    // 加载时间评分 (1秒以下为满分)
    if (loadTime > 5000) score -= 25
    else if (loadTime > 3000) score -= 15
    else if (loadTime > 1000) score -= 5
    
    // 网络延迟评分 (100ms以下为满分)
    if (networkLatency > 1000) score -= 15
    else if (networkLatency > 500) score -= 10
    else if (networkLatency > 100) score -= 5
    
    return Math.max(0, score)
  })

  // 性能等级
  const performanceGrade = computed(() => {
    const score = performanceScore.value
    if (score >= 90) return 'A'
    if (score >= 80) return 'B'
    if (score >= 70) return 'C'
    if (score >= 60) return 'D'
    return 'F'
  })

  return {
    metrics,
    isMonitoring,
    performanceScore,
    performanceGrade,
    startMonitoring,
    stopMonitoring
  }
}

// 懒加载功能
export function useLazyLoad(options: LazyLoadOptions = {}) {
  const {
    root = null,
    rootMargin = '50px',
    threshold = 0.1,
    loadingClass = 'lazy-loading',
    errorClass = 'lazy-error',
    successClass = 'lazy-success'
  } = options

  const observer = ref<IntersectionObserver | null>(null)
  const loadedElements = new Set<Element>()

  const createObserver = () => {
    if (!('IntersectionObserver' in window)) {
      console.warn('IntersectionObserver not supported')
      return null
    }

    return new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting && !loadedElements.has(entry.target)) {
          loadElement(entry.target)
        }
      })
    }, {
      root,
      rootMargin,
      threshold
    })
  }

  const loadElement = async (element: Element) => {
    const img = element as HTMLImageElement
    const src = img.dataset.src

    if (!src) return

    loadedElements.add(element)
    img.classList.add(loadingClass)

    try {
      const image = new Image()
      image.onload = () => {
        img.src = src
        img.classList.remove(loadingClass)
        img.classList.add(successClass)
        observer.value?.unobserve(element)
      }
      image.onerror = () => {
        img.classList.remove(loadingClass)
        img.classList.add(errorClass)
        observer.value?.unobserve(element)
      }
      image.src = src
    } catch (error) {
      img.classList.remove(loadingClass)
      img.classList.add(errorClass)
      observer.value?.unobserve(element)
    }
  }

  const observe = (element: Element) => {
    if (!observer.value) {
      observer.value = createObserver()
    }
    observer.value?.observe(element)
  }

  const unobserve = (element: Element) => {
    observer.value?.unobserve(element)
    loadedElements.delete(element)
  }

  const disconnect = () => {
    observer.value?.disconnect()
    loadedElements.clear()
  }

  return {
    observe,
    unobserve,
    disconnect
  }
}

// 虚拟滚动功能
export function useVirtualScroll(options: VirtualScrollOptions) {
  const {
    itemHeight,
    containerHeight,
    buffer = 5,
    threshold = 0
  } = options

  const scrollTop = ref(0)
  const containerRef = ref<HTMLElement>()

  const visibleRange = computed(() => {
    const start = Math.floor(scrollTop.value / itemHeight)
    const end = Math.ceil((scrollTop.value + containerHeight) / itemHeight)
    
    return {
      start: Math.max(0, start - buffer),
      end: end + buffer
    }
  })

  const handleScroll = (event: Event) => {
    const target = event.target as HTMLElement
    scrollTop.value = target.scrollTop
  }

  const scrollToIndex = (index: number) => {
    if (containerRef.value) {
      containerRef.value.scrollTop = index * itemHeight
    }
  }

  return {
    scrollTop,
    containerRef,
    visibleRange,
    handleScroll,
    scrollToIndex
  }
}

// 防抖函数
export function useDebounce<T extends (...args: any[]) => void>(
  func: T,
  wait: number
): T {
  let timeout: NodeJS.Timeout

  return ((...args: any[]) => {
    clearTimeout(timeout)
    timeout = setTimeout(() => func.apply(null, args), wait)
  }) as T
}

// 节流函数
export function useThrottle<T extends (...args: any[]) => void>(
  func: T,
  limit: number
): T {
  let inThrottle: boolean

  return ((...args: any[]) => {
    if (!inThrottle) {
      func.apply(null, args)
      inThrottle = true
      setTimeout(() => inThrottle = false, limit)
    }
  }) as T
}

// 图片预加载
export function useImagePreload() {
  const preloadedImages = new Map<string, HTMLImageElement>()

  const preloadImage = (src: string): Promise<HTMLImageElement> => {
    if (preloadedImages.has(src)) {
      return Promise.resolve(preloadedImages.get(src)!)
    }

    return new Promise((resolve, reject) => {
      const img = new Image()
      img.onload = () => {
        preloadedImages.set(src, img)
        resolve(img)
      }
      img.onerror = reject
      img.src = src
    })
  }

  const preloadImages = (srcs: string[]): Promise<HTMLImageElement[]> => {
    return Promise.all(srcs.map(preloadImage))
  }

  const clearCache = () => {
    preloadedImages.clear()
  }

  return {
    preloadImage,
    preloadImages,
    clearCache
  }
}

// 全局性能监控实例
export function useGlobalPerformanceMonitor() {
  if (!globalPerformanceMonitor) {
    globalPerformanceMonitor = createPerformanceMonitor()
  }
  return globalPerformanceMonitor
}

// 局部性能监控实例
export function usePerformanceOptimization() {
  const monitor = createPerformanceMonitor()

  onMounted(() => {
    monitor.startMonitoring()
  })

  onUnmounted(() => {
    monitor.stopMonitoring()
  })

  return monitor
}

export default usePerformanceOptimization