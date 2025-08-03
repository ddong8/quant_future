<template>
  <el-dialog
    v-model="visible"
    title="订单详情"
    width="900px"
    :close-on-click-modal="false"
  >
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="8" animated />
    </div>

    <div v-else-if="order" class="order-detail">
      <!-- 基本信息 -->
      <el-card class="detail-card">
        <template #header>
          <div class="card-header">
            <span>基本信息</span>
            <div class="header-actions">
              <el-tag
                :type="getStatusTagType(order.status)"
                size="large"
              >
                {{ getStatusLabel(order.status) }}
              </el-tag>
            </div>
          </div>
        </template>

        <el-row :gutter="20">
          <el-col :span="8">
            <div class="info-item">
              <label>订单ID:</label>
              <span>{{ order.id }}</span>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="info-item">
              <label>UUID:</label>
              <span class="uuid">{{ order.uuid }}</span>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="info-item">
              <label>外部订单ID:</label>
              <span>{{ order.order_id_external || '-' }}</span>
            </div>
          </el-col>

          <el-col :span="8">
            <div class="info-item">
              <label>交易标的:</label>
              <span class="symbol">{{ order.symbol }}</span>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="info-item">
              <label>订单方向:</label>
              <el-tag
                :type="order.side === 'buy' ? 'success' : 'danger'"
                size="small"
              >
                {{ order.side === 'buy' ? '买入' : '卖出' }}
              </el-tag>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="info-item">
              <label>订单类型:</label>
              <span>{{ getOrderTypeLabel(order.order_type) }}</span>
            </div>
          </el-col>

          <el-col :span="8">
            <div class="info-item">
              <label>订单数量:</label>
              <span class="quantity">{{ formatNumber(order.quantity) }}</span>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="info-item">
              <label>订单价格:</label>
              <span v-if="order.price" class="price">{{ formatPrice(order.price) }}</span>
              <span v-else class="market-price">市价</span>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="info-item">
              <label>止损价格:</label>
              <span v-if="order.stop_price" class="price">{{ formatPrice(order.stop_price) }}</span>
              <span v-else>-</span>
            </div>
          </el-col>

          <el-col :span="8">
            <div class="info-item">
              <label>已成交数量:</label>
              <span class="filled-quantity">{{ formatNumber(order.filled_quantity) }}</span>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="info-item">
              <label>剩余数量:</label>
              <span>{{ order.remaining_quantity ? formatNumber(order.remaining_quantity) : '-' }}</span>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="info-item">
              <label>平均成交价:</label>
              <span v-if="order.avg_fill_price" class="avg-price">{{ formatPrice(order.avg_fill_price) }}</span>
              <span v-else>-</span>
            </div>
          </el-col>

          <el-col :span="8">
            <div class="info-item">
              <label>成交比例:</label>
              <div class="fill-ratio">
                <el-progress
                  :percentage="order.fill_ratio * 100"
                  :stroke-width="8"
                  :show-text="false"
                  :color="getProgressColor(order.fill_ratio)"
                />
                <span class="ratio-text">{{ (order.fill_ratio * 100).toFixed(1) }}%</span>
              </div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="info-item">
              <label>有效期:</label>
              <span>{{ getTimeInForceLabel(order.time_in_force) }}</span>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="info-item">
              <label>优先级:</label>
              <el-tag
                :type="getPriorityTagType(order.priority)"
                size="small"
              >
                {{ getPriorityLabel(order.priority) }}
              </el-tag>
            </div>
          </el-col>
        </el-row>
      </el-card>

      <!-- 高级参数 -->
      <el-card class="detail-card" v-if="hasAdvancedParams">
        <template #header>
          <span>高级参数</span>
        </template>

        <el-row :gutter="20">
          <el-col :span="8" v-if="order.iceberg_quantity">
            <div class="info-item">
              <label>冰山单显示数量:</label>
              <span>{{ formatNumber(order.iceberg_quantity) }}</span>
            </div>
          </el-col>
          <el-col :span="8" v-if="order.trailing_amount">
            <div class="info-item">
              <label>跟踪止损金额:</label>
              <span>{{ formatPrice(order.trailing_amount) }}</span>
            </div>
          </el-col>
          <el-col :span="8" v-if="order.trailing_percent">
            <div class="info-item">
              <label>跟踪止损百分比:</label>
              <span>{{ order.trailing_percent }}%</span>
            </div>
          </el-col>
          <el-col :span="8" v-if="order.expire_time">
            <div class="info-item">
              <label>过期时间:</label>
              <span>{{ formatDateTime(order.expire_time) }}</span>
            </div>
          </el-col>
          <el-col :span="8" v-if="order.max_position_size">
            <div class="info-item">
              <label>最大持仓限制:</label>
              <span>{{ formatNumber(order.max_position_size) }}</span>
            </div>
          </el-col>
        </el-row>
      </el-card>

      <!-- 关联信息 -->
      <el-card class="detail-card">
        <template #header>
          <span>关联信息</span>
        </template>

        <el-row :gutter="20">
          <el-col :span="8">
            <div class="info-item">
              <label>关联策略:</label>
              <span v-if="order.strategy_id">策略 #{{ order.strategy_id }}</span>
              <span v-else class="manual-order">手动交易</span>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="info-item">
              <label>关联回测:</label>
              <span v-if="order.backtest_id">回测 #{{ order.backtest_id }}</span>
              <span v-else>-</span>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="info-item">
              <label>父订单:</label>
              <span v-if="order.parent_order_id">订单 #{{ order.parent_order_id }}</span>
              <span v-else>-</span>
            </div>
          </el-col>

          <el-col :span="8">
            <div class="info-item">
              <label>订单来源:</label>
              <span>{{ getSourceLabel(order.source) }}</span>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="info-item">
              <label>券商:</label>
              <span>{{ order.broker || '-' }}</span>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="info-item">
              <label>账户ID:</label>
              <span>{{ order.account_id || '-' }}</span>
            </div>
          </el-col>
        </el-row>
      </el-card>

      <!-- 成交信息 -->
      <el-card class="detail-card">
        <template #header>
          <span>成交信息</span>
        </template>

        <el-row :gutter="20">
          <el-col :span="8">
            <div class="info-item">
              <label>手续费:</label>
              <span>{{ formatPrice(order.commission) }}</span>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="info-item">
              <label>手续费资产:</label>
              <span>{{ order.commission_asset || '-' }}</span>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="info-item">
              <label>订单总价值:</label>
              <span v-if="order.total_value">{{ formatPrice(order.total_value) }}</span>
              <span v-else>-</span>
            </div>
          </el-col>
        </el-row>
      </el-card>

      <!-- 风险检查 -->
      <el-card class="detail-card">
        <template #header>
          <span>风险检查</span>
        </template>

        <el-row :gutter="20">
          <el-col :span="8">
            <div class="info-item">
              <label>风险检查:</label>
              <el-tag
                :type="order.risk_check_passed ? 'success' : 'danger'"
                size="small"
              >
                {{ order.risk_check_passed ? '通过' : '未通过' }}
              </el-tag>
            </div>
          </el-col>
          <el-col :span="16">
            <div class="info-item">
              <label>风险检查消息:</label>
              <span>{{ order.risk_check_message || '-' }}</span>
            </div>
          </el-col>
        </el-row>
      </el-card>

      <!-- 时间信息 -->
      <el-card class="detail-card">
        <template #header>
          <span>时间信息</span>
        </template>

        <el-row :gutter="20">
          <el-col :span="12">
            <div class="info-item">
              <label>创建时间:</label>
              <span>{{ formatDateTime(order.created_at) }}</span>
            </div>
          </el-col>
          <el-col :span="12">
            <div class="info-item">
              <label>更新时间:</label>
              <span>{{ formatDateTime(order.updated_at) }}</span>
            </div>
          </el-col>
          <el-col :span="12" v-if="order.submitted_at">
            <div class="info-item">
              <label>提交时间:</label>
              <span>{{ formatDateTime(order.submitted_at) }}</span>
            </div>
          </el-col>
          <el-col :span="12" v-if="order.accepted_at">
            <div class="info-item">
              <label>接受时间:</label>
              <span>{{ formatDateTime(order.accepted_at) }}</span>
            </div>
          </el-col>
          <el-col :span="12" v-if="order.filled_at">
            <div class="info-item">
              <label>完全成交时间:</label>
              <span>{{ formatDateTime(order.filled_at) }}</span>
            </div>
          </el-col>
          <el-col :span="12" v-if="order.cancelled_at">
            <div class="info-item">
              <label>取消时间:</label>
              <span>{{ formatDateTime(order.cancelled_at) }}</span>
            </div>
          </el-col>
        </el-row>
      </el-card>

      <!-- 标签和备注 -->
      <el-card class="detail-card">
        <template #header>
          <span>标签和备注</span>
        </template>

        <el-row :gutter="20">
          <el-col :span="24">
            <div class="info-item">
              <label>标签:</label>
              <div class="tags-container">
                <el-tag
                  v-for="tag in order.tags"
                  :key="tag"
                  size="small"
                  class="tag-item"
                >
                  {{ tag }}
                </el-tag>
                <span v-if="order.tags.length === 0" class="no-tags">无标签</span>
              </div>
            </div>
          </el-col>
          <el-col :span="24">
            <div class="info-item">
              <label>备注:</label>
              <div class="notes-container">
                <p v-if="order.notes">{{ order.notes }}</p>
                <span v-else class="no-notes">无备注</span>
              </div>
            </div>
          </el-col>
        </el-row>
      </el-card>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="visible = false">关闭</el-button>
        <el-button
          v-if="order && order.is_active"
          type="primary"
          @click="handleEdit"
        >
          编辑订单
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { orderApi, type Order } from '@/api/order'
import { formatNumber, formatPrice, formatDateTime } from '@/utils/format'

// Props
const props = defineProps<{
  modelValue: boolean
  orderId?: number
}>()

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  edit: [orderId: number]
}>()

// 响应式数据
const loading = ref(false)
const order = ref<Order | null>(null)

// 计算属性
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const hasAdvancedParams = computed(() => {
  if (!order.value) return false
  return !!(
    order.value.iceberg_quantity ||
    order.value.trailing_amount ||
    order.value.trailing_percent ||
    order.value.expire_time ||
    order.value.max_position_size
  )
})

// 加载订单详情
const loadOrderDetail = async () => {
  if (!props.orderId) return

  try {
    loading.value = true
    const response = await orderApi.getOrder(props.orderId)
    order.value = response.data
  } catch (error) {
    console.error('加载订单详情失败:', error)
    ElMessage.error('加载订单详情失败')
  } finally {
    loading.value = false
  }
}

// 获取订单类型标签
const getOrderTypeLabel = (type: string) => {
  const typeMap: Record<string, string> = {
    market: '市价单',
    limit: '限价单',
    stop: '止损单',
    stop_limit: '止损限价单',
    trailing_stop: '跟踪止损单',
    iceberg: '冰山单',
    twap: 'TWAP单',
    vwap: 'VWAP单'
  }
  return typeMap[type] || type
}

// 获取状态标签类型
const getStatusTagType = (status: string) => {
  const statusTypeMap: Record<string, string> = {
    pending: 'info',
    submitted: 'warning',
    accepted: 'primary',
    partially_filled: 'warning',
    filled: 'success',
    cancelled: 'info',
    rejected: 'danger',
    expired: 'info',
    suspended: 'warning'
  }
  return statusTypeMap[status] || 'info'
}

// 获取状态标签
const getStatusLabel = (status: string) => {
  const statusMap: Record<string, string> = {
    pending: '待提交',
    submitted: '已提交',
    accepted: '已接受',
    partially_filled: '部分成交',
    filled: '完全成交',
    cancelled: '已取消',
    rejected: '已拒绝',
    expired: '已过期',
    suspended: '已暂停'
  }
  return statusMap[status] || status
}

// 获取有效期标签
const getTimeInForceLabel = (timeInForce: string) => {
  const timeInForceMap: Record<string, string> = {
    day: '当日有效',
    gtc: '撤销前有效',
    ioc: '立即成交或取消',
    fok: '全部成交或取消',
    gtd: '指定日期前有效'
  }
  return timeInForceMap[timeInForce] || timeInForce
}

// 获取优先级标签类型
const getPriorityTagType = (priority: string) => {
  const priorityTypeMap: Record<string, string> = {
    low: 'info',
    normal: '',
    high: 'warning',
    urgent: 'danger'
  }
  return priorityTypeMap[priority] || ''
}

// 获取优先级标签
const getPriorityLabel = (priority: string) => {
  const priorityMap: Record<string, string> = {
    low: '低',
    normal: '普通',
    high: '高',
    urgent: '紧急'
  }
  return priorityMap[priority] || priority
}

// 获取来源标签
const getSourceLabel = (source: string) => {
  const sourceMap: Record<string, string> = {
    manual: '手动',
    strategy: '策略',
    algorithm: '算法'
  }
  return sourceMap[source] || source
}

// 获取进度条颜色
const getProgressColor = (ratio: number) => {
  if (ratio === 0) return '#e4e7ed'
  if (ratio < 0.5) return '#f56c6c'
  if (ratio < 1) return '#e6a23c'
  return '#67c23a'
}

// 编辑订单
const handleEdit = () => {
  if (order.value) {
    emit('edit', order.value.id)
    visible.value = false
  }
}

// 监听订单ID变化
watch(() => props.orderId, () => {
  if (props.orderId && visible.value) {
    loadOrderDetail()
  }
})

// 监听对话框显示状态
watch(visible, (newVisible) => {
  if (newVisible && props.orderId) {
    loadOrderDetail()
  }
})
</script>

<style scoped>
.loading-container {
  padding: 20px;
}

.order-detail {
  max-height: 70vh;
  overflow-y: auto;
}

.detail-card {
  margin-bottom: 16px;
}

.detail-card:last-child {
  margin-bottom: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-item {
  margin-bottom: 16px;
}

.info-item label {
  display: inline-block;
  width: 120px;
  font-weight: 500;
  color: var(--el-text-color-regular);
}

.symbol {
  font-weight: 600;
  font-size: 16px;
}

.quantity,
.price,
.filled-quantity,
.avg-price {
  font-weight: 500;
}

.market-price {
  color: var(--el-text-color-secondary);
  font-style: italic;
}

.uuid {
  font-family: monospace;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.manual-order {
  color: var(--el-text-color-secondary);
  font-style: italic;
}

.fill-ratio {
  display: flex;
  align-items: center;
  gap: 8px;
}

.ratio-text {
  font-size: 12px;
  color: var(--el-text-color-regular);
  min-width: 40px;
}

.tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.tag-item {
  margin: 0;
}

.no-tags,
.no-notes {
  color: var(--el-text-color-secondary);
  font-style: italic;
}

.notes-container p {
  margin: 0;
  line-height: 1.6;
  white-space: pre-wrap;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

:deep(.el-progress-bar__outer) {
  background-color: var(--el-border-color-lighter);
}
</style>