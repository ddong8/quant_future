/**
 * 通知管理API接口
 */
import { request } from '@/utils/request'

export enum NotificationType {
  TRADE = 'trade',
  RISK = 'risk',
  SYSTEM = 'system',
  MARKET = 'market',
  ACCOUNT = 'account',
  SECURITY = 'security'
}

export enum NotificationChannel {
  IN_APP = 'in_app',
  EMAIL = 'email',
  SMS = 'sms',
  PUSH = 'push',
  WEBHOOK = 'webhook'
}

export enum NotificationPriority {
  LOW = 'low',
  NORMAL = 'normal',
  HIGH = 'high',
  URGENT = 'urgent'
}

export enum NotificationStatus {
  PENDING = 'pending',
  SENT = 'sent',
  DELIVERED = 'delivered',
  READ = 'read',
  FAILED = 'failed',
  CANCELLED = 'cancelled'
}

export interface Notification {
  id: number
  user_id: number
  template_id?: number
  type: NotificationType
  title: string
  content: string
  channel: NotificationChannel
  priority: NotificationPriority
  status: NotificationStatus
  recipient?: string
  sent_at?: string
  delivered_at?: string
  read_at?: string
  error_message?: string
  retry_count: number
  metadata?: Record<string, any>
  expires_at?: string
  created_at: string
  updated_at: string
}

export interface NotificationTemplate {
  id: number
  name: string
  code: string
  type: NotificationType
  title_template: string
  content_template: string
  channels: NotificationChannel[]
  variables: Record<string, any>
  default_priority: NotificationPriority
  created_at: string
  updated_at: string
}

export interface NotificationPreference {
  id: number
  user_id: number
  enabled: boolean
  quiet_hours_enabled: boolean
  quiet_hours_start: string
  quiet_hours_end: string
  email_enabled: boolean
  sms_enabled: boolean
  push_enabled: boolean
  in_app_enabled: boolean
  trade_notifications: Record<string, boolean>
  risk_notifications: Record<string, boolean>
  system_notifications: Record<string, boolean>
  market_notifications: Record<string, boolean>
  account_notifications: Record<string, boolean>
  security_notifications: Record<string, boolean>
  max_notifications_per_hour: number
  digest_enabled: boolean
  digest_frequency: string
  digest_time: string
  created_at: string
  updated_at: string
}

export interface NotificationRule {
  id: number
  user_id: number
  name: string
  description?: string
  event_type: string
  conditions: Record<string, any>
  template_code?: string
  channels: NotificationChannel[]
  priority: NotificationPriority
  rate_limit?: number
  max_per_day?: number
  is_active: boolean
  trigger_count: number
  last_triggered_at?: string
  created_at: string
  updated_at: string
}

export interface NotificationStats {
  total_notifications: number
  unread_notifications: number
  notifications_by_type: Record<string, number>
  notifications_by_channel: Record<string, number>
  notifications_by_status: Record<string, number>
  recent_notifications: Notification[]
}

export interface CreateNotificationRequest {
  user_id: number
  template_id?: number
  type: NotificationType
  title: string
  content: string
  channel: NotificationChannel
  priority?: NotificationPriority
  recipient?: string
  metadata?: Record<string, any>
  variables?: Record<string, any>
  expires_at?: string
}

export interface BatchCreateNotificationRequest {
  user_ids: number[]
  template_code: string
  variables?: Record<string, any>
  channels: NotificationChannel[]
  priority?: NotificationPriority
  scheduled_at?: string
}

export interface NotificationSearchRequest {
  keyword?: string
  type?: NotificationType
  channel?: NotificationChannel
  status?: NotificationStatus
  priority?: NotificationPriority
  date_from?: string
  date_to?: string
  page?: number
  page_size?: number
}

export interface NotificationSearchResponse {
  notifications: Notification[]
  total_count: number
  page: number
  page_size: number
  total_pages: number
}

// ==================== 通知消息管理 ====================

// 获取用户通知列表
export const getUserNotifications = (params: {
  limit?: number
  skip?: number
  unread_only?: boolean
}): Promise<{
  notifications: Notification[]
  total_count: number
  unread_count: number
  page_info: {
    skip: number
    limit: number
    has_more: boolean
  }
}> => {
  return request.get('/v1/notifications/', { params })
}

// 创建通知
export const createNotification = (data: CreateNotificationRequest): Promise<Notification> => {
  return request.post('/v1/notifications/', data)
}

// 批量创建通知
export const batchCreateNotifications = (data: BatchCreateNotificationRequest): Promise<{
  total_count: number
  success_count: number
  failed_count: number
  notification_ids: number[]
}> => {
  return request.post('/v1/notifications/batch', data)
}

// 搜索通知
export const searchNotifications = (data: NotificationSearchRequest): Promise<NotificationSearchResponse> => {
  return request.post('/v1/notifications/search', data)
}

// 标记通知为已读
export const markNotificationsRead = (notification_ids: number[]): Promise<{ message: string }> => {
  return request.post('/v1/notifications/mark-read', { notification_ids })
}

// 标记所有通知为已读
export const markAllNotificationsRead = (): Promise<{ message: string }> => {
  return request.post('/v1/notifications/mark-all-read')
}

// 批量删除通知
export const deleteNotifications = (notification_ids: number[], delete_type: 'soft' | 'hard' = 'soft'): Promise<{ message: string }> => {
  return request.delete('/v1/notifications/', {
    data: { notification_ids, delete_type }
  })
}

// 删除所有通知
export const deleteAllNotifications = (delete_type: 'soft' | 'hard' = 'soft'): Promise<{ message: string }> => {
  return request.delete('/v1/notifications/all', {
    params: { delete_type }
  })
}

// ==================== 通知偏好管理 ====================

// 获取通知偏好设置
export const getNotificationPreferences = (): Promise<NotificationPreference> => {
  return request.get('/v1/notifications/preferences')
}

// 更新通知偏好设置
export const updateNotificationPreferences = (data: Partial<NotificationPreference>): Promise<NotificationPreference> => {
  return request.put('/v1/notifications/preferences', data)
}

// ==================== 通知规则管理 ====================

// 创建通知规则
export const createNotificationRule = (data: Omit<NotificationRule, 'id' | 'user_id' | 'trigger_count' | 'last_triggered_at' | 'created_at' | 'updated_at'>): Promise<NotificationRule> => {
  return request.post('/v1/notifications/rules', data)
}

// 获取通知规则列表
export const getNotificationRules = (): Promise<NotificationRule[]> => {
  return request.get('/v1/notifications/rules')
}

// 更新通知规则
export const updateNotificationRule = (rule_id: number, data: Partial<NotificationRule>): Promise<NotificationRule> => {
  return request.put(`/v1/notifications/rules/${rule_id}`, data)
}

// 删除通知规则
export const deleteNotificationRule = (rule_id: number): Promise<{ message: string }> => {
  return request.delete(`/v1/notifications/rules/${rule_id}`)
}

// ==================== 通知模板管理 ====================

// 获取通知模板列表
export const getNotificationTemplates = (type_filter?: NotificationType): Promise<NotificationTemplate[]> => {
  return request.get('/v1/notifications/templates', {
    params: type_filter ? { type_filter } : {}
  })
}

// 获取通知模板详情
export const getNotificationTemplate = (template_code: string): Promise<NotificationTemplate> => {
  return request.get(`/v1/notifications/templates/${template_code}`)
}

// 测试通知模板
export const testNotificationTemplate = (data: {
  template_code: string
  channel: NotificationChannel
  variables?: Record<string, any>
  recipient?: string
}): Promise<any> => {
  return request.post('/v1/notifications/templates/test', data)
}

// ==================== 通知统计 ====================

// 获取通知统计
export const getNotificationStats = (days: number = 30): Promise<NotificationStats> => {
  return request.get('/v1/notifications/stats', {
    params: { days }
  })
}

// 获取未读通知数量
export const getUnreadCount = (): Promise<{ unread_count: number }> => {
  return request.get('/v1/notifications/unread-count')
}

// ==================== 通知导出 ====================

// 导出通知数据
export const exportNotifications = (data: {
  export_type?: string
  filters?: NotificationSearchRequest
  format?: string
  include_content?: boolean
}): Promise<{
  export_id: string
  status: string
  download_url?: string
  file_size?: number
  expires_at?: string
  created_at: string
}> => {
  return request.post('/v1/notifications/export', data)
}

// ==================== 工具函数 ====================

// 通知类型显示名称
export const getNotificationTypeLabel = (type: NotificationType): string => {
  const labels = {
    [NotificationType.TRADE]: '交易通知',
    [NotificationType.RISK]: '风险通知',
    [NotificationType.SYSTEM]: '系统通知',
    [NotificationType.MARKET]: '市场通知',
    [NotificationType.ACCOUNT]: '账户通知',
    [NotificationType.SECURITY]: '安全通知'
  }
  return labels[type] || type
}

// 通知渠道显示名称
export const getNotificationChannelLabel = (channel: NotificationChannel): string => {
  const labels = {
    [NotificationChannel.IN_APP]: '站内信',
    [NotificationChannel.EMAIL]: '邮件',
    [NotificationChannel.SMS]: '短信',
    [NotificationChannel.PUSH]: '推送',
    [NotificationChannel.WEBHOOK]: 'Webhook'
  }
  return labels[channel] || channel
}

// 通知优先级显示名称
export const getNotificationPriorityLabel = (priority: NotificationPriority): string => {
  const labels = {
    [NotificationPriority.LOW]: '低',
    [NotificationPriority.NORMAL]: '普通',
    [NotificationPriority.HIGH]: '高',
    [NotificationPriority.URGENT]: '紧急'
  }
  return labels[priority] || priority
}

// 通知状态显示名称
export const getNotificationStatusLabel = (status: NotificationStatus): string => {
  const labels = {
    [NotificationStatus.PENDING]: '待发送',
    [NotificationStatus.SENT]: '已发送',
    [NotificationStatus.DELIVERED]: '已送达',
    [NotificationStatus.READ]: '已读',
    [NotificationStatus.FAILED]: '发送失败',
    [NotificationStatus.CANCELLED]: '已取消'
  }
  return labels[status] || status
}

// 获取通知优先级颜色
export const getNotificationPriorityColor = (priority: NotificationPriority): string => {
  const colors = {
    [NotificationPriority.LOW]: '#909399',
    [NotificationPriority.NORMAL]: '#409eff',
    [NotificationPriority.HIGH]: '#e6a23c',
    [NotificationPriority.URGENT]: '#f56c6c'
  }
  return colors[priority] || colors[NotificationPriority.NORMAL]
}

// 获取通知状态颜色
export const getNotificationStatusColor = (status: NotificationStatus): string => {
  const colors = {
    [NotificationStatus.PENDING]: '#e6a23c',
    [NotificationStatus.SENT]: '#409eff',
    [NotificationStatus.DELIVERED]: '#67c23a',
    [NotificationStatus.READ]: '#909399',
    [NotificationStatus.FAILED]: '#f56c6c',
    [NotificationStatus.CANCELLED]: '#c0c4cc'
  }
  return colors[status] || colors[NotificationStatus.PENDING]
}

// 格式化通知时间
export const formatNotificationTime = (time: string): string => {
  const date = new Date(time)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / (1000 * 60))
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffMins < 1) return '刚刚'
  if (diffMins < 60) return `${diffMins}分钟前`
  if (diffHours < 24) return `${diffHours}小时前`
  if (diffDays < 7) return `${diffDays}天前`
  
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

// 检查通知是否已过期
export const isNotificationExpired = (notification: Notification): boolean => {
  if (!notification.expires_at) return false
  return new Date(notification.expires_at) < new Date()
}

// 检查通知是否未读
export const isNotificationUnread = (notification: Notification): boolean => {
  return !notification.read_at
}