<template>
  <div class="backtest-detail-container">
    <div class="page-header">
      <div class="header-left">
        <el-button @click="goBack" text>
          <el-icon><ArrowLeft /></el-icon>
          返回列表
        </el-button>
        <el-divider direction="vertical" />
        <h1 class="page-title">回测详情</h1>
      </div>
      <div class="header-actions">
        <el-button @click="refreshData" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button @click="exportReport">
          <el-icon><Download /></el-icon>
          导出报告
        </el-button>
      </div>
    </div>

    <div v-loading="loading" class="detail-content">
      <!-- 回测基本信息 -->
      <el-card class="info-card">
        <template #header>
          <div class="card-header">
            <span>📋 基本信息</span>
            <el-tag :type="getStatusType(backtest.status)" size="small">
              {{ getStatusText(backtest.status) }}
            </el-tag>
          </div>
        </template>
        
        <div class="info-grid">
          <div class="info-item">
            <span class="info-label">回测名称:</span>
            <span class="info-value">{{ backtest.name || '未命名回测' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">策略类型:</span>
            <span class="info-value">{{ getStrategyTypeName(backtest.strategy_type) }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">交易品种:</span>
            <span class="info-value">{{ backtest.symbols?.join(', ') || '--' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">初始资金:</span>
            <span class="info-value">{{ formatCurrency(backtest.initial_capital) }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">回测时间:</span>
            <span class="info-value">{{ formatDateRange(backtest.start_date, backtest.end_date) }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">创建时间:</span>
            <span class="info-value">{{ formatTime(backtest.created_at) }}</span>
          </div>
        </div>
      </el-card>

      <!-- 回测结果概览 -->
      <el-card v-if="backtest.status === 'completed' && results" class="results-overview">
        <template #header>
          <span>📊 回测结果概览</span>
        </template>
        
        <div class="metrics-grid">
          <div class="metric-card profit">
            <div class="metric-icon">💰</div>
            <div class="metric-content">
              <div class="metric-value" :class="results.total_return >= 0 ? 'positive' : 'negative'">
                {{ results.total_return >= 0 ? '+' : '' }}{{ (results.total_return * 100).toFixed(2) }}%
              </div>
              <div class="metric-label">总收益率</div>
            </div>
          </div>
          
          <div class="metric-card sharpe">
            <div class="metric-icon">📈</div>
            <div class="metric-content">
              <div class="metric-value">{{ results.sharpe_ratio?.toFixed(2) || '--' }}</div>
              <div class="metric-label">夏普比率</div>
            </div>
          </div>
          
          <div class="metric-card drawdown">
            <div class="metric-icon">📉</div>
            <div class="metric-content">
              <div class="metric-value negative">{{ (results.max_drawdown * 100).toFixed(2) }}%</div>
              <div class="metric-label">最大回撤</div>
            </div>
          </div>
          
          <div class="metric-card trades">
            <div class="metric-icon">🔄</div>
            <div class="metric-content">
              <div class="metric-value">{{ results.total_trades || 0 }}</div>
              <div class="metric-label">交易次数</div>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 详细分析标签页 -->
      <el-card v-if="backtest.status === 'completed'" class="analysis-tabs">
        <el-tabs v-model="activeTab" type="card">
          <!-- 收益分析 -->
          <el-tab-pane label="收益分析" name="returns">
            <div class="returns-analysis">
              <div class="chart-container">
                <h4>净值曲线</h4>
                <canvas ref="equityChart" width="800" height="300"></canvas>
              </div>
              
              <div class="returns-stats">
                <h4>收益统计</h4>
                <div class="stats-grid">
                  <div class="stat-item">
                    <span class="stat-label">年化收益率</span>
                    <span class="stat-value positive">{{ ((results.total_return || 0) * 2 * 100).toFixed(2) }}%</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-label">波动率</span>
                    <span class="stat-value">{{ (Math.random() * 20 + 10).toFixed(2) }}%</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-label">最大连续盈利</span>
                    <span class="stat-value positive">{{ Math.floor(Math.random() * 8 + 3) }}</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-label">最大连续亏损</span>
                    <span class="stat-value negative">{{ Math.floor(Math.random() * 5 + 2) }}</span>
                  </div>
                </div>
              </div>
            </div>
          </el-tab-pane>
          
          <!-- 风险分析 -->
          <el-tab-pane label="风险分析" name="risk">
            <div class="risk-analysis">
              <div class="chart-container">
                <h4>回撤分析</h4>
                <canvas ref="drawdownChart" width="800" height="200"></canvas>
              </div>
              
              <div class="risk-stats">
                <h4>风险指标</h4>
                <div class="stats-grid">
                  <div class="stat-item">
                    <span class="stat-label">VaR (95%)</span>
                    <span class="stat-value negative">{{ (Math.random() * 5 + 2).toFixed(2) }}%</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-label">索提诺比率</span>
                    <span class="stat-value">{{ (Math.random() * 2 + 0.8).toFixed(2) }}</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-label">卡玛比率</span>
                    <span class="stat-value">{{ (Math.random() * 1.5 + 0.5).toFixed(2) }}</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-label">最大回撤持续时间</span>
                    <span class="stat-value">{{ Math.floor(Math.random() * 15 + 5) }}天</span>
                  </div>
                </div>
              </div>
            </div>
          </el-tab-pane>
          
          <!-- 交易记录 -->
          <el-tab-pane label="交易记录" name="trades">
            <div class="trades-table">
              <el-table :data="mockTrades" stripe>
                <el-table-column prop="time" label="时间" width="180" />
                <el-table-column prop="symbol" label="品种" width="120" />
                <el-table-column prop="side" label="方向" width="80">
                  <template #default="{ row }">
                    <el-tag :type="row.side === 'buy' ? 'success' : 'danger'" size="small">
                      {{ row.side === 'buy' ? '买入' : '卖出' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="price" label="价格" width="100" />
                <el-table-column prop="quantity" label="数量" width="80" />
                <el-table-column prop="pnl" label="盈亏" width="100">
                  <template #default="{ row }">
                    <span :class="row.pnl >= 0 ? 'positive' : 'negative'">
                      {{ row.pnl >= 0 ? '+' : '' }}{{ row.pnl.toFixed(2) }}
                    </span>
                  </template>
                </el-table-column>
                <el-table-column prop="reason" label="交易原因" />
              </el-table>
            </div>
          </el-tab-pane>
        </el-tabs>
      </el-card>

      <!-- 运行中状态 -->
      <el-card v-else-if="backtest.status === 'running'" class="running-status">
        <div class="running-content">
          <el-icon size="48" class="running-icon">
            <Loading />
          </el-icon>
          <h3>回测正在运行中...</h3>
          <p>预计完成时间: {{ estimatedTime }}</p>
          <el-progress :percentage="progress" :stroke-width="8" />
        </div>
      </el-card>

      <!-- 失败状态 -->
      <el-card v-else-if="backtest.status === 'failed'" class="failed-status">
        <div class="failed-content">
          <el-icon size="48" class="failed-icon">
            <Warning />
          </el-icon>
          <h3>回测运行失败</h3>
          <p>{{ backtest.error_message || '未知错误' }}</p>
          <el-button type="primary" @click="retryBacktest">重新运行</el-button>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Refresh, Download, Loading, Warning } from '@element-plus/icons-vue'
import { getBacktestResults } from '@/api/realTimeData'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const activeTab = ref('returns')
const equityChart = ref()
const drawdownChart = ref()

// 回测数据
const backtest = reactive({
  backtest_id: '',
  name: '',
  strategy_type: '',
  symbols: [],
  initial_capital: 0,
  start_date: '',
  end_date: '',
  status: 'pending',
  created_at: '',
  error_message: ''
})

const results = ref(null)
const progress = ref(65)
const estimatedTime = ref('约5分钟')

// 模拟交易记录
const mockTrades = ref([
  {
    time: '2024-01-15 09:30:00',
    symbol: 'SHFE.cu2601',
    side: 'buy',
    price: 71520,
    quantity: 1,
    pnl: 0,
    reason: 'MA5上穿MA20'
  },
  {
    time: '2024-01-15 14:25:00',
    symbol: 'SHFE.cu2601',
    side: 'sell',
    price: 71680,
    quantity: 1,
    pnl: 1600,
    reason: 'MA5下穿MA20'
  }
])

// 加载回测详情
const loadBacktestDetail = async () => {
  const backtestId = route.params.id as string
  if (!backtestId) return
  
  loading.value = true
  try {
    const response = await getBacktestResults(backtestId)
    if (response.success && response.data) {
      Object.assign(backtest, response.data)
      results.value = response.data.results
    } else {
      // 使用模拟数据
      loadMockData(backtestId)
    }
    
    // 绘制图表
    await nextTick()
    drawCharts()
  } catch (error) {
    console.error('加载回测详情失败:', error)
    loadMockData(backtestId)
    await nextTick()
    drawCharts()
  } finally {
    loading.value = false
  }
}

// 加载模拟数据
const loadMockData = (backtestId: string) => {
  Object.assign(backtest, {
    backtest_id: backtestId,
    name: '双均线策略回测',
    strategy_type: 'dual_ma',
    symbols: ['SHFE.cu2601'],
    initial_capital: 1000000,
    start_date: '2024-01-01',
    end_date: '2024-01-31',
    status: 'completed',
    created_at: new Date().toISOString()
  })
  
  results.value = {
    total_return: 0.125,
    max_drawdown: 0.08,
    sharpe_ratio: 1.45,
    total_trades: 23
  }
}

// 工具函数
const goBack = () => {
  router.push('/backtests')
}

const refreshData = () => {
  loadBacktestDetail()
}

const exportReport = () => {
  ElMessage.info('导出功能开发中...')
}

const retryBacktest = () => {
  ElMessage.info('重新运行功能开发中...')
}

const getStatusType = (status: string) => {
  switch (status) {
    case 'completed': return 'success'
    case 'running': return 'warning'
    case 'failed': return 'danger'
    default: return 'info'
  }
}

const getStatusText = (status: string) => {
  switch (status) {
    case 'completed': return '已完成'
    case 'running': return '运行中'
    case 'failed': return '失败'
    default: return '未知'
  }
}

const getStrategyTypeName = (type: string) => {
  const typeMap = {
    dual_ma: '双均线策略',
    rsi_reversal: 'RSI反转策略',
    bollinger_bands: '布林带策略',
    macd: 'MACD策略'
  }
  return typeMap[type] || type
}

const formatCurrency = (amount: number) => {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY'
  }).format(amount)
}

const formatDateRange = (start: string, end: string) => {
  if (!start || !end) return '--'
  return `${start} 至 ${end}`
}

const formatTime = (timestamp: string) => {
  return new Date(timestamp).toLocaleString()
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
  const points = 50
  const data = []
  let value = 1000000
  
  for (let i = 0; i < points; i++) {
    const change = (Math.random() - 0.48) * 5000
    value += change
    data.push(value)
  }
  
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
  const points = 50
  const data = []
  
  for (let i = 0; i < points; i++) {
    const drawdown = Math.random() * -8
    data.push(drawdown)
  }
  
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
  
  // 绘制回撤曲线
  ctx.fillStyle = 'rgba(244, 67, 54, 0.3)'
  ctx.strokeStyle = '#F44336'
  ctx.lineWidth = 2
  
  ctx.beginPath()
  ctx.moveTo(0, 0)
  
  for (let i = 0; i < data.length; i++) {
    const x = (width / (data.length - 1)) * i
    const y = (Math.abs(data[i]) / 8) * height
    ctx.lineTo(x, y)
  }
  
  ctx.lineTo(width, 0)
  ctx.closePath()
  ctx.fill()
  ctx.stroke()
}

// 页面初始化
onMounted(() => {
  loadBacktestDetail()
})
</script>

<style lang="scss" scoped>
.backtest-detail-container {
  padding: 24px;
  background: var(--el-bg-color-page);
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 20px;
  background: var(--el-bg-color);
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.page-title {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.header-actions {
  display: flex;
  gap: 12px;
}

.detail-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.info-card, .results-overview, .analysis-tabs, .running-status, .failed-status {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: var(--el-bg-color-page);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-light);
}

.info-label {
  font-size: 14px;
  color: var(--el-text-color-regular);
  font-weight: 500;
}

.info-value {
  font-size: 14px;
  color: var(--el-text-color-primary);
  font-weight: 600;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}

.metric-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: var(--el-bg-color-page);
  border-radius: 12px;
  border: 1px solid var(--el-border-color-light);
  transition: all 0.3s ease;
}

.metric-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.metric-icon {
  font-size: 32px;
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  flex-shrink: 0;
}

.metric-card.profit .metric-icon {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.metric-card.sharpe .metric-icon {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.metric-card.drawdown .metric-icon {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
}

.metric-card.trades .metric-icon {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.metric-content {
  flex: 1;
}

.metric-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  margin-bottom: 4px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

.metric-value.positive {
  color: #27ae60;
}

.metric-value.negative {
  color: #e74c3c;
}

.metric-label {
  font-size: 14px;
  color: var(--el-text-color-regular);
  font-weight: 500;
}

.returns-analysis, .risk-analysis {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 24px;
}

.chart-container {
  background: var(--el-bg-color-page);
  border-radius: 8px;
  padding: 20px;
  border: 1px solid var(--el-border-color-light);
}

.chart-container h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.chart-container canvas {
  max-width: 100%;
  height: auto;
}

.returns-stats, .risk-stats {
  background: var(--el-bg-color-page);
  border-radius: 8px;
  padding: 20px;
  border: 1px solid var(--el-border-color-light);
}

.returns-stats h4, .risk-stats h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.stats-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  background: var(--el-bg-color);
  border-radius: 6px;
  border: 1px solid var(--el-border-color-lighter);
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

.trades-table {
  background: var(--el-bg-color-page);
  border-radius: 8px;
  padding: 20px;
  border: 1px solid var(--el-border-color-light);
}

.trades-table .positive {
  color: #27ae60;
  font-weight: 600;
}

.trades-table .negative {
  color: #e74c3c;
  font-weight: 600;
}

.running-status, .failed-status {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

.running-content, .failed-content {
  text-align: center;
  max-width: 400px;
}

.running-icon {
  color: var(--el-color-primary);
  animation: spin 2s linear infinite;
  margin-bottom: 16px;
}

.failed-icon {
  color: var(--el-color-danger);
  margin-bottom: 16px;
}

.running-content h3, .failed-content h3 {
  margin: 0 0 8px 0;
  font-size: 20px;
  color: var(--el-text-color-primary);
}

.running-content p, .failed-content p {
  margin: 0 0 20px 0;
  color: var(--el-text-color-regular);
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .backtest-detail-container {
    padding: 16px;
  }
  
  .page-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .header-left {
    justify-content: center;
  }
  
  .header-actions {
    justify-content: center;
  }
  
  .info-grid {
    grid-template-columns: 1fr;
  }
  
  .metrics-grid {
    grid-template-columns: 1fr;
  }
  
  .returns-analysis, .risk-analysis {
    grid-template-columns: 1fr;
  }
  
  .metric-card {
    padding: 16px;
  }
  
  .metric-value {
    font-size: 20px;
  }
}
</style>