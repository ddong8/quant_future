import { http } from '@/utils/request'

export interface DashboardSummary {
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

export interface UserProfile {
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

export const dashboardApi = {
  // 获取仪表板摘要 - 使用兼容性路由
  getSummary: () => {
    return http.get<DashboardSummary>('/api/dashboard/summary')
  },

  // 获取用户资料 - 使用兼容性路由
  getUserProfile: () => {
    return http.get<UserProfile>('/api/user/profile')
  }
}