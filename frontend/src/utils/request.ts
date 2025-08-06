import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import router from '@/router'

// 创建axios实例
const service: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
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
    const { response, message } = error
    
    if (response) {
      const { status, data } = response
      
      switch (status) {
        case 401:
          // 未授权，清除token并跳转到登录页
          const authStore = useAuthStore()
          authStore.logout()
          router.push('/login')
          ElMessage.error('登录已过期，请重新登录')
          break
          
        case 403:
          ElMessage.error('没有权限访问该资源')
          break
          
        case 404:
          ElMessage.error('请求的资源不存在')
          break
          
        case 422:
          // 表单验证错误
          if (data?.errors) {
            const errorMessages = Object.values(data.errors).flat()
            ElMessage.error(errorMessages.join(', '))
          } else {
            ElMessage.error(data?.message || '请求参数错误')
          }
          break
          
        case 429:
          ElMessage.error('请求过于频繁，请稍后再试')
          break
          
        case 500:
          ElMessage.error('服务器内部错误')
          break
          
        default:
          ElMessage.error(data?.message || `请求失败 (${status})`)
      }
    } else if (message.includes('timeout')) {
      ElMessage.error('请求超时，请检查网络连接')
    } else if (message.includes('Network Error')) {
      ElMessage.error('网络连接失败，请检查网络')
    } else {
      ElMessage.error('请求失败，请稍后重试')
    }
    
    return Promise.reject(error)
  }
)

// 生成请求ID
function generateRequestId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
}

// 请求方法封装
export const request = {
  get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return service.get(url, config)
  },
  
  post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return service.post(url, data, config)
  },
  
  put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return service.put(url, data, config)
  },
  
  patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return service.patch(url, data, config)
  },
  
  delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return service.delete(url, config)
  },
  
  upload<T = any>(url: string, formData: FormData, config?: AxiosRequestConfig): Promise<T> {
    return service.post(url, formData, {
      ...config,
      headers: {
        'Content-Type': 'multipart/form-data',
        ...config?.headers
      }
    })
  },
  
  download(url: string, config?: AxiosRequestConfig): Promise<Blob> {
    return service.get(url, {
      ...config,
      responseType: 'blob'
    })
  }
}

// 导出axios实例
export default service

// 兼容性导出
export const http = request