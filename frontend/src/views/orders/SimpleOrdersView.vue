<template>
  <div class="simple-orders-view">
    <div class="page-header">
      <h1 class="page-title">📋 订单管理</h1>
      <p class="page-description">管理和监控您的交易订单</p>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon">📄</div>
        <div class="stat-content">
          <div class="stat-value">{{ orderStats.totalOrders }}</div>
          <div class="stat-label">总订单数</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon">⚡</div>
        <div class="stat-content">
          <div class="stat-value">{{ orderStats.activeOrders }}</div>
          <div class="stat-label">活跃订单</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon">✅</div>
        <div class="stat-content">
          <div class="stat-value">{{ orderStats.completedOrders }}</div>
          <div class="stat-label">已完成订单</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon">❌</div>
        <div class="stat-content">
          <div class="stat-value">{{ orderStats.cancelledOrders }}</div>
          <div class="stat-label">已取消订单</div>
        </div>
      </div>
    </div>

    <!-- 操作按钮 -->
    <div class="actions-card">
      <h3>🚀 快速操作</h3>
      <div class="actions">
        <button class="action-btn primary" @click="refreshOrders">
          🔄 刷新订单
        </button>
        <button class="action-btn" @click="createOrder">
          ➕ 创建订单
        </button>
        <button class="action-btn" @click="exportOrders">
          📤 导出订单
        </button>
        <button class="action-btn" @click="showFilters = !showFilters">
          🔍 筛选订单
        </button>
      </div>
    </div>

    <!-- 筛选器 -->
    <div v-if="showFilters" class="filters-card">
      <h3>🔍 订单筛选</h3>
      <div class="filters">
        <div class="filter-item">
          <label>订单状态:</label>
          <select v-model="filters.status">
            <option value="">全部</option>
            <option value="pending">待处理</option>
            <option value="active">活跃</option>
            <option value="completed">已完成</option>
            <option value="cancelled">已取消</option>
          </select>
        </div>
        <div class="filter-item">
          <label>交易品种:</label>
          <select v-model="filters.symbol">
            <option value="">全部</option>
            <option value="BTCUSDT">BTC/USDT</option>
            <option value="ETHUSDT">ETH/USDT</option>
            <option value="ADAUSDT">ADA/USDT</option>
          </select>
        </div>
        <div class="filter-item">
          <label>订单类型:</label>
          <select v-model="filters.type">
            <option value="">全部</option>
            <option value="market">市价单</option>
            <option value="limit">限价单</option>
            <option value="stop">止损单</option>
          </select>
        </div>
      </div>
    </div>

    <!-- 订单列表 -->
    <div class="orders-card">
      <h3>📋 订单列表</h3>
      <div class="orders-table">
        <div class="table-header">
          <div class="header-cell">订单ID</div>
          <div class="header-cell">交易品种</div>
          <div class="header-cell">类型</div>
          <div class="header-cell">方向</div>
          <div class="header-cell">数量</div>
          <div class="header-cell">价格</div>
          <div class="header-cell">状态</div>
          <div class="header-cell">时间</div>
          <div class="header-cell">操作</div>
        </div>
        
        <div v-for="order in filteredOrders" :key="order.id" class="table-row">
          <div class="table-cell">{{ order.id }}</div>
          <div class="table-cell">{{ order.symbol }}</div>
          <div class="table-cell">{{ order.type }}</div>
          <div class="table-cell" :class="order.side">{{ order.side === 'buy' ? '买入' : '卖出' }}</div>
          <div class="table-cell">{{ order.quantity }}</div>
          <div class="table-cell">{{ order.price }}</div>
          <div class="table-cell">
            <span class="status" :class="order.status">{{ getStatusText(order.status) }}</span>
          </div>
          <div class="table-cell">{{ formatTime(order.created_at) }}</div>
          <div class="table-cell">
            <button v-if="order.status === 'pending'" class="btn-small danger" @click="cancelOrder(order.id)">
              取消
            </button>
            <button class="btn-small" @click="viewOrder(order.id)">
              详情
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

// 响应式数据
const showFilters = ref(false)
const orderStats = ref({
  totalOrders: 156,
  activeOrders: 23,
  completedOrders: 128,
  cancelledOrders: 5
})

const filters = ref({
  status: '',
  symbol: '',
  type: ''
})

// 模拟订单数据
const orders = ref([
  {
    id: 'ORD001',
    symbol: 'BTCUSDT',
    type: 'limit',
    side: 'buy',
    quantity: 0.5,
    price: 45000,
    status: 'pending',
    created_at: new Date('2025-08-05T10:30:00')
  },
  {
    id: 'ORD002',
    symbol: 'ETHUSDT',
    type: 'market',
    side: 'sell',
    quantity: 2.0,
    price: 3200,
    status: 'completed',
    created_at: new Date('2025-08-05T09:15:00')
  },
  {
    id: 'ORD003',
    symbol: 'ADAUSDT',
    type: 'limit',
    side: 'buy',
    quantity: 1000,
    price: 0.45,
    status: 'active',
    created_at: new Date('2025-08-05T08:45:00')
  },
  {
    id: 'ORD004',
    symbol: 'BTCUSDT',
    type: 'stop',
    side: 'sell',
    quantity: 0.3,
    price: 44000,
    status: 'cancelled',
    created_at: new Date('2025-08-05T07:20:00')
  }
])

// 计算属性
const filteredOrders = computed(() => {
  return orders.value.filter(order => {
    if (filters.value.status && order.status !== filters.value.status) return false
    if (filters.value.symbol && order.symbol !== filters.value.symbol) return false
    if (filters.value.type && order.type !== filters.value.type) return false
    return true
  })
})

// 工具函数
const formatTime = (time: Date) => {
  return time.toLocaleString('zh-CN')
}

const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    pending: '待处理',
    active: '活跃',
    completed: '已完成',
    cancelled: '已取消'
  }
  return statusMap[status] || status
}

// 页面操作
const refreshOrders = () => {
  console.log('🔄 刷新订单数据...')
  // 这里可以调用API刷新数据
}

const createOrder = () => {
  console.log('➕ 创建新订单...')
  // 这里可以打开创建订单的对话框
}

const exportOrders = () => {
  console.log('📤 导出订单数据...')
  // 这里可以导出订单数据
}

const cancelOrder = (orderId: string) => {
  console.log('❌ 取消订单:', orderId)
  // 这里可以调用API取消订单
}

const viewOrder = (orderId: string) => {
  console.log('👁️ 查看订单详情:', orderId)
  // 这里可以跳转到订单详情页面
}

// 生命周期
onMounted(() => {
  console.log('📋 订单管理页面已加载')
})
</script>

<style scoped>
.simple-orders-view {
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

/* 统计卡片 */
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

.stat-label {
  font-size: 14px;
  color: #7f8c8d;
  font-weight: 500;
}

/* 操作卡片 */
.actions-card, .filters-card, .orders-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  margin-bottom: 24px;
}

.actions-card h3, .filters-card h3, .orders-card h3 {
  margin: 0 0 20px 0;
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
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

/* 筛选器 */
.filters {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filter-item label {
  font-weight: 500;
  color: #2c3e50;
}

.filter-item select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
}

/* 订单表格 */
.orders-table {
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e9ecef;
}

.table-header {
  display: grid;
  grid-template-columns: 100px 120px 80px 80px 100px 100px 80px 140px 100px;
  background: #f8f9fa;
  font-weight: 600;
  color: #2c3e50;
}

.table-row {
  display: grid;
  grid-template-columns: 100px 120px 80px 80px 100px 100px 80px 140px 100px;
  border-top: 1px solid #e9ecef;
}

.table-row:hover {
  background: #f8f9fa;
}

.header-cell, .table-cell {
  padding: 12px 8px;
  text-align: center;
  font-size: 14px;
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
  background: #fff3cd;
  color: #856404;
}

.status.active {
  background: #d1ecf1;
  color: #0c5460;
}

.status.completed {
  background: #d4edda;
  color: #155724;
}

.status.cancelled {
  background: #f8d7da;
  color: #721c24;
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

.btn-small.danger {
  background: #dc3545;
}

.btn-small:hover {
  opacity: 0.8;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .simple-orders-view {
    padding: 16px;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .actions {
    flex-direction: column;
  }
  
  .orders-table {
    overflow-x: auto;
  }
}
</style>