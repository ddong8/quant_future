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

// 登录响应
export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: User
}

// 注册请求
export interface RegisterRequest {
  username: string
  email: string
  password: string
  confirm_password: string
  full_name?: string
  phone?: string
}

// 刷新token响应
export interface RefreshTokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

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