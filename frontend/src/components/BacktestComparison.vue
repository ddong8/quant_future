<template>
  <div class="backtest-comparison">
    <!-- 对比选择器 -->
    <div class="comparison-selector">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>回测对比分析</span>
            <el-button type="primary" @click="showSelectDialog = true">
              <el-icon><Plus /></el-icon>
              选择回测
            </el-button>
          </div>
        </template>
        
        <div class="selected-backtests">
          <div
            v-for="backtest in selectedBacktests"
            :key="backtest.id"
            class="backtest-item"
          >
            <div class="backtest-info">
              <div class="backtest-name">{{ backtest.name }}</div>
              <div class="backtest-meta">
                <el-tag size="small">{{ backtest.strategy_name }}</el-tag>
                <span class="meta-text">{{ formatDateRange(backtest.config) }}</span>
              </div>
            </div>
            <div class="backtest-actions">
              <el-button
                text
                size="small"
                type="danger"
                @click="removeBacktest(backtest.id)"
              >
                <el-icon><Close /></el-icon>
              </el-button>
            </div>
          </div>
          
          <div v-if="selectedBacktests.length === 0" class="empty-selection">
            <el-empty description="请选择要对比的回测" />
          </div>
        </div>
      </el-card>
    </div>

    <!-- 对比结果 -->
    <div v-if="selectedBacktests.length >= 2" class="comparison-results">
      <!-- 指标对比表格 -->
      <el-card title="指标对比" class="metrics-comparison">
        <el-table :data="comparisonMetrics" border>
          <el-table-column prop="metric" label="指标" width="150" fixed="left">
            <template #default="{ row }">
              <strong>{{ row.metric }}</strong>
            </template>
          </el-table-column>
          
          <el-table-column
            v-for="backtest in selectedBacktests"
            :key="backtest.id"
            :label="backtest.name"
            width="120"
            align="center"
          >
            <template #default="{ row }">
              <span :class="getMetricClass(row.values[backtest.id], row.type)">
                {{ formatMetricValue(row.values[backtest.id], row.type) }}
              </span>
            </template>
          </el-table-column>
          
          <el-table-column label="最佳" width="120" align="center">
            <template #default="{ row }">
              <el-tag type="success" size="small">
                {{ getBestBacktestName(row) }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <!-- 收益曲线对比 -->
      <el-card title="收益曲线对比" class="chart-comparison">
        <div ref="equityComparisonChartRef" class="chart-container"></div>
      </el-card>

      <!-- 回撤对比 -->
      <el-card title="回撤对比" class="chart-comparison">
        <div ref="drawdownComparisonChartRef" class="chart-container"></div>
      </el-card>

      <!-- 风险收益散点图 -->
      <el-card title="风险收益分析" class="chart-comparison">
        <div ref="riskReturnScatterRef" class="chart-container"></div>
      </el-card>

      <!-- 月度收益对比 -->
      <el-card title="月度收益对比" class="chart-comparison">
        <div ref="monthlyReturnsComparisonRef" class="chart-container"></div>
      </el-card>

      <!-- 相关性分析 -->
      <el-card title="相关性分析" class="correlation-analysis">
        <div class="correlation-matrix">
          <el-table :data="correlationMatrix" border>
            <el-table-column prop="name" label="策略" width="150" fixed="left" />
            <el-table-column
              v-for="backtest in selectedBacktests"
              :key="backtest.id"
              :label="backtest.name"
              width="120"
              align="center"
            >
              <template #default="{ row }">
                <span :class="getCorrelationClass(row.correlations[backtest.id])">
                  {{ row.correlations[backtest.id]?.toFixed(3) || '-' }}
                </span>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-card>

      <!-- 排名分析 -->
      <el-card title="综合排名" class="ranking-analysis">
        <div class="ranking-table">
          <el-table :data="rankingData" border>
            <el-table-column prop="rank" label="排名" width="80" align="center">
              <template #default="{ row }">
                <el-tag
                  :type="getRankTagType(row.rank)"
                  size="small"
                >
                  第{{ row.rank }}名
                </el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="name" label="回测名称" width="200" />
            
            <el-table-column prop="score" label="综合评分" width="120" align="center">
              <template #default="{ row }">
                <el-progress
                  :percentage="row.score"
                  :color="getScoreColor(row.score)"
                  :show-text="false"
                  style="width: 80px"
                />
                <span style="margin-left: 8px">{{ row.score }}</span>
              </template>
            </el-table-column>
            
            <el-table-column prop="total_return" label="总收益率" width="120" align="center">
              <template #default="{ row }">
                {{ formatPercent(row.total_return) }}
              </template>
            </el-table-column>
            
            <el-table-column prop="sharpe_ratio" label="夏普比率" width="120" align="center">
              <template #default="{ row }">
                {{ row.sharpe_ratio?.toFixed(2) || '-' }}
              </template>
            </el-table-column>
            
            <el-table-column prop="max_drawdown" label="最大回撤" width="120" align="center">
              <template #default="{ row }">
                {{ formatPercent(row.max_drawdown) }}
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-card>
    </div>

    <!-- 回测选择对话框 -->
    <el-dialog v-model="showSelectDialog" title="选择回测" width="800px">
      <div class="backtest-selection">
        <el-table
          :data="availableBacktests"
          @selection-change="handleSelectionChange"
          height="400"
        >
          <el-table-column type="selection" width="55" />
          <el-table-column prop="name" label="回测名称" width="200" />
          <el-table-column prop="strategy_name" label="策略" width="150" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getStatusTagType(row.status)" size="small">
                {{ getStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="时间范围" width="200">
            <template #default="{ row }">
              {{ formatDateRange(row.config) }}
            </template>
          </el-table-column>
          <el-table-column prop="completed_at" label="完成时间">
            <template #default="{ row }">
              {{ formatDateTime(row.completed_at) }}
            </template>
          </el-table-column>
        </el-table>
      </div>
      
      <template #footer>
        <el-button @click="showSelectDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmSelection">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Close } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { useBacktestStore } from '@/stores/backtest'
import type { Backtest, BacktestResult } from '@/types/backtest'

const backtestStore = useBacktestStore()

// 响应式数据
const showSelectDialog = ref(false)
const selectedBacktests = ref<Backtest[]>([])
const tempSelection = ref<Backtest[]>([])

// 图表实例
const equityComparisonChartRef = ref<HTMLElement>()
const drawdownComparisonChartRef = ref<HTMLElement>()
const riskReturnScatterRef = ref<HTMLElement>()
const monthlyReturnsComparisonRef = ref<HTMLElement>()

let equityComparisonChart: echarts.ECharts | null = null
let drawdownComparisonChart: echarts.ECharts | null = null
let riskReturnScatter: echarts.ECharts | null = null
let monthlyReturnsComparison: echarts.ECharts | null = null

// 计算属性
const availableBacktests = computed(() => {
  return backtestStore.backtests.filter(b => b.status === 'completed')
})

const comparisonMetrics = computed(() => {
  if (selectedBacktests.value.length === 0) return []
  
  const metrics = [
    { metric: '总收益率', key: 'total_return', type: 'percent', higher_better: true },
    { metric: '年化收益率', key: 'annualized_return', type: 'percent', higher_better: true },
    { metric: '夏普比率', key: 'sharpe_ratio', type: 'number', higher_better: true },
    { metric: '索提诺比率', key: 'sortino_ratio', type: 'number', higher_better: true },
    { metric: '最大回撤', key: 'max_drawdown', type: 'percent', higher_better: false },
    { metric: '波动率', key: 'volatility', type: 'percent', higher_better: false },
    { metric: '卡玛比率', key: 'calmar_ratio', type: 'number', higher_better: true },
    { metric: '胜率', key: 'win_rate', type: 'percent', higher_better: true },
    { metric: '盈亏比', key: 'profit_factor', type: 'number', higher_better: true },
    { metric: '总交易次数', key: 'total_trades', type: 'number', higher_better: null }
  ]
  
  return metrics.map(metric => {
    const values: Record<number, number> = {}
    selectedBacktests.value.forEach(backtest => {
      if (backtest.result) {
        values[backtest.id] = (backtest.result as any)[metric.key] || 0
      }
    })
    
    return {
      ...metric,
      values
    }
  })
})

const correlationMatrix = computed(() => {
  return selectedBacktests.value.map(backtest => {
    const correlations: Record<number, number> = {}
    
    selectedBacktests.value.forEach(otherBacktest => {
      if (backtest.id === otherBacktest.id) {
        correlations[otherBacktest.id] = 1.0
      } else {
        // 模拟相关性计算
        correlations[otherBacktest.id] = Math.random() * 0.8 + 0.1
      }
    })
    
    return {
      name: backtest.name,
      correlations
    }
  })
})

const rankingData = computed(() => {
  const rankings = selectedBacktests.value.map(backtest => {
    const result = backtest.result
    if (!result) return null
    
    // 计算综合评分 (简化算法)
    const returnScore = (result.total_return || 0) * 100
    const sharpeScore = (result.sharpe_ratio || 0) * 20
    const drawdownScore = (1 - (result.max_drawdown || 0)) * 50
    
    const score = Math.max(0, Math.min(100, returnScore + sharpeScore + drawdownScore))
    
    return {
      id: backtest.id,
      name: backtest.name,
      score: Math.round(score),
      total_return: result.total_return,
      sharpe_ratio: result.sharpe_ratio,
      max_drawdown: result.max_drawdown
    }
  }).filter(Boolean)
  
  return rankings
    .sort((a, b) => (b?.score || 0) - (a?.score || 0))
    .map((item, index) => ({ ...item, rank: index + 1 }))
})

// 方法
const initCharts = async () => {
  await nextTick()
  
  if (equityComparisonChartRef.value) {
    equityComparisonChart = echarts.init(equityComparisonChartRef.value)
    updateEquityComparisonChart()
  }
  
  if (drawdownComparisonChartRef.value) {
    drawdownComparisonChart = echarts.init(drawdownComparisonChartRef.value)
    updateDrawdownComparisonChart()
  }
  
  if (riskReturnScatterRef.value) {
    riskReturnScatter = echarts.init(riskReturnScatterRef.value)
    updateRiskReturnScatter()
  }
  
  if (monthlyReturnsComparisonRef.value) {
    monthlyReturnsComparison = echarts.init(monthlyReturnsComparisonRef.value)
    updateMonthlyReturnsComparison()
  }
  
  window.addEventListener('resize', handleResize)
}

const updateEquityComparisonChart = () => {
  if (!equityComparisonChart) return
  
  const series = selectedBacktests.value.map((backtest, index) => {
    // 模拟收益曲线数据
    const data = Array.from({ length: 100 }, (_, i) => {
      const baseReturn = (backtest.result?.total_return || 0) * 100
      const volatility = (backtest.result?.volatility || 0.1) * 100
      const randomWalk = Math.random() * volatility - volatility / 2
      return baseReturn * (i / 100) + randomWalk
    })
    
    return {
      name: backtest.name,
      type: 'line',
      data: data,
      smooth: true
    }
  })
  
  const option = {
    title: {
      text: '收益曲线对比',
      textStyle: { fontSize: 14 }
    },
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: selectedBacktests.value.map(b => b.name)
    },
    xAxis: {
      type: 'category',
      data: Array.from({ length: 100 }, (_, i) => `Day ${i + 1}`)
    },
    yAxis: {
      type: 'value',
      name: '累计收益率(%)'
    },
    series: series
  }
  
  equityComparisonChart.setOption(option)
}

const updateDrawdownComparisonChart = () => {
  if (!drawdownComparisonChart) return
  
  const series = selectedBacktests.value.map(backtest => {
    // 模拟回撤数据
    const maxDrawdown = backtest.result?.max_drawdown || 0.1
    const data = Array.from({ length: 100 }, (_, i) => {
      return -Math.random() * maxDrawdown * 100
    })
    
    return {
      name: backtest.name,
      type: 'line',
      data: data,
      smooth: true,
      areaStyle: { opacity: 0.3 }
    }
  })
  
  const option = {
    title: {
      text: '回撤对比',
      textStyle: { fontSize: 14 }
    },
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: selectedBacktests.value.map(b => b.name)
    },
    xAxis: {
      type: 'category',
      data: Array.from({ length: 100 }, (_, i) => `Day ${i + 1}`)
    },
    yAxis: {
      type: 'value',
      name: '回撤(%)',
      max: 0
    },
    series: series
  }
  
  drawdownComparisonChart.setOption(option)
}

const updateRiskReturnScatter = () => {
  if (!riskReturnScatter) return
  
  const data = selectedBacktests.value.map(backtest => {
    const result = backtest.result
    return {
      name: backtest.name,
      value: [
        (result?.volatility || 0) * 100, // x轴: 风险(波动率)
        (result?.total_return || 0) * 100 // y轴: 收益率
      ]
    }
  })
  
  const option = {
    title: {
      text: '风险收益散点图',
      textStyle: { fontSize: 14 }
    },
    tooltip: {
      trigger: 'item',
      formatter: (params: any) => {
        return `${params.data.name}<br/>风险: ${params.data.value[0].toFixed(2)}%<br/>收益: ${params.data.value[1].toFixed(2)}%`
      }
    },
    xAxis: {
      type: 'value',
      name: '风险(波动率%)'
    },
    yAxis: {
      type: 'value',
      name: '收益率(%)'
    },
    series: [{
      type: 'scatter',
      data: data,
      symbolSize: 20,
      label: {
        show: true,
        position: 'top',
        formatter: '{b}'
      }
    }]
  }
  
  riskReturnScatter.setOption(option)
}

const updateMonthlyReturnsComparison = () => {
  if (!monthlyReturnsComparison) return
  
  const months = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']
  
  const series = selectedBacktests.value.map(backtest => {
    // 模拟月度收益数据
    const data = months.map(() => (Math.random() - 0.5) * 10)
    
    return {
      name: backtest.name,
      type: 'bar',
      data: data
    }
  })
  
  const option = {
    title: {
      text: '月度收益对比',
      textStyle: { fontSize: 14 }
    },
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: selectedBacktests.value.map(b => b.name)
    },
    xAxis: {
      type: 'category',
      data: months
    },
    yAxis: {
      type: 'value',
      name: '月度收益率(%)'
    },
    series: series
  }
  
  monthlyReturnsComparison.setOption(option)
}

const handleResize = () => {
  equityComparisonChart?.resize()
  drawdownComparisonChart?.resize()
  riskReturnScatter?.resize()
  monthlyReturnsComparison?.resize()
}

const handleSelectionChange = (selection: Backtest[]) => {
  tempSelection.value = selection
}

const confirmSelection = () => {
  if (tempSelection.value.length < 2) {
    ElMessage.warning('请至少选择2个回测进行对比')
    return
  }
  
  if (tempSelection.value.length > 5) {
    ElMessage.warning('最多只能选择5个回测进行对比')
    return
  }
  
  selectedBacktests.value = [...tempSelection.value]
  showSelectDialog.value = false
  
  // 更新图表
  nextTick(() => {
    initCharts()
  })
}

const removeBacktest = (backtestId: number) => {
  selectedBacktests.value = selectedBacktests.value.filter(b => b.id !== backtestId)
  
  if (selectedBacktests.value.length >= 2) {
    nextTick(() => {
      initCharts()
    })
  }
}

const getBestBacktestName = (row: any) => {
  const values = row.values
  const backtestIds = Object.keys(values).map(Number)
  
  let bestId: number
  if (row.higher_better) {
    bestId = backtestIds.reduce((a, b) => values[a] > values[b] ? a : b)
  } else {
    bestId = backtestIds.reduce((a, b) => values[a] < values[b] ? a : b)
  }
  
  const bestBacktest = selectedBacktests.value.find(b => b.id === bestId)
  return bestBacktest?.name || '-'
}

// 格式化函数
const formatDateRange = (config: any) => {
  if (!config) return '-'
  return `${config.start_date} ~ ${config.end_date}`
}

const formatDateTime = (dateString?: string) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString('zh-CN')
}

const formatPercent = (value?: number) => {
  if (value === undefined || value === null) return '-'
  return `${(value * 100).toFixed(2)}%`
}

const formatMetricValue = (value: number, type: string) => {
  if (value === undefined || value === null) return '-'
  
  switch (type) {
    case 'percent':
      return `${(value * 100).toFixed(2)}%`
    case 'number':
      return value.toFixed(2)
    default:
      return value.toString()
  }
}

const getMetricClass = (value: number, type: string) => {
  if (value === undefined || value === null) return ''
  
  if (type === 'percent') {
    return value > 0 ? 'positive' : value < 0 ? 'negative' : 'neutral'
  }
  
  return ''
}

const getStatusTagType = (status: string) => {
  const typeMap: Record<string, string> = {
    completed: 'success',
    running: 'warning',
    failed: 'danger'
  }
  return typeMap[status] || 'info'
}

const getStatusText = (status: string) => {
  const textMap: Record<string, string> = {
    completed: '已完成',
    running: '运行中',
    failed: '失败'
  }
  return textMap[status] || status
}

const getCorrelationClass = (correlation?: number) => {
  if (!correlation) return ''
  
  if (correlation > 0.7) return 'high-correlation'
  if (correlation > 0.3) return 'medium-correlation'
  return 'low-correlation'
}

const getRankTagType = (rank: number) => {
  if (rank === 1) return 'success'
  if (rank <= 3) return 'warning'
  return 'info'
}

const getScoreColor = (score: number) => {
  if (score >= 80) return '#67c23a'
  if (score >= 60) return '#e6a23c'
  return '#f56c6c'
}

// 生命周期
onMounted(() => {
  // 加载回测列表
  if (backtestStore.backtests.length === 0) {
    backtestStore.fetchBacktests()
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  
  equityComparisonChart?.dispose()
  drawdownComparisonChart?.dispose()
  riskReturnScatter?.dispose()
  monthlyReturnsComparison?.dispose()
})
</script>

<style scoped lang="scss">
.backtest-comparison {
  .comparison-selector {
    margin-bottom: 24px;
    
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    
    .selected-backtests {
      .backtest-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px;
        margin-bottom: 8px;
        background: var(--el-bg-color-page);
        border-radius: 6px;
        
        .backtest-info {
          .backtest-name {
            font-weight: 600;
            color: #303133;
            margin-bottom: 4px;
          }
          
          .backtest-meta {
            display: flex;
            align-items: center;
            gap: 8px;
            
            .meta-text {
              font-size: 12px;
              color: #909399;
            }
          }
        }
      }
      
      .empty-selection {
        text-align: center;
        padding: 40px 0;
      }
    }
  }
  
  .comparison-results {
    .metrics-comparison,
    .chart-comparison,
    .correlation-analysis,
    .ranking-analysis {
      margin-bottom: 24px;
    }
    
    .chart-container {
      height: 400px;
    }
    
    .positive {
      color: #67c23a;
      font-weight: 600;
    }
    
    .negative {
      color: #f56c6c;
      font-weight: 600;
    }
    
    .neutral {
      color: #909399;
    }
    
    .high-correlation {
      color: #f56c6c;
      font-weight: 600;
    }
    
    .medium-correlation {
      color: #e6a23c;
      font-weight: 600;
    }
    
    .low-correlation {
      color: #67c23a;
      font-weight: 600;
    }
  }
}
</style>