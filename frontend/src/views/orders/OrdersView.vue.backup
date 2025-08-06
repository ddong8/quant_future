<template>
  <div class="orders-view">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">订单管理</h1>
        <div class="page-description-container">
          <p class="page-description">管理和监控您的交易订单</p>
          <div class="connection-status">
            <el-tag
              :type="getConnectionStatusType(orderWebSocket.connectionStatus.value)"
              size="small"
              effect="plain"
            >
              <el-icon><Connection /></el-icon>
              {{ getConnectionStatusText(orderWebSocket.connectionStatus.value) }}
            </el-tag>
          </div>
        </div>
      </div>
      <div class="header-right">
        <el-button @click="showExecutionPanel = true">
          <el-icon><Setting /></el-icon>
          执行管理
        </el-button>
        <el-button type="primary" @click="showCreateOrder = true">
          <el-icon><Plus /></el-icon>
          创建订单
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-value">{{ stats.total_orders }}</div>
              <div class="stat-label">总订单数</div>
            </div>
            <el-icon class="stat-icon"><Document /></el-icon>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card active">
            <div class="stat-content">
              <div class="stat-value">{{ stats.active_orders }}</div>
              <div class="stat-label">活跃订单</div>
            </div>
            <el-icon class="stat-icon"><Clock /></el-icon>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card success">
            <div class="stat-content">
              <div class="stat-value">{{ stats.filled_orders }}</div>
              <div class="stat-label">已成交</div>
            </div>
            <el-icon class="stat-icon"><Check /></el-icon>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-value">{{ (stats.success_rate * 100).toFixed(1) }}%</div>
              <div class="stat-label">成功率</div>
            </div>
            <el-icon class="stat-icon"><TrendCharts /></el-icon>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 筛选和搜索 -->
    <el-card class="filter-card">
      <OrderFilter 
        v-model="searchParams" 
        @search="handleSearch"
        @reset="handleResetFilter"
      />
    </el-card>

    <!-- 订单表格 -->
    <el-card class="table-card">
      <template #header>
        <div class="card-header">
          <span>订单列表</span>
          <div class="header-actions">
            <el-button 
              size="small" 
              @click="refreshOrders"
              :loading="loading"
            >
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
            <el-button 
              size="small" 
              @click="handleBatchCancel"
              :disabled="selectedOrders.length === 0"
            >
              批量取消
            </el-button>
          </div>
        </div>
      </template>

      <OrderTable
        :orders="orders"
        :loading="loading"
        @selection-change="handleSelectionChange"
        @view-order="handleViewOrder"
        @edit-order="handleEditOrder"
        @cancel-order="handleCancelOrder"
        @view-fills="handleViewFills"
      />

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="searchParams.page"
          v-model:page-size="searchParams.page_size"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handlePageSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 创建订单对话框 -->
    <CreateOrderDialog
      v-model="showCreateOrder"
      @success="handleOrderCreated"
    />

    <!-- 订单详情对话框 -->
    <OrderDetailDialog
      v-model="showOrderDetail"
      :order-id="selectedOrderId"
    />

    <!-- 编辑订单对话框 -->
    <EditOrderDialog
      v-model="showEditOrder"
      :order-id="selectedOrderId"
      @success="handleOrderUpdated"
    />

    <!-- 成交记录对话框 -->
    <OrderFillsDialog
      v-model="showOrderFills"
      :order-id="selectedOrderId"
    />

    <!-- 执行管理面板 -->
    <el-dialog
      v-model="showExecutionPanel"
      title="订单执行管理"
      width="90%"
      :close-on-click-modal="false"
    >
      <OrderExecutionPanel />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Document, Clock, Check, TrendCharts, Refresh, Connection, Setting } from '@element-plus/icons-vue'
import { orderApi, type Order, type OrderSearchParams, type OrderStats } from '@/api/order'
import { useOrderWebSocket } from '@/composables/useOrderWebSocket'
import { useOrderStore } from '@/stores/order'
import OrderFilter from './components/OrderFilter.vue'
import OrderTable from './components/OrderTable.vue'
import CreateOrderDialog from './components/CreateOrderDialog.vue'
import OrderDetailDialog from './components/OrderDetailDialog.vue'
import EditOrderDialog from './components/EditOrderDialog.vue'
import OrderFillsDialog from './components/OrderFillsDialog.vue'
import OrderExecutionPanel from './components/OrderExecutionPanel.vue'

// 响应式数据
const loading = ref(false)
const orders = ref<Order[]>([])
const selectedOrders = ref<Order[]>([])
const total = ref(0)

// WebSocket和状态管理
const orderWebSocket = useOrderWebSocket()
const orderStore = useOrderStore()

// 统计数据
const stats = ref<OrderStats>({
  total_orders: 0,
  active_orders: 0,
  filled_orders: 0,
  cancelled_orders: 0,
  rejected_orders: 0,
  total_volume: 0,
  total_value: 0,
  avg_fill_ratio: 0,
  success_rate: 0
})

// 搜索参数
const searchParams = ref<OrderSearchParams>({
  page: 1,
  page_size: 20,
  sort_by: 'created_at',
  sort_order: 'desc'
})

// 对话框状态
const showCreateOrder = ref(false)
const showOrderDetail = ref(false)
const showEditOrder = ref(false)
const showOrderFills = ref(false)
const showExecutionPanel = ref(false)
const selectedOrderId = ref<number>()

// 加载订单列表
const loadOrders = async () => {
  try {
    loading.value = true
    const response = await orderApi.searchOrders(searchParams.value)
    orders.value = response.data.data
    total.value = response.data.meta.total
  } catch (error) {
    console.error('加载订单列表失败:', error)
    ElMessage.error('加载订单列表失败')
  } finally {
    loading.value = false
  }
}

// 加载统计数据
const loadStats = async () => {
  try {
    const response = await orderApi.getOrderStats()
    stats.value = response.data
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

// 搜索处理
const handleSearch = () => {
  searchParams.value.page = 1
  loadOrders()
}

// 重置筛选
const handleResetFilter = () => {
  Object.assign(searchParams.value, {
    symbol: undefined,
    order_type: undefined,
    side: undefined,
    status: undefined,
    strategy_id: undefined,
    backtest_id: undefined,
    tags: undefined,
    created_after: undefined,
    created_before: undefined,
    page: 1,
    page_size: 20,
    sort_by: 'created_at',
    sort_order: 'desc'
  })
  loadOrders()
}

// 刷新订单
const refreshOrders = () => {
  loadOrders()
  loadStats()
}

// 分页处理
const handlePageChange = (page: number) => {
  searchParams.value.page = page
  loadOrders()
}

const handlePageSizeChange = (pageSize: number) => {
  searchParams.value.page_size = pageSize
  searchParams.value.page = 1
  loadOrders()
}

// 选择处理
const handleSelectionChange = (selection: Order[]) => {
  selectedOrders.value = selection
}

// 查看订单详情
const handleViewOrder = (order: Order) => {
  selectedOrderId.value = order.id
  showOrderDetail.value = true
}

// 编辑订单
const handleEditOrder = (order: Order) => {
  if (!order.is_active) {
    ElMessage.warning('只能编辑活跃状态的订单')
    return
  }
  selectedOrderId.value = order.id
  showEditOrder.value = true
}

// 取消订单
const handleCancelOrder = async (order: Order) => {
  if (!order.is_active) {
    ElMessage.warning('订单已结束，无法取消')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要取消订单 ${order.symbol} ${order.side.toUpperCase()} ${order.quantity} 吗？`,
      '取消订单',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await orderApi.cancelOrder(order.id)
    ElMessage.success('订单取消成功')
    refreshOrders()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('取消订单失败:', error)
      ElMessage.error('取消订单失败')
    }
  }
}

// 批量取消订单
const handleBatchCancel = async () => {
  const activeOrders = selectedOrders.value.filter(order => order.is_active)
  
  if (activeOrders.length === 0) {
    ElMessage.warning('请选择活跃状态的订单')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要取消选中的 ${activeOrders.length} 个订单吗？`,
      '批量取消订单',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const orderIds = activeOrders.map(order => order.id)
    await orderApi.batchCancelOrders(orderIds)
    ElMessage.success('批量取消订单成功')
    refreshOrders()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('批量取消订单失败:', error)
      ElMessage.error('批量取消订单失败')
    }
  }
}

// 查看成交记录
const handleViewFills = (order: Order) => {
  selectedOrderId.value = order.id
  showOrderFills.value = true
}

// 订单创建成功
const handleOrderCreated = () => {
  refreshOrders()
}

// 订单更新成功
const handleOrderUpdated = () => {
  refreshOrders()
}

// 连接状态辅助函数
const getConnectionStatusType = (status: string) => {
  const typeMap: Record<string, string> = {
    connected: 'success',
    reconnecting: 'warning',
    disconnected: 'danger'
  }
  return typeMap[status] || 'info'
}

const getConnectionStatusText = (status: string) => {
  const textMap: Record<string, string> = {
    connected: '实时连接',
    reconnecting: '重连中',
    disconnected: '连接断开'
  }
  return textMap[status] || '未知状态'
}

// WebSocket消息处理
const setupWebSocketHandlers = () => {
  // 监听订单状态变化
  orderWebSocket.onMessage('order_status_changed', (message: any) => {
    // 如果当前页面显示的订单包含更新的订单，刷新列表
    const updatedOrder = orders.value.find(order => order.id === message.order_id)
    if (updatedOrder) {
      // 更新本地订单数据
      Object.assign(updatedOrder, {
        status: message.status,
        filled_quantity: message.filled_quantity,
        remaining_quantity: message.remaining_quantity,
        fill_ratio: message.fill_ratio,
        is_active: message.is_active,
        is_finished: message.is_finished
      })
      
      // 刷新统计数据
      loadStats()
    }
  })
  
  // 监听订单创建
  orderWebSocket.onMessage('order_created', () => {
    // 刷新订单列表和统计
    loadOrders()
    loadStats()
  })
  
  // 监听订单成交
  orderWebSocket.onMessage('order_filled', (message: any) => {
    const updatedOrder = orders.value.find(order => order.id === message.order_id)
    if (updatedOrder) {
      // 更新订单状态
      Object.assign(updatedOrder, message.order_status)
      
      // 刷新统计数据
      loadStats()
    }
  })
  
  // 监听订单取消
  orderWebSocket.onMessage('order_cancelled', (message: any) => {
    const updatedOrder = orders.value.find(order => order.id === message.order_id)
    if (updatedOrder) {
      updatedOrder.status = 'cancelled'
      updatedOrder.is_active = false
      updatedOrder.is_finished = true
      
      // 刷新统计数据
      loadStats()
    }
  })
  
  // 监听批量操作结果
  orderWebSocket.onMessage('batch_operation_result', () => {
    // 刷新订单列表和统计
    loadOrders()
    loadStats()
  })
}

// 初始化
onMounted(() => {
  loadOrders()
  loadStats()
  
  // 建立WebSocket连接
  orderWebSocket.connect()
  setupWebSocketHandlers()
})

// 清理
onUnmounted(() => {
  orderWebSocket.disconnect()
})
</script>

<style scoped>
.orders-view {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-title {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.page-description-container {
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-description {
  margin: 4px 0 0 0;
  color: var(--el-text-color-regular);
}

.connection-status {
  display: flex;
  align-items: center;
}

.stats-cards {
  margin-bottom: 20px;
}

.stat-card {
  position: relative;
  overflow: hidden;
}

.stat-card.active {
  border-color: var(--el-color-warning);
}

.stat-card.success {
  border-color: var(--el-color-success);
}

.stat-card :deep(.el-card__body) {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  line-height: 1;
}

.stat-label {
  font-size: 14px;
  color: var(--el-text-color-regular);
  margin-top: 4px;
}

.stat-icon {
  font-size: 32px;
  color: var(--el-color-primary);
  opacity: 0.8;
}

.filter-card,
.table-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}
</style>