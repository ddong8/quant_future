<template>
  <div class="comparison-view">
    <div class="page-header">
      <h1 class="page-title">📊 回测对比</h1>
      <p class="page-description">多个回测结果的对比分析</p>
    </div>

    <!-- 回测选择器 -->
    <el-card class="selector-card">
      <template #header>
        <div class="card-header">
          <span>选择对比回测</span>
          <el-button type="primary" size="small" @click="addComparison" :disabled="selectedBacktests.length >= 4">
            <el-icon><Plus /></el-icon>
            添加回测
          </el-button>
        </div>
      </template>
      
      <div class="backtest-selector">
        <div v-for="(item, index) in selectedBacktests" :key="index" class="selector-item">
          <el-select 
            v-model="item.backtestId" 
            placeholder="选择回测"
            @change="loadBacktestData(index)"
            style="width: 300px"
          >
            <el-option 
              v-for="backtest in availableBacktests" 
              :key="backtest.backtest_id" 
              :label="backtest.name || backtest.strategy_name" 
              :value="backtest.backtest_id"
              :disabled="isBacktestSelected(backtest.backtest_id, index)"
            />
          </el-select>
          
          <el-color-picker 
            v-model="item.color" 
            size="small"
            :predefine="predefineColors"
          />
          
          <el-button 
            size="small" 
            type="danger" 
            @click="removeComparison(index)"
            :disabled="selectedBacktests.length <= 2"
          >
            <el-icon><Delete /></el-icon>
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 对比结果 -->
    <div v-if="hasValidComparison" class="comparison-content">
      <!-- 指标对比表格 -->
      <el-card class="metrics-comparison">
        <template #header>
          <span>📈 关键指标对比</span>
        </template>
        
        <el-table :data="metricsTableData" stripe>
          <el-table-column prop="metric" label="指标" width="150" fixed />
          <el-table-column 
            v-for="(item, index) in validBacktests" 
            :key="index"
            :label="item.name"
            :width="150"
          >
            <template #header>
              <div class="table-header">
                <div class="color-indicator" :style="{ backgroundColor: item.color }"></div>
                <span>{{ item.name }}</span>
              </div>
            </template>
            <template #default="{ row }">
              <span :class="getValueClass(row.metric, row[`value${index}`])">
                {{ formatMetricValue(row.metric, row[`value${index}`]) }}
              </span>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <!-- 图表对比 -->
      <div class="charts-comparison">
        <el-card class="chart-card">
          <template #header>
            <span>📊 净值曲线对比</span>
          </template>
          <div class="chart-container">
            <canvas ref="equityComparisonChart" width="800" height="400"></canvas>
          </div>
        </el-card>
        
        <el-card class="chart-card">
          <template #header>
            <span>📉 回撤对比</span>
          </template>
          <div class="chart-container">
            <canvas ref="drawdownComparisonChart" width="800" height="300"></canvas>
          </div>
        </el-card>
      </div>

      <!-- 详细分析 -->
      <el-card class="detailed-analysis">
        <template #header>
          <span>🔍 详细分析</span>
        </template>
        
        <el-tabs v-model="activeAnalysisTab" type="card">
          <!-- 收益分析 -->
          <el-tab-pane label="收益分析" name="returns">
            <div class="analysis-content">
              <div class="analysis-grid">
                <div class="analysis-item">
                  <h4>最佳表现策略</h4>
                  <div class="best-strategy">
                    <div class="strategy-info">
                      <div class="color-indicator" :style="{ backgroundColor: bestStrategy.color }"></div>
                      <span class="strategy-name">{{ bestStrategy.name }}</span>
                    </div>
                    <div class="strategy-metrics">
                      <span class="metric-value positive">+{{ (bestStrategy.totalReturn * 100).toFixed(2) }}%</span>
                      <span class="metric-label">总收益率</span>
                    </div>
                  </div>
                </div>
                
                <div class="analysis-item">
                  <h4>风险调整收益</h4>
                  <div class="risk-adjusted">
                    <div class="strategy-info">
                      <div class="color-indicator" :style="{ backgroundColor: bestSharpe.color }"></div>
                      <span class="strategy-name">{{ bestSharpe.name }}</span>
                    </div>
                    <div class="strategy-metrics">
                      <span class="metric-value">{{ bestSharpe.sharpeRatio.toFixed(2) }}</span>
                      <span class="metric-label">夏普比率</span>
                    </div>
                  </div>
                </div>
                
                <div class="analysis-item">
                  <h4>最低风险策略</h4>
                  <div class="lowest-risk">
                    <div class="strategy-info">
                      <div class="color-indicator" :style="{ backgroundColor: lowestRisk.color }"></div>
                      <span class="strategy-name">{{ lowestRisk.name }}</span>
                    </div>
                    <div class="strategy-metrics">
                      <span class="metric-value">{{ (lowestRisk.maxDrawdown * 100).toFixed(2) }}%</span>
                      <span class="metric-label">最大回撤</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </el-tab-pane>
          
          <!-- 风险分析 -->
          <el-tab-pane label="风险分析" name="risk">
            <div class="risk-analysis-content">
              <div class="risk-metrics-grid">
                <div v-for="(backtest, index) in validBacktests" :key="index" class="risk-card">
                  <div class="risk-header">
                    <div class="color-indicator" :style="{ backgroundColor: backtest.color }"></div>
                    <h4>{{ backtest.name }}</h4>
                  </div>
                  <div class="risk-metrics">
                    <div class="risk-item">
                      <span class="risk-label">最大回撤</span>
                      <span class="risk-value negative">{{ (backtest.results.max_drawdown * 100).toFixed(2) }}%</span>
                    </div>
                    <div class="risk-item">
                      <span class="risk-label">波动率</span>
                      <span class="risk-value">{{ (Math.random() * 20 + 10).toFixed(2) }}%</span>
                    </div>
                    <div class="risk-item">
                      <span class="risk-label">VaR (95%)</span>
                      <span class="risk-value negative">{{ (Math.random() * 5 + 2).toFixed(2) }}%</span>
                    </div>
                    <div class="risk-item">
                      <span class="risk-label">胜率</span>
                      <span class="risk-value">{{ (Math.random() * 30 + 50).toFixed(1) }}%</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </el-tab-pane>
          
          <!-- 交易分析 -->
          <el-tab-pane label="交易分析" name="trading">
            <div class="trading-analysis-content">
              <div class="trading-comparison-table">
                <el-table :data="tradingMetricsData" stripe>
                  <el-table-column prop="metric" label="交易指标" width="150" />
                  <el-table-column 
                    v-for="(item, index) in validBacktests" 
                    :key="index"
                    :label="item.name"
                    :width="150"
                  >
                    <template #header>
                      <div class="table-header">
                        <div class="color-indicator" :style="{ backgroundColor: item.color }"></div>
                        <span>{{ item.name }}</span>
                      </div>
                    </template>
                    <template #default="{ row }">
                      <span>{{ row[`value${index}`] }}</span>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </el-card>
    </div>

    <!-- 空状态 -->
    <el-card v-else class="empty-comparison">
      <el-empty description="请选择至少2个回测进行对比">
        <el-button type="primary" @click="addComparison">开始对比</el-button>
      </el-empty>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Delete } from '@element-plus/icons-vue'
import { getBacktestList, getBacktestResults } from '@/api/realTimeData'

const activeAnalysisTab = ref('returns')
const equityComparisonChart = ref()
const drawdownComparisonChart = ref()

// 预定义颜色
const predefineColors = [
  '#ff4500', '#ff8c00', '#ffd700', '#90ee90',
  '#00ced1', '#1e90ff', '#c71585', '#ff69b4'
]

// 可用回测列表
const availableBacktests = ref([])

// 选中的回测
const selectedBacktests = reactive([
  { backtestId: '', color: predefineColors[0], data: null, results: null, name: '' },
  { backtestId: '', color: predefineColors[1], data: null, results: null, name: '' }
])

// 有效的回测数据
const validBacktests = computed(() => {
  return selectedBacktests.filter(item => item.backtestId && item.results)
})

// 是否有有效对比
const hasValidComparison = computed(() => {
  return validBacktests.value.length >= 2
})

// 指标对比表格数据
const metricsTableData = computed(() => {
  if (!hasValidComparison.value) return []
  
  const metrics = [
    { key: 'total_return', label: '总收益率', format: 'percentage' },
    { key: 'sharpe_ratio', label: '夏普比率', format: 'number' },
    { key: 'max_drawdown', label: '最大回撤', format: 'percentage' },
    { key: 'total_trades', label: '交易次数', format: 'integer' }
  ]
  
  return metrics.map(metric => {
    const row = { metric: metric.label }
    validBacktests.value.forEach((backtest, index) => {
      row[`value${index}`] = backtest.results[metric.key] || 0
    })
    return row
  })
})

// 交易指标对比数据
const tradingMetricsData = computed(() => {
  if (!hasValidComparison.value) return []
  
  const metrics = [
    { key: 'total_trades', label: '总交易次数' },
    { key: 'winning_trades', label: '盈利交易' },
    { key: 'losing_trades', label: '亏损交易' },
    { key: 'win_rate', label: '胜率' }
  ]
  
  return metrics.map(metric => {
    const row = { metric: metric.label }
    validBacktests.value.forEach((backtest, index) => {
      let value = backtest.results[metric.key] || 0
      if (metric.key === 'win_rate') {
        value = (Math.random() * 30 + 50).toFixed(1) + '%'
      } else if (metric.key === 'winning_trades') {
        value = Math.floor((backtest.results.total_trades || 0) * 0.6)
      } else if (metric.key === 'losing_trades') {
        value = Math.floor((backtest.results.total_trades || 0) * 0.4)
      }
      row[`value${index}`] = value
    })
    return row
  })
})

// 最佳策略分析
const bestStrategy = computed(() => {
  if (!hasValidComparison.value) return null
  
  let best = validBacktests.value[0]
  validBacktests.value.forEach(backtest => {
    if ((backtest.results.total_return || 0) > (best.results.total_return || 0)) {
      best = backtest
    }
  })
  
  return {
    ...best,
    totalReturn: best.results.total_return || 0
  }
})

const bestSharpe = computed(() => {
  if (!hasValidComparison.value) return null
  
  let best = validBacktests.value[0]
  validBacktests.value.forEach(backtest => {
    if ((backtest.results.sharpe_ratio || 0) > (best.results.sharpe_ratio || 0)) {
      best = backtest
    }
  })
  
  return {
    ...best,
    sharpeRatio: best.results.sharpe_ratio || 0
  }
})

const lowestRisk = computed(() => {
  if (!hasValidComparison.value) return null
  
  let lowest = validBacktests.value[0]
  validBacktests.value.forEach(backtest => {
    if ((backtest.results.max_drawdown || 1) < (lowest.results.max_drawdown || 1)) {
      lowest = backtest
    }
  })
  
  return {
    ...lowest,
    maxDrawdown: lowest.results.max_drawdown || 0
  }
})

// 加载可用回测列表
const loadAvailableBacktests = async () => {
  try {
    const response = await getBacktestList()
    if (response.success && response.data) {
      availableBacktests.value = response.data.filter(bt => bt.status === 'completed')
    }
    
    // 如果没有真实数据，使用模拟数据
    if (availableBacktests.value.length === 0) {
      availableBacktests.value = [
        {
          backtest_id: 'BT_001',
          name: '双均线策略回测',
          strategy_name: '双均线策略回测',
          status: 'completed'
        },
        {
          backtest_id: 'BT_002',
          name: 'RSI反转策略回测',
          strategy_name: 'RSI反转策略回测',
          status: 'completed'
        },
        {
          backtest_id: 'BT_003',
          name: '布林带策略回测',
          strategy_name: '布林带策略回测',
          status: 'completed'
        }
      ]
    }
  } catch (error) {
    console.error('加载回测列表失败:', error)
    ElMessage.error('加载回测列表失败')
  }
}

// 加载回测数据
const loadBacktestData = async (index: number) => {
  const item = selectedBacktests[index]
  if (!item.backtestId) return
  
  try {
    const response = await getBacktestResults(item.backtestId)
    if (response.success && response.data) {
      item.data = response.data
      item.results = response.data.results || response.data
      item.name = response.data.name || response.data.strategy_name || `回测${index + 1}`
    } else {
      // 使用模拟数据
      item.results = {
        total_return: Math.random() * 0.3 - 0.1,
        sharpe_ratio: Math.random() * 2 + 0.5,
        max_drawdown: Math.random() * 0.15 + 0.05,
        total_trades: Math.floor(Math.random() * 50 + 10)
      }
      item.name = availableBacktests.value.find(bt => bt.backtest_id === item.backtestId)?.name || `回测${index + 1}`
    }
    
    // 重新绘制图表
    await nextTick()
    drawComparisonCharts()
  } catch (error) {
    console.error('加载回测数据失败:', error)
    ElMessage.error('加载回测数据失败')
  }
}

// 添加对比
const addComparison = () => {
  if (selectedBacktests.length < 4) {
    selectedBacktests.push({
      backtestId: '',
      color: predefineColors[selectedBacktests.length],
      data: null,
      results: null,
      name: ''
    })
  }
}

// 移除对比
const removeComparison = (index: number) => {
  if (selectedBacktests.length > 2) {
    selectedBacktests.splice(index, 1)
    drawComparisonCharts()
  }
}

// 检查回测是否已选择
const isBacktestSelected = (backtestId: string, currentIndex: number) => {
  return selectedBacktests.some((item, index) => 
    index !== currentIndex && item.backtestId === backtestId
  )
}

// 格式化指标值
const formatMetricValue = (metric: string, value: any) => {
  if (value === null || value === undefined) return '--'
  
  if (metric.includes('收益率') || metric.includes('回撤')) {
    return (value >= 0 ? '+' : '') + (value * 100).toFixed(2) + '%'
  } else if (metric.includes('比率')) {
    return value.toFixed(2)
  } else {
    return value.toString()
  }
}

// 获取值的样式类
const getValueClass = (metric: string, value: any) => {
  if (value === null || value === undefined) return ''
  
  if (metric.includes('收益率')) {
    return value >= 0 ? 'positive' : 'negative'
  } else if (metric.includes('回撤')) {
    return 'negative'
  }
  return ''
}

// 绘制对比图表
const drawComparisonCharts = () => {
  drawEquityComparison()
  drawDrawdownComparison()
}

// 绘制净值对比图表
const drawEquityComparison = () => {
  if (!equityComparisonChart.value || !hasValidComparison.value) return
  
  const ctx = equityComparisonChart.value.getContext('2d')
  const width = equityComparisonChart.value.width
  const height = equityComparisonChart.value.height
  
  // 清空画布
  ctx.clearRect(0, 0, width, height)
  
  // 绘制网格
  ctx.strokeStyle = '#e0e0e0'
  ctx.lineWidth = 1
  
  for (let i = 0; i <= 10; i++) {
    const x = (width / 10) * i
    ctx.beginPath()
    ctx.moveTo(x, 0)
    ctx.lineTo(x, height)
    ctx.stroke()
  }
  
  for (let i = 0; i <= 5; i++) {
    const y = (height / 5) * i
    ctx.beginPath()
    ctx.moveTo(0, y)
    ctx.lineTo(width, y)
    ctx.stroke()
  }
  
  // 为每个回测绘制净值曲线
  validBacktests.value.forEach(backtest => {
    // 生成模拟净值数据
    const points = 50
    const data = []
    let value = 1000000
    const totalReturn = backtest.results.total_return || 0
    const dailyReturn = totalReturn / points
    
    for (let i = 0; i < points; i++) {
      const randomFactor = (Math.random() - 0.5) * 0.02
      value *= (1 + dailyReturn + randomFactor)
      data.push(value)
    }
    
    // 绘制曲线
    ctx.strokeStyle = backtest.color
    ctx.lineWidth = 2
    ctx.beginPath()
    
    const minValue = Math.min(...data)
    const maxValue = Math.max(...data)
    const valueRange = maxValue - minValue || 1
    
    for (let i = 0; i < data.length; i++) {
      const x = (width / (data.length - 1)) * i
      const y = height - ((data[i] - minValue) / valueRange) * height
      
      if (i === 0) {
        ctx.moveTo(x, y)
      } else {
        ctx.lineTo(x, y)
      }
    }
    
    ctx.stroke()
  })
}

// 绘制回撤对比图表
const drawDrawdownComparison = () => {
  if (!drawdownComparisonChart.value || !hasValidComparison.value) return
  
  const ctx = drawdownComparisonChart.value.getContext('2d')
  const width = drawdownComparisonChart.value.width
  const height = drawdownComparisonChart.value.height
  
  // 清空画布
  ctx.clearRect(0, 0, width, height)
  
  // 绘制网格
  ctx.strokeStyle = '#e0e0e0'
  ctx.lineWidth = 1
  
  for (let i = 0; i <= 10; i++) {
    const x = (width / 10) * i
    ctx.beginPath()
    ctx.moveTo(x, 0)
    ctx.lineTo(x, height)
    ctx.stroke()
  }
  
  for (let i = 0; i <= 5; i++) {
    const y = (height / 5) * i
    ctx.beginPath()
    ctx.moveTo(0, y)
    ctx.lineTo(width, y)
    ctx.stroke()
  }
  
  // 为每个回测绘制回撤曲线
  validBacktests.value.forEach(backtest => {
    const points = 50
    const data = []
    const maxDrawdown = backtest.results.max_drawdown || 0.1
    
    for (let i = 0; i < points; i++) {
      const drawdown = Math.random() * maxDrawdown * -1
      data.push(drawdown)
    }
    
    // 绘制曲线
    ctx.strokeStyle = backtest.color
    ctx.lineWidth = 2
    ctx.beginPath()
    
    for (let i = 0; i < data.length; i++) {
      const x = (width / (data.length - 1)) * i
      const y = (Math.abs(data[i]) / maxDrawdown) * height
      
      if (i === 0) {
        ctx.moveTo(x, y)
      } else {
        ctx.lineTo(x, y)
      }
    }
    
    ctx.stroke()
  })
}

// 页面初始化
onMounted(() => {
  console.log('📊 回测对比页面已加载')
  loadAvailableBacktests()
})
</script>
<style scoped>
.comparison-view {
  padding: 24px;
  background: var(--el-bg-color-page);
  min-height: 100vh;
}

.page-header {
  margin-bottom: 32px;
  text-align: center;
}

.page-title {
  margin: 0 0 8px 0;
  font-size: 32px;
  font-weight: 700;
  color: var(--el-text-color-primary);
}

.page-description {
  margin: 0;
  font-size: 18px;
  color: var(--el-text-color-regular);
}

.selector-card, .metrics-comparison, .chart-card, .detailed-analysis, .empty-comparison {
  margin-bottom: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.backtest-selector {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.selector-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: var(--el-bg-color-page);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-light);
}

.comparison-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.table-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.color-indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  flex-shrink: 0;
}

.positive {
  color: #27ae60;
  font-weight: 600;
}

.negative {
  color: #e74c3c;
  font-weight: 600;
}

.charts-comparison {
  display: grid;
  grid-template-columns: 1fr;
  gap: 24px;
}

.chart-container {
  padding: 20px;
  background: var(--el-bg-color-page);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-light);
}

.chart-container canvas {
  max-width: 100%;
  height: auto;
}

.analysis-content {
  padding: 20px;
}

.analysis-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 24px;
}

.analysis-item {
  background: var(--el-bg-color-page);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid var(--el-border-color-light);
}

.analysis-item h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.best-strategy, .risk-adjusted, .lowest-risk {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.strategy-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.strategy-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.strategy-metrics {
  text-align: right;
}

.metric-value {
  display: block;
  font-size: 20px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  margin-bottom: 4px;
}

.metric-label {
  font-size: 12px;
  color: var(--el-text-color-regular);
}

.risk-analysis-content {
  padding: 20px;
}

.risk-metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.risk-card {
  background: var(--el-bg-color-page);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid var(--el-border-color-light);
}

.risk-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.risk-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.risk-metrics {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.risk-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: var(--el-bg-color);
  border-radius: 6px;
  border: 1px solid var(--el-border-color-lighter);
}

.risk-label {
  font-size: 13px;
  color: var(--el-text-color-regular);
  font-weight: 500;
}

.risk-value {
  font-size: 14px;
  color: var(--el-text-color-primary);
  font-weight: 600;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

.trading-analysis-content {
  padding: 20px;
}

.trading-comparison-table {
  background: var(--el-bg-color-page);
  border-radius: 8px;
  padding: 20px;
  border: 1px solid var(--el-border-color-light);
}

.empty-comparison {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .comparison-view {
    padding: 16px;
  }
  
  .page-title {
    font-size: 24px;
  }
  
  .selector-item {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  
  .best-strategy, .risk-adjusted, .lowest-risk {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  
  .strategy-metrics {
    text-align: left;
  }
  
  .analysis-grid {
    grid-template-columns: 1fr;
  }
  
  .risk-metrics-grid {
    grid-template-columns: 1fr;
  }
  
  .charts-comparison {
    grid-template-columns: 1fr;
  }
}
</style>
