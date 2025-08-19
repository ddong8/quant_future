/**
 * 账户管理API接口
 */
import { request } from '@/utils/request'

export interface Account {
  id: number
  user_id: number
  account_id: string  // 后端使用account_id而不是account_number
  account_name: string
  broker?: string
  
  // 资金信息 - 匹配后端字段名
  balance?: number  // 总余额
  available?: number  // 可用资金
  margin?: number  // 保证金
  frozen?: number  // 冻结资金
  
  // 盈亏信息
  realized_pnl?: number
  unrealized_pnl?: number
  total_pnl?: number
  risk_ratio?: number
  
  // 状态
  is_active?: boolean
  
  // 时间信息
  created_at?: string
  updated_at?: string
  
  // 兼容前端显示的计算属性
  account_number?: string  // 映射到account_id
  account_type?: 'CASH' | 'MARGIN' | 'FUTURES' | 'OPTIONS'
  base_currency?: string
  status?: 'ACTIVE' | 'INACTIVE' | 'SUSPENDED' | 'CLOSED'
  risk_level?: 'LOW' | 'MEDIUM' | 'HIGH'
  total_assets?: number
  available_cash?: number
  frozen_cash?: number
  market_value?: number
  buying_power?: number
  last_activity_at?: string
}

export interface AccountTransaction {
  id: number
  account_id: number
  transaction_type: 'DEPOSIT' | 'WITHDRAW' | 'TRADE' | 'FEE' | 'INTEREST' | 'DIVIDEND' | 'TRANSFER' | 'FREEZE' | 'UNFREEZE'
  amount: number
  balance_before: number
  balance_after: number
  currency: string
  description?: string
  reference_id?: string
  order_id?: number
  position_id?: number
  symbol?: string
  status: 'PENDING' | 'COMPLETED' | 'FAILED' | 'CANCELLED'
  created_at: string
  updated_at: string
}

export interface DepositRequest {
  amount: number
  description?: string
}

export interface WithdrawRequest {
  amount: number
  description?: string
}

export interface TransferRequest {
  to_account_id: string
  amount: number
  description?: string
}

export interface AccountSettings {
  auto_transfer: boolean
  risk_alert_threshold: number
  margin_call_threshold?: number
  notification_preferences: {
    email: boolean
    sms: boolean
    push: boolean
  }
}

export const accountApi = {
  /**
   * 获取账户列表
   */
  async getAccounts(): Promise<{ data: Account[] }> {
    return request.get('/v1/accounts')
  },

  /**
   * 获取账户详情
   */
  async getAccount(accountId: string): Promise<{ data: Account }> {
    return request.get(`/v1/accounts/${accountId}`)
  },

  /**
   * 创建账户
   */
  async createAccount(data: {
    account_type: Account['account_type']
    currency: string
    initial_balance?: number
  }): Promise<{ data: Account }> {
    return request.post('/v1/accounts', data)
  },

  /**
   * 更新账户设置
   */
  async updateAccountSettings(accountId: string, settings: Partial<AccountSettings>): Promise<{ data: Account }> {
    return request.put(`/v1/accounts/${accountId}/settings`, settings)
  },

  /**
   * 充值
   */
  async deposit(accountId: string, data: DepositRequest): Promise<{ data: AccountTransaction }> {
    return request.post(`/v1/accounts/${accountId}/deposit`, data)
  },

  /**
   * 提现
   */
  async withdraw(accountId: string, data: WithdrawRequest): Promise<{ data: AccountTransaction }> {
    return request.post(`/v1/accounts/${accountId}/withdraw`, data)
  },

  /**
   * 转账
   */
  async transfer(fromAccountId: string, data: TransferRequest): Promise<{ data: AccountTransaction }> {
    return request.post(`/v1/accounts/${fromAccountId}/transfer`, data)
  },

  /**
   * 获取交易记录
   */
  async getTransactions(accountId?: string, params?: {
    transaction_type?: AccountTransaction['transaction_type']
    status?: AccountTransaction['status']
    start_date?: string
    end_date?: string
    page?: number
    page_size?: number
  }): Promise<{ 
    data: { 
      data: AccountTransaction[]
      meta: {
        total: number
        page: number
        page_size: number
        total_pages: number
      }
    }
  }> {
    const url = accountId ? `/v1/accounts/${accountId}/transactions` : '/v1/transactions'
    return request.get(url, { params })
  },

  /**
   * 获取账户统计
   */
  async getAccountStats(accountId: string, period?: '1d' | '7d' | '30d' | '90d'): Promise<{
    data: {
      total_deposits: number
      total_withdrawals: number
      total_trades: number
      profit_loss: number
      return_rate: number
      max_drawdown: number
      sharpe_ratio: number
    }
  }> {
    return request.get(`/v1/accounts/${accountId}/stats`, { params: { period } })
  },

  /**
   * 获取资金流水图表数据
   */
  async getBalanceHistory(accountId: string, period?: '1d' | '7d' | '30d' | '90d'): Promise<{
    data: Array<{
      date: string
      balance: number
      available_balance: number
      frozen_balance: number
    }>
  }> {
    return request.get(`/v1/accounts/${accountId}/balance-history`, { params: { period } })
  },

  /**
   * 冻结/解冻账户
   */
  async toggleAccountStatus(accountId: string, status: Account['status']): Promise<{ data: Account }> {
    return request.patch(`/v1/accounts/${accountId}/status`, { status })
  },

  /**
   * 删除账户
   */
  async deleteAccount(accountId: string): Promise<{ message: string }> {
    return request.delete(`/v1/accounts/${accountId}`)
  }
}

// 导出便捷方法
export const {
  getAccounts,
  getAccount,
  createAccount,
  updateAccountSettings,
  deposit,
  withdraw,
  transfer,
  getTransactions,
  getAccountStats,
  getBalanceHistory,
  toggleAccountStatus,
  deleteAccount
} = accountApi