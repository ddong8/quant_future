/**
 * 订单管理API
 */

import { request } from '@/utils/request'

// 订单类型定义
export enum OrderType {
  MARKET = 'market',
  LIMIT = 'limit',
  STOP = 'stop',
  STOP_LIMIT = 'stop_limit',
  TRAILING_STOP = 'trailing_stop',
  ICEBERG = 'iceberg',
  TWAP = 'twap',
  VWAP = 'vwap'
}

export enum OrderSide {
  BUY = 'buy',
  SELL = 'sell'
}

export enum OrderStatus {
  PENDING = 'pending',
  SUBMITTED = 'submitted',
  ACCEPTED = 'accepted',
  PARTIALLY_FILLED = 'partially_filled',
  FILLED = 'filled',
  CANCELLED = 'cancelled',
  REJECTED = 'rejected',
  EXPIRED = 'expired',
  SUSPENDED = 'suspended'
}

export enum OrderTimeInForce {
  DAY = 'day',
  GTC = 'gtc',
  IOC = 'ioc',
  FOK = 'fok',
  GTD = 'gtd'
}

export enum OrderPriority {
  LOW = 'low',
  NORMAL = 'normal',
  HIGH = 'high',
  URGENT = 'urgent'
}

// 订单接口定义
export interface Order {
  id: number
  uuid: string
  symbol: string
  order_type: OrderType
  side: OrderSide
  status: OrderStatus
  quantity: number
  price?: number
  stop_price?: number
  filled_quantity: number
  remaining_quantity?: number
  avg_fill_price?: number
  time_in_force: OrderTimeInForce
  priority: OrderPriority
  iceberg_quantity?: number
  trailing_amount?: number
  trailing_percent?: number
  expire_time?: string
  submitted_at?: string
  accepted_at?: string
  filled_at?: string
  cancelled_at?: string
  commission: number
  commission_asset?: string
  total_value?: number
  max_position_size?: number
  risk_check_passed: boolean
  risk_check_message?: string
  strategy_id?: number
  backtest_id?: number
  parent_order_id?: number
  source: string
  source_id?: string
  broker?: string
  account_id?: string
  order_id_external?: string
  tags: string[]
  notes?: string
  metadata: Record<string, any>
  user_id: number
  created_at: string
  updated_at: string
  fill_ratio: number
  is_active: boolean
  is_finished: boolean
}

export interface OrderCreate {
  symbol: string
  order_type: OrderType
  side: OrderSide
  quantity: number
  price?: number
  stop_price?: number
  time_in_force?: OrderTimeInForce
  priority?: OrderPriority
  iceberg_quantity?: number
  trailing_amount?: number
  trailing_percent?: number
  expire_time?: string
  max_position_size?: number
  strategy_id?: number
  backtest_id?: number
  parent_order_id?: number
  broker?: string
  account_id?: string
  tags?: string[]
  notes?: string
  metadata?: Record<string, any>
}

export interface OrderUpdate {
  quantity?: number
  price?: number
  stop_price?: number
  time_in_force?: OrderTimeInForce
  priority?: OrderPriority
  expire_time?: string
  tags?: string[]
  notes?: string
  metadata?: Record<string, any>
}

export interface OrderSearchParams {
  symbol?: string
  order_type?: OrderType
  side?: OrderSide
  status?: OrderStatus
  strategy_id?: number
  backtest_id?: number
  tags?: string[]
  created_after?: string
  created_before?: string
  min_quantity?: number
  max_quantity?: number
  min_price?: number
  max_price?: number
  sort_by?: string
  sort_order?: string
  page?: number
  page_size?: number
}

export interface OrderStats {
  total_orders: number
  active_orders: number
  filled_orders: number
  cancelled_orders: number
  rejected_orders: number
  total_volume: number
  total_value: number
  avg_fill_ratio: number
  success_rate: number
}

export interface OrderFill {
  id: number
  uuid: string
  order_id: number
  fill_id_external?: string
  quantity: number
  price: number
  value: number
  commission: number
  commission_asset?: string
  fill_time: string
  liquidity?: string
  counterparty?: string
  metadata: Record<string, any>
  created_at: string
}

export interface OrderTemplate {
  id: number
  uuid: string
  name: string
  description?: string
  category?: string
  template_config: Record<string, any>
  default_parameters: Record<string, any>
  usage_count: number
  tags: string[]
  is_official: boolean
  is_active: boolean
  author_id?: number
  created_at: string
  updated_at: string
}

export interface OrderRiskCheck {
  symbol: string
  side: OrderSide
  quantity: number
  price?: number
  order_type: OrderType
  strategy_id?: number
}

export interface OrderRiskCheckResult {
  passed: boolean
  risk_level: string
  warnings: string[]
  errors: string[]
  suggestions: string[]
  risk_score: number
  max_allowed_quantity?: number
  estimated_margin?: number
}

// API函数
export const orderApi = {
  // 创建订单
  createOrder: (data: OrderCreate) => 
    request.post<Order>('/api/v1/orders/', data),

  // 搜索订单
  searchOrders: (params: OrderSearchParams) => 
    request.get<{ data: Order[], meta: any }>('/api/v1/orders/', { params }),

  // 获取订单统计
  getOrderStats: () => 
    request.get<OrderStats>('/api/v1/orders/stats'),

  // 获取活跃订单
  getActiveOrders: () => 
    request.get<Order[]>('/api/v1/orders/active'),

  // 获取我的订单
  getMyOrders: (params?: { status?: OrderStatus, limit?: number }) => 
    request.get<Order[]>('/api/v1/orders/my', { params }),

  // 获取订单详情
  getOrder: (orderId: number) => 
    request.get<Order>(`/api/v1/orders/${orderId}`),

  // 通过UUID获取订单
  getOrderByUuid: (uuid: string) => 
    request.get<Order>(`/api/v1/orders/uuid/${uuid}`),

  // 更新订单
  updateOrder: (orderId: number, data: OrderUpdate) => 
    request.put<Order>(`/api/v1/orders/${orderId}`, data),

  // 取消订单
  cancelOrder: (orderId: number, reason?: string) => 
    request.delete<Order>(`/api/v1/orders/${orderId}`, { 
      params: reason ? { reason } : undefined 
    }),

  // 批量取消订单
  batchCancelOrders: (orderIds: number[]) => 
    request.post<any>('/api/v1/orders/batch/cancel', orderIds),

  // 订单风险检查
  checkOrderRisk: (data: OrderRiskCheck) => 
    request.post<OrderRiskCheckResult>('/api/v1/orders/risk-check', data),

  // 获取订单成交记录
  getOrderFills: (orderId: number) => 
    request.get<OrderFill[]>(`/api/v1/orders/${orderId}/fills`),

  // 获取订单模板列表
  getOrderTemplates: (params?: { category?: string, is_official?: boolean }) => 
    request.get<OrderTemplate[]>('/api/v1/orders/templates/', { params }),

  // 获取订单模板详情
  getOrderTemplate: (templateId: number) => 
    request.get<OrderTemplate>(`/api/v1/orders/templates/${templateId}`),

  // 创建订单模板
  createOrderTemplate: (data: Partial<OrderTemplate>) => 
    request.post<OrderTemplate>('/api/v1/orders/templates/', data),

  // 订单执行相关
  executeOrder: (orderId: number, tradingSystem?: string) => 
    request.post(`/api/v1/orders/${orderId}/execute`, {}, { 
      params: tradingSystem ? { trading_system: tradingSystem } : undefined 
    }),

  getOrderExecutionStatus: (orderId: number) => 
    request.get(`/api/v1/orders/${orderId}/execution-status`),

  getExecutionServiceStatus: () => 
    request.get('/api/v1/orders/execution/service-status'),

  getExecutionStatistics: () => 
    request.get('/api/v1/orders/execution/statistics'),

  startExecutionService: () => 
    request.post('/api/v1/orders/execution/start-service'),

  stopExecutionService: () => 
    request.post('/api/v1/orders/execution/stop-service')
}