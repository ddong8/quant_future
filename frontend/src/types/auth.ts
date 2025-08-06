// 用户信息
export interface User {
  id: number
  username: string
  email: string
  full_name?: string
  phone?: string
  avatar_url?: string
  role: 'admin' | 'trader' | 'viewer'
  is_active: boolean
  is_verified: boolean
  created_at: string
  updated_at: string
  last_login_at?: string
}

// 登录请求
export interface LoginRequest {
  username: string
  password: string
  remember_me?: boolean
}

// 登录响应数据
export interface LoginResponseData {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user_id: number
  username: string
  role: string
}

// 统一API响应格式
export interface ApiResponse<T = any> {
  success: boolean
  message: string
  timestamp: number
  request_id: string | null
  data: T
}

// 登录响应
export interface LoginResponse extends ApiResponse<LoginResponseData> {}

// 注册请求
export interface RegisterRequest {
  username: string
  email: string
  password: string
  confirm_password: string
  full_name?: string
  phone?: string
}

// 刷新token响应数据
export interface RefreshTokenResponseData {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

// 刷新token响应
export interface RefreshTokenResponse extends ApiResponse<RefreshTokenResponseData> {}

// 用户会话信息
export interface UserSession {
  id: number
  user_id: number
  session_token: string
  ip_address?: string
  user_agent?: string
  is_active: boolean
  created_at: string
  expires_at: string
  last_accessed_at: string
}