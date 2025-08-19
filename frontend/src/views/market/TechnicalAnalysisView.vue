<template>
  <div class="technical-analysis">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">技术分析</h1>
        <p class="page-description">基于tqsdk的实时技术指标分析</p>
      </div>
      <div class="header-right">
        <el-select v-model="selectedSymbol" placeholder="选择合约" @change="loadTechnicalData">
          <el-option
            v-for="contract in contracts"
            :key="contract.symbol"
            :label="`${contract.name} (${contract.symbol})`"
            :value="contract.symbol"
          />
        </el-select>
        <el-select v-model="selectedPeriod" placeholder="选择周期" @change="loadTechnicalData">
          <el-option label="1分钟" value="1m" />
          <el-option label="5分钟" value="5m" />
          <el-option label="15分钟" value="15m" />
          <el-option label="1小时" value="1h" />
          <el-option label="1天" value="1d" />
        </el-select>
        <el-button @click="loadTechnicalData" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 主要内容 -->
    <div v-if="selectedSymbol" class="analysis-content">
      <!-- 基础信息卡片 -->
      <el-row :gutter="20" class="info-cards">
        <el-col :span="6">
          <el-card class="info-card">
            <div class="info-item">
              <div class="info-label">当前价格</div>
              <div class="info-value price">
                {{ currentQuote?.last_price?.toFixed(2) || '--' }}
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="info-card">
            <div class="info-item">
              <div class="info-label">涨跌幅</div>
              <div class="info-value" :class="getChangeClass(currentQuote?.change_percent)">
                {{ formatPercent(currentQuote?.change_percent) }}
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="info-card">
            <div class="info-item">
              <div class="info-label">成交量</div>
              <div class="info-value">
                {{ formatVolume(currentQuote?.volume) }}
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="info-card">
            <div class="info-item">
              <div class="info-label">持仓量</div>
              <div class="info-value">
                {{ formatVolume(currentQuote?.open_interest) }}
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 技术指标面板 -->
      <el-row :gutter="20">
        <!-- 左侧：技术指标数值 -->
        <el-col :span="8">
          <el-card title="技术指标">
            <template #header>
              <div class="card-header">
                <span>技术指标</span>
                <el-tag v-if="indicators.timestamp" size="small" type="info">
                  {{ formatTime(indicators.timestamp) }}
                </el-tag>
              </div>
            </template>

            <div class="indicators-list">
              <!-- 移动平均线 -->
              <div class="indicator-group">
                <h4>移动平均线</h4>
                <div class="indicator-items">
                  <div class="indicator-item">
                    <span class="indicator-name">MA5</span>
                    <span class="indicator-value">{{ formatPrice(indicators.latest_values?.ma5) }}</span>
                  </div>
                  <div class="indicator-item">
                    <span class="indicator-name">MA10</span>
                    <span class="indicator-value">{{ formatPrice(indicators.latest_values?.ma10) }}</span>
                  </div>
                  <div class="indicator-item">
                    <span class="indicator-name">MA20</span>
                    <span class="indicator-value">{{ formatPrice(indicators.latest_values?.ma20) }}</span>
                  </div>
                </div>
              </div>

              <!-- RSI -->
              <div class="indicator-group">
                <h4>相对强弱指标</h4>
                <div class="indicator-items">
                  <div class="indicator-item">
                    <span class="indicator-name">RSI</span>
                    <span class="indicator-value">{{ formatRSI(indicators.latest_values?.rsi) }}</span>
                    <el-tag 
                      v-if="indicators.signals?.rsi" 
                      :type="getSignalType(indicators.signals.rsi)" 
                      size="small"
                    >
                      {{ indicators.signals.rsi }}
                    </el-tag>
                  </div>
                </div>
              </div>

              <!-- MACD -->
              <div class="indicator-group">
                <h4>MACD</h4>
                <div class="indicator-items">
                  <div class="indicator-item">
                    <span class="indicator-name">MACD</span>
                    <span class="indicator-value">{{ formatPrice(indicators.latest_values?.macd) }}</span>
                  </div>
                  <div class="indicator-item">
                    <span class="indicator-name">Signal</span>
                    <span class="indicator-value">{{ formatPrice(indicators.latest_values?.macd_signal) }}</span>
                  </div>
                  <div class="indicator-item">
                    <span class="indicator-name">Histogram</span>
                    <span class="indicator-value">{{ formatPrice(indicators.latest_values?.macd_histogram) }}</span>
                    <el-tag 
                      v-if="indicators.signals?.macd" 
                      :type="getSignalType(indicators.signals.macd)" 
                      size="small"
                    >
                      {{ indicators.signals.macd }}
                    </el-tag>
                  </div>
                </div>
              </div>

              <!-- 布林带 -->
              <div class="indicator-group">
                <h4>布林带</h4>
                <div class="indicator-items">
                  <div class="indicator-item">
                    <span class="indicator-name">上轨</span>
                    <span class="indicator-value">{{ formatPrice(indicators.latest_values?.bb_upper) }}</span>
                  </div>
                  <div class="indicator-item">
                    <span class="indicator-name">中轨</span>
                    <span class="indicator-value">{{ formatPrice(indicators.latest_values?.bb_middle) }}</span>
                  </div>
                  <div class="indicator-item">
                    <span class="indicator-name">下轨</span>
                    <span class="indicator-value">{{ formatPrice(indicators.latest_values?.bb_lower) }}</span>
                  </div>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>

        <!-- 右侧：交易信号和多时间框架分析 -->
        <el-col :span="16">
          <el-card>
            <template #header>
              <el-tabs v-model="rightTabActive">
                <el-tab-pane label="交易信号" name="signals" />
                <el-tab-pane label="多时间框架" name="timeframes" />
                <el-tab-pane label="K线数据" name="klines" />
              </el-tabs>
            </template>

            <!-- 交易信号 -->
            <div v-if="rightTabActive === 'signals'" class="signals-panel">
              <div v-if="tradingSignals.length === 0" class="empty-state">
                <el-empty description="暂无交易信号" />
              </div>
              <div v-else class="signals-list">
                <div v-for="signal in tradingSignals" :key="signal.timestamp" class="signal-item">
                  <div class="signal-header">
                    <el-tag :type="getSignalType(signal.signal)" size="large">
                      {{ signal.signal }}
                    </el-tag>
                    <span class="signal-time">{{ formatTime(signal.timestamp) }}</span>
                  </div>
                  <div class="signal-details">
                    <div class="signal-info">
                      <span>指标: {{ signal.indicator }}</span>
                      <span>置信度: {{ (signal.confidence * 100).toFixed(1) }}%</span>
                      <span>价格: {{ signal.price }}</span>
                    </div>
                    <div class="signal-description">{{ signal.description }}</div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 多时间框架分析 -->
            <div v-if="rightTabActive === 'timeframes'" class="timeframes-panel">
              <div v-if="!multiTimeframe.symbol" class="empty-state">
                <el-empty description="暂无多时间框架数据" />
              </div>
              <div v-else class="timeframes-grid">
                <div v-for="(analysis, period) in multiTimeframe.analysis" :key="period" class="timeframe-item">
                  <div class="timeframe-header">
                    <h4>{{ getPeriodName(period) }}</h4>
                    <el-tag :type="getTrendType(analysis.trend)" size="small">
                      {{ analysis.trend }}
                    </el-tag>
                  </div>
                  <div class="timeframe-indicators">
                    <div class="tf-indicator">
                      <span>RSI: {{ formatRSI(analysis.rsi) }}</span>
                      <el-tag v-if="analysis.rsi_signal" :type="getSignalType(analysis.rsi_signal)" size="small">
                        {{ analysis.rsi_signal }}
                      </el-tag>
                    </div>
                    <div class="tf-indicator">
                      <span>MACD: {{ analysis.macd_signal || '中性' }}</span>
                    </div>
                    <div class="tf-indicator">
                      <span>MA趋势: {{ analysis.ma_trend || '中性' }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- K线数据 -->
            <div v-if="rightTabActive === 'klines'" class="klines-panel">
              <div v-if="klineData.length === 0" class="empty-state">
                <el-empty description="暂无K线数据" />
              </div>
              <div v-else class="klines-table">
                <el-table :data="klineData.slice(0, 20)" size="small" height="400">
                  <el-table-column prop="datetime" label="时间" width="150">
                    <template #default="{ row }">
                      {{ formatTime(row.datetime) }}
                    </template>
                  </el-table-column>
                  <el-table-column prop="open" label="开盘" width="80">
                    <template #default="{ row }">
                      {{ row.open.toFixed(2) }}
                    </template>
                  </el-table-column>
                  <el-table-column prop="high" label="最高" width="80">
                    <template #default="{ row }">
                      {{ row.high.toFixed(2) }}
                    </template>
                  </el-table-column>
                  <el-table-column prop="low" label="最低" width="80">
                    <template #default="{ row }">
                      {{ row.low.toFixed(2) }}
                    </template>
                  </el-table-column>
                  <el-table-column prop="close" label="收盘" width="80">
                    <template #default="{ row }">
                      <span :class="getChangeClass(row.close - row.open)">
                        {{ row.close.toFixed(2) }}
                      </span>
                    </template>
                  </el-table-column>
                  <el-table-column prop="volume" label="成交量" width="100">
                    <template #default="{ row }">
                      {{ formatVolume(row.volume) }}
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 未选择合约时的提示 -->
    <div v-else class="empty-state-main">
      <el-empty description="请选择一个合约开始技术分析" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import {
  getContractList,
  getRealTimeQuote,
  getTechnicalIndicators,
  getTradingSignals,
  getMultiTimeframeAnalysis,
  getKlineData,
  type ContractInfo,
  type RealTimeQuote,
  type TechnicalIndicators
} from '@/api/realTimeData'

// 响应式数据
const loading = ref(false)
const selectedSymbol = ref('')
const selectedPeriod = ref('1m')
const rightTabActive = ref('signals')

// 数据
const contracts = ref<ContractInfo[]>([])
const currentQuote = ref<RealTimeQuote | null>(null)
const indicators = ref<TechnicalIndicators>({
  symbol: '',
  period: '',
  latest_values: {},
  signals: {},
  timestamp: ''
})
const tradingSignals = ref([])
const multiTimeframe = ref({ symbol: '', analysis: {} })
const klineData = ref([])

// 定时器
let refreshTimer: NodeJS.Timeout | null = null

// 加载合约列表
const loadContracts = async () => {
  try {
    const response = await getContractList()
    if (response.success && response.data) {
      contracts.value = response.data.slice(0, 20) // 取前20个合约
      if (contracts.value.length > 0 && !selectedSymbol.value) {
        selectedSymbol.value = contracts.value[0].symbol
        await loadTechnicalData()
      }
    }
  } catch (error) {
    console.error('加载合约列表失败:', error)
    ElMessage.error('加载合约列表失败')
  }
}

// 加载技术分析数据
const loadTechnicalData = async () => {
  if (!selectedSymbol.value) return
  
  loading.value = true
  try {
    // 并行加载多个数据
    const [quoteRes, indicatorsRes, signalsRes, multiTimeRes, klineRes] = await Promise.allSettled([
      getRealTimeQuote(selectedSymbol.value),
      getTechnicalIndicators(selectedSymbol.value, selectedPeriod.value),
      getTradingSignals(selectedSymbol.value, selectedPeriod.value),
      getMultiTimeframeAnalysis(selectedSymbol.value),
      getKlineData(selectedSymbol.value, selectedPeriod.value, 50)
    ])

    // 处理实时行情
    if (quoteRes.status === 'fulfilled' && quoteRes.value.success) {
      currentQuote.value = quoteRes.value.data
    }

    // 处理技术指标
    if (indicatorsRes.status === 'fulfilled' && indicatorsRes.value.success) {
      indicators.value = indicatorsRes.value.data
    }

    // 处理交易信号
    if (signalsRes.status === 'fulfilled' && signalsRes.value.success) {
      tradingSignals.value = signalsRes.value.data.signals || []
    }

    // 处理多时间框架
    if (multiTimeRes.status === 'fulfilled' && multiTimeRes.value.success) {
      multiTimeframe.value = multiTimeRes.value.data
    }

    // 处理K线数据
    if (klineRes.status === 'fulfilled' && klineRes.value.success) {
      klineData.value = klineRes.value.data.data || []
    }

  } catch (error) {
    console.error('加载技术分析数据失败:', error)
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

// 格式化函数
const formatPrice = (price: number | undefined) => {
  return price ? price.toFixed(2) : '--'
}

const formatRSI = (rsi: number | undefined) => {
  return rsi ? rsi.toFixed(1) : '--'
}

const formatPercent = (percent: number | undefined) => {
  if (percent === undefined) return '--'
  return `${percent >= 0 ? '+' : ''}${percent.toFixed(2)}%`
}

const formatVolume = (volume: number | undefined) => {
  if (!volume) return '--'
  if (volume >= 10000) {
    return `${(volume / 10000).toFixed(1)}万`
  }
  return volume.toString()
}

const formatTime = (timestamp: string) => {
  return new Date(timestamp).toLocaleString()
}

const getPeriodName = (period: string) => {
  const names: Record<string, string> = {
    '1m': '1分钟',
    '5m': '5分钟',
    '15m': '15分钟',
    '1h': '1小时',
    '1d': '1天'
  }
  return names[period] || period
}

// 样式类函数
const getChangeClass = (change: number | undefined) => {
  if (!change) return ''
  return change >= 0 ? 'positive' : 'negative'
}

const getSignalType = (signal: string) => {
  switch (signal) {
    case '买入':
    case 'BUY':
    case '看涨':
      return 'success'
    case '卖出':
    case 'SELL':
    case '看跌':
      return 'danger'
    case '中性':
    case 'HOLD':
      return 'info'
    default:
      return 'warning'
  }
}

const getTrendType = (trend: string) => {
  switch (trend) {
    case '上涨':
    case '看涨':
      return 'success'
    case '下跌':
    case '看跌':
      return 'danger'
    case '震荡':
    case '中性':
      return 'info'
    default:
      return 'warning'
  }
}

// 启动定时刷新
const startAutoRefresh = () => {
  refreshTimer = setInterval(() => {
    if (selectedSymbol.value) {
      loadTechnicalData()
    }
  }, 30000) // 30秒刷新一次
}

// 停止定时刷新
const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

// 组件挂载
onMounted(() => {
  loadContracts()
  startAutoRefresh()
})

// 组件卸载
onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style scoped>
.technical-analysis {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #e4e7ed;
}

.header-left {
  flex: 1;
}

.page-title {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.page-description {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.header-right {
  display: flex;
  gap: 12px;
}

.info-cards {
  margin-bottom: 20px;
}

.info-card {
  text-align: center;
}

.info-item {
  padding: 10px;
}

.info-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.info-value {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.info-value.price {
  font-size: 24px;
}

.positive {
  color: #67c23a;
}

.negative {
  color: #f56c6c;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.indicators-list {
  max-height: 500px;
  overflow-y: auto;
}

.indicator-group {
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #f0f0f0;
}

.indicator-group h4 {
  margin: 0 0 10px 0;
  font-size: 14px;
  color: #606266;
}

.indicator-items {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.indicator-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 5px 0;
}

.indicator-name {
  font-size: 13px;
  color: #909399;
  min-width: 60px;
}

.indicator-value {
  font-weight: 600;
  color: #303133;
}

.signals-list {
  max-height: 400px;
  overflow-y: auto;
}

.signal-item {
  padding: 15px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  margin-bottom: 10px;
}

.signal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.signal-time {
  font-size: 12px;
  color: #909399;
}

.signal-details {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.signal-info {
  display: flex;
  gap: 15px;
  font-size: 12px;
  color: #606266;
}

.signal-description {
  font-size: 13px;
  color: #909399;
  font-style: italic;
}

.timeframes-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
}

.timeframe-item {
  padding: 15px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
}

.timeframe-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.timeframe-header h4 {
  margin: 0;
  font-size: 14px;
}

.timeframe-indicators {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.tf-indicator {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #606266;
}

.klines-table {
  height: 400px;
}

.empty-state {
  text-align: center;
  padding: 40px;
}

.empty-state-main {
  text-align: center;
  padding: 100px;
}
</style>