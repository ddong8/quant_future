<template>
  <div class="trading-view">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">实时交易</h1>
        <p class="page-description">基于tqsdk的实时交易功能</p>
      </div>
      <div class="header-right">
        <el-tag :type="tradingStatus.is_trading_available ? 'success' : 'danger'">
          {{ tradingStatus.is_trading_available ? '交易可用' : '交易不可用' }}
        </el-tag>
        <el-tag v-if="tradingStatus.is_simulation" type="warning">模拟交易</el-tag>
        <el-button @click="refreshData" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <el-row :gutter="20">
      <!-- 左侧：账户信息和下单 -->
      <el-col :xs="24" :sm="24" :md="12" :lg="8">
        <!-- 账户信息 -->
        <el-card class="account-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>账户信息</span>
              <el-button text @click="loadAccountInfo">
                <el-icon><Refresh /></el-icon>
              </el-button>
            </div>
          </template>
          
          <div class="account-info">
            <div class="info-item">
              <span class="label">账户ID:</span>
              <span class="value">{{ accountInfo.account_id }}</span>
            </div>
            <div class="info-item">
              <span class="label">总资产:</span>
              <span class="value amount">{{ formatCurrency(accountInfo.total_asset) }}</span>
            </div>
            <div class="info-item">
              <span class="label">可用资金:</span>
              <span class="value amount">{{ formatCurrency(accountInfo.available) }}</span>
            </div>
            <div class="info-item">
              <span class="label">保证金:</span>
              <span class="value amount">{{ formatCurrency(accountInfo.margin) }}</span>
            </div>
            <div class="info-item">
              <span class="label">浮动盈亏:</span>
              <span class="value" :class="getPnlClass(accountInfo.unrealized_pnl)">
                {{ formatCurrency(accountInfo.unrealized_pnl) }}
              </span>
            </div>
            <div class="info-item">
              <span class="label">风险度:</span>
              <span class="value">{{ (accountInfo.risk_ratio * 100).toFixed(2) }}%</span>
            </div>
          </div>
        </el-card>

        <!-- 下单面板 -->
        <el-card class="order-card" shadow="hover">
          <template #header>
            <span>快速下单</span>
          </template>
          
          <el-form :model="orderForm" label-width="80px" size="default">
            <el-form-item label="合约">
              <el-select v-model="orderForm.symbol" placeholder="选择合约" style="width: 100%">
                <el-option
                  v-for="instrument in instruments"
                  :key="instrument.symbol"
                  :label="`${instrument.name} (${instrument.symbol})`"
                  :value="instrument.symbol"
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
                style="width: 100%"
              />
            </el-form-item>
            
            <el-form-item label="类型">
              <el-radio-group v-model="orderForm.order_type">
                <el-radio-button label="MARKET">市价</el-radio-button>
                <el-radio-button label="LIMIT">限价</el-radio-button>
              </el-radio-group>
            </el-form-item>
            
            <el-form-item v-if="orderForm.order_type === 'LIMIT'" label="价格">
              <el-input-number
                v-model="orderForm.price"
                :precision="2"
                :step="1"
                style="width: 100%"
              />
            </el-form-item>
            
            <el-form-item>
              <el-button
                type="primary"
                @click="placeOrder"
                :loading="orderLoading"
                :disabled="!canPlaceOrder"
                style="width: 100%"
              >
                {{ orderForm.direction === 'BUY' ? '买入' : '卖出' }}
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <!-- 中间：订单和持仓 -->
      <el-col :xs="24" :sm="24" :md="12" :lg="8">
        <!-- 当前订单 -->
        <el-card class="orders-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>当前订单</span>
              <el-button text @click="loadOrders">
                <el-icon><Refresh /></el-icon>
              </el-button>
            </div>
          </template>
          
          <div class="orders-list">
            <div v-if="orders.length === 0" class="empty-state">
              <el-empty description="暂无订单" :image-size="60" />
            </div>
            <div v-else>
              <div
                v-for="order in orders"
                :key="order.order_id"
                class="order-item"
              >
                <div class="order-header">
                  <span class="symbol">{{ order.symbol }}</span>
                  <el-tag
                    :type="order.status === 'FILLED' ? 'success' : 'warning'"
                    size="small"
                  >
                    {{ getOrderStatusText(order.status) }}
                  </el-tag>
                </div>
                <div class="order-details">
                  <span :class="order.direction === 'BUY' ? 'buy' : 'sell'">
                    {{ order.direction === 'BUY' ? '买入' : '卖出' }}
                  </span>
                  <span>{{ order.volume }}手</span>
                  <span>@{{ order.price }}</span>
                </div>
                <div class="order-time">
                  {{ formatTime(order.create_time) }}
                </div>
              </div>
            </div>
          </div>
        </el-card>

        <!-- 当前持仓 -->
        <el-card class="positions-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>当前持仓</span>
              <el-button text @click="loadPositions">
                <el-icon><Refresh /></el-icon>
              </el-button>
            </div>
          </template>
          
          <div class="positions-list">
            <div v-if="positions.length === 0" class="empty-state">
              <el-empty description="暂无持仓" :image-size="60" />
            </div>
            <div v-else>
              <div
                v-for="position in positions"
                :key="position.symbol"
                class="position-item"
              >
                <div class="position-header">
                  <span class="symbol">{{ position.symbol }}</span>
                  <span :class="position.quantity > 0 ? 'long' : 'short'">
                    {{ position.quantity > 0 ? '多' : '空' }}
                  </span>
                </div>
                <div class="position-details">
                  <div class="detail-row">
                    <span>数量: {{ Math.abs(position.quantity) }}手</span>
                    <span>均价: {{ position.avg_price.toFixed(2) }}</span>
                  </div>
                  <div class="detail-row">
                    <span>浮盈: </span>
                    <span :class="getPnlClass(position.unrealized_pnl)">
                      {{ formatCurrency(position.unrealized_pnl) }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：行情信息 -->
      <el-col :xs="24" :sm="24" :md="24" :lg="8">
        <el-card class="quotes-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>实时行情</span>
              <el-button text @click="loadQuotes">
                <el-icon><Refresh /></el-icon>
              </el-button>
            </div>
          </template>
          
          <div class="quotes-list">
            <div
              v-for="quote in quotes"
              :key="quote.symbol"
              class="quote-item"
            >
              <div class="quote-header">
                <span class="symbol">{{ quote.symbol }}</span>
                <span class="price">{{ quote.last_price.toFixed(2) }}</span>
              </div>
              <div class="quote-details">
                <div class="detail-row">
                  <span>买一: {{ quote.bid_price.toFixed(2) }}</span>
                  <span>卖一: {{ quote.ask_price.toFixed(2) }}</span>
                </div>
                <div class="detail-row">
                  <span>成交量: {{ formatVolume(quote.volume) }}</span>
                  <span>持仓量: {{ formatVolume(quote.open_interest) }}</span>
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
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { request } from '@/utils/request'

// 响应式数据
const loading = ref(false)
const orderLoading = ref(false)

// 交易状态
const tradingStatus = ref({
  is_trading_available: false,
  is_simulation: true,
  connection_status: 'disconnected',
  service_status: 'running'
})

// 账户信息
const accountInfo = ref({
  account_id: '',
  balance: 0,
  available: 0,
  margin: 0,
  total_asset: 0,
  unrealized_pnl: 0,
  risk_ratio: 0
})

// 合约信息
const instruments = ref([])

// 下单表单
const orderForm = ref({
  symbol: '',
  direction: 'BUY',
  volume: 1,
  order_type: 'LIMIT',
  price: 0
})

// 订单列表
const orders = ref([])

// 持仓列表
const positions = ref([])

// 行情数据
const quotes = ref([])

// 计算属性
const canPlaceOrder = computed(() => {
  return orderForm.value.symbol && 
         orderForm.value.volume > 0 && 
         (orderForm.value.order_type === 'MARKET' || orderForm.value.price > 0)
})

// 方法
const formatCurrency = (amount: number) => {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY',
    minimumFractionDigits: 2
  }).format(amount)
}

const formatVolume = (volume: number) => {
  if (volume >= 10000) {
    return (volume / 10000).toFixed(1) + '万'
  }
  return volume.toString()
}

const formatTime = (timeStr: string) => {
  return new Date(timeStr).toLocaleTimeString('zh-CN')
}

const getPnlClass = (pnl: number) => {
  if (pnl > 0) return 'profit'
  if (pnl < 0) return 'loss'
  return 'neutral'
}

const getOrderStatusText = (status: string) => {
  const statusMap = {
    'PENDING': '待成交',
    'FILLED': '已成交',
    'CANCELLED': '已撤销'
  }
  return statusMap[status] || status
}

// API 调用方法
const loadTradingStatus = async () => {
  try {
    const response = await request.get('/v1/trading/trading-status')
    if (response.success) {
      tradingStatus.value = response.data
    }
  } catch (error) {
    console.error('获取交易状态失败:', error)
  }
}

const loadAccountInfo = async () => {
  try {
    const response = await request.get('/v1/trading/account')
    if (response.success) {
      accountInfo.value = response.data
    }
  } catch (error) {
    console.error('获取账户信息失败:', error)
    ElMessage.error('获取账户信息失败')
  }
}

const loadInstruments = async () => {
  try {
    const response = await request.get('/v1/market/instruments')
    if (response.success) {
      instruments.value = response.data
      if (response.data.length > 0 && !orderForm.value.symbol) {
        orderForm.value.symbol = response.data[0].symbol
      }
    }
  } catch (error) {
    console.error('获取合约信息失败:', error)
  }
}

const loadOrders = async () => {
  try {
    const response = await request.get('/v1/trading/orders')
    if (response.success) {
      orders.value = response.data
    }
  } catch (error) {
    console.error('获取订单列表失败:', error)
  }
}

const loadPositions = async () => {
  try {
    const response = await request.get('/v1/trading/positions')
    if (response.success) {
      positions.value = response.data
    }
  } catch (error) {
    console.error('获取持仓列表失败:', error)
  }
}

const loadQuotes = async () => {
  try {
    if (instruments.value.length > 0) {
      const symbols = instruments.value.slice(0, 5).map(inst => inst.symbol)
      const quotePromises = symbols.map(symbol => 
        request.get(`/v1/market/quotes/${symbol}`)
      )
      
      const responses = await Promise.all(quotePromises)
      quotes.value = responses
        .filter(response => response.success)
        .map(response => response.data)
    }
  } catch (error) {
    console.error('获取行情数据失败:', error)
  }
}

const placeOrder = async () => {
  try {
    orderLoading.value = true
    
    const response = await request.post('/v1/trading/orders', orderForm.value)
    
    if (response.success) {
      ElMessage.success('下单成功')
      
      // 重置表单
      orderForm.value.volume = 1
      if (orderForm.value.order_type === 'LIMIT') {
        orderForm.value.price = 0
      }
      
      // 刷新数据
      await Promise.all([
        loadOrders(),
        loadPositions(),
        loadAccountInfo()
      ])
    } else {
      ElMessage.error('下单失败')
    }
  } catch (error) {
    console.error('下单失败:', error)
    ElMessage.error('下单失败')
  } finally {
    orderLoading.value = false
  }
}

const refreshData = async () => {
  try {
    loading.value = true
    await Promise.all([
      loadTradingStatus(),
      loadAccountInfo(),
      loadOrders(),
      loadPositions(),
      loadQuotes()
    ])
  } catch (error) {
    console.error('刷新数据失败:', error)
  } finally {
    loading.value = false
  }
}

// 初始化
onMounted(async () => {
  await loadInstruments()
  await refreshData()
  
  // 定时刷新数据
  setInterval(() => {
    loadQuotes()
    loadAccountInfo()
  }, 5000) // 每5秒刷新一次
})
</script>

<style scoped>
.trading-view {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--el-border-color-light);
}

.header-left {
  flex: 1;
}

.page-title {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.page-description {
  margin: 0;
  color: var(--el-text-color-regular);
  font-size: 14px;
}

.header-right {
  display: flex;
  gap: 12px;
  align-items: center;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.account-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.label {
  color: var(--el-text-color-regular);
  font-size: 14px;
}

.value {
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.amount {
  font-family: 'Courier New', monospace;
}

.profit {
  color: #f56c6c;
}

.loss {
  color: #67c23a;
}

.neutral {
  color: var(--el-text-color-regular);
}

.orders-list,
.positions-list {
  max-height: 300px;
  overflow-y: auto;
}

.order-item,
.position-item {
  padding: 12px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 6px;
  margin-bottom: 8px;
}

.order-header,
.position-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.symbol {
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.order-details,
.position-details {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: var(--el-text-color-regular);
}

.detail-row {
  display: flex;
  justify-content: space-between;
  width: 100%;
  margin-bottom: 4px;
}

.buy {
  color: #f56c6c;
}

.sell {
  color: #67c23a;
}

.long {
  color: #f56c6c;
  background: #fef0f0;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
}

.short {
  color: #67c23a;
  background: #f0f9ff;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
}

.order-time {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
  margin-top: 4px;
}

.quotes-list {
  max-height: 400px;
  overflow-y: auto;
}

.quote-item {
  padding: 12px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 6px;
  margin-bottom: 8px;
}

.quote-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.price {
  font-weight: 600;
  font-family: 'Courier New', monospace;
  color: var(--el-text-color-primary);
}

.quote-details {
  font-size: 12px;
  color: var(--el-text-color-regular);
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 120px;
}

.account-card,
.order-card,
.orders-card,
.positions-card,
.quotes-card {
  margin-bottom: 20px;
}

@media (max-width: 768px) {
  .trading-view {
    padding: 10px;
  }
  
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .header-right {
    width: 100%;
    justify-content: flex-end;
  }
}
</style>