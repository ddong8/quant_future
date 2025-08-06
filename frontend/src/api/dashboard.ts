import { http } from '@/utils/request'
import type { ApiResponse } from '@/types/auth'

export interface DashboardSummaryData {
  user: {
    id: number
    username: string
    role: string
  }
  stats: {
    total_strategies: number
    active_positions: number
    total_orders: number
    account_balance: number
  }
  recent_activities: any[]
  market_status: string
  notifications: any[]
}

export interface UserProfileData {
  id: number
  username: string
  email: string
  full_name: string
  phone: string | null
  avatar_url: string | null
  role: string
  is_active: boolean
  is_verified: boolean
  created_at: string
  last_login_at: string | null
}

// 统一响应格式的类型
export interface DashboardSummary extends ApiResponse<DashboardSummaryData> {}
export interface UserProfile extends ApiResponse<UserProfileData> {}

export const dashboardApi = {
  // 获取仪表板摘要
  getSummary: () => {
    return http.get<DashboardSummary>('/v1/dashboard/summary')
  },

  // 获取用户资料
  getUserProfile: () => {
    return http.get<UserProfile>('/v1/user/profile')
  }
}