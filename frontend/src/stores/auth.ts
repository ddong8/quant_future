import { defineStore } from 'pinia'
import { ref, computed, readonly } from 'vue'
import type { User, LoginRequest, RegisterRequest } from '@/types/auth'
import { authApi } from '@/api/auth'
import { ElMessage } from 'element-plus'

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const user = ref<User | null>(null)
  const token = ref<string | null>(null)
  const refreshToken = ref<string | null>(null)
  const loading = ref(false)

  // 计算属性
  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const userRole = computed(() => user.value?.role)
  const userName = computed(() => user.value?.username)

  // 初始化认证状态
  const initAuth = async () => {
    const savedToken = localStorage.getItem('access_token')
    const savedRefreshToken = localStorage.getItem('refresh_token')
    
    if (savedToken && savedRefreshToken) {
      token.value = savedToken
      refreshToken.value = savedRefreshToken
      
      try {
        // 验证token并获取用户信息
        await getCurrentUser()
      } catch (error) {
        // token无效，清除认证状态
        clearAuth()
      }
    }
  }

  // 登录
  const login = async (loginData: LoginRequest) => {
    loading.value = true
    try {
      const response = await authApi.login(loginData)
      
      // 现在后端返回统一格式：{ success: true, data: TokenResponse, message: string }
      if (response.success && response.data) {
        const { access_token, refresh_token, user_id, username, role } = response.data
        
        // 构造用户对象
        const userData: User = {
          id: user_id,
          username: username,
          email: '', // 后续通过 getCurrentUser 获取完整信息
          role: role as 'admin' | 'trader' | 'viewer',
          is_active: true,
          is_verified: true,
          created_at: '',
          updated_at: ''
        }
        
        // 保存认证信息
        token.value = access_token
        refreshToken.value = refresh_token
        user.value = userData
        
        // 持久化存储
        localStorage.setItem('access_token', access_token)
        localStorage.setItem('refresh_token', refresh_token)
        
        // 获取完整用户信息
        try {
          await getCurrentUser()
        } catch (error) {
          console.warn('获取用户详细信息失败，使用基本信息')
        }
        
        // 登录成功后，触发数据预加载
        try {
          await loadUserProfileData()
        } catch (error) {
          console.warn('预加载用户数据失败:', error)
        }
        
        ElMessage.success(response.message || '登录成功')
        return true
      } else {
        ElMessage.error(response.message || '登录失败')
        return false
      }
    } catch (error: any) {
      console.error('登录错误:', error)
      ElMessage.error(error.message || '登录失败')
      return false
    } finally {
      loading.value = false
    }
  }

  // 注册
  const register = async (registerData: RegisterRequest) => {
    loading.value = true
    try {
      const response = await authApi.register(registerData)
      
      if (response.success) {
        ElMessage.success('注册成功，请登录')
        return true
      } else {
        ElMessage.error(response.message || '注册失败')
        return false
      }
    } catch (error: any) {
      ElMessage.error(error.message || '注册失败')
      return false
    } finally {
      loading.value = false
    }
  }

  // 登出
  const logout = async () => {
    try {
      if (token.value) {
        await authApi.logout()
      }
    } catch (error) {
      console.error('登出请求失败:', error)
    } finally {
      clearAuth()
      ElMessage.success('已退出登录')
    }
  }

  // 获取当前用户信息
  const getCurrentUser = async () => {
    try {
      const response = await authApi.getCurrentUser()
      // 检查响应格式，适配不同的返回格式
      if (response.success && response.data) {
        user.value = response.data
      } else if (response.id) {
        // 直接返回用户对象的情况
        user.value = response as User
      } else {
        throw new Error('获取用户信息失败')
      }
    } catch (error) {
      console.warn('获取用户信息失败:', error)
      // 不清除认证状态，因为可能只是这个接口有问题
      throw error
    }
  }

  // 刷新token
  const refreshAccessToken = async () => {
    if (!refreshToken.value) {
      clearAuth()
      return false
    }

    try {
      const response = await authApi.refreshToken(refreshToken.value)
      
      // 适配后端直接返回 TokenResponse 的格式
      if (response.access_token) {
        const { access_token, refresh_token: newRefreshToken } = response
        
        token.value = access_token
        refreshToken.value = newRefreshToken
        
        localStorage.setItem('access_token', access_token)
        localStorage.setItem('refresh_token', newRefreshToken)
        
        return true
      } else {
        clearAuth()
        return false
      }
    } catch (error) {
      clearAuth()
      return false
    }
  }

  // 清除认证状态
  const clearAuth = () => {
    user.value = null
    token.value = null
    refreshToken.value = null
    
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  // 更新用户信息
  const updateUser = (userData: Partial<User>) => {
    if (user.value) {
      user.value = { ...user.value, ...userData }
    }
  }

  // 检查权限
  const hasPermission = (requiredRole: string | string[]) => {
    if (!user.value) return false
    
    const roles = Array.isArray(requiredRole) ? requiredRole : [requiredRole]
    return roles.includes(user.value.role)
  }

  // 加载用户资料数据
  const loadUserProfileData = async () => {
    try {
      // 动态导入dashboard API
      const { dashboardApi } = await import('@/api/dashboard')
      
      // 加载用户资料
      const profileResponse = await dashboardApi.getUserProfile()
      if (profileResponse.success && profileResponse.data) {
        updateUser(profileResponse.data)
        console.log('用户资料预加载成功')
      }
    } catch (error) {
      console.warn('预加载用户资料失败:', error)
      // 不抛出错误，因为这不是关键操作
    }
  }

  return {
    // 状态
    user: readonly(user),
    token: readonly(token),
    loading: readonly(loading),
    
    // 计算属性
    isAuthenticated,
    userRole,
    userName,
    
    // 方法
    initAuth,
    login,
    register,
    logout,
    getCurrentUser,
    refreshAccessToken,
    clearAuth,
    updateUser,
    hasPermission,
    loadUserProfileData
  }
})