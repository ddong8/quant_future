import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import router from '@/router'

// 创建axios实例
const service: AxiosInstance = axios.create({
  baseURL: '/api',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
service.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    
    // 添加认证token
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
      console.log(`🔑 [${config.method?.toUpperCase()}] ${config.url} - 添加Authorization头:`, authStore.token.substring(0, 20) + '...')
    } else {
      console.log(`⚠️ [${config.method?.toUpperCase()}] ${config.url} - 没有token，未添加Authorization头`)
    }
    
    // 添加请求ID用于追踪
    config.headers['X-Request-ID'] = generateRequestId()
    
    return config
  },
  (error) => {
    console.error('Request error:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  (response: AxiosResponse) => {
    const { data, status } = response
    
    // 处理成功响应
    if (status >= 200 && status < 300) {
      return data
    }
    
    return response
  },
  (error) => {
    const { response, message, code } = error
    
    // 增强错误信息
    error.userMessage = getUserFriendlyErrorMessage(error)
    
    if (response) {
      const { status, data } = response
      
      switch (status) {
        case 401:
          // 未授权，清除token并跳转到登录页
          const authStore = useAuthStore()
          authStore.logout()
          router.push('/login')
          // 不显示错误消息，因为会自动跳转到登录页
          break
          
        case 403:
          // 权限错误不显示消息，让组件自己处理
          break
          
        case 404:
          // 资源不存在错误不显示消息，让组件自己处理
          break
          
        case 422:
          // 表单验证错误不显示消息，让组件自己处理
          break
          
        case 429:
          ElMessage.error('请求过于频繁，请稍后再试')
          break
          
        case 500:
        case 502:
        case 503:
        case 504:
          // 服务器错误不显示消息，让组件自己处理
          break
          
        default:
          // 其他错误不显示消息，让组件自己处理
          break
      }
    } else if (code === 'ECONNABORTED') {
      // 超时错误不显示消息，让组件自己处理
    } else if (code === 'ERR_NETWORK' || code === 'ECONNREFUSED') {
      // 网络错误不显示消息，让组件自己处理
    }
    
    return Promise.reject(error)
  }
)

// 获取用户友好的错误消息
function getUserFriendlyErrorMessage(error: any): string {
  const { response, message, code } = error
  
  if (response) {
    const { status, data } = response
    
    switch (status) {
      case 401:
        return '登录已过期，请重新登录'
      case 403:
        return '没有权限访问该资源'
      case 404:
        return '请求的资源不存在'
      case 422:
        if (data?.errors) {
          const errorMessages = Object.values(data.errors).flat()
          return errorMessages.join(', ')
        }
        return data?.message || '请求参数错误'
      case 429:
        return '请求过于频繁，请稍后再试'
      case 500:
        return '服务器内部错误，请稍后重试'
      case 502:
        return '网关错误，请稍后重试'
      case 503:
        return '服务暂时不可用，请稍后重试'
      case 504:
        return '网关超时，请稍后重试'
      default:
        return data?.message || `请求失败 (${status})`
    }
  } else if (code === 'ECONNABORTED') {
    return '请求超时，请检查网络连接'
  } else if (code === 'ERR_NETWORK' || code === 'ECONNREFUSED') {
    return '网络连接失败，请检查网络连接'
  } else {
    return message || '请求失败，请稍后重试'
  }
}

// 生成请求ID
function generateRequestId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
}

// 请求重试配置
interface RetryConfig {
  retries?: number
  retryDelay?: number
  retryCondition?: (error: any) => boolean
}

// 默认重试条件
const defaultRetryCondition = (error: any) => {
  return error.code === 'ERR_NETWORK' || 
         error.code === 'ECONNREFUSED' || 
         error.code === 'ECONNABORTED' ||
         (error.response && error.response.status >= 500)
}

// 带重试的请求方法
async function requestWithRetry<T = any>(
  requestFn: () => Promise<T>,
  config: RetryConfig = {}
): Promise<T> {
  const {
    retries = 2,
    retryDelay = 1000,
    retryCondition = defaultRetryCondition
  } = config

  let lastError: any

  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      return await requestFn()
    } catch (error: any) {
      lastError = error
      
      // 如果是最后一次尝试或不满足重试条件，直接抛出错误
      if (attempt === retries || !retryCondition(error)) {
        throw error
      }
      
      // 等待后重试
      await new Promise(resolve => setTimeout(resolve, retryDelay * (attempt + 1)))
      console.log(`请求失败，${retryDelay * (attempt + 1)}ms后进行第${attempt + 2}次尝试`)
    }
  }

  throw lastError
}

// 请求方法封装
export const request = {
  get<T = any>(url: string, config?: AxiosRequestConfig & RetryConfig): Promise<T> {
    const { retries, retryDelay, retryCondition, ...axiosConfig } = config || {}
    return requestWithRetry(
      () => service.get(url, axiosConfig),
      { retries, retryDelay, retryCondition }
    )
  },
  
  post<T = any>(url: string, data?: any, config?: AxiosRequestConfig & RetryConfig): Promise<T> {
    const { retries, retryDelay, retryCondition, ...axiosConfig } = config || {}
    return requestWithRetry(
      () => service.post(url, data, axiosConfig),
      { retries, retryDelay, retryCondition }
    )
  },
  
  put<T = any>(url: string, data?: any, config?: AxiosRequestConfig & RetryConfig): Promise<T> {
    const { retries, retryDelay, retryCondition, ...axiosConfig } = config || {}
    return requestWithRetry(
      () => service.put(url, data, axiosConfig),
      { retries, retryDelay, retryCondition }
    )
  },
  
  patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig & RetryConfig): Promise<T> {
    const { retries, retryDelay, retryCondition, ...axiosConfig } = config || {}
    return requestWithRetry(
      () => service.patch(url, data, axiosConfig),
      { retries, retryDelay, retryCondition }
    )
  },
  
  delete<T = any>(url: string, config?: AxiosRequestConfig & RetryConfig): Promise<T> {
    const { retries, retryDelay, retryCondition, ...axiosConfig } = config || {}
    return requestWithRetry(
      () => service.delete(url, axiosConfig),
      { retries, retryDelay, retryCondition }
    )
  },
  
  upload<T = any>(url: string, formData: FormData, config?: AxiosRequestConfig & RetryConfig): Promise<T> {
    const { retries, retryDelay, retryCondition, ...axiosConfig } = config || {}
    return requestWithRetry(
      () => service.post(url, formData, {
        ...axiosConfig,
        headers: {
          'Content-Type': 'multipart/form-data',
          ...axiosConfig?.headers
        }
      }),
      { retries, retryDelay, retryCondition }
    )
  },
  
  download(url: string, config?: AxiosRequestConfig & RetryConfig): Promise<Blob> {
    const { retries, retryDelay, retryCondition, ...axiosConfig } = config || {}
    return requestWithRetry(
      () => service.get(url, {
        ...axiosConfig,
        responseType: 'blob'
      }),
      { retries, retryDelay, retryCondition }
    )
  }
}

// 导出axios实例
export default service

// 兼容性导出
export const http = request