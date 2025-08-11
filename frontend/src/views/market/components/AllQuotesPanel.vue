<template>
  <div class="all-quotes-panel">
    <!-- 筛选器 -->
    <div class="filter-bar">
      <el-form :model="filters" inline>
        <el-form-item label="交易所">
          <el-select v-model="filters.exchange" placeholder="全部" clearable style="width: 120px">
            <el-option label="全部" value="" />
            <el-option label="NYSE" value="NYSE" />
            <el-option label="NASDAQ" value="NASDAQ" />
            <el-option label="SSE" value="SSE" />
            <el-option label="SZSE" value="SZSE" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="资产类型">
          <el-select v-model="filters.assetType" placeholder="全部" clearable style="width: 120px">
            <el-option label="全部" value="" />
            <el-option label="股票" value="stock" />
            <el-option label="ETF" value="etf" />
            <el-option label="加密货币" value="crypto" />
            <el-option label="外汇" value="forex" />
          </el-select>
        </el-form-item>

        <el-form-item label="涨跌幅">
          <el-select v-model="filters.changeRange" placeholder="全部" clearable style="width: 120px">
            <el-option label="全部" value="" />
            <el-option label="上涨" value="up" />
            <el-option label="下跌" value="down" />
            <el-option label=">5%" value="up5" />
            <el-option label="<-5%" value="down5" />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="applyFilters">筛选</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 行情表格 -->
    <el-table 
      :data="filteredQuotes"
      :loading="loading"
      stripe
      @sort-change="handleSortChange"
      max-height="600"
    >
      <!-- 标的信息 -->
      <el-table-column label="标的" min-width="150" fixed="left">
        <template #default="{ row }">
          <div class="symbol-info">
            <div class="symbol-code">{{ row.symbol?.symbol || '--' }}</div>
            <div class="symbol-name">{{ row.symbol?.name || '--' }}</div>
            <div class="symbol-meta">
              <span class="exchange">{{ row.symbol?.exchange }}</span>
              <span class="asset-type">{{ getAssetTypeText(row.symbol?.asset_type) }}</span>
            </div>
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

    <!-- 分页 -->
    <div class="pagination-wrapper">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[20, 50, 100, 200]"
        :total="totalCount"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Quote } from '@/api/marketQuotes'
import { formatPrice, formatChange, formatPercent, formatVolume, formatAmount } from '@/utils/format'

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

// 筛选条件
const filters = ref({
  exchange: '',
  assetType: '',
  changeRange: ''
})

// 分页
const currentPage = ref(1)
const pageSize = ref(50)
const totalCount = ref(0)

// 筛选后的数据
const filteredQuotes = computed(() => {
  let result = props.quotes

  // 交易所筛选
  if (filters.value.exchange) {
    result = result.filter(quote => quote.symbol?.exchange === filters.value.exchange)
  }

  // 资产类型筛选
  if (filters.value.assetType) {
    result = result.filter(quote => quote.symbol?.asset_type === filters.value.assetType)
  }

  // 涨跌幅筛选
  if (filters.value.changeRange) {
    switch (filters.value.changeRange) {
      case 'up':
        result = result.filter(quote => (quote.change_percent || 0) > 0)
        break
      case 'down':
        result = result.filter(quote => (quote.change_percent || 0) < 0)
        break
      case 'up5':
        result = result.filter(quote => (quote.change_percent || 0) > 5)
        break
      case 'down5':
        result = result.filter(quote => (quote.change_percent || 0) < -5)
        break
    }
  }

  totalCount.value = result.length

  // 分页
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return result.slice(start, end)
})

// 获取资产类型文本
const getAssetTypeText = (assetType?: string) => {
  switch (assetType) {
    case 'stock': return '股票'
    case 'etf': return 'ETF'
    case 'crypto': return '加密货币'
    case 'forex': return '外汇'
    case 'commodity': return '商品'
    default: return assetType || '--'
  }
}

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

// 应用筛选
const applyFilters = () => {
  currentPage.value = 1
}

// 重置筛选
const resetFilters = () => {
  filters.value = {
    exchange: '',
    assetType: '',
    changeRange: ''
  }
  currentPage.value = 1
}

// 处理排序
const handleSortChange = ({ prop, order }: any) => {
  console.log('排序:', prop, order)
}

// 分页大小改变
const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
}

// 当前页改变
const handleCurrentChange = (page: number) => {
  currentPage.value = page
}

// 添加到自选股
const handleAddToWatchlist = (quote: Quote) => {
  if (quote.symbol?.symbol) {
    emit('add-to-watchlist', quote.symbol.symbol)
  }
}
</script>

<style scoped>
.all-quotes-panel {
  min-height: 400px;
}

.filter-bar {
  margin-bottom: 16px;
  padding: 16px;
  background: var(--el-bg-color-page);
  border-radius: 6px;
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

.symbol-meta {
  display: flex;
  gap: 8px;
  font-size: 11px;
  color: #c0c4cc;
}

.exchange {
  background: #e1f3d8;
  color: #67c23a;
  padding: 1px 4px;
  border-radius: 2px;
}

.asset-type {
  background: #ecf5ff;
  color: #409eff;
  padding: 1px 4px;
  border-radius: 2px;
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

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

:deep(.el-table__row:hover) {
  background-color: var(--el-fill-color-light);
}
</style>