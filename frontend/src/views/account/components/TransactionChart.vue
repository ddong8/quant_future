<template>
  <div class="transaction-chart">
    <el-row :gutter="16">
      <!-- 图表类型选择 -->
      <el-col :span="24">
        <div class="chart-controls">
          <el-radio-group v-model="chartType" @change="handleChartTypeChange">
            <el-radio-button label="daily">每日趋势</el-radio-button>
            <el-radio-button label="type">类型分布</el-radio-button>
            <el-radio-button label="cashflow">现金流</el-radio-button>
          </el-radio-group>
          
          <div class="chart-actions">
            <el-button size="small" @click="refreshChart">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 图表容器 -->
    <el-row :gutter="16" class="chart-row">
      <el-col :span="24">
        <div class="chart-container">
          <!-- 每日趋势图 -->
          <div v-if="chartType === 'daily'" ref="dailyChartRef" class="chart" />
          
          <!-- 类型分布图 -->
          <div v-else-if="chartType === 'type'" class="type-charts">
            <el-row :gutter="16">
              <el-col :span="12">
                <div ref="typeChartRef" class="chart" />
              </el-col>
              <el-col :span="12">
                <div ref="statusChartRef" class="chart" />
              </el-col>
            </el-row>
          </div>
          
          <!-- 现金流图 -->
          <div v-else-if="chartType === 'cashflow'" ref="cashflowChartRef" class="chart" />
        </div>
      </el-col>
    </el-row>

    <!-- 统计摘要 -->
    <el-row :gutter="16" class="summary-row">
      <el-col :span="6">
        <el-statistic
          title="总交易数"
          :value="statistics.summary?.total_transactions || 0"
          :precision="0"
        />
      </el-col>
      <el-col :span="6">
        <el-statistic
          title="总收入"
          :value="statistics.summary?.total_income || 0"
          :precision="2"
          prefix="$"
        />
      </el-col>
      <el-col :span="6">
        <el-statistic
          title="总支出"
          :value="statistics.summary?.total_expense || 0"
          :precision="2"
          prefix="$"
        />
      </el-col>
      <el-col :span="6">
        <el-statistic
          title="净流量"
          :value="statistics.summary?.net_flow || 0"
          :precision="2"
          prefix="$"
          :value-style="{ 
            color: (statistics.summary?.net_flow || 0) >= 0 ? '#3f8600' : '#cf1322' 
          }"
        />
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import type { ECharts } from 'echarts'
import { 
  type TransactionStatistics,
  getCashFlowAnalysis,
  getTransactionCategories,
  TransactionTypeLabels
} from '@/api/transaction'

interface Props {
  statistics: TransactionStatistics
}

const props = defineProps<Props>()

// 响应式数据
const chartType = ref<'daily' | 'type' | 'cashflow'>('daily')
const dailyChartRef = ref<HTMLElement>()
const typeChartRef = ref<HTMLElement>()
const statusChartRef = ref<HTMLElement>()
const cashflowChartRef = ref<HTMLElement>()

// 图表实例
let dailyChart: ECharts | null = null
let typeChart: ECharts | null = null
let statusChart: ECharts | null = null
let cashflowChart: ECharts | null = null

// 方法
const initDailyChart = () => {
  if (!dailyChartRef.value || !props.statistics.daily_stats) return

  dailyChart = echarts.init(dailyChartRef.value)
  
  const dates = props.statistics.daily_stats.map(item => item.date)
  const amounts = props.statistics.daily_stats.map(item => item.total_amount)
  const counts = props.statistics.daily_stats.map(item => item.count)

  const option = {
    title: {
      text: '每日交易趋势',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: ['交易金额', '交易笔数'],
      top: 30
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLabel: {
        formatter: (value: string) => {
          return new Date(value).toLocaleDateString('zh-CN', { 
            month: 'short', 
            day: 'numeric' 
          })
        }
      }
    },
    yAxis: [
      {
        type: 'value',
        name: '金额',
        position: 'left',
        axisLabel: {
          formatter: '${value}'
        }
      },
      {
        type: 'value',
        name: '笔数',
        position: 'right'
      }
    ],
    series: [
      {
        name: '交易金额',
        type: 'line',
        yAxisIndex: 0,
        data: amounts,
        smooth: true,
        itemStyle: {
          color: '#409EFF'
        },
        areaStyle: {
          opacity: 0.3
        }
      },
      {
        name: '交易笔数',
        type: 'bar',
        yAxisIndex: 1,
        data: counts,
        itemStyle: {
          color: '#67C23A'
        }
      }
    ],
    grid: {
      top: 80,
      bottom: 60,
      left: 60,
      right: 60
    }
  }

  dailyChart.setOption(option)
}

const initTypeChart = async () => {
  if (!typeChartRef.value) return

  try {
    const categories = await getTransactionCategories()
    
    typeChart = echarts.init(typeChartRef.value)
    
    const typeData = categories.by_type.map(item => ({
      name: TransactionTypeLabels[item.type] || item.type,
      value: Math.abs(item.total_amount)
    }))

    const option = {
      title: {
        text: '交易类型分布',
        left: 'center'
      },
      tooltip: {
        trigger: 'item',
        formatter: '{a} <br/>{b}: ${c} ({d}%)'
      },
      legend: {
        orient: 'vertical',
        left: 'left',
        top: 'middle'
      },
      series: [
        {
          name: '交易类型',
          type: 'pie',
          radius: ['40%', '70%'],
          center: ['60%', '50%'],
          data: typeData,
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          }
        }
      ]
    }

    typeChart.setOption(option)
  } catch (error) {
    console.error('初始化类型图表失败:', error)
  }
}

const initStatusChart = async () => {
  if (!statusChartRef.value) return

  try {
    const categories = await getTransactionCategories()
    
    statusChart = echarts.init(statusChartRef.value)
    
    const statusData = categories.by_status.map(item => ({
      name: item.status,
      value: item.count
    }))

    const option = {
      title: {
        text: '交易状态分布',
        left: 'center'
      },
      tooltip: {
        trigger: 'item',
        formatter: '{a} <br/>{b}: {c} ({d}%)'
      },
      legend: {
        orient: 'vertical',
        left: 'left',
        top: 'middle'
      },
      series: [
        {
          name: '交易状态',
          type: 'pie',
          radius: '60%',
          center: ['60%', '50%'],
          data: statusData,
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          }
        }
      ]
    }

    statusChart.setOption(option)
  } catch (error) {
    console.error('初始化状态图表失败:', error)
  }
}

const initCashflowChart = async () => {
  if (!cashflowChartRef.value) return

  try {
    const cashflowData = await getCashFlowAnalysis('month')
    
    cashflowChart = echarts.init(cashflowChartRef.value)
    
    const periods = cashflowData.cash_flow_data.map(item => item.period)
    const inflows = cashflowData.cash_flow_data.map(item => item.inflow)
    const outflows = cashflowData.cash_flow_data.map(item => -item.outflow) // 负值显示
    const netFlows = cashflowData.cash_flow_data.map(item => item.net_flow)

    const option = {
      title: {
        text: '现金流分析',
        left: 'center'
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross'
        }
      },
      legend: {
        data: ['流入', '流出', '净流量'],
        top: 30
      },
      xAxis: {
        type: 'category',
        data: periods,
        axisLabel: {
          formatter: (value: string) => {
            return new Date(value).toLocaleDateString('zh-CN', { 
              month: 'short', 
              day: 'numeric' 
            })
          }
        }
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          formatter: '${value}'
        }
      },
      series: [
        {
          name: '流入',
          type: 'bar',
          stack: 'cashflow',
          data: inflows,
          itemStyle: {
            color: '#67C23A'
          }
        },
        {
          name: '流出',
          type: 'bar',
          stack: 'cashflow',
          data: outflows,
          itemStyle: {
            color: '#F56C6C'
          }
        },
        {
          name: '净流量',
          type: 'line',
          data: netFlows,
          smooth: true,
          itemStyle: {
            color: '#409EFF'
          },
          lineStyle: {
            width: 3
          }
        }
      ],
      grid: {
        top: 80,
        bottom: 60,
        left: 60,
        right: 40
      }
    }

    cashflowChart.setOption(option)
  } catch (error) {
    console.error('初始化现金流图表失败:', error)
  }
}

const handleChartTypeChange = async () => {
  await nextTick()
  
  if (chartType.value === 'daily') {
    initDailyChart()
  } else if (chartType.value === 'type') {
    initTypeChart()
    initStatusChart()
  } else if (chartType.value === 'cashflow') {
    initCashflowChart()
  }
}

const refreshChart = () => {
  handleChartTypeChange()
}

const resizeCharts = () => {
  dailyChart?.resize()
  typeChart?.resize()
  statusChart?.resize()
  cashflowChart?.resize()
}

const disposeCharts = () => {
  dailyChart?.dispose()
  typeChart?.dispose()
  statusChart?.dispose()
  cashflowChart?.dispose()
}

// 监听统计数据变化
watch(() => props.statistics, () => {
  if (chartType.value === 'daily') {
    initDailyChart()
  }
}, { deep: true })

// 生命周期
onMounted(() => {
  nextTick(() => {
    initDailyChart()
  })
  
  // 监听窗口大小变化
  window.addEventListener('resize', resizeCharts)
})

onUnmounted(() => {
  disposeCharts()
  window.removeEventListener('resize', resizeCharts)
})
</script>

<style scoped>
.transaction-chart {
  padding: 20px;
}

.chart-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 16px;
  background-color: #f5f7fa;
  border-radius: 8px;
}

.chart-actions {
  display: flex;
  gap: 8px;
}

.chart-row {
  margin-bottom: 20px;
}

.chart-container {
  background-color: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.chart {
  width: 100%;
  height: 400px;
}

.type-charts .chart {
  height: 350px;
}

.summary-row {
  margin-top: 20px;
}

.summary-row .el-col {
  text-align: center;
  padding: 20px;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.summary-row .el-col:not(:last-child) {
  margin-right: 16px;
}
</style>