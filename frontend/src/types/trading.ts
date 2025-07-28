// 交易相关类型定义

// 订单基础信息
export interface Order {
  id: number
  user_id: number
  strategy_id?: number
  symbol: string
  side: OrderSide
  order_type: OrderType
  quantity: number
  price?: number
  filled_quantity: number
  remaining_quantity: number
  avg_fill_price: number
  status: OrderStatus
  time_in_force: TimeInForce
  created_at: string
  updated_at: string
  filled_at?: string
  cancelled_at?: string
  
  // 订单元数据
  client_order_id?: string
  parent_order_id?: number
  stop_price?: number
  trail_amount?: number
  trail_percent?: number
  
  // 费用信息
  commission: number
  fees: number
  
  // 风险信息
  risk_check_passed: boolean
  risk_message?: string
  
  // 执行信息
  execution_reports: ExecutionReport[]
}

// 订单方向
export enum OrderSide {
  BUY = 'buy',
  SELL = 'sell'
}

// 订单类型
export enum OrderType {
  MARKET = 'market',
  LIMIT = 'limit',
  STOP = 'stop',
  STOP_LIMIT = 'stop_limit',
  TRAILING_STOP = 'trailing_stop'
}

// 订单状态
export enum OrderStatus {
  PENDING = 'pending',
  SUBMITTED = 'submitted',
  PARTIALLY_FILLED = 'partially_filled',
  FILLED = 'filled',
  CANCELLED = 'cancelled',
  REJECTED = 'rejected',
  EXPIRED = 'expired'
}

// 有效期类型
export enum TimeInForce {
  DAY = 'day',
  GTC = 'gtc', // Good Till Cancelled
  IOC = 'ioc', // Immediate Or Cancel
  FOK = 'fok'  // Fill Or Kill
}

// 执行报告
export interface ExecutionReport {
  id: number
  order_id: number
  execution_id: string
  symbol: string
  side: OrderSide
  quantity: number
  price: number
  timestamp: string
  commission: number
  fees: number
  liquidity: 'maker' | 'taker'
}

// 持仓信息
export interface Position {
  id: number
  user_id: number
  account_id: number
  symbol: string
  side: 'long' | 'short'
  quantity: number
  avg_cost: number
  market_value: number
  unrealized_pnl: number
  realized_pnl: number
  total_pnl: number
  cost_basis: number
  last_price: number
  change_percent: number
  created_at: string
  updated_at: string
  
  // 风险指标
  margin_requirement: number
  maintenance_margin: number
  buying_power_effect: number
  
  // 持仓详情
  lots: PositionLot[]
}

// 持仓批次
export interface PositionLot {
  id: number
  position_id: number
  quantity: number
  cost_price: number
  open_date: string
  pnl: number
}

// 账户信息
export interface TradingAccount {
  id: number
  user_id: number
  account_name: string
  account_type: AccountType
  status: AccountStatus
  currency: string
  
  // 资金信息
  total_equity: number
  available_cash: number
  buying_power: number
  margin_used: number
  margin_available: number
  maintenance_margin: number
  
  // 盈亏信息
  day_pnl: number
  total_pnl: number
  unrealized_pnl: number
  realized_pnl: number
  
  // 风险指标
  margin_ratio: number
  risk_level: RiskLevel
  max_position_size: number
  
  created_at: string
  updated_at: string
}

// 账户类型
export enum AccountType {
  CASH = 'cash',
  MARGIN = 'margin',
  FUTURES = 'futures'
}

// 账户状态
export enum AccountStatus {
  ACTIVE = 'active',
  SUSPENDED = 'suspended',
  CLOSED = 'closed'
}

// 风险等级
export enum RiskLevel {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical'
}

// 交易历史
export interface TradeHistory {
  id: number
  order_id: number
  symbol: string
  side: OrderSide
  quantity: number
  price: number
  amount: number
  commission: number
  fees: number
  pnl: number
  timestamp: string
  settlement_date: string
  trade_type: 'normal' | 'correction' | 'cancel'
  counterparty?: string
  execution_venue: string
  
  // 策略信息
  strategy_id?: number
  strategy_name?: string
  signal_type?: string
}

// 实时盈亏
export interface RealTimePnL {
  account_id: number
  symbol?: string
  
  // 当日盈亏
  day_pnl: number
  day_pnl_percent: number
  
  // 总盈亏
  total_pnl: number
  total_pnl_percent: number
  
  // 未实现盈亏
  unrealized_pnl: number
  unrealized_pnl_percent: number
  
  // 已实现盈亏
  realized_pnl: number
  realized_pnl_percent: number
  
  // 更新时间
  last_updated: string
}

// 市场数据
export interface MarketData {
  symbol: string
  last_price: number
  change: number
  change_percent: number
  volume: number
  turnover: number
  high: number
  low: number
  open: number
  close: number
  bid_price: number
  bid_size: number
  ask_price: number
  ask_size: number
  timestamp: string
}

// 订单簿
export interface OrderBook {
  symbol: string
  bids: OrderBookLevel[]
  asks: OrderBookLevel[]
  timestamp: string
}

export interface OrderBookLevel {
  price: number
  size: number
  orders: number
}

// 交易信号
export interface TradingSignal {
  id: number
  strategy_id: number
  symbol: string
  signal_type: 'buy' | 'sell' | 'hold'
  strength: number
  price: number
  quantity: number
  timestamp: string
  metadata: Record<string, any>
  executed: boolean
  order_id?: number
}

// 风险指标
export interface RiskMetrics {
  account_id: number
  
  // 保证金指标
  margin_ratio: number
  maintenance_margin_ratio: number
  buying_power_ratio: number
  
  // 集中度风险
  concentration_risk: number
  max_position_weight: number
  
  // 流动性风险
  liquidity_risk: number
  
  // VaR指标
  var_1d: number
  var_5d: number
  
  // 压力测试
  stress_test_result: number
  
  last_updated: string
}

// 创建订单请求
export interface CreateOrderRequest {
  symbol: string
  side: OrderSide
  order_type: OrderType
  quantity: number
  price?: number
  stop_price?: number
  time_in_force: TimeInForce
  client_order_id?: string
  strategy_id?: number
  
  // 风险控制
  max_position_size?: number
  risk_check?: boolean
}

// 修改订单请求
export interface ModifyOrderRequest {
  quantity?: number
  price?: number
  stop_price?: number
}

// 批量订单请求
export interface BatchOrderRequest {
  orders: CreateOrderRequest[]
  all_or_none?: boolean
  max_failures?: number
}

// 交易统计
export interface TradingStats {
  account_id: number
  period: 'day' | 'week' | 'month' | 'year'
  
  // 交易统计
  total_trades: number
  buy_trades: number
  sell_trades: number
  avg_trade_size: number
  
  // 盈亏统计
  gross_pnl: number
  net_pnl: number
  commission_paid: number
  fees_paid: number
  
  // 成功率
  winning_trades: number
  losing_trades: number
  win_rate: number
  
  // 风险指标
  max_drawdown: number
  sharpe_ratio: number
  
  // 时间统计
  avg_holding_period: number
  max_holding_period: number
  
  last_updated: string
}

// API响应类型
export interface OrderListResponse {
  orders: Order[]
  total: number
  page: number
  page_size: number
}

export interface PositionListResponse {
  positions: Position[]
  total_value: number
  total_pnl: number
}

export interface TradeHistoryResponse {
  trades: TradeHistory[]
  total: number
  page: number
  page_size: number
}

export interface TradingAccountResponse {
  account: TradingAccount
}

export interface RealTimePnLResponse {
  pnl: RealTimePnL
}

export interface MarketDataResponse {
  data: MarketData[]
}

export interface OrderBookResponse {
  orderbook: OrderBook
}

export interface TradingStatsResponse {
  stats: TradingStats
}

// WebSocket消息类型
export interface WSOrderUpdate {
  type: 'order_update'
  data: Order
}

export interface WSPositionUpdate {
  type: 'position_update'
  data: Position
}

export interface WSPnLUpdate {
  type: 'pnl_update'
  data: RealTimePnL
}

export interface WSMarketDataUpdate {
  type: 'market_data'
  data: MarketData
}

export interface WSTradingSignal {
  type: 'trading_signal'
  data: TradingSignal
}

export type WSMessage = 
  | WSOrderUpdate 
  | WSPositionUpdate 
  | WSPnLUpdate 
  | WSMarketDataUpdate 
  | WSTradingSignal