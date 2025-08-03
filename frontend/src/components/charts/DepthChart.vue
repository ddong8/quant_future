<template>
  <div class="depth-chart">
    <!-- 图表工具栏 -->
    <div class="chart-toolbar">
      <div class="toolbar-left">
        <h3 class="chart-title">{{ symbol }} 市场深度</h3>
      </div>
      <div class="toolbar-right">
        <el-button size="small" @click="refreshData" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button size="small" @click="showAnalysis = !showAnalysis">
          <el-icon><DataAnalysis /></el-icon>
          {{ showAnalysis ? '隐藏' : '显示' }}分析
        </el-button>
      </div>
    </div>

    <!-- 深度分析面板 -->
    <div v-if="showAnalysis && depthAnalysis" class="analysis-panel">
      <div class="analysis-item">
        <span class="label">买盘占比:</span>
        <span class="value" :class="{ 'buy-heavy': depthAnalysis.bid_ratio > 55 }">
          {{ depthAnalysis.bid_ratio }}%
        </span>
      </div>
      <div class="analysis-item">
        <span class="label">卖盘占比:</span>
        <span class="value" :class="{ 'sell-heavy': depthAnalysis.ask_ratio > 55 }">
          {{ depthAnalysis.ask_ratio }}%
        </span>
      </div>
      <div class="analysis-item">
        <span class="label">失衡程度:</span>
        <el-tag :type="getImbalanceType(depthAnalysis.imbalance_level)" size="small">
          {{ getImbalanceText(depthAnalysis.imbalance_level) }}
        </el-tag>
      </div>
      <div class="analysis-item">
        <span class="label">市场倾向:</span>
        <el-tag :type="getBiasType(depthAnalysis.bias)" size="small">
          {{ getBiasText(depthAnalysis.bias) }}
        </el-tag>
      </div>
    </div>

    <!-- 深度图表 -->
    <div class="chart-container">
      <div ref="chartRef" class="depth-chart-canvas"></div>
    </div>

    <!-- 深度数据表格 -->
    <div class="depth-tables">
      <div class="table-container">
        <h4>买盘深度</h4>
        <el-table :data="bidsData" size="small" max-height="300">
          <el-table-column label="价格" prop="price" width="100" align="right">
            <template #default="{ row }">
              <span class="price buy-price">{{ formatPrice(row.price) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="数量" prop="volume" width="120" align="right">
            <template #default="{ row }">
              {{ formatVolume(row.volume) }}
            </template>
          </el-table-column>
          <el-table-column label="累计" prop="cumulative_volume" width="120" align="right">
            <template #default="{ row }">
              {{ formatVolume(row.cumulative_volume) }}
            </template>
          </el-table-column>
          <el-table-column label="金额" prop="amount" width="120" align="right">
            <template #default="{ row }">
              {{ formatAmount(row.amount) }}
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div class="table-container">
        <h4>卖盘深度</h4>
        <el-table :data="asksData" size="small" max-height="300">
          <el-table-column label="价格" prop="price" width="100" align="right">
            <template #default="{ row }">
              <span class="price sell-price">{{ formatPrice(row.price) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="数量" prop="volume" width="120" align="right">
            <template #default="{ row }">
              {{ formatVolume(row.volume) }}
            </template>
          </el-table-column>
          <el-table-column label="累计" prop="cumulative_volume" width="120" align="right">
            <template #default="{ row }">
              {{ formatVolume(row.cumulative_volume) }}
            </template>
          </el-table-column>
          <el-table-column label="金额" prop="amount" width="120" align="right">
            <template #default="{ row }">
              {{ formatAmount(row.amount) }}
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, DataAnalysis } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import type { ECharts } from 'echarts'
import { getMarketDepth, analyzeDepthImbalance, type MarketDepth, type DepthAnalysis } from '@/api/marketDepth'
import { formatPrice, formatVolume, formatAmount } from '@/utils/format'

interface Props {
  symbol: string
  height?: number
  autoRefresh?: boolean
  refreshInterval?: number
}

const props = withDefaults(defineProps<Props>(), {
  symbol: 'AAPL',
  height: 400,
  autoRefresh: true,
  refreshInterval: 5000
})

// 响应式数据
const loading = ref(false)
const showAnalysis = ref(true)
const chartRef = ref<HTMLElement>()
let chart: ECharts | null = null

// 数据
const depthData = ref<MarketDepth | null>(null)
const depthAnalysis = ref<DepthAnalysis | null>(null)
const bidsData = ref<any[]>([])
const asksData = ref<any[]>([])

// 定时器
let refreshTimer: NodeJS.Timeout | null = null

// 初始化图表
const initChart = () => {
  if (!chartRef.value) return
  
  chart = echarts.init(chartRef.value)
  updateChart()
}

// 更新图表
const updateChart = () => {
  if (!chart || !depthData.value) return
  
  const { bids, asks } = depthData.value
  
  // 准备数据
  const bidPrices = bids.map(item => item.price)
  const bidVolumes = bids.map(item => item.cumulative_volume)
  const askPrices = asks.map(item => item.price)
  const askVolumes = asks.map(item => item.cumulative_volume)
  
  const option = {
    title: {
      text: '市场深度图',
      left: 'center',
      textStyle: {
        fontSize: 14
      }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      },
      formatter: function(params: any) {
        const param = params[0]
        const price = param.axisValue
        const volume = param.data
        const side = param.seriesName
        return `${side}<br/>价格: ${price}<br/>累计量: ${formatVolume(volume)}`
      }
    },
    legend: {
      data: ['买盘深度', '卖盘深度'],
      top: 30
    },
    grid: {
      left: '10%',
      right: '10%',
      top: '20%',
      bottom: '15%'
    },
    xAxis: {
      type: 'value',
      name: '价格',
      nameLocation: 'middle',
      nameGap: 25,
      axisLabel: {
        formatter: function(value: number) {
          return formatPrice(value)
        }
      }
    },
    yAxis: {
      type: 'value',
      name: '累计量',
      nameLocation: 'middle',
      nameGap: 40,
      axisLabel: {
        formatter: function(value: number) {
          return formatVolume(value)
        }
      }
    },
    series: [
      {
        name: '买盘深度',
        type: 'line',
        data: bidPrices.map((price, index) => [price, bidVolumes[index]]),
        smooth: false,
        step: 'end',
        lineStyle: {
          color: '#67c23a',
          width: 2
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 1, y2: 0,
            colorStops: [
              { offset: 0, color: 'rgba(103, 194, 58, 0.3)' },
              { offset: 1, color: 'rgba(103, 194, 58, 0.1)' }
            ]
          }
        },
        showSymbol: false
      },
      {
        name: '卖盘深度',
        type: 'line',
        data: askPrices.map((price, index) => [price, askVolumes[index]]),
        smooth: false,
        step: 'end',
        lineStyle: {
          color: '#f56c6c',
          width: 2
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 1, y2: 0,
            colorStops: [
              { offset: 0, color: 'rgba(245, 108, 108, 0.1)' },
              { offset: 1, color: 'rgba(245, 108, 108, 0.3)' }
            ]
          }
        },
        showSymbol: false
      }
    ]
  }
  
  chart.setOption(option, true)
}

// 加载数据
const loadData = async () => {
  try {
    loading.value = true
    
    // 获取深度数据
    const depthResponse = await getMarketDepth(props.symbol, 20)
    depthData.value = depthResponse.data
    
    // 更新表格数据
    bidsData.value = depthResponse.data.bids.slice(0, 10).reverse() // 买盘从高到低
    asksData.value = depthResponse.data.asks.slice(0, 10) // 卖盘从低到高
    
    // 获取深度分析
    const analysisResponse = await analyzeDepthImbalance(props.symbol)
    depthAnalysis.value = analysisResponse.data
    
    // 更新图表
    await nextTick()
    updateChart()
    
  } catch (error) {
    console.error('加载深度数据失败:', error)
    ElMessage.error('加载深度数据失败')
  } finally {
    loading.value = false
  }
}

// 刷新数据
const refreshData = () => {
  loadData()
}

// 获取失衡程度类型
const getImbalanceType = (level: string) => {
  switch (level) {
    case 'HIGH': return 'danger'
    case 'MEDIUM': return 'warning'
    case 'LOW': return 'success'
    default: return 'info'
  }
}

// 获取失衡程度文本
const getImbalanceText = (level: string) => {
  switch (level) {
    case 'HIGH': return '高度失衡'
    case 'MEDIUM': return '中度失衡'
    case 'LOW': return '基本平衡'
    default: return '未知'
  }
}

// 获取市场倾向类型
const getBiasType = (bias: string) => {
  switch (bias) {
    case 'BUY_HEAVY': return 'success'
    case 'SELL_HEAVY': return 'danger'
    case 'BALANCED': return 'info'
    default: return 'info'
  }
}

// 获取市场倾向文本
const getBiasText = (bias: string) => {
  switch (bias) {
    case 'BUY_HEAVY': return '买盘占优'
    case 'SELL_HEAVY': return '卖盘占优'
    case 'BALANCED': return '买卖平衡'
    default: return '未知'
  }
}

// 启动自动刷新
const startAutoRefresh = () => {
  if (props.autoRefresh) {
    refreshTimer = setInterval(() => {
      loadData()
    }, props.refreshInterval)
  }
}

// 停止自动刷新
const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

// 窗口大小调整
const handleResize = () => {
  chart?.resize()
}

// 监听symbol变化
watch(() => props.symbol, () => {
  loadData()
})

// 组件挂载
onMounted(() => {
  initChart()
  loadData()
  startAutoRefresh()
  window.addEventListener('resize', handleResize)
})

// 组件卸载
onUnmounted(() => {
  chart?.dispose()
  stopAutoRefresh()
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.depth-chart {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.chart-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #e4e7ed;
}

.chart-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.toolbar-right {
  display: flex;
  gap: 8px;
}

.analysis-panel {
  display: flex;
  justify-content: space-around;
  padding: 16px;
  background: #f8f9fa;
  border-bottom: 1px solid #e4e7ed;
}

.analysis-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.analysis-item .label {
  font-size: 12px;
  color: #909399;
}

.analysis-item .value {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.analysis-item .value.buy-heavy {
  color: #67c23a;
}

.analysis-item .value.sell-heavy {
  color: #f56c6c;
}

.chart-container {
  padding: 16px;
}

.depth-chart-canvas {
  width: 100%;
  height: 400px;
}

.depth-tables {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  padding: 16px;
  border-top: 1px solid #e4e7ed;
}

.table-container h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.price {
  font-family: 'Courier New', monospace;
  font-weight: 600;
}

.buy-price {
  color: #67c23a;
}

.sell-price {
  color: #f56c6c;
}

:deep(.el-table__row:hover) {
  background-color: #f5f7fa;
}

:deep(.el-table th) {
  background-color: #fafafa;
}
</style>