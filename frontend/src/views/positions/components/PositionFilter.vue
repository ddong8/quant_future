<template>
  <div class="position-filter">
    <div class="filter-form">
      <el-form :model="filterForm" inline>
        <!-- 持仓状态 -->
        <el-form-item label="状态">
          <el-select 
            v-model="filterForm.status" 
            placeholder="全部状态"
            clearable
            style="width: 120px"
          >
            <el-option label="持仓中" value="OPEN" />
            <el-option label="已平仓" value="CLOSED" />
            <el-option label="暂停" value="SUSPENDED" />
          </el-select>
        </el-form-item>

        <!-- 持仓类型 -->
        <el-form-item label="类型">
          <el-select 
            v-model="filterForm.position_type" 
            placeholder="全部类型"
            clearable
            style="width: 120px"
          >
            <el-option label="多头" value="LONG" />
            <el-option label="空头" value="SHORT" />
          </el-select>
        </el-form-item>

        <!-- 交易标的 -->
        <el-form-item label="标的">
          <el-input
            v-model="filterForm.symbol"
            placeholder="输入标的代码"
            clearable
            style="width: 150px"
          />
        </el-form-item>

        <!-- 策略 -->
        <el-form-item label="策略">
          <el-select 
            v-model="filterForm.strategy_id" 
            placeholder="选择策略"
            clearable
            filterable
            style="width: 180px"
          >
            <el-option
              v-for="strategy in strategies"
              :key="strategy.id"
              :label="strategy.name"
              :value="strategy.id"
            />
          </el-select>
        </el-form-item>

        <!-- 回测 -->
        <el-form-item label="回测">
          <el-select 
            v-model="filterForm.backtest_id" 
            placeholder="选择回测"
            clearable
            filterable
            style="width: 180px"
          >
            <el-option
              v-for="backtest in backtests"
              :key="backtest.id"
              :label="backtest.name"
              :value="backtest.id"
            />
          </el-select>
        </el-form-item>

        <!-- 操作按钮 -->
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 快速筛选标签 -->
    <div class="quick-filters">
      <div class="filter-tags">
        <el-tag
          :type="activeQuickFilter === 'all' ? 'primary' : 'info'"
          :effect="activeQuickFilter === 'all' ? 'dark' : 'plain'"
          @click="handleQuickFilter('all')"
          class="filter-tag"
        >
          全部 ({{ totalCount }})
        </el-tag>
        <el-tag
          :type="activeQuickFilter === 'open' ? 'success' : 'info'"
          :effect="activeQuickFilter === 'open' ? 'dark' : 'plain'"
          @click="handleQuickFilter('open')"
          class="filter-tag"
        >
          持仓中 ({{ openCount }})
        </el-tag>
        <el-tag
          :type="activeQuickFilter === 'profit' ? 'success' : 'info'"
          :effect="activeQuickFilter === 'profit' ? 'dark' : 'plain'"
          @click="handleQuickFilter('profit')"
          class="filter-tag"
        >
          盈利 ({{ profitCount }})
        </el-tag>
        <el-tag
          :type="activeQuickFilter === 'loss' ? 'danger' : 'info'"
          :effect="activeQuickFilter === 'loss' ? 'dark' : 'plain'"
          @click="handleQuickFilter('loss')"
          class="filter-tag"
        >
          亏损 ({{ lossCount }})
        </el-tag>
        <el-tag
          :type="activeQuickFilter === 'long' ? 'warning' : 'info'"
          :effect="activeQuickFilter === 'long' ? 'dark' : 'plain'"
          @click="handleQuickFilter('long')"
          class="filter-tag"
        >
          多头 ({{ longCount }})
        </el-tag>
        <el-tag
          :type="activeQuickFilter === 'short' ? 'warning' : 'info'"
          :effect="activeQuickFilter === 'short' ? 'dark' : 'plain'"
          @click="handleQuickFilter('short')"
          class="filter-tag"
        >
          空头 ({{ shortCount }})
        </el-tag>
      </div>

      <!-- 排序选项 -->
      <div class="sort-options">
        <el-select 
          v-model="sortBy" 
          placeholder="排序方式"
          style="width: 150px"
          @change="handleSortChange"
        >
          <el-option label="更新时间" value="updated_at" />
          <el-option label="开仓时间" value="opened_at" />
          <el-option label="市值" value="market_value" />
          <el-option label="盈亏" value="total_pnl" />
          <el-option label="收益率" value="return_rate" />
        </el-select>
        <el-button-group>
          <el-button
            :type="sortOrder === 'desc' ? 'primary' : 'default'"
            size="small"
            @click="setSortOrder('desc')"
          >
            <el-icon><ArrowDown /></el-icon>
          </el-button>
          <el-button
            :type="sortOrder === 'asc' ? 'primary' : 'default'"
            size="small"
            @click="setSortOrder('asc')"
          >
            <el-icon><ArrowUp /></el-icon>
          </el-button>
        </el-button-group>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { Search, Refresh, ArrowUp, ArrowDown } from '@element-plus/icons-vue'
import { usePositionStore } from '@/stores/position'
import { strategyApi } from '@/api/strategy'
import { backtestApi } from '@/api/backtest'

// 事件定义
const emit = defineEmits<{
  'filter-change': [filter: any]
}>()

// 状态管理
const positionStore = usePositionStore()

// 响应式数据
const filterForm = reactive({
  status: undefined as 'OPEN' | 'CLOSED' | 'SUSPENDED' | undefined,
  position_type: undefined as 'LONG' | 'SHORT' | undefined,
  symbol: '',
  strategy_id: undefined as number | undefined,
  backtest_id: undefined as number | undefined
})

const activeQuickFilter = ref<string>('all')
const sortBy = ref<string>('updated_at')
const sortOrder = ref<'asc' | 'desc'>('desc')

const strategies = ref<Array<{ id: number; name: string }>>([])
const backtests = ref<Array<{ id: number; name: string }>>([])

// 计算属性
const totalCount = computed(() => positionStore.positions.length)
const openCount = computed(() => positionStore.openPositions.length)
const profitCount = computed(() => positionStore.profitPositions.length)
const lossCount = computed(() => positionStore.lossPositions.length)
const longCount = computed(() => positionStore.longPositions.length)
const shortCount = computed(() => positionStore.shortPositions.length)

// 生命周期
onMounted(() => {
  loadStrategies()
  loadBacktests()
})

// 方法
const loadStrategies = async () => {
  try {
    const response = await strategyApi.getStrategies({ size: 1000 })
    if (response.success) {
      strategies.value = response.data.items.map(item => ({
        id: item.id,
        name: item.name
      }))
    }
  } catch (error) {
    console.error('加载策略列表失败:', error)
  }
}

const loadBacktests = async () => {
  try {
    const response = await backtestApi.getBacktests({ size: 1000 })
    if (response.success) {
      backtests.value = response.data.items.map(item => ({
        id: item.id,
        name: item.name
      }))
    }
  } catch (error) {
    console.error('加载回测列表失败:', error)
  }
}

const handleSearch = () => {
  const filter = {
    ...filterForm,
    symbol: filterForm.symbol || undefined
  }
  
  // 清除空值
  Object.keys(filter).forEach(key => {
    if (filter[key] === '' || filter[key] === undefined) {
      delete filter[key]
    }
  })

  activeQuickFilter.value = 'all'
  emit('filter-change', filter)
}

const handleReset = () => {
  filterForm.status = undefined
  filterForm.position_type = undefined
  filterForm.symbol = ''
  filterForm.strategy_id = undefined
  filterForm.backtest_id = undefined
  
  activeQuickFilter.value = 'all'
  sortBy.value = 'updated_at'
  sortOrder.value = 'desc'
  
  emit('filter-change', {})
}

const handleQuickFilter = (type: string) => {
  activeQuickFilter.value = type
  
  // 重置表单
  filterForm.status = undefined
  filterForm.position_type = undefined
  filterForm.symbol = ''
  filterForm.strategy_id = undefined
  filterForm.backtest_id = undefined
  
  let filter = {}
  
  switch (type) {
    case 'open':
      filter = { status: 'OPEN' }
      filterForm.status = 'OPEN'
      break
    case 'profit':
      // 这里需要后端支持按盈亏筛选
      filter = { min_pnl: 0.01 }
      break
    case 'loss':
      filter = { max_pnl: -0.01 }
      break
    case 'long':
      filter = { position_type: 'LONG' }
      filterForm.position_type = 'LONG'
      break
    case 'short':
      filter = { position_type: 'SHORT' }
      filterForm.position_type = 'SHORT'
      break
    default:
      filter = {}
  }
  
  emit('filter-change', filter)
}

const handleSortChange = () => {
  // 这里可以添加排序逻辑
  // 目前前端排序，后续可以改为后端排序
  const filter = {
    sort_by: sortBy.value,
    sort_order: sortOrder.value
  }
  emit('filter-change', filter)
}

const setSortOrder = (order: 'asc' | 'desc') => {
  sortOrder.value = order
  handleSortChange()
}
</script>

<style scoped>
.position-filter {
  background: var(--el-bg-color);
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.filter-form {
  margin-bottom: 16px;
}

.filter-form :deep(.el-form-item) {
  margin-bottom: 12px;
  margin-right: 16px;
}

.filter-form :deep(.el-form-item__label) {
  font-weight: 500;
  color: #374151;
}

.quick-filters {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 16px;
  border-top: 1px solid #e5e7eb;
}

.filter-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.filter-tag {
  cursor: pointer;
  transition: all 0.2s;
}

.filter-tag:hover {
  transform: translateY(-1px);
}

.sort-options {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .filter-form :deep(.el-form) {
    display: flex;
    flex-direction: column;
  }
  
  .filter-form :deep(.el-form-item) {
    margin-right: 0;
    width: 100%;
  }
  
  .filter-form :deep(.el-select),
  .filter-form :deep(.el-input) {
    width: 100% !important;
  }
}

@media (max-width: 768px) {
  .position-filter {
    padding: 16px;
  }
  
  .quick-filters {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .filter-tags {
    justify-content: center;
  }
  
  .sort-options {
    justify-content: center;
  }
}
</style>