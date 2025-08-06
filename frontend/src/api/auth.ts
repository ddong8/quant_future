import { http } from '@/utils/request'
import type { 
  LoginRequest, 
  LoginResponse, 
  RegisterRequest, 
  User,
  RefreshTokenResponse,
  ApiResponse
} from '@/types/auth'

export const authApi = {
  // 登录
  login: (data: LoginRequest) => {
    return http.post<LoginResponse>('/v1/auth/login', data)
  },

  // 注册
  register: (data: RegisterRequest) => {
    return http.post<ApiResponse<any>>('/v1/auth/register', data)
  },

  // 登出
  logout: () => {
    return http.post('/v1/auth/logout')
  },

  // 获取当前用户信息
  getCurrentUser: () => {
    return http.get<ApiResponse<User>>('/v1/auth/me')
  },

  // 刷新token
  refreshToken: (refreshToken: string) => {
    return http.post<RefreshTokenResponse>('/v1/auth/refresh', {
      refresh_token: refreshToken
    })
  },

  // 修改密码
  changePassword: (data: {
    old_password: string
    new_password: string
  }) => {
    return http.post('/v1/auth/change-password', data)
  },

  // 重置密码
  resetPassword: (data: {
    email: string
  }) => {
    return http.post('/v1/auth/reset-password', data)
  }
}