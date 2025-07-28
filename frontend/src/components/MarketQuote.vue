<template>
  <div class="market-quote">
    <div class="quote-header">
      <div class="symbol-info">
        <span class="symbol">{{ symbol }}</span>
        <span class="symbol-name">{{ symbolName }}</span>
        <el-tag v-if="connected" type="success" size="small">实时</el-tag>
        <el-tag v-else type="danger" size="small">离线</el-tag>
      </div>
      
      <div class="quote-controls">
        <el-button 
          size="small" 
          :icon="autoUpdate ? 'VideoPause' : 'VideoPlay'"
          @click="toggleAutoUpdate"
        >
          {{ autoUpdate ? '暂停' : '开始' }}
        </el-button>
      </div>
    </div>
    
    <div class="quote-content">
      <!-- 主要价格信息 -->
      <div class="main-price">
        <div class="current-price" :class="getPriceClass(quote.last_price, quote.prev_close)">
          {{ formatPrice(quote.last_price) }}
        </div>
        <div class="price-change">
          <span class="change-amount" :class="getPriceClass(priceChange, 0)">
            {{ priceChange >= 0 ? '+' : '' }}{{ formatPrice(priceChange) }}
          </span>
          <span class="change-percent" :class="getPriceClass(priceChangePercent, 0)">
            ({{ priceChangePercent >= 0 ? '+' : '' }}{{ priceChangePercent.toFixed(2) }}%)
          </span>
        </div>
      </div>
      
      <!-- 详细行情信息 -->
      <div class="quote-details">
        <div class="detail-row">
          <div class="detail-item">
            <span class="label">开盘:</span>
            <span class="value" :class="getPriceClass(quote.open, quote.prev_close)">
              {{ formatPrice(quote.open) }}
            </span>
          </div>
          <div class="detail-item">
            <span class="label">最高:</span>
            <span class="value price-up">{{ formatPrice(quote.high) }}</span>
          </div>
          <div class="detail-item">
            <span class="label">最低:</span>
            <span class="value price-down">{{ formatPrice(quote.low) }}</span>
          </div>
        </div>
        
        <div class="detail-row">
          <div class="detail-item">
            <span class="label">成交量:</span>
            <span class="value">{{ formatVolume(quote.volume) }}</span>
          </div>
          <div class="detail-item">
            <span class="label">成交额:</span>
            <span class="value">{{ formatAmount(quote.amount) }}</span>
          </div>
          <div class="detail-item">
            <span class="label">持仓量:</span>
            <span class="value">{{ formatVolume(quote.open_interest) }}</span>
          </div>
        </div>
        
        <div class="detail-row">
          <div class="detail-item">
            <span class="label">昨收:</span>
            <span class="value">{{ formatPrice(quote.prev_close) }}</span>
          </div>
          <div class="detail-item">
            <span class="label">昨结:</span>
            <span class="value">{{ formatPrice(quote.prev_settlement) }}</span>
          </div>
          <div class="detail-item">
            <span class="label">更新:</span>
            <span class="value time">{{ formatTime(quote.update_time) }}</span>
          </div>
        </div>
      </div>
      
      <!-- 买卖盘口 -->
      <div v-if="showDepth" class="depth-panel">
        <div class="depth-header">
          <span>买卖盘口</span>
        </div>
        
        <div class="depth-content">
          <!-- 卖盘 -->
          <div class="sell-orders">
            <div 
              v-for="(item, index) in sellOrders" 
              :key="`sell-${index}`"
              class="depth-item sell"
            >
              <span class="price">{{ formatPrice(item.price) }}</span>
              <span class="volume">{{ item.volume }}</span>
            </div>
          </div>
          
          <!-- 分隔线 -->
          <div class="depth-separator">
            <span class="spread">价差: {{ formatPrice(spread) }}</span>
          </div>
          
          <!-- 买盘 -->
          <div class="buy-orders">
            <div 
              v-for="(item, index) in buyOrders" 
              :key="`buy-${index}`"
              class="depth-item buy"
            >
              <span class="price">{{ formatPrice(item.price) }}</span>
              <span class="volume">{{ item.volume }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useMarketWebSocket } from '@/utils/websocket'
import type { WebSocketMessage } from '@/utils/websocket'
import dayjs from 'dayjs'

interface Props {
  symbol: string
  symbolName?: string
  showDepth?: boolean
  autoStart?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  symbolName: '',
  showDepth: true,
  autoStart: true
})

const emit = defineEmits<{
  quoteUpdate: [quote: any]
  depthUpdate: [depth: any]
}>()

// 响应式数据
const autoUpdate = ref(props.autoStart)
const quote = ref({
  last_price: 0,
  open: 0,
  high: 0,
  low: 0,
  prev_close: 0,
  prev_settlement: 0,
  volume: 0,
  amount: 0,
  open_interest: 0,
  update_time: new Date().toISOString()
})

const buyOrders = ref([
  { price: 71990, volume: 10 },
  { price: 71980, volume: 15 },
  { price: 71970, volume: 8 },
  { price: 71960, volume: 12 },
  { price: 71950, volume: 20 }
])

const sellOrders = ref([
  { price: 72010, volume: 8 },
  { price: 72020, volume: 12 },
  { price: 72030, volume: 15 },
  { price: 72040, volume: 10 },
  { price: 72050, volume: 18 }
])

// WebSocket连接
const { ws, subscribeQuote, subscribeDepth } = useMarketWebSocket()
const connected = computed(() => ws.connected.value)

// 计算价格变化
const priceChange = computed(() => quote.value.last_price - quote.value.prev_close)
const priceChangePercent = computed(() => {
  if (quote.value.prev_close === 0) return 0
  return (priceChange.value / quote.value.prev_close) * 100
})

// 计算价差
const spread = computed(() => {
  if (sellOrders.value.length > 0 && buyOrders.value.length > 0) {
    return sellOrders.value[0].price - buyOrders.value[0].price
  }
  return 0
})

// 格式化价格
const formatPrice = (price: number) => {
  if (typeof price !== 'number' || price === 0) return '-'
  return new Intl.NumberFormat('zh-CN', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2
  }).format(price)
}

// 格式化成交量
const formatVolume = (volume: number) => {
  if (typeof volume !== 'number' || volume === 0) return '-'
  if (volume >= 10000) {
    return `${(volume / 10000).toFixed(1)}万`
  }
  return volume.toString()
}

// 格式化成交额
const formatAmount = (amount: number) => {
  if (typeof amount !== 'number' || amount === 0) return '-'
  if (amount >= 100000000) {
    return `${(amount / 100000000).toFixed(2)}亿`
  } else if (amount >= 10000) {
    return `${(amount / 10000).toFixed(1)}万`
  }
  return amount.toString()
}

// 格式化时间
const formatTime = (time: string) => {
  if (!time) return '-'
  return dayjs(time).format('HH:mm:ss')
}

// 获取价格样式类
const getPriceClass = (current: number, previous: number) => {
  if (typeof current !== 'number' || typeof previous !== 'number') return 'price-neutral'
  if (current > previous) return 'price-up'
  if (current < previous) return 'price-down'
  return 'price-neutral'
}

// 切换自动更新
const toggleAutoUpdate = () => {
  autoUpdate.value = !autoUpdate.value
  if (autoUpdate.value) {
    startRealTimeUpdate()
  } else {
    stopRealTimeUpdate()
  }
}

// 开始实时更新
const startRealTimeUpdate = () => {
  if (!ws.connected.value) {
    ws.connect()
  }
  
  // 订阅行情数据
  subscribeQuote(props.symbol)
  
  // 订阅深度数据
  if (props.showDepth) {
    subscribeDepth(props.symbol)
  }
}

// 停止实时更新
const stopRealTimeUpdate = () => {
  ws.unsubscribe('quote')
  ws.unsubscribe('depth')
}

// 处理WebSocket消息
const handleWebSocketMessage = (message: WebSocketMessage) => {
  if (!autoUpdate.value) return
  
  if (message.type === 'quote' && message.data.symbol === props.symbol) {
    quote.value = { ...quote.value, ...message.data }
    emit('quoteUpdate', message.data)
  } else if (message.type === 'depth' && message.data.symbol === props.symbol) {
    const depth = message.data
    buyOrders.value = depth.bids || []
    sellOrders.value = depth.asks || []
    emit('depthUpdate', depth)
  }
}

// 监听WebSocket消息
watch(() => ws.lastMessage.value, (message) => {
  if (message) {
    handleWebSocketMessage(message)
  }
})

// 生命周期
onMounted(() => {
  if (props.autoStart) {
    startRealTimeUpdate()
  }
  
  // 模拟初始数据
  quote.value = {
    last_price: 72000,
    open: 71800,
    high: 72200,
    low: 71600,
    prev_close: 71900,
    prev_settlement: 71850,
    volume: 125000,
    amount: 9000000000,
    open_interest: 85000,
    update_time: new Date().toISOString()
  }
})

onUnmounted(() => {
  stopRealTimeUpdate()
})
</script>

<style lang="scss" scoped>
.market-quote {
  border: 1px solid var(--el-border-color-light);
  border-radius: var(--el-border-radius-base);
  overflow: hidden;
  
  .quote-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    background: var(--el-bg-color-page);
    border-bottom: 1px solid var(--el-border-color-lighter);
    
    .symbol-info {
      display: flex;
      align-items: center;
      gap: 8px;
      
      .symbol {
        font-size: 16px;
        font-weight: 600;
        color: var(--el-text-color-primary);
      }
      
      .symbol-name {
        font-size: 14px;
        color: var(--el-text-color-secondary);
      }
    }
  }
  
  .quote-content {
    padding: 16px;
    
    .main-price {
      text-align: center;
      margin-bottom: 20px;
      
      .current-price {
        font-size: 32px;
        font-weight: bold;
        font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
        margin-bottom: 8px;
        
        &.price-up {
          color: var(--el-color-success);
        }
        
        &.price-down {
          color: var(--el-color-danger);
        }
        
        &.price-neutral {
          color: var(--el-text-color-primary);
        }
      }
      
      .price-change {
        display: flex;
        justify-content: center;
        gap: 8px;
        font-size: 14px;
        font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
        
        .change-amount,
        .change-percent {
          &.price-up {
            color: var(--el-color-success);
          }
          
          &.price-down {
            color: var(--el-color-danger);
          }
          
          &.price-neutral {
            color: var(--el-text-color-primary);
          }
        }
      }
    }
    
    .quote-details {
      margin-bottom: 20px;
      
      .detail-row {
        display: flex;
        justify-content: space-between;
        margin-bottom: 8px;
        
        .detail-item {
          display: flex;
          flex-direction: column;
          align-items: center;
          flex: 1;
          
          .label {
            font-size: 12px;
            color: var(--el-text-color-secondary);
            margin-bottom: 4px;
          }
          
          .value {
            font-size: 14px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            color: var(--el-text-color-primary);
            
            &.price-up {
              color: var(--el-color-success);
            }
            
            &.price-down {
              color: var(--el-color-danger);
            }
            
            &.time {
              font-size: 12px;
              color: var(--el-text-color-secondary);
            }
          }
        }
      }
    }
    
    .depth-panel {
      .depth-header {
        text-align: center;
        font-weight: 500;
        color: var(--el-text-color-primary);
        margin-bottom: 12px;
        padding-bottom: 8px;
        border-bottom: 1px solid var(--el-border-color-lighter);
      }
      
      .depth-content {
        .sell-orders,
        .buy-orders {
          .depth-item {
            display: flex;
            justify-content: space-between;
            padding: 4px 8px;
            font-size: 12px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            
            &.sell {
              background: rgba(239, 68, 68, 0.1);
              color: var(--el-color-danger);
            }
            
            &.buy {
              background: rgba(34, 197, 94, 0.1);
              color: var(--el-color-success);
            }
          }
        }
        
        .depth-separator {
          text-align: center;
          padding: 8px;
          margin: 8px 0;
          background: var(--el-bg-color-page);
          border: 1px solid var(--el-border-color-lighter);
          border-radius: 4px;
          
          .spread {
            font-size: 12px;
            color: var(--el-text-color-secondary);
          }
        }
      }
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .market-quote {
    .quote-content {
      padding: 12px;
      
      .main-price {
        .current-price {
          font-size: 24px;
        }
      }
      
      .quote-details {
        .detail-row {
          .detail-item {
            .label {
              font-size: 11px;
            }
            
            .value {
              font-size: 12px;
            }
          }
        }
      }
    }
  }
}
</style>