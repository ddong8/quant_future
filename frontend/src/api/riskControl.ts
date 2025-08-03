/**
 * 风险控制自动化执行API
 */
import { request } from '@/utils/request'

export interface RiskCheckRequest {
  user_id: number
  order_data: Record<string, any>
}

export interface RiskAction {
  action_type: string
  parameters: Record<string, any>
  reason: string
}

export interface RiskCheckResult {
  passed: boolean
  risk_level: string
  message: string
  actions: RiskAction[]
}

export interface RiskControlActionRequest {
  user_id: number
  action: string
  context: Record<string, any>
}

export interface RiskControlActionResult {
  success: boolean
  action: string
  user_id: number
  executed_at: string
  message: string
}

export interface EmergencyRiskControlRequest {
  user_id: number
  reason: string
}

export interface RiskMonitoringStatus {
  user_id: number
  is_monitoring: boolean
  last_check_time?: string
  risk_level: string
  active_rules_count: number
  triggered_actions_count: number
}

export interface RiskControlConfig {
  max_position_size_ratio: number
  max_daily_loss_ratio: number
  margin_call_ratio: number
  liquidation_ratio: number
  max_order_value_ratio: number
  auto_risk_control_enabled: boolean
  emergency_control_enabled: boolean
}

export interface RiskActionHistory {
  id: number
  user_id: number
  action: string
  context: Record<string, any>
  success: boolean
  error?: string
  created_at: string
  severity: string
  description: string
}

export interface RiskControlStatistics {
  time_range: {
    start_date: string
    end_date: string
  }
  total_events: number
  event_type_distribution: Record<string, number>
  severity_distribution: Record<string, number>
  risk_actions: {
    total_actions: number
    success_rate: number
    action_breakdown: Record<string, {
      total: number
      success: number
      failure: number
    }>
  }
}

export interface RiskControlHealth {
  status: 'healthy' | 'unhealthy'
  timestamp: string
  components?: {
    risk_engine: string
    notification_service: string
    websocket_manager: string
    database: string
  }
  config?: RiskControlConfig
  active_monitoring_sessions?: number
  error?: string
}

// 风险控制API
export const riskControlApi = {
  // 订单风险检查
  checkOrderRisk: (data: RiskCheckRequest): Promise<RiskCheckResult> => {
    return request.post('/risk-control/check-order', data)
  },

  // 执行风险控制动作
  executeRiskAction: (data: RiskControlActionRequest): Promise<RiskControlActionResult> => {
    return request.post('/risk-control/execute-action', data)
  },

  // 紧急风险控制
  emergencyRiskControl: (data: EmergencyRiskControlRequest): Promise<RiskControlActionResult> => {
    return request.post('/risk-control/emergency-control', data)
  },

  // 启动风险监控
  startRiskMonitoring: (userId: number): Promise<{ message: string }> => {
    return request.post(`/risk-control/monitor/${userId}`)
  },

  // 获取监控状态
  getMonitoringStatus: (userId: number): Promise<RiskMonitoringStatus> => {
    return request.get(`/risk-control/monitoring-status/${userId}`)
  },

  // 获取风险控制配置
  getRiskControlConfig: (): Promise<RiskControlConfig> => {
    return request.get('/risk-control/config')
  },

  // 更新风险控制配置
  updateRiskControlConfig: (config: RiskControlConfig): Promise<RiskControlConfig> => {
    return request.put('/risk-control/config', config)
  },

  // 获取风险控制动作历史
  getRiskActionsHistory: (params?: {
    user_id?: number
    start_date?: string
    end_date?: string
    action_type?: string
    skip?: number
    limit?: number
  }): Promise<{
    total: number
    events: RiskActionHistory[]
  }> => {
    return request.get('/risk-control/actions/history', { params })
  },

  // 获取风险控制统计
  getRiskControlStatistics: (params?: {
    start_date?: string
    end_date?: string
  }): Promise<RiskControlStatistics> => {
    return request.get('/risk-control/statistics', { params })
  },

  // 测试风险场景
  testRiskScenario: (scenarioData: Record<string, any>): Promise<{
    scenario: string
    result?: any
    success?: boolean
  }> => {
    return request.post('/risk-control/test-scenario', scenarioData)
  },

  // 健康检查
  healthCheck: (): Promise<RiskControlHealth> => {
    return request.get('/risk-control/health')
  }
}

export default riskControlApi