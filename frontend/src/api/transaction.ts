/**
 * 交易流水API接口
 */
import { request } from '@/utils/request'

export interface Transaction {
  id: number
  transaction_id: string
  account_id: number
  transaction_type: string
  status: string
  amount: number
  currency: string
  exchange_rate: number
  balance_before?: number
  balance_after?: number
  order_id?: number
  position_id?: number
  symbol?: string
  description?: string
  reference_id?: string
  fee_amount: number
  tax_amount: number
  metadata: Record<string, any>
  transaction_time?: string
  created_at: string
  updated_at: string
}

export interface TransactionCreate {
  account_id: number
  transaction_type: string
  amount: number
  currency?: string
  exchange_rate?: number
  symbol?: string
  description?: string
  reference_id?: string
  fee_amount?: number
  tax_amount?: number
  metadata?: Record<string, any>
  transaction_id?: string
  status?: string
  balance_before?: number
  balance_after?: number
  order_id?: number
  position_id?: number
  transaction_time?: string
}

export interface TransactionSearchParams {
  account_ids?: number[]
  transaction_types?: string[]
  status_list?: string[]
  start_date?: string
  end_date?: string
  min_amount?: number
  max_amount?: number
  symbols?: string[]
  keyword?: string
  sort_field?: string
  sort_order?: string
  skip?: number
  limit?: number
}

export interface TransactionSearchResult {
  transactions: Transaction[]
  total_count: number
  page_info: {
    skip: number
    limit: number
    has_more: boolean
  }
}

export interface TransactionStatistics {
  period: string
  start_date: string
  end_date: string
  summary: {
    total_transactions: number
    total_income: number
    total_expense: number
    net_flow: number
    total_fees: number
    avg_transaction_amount: number
  }
  extremes: {
    max_income: {
      amount: number
      date?: string
      description?: string
    }
    max_expense: {
      amount: number
      date?: string
      description?: string
    }
  }
  daily_stats: Array<{
    date: string
    count: number
    total_amount: number
    total_volume: number
  }>
  type_breakdown: Array<{
    type: string
    count: number
    total_amount: number
    total_fees: number
  }>
}

export interface TransactionCategories {
  by_type: Array<{
    type: string
    count: number
    total_amount: number
    avg_amount: number
  }>
  by_status: Array<{
    status: string
    count: number
  }>
  by_currency: Array<{
    currency: string
    count: number
    total_amount: number
  }>
}

export interface CashFlowAnalysis {
  period: string
  interval: string
  start_date: string
  end_date: string
  cash_flow_data: Array<{
    period: string
    inflow: number
    outflow: number
    net_flow: number
  }>
  metrics: {
    volatility: number
    trend: number
    positive_ratio: number
    total_periods: number
  }
  inflow_analysis: {
    total_inflow: number
    by_type: Array<{
      type: string
      count: number
      total_amount: number
      avg_amount: number
      percentage: number
    }>
  }
  outflow_analysis: {
    total_outflow: number
    by_type: Array<{
      type: string
      count: number
      total_amount: number
      avg_amount: number
      percentage: number
    }>
  }
}

export interface SuspiciousTransaction {
  transaction_id: string
  transaction_time?: string
  amount: number
  transaction_type: string
  status: string
  description?: string
  suspicion_reasons: string[]
  risk_level: number
}

export interface TransactionAudit {
  audit_type: string
  total_issues: number
  issues: Array<{
    type: string
    transaction_id?: string
    account_id?: number
    description: string
  }>
  status: string
  audited_at: string
}

// 创建交易流水记录
export const createTransaction = (data: TransactionCreate): Promise<Transaction> => {
  return request.post('/api/v1/transactions/', data)
}

// 搜索交易流水
export const searchTransactions = (params: TransactionSearchParams): Promise<TransactionSearchResult> => {
  return request.get('/api/v1/transactions/search', { params })
}

// 获取单个交易流水
export const getTransaction = (transactionId: string): Promise<Transaction> => {
  return request.get(`/api/v1/transactions/${transactionId}`)
}

// 获取账户交易流水
export const getAccountTransactions = (
  accountId: number,
  params?: {
    skip?: number
    limit?: number
    transaction_types?: string[]
    status?: string
    start_date?: string
    end_date?: string
  }
): Promise<Transaction[]> => {
  return request.get(`/api/v1/transactions/account/${accountId}`, { params })
}

// 更新交易状态
export const updateTransactionStatus = (
  transactionId: string,
  status: string,
  metadata?: Record<string, any>
): Promise<Transaction> => {
  return request.put(`/api/v1/transactions/${transactionId}/status`, {
    status,
    metadata
  })
}

// 获取交易分类统计
export const getTransactionCategories = (): Promise<TransactionCategories> => {
  return request.get('/api/v1/transactions/categories/statistics')
}

// 获取交易统计分析
export const getTransactionStatistics = (period: string = 'month'): Promise<TransactionStatistics> => {
  return request.get('/api/v1/transactions/statistics/summary', {
    params: { period }
  })
}

// 现金流分析
export const getCashFlowAnalysis = (period: string = 'month'): Promise<CashFlowAnalysis> => {
  return request.get('/api/v1/transactions/analysis/cash-flow', {
    params: { period }
  })
}

// 生成交易报表
export const generateTransactionReport = (
  reportType: string = 'summary',
  startDate?: string,
  endDate?: string
): Promise<any> => {
  return request.get('/api/v1/transactions/reports/generate', {
    params: {
      report_type: reportType,
      start_date: startDate,
      end_date: endDate
    }
  })
}

// 导出交易流水
export const exportTransactions = (
  exportFormat: string = 'csv',
  params?: {
    account_ids?: number[]
    transaction_types?: string[]
    start_date?: string
    end_date?: string
  }
): Promise<Blob> => {
  return request.post('/api/v1/transactions/export', null, {
    params: {
      export_format: exportFormat,
      ...params
    },
    responseType: 'blob'
  })
}

// 交易流水审计
export const auditTransactions = (auditType: string = 'consistency'): Promise<TransactionAudit> => {
  return request.get('/api/v1/transactions/audit/check', {
    params: { audit_type: auditType }
  })
}

// 获取可疑交易
export const getSuspiciousTransactions = (days: number = 30): Promise<SuspiciousTransaction[]> => {
  return request.get('/api/v1/transactions/audit/suspicious', {
    params: { days }
  })
}

// 交易类型枚举
export const TransactionTypes = {
  DEPOSIT: 'DEPOSIT',
  WITHDRAWAL: 'WITHDRAWAL',
  TRADE_BUY: 'TRADE_BUY',
  TRADE_SELL: 'TRADE_SELL',
  DIVIDEND: 'DIVIDEND',
  INTEREST: 'INTEREST',
  FEE: 'FEE',
  TAX: 'TAX',
  TRANSFER_IN: 'TRANSFER_IN',
  TRANSFER_OUT: 'TRANSFER_OUT',
  ADJUSTMENT: 'ADJUSTMENT'
} as const

// 交易状态枚举
export const TransactionStatus = {
  PENDING: 'PENDING',
  PROCESSING: 'PROCESSING',
  COMPLETED: 'COMPLETED',
  FAILED: 'FAILED',
  CANCELLED: 'CANCELLED'
} as const

// 交易类型标签映射
export const TransactionTypeLabels: Record<string, string> = {
  DEPOSIT: '入金',
  WITHDRAWAL: '出金',
  TRADE_BUY: '买入',
  TRADE_SELL: '卖出',
  DIVIDEND: '分红',
  INTEREST: '利息',
  FEE: '手续费',
  TAX: '税费',
  TRANSFER_IN: '转入',
  TRANSFER_OUT: '转出',
  ADJUSTMENT: '调整'
}

// 交易状态标签映射
export const TransactionStatusLabels: Record<string, string> = {
  PENDING: '待处理',
  PROCESSING: '处理中',
  COMPLETED: '已完成',
  FAILED: '失败',
  CANCELLED: '已取消'
}

// 交易状态颜色映射
export const TransactionStatusColors: Record<string, string> = {
  PENDING: 'warning',
  PROCESSING: 'info',
  COMPLETED: 'success',
  FAILED: 'error',
  CANCELLED: 'default'
}

// 格式化交易金额
export const formatTransactionAmount = (amount: number, currency: string = 'USD'): string => {
  const formatter = new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
  return formatter.format(amount)
}

// 获取交易类型颜色
export const getTransactionTypeColor = (type: string): string => {
  const colorMap: Record<string, string> = {
    DEPOSIT: 'success',
    WITHDRAWAL: 'warning',
    TRADE_BUY: 'info',
    TRADE_SELL: 'primary',
    DIVIDEND: 'success',
    INTEREST: 'success',
    FEE: 'error',
    TAX: 'error',
    TRANSFER_IN: 'info',
    TRANSFER_OUT: 'warning',
    ADJUSTMENT: 'default'
  }
  return colorMap[type] || 'default'
}