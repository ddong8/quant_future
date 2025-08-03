/**
 * 策略相关类型定义
 */

// 策略状态枚举
export enum StrategyStatus {
  DRAFT = 'draft',
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  TESTING = 'testing',
  ERROR = 'error'
}

// 策略类型枚举
export enum StrategyType {
  TREND_FOLLOWING = 'trend_following',
  MEAN_REVERSION = 'mean_reversion',
  ARBITRAGE = 'arbitrage',
  MARKET_MAKING = 'market_making',
  MOMENTUM = 'momentum',
  STATISTICAL = 'statistical',
  CUSTOM = 'custom'
}

// 策略基础接口
export interface Strategy {
  id: number
  uuid: string
  name: string
  description?: string
  strategy_type: StrategyType
  status: StrategyStatus
  code: string
  entry_point: string
  language: string
  parameters: Record<string, any>
  symbols: string[]
  timeframe?: string
  max_position_size?: number
  max_drawdown?: number
  stop_loss?: number
  take_profit?: number
  total_returns: number
  sharpe_ratio?: number
  max_drawdown_pct?: number
  win_rate?: number
  total_trades: number
  is_running: boolean
  last_run_at?: string
  last_error?: string
  version: number
  tags: string[]
  is_public: boolean
  is_template: boolean
  user_id: number
  created_at: string
  updated_at: string
}

// 策略列表项接口
export interface StrategyListItem {
  id: number
  uuid: string
  name: string
  description?: string
  strategy_type: StrategyType
  status: StrategyStatus
  version: number
  total_returns: number
  sharpe_ratio?: number
  win_rate?: number
  total_trades: number
  is_running: boolean
  last_run_at?: string
  tags: string[]
  is_public: boolean
  is_template: boolean
  user_id: number
  created_at: string
  updated_at: string
}

// 策略创建请求
export interface StrategyCreateRequest {
  name: string
  description?: string
  strategy_type: StrategyType
  code: string
  entry_point?: string
  language?: string
  parameters?: Record<string, any>
  symbols?: string[]
  timeframe?: string
  max_position_size?: number
  max_drawdown?: number
  stop_loss?: number
  take_profit?: number
  tags?: string[]
  is_public?: boolean
}

// 策略更新请求
export interface StrategyUpdateRequest {
  name?: string
  description?: string
  strategy_type?: StrategyType
  code?: string
  entry_point?: string
  language?: string
  parameters?: Record<string, any>
  symbols?: string[]
  timeframe?: string
  max_position_size?: number
  max_drawdown?: number
  stop_loss?: number
  take_profit?: number
  tags?: string[]
  is_public?: boolean
  status?: StrategyStatus
}

// 策略搜索参数
export interface StrategySearchParams {
  keyword?: string
  strategy_type?: StrategyType
  status?: StrategyStatus
  tags?: string[]
  is_public?: boolean
  is_template?: boolean
  is_running?: boolean
  created_after?: string
  created_before?: string
  sort_by?: string
  sort_order?: 'asc' | 'desc'
  page?: number
  page_size?: number
}

// 策略版本接口
export interface StrategyVersion {
  id: number
  version_number: number
  version_name?: string
  description?: string
  code: string
  entry_point: string
  parameters: Record<string, any>
  change_log?: string
  is_major_version: boolean
  performance_data: Record<string, any>
  strategy_id: number
  user_id: number
  created_at: string
}

// 策略模板接口
export interface StrategyTemplate {
  id: number
  uuid: string
  name: string
  description?: string
  strategy_type: StrategyType
  category?: string
  code_template: string
  default_parameters: Record<string, any>
  usage_count: number
  rating: number
  tags: string[]
  is_official: boolean
  is_active: boolean
  author_id?: number
  created_at: string
  updated_at: string
}

// 策略统计接口
export interface StrategyStats {
  total_strategies: number
  active_strategies: number
  running_strategies: number
  draft_strategies: number
  public_strategies: number
  template_strategies: number
  avg_returns: number
  avg_sharpe_ratio: number
  avg_win_rate: number
  total_trades: number
}

// 策略执行请求
export interface StrategyExecutionRequest {
  action: 'start' | 'stop' | 'pause' | 'resume'
  parameters?: Record<string, any>
}

// 策略执行响应
export interface StrategyExecutionResponse {
  strategy_id: number
  action: string
  success: boolean
  message: string
  execution_id?: string
  timestamp: string
}

// 策略类型选项
export const STRATEGY_TYPE_OPTIONS = [
  { label: '趋势跟踪', value: StrategyType.TREND_FOLLOWING },
  { label: '均值回归', value: StrategyType.MEAN_REVERSION },
  { label: '套利策略', value: StrategyType.ARBITRAGE },
  { label: '做市策略', value: StrategyType.MARKET_MAKING },
  { label: '动量策略', value: StrategyType.MOMENTUM },
  { label: '统计套利', value: StrategyType.STATISTICAL },
  { label: '自定义', value: StrategyType.CUSTOM }
]

// 策略状态选项
export const STRATEGY_STATUS_OPTIONS = [
  { label: '草稿', value: StrategyStatus.DRAFT, type: 'info' },
  { label: '活跃', value: StrategyStatus.ACTIVE, type: 'success' },
  { label: '已停用', value: StrategyStatus.INACTIVE, type: 'warning' },
  { label: '测试中', value: StrategyStatus.TESTING, type: 'primary' },
  { label: '错误', value: StrategyStatus.ERROR, type: 'danger' }
]

// 策略类型标签映射
export const STRATEGY_TYPE_LABELS: Record<StrategyType, string> = {
  [StrategyType.TREND_FOLLOWING]: '趋势跟踪',
  [StrategyType.MEAN_REVERSION]: '均值回归',
  [StrategyType.ARBITRAGE]: '套利策略',
  [StrategyType.MARKET_MAKING]: '做市策略',
  [StrategyType.MOMENTUM]: '动量策略',
  [StrategyType.STATISTICAL]: '统计套利',
  [StrategyType.CUSTOM]: '自定义'
}

// 策略状态标签映射
export const STRATEGY_STATUS_LABELS: Record<StrategyStatus, string> = {
  [StrategyStatus.DRAFT]: '草稿',
  [StrategyStatus.ACTIVE]: '活跃',
  [StrategyStatus.INACTIVE]: '已停用',
  [StrategyStatus.TESTING]: '测试中',
  [StrategyStatus.ERROR]: '错误'
}

// 策略状态颜色映射
export const STRATEGY_STATUS_COLORS: Record<StrategyStatus, string> = {
  [StrategyStatus.DRAFT]: '#909399',
  [StrategyStatus.ACTIVE]: '#67C23A',
  [StrategyStatus.INACTIVE]: '#E6A23C',
  [StrategyStatus.TESTING]: '#409EFF',
  [StrategyStatus.ERROR]: '#F56C6C'
}