/**
 * 策略状态管理
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { StrategyApi } from '@/api/strategy'
import type {
  Strategy,
  StrategyListItem,
  StrategyCreateRequest,
  StrategyUpdateRequest,
  StrategySearchParams,
  StrategyVersion,
  StrategyStats,
  StrategyExecutionRequest,
  StrategyStatus
} from '@/types/strategy'

export const useStrategyStore = defineStore('strategy', () => {
  // 状态
  const strategies = ref<StrategyListItem[]>([])
  const currentStrategy = ref<Strategy | null>(null)
  const strategyVersions = ref<StrategyVersion[]>([])
  const strategyStats = ref<StrategyStats | null>(null)
  const loading = ref(false)
  const searchParams = ref<StrategySearchParams>({
    page: 1,
    page_size: 20,
    sort_by: 'updated_at',
    sort_order: 'desc'
  })
  const total = ref(0)

  // 计算属性
  const hasStrategies = computed(() => strategies.value.length > 0)
  const totalPages = computed(() => Math.ceil(total.value / (searchParams.value.page_size || 20)))
  const runningStrategies = computed(() => strategies.value.filter((s) => s.is_running))
  const activeStrategies = computed(() => strategies.value.filter((s) => s.status === 'active'))
  const draftStrategies = computed(() => strategies.value.filter((s) => s.status === 'draft'))

  // 操作方法
  const fetchStrategies = async (params?: StrategySearchParams) => {
    try {
      loading.value = true

      if (params) {
        searchParams.value = { ...searchParams.value, ...params }
      }

      const response = await StrategyApi.getStrategies(searchParams.value)

      if (response.success) {
        strategies.value = response.data.items
        total.value = response.data.total
      } else {
        ElMessage.error(response.message || '获取策略列表失败')
      }
    } catch (error) {
      console.error('获取策略列表失败:', error)
      ElMessage.error('获取策略列表失败')
    } finally {
      loading.value = false
    }
  }

  const fetchMyStrategies = async (status?: StrategyStatus) => {
    try {
      loading.value = true
      const response = await StrategyApi.getMyStrategies(status)

      if (response.success) {
        strategies.value = response.data
      } else {
        ElMessage.error(response.message || '获取我的策略失败')
      }
    } catch (error) {
      console.error('获取我的策略失败:', error)
      ElMessage.error('获取我的策略失败')
    } finally {
      loading.value = false
    }
  }

  const fetchStrategyStats = async () => {
    try {
      const response = await StrategyApi.getStrategyStats()

      if (response.success) {
        strategyStats.value = response.data
      } else {
        ElMessage.error(response.message || '获取策略统计失败')
      }
    } catch (error) {
      console.error('获取策略统计失败:', error)
      ElMessage.error('获取策略统计失败')
    }
  }

  const fetchStrategy = async (id: number) => {
    try {
      loading.value = true
      const response = await StrategyApi.getStrategy(id)

      if (response.success) {
        currentStrategy.value = response.data
        return response.data
      } else {
        ElMessage.error(response.message || '获取策略详情失败')
        return null
      }
    } catch (error) {
      console.error('获取策略详情失败:', error)
      ElMessage.error('获取策略详情失败')
      return null
    } finally {
      loading.value = false
    }
  }

  const fetchStrategyByUuid = async (uuid: string) => {
    try {
      loading.value = true
      const response = await StrategyApi.getStrategyByUuid(uuid)

      if (response.success) {
        currentStrategy.value = response.data
        return response.data
      } else {
        ElMessage.error(response.message || '获取策略详情失败')
        return null
      }
    } catch (error) {
      console.error('获取策略详情失败:', error)
      ElMessage.error('获取策略详情失败')
      return null
    } finally {
      loading.value = false
    }
  }

  const createStrategy = async (data: StrategyCreateRequest) => {
    try {
      loading.value = true
      const response = await StrategyApi.createStrategy(data)

      if (response.success) {
        ElMessage.success('策略创建成功')
        // 刷新策略列表
        await fetchMyStrategies()
        return response.data
      } else {
        ElMessage.error(response.message || '创建策略失败')
        return null
      }
    } catch (error) {
      console.error('创建策略失败:', error)
      ElMessage.error('创建策略失败')
      return null
    } finally {
      loading.value = false
    }
  }

  const updateStrategy = async (id: number, data: StrategyUpdateRequest) => {
    try {
      loading.value = true
      const response = await StrategyApi.updateStrategy(id, data)

      if (response.success) {
        ElMessage.success('策略更新成功')

        // 更新当前策略
        if (currentStrategy.value && currentStrategy.value.id === id) {
          currentStrategy.value = response.data
        }

        // 更新策略列表中的项
        const index = strategies.value.findIndex((s) => s.id === id)
        if (index !== -1) {
          strategies.value[index] = { ...strategies.value[index], ...response.data }
        }

        return response.data
      } else {
        ElMessage.error(response.message || '更新策略失败')
        return null
      }
    } catch (error) {
      console.error('更新策略失败:', error)
      ElMessage.error('更新策略失败')
      return null
    } finally {
      loading.value = false
    }
  }

  const deleteStrategy = async (id: number) => {
    try {
      loading.value = true
      const response = await StrategyApi.deleteStrategy(id)

      if (response.success) {
        ElMessage.success('策略删除成功')

        // 从列表中移除
        strategies.value = strategies.value.filter((s) => s.id !== id)

        // 如果删除的是当前策略，清空当前策略
        if (currentStrategy.value && currentStrategy.value.id === id) {
          currentStrategy.value = null
        }

        return true
      } else {
        ElMessage.error(response.message || '删除策略失败')
        return false
      }
    } catch (error) {
      console.error('删除策略失败:', error)
      ElMessage.error('删除策略失败')
      return false
    } finally {
      loading.value = false
    }
  }

  const copyStrategy = async (id: number, newName?: string) => {
    try {
      loading.value = true
      const response = await StrategyApi.copyStrategy(id, newName)

      if (response.success) {
        ElMessage.success('策略复制成功')
        // 刷新策略列表
        await fetchMyStrategies()
        return response.data
      } else {
        ElMessage.error(response.message || '复制策略失败')
        return null
      }
    } catch (error) {
      console.error('复制策略失败:', error)
      ElMessage.error('复制策略失败')
      return null
    } finally {
      loading.value = false
    }
  }

  const executeStrategy = async (id: number, request: StrategyExecutionRequest) => {
    try {
      loading.value = true
      const response = await StrategyApi.executeStrategy(id, request)

      if (response.success) {
        const actionText =
          {
            start: '启动',
            stop: '停止',
            pause: '暂停',
            resume: '恢复'
          }[request.action] || request.action

        ElMessage.success(`策略${actionText}成功`)

        // 更新策略状态
        if (currentStrategy.value && currentStrategy.value.id === id) {
          currentStrategy.value.is_running =
            request.action === 'start' || request.action === 'resume'
        }

        const index = strategies.value.findIndex((s) => s.id === id)
        if (index !== -1) {
          strategies.value[index].is_running =
            request.action === 'start' || request.action === 'resume'
        }

        return response.data
      } else {
        ElMessage.error(response.message || '策略操作失败')
        return null
      }
    } catch (error) {
      console.error('策略操作失败:', error)
      ElMessage.error('策略操作失败')
      return null
    } finally {
      loading.value = false
    }
  }

  const fetchStrategyVersions = async (id: number) => {
    try {
      const response = await StrategyApi.getStrategyVersions(id)

      if (response.success) {
        strategyVersions.value = response.data
        return response.data
      } else {
        ElMessage.error(response.message || '获取策略版本失败')
        return []
      }
    } catch (error) {
      console.error('获取策略版本失败:', error)
      ElMessage.error('获取策略版本失败')
      return []
    }
  }

  const restoreStrategyVersion = async (strategyId: number, versionId: number) => {
    try {
      loading.value = true
      const response = await StrategyApi.restoreStrategyVersion(strategyId, versionId)

      if (response.success) {
        ElMessage.success('版本恢复成功')

        // 更新当前策略
        if (currentStrategy.value && currentStrategy.value.id === strategyId) {
          currentStrategy.value = response.data
        }

        // 刷新版本列表
        await fetchStrategyVersions(strategyId)

        return response.data
      } else {
        ElMessage.error(response.message || '版本恢复失败')
        return null
      }
    } catch (error) {
      console.error('版本恢复失败:', error)
      ElMessage.error('版本恢复失败')
      return null
    } finally {
      loading.value = false
    }
  }

  const searchStrategies = async (keyword: string) => {
    await fetchStrategies({ ...searchParams.value, keyword, page: 1 })
  }

  const filterStrategies = async (filters: Partial<StrategySearchParams>) => {
    await fetchStrategies({ ...searchParams.value, ...filters, page: 1 })
  }

  const changePage = async (page: number) => {
    await fetchStrategies({ ...searchParams.value, page })
  }

  const changePageSize = async (pageSize: number) => {
    await fetchStrategies({ ...searchParams.value, page_size: pageSize, page: 1 })
  }

  const sortStrategies = async (sortBy: string, sortOrder: 'asc' | 'desc') => {
    await fetchStrategies({
      ...searchParams.value,
      sort_by: sortBy,
      sort_order: sortOrder,
      page: 1
    })
  }

  const clearCurrentStrategy = () => {
    currentStrategy.value = null
  }

  const clearStrategies = () => {
    strategies.value = []
    total.value = 0
  }

  const reset = () => {
    strategies.value = []
    currentStrategy.value = null
    strategyVersions.value = []
    strategyStats.value = null
    loading.value = false
    searchParams.value = {
      page: 1,
      page_size: 20,
      sort_by: 'updated_at',
      sort_order: 'desc'
    }
    total.value = 0
  }

  // 别名方法（为了兼容性）
  const loadStrategies = fetchStrategies

  return {
    // 状态
    strategies,
    currentStrategy,
    strategyVersions,
    strategyStats,
    loading,
    searchParams,
    total,

    // 计算属性
    hasStrategies,
    totalPages,
    runningStrategies,
    activeStrategies,
    draftStrategies,

    // 方法
    fetchStrategies,
    fetchMyStrategies,
    fetchStrategyStats,
    fetchStrategy,
    fetchStrategyByUuid,
    createStrategy,
    updateStrategy,
    deleteStrategy,
    copyStrategy,
    executeStrategy,
    fetchStrategyVersions,
    restoreStrategyVersion,
    searchStrategies,
    filterStrategies,
    changePage,
    changePageSize,
    sortStrategies,
    clearCurrentStrategy,
    clearStrategies,
    reset,

    // 别名方法
    loadStrategies
  }
})
