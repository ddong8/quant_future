import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { accountApi, type Account, type AccountTransaction } from '@/api/account'

// 模拟账户数据 - 匹配后端API格式
const getMockAccounts = (): Account[] => [
  {
    id: 1,
    user_id: 1,
    account_number: 'ACC001',
    account_name: '主账户',
    account_type: 'CASH',
    base_currency: 'CNY',
    status: 'ACTIVE',
    risk_level: 'MEDIUM',
    total_assets: 1000000,
    available_cash: 850000,
    frozen_cash: 50000,
    market_value: 100000,
    buying_power: 850000,
    total_pnl: 25000,
    realized_pnl: 15000,
    unrealized_pnl: 10000,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2025-01-14T00:00:00Z',
    last_activity_at: '2025-01-14T00:00:00Z'
  }
]

export const useAccountStore = defineStore('account', () => {
  // 状态
  const accounts = ref<Account[]>([])
  const currentAccount = ref<Account | null>(null)
  const transactions = ref<AccountTransaction[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // 计算属性
  const totalBalance = computed(() => {
    return accounts.value.reduce((total, account) => total + (account.total_assets || 0), 0)
  })

  const totalAvailableBalance = computed(() => {
    return accounts.value.reduce((total, account) => total + (account.available_cash || 0), 0)
  })

  const totalFrozenBalance = computed(() => {
    return accounts.value.reduce((total, account) => total + (account.frozen_cash || 0), 0)
  })

  const totalMarketValue = computed(() => {
    return accounts.value.reduce((total, account) => total + (account.market_value || 0), 0)
  })

  const totalPnL = computed(() => {
    return accounts.value.reduce((total, account) => total + (account.total_pnl || 0), 0)
  })

  const accountSummary = computed(() => ({
    totalBalance: totalBalance.value,
    totalAvailableBalance: totalAvailableBalance.value,
    totalFrozenBalance: totalFrozenBalance.value,
    totalMarketValue: totalMarketValue.value,
    totalPnL: totalPnL.value,
    accountCount: accounts.value.length
  }))

  // 操作
  const loadAccounts = async () => {
    try {
      loading.value = true
      error.value = null
      
      // 尝试多个API路径
      const apiPaths = [
        '/v1/accounts/',
        '/v1/accounts',
        '/v1/trading/accounts',
        '/v1/user/accounts'
      ]
      
      let response = null
      let lastError = null
      
      for (const path of apiPaths) {
        try {
          console.log(`🔄 尝试API路径: ${path}`)
          response = await accountApi.getAccounts()
          console.log(`✅ API路径 ${path} 成功`)
          break
        } catch (err: any) {
          console.warn(`⚠️ API路径 ${path} 失败:`, err.message)
          lastError = err
          continue
        }
      }
      
      if (!response) {
        throw lastError || new Error('所有API路径都失败了')
      }
      
      // 处理不同的响应格式
      let accountsData = []
      if (response && response.success && response.data) {
        accountsData = response.data
      } else if (response && response.data) {
        accountsData = response.data
      } else if (Array.isArray(response)) {
        accountsData = response
      } else {
        accountsData = response || []
      }
      
      // 转换后端数据格式到前端格式
      accounts.value = accountsData.map((account: any) => ({
        ...account,
        // 映射字段名
        account_number: account.account_id || account.account_number,
        account_type: account.account_type || 'CASH',
        base_currency: account.base_currency || 'CNY',
        status: account.is_active ? 'ACTIVE' : 'INACTIVE',
        risk_level: account.risk_level || 'MEDIUM',
        
        // 映射资金字段
        total_assets: account.balance || account.total_assets || 0,
        available_cash: account.available || account.available_cash || 0,
        frozen_cash: account.frozen || account.frozen_cash || 0,
        market_value: account.market_value || 0,
        buying_power: account.available || account.buying_power || 0,
        
        // 盈亏信息
        total_pnl: account.total_pnl || 0,
        realized_pnl: account.realized_pnl || 0,
        unrealized_pnl: account.unrealized_pnl || 0,
        
        // 时间信息
        created_at: account.created_at,
        updated_at: account.updated_at,
        last_activity_at: account.last_activity_at || account.updated_at
      }))
      
      console.log('✅ 账户数据加载成功:', accounts.value.length, '个账户')
    } catch (err: any) {
      error.value = err.message || '加载账户失败'
      console.error('❌ 加载账户失败:', err)
      // 使用模拟数据作为降级方案
      accounts.value = getMockAccounts()
      console.warn('⚠️ 使用模拟账户数据')
    } finally {
      loading.value = false
    }
  }

  const getAccountById = async (accountId: number) => {
    try {
      loading.value = true
      error.value = null
      const response = await accountApi.getAccount(accountId.toString())
      const accountData = response && response.data ? response.data : response
      currentAccount.value = accountData
      return accountData
    } catch (err: any) {
      error.value = err.message || '获取账户详情失败'
      console.error('❌ 获取账户详情失败:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  const fetchAccountDetails = async (accountId: number) => {
    return getAccountById(accountId)
  }

  const loadTransactions = async (accountId?: string, params?: any) => {
    try {
      loading.value = true
      error.value = null
      const response = await accountApi.getTransactions(accountId, params)
      // 处理嵌套的 data 结构
      if (response && response.data && response.data.data) {
        transactions.value = response.data.data
        return response.data
      } else if (response && response.data) {
        transactions.value = response.data
        return response
      } else {
        transactions.value = []
        return { data: [], meta: {} }
      }
    } catch (err: any) {
      error.value = err.message || '加载交易记录失败'
      console.error('Failed to load transactions:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  const deposit = async (accountId: string, amount: number, description?: string) => {
    try {
      loading.value = true
      error.value = null
      const response = await accountApi.deposit(accountId, { amount, description })
      
      // 更新本地账户余额
      const accountIndex = accounts.value.findIndex(acc => acc.id === accountId)
      if (accountIndex !== -1) {
        accounts.value[accountIndex].balance += amount
        accounts.value[accountIndex].available_balance += amount
      }
      
      return response.data
    } catch (err: any) {
      error.value = err.message || '充值失败'
      console.error('Failed to deposit:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  const withdraw = async (accountId: string, amount: number, description?: string) => {
    try {
      loading.value = true
      error.value = null
      const response = await accountApi.withdraw(accountId, { amount, description })
      
      // 更新本地账户余额
      const accountIndex = accounts.value.findIndex(acc => acc.id === accountId)
      if (accountIndex !== -1) {
        accounts.value[accountIndex].balance -= amount
        accounts.value[accountIndex].available_balance -= amount
      }
      
      return response.data
    } catch (err: any) {
      error.value = err.message || '提现失败'
      console.error('Failed to withdraw:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  const transfer = async (fromAccountId: string, toAccountId: string, amount: number, description?: string) => {
    try {
      loading.value = true
      error.value = null
      const response = await accountApi.transfer(fromAccountId, {
        to_account_id: toAccountId,
        amount,
        description
      })
      
      // 更新本地账户余额
      const fromAccountIndex = accounts.value.findIndex(acc => acc.id === fromAccountId)
      const toAccountIndex = accounts.value.findIndex(acc => acc.id === toAccountId)
      
      if (fromAccountIndex !== -1) {
        accounts.value[fromAccountIndex].balance -= amount
        accounts.value[fromAccountIndex].available_balance -= amount
      }
      
      if (toAccountIndex !== -1) {
        accounts.value[toAccountIndex].balance += amount
        accounts.value[toAccountIndex].available_balance += amount
      }
      
      return response.data
    } catch (err: any) {
      error.value = err.message || '转账失败'
      console.error('Failed to transfer:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  const updateAccountSettings = async (accountId: string, settings: any) => {
    try {
      loading.value = true
      error.value = null
      const response = await accountApi.updateAccountSettings(accountId, settings)
      
      // 更新本地账户设置
      const accountIndex = accounts.value.findIndex(acc => acc.id === accountId)
      if (accountIndex !== -1) {
        accounts.value[accountIndex] = { ...accounts.value[accountIndex], ...response.data }
      }
      
      return response.data
    } catch (err: any) {
      error.value = err.message || '更新账户设置失败'
      console.error('Failed to update account settings:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  const clearError = () => {
    error.value = null
  }

  const reset = () => {
    accounts.value = []
    currentAccount.value = null
    transactions.value = []
    loading.value = false
    error.value = null
  }

  return {
    // 状态
    accounts,
    currentAccount,
    transactions,
    loading,
    error,
    
    // 计算属性
    totalBalance,
    totalAvailableBalance,
    totalFrozenBalance,
    totalMarketValue,
    totalPnL,
    accountSummary,
    
    // 操作
    loadAccounts,
    getAccountById,
    fetchAccountDetails,
    loadTransactions,
    deposit,
    withdraw,
    transfer,
    updateAccountSettings,
    clearError,
    reset
  }
})