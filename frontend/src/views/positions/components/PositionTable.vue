<template>
  <div class="position-table">
    <el-table
      :data="positions"
      :loading="loading"
      stripe
      @row-click="handleRowClick"
      class="positions-table"
    >
      <!-- 标的 -->
      <el-table-column prop="symbol" label="标的" width="100" fixed="left">
        <template #default="{ row }">
          <div class="symbol-cell">
            <span class="symbol-text">{{ row.symbol }}</span>
            <el-tag 
              :type="row.position_type === 'LONG' ? 'success' : 'warning'"
              size="small"
            >
              {{ row.position_type === 'LONG' ? '多' : '空' }}
            </el-tag>
          </div>
        </template>
      </el-table-column>

      <!-- 状态 -->
      <el-table-column prop="status" label="状态" width="80">
        <template #default="{ row }">
          <el-tag 
            :type="getStatusType(row.status)"
            size="small"
          >
            {{ getStatusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>

      <!-- 持仓数量 -->
      <el-table-column prop="quantity" label="持仓数量" width="120" align="right">
        <template #default="{ row }">
          <div class="quantity-cell">
            <div class="quantity-total">{{ formatNumber(row.quantity) }}</div>
            <div class="quantity-detail">
              可用: {{ formatNumber(row.available_quantity) }}
              <span v-if="row.frozen_quantity > 0" class="frozen">
                | 冻结: {{ formatNumber(row.frozen_quantity) }}
              </span>
            </div>
          </div>
        </template>
      </el-table-column>

      <!-- 成本价 -->
      <el-table-column prop="average_cost" label="成本价" width="100" align="right">
        <template #default="{ row }">
          {{ formatCurrency(row.average_cost) }}
        </template>
      </el-table-column>

      <!-- 现价 -->
      <el-table-column prop="current_price" label="现价" width="100" align="right">
        <template #default="{ row }">
          <span v-if="row.current_price">
            {{ formatCurrency(row.current_price) }}
          </span>
          <span v-else class="text-muted">--</span>
        </template>
      </el-table-column>

      <!-- 市值 -->
      <el-table-column prop="market_value" label="市值" width="120" align="right">
        <template #default="{ row }">
          <span v-if="row.market_value">
            {{ formatCurrency(row.market_value) }}
          </span>
          <span v-else class="text-muted">--</span>
        </template>
      </el-table-column>

      <!-- 盈亏 -->
      <el-table-column label="盈亏" width="140" align="right">
        <template #default="{ row }">
          <div class="pnl-cell">
            <div class="pnl-total" :class="getPnLClass(row.total_pnl)">
              {{ formatCurrency(row.total_pnl) }}
            </div>
            <div class="pnl-detail">
              已实现: <span :class="getPnLClass(row.realized_pnl)">{{ formatCurrency(row.realized_pnl) }}</span>
            </div>
          </div>
        </template>
      </el-table-column>

      <!-- 收益率 -->
      <el-table-column prop="return_rate" label="收益率" width="100" align="right">
        <template #default="{ row }">
          <span :class="getPnLClass(row.total_pnl)">
            {{ formatPercent(row.return_rate) }}
          </span>
        </template>
      </el-table-column>

      <!-- 止损止盈 -->
      <el-table-column label="止损/止盈" width="120" align="center">
        <template #default="{ row }">
          <div class="stop-cell">
            <div v-if="row.stop_loss_price" class="stop-loss">
              止损: {{ formatCurrency(row.stop_loss_price) }}
            </div>
            <div v-if="row.take_profit_price" class="take-profit">
              止盈: {{ formatCurrency(row.take_profit_price) }}
            </div>
            <div v-if="!row.stop_loss_price && !row.take_profit_price" class="text-muted">
              未设置
            </div>
          </div>
        </template>
      </el-table-column>

      <!-- 开仓时间 -->
      <el-table-column prop="opened_at" label="开仓时间" width="120">
        <template #default="{ row }">
          <span v-if="row.opened_at">
            {{ formatDateTime(row.opened_at) }}
          </span>
          <span v-else class="text-muted">--</span>
        </template>
      </el-table-column>

      <!-- 操作 -->
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <div class="action-buttons">
            <el-button
              v-if="row.is_open"
              type="primary"
              size="small"
              @click.stop="handleSetStopLoss(row)"
            >
              止损
            </el-button>
            <el-button
              v-if="row.is_open"
              type="success"
              size="small"
              @click.stop="handleSetTakeProfit(row)"
            >
              止盈
            </el-button>
            <el-button
              v-if="row.is_open"
              type="danger"
              size="small"
              @click.stop="handleClosePosition(row)"
            >
              平仓
            </el-button>
            <el-button
              type="info"
              size="small"
              @click.stop="handleViewDetail(row)"
            >
              详情
            </el-button>
          </div>
        </template>
      </el-table-column>
    </el-table>

    <!-- 空状态 -->
    <div v-if="!loading && positions.length === 0" class="empty-state">
      <el-empty description="暂无持仓数据">
        <el-button type="primary">创建持仓</el-button>
      </el-empty>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Position } from '@/api/position'
import { formatCurrency, formatNumber, formatPercent, formatDateTime } from '@/utils/format'

// Props
interface Props {
  positions: Position[]
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

// 事件定义
const emit = defineEmits<{
  'position-click': [position: Position]
  'set-stop-loss': [position: Position]
  'set-take-profit': [position: Position]
  'close-position': [position: Position]
}>()

// 方法
const handleRowClick = (row: Position) => {
  emit('position-click', row)
}

const handleSetStopLoss = (position: Position) => {
  emit('set-stop-loss', position)
}

const handleSetTakeProfit = (position: Position) => {
  emit('set-take-profit', position)
}

const handleClosePosition = (position: Position) => {
  emit('close-position', position)
}

const handleViewDetail = (position: Position) => {
  emit('position-click', position)
}

const getStatusType = (status: string) => {
  switch (status) {
    case 'OPEN':
      return 'success'
    case 'CLOSED':
      return 'info'
    case 'SUSPENDED':
      return 'warning'
    default:
      return 'info'
  }
}

const getStatusText = (status: string) => {
  switch (status) {
    case 'OPEN':
      return '持仓中'
    case 'CLOSED':
      return '已平仓'
    case 'SUSPENDED':
      return '暂停'
    default:
      return status
  }
}

const getPnLClass = (value: number) => {
  if (value > 0) return 'profit'
  if (value < 0) return 'loss'
  return 'neutral'
}
</script>

<style scoped>
.position-table {
  background: var(--el-bg-color);
}

.positions-table {
  width: 100%;
}

.positions-table :deep(.el-table__row) {
  cursor: pointer;
}

.positions-table :deep(.el-table__row:hover) {
  background-color: var(--el-fill-color-light);
}

.symbol-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.symbol-text {
  font-weight: 600;
  color: #1f2937;
}

.quantity-cell {
  text-align: right;
}

.quantity-total {
  font-weight: 500;
  color: #1f2937;
}

.quantity-detail {
  font-size: 12px;
  color: #6b7280;
  margin-top: 2px;
}

.frozen {
  color: #f59e0b;
}

.pnl-cell {
  text-align: right;
}

.pnl-total {
  font-weight: 500;
}

.pnl-detail {
  font-size: 12px;
  color: #6b7280;
  margin-top: 2px;
}

.stop-cell {
  font-size: 12px;
}

.stop-loss {
  color: #ef4444;
  margin-bottom: 2px;
}

.take-profit {
  color: #10b981;
}

.action-buttons {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.action-buttons .el-button {
  padding: 4px 8px;
  font-size: 12px;
}

.profit {
  color: #10b981;
}

.loss {
  color: #ef4444;
}

.neutral {
  color: #6b7280;
}

.text-muted {
  color: #9ca3af;
}

.empty-state {
  padding: 40px;
  text-align: center;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .positions-table :deep(.el-table__fixed-right) {
    display: none;
  }
  
  .action-buttons {
    justify-content: center;
  }
}

@media (max-width: 768px) {
  .positions-table :deep(.el-table__fixed) {
    display: none;
  }
  
  .positions-table :deep(.el-table__body-wrapper) {
    overflow-x: auto;
  }
  
  .action-buttons .el-button {
    padding: 2px 6px;
    font-size: 11px;
  }
}
</style>