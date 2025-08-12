/**
 * 账户管理API接口
 */
import { request } from '@/utils/request'

export interface Account {
  id: string
  user_id: string
  account_type: 'CASH' | 'MARGIN' | 'FUTURES'
  currency: string
  balance: number
  available_balance: number
  frozen_balance: number
  margin_balance?: number
  equity?: number
  margin_ratio?: number
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH'
  status: 'ACTIVE' | 'SUSPENDED' | 'CLOSED'
  created_at: string
  updated_at: string
}

export interface AccountTransaction {
  id: string
  account_id: string
  transaction_type: 'DEPOSIT' | 'WITHDRAW' | 'TRADE' | 'FEE' | 'INTEREST' | 'DIVIDEND' | 'TRANSFER'
  amount: number
  balance_before: number
  balance_after: number
  currency: string
  description?: string
  reference_id?: string
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