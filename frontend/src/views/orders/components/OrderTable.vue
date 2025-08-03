<template>
  <div class="order-table">
    <el-table
      :data="orders"
      :loading="loading"
      @selection-change="handleSelectionChange"
      stripe
      style="width: 100%"
    >
      <!-- 选择列 -->
      <el-table-column type="selection" width="55" />

      <!-- 标的 -->
      <el-table-column prop="symbol" label="标的" width="100" fixed="left">
        <template #default="{ row }">
          <div class="symbol-cell">
            <span class="symbol-text">{{ row.symbol }}</span>
          </div>
        </template>
      </el-table-column>

      <!-- 方向 -->
      <el-table-column prop="side" label="方向" width="80">
        <template #default="{ row }">
          <el-tag
            :type="row.side === 'buy' ? 'success' : 'danger'"
            size="small"
          >
            {{ row.side === 'buy' ? '买入' : '卖出' }}
          </el-tag>
        </template>
      </el-table-column>

      <!-- 类型 -->
      <el-table-column prop="order_type" label="类型" width="100">
        <template #default="{ row }">
          <span>{{ getOrderTypeLabel(row.order_type) }}</span>
        </template>
      </el-table-column>

      <!-- 状态 -->
      <el-table-column prop="status" label="状态" width="120">
        <template #default="{ row }">
          <div class="status-cell">
            <el-tag
              :type="getStatusTagType(row.status)"
              size="small"
            >
              {{ getStatusLabel(row.status) }}
            </el-tag>
            <div 
              v-if="isOrderRecentlyUpdated(row.id)"
              class="update-indicator"
              title="最近更新"
            >
              <el-icon class="pulse-icon"><Clock /></el-icon>
            </div>
          </div>
        </template>
      </el-table-column>

      <!-- 数量 -->
      <el-table-column prop="quantity" label="数量" width="120" align="right">
        <template #default="{ row }">
          <div class="quantity-cell">
            <div>{{ formatNumber(row.quantity) }}</div>
            <div class="filled-info" v-if="row.filled_quantity > 0">
              已成交: {{ formatNumber(row.filled_quantity) }}
            </div>
          </div>
        </template>
      </el-table-column>

      <!-- 价格 -->
      <el-table-column prop="price" label="价格" width="120" align="right">
        <template #default="{ row }">
          <div v-if="row.price">
            <div>{{ formatPrice(row.price) }}</div>
            <div class="avg-price" v-if="row.avg_fill_price">
              均价: {{ formatPrice(row.avg_fill_price) }}
            </div>
          </div>
          <span v-else class="market-order">市价</span>
        </template>
      </el-table-column>

      <!-- 成交比例 -->
      <el-table-column label="成交比例" width="120">
        <template #default="{ row }">
          <div class="fill-ratio-cell">
            <el-progress
              :percentage="row.fill_ratio * 100"
              :stroke-width="6"
              :show-text="false"
              :color="getProgressColor(row.fill_ratio)"
            />
            <span class="ratio-text">{{ (row.fill_ratio * 100).toFixed(1) }}%</span>
          </div>
        </template>
      </el-table-column>

      <!-- 优先级 -->
      <el-table-column prop="priority" label="优先级" width="80">
        <template #default="{ row }">
          <el-tag
            :type="getPriorityTagType(row.priority)"
            size="small"
          >
            {{ getPriorityLabel(row.priority) }}
          </el-tag>
        </template>
      </el-table-column>

      <!-- 策略 -->
      <el-table-column prop="strategy_id" label="策略" width="120">
        <template #default="{ row }">
          <span v-if="row.strategy_id">策略 #{{ row.strategy_id }}</span>
          <span v-else class="manual-order">手动</span>
        </template>
      </el-table-column>

      <!-- 标签 -->
      <el-table-column prop="tags" label="标签" width="150">
        <template #default="{ row }">
          <div class="tags-cell">
            <el-tag
              v-for="tag in row.tags.slice(0, 2)"
              :key="tag"
              size="small"
              class="tag-item"
            >
              {{ tag }}
            </el-tag>
            <el-tooltip
              v-if="row.tags.length > 2"
              :content="row.tags.slice(2).join(', ')"
              placement="top"
            >
              <el-tag size="small" class="more-tags">
                +{{ row.tags.length - 2 }}
              </el-tag>
            </el-tooltip>
          </div>
        </template>
      </el-table-column>

      <!-- 创建时间 -->
      <el-table-column prop="created_at" label="创建时间" width="160">
        <template #default="{ row }">
          {{ formatDateTime(row.created_at) }}
        </template>
      </el-table-column>

      <!-- 操作 -->
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <div class="action-buttons">
            <el-button
              type="text"
              size="small"
              @click="$emit('view-order', row)"
            >
              详情
            </el-button>
            
            <el-button
              type="text"
              size="small"
              @click="$emit('edit-order', row)"
              :disabled="!row.is_active"
            >
              编辑
            </el-button>
            
            <el-button
              type="text"
              size="small"
              @click="$emit('cancel-order', row)"
              :disabled="!row.is_active"
              class="cancel-btn"
            >
              取消
            </el-button>
            
            <el-button
              type="text"
              size="small"
              @click="$emit('view-fills', row)"
              :disabled="row.filled_quantity === 0"
            >
              成交
            </el-button>
          </div>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Order } from '@/api/order'
import { formatNumber, formatPrice, formatDateTime } from '@/utils/format'
import { useOrderStore } from '@/stores/order'
import { Clock } from '@element-plus/icons-vue'

// Props
const props = defineProps<{
  orders: Order[]
  loading: boolean
}>()

// Emits
const emit = defineEmits<{
  'selection-change': [orders: Order[]]
  'view-order': [order: Order]
  'edit-order': [order: Order]
  'cancel-order': [order: Order]
  'view-fills': [order: Order]
}>()

// 状态管理
const orderStore = useOrderStore()

// 选择变化处理
const handleSelectionChange = (selection: Order[]) => {
  emit('selection-change', selection)
}

// 获取订单类型标签
const getOrderTypeLabel = (type: string) => {
  const typeMap: Record<string, string> = {
    market: '市价',
    limit: '限价',
    stop: '止损',
    stop_limit: '止损限价',
    trailing_stop: '跟踪止损',
    iceberg: '冰山',
    twap: 'TWAP',
    vwap: 'VWAP'
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

// 获取进度条颜色
const getProgressColor = (ratio: number) => {
  if (ratio === 0) return '#e4e7ed'
  if (ratio < 0.5) return '#f56c6c'
  if (ratio < 1) return '#e6a23c'
  return '#67c23a'
}

// 检查订单是否最近更新
const isOrderRecentlyUpdated = (orderId: number) => {
  return orderStore.isOrderRecentlyUpdated(orderId, 2) // 2分钟内
}
</script>

<style scoped>
.order-table {
  width: 100%;
}

.symbol-cell {
  font-weight: 600;
}

.quantity-cell {
  text-align: right;
}

.filled-info {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 2px;
}

.avg-price {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 2px;
}

.market-order {
  color: var(--el-text-color-secondary);
  font-style: italic;
}

.fill-ratio-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.ratio-text {
  font-size: 12px;
  color: var(--el-text-color-regular);
}

.manual-order {
  color: var(--el-text-color-secondary);
  font-style: italic;
}

.tags-cell {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.tag-item {
  margin: 0;
}

.more-tags {
  background-color: var(--el-color-info-light-8);
  border-color: var(--el-color-info-light-6);
  color: var(--el-color-info);
}

.action-buttons {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.cancel-btn {
  color: var(--el-color-danger);
}

.cancel-btn:hover {
  color: var(--el-color-danger-light-3);
}

.status-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.update-indicator {
  display: flex;
  align-items: center;
}

.pulse-icon {
  color: var(--el-color-primary);
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.5;
    transform: scale(1.1);
  }
  100% {
    opacity: 1;
    transform: scale(1);
  }
}

:deep(.el-table__row) {
  cursor: pointer;
}

:deep(.el-table__row:hover) {
  background-color: var(--el-table-row-hover-bg-color);
}

:deep(.el-progress-bar__outer) {
  background-color: var(--el-border-color-lighter);
}
</style>