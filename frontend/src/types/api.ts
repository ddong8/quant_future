/**
 * API 响应类型定义
 */

// 基础 API 响应类型
export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
  timestamp?: string
  request_id?: string
}

// 分页响应类型
export interface PaginatedResponse<T = any> {
  data: T[]
  meta: {
    total: number
    page: number
    page_size: number
    total_pages: number
    has_next: boolean
    has_prev: boolean
  }
}

// 错误响应类型
export interface ErrorResponse {
  code: number
  message: string
  errors?: Record<string, string[]>
  timestamp: string
  request_id: string
}

// 列表查询参数
export interface ListParams {
  page?: number
  page_size?: number
  sort?: string
  order?: 'asc' | 'desc'
  search?: string
}

// 日期范围参数
export interface DateRangeParams {
  start_date?: string
  end_date?: string
}

// 状态筛选参数
export interface StatusParams {
  status?: string | string[]
}

// 通用查询参数
export interface QueryParams extends ListParams, DateRangeParams, StatusParams {
  [key: string]: any
}

// WebSocket 消息类型
export interface WebSocketMessage<T = any> {
  type: string
  data: T
  timestamp: string
  channel?: string
}

// 文件上传响应
export interface UploadResponse {
  filename: string
  original_name: string
  size: number
  url: string
  mime_type: string
}

// 批量操作响应
export interface BatchResponse {
  success_count: number
  error_count: number
  errors: Array<{
    index: number
    message: string
  }>
}

// 统计数据类型
export interface StatsData {
  [key: string]: number | string
}

// 图表数据类型
export interface ChartData {
  labels: string[]
  datasets: Array<{
    label: string
    data: number[]
    backgroundColor?: string | string[]
    borderColor?: string | string[]
    [key: string]: any
  }>
}

// 导出任务状态
export interface ExportTask {
  id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress: number
  file_url?: string
  error_message?: string
  created_at: string
  completed_at?: string
}