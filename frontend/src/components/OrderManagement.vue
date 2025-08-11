<template>
  <div class="order-management">
    <div class="order-header">
      <div class="header-left">
        <h3>订单管理</h3>
        <div class="order-stats">
          <span class="stat-item">
            活跃订单: <strong class="active">{{ activeOrders.length }}</strong>
          </span>
          <span class="stat-item">
            已成交: <strong class="filled">{{ filledOrders.length }}</strong>
          </span>
          <span class="stat-item">
            已取消: <strong class="cancelled">{{ cancelledOrders.length }}</strong>
          </span>
        </div>
      </div>
      
      <div class="header-actions">
        <el-select v-model="filters.symbol" placeholder="品种" clearable size="small">
          <el-option
            v-for="symbol in availableSymbols"
            :key="symbol"
            :label="symbol"
            :value="symbol"
          />
        </el-select>
        
        <el-select v-model="filters.status" placeholder="状态" clearable size="small">
          <el-option label="待提交" value="pending" />
          <el-option label="已提交" value="submitted" />
          <el-option label="部分成交" value="partially_filled" />
          <el-option label="已成交" value="filled" />
          <el-option label="已取消" value="cancelled" />
          <el-option label="已拒绝" value="rejected" />
        </el-select>
        
        <el-select v-model="filters.side" placeholder="方向" clearable size="small">
          <el-option label="买入" value="buy" />
          <el-option label="卖出" value="sell" />
        </el-select>
        
        <el-date-picker
          v-model="filters.dateRange"
          type="datetimerange"
          range-separator="至"
          start-placeholder="开始时间"
          end-placeholder="结束时间"
          size="small"
          style="width: 300px"
        />
        
        <el-button size="small" @click="handleRefresh" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        
        <el-button size="small" type="danger" @click="handleCancelAll">
          <el-icon><Close /></el-icon>
          取消全部
        </el-button>
      </div>
    </div>

    <!-- 订单表格 -->
    <div class="order-table">
      <el-table
        :data="filteredOrders"
        v-loading="loading"
        @row-click="handleRowClick"
        :default-sort="{ prop: 'created_at', order: 'descending' }"
        height="500"
        stripe
      >
        <el-table-column prop="id" label="订单ID" width="100" />
        
        <el-table-column prop="created_at" label="时间" width="180" sortable>
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="symbol" label="品种" width="120" sortable>
          <template #default="{ row }">
            <el-tag size="small">{{ row.symbol }}</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="side" label="方向" width="80" sortable>
          <template #default="{ row }">
            <el-tag :type="row.side === 'buy' ? 'success' : 'danger'" size="small">
              {{ row.side === 'buy' ? '买入' : '卖出' }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="order_type" label="类型" width="100" sortable>
          <template #default="{ row }">
            {{ getOrderTypeText(row.order_type) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="quantity" label="数量" width="100" sortable align="right">
          <template #default="{ row }">
            {{ formatNumber(row.quantity) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="price" label="价格" width="120" sortable align="right">
          <template #default="{ row }">
            {{ row.price ? formatPrice(row.price) : '-' }}
          </template>
        </el-table-column>
        
        <el-table-column label="成交信息" width="150" align="right">
          <template #default="{ row }">
            <div class="fill-info">
              <div>{{ formatNumber(row.filled_quantity) }}/{{ formatNumber(row.quantity) }}</div>
              <div class="avg-price">
                均价: {{ row.avg_fill_price ? formatPrice(row.avg_fill_price) : '-' }}
              </div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="status" label="状态" width="120" sortable>
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="time_in_force" label="有效期" width="100">
          <template #default="{ row }">
            {{ getTimeInForceText(row.time_in_force) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="canModify(row.status)"
              text
              size="small"
              @click.stop="handleModify(row)"
            >
              修改
            </el-button>
            <el-button
              v-if="canCancel(row.status)"
              text
              size="small"
              type="danger"
              @click.stop="handleCancel(row)"
            >
              取消
            </el-button>
            <el-button text size="small" @click.stop="handleViewDetail(row)">
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 分页 -->
    <div class="order-pagination">
      <el-pagination
        v-model:current-page="pagination.current"
        v-model:page-size="pagination.size"
        :total="ordersTotal"
        :page-sizes="[20, 50, 100, 200]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>

    <!-- 订单详情对话框 -->
    <el-dialog v-model="showDetailDialog" title="订单详情" width="800px">
      <div v-if="selectedOrder" class="order-detail">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-card title="基本信息">
              <el-descriptions :column="1" border>
                <el-descriptions-item label="订单ID">
                  {{ selectedOrder.id }}
                </el-descriptions-item>
                <el-descriptions-item label="客户订单ID">
                  {{ selectedOrder.client_order_id || '-' }}
                </el-descriptions-item>
                <el-descriptions-item label="品种">
                  {{ selectedOrder.symbol }}
                </el-descriptions-item>
                <el-descriptions-item label="方向">
                  <el-tag :type="selectedOrder.side === 'buy' ? 'success' : 'danger'">
                    {{ selectedOrder.side === 'buy' ? '买入' : '卖出' }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="订单类型">
                  {{ getOrderTypeText(selectedOrder.order_type) }}
                </el-descriptions-item>
                <el-descriptions-item label="数量">
                  {{ formatNumber(selectedOrder.quantity) }}
                </el-descriptions-item>
                <el-descriptions-item label="价格">
                  {{ selectedOrder.price ? formatPrice(selectedOrder.price) : '-' }}
                </el-descriptions-item>
                <el-descriptions-item label="有效期">
                  {{ getTimeInForceText(selectedOrder.time_in_force) }}
                </el-descriptions-item>
              </el-descriptions>
            </el-card>
          </el-col>
          
          <el-col :span="12">
            <el-card title="执行信息">
              <el-descriptions :column="1" border>
                <el-descriptions-item label="状态">
                  <el-tag :type="getStatusTagType(selectedOrder.status)">
                    {{ getStatusText(selectedOrder.status) }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="已成交数量">
                  {{ formatNumber(selectedOrder.filled_quantity) }}
                </el-descriptions-item>
                <el-descriptions-item label="剩余数量">
                  {{ formatNumber(selectedOrder.remaining_quantity) }}
                </el-descriptions-item>
                <el-descriptions-item label="平均成交价">
                  {{ selectedOrder.avg_fill_price ? formatPrice(selectedOrder.avg_fill_price) : '-' }}
                </el-descriptions-item>
                <el-descriptions-item label="手续费">
                  {{ formatCurrency(selectedOrder.commission) }}
                </el-descriptions-item>
                <el-descriptions-item label="其他费用">
                  {{ formatCurrency(selectedOrder.fees) }}
                </el-descriptions-item>
                <el-descriptions-item label="创建时间">
                  {{ formatDateTime(selectedOrder.created_at) }}
                </el-descriptions-item>
                <el-descriptions-item label="更新时间">
                  {{ formatDateTime(selectedOrder.updated_at) }}
                </el-descriptions-item>
              </el-descriptions>
            </el-card>
          </el-col>
        </el-row>
        
        <!-- 执行报告 -->
        <el-card title="执行报告" style="margin-top: 16px" v-if="selectedOrder.execution_reports?.length">
          <el-table :data="selectedOrder.execution_reports" size="small">
            <el-table-column prop="execution_id" label="执行ID" width="150" />
            <el-table-column prop="timestamp" label="时间" width="180">
              <template #default="{ row }">
                {{ formatDateTime(row.timestamp) }}
              </template>
            </el-table-column>
            <el-table-column prop="quantity" label="数量" width="100" align="right">
              <template #default="{ row }">
                {{ formatNumber(row.quantity) }}
              </template>
            </el-table-column>
            <el-table-column prop="price" label="价格" width="120" align="right">
              <template #default="{ row }">
                {{ formatPrice(row.price) }}
              </template>
            </el-table-column>
            <el-table-column prop="commission" label="手续费" width="100" align="right">
              <template #default="{ row }">
                {{ formatCurrency(row.commission) }}
              </template>
            </el-table-column>
            <el-table-column prop="liquidity" label="流动性" width="100">
              <template #default="{ row }">
                <el-tag :type="row.liquidity === 'maker' ? 'success' : 'warning'" size="small">
                  {{ row.liquidity === 'maker' ? 'Maker' : 'Taker' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </div>
    </el-dialog>

    <!-- 修改订单对话框 -->
    <el-dialog v-model="showModifyDialog" title="修改订单" width="400px">
      <el-form :model="modifyForm" label-width="80px">
        <el-form-item label="订单ID">
          <span>{{ modifyForm.orderId }}</span>
        </el-form-item>
        <el-form-item label="品种">
          <span>{{ modifyForm.symbol }}</span>
        </el-form-item>
        <el-form-item label="原数量">
          <span>{{ formatNumber(modifyForm.originalQuantity) }}</span>
        </el-form-item>
        <el-form-item label="新数量">
          <el-input-number
            v-model="modifyForm.quantity"
            :min="1"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="原价格">
          <span>{{ modifyForm.originalPrice ? formatPrice(modifyForm.originalPrice) : '-' }}</span>
        </el-form-item>
        <el-form-item label="新价格">
          <el-input-number
            v-model="modifyForm.price"
            :precision="2"
            :min="0"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showModifyDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmModify" :loading="loading">
          确认修改
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Close } from '@element-plus/icons-vue'
import { useTradingStore } from '@/stores/trading'
import type { Order } from '@/types/trading'

const tradingStore = useTradingStore()

// 响应式数据
const showDetailDialog = ref(false)
const showModifyDialog = ref(false)
const selectedOrder = ref<Order | null>(null)

// 筛选条件
const filters = ref({
  symbol: '',
  status: '',
  side: '',
  dateRange: []
})

// 分页
const pagination = ref({
  current: 1,
  size: 50
})

// 修改订单表单
const modifyForm = ref({
  orderId: 0,
  symbol: '',
  originalQuantity: 0,
  originalPrice: 0,
  quantity: 0,
  price: 0
})

// 计算属性
const orders = computed(() => tradingStore.orders)
const activeOrders = computed(() => tradingStore.activeOrders)
const filledOrders = computed(() => tradingStore.filledOrders)
const cancelledOrders = computed(() => tradingStore.cancelledOrders)
const loading = computed(() => tradingStore.loading)
const ordersTotal = computed(() => tradingStore.ordersTotal)

const availableSymbols = computed(() => {
  const symbols = new Set(orders.value.map(order => order.symbol))
  return Array.from(symbols)
})

const filteredOrders = computed(() => {
  let result = orders.value
  
  // 品种筛选
  if (filters.value.symbol) {
    result = result.filter(order => order.symbol === filters.value.symbol)
  }
  
  // 状态筛选
  if (filters.value.status) {
    result = result.filter(order => order.status === filters.value.status)
  }
  
  // 方向筛选
  if (filters.value.side) {
    result = result.filter(order => order.side === filters.value.side)
  }
  
  // 时间筛选
  if (filters.value.dateRange && filters.value.dateRange.length === 2) {
    const [startDate, endDate] = filters.value.dateRange
    result = result.filter(order => {
      const orderTime = new Date(order.created_at).getTime()
      return orderTime >= startDate.getTime() && orderTime <= endDate.getTime()
    })
  }
  
  return result
})

// 方法
const handleRefresh = () => {
  const accountId = tradingStore.currentAccount?.id
  if (accountId) {
    tradingStore.fetchOrders({
      account_id: accountId,
      page: pagination.value.current,
      page_size: pagination.value.size,
      ...filters.value
    })
  }
}

const handleSizeChange = () => {
  handleRefresh()
}

const handleCurrentChange = () => {
  handleRefresh()
}

const handleRowClick = (order: Order) => {
  selectedOrder.value = order
  showDetailDialog.value = true
}

const handleViewDetail = (order: Order) => {
  selectedOrder.value = order
  showDetailDialog.value = true
}

const handleModify = (order: Order) => {
  modifyForm.value = {
    orderId: order.id,
    symbol: order.symbol,
    originalQuantity: order.quantity,
    originalPrice: order.price || 0,
    quantity: order.remaining_quantity,
    price: order.price || 0
  }
  showModifyDialog.value = true
}

const confirmModify = async () => {
  try {
    await tradingStore.modifyOrder(modifyForm.value.orderId, {
      quantity: modifyForm.value.quantity,
      price: modifyForm.value.price
    })
    showModifyDialog.value = false
  } catch (error) {
    // 错误已在store中处理
  }
}

const handleCancel = async (order: Order) => {
  try {
    await ElMessageBox.confirm(
      `确定要取消订单 ${order.id} 吗？`,
      '确认取消',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await tradingStore.cancelOrder(order.id)
  } catch (error) {
    // 用户取消或错误已在store中处理
  }
}

const handleCancelAll = async () => {
  const accountId = tradingStore.currentAccount?.id
  if (!accountId) {
    ElMessage.warning('请先选择交易账户')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      '确定要取消所有活跃订单吗？',
      '确认取消全部',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await tradingStore.cancelAllOrders({ account_id: accountId })
  } catch (error) {
    // 用户取消或错误已在store中处理
  }
}

const canModify = (status: string) => {
  return ['pending', 'submitted', 'partially_filled'].includes(status)
}

const canCancel = (status: string) => {
  return ['pending', 'submitted', 'partially_filled'].includes(status)
}

// 格式化函数
const formatNumber = (num: number) => {
  return new Intl.NumberFormat('zh-CN').format(num)
}

const formatPrice = (price: number) => {
  return price.toFixed(2)
}

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY'
  }).format(value)
}

const formatDateTime = (dateString: string) => {
  return new Date(dateString).toLocaleString('zh-CN')
}

const getOrderTypeText = (type: string) => {
  const textMap: Record<string, string> = {
    market: '市价',
    limit: '限价',
    stop: '止损',
    stop_limit: '止损限价',
    trailing_stop: '跟踪止损'
  }
  return textMap[type] || type
}

const getStatusText = (status: string) => {
  const textMap: Record<string, string> = {
    pending: '待提交',
    submitted: '已提交',
    partially_filled: '部分成交',
    filled: '已成交',
    cancelled: '已取消',
    rejected: '已拒绝',
    expired: '已过期'
  }
  return textMap[status] || status
}

const getStatusTagType = (status: string) => {
  const typeMap: Record<string, string> = {
    pending: 'info',
    submitted: 'warning',
    partially_filled: 'primary',
    filled: 'success',
    cancelled: 'info',
    rejected: 'danger',
    expired: 'info'
  }
  return typeMap[status] || 'info'
}

const getTimeInForceText = (tif: string) => {
  const textMap: Record<string, string> = {
    day: '当日有效',
    gtc: '撤销前有效',
    ioc: '立即成交或取消',
    fok: '全部成交或取消'
  }
  return textMap[tif] || tif
}

// 生命周期
onMounted(() => {
  handleRefresh()
})
</script>

<style scoped lang="scss">
.order-management {
  .order-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 16px;
    padding: 16px;
    background: var(--el-bg-color);
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    
    .header-left {
      h3 {
        margin: 0 0 8px 0;
        font-size: 18px;
        font-weight: 600;
        color: #303133;
      }
      
      .order-stats {
        display: flex;
        gap: 24px;
        
        .stat-item {
          font-size: 14px;
          color: #606266;
          
          strong {
            color: #303133;
            
            &.active {
              color: #409eff;
            }
            
            &.filled {
              color: #67c23a;
            }
            
            &.cancelled {
              color: #909399;
            }
          }
        }
      }
    }
    
    .header-actions {
      display: flex;
      gap: 12px;
      align-items: center;
      flex-wrap: wrap;
    }
  }
  
  .order-table {
    background: var(--el-bg-color);
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    margin-bottom: 16px;
    
    .fill-info {
      .avg-price {
        font-size: 12px;
        color: #909399;
        margin-top: 2px;
      }
    }
  }
  
  .order-pagination {
    display: flex;
    justify-content: center;
    padding: 16px;
    background: var(--el-bg-color);
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }
  
  .order-detail {
    :deep(.el-card__header) {
      padding: 12px 16px;
      font-weight: 600;
    }
  }
}
</style>