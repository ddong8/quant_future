<template>
  <div class="watchlist-panel">
    <!-- 空状态 -->
    <div v-if="!loading && watchlist.length === 0" class="empty-state">
      <el-empty description="暂无自选股">
        <el-button type="primary" @click="$emit('refresh')">
          添加自选股
        </el-button>
      </el-empty>
    </div>

    <!-- 自选股表格 -->
    <el-table 
      v-else
      :data="watchlist"
      :loading="loading"
      stripe
      @sort-change="handleSortChange"
    >
      <!-- 排序拖拽列 -->
      <el-table-column width="50" align="center">
        <template #default>
          <el-icon class="drag-handle">
            <Rank />
          </el-icon>
        </template>
      </el-table-column>

      <!-- 标的信息 -->
      <el-table-column label="标的" min-width="150">
        <template #default="{ row }">
          <div class="symbol-info">
            <div class="symbol-code">{{ row.symbol.symbol }}</div>
            <div class="symbol-name">{{ row.symbol.name }}</div>
          </div>
        </template>
      </el-table-column>

      <!-- 当前价格 -->
      <el-table-column label="最新价" prop="quote.price" sortable width="120" align="right">
        <template #default="{ row }">
          <span v-if="row.quote" class="price">
            {{ formatPrice(row.quote.price) }}
          </span>
          <span v-else class="no-data">--</span>
        </template>
      </el-table-column>

      <!-- 涨跌额 -->
      <el-table-column label="涨跌额" width="100" align="right">
        <template #default="{ row }">
          <span v-if="row.quote?.change" :class="getChangeClass(row.quote.change)">
            {{ formatChange(row.quote.change) }}
          </span>
          <span v-else class="no-data">--</span>
        </template>
      </el-table-column>

      <!-- 涨跌幅 -->
      <el-table-column label="涨跌幅" width="100" align="right">
        <template #default="{ row }">
          <span v-if="row.quote?.change_percent" :class="getChangeClass(row.quote.change_percent)">
            {{ formatPercent(row.quote.change_percent) }}
          </span>
          <span v-else class="no-data">--</span>
        </template>
      </el-table-column>

      <!-- 成交量 -->
      <el-table-column label="成交量" width="120" align="right">
        <template #default="{ row }">
          <span v-if="row.quote?.volume">
            {{ formatVolume(row.quote.volume) }}
          </span>
          <span v-else class="no-data">--</span>
        </template>
      </el-table-column>

      <!-- 成交额 -->
      <el-table-column label="成交额" width="120" align="right">
        <template #default="{ row }">
          <span v-if="row.quote?.turnover">
            {{ formatAmount(row.quote.turnover) }}
          </span>
          <span v-else class="no-data">--</span>
        </template>
      </el-table-column>

      <!-- 数据状态 -->
      <el-table-column label="状态" width="80" align="center">
        <template #default="{ row }">
          <el-tag 
            v-if="row.quote"
            :type="getStatusType(row.quote.data_status)"
            size="small"
          >
            {{ getStatusText(row.quote.data_status) }}
          </el-tag>
          <span v-else class="no-data">--</span>
        </template>
      </el-table-column>

      <!-- 更新时间 -->
      <el-table-column label="更新时间" width="120">
        <template #default="{ row }">
          <span v-if="row.quote" class="update-time">
            {{ formatTime(row.quote.quote_time) }}
          </span>
          <span v-else class="no-data">--</span>
        </template>
      </el-table-column>

      <!-- 操作 -->
      <el-table-column label="操作" width="100" align="center" fixed="right">
        <template #default="{ row }">
          <el-button 
            type="danger" 
            size="small" 
            text
            @click="handleRemove(row)"
          >
            移除
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ElMessageBox } from 'element-plus'
import { Rank } from '@element-plus/icons-vue'
import type { WatchlistItem } from '@/api/marketQuotes'
import { formatPrice, formatChange, formatPercent, formatVolume, formatAmount, formatTime } from '@/utils/format'

interface Props {
  watchlist: WatchlistItem[]
  loading: boolean
}

interface Emits {
  (e: 'refresh'): void
  (e: 'remove', watchlistId: number): void
  (e: 'reorder', watchlistIds: number[]): void
}

defineProps<Props>()
const emit = defineEmits<Emits>()

// 获取涨跌颜色类名
const getChangeClass = (value: number) => {
  if (value > 0) return 'price-up'
  if (value < 0) return 'price-down'
  return 'price-neutral'
}

// 获取状态类型
const getStatusType = (status: string) => {
  switch (status) {
    case 'ACTIVE': return 'success'
    case 'DELAYED': return 'warning'
    case 'STALE': return 'info'
    case 'ERROR': return 'danger'
    default: return 'info'
  }
}

// 获取状态文本
const getStatusText = (status: string) => {
  switch (status) {
    case 'ACTIVE': return '实时'
    case 'DELAYED': return '延迟'
    case 'STALE': return '过期'
    case 'ERROR': return '错误'
    default: return '未知'
  }
}

// 处理排序
const handleSortChange = ({ prop, order }: any) => {
  // 这里可以实现排序逻辑
  console.log('排序:', prop, order)
}

// 处理移除
const handleRemove = async (item: WatchlistItem) => {
  try {
    await ElMessageBox.confirm(
      `确定要从自选股中移除 ${item.symbol.symbol} 吗？`,
      '确认移除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    emit('remove', item.id)
  } catch {
    // 用户取消
  }
}
</script>

<style scoped>
.watchlist-panel {
  min-height: 400px;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.drag-handle {
  cursor: move;
  color: #c0c4cc;
}

.drag-handle:hover {
  color: #409eff;
}

.symbol-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.symbol-code {
  font-weight: 600;
  color: #303133;
}

.symbol-name {
  font-size: 12px;
  color: #909399;
}

.price {
  font-weight: 600;
  font-family: 'Courier New', monospace;
}

.price-up {
  color: #f56c6c;
}

.price-down {
  color: #67c23a;
}

.price-neutral {
  color: #909399;
}

.no-data {
  color: #c0c4cc;
}

.update-time {
  font-size: 12px;
  color: #909399;
}

:deep(.el-table__row:hover) {
  background-color: #f5f7fa;
}
</style>