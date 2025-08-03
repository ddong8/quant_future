/**
 * 市场深度和价格提醒API
 */
import { request } from '@/utils/request'

export interface DepthItem {
  price: number
  volume: number
  cumulative_volume: number
  amount: number
}

export interface MarketDepth {
  symbol: string
  timestamp: number
  bids: DepthItem[]
  asks: DepthItem[]
  statistics: {
    best_bid: number
    best_ask: number
    spread: number
    spread_percent: number
    total_bid_volume: number
    total_ask_volume: number
    bid_count: number
    ask_count: number
  }
}

export interface DepthAnalysis {
  symbol: string
  bid_ratio: number
  ask_ratio: number
  imbalance_ratio: number
  imbalance_level: string
  bias: string
  total_bid_amount: number
  total_ask_amount: number
}

export interface PriceAlert {
  id: number
  symbol: {
    id: number
    symbol: string
    name: string
  }
  alert_type: string
  condition_value: number
  comparison_operator: string
  is_active: boolean
  is_repeatable: boolean
  notification_methods: string[]
  triggered_at?: string
  triggered_price?: number
  trigger_count: number
  expires_at?: string
  note?: string
  created_at: string
}

export interface MarketAnomaly {
  id: number
  symbol: {
    id: number
    symbol: string
    name: string
  }
  anomaly_type: string
  severity: string
  title: string
  description: string
  trigger_price: number
  price_change: number
  price_change_percent: number
  volume_ratio: number
  detected_at: string
  is_processed: boolean
  is_notified: boolean
}

// 获取市场深度数据
export function getMarketDepth(symbolCode: string, depthLevel: number = 20) {
  return request<MarketDepth>({
    url: `/depth/depth/${symbolCode}`,
    method: 'GET',
    params: { depth_level: depthLevel }
  })
}

// 分析深度失衡
export function analyzeDepthImbalance(symbolCode: string) {
  return request<DepthAnalysis>({
    url: `/depth/depth/${symbolCode}/analysis`,
    method: 'GET'
  })
}

// 创建价格提醒
export function createPriceAlert(alertData: {
  symbol_code: string
  alert_type: string
  condition_value: number
  comparison_operator: string
  is_active?: boolean
  is_repeatable?: boolean
  notification_methods?: string[]
  expires_at?: string
  note?: string
}) {
  return request({
    url: '/depth/alerts',
    method: 'POST',
    data: alertData
  })
}

// 获取用户的价格提醒
export function getUserAlerts(isActive?: boolean) {
  const params: any = {}
  if (isActive !== undefined) params.is_active = isActive

  return request<{
    alerts: PriceAlert[]
    count: number
  }>({
    url: '/depth/alerts',
    method: 'GET',
    params
  })
}

// 更新价格提醒
export function updatePriceAlert(alertId: number, updateData: {
  condition_value?: number
  comparison_operator?: string
  is_active?: boolean
  is_repeatable?: boolean
  notification_methods?: string[]
  expires_at?: string
  note?: string
}) {
  return request({
    url: `/depth/alerts/${alertId}`,
    method: 'PUT',
    data: updateData
  })
}

// 删除价格提醒
export function deletePriceAlert(alertId: number) {
  return request({
    url: `/depth/alerts/${alertId}`,
    method: 'DELETE'
  })
}

// 获取市场异动
export function getMarketAnomalies(hours: number = 24, severity?: string) {
  const params: any = { hours }
  if (severity) params.severity = severity

  return request<{
    anomalies: MarketAnomaly[]
    count: number
  }>({
    url: '/depth/anomalies',
    method: 'GET',
    params
  })
}

// 检测指定标的的市场异动
export function detectSymbolAnomalies(symbolCode: string) {
  return request<{
    symbol: string
    anomalies: MarketAnomaly[]
    count: number
  }>({
    url: `/depth/anomalies/detect/${symbolCode}`,
    method: 'POST'
  })
}

// 检查指定标的的价格提醒
export function checkSymbolAlerts(symbolCode: string, currentPrice: number) {
  return request<{
    symbol: string
    current_price: number
    triggered_alerts: any[]
    count: number
  }>({
    url: `/depth/alerts/check/${symbolCode}`,
    method: 'POST',
    data: { current_price: currentPrice }
  })
}