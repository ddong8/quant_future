/**
 * CDN配置和资源管理
 */

// CDN配置
export interface CDNConfig {
  baseUrl: string
  domains: string[]
  enableSharding: boolean
  enableCompression: boolean
  enableWebP: boolean
  fallbackUrl?: string
}

// 默认CDN配置
const defaultCDNConfig: CDNConfig = {
  baseUrl: process.env.VITE_CDN_BASE_URL || '',
  domains: [
    'cdn1.example.com',
    'cdn2.example.com',
    'cdn3.example.com'
  ],
  enableSharding: true,
  enableCompression: true,
  enableWebP: true,
  fallbackUrl: '/assets'
}

// CDN管理器
export class CDNManager {
  private config: CDNConfig
  private domainIndex = 0
  private webpSupported: boolean | null = null
  
  constructor(config: CDNConfig = defaultCDNConfig) {
    this.config = config
    this.detectWebPSupport()
  }
  
  // 检测WebP支持
  private async detectWebPSupport(): Promise<void> {
    if (this.webpSupported !== null) return
    
    try {
      const webpData = 'data:image/webp;base64,UklGRjoAAABXRUJQVlA4IC4AAACyAgCdASoCAAIALmk0mk0iIiIiIgBoSygABc6WWgAA/veff/0PP8bA//LwYAAA'
      const img = new Image()
      
      this.webpSupported = await new Promise((resolve) => {
        img.onload = () => resolve(img.width === 2 && img.height === 2)
        img.onerror = () => resolve(false)
        img.src = webpData
      })
    } catch {
      this.webpSupported = false
    }
  }
  
  // 获取下一个CDN域名
  private getNextDomain(): string {
    if (!this.config.enableSharding || this.config.domains.length === 0) {
      return this.config.baseUrl
    }
    
    const domain = this.config.domains[this.domainIndex]
    this.domainIndex = (this.domainIndex + 1) % this.config.domains.length
    
    return `https://${domain}`
  }
  
  // 生成资源URL
  getResourceUrl(path: string, options: {
    width?: number
    height?: number
    quality?: number
    format?: 'webp' | 'jpg' | 'png'
    enableWebP?: boolean
  } = {}): string {
    let url = path
    
    // 如果是相对路径，添加CDN域名
    if (!path.startsWith('http') && !path.startsWith('//')) {
      const baseUrl = this.config.baseUrl || this.getNextDomain()
      url = `${baseUrl}${path.startsWith('/') ? '' : '/'}${path}`
    }
    
    // 图片优化参数
    const params = new URLSearchParams()
    
    if (options.width) {
      params.append('w', options.width.toString())
    }
    
    if (options.height) {
      params.append('h', options.height.toString())
    }
    
    if (options.quality && options.quality !== 100) {
      params.append('q', options.quality.toString())
    }
    
    // WebP格式支持
    if (this.config.enableWebP && 
        (options.enableWebP !== false) && 
        this.webpSupported && 
        !options.format) {
      params.append('f', 'webp')
    } else if (options.format) {
      params.append('f', options.format)
    }
    
    // 压缩支持
    if (this.config.enableCompression) {
      params.append('compress', '1')
    }
    
    // 添加参数到URL
    if (params.toString()) {
      const separator = url.includes('?') ? '&' : '?'
      url += separator + params.toString()
    }
    
    return url
  }
  
  // 预加载资源
  preloadResource(url: string, type: 'image' | 'script' | 'style' = 'image'): Promise<void> {
    return new Promise((resolve, reject) => {
      const link = document.createElement('link')
      link.rel = 'preload'
      link.as = type
      link.href = url
      
      link.onload = () => resolve()
      link.onerror = () => reject(new Error(`Failed to preload ${url}`))
      
      document.head.appendChild(link)
    })
  }
  
  // 批量预加载资源
  async preloadResources(urls: string[], type: 'image' | 'script' | 'style' = 'image'): Promise<void> {
    const promises = urls.map(url => this.preloadResource(url, type))
    await Promise.allSettled(promises)
  }
  
  // 获取响应式图片URL
  getResponsiveImageUrls(path: string, sizes: number[] = [320, 640, 1024, 1920]): {
    srcset: string
    sizes: string
  } {
    const srcset = sizes.map(size => {
      const url = this.getResourceUrl(path, { width: size })
      return `${url} ${size}w`
    }).join(', ')
    
    const sizesAttr = sizes.map((size, index) => {
      if (index === sizes.length - 1) {
        return `${size}px`
      }
      return `(max-width: ${size}px) ${size}px`
    }).join(', ')
    
    return { srcset, sizes: sizesAttr }
  }
  
  // 获取配置
  getConfig(): CDNConfig {
    return { ...this.config }
  }
  
  // 更新配置
  updateConfig(newConfig: Partial<CDNConfig>): void {
    this.config = { ...this.config, ...newConfig }
  }
}

// 资源压缩工具
export class ResourceCompressor {
  // 压缩图片
  static compressImage(
    file: File,
    options: {
      maxWidth?: number
      maxHeight?: number
      quality?: number
      format?: 'jpeg' | 'png' | 'webp'
    } = {}
  ): Promise<Blob> {
    return new Promise((resolve, reject) => {
      const canvas = document.createElement('canvas')
      const ctx = canvas.getContext('2d')
      const img = new Image()
      
      img.onload = () => {
        const { maxWidth = 1920, maxHeight = 1080, quality = 0.8, format = 'jpeg' } = options
        
        // 计算新尺寸
        let { width, height } = img
        
        if (width > maxWidth) {
          height = (height * maxWidth) / width
          width = maxWidth
        }
        
        if (height > maxHeight) {
          width = (width * maxHeight) / height
          height = maxHeight
        }
        
        // 设置画布尺寸
        canvas.width = width
        canvas.height = height
        
        // 绘制图片
        ctx?.drawImage(img, 0, 0, width, height)
        
        // 转换为Blob
        canvas.toBlob(
          (blob) => {
            if (blob) {
              resolve(blob)
            } else {
              reject(new Error('Failed to compress image'))
            }
          },
          `image/${format}`,
          quality
        )
      }
      
      img.onerror = () => reject(new Error('Failed to load image'))
      img.src = URL.createObjectURL(file)
    })
  }
  
  // 压缩文本
  static compressText(text: string): string {
    // 移除多余空白
    return text
      .replace(/\s+/g, ' ')
      .replace(/>\s+</g, '><')
      .trim()
  }
  
  // 压缩JSON
  static compressJSON(obj: any): string {
    return JSON.stringify(obj)
  }
}

// 缓存管理器
export class AssetCacheManager {
  private cache = new Map<string, { data: any, expiry: number }>()
  private maxSize: number
  private defaultTTL: number
  
  constructor(maxSize = 100, defaultTTL = 3600000) { // 1小时默认TTL
    this.maxSize = maxSize
    this.defaultTTL = defaultTTL
  }
  
  // 设置缓存
  set(key: string, data: any, ttl?: number): void {
    const expiry = Date.now() + (ttl || this.defaultTTL)
    
    // 如果缓存已满，删除最旧的项目
    if (this.cache.size >= this.maxSize) {
      const oldestKey = this.cache.keys().next().value
      this.cache.delete(oldestKey)
    }
    
    this.cache.set(key, { data, expiry })
  }
  
  // 获取缓存
  get(key: string): any | null {
    const item = this.cache.get(key)
    
    if (!item) return null
    
    if (Date.now() > item.expiry) {
      this.cache.delete(key)
      return null
    }
    
    return item.data
  }
  
  // 删除缓存
  delete(key: string): boolean {
    return this.cache.delete(key)
  }
  
  // 清空缓存
  clear(): void {
    this.cache.clear()
  }
  
  // 清理过期缓存
  cleanup(): void {
    const now = Date.now()
    for (const [key, item] of this.cache.entries()) {
      if (now > item.expiry) {
        this.cache.delete(key)
      }
    }
  }
  
  // 获取缓存统计
  getStats(): { size: number, maxSize: number } {
    return {
      size: this.cache.size,
      maxSize: this.maxSize
    }
  }
}

// 全局实例
export const cdnManager = new CDNManager()
export const assetCache = new AssetCacheManager()

// 定期清理缓存
setInterval(() => {
  assetCache.cleanup()
}, 300000) // 每5分钟清理一次

// 工具函数
export function getOptimizedImageUrl(
  path: string,
  width?: number,
  height?: number,
  quality = 80
): string {
  return cdnManager.getResourceUrl(path, { width, height, quality })
}

export function getResponsiveImageProps(path: string): {
  srcset: string
  sizes: string
} {
  return cdnManager.getResponsiveImageUrls(path)
}

export async function preloadCriticalAssets(urls: string[]): Promise<void> {
  await cdnManager.preloadResources(urls)
}

export function compressImageFile(
  file: File,
  maxWidth = 1920,
  maxHeight = 1080,
  quality = 0.8
): Promise<Blob> {
  return ResourceCompressor.compressImage(file, {
    maxWidth,
    maxHeight,
    quality
  })
}