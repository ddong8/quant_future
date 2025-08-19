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
            <option value="SHFE.cu2601">沪铜2601</option>
            <option value="DCE.i2601">铁矿石2601</option>
            <option value="CZCE.MA601">甲醇2601</option>
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
      <div v-loading="loading" class="orders-table">
        <div v-if="filteredOrders.length === 0" class="empty-state">
          <div class="empty-icon">📋</div>
          <div class="empty-text">暂无订单数据</div>
        </div>
        <div v-else class="orders-grid">
          <div v-for="order in filteredOrders" :key="order.order_id || order.id" class="order-card">
            <div class="order-header">
              <span class="order-id">#{{ order.order_id || order.id }}</span>
              <span class="order-status" :class="order.status">
                {{ getStatusText(order.status) }}
              </span>
            </div>
            <div class="order-content">
              <div class="order-info">
                <div class="info-row">
                  <span class="label">品种:</span>
                  <span class="value">{{ order.symbol }}</span>
                </div>
                <div class="info-row">
                  <span class="label">方向:</span>
                  <span class="value" :class="order.direction || order.side">
                    {{ getDirectionText(order.direction || order.side) }}
                  </span>
                </div>
                <div class="info-row">
                  <span class="label">数量:</span>
                  <span class="value">{{ order.volume || order.quantity }}</span>
                </div>
                <div class="info-row">
                  <span class="label">价格:</span>
                  <span class="value">
                    {{ order.price ? formatNumber(order.price) : '市价' }}
                  </span>
                </div>
                <div class="info-row">
                  <span class="label">时间:</span>
                  <span class="value">{{ formatTime(order.created_at || order.insert_date_time) }}</span>
                </div>
              </div>
              <div class="order-actions">
                <button 
                  v-if="order.status === 'ALIVE' || order.status === 'pending'" 
                  class="btn-small danger" 
                  @click="cancelOrder(order)"
                >
                  ❌ 撤单
                </button>
                <button class="btn-small" @click="viewOrderDetail(order)">
                  👁️ 详情
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { request } from '@/utils/request'

// 响应式数据
const loading = ref(false)
const showFilters = ref(false)

// 订单统计
const orderStats = reactive({
  totalOrders: 0,
  activeOrders: 0,
  completedOrders: 0,
  cancelledOrders: 0
})

// 筛选条件
const filters = reactive({
  status: '',
  symbol: '',
  type: ''
})

// 订单列表
const orders = ref([])

// 过滤后的订单
const filteredOrders = computed(() => {
  let filtered = orders.value
  
  if (filters.status) {
    filtered = filtered.filter(order => order.status === filters.status)
  }
  
  if (filters.symbol) {
    filtered = filtered.filter(order => order.symbol === filters.symbol)
  }
  
  if (filters.type) {
    filtered = filtered.filter(order => (order.order_type || order.type) === filters.type)
  }
  
  return filtered
})

// 加载订单数据
const loadOrders = async () => {
  loading.value = true
  try {
    // 尝试多个API路径，按优先级顺序
    const apiConfigs = [
      {
        path: '/v1/orders/my',
        params: { limit: 100 }
      },
      {
        path: '/v1/simple-trading/orders',
        params: {}
      },
      {
        path: '/v1/algo-trading/orders',
        params: { limit: 100 }
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
          
          orders.value = orderData.map(order => ({
            id: order.order_id || order.id || order.uuid,
            order_id: order.order_id || order.id || order.uuid,
            symbol: order.symbol,
            direction: order.direction || order.side,
            volume: order.volume || order.quantity,
            price: order.price,
            status: order.status,
            order_type: order.order_type || order.type,
            created_at: order.created_at || order.insert_date_time || order.submitted_at
          }))
          
          updateOrderStats()
          success = true
          console.log(`✅ 成功从 ${config.path} 加载 ${orders.value.length} 个订单`)
          break
        }
      } catch (apiError) {
        console.log(`❌ API ${config.path} 失败:`, apiError.message)
        continue
      }
    }
    
    if (!success) {
      console.warn('⚠️ 所有订单API都无法访问，使用模拟数据')
      ElMessage.warning('连接订单API失败，使用模拟数据')
      loadMockOrders()
    }
  } catch (error) {
    console.error('❌ 加载订单失败:', error)
    ElMessage.warning('连接订单API失败，使用模拟数据')
    loadMockOrders()
  } finally {
    loading.value = false
  }
}

// 加载模拟订单数据
const loadMockOrders = () => {
  orders.value = [
    {
      id: 'ORD001',
      symbol: 'SHFE.cu2601',
      direction: 'BUY',
      volume: 1,
      price: 71520,
      status: 'ALIVE',
      order_type: 'LIMIT',
      created_at: new Date().toISOString()
    },
    {
      id: 'ORD002',
      symbol: 'DCE.i2601',
      direction: 'SELL',
      volume: 2,
      price: 820,
      status: 'FINISHED',
      order_type: 'LIMIT',
      created_at: new Date(Date.now() - 3600000).toISOString()
    },
    {
      id: 'ORD003',
      symbol: 'CZCE.MA601',
      direction: 'BUY',
      volume: 1,
      price: null,
      status: 'FINISHED',
      order_type: 'MARKET',
      created_at: new Date(Date.now() - 7200000).toISOString()
    }
  ]
  updateOrderStats()
}

// 更新订单统计
const updateOrderStats = () => {
  orderStats.totalOrders = orders.value.length
  orderStats.activeOrders = orders.value.filter(o => o.status === 'ALIVE' || o.status === 'pending').length
  orderStats.completedOrders = orders.value.filter(o => o.status === 'FINISHED' || o.status === 'completed').length
  orderStats.cancelledOrders = orders.value.filter(o => o.status === 'CANCELLED' || o.status === 'cancelled').length
}

// 刷新订单
const refreshOrders = async () => {
  await loadOrders()
  ElMessage.success('订单数据已刷新')
}

// 创建订单
const createOrder = () => {
  ElMessage.info('跳转到交易页面创建订单')
  // 这里可以跳转到交易页面
}

// 导出订单
const exportOrders = () => {
  try {
    const exportData = {
      orders: orders.value,
      export_time: new Date().toISOString(),
      total_count: orders.value.length
    }
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: 'application/json'
    })
    
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `orders_export_${new Date().toISOString().split('T')[0]}.json`
    a.click()
    
    URL.revokeObjectURL(url)
    ElMessage.success('订单数据导出成功')
  } catch (error) {
    ElMessage.error('导出失败')
  }
}

// 撤销订单
const cancelOrder = async (order: any) => {
  try {
    await ElMessageBox.confirm(`确定要撤销订单 #${order.order_id || order.id} 吗？`, '确认撤单', {
      type: 'warning'
    })
    
    // 尝试多个撤单API路径
    const cancelApis = [
      `/v1/orders/${order.order_id || order.id}`,
      `/v1/simple-trading/orders/${order.order_id || order.id}`
    ]
    
    let success = false
    for (const apiPath of cancelApis) {
      try {
        const result = await request.delete(apiPath)
        
        if (result.success) {
          ElMessage.success('订单撤销成功')
          await loadOrders()
          success = true
          break
        }
      } catch (apiError) {
        console.log(`撤单API ${apiPath} 失败:`, apiError)
        continue
      }
    }
    
    if (!success) {
      throw new Error('所有撤单API都无法访问')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('❌ 撤单失败:', error)
      ElMessage.error(`撤单失败: ${error.message || error}`)
    }
  }
}

// 查看订单详情
const viewOrderDetail = (order: any) => {
  ElMessage.info(`查看订单详情: #${order.order_id || order.id}`)
  // 这里可以打开订单详情对话框
}

// 工具函数
const getStatusText = (status: string) => {
  const statusMap = {
    'ALIVE': '活跃',
    'FINISHED': '已完成',
    'CANCELLED': '已取消',
    'pending': '待处理',
    'active': '活跃',
    'completed': '已完成',
    'cancelled': '已取消'
  }
  return statusMap[status] || status
}

const getDirectionText = (direction: string) => {
  const directionMap = {
    'BUY': '买入',
    'SELL': '卖出',
    'buy': '买入',
    'sell': '卖出'
  }
  return directionMap[direction] || direction
}

const formatNumber = (num: number) => {
  return new Intl.NumberFormat('zh-CN').format(num)
}

const formatTime = (timestamp: string) => {
  if (!timestamp) return '--'
  return new Date(timestamp).toLocaleString()
}

// 页面初始化
onMounted(() => {
  console.log('📋 订单管理页面已加载')
  loadOrders()
})
</script>

<style scoped>
.simple-orders-view {
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

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
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
  color: white;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  margin-bottom: 4px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

.stat-label {
  font-size: 14px;
  color: var(--el-text-color-regular);
  font-weight: 500;
}

.actions-card, .filters-card, .orders-card {
  background: var(--el-bg-color);
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  margin-bottom: 24px;
}

.actions-card h3, .filters-card h3, .orders-card h3 {
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

.filters {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filter-item label {
  font-size: 14px;
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.filter-item select {
  padding: 8px 12px;
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
  background: var(--el-bg-color-page);
  color: var(--el-text-color-primary);
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
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
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
}

.order-id {
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.order-status {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
}

.order-status.ALIVE, .order-status.pending {
  background: #fff3cd;
  color: #856404;
}

.order-status.FINISHED, .order-status.completed {
  background: #d4edda;
  color: #155724;
}

.order-status.CANCELLED, .order-status.cancelled {
  background: #f8d7da;
  color: #721c24;
}

.order-info {
  margin-bottom: 16px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.info-row:last-child {
  border-bottom: none;
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

.value.BUY, .value.buy {
  color: #27ae60;
}

.value.SELL, .value.sell {
  color: #e74c3c;
}

.order-actions {
  display: flex;
  gap: 8px;
}

.btn-small {
  padding: 6px 12px;
  font-size: 12px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  background: #6c757d;
  color: white;
  font-weight: 500;
  transition: all 0.3s ease;
}

.btn-small:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.btn-small.danger {
  background: #dc3545;
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
  
  .filters {
    flex-direction: column;
  }
  
  .orders-grid {
    grid-template-columns: 1fr;
  }
}
</style>