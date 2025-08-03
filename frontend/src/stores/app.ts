import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface AppState {
  loading: boolean
  sidebarCollapsed: boolean
  theme: 'light' | 'dark' | 'auto'
  language: 'zh-CN' | 'en-US'
  title: string
  version: string
}

export const useAppStore = defineStore('app', () => {
  // 状态
  const loading = ref(false)
  const sidebarCollapsed = ref(false)
  const theme = ref<AppState['theme']>('light')
  const language = ref<AppState['language']>('zh-CN')
  const title = ref('量化交易平台')
  const version = ref('1.0.0')

  // 计算属性
  const isDark = computed(() => {
    if (theme.value === 'auto') {
      return window.matchMedia('(prefers-color-scheme: dark)').matches
    }
    return theme.value === 'dark'
  })

  const isLight = computed(() => !isDark.value)

  // 操作
  const setLoading = (value: boolean) => {
    loading.value = value
  }

  const toggleSidebar = () => {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  const setSidebarCollapsed = (value: boolean) => {
    sidebarCollapsed.value = value
  }

  const setTheme = (value: AppState['theme']) => {
    theme.value = value
    // 保存到本地存储
    localStorage.setItem('app-theme', value)
    // 更新 HTML 类名
    updateThemeClass()
  }

  const setLanguage = (value: AppState['language']) => {
    language.value = value
    // 保存到本地存储
    localStorage.setItem('app-language', value)
  }

  const setTitle = (value: string) => {
    title.value = value
    // 更新页面标题
    document.title = value
  }

  const updateThemeClass = () => {
    const html = document.documentElement
    if (isDark.value) {
      html.classList.add('dark')
    } else {
      html.classList.remove('dark')
    }
  }

  // 初始化
  const init = () => {
    // 从本地存储恢复设置
    const savedTheme = localStorage.getItem('app-theme') as AppState['theme']
    if (savedTheme) {
      theme.value = savedTheme
    }

    const savedLanguage = localStorage.getItem('app-language') as AppState['language']
    if (savedLanguage) {
      language.value = savedLanguage
    }

    const savedSidebarState = localStorage.getItem('sidebar-collapsed')
    if (savedSidebarState) {
      sidebarCollapsed.value = JSON.parse(savedSidebarState)
    }

    // 初始化主题
    updateThemeClass()

    // 监听系统主题变化
    if (theme.value === 'auto') {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
      mediaQuery.addEventListener('change', updateThemeClass)
    }

    // 设置页面标题
    document.title = title.value
  }

  // 保存侧边栏状态
  const saveSidebarState = () => {
    localStorage.setItem('sidebar-collapsed', JSON.stringify(sidebarCollapsed.value))
  }

  return {
    // 状态
    loading,
    sidebarCollapsed,
    theme,
    language,
    title,
    version,
    
    // 计算属性
    isDark,
    isLight,
    
    // 操作
    setLoading,
    toggleSidebar,
    setSidebarCollapsed,
    setTheme,
    setLanguage,
    setTitle,
    updateThemeClass,
    init,
    saveSidebarState
  }
})