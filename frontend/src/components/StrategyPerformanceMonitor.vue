<template>
  <div class="strategy-performance-monitor">
    <!-- 控制面板 -->
    <div class="monitor-controls">
      <div class="controls-left">
        <el-select v-model="timeRange" size="small" style="width: 150px">
          <el-option label="最近1小时" value="1h" />
          <el-option label="最近6小时" value="6h" />
          <el-option label="最近24小时" value="24h" />
          <el-option label="最近7天" value="7d" />
          <el-option label="最近30天" value="30d" />
        </el-select>
        
        <el-button size="small" @click="handleRefresh" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        
        <el-switch
          v-model="autoRefresh"
          active-text="自动刷新"
          inactive-text="手动刷新"
          size="small"
          @change="handleAutoRefreshChange"
        />
      </div>
      
      <div class="controls-right">
        <el-button size="small" @click="handleExport">
          <el-icon><Download /></el-icon>
          导出报告
        </el-button>
        
        <el-button size="small" @click="showSettingsDialog = true">
          <el-icon><Setting /></el-icon>
          设置
        </el-button>
      </div>
    </div>

    <!-- 关键指标卡片 -->
    <div class="metrics-cards">
      <el-row :gutter="16">
        <el-col :span="6">
          <el-card class="metric-card">
            <div class="metric-content">
              <div class="metric-icon profit">
                <el-icon><TrendCharts /></el-icon>
              </div>
              <div class="metric-info">
                <div class="metric-value">{{ formatCurrency(metrics.totalPnl) }}</div>
                <div class="metric-label">总盈亏</div>
                <div class="metric-change" :class="metrics.totalPnl >= 0 ? 'positive' : 'negative'">
                  <el-icon>
                    <ArrowUp v-if="metrics.totalPnl >= 0" />
                    <ArrowDown v-else />
                  </el-icon>
                  {{ formatPercent(metrics.pnlChange) }}
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="6">
          <el-card class="metric-card">
            <div class="metric-content">
              <div class="metric-icon success">
                <el-icon><CircleCheck /></el-icon>
              </div>
              <div class="metric-info">
                <div class="metric-value">{{ formatPercent(metrics.winRate) }}</div>
                <div class="metric-label">胜率</div>
                <div class="metric-change">
                  {{ metrics.winningTrades }}/{{ metrics.totalTrades }}
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="6">
          <el-card class="metric-card">
            <div class="metric-content">
              <div class="metric-icon warning">
                <el-icon><Warning /></el-icon>
              </div>
              <div class="metric-info">
                <div class="metric-value">{{ formatPercent(metrics.maxDrawdown) }}</div>
                <div class="metric-label">最大回撤</div>
                <div class="metric-change negative">
                  风险等级: {{ getRiskLevel(metrics.maxDrawdown) }}
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="6">
          <el-card class="metric-card">
            <div class="metric-content">
              <div class="metric-icon info">
                <el-icon><DataAnalysis /></el-icon>
              </div>
              <div class="metric-info">
                <div class="metric-value">{{ metrics.sharpeRatio?.toFixed(2) || '-' }}</div>
                <div class="metric-label">夏普比率</div>
                <div class="metric-change">
                  {{ getPerformanceRating(metrics.sharpeRatio) }}
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 图表区域 -->
    <div class="charts-section">
      <el-row :gutter="16">
        <!-- 盈亏曲线 -->
        <el-col :span="12">
          <el-card title="盈亏曲线" class="chart-card">
            <div ref="pnlChartRef" class="chart-container"></div>
          </el-card>
        </el-col>
        
        <!-- 持仓分布 -->
        <el-col :span="12">
          <el-card title="持仓分布" class="chart-card">
            <div ref="positionChartRef" class="chart-container"></div>
          </el-card>
        </el-col>
      </el-row>
      
      <el-row :gutter="16" style="margin-top: 16px">
        <!-- 交易频率 -->
        <el-col :span="12">
          <el-card title="交易频率" class="chart-card">
            <div ref="tradeFrequencyChartRef" class="chart-container"></div>
          </el-card>
        </el-col>
        
        <!-- 风险指标 -->
        <el-col :span="12">
          <el-card title="风险指标" class="chart-card">
            <div ref="riskChartRef" class="chart-container"></div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 实时状态 -->
    <div class="status-section">
      <el-card title="实时状态">
        <el-row :gutter="16">
          <el-col :span="8">
            <div class="status-item">
              <span class="status-label">策略状态:</span>
              <el-tag :type="getStatusTagType(status.strategy_status)">
                {{ getStatusText(status.strategy_status) }}
              </el-tag>
            </div>
            <div class="status-item">
              <span class="status-label">运行时间:</span>
              <span class="status-value">{{ formatDuration(status.runtime) }}</span>
            </div>
            <div class="status-item">
              <span class="status-label">当前持仓:</span>
              <span class="status-value">{{ status.current_positions }}</span>
            </div>
          </el-col>
          
          <el-col :span="8">
            <div class="status-item">
              <span class="status-label">CPU使用率:</span>
              <el-progress :percentage="status.cpu_usage" :color="getProgressColor(status.cpu_usage)" />
            </div>
            <div class="status-item">
              <span class="status-label">内存使用率:</span>
              <el-progress :percentage="status.memory_usage" :color="getProgressColor(status.memory_usage)" />
            </div>
            <div class="status-item">
              <span class="status-label">网络延迟:</span>
              <span class="status-value">{{ status.network_latency }}ms</span>
            </div>
          </el-col>
          
          <el-col :span="8">
            <div class="status-item">
              <span class="status-label">今日交易:</span>
              <span class="status-value">{{ status.daily_trades }}</span>
            </div>
            <div class="status-item">
              <span class="status-label">今日盈亏:</span>
              <span :class="['status-value', status.daily_pnl >= 0 ? 'positive' : 'negative']">
                {{ formatCurrency(status.daily_pnl) }}
              </span>
            </div>
            <div class="status-item">
              <span class="status-label">最后更新:</span>
              <span class="status-value">{{ formatTime(status.last_update) }}</span>
            </div>
          </el-col>
        </el-row>
      </el-card>
    </div>

    <!-- 设置对话框 -->
    <el-dialog v-model="showSettingsDialog" title="监控设置" width="500px">
      <el-form :model="settings" label-width="120px">
        <el-form-item label="刷新间隔(秒)">
          <el-input-number
            v-model="settings.refresh_interval"
            :min="5"
            :max="300"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item label="数据保留天数">
          <el-input-number
            v-model="settings.data_retention_days"
            :min="1"
            :max="365"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item label="告警阈值">
          <el-row :gutter="16">
            <el-col :span="12">
              <el-form-item label="最大回撤">
                <el-input-number
                  v-model="settings.alert_thresholds.max_drawdown"
                  :min="0"
                  :max="1"
                  :step="0.05"
                  :precision="2"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="日亏损限额">
                <el-input-number
                  v-model="settings.alert_thresholds.daily_loss_limit"
                  :min="0"
                  :max="100000"
                  :step="1000"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
          </el-row>
        </el-form-item>
        
        <el-form-item label="启用告警">
          <el-switch v-model="settings.enable_alerts" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showSettingsDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSaveSettings">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Refresh,
  Download,
  Setting,
  TrendCharts,
  CircleCheck,
  Warning,
  DataAnalysis,
  ArrowUp,
  ArrowDown
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'

interface Props {
  strategyId: number
}

const props = defineProps<Props>()

// 响应式数据
const loading = ref(false)
const autoRefresh = ref(false)
const timeRange = ref('24h')
const showSettingsDialog = ref(false)

let refreshTimer: NodeJS.Timeout | null = null

// 图表实例
const pnlChartRef = ref<HTMLElement>()
const positionChartRef = ref<HTMLElement>()
const tradeFrequencyChartRef = ref<HTMLElement>()
const riskChartRef = ref<HTMLElement>()

let pnlChart: echarts.ECharts | null = null
let positionChart: echarts.ECharts | null = null
let tradeFrequencyChart: echarts.ECharts | null = null
let riskChart: echarts.ECharts | null = null

// 性能指标
const metrics = ref({
  totalPnl: 15680.50,
  pnlChange: 0.0234,
  winRate: 0.68,
  winningTrades: 34,
  totalTrades: 50,
  maxDrawdown: 0.12,
  sharpeRatio: 1.85
})

// 实时状态
const status = ref({
  strategy_status: 'running',
  runtime: 86400, // 秒
  current_positions: 3,
  cpu_usage: 45,
  memory_usage: 62,
  network_latency: 23,
  daily_trades: 12,
  daily_pnl: 2340.80,
  last_update: new Date().toISOString()
})

// 设置
const settings = ref({
  refresh_interval: 30,
  data_retention_days: 30,
  alert_thresholds: {
    max_drawdown: 0.2,
    daily_loss_limit: 10000
  },
  enable_alerts: true
})

// 方法
const loadPerformanceData = async () => {
  try {
    loading.value = true
    
    // 调用API获取性能数据
    // const response = await strategyApi.getStrategyPerformance(props.strategyId, {
    //   period: timeRange.value
    // })
    
    // 模拟数据加载
    await new Promise(resolve => setTimeout(resolve, 500))
    
    // 更新图表
    updateCharts()
    
  } catch (error) {
    ElMessage.error('加载性能数据失败')
  } finally {
    loading.value = false
  }
}

const updateCharts = () => {
  updatePnlChart()
  updatePositionChart()
  updateTradeFrequencyChart()
  updateRiskChart()
}

const updatePnlChart = () => {
  if (!pnlChart) return
  
  const option = {
    title: {
      text: '累计盈亏',
      textStyle: { fontSize: 14 }
    },
    tooltip: {
      trigger: 'axis',
      formatter: '{b}: {c}'
    },
    xAxis: {
      type: 'category',
      data: ['09:00', '10:00', '11:00', '13:00', '14:00', '15:00']
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: '{value}'
      }
    },
    series: [{
      data: [0, 1200, 800, 1500, 2100, 1568],
      type: 'line',
      smooth: true,
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
          { offset: 1, color: 'rgba(64, 158, 255, 0.1)' }
        ])
      },
      lineStyle: {
        color: '#409eff'
      }
    }]
  }
  
  pnlChart.setOption(option)
}

const updatePositionChart = () => {
  if (!positionChart) return
  
  const option = {
    title: {
      text: '持仓分布',
      textStyle: { fontSize: 14 }
    },
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)'
    },
    series: [{
      name: '持仓',
      type: 'pie',
      radius: '60%',
      data: [
        { value: 35, name: 'SHFE.cu2401' },
        { value: 25, name: 'DCE.i2401' },
        { value: 20, name: 'CZCE.MA401' },
        { value: 20, name: '现金' }
      ],
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }]
  }
  
  positionChart.setOption(option)
}

const updateTradeFrequencyChart = () => {
  if (!tradeFrequencyChart) return
  
  const option = {
    title: {
      text: '交易频率',
      textStyle: { fontSize: 14 }
    },
    tooltip: {
      trigger: 'axis'
    },
    xAxis: {
      type: 'category',
      data: ['周一', '周二', '周三', '周四', '周五']
    },
    yAxis: {
      type: 'value'
    },
    series: [{
      data: [8, 12, 15, 10, 14],
      type: 'bar',
      itemStyle: {
        color: '#67c23a'
      }
    }]
  }
  
  tradeFrequencyChart.setOption(option)
}

const updateRiskChart = () => {
  if (!riskChart) return
  
  const option = {
    title: {
      text: '风险指标',
      textStyle: { fontSize: 14 }
    },
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['回撤', '波动率']
    },
    xAxis: {
      type: 'category',
      data: ['1天前', '6小时前', '3小时前', '1小时前', '现在']
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: '{value}%'
      }
    },
    series: [
      {
        name: '回撤',
        type: 'line',
        data: [5, 8, 12, 10, 12],
        itemStyle: { color: '#f56c6c' }
      },
      {
        name: '波动率',
        type: 'line',
        data: [15, 18, 22, 20, 25],
        itemStyle: { color: '#e6a23c' }
      }
    ]
  }
  
  riskChart.setOption(option)
}

const initCharts = async () => {
  await nextTick()
  
  if (pnlChartRef.value) {
    pnlChart = echarts.init(pnlChartRef.value)
  }
  if (positionChartRef.value) {
    positionChart = echarts.init(positionChartRef.value)
  }
  if (tradeFrequencyChartRef.value) {
    tradeFrequencyChart = echarts.init(tradeFrequencyChartRef.value)
  }
  if (riskChartRef.value) {
    riskChart = echarts.init(riskChartRef.value)
  }
  
  // 监听窗口大小变化
  window.addEventListener('resize', handleResize)
}

const handleResize = () => {
  pnlChart?.resize()
  positionChart?.resize()
  tradeFrequencyChart?.resize()
  riskChart?.resize()
}

const handleRefresh = () => {
  loadPerformanceData()
}

const handleAutoRefreshChange = (enabled: boolean) => {
  if (enabled) {
    refreshTimer = setInterval(() => {
      loadPerformanceData()
    }, settings.value.refresh_interval * 1000)
  } else {
    if (refreshTimer) {
      clearInterval(refreshTimer)
      refreshTimer = null
    }
  }
}

const handleExport = () => {
  // 导出性能报告
  ElMessage.success('报告导出功能开发中')
}

const handleSaveSettings = () => {
  // 保存设置
  showSettingsDialog.value = false
  ElMessage.success('设置已保存')
  
  // 如果自动刷新已启用，重新设置定时器
  if (autoRefresh.value) {
    handleAutoRefreshChange(false)
    handleAutoRefreshChange(true)
  }
}

// 格式化函数
const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY'
  }).format(value)
}

const formatPercent = (value: number) => {
  return `${(value * 100).toFixed(2)}%`
}

const formatDuration = (seconds: number) => {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  return `${hours}小时${minutes}分钟`
}

const formatTime = (timestamp: string) => {
  return new Date(timestamp).toLocaleTimeString()
}

const getRiskLevel = (drawdown: number) => {
  if (drawdown < 0.05) return '低'
  if (drawdown < 0.15) return '中'
  return '高'
}

const getPerformanceRating = (sharpe?: number) => {
  if (!sharpe) return '未知'
  if (sharpe > 2) return '优秀'
  if (sharpe > 1) return '良好'
  if (sharpe > 0) return '一般'
  return '较差'
}

const getStatusTagType = (status: string) => {
  const typeMap: Record<string, string> = {
    running: 'success',
    paused: 'warning',
    stopped: 'info',
    error: 'danger'
  }
  return typeMap[status] || 'info'
}

const getStatusText = (status: string) => {
  const textMap: Record<string, string> = {
    running: '运行中',
    paused: '已暂停',
    stopped: '已停止',
    error: '错误'
  }
  return textMap[status] || '未知'
}

const getProgressColor = (percentage: number) => {
  if (percentage < 50) return '#67c23a'
  if (percentage < 80) return '#e6a23c'
  return '#f56c6c'
}

// 生命周期
onMounted(async () => {
  await initCharts()
  await loadPerformanceData()
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
  
  window.removeEventListener('resize', handleResize)
  
  pnlChart?.dispose()
  positionChart?.dispose()
  tradeFrequencyChart?.dispose()
  riskChart?.dispose()
})
</script>

<style scoped lang="scss">
.strategy-performance-monitor {
  .monitor-controls {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px;
    background: var(--el-bg-color);
    border-radius: 8px;
    margin-bottom: 16px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    
    .controls-left,
    .controls-right {
      display: flex;
      align-items: center;
      gap: 12px;
    }
  }
  
  .metrics-cards {
    margin-bottom: 16px;
    
    .metric-card {
      .metric-content {
        display: flex;
        align-items: center;
        gap: 16px;
        
        .metric-icon {
          width: 48px;
          height: 48px;
          border-radius: 8px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 24px;
          
          &.profit { background: #e6f7ff; color: #1890ff; }
          &.success { background: #f6ffed; color: #52c41a; }
          &.warning { background: var(--el-bg-color)7e6; color: #fa8c16; }
          &.info { background: #f0f5ff; color: #722ed1; }
        }
        
        .metric-info {
          flex: 1;
          
          .metric-value {
            font-size: 24px;
            font-weight: 600;
            color: #303133;
            line-height: 1;
            margin-bottom: 4px;
          }
          
          .metric-label {
            font-size: 14px;
            color: #909399;
            margin-bottom: 4px;
          }
          
          .metric-change {
            font-size: 12px;
            display: flex;
            align-items: center;
            gap: 4px;
            
            &.positive { color: #67c23a; }
            &.negative { color: #f56c6c; }
          }
        }
      }
    }
  }
  
  .charts-section {
    margin-bottom: 16px;
    
    .chart-card {
      .chart-container {
        height: 300px;
      }
    }
  }
  
  .status-section {
    .status-item {
      display: flex;
      align-items: center;
      margin-bottom: 12px;
      
      .status-label {
        min-width: 80px;
        font-size: 14px;
        color: #606266;
      }
      
      .status-value {
        font-size: 14px;
        color: #303133;
        
        &.positive { color: #67c23a; }
        &.negative { color: #f56c6c; }
      }
    }
  }
}
</style>