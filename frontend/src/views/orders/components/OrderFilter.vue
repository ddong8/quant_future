<template>
  <div class="order-filter">
    <el-form :model="filterForm" inline>
      <el-form-item label="交易标的">
        <el-input
          v-model="filterForm.symbol"
          placeholder="请输入标的代码"
          clearable
          style="width: 150px"
        />
      </el-form-item>

      <el-form-item label="订单类型">
        <el-select
          v-model="filterForm.order_type"
          placeholder="选择订单类型"
          clearable
          style="width: 120px"
        >
          <el-option
            v-for="type in orderTypes"
            :key="type.value"
            :label="type.label"
            :value="type.value"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="订单方向">
        <el-select
          v-model="filterForm.side"
          placeholder="选择方向"
          clearable
          style="width: 100px"
        >
          <el-option label="买入" value="buy" />
          <el-option label="卖出" value="sell" />
        </el-select>
      </el-form-item>

      <el-form-item label="订单状态">
        <el-select
          v-model="filterForm.status"
          placeholder="选择状态"
          clearable
          style="width: 120px"
        >
          <el-option
            v-for="status in orderStatuses"
            :key="status.value"
            :label="status.label"
            :value="status.value"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="策略">
        <el-select
          v-model="filterForm.strategy_id"
          placeholder="选择策略"
          clearable
          filterable
          style="width: 150px"
        >
          <el-option
            v-for="strategy in strategies"
            :key="strategy.id"
            :label="strategy.name"
            :value="strategy.id"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="创建时间">
        <el-date-picker
          v-model="dateRange"
          type="datetimerange"
          range-separator="至"
          start-placeholder="开始时间"
          end-placeholder="结束时间"
          format="YYYY-MM-DD HH:mm:ss"
          value-format="YYYY-MM-DDTHH:mm:ss"
          style="width: 350px"
          @change="handleDateRangeChange"
        />
      </el-form-item>

      <el-form-item label="标签">
        <el-select
          v-model="filterForm.tags"
          placeholder="选择标签"
          multiple
          clearable
          style="width: 150px"
        >
          <el-option
            v-for="tag in availableTags"
            :key="tag"
            :label="tag"
            :value="tag"
          />
        </el-select>
      </el-form-item>

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

    <!-- 高级筛选 -->
    <div class="advanced-filter" v-if="showAdvanced">
      <el-divider content-position="left">高级筛选</el-divider>
      <el-form :model="filterForm" inline>
        <el-form-item label="数量范围">
          <el-input-number
            v-model="filterForm.min_quantity"
            placeholder="最小数量"
            :min="0"
            :precision="2"
            style="width: 120px"
          />
          <span style="margin: 0 8px">-</span>
          <el-input-number
            v-model="filterForm.max_quantity"
            placeholder="最大数量"
            :min="0"
            :precision="2"
            style="width: 120px"
          />
        </el-form-item>

        <el-form-item label="价格范围">
          <el-input-number
            v-model="filterForm.min_price"
            placeholder="最小价格"
            :min="0"
            :precision="2"
            style="width: 120px"
          />
          <span style="margin: 0 8px">-</span>
          <el-input-number
            v-model="filterForm.max_price"
            placeholder="最大价格"
            :min="0"
            :precision="2"
            style="width: 120px"
          />
        </el-form-item>

        <el-form-item label="排序">
          <el-select
            v-model="filterForm.sort_by"
            style="width: 120px"
          >
            <el-option label="创建时间" value="created_at" />
            <el-option label="更新时间" value="updated_at" />
            <el-option label="标的" value="symbol" />
            <el-option label="数量" value="quantity" />
            <el-option label="价格" value="price" />
            <el-option label="状态" value="status" />
          </el-select>
          <el-select
            v-model="filterForm.sort_order"
            style="width: 80px; margin-left: 8px"
          >
            <el-option label="降序" value="desc" />
            <el-option label="升序" value="asc" />
          </el-select>
        </el-form-item>
      </el-form>
    </div>

    <div class="filter-actions">
      <el-button
        type="text"
        @click="showAdvanced = !showAdvanced"
      >
        {{ showAdvanced ? '收起' : '展开' }}高级筛选
        <el-icon>
          <ArrowDown v-if="!showAdvanced" />
          <ArrowUp v-else />
        </el-icon>
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch, onMounted } from 'vue'
import { Search, Refresh, ArrowDown, ArrowUp } from '@element-plus/icons-vue'
import { OrderType, OrderStatus, type OrderSearchParams } from '@/api/order'
import { strategyApi } from '@/api/strategy'

// Props
const props = defineProps<{
  modelValue: OrderSearchParams
}>()

// Emits
const emit = defineEmits<{
  search: []
  reset: []
}>()

// 响应式数据
const showAdvanced = ref(false)
const dateRange = ref<[string, string] | null>(null)
const strategies = ref<any[]>([])
const availableTags = ref<string[]>([])

// 表单数据
const filterForm = reactive<OrderSearchParams>({
  ...props.modelValue
})

// 订单类型选项
const orderTypes = [
  { label: '市价单', value: OrderType.MARKET },
  { label: '限价单', value: OrderType.LIMIT },
  { label: '止损单', value: OrderType.STOP },
  { label: '止损限价单', value: OrderType.STOP_LIMIT },
  { label: '跟踪止损单', value: OrderType.TRAILING_STOP },
  { label: '冰山单', value: OrderType.ICEBERG },
  { label: 'TWAP单', value: OrderType.TWAP },
  { label: 'VWAP单', value: OrderType.VWAP }
]

// 订单状态选项
const orderStatuses = [
  { label: '待提交', value: OrderStatus.PENDING },
  { label: '已提交', value: OrderStatus.SUBMITTED },
  { label: '已接受', value: OrderStatus.ACCEPTED },
  { label: '部分成交', value: OrderStatus.PARTIALLY_FILLED },
  { label: '完全成交', value: OrderStatus.FILLED },
  { label: '已取消', value: OrderStatus.CANCELLED },
  { label: '已拒绝', value: OrderStatus.REJECTED },
  { label: '已过期', value: OrderStatus.EXPIRED },
  { label: '已暂停', value: OrderStatus.SUSPENDED }
]

// 监听表单变化
watch(filterForm, (newValue) => {
  Object.assign(props.modelValue, newValue)
}, { deep: true })

// 处理日期范围变化
const handleDateRangeChange = (value: [string, string] | null) => {
  if (value) {
    filterForm.created_after = value[0]
    filterForm.created_before = value[1]
  } else {
    filterForm.created_after = undefined
    filterForm.created_before = undefined
  }
}

// 搜索处理
const handleSearch = () => {
  emit('search')
}

// 重置处理
const handleReset = () => {
  Object.assign(filterForm, {
    symbol: undefined,
    order_type: undefined,
    side: undefined,
    status: undefined,
    strategy_id: undefined,
    backtest_id: undefined,
    tags: undefined,
    created_after: undefined,
    created_before: undefined,
    min_quantity: undefined,
    max_quantity: undefined,
    min_price: undefined,
    max_price: undefined,
    sort_by: 'created_at',
    sort_order: 'desc'
  })
  dateRange.value = null
  emit('reset')
}

// 加载策略列表
const loadStrategies = async () => {
  try {
    const response = await strategyApi.getStrategies({ page_size: 100 })
    strategies.value = response.data.data || []
  } catch (error) {
    console.error('加载策略列表失败:', error)
  }
}

// 加载可用标签
const loadAvailableTags = () => {
  // 这里可以从API获取常用标签
  availableTags.value = [
    '手动交易',
    '策略交易',
    '回测',
    '测试',
    '紧急',
    '重要',
    '日内',
    '隔夜'
  ]
}

// 初始化
onMounted(() => {
  loadStrategies()
  loadAvailableTags()
  
  // 初始化日期范围
  if (filterForm.created_after && filterForm.created_before) {
    dateRange.value = [filterForm.created_after, filterForm.created_before]
  }
})
</script>

<style scoped>
.order-filter {
  padding: 16px;
}

.advanced-filter {
  margin-top: 16px;
}

.filter-actions {
  text-align: center;
  margin-top: 8px;
}

:deep(.el-form-item) {
  margin-bottom: 16px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
}
</style>