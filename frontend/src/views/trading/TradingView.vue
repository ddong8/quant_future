<template>
  <div class="simple-trading-view">
    <div class="page-header">
      <h1 class="page-title">📈 交易中心</h1>
      <p class="page-description">执行您的交易策略</p>
    </div>

    <!-- 市场概览 -->
    <div class="market-overview">
      <h3>📊 市场概览</h3>
      <div class="market-grid">
        <div v-for="market in marketData" :key="market.symbol" class="market-card">
          <div class="market-symbol">{{ market.symbol }}</div>
          <div class="market-price" :class="market.change >= 0 ? 'positive' : 'negative'">
            ¥{{ formatNumber(market.price) }}
          </div>
          <div class="market-change" :class="market.change >= 0 ? 'positive' : 'negative'">
            {{ market.change >= 0 ? '+' : '' }}{{ market.change.toFixed(2) }}%
          </div>
        </div>
      </div>
    </div>

    <!-- 交易面板 -->
    <div class="trading-panels">
      <div class="trading-panel">
        <h3>🟢 买入订单</h3>
        <div class="order-form">
          <div class="form-group">
            <label>交易品种:</label>
            <select v-model="buyOrder.symbol">
              <option value="BTCUSDT">BTC/USDT</option>
              <option value="ETHUSDT">ETH/USDT</option>
              <option value="ADAUSDT">ADA/USDT</option>
              <option value="SOLUSDT">SOL/USDT</option>
            </select>
          </div>
          
          <div class="form-group">
            <label>订单类型:</label>
            <select v-model="buyOrder.type">
              <option value="market">市价单</option>
              <option value="limit">限价单</option>
              <option value="stop">止损单</option>
            </select>
          </div>
          
          <div class="form-group">
            <label>数量:</label>
            <input v-model="buyOrder.quantity" type="number" step="0.01" placeholder="输入数量">
          </div>
          
          <div v-if="buyOrder.type !== 'market'" class="form-group">
            <label>价格:</label>
            <input v-model="buyOrder.price" type="number" step="0.01" placeholder="输入价格">
          </div>
          
          <button class="order-btn buy" @click="placeBuyOrder">
            🟢 买入 {{ buyOrder.symbol }}
          </button>
        </div>
      </div>

      <div class="trading-panel">
        <h3>🔴 卖出订单</h3>
        <div class="order-form">
          <div class="form-group">
            <label>交易品种:</label>
            <select v-model="sellOrder.symbol">
              <option value="BTCUSDT">BTC/USDT</option>
              <option value="ETHUSDT">ETH/USDT</option>
              <option value="ADAUSDT">ADA/USDT</option>
              <option value="SOLUSDT">SOL/USDT</option>
            </select>
          </div>
          
          <div class="form-group">
            <label>订单类型:</label>
            <select v-model="sellOrder.type">
              <option value="market">市价单</option>
              <option value="limit">限价单</option>
              <option value="stop">止损单</option>
            </select>
          </div>
          
          <div class="form-group">
            <label>数量:</label>
            <input v-model="sellOrder.quantity" type="number" step="0.01" placeholder="输入数量">
          </div>
          
          <div v-if="sellOrder.type !== 'market'" class="form-group">
            <label>价格:</label>
            <input v-model="sellOrder.price" type="number" step="0.01" placeholder="输入价格">
          </div>
          
          <button class="order-btn sell" @click="placeSellOrder">
            🔴 卖出 {{ sellOrder.symbol }}
          </button>
        </div>
      </div>
    </div>

    <!-- 快速交易 -->
    <div class="quick-trading">
      <h3>⚡ 快速交易</h3>
      <div class="quick-buttons">
        <button class="quick-btn" @click="quickTrade('BTCUSDT', 'buy', 0.1)">
          快速买入 0.1 BTC
        </button>
        <button class="quick-btn" @click="quickTrade('ETHUSDT', 'buy', 1)">
          快速买入 1 ETH
        </button>
        <button class="quick-btn" @click="quickTrade('BTCUSDT', 'sell', 0.1)">
          快速卖出 0.1 BTC
        </button>
        <button class="quick-btn" @click="quickTrade('ETHUSDT', 'sell', 1)">
          快速卖出 1 ETH
        </button>
      </div>
    </div>

    <!-- 交易历史 -->
    <div class="trading-history">
      <h3>📋 最近交易</h3>
      <div class="history-table">
        <div class="table-header">
          <div class="header-cell">时间</div>
          <div class="header-cell">品种</div>
          <div class="header-cell">类型</div>
          <div class="header-cell">方向</div>
          <div class="header-cell">数量</div>
          <div class="header-cell">价格</div>
          <div class="header-cell">状态</div>
        </div>
        
        <div v-for="trade in recentTrades" :key="trade.id" class="table-row">
          <div class="table-cell">{{ formatTime(trade.time) }}</div>
          <div class="table-cell">{{ trade.symbol }}</div>
          <div class="table-cell">{{ trade.type }}</div>
          <div class="table-cell" :class="trade.side">
            {{ trade.side === 'buy' ? '🟢 买入' : '🔴 卖出' }}
          </div>
          <div class="table-cell">{{ trade.quantity }}</div>
          <div class="table-cell">¥{{ formatNumber(trade.price) }}</div>
          <div class="table-cell">
            <span class="status" :class="trade.status">{{ getStatusText(trade.status) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

// 响应式数据
const buyOrder = ref({
  symbol: 'BTCUSDT',
  type: 'market',
  quantity: 0,
  price: 0
})

const sellOrder = ref({
  symbol: 'BTCUSDT',
  type: 'market',
  quantity: 0,
  price: 0
})

// 模拟市场数据
const marketData = ref([
  { symbol: 'BTC/USDT', price: 45200, change: 2.35 },
  { symbol: 'ETH/USDT', price: 3180, change: -1.25 },
  { symbol: 'ADA/USDT', price: 0.45, change: 5.67 },
  { symbol: 'SOL/USDT', price: 98.20, change: 3.42 }
])

// 模拟交易历史
const recentTrades = ref([
  {
    id: 'T001',
    time: new Date('2025-08-05T14:30:00'),
    symbol: 'BTCUSDT',
    type: 'market',
    side: 'buy',
    quantity: 0.1,
    price: 45100,
    status: 'completed'
  },
  {
    id: 'T002',
    time: new Date('2025-08-05T13:45:00'),
    symbol: 'ETHUSDT',
    type: 'limit',
    side: 'sell',
    quantity: 2.0,
    price: 3200,
    status: 'completed'
  },
  {
    id: 'T003',
    time: new Date('2025-08-05T12:20:00'),
    symbol: 'ADAUSDT',
    type: 'market',
    side: 'buy',
    quantity: 1000,
    price: 0.44,
    status: 'pending'
  }
])

// 工具函数
const formatNumber = (num: number) => {
  return new Intl.NumberFormat('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(num)
}

const formatTime = (time: Date) => {
  return time.toLocaleTimeString('zh-CN')
}

const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    pending: '待处理',
    completed: '已完成',
    cancelled: '已取消'
  }
  return statusMap[status] || status
}

// 交易操作
const placeBuyOrder = () => {
  console.log('🟢 下买单:', buyOrder.value)
  // 这里可以调用API下买单
  alert(`买入订单已提交: ${buyOrder.value.quantity} ${buyOrder.value.symbol}`)
}

const placeSellOrder = () => {
  console.log('🔴 下卖单:', sellOrder.value)
  // 这里可以调用API下卖单
  alert(`卖出订单已提交: ${sellOrder.value.quantity} ${sellOrder.value.symbol}`)
}

const quickTrade = (symbol: string, side: string, quantity: number) => {
  console.log(`⚡ 快速交易: ${side} ${quantity} ${symbol}`)
  // 这里可以调用API快速交易
  alert(`快速${side === 'buy' ? '买入' : '卖出'}订单已提交: ${quantity} ${symbol}`)
}

// 生命周期
onMounted(() => {
  console.log('📈 交易中心页面已加载')
})
</script>

<style scoped>
.simple-trading-view {
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

/* 市场概览 */
.market-overview {
  background: var(--el-bg-color);
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  margin-bottom: 24px;
}

.market-overview h3 {
  margin: 0 0 20px 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.market-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.market-card {
  background: var(--el-bg-color-page);
  border-radius: 8px;
  padding: 16px;
  text-align: center;
  border: 1px solid #e9ecef;
}

.market-symbol {
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin-bottom: 8px;
}

.market-price {
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 4px;
}

.market-change {
  font-size: 14px;
  font-weight: 600;
}

.market-price.positive, .market-change.positive {
  color: #27ae60;
}

.market-price.negative, .market-change.negative {
  color: #e74c3c;
}

/* 交易面板 */
.trading-panels {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-bottom: 24px;
}

.trading-panel {
  background: var(--el-bg-color);
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.trading-panel h3 {
  margin: 0 0 20px 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.order-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.form-group select,
.form-group input {
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
}

.order-btn {
  padding: 16px;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.order-btn.buy {
  background: #27ae60;
  color: white;
}

.order-btn.sell {
  background: #e74c3c;
  color: white;
}

.order-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

/* 快速交易 */
.quick-trading, .trading-history {
  background: var(--el-bg-color);
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  margin-bottom: 24px;
}

.quick-trading h3, .trading-history h3 {
  margin: 0 0 20px 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.quick-buttons {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.quick-btn {
  padding: 12px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.quick-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

/* 交易历史表格 */
.history-table {
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e9ecef;
}

.table-header {
  display: grid;
  grid-template-columns: 120px 100px 80px 100px 100px 100px 80px;
  background: var(--el-bg-color-page);
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.table-row {
  display: grid;
  grid-template-columns: 120px 100px 80px 100px 100px 100px 80px;
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

.table-cell.buy {
  color: #27ae60;
  font-weight: 600;
}

.table-cell.sell {
  color: #e74c3c;
  font-weight: 600;
}

.status {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.status.pending {
  background: var(--el-color-warning-light-9);
  color: var(--el-color-warning);
}

.status.completed {
  background: #d4edda;
  color: #155724;
}

.status.cancelled {
  background: var(--el-color-danger-light-9);
  color: #721c24;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .simple-trading-view {
    padding: 16px;
  }
  
  .trading-panels {
    grid-template-columns: 1fr;
  }
  
  .market-grid {
    grid-template-columns: 1fr;
  }
  
  .quick-buttons {
    grid-template-columns: 1fr;
  }
  
  .history-table {
    overflow-x: auto;
  }
}
</style>