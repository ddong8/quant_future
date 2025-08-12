/**
 * 用户设置API接口
 */
import { request } from '@/utils/request'

export interface UserProfile {
  id: number
  username: string
  email: string
  full_name?: string
  phone?: string
  avatar?: string
  timezone?: string
  language?: string
  date_format?: string
  currency_display?: string
  created_at: string
  updated_at: string
  last_login_at?: string
}

export interface UserSettings {
  id: number
  user_id: number
  theme: string
  sidebar_collapsed: boolean
  auto_refresh: boolean
  refresh_interval: number
  default_chart_period: string
  show_advanced_features: boolean
  dashboard_layout?: Record<string, any>
  favorite_symbols?: string[]
  watchlists?: Array<Record<string, any>>
  quick_actions?: string[]
  chart_settings?: Record<string, any>
  created_at: string
  updated_at: string
}

export interface SecuritySettings {
  id: number
  user_id: number
  two_factor_enabled: boolean
  login_notifications: boolean
  session_timeout: number
  ip_whitelist: string[]
  allowed_devices: number
  created_at: string
  updated_at: string
}

export interface NotificationSettings {
  id: number
  user_id: number
  email_enabled: boolean
  sms_enabled: boolean
  push_enabled: boolean
  trade_notifications: string[]
  risk_notifications: string[]
  system_notifications: string[]
  notification_hours: Record<string, string>
  created_at: string
  updated_at: string
}

export interface LoginDevice {
  id: number
  user_id: number
  device_name: string
  device_type: string
  browser?: string
  os?: string
  ip_address: string
  location?: string
  is_current: boolean
  last_login_at: string
  created_at: string
}

export interface UserActivityLog {
  id: number
  user_id: number
  action: string
  description: string
  ip_address?: string
  user_agent?: string
  metadata?: Record<string, any>
  created_at: string
}

export interface PasswordChangeRequest {
  current_password: string
  new_password: string
}

export interface TwoFactorQRCode {
  qr_code_url: string
  secret_key: string
  backup_codes: string[]
}

// 获取用户个人资料
export const getUserProfile = (): Promise<UserProfile> => {
  return request.get('/v1/user-settings/profile')
}

// 更新用户个人资料
export const updateUserProfile = (profileData: Partial<UserProfile>): Promise<{ message: string; profile: UserProfile }> => {
  return request.put('/v1/user-settings/profile', profileData)
}

// 获取用户设置
export const getUserSettings = (): Promise<UserSettings> => {
  return request.get('/v1/user-settings/settings')
}

// 更新用户设置
export const updateUserSettings = (settingsData: Partial<UserSettings>): Promise<{ message: string; settings: UserSettings }> => {
  return request.put('/v1/user-settings/settings', settingsData)
}

// 获取安全设置
export const getSecuritySettings = (): Promise<SecuritySettings> => {
  return request.get('/v1/user-settings/security')
}

// 更新安全设置
export const updateSecuritySettings = (securityData: Partial<SecuritySettings>): Promise<{ message: string; settings: SecuritySettings }> => {
  return request.put('/v1/user-settings/security', securityData)
}

// 修改密码
export const changePassword = (passwordData: PasswordChangeRequest): Promise<{ message: string }> => {
  return request.post('/v1/user-settings/change-password', passwordData)
}

// 启用/关闭双因子认证
export const toggleTwoFactor = (enabled: boolean, verificationCode?: string): Promise<{ message: string; enabled: boolean }> => {
  return request.post('/v1/user-settings/two-factor/toggle', {
    enabled,
    verification_code: verificationCode
  })
}

// 获取双因子认证二维码
export const getTwoFactorQRCode = (): Promise<TwoFactorQRCode> => {
  return request.get('/v1/user-settings/two-factor/qr-code')
}

// 验证双因子认证码
export const verifyTwoFactorCode = (code: string): Promise<{ message: string; valid: boolean }> => {
  return request.post('/v1/user-settings/two-factor/verify', { code })
}

// 获取通知设置
export const getNotificationSettings = (): Promise<NotificationSettings> => {
  return request.get('/v1/user-settings/notifications')
}

// 更新通知设置
export const updateNotificationSettings = (notificationData: Partial<NotificationSettings>): Promise<{ message: string; settings: NotificationSettings }> => {
  return request.put('/v1/user-settings/notifications', notificationData)
}

// 获取登录设备列表
export const getLoginDevices = (): Promise<LoginDevice[]> => {
  return request.get('/v1/user-settings/devices')
}

// 移除登录设备
export const removeLoginDevice = (deviceId: number): Promise<{ message: string }> => {
  return request.delete(`/v1/user-settings/devices/${deviceId}`)
}

// 登出所有设备
export const logoutAllDevices = (): Promise<{ message: string }> => {
  return request.post('/v1/user-settings/devices/logout-all')
}

// 获取用户活动日志
export const getUserActivityLog = (limit: number = 50, skip: number = 0): Promise<{
  logs: UserActivityLog[]
  total_count: number
  page_info: {
    skip: number
    limit: number
    has_more: boolean
  }
}> => {
  return request.get('/v1/user-settings/activity-log', {
    params: { limit, skip }
  })
}

// 导出用户数据
export const exportUserData = (exportType: string = 'all'): Promise<{
  export_id: string
  status: string
  content?: string
  download_url?: string
  file_size?: number
  created_at: string
}> => {
  return request.post('/v1/user-settings/export-data', { export_type: exportType })
}

// 删除账户
export const deleteAccount = (password: string, reason?: string): Promise<{ message: string }> => {
  return request.delete('/v1/user-settings/account', {
    data: { password, reason }
  })
}

// 用户设置相关的工具函数

// 主题选项
export const ThemeOptions = [
  { label: '浅色主题', value: 'light' },
  { label: '深色主题', value: 'dark' },
  { label: '自动切换', value: 'auto' }
] as const

// 语言选项
export const LanguageOptions = [
  { label: '简体中文', value: 'zh-CN' },
  { label: 'English', value: 'en-US' },
  { label: '繁體中文', value: 'zh-TW' },
  { label: '日本語', value: 'ja-JP' }
] as const

// 时区选项
export const TimezoneOptions = [
  { label: '北京时间 (UTC+8)', value: 'Asia/Shanghai' },
  { label: '纽约时间 (UTC-5)', value: 'America/New_York' },
  { label: '伦敦时间 (UTC+0)', value: 'Europe/London' },
  { label: '东京时间 (UTC+9)', value: 'Asia/Tokyo' }
] as const

// 货币选项
export const CurrencyOptions = [
  { label: '美元 (USD)', value: 'USD' },
  { label: '人民币 (CNY)', value: 'CNY' },
  { label: '欧元 (EUR)', value: 'EUR' },
  { label: '日元 (JPY)', value: 'JPY' }
] as const

// 图表周期选项
export const ChartPeriodOptions = [
  { label: '1分钟', value: '1m' },
  { label: '5分钟', value: '5m' },
  { label: '15分钟', value: '15m' },
  { label: '1小时', value: '1h' },
  { label: '1天', value: '1d' },
  { label: '1周', value: '1w' },
  { label: '1月', value: '1M' }
] as const

// 通知类型选项
export const TradeNotificationOptions = [
  { label: '订单成交', value: 'order_filled' },
  { label: '持仓平仓', value: 'position_closed' },
  { label: '止损触发', value: 'stop_loss_triggered' },
  { label: '止盈触发', value: 'take_profit_triggered' },
  { label: '订单取消', value: 'order_cancelled' }
] as const

export const RiskNotificationOptions = [
  { label: '保证金不足', value: 'margin_call' },
  { label: '大额亏损', value: 'large_loss' },
  { label: '持仓限制', value: 'position_limit' },
  { label: '日亏损限制', value: 'daily_loss_limit' },
  { label: '风险等级变化', value: 'risk_level_change' }
] as const

export const SystemNotificationOptions = [
  { label: '系统维护', value: 'maintenance' },
  { label: '安全提醒', value: 'security_alert' },
  { label: '功能更新', value: 'feature_update' },
  { label: '账户状态变化', value: 'account_status_change' }
] as const

// 格式化设备信息
export const formatDeviceInfo = (device: LoginDevice): string => {
  const parts = []
  if (device.browser) parts.push(device.browser)
  if (device.os) parts.push(device.os)
  return parts.length > 0 ? parts.join(' on ') : device.device_name
}

// 格式化最后登录时间
export const formatLastLogin = (lastLogin: string): string => {
  const date = new Date(lastLogin)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / (1000 * 60))
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffMins < 1) return '刚刚'
  if (diffMins < 60) return `${diffMins}分钟前`
  if (diffHours < 24) return `${diffHours}小时前`
  if (diffDays < 7) return `${diffDays}天前`
  
  return date.toLocaleDateString('zh-CN')
}

// 验证密码强度
export const validatePasswordStrength = (password: string): {
  isValid: boolean
  score: number
  feedback: string[]
} => {
  const feedback: string[] = []
  let score = 0

  if (password.length < 8) {
    feedback.push('密码长度至少8位')
  } else {
    score += 1
  }

  if (!/[a-z]/.test(password)) {
    feedback.push('需要包含小写字母')
  } else {
    score += 1
  }

  if (!/[A-Z]/.test(password)) {
    feedback.push('需要包含大写字母')
  } else {
    score += 1
  }

  if (!/\d/.test(password)) {
    feedback.push('需要包含数字')
  } else {
    score += 1
  }

  if (!/[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/.test(password)) {
    feedback.push('需要包含特殊字符')
  } else {
    score += 1
  }

  return {
    isValid: score >= 4 && password.length >= 8,
    score,
    feedback
  }
}

// ==================== 设置管理增强功能 ====================

export interface SettingsCategory {
  id: number
  name: string
  display_name: string
  description?: string
  icon?: string
  sort_order: number
}

export interface SettingsItem {
  id: number
  category_id: number
  key: string
  name: string
  description?: string
  data_type: string
  default_value: any
  validation_rules: Record<string, any>
  options?: any[]
  display_type: string
  is_visible: boolean
  is_editable: boolean
  sort_order: number
  current_value?: any
}

export interface SettingsHistory {
  id: number
  settings_item_id: number
  action: string
  old_value: any
  new_value: any
  reason?: string
  source: string
  created_at: string
}

export interface SettingsTemplate {
  id: number
  name: string
  description?: string
  is_default: boolean
  usage_count: number
}

// 获取设置分类
export const getSettingsCategories = (): Promise<SettingsCategory[]> => {
  return request.get('/v1/user-settings/categories')
}

// 获取设置项
export const getSettingsItems = (categoryId?: number): Promise<SettingsItem[]> => {
  return request.get('/v1/user-settings/items', {
    params: categoryId ? { category_id: categoryId } : {}
  })
}

// 获取单个设置值
export const getSettingValue = (settingsItemId: number): Promise<{ value: any }> => {
  return request.get(`/v1/user-settings/values/${settingsItemId}`)
}

// 设置单个设置值
export const setSettingValue = (
  settingsItemId: number, 
  value: any, 
  reason?: string, 
  source?: string
): Promise<{
  message: string
  value: any
  version: number
  previous_value: any
}> => {
  return request.put(`/v1/user-settings/values/${settingsItemId}`, {
    value,
    reason,
    source
  })
}

// 批量更新设置
export const batchUpdateSettings = (
  settings: Record<string, any>, 
  reason?: string
): Promise<{
  message: string
  updated_count: number
  failed_items: string[]
}> => {
  return request.post('/v1/user-settings/batch-update', {
    settings,
    reason
  })
}

// 获取设置历史记录
export const getSettingsHistory = (
  settingsItemId?: number,
  limit: number = 50,
  skip: number = 0
): Promise<{
  history: SettingsHistory[]
  total_count: number
  page_info: {
    skip: number
    limit: number
    has_more: boolean
  }
}> => {
  return request.get('/v1/user-settings/history', {
    params: {
      settings_item_id: settingsItemId,
      limit,
      skip
    }
  })
}

// 回滚设置到指定版本
export const rollbackSetting = (
  settingsItemId: number,
  targetVersion: number,
  reason?: string
): Promise<{
  message: string
  value: any
  version: number
  previous_value: any
}> => {
  return request.post('/v1/user-settings/rollback', {
    settings_item_id: settingsItemId,
    target_version: targetVersion,
    reason
  })
}

// 获取设置模板
export const getSettingsTemplates = (): Promise<SettingsTemplate[]> => {
  return request.get('/v1/user-settings/templates')
}

// 应用设置模板
export const applySettingsTemplate = (
  templateId: number,
  reason?: string
): Promise<{
  message: string
  applied_count: number
  failed_items: string[]
  template_name: string
}> => {
  return request.post(`/v1/user-settings/templates/${templateId}/apply`, {
    reason
  })
}

// 导出用户设置
export const exportSettings = (): Promise<{
  user_id: number
  export_time: string
  settings_count: number
  settings_data: Record<string, any>
}> => {
  return request.get('/v1/user-settings/export')
}

// 导入用户设置
export const importSettings = (
  settingsData: Record<string, any>,
  reason?: string
): Promise<{
  message: string
  updated_count: number
  failed_items: string[]
}> => {
  return request.post('/v1/user-settings/import', {
    settings_data: settingsData,
    reason
  })
}

// 设置管理工具函数

// 根据数据类型获取默认的显示组件
export const getDisplayComponent = (item: SettingsItem): string => {
  if (item.display_type !== 'input') {
    return item.display_type
  }

  switch (item.data_type) {
    case 'boolean':
      return 'switch'
    case 'integer':
    case 'number':
      return 'number'
    case 'string':
      return item.options ? 'select' : 'input'
    case 'array':
      return 'multi-select'
    case 'object':
      return 'json-editor'
    default:
      return 'input'
  }
}

// 验证设置值
export const validateSettingValue = (item: SettingsItem, value: any): {
  isValid: boolean
  errors: string[]
} => {
  const errors: string[] = []

  // 基本数据类型检查
  switch (item.data_type) {
    case 'string':
      if (typeof value !== 'string') {
        errors.push('值必须是字符串类型')
      }
      break
    case 'integer':
      if (!Number.isInteger(value)) {
        errors.push('值必须是整数')
      }
      break
    case 'number':
      if (typeof value !== 'number') {
        errors.push('值必须是数字类型')
      }
      break
    case 'boolean':
      if (typeof value !== 'boolean') {
        errors.push('值必须是布尔类型')
      }
      break
    case 'array':
      if (!Array.isArray(value)) {
        errors.push('值必须是数组类型')
      }
      break
    case 'object':
      if (typeof value !== 'object' || Array.isArray(value)) {
        errors.push('值必须是对象类型')
      }
      break
  }

  // 验证规则检查
  if (item.validation_rules) {
    const rules = item.validation_rules

    // 字符串长度检查
    if (rules.min_length && typeof value === 'string') {
      if (value.length < rules.min_length) {
        errors.push(`长度不能少于${rules.min_length}个字符`)
      }
    }

    if (rules.max_length && typeof value === 'string') {
      if (value.length > rules.max_length) {
        errors.push(`长度不能超过${rules.max_length}个字符`)
      }
    }

    // 数值范围检查
    if (rules.min_value && typeof value === 'number') {
      if (value < rules.min_value) {
        errors.push(`值不能小于${rules.min_value}`)
      }
    }

    if (rules.max_value && typeof value === 'number') {
      if (value > rules.max_value) {
        errors.push(`值不能大于${rules.max_value}`)
      }
    }

    // 选项检查
    if (rules.allowed_values && Array.isArray(rules.allowed_values)) {
      if (!rules.allowed_values.includes(value)) {
        errors.push('值不在允许的选项中')
      }
    }

    // 正则表达式检查
    if (rules.pattern && typeof value === 'string') {
      const regex = new RegExp(rules.pattern)
      if (!regex.test(value)) {
        errors.push(rules.pattern_message || '值格式不正确')
      }
    }
  }

  return {
    isValid: errors.length === 0,
    errors
  }
}

// 格式化设置值用于显示
export const formatSettingValue = (item: SettingsItem, value: any): string => {
  if (value === null || value === undefined) {
    return '未设置'
  }

  switch (item.data_type) {
    case 'boolean':
      return value ? '是' : '否'
    case 'array':
      return Array.isArray(value) ? `${value.length}项` : '无效数组'
    case 'object':
      return typeof value === 'object' ? 'JSON对象' : '无效对象'
    case 'string':
      // 如果有选项，显示选项标签
      if (item.options && Array.isArray(item.options)) {
        const option = item.options.find(opt => opt.value === value)
        return option ? option.label : value
      }
      return value
    default:
      return String(value)
  }
}

// 获取设置项的图标
export const getSettingIcon = (item: SettingsItem): string => {
  const iconMap: Record<string, string> = {
    theme: 'palette',
    language: 'translate',
    timezone: 'clock',
    currency: 'dollar-sign',
    notifications: 'bell',
    security: 'shield',
    privacy: 'lock',
    trading: 'trending-up',
    chart: 'bar-chart',
    display: 'monitor',
    sound: 'volume-2',
    animation: 'zap'
  }

  // 根据设置键匹配图标
  for (const [keyword, icon] of Object.entries(iconMap)) {
    if (item.key.toLowerCase().includes(keyword)) {
      return icon
    }
  }

  // 根据数据类型返回默认图标
  switch (item.data_type) {
    case 'boolean':
      return 'toggle-left'
    case 'number':
    case 'integer':
      return 'hash'
    case 'string':
      return 'type'
    case 'array':
      return 'list'
    case 'object':
      return 'code'
    default:
      return 'settings'
  }
}