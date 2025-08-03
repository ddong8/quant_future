/**
 * 布局管理组合式函数
 */
import { ref, computed, watch, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { updateUserSettings } from '@/api/userSettings'

export type LayoutMode = 'fixed' | 'fluid' | 'boxed'
export type SidebarPosition = 'left' | 'right'
export type HeaderStyle = 'fixed' | 'static' | 'hidden'
export type FooterStyle = 'fixed' | 'static' | 'hidden'

export interface LayoutConfig {
  mode: LayoutMode
  sidebarPosition: SidebarPosition
  sidebarCollapsed: boolean
  sidebarWidth: number
  headerStyle: HeaderStyle
  headerHeight: number
  footerStyle: FooterStyle
  footerHeight: number
  showBreadcrumb: boolean
  showTabs: boolean
  contentPadding: number
  maxWidth: number
}

export interface DashboardLayout {
  widgets: DashboardWidget[]
  columns: number
  gap: number
  autoHeight: boolean
}

export interface DashboardWidget {
  id: string
  type: string
  title: string
  x: number
  y: number
  width: number
  height: number
  config: Record<string, any>
  visible: boolean
}

// 预定义的布局模板
const LAYOUT_TEMPLATES = {
  default: {
    mode: 'fluid' as LayoutMode,
    sidebarPosition: 'left' as SidebarPosition,
    sidebarCollapsed: false,
    sidebarWidth: 240,
    headerStyle: 'fixed' as HeaderStyle,
    headerHeight: 60,
    footerStyle: 'static' as FooterStyle,
    footerHeight: 40,
    showBreadcrumb: true,
    showTabs: true,
    contentPadding: 20,
    maxWidth: 1200
  },
  compact: {
    mode: 'boxed' as LayoutMode,
    sidebarPosition: 'left' as SidebarPosition,
    sidebarCollapsed: true,
    sidebarWidth: 60,
    headerStyle: 'fixed' as HeaderStyle,
    headerHeight: 50,
    footerStyle: 'hidden' as FooterStyle,
    footerHeight: 0,
    showBreadcrumb: false,
    showTabs: false,
    contentPadding: 12,
    maxWidth: 1000
  },
  wide: {
    mode: 'fluid' as LayoutMode,
    sidebarPosition: 'left' as SidebarPosition,
    sidebarCollapsed: false,
    sidebarWidth: 280,
    headerStyle: 'fixed' as HeaderStyle,
    headerHeight: 70,
    footerStyle: 'static' as FooterStyle,
    footerHeight: 50,
    showBreadcrumb: true,
    showTabs: true,
    contentPadding: 24,
    maxWidth: 1600
  }
}

export function useLayout() {
  const userStore = useUserStore()
  
  // 布局配置
  const layoutConfig = ref<LayoutConfig>({ ...LAYOUT_TEMPLATES.default })
  
  // 仪表板布局
  const dashboardLayout = ref<DashboardLayout>({
    widgets: [],
    columns: 12,
    gap: 16,
    autoHeight: true
  })
  
  // 响应式断点
  const breakpoints = {
    xs: 480,
    sm: 768,
    md: 1024,
    lg: 1280,
    xl: 1920
  }
  
  // 当前屏幕尺寸
  const screenWidth = ref(window.innerWidth)
  const screenHeight = ref(window.innerHeight)
  
  // 当前断点
  const currentBreakpoint = computed(() => {
    const width = screenWidth.value
    if (width < breakpoints.xs) return 'xs'
    if (width < breakpoints.sm) return 'sm'
    if (width < breakpoints.md) return 'md'
    if (width < breakpoints.lg) return 'lg'
    if (width < breakpoints.xl) return 'xl'
    return 'xxl'
  })
  
  // 是否移动端
  const isMobile = computed(() => currentBreakpoint.value === 'xs')
  const isTablet = computed(() => ['sm', 'md'].includes(currentBreakpoint.value))
  const isDesktop = computed(() => ['lg', 'xl', 'xxl'].includes(currentBreakpoint.value))
  
  // 计算后的布局样式
  const layoutStyles = computed(() => {
    const config = layoutConfig.value
    const styles: Record<string, any> = {}
    
    // 容器样式
    if (config.mode === 'boxed') {
      styles['--layout-max-width'] = `${config.maxWidth}px`
      styles['--layout-margin'] = 'auto'
    } else {
      styles['--layout-max-width'] = '100%'
      styles['--layout-margin'] = '0'
    }
    
    // 侧边栏样式
    styles['--sidebar-width'] = config.sidebarCollapsed ? '60px' : `${config.sidebarWidth}px`
    styles['--sidebar-position'] = config.sidebarPosition
    
    // 头部样式
    styles['--header-height'] = `${config.headerHeight}px`
    styles['--header-position'] = config.headerStyle === 'fixed' ? 'fixed' : 'static'
    styles['--header-display'] = config.headerStyle === 'hidden' ? 'none' : 'block'
    
    // 底部样式
    styles['--footer-height'] = `${config.footerHeight}px`
    styles['--footer-position'] = config.footerStyle === 'fixed' ? 'fixed' : 'static'
    styles['--footer-display'] = config.footerStyle === 'hidden' ? 'none' : 'block'
    
    // 内容样式
    styles['--content-padding'] = `${config.contentPadding}px`
    
    // 计算内容区域的偏移
    let contentMarginTop = 0
    let contentMarginBottom = 0
    
    if (config.headerStyle === 'fixed') {
      contentMarginTop += config.headerHeight
    }
    if (config.footerStyle === 'fixed') {
      contentMarginBottom += config.footerHeight
    }
    
    styles['--content-margin-top'] = `${contentMarginTop}px`
    styles['--content-margin-bottom'] = `${contentMarginBottom}px`
    
    return styles
  })
  
  // 应用布局样式
  const applyLayout = () => {
    const root = document.documentElement
    const styles = layoutStyles.value
    
    // 设置CSS变量
    Object.entries(styles).forEach(([key, value]) => {
      root.style.setProperty(key, String(value))
    })
    
    // 设置布局类名
    root.className = root.className.replace(/layout-\w+/g, '')
    root.classList.add(`layout-${layoutConfig.value.mode}`)
    root.classList.add(`sidebar-${layoutConfig.value.sidebarPosition}`)
    
    if (layoutConfig.value.sidebarCollapsed) {
      root.classList.add('sidebar-collapsed')
    } else {
      root.classList.remove('sidebar-collapsed')
    }
    
    if (isMobile.value) {
      root.classList.add('mobile-layout')
    } else {
      root.classList.remove('mobile-layout')
    }
  }
  
  // 切换侧边栏
  const toggleSidebar = async () => {
    layoutConfig.value.sidebarCollapsed = !layoutConfig.value.sidebarCollapsed
    await saveLayoutConfig()
  }
  
  // 设置布局模式
  const setLayoutMode = async (mode: LayoutMode) => {
    layoutConfig.value.mode = mode
    await saveLayoutConfig()
  }
  
  // 设置侧边栏位置
  const setSidebarPosition = async (position: SidebarPosition) => {
    layoutConfig.value.sidebarPosition = position
    await saveLayoutConfig()
  }
  
  // 设置侧边栏宽度
  const setSidebarWidth = async (width: number) => {
    layoutConfig.value.sidebarWidth = Math.max(200, Math.min(400, width))
    await saveLayoutConfig()
  }
  
  // 设置头部样式
  const setHeaderStyle = async (style: HeaderStyle) => {
    layoutConfig.value.headerStyle = style
    await saveLayoutConfig()
  }
  
  // 设置底部样式
  const setFooterStyle = async (style: FooterStyle) => {
    layoutConfig.value.footerStyle = style
    await saveLayoutConfig()
  }
  
  // 应用布局模板
  const applyLayoutTemplate = async (templateName: keyof typeof LAYOUT_TEMPLATES) => {
    const template = LAYOUT_TEMPLATES[templateName]
    if (template) {
      Object.assign(layoutConfig.value, template)
      await saveLayoutConfig()
    }
  }
  
  // 重置布局配置
  const resetLayoutConfig = async () => {
    Object.assign(layoutConfig.value, LAYOUT_TEMPLATES.default)
    await saveLayoutConfig()
  }
  
  // 保存布局配置
  const saveLayoutConfig = async () => {
    try {
      await updateUserSettings({
        sidebar_collapsed: layoutConfig.value.sidebarCollapsed,
        dashboard_layout: {
          layout_config: layoutConfig.value,
          dashboard_layout: dashboardLayout.value
        }
      })
    } catch (error) {
      console.error('保存布局配置失败:', error)
    }
  }
  
  // 加载布局配置
  const loadLayoutConfig = () => {
    try {
      const userSettings = userStore.settings
      if (userSettings?.sidebar_collapsed !== undefined) {
        layoutConfig.value.sidebarCollapsed = userSettings.sidebar_collapsed
      }
      if (userSettings?.dashboard_layout) {
        const saved = userSettings.dashboard_layout
        if (saved.layout_config) {
          Object.assign(layoutConfig.value, saved.layout_config)
        }
        if (saved.dashboard_layout) {
          Object.assign(dashboardLayout.value, saved.dashboard_layout)
        }
      }
    } catch (error) {
      console.warn('加载布局配置失败:', error)
    }
  }
  
  // 仪表板小部件管理
  const addWidget = async (widget: Omit<DashboardWidget, 'id'>) => {
    const newWidget: DashboardWidget = {
      ...widget,
      id: `widget_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    }
    dashboardLayout.value.widgets.push(newWidget)
    await saveLayoutConfig()
    return newWidget.id
  }
  
  const removeWidget = async (widgetId: string) => {
    const index = dashboardLayout.value.widgets.findIndex(w => w.id === widgetId)
    if (index > -1) {
      dashboardLayout.value.widgets.splice(index, 1)
      await saveLayoutConfig()
    }
  }
  
  const updateWidget = async (widgetId: string, updates: Partial<DashboardWidget>) => {
    const widget = dashboardLayout.value.widgets.find(w => w.id === widgetId)
    if (widget) {
      Object.assign(widget, updates)
      await saveLayoutConfig()
    }
  }
  
  const moveWidget = async (widgetId: string, x: number, y: number) => {
    const widget = dashboardLayout.value.widgets.find(w => w.id === widgetId)
    if (widget) {
      widget.x = x
      widget.y = y
      await saveLayoutConfig()
    }
  }
  
  const resizeWidget = async (widgetId: string, width: number, height: number) => {
    const widget = dashboardLayout.value.widgets.find(w => w.id === widgetId)
    if (widget) {
      widget.width = width
      widget.height = height
      await saveLayoutConfig()
    }
  }
  
  // 获取小部件
  const getWidget = (widgetId: string) => {
    return dashboardLayout.value.widgets.find(w => w.id === widgetId)
  }
  
  // 获取可见小部件
  const getVisibleWidgets = () => {
    return dashboardLayout.value.widgets.filter(w => w.visible)
  }
  
  // 导出布局配置
  const exportLayoutConfig = () => {
    return {
      layoutConfig: layoutConfig.value,
      dashboardLayout: dashboardLayout.value,
      exportTime: new Date().toISOString(),
      version: '1.0'
    }
  }
  
  // 导入布局配置
  const importLayoutConfig = async (config: any) => {
    try {
      if (config.version === '1.0') {
        if (config.layoutConfig) {
          Object.assign(layoutConfig.value, config.layoutConfig)
        }
        if (config.dashboardLayout) {
          Object.assign(dashboardLayout.value, config.dashboardLayout)
        }
        await saveLayoutConfig()
        return true
      }
      return false
    } catch (error) {
      console.error('导入布局配置失败:', error)
      return false
    }
  }
  
  // 监听窗口大小变化
  const handleResize = () => {
    screenWidth.value = window.innerWidth
    screenHeight.value = window.innerHeight
  }
  
  // 监听配置变化并应用布局
  watch(layoutConfig, applyLayout, { deep: true })
  watch(currentBreakpoint, () => {
    // 移动端自动折叠侧边栏
    if (isMobile.value && !layoutConfig.value.sidebarCollapsed) {
      layoutConfig.value.sidebarCollapsed = true
    }
  })
  
  // 初始化
  onMounted(() => {
    loadLayoutConfig()
    applyLayout()
    
    window.addEventListener('resize', handleResize)
    
    // 清理函数
    return () => {
      window.removeEventListener('resize', handleResize)
    }
  })
  
  return {
    // 状态
    layoutConfig,
    dashboardLayout,
    screenWidth,
    screenHeight,
    currentBreakpoint,
    isMobile,
    isTablet,
    isDesktop,
    layoutStyles,
    
    // 布局方法
    toggleSidebar,
    setLayoutMode,
    setSidebarPosition,
    setSidebarWidth,
    setHeaderStyle,
    setFooterStyle,
    applyLayoutTemplate,
    resetLayoutConfig,
    applyLayout,
    
    // 小部件方法
    addWidget,
    removeWidget,
    updateWidget,
    moveWidget,
    resizeWidget,
    getWidget,
    getVisibleWidgets,
    
    // 导入导出
    exportLayoutConfig,
    importLayoutConfig,
    
    // 常量
    LAYOUT_TEMPLATES,
    breakpoints
  }
}