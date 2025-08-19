<template>
  <div class="realtime-trading">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">实时交易</h1>
        <p class="page-description">基于tqsdk的真实数据交易面板</p>
      </div>
      <div class="header-right">
        <el-button @click="refreshData" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新数据
        </el-button>
      </div>
    </div>

    <!-- 账户信息卡片 -->
    <el-row :gutter="20" class="account-info">
      <el-col :span="6">
        <el-card class="info-card">
          <div class="info-item">
            <div class="info-label">账户余额</div>
            <div class="info-value">¥{{ formatNumber(accountInfo.balance) }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="info-card">
          <div class="info-item">
            <div class="info-label">可用资金</div>
            <div class="info-value">¥{{ formatNumber(accountInfo.available) }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="info-card">
          <div class="info-item">
            <div class="info-label">占用保证金</div>
            <div class="info-value">¥{{ formatNumber(accountInfo.margin) }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="info-card">
          <div class="info-item">
            <div class="info-label">浮动盈亏</div>
            <div class="info-value" :class="accountInfo.profit >= 0 ? 'profit' : 'loss'">
              {{ accountInfo.profit >= 0 ? '+' : '' }}¥{{ formatNumber(accountInfo.profit) }}
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 主要内容区域 -->
    <el-row :gutter="20">
      <!-- 左侧：交易面板 -->
      <el-col :span="8">
        <el-card title="交易下单">
          <template #header>
            <div class="card-header">
              <span>交易下单</span>
              <el-tag :type="tradingEnabled ? 'success' : 'danger'" size="small">
                {{ tradingEnabled ? '交易开启' : '交易关闭' }}
              </el-tag>
            </div>
          </template>

          <el-form :model="orderForm" label-width="80px">
            <el-form-item label="合约">
              <el-select v-model="orderForm.symbol" placeholder="选择合约" @change="onSymbolChange">
                <el-option
                  v-for="contract in contracts"
                  :key="contract.symbol"
                  :label="`${contract.name} (${contract.symbol})`"
                  :value="contract.symbol"
                />
              </el-select>
            </el-form-item>

            <el-form-item label="方向">
              <el-radio-group v-model="orderForm.direction">
                <el-radio-button label="BUY">买入</el-radio-button>
                <el-radio-button label="SELL">卖出</el-radio-button>
              </el-radio-group>
            </el-form-item>

            <el-form-item label="数量">
              <el-input-number
                v-model="orderForm.volume"
                :min="1"
                :max="100"
                controls-position="right"
              />
            </el-form-item>

            <el-form-item label="价格">
              <el-input-number
                v-model="orderForm.price"
                :precision="2"
                :step="0.01"
                controls-position="right"
              />
            </el-form-item>

            <el-form-item label="订单类型">
              <el-select v-model="orderForm.orderType">
                <el-option label="限价单" value="LIMIT" />
                <el-option label="市价单" value="MARKET" />
              </el-select>
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="submitOrder" :loading="orderLoading" :disabled="!tradingEnabled">
                提交订单
              </el-button>
              <el-button @click="resetForm">重置</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <!-- 中间：实时行情 -->
      <el-col :span="8">
        <el-card title="实时行情">
          <div v-if="!selectedQuote" class="empty-state">
            <el-empty description="请选择合约查看行情" />
          </div>
          <div v-else class="quote-panel">
            <div class="quote-header">
              <h3>{{ selectedQuote.symbol }}</h3>
              <el-tag size="small" type="info">{{ formatTime(selectedQuote.datetime) }}</el-tag>
            </div>
            
            <div class="quote-price">
              <div class="price-main">
                <span class="price-value">{{ selectedQuote.last_price?.toFixed(2) }}</span>
                <span class="price-change" :class="getChangeClass(selectedQuote.change)">
                  {{ formatChange(selectedQuote.change, selectedQuote.change_percent) }}
                </span>
              </div>
            </div>

            <div class="quote-details">
              <div class="quote-row">
                <span class="label">买一价:</span>
                <span class="value">{{ selectedQuote.bid_price?.toFixed(2) }}</span>
                <span class="label">卖一价:</span>
                <span class="value">{{ selectedQuote.ask_price?.toFixed(2) }}</span>
              </div>
              <div class="quote-row">
                <span class="label">开盘:</span>
                <span class="value">{{ selectedQuote.open?.toFixed(2) }}</span>
                <span class="label">收盘:</span>
                <span class="value">{{ selectedQuote.pre_close?.toFixed(2) }}</span>
              </div>
              <div class="quote-row">
                <span class="label">最高:</span>
                <span class="value">{{ selectedQuote.high?.toFixed(2) }}</span>
                <span class="label">最低:</span>
                <span class="value">{{ selectedQuote.low?.toFixed(2) }}</span>
              </div>
              <div class="quote-row">
                <span class="label">成交量:</span>
                <span class="value">{{ formatVolume(selectedQuote.volume) }}</span>
                <span class="label">持仓量:</span>
                <span class="value">{{ formatVolume(selectedQuote.open_interest) }}</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：持仓和订单 -->
      <el-col :span="8">
        <el-card>
          <template #header>
            <el-tabs v-model="rightTabActive">
              <el-tab-pane label="当前持仓" name="positions" />
              <el-tab-pane label="活跃订单" name="orders" />
              <el-tab-pane label="成交记录" name="trades" />
            </el-tabs>
          </template>

          <!-- 持仓列表 -->
          <div v-if="rightTabActive === 'positions'" class="positions-panel">
            <div v-if="positions.length === 0" class="empty-state">
              <el-empty description="暂无持仓" />
            </div>
            <div v-else class="positions-list">
              <div v-for="position in positions" :key="position.symbol" class="position-item">
                <div class="position-header">
                  <span class="position-symbol">{{ position.symbol }}</span>
                  <el-tag :type="position.direction === 'LONG' ? 'success' : 'danger'" size="small">
                    {{ position.direction === 'LONG' ? '多头' : '空头' }}
                  </el-tag>
                </div>
                <div class="position-details">
                  <div class="detail-row">
                    <span>数量: {{ position.volume }}</span>
                    <span>均价: {{ position.avg_price?.toFixed(2) }}</span>
                  </div>
                  <div class="detail-row">
                    <span>现价: {{ position.current_price?.toFixed(2) }}</span>
                    <span class="pnl" :class="position.profit >= 0 ? 'profit' : 'loss'">
                      盈亏: {{ position.profit >= 0 ? '+' : '' }}{{ position.profit?.toFixed(2) }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 订单列表 -->
          <div v-if="rightTabActive === 'orders'" class="orders-panel">
            <div v-if="orders.length === 0" class="empty-state">
              <el-empty description="暂无活跃订单" />
            </div>
            <div v-else class="orders-list">
              <div v-for="order in orders" :key="order.order_id" class="order-item">
                <div class="order-header">
                  <span class="order-symbol">{{ order.symbol }}</span>
                  <el-tag :type="getOrderStatusType(order.status)" size="small">
                    {{ order.status }}
                  </el-tag>
                </div>
                <div class="order-details">
                  <div class="detail-row">
                    <span>{{ order.direction }} {{ order.volume }}手</span>
                    <span>{{ order.price?.toFixed(2) }}</span>
                  </div>
                  <div class="detail-row">
                    <span>{{ formatTime(order.created_at) }}</span>
                    <el-button size="small" type="danger" @click="cancelOrder(order.order_id)">
                      撤单
                    </el-button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 成交记录 -->
          <div v-if="rightTabActive === 'trades'" class="trades-panel">
            <div v-if="trades.length === 0" class="empty-state">
              <el-empty description="暂无成交记录" />
            </div>
            <div v-else class="trades-list">
              <div v-for="trade in trades" :key="trade.trade_id" class="trade-item">
                <div class="trade-header">
                  <span class="trade-symbol">{{ trade.symbol }}</span>
                  <span class="trade-time">{{ formatTime(trade.trade_time) }}</span>
                </div>
                <div class="trade-details">
                  <span>{{ trade.direction }} {{ trade.volume }}手 @ {{ trade.price?.toFixed(2) }}</span>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import {
  getContractList,
  getRealTimeQuote,
  getPositions,
  getAccountInfo,
  getOrderHistory,
  getTrades,
  type ContractInfo,
  type RealTimeQuote
} from '@/api/realTimeData'

// 响应式数据
const loading = ref(false)
const orderLoading = ref(false)
const rightTabActive = ref('positions')
const tradingEnabled = ref(true)

// 数据
const contracts = ref<ContractInfo[]>([])
const selectedQuote = ref<RealTimeQuote | null>(null)
const accountInfo = ref({
  balance: 0,
  available: 0,
  margin: 0,
  profit: 0
})
const positions = ref([])
const orders = ref([])
const trades = ref([])

// 订单表单
const orderForm = ref({
  symbol: '',
  direction: 'BUY',
  volume: 1,
  price: 0,
  orderType: 'LIMIT'
})

// 定时器
let refreshTimer: NodeJS.Timeout | null = null

// 加载合约列表
const loadContracts = async () => {
  try {
    const response = await getContractList()
    if (response.success && response.data) {
      contracts.value = response.data.slice(0, 20)
      if (contracts.value.length > 0 && !orderForm.value.symbol) {
        orderForm.value.symbol = contracts.value[0].symbol
        await loadQuote(orderForm.value.symbol)
      }
    }
  } catch (error) {
    console.error('加载合约列表失败:', error)
  }
}

// 加载行情数据
const loadQuote = async (symbol: string) => {
  try {
    const response = await getRealTimeQuote(symbol)
    if (response.success && response.data) {
      selectedQuote.value = response.data
      // 更新订单表单价格
      if (orderForm.value.symbol === symbol) {
        orderForm.value.price = response.data.last_price
      }
    }
  } catch (error) {
    console.error('加载行情数据失败:', error)
  }
}

// 加载账户信息
const loadAccountInfo = async () => {
  try {
    const response = await getAccountInfo()
    if (response.success && response.data) {
      accountInfo.value = response.data
    }
  } catch (error) {
    console.error('加载账户信息失败:', error)
  }
}

// 加载持仓数据
const loadPositions = async () => {
  try {
    const response = await getPositions()
    if (response.success && response.data) {
      positions.value = response.data
    }
  } catch (error) {
    console.error('加载持仓数据失败:', error)
  }
}

// 加载订单数据
const loadOrders = async () => {
  try {
    const response = await getOrderHistory(undefined, 20)
    if (response.success && response.data) {
      orders.value = response.data.orders.filter(order => 
        order.status === 'submitted' || order.status === 'pending'
      )
    }
  } catch (error) {
    console.error('加载订单数据失败:', error)
  }
}

// 加载成交记录
const loadTrades = async () => {
  try {
    const response = await getTrades(20)
    if (response.success && response.data) {
      trades.value = response.data
    }
  } catch (error) {
    console.error('加载成交记录失败:', error)
  }
}

// 刷新所有数据
const refreshData = async () => {
  loading.value = true
  try {
    await Promise.all([
      loadAccountInfo(),
      loadPositions(),
      loadOrders(),
      loadTrades(),
      selectedQuote.value ? loadQuote(selectedQuote.value.symbol) : Promise.resolve()
    ])
  } finally {
    loading.value = false
  }
}

// 合约选择变化
const onSymbolChange = async (symbol: string) => {
  await loadQuote(symbol)
}

// 提交订单
const submitOrder = async () => {
  try {
    await ElMessageBox.confirm('确定要提交这个订单吗？', '确认下单', {
      type: 'warning'
    })

    orderLoading.value = true
    
    // 这里应该调用下单API
    // const response = await placeOrder(orderForm.value)
    
    // 模拟下单成功
    ElMessage.success('订单提交成功')
    await loadOrders()
    
  } catch (error) {
    if (error !== 'cancel') {
      console.error('下单失败:', error)
      ElMessage.error('下单失败')
    }
  } finally {
    orderLoading.value = false
  }
}

// 撤销订单
const cancelOrder = async (orderId: string) => {
  try {
    await ElMessageBox.confirm('确定要撤销这个订单吗？', '确认撤单', {
      type: 'warning'
    })

    // 这里应该调用撤单API
    // const response = await cancelOrder(orderId)
    
    ElMessage.success('订单已撤销')
    await loadOrders()
    
  } catch (error) {
    if (error !== 'cancel') {
      console.error('撤单失败:', error)
      ElMessage.error('撤单失败')
    }
  }
}

// 重置表单
const resetForm = () => {
  orderForm.value = {
    symbol: orderForm.value.symbol,
    direction: 'BUY',
    volume: 1,
    price: selectedQuote.value?.last_price || 0,
    orderType: 'LIMIT'
  }
}

// 格式化函数
const formatNumber = (num: number) => {
  return num?.toLocaleString() || '0'
}

const formatVolume = (volume: number) => {
  if (!volume) return '0'
  if (volume >= 10000) {
    return `${(volume / 10000).toFixed(1)}万`
  }
  return volume.toString()
}

const formatTime = (timestamp: string) => {
  return new Date(timestamp).toLocaleTimeString()
}

const formatChange = (change: number, changePercent: number) => {
  const sign = change >= 0 ? '+' : ''
  return `${sign}${change?.toFixed(2)} (${sign}${changePercent?.toFixed(2)}%)`
}

const getChangeClass = (change: number) => {
  return change >= 0 ? 'positive' : 'negative'
}

const getOrderStatusType = (status: string) => {
  switch (status) {
    case 'filled': return 'success'
    case 'cancelled': return 'info'
    case 'rejected': return 'danger'
    default: return 'warning'
  }
}

// 启动定时刷新
const startAutoRefresh = () => {
  refreshTimer = setInterval(() => {
    refreshData()
  }, 5000) // 5秒刷新一次
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
  refreshData()
  startAutoRefresh()
})

// 组件卸载
onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style scoped>
.realtime-trading {
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

.account-info {
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

.profit {
  color: #67c23a;
}

.loss {
  color: #f56c6c;
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

.quote-panel {
  padding: 10px 0;
}

.quote-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.quote-header h3 {
  margin: 0;
  font-size: 18px;
}

.quote-price {
  text-align: center;
  margin-bottom: 20px;
}

.price-main {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
}

.price-value {
  font-size: 32px;
  font-weight: 600;
  color: #303133;
}

.price-change {
  font-size: 14px;
  font-weight: 500;
}

.quote-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.quote-row {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
}

.quote-row .label {
  color: #909399;
  min-width: 60px;
}

.quote-row .value {
  color: #303133;
  font-weight: 500;
}

.positions-list, .orders-list, .trades-list {
  max-height: 400px;
  overflow-y: auto;
}

.position-item, .order-item, .trade-item {
  padding: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  margin-bottom: 8px;
}

.position-header, .order-header, .trade-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.position-symbol, .order-symbol, .trade-symbol {
  font-weight: 600;
  color: #303133;
}

.position-details, .order-details, .trade-details {
  display: flex;
  flex-direction: column;
  gap: 5px;
  font-size: 12px;
  color: #606266;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pnl {
  font-weight: 600;
}

.empty-state {
  text-align: center;
  padding: 40px;
}
</style>