import { defineStore } from 'pinia'
import { ref, computed, readonly } from 'vue'
import type {
  Backtest,
  BacktestResult,
  BacktestProgress,
  BacktestTemplate,
  CreateBacktestRequest,
  UpdateBacktestRequest,
  HistoricalDataInfo
} from '@/types/backtest'
import { backtestApi } from '@/api/backtest'
import { ElMessage } from 'element-plus'

export const useBacktestStore = defineStore('backtest', () => {
  // 状态
  const backtests = ref<Backtest[]>([])
  const currentBacktest = ref<Backtest | null>(null)
  const currentResult = ref<BacktestResult | null>(null)
  const currentProgress = ref<BacktestProgress | null>(null)
  const templates = ref<BacktestTemplate[]>([])
  const historicalDataInfo = ref<HistoricalDataInfo[]>([])
  const loading = ref(false)
  const total = ref(0)
  const currentPage = ref(1)
  const pageSize = ref(20)

  // 计算属性
  const runningBacktests = computed(() => 
    backtests.value.filter(b => b.status === 'running')
  )
  
  const completedBacktests = computed(() => 
    backtests.value.filter(b => b.status === 'completed')
  )
  
  const failedBacktests = computed(() => 
    backtests.value.filter(b => b.status === 'failed')
  )

  // 获取回测列表
  const fetchBacktests = async (params?: {
    page?: number
    page_size?: number
    strategy_id?: number
    status?: string
    start_date?: string
    end_date?: string
    search?: string
  }) => {
    try {
      loading.value = true
      const response = await backtestApi.getBacktests(params)
      
      if (response.success) {
        backtests.value = response.data.backtests
        total.value = response.data.total
        currentPage.value = response.data.page
        pageSize.value = response.data.page_size
      }
    } catch (error: any) {
      ElMessage.error(error.message || '获取回测列表失败')
    } finally {
      loading.value = false
    }
  }

  // 获取单个回测
  const fetchBacktest = async (id: number) => {
    try {
      loading.value = true
      const response = await backtestApi.getBacktest(id)
      
      if (response.success) {
        currentBacktest.value = response.data.backtest
        return response.data.backtest
      }
    } catch (error: any) {
      ElMessage.error(error.message || '获取回测详情失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  // 创建回测
  const createBacktest = async (data: CreateBacktestRequest) => {
    try {
      loading.value = true
      const response = await backtestApi.createBacktest(data)
      
      if (response.success) {
        backtests.value.unshift(response.data.backtest)
        total.value += 1
        ElMessage.success('回测创建成功')
        return response.data.backtest
      }
    } catch (error: any) {
      ElMessage.error(error.message || '创建回测失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  // 更新回测
  const updateBacktest = async (id: number, data: UpdateBacktestRequest) => {
    try {
      loading.value = true
      const response = await backtestApi.updateBacktest(id, data)
      
      if (response.success) {
        const index = backtests.value.findIndex(b => b.id === id)
        if (index !== -1) {
          backtests.value[index] = response.data.backtest
        }
        
        if (currentBacktest.value?.id === id) {
          currentBacktest.value = response.data.backtest
        }
        
        ElMessage.success('回测更新成功')
        return response.data.backtest
      }
    } catch (error: any) {
      ElMessage.error(error.message || '更新回测失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  // 删除回测
  const deleteBacktest = async (id: number) => {
    try {
      loading.value = true
      const response = await backtestApi.deleteBacktest(id)
      
      if (response.success) {
        backtests.value = backtests.value.filter(b => b.id !== id)
        total.value -= 1
        
        if (currentBacktest.value?.id === id) {
          currentBacktest.value = null
          currentResult.value = null
          currentProgress.value = null
        }
        
        ElMessage.success('回测删除成功')
      }
    } catch (error: any) {
      ElMessage.error(error.message || '删除回测失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  // 克隆回测
  const cloneBacktest = async (id: number, name: string) => {
    try {
      loading.value = true
      const response = await backtestApi.cloneBacktest(id, name)
      
      if (response.success) {
        backtests.value.unshift(response.data.backtest)
        total.value += 1
        ElMessage.success('回测克隆成功')
        return response.data.backtest
      }
    } catch (error: any) {
      ElMessage.error(error.message || '克隆回测失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  // 启动回测
  const startBacktest = async (id: number) => {
    try {
      const response = await backtestApi.startBacktest(id)
      
      if (response.success) {
        // 更新回测状态
        const backtest = backtests.value.find(b => b.id === id)
        if (backtest) {
          backtest.status = 'running'
          backtest.started_at = new Date().toISOString()
        }
        
        if (currentBacktest.value?.id === id) {
          currentBacktest.value.status = 'running'
          currentBacktest.value.started_at = new Date().toISOString()
        }
        
        ElMessage.success('回测启动成功')
      }
    } catch (error: any) {
      ElMessage.error(error.message || '启动回测失败')
      throw error
    }
  }

  // 停止回测
  const stopBacktest = async (id: number) => {
    try {
      const response = await backtestApi.stopBacktest(id)
      
      if (response.success) {
        // 更新回测状态
        const backtest = backtests.value.find(b => b.id === id)
        if (backtest) {
          backtest.status = 'cancelled'
        }
        
        if (currentBacktest.value?.id === id) {
          currentBacktest.value.status = 'cancelled'
        }
        
        ElMessage.success('回测停止成功')
      }
    } catch (error: any) {
      ElMessage.error(error.message || '停止回测失败')
      throw error
    }
  }

  // 获取回测结果
  const fetchBacktestResult = async (id: number) => {
    try {
      const response = await backtestApi.getBacktestResult(id)
      
      if (response.success) {
        currentResult.value = response.data.result
        return response.data.result
      }
    } catch (error: any) {
      ElMessage.error(error.message || '获取回测结果失败')
      throw error
    }
  }

  // 获取回测进度
  const fetchBacktestProgress = async (id: number) => {
    try {
      const response = await backtestApi.getBacktestProgress(id)
      
      if (response.success) {
        currentProgress.value = response.data.progress
        return response.data.progress
      }
    } catch (error: any) {
      ElMessage.error(error.message || '获取回测进度失败')
      throw error
    }
  }

  // 获取回测模板
  const fetchTemplates = async (params?: {
    category?: string
    search?: string
  }) => {
    try {
      const response = await backtestApi.getBacktestTemplates(params)
      
      if (response.success) {
        templates.value = response.data.templates
        return response.data.templates
      }
    } catch (error: any) {
      ElMessage.error(error.message || '获取模板失败')
      throw error
    }
  }

  // 从模板创建回测
  const createFromTemplate = async (templateId: number, data: {
    name: string
    description?: string
    strategy_id: number
    config_overrides?: any
  }) => {
    try {
      loading.value = true
      const response = await backtestApi.createFromTemplate(templateId, data)
      
      if (response.success) {
        backtests.value.unshift(response.data.backtest)
        total.value += 1
        ElMessage.success('从模板创建回测成功')
        return response.data.backtest
      }
    } catch (error: any) {
      ElMessage.error(error.message || '从模板创建回测失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  // 获取历史数据信息
  const fetchHistoricalDataInfo = async (params: {
    symbols: string[]
    start_date: string
    end_date: string
    frequency: string
  }) => {
    try {
      const response = await backtestApi.getHistoricalDataInfo(params)
      
      if (response.success) {
        historicalDataInfo.value = response.data.data_info
        return response.data.data_info
      }
    } catch (error: any) {
      ElMessage.error(error.message || '获取历史数据信息失败')
      throw error
    }
  }

  // 验证历史数据
  const validateHistoricalData = async (params: {
    symbols: string[]
    start_date: string
    end_date: string
    frequency: string
  }) => {
    try {
      const response = await backtestApi.validateHistoricalData(params)
      
      if (response.success) {
        return response.data
      }
    } catch (error: any) {
      ElMessage.error(error.message || '验证历史数据失败')
      throw error
    }
  }

  // 验证回测配置
  const validateBacktestConfig = async (config: any) => {
    try {
      const response = await backtestApi.validateBacktestConfig(config)
      
      if (response.success) {
        return response.data
      }
    } catch (error: any) {
      ElMessage.error(error.message || '验证回测配置失败')
      throw error
    }
  }

  // 清空状态
  const clearState = () => {
    backtests.value = []
    currentBacktest.value = null
    currentResult.value = null
    currentProgress.value = null
    historicalDataInfo.value = []
    total.value = 0
    currentPage.value = 1
  }

  // 清空当前回测相关状态
  const clearCurrentBacktest = () => {
    currentBacktest.value = null
    currentResult.value = null
    currentProgress.value = null
  }

  return {
    // 状态
    backtests: readonly(backtests),
    currentBacktest: readonly(currentBacktest),
    currentResult: readonly(currentResult),
    currentProgress: readonly(currentProgress),
    templates: readonly(templates),
    historicalDataInfo: readonly(historicalDataInfo),
    loading: readonly(loading),
    total: readonly(total),
    currentPage: readonly(currentPage),
    pageSize: readonly(pageSize),
    
    // 计算属性
    runningBacktests,
    completedBacktests,
    failedBacktests,
    
    // 方法
    fetchBacktests,
    fetchBacktest,
    createBacktest,
    updateBacktest,
    deleteBacktest,
    cloneBacktest,
    startBacktest,
    stopBacktest,
    fetchBacktestResult,
    fetchBacktestProgress,
    fetchTemplates,
    createFromTemplate,
    fetchHistoricalDataInfo,
    validateHistoricalData,
    validateBacktestConfig,
    clearState,
    clearCurrentBacktest
  }
})