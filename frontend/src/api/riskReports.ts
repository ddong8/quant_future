/**
 * 风险报告和分析API
 */
import { request } from '@/utils/request'

export interface RiskReportRequest {
  user_id: number
  report_type: 'daily' | 'weekly' | 'monthly' | 'custom'
  start_date: string
  end_date: string
  custom_config?: Record<string, any>
}

export interface RiskReport {
  report_id: string
  user_id: number
  report_type: string
  generated_at: string
  period: {
    start_date: string
    end_date: string
  }
  executive_summary: {
    risk_score: number
    risk_level: string
    total_events: number
    critical_events: number
    high_events: number
    portfolio_value: number
    max_drawdown: number
    var_95: number
    key_findings: string[]
  }
  risk_metrics: {
    period_return: number
    avg_daily_return: number
    return_volatility: number
    max_drawdown: number
    avg_var_95: number
    max_var_95: number
    avg_sharpe_ratio: number
    max_leverage: number
    time_series: {
      dates: string[]
      portfolio_values: number[]
      daily_returns: number[]
      volatilities: number[]
      drawdowns: number[]
      var_values: number[]
    }
  }
  risk_events: {
    total_events: number
    severity_distribution: Record<string, number>
    type_distribution: Record<string, number>
    recent_critical_events: Array<{
      id: number
      type: string
      severity: string
      title: string
      message: string
      created_at: string
    }>
  }
  position_analysis: {
    total_positions: number
    total_exposure: number
    top_positions: Array<{
      symbol: string
      quantity: number
      market_value: number
      concentration: number
      unrealized_pnl: number
    }>
    top_5_concentration: number
    sector_exposure: Record<string, number>
  }
  risk_attribution: {
    total_var: number
    position_contributions: Array<{
      symbol: string
      var_contribution: number
      weight: number
    }>
    factor_contributions: Record<string, number>
  }
  trend_analysis: {
    metric_trends: Record<string, {
      direction: string
      magnitude: number
      current_value: number
      period_change: number
    }>
    risk_forecast: {
      forecast_period: string
      current_var: number
      forecasted_var: number
      trend_direction: string
      confidence: string
    }
  }
  recommendations: Array<{
    category: string
    priority: string
    title: string
    description: string
    action_items: string[]
  }>
  charts_data: {
    risk_metrics_timeline: {
      dates: string[]
      var_95: number[]
      volatility: number[]
      max_drawdown: number[]
      portfolio_value: number[]
    }
    risk_events_distribution: {
      labels: string[]
      values: number[]
    }
    position_concentration: {
      symbols: string[]
      values: number[]
    }
  }
}

export interface ReportTemplate {
  id: string
  name: string
  description: string
  report_type: string
  sections: string[] | string
}

export interface ReportHistory {
  report_id: string
  user_id: number
  report_type: string
  generated_at: string
  period: {
    start_date: string
    end_date: string
  }
  risk_score: number
  status: string
}

export interface RiskAnalysisRequest {
  user_id: number
  start_date: string
  end_date: string
  analysis_types: string[]
}

export interface RiskAnalysisResult {
  analysis_id: string
  user_id: number
  period: {
    start_date: string
    end_date: string
  }
  analysis_types: string[]
  results: Record<string, any>
  generated_at: string
}

export interface ReportScheduleConfig {
  user_id: number
  daily_enabled: boolean
  weekly_enabled: boolean
  monthly_enabled: boolean
  email_delivery: boolean
  notification_delivery: boolean
  custom_schedule?: string
}

export interface RiskInsightsSummary {
  user_id: number
  period_days: number
  risk_score: number
  key_findings: string[]
  recommendations: Array<{
    category: string
    priority: string
    title: string
    description: string
    action_items: string[]
  }>
  trend_summary: string
  generated_at: string
}

// 风险报告API
export const riskReportsApi = {
  // 生成风险报告
  generateReport: (data: RiskReportRequest): Promise<RiskReport> => {
    return request.post('/risk-reports/generate', data)
  },

  // 获取报告模板
  getReportTemplates: (): Promise<{ templates: ReportTemplate[] }> => {
    return request.get('/risk-reports/templates')
  },

  // 获取报告历史
  getReportHistory: (params?: {
    user_id?: number
    report_type?: string
    start_date?: string
    end_date?: string
    skip?: number
    limit?: number
  }): Promise<{
    total: number
    reports: ReportHistory[]
  }> => {
    return request.get('/risk-reports/history', { params })
  },

  // 获取报告详情
  getReportDetail: (reportId: string): Promise<RiskReport> => {
    return request.get(`/risk-reports/${reportId}`)
  },

  // 导出报告
  exportReport: (reportId: string, format: 'pdf' | 'excel' | 'json'): string => {
    return `/v1/risk-reports/${reportId}/export?format=${format}`
  },

  // 配置定期报告
  scheduleReports: (config: ReportScheduleConfig): Promise<{
    message: string
    config: ReportScheduleConfig
  }> => {
    return request.post('/risk-reports/schedule', config)
  },

  // 获取报告调度配置
  getReportSchedule: (userId: number): Promise<ReportScheduleConfig> => {
    return request.get(`/risk-reports/schedule/${userId}`)
  },

  // 执行风险数据分析
  analyzeRiskData: (data: RiskAnalysisRequest): Promise<RiskAnalysisResult> => {
    return request.post('/risk-reports/analyze', data)
  },

  // 获取风险洞察摘要
  getRiskInsightsSummary: (params?: {
    user_id?: number
    days?: number
  }): Promise<RiskInsightsSummary> => {
    return request.get('/risk-reports/insights/summary', { params })
  },

  // 批量生成报告
  batchGenerateReports: (data: {
    user_ids: number[]
    report_type: string
    start_date: string
    end_date: string
  }): Promise<{
    message: string
    user_count: number
    report_type: string
  }> => {
    return request.post('/risk-reports/batch-generate', data)
  }
}

export default riskReportsApi