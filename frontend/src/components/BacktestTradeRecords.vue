<template>
  <div class="backtest-trade-records">
    <div class="records-header">
      <div class="header-left">
        <h3>交易记录</h3>
        <div class="records-stats">
          <span class="stat-item">
            总交易: <strong>{{ trades.length }}</strong>
          </span>
          <span class="stat-item">
            盈利: <strong class="profit">{{ profitableTrades }}</strong>
          </span>
          <span class="stat-item">
            亏损: <strong class="loss">{{ losingTrades }}</strong>
          </span>
          <span class="stat-item">
            胜率: <strong>{{ winRate }}%</strong>
          </span>
        </div>
      </div>
      
      <div class="header-actions">
        <el-select v-model="filters.symbol" placeholder="品种" clearable size="small">
          <el-option
            v-for="symbol in availableSymbols"
            :key="symbol"
            :label="symbol"
            :value="symbol"
          />
        </el-select>
        
        <el-select v-model="filters.side" placeholder="方向" clearable size="small">
          <el-option label="买入" value="buy" />
          <el-option label="卖出" value="sell" />
        </el-select>
        
        <el-date-picker
          v-model="filters.dateRange"
          type="datetimerange"
          range-separator="至"
          start-placeholder="开始时间"
          end-placeholder="结束时间"
          size="small"
          style="width: 300px"
        />
        
        <el-button size="small" @click="handleExport">
          <el-icon><Download /></el-icon>
          导出
        </el-button>
      </div>
    </div>

    <!-- 交易记录表格 -->
    <div class="records-table">
      <el-table
        :data="filteredTrades"
        :default-sort="{ prop: 'timestamp', order: 'descending' }"
        height="600"
        stripe
      >
        <el-table-column prop="id" label="ID" width="80" />
        
        <el-table-column prop="timestamp" label="时间" width="180" sortable>
          <template #default="{ row }">
            {{ formatDateTime(row.timestamp) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="symbol" label="品种" width="120" sortable>
          <template #default="{ row }">
            <el-tag size="small">{{ row.symbol }}</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="side" label="方向" width="80" sortable>
          <template #default="{ row }">
            <el-tag :type="row.side === 'buy' ? 'success' : 'danger'" size="small">
              {{ row.side === 'buy' ? '买入' : '卖出' }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="quantity" label="数量" width="100" sortable align="right">
          <template #default="{ row }">
            {{ formatNumber(row.quantity) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="price" label="价格" width="120" sortable align="right">
          <template #default="{ row }">
            {{ formatPrice(row.price) }}
          </template>
        </el-table-column>
        
        <el-table-column label="成交金额" width="140" align="right">
          <template #default="{ row }">
            {{ formatCurrency(row.quantity * row.price) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="commission" label="手续费" width="100" sortable align="right">
          <template #default="{ row }">
            {{ formatCurrency(row.commission) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="slippage" label="滑点" width="100" sortable align="right">
          <template #default="{ row }">
            {{ formatCurrency(row.slippage) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="pnl" label="盈亏" width="120" sortable align="right">
          <template #default="{ row }">
            <span :class="getPnlClass(row.pnl)">
              {{ formatCurrency(row.pnl) }}
            </span>
          </template>
        </el-table-column>
        
        <el-table-column prop="cumulative_pnl" label="累计盈亏" width="140" sortable align="right">
          <template #default="{ row }">
            <span :class="getPnlClass(row.cumulative_pnl)">
              {{ formatCurrency(row.cumulative_pnl) }}
            </span>
          </template>
        </el-table-column>
        
        <el-table-column prop="strategy_signal" label="信号" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.strategy_signal" type="info" size="small">
              {{ row.strategy_signal }}
            </el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button text size="small" @click="viewTradeDetail(row)">
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 分页 -->
    <div class="records-pagination">
      <el-pagination
        v-model:current-page="pagination.current"
        v-model:page-size="pagination.size"
        :total="filteredTrades.length"
        :page-sizes="[50, 100, 200, 500]"
        layout="total, sizes, prev, pager, next, jumper"
      />
    </div>

    <!-- 交易详情对话框 -->
    <el-dialog v-model="showDetailDialog" title="交易详情" width="600px">
      <div v-if="selectedTrade" class="trade-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="交易ID">
            {{ selectedTrade.id }}
          </el-descriptions-item>
          <el-descriptions-item label="时间">
            {{ formatDateTime(selectedTrade.timestamp) }}
          </el-descriptions-item>
          <el-descriptions-item label="品种">
            {{ selectedTrade.symbol }}
          </el-descriptions-item>
          <el-descriptions-item label="方向">
            <el-tag :type="selectedTrade.side === 'buy' ? 'success' : 'danger'" size="small">
              {{ selectedTrade.side === 'buy' ? '买入' : '卖出' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="数量">
            {{ formatNumber(selectedTrade.quantity) }}
          </el-descriptions-item>
          <el-descriptions-item label="价格">
            {{ formatPrice(selectedTrade.price) }}
          </el-descriptions-item>
          <el-descriptions-item label="成交金额">
            {{ formatCurrency(selectedTrade.quantity * selectedTrade.price) }}
          </el-descriptions-item>
          <el-descriptions-item label="手续费">
            {{ formatCurrency(selectedTrade.commission) }}
          </el-descriptions-item>
          <el-descriptions-item label="滑点成本">
            {{ formatCurrency(selectedTrade.slippage) }}
          </el-descriptions-item>
          <el-descriptions-item label="盈亏">
            <span :class="getPnlClass(selectedTrade.pnl)">
              {{ formatCurrency(selectedTrade.pnl) }}
            </span>
          </el-descriptions-item>
          <el-descriptions-item label="累计盈亏">
            <span :class="getPnlClass(selectedTrade.cumulative_pnl)">
              {{ formatCurrency(selectedTrade.cumulative_pnl) }}
            </span>
          </el-descriptions-item>
          <el-descriptions-item label="策略信号">
            {{ selectedTrade.strategy_signal || '-' }}
          </el-descriptions-item>
        </el-descriptions>
        
        <div v-if="selectedTrade.metadata" class="trade-metadata">
          <h4>附加信息</h4>
          <pre class="metadata-content">{{ JSON.stringify(selectedTrade.metadata, null, 2) }}</pre>
        </div>
      </div>
    </el-dialog>

    <!-- 统计图表 -->
    <div class="trade-charts">
      <el-row :gutter="16">
        <el-col :span="12">
          <el-card title="盈亏分布">
            <div ref="pnlDistributionChartRef" class="chart-container"></div>
          </el-card>
        </el-col>
        
        <el-col :span="12">
          <el-card title="交易频率">
            <div ref="tradeFrequencyChartRef" class="chart-container"></div>
          </el-card>
        </el-col>
      </el-row>
      
      <el-row :gutter="16" style="margin-top: 16px">
        <el-col :span="24">
          <el-card title="累计盈亏曲线">
            <div ref="cumulativePnlChartRef" class="chart-container"></div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Download } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import type { TradeRecord } from '@/types/backtest'

interface Props {
  trades: TradeRecord[]
}

const props = defineProps<Props>()

// 响应式数据
const showDetailDialog = ref(false)
const selectedTrade = ref<TradeRecord | null>(null)

// 筛选条件
const filters = ref({
  symbol: '',
  side: '',
  dateRange: []
})

// 分页
const pagination = ref({
  current: 1,
  size: 100
})

// 图表实例
const pnlDistributionChartRef = ref<HTMLElement>()
const tradeFrequencyChartRef = ref<HTMLElement>()
const cumulativePnlChartRef = ref<HTMLElement>()

let pnlDistributionChart: echarts.ECharts | null = null
let tradeFrequencyChart: echarts.ECharts | null = null
let cumulativePnlChart: echarts.ECharts | null = null

// 计算属性
const availableSymbols = computed(() => {
  const symbols = new Set(props.trades.map(trade => trade.symbol))
  return Array.from(symbols)
})

const filteredTrades = computed(() => {
  let result = props.trades
  
  // 品种筛选
  if (filters.value.symbol) {
    result = result.filter(trade => trade.symbol === filters.value.symbol)
  }
  
  // 方向筛选
  if (filters.value.side) {
    result = result.filter(trade => trade.side === filters.value.side)
  }
  
  // 时间筛选
  if (filters.value.dateRange && filters.value.dateRange.length === 2) {
    const [startDate, endDate] = filters.value.dateRange
    result = result.filter(trade => {
      const tradeTime = new Date(trade.timestamp).getTime()
      return tradeTime >= startDate.getTime() && tradeTime <= endDate.getTime()
    })
  }
  
  return result
})

const profitableTrades = computed(() => {
  return filteredTrades.value.filter(trade => trade.pnl > 0).length
})

const losingTrades = computed(() => {
  return filteredTrades.value.filter(trade => trade.pnl < 0).length
})

const winRate = computed(() => {
  if (filteredTrades.value.length === 0) return 0
  return ((profitableTrades.value / filteredTrades.value.length) * 100).toFixed(1)
})

// 方法
const initCharts = async () => {
  await nextTick()
  
  if (pnlDistributionChartRef.value) {
    pnlDistributionChart = echarts.init(pnlDistributionChartRef.value)
    updatePnlDistributionChart()
  }
  
  if (tradeFrequencyChartRef.value) {
    tradeFrequencyChart = echarts.init(tradeFrequencyChartRef.value)
    updateTradeFrequencyChart()
  }
  
  if (cumulativePnlChartRef.value) {
    cumulativePnlChart = echarts.init(cumulativePnlChartRef.value)
    updateCumulativePnlChart()
  }
  
  window.addEventListener('resize', handleResize)
}

const updatePnlDistributionChart = () => {
  if (!pnlDistributionChart) return
  
  // 计算盈亏分布
  const pnlRanges = [
    { range: '< -1000', min: -Infinity, max: -1000, count: 0 },
    { range: '-1000 ~ -500', min: -1000, max: -500, count: 0 },
    { range: '-500 ~ 0', min: -500, max: 0, count: 0 },
    { range: '0 ~ 500', min: 0, max: 500, count: 0 },
    { range: '500 ~ 1000', min: 500, max: 1000, count: 0 },
    { range: '> 1000', min: 1000, max: Infinity, count: 0 }
  ]
  
  filteredTrades.value.forEach(trade => {
    const pnl = trade.pnl
    for (const range of pnlRanges) {
      if (pnl > range.min && pnl <= range.max) {
        range.count++
        break
      }
    }
  })
  
  const option = {
    title: {
      text: '盈亏分布',
      textStyle: { fontSize: 14 }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    xAxis: {
      type: 'category',
      data: pnlRanges.map(r => r.range)
    },
    yAxis: {
      type: 'value',
      name: '交易次数'
    },
    series: [{
      data: pnlRanges.map(r => ({
        value: r.count,
        itemStyle: {
          color: r.min >= 0 ? '#67c23a' : '#f56c6c'
        }
      })),
      type: 'bar'
    }]
  }
  
  pnlDistributionChart.setOption(option)
}

const updateTradeFrequencyChart = () => {
  if (!tradeFrequencyChart) return
  
  // 按小时统计交易频率
  const hourlyTrades = new Array(24).fill(0)
  
  filteredTrades.value.forEach(trade => {
    const hour = new Date(trade.timestamp).getHours()
    hourlyTrades[hour]++
  })
  
  const option = {
    title: {
      text: '交易频率(按小时)',
      textStyle: { fontSize: 14 }
    },
    tooltip: {
      trigger: 'axis'
    },
    xAxis: {
      type: 'category',
      data: Array.from({ length: 24 }, (_, i) => `${i}:00`)
    },
    yAxis: {
      type: 'value',
      name: '交易次数'
    },
    series: [{
      data: hourlyTrades,
      type: 'line',
      smooth: true,
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
          { offset: 1, color: 'rgba(64, 158, 255, 0.1)' }
        ])
      },
      lineStyle: { color: '#409eff' }
    }]
  }
  
  tradeFrequencyChart.setOption(option)
}

const updateCumulativePnlChart = () => {
  if (!cumulativePnlChart) return
  
  const data = filteredTrades.value.map(trade => ({
    time: trade.timestamp,
    pnl: trade.cumulative_pnl
  })).sort((a, b) => new Date(a.time).getTime() - new Date(b.time).getTime())
  
  const option = {
    title: {
      text: '累计盈亏曲线',
      textStyle: { fontSize: 14 }
    },
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const point = params[0]
        return `${point.axisValue}<br/>累计盈亏: ${formatCurrency(point.value)}`
      }
    },
    xAxis: {
      type: 'category',
      data: data.map(d => formatDateTime(d.time))
    },
    yAxis: {
      type: 'value',
      name: '累计盈亏'
    },
    series: [{
      data: data.map(d => d.pnl),
      type: 'line',
      smooth: true,
      lineStyle: { color: '#67c23a' }
    }]
  }
  
  cumulativePnlChart.setOption(option)
}

const handleResize = () => {
  pnlDistributionChart?.resize()
  tradeFrequencyChart?.resize()
  cumulativePnlChart?.resize()
}

const viewTradeDetail = (trade: TradeRecord) => {
  selectedTrade.value = trade
  showDetailDialog.value = true
}

const handleExport = () => {
  // 导出交易记录
  const csvContent = [
    ['ID', '时间', '品种', '方向', '数量', '价格', '成交金额', '手续费', '滑点', '盈亏', '累计盈亏', '策略信号'].join(','),
    ...filteredTrades.value.map(trade => [
      trade.id,
      trade.timestamp,
      trade.symbol,
      trade.side === 'buy' ? '买入' : '卖出',
      trade.quantity,
      trade.price,
      trade.quantity * trade.price,
      trade.commission,
      trade.slippage,
      trade.pnl,
      trade.cumulative_pnl,
      trade.strategy_signal || ''
    ].join(','))
  ].join('\n')
  
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `trade_records_${new Date().toISOString().split('T')[0]}.csv`
  link.click()
  
  ElMessage.success('交易记录已导出')
}

// 格式化函数
const formatDateTime = (dateString: string) => {
  return new Date(dateString).toLocaleString('zh-CN')
}

const formatNumber = (num: number) => {
  return new Intl.NumberFormat('zh-CN').format(num)
}

const formatPrice = (price: number) => {
  return price.toFixed(2)
}

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY'
  }).format(value)
}

const getPnlClass = (pnl: number) => {
  if (pnl > 0) return 'profit'
  if (pnl < 0) return 'loss'
  return 'neutral'
}

// 生命周期
onMounted(() => {
  initCharts()
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  
  pnlDistributionChart?.dispose()
  tradeFrequencyChart?.dispose()
  cumulativePnlChart?.dispose()
})
</script>

<style scoped lang="scss">
.backtest-trade-records {
  .records-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 16px;
    padding: 16px;
    background: var(--el-bg-color);
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    
    .header-left {
      h3 {
        margin: 0 0 8px 0;
        font-size: 18px;
        font-weight: 600;
        color: #303133;
      }
      
      .records-stats {
        display: flex;
        gap: 16px;
        
        .stat-item {
          font-size: 14px;
          color: #606266;
          
          strong {
            color: #303133;
            
            &.profit {
              color: #67c23a;
            }
            
            &.loss {
              color: #f56c6c;
            }
          }
        }
      }
    }
    
    .header-actions {
      display: flex;
      gap: 12px;
      align-items: center;
    }
  }
  
  .records-table {
    background: var(--el-bg-color);
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    
    .profit {
      color: #67c23a;
      font-weight: 600;
    }
    
    .loss {
      color: #f56c6c;
      font-weight: 600;
    }
    
    .neutral {
      color: #909399;
    }
  }
  
  .records-pagination {
    display: flex;
    justify-content: center;
    padding: 20px;
  }
  
  .trade-detail {
    .trade-metadata {
      margin-top: 20px;
      
      h4 {
        margin: 0 0 12px 0;
        font-size: 14px;
        color: #303133;
      }
      
      .metadata-content {
        background: var(--el-bg-color-page);
        padding: 12px;
        border-radius: 4px;
        font-size: 12px;
        color: #606266;
        max-height: 200px;
        overflow-y: auto;
      }
    }
  }
  
  .trade-charts {
    margin-top: 24px;
    
    .chart-container {
      height: 300px;
    }
  }
}
</style>