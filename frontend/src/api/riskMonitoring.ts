/**
 * 风险监控API
 */
import { request } from '@/utils/request'

export interface RiskMetrics {
  account_metrics: {
    total_equity: number
    available_balance: number
    used_margin: number
    margin_ratio: number
    free_margin_ratio: number
  }
  position_metrics: {
    total_positions: number
    total_position_value: number
    total_unrealized_pnl: number
    position_concentration: {
      herfindahl_index: number
      top3_concentration: number
      top5_concentration: number
    }
    largest_position_ratio: number
  }
  risk_indicators: {
    leverage_ratio: number
    drawdown_ratio: number
    var_1d: number
    var_5d: number
    beta: number
    sharpe_ratio: number
  }
  order_metrics: {
    active_orders: number
    pending_buy_value: number
    pending_sell_value: number
  }
  timestamp: string
}

export interface RiskAlert {
  type: string
  severity: string
  title: string
  message: string
  value: number
  threshold: number
  timestamp: string
}

export interface RiskEvent {
  id: number
  event_type: string
  severity: string
  title: string
  description: string
  risk_value: number
  threshold_value: number
  triggered_rule_id?: number
  metadata: any
  is_resolved: boolean
  resolved_at?: string
  created_at: string
}

export interface RiskStatistics {
  period_days: number
  event_statistics: {
    total_events: number
    resolved_events: number
    unresolved_events: number
    resolution_rate: number
    severity_distribution: {
      HIGH: number
      MEDIUM: number
      LOW: number
    }
    event_type_distribution: Record<string, number>
  }
  current_risk_level: string
  risk_trend: string
  recommendations: string[]
}

export interface RiskDashboard {
  metrics: RiskMetrics
  alerts: {
    items: RiskAlert[]
    count: number
    has_high_risk: boolean
  }
  recent_events: {
    items: RiskEvent[]
    count: number
  }
  statistics: RiskStatistics
  last_updated: string
}

// 获取实时风险指标
export function getRealTimeRiskMetrics() {
  return request<RiskMetrics>({
    url: '/risk-monitoring/metrics',
    method: 'GET'
  })
}

// 获取风险预警
export function getRiskAlerts() {
  return request<{
    alerts: RiskAlert[]
    count: number
    has_high_risk: boolean
  }>({
    url: '/risk-monitoring/alerts',
    method: 'GET'
  })
}

// 记录风险事件
export function recordRiskEvent(eventData: {
  event_type: string
  severity: string
  title: string
  description?: string
  risk_value?: number
  threshold_value?: number
  triggered_rule_id?: number
  metadata?: any
}) {
  return request({
    url: '/risk-monitoring/events',
    method: 'POST',
    data: eventData
  })
}

// 获取风险事件
export function getRiskEvents(params: {
  days?: number
  event_type?: string
  severity?: string
}) {
  return request<{
    events: RiskEvent[]
    count: number
  }>({
    url: '/risk-monitoring/events',
    method: 'GET',
    params
  })
}

// 解决风险事件
export function resolveRiskEvent(eventId: number, resolutionNote?: string) {
  return request({
    url: `/risk-monitoring/events/${eventId}/resolve`,
    method: 'PUT',
    data: resolutionNote ? { resolution_note: resolutionNote } : {}
  })
}

// 获取风险统计
export function getRiskStatistics(days: number = 30) {
  return request<RiskStatistics>({
    url: '/risk-monitoring/statistics',
    method: 'GET',
    params: { days }
  })
}

// 获取风险仪表板数据
export function getRiskDashboard() {
  return request<RiskDashboard>({
    url: '/risk-monitoring/dashboard',
    method: 'GET'
  })
}

// 启动风险监控
export function startRiskMonitoring() {
  return request({
    url: '/risk-monitoring/monitor/start',
    method: 'POST'
  })
}

// 获取监控系统健康状态
export function getMonitoringHealth() {
  return request<{
    status: string
    timestamp: string
    version: string
  }>({
    url: '/risk-monitoring/health',
    method: 'GET'
  })
}