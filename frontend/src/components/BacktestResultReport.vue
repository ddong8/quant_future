<template>
  <div class="backtest-result-report">
    <!-- 报告头部 -->
    <div class="report-header">
      <div class="header-info">
        <h2 class="report-title">{{ backtest?.name || '回测报告' }}</h2>
        <div class="report-meta">
          <el-tag :type="getStatusTagType(backtest?.status)" size="small">
            {{ getStatusText(backtest?.status) }}
          </el-tag>
          <span class="meta-item">
            策略: {{ backtest?.strategy_name }}
          </span>
          <span class="meta-item">
            时间: {{ formatDateRange() }}
          </span>
          <span class="meta-item">
            完成时间: {{ formatDateTime(backtest?.completed_at) }}
          </span>
        </div>
      </div>
      
      <div class="header-actions">
        <el-button @click="handleExportReport">
          <el-icon><Download /></el-icon>
          导出报告
        </el-button>
        <el-button @click="handleCompare">
          <el-icon><DataAnalysis /></el-icon>
          对比分析
        </el-button>
        <el-button type="primary" @click="handleShare">
          <el-icon><Share /></el-icon>
          分享报告
        </el-button>
      </div>
    </div>

    <!-- 核心指标概览 -->
    <div class="metrics-overview">
      <el-row :gutter="16">
        <el-col :span="6">
          <div class="metric-card primary">
            <div class="metric-icon">
              <el-icon><TrendCharts /></el-icon>
            </div>
            <div class="metric-content">
              <div class="metric-value">{{ formatPercent(result?.total_return) }}</div>
              <div class="metric-label">总收益率</div>
              <div class="metric-sub">
                年化: {{ formatPercent(result?.annualized_return) }}
              </div>
            </div>
          </div>
        </el-col>
        
        <el-col :span="6">
          <div class="metric-card success">
            <div class="metric-icon">
              <el-icon><Trophy /></el-icon>
            </div>
            <div class="metric-content">
              <div class="metric-value">{{ result?.sharpe_ratio?.toFixed(2) || '-' }}</div>
              <div class="metric-label">夏普比率</div>
              <div class="metric-sub">
                索提诺: {{ result?.sortino_ratio?.toFixed(2) || '-' }}
              </div>
            </div>
          </div>
        </el-col>
        
        <el-col :span="6">
          <div class="metric-card warning">
            <div class="metric-icon">
              <el-icon><Warning /></el-icon>
            </div>
            <div class="metric-content">
              <div class="metric-value">{{ formatPercent(result?.max_drawdown) }}</div>
              <div class="metric-label">最大回撤</div>
              <div class="metric-sub">
                卡玛比率: {{ result?.calmar_ratio?.toFixed(2) || '-' }}
              </div>
            </div>
          </div>
        </el-col>
        
        <el-col :span="6">
          <div class="metric-card info">
            <div class="metric-icon">
              <el-icon><DataBoard /></el-icon>
            </div>
            <div class="metric-content">
              <div class="metric-value">{{ formatPercent(result?.win_rate) }}</div>
              <div class="metric-label">胜率</div>
              <div class="metric-sub">
                盈亏比: {{ result?.profit_factor?.toFixed(2) || '-' }}
              </div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 图表区域 -->
    <div class="charts-section">
      <el-row :gutter="16">
        <!-- 收益曲线 -->
        <el-col :span="12">
          <el-card title="收益曲线" class="chart-card">
            <div ref="equityChartRef" class="chart-container"></div>
          </el-card>
        </el-col>
        
        <!-- 回撤曲线 -->
        <el-col :span="12">
          <el-card title="回撤曲线" class="chart-card">
            <div ref="drawdownChartRef" class="chart-container"></div>
          </el-card>
        </el-col>
      </el-row>
      
      <el-row :gutter="16" style="margin-top: 16px">
        <!-- 月度收益热力图 -->
        <el-col :span="12">
          <el-card title="月度收益热力图" class="chart-card">
            <div ref="monthlyReturnsChartRef" class="chart-container"></div>
          </el-card>
        </el-col>
        
        <!-- 收益分布 -->
        <el-col :span="12">
          <el-card title="收益分布" class="chart-card">
            <div ref="returnsDistributionChartRef" class="chart-container"></div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 详细统计 -->
    <div class="detailed-stats">
      <el-card title="详细统计">
        <el-row :gutter="32">
          <el-col :span="8">
            <h4>收益统计</h4>
            <el-descriptions :column="1" size="small">
              <el-descriptions-item label="总收益率">
                {{ formatPercent(result?.total_return) }}
              </el-descriptions-item>
              <el-descriptions-item label="年化收益率">
                {{ formatPercent(result?.annualized_return) }}
              </el-descriptions-item>
              <el-descriptions-item label="波动率">
                {{ formatPercent(result?.volatility) }}
              </el-descriptions-item>
              <el-descriptions-item label="夏普比率">
                {{ result?.sharpe_ratio?.toFixed(3) || '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="索提诺比率">
                {{ result?.sortino_ratio?.toFixed(3) || '-' }}
              </el-descriptions-item>
            </el-descriptions>
          </el-col>
          
          <el-col :span="8">
            <h4>风险统计</h4>
            <el-descriptions :column="1" size="small">
              <el-descriptions-item label="最大回撤">
                {{ formatPercent(result?.max_drawdown) }}
              </el-descriptions-item>
              <el-descriptions-item label="卡玛比率">
                {{ result?.calmar_ratio?.toFixed(3) || '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="95% VaR">
                {{ formatPercent(result?.risk_metrics?.var_95) }}
              </el-descriptions-item>
              <el-descriptions-item label="95% CVaR">
                {{ formatPercent(result?.risk_metrics?.cvar_95) }}
              </el-descriptions-item>
              <el-descriptions-item label="偏度">
                {{ result?.risk_metrics?.skewness?.toFixed(3) || '-' }}
              </el-descriptions-item>
            </el-descriptions>
          </el-col>
          
          <el-col :span="8">
            <h4>交易统计</h4>
            <el-descriptions :column="1" size="small">
              <el-descriptions-item label="总交易次数">
                {{ result?.total_trades || 0 }}
              </el-descriptions-item>
              <el-descriptions-item label="盈利交易">
                {{ result?.winning_trades || 0 }}
              </el-descriptions-item>
              <el-descriptions-item label="亏损交易">
                {{ result?.losing_trades || 0 }}
              </el-descriptions-item>
              <el-descriptions-item label="胜率">
                {{ formatPercent(result?.win_rate) }}
              </el-descriptions-item>
              <el-descriptions-item label="盈亏比">
                {{ result?.profit_factor?.toFixed(2) || '-' }}
              </el-descriptions-item>
            </el-descriptions>
          </el-col>
        </el-row>
      </el-card>
    </div>

    <!-- 基准比较 -->
    <div v-if="result?.benchmark_comparison" class="benchmark-comparison">
      <el-card title="基准比较">
        <el-row :gutter="16">
          <el-col :span="6">
            <div class="comparison-item">
              <div class="comparison-label">基准收益率</div>
              <div class="comparison-value">
                {{ formatPercent(result.benchmark_comparison.benchmark_return) }}
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="comparison-item">
              <div class="comparison-label">Alpha</div>
              <div class="comparison-value" :class="getAlphaClass()">
                {{ formatPercent(result.benchmark_comparison.alpha) }}
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="comparison-item">
              <div class="comparison-label">Beta</div>
              <div class="comparison-value">
                {{ result.benchmark_comparison.beta?.toFixed(3) || '-' }}
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="comparison-item">
              <div class="comparison-label">相关性</div>
              <div class="comparison-value">
                {{ result.benchmark_comparison.correlation?.toFixed(3) || '-' }}
              </div>
            </div>
          </el-col>
        </el-row>
      </el-card>
    </div>

    <!-- 持仓分析 -->
    <div class="position-analysis">
      <el-card title="持仓分析">
        <div ref="positionAnalysisChartRef" class="chart-container"></div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Download,
  DataAnalysis,
  Share,
  TrendCharts,
  Trophy,
  Warning,
  DataBoard
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import type { Backtest, BacktestResult } from '@/types/backtest'

interface Props {
  backtest: Backtest | null
  result: BacktestResult | null
}

const props = defineProps<Props>()

// 图表实例
const equityChartRef = ref<HTMLElement>()
const drawdownChartRef = ref<HTMLElement>()
const monthlyReturnsChartRef = ref<HTMLElement>()
const returnsDistributionChartRef = ref<HTMLElement>()
const positionAnalysisChartRef = ref<HTMLElement>()

let equityChart: echarts.ECharts | null = null
let drawdownChart: echarts.ECharts | null = null
let monthlyReturnsChart: echarts.ECharts | null = null
let returnsDistributionChart: echarts.ECharts | null = null
let positionAnalysisChart: echarts.ECharts | null = null

// 方法
const initCharts = async () => {
  await nextTick()
  
  if (equityChartRef.value) {
    equityChart = echarts.init(equityChartRef.value)
    updateEquityChart()
  }
  
  if (drawdownChartRef.value) {
    drawdownChart = echarts.init(drawdownChartRef.value)
    updateDrawdownChart()
  }
  
  if (monthlyReturnsChartRef.value) {
    monthlyReturnsChart = echarts.init(monthlyReturnsChartRef.value)
    updateMonthlyReturnsChart()
  }
  
  if (returnsDistributionChartRef.value) {
    returnsDistributionChart = echarts.init(returnsDistributionChartRef.value)
    updateReturnsDistributionChart()
  }
  
  if (positionAnalysisChartRef.value) {
    positionAnalysisChart = echarts.init(positionAnalysisChartRef.value)
    updatePositionAnalysisChart()
  }
  
  // 监听窗口大小变化
  window.addEventListener('resize', handleResize)
}

const updateEquityChart = () => {
  if (!equityChart || !props.result?.equity_curve) return
  
  const dates = props.result.equity_curve.map(point => point.date)
  const equity = props.result.equity_curve.map(point => point.equity)
  const returns = props.result.equity_curve.map(point => point.cumulative_returns * 100)
  
  const option = {
    title: {
      text: '资金曲线',
      textStyle: { fontSize: 14 }
    },
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const date = params[0].axisValue
        const equityValue = params[0].value
        const returnValue = params[1].value
        return `${date}<br/>净值: ${equityValue}<br/>累计收益: ${returnValue.toFixed(2)}%`
      }
    },
    legend: {
      data: ['净值', '累计收益率']
    },
    xAxis: {
      type: 'category',
      data: dates
    },
    yAxis: [
      {
        type: 'value',
        name: '净值',
        position: 'left'
      },
      {
        type: 'value',
        name: '收益率(%)',
        position: 'right'
      }
    ],
    series: [
      {
        name: '净值',
        type: 'line',
        data: equity,
        smooth: true,
        lineStyle: { color: '#409eff' }
      },
      {
        name: '累计收益率',
        type: 'line',
        yAxisIndex: 1,
        data: returns,
        smooth: true,
        lineStyle: { color: '#67c23a' }
      }
    ]
  }
  
  equityChart.setOption(option)
}

const updateDrawdownChart = () => {
  if (!drawdownChart || !props.result?.drawdown_curve) return
  
  const dates = props.result.drawdown_curve.map(point => point.date)
  const drawdowns = props.result.drawdown_curve.map(point => point.drawdown * 100)
  
  const option = {
    title: {
      text: '回撤曲线',
      textStyle: { fontSize: 14 }
    },
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const date = params[0].axisValue
        const drawdown = params[0].value
        return `${date}<br/>回撤: ${drawdown.toFixed(2)}%`
      }
    },
    xAxis: {
      type: 'category',
      data: dates
    },
    yAxis: {
      type: 'value',
      name: '回撤(%)',
      max: 0
    },
    series: [{
      data: drawdowns,
      type: 'line',
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(245, 108, 108, 0.3)' },
          { offset: 1, color: 'rgba(245, 108, 108, 0.1)' }
        ])
      },
      lineStyle: { color: '#f56c6c' },
      smooth: true
    }]
  }
  
  drawdownChart.setOption(option)
}

const updateMonthlyReturnsChart = () => {
  if (!monthlyReturnsChart) return
  
  // 模拟月度收益数据
  const monthlyData = [
    ['2023-01', 2.5], ['2023-02', -1.2], ['2023-03', 3.8], ['2023-04', 1.5],
    ['2023-05', -0.8], ['2023-06', 2.1], ['2023-07', 4.2], ['2023-08', -2.1],
    ['2023-09', 1.8], ['2023-10', 3.5], ['2023-11', -1.5], ['2023-12', 2.8]
  ]
  
  const option = {
    title: {
      text: '月度收益热力图',
      textStyle: { fontSize: 14 }
    },
    tooltip: {
      position: 'top',
      formatter: (params: any) => {
        return `${params.data[0]}: ${params.data[1]}%`
      }
    },
    visualMap: {
      min: -5,
      max: 5,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: '10%',
      inRange: {
        color: ['#f56c6c', '#ffffff', '#67c23a']
      }
    },
    calendar: {
      top: 60,
      left: 30,
      right: 30,
      cellSize: ['auto', 20],
      range: '2023',
      itemStyle: {
        borderWidth: 0.5
      },
      yearLabel: { show: false }
    },
    series: [{
      type: 'heatmap',
      coordinateSystem: 'calendar',
      data: monthlyData
    }]
  }
  
  monthlyReturnsChart.setOption(option)
}

const updateReturnsDistributionChart = () => {
  if (!returnsDistributionChart) return
  
  // 模拟收益分布数据
  const distributionData = [
    { value: 5, name: '< -5%' },
    { value: 12, name: '-5% ~ -2%' },
    { value: 25, name: '-2% ~ 0%' },
    { value: 35, name: '0% ~ 2%' },
    { value: 18, name: '2% ~ 5%' },
    { value: 5, name: '> 5%' }
  ]
  
  const option = {
    title: {
      text: '收益分布',
      textStyle: { fontSize: 14 }
    },
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)'
    },
    series: [{
      name: '收益分布',
      type: 'pie',
      radius: '60%',
      data: distributionData,
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }]
  }
  
  returnsDistributionChart.setOption(option)
}

const updatePositionAnalysisChart = () => {
  if (!positionAnalysisChart) return
  
  // 模拟持仓分析数据
  const positionData = [
    { name: 'SHFE.cu2601', value: 35, weight: 0.35 },
    { name: 'DCE.i2601', value: 25, weight: 0.25 },
    { name: 'CZCE.MA2601', value: 20, weight: 0.20 },
    { name: 'CFFEX.IF2601', value: 20, weight: 0.20 }
  ]
  
  const option = {
    title: {
      text: '持仓权重分析',
      textStyle: { fontSize: 14 }
    },
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c}% (权重: {d}%)'
    },
    series: [{
      name: '持仓分析',
      type: 'pie',
      radius: ['40%', '70%'],
      data: positionData.map(item => ({
        name: item.name,
        value: item.value
      })),
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      },
      label: {
        show: true,
        formatter: '{b}: {c}%'
      }
    }]
  }
  
  positionAnalysisChart.setOption(option)
}

const handleResize = () => {
  equityChart?.resize()
  drawdownChart?.resize()
  monthlyReturnsChart?.resize()
  returnsDistributionChart?.resize()
  positionAnalysisChart?.resize()
}

const handleExportReport = () => {
  ElMessage.success('报告导出功能开发中')
}

const handleCompare = () => {
  ElMessage.success('对比分析功能开发中')
}

const handleShare = () => {
  ElMessage.success('分享报告功能开发中')
}

// 格式化函数
const getStatusTagType = (status?: string) => {
  const typeMap: Record<string, string> = {
    completed: 'success',
    running: 'warning',
    failed: 'danger',
    cancelled: 'info'
  }
  return typeMap[status || ''] || 'info'
}

const getStatusText = (status?: string) => {
  const textMap: Record<string, string> = {
    completed: '已完成',
    running: '运行中',
    failed: '失败',
    cancelled: '已取消'
  }
  return textMap[status || ''] || '未知'
}

const formatDateRange = () => {
  if (!props.backtest?.config) return '-'
  
  const { start_date, end_date } = props.backtest.config
  return `${start_date} ~ ${end_date}`
}

const formatDateTime = (dateString?: string) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('zh-CN')
}

const formatPercent = (value?: number) => {
  if (value === undefined || value === null) return '-'
  return `${(value * 100).toFixed(2)}%`
}

const getAlphaClass = () => {
  const alpha = props.result?.benchmark_comparison?.alpha || 0
  return alpha > 0 ? 'positive' : alpha < 0 ? 'negative' : 'neutral'
}

// 生命周期
onMounted(() => {
  initCharts()
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  
  equityChart?.dispose()
  drawdownChart?.dispose()
  monthlyReturnsChart?.dispose()
  returnsDistributionChart?.dispose()
  positionAnalysisChart?.dispose()
})
</script>

<style scoped lang="scss">
.backtest-result-report {
  .report-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 24px;
    padding: 20px;
    background: var(--el-bg-color);
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    
    .header-info {
      .report-title {
        margin: 0 0 8px 0;
        font-size: 24px;
        font-weight: 600;
        color: #303133;
      }
      
      .report-meta {
        display: flex;
        align-items: center;
        gap: 16px;
        
        .meta-item {
          font-size: 14px;
          color: #606266;
        }
      }
    }
    
    .header-actions {
      display: flex;
      gap: 12px;
    }
  }
  
  .metrics-overview {
    margin-bottom: 24px;
    
    .metric-card {
      display: flex;
      align-items: center;
      padding: 20px;
      background: var(--el-bg-color);
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
      
      .metric-icon {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        margin-right: 16px;
      }
      
      .metric-content {
        flex: 1;
        
        .metric-value {
          font-size: 28px;
          font-weight: 600;
          line-height: 1;
          margin-bottom: 4px;
        }
        
        .metric-label {
          font-size: 14px;
          color: #606266;
          margin-bottom: 4px;
        }
        
        .metric-sub {
          font-size: 12px;
          color: #909399;
        }
      }
      
      &.primary {
        .metric-icon {
          background: #ecf5ff;
          color: #409eff;
        }
        .metric-value {
          color: #409eff;
        }
      }
      
      &.success {
        .metric-icon {
          background: var(--el-color-primary-light-9);
          color: #67c23a;
        }
        .metric-value {
          color: #67c23a;
        }
      }
      
      &.warning {
        .metric-icon {
          background: var(--el-color-warning-light-9);
          color: #e6a23c;
        }
        .metric-value {
          color: #e6a23c;
        }
      }
      
      &.info {
        .metric-icon {
          background: var(--el-fill-color-light);
          color: #909399;
        }
        .metric-value {
          color: #303133;
        }
      }
    }
  }
  
  .charts-section {
    margin-bottom: 24px;
    
    .chart-card {
      .chart-container {
        height: 300px;
      }
    }
  }
  
  .detailed-stats {
    margin-bottom: 24px;
    
    h4 {
      margin: 0 0 16px 0;
      font-size: 16px;
      font-weight: 600;
      color: #303133;
      border-bottom: 2px solid #409eff;
      padding-bottom: 8px;
    }
  }
  
  .benchmark-comparison {
    margin-bottom: 24px;
    
    .comparison-item {
      text-align: center;
      padding: 16px;
      background: var(--el-bg-color-page);
      border-radius: 8px;
      
      .comparison-label {
        font-size: 14px;
        color: #606266;
        margin-bottom: 8px;
      }
      
      .comparison-value {
        font-size: 20px;
        font-weight: 600;
        color: #303133;
        
        &.positive {
          color: #67c23a;
        }
        
        &.negative {
          color: #f56c6c;
        }
        
        &.neutral {
          color: #909399;
        }
      }
    }
  }
  
  .position-analysis {
    .chart-container {
      height: 400px;
    }
  }
}
</style>