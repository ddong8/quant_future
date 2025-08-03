/**
 * 持仓状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { positionApi, type Position, type PortfolioMetrics, type PositionStatistics } from '@/api/position'
import { ElMessage } from 'element-plus'

export const usePositionStore = defineStore('position', () => {
  // 状态
  const positions = ref<Position[]>([])
  const currentPosition = ref<Position | null>(null)
  const portfolioMetrics = ref<PortfolioMetrics | null>(null)
  const statistics = ref<PositionStatistics | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // 筛选条件
  const filter = ref({
    status: undefined as 'OPEN' | 'CLOSED' | 'SUSPENDED' | undefined,
    symbol: '',
    position_type: undefined as 'LONG' | 'SHORT' | undefined,
    strategy_id: undefined as number | undefined,
    backtest_id: undefined as number | undefined
  })

  // 分页信息
  const pagination = ref({
    page: 1,
    size: 20,
    total: 0,
    has_next: false
  })

  // 计算属性
  const openPositions = computed(() => 
    positions.value.filter(p => p.status === 'OPEN')
  )

  const closedPositions = computed(() => 
    positions.value.filter(p => p.status === 'CLOSED')
  )

  const longPositions = computed(() => 
    positions.value.filter(p => p.position_type === 'LONG')
  )

  const shortPositions = computed(() => 
    positions.value.filter(p => p.position_type === 'SHORT')
  )

  const profitPositions = computed(() => 
    positions.value.filter(p => p.total_pnl > 0)
  )

  const lossPositions = computed(() => 
    positions.value.filter(p => p.total_pnl < 0)
  )

  const totalMarketValue = computed(() => 
    positions.value.reduce((sum, p) => sum + (p.market_value || 0), 0)
  )

  const totalPnL = computed(() => 
    positions.value.reduce((sum, p) => sum + p.total_pnl, 0)
  )

  const totalRealizedPnL = computed(() => 
    positions.value.reduce((sum, p) => sum + p.realized_pnl, 0)
  )

  const totalUnrealizedPnL = computed(() => 
    positions.value.reduce((sum, p) => sum + p.unrealized_pnl, 0)
  )

  // 操作方法
  const fetchPositions = async (params?: any) => {
    try {
      loading.value = true
      error.value = null

      const response = await positionApi.getPositions({
        ...filter.value,
        page: pagination.value.page,
        size: pagination.value.size,
        ...params
      })

      if (response.success) {
        positions.value = response.data.items
        pagination.value = {
          page: response.data.page,
          size: response.data.size,
          total: response.data.total,
          has_next: response.data.has_next
        }
      } else {
        throw new Error(response.message)
      }
    } catch (err: any) {
      error.value = err.message || '获取持仓列表失败'
      ElMessage.error(error.value)
    } finally {
      loading.value = false
    }
  }

  const fetchPosition = async (id: number) => {
    try {
      loading.value = true
      error.value = null

      const response = await positionApi.getPosition(id)
      if (response.success) {
        currentPosition.value = response.data
        
        // 更新列表中的对应项
        const index = positions.value.findIndex(p => p.id === id)
        if (index !== -1) {
          positions.value[index] = response.data
        }
      } else {
        throw new Error(response.message)
      }
    } catch (err: any) {
      error.value = err.message || '获取持仓详情失败'
      ElMessage.error(error.value)
    } finally {
      loading.value = false
    }
  }

  const updatePosition = async (id: number, data: any) => {
    try {
      loading.value = true
      error.value = null

      const response = await positionApi.updatePosition(id, data)
      if (response.success) {
        // 更新当前持仓
        if (currentPosition.value?.id === id) {
          currentPosition.value = response.data
        }
        
        // 更新列表中的对应项
        const index = positions.value.findIndex(p => p.id === id)
        if (index !== -1) {
          positions.value[index] = response.data
        }

        ElMessage.success('持仓更新成功')
        return response.data
      } else {
        throw new Error(response.message)
      }
    } catch (err: any) {
      error.value = err.message || '更新持仓失败'
      ElMessage.error(error.value)
      throw err
    } finally {
      loading.value = false
    }
  }

  const setStopLoss = async (id: number, stopPrice: number, orderId?: number) => {
    try {
      loading.value = true
      error.value = null

      const response = await positionApi.setStopLoss(id, {
        stop_price: stopPrice,
        order_id: orderId
      })

      if (response.success) {
        // 更新持仓数据
        if (currentPosition.value?.id === id) {
          currentPosition.value = response.data
        }
        
        const index = positions.value.findIndex(p => p.id === id)
        if (index !== -1) {
          positions.value[index] = response.data
        }

        ElMessage.success('止损设置成功')
        return response.data
      } else {
        throw new Error(response.message)
      }
    } catch (err: any) {
      error.value = err.message || '设置止损失败'
      ElMessage.error(error.value)
      throw err
    } finally {
      loading.value = false
    }
  }

  const setTakeProfit = async (id: number, profitPrice: number, orderId?: number) => {
    try {
      loading.value = true
      error.value = null

      const response = await positionApi.setTakeProfit(id, {
        profit_price: profitPrice,
        order_id: orderId
      })

      if (response.success) {
        // 更新持仓数据
        if (currentPosition.value?.id === id) {
          currentPosition.value = response.data
        }
        
        const index = positions.value.findIndex(p => p.id === id)
        if (index !== -1) {
          positions.value[index] = response.data
        }

        ElMessage.success('止盈设置成功')
        return response.data
      } else {
        throw new Error(response.message)
      }
    } catch (err: any) {
      error.value = err.message || '设置止盈失败'
      ElMessage.error(error.value)
      throw err
    } finally {
      loading.value = false
    }
  }

  const closePosition = async (id: number, closePrice: number, reason?: string) => {
    try {
      loading.value = true
      error.value = null

      const response = await positionApi.closePosition(id, {
        close_price: closePrice,
        reason
      })

      if (response.success) {
        // 更新持仓数据
        if (currentPosition.value?.id === id) {
          currentPosition.value = response.data
        }
        
        const index = positions.value.findIndex(p => p.id === id)
        if (index !== -1) {
          positions.value[index] = response.data
        }

        ElMessage.success('平仓成功')
        return response.data
      } else {
        throw new Error(response.message)
      }
    } catch (err: any) {
      error.value = err.message || '平仓失败'
      ElMessage.error(error.value)
      throw err
    } finally {
      loading.value = false
    }
  }

  const fetchPortfolioSummary = async () => {
    try {
      const response = await positionApi.getPortfolioSummary()
      if (response.success) {
        portfolioMetrics.value = response.data
      } else {
        throw new Error(response.message)
      }
    } catch (err: any) {
      error.value = err.message || '获取投资组合摘要失败'
      ElMessage.error(error.value)
    }
  }

  const fetchStatistics = async () => {
    try {
      const response = await positionApi.getPositionStatistics()
      if (response.success) {
        statistics.value = response.data
      } else {
        throw new Error(response.message)
      }
    } catch (err: any) {
      error.value = err.message || '获取持仓统计失败'
      ElMessage.error(error.value)
    }
  }

  const checkStopTriggers = async () => {
    try {
      const response = await positionApi.checkStopTriggers()
      if (response.success) {
        const triggers = response.data
        if (triggers.length > 0) {
          ElMessage.warning(`发现 ${triggers.length} 个止损止盈触发条件`)
        }
        return triggers
      } else {
        throw new Error(response.message)
      }
    } catch (err: any) {
      error.value = err.message || '检查止损止盈触发失败'
      ElMessage.error(error.value)
      return []
    }
  }

  const exportPositions = async (params?: any) => {
    try {
      loading.value = true
      const response = await positionApi.exportCSV(params)
      
      if (response.success) {
        // 创建下载链接
        const blob = new Blob([response.data.csv_content], { type: 'text/csv;charset=utf-8;' })
        const link = document.createElement('a')
        const url = URL.createObjectURL(blob)
        link.setAttribute('href', url)
        link.setAttribute('download', response.data.filename)
        link.style.visibility = 'hidden'
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        
        ElMessage.success(`成功导出 ${response.data.record_count} 条持仓记录`)
      } else {
        throw new Error(response.message)
      }
    } catch (err: any) {
      error.value = err.message || '导出持仓数据失败'
      ElMessage.error(error.value)
    } finally {
      loading.value = false
    }
  }

  // 筛选方法
  const setFilter = (newFilter: Partial<typeof filter.value>) => {
    filter.value = { ...filter.value, ...newFilter }
    pagination.value.page = 1 // 重置页码
  }

  const clearFilter = () => {
    filter.value = {
      status: undefined,
      symbol: '',
      position_type: undefined,
      strategy_id: undefined,
      backtest_id: undefined
    }
    pagination.value.page = 1
  }

  // 分页方法
  const setPage = (page: number) => {
    pagination.value.page = page
  }

  const setPageSize = (size: number) => {
    pagination.value.size = size
    pagination.value.page = 1
  }

  // 重置状态
  const reset = () => {
    positions.value = []
    currentPosition.value = null
    portfolioMetrics.value = null
    statistics.value = null
    loading.value = false
    error.value = null
    clearFilter()
    pagination.value = {
      page: 1,
      size: 20,
      total: 0,
      has_next: false
    }
  }

  return {
    // 状态
    positions,
    currentPosition,
    portfolioMetrics,
    statistics,
    loading,
    error,
    filter,
    pagination,

    // 计算属性
    openPositions,
    closedPositions,
    longPositions,
    shortPositions,
    profitPositions,
    lossPositions,
    totalMarketValue,
    totalPnL,
    totalRealizedPnL,
    totalUnrealizedPnL,

    // 方法
    fetchPositions,
    fetchPosition,
    updatePosition,
    setStopLoss,
    setTakeProfit,
    closePosition,
    fetchPortfolioSummary,
    fetchStatistics,
    checkStopTriggers,
    exportPositions,
    setFilter,
    clearFilter,
    setPage,
    setPageSize,
    reset
  }
})