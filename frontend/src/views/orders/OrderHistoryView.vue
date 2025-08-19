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
            <option value="SHFE.cu">沪铜</option>
            <option value="DCE.i">铁矿石</option>
            <option value="CZCE.MA">甲醇</option>
          </select>
        </div>
        <button class="filter-btn" @click="applyFilters">应用筛选</button>
      </div>
    </div>

    <!-- 历史订单列表 -->
    <div class="history-list">
      <h3>📊 订单记录</h3>
      <div v-if="filteredOrders.length === 0" class="empty-state">
        <div class="empty-icon">📋</div>
        <div class="empty-text">暂无历史订单记录</div>
      </div>
      <div v-else class="orders-grid">
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
                <span class="value">{{ formatNumber(order.price) }}</span>
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
import { ElMessage } from 'element-plus'
import { request } from '@/utils/request'

// 筛选条件
const filters = ref({
  timeRange: '30d',
  status: '',
  symbol: ''
})

// 历史订单数据
const historyOrders = ref([])

// 加载历史订单数据
const loadHistoryOrders = async () => {
  try {
    // 尝试多个API路径获取历史订单
    const apiConfigs = [
      {
        path: '/v1/orders',
        params: { 
          page_size: 100,
          sort_by: 'created_at',
          sort_order: 'desc'
        }
      },
      {
        path: '/v1/algo-trading/orders',
        params: { limit: 100 }
      },
      {
        path: '/v1/simple-trading/orders',
        params: {}
      }
    ]
    
    let success = false
    for (const config of apiConfigs) {
      try {
        const result = await request.get(config.path, { params: config.params })
        
        if (result.success && result.data) {
          // 处理不同API返回的数据格式
          let orderData = result.data
          if (Array.isArray(result.data.orders)) {
            orderData = result.data.orders
          } else if (!Array.isArray(orderData)) {
            orderData = []
          }
          
          // 转换数据格式
          historyOrders.value = orderData.map(order => ({
            id: order.order_id || order.id || order.uuid,
            symbol: order.symbol,
            side: (order.direction || order.side || 'buy').toLowerCase(),
            quantity: order.volume || order.quantity,
            price: order.price,
            status: (order.status || 'filled').toLowerCase(),
            created_at: order.created_at || order.insert_date_time || order.submitted_at
          }))
          
          success = true
          console.log(`✅ 成功从 ${config.path} 加载 ${historyOrders.value.length} 个历史订单`)
          break
        }
      } catch (apiError) {
        console.log(`❌ 历史订单API ${config.path} 失败:`, apiError.message)
        continue
      }
    }
    
    if (!success) {
      console.warn('⚠️ 所有历史订单API都无法访问，使用模拟数据')
      ElMessage.warning('加载历史订单失败，使用模拟数据')
      loadMockHistoryOrders()
    }
  } catch (error) {
    console.error('❌ 加载历史订单失败:', error)
    ElMessage.warning('加载历史订单失败，使用模拟数据')
    loadMockHistoryOrders()
  }
}

// 加载模拟历史订单数据
const loadMockHistoryOrders = () => {
  historyOrders.value = [
    {
      id: 'H001',
      symbol: 'SHFE.cu2601',
      side: 'buy',
      quantity: 1,
      price: 71500,
      status: 'filled',
      created_at: '2025-01-15 10:30:00'
    },
    {
      id: 'H002',
      symbol: 'DCE.i2601',
      side: 'sell',
      quantity: 2,
      price: 820,
      status: 'filled',
      created_at: '2025-01-14 14:15:00'
    },
    {
      id: 'H003',
      symbol: 'CZCE.MA601',
      side: 'buy',
      quantity: 1,
      price: 2850,
      status: 'cancelled',
      created_at: '2025-01-13 09:20:00'
    },
    {
      id: 'H004',
      symbol: 'SHFE.rb2601',
      side: 'sell',
      quantity: 1,
      price: 3650,
      status: 'filled',
      created_at: '2025-01-12 16:45:00'
    }
  ]
}

// 筛选后的订单
const filteredOrders = computed(() => {
  let filtered = historyOrders.value
  
  if (filters.value.status) {
    filtered = filtered.filter(order => order.status === filters.value.status)
  }
  
  if (filters.value.symbol) {
    filtered = filtered.filter(order => order.symbol.includes(filters.value.symbol))
  }
  
  // 根据时间范围筛选
  if (filters.value.timeRange !== 'all') {
    const now = new Date()
    const days = parseInt(filters.value.timeRange.replace('d', ''))
    const cutoffDate = new Date(now.getTime() - days * 24 * 60 * 60 * 1000)
    
    filtered = filtered.filter(order => {
      const orderDate = new Date(order.created_at)
      return orderDate >= cutoffDate
    })
  }
  
  return filtered
})

// 应用筛选
const applyFilters = () => {
  ElMessage.success('筛选条件已应用')
}

// 获取状态文本
const getStatusText = (status: string) => {
  const statusMap = {
    'filled': '✅ 已成交',
    'cancelled': '❌ 已取消',
    'rejected': '🚫 已拒绝',
    'pending': '⏳ 待处理'
  }
  return statusMap[status] || status
}

// 工具函数
const formatNumber = (num: number) => {
  return new Intl.NumberFormat('zh-CN', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2
  }).format(num)
}

const formatTime = (timeStr: string) => {
  if (!timeStr) return '--'
  return new Date(timeStr).toLocaleString()
}

// 页面初始化
onMounted(() => {
  console.log('📋 历史订单页面已加载')
  loadHistoryOrders()
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
  gap: 20px;
  flex-wrap: wrap;
  align-items: end;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filter-group label {
  font-size: 14px;
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.filter-group select {
  padding: 8px 12px;
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
  background: var(--el-bg-color-page);
  color: var(--el-text-color-primary);
  min-width: 120px;
}

.filter-btn {
  padding: 8px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.filter-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--el-text-color-secondary);
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.empty-text {
  font-size: 16px;
}

.orders-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
}

.order-card {
  background: var(--el-bg-color-page);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid var(--el-border-color-light);
  transition: all 0.3s ease;
}

.order-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.order-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.order-id {
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.order-time {
  font-size: 12px;
  color: var(--el-text-color-regular);
}

.order-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.order-info {
  flex: 1;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
}

.label {
  font-size: 13px;
  color: var(--el-text-color-regular);
  font-weight: 500;
}

.value {
  font-size: 14px;
  color: var(--el-text-color-primary);
  font-weight: 600;
}

.value.buy {
  color: #27ae60;
}

.value.sell {
  color: #e74c3c;
}

.order-status {
  padding: 8px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  text-align: center;
  min-width: 80px;
}

.order-status.filled {
  background: #d4edda;
  color: #155724;
}

.order-status.cancelled {
  background: #f8d7da;
  color: #721c24;
}

.order-status.rejected {
  background: #f8d7da;
  color: #721c24;
}

.order-status.pending {
  background: #fff3cd;
  color: #856404;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .order-history-view {
    padding: 16px;
  }
  
  .page-title {
    font-size: 24px;
  }
  
  .filters {
    flex-direction: column;
    gap: 16px;
  }
  
  .filter-group {
    width: 100%;
  }
  
  .filter-group select {
    width: 100%;
  }
  
  .orders-grid {
    grid-template-columns: 1fr;
  }
  
  .order-content {
    flex-direction: column;
    gap: 12px;
  }
  
  .order-status {
    align-self: flex-start;
  }
}
</style>