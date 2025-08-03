/**
 * 持仓管理API
 */
import { request } from '@/utils/request'

export interface Position {
  id: number
  uuid: string
  symbol: string
  position_type: 'LONG' | 'SHORT'
  status: 'OPEN' | 'CLOSED' | 'SUSPENDED'
  quantity: number
  available_quantity: number
  frozen_quantity: number
  average_cost: number
  total_cost: number
  realized_pnl: number
  unrealized_pnl: number
  total_pnl: number
  current_price?: number
  market_value?: number
  max_drawdown: number
  max_profit: number
  return_rate: number
  unrealized_return_rate: number
  stop_loss_price?: number
  take_profit_price?: number
  stop_loss_order_id?: number
  take_profit_order_id?: number
  strategy_id?: number
  backtest_id?: number
  source: string
  source_id?: string
  tags: string[]
  notes?: string
  user_id: number
  opened_at?: string
  closed_at?: string
  created_at: string
  updated_at: string
  is_long: boolean
  is_short: boolean
  is_open: boolean
  is_closed: boolean
}

export interface PositionHistory {
  id: number
  uuid: string
  position_id: number
  action: string
  details: Record<string, any>
  quantity_snapshot?: number
  average_cost_snapshot?: number
  total_cost_snapshot?: number
  realized_pnl_snapshot?: number
  unrealized_pnl_snapshot?: number
  current_price_snapshot?: number
  created_at: string
}

export interface PortfolioMetrics {
  total_positions: number
  total_market_value: number
  total_cost: number
  total_pnl: number
  total_realized_pnl: number
  total_unrealized_pnl: number
  return_rate: number
  positions_by_symbol: Record<string, any>
}

export interface PositionStatistics {
  total_positions: number
  open_positions: number
  closed_positions: number
  profit_positions: number
  loss_positions: number
  win_rate: number
  portfolio_metrics: PortfolioMetrics
}

export interface PositionFilter {
  status?: 'OPEN' | 'CLOSED' | 'SUSPENDED'
  symbol?: string
  position_type?: 'LONG' | 'SHORT'
  strategy_id?: number
  backtest_id?: number
  page?: number
  size?: number
}

export interface StopLossRequest {
  stop_price: number
  order_id?: number
}

export interface TakeProfitRequest {
  profit_price: number
  order_id?: number
}

export interface ClosePositionRequest {
  close_price: number
  reason?: string
}

export interface FreezeQuantityRequest {
  quantity: number
  reason?: string
}

export interface UnfreezeQuantityRequest {
  quantity: number
  reason?: string
}

export interface MarketDataUpdate {
  symbol: string
  price: number
  timestamp?: string
}

export interface BatchMarketDataUpdate {
  price_data: Record<string, number>
  timestamp?: string
}

// 持仓管理API
export const positionApi = {
  // 获取持仓列表
  getPositions(params?: PositionFilter) {
    return request.get<{
      items: Position[]
      total: number
      page: number
      size: number
      has_next: boolean
    }>('/positions', { params })
  },

  // 获取持仓详情
  getPosition(id: number) {
    return request.get<Position>(`/positions/${id}`)
  },

  // 更新持仓信息
  updatePosition(id: number, data: {
    stop_loss_price?: number
    take_profit_price?: number
    notes?: string
    tags?: string[]
  }) {
    return request.put<Position>(`/positions/${id}`, data)
  },

  // 设置止损
  setStopLoss(id: number, data: StopLossRequest) {
    return request.post<Position>(`/positions/${id}/stop-loss`, data)
  },

  // 设置止盈
  setTakeProfit(id: number, data: TakeProfitRequest) {
    return request.post<Position>(`/positions/${id}/take-profit`, data)
  },

  // 平仓
  closePosition(id: number, data: ClosePositionRequest) {
    return request.post<Position>(`/positions/${id}/close`, data)
  },

  // 冻结持仓数量
  freezeQuantity(id: number, data: FreezeQuantityRequest) {
    return request.post<Position>(`/positions/${id}/freeze`, data)
  },

  // 解冻持仓数量
  unfreezeQuantity(id: number, data: UnfreezeQuantityRequest) {
    return request.post<Position>(`/positions/${id}/unfreeze`, data)
  },

  // 获取持仓历史记录
  getPositionHistory(id: number, params?: {
    action?: string
    page?: number
    size?: number
  }) {
    return request.get<{
      items: PositionHistory[]
      total: number
      page: number
      size: number
      has_next: boolean
    }>(`/positions/${id}/history`, { params })
  },

  // 获取投资组合摘要
  getPortfolioSummary() {
    return request.get<PortfolioMetrics>('/positions/portfolio/summary')
  },

  // 获取持仓统计信息
  getPositionStatistics() {
    return request.get<PositionStatistics>('/positions/portfolio/statistics')
  },

  // 根据标的获取持仓
  getPositionBySymbol(symbol: string, params?: {
    strategy_id?: number
    backtest_id?: number
  }) {
    return request.get<Position | null>(`/positions/symbols/${symbol}`, { params })
  },

  // 检查止损止盈触发
  checkStopTriggers() {
    return request.get<Array<{
      position_id: number
      symbol: string
      trigger_type: string
      trigger_price: number
      current_price: number
      order_id?: number
    }>>('/positions/stop-triggers/check')
  },

  // 批量更新市场数据
  updateMarketData(data: BatchMarketDataUpdate) {
    return request.post('/positions/market-data/update', data)
  },

  // 检查持仓数据一致性
  checkConsistency() {
    return request.post<{
      total_positions_checked: number
      inconsistencies_found: number
      inconsistencies: Array<{
        position_id: number
        symbol: string
        field: string
        current_value: number
        calculated_value: number
        difference: number
      }>
      is_consistent: boolean
    }>('/positions/consistency/check')
  },

  // 修复持仓数据
  repairData(position_id?: number) {
    return request.post<{
      repaired_positions: number
      message: string
    }>('/positions/consistency/repair', {}, {
      params: position_id ? { position_id } : undefined
    })
  },

  // 导出持仓数据
  exportCSV(params?: {
    status?: 'OPEN' | 'CLOSED' | 'SUSPENDED'
    symbol?: string
  }) {
    return request.get<{
      csv_content: string
      filename: string
      record_count: number
    }>('/positions/export/csv', { params })
  }
}