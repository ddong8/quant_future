/**
 * 格式化工具函数
 */

/**
 * 格式化数字
 */
export function formatNumber(value: number | string | null | undefined, precision = 2): string {
  if (value === null || value === undefined || value === '') {
    return '0'
  }
  
  const num = typeof value === 'string' ? parseFloat(value) : value
  if (isNaN(num)) {
    return '0'
  }
  
  return num.toLocaleString('zh-CN', {
    minimumFractionDigits: 0,
    maximumFractionDigits: precision
  })
}

/**
 * 格式化价格
 */
export function formatPrice(value: number | string | null | undefined, precision = 2): string {
  if (value === null || value === undefined || value === '') {
    return '0.00'
  }
  
  const num = typeof value === 'string' ? parseFloat(value) : value
  if (isNaN(num)) {
    return '0.00'
  }
  
  return num.toLocaleString('zh-CN', {
    minimumFractionDigits: precision,
    maximumFractionDigits: precision
  })
}

/**
 * 格式化百分比
 */
export function formatPercent(value: number | string | null | undefined, precision = 2): string {
  if (value === null || value === undefined || value === '') {
    return '0.00%'
  }
  
  const num = typeof value === 'string' ? parseFloat(value) : value
  if (isNaN(num)) {
    return '0.00%'
  }
  
  return (num * 100).toLocaleString('zh-CN', {
    minimumFractionDigits: precision,
    maximumFractionDigits: precision
  }) + '%'
}

/**
 * 格式化日期时间
 */
export function formatDateTime(value: string | Date | null | undefined, format = 'YYYY-MM-DD HH:mm:ss'): string {
  if (!value) {
    return '-'
  }
  
  const date = typeof value === 'string' ? new Date(value) : value
  if (isNaN(date.getTime())) {
    return '-'
  }
  
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')
  
  switch (format) {
    case 'YYYY-MM-DD':
      return `${year}-${month}-${day}`
    case 'HH:mm:ss':
      return `${hours}:${minutes}:${seconds}`
    case 'MM-DD HH:mm':
      return `${month}-${day} ${hours}:${minutes}`
    case 'YYYY-MM-DD HH:mm:ss':
    default:
      return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
  }
}

/**
 * 格式化日期
 */
export function formatDate(value: string | Date | null | undefined): string {
  return formatDateTime(value, 'YYYY-MM-DD')
}

/**
 * 格式化时间
 */
export function formatTime(value: string | Date | null | undefined): string {
  return formatDateTime(value, 'HH:mm:ss')
}

/**
 * 格式化文件大小
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

/**
 * 格式化持续时间
 */
export function formatDuration(seconds: number): string {
  if (seconds < 60) {
    return `${Math.round(seconds)}秒`
  } else if (seconds < 3600) {
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = Math.round(seconds % 60)
    return remainingSeconds > 0 ? `${minutes}分${remainingSeconds}秒` : `${minutes}分`
  } else if (seconds < 86400) {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    return minutes > 0 ? `${hours}小时${minutes}分` : `${hours}小时`
  } else {
    const days = Math.floor(seconds / 86400)
    const hours = Math.floor((seconds % 86400) / 3600)
    return hours > 0 ? `${days}天${hours}小时` : `${days}天`
  }
}

/**
 * 格式化相对时间
 */
export function formatRelativeTime(value: string | Date | null | undefined): string {
  if (!value) {
    return '-'
  }
  
  const date = typeof value === 'string' ? new Date(value) : value
  if (isNaN(date.getTime())) {
    return '-'
  }
  
  const now = new Date()
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000)
  
  if (diffInSeconds < 60) {
    return '刚刚'
  } else if (diffInSeconds < 3600) {
    const minutes = Math.floor(diffInSeconds / 60)
    return `${minutes}分钟前`
  } else if (diffInSeconds < 86400) {
    const hours = Math.floor(diffInSeconds / 3600)
    return `${hours}小时前`
  } else if (diffInSeconds < 2592000) {
    const days = Math.floor(diffInSeconds / 86400)
    return `${days}天前`
  } else {
    return formatDate(date)
  }
}

/**
 * 截断文本
 */
export function truncateText(text: string, maxLength: number, suffix = '...'): string {
  if (!text || text.length <= maxLength) {
    return text || ''
  }
  
  return text.substring(0, maxLength - suffix.length) + suffix
}

/**
 * 格式化货币
 */
export function formatCurrency(value: number | string | null | undefined, currency = '¥', precision = 2): string {
  if (value === null || value === undefined || value === '') {
    return `${currency}0.00`
  }
  
  const num = typeof value === 'string' ? parseFloat(value) : value
  if (isNaN(num)) {
    return `${currency}0.00`
  }
  
  const formatted = num.toLocaleString('zh-CN', {
    minimumFractionDigits: precision,
    maximumFractionDigits: precision
  })
  
  return `${currency}${formatted}`
}

/**
 * 格式化变化量
 */
export function formatChange(value: number | string | null | undefined, precision = 2): {
  text: string
  type: 'up' | 'down' | 'neutral'
} {
  if (value === null || value === undefined || value === '') {
    return { text: '0.00', type: 'neutral' }
  }
  
  const num = typeof value === 'string' ? parseFloat(value) : value
  if (isNaN(num)) {
    return { text: '0.00', type: 'neutral' }
  }
  
  const formatted = Math.abs(num).toLocaleString('zh-CN', {
    minimumFractionDigits: precision,
    maximumFractionDigits: precision
  })
  
  if (num > 0) {
    return { text: `+${formatted}`, type: 'up' }
  } else if (num < 0) {
    return { text: `-${formatted}`, type: 'down' }
  } else {
    return { text: formatted, type: 'neutral' }
  }
}

/**
 * 格式化成交量
 */
export function formatVolume(value: number | string | null | undefined): string {
  if (value === null || value === undefined || value === '') {
    return '0'
  }
  
  const num = typeof value === 'string' ? parseFloat(value) : value
  if (isNaN(num)) {
    return '0'
  }
  
  if (num >= 100000000) {
    return (num / 100000000).toFixed(2) + '亿'
  } else if (num >= 10000) {
    return (num / 10000).toFixed(2) + '万'
  } else {
    return num.toLocaleString('zh-CN')
  }
}

/**
 * 格式化金额（带单位）
 */
export function formatAmount(value: number | string | null | undefined, unit = '元'): string {
  const formatted = formatPrice(value)
  return `${formatted} ${unit}`
}

/**
 * 格式化盈亏
 */
export function formatPnL(value: number | string | null | undefined, showSign = true): {
  text: string
  type: 'profit' | 'loss' | 'neutral'
} {
  if (value === null || value === undefined || value === '') {
    return { text: '0.00', type: 'neutral' }
  }
  
  const num = typeof value === 'string' ? parseFloat(value) : value
  if (isNaN(num)) {
    return { text: '0.00', type: 'neutral' }
  }
  
  const formatted = formatPrice(Math.abs(num))
  let text = formatted
  let type: 'profit' | 'loss' | 'neutral' = 'neutral'
  
  if (num > 0) {
    text = showSign ? `+${formatted}` : formatted
    type = 'profit'
  } else if (num < 0) {
    text = showSign ? `-${formatted}` : formatted
    type = 'loss'
  }
  
  return { text, type }
}

/**
 * 格式化盈亏百分比
 */
export function formatPnLPercent(value: number | string | null | undefined, showSign = true): {
  text: string
  type: 'profit' | 'loss' | 'neutral'
} {
  if (value === null || value === undefined || value === '') {
    return { text: '0.00%', type: 'neutral' }
  }
  
  const num = typeof value === 'string' ? parseFloat(value) : value
  if (isNaN(num)) {
    return { text: '0.00%', type: 'neutral' }
  }
  
  const formatted = formatPercent(Math.abs(num))
  let text = formatted
  let type: 'profit' | 'loss' | 'neutral' = 'neutral'
  
  if (num > 0) {
    text = showSign ? `+${formatted}` : formatted
    type = 'profit'
  } else if (num < 0) {
    text = showSign ? `-${formatted}` : formatted
    type = 'loss'
  }
  
  return { text, type }
}