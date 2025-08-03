import { ref, onMounted, onUnmounted } from 'vue'

interface PerformanceMetrics {
  loadTime: number
  domContentLoaded: number
  firstPaint: number
  firstContentfulPaint: number
  memoryUsage?: number
  jsHeapSize?: number
}

interface OptimizationConfig {
  enableLazyLoading: boolean
  enableImageOptimization: boolean
  enableCodeSplitting: boolean
  enableCaching: boolean
  maxCacheSize: number
}

export function usePerformanceOptimization() {
  const metrics = ref<PerformanceMetrics>({
    loadTime: 0,
    domContentLoaded: 0,
    firstPaint: 0,
    firstContentfulPaint: 0
  })

  const config = ref<OptimizationConfig>({
    enableLazyLoading: true,
    enableImageOptimization: true,
    enableCodeSplitting: true,
    enableCaching: true,
    maxCacheSize: 50 * 1024 * 1024 // 50MB
  })

  const isOptimizing = ref(false)

  // 收集性能指标
  const collectMetrics = () => {
    if ('performance' in window) {
      const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming
      if (navigation) {
        metrics.value = {
          loadTime: navigation.loadEventEnd - navigation.loadEventStart,
          domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
          firstPaint: performance.getEntriesByName('first-paint')[0]?.startTime || 0,
          firstContentfulPaint: performance.getEntriesByName('first-contentful-paint')[0]?.startTime || 0
        }

        // 内存使用情况
        if ('memory' in performance) {
          const memory = (performance as any).memory
          metrics.value.memoryUsage = memory.usedJSHeapSize
          metrics.value.jsHeapSize = memory.totalJSHeapSize
        }
      }
    }
  }

  // 优化图片加载
  const optimizeImages = () => {
    if (!config.value.enableImageOptimization) return

    const images = document.querySelectorAll('img[data-src]')
    const imageObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const img = entry.target as HTMLImageElement
          const src = img.getAttribute('data-src')
          if (src) {
            img.src = src
            img.removeAttribute('data-src')
            imageObserver.unobserve(img)
          }
        }
      })
    })

    images.forEach(img => imageObserver.observe(img))
  }

  // 预加载关键资源
  const preloadCriticalResources = (resources: string[]) => {
    resources.forEach(resource => {
      const link = document.createElement('link')
      link.rel = 'prefetch'
      link.href = resource
      document.head.appendChild(link)
    })
  }

  // 清理缓存
  const clearCache = async () => {
    if ('caches' in window) {
      const cacheNames = await caches.keys()
      await Promise.all(
        cacheNames.map(cacheName => caches.delete(cacheName))
      )
    }
    
    // 清理 localStorage
    const storageSize = JSON.stringify(localStorage).length
    if (storageSize > config.value.maxCacheSize) {
      const keys = Object.keys(localStorage)
      // 保留重要的键，清理其他的
      const importantKeys = ['auth-token', 'user-settings', 'theme']
      keys.forEach(key => {
        if (!importantKeys.includes(key)) {
          localStorage.removeItem(key)
        }
      })
    }
  }

  // 自动优化
  const autoOptimize = async () => {
    if (isOptimizing.value) return
    
    isOptimizing.value = true
    
    try {
      // 收集性能指标
      collectMetrics()
      
      // 优化图片
      optimizeImages()
      
      // 清理缓存（如果需要）
      await clearCache()
      
      console.log('Performance optimization completed', metrics.value)
    } catch (error) {
      console.error('Performance optimization failed:', error)
    } finally {
      isOptimizing.value = false
    }
  }

  // 监控性能
  const startPerformanceMonitoring = () => {
    // 监控长任务
    if ('PerformanceObserver' in window) {
      const observer = new PerformanceObserver((list) => {
        const entries = list.getEntries()
        entries.forEach(entry => {
          if (entry.duration > 50) { // 长任务阈值 50ms
            console.warn('Long task detected:', entry.name, entry.duration)
          }
        })
      })
      
      try {
        observer.observe({ entryTypes: ['longtask'] })
      } catch (e) {
        // longtask 可能不被支持
        console.log('Long task monitoring not supported')
      }
    }
  }

  // 获取性能建议
  const getPerformanceRecommendations = () => {
    const recommendations: string[] = []
    
    if (metrics.value.loadTime > 3000) {
      recommendations.push('页面加载时间过长，建议优化资源加载')
    }
    
    if (metrics.value.firstContentfulPaint > 2500) {
      recommendations.push('首次内容绘制时间过长，建议优化关键渲染路径')
    }
    
    if (metrics.value.memoryUsage && metrics.value.memoryUsage > 50 * 1024 * 1024) {
      recommendations.push('内存使用过高，建议检查内存泄漏')
    }
    
    return recommendations
  }

  onMounted(() => {
    // 延迟执行，避免影响初始加载
    setTimeout(() => {
      collectMetrics()
      startPerformanceMonitoring()
    }, 1000)
  })

  return {
    metrics,
    config,
    isOptimizing,
    collectMetrics,
    optimizeImages,
    preloadCriticalResources,
    clearCache,
    autoOptimize,
    startPerformanceMonitoring,
    getPerformanceRecommendations
  }
}