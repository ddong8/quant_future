<template>
  <div class="popular-quotes-panel">
    <!-- 行情表格 -->
    <el-table 
      :data="quotes"
      :loading="loading"
      stripe
      @sort-change="handleSortChange"
    >
      <!-- 标的信息 -->
      <el-table-column label="标的" min-width="150">
        <template #default="{ row }">
          <div class="symbol-info">
            <div class="symbol-code">{{ row.symbol?.symbol || '--' }}</div>
            <div class="symbol-name">{{ row.symbol?.name || '--' }}</div>
            <div class="symbol-exchange">{{ row.symbol?.exchange || '--' }}</div>
          </div>
        </template>
      </el-table-column>

      <!-- 当前价格 -->
      <el-table-column label="最新价" prop="price" sortable width="120" align="right">
        <template #default="{ row }">
          <span class="price">{{ formatPrice(row.price) }}</span>
        </template>
      </el-table-column>

      <!-- 涨跌额 -->
      <el-table-column label="涨跌额" prop="change" sortable width="100" align="right">
        <template #default="{ row }">
          <span v-if="row.change" :class="getChangeClass(row.change)">
            {{ formatChange(row.change) }}
          </span>
          <span v-else class="no-data">--</span>
        </template>
      </el-table-column>

      <!-- 涨跌幅 -->
      <el-table-column label="涨跌幅" prop="change_percent" sortable width="100" align="right">
        <template #default="{ row }">
          <span v-if="row.change_percent" :class="getChangeClass(row.change_percent)">
            {{ formatPercent(row.change_percent) }}
          </span>
          <span v-else class="no-data">--</span>
        </template>
      </el-table-column>

      <!-- 开盘价 -->
      <el-table-column label="开盘价" prop="open_price" width="100" align="right">
        <template #default="{ row }">
          <span v-if="row.open_price">{{ formatPrice(row.open_price) }}</span>
          <span v-else class="no-data">--</span>
        </template>
      </el-table-column>

      <!-- 最高价 -->
      <el-table-column label="最高价" prop="high_price" width="100" align="right">
        <template #default="{ row }">
          <span v-if="row.high_price" class="price-up">{{ formatPrice(row.high_price) }}</span>
          <span v-else class="no-data">--</span>
        </template>
      </el-table-column>

      <!-- 最低价 -->
      <el-table-column label="最低价" prop="low_price" width="100" align="right">
        <template #default="{ row }">
          <span v-if="row.low_price" class="price-down">{{ formatPrice(row.low_price) }}</span>
          <span v-else class="no-data">--</span>
        </template>
      </el-table-column>

      <!-- 成交量 -->
      <el-table-column label="成交量" prop="volume" sortable width="120" align="right">
        <template #default="{ row }">
          <span v-if="row.volume">{{ formatVolume(row.volume) }}</span>
          <span v-else class="no-data">--</span>
        </template>
      </el-table-column>

      <!-- 成交额 -->
      <el-table-column label="成交额" prop="turnover" sortable width="120" align="right">
        <template #default="{ row }">
          <span v-if="row.turnover">{{ formatAmount(row.turnover) }}</span>
          <span v-else class="no-data">--</span>
        </template>
      </el-table-column>

      <!-- 买卖盘 -->
      <el-table-column label="买/卖盘" width="120" align="center">
        <template #default="{ row }">
          <div v-if="row.bid_price && row.ask_price" class="bid-ask">
            <div class="bid">买: {{ formatPrice(row.bid_price) }}</div>
            <div class="ask">卖: {{ formatPrice(row.ask_price) }}</div>
          </div>
          <span v-else class="no-data">--</span>
        </template>
      </el-table-column>

      <!-- 数据状态 -->
      <el-table-column label="状态" width="80" align="center">
        <template #default="{ row }">
          <el-tag 
            :type="getStatusType(row.data_status)"
            size="small"
          >
            {{ getStatusText(row.data_status) }}
          </el-tag>
        </template>
      </el-table-column>

      <!-- 更新时间 -->
      <el-table-column label="更新时间" width="120">
        <template #default="{ row }">
          <span class="update-time">{{ formatTime(row.quote_time) }}</span>
        </template>
      </el-table-column>

      <!-- 操作 -->
      <el-table-column label="操作" width="100" align="center" fixed="right">
        <template #default="{ row }">
          <el-button 
            type="primary" 
            size="small" 
            text
            @click="handleAddToWatchlist(row)"
          >
            自选
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import type { Quote } from '@/api/marketQuotes'
import { formatPrice, formatChange, formatPercent, formatVolume, formatAmount, formatTime } from '@/utils/format'

interface Props {
  quotes: Quote[]
  loading: boolean
}

interface Emits {
  (e: 'refresh'): void
  (e: 'add-to-watchlist', symbolCode: string): void
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
  console.log('排序:', prop, order)
}

// 添加到自选股
const handleAddToWatchlist = (quote: Quote) => {
  if (quote.symbol?.symbol) {
    emit('add-to-watchlist', quote.symbol.symbol)
  }
}
</script>

<style scoped>
.popular-quotes-panel {
  min-height: 400px;
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

.symbol-exchange {
  font-size: 11px;
  color: #c0c4cc;
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

.bid-ask {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 12px;
}

.bid {
  color: #f56c6c;
}

.ask {
  color: #67c23a;
}

.no-data {
  color: #c0c4cc;
}

.update-time {
  font-size: 12px;
  color: #909399;
}

:deep(.el-table__row:hover) {
  background-color: var(--el-fill-color-light);
}
</style>