<template>
  <div class="order-history-view">
    <div class="page-header">
      <h1 class="page-title">📋 历史订单</h1>
      <p class="page-description">查看所有历史交易订单记录</p>
    </div>

    <!-- 筛选器 -->
    <div class="filters-card">
      <h3>🔍 筛选条件</h3>
      <div class="filters">
        <div class="filter-group">
          <label>时间范围:</label>
          <select v-model="filters.timeRange">
            <option value="7d">最近7天</option>
            <option value="30d">最近30天</option>
            <option value="90d">最近90天</option>
            <option value="all">全部</option>
          </select>
        </div>
        <div class="filter-group">
          <label>订单状态:</label>
          <select v-model="filters.status">
            <option value="">全部状态</option>
            <option value="filled">已成交</option>
            <option value="cancelled">已取消</option>
            <option value="rejected">已拒绝</option>
          </select>
        </div>
        <div class="filter-group">
          <label>交易品种:</label>
          <select v-model="filters.symbol">
            <option value="">全部品种</option>
            <option value="BTCUSDT">BTC/USDT</option>
            <option value="ETHUSDT">ETH/USDT</option>
            <option value="ADAUSDT">ADA/USDT</option>
          </select>
        </div>
        <button class="filter-btn" @click="applyFilters">应用筛选</button>
      </div>
    </div>

    <!-- 历史订单列表 -->
    <div class="history-list">
      <h3>📊 订单记录</h3>
      <div class="orders-grid">
        <div v-for="order in filteredOrders" :key="order.id" class="order-card">
          <div class="order-header">
            <span class="order-id">#{{ order.id }}</span>
            <span class="order-time">{{ formatTime(order.created_at) }}</span>
          </div>
          <div class="order-content">
            <div class="order-info">
              <div class="info-row">
                <span class="label">品种:</span>
                <span class="value">{{ order.symbol }}</span>
              </div>
              <div class="info-row">
                <span class="label">方向:</span>
                <span class="value" :class="order.side">
                  {{ order.side === 'buy' ? '买入' : '卖出' }}
                </span>
              </div>
              <div class="info-row">
                <span class="label">数量:</span>
                <span class="value">{{ order.quantity }}</span>
              </div>
              <div class="info-row">
                <span class="label">价格:</span>
                <span class="value">¥{{ formatNumber(order.price) }}</span>
              </div>
            </div>
            <div class="order-status" :class="order.status">
              {{ getStatusText(order.status) }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

// 筛选条件
const filters = ref({
  timeRange: '30d',
  status: '',
  symbol: ''
})

// 模拟历史订单数据
const historyOrders = ref([
  {
    id: 'H001',
    symbol: 'BTCUSDT',
    side: 'buy',
    quantity: 0.5,
    price: 44500,
    status: 'filled',
    created_at: '2025-08-01 10:30:00'
  },
  {
    id: 'H002',
    symbol: 'ETHUSDT',
    side: 'sell',
    quantity: 2.0,
    price: 3200,
    status: 'filled',
    created_at: '2025-08-02 14:15:00'
  },
  {
    id: 'H003',
    symbol: 'ADAUSDT',
    side: 'buy',
    quantity: 1000,
    price: 0.48,
    status: 'cancelled',
    created_at: '2025-08-03 09:20:00'
  }
])

// 筛选后的订单
const filteredOrders = computed(() => {
  let filtered = historyOrders.value
  
  if (filters.value.status) {
    filtered = filtered.filter(order => order.status === filters.value.status)
  }
  
  if (filters.value.symbol) {
    filtered = filtered.filter(order => order.symbol === filters.value.symbol)
  }
  
  return filtered
})

// 工具函数
const formatNumber = (num: number) => {
  return new Intl.NumberFormat('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(num)
}

const formatTime = (timeStr: string) => {
  return timeStr
}

const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    filled: '✅ 已成交',
    cancelled: '❌ 已取消',
    rejected: '🚫 已拒绝'
  }
  return statusMap[status] || status
}

const applyFilters = () => {
  console.log('🔍 应用筛选条件:', filters.value)
}

onMounted(() => {
  console.log('📋 历史订单页面已加载')
})
</script>

<style scoped>
.order-history-view {
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

.filters-card, .history-list {
  background: var(--el-bg-color);
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  margin-bottom: 24px;
}

.filters-card h3, .history-list h3 {
  margin: 0 0 20px 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.filters {
  display: flex;
  gap: 16px;
  align-items: end;
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filter-group label {
  font-weight: 500;
  color: var(--el-text-color-primary);
  font-size: 14px;
}

.filter-group select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  min-width: 120px;
}

.filter-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.3s ease;
}

.filter-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.orders-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 16px;
}

.order-card {
  background: var(--el-bg-color-page);
  border-radius: 8px;
  padding: 16px;
  border: 1px solid #dee2e6;
  transition: all 0.3s ease;
}

.order-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  background: var(--el-bg-color);
}

.order-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.order-id {
  font-weight: 600;
  color: var(--el-text-color-primary);
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

.order-time {
  font-size: 12px;
  color: var(--el-text-color-regular);
}

.order-content {
  display: flex;
  justify-content: space-between;
  align-items: end;
}

.order-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-row {
  display: flex;
  gap: 8px;
}

.info-row .label {
  font-size: 12px;
  color: var(--el-text-color-regular);
  font-weight: 500;
  min-width: 40px;
}

.info-row .value {
  font-size: 14px;
  color: var(--el-text-color-primary);
  font-weight: 600;
}

.info-row .value.buy {
  color: #27ae60;
}

.info-row .value.sell {
  color: #e74c3c;
}

.order-status {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.order-status.filled {
  background: #d4edda;
  color: #155724;
}

.order-status.cancelled {
  background: var(--el-color-danger-light-9);
  color: #721c24;
}

.order-status.rejected {
  background: var(--el-bg-color)3cd;
  color: var(--el-color-warning);
}

@media (max-width: 768px) {
  .order-history-view {
    padding: 16px;
  }
  
  .filters {
    flex-direction: column;
    align-items: stretch;
  }
  
  .orders-grid {
    grid-template-columns: 1fr;
  }
}
</style>