import { defineStore } from 'pinia'
import { ref, readonly } from 'vue'

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
    
    // 直接同步更新，避免闪烁
    const html = document.documentElement
    
    // 临时禁用过渡效果
    html.style.setProperty('--transition-duration', '0s')
    
    // 立即切换主题
    if (shouldBeDark) {
      html.classList.add('dark')
      html.setAttribute('data-theme', 'dark')
    } else {
      html.classList.remove('dark')
      html.setAttribute('data-theme', 'light')
    }
    
    // 设置Element Plus主题
    html.style.colorScheme = shouldBeDark ? 'dark' : 'light'
    
    // 强制重绘
    html.offsetHeight
    
    // 恢复过渡效果
    setTimeout(() => {
      html.style.removeProperty('--transition-duration')
    }, 50)
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