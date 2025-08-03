<template>
  <div class="base-chart">
    <div
      ref="chartRef"
      :style="{ width: width, height: height }"
      class="chart-container"
    />
    
    <!-- 加载状态 -->
    <div v-if="loading" class="chart-loading">
      <el-loading :text="loadingText" />
    </div>
    
    <!-- 空数据状态 -->
    <div v-if="!loading && isEmpty" class="chart-empty">
      <el-empty :description="emptyText" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick, computed } from 'vue'
import * as echarts from 'echarts'
import { ElLoading, ElEmpty } from 'element-plus'

// 类型定义
interface Props {
  option: any
  width?: string
  height?: string
  loading?: boolean
  loadingText?: string
  emptyText?: string
  theme?: string
  autoResize?: boolean
  notMerge?: boolean
  lazyUpdate?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  width: '100%',
  height: '400px',
  loading: false,
  loadingText: '加载中...',
  emptyText: '暂无数据',
  theme: 'default',
  autoResize: true,
  notMerge: false,
  lazyUpdate: false
})

// 事件定义
const emit = defineEmits<{
  'chart-ready': [chart: echarts.ECharts]
  'chart-click': [params: any]
  'chart-dblclick': [params: any]
  'chart-mouseover': [params: any]
  'chart-mouseout': [params: any]
  'chart-selectchanged': [params: any]
}>()

// 响应式数据
const chartRef = ref<HTMLDivElement>()
let chartInstance: echarts.ECharts | null = null
let resizeObserver: ResizeObserver | null = null

// 计算属性
const isEmpty = computed(() => {
  if (!props.option || !props.option.series) return true
  
  return props.option.series.every((series: any) => {
    return !series.data || series.data.length === 0
  })
})

// 初始化图表
const initChart = async () => {
  if (!chartRef.value) return
  
  await nextTick()
  
  // 销毁已存在的实例
  if (chartInstance) {
    chartInstance.dispose()
  }
  
  // 创建新实例
  chartInstance = echarts.init(chartRef.value, props.theme)
  
  // 绑定事件
  bindEvents()
  
  // 设置配置
  updateChart()
  
  // 设置自动调整大小
  if (props.autoResize) {
    setupResize()
  }
  
  emit('chart-ready', chartInstance)
}

// 更新图表
const updateChart = () => {
  if (!chartInstance || !props.option) return
  
  chartInstance.setOption(props.option, props.notMerge, props.lazyUpdate)
}

// 绑定事件
const bindEvents = () => {
  if (!chartInstance) return
  
  chartInstance.on('click', (params) => {
    emit('chart-click', params)
  })
  
  chartInstance.on('dblclick', (params) => {
    emit('chart-dblclick', params)
  })
  
  chartInstance.on('mouseover', (params) => {
    emit('chart-mouseover', params)
  })
  
  chartInstance.on('mouseout', (params) => {
    emit('chart-mouseout', params)
  })
  
  chartInstance.on('selectchanged', (params) => {
    emit('chart-selectchanged', params)
  })
}

// 设置自动调整大小
const setupResize = () => {
  if (!chartRef.value || !chartInstance) return
  
  // 使用 ResizeObserver 监听容器大小变化
  resizeObserver = new ResizeObserver(() => {
    chartInstance?.resize()
  })
  
  resizeObserver.observe(chartRef.value)
  
  // 监听窗口大小变化
  window.addEventListener('resize', handleWindowResize)
}

// 处理窗口大小变化
const handleWindowResize = () => {
  chartInstance?.resize()
}

// 清理资源
const cleanup = () => {
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }
  
  window.removeEventListener('resize', handleWindowResize)
  
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
}

// 公开方法
const resize = () => {
  chartInstance?.resize()
}

const getDataURL = (opts?: any) => {
  return chartInstance?.getDataURL(opts)
}

const getConnectedDataURL = (opts?: any) => {
  return chartInstance?.getConnectedDataURL(opts)
}

const convertToPixel = (finder: any, value: any) => {
  return chartInstance?.convertToPixel(finder, value)
}

const convertFromPixel = (finder: any, value: any) => {
  return chartInstance?.convertFromPixel(finder, value)
}

const containPixel = (finder: any, value: any) => {
  return chartInstance?.containPixel(finder, value)
}

const showLoading = (type?: string, opts?: any) => {
  chartInstance?.showLoading(type, opts)
}

const hideLoading = () => {
  chartInstance?.hideLoading()
}

const clear = () => {
  chartInstance?.clear()
}

const dispose = () => {
  cleanup()
}

// 监听配置变化
watch(
  () => props.option,
  () => {
    updateChart()
  },
  { deep: true }
)

watch(
  () => props.theme,
  () => {
    initChart()
  }
)

// 生命周期
onMounted(() => {
  initChart()
})

onUnmounted(() => {
  cleanup()
})

// 暴露方法
defineExpose({
  resize,
  getDataURL,
  getConnectedDataURL,
  convertToPixel,
  convertFromPixel,
  containPixel,
  showLoading,
  hideLoading,
  clear,
  dispose,
  chartInstance: () => chartInstance
})
</script>

<style lang="scss" scoped>
.base-chart {
  position: relative;
  
  .chart-container {
    position: relative;
  }
  
  .chart-loading {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(255, 255, 255, 0.8);
    z-index: 10;
  }
  
  .chart-empty {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 5;
  }
}
</style>