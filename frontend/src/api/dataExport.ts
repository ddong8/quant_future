/**
 * 数据导出API
 */
import { request } from '@/utils/request'

export interface DataExportRequest {
  export_type: 'orders' | 'positions' | 'transactions' | 'strategies' | 'backtests' | 'risk_reports' | 'system_logs' | 'user_data' | 'full_backup'
  format: 'csv' | 'excel' | 'json' | 'pdf'
  start_date?: string
  end_date?: string
  filters?: Record<string, any>
  include_fields?: string[]
  exclude_fields?: string[]
  compress?: boolean
  password_protect?: boolean
  password?: string
}

export interface DataExportTask {
  id: number
  user_id: number
  export_type: string
  format: string
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled'
  progress: number
  file_path?: string
  file_size?: number
  download_url?: string
  error_message?: string
  created_at: string
  started_at?: string
  completed_at?: string
  expires_at?: string
}

export interface SystemBackupRequest {
  include_user_data?: boolean
  include_system_logs?: boolean
  include_market_data?: boolean
  compress?: boolean
  encrypt?: boolean
  password?: string
}

export interface SystemBackupInfo {
  id: number
  backup_type: string
  file_path: string
  file_size: number
  created_at: string
  expires_at?: string
  checksum: string
}

export interface SystemLogQuery {
  start_date?: string
  end_date?: string
  level?: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL'
  module?: string
  user_id?: number
  message_contains?: string
  limit?: number
  offset?: number
}

export interface SystemLogEntry {
  id: number
  timestamp: string
  level: string
  module: string
  message: string
  user_id?: number
  ip_address?: string
  user_agent?: string
  request_id?: string
  extra_data?: Record<string, any>
}

export interface SystemMetrics {
  cpu_usage: number
  memory_usage: number
  disk_usage: number
  active_connections: number
  request_count: number
  error_count: number
  response_time_avg: number
  timestamp: string
}

export interface PerformanceReport {
  report_id: string
  generated_at: string
  time_range: {
    start: string
    end: string
  }
  metrics: SystemMetrics
  slow_queries: Array<{
    query: string
    duration: number
    count: number
    avg_duration: number
  }>
  error_summary: Record<string, number>
  recommendations: string[]
  charts_data: Record<string, any>
}

export interface DataIntegrityCheck {
  check_id: string
  started_at: string
  completed_at?: string
  status: string
  total_tables: number
  checked_tables: number
  issues_found: number
  issues: Array<{
    table?: string
    type: string
    count?: number
    description: string
  }>
  recommendations: string[]
}

export interface StorageUsage {
  disk_total: number
  disk_used: number
  disk_free: number
  disk_percent: number
  database_size: number
  upload_files_size: number
  timestamp: string
}

export interface SystemInfo {
  platform: string
  python_version: string
  cpu_count: number
  memory_total: number
  boot_time: string
  application_version: string
  database_url: string
  redis_url: string
  environment: string
  database_stats: Record<string, number>
}

// 数据导出相关API
export const dataExportApi = {
  // 创建导出任务
  createExportTask: (data: DataExportRequest): Promise<DataExportTask> => {
    return request.post('/data-export/export', data)
  },

  // 获取导出任务列表
  getExportTasks: (params?: { skip?: number; limit?: number }): Promise<DataExportTask[]> => {
    return request.get('/data-export/export/tasks', { params })
  },

  // 获取导出任务详情
  getExportTask: (taskId: number): Promise<DataExportTask> => {
    return request.get(`/data-export/export/tasks/${taskId}`)
  },

  // 取消导出任务
  cancelExportTask: (taskId: number): Promise<{ message: string }> => {
    return request.post(`/data-export/export/tasks/${taskId}/cancel`)
  },

  // 下载导出文件
  downloadExportFile: (taskId: number): string => {
    return `/v1/data-export/export/download/${taskId}`
  },

  // 创建系统备份
  createSystemBackup: (data: SystemBackupRequest): Promise<SystemBackupInfo> => {
    return request.post('/data-export/backup', data)
  },

  // 获取系统日志
  getSystemLogs: (params: SystemLogQuery): Promise<SystemLogEntry[]> => {
    return request.get('/data-export/logs', { params })
  },

  // 获取系统指标
  getSystemMetrics: (): Promise<SystemMetrics> => {
    return request.get('/data-export/metrics')
  },

  // 生成性能报告
  generatePerformanceReport: (startDate: string, endDate: string): Promise<PerformanceReport> => {
    return request.get('/data-export/performance-report', {
      params: { start_date: startDate, end_date: endDate }
    })
  },

  // 检查数据完整性
  checkDataIntegrity: (): Promise<DataIntegrityCheck> => {
    return request.post('/data-export/integrity-check')
  },

  // 获取存储使用情况
  getStorageUsage: (): Promise<StorageUsage> => {
    return request.get('/data-export/storage-usage')
  },

  // 清理过期导出文件
  cleanupExpiredExports: (): Promise<{
    cleaned_files: number
    freed_space_bytes: number
    freed_space_mb: number
  }> => {
    return request.delete('/data-export/cleanup/expired-exports')
  },

  // 获取系统信息
  getSystemInfo: (): Promise<SystemInfo> => {
    return request.get('/data-export/system-info')
  }
}

export default dataExportApi