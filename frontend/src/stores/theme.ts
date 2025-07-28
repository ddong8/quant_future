import { defineStore } from 'pinia'
import { ref } from 'vue'

export type ThemeMode = 'light' | 'dark' | 'auto'

export const useThemeStore = defineStore('theme', () => {
  // 状态
  const mode = ref<ThemeMode>('light')
  const isDark = ref(false)

  // 初始化主题
  const initTheme = () => {
    const savedMode = localStorage.getItem('theme-mode') as ThemeMode
    if (savedMode) {
      mode.value = savedMode
    }
    
    applyTheme()
    
    // 监听系统主题变化
    if (mode.value === 'auto') {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
      mediaQuery.addEventListener('change', handleSystemThemeChange)
    }
  }

  // 设置主题模式
  const setThemeMode = (newMode: ThemeMode) => {
    mode.value = newMode
    localStorage.setItem('theme-mode', newMode)
    applyTheme()
    
    // 重新监听系统主题变化
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    mediaQuery.removeEventListener('change', handleSystemThemeChange)
    
    if (newMode === 'auto') {
      mediaQuery.addEventListener('change', handleSystemThemeChange)
    }
  }

  // 应用主题
  const applyTheme = () => {
    let shouldBeDark = false
    
    switch (mode.value) {
      case 'dark':
        shouldBeDark = true
        break
      case 'light':
        shouldBeDark = false
        break
      case 'auto':
        shouldBeDark = window.matchMedia('(prefers-color-scheme: dark)').matches
        break
    }
    
    isDark.value = shouldBeDark
    
    // 切换HTML类名
    const html = document.documentElement
    if (shouldBeDark) {
      html.classList.add('dark')
    } else {
      html.classList.remove('dark')
    }
    
    // 设置Element Plus主题
    html.style.colorScheme = shouldBeDark ? 'dark' : 'light'
  }

  // 处理系统主题变化
  const handleSystemThemeChange = () => {
    if (mode.value === 'auto') {
      applyTheme()
    }
  }

  // 切换主题
  const toggleTheme = () => {
    const newMode = isDark.value ? 'light' : 'dark'
    setThemeMode(newMode)
  }

  return {
    // 状态
    mode: readonly(mode),
    isDark: readonly(isDark),
    
    // 方法
    initTheme,
    setThemeMode,
    toggleTheme
  }
})