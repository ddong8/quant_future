import { defineStore } from 'pinia'
import { ref, computed, readonly } from 'vue'
import type {
  Strategy,
  StrategyFile,
  StrategyTemplate,
  StrategyCategory,
  CreateStrategyRequest,
  UpdateStrategyRequest
} from '@/types/strategy'
import { strategyApi } from '@/api/strategy'
import { ElMessage } from 'element-plus'

export const useStrategyStore = defineStore('strategy', () => {
  // 状态
  const strategies = ref<Strategy[]>([])
  const currentStrategy = ref<Strategy | null>(null)
  const strategyFiles = ref<StrategyFile[]>([])
  const templates = ref<StrategyTemplate[]>([])
  const categories = ref<StrategyCategory[]>([])
  const loading = ref(false)
  const total = ref(0)
  const currentPage = ref(1)
  const pageSize = ref(20)

  // 计算属性
  const activeStrategies = computed(() => 
    strategies.value.filter(s => s.status === 'active')
  )
  
  const draftStrategies = computed(() => 
    strategies.value.filter(s => s.status === 'draft')
  )
  
  const runningStrategies = computed(() => 
    strategies.value.filter(s => s.runtime?.is_running)
  )

  // 获取策略列表
  const fetchStrategies = async (params?: {
    page?: number
    page_size?: number
    category?: string
    status?: string
    search?: string
    user_id?: number
    is_public?: boolean
  }) => {
    try {
      loading.value = true
      const response = await strategyApi.getStrategies(params)
      
      if (response.success) {
        strategies.value = response.data.strategies
        total.value = response.data.total
        currentPage.value = response.data.page
        pageSize.value = response.data.page_size
      }
    } catch (error: any) {
      ElMessage.error(error.message || '获取策略列表失败')
    } finally {
      loading.value = false
    }
  }

  // 获取单个策略
  const fetchStrategy = async (id: number) => {
    try {
      loading.value = true
      const response = await strategyApi.getStrategy(id)
      
      if (response.success) {
        currentStrategy.value = response.data.strategy
        return response.data.strategy
      }
    } catch (error: any) {
      ElMessage.error(error.message || '获取策略详情失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  // 创建策略
  const createStrategy = async (data: CreateStrategyRequest) => {
    try {
      loading.value = true
      const response = await strategyApi.createStrategy(data)
      
      if (response.success) {
        strategies.value.unshift(response.data.strategy)
        total.value += 1
        ElMessage.success('策略创建成功')
        return response.data.strategy
      }
    } catch (error: any) {
      ElMessage.error(error.message || '创建策略失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  // 更新策略
  const updateStrategy = async (id: number, data: UpdateStrategyRequest) => {
    try {
      loading.value = true
      const response = await strategyApi.updateStrategy(id, data)
      
      if (response.success) {
        const index = strategies.value.findIndex(s => s.id === id)
        if (index !== -1) {
          strategies.value[index] = response.data.strategy
        }
        
        if (currentStrategy.value?.id === id) {
          currentStrategy.value = response.data.strategy
        }
        
        ElMessage.success('策略更新成功')
        return response.data.strategy
      }
    } catch (error: any) {
      ElMessage.error(error.message || '更新策略失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  // 删除策略
  const deleteStrategy = async (id: number) => {
    try {
      loading.value = true
      const response = await strategyApi.deleteStrategy(id)
      
      if (response.success) {
        strategies.value = strategies.value.filter(s => s.id !== id)
        total.value -= 1
        
        if (currentStrategy.value?.id === id) {
          currentStrategy.value = null
        }
        
        ElMessage.success('策略删除成功')
      }
    } catch (error: any) {
      ElMessage.error(error.message || '删除策略失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  // 克隆策略
  const cloneStrategy = async (id: number, name: string) => {
    try {
      loading.value = true
      const response = await strategyApi.cloneStrategy(id, name)
      
      if (response.success) {
        strategies.value.unshift(response.data.strategy)
        total.value += 1
        ElMessage.success('策略克隆成功')
        return response.data.strategy
      }
    } catch (error: any) {
      ElMessage.error(error.message || '克隆策略失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  // 启动策略
  const startStrategy = async (id: number, config?: any) => {
    try {
      const response = await strategyApi.startStrategy(id, config)
      
      if (response.success) {
        // 更新策略状态
        const strategy = strategies.value.find(s => s.id === id)
        if (strategy) {
          strategy.status = 'active'
          if (strategy.runtime) {
            strategy.runtime.is_running = true
            strategy.runtime.start_time = new Date().toISOString()
          }
        }
        
        ElMessage.success('策略启动成功')
      }
    } catch (error: any) {
      ElMessage.error(error.message || '启动策略失败')
      throw error
    }
  }

  // 停止策略
  const stopStrategy = async (id: number) => {
    try {
      const response = await strategyApi.stopStrategy(id)
      
      if (response.success) {
        // 更新策略状态
        const strategy = strategies.value.find(s => s.id === id)
        if (strategy) {
          strategy.status = 'stopped'
          if (strategy.runtime) {
            strategy.runtime.is_running = false
          }
        }
        
        ElMessage.success('策略停止成功')
      }
    } catch (error: any) {
      ElMessage.error(error.message || '停止策略失败')
      throw error
    }
  }

  // 获取策略文件
  const fetchStrategyFiles = async (strategyId: number) => {
    try {
      const response = await strategyApi.getStrategyFiles(strategyId)
      
      if (response.success) {
        strategyFiles.value = response.data.files
        return response.data.files
      }
    } catch (error: any) {
      ElMessage.error(error.message || '获取策略文件失败')
      throw error
    }
  }

  // 创建策略文件
  const createStrategyFile = async (strategyId: number, data: {
    filename: string
    content: string
    file_type: string
  }) => {
    try {
      const response = await strategyApi.createStrategyFile(strategyId, data)
      
      if (response.success) {
        strategyFiles.value.push(response.data.file)
        ElMessage.success('文件创建成功')
        return response.data.file
      }
    } catch (error: any) {
      ElMessage.error(error.message || '创建文件失败')
      throw error
    }
  }

  // 更新策略文件
  const updateStrategyFile = async (strategyId: number, fileId: number, data: {
    filename?: string
    content?: string
  }) => {
    try {
      const response = await strategyApi.updateStrategyFile(strategyId, fileId, data)
      
      if (response.success) {
        const index = strategyFiles.value.findIndex(f => f.id === fileId)
        if (index !== -1) {
          strategyFiles.value[index] = response.data.file
        }
        
        ElMessage.success('文件更新成功')
        return response.data.file
      }
    } catch (error: any) {
      ElMessage.error(error.message || '更新文件失败')
      throw error
    }
  }

  // 删除策略文件
  const deleteStrategyFile = async (strategyId: number, fileId: number) => {
    try {
      const response = await strategyApi.deleteStrategyFile(strategyId, fileId)
      
      if (response.success) {
        strategyFiles.value = strategyFiles.value.filter(f => f.id !== fileId)
        ElMessage.success('文件删除成功')
      }
    } catch (error: any) {
      ElMessage.error(error.message || '删除文件失败')
      throw error
    }
  }

  // 获取模板
  const fetchTemplates = async (params?: {
    category?: string
    difficulty?: string
    search?: string
  }) => {
    try {
      const response = await strategyApi.getTemplates(params)
      
      if (response.success) {
        templates.value = response.data.templates
        return response.data.templates
      }
    } catch (error: any) {
      ElMessage.error(error.message || '获取模板失败')
      throw error
    }
  }

  // 获取分类
  const fetchCategories = async () => {
    try {
      const response = await strategyApi.getCategories()
      
      if (response.success) {
        categories.value = response.data.categories
        return response.data.categories
      }
    } catch (error: any) {
      ElMessage.error(error.message || '获取分类失败')
      throw error
    }
  }

  // 从模板创建策略
  const createFromTemplate = async (templateId: number, data: {
    name: string
    description?: string
    config?: any
  }) => {
    try {
      loading.value = true
      const response = await strategyApi.createFromTemplate(templateId, data)
      
      if (response.success) {
        strategies.value.unshift(response.data.strategy)
        total.value += 1
        ElMessage.success('从模板创建策略成功')
        return response.data.strategy
      }
    } catch (error: any) {
      ElMessage.error(error.message || '从模板创建策略失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  // 清空状态
  const clearState = () => {
    strategies.value = []
    currentStrategy.value = null
    strategyFiles.value = []
    total.value = 0
    currentPage.value = 1
  }

  return {
    // 状态
    strategies: readonly(strategies),
    currentStrategy: readonly(currentStrategy),
    strategyFiles: readonly(strategyFiles),
    templates: readonly(templates),
    categories: readonly(categories),
    loading: readonly(loading),
    total: readonly(total),
    currentPage: readonly(currentPage),
    pageSize: readonly(pageSize),
    
    // 计算属性
    activeStrategies,
    draftStrategies,
    runningStrategies,
    
    // 方法
    fetchStrategies,
    fetchStrategy,
    createStrategy,
    updateStrategy,
    deleteStrategy,
    cloneStrategy,
    startStrategy,
    stopStrategy,
    fetchStrategyFiles,
    createStrategyFile,
    updateStrategyFile,
    deleteStrategyFile,
    fetchTemplates,
    fetchCategories,
    createFromTemplate,
    clearState
  }
})