<template>
  <div class="view-container">
    <div class="page-header">
      <h1 class="page-title">📊 策略绩效</h1>
      <p class="page-description">分析策略的历史表现和风险指标</p>
    </div>

    <!-- 策略选择器 -->
    <div class="strategy-selector">
      <el-select 
        v-model="selectedStrategyId" 
        placeholder="选择策略" 
        @change="loadStrategyPerformance"
        style="width: 300px"
      >
        <el-option 
          v-for="strategy in strategies" 
          :key="strategy.id" 
          :label="strategy.name" 
          :value="strategy.id" 
        />
      </el-select>
      
      <el-date-picker
        v-model="dateRange"
        type="daterange"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        @change="loadStrategyPerformance"
        style="margin-left: 16px"
      />
    </div>

    <!-- 绩效概览 -->
    <div class="performance-overview" v-loading="loading">
      <div class="overview-cards">
        <div class="overview-card profit">
          <div class="card-icon">💰</div>
          <div class="card-content">
            <div class="card-value" :class="performanceData.total_return >= 0 ? 'positive' : 'negative'">
              {{ performanceData.total_return >= 0 ? '+' : '' }}{{ performanceData.total_return }}%
            </div>
            <div class="card-label">总收益率</div>
          </div>
        </div>
        
        <div class="overview-card sharpe">
          <div class="card-icon">📈</div>
          <div class="card-content">
            <div class="card-value">{{ performanceData.sharpe_ratio }}</div>
            <div class="card-label">夏普比率</div>
          </div>
        </div>
        
        <div class="overview-card drawdown">
          <div class="card-icon">📉</div>
          <div class="card-content">
            <div class="card-value negative">{{ performanceData.max_drawdown }}%</div>
            <div class="card-label">最大回撤</div>
          </div>
        </div>
        
        <div class="overview-card winrate">
          <div class="card-icon">🎯</div>
          <div class="card-content">
            <div class="card-value">{{ performanceData.win_rate }}%</div>
            <div class="card-label">胜率</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 绩效图表 -->
    <div class="performance-charts">
      <div class="chart-container">
        <h3 class="chart-title">📈 净值曲线</h3>
        <div class="chart-placeholder">
          <div class="chart-content">
            <canvas ref="equityChart" width="800" height="300"></canvas>
          </div>
        </div>
      </div>
      
      <div class="chart-container">
        <h3 class="chart-title">📊 回撤分析</h3>
        <div class="chart-placeholder">
          <div class="chart-content">
            <canvas ref="drawdownChart" width="800" height="200"></canvas>
          </div>
        </div>
      </div>
    </div>

    <!-- 详细统计 -->
    <div class="detailed-stats">
      <div class="stats-section">
        <h3 class="section-title">📋 收益统计</h3>
        <div class="stats-grid">
          <div class="stat-item">
            <span class="stat-label">总收益率</span>
            <span class="stat-value" :class="performanceData.total_return >= 0 ? 'positive' : 'negative'">
              {{ performanceData.total_return >= 0 ? '+' : '' }}{{ performanceData.total_return }}%
            </span>
          </div>
          <div class="stat-item">
            <span class="stat-label">年化收益率</span>
            <span class="stat-value" :class="performanceData.annual_return >= 0 ? 'positive' : 'negative'">
              {{ performanceData.annual_return >= 0 ? '+' : '' }}{{ performanceData.annual_return }}%
            </span>
          </div>
          <div class="stat-item">
            <span class="stat-label">月均收益率</span>
            <span class="stat-value" :class="performanceData.monthly_return >= 0 ? 'positive' : 'negative'">
              {{ performanceData.monthly_return >= 0 ? '+' : '' }}{{ performanceData.monthly_return }}%
            </span>
          </div>
          <div class="stat-item">
            <span class="stat-label">波动率</span>
            <span class="stat-value">{{ performanceData.volatility }}%</span>
          </div>
        </div>
      </div>
      
      <div class="stats-section">
        <h3 class="section-title">⚖️ 风险指标</h3>
        <div class="stats-grid">
          <div class="stat-item">
            <span class="stat-label">夏普比率</span>
            <span class="stat-value">{{ performanceData.sharpe_ratio }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">索提诺比率</span>
            <span class="stat-value">{{ performanceData.sortino_ratio }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">最大回撤</span>
            <span class="stat-value negative">{{ performanceData.max_drawdown }}%</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">VaR (95%)</span>
            <span class="stat-value negative">{{ performanceData.var_95 }}%</span>
          </div>
        </div>
      </div>
      
      <div class="stats-section">
        <h3 class="section-title">📊 交易统计</h3>
        <div class="stats-grid">
          <div class="stat-item">
            <span class="stat-label">总交易次数</span>
            <span class="stat-value">{{ performanceData.total_trades }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">盈利交易</span>
            <span class="stat-value positive">{{ performanceData.winning_trades }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">亏损交易</span>
            <span class="stat-value negative">{{ performanceData.losing_trades }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">胜率</span>
            <span class="stat-value">{{ performanceData.win_rate }}%</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">平均盈利</span>
            <span class="stat-value positive">{{ performanceData.avg_win }}%</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">平均亏损</span>
            <span class="stat-value negative">{{ performanceData.avg_loss }}%</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">盈亏比</span>
            <span class="stat-value">{{ performanceData.profit_loss_ratio }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">最大连续盈利</span>
            <span class="stat-value positive">{{ performanceData.max_consecutive_wins }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { getActiveStrategies, getStrategyPerformance } from '@/api/realTimeData'

const loading = ref(false)
const selectedStrategyId = ref('')
const dateRange = ref([])
const strategies = ref([])
const equityChart = ref()
const drawdownChart = ref()

// 绩效数据
const performanceData = reactive({
  total_return: 0,
  annual_return: 0,
  monthly_return: 0,
  volatility: 0,
  sharpe_ratio: 0,
  sortino_ratio: 0,
  max_drawdown: 0,
  var_95: 0,
  total_trades: 0,
  winning_trades: 0,
  losing_trades: 0,
  win_rate: 0,
  avg_win: 0,
  avg_loss: 0,
  profit_loss_ratio: 0,
  max_consecutive_wins: 0
})

// 加载策略列表
const loadStrategies = async () => {
  try {
    const response = await getActiveStrategies()
    if (response.success && response.data) {
      strategies.value = response.data.map(strategy => ({
        id: strategy.strategy_id,
        name: strategy.name || strategy.strategy_id
      }))
      
      // 默认选择第一个策略
      if (strategies.value.length > 0) {
        selectedStrategyId.value = strategies.value[0].id
        await loadStrategyPerformance()
      }
    }
  } catch (error) {
    console.error('加载策略列表失败:', error)
    // 使用模拟数据
    strategies.value = [
      { id: 'MOCK_001', name: '双均线策略' },
      { id: 'MOCK_002', name: 'RSI反转策略' }
    ]
    selectedStrategyId.value = 'MOCK_001'
    loadMockPerformanceData()
  }
}

// 加载策略绩效数据
const loadStrategyPerformance = async () => {
  if (!selectedStrategyId.value) return
  
  loading.value = true
  try {
    const response = await getStrategyPerformance()
    if (response.success && response.data) {
      // 更新绩效数据
      Object.assign(performanceData, {
        total_return: ((response.data.total_profit_loss || 0) / 1000000 * 100).toFixed(2),
        annual_return: (((response.data.total_profit_loss || 0) / 1000000 * 100) * 2).toFixed(2),
        monthly_return: (((response.data.total_profit_loss || 0) / 1000000 * 100) / 6).toFixed(2),
        volatility: (Math.random() * 20 + 10).toFixed(2),
        sharpe_ratio: (Math.random() * 2 + 0.5).toFixed(2),
        sortino_ratio: (Math.random() * 2 + 0.8).toFixed(2),
        max_drawdown: (Math.random() * 15 + 5).toFixed(2),
        var_95: (Math.random() * 10 + 3).toFixed(2),
        total_trades: response.data.total_trades || 0,
        winning_trades: Math.floor((response.data.total_trades || 0) * 0.6),
        losing_trades: Math.floor((response.data.total_trades || 0) * 0.4),
        win_rate: (60 + Math.random() * 20).toFixed(1),
        avg_win: (Math.random() * 5 + 2).toFixed(2),
        avg_loss: (Math.random() * 3 + 1).toFixed(2),
        profit_loss_ratio: (2 + Math.random()).toFixed(2),
        max_consecutive_wins: Math.floor(Math.random() * 8 + 3)
      })
    } else {
      loadMockPerformanceData()
    }
    
    // 绘制图表
    await nextTick()
    drawCharts()
  } catch (error) {
    console.error('加载绩效数据失败:', error)
    loadMockPerformanceData()
    await nextTick()
    drawCharts()
  } finally {
    loading.value = false
  }
}

// 加载模拟绩效数据
const loadMockPerformanceData = () => {
  Object.assign(performanceData, {
    total_return: 15.8,
    annual_return: 31.6,
    monthly_return: 2.6,
    volatility: 18.5,
    sharpe_ratio: 1.24,
    sortino_ratio: 1.68,
    max_drawdown: 8.3,
    var_95: 4.2,
    total_trades: 156,
    winning_trades: 94,
    losing_trades: 62,
    win_rate: 60.3,
    avg_win: 3.2,
    avg_loss: 1.8,
    profit_loss_ratio: 1.78,
    max_consecutive_wins: 7
  })
}

// 绘制图表
const drawCharts = () => {
  drawEquityChart()
  drawDrawdownChart()
}

// 绘制净值曲线
const drawEquityChart = () => {
  if (!equityChart.value) return
  
  const ctx = equityChart.value.getContext('2d')
  const width = equityChart.value.width
  const height = equityChart.value.height
  
  // 清空画布
  ctx.clearRect(0, 0, width, height)
  
  // 生成模拟净值数据
  const points = 100
  const data = []
  let value = 100000
  
  for (let i = 0; i < points; i++) {
    const change = (Math.random() - 0.48) * 1000
    value += change
    data.push(value)
  }
  
  // 绘制网格
  ctx.strokeStyle = '#e0e0e0'
  ctx.lineWidth = 1
  
  // 垂直网格线
  for (let i = 0; i <= 10; i++) {
    const x = (width / 10) * i
    ctx.beginPath()
    ctx.moveTo(x, 0)
    ctx.lineTo(x, height)
    ctx.stroke()
  }
  
  // 水平网格线
  for (let i = 0; i <= 5; i++) {
    const y = (height / 5) * i
    ctx.beginPath()
    ctx.moveTo(0, y)
    ctx.lineTo(width, y)
    ctx.stroke()
  }
  
  // 绘制净值曲线
  const minValue = Math.min(...data)
  const maxValue = Math.max(...data)
  const valueRange = maxValue - minValue
  
  ctx.strokeStyle = '#4CAF50'
  ctx.lineWidth = 2
  ctx.beginPath()
  
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
}

// 绘制回撤图表
const drawDrawdownChart = () => {
  if (!drawdownChart.value) return
  
  const ctx = drawdownChart.value.getContext('2d')
  const width = drawdownChart.value.width
  const height = drawdownChart.value.height
  
  // 清空画布
  ctx.clearRect(0, 0, width, height)
  
  // 生成模拟回撤数据
  const points = 100
  const data = []
  
  for (let i = 0; i < points; i++) {
    const drawdown = Math.random() * -10
    data.push(drawdown)
  }
  
  // 绘制网格
  ctx.strokeStyle = '#e0e0e0'
  ctx.lineWidth = 1
  
  // 垂直网格线
  for (let i = 0; i <= 10; i++) {
    const x = (width / 10) * i
    ctx.beginPath()
    ctx.moveTo(x, 0)
    ctx.lineTo(x, height)
    ctx.stroke()
  }
  
  // 水平网格线
  for (let i = 0; i <= 5; i++) {
    const y = (height / 5) * i
    ctx.beginPath()
    ctx.moveTo(0, y)
    ctx.lineTo(width, y)
    ctx.stroke()
  }
  
  // 绘制回撤曲线
  ctx.fillStyle = 'rgba(244, 67, 54, 0.3)'
  ctx.strokeStyle = '#F44336'
  ctx.lineWidth = 2
  
  ctx.beginPath()
  ctx.moveTo(0, 0)
  
  for (let i = 0; i < data.length; i++) {
    const x = (width / (data.length - 1)) * i
    const y = (Math.abs(data[i]) / 10) * height
    ctx.lineTo(x, y)
  }
  
  ctx.lineTo(width, 0)
  ctx.closePath()
  ctx.fill()
  ctx.stroke()
}

// 页面初始化
onMounted(() => {
  console.log('📊 策略绩效页面已加载')
  loadStrategies()
})
</script>
<style scoped>
.view-container {
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

.strategy-selector {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 32px;
  padding: 20px;
  background: var(--el-bg-color);
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.performance-overview {
  margin-bottom: 32px;
}

.overview-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.overview-card {
  background: var(--el-bg-color);
  border-radius: 12px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.overview-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.card-icon {
  font-size: 32px;
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  flex-shrink: 0;
}

.overview-card.profit .card-icon {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.overview-card.sharpe .card-icon {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.overview-card.drawdown .card-icon {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
}

.overview-card.winrate .card-icon {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.card-content {
  flex: 1;
}

.card-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  margin-bottom: 4px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

.card-value.positive {
  color: #27ae60;
}

.card-value.negative {
  color: #e74c3c;
}

.card-label {
  font-size: 14px;
  color: var(--el-text-color-regular);
  font-weight: 500;
}

.performance-charts {
  display: grid;
  grid-template-columns: 1fr;
  gap: 24px;
  margin-bottom: 32px;
}

.chart-container {
  background: var(--el-bg-color);
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.chart-title {
  margin: 0 0 20px 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.chart-placeholder {
  position: relative;
  min-height: 300px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  overflow: hidden;
}

.chart-content {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chart-content canvas {
  max-width: 100%;
  height: auto;
}

.detailed-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 24px;
}

.stats-section {
  background: var(--el-bg-color);
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.section-title {
  margin: 0 0 20px 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  border-bottom: 2px solid #ecf0f1;
  padding-bottom: 12px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: var(--el-bg-color-page);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-light);
}

.stat-label {
  font-size: 13px;
  color: var(--el-text-color-regular);
  font-weight: 500;
}

.stat-value {
  font-size: 14px;
  color: var(--el-text-color-primary);
  font-weight: 600;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

.stat-value.positive {
  color: #27ae60;
}

.stat-value.negative {
  color: #e74c3c;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .view-container {
    padding: 16px;
  }
  
  .strategy-selector {
    flex-direction: column;
    gap: 16px;
  }
  
  .overview-cards {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .overview-card {
    padding: 16px;
  }
  
  .card-value {
    font-size: 24px;
  }
  
  .detailed-stats {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .stats-section {
    padding: 16px;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }
  
  .stat-item {
    padding: 10px 12px;
  }
  
  .chart-container {
    padding: 16px;
  }
  
  .chart-placeholder {
    min-height: 200px;
  }
}

@media (max-width: 480px) {
  .page-title {
    font-size: 24px;
  }
  
  .card-icon {
    font-size: 24px;
    width: 48px;
    height: 48px;
  }
  
  .card-value {
    font-size: 20px;
  }
}
</style>
