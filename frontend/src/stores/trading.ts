import { defineStore } from 'pinia'
import { ref, computed, readonly } from 'vue'
import type {
  Order,
  Position,
  TradingAccount,
  TradeHistory,
  RealTimePnL,
  MarketData,
  TradingStats,
  CreateOrderRequest,
  ModifyOrderRequest
} from '@/types/trading'
import { tradingApi } from '@/api/trading'
import { ElMessage } from 'element-plus'

// 错误消息处理函数
const getErrorMessage = (error: any): string => {
  if (error.code === 'ERR_NETWORK' || error.code === 'ECONNREFUSED') {
    return '网络连接失败，请检查网络连接'
  } else if (error.code === 'ECONNABORTED') {
    return '请求超时，请稍后重试'
  } else if (error.response?.status === 401) {
    return '登录已过期，请重新登录'
  } else if (error.response?.status === 403) {
    return '没有权限访问该资源'
  } else if (error.response?.status === 404) {
    return '请求的资源不存在'
  } else if (error.response?.status >= 500) {
    return '服务器暂时不可用，请稍后重试'
  } else {
    return error.message || '操作失败，请稍后重试'
  }
}

export const useTradingStore = defineStore('trading', () => {
  // 状态
  const orders = ref<Order[]>([])
  const positions = ref<Position[]>([])
  const accounts = ref<TradingAccount[]>([])
  const currentAccount = ref<TradingAccount | null>(null)
  const tradeHistory = ref<TradeHistory[]>([])
  const realTimePnL = ref<RealTimePnL | null>(null)
  const marketData = ref<Record<string, MarketData>>({})
  const tradingStats = ref<TradingStats | null>(null)
  const loading = ref(false)
  const ordersTotal = ref(0)
  const historyTotal = ref(0)

  // 计算属性
  const activeOrders = computed(() => 
    orders.value.filter(order => 
      ['pending', 'submitted', 'partially_filled'].includes(order.status)
    )
  )
  
  const filledOrders = computed(() => 
    orders.value.filter(order => order.status === 'filled')
  )
  
  const cancelledOrders = computed(() => 
    orders.value.filter(order => order.status === 'cancelled')
  )
  
  const totalPositionValue = computed(() => 
    positions.value.reduce((sum, pos) => sum + pos.market_value, 0)
  )
  
  const totalUnrealizedPnL = computed(() => 
    positions.value.reduce((sum, pos) => sum + pos.unrealized_pnl, 0)
  )
  
  const longPositions = computed(() => 
    positions.value.filter(pos => pos.side === 'long')
  )
  
  const shortPositions = computed(() => 
    positions.value.filter(pos => pos.side === 'short')
  )

  // 获取订单列表（改进版本，添加重试和默认值）
  const fetchOrders = async (params?: {
    account_id?: number
    symbol?: string
    status?: string
    side?: string
    start_date?: string
    end_date?: string
    page?: number
    page_size?: number
  }, retryCount = 0) => {
    try {
      loading.value = true
      const response = await tradingApi.getOrders(params)
      
      if (response?.success && response?.data) {
        orders.value = Array.isArray(response.data.orders) ? response.data.orders : []
        ordersTotal.value = Number(response.data.total) || 0
      } else {
        // 如果响应格式不正确，使用默认值
        orders.value = []
        ordersTotal.value = 0
        console.warn('订单数据格式不正确:', response)
      }
    } catch (error: any) {
      console.error('获取订单列表失败:', error)
      
      // 网络错误重试
      if (retryCount < 2 && (error.code === 'ERR_NETWORK' || error.code === 'ECONNREFUSED')) {
        console.log(`网络错误，${retryCount + 1}秒后重试...`)
        setTimeout(() => {
          fetchOrders(params, retryCount + 1)
        }, (retryCount + 1) * 1000)
        return
      }
      
      // 设置默认值
      orders.value = []
      ordersTotal.value = 0
      
      // 用户友好的错误提示
      const errorMessage = getErrorMessage(error)
      ElMessage.error(errorMessage)
    } finally {
      loading.value = false
    }
  }

  // 创建订单（改进版本，添加更好的错误处理）
  const createOrder = async (data: CreateOrderRequest) => {
    try {
      loading.value = true
      const response = await tradingApi.createOrder(data)
      
      if (response?.success && response?.data?.order) {
        orders.value.unshift(response.data.order)
        ElMessage.success('订单创建成功')
        return response.data.order
      } else {
        throw new Error('订单创建响应格式不正确')
      }
    } catch (error: any) {
      console.error('创建订单失败:', error)
      const errorMessage = getErrorMessage(error)
      ElMessage.error(errorMessage)
      throw error
    } finally {
      loading.value = false
    }
  }

  // 修改订单
  const modifyOrder = async (orderId: number, data: ModifyOrderRequest) => {
    try {
      const response = await tradingApi.modifyOrder(orderId, data)
      
      if (response.success) {
        const index = orders.value.findIndex(order => order.id === orderId)
        if (index !== -1) {
          orders.value[index] = response.data.order
        }
        ElMessage.success('订单修改成功')
        return response.data.order
      }
    } catch (error: any) {
      ElMessage.error(error.message || '修改订单失败')
      throw error
    }
  }

  // 取消订单
  const cancelOrder = async (orderId: number) => {
    try {
      const response = await tradingApi.cancelOrder(orderId)
      
      if (response.success) {
        const order = orders.value.find(o => o.id === orderId)
        if (order) {
          order.status = 'cancelled'
          order.cancelled_at = new Date().toISOString()
        }
        ElMessage.success('订单取消成功')
      }
    } catch (error: any) {
      ElMessage.error(error.message || '取消订单失败')
      throw error
    }
  }

  // 取消所有订单
  const cancelAllOrders = async (params?: {
    account_id?: number
    symbol?: string
  }) => {
    try {
      const response = await tradingApi.cancelAllOrders(params)
      
      if (response.success) {
        // 更新本地订单状态
        orders.value.forEach(order => {
          if (['pending', 'submitted', 'partially_filled'].includes(order.status)) {
            if (!params?.symbol || order.symbol === params.symbol) {
              if (!params?.account_id || order.user_id === params.account_id) {
                order.status = 'cancelled'
                order.cancelled_at = new Date().toISOString()
              }
            }
          }
        })
        ElMessage.success('所有订单已取消')
      }
    } catch (error: any) {
      ElMessage.error(error.message || '取消所有订单失败')
      throw error
    }
  }

  // 获取持仓列表（改进版本，添加重试和默认值）
  const fetchPositions = async (params?: {
    account_id?: number
    symbol?: string
  }, retryCount = 0) => {
    try {
      const response = await tradingApi.getPositions(params)
      
      if (response?.success && response?.data) {
        positions.value = Array.isArray(response.data.positions) ? response.data.positions : []
      } else {
        positions.value = []
        console.warn('持仓数据格式不正确:', response)
      }
    } catch (error: any) {
      console.error('获取持仓列表失败:', error)
      
      // 网络错误重试
      if (retryCount < 2 && (error.code === 'ERR_NETWORK' || error.code === 'ECONNREFUSED')) {
        console.log(`网络错误，${retryCount + 1}秒后重试...`)
        setTimeout(() => {
          fetchPositions(params, retryCount + 1)
        }, (retryCount + 1) * 1000)
        return
      }
      
      // 设置默认值
      positions.value = []
      
      // 用户友好的错误提示
      const errorMessage = getErrorMessage(error)
      ElMessage.error(errorMessage)
    }
  }

  // 平仓
  const closePosition = async (positionId: number, quantity?: number) => {
    try {
      const response = await tradingApi.closePosition(positionId, quantity)
      
      if (response.success) {
        // 更新持仓列表
        await fetchPositions()
        ElMessage.success('平仓成功')
      }
    } catch (error: any) {
      ElMessage.error(error.message || '平仓失败')
      throw error
    }
  }

  // 获取账户列表（改进版本，添加重试和默认值）
  const fetchAccounts = async (retryCount = 0) => {
    try {
      const response = await tradingApi.getAccounts()
      
      if (response?.success && response?.data) {
        accounts.value = Array.isArray(response.data.accounts) ? response.data.accounts : []
        if (accounts.value.length > 0 && !currentAccount.value) {
          currentAccount.value = accounts.value[0]
        }
      } else {
        accounts.value = []
        console.warn('账户数据格式不正确:', response)
      }
    } catch (error: any) {
      console.error('获取账户列表失败:', error)
      
      // 网络错误重试
      if (retryCount < 2 && (error.code === 'ERR_NETWORK' || error.code === 'ECONNREFUSED')) {
        console.log(`网络错误，${retryCount + 1}秒后重试...`)
        setTimeout(() => {
          fetchAccounts(retryCount + 1)
        }, (retryCount + 1) * 1000)
        return
      }
      
      // 设置默认值
      accounts.value = []
      
      // 用户友好的错误提示
      const errorMessage = getErrorMessage(error)
      ElMessage.error(errorMessage)
    }
  }

  // 获取账户详情
  const fetchAccount = async (accountId: number) => {
    try {
      const response = await tradingApi.getAccount(accountId)
      
      if (response.success) {
        currentAccount.value = response.data.account
        
        // 更新账户列表中的对应项
        const index = accounts.value.findIndex(acc => acc.id === accountId)
        if (index !== -1) {
          accounts.value[index] = response.data.account
        }
        
        return response.data.account
      }
    } catch (error: any) {
      ElMessage.error(error.message || '获取账户详情失败')
      throw error
    }
  }

  // 获取交易历史
  const fetchTradeHistory = async (params?: {
    account_id?: number
    symbol?: string
    start_date?: string
    end_date?: string
    page?: number
    page_size?: number
  }) => {
    try {
      loading.value = true
      const response = await tradingApi.getTradeHistory(params)
      
      if (response.success) {
        tradeHistory.value = response.data.trades
        historyTotal.value = response.data.total
      }
    } catch (error: any) {
      ElMessage.error(error.message || '获取交易历史失败')
    } finally {
      loading.value = false
    }
  }

  // 获取实时盈亏
  const fetchRealTimePnL = async (accountId: number, symbol?: string) => {
    try {
      const response = await tradingApi.getRealTimePnL(accountId, symbol)
      
      if (response.success) {
        realTimePnL.value = response.data.pnl
        return response.data.pnl
      }
    } catch (error: any) {
      ElMessage.error(error.message || '获取实时盈亏失败')
      throw error
    }
  }

  // 获取市场数据
  const fetchMarketData = async (symbols: string[]) => {
    try {
      const response = await tradingApi.getMarketData(symbols)
      
      if (response.success) {
        response.data.data.forEach(data => {
          marketData.value[data.symbol] = data
        })
        return response.data.data
      }
    } catch (error: any) {
      ElMessage.error(error.message || '获取市场数据失败')
      throw error
    }
  }

  // 获取交易统计
  const fetchTradingStats = async (accountId: number, period: string) => {
    try {
      const response = await tradingApi.getTradingStats(accountId, period)
      
      if (response.success) {
        tradingStats.value = response.data.stats
        return response.data.stats
      }
    } catch (error: any) {
      ElMessage.error(error.message || '获取交易统计失败')
      throw error
    }
  }

  // 设置当前账户
  const setCurrentAccount = (account: TradingAccount) => {
    currentAccount.value = account
  }

  // 更新订单状态（WebSocket）
  const updateOrder = (updatedOrder: Order) => {
    const index = orders.value.findIndex(order => order.id === updatedOrder.id)
    if (index !== -1) {
      orders.value[index] = updatedOrder
    } else {
      orders.value.unshift(updatedOrder)
    }
  }

  // 更新持仓（WebSocket）
  const updatePosition = (updatedPosition: Position) => {
    const index = positions.value.findIndex(pos => pos.id === updatedPosition.id)
    if (index !== -1) {
      positions.value[index] = updatedPosition
    } else {
      positions.value.push(updatedPosition)
    }
  }

  // 更新市场数据（WebSocket）
  const updateMarketData = (data: MarketData) => {
    marketData.value[data.symbol] = data
  }

  // 更新实时盈亏（WebSocket）
  const updateRealTimePnL = (pnl: RealTimePnL) => {
    realTimePnL.value = pnl
  }

  // 清空状态
  const clearState = () => {
    orders.value = []
    positions.value = []
    tradeHistory.value = []
    realTimePnL.value = null
    marketData.value = {}
    tradingStats.value = null
    ordersTotal.value = 0
    historyTotal.value = 0
  }

  return {
    // 状态
    orders: readonly(orders),
    positions: readonly(positions),
    accounts: readonly(accounts),
    currentAccount: readonly(currentAccount),
    tradeHistory: readonly(tradeHistory),
    realTimePnL: readonly(realTimePnL),
    marketData: readonly(marketData),
    tradingStats: readonly(tradingStats),
    loading: readonly(loading),
    ordersTotal: readonly(ordersTotal),
    historyTotal: readonly(historyTotal),
    
    // 计算属性
    activeOrders,
    filledOrders,
    cancelledOrders,
    totalPositionValue,
    totalUnrealizedPnL,
    longPositions,
    shortPositions,
    
    // 方法
    fetchOrders,
    createOrder,
    modifyOrder,
    cancelOrder,
    cancelAllOrders,
    fetchPositions,
    closePosition,
    fetchAccounts,
    fetchAccount,
    fetchTradeHistory,
    fetchRealTimePnL,
    fetchMarketData,
    fetchTradingStats,
    setCurrentAccount,
    updateOrder,
    updatePosition,
    updateMarketData,
    updateRealTimePnL,
    clearState
  }
})