import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { accountApi, type Account, type AccountTransaction } from '@/api/account'

export const useAccountStore = defineStore('account', () => {
  // 状态
  const accounts = ref<Account[]>([])
  const currentAccount = ref<Account | null>(null)
  const transactions = ref<AccountTransaction[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // 计算属性
  const totalBalance = computed(() => {
    return accounts.value.reduce((total, account) => total + account.balance, 0)
  })

  const totalAvailableBalance = computed(() => {
    return accounts.value.reduce((total, account) => total + account.available_balance, 0)
  })

  const totalFrozenBalance = computed(() => {
    return accounts.value.reduce((total, account) => total + account.frozen_balance, 0)
  })

  const accountSummary = computed(() => ({
    totalBalance: totalBalance.value,
    totalAvailableBalance: totalAvailableBalance.value,
    totalFrozenBalance: totalFrozenBalance.value,
    accountCount: accounts.value.length
  }))

  // 操作
  const loadAccounts = async () => {
    try {
      loading.value = true
      error.value = null
      const response = await accountApi.getAccounts()
      // 后端返回格式: { success: true, data: [...] }
      // 响应拦截器返回完整的 data 对象
      if (response && response.data) {
        accounts.value = response.data
      } else {
        accounts.value = response || []
      }
    } catch (err: any) {
      error.value = err.message || '加载账户失败'
      console.error('Failed to load accounts:', err)
    } finally {
      loading.value = false
    }
  }

  const getAccountById = async (accountId: string) => {
    try {
      loading.value = true
      error.value = null
      const response = await accountApi.getAccount(accountId)
      const accountData = response && response.data ? response.data : response
      currentAccount.value = accountData
      return accountData
    } catch (err: any) {
      error.value = err.message || '获取账户详情失败'
      console.error('Failed to get account:', err)
      throw err
    } finally {
      loading.value = false
    }
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
    accountSummary,
    
    // 操作
    loadAccounts,
    getAccountById,
    loadTransactions,
    deposit,
    withdraw,
    transfer,
    updateAccountSettings,
    clearError,
    reset
  }
})