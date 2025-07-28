import { http } from '@/utils/request'
import type {
  Backtest,
  CreateBacktestRequest,
  UpdateBacktestRequest,
  BacktestResult,
  BacktestProgress,
  BacktestTemplate,
  BacktestComparison,
  BacktestOptimization,
  BacktestReport,
  HistoricalDataInfo,
  BacktestListResponse,
  BacktestResponse,
  BacktestResultResponse,
  BacktestProgressResponse,
  BacktestTemplatesResponse,
  HistoricalDataResponse,
  BacktestReportsResponse
} from '@/types/backtest'

export const backtestApi = {
  // 回测管理
  getBacktests: (params?: {
    page?: number
    page_size?: number
    strategy_id?: number
    status?: string
    start_date?: string
    end_date?: string
    search?: string
  }) => {
    return http.get<BacktestListResponse>('/backtests', { params })
  },

  getBacktest: (id: number) => {
    return http.get<BacktestResponse>(`/backtests/${id}`)
  },

  createBacktest: (data: CreateBacktestRequest) => {
    return http.post<BacktestResponse>('/backtests', data)
  },

  updateBacktest: (id: number, data: UpdateBacktestRequest) => {
    return http.put<BacktestResponse>(`/backtests/${id}`, data)
  },

  deleteBacktest: (id: number) => {
    return http.delete(`/backtests/${id}`)
  },

  cloneBacktest: (id: number, name: string) => {
    return http.post<BacktestResponse>(`/backtests/${id}/clone`, { name })
  },

  // 回测执行控制
  startBacktest: (id: number) => {
    return http.post(`/backtests/${id}/start`)
  },

  stopBacktest: (id: number) => {
    return http.post(`/backtests/${id}/stop`)
  },

  pauseBacktest: (id: number) => {
    return http.post(`/backtests/${id}/pause`)
  },

  resumeBacktest: (id: number) => {
    return http.post(`/backtests/${id}/resume`)
  },

  // 回测结果
  getBacktestResult: (id: number) => {
    return http.get<BacktestResultResponse>(`/backtests/${id}/result`)
  },

  getBacktestProgress: (id: number) => {
    return http.get<BacktestProgressResponse>(`/backtests/${id}/progress`)
  },

  // 回测模板
  getBacktestTemplates: (params?: {
    category?: string
    search?: string
  }) => {
    return http.get<BacktestTemplatesResponse>('/backtests/templates', { params })
  },

  getBacktestTemplate: (id: number) => {
    return http.get<{ template: BacktestTemplate }>(`/backtests/templates/${id}`)
  },

  createFromTemplate: (templateId: number, data: {
    name: string
    description?: string
    strategy_id: number
    config_overrides?: any
  }) => {
    return http.post<BacktestResponse>(`/backtests/templates/${templateId}/create`, data)
  },

  saveAsTemplate: (backtestId: number, data: {
    name: string
    description?: string
    is_public: boolean
  }) => {
    return http.post<{ template: BacktestTemplate }>(`/backtests/${backtestId}/save-template`, data)
  },

  // 历史数据
  getHistoricalDataInfo: (params: {
    symbols: string[]
    start_date: string
    end_date: string
    frequency: string
  }) => {
    return http.get<HistoricalDataResponse>('/backtests/historical-data-info', { params })
  },

  validateHistoricalData: (params: {
    symbols: string[]
    start_date: string
    end_date: string
    frequency: string
  }) => {
    return http.post('/backtests/validate-historical-data', params)
  },

  // 回测比较
  compareBacktests: (backtestIds: number[], params?: {
    metrics?: string[]
    benchmark?: string
  }) => {
    return http.post<{ comparison: BacktestComparison }>('/backtests/compare', {
      backtest_ids: backtestIds,
      ...params
    })
  },

  // 回测优化
  createOptimization: (backtestId: number, data: {
    parameter_ranges: Record<string, { min: number; max: number; step: number }>
    optimization_target: string
    optimization_method: string
    max_iterations: number
  }) => {
    return http.post<{ optimization: BacktestOptimization }>(`/backtests/${backtestId}/optimize`, data)
  },

  getOptimization: (optimizationId: number) => {
    return http.get<{ optimization: BacktestOptimization }>(`/backtests/optimizations/${optimizationId}`)
  },

  getOptimizations: (backtestId: number) => {
    return http.get<{ optimizations: BacktestOptimization[] }>(`/backtests/${backtestId}/optimizations`)
  },

  // 回测报告
  generateReport: (backtestId: number, data: {
    report_type: string
    format: string
    include_charts: boolean
    include_trades: boolean
  }) => {
    return http.post<{ report: BacktestReport }>(`/backtests/${backtestId}/reports`, data)
  },

  getReports: (backtestId: number) => {
    return http.get<BacktestReportsResponse>(`/backtests/${backtestId}/reports`)
  },

  downloadReport: (reportId: number) => {
    return http.get(`/backtests/reports/${reportId}/download`, {
      responseType: 'blob'
    })
  },

  deleteReport: (reportId: number) => {
    return http.delete(`/backtests/reports/${reportId}`)
  },

  // 回测统计
  getBacktestStats: (params?: {
    strategy_id?: number
    start_date?: string
    end_date?: string
  }) => {
    return http.get('/backtests/stats', { params })
  },

  // 回测任务
  getBacktestTasks: (backtestId: number) => {
    return http.get(`/backtests/${backtestId}/tasks`)
  },

  retryFailedTask: (taskId: number) => {
    return http.post(`/backtests/tasks/${taskId}/retry`)
  },

  // 回测数据导出
  exportBacktestData: (backtestId: number, data: {
    data_type: 'equity_curve' | 'trades' | 'positions' | 'all'
    format: 'csv' | 'excel' | 'json'
  }) => {
    return http.post(`/backtests/${backtestId}/export`, data, {
      responseType: 'blob'
    })
  },

  // 回测配置验证
  validateBacktestConfig: (config: any) => {
    return http.post('/backtests/validate-config', { config })
  },

  // 获取可用基准
  getAvailableBenchmarks: () => {
    return http.get<{ benchmarks: Array<{ symbol: string; name: string; description: string }> }>('/backtests/benchmarks')
  },

  // 获取交易日历
  getTradingCalendar: (params: {
    start_date: string
    end_date: string
    exchange?: string
  }) => {
    return http.get('/backtests/trading-calendar', { params })
  },

  // 回测性能分析
  getPerformanceAnalysis: (backtestId: number, params?: {
    analysis_type?: 'returns' | 'risk' | 'attribution' | 'all'
    period?: 'daily' | 'weekly' | 'monthly'
  }) => {
    return http.get(`/backtests/${backtestId}/performance-analysis`, { params })
  },

  // 回测风险分析
  getRiskAnalysis: (backtestId: number, params?: {
    confidence_level?: number
    lookback_period?: number
  }) => {
    return http.get(`/backtests/${backtestId}/risk-analysis`, { params })
  }
}