<template>
  <div class="quick-trading-buttons">
    <el-card title="快速交易">
      <template #header>
        <div class="card-header">
          <span>快速交易</span>
          <el-button text @click="showSettings = true">
            <el-icon><Setting /></el-icon>
            设置
          </el-button>
        </div>
      </template>

      <!-- 合约选择 -->
      <div class="symbol-selector">
        <el-select
          v-model="selectedSymbol"
          placeholder="选择交易合约"
          filterable
          style="width: 100%"
          @change="onSymbolChange"
        >
          <el-option
            v-for="symbol in quickSymbols"
            :key="symbol.code"
            :label="`${symbol.name} (${symbol.code})`"
            :value="symbol.code"
          >
            <div class="symbol-option">
              <span class="symbol-name">{{ symbol.name }}</span>
              <span class="symbol-price">{{ formatPrice(symbol.last_price) }}</span>
            </div>
          </el-option>
        </el-select>
      </div>

      <!-- 当前价格显示 -->
      <div v-if="currentSymbol" class="price-display">
        <div class="price-info">
          <span class="current-price" :class="priceChangeClass">
            {{ formatPrice(currentSymbol.last_price) }}
          </span>
          <span class="price-change" :class="priceChangeClass">
            {{ formatPriceChange(currentSymbol.change) }}
            ({{ formatPercent(currentSymbol.change_percent) }})
          </span>
        </div>
        <div class="bid-ask">
          <span class="bid">买: {{ formatPrice(currentSymbol.bid_price) }}</span>
          <span class="ask">卖: {{ formatPrice(currentSymbol.ask_price) }}</span>
        </div>
      </div>

      <!-- 数量设置 -->
      <div class="quantity-selector">
        <div class="quantity-buttons">
          <el-button
            v-for="qty in quickQuantities"
            :key="qty"
            :class="{ active: selectedQuantity === qty }"
            size="small"
            @click="selectedQuantity = qty"
          >
            {{ qty }}手
          </el-button>
        </div>
        <el-input-number
          v-model="customQuantity"
          :min="1"
          :max="1000"
          size="small"
          placeholder="自定义"
          @change="selectedQuantity = customQuantity"
        />
      </div>

      <!-- 交易按钮 -->
      <div class="trading-buttons">
        <div class="button-row">
          <el-button
            type="danger"
            class="buy-button"
            :disabled="!canTrade"
            :loading="buyLoading"
            @click="quickBuy"
          >
            买入 {{ selectedQuantity }}手
          </el-button>
          <el-button
            type="success"
            class="sell-button"
            :disabled="!canTrade"
            :loading="sellLoading"
            @click="quickSell"
          >
            卖出 {{ selectedQuantity }}手
          </el-button>
        </div>
        
        <!-- 一键平仓 -->
        <div class="close-buttons">
          <el-button
            type="warning"
            size="small"
            :disabled="!hasPosition"
            :loading="closeLoading"
            @click="closeAllPositions"
          >
            一键平仓
          </el-button>
          <el-button
            type="info"
            size="small"
            :disabled="!hasOrders"
            :loading="cancelLoading"
            @click="cancelAllOrders"
          >
            撤销全部
          </el-button>
        </div>
      </div>

      <!-- 持仓信息 -->
      <div v-if="currentPosition" class="position-info">
        <div class="position-header">
          <span>当前持仓</span>
          <span class="position-pnl" :class="currentPosition.unrealized_pnl >= 0 ? 'profit' : 'loss'">
            {{ formatCurrency(currentPosition.unrealized_pnl) }}
          </span>
        </div>
        <div class="position-details">
          <div class="detail-item">
            <span class="label">方向:</span>
            <span class="value" :class="currentPosition.side">
              {{ currentPosition.side === 'long' ? '多头' : '空头' }}
            </span>
          </div>
          <div class="detail-item">
            <span class="label">数量:</span>
            <span class="value">{{ currentPosition.quantity }}手</span>
          </div>
          <div class="detail-item">
            <span class="label">均价:</span>
            <span class="value">{{ formatPrice(currentPosition.avg_cost) }}</span>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 设置对话框 -->
    <el-dialog v-model="showSettings" title="快速交易设置" width="400px">
      <el-form :model="settings" label-width="120px">
        <el-form-item label="快速数量">
          <el-input
            v-model="settingsForm.quantities"
            placeholder="用逗号分隔，如: 1,5,10,20"
          />
        </el-form-item>
        
        <el-form-item label="确认模式">
          <el-radio-group v-model="settingsForm.confirmMode">
            <el-radio label="none">无确认</el-radio>
            <el-radio label="simple">简单确认</el-radio>
            <el-radio label="full">完整确认</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="默认订单类型">
          <el-select v-model="settingsForm.defaultOrderType">
            <el-option label="市价单" value="market" />
            <el-option label="限价单" value="limit" />
          </el-select>
        </el-form-item>
        
        <el-form-item>
          <el-checkbox v-model="settingsForm.autoRefresh">
            自动刷新价格
          </el-checkbox>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showSettings = false">取消</el-button>
        <el-button type="primary" @click="saveSettings">保存</el-button>
      </template>
    </el-dialog>

    <!-- 简单确认对话框 -->
    <el-dialog v-model="showSimpleConfirm" title="交易确认" width="300px">
      <div class="simple-confirm">
        <p>
          确认{{ pendingOrder?.side === 'buy' ? '买入' : '卖出' }}
          <strong>{{ pendingOrder?.quantity }}手</strong>
          <strong>{{ selectedSymbol }}</strong>？
        </p>
        <div class="confirm-info">
          <span>预估金额: {{ formatCurrency(estimatedCost) }}</span>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="showSimpleConfirm = false">取消</el-button>
        <el-button type="primary" @click="confirmQuickOrder" :loading="confirming">
          确认
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Setting } from '@element-plus/icons-vue'
import { useTradingStore } from '@/stores/trading'
import type { CreateOrderRequest, OrderSide } from '@/types/trading'

const tradingStore = useTradingStore()

// 响应式数据
const selectedSymbol = ref('')
const selectedQuantity = ref(1)
const customQuantity = ref(1)
const buyLoading = ref(false)
const sellLoading = ref(false)
const closeLoading = ref(false)
const cancelLoading = ref(false)
const confirming = ref(false)
const showSettings = ref(false)
const showSimpleConfirm = ref(false)

// 设置
const settings = ref({
  quantities: [1, 5, 10, 20],
  confirmMode: 'simple' as 'none' | 'simple' | 'full',
  defaultOrderType: 'market' as 'market' | 'limit',
  autoRefresh: true
})

const settingsForm = ref({
  quantities: '1,5,10,20',
  confirmMode: 'simple' as 'none' | 'simple' | 'full',
  defaultOrderType: 'market' as 'market' | 'limit',
  autoRefresh: true
})

// 待处理订单
const pendingOrder = ref<{
  side: OrderSide
  quantity: number
} | null>(null)

// 快速交易合约
const quickSymbols = ref([
  {
    code: 'SHFE.cu2401',
    name: '沪铜2401',
    last_price: 68500,
    change: 150,
    change_percent: 0.22,
    bid_price: 68490,
    ask_price: 68510,
    multiplier: 5,
    margin_ratio: 0.08
  },
  {
    code: 'DCE.i2401',
    name: '铁矿石2401',
    last_price: 850,
    change: -5,
    change_percent: -0.58,
    bid_price: 849.5,
    ask_price: 850.5,
    multiplier: 100,
    margin_ratio: 0.1
  }
])

// 计算属性
const quickQuantities = computed(() => settings.value.quantities)

const currentSymbol = computed(() => {
  return quickSymbols.value.find(s => s.code === selectedSymbol.value)
})

const currentPosition = computed(() => {
  return tradingStore.positions.find(p => p.symbol === selectedSymbol.value)
})

const canTrade = computed(() => {
  return selectedSymbol.value && selectedQuantity.value > 0
})

const hasPosition = computed(() => {
  return tradingStore.positions.some(p => p.quantity > 0)
})

const hasOrders = computed(() => {
  return tradingStore.orders.some(o => ['pending', 'submitted', 'partially_filled'].includes(o.status))
})

const priceChangeClass = computed(() => {
  if (!currentSymbol.value) return ''
  return currentSymbol.value.change >= 0 ? 'up' : 'down'
})

const estimatedCost = computed(() => {
  if (!currentSymbol.value || !selectedQuantity.value) return 0
  
  const price = currentSymbol.value.last_price
  const amount = price * selectedQuantity.value * currentSymbol.value.multiplier
  const margin = amount * currentSymbol.value.margin_ratio
  const fee = amount * 0.0001
  
  return margin + fee
})

// 方法
const onSymbolChange = () => {
  // 刷新价格数据
  refreshPriceData()
}

const refreshPriceData = async () => {
  if (!selectedSymbol.value) return
  
  try {
    // 获取最新价格
    // const response = await tradingApi.getMarketData(selectedSymbol.value)
    // 更新价格数据
  } catch (error) {
    console.error('刷新价格失败:', error)
  }
}

const quickBuy = async () => {
  if (settings.value.confirmMode === 'none') {
    await executeQuickOrder('buy')
  } else if (settings.value.confirmMode === 'simple') {
    pendingOrder.value = { side: 'buy', quantity: selectedQuantity.value }
    showSimpleConfirm.value = true
  } else {
    // 使用完整确认对话框
    await executeQuickOrder('buy')
  }
}

const quickSell = async () => {
  if (settings.value.confirmMode === 'none') {
    await executeQuickOrder('sell')
  } else if (settings.value.confirmMode === 'simple') {
    pendingOrder.value = { side: 'sell', quantity: selectedQuantity.value }
    showSimpleConfirm.value = true
  } else {
    // 使用完整确认对话框
    await executeQuickOrder('sell')
  }
}

const confirmQuickOrder = async () => {
  if (!pendingOrder.value) return
  
  try {
    confirming.value = true
    await executeQuickOrder(pendingOrder.value.side)
    showSimpleConfirm.value = false
    pendingOrder.value = null
  } finally {
    confirming.value = false
  }
}

const executeQuickOrder = async (side: OrderSide) => {
  if (!canTrade.value) return
  
  const loadingRef = side === 'buy' ? buyLoading : sellLoading
  
  try {
    loadingRef.value = true
    
    const orderRequest: CreateOrderRequest = {
      symbol: selectedSymbol.value,
      side,
      order_type: settings.value.defaultOrderType,
      quantity: selectedQuantity.value,
      time_in_force: 'day',
      risk_check: true
    }
    
    // 如果是限价单，使用对手价
    if (settings.value.defaultOrderType === 'limit') {
      orderRequest.price = side === 'buy' 
        ? currentSymbol.value?.ask_price 
        : currentSymbol.value?.bid_price
    }
    
    await tradingStore.createOrder(orderRequest)
    
    ElMessage.success(`${side === 'buy' ? '买入' : '卖出'}订单提交成功`)
  } catch (error: any) {
    ElMessage.error(error.message || '订单提交失败')
  } finally {
    loadingRef.value = false
  }
}

const closeAllPositions = async () => {
  try {
    await ElMessageBox.confirm('确定要平掉所有持仓吗？', '确认平仓', {
      type: 'warning'
    })
    
    closeLoading.value = true
    
    // 平掉所有持仓
    for (const position of tradingStore.positions) {
      if (position.quantity > 0) {
        const side: OrderSide = position.side === 'long' ? 'sell' : 'buy'
        
        const orderRequest: CreateOrderRequest = {
          symbol: position.symbol,
          side,
          order_type: 'market',
          quantity: position.quantity,
          time_in_force: 'ioc',
          risk_check: false
        }
        
        await tradingStore.createOrder(orderRequest)
      }
    }
    
    ElMessage.success('平仓订单已提交')
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('平仓失败')
    }
  } finally {
    closeLoading.value = false
  }
}

const cancelAllOrders = async () => {
  try {
    await ElMessageBox.confirm('确定要撤销所有未成交订单吗？', '确认撤销', {
      type: 'warning'
    })
    
    cancelLoading.value = true
    
    // 撤销所有未成交订单
    const activeOrders = tradingStore.orders.filter(o => 
      ['pending', 'submitted', 'partially_filled'].includes(o.status)
    )
    
    for (const order of activeOrders) {
      await tradingStore.cancelOrder(order.id)
    }
    
    ElMessage.success('撤销订单已提交')
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('撤销订单失败')
    }
  } finally {
    cancelLoading.value = false
  }
}

const saveSettings = () => {
  // 解析数量设置
  const quantities = settingsForm.value.quantities
    .split(',')
    .map(q => parseInt(q.trim()))
    .filter(q => !isNaN(q) && q > 0)
  
  if (quantities.length === 0) {
    ElMessage.error('请输入有效的快速数量')
    return
  }
  
  settings.value = {
    quantities,
    confirmMode: settingsForm.value.confirmMode,
    defaultOrderType: settingsForm.value.defaultOrderType,
    autoRefresh: settingsForm.value.autoRefresh
  }
  
  // 保存到本地存储
  localStorage.setItem('quickTradingSettings', JSON.stringify(settings.value))
  
  showSettings.value = false
  ElMessage.success('设置保存成功')
}

const loadSettings = () => {
  const saved = localStorage.getItem('quickTradingSettings')
  if (saved) {
    try {
      const parsed = JSON.parse(saved)
      settings.value = { ...settings.value, ...parsed }
      settingsForm.value.quantities = settings.value.quantities.join(',')
      settingsForm.value.confirmMode = settings.value.confirmMode
      settingsForm.value.defaultOrderType = settings.value.defaultOrderType
      settingsForm.value.autoRefresh = settings.value.autoRefresh
    } catch (error) {
      console.error('加载设置失败:', error)
    }
  }
}

// 格式化函数
const formatPrice = (price: number) => {
  return price?.toFixed(2) || '-'
}

const formatPriceChange = (change: number) => {
  const sign = change >= 0 ? '+' : ''
  return `${sign}${change.toFixed(2)}`
}

const formatPercent = (percent: number) => {
  const sign = percent >= 0 ? '+' : ''
  return `${sign}${percent.toFixed(2)}%`
}

const formatCurrency = (amount: number) => {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY'
  }).format(amount)
}

// 自动刷新价格
let refreshInterval: NodeJS.Timeout | null = null

const startAutoRefresh = () => {
  if (settings.value.autoRefresh && selectedSymbol.value) {
    refreshInterval = setInterval(refreshPriceData, 1000)
  }
}

const stopAutoRefresh = () => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
    refreshInterval = null
  }
}

// 监听器
watch(() => settings.value.autoRefresh, (newVal) => {
  if (newVal) {
    startAutoRefresh()
  } else {
    stopAutoRefresh()
  }
})

watch(selectedSymbol, () => {
  stopAutoRefresh()
  startAutoRefresh()
})

// 生命周期
onMounted(() => {
  loadSettings()
  
  // 默认选择第一个合约
  if (quickSymbols.value.length > 0) {
    selectedSymbol.value = quickSymbols.value[0].code
  }
  
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style 
scoped lang="scss">
.quick-trading-buttons {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .symbol-selector {
    margin-bottom: 16px;
    
    .symbol-option {
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      .symbol-name {
        font-weight: 600;
      }
      
      .symbol-price {
        font-weight: 600;
        color: #f56c6c;
      }
    }
  }
  
  .price-display {
    background: var(--el-bg-color-page);
    padding: 12px;
    border-radius: 6px;
    margin-bottom: 16px;
    
    .price-info {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 4px;
      
      .current-price {
        font-size: 18px;
        font-weight: 600;
        
        &.up {
          color: #f56c6c;
        }
        
        &.down {
          color: #67c23a;
        }
      }
      
      .price-change {
        font-size: 12px;
        
        &.up {
          color: #f56c6c;
        }
        
        &.down {
          color: #67c23a;
        }
      }
    }
    
    .bid-ask {
      display: flex;
      gap: 16px;
      font-size: 12px;
      color: #606266;
      
      .bid {
        color: #67c23a;
      }
      
      .ask {
        color: #f56c6c;
      }
    }
  }
  
  .quantity-selector {
    margin-bottom: 16px;
    
    .quantity-buttons {
      display: flex;
      gap: 8px;
      margin-bottom: 8px;
      
      .el-button {
        flex: 1;
        
        &.active {
          background-color: #409eff;
          border-color: #409eff;
          color: white;
        }
      }
    }
  }
  
  .trading-buttons {
    .button-row {
      display: flex;
      gap: 8px;
      margin-bottom: 8px;
      
      .buy-button {
        flex: 1;
        background-color: #f56c6c;
        border-color: #f56c6c;
        
        &:hover:not(:disabled) {
          background-color: #f78989;
          border-color: #f78989;
        }
      }
      
      .sell-button {
        flex: 1;
        background-color: #67c23a;
        border-color: #67c23a;
        
        &:hover:not(:disabled) {
          background-color: #85ce61;
          border-color: #85ce61;
        }
      }
    }
    
    .close-buttons {
      display: flex;
      gap: 8px;
      
      .el-button {
        flex: 1;
      }
    }
  }
  
  .position-info {
    margin-top: 16px;
    padding: 12px;
    background: var(--el-bg-color-page);
    border-radius: 6px;
    
    .position-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
      font-weight: 600;
      
      .position-pnl {
        &.profit {
          color: #f56c6c;
        }
        
        &.loss {
          color: #67c23a;
        }
      }
    }
    
    .position-details {
      display: flex;
      gap: 16px;
      
      .detail-item {
        display: flex;
        align-items: center;
        gap: 4px;
        font-size: 12px;
        
        .label {
          color: #909399;
        }
        
        .value {
          font-weight: 600;
          color: #303133;
          
          &.long {
            color: #f56c6c;
          }
          
          &.short {
            color: #67c23a;
          }
        }
      }
    }
  }
  
  .simple-confirm {
    text-align: center;
    
    p {
      margin-bottom: 16px;
      font-size: 16px;
    }
    
    .confirm-info {
      color: #606266;
      font-size: 14px;
    }
  }
}
</style>