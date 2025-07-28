import { http } from '@/utils/request'
import type { 
  LoginRequest, 
  LoginResponse, 
  RegisterRequest, 
  User,
  RefreshTokenResponse 
} from '@/types/auth'

export const authApi = {
  // 登录
  login: (data: LoginRequest) => {
    return http.post<LoginResponse>('/auth/login', data)
  },

  // 注册
  register: (data: RegisterRequest) => {
    return http.post<{ message: string }>('/auth/register', data)
  },

  // 登出
  logout: () => {
    return http.post('/auth/logout')
  },

  // 获取当前用户信息
  getCurrentUser: () => {
    return http.get<User>('/auth/me')
  },

  // 刷新token
  refreshToken: (refreshToken: string) => {
    return http.post<RefreshTokenResponse>('/auth/refresh', {
      refresh_token: refreshToken
    })
  },

  // 修改密码
  changePassword: (data: {
    old_password: string
    new_password: string
  }) => {
    return http.post('/auth/change-password', data)
  },

  // 重置密码
  resetPassword: (data: {
    email: string
  }) => {
    return http.post('/auth/reset-password', data)
  }
}