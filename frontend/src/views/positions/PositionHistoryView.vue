<template>
  <div class="position-history-view">
    <div class="page-header">
      <h1 class="page-title">🕒 持仓历史</h1>
      <p class="page-description">查看历史持仓记录和盈亏情况</p>
    </div>

    <!-- 统计概览 -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon">📊</div>
        <div class="stat-content">
          <div class="stat-value">{{ historyStats.totalPositions }}</div>
          <div class="stat-label">历史持仓</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">💰</div>
        <div class="stat-content">
          <div class="stat-value positive">+¥{{ formatNumber(historyStats.totalProfit) }}</div>
          <div class="stat-label">总盈利</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">📈</div>
        <div class="stat-content">
          <div class="stat-value">{{ historyStats.winRate }}%</div>
          <div class="stat-label">胜率</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">⏱️</div>
        <div class="stat-content">
          <div class="stat-value">{{ historyStats.avgHoldTime }}</div>
          <div class="stat-label">平均持仓时间</div>
        </div>
      </div>
    </div>

    <!-- 历史持仓列表 -->
    <div class="history-list">
      <h3>📋 历史记录</h3>
      <div class="positions-grid">
        <div v-for="position in historyPositions" :key="position.id" class="position-card">
          <div class="position-header">
            <span class="position-symbol">{{ position.symbol }}</span>
            <span class="position-date">{{ formatDate(position.closeTime) }}</span>
          </div>
          <div class="position-content">
            <div class="position-info">
              <div class="info-row">
                <span class="label">方向:</span>
                <span class="value" :class="position.side">
                  {{ position.side === 'long' ? '🟢 多头' : '🔴 空头' }}
                </span>
              </div>
              <div class="info-row">
                <span class="label">数量:</span>
                <span class="value">{{ position.quantity }}</span>
              </div>
              <div class="info-row">
                <span class="label">开仓价:</span>
                <span class="value">¥{{ formatNumber(position.entryPrice) }}</span>
              </div>
              <div class="info-row">
                <span class="label">平仓价:</span>
                <span class="value">¥{{ formatNumber(position.exitPrice) }}</span>
              </div>
              <div class="info-row">
                <span class="label">盈亏:</span>
                <span class="value" :class="position.pnl >= 0 ? 'positive' : 'negative'">
                  {{ position.pnl >= 0 ? '+' : '' }}¥{{ formatNumber(position.pnl) }}
                </span>
              </div>
              <div class="info-row">
                <span class="label">持仓时间:</span>
                <span class="value">{{ formatDuration(position.holdTime) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

// 历史统计数据
const historyStats = ref({
  totalPositions: 25,
  totalProfit: 8750.50,
  winRate: 72,
  avgHoldTime: '3.5天'
})

// 模拟历史持仓数据
const historyPositions = ref([
  {
    id: 'PH001',
    symbol: 'BTCUSDT',
    side: 'long',
    quantity: 0.5,
    entryPrice: 42000,
    exitPrice: 45000,
    pnl: 1500,
    holdTime: 5 * 24 * 60 * 60 * 1000, // 5天
    closeTime: '2025-08-01'
  },
  {
    id: 'PH002',
    symbol: 'ETHUSDT',
    side: 'short',
    quantity: 2.0,
    entryPrice: 3200,
    exitPrice: 3000,
    pnl: 400,
    holdTime: 2 * 24 * 60 * 60 * 1000, // 2天
    closeTime: '2025-07-30'
  },
  {
    id: 'PH003',
    symbol: 'ADAUSDT',
    side: 'long',
    quantity: 1000,
    entryPrice: 0.50,
    exitPrice: 0.45,
    pnl: -50,
    holdTime: 7 * 24 * 60 * 60 * 1000, // 7天
    closeTime: '2025-07-28'
  }
])

// 工具函数
const formatNumber = (num: number) => {
  return new Intl.NumberFormat('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(num)
}

const formatDate = (dateStr: string) => {
  return dateStr
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

onMounted(() => {
  console.log('🕒 持仓历史页面已加载')
})
</script>

<style scoped>
.position-history-view {
  padding: 24px;
  background: #f8f9fa;
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
  color: #2c3e50;
}

.page-description {
  margin: 0;
  font-size: 18px;
  color: #7f8c8d;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 32px;
}

.stat-card {
  background: white;
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
  color: #2c3e50;
  margin-bottom: 4px;
}

.stat-value.positive {
  color: #27ae60;
}

.stat-label {
  font-size: 14px;
  color: #7f8c8d;
  font-weight: 500;
}

.history-list {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.history-list h3 {
  margin: 0 0 20px 0;
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
}

.positions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 16px;
}

.position-card {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 16px;
  border: 1px solid #dee2e6;
  transition: all 0.3s ease;
}

.position-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  background: white;
}

.position-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.position-symbol {
  font-weight: 600;
  color: #2c3e50;
  font-size: 16px;
}

.position-date {
  font-size: 12px;
  color: #7f8c8d;
}

.position-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-row .label {
  font-size: 12px;
  color: #7f8c8d;
  font-weight: 500;
}

.info-row .value {
  font-size: 14px;
  color: #2c3e50;
  font-weight: 600;
}

.info-row .value.long {
  color: #27ae60;
}

.info-row .value.short {
  color: #e74c3c;
}

.info-row .value.positive {
  color: #27ae60;
}

.info-row .value.negative {
  color: #e74c3c;
}

@media (max-width: 768px) {
  .position-history-view {
    padding: 16px;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .positions-grid {
    grid-template-columns: 1fr;
  }
}
</style>