/**
 * 主题管理组合式函数
 */
import { ref, computed, watch, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { updateUserSettings } from '@/api/userSettings'

export type ThemeMode = 'light' | 'dark' | 'auto'
export type ColorScheme = 'default' | 'blue' | 'green' | 'purple' | 'orange'

export interface ThemeConfig {
  mode: ThemeMode
  colorScheme: ColorScheme
  fontSize: number
  borderRadius: number
  compactMode: boolean
  highContrast: boolean
  reducedMotion: boolean
}

export interface ThemeColors {
  primary: string
  primaryHover: string
  primaryActive: string
  secondary: string
  success: string
  warning: string
  danger: string
  info: string
  background: string
  surface: string
  text: string
  textSecondary: string
  border: string
  shadow: string
}

// 预定义的颜色方案
const COLOR_SCHEMES: Record<ColorScheme, Partial<ThemeColors>> = {
  default: {
    primary: '#409eff',
    primaryHover: '#66b1ff',
    primaryActive: '#3a8ee6',
    secondary: '#909399',
    success: '#67c23a',
    warning: '#e6a23c',
    danger: '#f56c6c',
    info: '#909399'
  },
  blue: {
    primary: '#1890ff',
    primaryHover: '#40a9ff',
    primaryActive: '#096dd9',
    secondary: '#722ed1',
    success: '#52c41a',
    warning: '#faad14',
    danger: '#ff4d4f',
    info: '#13c2c2'
  },
  green: {
    primary: '#52c41a',
    primaryHover: '#73d13d',
    primaryActive: '#389e0d',
    secondary: '#722ed1',
    success: '#52c41a',
    warning: '#faad14',
    danger: '#ff4d4f',
    info: '#13c2c2'
  },
  purple: {
    primary: '#722ed1',
    primaryHover: '#9254de',
    primaryActive: '#531dab',
    secondary: '#1890ff',
    success: '#52c41a',
    warning: '#faad14',
    danger: '#ff4d4f',
    info: '#13c2c2'
  },
  orange: {
    primary: '#fa8c16',
    primaryHover: '#ffa940',
    primaryActive: '#d46b08',
    secondary: '#722ed1',
    success: '#52c41a',
    warning: '#faad14',
    danger: '#ff4d4f',
    info: '#13c2c2'
  }
}

// 浅色主题基础颜色
const LIGHT_THEME_BASE: ThemeColors = {
  primary: '#409eff',
  primaryHover: '#66b1ff',
  primaryActive: '#3a8ee6',
  secondary: '#909399',
  success: '#67c23a',
  warning: '#e6a23c',
  danger: '#f56c6c',
  info: '#909399',
  background: '#ffffff',
  surface: '#f5f7fa',
  text: '#303133',
  textSecondary: '#606266',
  border: '#dcdfe6',
  shadow: 'rgba(0, 0, 0, 0.12)'
}

// 深色主题基础颜色
const DARK_THEME_BASE: ThemeColors = {
  primary: '#409eff',
  primaryHover: '#66b1ff',
  primaryActive: '#3a8ee6',
  secondary: '#909399',
  success: '#67c23a',
  warning: '#e6a23c',
  danger: '#f56c6c',
  info: '#909399',
  background: '#1a1a1a',
  surface: '#2d2d2d',
  text: '#e4e7ed',
  textSecondary: '#c0c4cc',
  border: '#4c4d4f',
  shadow: 'rgba(0, 0, 0, 0.3)'
}

export function useTheme() {
  const userStore = useUserStore()
  
  // 主题配置
  const themeConfig = ref<ThemeConfig>({
    mode: 'light',
    colorScheme: 'default',
    fontSize: 14,
    borderRadius: 4,
    compactMode: false,
    highContrast: false,
    reducedMotion: false
  })
  
  // 当前实际主题模式（考虑系统偏好）
  const actualThemeMode = computed(() => {
    if (themeConfig.value.mode === 'auto') {
      return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
    }
    return themeConfig.value.mode
  })
  
  // 当前主题颜色
  const themeColors = computed<ThemeColors>(() => {
    const baseColors = actualThemeMode.value === 'dark' ? DARK_THEME_BASE : LIGHT_THEME_BASE
    const schemeColors = COLOR_SCHEMES[themeConfig.value.colorScheme] || {}
    
    let colors = { ...baseColors, ...schemeColors }
    
    // 高对比度调整
    if (themeConfig.value.highContrast) {
      if (actualThemeMode.value === 'dark') {
        colors.text = '#ffffff'
        colors.background = '#000000'
        colors.border = '#666666'
      } else {
        colors.text = '#000000'
        colors.background = '#ffffff'
        colors.border = '#333333'
      }
    }
    
    return colors
  })
  
  // CSS 变量
  const cssVariables = computed(() => {
    const colors = themeColors.value
    const config = themeConfig.value
    
    return {
      // 颜色变量
      '--color-primary': colors.primary,
      '--color-primary-hover': colors.primaryHover,
      '--color-primary-active': colors.primaryActive,
      '--color-secondary': colors.secondary,
      '--color-success': colors.success,
      '--color-warning': colors.warning,
      '--color-danger': colors.danger,
      '--color-info': colors.info,
      '--color-background': colors.background,
      '--color-surface': colors.surface,
      '--color-text': colors.text,
      '--color-text-secondary': colors.textSecondary,
      '--color-border': colors.border,
      '--color-shadow': colors.shadow,
      
      // 尺寸变量
      '--font-size-base': `${config.fontSize}px`,
      '--font-size-small': `${config.fontSize - 2}px`,
      '--font-size-large': `${config.fontSize + 2}px`,
      '--font-size-xl': `${config.fontSize + 4}px`,
      '--border-radius': `${config.borderRadius}px`,
      '--border-radius-small': `${Math.max(2, config.borderRadius - 2)}px`,
      '--border-radius-large': `${config.borderRadius + 2}px`,
      
      // 间距变量（紧凑模式）
      '--spacing-xs': config.compactMode ? '4px' : '8px',
      '--spacing-sm': config.compactMode ? '8px' : '12px',
      '--spacing-md': config.compactMode ? '12px' : '16px',
      '--spacing-lg': config.compactMode ? '16px' : '24px',
      '--spacing-xl': config.compactMode ? '20px' : '32px',
      
      // 动画变量
      '--transition-duration': config.reducedMotion ? '0ms' : '200ms',
      '--animation-duration': config.reducedMotion ? '0ms' : '300ms'
    }
  })
  
  // 应用主题到DOM
  const applyTheme = () => {
    const root = document.documentElement
    const variables = cssVariables.value
    
    // 设置CSS变量
    Object.entries(variables).forEach(([key, value]) => {
      root.style.setProperty(key, value)
    })
    
    // 设置主题类名
    root.className = root.className.replace(/theme-\w+/g, '')
    root.classList.add(`theme-${actualThemeMode.value}`)
    root.classList.add(`scheme-${themeConfig.value.colorScheme}`)
    
    if (themeConfig.value.compactMode) {
      root.classList.add('compact-mode')
    } else {
      root.classList.remove('compact-mode')
    }
    
    if (themeConfig.value.highContrast) {
      root.classList.add('high-contrast')
    } else {
      root.classList.remove('high-contrast')
    }
    
    if (themeConfig.value.reducedMotion) {
      root.classList.add('reduced-motion')
    } else {
      root.classList.remove('reduced-motion')
    }
    
    // 更新meta标签
    updateMetaThemeColor()
  }
  
  // 更新meta主题颜色
  const updateMetaThemeColor = () => {
    let metaThemeColor = document.querySelector('meta[name="theme-color"]')
    if (!metaThemeColor) {
      metaThemeColor = document.createElement('meta')
      metaThemeColor.setAttribute('name', 'theme-color')
      document.head.appendChild(metaThemeColor)
    }
    metaThemeColor.setAttribute('content', themeColors.value.primary)
  }
  
  // 切换主题模式
  const setThemeMode = async (mode: ThemeMode) => {
    themeConfig.value.mode = mode
    await saveThemeConfig()
  }
  
  // 设置颜色方案
  const setColorScheme = async (scheme: ColorScheme) => {
    themeConfig.value.colorScheme = scheme
    await saveThemeConfig()
  }
  
  // 设置字体大小
  const setFontSize = async (size: number) => {
    themeConfig.value.fontSize = Math.max(12, Math.min(20, size))
    await saveThemeConfig()
  }
  
  // 设置边框圆角
  const setBorderRadius = async (radius: number) => {
    themeConfig.value.borderRadius = Math.max(0, Math.min(12, radius))
    await saveThemeConfig()
  }
  
  // 切换紧凑模式
  const toggleCompactMode = async () => {
    themeConfig.value.compactMode = !themeConfig.value.compactMode
    await saveThemeConfig()
  }
  
  // 切换高对比度
  const toggleHighContrast = async () => {
    themeConfig.value.highContrast = !themeConfig.value.highContrast
    await saveThemeConfig()
  }
  
  // 切换减少动画
  const toggleReducedMotion = async () => {
    themeConfig.value.reducedMotion = !themeConfig.value.reducedMotion
    await saveThemeConfig()
  }
  
  // 重置主题配置
  const resetThemeConfig = async () => {
    themeConfig.value = {
      mode: 'light',
      colorScheme: 'default',
      fontSize: 14,
      borderRadius: 4,
      compactMode: false,
      highContrast: false,
      reducedMotion: false
    }
    await saveThemeConfig()
  }
  
  // 保存主题配置
  const saveThemeConfig = async () => {
    try {
      await updateUserSettings({
        theme: themeConfig.value.mode,
        theme_config: themeConfig.value
      })
    } catch (error) {
      console.error('保存主题配置失败:', error)
    }
  }
  
  // 加载主题配置
  const loadThemeConfig = () => {
    try {
      // 从用户设置加载
      const userSettings = userStore.settings
      if (userSettings?.theme) {
        themeConfig.value.mode = userSettings.theme as ThemeMode
      }
      if (userSettings?.theme_config) {
        Object.assign(themeConfig.value, userSettings.theme_config)
      }
      
      // 从localStorage加载（备用）
      const saved = localStorage.getItem('theme-config')
      if (saved) {
        const config = JSON.parse(saved)
        Object.assign(themeConfig.value, config)
      }
    } catch (error) {
      console.warn('加载主题配置失败:', error)
    }
  }
  
  // 监听系统主题变化
  const watchSystemTheme = () => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    const handleChange = () => {
      if (themeConfig.value.mode === 'auto') {
        applyTheme()
      }
    }
    
    mediaQuery.addEventListener('change', handleChange)
    
    return () => {
      mediaQuery.removeEventListener('change', handleChange)
    }
  }
  
  // 获取主题预览
  const getThemePreview = (mode: ThemeMode, scheme: ColorScheme) => {
    const previewMode = mode === 'auto' 
      ? (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
      : mode
    
    const baseColors = previewMode === 'dark' ? DARK_THEME_BASE : LIGHT_THEME_BASE
    const schemeColors = COLOR_SCHEMES[scheme] || {}
    
    return { ...baseColors, ...schemeColors }
  }
  
  // 导出主题配置
  const exportThemeConfig = () => {
    return {
      ...themeConfig.value,
      exportTime: new Date().toISOString(),
      version: '1.0'
    }
  }
  
  // 导入主题配置
  const importThemeConfig = async (config: any) => {
    try {
      if (config.version === '1.0') {
        const { exportTime, version, ...themeData } = config
        Object.assign(themeConfig.value, themeData)
        await saveThemeConfig()
        return true
      }
      return false
    } catch (error) {
      console.error('导入主题配置失败:', error)
      return false
    }
  }
  
  // 监听配置变化并应用主题
  watch(themeConfig, applyTheme, { deep: true })
  
  // 初始化
  onMounted(() => {
    loadThemeConfig()
    applyTheme()
    watchSystemTheme()
  })
  
  return {
    // 状态
    themeConfig,
    actualThemeMode,
    themeColors,
    cssVariables,
    
    // 方法
    setThemeMode,
    setColorScheme,
    setFontSize,
    setBorderRadius,
    toggleCompactMode,
    toggleHighContrast,
    toggleReducedMotion,
    resetThemeConfig,
    applyTheme,
    getThemePreview,
    exportThemeConfig,
    importThemeConfig,
    
    // 常量
    COLOR_SCHEMES
  }
}