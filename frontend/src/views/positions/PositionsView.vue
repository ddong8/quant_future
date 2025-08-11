<template>
  <div class="simple-positions-view">
    <div class="page-header">
      <h1 class="page-title">📊 持仓管理</h1>
      <p class="page-description">管理和监控您的交易持仓</p>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon">📈</div>
        <div class="stat-content">
          <div class="stat-value">{{ positionStats.totalPositions }}</div>
          <div class="stat-label">总持仓数</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon">💰</div>
        <div class="stat-content">
          <div class="stat-value positive">+¥{{ formatNumber(positionStats.totalPnl) }}</div>
          <div class="stat-label">总盈亏</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon">💎</div>
        <div class="stat-content">
          <div class="stat-value">¥{{ formatNumber(positionStats.totalValue) }}</div>
          <div class="stat-label">持仓价值</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon">⚖️</div>
        <div class="stat-content">
          <div class="stat-value">{{ positionStats.riskLevel }}</div>
          <div class="stat-label">风险等级</div>
        </div>
      </div>
    </div>

    <!-- 操作按钮 -->
    <div class="actions-card">
      <h3>🚀 快速操作</h3>
      <div class="actions">
        <button class="action-btn primary" @click="refreshPositions">
          🔄 刷新持仓
        </button>
        <button class="action-btn" @click="closeAllPositions">
          🔒 全部平仓
        </button>
        <button class="action-btn" @click="exportPositions">
          📤 导出持仓
        </button>
        <button class="action-btn" @click="showRiskAnalysis = !showRiskAnalysis">
          📊 风险分析
        </button>
      </div>
    </div>

    <!-- 风险分析 -->
    <div v-if="showRiskAnalysis" class="risk-card">
      <h3>📊 风险分析</h3>
      <div class="risk-metrics">
        <div class="risk-item">
          <span class="risk-label">总风险敞口:</span>
          <span class="risk-value">¥{{ formatNumber(riskMetrics.totalExposure) }}</span>
        </div>
        <div class="risk-item">
          <span class="risk-label">最大回撤:</span>
          <span class="risk-value negative">{{ riskMetrics.maxDrawdown }}%</span>
        </div>
        <div class="risk-item">
          <span class="risk-label">夏普比率:</span>
          <span class="risk-value">{{ riskMetrics.sharpeRatio }}</span>
        </div>
        <div class="risk-item">
          <span class="risk-label">胜率:</span>
          <span class="risk-value">{{ riskMetrics.winRate }}%</span>
        </div>
      </div>
    </div>

    <!-- 持仓列表 -->
    <div class="positions-card">
      <h3>📊 持仓列表</h3>
      <div class="positions-table">
        <div class="table-header">
          <div class="header-cell">交易品种</div>
          <div class="header-cell">方向</div>
          <div class="header-cell">数量</div>
          <div class="header-cell">开仓价</div>
          <div class="header-cell">当前价</div>
          <div class="header-cell">盈亏</div>
          <div class="header-cell">盈亏率</div>
          <div class="header-cell">持仓时间</div>
          <div class="header-cell">操作</div>
        </div>
        
        <div v-for="position in positions" :key="position.id" class="table-row">
          <div class="table-cell">
            <div class="symbol-info">
              <span class="symbol">{{ position.symbol }}</span>
              <span class="symbol-desc">{{ getSymbolDesc(position.symbol) }}</span>
            </div>
          </div>
          <div class="table-cell" :class="position.side">
            {{ position.side === 'long' ? '🟢 多头' : '🔴 空头' }}
          </div>
          <div class="table-cell">{{ position.quantity }}</div>
          <div class="table-cell">¥{{ formatNumber(position.entry_price) }}</div>
          <div class="table-cell">¥{{ formatNumber(position.current_price) }}</div>
          <div class="table-cell" :class="position.pnl >= 0 ? 'positive' : 'negative'">
            {{ position.pnl >= 0 ? '+' : '' }}¥{{ formatNumber(position.pnl) }}
          </div>
          <div class="table-cell" :class="position.pnl_percent >= 0 ? 'positive' : 'negative'">
            {{ position.pnl_percent >= 0 ? '+' : '' }}{{ position.pnl_percent.toFixed(2) }}%
          </div>
          <div class="table-cell">{{ formatDuration(position.hold_time) }}</div>
          <div class="table-cell">
            <button class="btn-small primary" @click="adjustPosition(position.id)">
              调整
            </button>
            <button class="btn-small danger" @click="closePosition(position.id)">
              平仓
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

// 响应式数据
const showRiskAnalysis = ref(false)
const positionStats = ref({
  totalPositions: 8,
  totalPnl: 15420.50,
  totalValue: 125000.00,
  riskLevel: '中等'
})

const riskMetrics = ref({
  totalExposure: 125000.00,
  maxDrawdown: -8.5,
  sharpeRatio: 1.85,
  winRate: 68.5
})

// 模拟持仓数据
const positions = ref([
  {
    id: 'POS001',
    symbol: 'BTCUSDT',
    side: 'long',
    quantity: 0.5,
    entry_price: 44500,
    current_price: 45200,
    pnl: 350,
    pnl_percent: 1.57,
    hold_time: 2 * 24 * 60 * 60 * 1000 // 2天
  },
  {
    id: 'POS002',
    symbol: 'ETHUSDT',
    side: 'short',
    quantity: 2.0,
    entry_price: 3250,
    current_price: 3180,
    pnl: 140,
    pnl_percent: 2.15,
    hold_time: 1 * 24 * 60 * 60 * 1000 // 1天
  },
  {
    id: 'POS003',
    symbol: 'ADAUSDT',
    side: 'long',
    quantity: 1000,
    entry_price: 0.48,
    current_price: 0.45,
    pnl: -30,
    pnl_percent: -6.25,
    hold_time: 5 * 24 * 60 * 60 * 1000 // 5天
  },
  {
    id: 'POS004',
    symbol: 'SOLUSDT',
    side: 'long',
    quantity: 10,
    entry_price: 95.50,
    current_price: 98.20,
    pnl: 27,
    pnl_percent: 2.83,
    hold_time: 3 * 60 * 60 * 1000 // 3小时
  }
])

// 工具函数
const formatNumber = (num: number) => {
  return new Intl.NumberFormat('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(num)
}

const formatDuration = (ms: number) => {
  const days = Math.floor(ms / (24 * 60 * 60 * 1000))
  const hours = Math.floor((ms % (24 * 60 * 60 * 1000)) / (60 * 60 * 1000))
  
  if (days > 0) {
    return `${days}天${hours}小时`
  } else if (hours > 0) {
    return `${hours}小时`
  } else {
    const minutes = Math.floor((ms % (60 * 60 * 1000)) / (60 * 1000))
    return `${minutes}分钟`
  }
}

const getSymbolDesc = (symbol: string) => {
  const descriptions: Record<string, string> = {
    'BTCUSDT': '比特币',
    'ETHUSDT': '以太坊',
    'ADAUSDT': '艾达币',
    'SOLUSDT': 'Solana'
  }
  return descriptions[symbol] || symbol
}

// 页面操作
const refreshPositions = () => {
  console.log('🔄 刷新持仓数据...')
  // 这里可以调用API刷新数据
}

const closeAllPositions = () => {
  console.log('🔒 全部平仓...')
  // 这里可以调用API全部平仓
}

const exportPositions = () => {
  console.log('📤 导出持仓数据...')
  // 这里可以导出持仓数据
}

const adjustPosition = (positionId: string) => {
  console.log('⚙️ 调整持仓:', positionId)
  // 这里可以打开调整持仓的对话框
}

const closePosition = (positionId: string) => {
  console.log('🔒 平仓:', positionId)
  // 这里可以调用API平仓
}

// 生命周期
onMounted(() => {
  console.log('📊 持仓管理页面已加载')
})
</script>

<style scoped>
.simple-positions-view {
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

/* 统计卡片 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 32px;
}

.stat-card {
  background: var(--el-bg-color);
  border-radius: 12px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.stat-icon {
  font-size: 32px;
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  margin-bottom: 4px;
}

.stat-value.positive {
  color: #27ae60;
}

.stat-value.negative {
  color: #e74c3c;
}

.stat-label {
  font-size: 14px;
  color: var(--el-text-color-regular);
  font-weight: 500;
}

/* 操作和风险卡片 */
.actions-card, .risk-card, .positions-card {
  background: var(--el-bg-color);
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  margin-bottom: 24px;
}

.actions-card h3, .risk-card h3, .positions-card h3 {
  margin: 0 0 20px 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.action-btn {
  background: #6c757d;
  color: white;
  border: none;
  padding: 12px 20px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.action-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.action-btn.primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

/* 风险分析 */
.risk-metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.risk-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: var(--el-bg-color-page);
  border-radius: 8px;
}

.risk-label {
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.risk-value {
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.risk-value.positive {
  color: #27ae60;
}

.risk-value.negative {
  color: #e74c3c;
}

/* 持仓表格 */
.positions-table {
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e9ecef;
}

.table-header {
  display: grid;
  grid-template-columns: 140px 100px 80px 100px 100px 120px 100px 120px 120px;
  background: var(--el-bg-color-page);
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.table-row {
  display: grid;
  grid-template-columns: 140px 100px 80px 100px 100px 120px 100px 120px 120px;
  border-top: 1px solid #e9ecef;
}

.table-row:hover {
  background: var(--el-bg-color-page);
}

.header-cell, .table-cell {
  padding: 12px 8px;
  text-align: center;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.symbol-info {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.symbol {
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.symbol-desc {
  font-size: 12px;
  color: var(--el-text-color-regular);
}

.table-cell.long {
  color: #27ae60;
  font-weight: 600;
}

.table-cell.short {
  color: #e74c3c;
  font-weight: 600;
}

.table-cell.positive {
  color: #27ae60;
  font-weight: 600;
}

.table-cell.negative {
  color: #e74c3c;
  font-weight: 600;
}

.btn-small {
  padding: 4px 8px;
  font-size: 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  margin: 0 2px;
  background: #6c757d;
  color: white;
}

.btn-small.primary {
  background: #007bff;
}

.btn-small.danger {
  background: #dc3545;
}

.btn-small:hover {
  opacity: 0.8;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .simple-positions-view {
    padding: 16px;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .actions {
    flex-direction: column;
  }
  
  .positions-table {
    overflow-x: auto;
  }
  
  .risk-metrics {
    grid-template-columns: 1fr;
  }
}
</style>