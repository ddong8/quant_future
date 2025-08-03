<template>
  <div class="portfolio-summary">
    <div class="summary-cards">
      <!-- 总市值 -->
      <div class="summary-card">
        <div class="card-icon market-value">
          <el-icon><TrendCharts /></el-icon>
        </div>
        <div class="card-content">
          <div class="card-title">总市值</div>
          <div class="card-value">{{ formatCurrency(portfolioMetrics?.total_market_value || 0) }}</div>
          <div class="card-change" :class="getChangeClass(portfolioMetrics?.return_rate || 0)">
            <el-icon v-if="(portfolioMetrics?.return_rate || 0) > 0"><ArrowUp /></el-icon>
            <el-icon v-else-if="(portfolioMetrics?.return_rate || 0) < 0"><ArrowDown /></el-icon>
            {{ formatPercent(portfolioMetrics?.return_rate || 0) }}
          </div>
        </div>
      </div>

      <!-- 总盈亏 -->
      <div class="summary-card">
        <div class="card-icon pnl" :class="getPnLClass(portfolioMetrics?.total_pnl || 0)">
          <el-icon><Money /></el-icon>
        </div>
        <div class="card-content">
          <div class="card-title">总盈亏</div>
          <div class="card-value" :class="getPnLClass(portfolioMetrics?.total_pnl || 0)">
            {{ formatCurrency(portfolioMetrics?.total_pnl || 0) }}
          </div>
          <div class="card-subtitle">
            已实现: {{ formatCurrency(portfolioMetrics?.total_realized_pnl || 0) }}
          </div>
        </div>
      </div>

      <!-- 持仓数量 -->
      <div class="summary-card">
        <div class="card-icon positions">
          <el-icon><Grid /></el-icon>
        </div>
        <div class="card-content">
          <div class="card-title">持仓数量</div>
          <div class="card-value">{{ portfolioMetrics?.total_positions || 0 }}</div>
          <div class="card-subtitle">
            开仓: {{ statistics?.open_positions || 0 }} | 
            平仓: {{ statistics?.closed_positions || 0 }}
          </div>
        </div>
      </div>

      <!-- 胜率 -->
      <div class="summary-card">
        <div class="card-icon win-rate">
          <el-icon><Trophy /></el-icon>
        </div>
        <div class="card-content">
          <div class="card-title">胜率</div>
          <div class="card-value">{{ formatPercent(statistics?.win_rate || 0) }}</div>
          <div class="card-subtitle">
            盈利: {{ statistics?.profit_positions || 0 }} | 
            亏损: {{ statistics?.loss_positions || 0 }}
          </div>
        </div>
      </div>
    </div>

    <!-- 持仓分布图表 -->
    <div class="portfolio-charts">
      <div class="chart-container">
        <div class="chart-header">
          <h3>持仓分布</h3>
          <el-button-group>
            <el-button 
              :type="chartType === 'pie' ? 'primary' : 'default'"
              size="small"
              @click="chartType = 'pie'"
            >
              饼图
            </el-button>
            <el-button 
              :type="chartType === 'bar' ? 'primary' : 'default'"
              size="small"
              @click="chartType = 'bar'"
            >
              柱图
            </el-button>
          </el-button-group>
        </div>
        <div ref="chartRef" class="chart" style="height: 300px;"></div>
      </div>

      <!-- 持仓列表 -->
      <div class="position-list">
        <div class="list-header">
          <h3>主要持仓</h3>
        </div>
        <div class="position-items">
          <div 
            v-for="(position, symbol) in topPositions" 
            :key="symbol"
            class="position-item"
          >
            <div class="position-symbol">{{ symbol }}</div>
            <div class="position-info">
              <div class="position-value">{{ formatCurrency(position.total_market_value) }}</div>
              <div class="position-pnl" :class="getPnLClass(position.total_pnl)">
                {{ formatCurrency(position.total_pnl) }}
              </div>
            </div>
            <div class="position-weight">
              {{ formatPercent(position.total_market_value / (portfolioMetrics?.total_market_value || 1)) }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { 
  TrendCharts, 
  Money, 
  Grid, 
  Trophy, 
  ArrowUp, 
  ArrowDown 
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { usePositionStore } from '@/stores/position'
import { formatCurrency, formatPercent } from '@/utils/format'

// 状态管理
const positionStore = usePositionStore()

// 响应式数据
const chartRef = ref<HTMLElement>()
const chartType = ref<'pie' | 'bar'>('pie')
let chart: echarts.ECharts | null = null

// 计算属性
const portfolioMetrics = computed(() => positionStore.portfolioMetrics)
const statistics = computed(() => positionStore.statistics)

const topPositions = computed(() => {
  if (!portfolioMetrics.value?.positions_by_symbol) return {}
  
  const positions = portfolioMetrics.value.positions_by_symbol
  const sorted = Object.entries(positions)
    .sort(([, a], [, b]) => b.total_market_value - a.total_market_value)
    .slice(0, 5)
  
  return Object.fromEntries(sorted)
})

const chartData = computed(() => {
  if (!portfolioMetrics.value?.positions_by_symbol) return []
  
  return Object.entries(portfolioMetrics.value.positions_by_symbol)
    .map(([symbol, data]) => ({
      name: symbol,
      value: data.total_market_value,
      pnl: data.total_pnl
    }))
    .sort((a, b) => b.value - a.value)
})

// 生命周期
onMounted(() => {
  nextTick(() => {
    initChart()
  })
})

// 监听图表类型变化
watch(chartType, () => {
  updateChart()
})

// 监听数据变化
watch(chartData, () => {
  updateChart()
}, { deep: true })

// 方法
const initChart = () => {
  if (!chartRef.value) return
  
  chart = echarts.init(chartRef.value)
  updateChart()
  
  // 响应式调整
  window.addEventListener('resize', () => {
    chart?.resize()
  })
}

const updateChart = () => {
  if (!chart || !chartData.value.length) return
  
  const option = chartType.value === 'pie' ? getPieOption() : getBarOption()
  chart.setOption(option, true)
}

const getPieOption = () => {
  return {
    tooltip: {
      trigger: 'item',
      formatter: (params: any) => {
        const data = params.data
        const percent = ((data.value / (portfolioMetrics.value?.total_market_value || 1)) * 100).toFixed(1)
        return `
          <div>
            <strong>${data.name}</strong><br/>
            市值: ${formatCurrency(data.value)}<br/>
            占比: ${percent}%<br/>
            盈亏: <span style="color: ${data.pnl >= 0 ? '#67C23A' : '#F56C6C'}">${formatCurrency(data.pnl)}</span>
          </div>
        `
      }
    },
    legend: {
      orient: 'vertical',
      left: 'left',
      top: 'middle'
    },
    series: [
      {
        name: '持仓分布',
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['60%', '50%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 4,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: false,
          position: 'center'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 16,
            fontWeight: 'bold'
          }
        },
        labelLine: {
          show: false
        },
        data: chartData.value.map(item => ({
          ...item,
          itemStyle: {
            color: item.pnl >= 0 ? '#67C23A' : '#F56C6C'
          }
        }))
      }
    ]
  }
}

const getBarOption = () => {
  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      formatter: (params: any) => {
        const data = params[0]
        const item = chartData.value[data.dataIndex]
        return `
          <div>
            <strong>${data.name}</strong><br/>
            市值: ${formatCurrency(data.value)}<br/>
            盈亏: <span style="color: ${item.pnl >= 0 ? '#67C23A' : '#F56C6C'}">${formatCurrency(item.pnl)}</span>
          </div>
        `
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: chartData.value.map(item => item.name),
      axisTick: {
        alignWithLabel: true
      }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: (value: number) => formatCurrency(value, 0)
      }
    },
    series: [
      {
        name: '市值',
        type: 'bar',
        barWidth: '60%',
        data: chartData.value.map(item => ({
          value: item.value,
          itemStyle: {
            color: item.pnl >= 0 ? '#67C23A' : '#F56C6C'
          }
        }))
      }
    ]
  }
}

const getChangeClass = (value: number) => {
  if (value > 0) return 'positive'
  if (value < 0) return 'negative'
  return 'neutral'
}

const getPnLClass = (value: number) => {
  if (value > 0) return 'profit'
  if (value < 0) return 'loss'
  return 'neutral'
}
</script>

<style scoped>
.portfolio-summary {
  margin-bottom: 24px;
}

.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.summary-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  gap: 16px;
}

.card-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: white;
}

.card-icon.market-value {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.card-icon.pnl.profit {
  background: linear-gradient(135deg, #67C23A 0%, #85ce61 100%);
}

.card-icon.pnl.loss {
  background: linear-gradient(135deg, #F56C6C 0%, #f78989 100%);
}

.card-icon.pnl.neutral {
  background: linear-gradient(135deg, #909399 0%, #b1b3b8 100%);
}

.card-icon.positions {
  background: linear-gradient(135deg, #409EFF 0%, #66b1ff 100%);
}

.card-icon.win-rate {
  background: linear-gradient(135deg, #E6A23C 0%, #ebb563 100%);
}

.card-content {
  flex: 1;
}

.card-title {
  font-size: 14px;
  color: #6b7280;
  margin-bottom: 4px;
}

.card-value {
  font-size: 24px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 4px;
}

.card-value.profit {
  color: #67C23A;
}

.card-value.loss {
  color: #F56C6C;
}

.card-change {
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 2px;
}

.card-change.positive {
  color: #67C23A;
}

.card-change.negative {
  color: #F56C6C;
}

.card-change.neutral {
  color: #909399;
}

.card-subtitle {
  font-size: 12px;
  color: #9ca3af;
}

.portfolio-charts {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 24px;
}

.chart-container,
.position-list {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.chart-header,
.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.chart-header h3,
.list-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.position-items {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.position-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  background: #f9fafb;
  border-radius: 6px;
}

.position-symbol {
  font-weight: 600;
  color: #1f2937;
}

.position-info {
  flex: 1;
  text-align: right;
  margin-right: 12px;
}

.position-value {
  font-size: 14px;
  font-weight: 500;
  color: #1f2937;
}

.position-pnl {
  font-size: 12px;
}

.position-pnl.profit {
  color: #67C23A;
}

.position-pnl.loss {
  color: #F56C6C;
}

.position-weight {
  font-size: 12px;
  color: #6b7280;
  min-width: 50px;
  text-align: right;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .portfolio-charts {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .summary-cards {
    grid-template-columns: 1fr;
  }
  
  .summary-card {
    padding: 16px;
  }
  
  .card-value {
    font-size: 20px;
  }
}
</style>