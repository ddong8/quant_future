import axios from 'axios'
import type { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import router from '@/router'
import NProgress from 'nprogress'

// 响应数据类型
export interface ApiResponse<T = any> {
  success: boolean
  data: T
  message: string
  code?: string
  timestamp?: string
}

// 创建axios实例
const request: AxiosInstance = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
request.interceptors.request.use(
  (config: AxiosRequestConfig) => {
    // 显示加载进度
    NProgress.start()
    
    // 添加认证token
    const authStore = useAuthStore()
    if (authStore.token) {
      config.headers = config.headers || {}
      config.headers.Authorization = `Bearer ${authStore.token}`
    }
    
    return config
  },
  (error) => {
    NProgress.done()
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (response: AxiosResponse<ApiResponse>) => {
    NProgress.done()
    
    const { data } = response
    
    // 检查业务状态码
    if (data.success === false) {
      // 根据错误码处理不同情况
      if (data.code === 'UNAUTHORIZED' || data.code === 'TOKEN_EXPIRED') {
        handleAuthError()
        return Promise.reject(new Error(data.message || '认证失败'))
      }
      
      // 其他业务错误
      ElMessage.error(data.message || '请求失败')
      return Promise.reject(new Error(data.message || '请求失败'))
    }
    
    return data
  },
  async (error) => {
    NProgress.done()
    
    const { response } = error
    
    if (response) {
      const { status, data } = response
      
      switch (status) {
        case 401:
          // 未授权，尝试刷新token
          const refreshed = await handleTokenRefresh()
          if (refreshed) {
            // 重新发送原请求
            return request(error.config)
          } else {
            handleAuthError()
          }
          break
          
        case 403:
          ElMessage.error('权限不足')
          break
          
        case 404:
          ElMessage.error('请求的资源不存在')
          break
          
        case 422:
          // 参数验证错误
          const validationErrors = data?.details?.validation_errors
          if (validationErrors && Array.isArray(validationErrors)) {
            const errorMessages = validationErrors.map((err: any) => err.msg).join('; ')
            ElMessage.error(`参数错误: ${errorMessages}`)
          } else {
            ElMessage.error(data?.message || '参数验证失败')
          }
          break
          
        case 429:
          ElMessage.error('请求过于频繁，请稍后再试')
          break
          
        case 500:
          ElMessage.error('服务器内部错误')
          break
          
        case 502:
        case 503:
        case 504:
          ElMessage.error('服务暂时不可用，请稍后再试')
          break
          
        default:
          ElMessage.error(data?.message || `请求失败 (${status})`)
      }
    } else if (error.code === 'ECONNABORTED') {
      ElMessage.error('请求超时，请检查网络连接')
    } else if (error.message === 'Network Error') {
      ElMessage.error('网络连接失败，请检查网络')
    } else {
      ElMessage.error(error.message || '请求失败')
    }
    
    return Promise.reject(error)
  }
)

// 处理认证错误
const handleAuthError = () => {
  const authStore = useAuthStore()
  
  ElMessageBox.confirm(
    '登录状态已过期，请重新登录',
    '提示',
    {
      confirmButtonText: '重新登录',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    authStore.clearAuth()
    router.push('/login')
  }).catch(() => {
    // 用户取消
  })
}

// 处理token刷新
const handleTokenRefresh = async (): Promise<boolean> => {
  const authStore = useAuthStore()
  
  try {
    const success = await authStore.refreshAccessToken()
    return success
  } catch (error) {
    return false
  }
}

// 请求方法封装
export const http = {
  get: <T = any>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> => {
    return request.get(url, config)
  },
  
  post: <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> => {
    return request.post(url, data, config)
  },
  
  put: <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> => {
    return request.put(url, data, config)
  },
  
  delete: <T = any>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> => {
    return request.delete(url, config)
  },
  
  patch: <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> => {
    return request.patch(url, data, config)
  }
}

export default request