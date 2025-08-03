/**
 * 回测管理API服务
 */

import { request } from '@/utils/request'
import type { ApiResponse, PaginatedResponse } from '@/types/api'

/**
 * 回测相关类型定义
 */
export interface BacktestConfig {
  name: string
  description?: string
  backtest_type: 'simple' | 'walk_forward' | 'monte_carlo' | 'cross_validation'
  strategy_id: number
  strategy_version_id?: number
  start_date: string
  end_date: string
  initial_capital: number
  benchmark?: string
  commission_rate: number
  slippage_rate: number
  min_commission: number
  max_position_size?: number
  stop_loss?: number
  take_profit?: number
  data_source: string
  symbols: string[]
  frequency: string
  tags: string[]
  is_public: boolean
  walk_forward_settings?: {
    training_period: number
    testing_period: number
    step_size: number
  }
  monte_carlo_settings?: {
    simulation_count: number
    confidence_level: number
    random_seed: number
  }
}

export interface Backtest {
  id: number
  uuid: string
  name: string
  description?: string
  backtest_type: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled' | 'paused'
  strategy_id: number
  strategy_version_id?: number
  start_date: string
  end_date: string
  initial_capital: number
  benchmark?: string
  commission_rate: number
  slippage_rate: number
  min_commission: number
  max_position_size?: number
  stop_loss?: number
  take_profit?: number
  data_source: string
  symbols: string[]
  frequency: string
  started_at?: string
  completed_at?: string
  progress: number
  total_return?: number
  annual_return?: number
  max_drawdown?: number
  sharpe_ratio?: number
  sortino_ratio?: number
  calmar_ratio?: number
  volatility?: number
  total_trades: number
  winning_trades: number
  losing_trades: number
  win_rate?: number
  avg_win?: number
  avg_loss?: number
  profit_factor?: number
  benchmark_return?: number
  alpha?: number
  beta?: number
  information_ratio?: number
  tracking_error?: number
  equity_curve?: any[]
  drawdown_curve?: any[]
  trades_detail?: any[]
  daily_returns?: any[]
  positions?: any[]
  error_message?: string
  config_snapshot?: any
  tags: string[]
  is_public: boolean
  user_id: number
  created_at: string
  updated_at: string
}

export interface BacktestTemplate {
  id: number
  uuid: string
  name: string
  description?: string
  category?: string
  config_template: any
  default_parameters: any
  usage_count: number
  rating: number
  tags: string[]
  is_official: boolean
  is_active: boolean
  author_id?: number
  created_at: string
  updated_at: string
}

export interface BacktestSearchParams {
  keyword?: string
  strategy_id?: number
  backtest_type?: string
  status?: string
  tags?: string[]
  is_public?: boolean
  start_date_from?: string
  start_date_to?: string
  created_after?: string
  created_before?: string
  sort_by?: string
  sort_order?: string
  page?: number
  page_size?: number
}

export interface BacktestStats {
  total_backtests: number
  completed_backtests: number
  running_backtests: number
  failed_backtests: number
  avg_return: number
  avg_sharpe_ratio: number
  avg_max_drawdown: number
  avg_win_rate: number
  total_trades: number
}

export interface BacktestExecutionRequest {
  action: 'start' | 'stop' | 'pause' | 'resume'
  parameters?: any
}

export interface BacktestExecutionResponse {
  backtest_id: number
  action: string
  success: boolean
  message: string
  execution_id?: string
  timestamp: string
}

/**
 * 回测API服务类
 */
export class BacktestApi {
  /**
   * 创建回测
   */
  static async createBacktest(data: BacktestConfig): Promise<ApiResponse<Backtest>> {
    return request.post('/backtests', data)
  }

  /**
   * 获取回测列表
   */
  static async getBacktests(params?: BacktestSearchParams): Promise<ApiResponse<PaginatedResponse<Backtest>>> {
    return request.get('/backtests', { params })
  }

  /**
   * 获取我的回测
   */
  static async getMyBacktests(limit: number = 10): Promise<ApiResponse<Backtest[]>> {
    return request.get('/backtests/my', { params: { limit } })
  }

  /**
   * 获取回测统计
   */
  static async getBacktestStats(): Promise<ApiResponse<BacktestStats>> {
    return request.get('/backtests/stats')
  }

  /**
   * 获取回测详情
   */
  static async getBacktest(id: number): Promise<ApiResponse<Backtest>> {
    return request.get(`/backtests/${id}`)
  }

  /**
   * 通过UUID获取回测
   */
  static async getBacktestByUuid(uuid: string): Promise<ApiResponse<Backtest>> {
    return request.get(`/backtests/uuid/${uuid}`)
  }

  /**
   * 更新回测
   */
  static async updateBacktest(id: number, data: Partial<BacktestConfig>): Promise<ApiResponse<Backtest>> {
    return request.put(`/backtests/${id}`, data)
  }

  /**
   * 删除回测
   */
  static async deleteBacktest(id: number): Promise<ApiResponse<{ deleted: boolean }>> {
    return request.delete(`/backtests/${id}`)
  }

  /**
   * 执行回测操作
   */
  static async executeBacktest(id: number, data: BacktestExecutionRequest): Promise<ApiResponse<BacktestExecutionResponse>> {
    return request.post(`/backtests/${id}/execute`, data)
  }

  /**
   * 获取配置模板列表
   */
  static async getConfigTemplates(params?: {
    category?: string
    is_official?: boolean
    page?: number
    page_size?: number
  }): Promise<ApiResponse<PaginatedResponse<BacktestTemplate>>> {
    return request.get('/backtests/templates', { params })
  }

  /**
   * 获取配置模板详情
   */
  static async getConfigTemplate(id: number): Promise<ApiResponse<BacktestTemplate>> {
    return request.get(`/backtests/templates/${id}`)
  }

  /**
   * 创建配置模板
   */
  static async createConfigTemplate(data: {
    name: string
    description?: string
    category?: string
    config_template: any
    default_parameters?: any
    tags?: string[]
  }): Promise<ApiResponse<BacktestTemplate>> {
    return request.post('/backtests/templates', data)
  }

  /**
   * 更新配置模板
   */
  static async updateConfigTemplate(id: number, data: {
    name?: string
    description?: string
    category?: string
    config_template?: any
    default_parameters?: any
    tags?: string[]
    is_active?: boolean
  }): Promise<ApiResponse<BacktestTemplate>> {
    return request.put(`/backtests/templates/${id}`, data)
  }

  /**
   * 删除配置模板
   */
  static async deleteConfigTemplate(id: number): Promise<ApiResponse<{ deleted: boolean }>> {
    return request.delete(`/backtests/templates/${id}`)
  }

  /**
   * 保存配置模板
   */
  static async saveConfigTemplate(data: {
    name: string
    description?: string
    category?: string
    config_template: any
  }): Promise<ApiResponse<BacktestTemplate>> {
    return request.post('/backtests/templates', data)
  }

  /**
   * 获取用户配置列表
   */
  static async getUserConfigs(): Promise<ApiResponse<any[]>> {
    return request.get('/backtests/configs/user')
  }

  /**
   * 获取热门配置
   */
  static async getPopularConfigs(limit: number = 10): Promise<ApiResponse<any[]>> {
    return request.get('/backtests/configs/popular', { params: { limit } })
  }

  /**
   * 获取默认配置
   */
  static async getDefaultConfig(backtest_type: string = 'simple'): Promise<ApiResponse<any>> {
    return request.get('/backtests/configs/default', { params: { backtest_type } })
  }

  /**
   * 验证配置
   */
  static async validateConfig(config: any): Promise<ApiResponse<{
    is_valid: boolean
    errors: string[]
  }>> {
    return request.post('/backtests/configs/validate', { config })
  }

  /**
   * 获取配置分类
   */
  static async getConfigCategories(): Promise<ApiResponse<any[]>> {
    return request.get('/backtests/configs/categories')
  }

  /**
   * 创建回测比较
   */
  static async createBacktestComparison(data: {
    name: string
    description?: string
    backtest_ids: number[]
    tags?: string[]
    is_public?: boolean
  }): Promise<ApiResponse<any>> {
    return request.post('/backtests/comparisons', data)
  }

  /**
   * 获取回测比较列表
   */
  static async getBacktestComparisons(params?: {
    page?: number
    page_size?: number
  }): Promise<ApiResponse<PaginatedResponse<any>>> {
    return request.get('/backtests/comparisons', { params })
  }

  /**
   * 获取回测比较详情
   */
  static async getBacktestComparison(id: number): Promise<ApiResponse<any>> {
    return request.get(`/backtests/comparisons/${id}`)
  }

  /**
   * 删除回测比较
   */
  static async deleteBacktestComparison(id: number): Promise<ApiResponse<{ deleted: boolean }>> {
    return request.delete(`/backtests/comparisons/${id}`)
  }
}

// 导出便捷方法
export const {
  createBacktest,
  getBacktests,
  getMyBacktests,
  getBacktestStats,
  getBacktest,
  getBacktestByUuid,
  updateBacktest,
  deleteBacktest,
  executeBacktest,
  getConfigTemplates,
  getConfigTemplate,
  createConfigTemplate,
  updateConfigTemplate,
  deleteConfigTemplate,
  saveConfigTemplate,
  getUserConfigs,
  getPopularConfigs,
  getDefaultConfig,
  validateConfig,
  getConfigCategories,
  createBacktestComparison,
  getBacktestComparisons,
  getBacktestComparison,
  deleteBacktestComparison
} = BacktestApi

// 创建回测API实例
export const backtestApi = BacktestApi