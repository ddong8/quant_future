<template>
  <div class="technical-chart">
    <!-- 图表工具栏 -->
    <div class="chart-toolbar">
      <div class="toolbar-left">
        <el-select v-model="selectedSymbol" placeholder="选择标的" style="width: 150px" @change="handleSymbolChange">
          <el-option
            v-for="symbol in availableSymbols"
            :key="symbol.value"
            :label="symbol.label"
            :value="symbol.value"
          />
        </el-select>
        
        <el-select v-model="selectedInterval" placeholder="时间周期" style="width: 100px; margin-left: 12px" @change="handleIntervalChange">
          <el-option label="1分钟" value="1m" />
          <el-option label="5分钟" value="5m" />
          <el-option label="15分钟" value="15m" />
          <el-option label="1小时" value="1h" />
          <el-option label="1天" value="1d" />
          <el-option label="1周" value="1w" />
        </el-select>
      </div>
      
      <div class="toolbar-right">
        <el-button-group>
          <el-button 
            :type="chartType === 'candlestick' ? 'primary' : 'default'"
            size="small"
            @click="setChartType('candlestick')"
          >
            K线图
          </el-button>
          <el-button 
            :type="chartType === 'line' ? 'primary' : 'default'"
            size="small"
            @click="setChartType('line')"
          >
            分时图
          </el-button>
        </el-button-group>
        
        <el-dropdown @command="handleIndicatorCommand" style="margin-left: 12px">
          <el-button size="small">
            技术指标 <el-icon><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="ma">移动平均线</el-dropdown-item>
              <el-dropdown-item command="bollinger">布林带</el-dropdown-item>
              <el-dropdown-item command="rsi">RSI</el-dropdown-item>
              <el-dropdown-item command="macd">MACD</el-dropdown-item>
              <el-dropdown-item command="kdj">KDJ</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        
        <el-button size="small" @click="showConfigDialog = true" style="margin-left: 12px">
          <el-icon><Setting /></el-icon>
          配置
        </el-button>
        
        <el-button size="small" @click="refreshChart" :loading="loading" style="margin-left: 12px">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>
    
    <!-- 主图表容器 -->
    <div class="chart-container">
      <div ref="mainChartRef" class="main-chart" :style="{ height: mainChartHeight + 'px' }"></div>
      
      <!-- 副图表容器 -->
      <div v-if="subCharts.length > 0" class="sub-charts">
        <div
          v-for="(subChart, index) in subCharts"
          :key="subChart.id"
          :ref="el => setSubChartRef(el, index)"
          class="sub-chart"
          :style="{ height: subChartHeight + 'px' }"
        ></div>
      </div>
    </div>
    
    <!-- 图表配置对话框 -->
    <ChartConfigDialog 
      v-model="showConfigDialog"
      :current-config="chartConfig"
      @save="handleConfigSave"
    />
    
    <!-- 指标参数设置对话框 -->
    <IndicatorParamsDialog
      v-model="showIndicatorDialog"
      :indicator-type="currentIndicator"
      @confirm="handleIndicatorConfirm"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { ArrowDown, Setting, Refresh } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import type { ECharts } from 'echarts'
import { getTechnicalIndicators, type KlineData, type TechnicalIndicators } from '@/api/technicalAnalysis'
import ChartConfigDialog from './ChartConfigDialog.vue'
import IndicatorParamsDialog from './IndicatorParamsDialog.vue'

interface Props {
  symbol?: string
  height?: number
}

interface SubChart {
  id: string
  type: string
  title: string
  instance?: ECharts
}

const props = withDefaults(defineProps<Props>(), {
  symbol: 'AAPL',
  height: 600
})

// 响应式数据
const selectedSymbol = ref(props.symbol)
const selectedInterval = ref('1d')
const chartType = ref<'candlestick' | 'line'>('candlestick')
const loading = ref(false)
const showConfigDialog = ref(false)
const showIndicatorDialog = ref(false)
const currentIndicator = ref('')

// 图表实例
const mainChartRef = ref<HTMLElement>()
const subChartRefs = ref<HTMLElement[]>([])
let mainChart: ECharts | null = null
const subCharts = ref<SubChart[]>([])

// 图表配置
const chartConfig = ref({
  indicators: ['ma5', 'ma10', 'ma20'],
  theme: 'light',
  showVolume: true,
  showGrid: true
})

// 图表尺寸
const mainChartHeight = ref(400)
const subChartHeight = ref(150)

// 可用标的列表
const availableSymbols = ref([
  { label: 'AAPL', value: 'AAPL' },
  { label: 'GOOGL', value: 'GOOGL' },
  { label: 'MSFT', value: 'MSFT' },
  { label: 'TSLA', value: 'TSLA' },
  { label: 'AMZN', value: 'AMZN' }
])

// 图表数据
const chartData = ref<TechnicalIndicators | null>(null)

// 设置副图表引用
const setSubChartRef = (el: HTMLElement | null, index: number) => {
  if (el) {
    subChartRefs.value[index] = el
  }
}

// 初始化主图表
const initMainChart = () => {
  if (!mainChartRef.value) return
  
  mainChart = echarts.init(mainChartRef.value)
  
  // 设置图表配置
  const option = getMainChartOption()
  mainChart.setOption(option)
  
  // 添加事件监听
  mainChart.on('datazoom', handleDataZoom)
  mainChart.on('brush', handleBrush)
}

// 获取主图表配置
const getMainChartOption = () => {
  if (!chartData.value) return {}
  
  const { kline_data, indicators } = chartData.value
  
  // 准备数据
  const dates = kline_data.map(item => new Date(item.timestamp).toLocaleString())
  const ohlcData = kline_data.map(item => [item.open, item.close, item.low, item.high])
  const volumeData = kline_data.map(item => item.volume)
  
  const series: any[] = []
  
  // K线图或分时图
  if (chartType.value === 'candlestick') {
    series.push({
      name: 'K线',
      type: 'candlestick',
      data: ohlcData,
      itemStyle: {
        color: '#ef232a',
        color0: '#14b143',
        borderColor: '#ef232a',
        borderColor0: '#14b143'
      }
    })
  } else {
    const lineData = kline_data.map(item => item.close)
    series.push({
      name: '价格',
      type: 'line',
      data: lineData,
      smooth: true,
      lineStyle: {
        color: '#409eff'
      }
    })
  }
  
  // 添加移动平均线
  if (indicators.ma5) {
    series.push({
      name: 'MA5',
      type: 'line',
      data: indicators.ma5,
      smooth: true,
      lineStyle: { color: '#ff6b6b', width: 1 },
      showSymbol: false
    })
  }
  
  if (indicators.ma10) {
    series.push({
      name: 'MA10',
      type: 'line',
      data: indicators.ma10,
      smooth: true,
      lineStyle: { color: '#4ecdc4', width: 1 },
      showSymbol: false
    })
  }
  
  if (indicators.ma20) {
    series.push({
      name: 'MA20',
      type: 'line',
      data: indicators.ma20,
      smooth: true,
      lineStyle: { color: '#45b7d1', width: 1 },
      showSymbol: false
    })
  }
  
  // 添加布林带
  if (indicators.bollinger) {
    const { upper, middle, lower } = indicators.bollinger
    series.push(
      {
        name: '布林上轨',
        type: 'line',
        data: upper,
        lineStyle: { color: '#ff9f43', width: 1, type: 'dashed' },
        showSymbol: false
      },
      {
        name: '布林中轨',
        type: 'line',
        data: middle,
        lineStyle: { color: '#feca57', width: 1 },
        showSymbol: false
      },
      {
        name: '布林下轨',
        type: 'line',
        data: lower,
        lineStyle: { color: '#ff9f43', width: 1, type: 'dashed' },
        showSymbol: false
      }
    )
  }
  
  // 成交量
  if (chartConfig.value.showVolume) {
    series.push({
      name: '成交量',
      type: 'bar',
      yAxisIndex: 1,
      data: volumeData,
      itemStyle: {
        color: function(params: any) {
          const dataIndex = params.dataIndex
          if (dataIndex === 0) return '#14b143'
          const current = kline_data[dataIndex]
          const previous = kline_data[dataIndex - 1]
          return current.close >= previous.close ? '#ef232a' : '#14b143'
        }
      }
    })
  }
  
  return {
    animation: false,
    legend: {
      data: series.map(s => s.name),
      top: 10
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      },
      formatter: function(params: any) {
        let result = `${dates[params[0].dataIndex]}<br/>`
        params.forEach((param: any) => {
          if (param.seriesName === 'K线') {
            const data = param.data
            result += `开盘: ${data[0]}<br/>收盘: ${data[1]}<br/>最低: ${data[2]}<br/>最高: ${data[3]}<br/>`
          } else {
            result += `${param.seriesName}: ${param.data}<br/>`
          }
        })
        return result
      }
    },
    axisPointer: {
      link: { xAxisIndex: 'all' },
      label: {
        backgroundColor: '#777'
      }
    },
    toolbox: {
      feature: {
        dataZoom: {
          yAxisIndex: false
        },
        brush: {
          type: ['lineX', 'clear']
        }
      }
    },
    brush: {
      xAxisIndex: 'all',
      brushLink: 'all',
      outOfBrush: {
        colorAlpha: 0.1
      }
    },
    grid: [
      {
        left: '10%',
        right: '8%',
        height: chartConfig.value.showVolume ? '50%' : '70%'
      },
      {
        left: '10%',
        right: '8%',
        top: '70%',
        height: '16%'
      }
    ],
    xAxis: [
      {
        type: 'category',
        data: dates,
        scale: true,
        boundaryGap: false,
        axisLine: { onZero: false },
        splitLine: { show: false },
        min: 'dataMin',
        max: 'dataMax'
      },
      {
        type: 'category',
        gridIndex: 1,
        data: dates,
        scale: true,
        boundaryGap: false,
        axisLine: { onZero: false },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: { show: false },
        min: 'dataMin',
        max: 'dataMax'
      }
    ],
    yAxis: [
      {
        scale: true,
        splitArea: {
          show: true
        }
      },
      {
        scale: true,
        gridIndex: 1,
        splitNumber: 2,
        axisLabel: { show: false },
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { show: false }
      }
    ],
    dataZoom: [
      {
        type: 'inside',
        xAxisIndex: [0, 1],
        start: 80,
        end: 100
      },
      {
        show: true,
        xAxisIndex: [0, 1],
        type: 'slider',
        top: '85%',
        start: 80,
        end: 100
      }
    ],
    series
  }
}

// 初始化副图表
const initSubChart = (index: number, type: string) => {
  const element = subChartRefs.value[index]
  if (!element || !chartData.value) return
  
  const chart = echarts.init(element)
  subCharts.value[index].instance = chart
  
  let option = {}
  
  if (type === 'rsi') {
    option = getRSIChartOption()
  } else if (type === 'macd') {
    option = getMACDChartOption()
  } else if (type === 'kdj') {
    option = getKDJChartOption()
  }
  
  chart.setOption(option)
}

// 获取RSI图表配置
const getRSIChartOption = () => {
  if (!chartData.value?.indicators.rsi) return {}
  
  const dates = chartData.value.kline_data.map(item => new Date(item.timestamp).toLocaleString())
  
  return {
    title: {
      text: 'RSI',
      left: 0,
      textStyle: { fontSize: 12 }
    },
    grid: {
      left: '10%',
      right: '8%',
      top: '15%',
      bottom: '15%'
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLabel: { show: false }
    },
    yAxis: {
      type: 'value',
      scale: true,
      min: 0,
      max: 100,
      splitLine: {
        lineStyle: { type: 'dashed' }
      }
    },
    series: [
      {
        name: 'RSI',
        type: 'line',
        data: chartData.value.indicators.rsi,
        smooth: true,
        lineStyle: { color: '#ff6b6b' },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(255, 107, 107, 0.3)' },
              { offset: 1, color: 'rgba(255, 107, 107, 0.1)' }
            ]
          }
        }
      }
    ],
    tooltip: {
      trigger: 'axis',
      formatter: function(params: any) {
        return `${dates[params[0].dataIndex]}<br/>RSI: ${params[0].data}`
      }
    }
  }
}

// 获取MACD图表配置
const getMACDChartOption = () => {
  if (!chartData.value?.indicators.macd) return {}
  
  const dates = chartData.value.kline_data.map(item => new Date(item.timestamp).toLocaleString())
  const { macd, signal, histogram } = chartData.value.indicators.macd
  
  return {
    title: {
      text: 'MACD',
      left: 0,
      textStyle: { fontSize: 12 }
    },
    legend: {
      data: ['MACD', 'Signal', 'Histogram'],
      top: 0,
      right: 0,
      textStyle: { fontSize: 10 }
    },
    grid: {
      left: '10%',
      right: '8%',
      top: '20%',
      bottom: '15%'
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLabel: { show: false }
    },
    yAxis: {
      type: 'value',
      scale: true,
      splitLine: {
        lineStyle: { type: 'dashed' }
      }
    },
    series: [
      {
        name: 'MACD',
        type: 'line',
        data: macd,
        smooth: true,
        lineStyle: { color: '#409eff', width: 1 },
        showSymbol: false
      },
      {
        name: 'Signal',
        type: 'line',
        data: signal,
        smooth: true,
        lineStyle: { color: '#ff6b6b', width: 1 },
        showSymbol: false
      },
      {
        name: 'Histogram',
        type: 'bar',
        data: histogram,
        itemStyle: {
          color: function(params: any) {
            return params.data >= 0 ? '#ef232a' : '#14b143'
          }
        }
      }
    ],
    tooltip: {
      trigger: 'axis',
      formatter: function(params: any) {
        let result = `${dates[params[0].dataIndex]}<br/>`
        params.forEach((param: any) => {
          result += `${param.seriesName}: ${param.data}<br/>`
        })
        return result
      }
    }
  }
}

// 获取KDJ图表配置
const getKDJChartOption = () => {
  if (!chartData.value?.indicators.kdj) return {}
  
  const dates = chartData.value.kline_data.map(item => new Date(item.timestamp).toLocaleString())
  const { k, d, j } = chartData.value.indicators.kdj
  
  return {
    title: {
      text: 'KDJ',
      left: 0,
      textStyle: { fontSize: 12 }
    },
    legend: {
      data: ['K', 'D', 'J'],
      top: 0,
      right: 0,
      textStyle: { fontSize: 10 }
    },
    grid: {
      left: '10%',
      right: '8%',
      top: '20%',
      bottom: '15%'
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLabel: { show: false }
    },
    yAxis: {
      type: 'value',
      scale: true,
      min: 0,
      max: 100,
      splitLine: {
        lineStyle: { type: 'dashed' }
      }
    },
    series: [
      {
        name: 'K',
        type: 'line',
        data: k,
        smooth: true,
        lineStyle: { color: '#409eff', width: 1 },
        showSymbol: false
      },
      {
        name: 'D',
        type: 'line',
        data: d,
        smooth: true,
        lineStyle: { color: '#ff6b6b', width: 1 },
        showSymbol: false
      },
      {
        name: 'J',
        type: 'line',
        data: j,
        smooth: true,
        lineStyle: { color: '#67c23a', width: 1 },
        showSymbol: false
      }
    ],
    tooltip: {
      trigger: 'axis',
      formatter: function(params: any) {
        let result = `${dates[params[0].dataIndex]}<br/>`
        params.forEach((param: any) => {
          result += `${param.seriesName}: ${param.data}<br/>`
        })
        return result
      }
    }
  }
}

// 加载图表数据
const loadChartData = async () => {
  try {
    loading.value = true
    
    const response = await getTechnicalIndicators(
      selectedSymbol.value,
      selectedInterval.value,
      chartConfig.value.indicators,
      500
    )
    
    chartData.value = response.data
    
    // 更新图表
    await nextTick()
    updateCharts()
    
  } catch (error) {
    console.error('加载图表数据失败:', error)
    ElMessage.error('加载图表数据失败')
  } finally {
    loading.value = false
  }
}

// 更新图表
const updateCharts = () => {
  // 更新主图表
  if (mainChart && chartData.value) {
    const option = getMainChartOption()
    mainChart.setOption(option, true)
  }
  
  // 更新副图表
  subCharts.value.forEach((subChart, index) => {
    if (subChart.instance) {
      let option = {}
      if (subChart.type === 'rsi') {
        option = getRSIChartOption()
      } else if (subChart.type === 'macd') {
        option = getMACDChartOption()
      } else if (subChart.type === 'kdj') {
        option = getKDJChartOption()
      }
      subChart.instance.setOption(option, true)
    }
  })
}

// 事件处理
const handleSymbolChange = () => {
  loadChartData()
}

const handleIntervalChange = () => {
  loadChartData()
}

const setChartType = (type: 'candlestick' | 'line') => {
  chartType.value = type
  updateCharts()
}

const handleIndicatorCommand = (command: string) => {
  currentIndicator.value = command
  showIndicatorDialog.value = true
}

const handleIndicatorConfirm = (params: any) => {
  // 根据指标类型添加副图表
  if (currentIndicator.value === 'rsi' || currentIndicator.value === 'macd' || currentIndicator.value === 'kdj') {
    const existingIndex = subCharts.value.findIndex(chart => chart.type === currentIndicator.value)
    if (existingIndex === -1) {
      subCharts.value.push({
        id: `${currentIndicator.value}_${Date.now()}`,
        type: currentIndicator.value,
        title: currentIndicator.value.toUpperCase()
      })
    }
  } else {
    // 主图指标
    if (!chartConfig.value.indicators.includes(currentIndicator.value)) {
      chartConfig.value.indicators.push(currentIndicator.value)
    }
  }
  
  loadChartData()
}

const handleConfigSave = (config: any) => {
  chartConfig.value = { ...config }
  loadChartData()
}

const refreshChart = () => {
  loadChartData()
}

const handleDataZoom = (params: any) => {
  // 同步所有图表的缩放
  subCharts.value.forEach(subChart => {
    if (subChart.instance) {
      subChart.instance.dispatchAction({
        type: 'dataZoom',
        ...params
      })
    }
  })
}

const handleBrush = (params: any) => {
  // 处理刷选事件
  console.log('Brush event:', params)
}

// 窗口大小调整
const handleResize = () => {
  mainChart?.resize()
  subCharts.value.forEach(subChart => {
    subChart.instance?.resize()
  })
}

// 监听副图表变化
watch(() => subCharts.value.length, async (newLength, oldLength) => {
  if (newLength > oldLength) {
    await nextTick()
    // 初始化新添加的副图表
    for (let i = oldLength; i < newLength; i++) {
      initSubChart(i, subCharts.value[i].type)
    }
  }
})

// 组件挂载
onMounted(() => {
  initMainChart()
  loadChartData()
  window.addEventListener('resize', handleResize)
})

// 组件卸载
onUnmounted(() => {
  mainChart?.dispose()
  subCharts.value.forEach(subChart => {
    subChart.instance?.dispose()
  })
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.technical-chart {
  width: 100%;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.chart-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #e4e7ed;
}

.toolbar-left {
  display: flex;
  align-items: center;
}

.toolbar-right {
  display: flex;
  align-items: center;
}

.chart-container {
  padding: 16px;
}

.main-chart {
  width: 100%;
  border-bottom: 1px solid #e4e7ed;
}

.sub-charts {
  margin-top: 16px;
}

.sub-chart {
  width: 100%;
  margin-bottom: 16px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
}

.sub-chart:last-child {
  margin-bottom: 0;
}
</style>