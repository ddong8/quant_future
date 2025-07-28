import { http } from '@/utils/request'
import type {
  Order,
  Position,
  TradingAccount,
  TradeHistory,
  RealTimePnL,
  MarketData,
  OrderBook,
  TradingStats,
  RiskMetrics,
  CreateOrderRequest,
  ModifyOrderRequest,
  BatchOrderRequest,
  OrderListResponse,
  PositionListResponse,
  TradeHistoryResponse,
  TradingAccountResponse,
  RealTimePnLResponse,
  MarketDataResponse,
  OrderBookResponse,
  TradingStatsResponse
} from '@/types/trading'

export const tradingApi = {
  // 订单管理
  getOrders: (params?: {
    account_id?: number
    symbol?: string
    status?: string
    side?: string
    start_date?: string
    end_date?: string
    page?: number
    page_size?: number
  }) => {
    return http.get<OrderListResponse>('/trading/orders', { params })
  },

  getOrder: (orderId: number) => {
    return http.get<{ order: Order }>(`/trading/orders/${orderId}`)
  },

  createOrder: (data: CreateOrderRequest) => {
    return http.post<{ order: Order }>('/trading/orders', data)
  },

  modifyOrder: (orderId: number, data: ModifyOrderRequest) => {
    return http.put<{ order: Order }>(`/trading/orders/${orderId}`, data)
  },

  cancelOrder: (orderId: number) => {
    return http.delete(`/trading/orders/${orderId}`)
  },

  cancelAllOrders: (params?: {
    account_id?: number
    symbol?: string
  }) => {
    return http.post('/trading/orders/cancel-all', params)
  },

  // 批量订单
  createBatchOrders: (data: BatchOrderRequest) => {
    return http.post<{ orders: Order[] }>('/trading/orders/batch', data)
  },

  // 持仓管理
  getPositions: (params?: {
    account_id?: number
    symbol?: string
  }) => {
    return http.get<PositionListResponse>('/trading/positions', { params })
  },

  getPosition: (positionId: number) => {
    return http.get<{ position: Position }>(`/trading/positions/${positionId}`)
  },

  closePosition: (positionId: number, quantity?: number) => {
    return http.post(`/trading/positions/${positionId}/close`, { quantity })
  },

  closeAllPositions: (accountId: number) => {
    return http.post(`/trading/positions/close-all`, { account_id: accountId })
  },

  // 账户管理
  getAccounts: () => {
    return http.get<{ accounts: TradingAccount[] }>('/trading/accounts')
  },

  getAccount: (accountId: number) => {
    return http.get<TradingAccountResponse>(`/trading/accounts/${accountId}`)
  },

  updateAccount: (accountId: number, data: Partial<TradingAccount>) => {
    return http.put<TradingAccountResponse>(`/trading/accounts/${accountId}`, data)
  },

  // 交易历史
  getTradeHistory: (params?: {
    account_id?: number
    symbol?: string
    start_date?: string
    end_date?: string
    page?: number
    page_size?: number
  }) => {
    return http.get<TradeHistoryResponse>('/trading/history', { params })
  },

  exportTradeHistory: (params: {
    account_id?: number
    symbol?: string
    start_date?: string
    end_date?: string
    format: 'csv' | 'excel'
  }) => {
    return http.get('/trading/history/export', {
      params,
      responseType: 'blob'
    })
  },

  // 实时盈亏
  getRealTimePnL: (accountId: number, symbol?: string) => {
    return http.get<RealTimePnLResponse>('/trading/pnl', {
      params: { account_id: accountId, symbol }
    })
  },

  // 市场数据
  getMarketData: (symbols: string[]) => {
    return http.get<MarketDataResponse>('/trading/market-data', {
      params: { symbols: symbols.join(',') }
    })
  },

  getOrderBook: (symbol: string, depth?: number) => {
    return http.get<OrderBookResponse>('/trading/orderbook', {
      params: { symbol, depth }
    })
  },

  // 交易统计
  getTradingStats: (accountId: number, period: string) => {
    return http.get<TradingStatsResponse>('/trading/stats', {
      params: { account_id: accountId, period }
    })
  },

  // 风险指标
  getRiskMetrics: (accountId: number) => {
    return http.get<{ metrics: RiskMetrics }>('/trading/risk-metrics', {
      params: { account_id: accountId }
    })
  },

  // 风险检查
  checkOrderRisk: (data: CreateOrderRequest) => {
    return http.post('/trading/risk-check', data)
  },

  // 交易信号
  getTradingSignals: (params?: {
    strategy_id?: number
    symbol?: string
    start_date?: string
    end_date?: string
  }) => {
    return http.get('/trading/signals', { params })
  },

  executeSignal: (signalId: number) => {
    return http.post(`/trading/signals/${signalId}/execute`)
  },

  // 交易设置
  getTradingSettings: (accountId: number) => {
    return http.get(`/trading/accounts/${accountId}/settings`)
  },

  updateTradingSettings: (accountId: number, settings: any) => {
    return http.put(`/trading/accounts/${accountId}/settings`, settings)
  },

  // 交易限制
  getTradingLimits: (accountId: number) => {
    return http.get(`/trading/accounts/${accountId}/limits`)
  },

  updateTradingLimits: (accountId: number, limits: any) => {
    return http.put(`/trading/accounts/${accountId}/limits`, limits)
  },

  // 交易日历
  getTradingCalendar: (params?: {
    start_date?: string
    end_date?: string
    exchange?: string
  }) => {
    return http.get('/trading/calendar', { params })
  },

  // 交易费用
  getTradingFees: (accountId: number) => {
    return http.get(`/trading/accounts/${accountId}/fees`)
  },

  calculateCommission: (data: {
    symbol: string
    quantity: number
    price: number
    side: string
  }) => {
    return http.post('/trading/calculate-commission', data)
  },

  // 交易报告
  generateTradingReport: (params: {
    account_id: number
    start_date: string
    end_date: string
    report_type: string
    format: string
  }) => {
    return http.post('/trading/reports', params, {
      responseType: 'blob'
    })
  },

  // 交易审计
  getAuditLog: (params?: {
    account_id?: number
    action_type?: string
    start_date?: string
    end_date?: string
    page?: number
    page_size?: number
  }) => {
    return http.get('/trading/audit', { params })
  },

  // 交易权限
  getTradingPermissions: (accountId: number) => {
    return http.get(`/trading/accounts/${accountId}/permissions`)
  },

  updateTradingPermissions: (accountId: number, permissions: any) => {
    return http.put(`/trading/accounts/${accountId}/permissions`, permissions)
  },

  // 交易状态
  getTradingStatus: () => {
    return http.get('/trading/status')
  },

  // 紧急操作
  emergencyStop: (accountId: number) => {
    return http.post(`/trading/accounts/${accountId}/emergency-stop`)
  },

  resumeTrading: (accountId: number) => {
    return http.post(`/trading/accounts/${accountId}/resume`)
  }
}