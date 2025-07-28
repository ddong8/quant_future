/**
 * 前端性能优化工具
 */

// 防抖函数
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number,
  immediate = false
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null
  
  return function executedFunction(...args: Parameters<T>) {
    const later = () => {
      timeout = null
      if (!immediate) func(...args)
    }
    
    const callNow = immediate && !timeout
    
    if (timeout) clearTimeout(timeout)
    timeout = setTimeout(later, wait)
    
    if (callNow) func(...args)
  }
}

// 节流函数
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle: boolean
  
  return function executedFunction(...args: Parameters<T>) {
    if (!inThrottle) {
      func(...args)
      inThrottle = true
      setTimeout(() => inThrottle = false, limit)
    }
  }
}

// 延迟执行
export function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

// 空闲时执行
export function runOnIdle(callback: () => void, timeout = 5000): void {
  if ('requestIdleCallback' in window) {
    requestIdleCallback(callback, { timeout })
  } else {
    setTimeout(callback, 1)
  }
}

// 图片懒加载
export class LazyImageLoader {
  private observer: IntersectionObserver | null = null
  private images = new Set<HTMLImageElement>()
  
  constructor() {
    this.init()
  }
  
  private init(): void {
    if ('IntersectionObserver' in window) {
      this.observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              const img = entry.target as HTMLImageElement
              this.loadImage(img)
              this.observer?.unobserve(img)
              this.images.delete(img)
            }
          })
        },
        {
          rootMargin: '50px 0px',
          threshold: 0.01
        }
      )
    }
  }
  
  observe(img: HTMLImageElement): void {
    if (this.observer) {
      this.observer.observe(img)
      this.images.add(img)
    } else {
      // 降级方案：直接加载
      this.loadImage(img)
    }
  }
  
  private loadImage(img: HTMLImageElement): void {
    const src = img.dataset.src
    if (src) {
      img.src = src
      img.removeAttribute('data-src')
      img.classList.add('loaded')
    }
  }
  
  disconnect(): void {
    if (this.observer) {
      this.observer.disconnect()
      this.images.clear()
    }
  }
}

// 虚拟滚动
export class VirtualScroller {
  private container: HTMLElement
  private items: any[]
  private itemHeight: number
  private visibleCount: number
  private startIndex = 0
  private endIndex = 0
  
  constructor(
    container: HTMLElement,
    items: any[],
    itemHeight: number,
    visibleCount: number
  ) {
    this.container = container
    this.items = items
    this.itemHeight = itemHeight
    this.visibleCount = visibleCount
    
    this.init()
  }
  
  private init(): void {
    this.container.style.height = `${this.items.length * this.itemHeight}px`
    this.container.addEventListener('scroll', this.onScroll.bind(this))
    this.updateVisibleItems()
  }
  
  private onScroll(): void {
    const scrollTop = this.container.scrollTop
    this.startIndex = Math.floor(scrollTop / this.itemHeight)
    this.endIndex = Math.min(
      this.startIndex + this.visibleCount,
      this.items.length
    )
    
    this.updateVisibleItems()
  }
  
  private updateVisibleItems(): void {
    // 这里应该更新DOM，显示可见的项目
    // 具体实现取决于使用的框架
  }
  
  getVisibleItems(): any[] {
    return this.items.slice(this.startIndex, this.endIndex)
  }
  
  getStartIndex(): number {
    return this.startIndex
  }
  
  getEndIndex(): number {
    return this.endIndex
  }
}

// 内存管理
export class MemoryManager {
  private cache = new Map<string, any>()
  private maxSize: number
  private currentSize = 0
  
  constructor(maxSize = 100) {
    this.maxSize = maxSize
  }
  
  set(key: string, value: any): void {
    if (this.cache.has(key)) {
      this.cache.delete(key)
    } else if (this.currentSize >= this.maxSize) {
      // 删除最旧的项目
      const firstKey = this.cache.keys().next().value
      this.cache.delete(firstKey)
      this.currentSize--
    }
    
    this.cache.set(key, value)
    this.currentSize++
  }
  
  get(key: string): any {
    const value = this.cache.get(key)
    if (value !== undefined) {
      // 移到最后（LRU策略）
      this.cache.delete(key)
      this.cache.set(key, value)
    }
    return value
  }
  
  has(key: string): boolean {
    return this.cache.has(key)
  }
  
  delete(key: string): boolean {
    const deleted = this.cache.delete(key)
    if (deleted) {
      this.currentSize--
    }
    return deleted
  }
  
  clear(): void {
    this.cache.clear()
    this.currentSize = 0
  }
  
  size(): number {
    return this.currentSize
  }
}

// 性能监控
export class PerformanceMonitor {
  private metrics = new Map<string, number[]>()
  
  // 标记性能开始
  mark(name: string): void {
    performance.mark(`${name}-start`)
  }
  
  // 测量性能
  measure(name: string): number {
    performance.mark(`${name}-end`)
    performance.measure(name, `${name}-start`, `${name}-end`)
    
    const entries = performance.getEntriesByName(name, 'measure')
    const duration = entries[entries.length - 1]?.duration || 0
    
    // 记录指标
    if (!this.metrics.has(name)) {
      this.metrics.set(name, [])
    }
    this.metrics.get(name)!.push(duration)
    
    // 清理性能条目
    performance.clearMarks(`${name}-start`)
    performance.clearMarks(`${name}-end`)
    performance.clearMeasures(name)
    
    return duration
  }
  
  // 获取平均性能
  getAverage(name: string): number {
    const values = this.metrics.get(name) || []
    if (values.length === 0) return 0
    
    const sum = values.reduce((a, b) => a + b, 0)
    return sum / values.length
  }
  
  // 获取所有指标
  getAllMetrics(): Record<string, { average: number, count: number, latest: number }> {
    const result: Record<string, any> = {}
    
    this.metrics.forEach((values, name) => {
      result[name] = {
        average: this.getAverage(name),
        count: values.length,
        latest: values[values.length - 1] || 0
      }
    })
    
    return result
  }
  
  // 清理旧指标
  cleanup(maxAge = 1000): void {
    this.metrics.forEach((values, name) => {
      if (values.length > maxAge) {
        this.metrics.set(name, values.slice(-maxAge))
      }
    })
  }
}

// 资源预加载
export class ResourcePreloader {
  private preloadedResources = new Set<string>()
  
  // 预加载图片
  preloadImage(src: string): Promise<void> {
    if (this.preloadedResources.has(src)) {
      return Promise.resolve()
    }
    
    return new Promise((resolve, reject) => {
      const img = new Image()
      img.onload = () => {
        this.preloadedResources.add(src)
        resolve()
      }
      img.onerror = reject
      img.src = src
    })
  }
  
  // 预加载多个图片
  async preloadImages(srcs: string[]): Promise<void> {
    const promises = srcs.map(src => this.preloadImage(src))
    await Promise.allSettled(promises)
  }
  
  // 预加载脚本
  preloadScript(src: string): Promise<void> {
    if (this.preloadedResources.has(src)) {
      return Promise.resolve()
    }
    
    return new Promise((resolve, reject) => {
      const link = document.createElement('link')
      link.rel = 'preload'
      link.as = 'script'
      link.href = src
      link.onload = () => {
        this.preloadedResources.add(src)
        resolve()
      }
      link.onerror = reject
      document.head.appendChild(link)
    })
  }
  
  // 预加载样式
  preloadStyle(href: string): Promise<void> {
    if (this.preloadedResources.has(href)) {
      return Promise.resolve()
    }
    
    return new Promise((resolve, reject) => {
      const link = document.createElement('link')
      link.rel = 'preload'
      link.as = 'style'
      link.href = href
      link.onload = () => {
        this.preloadedResources.add(href)
        resolve()
      }
      link.onerror = reject
      document.head.appendChild(link)
    })
  }
}

// 批处理器
export class BatchProcessor<T> {
  private queue: T[] = []
  private batchSize: number
  private delay: number
  private processor: (items: T[]) => void
  private timeoutId: NodeJS.Timeout | null = null
  
  constructor(
    processor: (items: T[]) => void,
    batchSize = 10,
    delay = 100
  ) {
    this.processor = processor
    this.batchSize = batchSize
    this.delay = delay
  }
  
  add(item: T): void {
    this.queue.push(item)
    
    if (this.queue.length >= this.batchSize) {
      this.flush()
    } else if (!this.timeoutId) {
      this.timeoutId = setTimeout(() => this.flush(), this.delay)
    }
  }
  
  flush(): void {
    if (this.queue.length === 0) return
    
    const items = this.queue.splice(0, this.batchSize)
    this.processor(items)
    
    if (this.timeoutId) {
      clearTimeout(this.timeoutId)
      this.timeoutId = null
    }
    
    // 如果还有剩余项目，继续处理
    if (this.queue.length > 0) {
      this.timeoutId = setTimeout(() => this.flush(), this.delay)
    }
  }
  
  clear(): void {
    this.queue = []
    if (this.timeoutId) {
      clearTimeout(this.timeoutId)
      this.timeoutId = null
    }
  }
}

// 全局实例
export const lazyImageLoader = new LazyImageLoader()
export const memoryManager = new MemoryManager()
export const performanceMonitor = new PerformanceMonitor()
export const resourcePreloader = new ResourcePreloader()

// 性能优化装饰器
export function measurePerformance(name: string) {
  return function (target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    const originalMethod = descriptor.value
    
    descriptor.value = function (...args: any[]) {
      performanceMonitor.mark(name)
      const result = originalMethod.apply(this, args)
      
      if (result instanceof Promise) {
        return result.finally(() => {
          performanceMonitor.measure(name)
        })
      } else {
        performanceMonitor.measure(name)
        return result
      }
    }
    
    return descriptor
  }
}

// 缓存装饰器
export function cached(ttl = 5000) {
  return function (target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    const originalMethod = descriptor.value
    const cache = new Map<string, { value: any, expiry: number }>()
    
    descriptor.value = function (...args: any[]) {
      const key = JSON.stringify(args)
      const now = Date.now()
      const cached = cache.get(key)
      
      if (cached && cached.expiry > now) {
        return cached.value
      }
      
      const result = originalMethod.apply(this, args)
      cache.set(key, { value: result, expiry: now + ttl })
      
      return result
    }
    
    return descriptor
  }
}