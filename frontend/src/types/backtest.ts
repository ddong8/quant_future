// 回测相关类型定义

// 回测基础信息
export interface Backtest {
  id: number
  name: string
  description: string
  strategy_id: number
  strategy_name: string
  status: BacktestStatus
  created_at: string
  updated_at: string
  started_at?: string
  completed_at?: string
  user_id: number
  
  // 回测配置
  config: BacktestConfig
  
  // 回测结果
  result?: BacktestResult
  
  // 进度信息
  progress?: BacktestProgress
}

// 回测状态
export enum BacktestStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled'
}

// 回测配置
export interface BacktestConfig {
  // 时间配置
  start_date: string
  end_date: string
  
  // 资金配置
  initial_capital: number
  
  // 交易品种
  symbols: string[]
  
  // 数据配置
  data_frequency: string // '1m', '5m', '15m', '30m', '1h', '4h', '1d'
  benchmark?: string
  
  // 手续费配置
  commission: {
    rate: number
    min_commission: number
    per_share: boolean
  }
  
  // 滑点配置
  slippage: {
    type: 'fixed' | 'percentage'
    value: number
  }
  
  // 风险管理
  risk_management: {
    max_position_size: number
    max_drawdown: number
    stop_loss?: number
    take_profit?: number
  }
  
  // 高级配置
  advanced: {
    warm_up_period: number // 预热期天数
    lookback_window: number // 回望窗口
    rebalance_frequency: string // 'daily', 'weekly', 'monthly'
    market_impact: boolean
    transaction_cost: boolean
  }
}

// 回测结果
export interface BacktestResult {
  // 基础统计
  total_return: number
  annualized_return: number
  volatility: number
  sharpe_ratio: number
  sortino_ratio: number
  max_drawdown: number
  calmar_ratio: number
  
  // 交易统计
  total_trades: number
  winning_trades: number
  losing_trades: number
  win_rate: number
  avg_trade_return: number
  avg_winning_trade: number
  avg_losing_trade: number
  profit_factor: number
  
  // 时间统计
  avg_trade_duration: number
  max_trade_duration: number
  min_trade_duration: number
  
  // 资金曲线
  equity_curve: EquityPoint[]
  
  // 回撤曲线
  drawdown_curve: DrawdownPoint[]
  
  // 交易记录
  trades: TradeRecord[]
  
  // 持仓记录
  positions: PositionRecord[]
  
  // 基准比较
  benchmark_comparison?: BenchmarkComparison
  
  // 风险指标
  risk_metrics: RiskMetrics
}

// 资金曲线点
export interface EquityPoint {
  date: string
  equity: number
  returns: number
  cumulative_returns: number
}

// 回撤曲线点
export interface DrawdownPoint {
  date: string
  drawdown: number
  underwater_duration: number
}

// 交易记录
export interface TradeRecord {
  id: number
  symbol: string
  side: 'buy' | 'sell'
  quantity: number
  price: number
  timestamp: string
  commission: number
  slippage: number
  pnl: number
  cumulative_pnl: number
  strategy_signal?: string
  metadata?: Record<string, any>
}

// 持仓记录
export interface PositionRecord {
  date: string
  symbol: string
  quantity: number
  market_value: number
  weight: number
  unrealized_pnl: number
}

// 基准比较
export interface BenchmarkComparison {
  benchmark_symbol: string
  benchmark_return: number
  alpha: number
  beta: number
  correlation: number
  tracking_error: number
  information_ratio: number
}

// 风险指标
export interface RiskMetrics {
  var_95: number // 95% VaR
  var_99: number // 99% VaR
  cvar_95: number // 95% CVaR
  cvar_99: number // 99% CVaR
  skewness: number
  kurtosis: number
  tail_ratio: number
  common_sense_ratio: number
}

// 回测进度
export interface BacktestProgress {
  current_date: string
  progress_percentage: number
  processed_days: number
  total_days: number
  estimated_remaining_time: number
  current_equity: number
  current_drawdown: number
  trades_count: number
  error_message?: string
}

// 回测创建请求
export interface CreateBacktestRequest {
  name: string
  description?: string
  strategy_id: number
  config: BacktestConfig
}

// 回测更新请求
export interface UpdateBacktestRequest {
  name?: string
  description?: string
  config?: Partial<BacktestConfig>
}

// 回测比较
export interface BacktestComparison {
  backtests: Backtest[]
  comparison_metrics: {
    [backtestId: number]: BacktestResult
  }
  relative_performance: {
    [backtestId: number]: {
      vs_benchmark: number
      vs_average: number
      rank: number
    }
  }
}

// 回测模板
export interface BacktestTemplate {
  id: number
  name: string
  description: string
  config: Partial<BacktestConfig>
  is_public: boolean
  created_by: number
  created_at: string
  usage_count: number
}

// 历史数据信息
export interface HistoricalDataInfo {
  symbol: string
  start_date: string
  end_date: string
  frequency: string
  total_records: number
  missing_days: string[]
  data_quality: number
}

// 回测任务
export interface BacktestTask {
  id: number
  backtest_id: number
  task_type: 'data_preparation' | 'calculation' | 'analysis' | 'report_generation'
  status: 'pending' | 'running' | 'completed' | 'failed'
  progress: number
  started_at?: string
  completed_at?: string
  error_message?: string
  result?: any
}

// 回测报告
export interface BacktestReport {
  id: number
  backtest_id: number
  report_type: 'summary' | 'detailed' | 'risk_analysis' | 'trade_analysis'
  format: 'html' | 'pdf' | 'excel'
  file_path: string
  file_size: number
  generated_at: string
}

// 回测优化
export interface BacktestOptimization {
  id: number
  backtest_id: number
  parameter_ranges: Record<string, {
    min: number
    max: number
    step: number
  }>
  optimization_target: 'sharpe_ratio' | 'total_return' | 'max_drawdown' | 'profit_factor'
  optimization_method: 'grid_search' | 'random_search' | 'genetic_algorithm'
  max_iterations: number
  status: 'pending' | 'running' | 'completed' | 'failed'
  best_parameters?: Record<string, number>
  best_result?: BacktestResult
  all_results?: Array<{
    parameters: Record<string, number>
    result: BacktestResult
  }>
}

// API响应类型
export interface BacktestListResponse {
  backtests: Backtest[]
  total: number
  page: number
  page_size: number
}

export interface BacktestResponse {
  backtest: Backtest
}

export interface BacktestResultResponse {
  result: BacktestResult
}

export interface BacktestProgressResponse {
  progress: BacktestProgress
}

export interface BacktestTemplatesResponse {
  templates: BacktestTemplate[]
}

export interface HistoricalDataResponse {
  data_info: HistoricalDataInfo[]
}

export interface BacktestReportsResponse {
  reports: BacktestReport[]
}

// 回测统计
export interface BacktestStats {
  total_backtests: number
  running_backtests: number
  completed_backtests: number
  failed_backtests: number
  avg_completion_time: number
  success_rate: number
}