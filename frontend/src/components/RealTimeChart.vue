<template>
  <div class="realtime-chart">
    <div class="chart-header">
      <div class="chart-title">
        <span>{{ title }}</span>
        <el-tag v-if="connected" type="success" size="small">实时</el-tag>
        <el-tag v-else type="danger" size="small">离线</el-tag>
      </div>
      
      <div class="chart-controls">
        <el-button-group size="small">
          <el-button 
            v-for="interval in intervals"
            :key="interval.value"
            :type="currentInterval === interval.value ? 'primary' : ''"
            @click="changeInterval(interval.value)"
          >
            {{ interval.label }}
          </el-button>
        </el-button-group>
        
        <el-button 
          size="small" 
          :icon="autoUpdate ? 'VideoPause' : 'VideoPlay'"
          @click="toggleAutoUpdate"
        >
          {{ autoUpdate ? '暂停' : '开始' }}
        </el-button>
      </div>
    </div>
    
    <div class="chart-container">
      <v-chart 
        :option="chartOption" 
        :loading="loading"
        :style="{ height: `${height}px` }"
        @click="handleChartClick"
      />
    </div>
    
    <div v-if="showStats" class="chart-stats">
      <div class="stat-item">
        <span class="stat-label">最新价:</span>
        <span class="stat-value" :class="getPriceClass(latestPrice, previousPrice)">
          {{ formatPrice(latestPrice) }}
        </span>
      </div>
      <div class="stat-item">
        <span class="stat-label">涨跌:</span>
        <span class="stat-value" :class="getPriceClass(priceChange, 0)">
          {{ priceChange >= 0 ? '+' : '' }}{{ formatPrice(priceChange) }}
        </span>
      </div>
      <div class="stat-item">
        <span class="stat-label">涨跌幅:</span>
        <span class="stat-value" :class="getPriceClass(priceChangePercent, 0)">
          {{ priceChangePercent >= 0 ? '+' : '' }}{{ priceChangePercent.toFixed(2) }}%
        </span>
      </div>
      <div class="stat-item">
        <span class="stat-label">成交量:</span>
        <span class="stat-value">{{ formatVolume(volume) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, CandlestickChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DataZoomComponent,
  ToolboxComponent
} from 'echarts/components'
import VChart from 'vue-echarts'
import { useMarketWebSocket } from '@/utils/websocket'
import type { WebSocketMessage } from '@/utils/websocket'

// 注册ECharts组件
use([
  CanvasRenderer,
  LineChart,
  CandlestickChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DataZoomComponent,
  ToolboxComponent
])

interface Props {
  symbol: string
  title?: string
  chartType?: 'line' | 'candlestick'
  height?: number
  showStats?: boolean
  autoStart?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  title: '实时图表',
  chartType: 'line',
  height: 400,
  showStats: true,
  autoStart: true
})

const emit = defineEmits<{
  dataUpdate: [data: any]
  click: [params: any]
}>()

// 响应式数据
const loading = ref(false)
const autoUpdate = ref(props.autoStart)
const currentInterval = ref('1m')
const chartData = ref<any[]>([])
const latestPrice = ref(0)
const previousPrice = ref(0)
const volume = ref(0)

// WebSocket连接
const { ws, subscribeQuote, subscribeKline } = useMarketWebSocket()
const connected = computed(() => ws.connected.value)

// 时间间隔选项
const intervals = [
  { label: '1分', value: '1m' },
  { label: '5分', value: '5m' },
  { label: '15分', value: '15m' },
  { label: '1小时', value: '1h' },
  { label: '1天', value: '1d' }
]

// 计算涨跌
const priceChange = computed(() => latestPrice.value - previousPrice.value)
const priceChangePercent = computed(() => {
  if (previousPrice.value === 0) return 0
  return (priceChange.value / previousPrice.value) * 100
})

// 图表配置
const chartOption = computed(() => {
  const baseOption = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: chartData.value.map(item => item.time),
      axisLine: {
        lineStyle: {
          color: 'var(--el-text-color-secondary)'
        }
      }
    },
    yAxis: {
      type: 'value',
      scale: true,
      axisLine: {
        lineStyle: {
          color: 'var(--el-text-color-secondary)'
        }
      },
      axisLabel: {
        formatter: (value: number) => formatPrice(value)
      }
    },
    dataZoom: [
      {
        type: 'inside',
        start: 80,
        end: 100
      },
      {
        show: true,
        type: 'slider',
        top: '90%',
        start: 80,
        end: 100
      }
    ],
    toolbox: {
      feature: {
        dataZoom: {
          yAxisIndex: 'none'
        },
        restore: {},
        saveAsImage: {}
      }
    }
  }

  if (props.chartType === 'candlestick') {
    return {
      ...baseOption,
      series: [
        {
          name: '价格',
          type: 'candlestick',
          data: chartData.value.map(item => [
            item.open,
            item.close,
            item.low,
            item.high
          ]),
          itemStyle: {
            color: '#ef4444',
            color0: '#22c55e',
            borderColor: '#ef4444',
            borderColor0: '#22c55e'
          }
        },
        {
          name: '成交量',
          type: 'bar',
          yAxisIndex: 1,
          data: chartData.value.map(item => item.volume),
          itemStyle: {
            color: 'rgba(64, 158, 255, 0.3)'
          }
        }
      ],
      yAxis: [
        baseOption.yAxis,
        {
          type: 'value',
          scale: true,
          axisLine: { show: false },
          axisTick: { show: false },
          axisLabel: { show: false },
          splitLine: { show: false }
        }
      ]
    }
  } else {
    return {
      ...baseOption,
      series: [
        {
          name: '价格',
          type: 'line',
          data: chartData.value.map(item => item.price || item.close),
          smooth: true,
          symbol: 'none',
          lineStyle: {
            color: '#409EFF',
            width: 2
          },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
                { offset: 1, color: 'rgba(64, 158, 255, 0.1)' }
              ]
            }
          }
        }
      ]
    }
  }
})

// 格式化价格
const formatPrice = (price: number) => {
  return new Intl.NumberFormat('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(price)
}

// 格式化成交量
const formatVolume = (vol: number) => {
  if (vol >= 10000) {
    return `${(vol / 10000).toFixed(1)}万`
  }
  return vol.toString()
}

// 获取价格样式类
const getPriceClass = (current: number, previous: number) => {
  if (current > previous) return 'price-up'
  if (current < previous) return 'price-down'
  return 'price-neutral'
}

// 切换时间间隔
const changeInterval = (interval: string) => {
  currentInterval.value = interval
  if (autoUpdate.value) {
    startRealTimeUpdate()
  }
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
  
  // 订阅数据
  if (props.chartType === 'candlestick') {
    subscribeKline(props.symbol, currentInterval.value)
  } else {
    subscribeQuote(props.symbol)
  }
}

// 停止实时更新
const stopRealTimeUpdate = () => {
  // 取消订阅
  ws.unsubscribe('quote')
  ws.unsubscribe('kline')
}

// 处理WebSocket消息
const handleWebSocketMessage = (message: WebSocketMessage) => {
  if (message.type === 'quote' && message.data.symbol === props.symbol) {
    // 处理实时报价
    const quote = message.data
    previousPrice.value = latestPrice.value
    latestPrice.value = quote.last_price
    volume.value = quote.volume
    
    // 更新图表数据
    if (props.chartType === 'line') {
      const newData = {
        time: new Date().toLocaleTimeString(),
        price: quote.last_price
      }
      
      chartData.value.push(newData)
      
      // 保持数据量在合理范围
      if (chartData.value.length > 100) {
        chartData.value.shift()
      }
    }
    
    emit('dataUpdate', quote)
  } else if (message.type === 'kline' && message.data.symbol === props.symbol) {
    // 处理K线数据
    const kline = message.data
    
    const newData = {
      time: new Date(kline.timestamp).toLocaleTimeString(),
      open: kline.open,
      high: kline.high,
      low: kline.low,
      close: kline.close,
      volume: kline.volume
    }
    
    // 更新或添加K线数据
    const lastIndex = chartData.value.length - 1
    if (lastIndex >= 0 && chartData.value[lastIndex].time === newData.time) {
      chartData.value[lastIndex] = newData
    } else {
      chartData.value.push(newData)
    }
    
    // 更新价格信息
    previousPrice.value = latestPrice.value
    latestPrice.value = kline.close
    volume.value = kline.volume
    
    emit('dataUpdate', kline)
  }
}

// 处理图表点击
const handleChartClick = (params: any) => {
  emit('click', params)
}

// 监听WebSocket消息
watch(() => ws.lastMessage.value, (message) => {
  if (message && autoUpdate.value) {
    handleWebSocketMessage(message)
  }
})

// 生命周期
onMounted(() => {
  if (props.autoStart) {
    startRealTimeUpdate()
  }
})

onUnmounted(() => {
  stopRealTimeUpdate()
})
</script>

<style lang="scss" scoped>
.realtime-chart {
  border: 1px solid var(--el-border-color-light);
  border-radius: var(--el-border-radius-base);
  overflow: hidden;
  
  .chart-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    background: var(--el-bg-color-page);
    border-bottom: 1px solid var(--el-border-color-lighter);
    
    .chart-title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: 500;
      color: var(--el-text-color-primary);
    }
    
    .chart-controls {
      display: flex;
      align-items: center;
      gap: 12px;
    }
  }
  
  .chart-container {
    background: var(--el-bg-color);
  }
  
  .chart-stats {
    display: flex;
    justify-content: space-around;
    padding: 12px 16px;
    background: var(--el-bg-color-page);
    border-top: 1px solid var(--el-border-color-lighter);
    
    .stat-item {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 4px;
      
      .stat-label {
        font-size: 12px;
        color: var(--el-text-color-secondary);
      }
      
      .stat-value {
        font-size: 14px;
        font-weight: 600;
        font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
        
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
}

// 响应式设计
@media (max-width: 768px) {
  .realtime-chart {
    .chart-header {
      flex-direction: column;
      gap: 12px;
      align-items: stretch;
      
      .chart-controls {
        justify-content: center;
      }
    }
    
    .chart-stats {
      flex-wrap: wrap;
      gap: 12px;
      
      .stat-item {
        flex: 1;
        min-width: 80px;
      }
    }
  }
}
</style>