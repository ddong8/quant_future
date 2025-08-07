/**
 * 路由预加载工具
 */

interface PreloadOptions {
  delay?: number
  priority?: 'high' | 'low'
  timeout?: number
}

class RoutePreloader {
  private preloadedRoutes = new Set<string>()
  private preloadPromises = new Map<string, Promise<any>>()

  /**
   * 预加载路由组件
   */
  async preloadRoute(routeName: string, importFn: () => Promise<any>, options: PreloadOptions = {}) {
    const { delay = 0, priority = 'low', timeout = 10000 } = options

    // 如果已经预加载过，直接返回
    if (this.preloadedRoutes.has(routeName)) {
      return this.preloadPromises.get(routeName)
    }

    // 延迟预加载
    if (delay > 0) {
      await new Promise(resolve => setTimeout(resolve, delay))
    }

    // 创建预加载 Promise
    const preloadPromise = Promise.race([
      importFn(),
      new Promise((_, reject) => 
        setTimeout(() => reject(new Error(`Preload timeout for ${routeName}`)), timeout)
      )
    ])

    this.preloadPromises.set(routeName, preloadPromise)

    try {
      await preloadPromise
      this.preloadedRoutes.add(routeName)
      console.log(`Route ${routeName} preloaded successfully`)
    } catch (error) {
      console.warn(`Failed to preload route ${routeName}:`, error)
      this.preloadPromises.delete(routeName)
    }

    return preloadPromise
  }

  /**
   * 批量预加载路由
   */
  async preloadRoutes(routes: Array<{ name: string; importFn: () => Promise<any>; options?: PreloadOptions }>) {
    const promises = routes.map(route => 
      this.preloadRoute(route.name, route.importFn, route.options)
    )

    try {
      await Promise.allSettled(promises)
    } catch (error) {
      console.warn('Some routes failed to preload:', error)
    }
  }

  /**
   * 预加载关键路由（用户可能立即访问的路由）
   */
  async preloadCriticalRoutes() {
    const criticalRoutes = [
      {
        name: 'Dashboard',
        importFn: () => import('@/views/dashboard/DashboardView.vue'),
        options: { priority: 'high' as const }
      },
      {
        name: 'Orders',
        importFn: () => import('@/views/orders/OrdersView.vue'),
        options: { priority: 'high' as const }
      },
      {
        name: 'Positions',
        importFn: () => import('@/views/positions/PositionsView.vue'),
        options: { priority: 'high' as const }
      }
    ]

    await this.preloadRoutes(criticalRoutes)
  }

  /**
   * 预加载次要路由（用户可能稍后访问的路由）
   */
  async preloadSecondaryRoutes() {
    const secondaryRoutes = [
      {
        name: 'MarketQuotes',
        importFn: () => import('@/views/market/MarketQuotes.vue'),
        options: { delay: 2000, priority: 'low' as const }
      },
      {
        name: 'TechnicalAnalysis',
        importFn: () => import('@/views/market/TechnicalAnalysisView.vue'),
        options: { delay: 3000, priority: 'low' as const }
      },
      {
        name: 'AccountOverview',
        importFn: () => import('@/views/account/AccountOverview.vue'),
        options: { delay: 4000, priority: 'low' as const }
      }
    ]

    await this.preloadRoutes(secondaryRoutes)
  }

  /**
   * 智能预加载（根据用户行为预测）
   */
  async smartPreload(currentRoute: string) {
    // 根据当前路由预测用户可能访问的下一个路由
    const routeMap: Record<string, string[]> = {
      'dashboard': ['orders', 'positions', 'market-quotes'],
      'orders': ['positions', 'order-history'],
      'positions': ['orders', 'risk-monitoring'],
      'market-quotes': ['technical-analysis', 'orders'],
      'backtest': ['strategy-management', 'backtest-results']
    }

    const nextRoutes = routeMap[currentRoute] || []
    
    for (const routeName of nextRoutes) {
      try {
        // 动态导入路由组件
        const importFn = () => import(`@/views/${routeName.replace('-', '/')}/index.vue`)
        await this.preloadRoute(routeName, importFn, { delay: 1000 })
      } catch (error) {
        // 忽略导入错误，可能路径不存在
      }
    }
  }

  /**
   * 检查路由是否已预加载
   */
  isPreloaded(routeName: string): boolean {
    return this.preloadedRoutes.has(routeName)
  }

  /**
   * 清理预加载缓存
   */
  clear() {
    this.preloadedRoutes.clear()
    this.preloadPromises.clear()
  }

  /**
   * 智能预加载（简化版本，用于路由后钩子）
   */
  async intelligentPreload() {
    try {
      // 预加载一些常用的路由
      await this.preloadCriticalRoutes()
    } catch (error) {
      console.warn('Intelligent preload failed:', error)
    }
  }

  /**
   * 获取预加载统计信息
   */
  getStats() {
    return {
      preloadedCount: this.preloadedRoutes.size,
      pendingCount: this.preloadPromises.size,
      preloadedRoutes: Array.from(this.preloadedRoutes)
    }
  }
}

// 创建全局实例
export const routePreloader = new RoutePreloader()

// 创建路由预加载器的工厂函数
export const createRoutePreloader = () => {
  return new RoutePreloader()
}

// 导出类型和工具函数
export type { PreloadOptions }
export { RoutePreloader }

// 默认导出
export default routePreloader