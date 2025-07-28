<template>
  <div class="risk-monitor-dashboard">
    <!-- 风险概览 -->
    <div class="risk-overview">
      <el-row :gutter="16">
        <el-col :span="6">
          <div class="risk-card critical">
            <div class="risk-icon">
              <el-icon><Warning /></el-icon>
            </div>
            <div class="risk-content">
              <div class="risk-value">{{ riskMetrics?.margin_ratio ? formatPercent(riskMetrics.margin_ratio) : '-' }}</div>
              <div class="risk-label">保证金比率</div>
              <div class="risk-status" :class="getMarginRiskLevel()">
                {{ getMarginRiskText() }}
              </div>
            </div>
          </div>
        </el-col>
        
        <el-col :span="6">
          <div class="risk-card high">
            <div class="risk-icon">
              <el-icon><TrendCharts /></el-icon>
            </div>
            <div class="risk-content">
              <div class="risk-value">{{ riskMetrics?.var_1d ? formatCurrency(riskMetrics.var_1d) : '-' }}</div>
              <div class="risk-label">1日VaR</div>
              <div class="risk-status">
                95%置信度
              </div>
            </div>
          </div>
        </el-col>
        
        <el-col :span="6">
          <div class="risk-card medium">
            <div class="risk-icon">
              <el-icon><PieChart /></el-icon>
            </div>
            <div class="risk-content">
              <div class="risk-value">{{ riskMetrics?.concentration_risk ? formatPercent(riskMetrics.concentration_risk) : '-' }}</div>
              <div class="risk-label">集中度风险</div>
              <div class="risk-status">
                最大权重: {{ riskMetrics?.max_position_weight ? formatPercent(riskMetrics.max_position_weight) : '-' }}
              </div>
            </div>
          </div>
        </el-col>
        
        <el-col :span="6">
          <div class="risk-card low">
            <div class="risk-icon">
              <el-icon><DataAnalysis /></el-icon>
            </div>
            <div class="risk-content">
              <div class="risk-value">{{ riskMetrics?.liquidity_risk ? formatPercent(riskMetrics.liquidity_risk) : '-' }}</div>
              <div class="risk-label">流动性风险</div>
              <div class="risk-status">
                {{ getLiquidityRiskText() }}
              </div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 风险图表 -->
    <div class="risk-charts">
      <el-row :gutter="16">
        <!-- VaR趋势图 -->
        <el-col :span="12">
          <el-card title="VaR趋势">
            <div ref="varTrendChartRef" class="chart-container"></div>
          </el-card>
        </el-col>
        
        <!-- 风险分解 -->
        <el-col :span="12">
          <el-card title="风险分解">
            <div ref="riskDecompositionChartRef" class="chart-container"></div>
          </el-card>
        </el-col>
      </el-row>
      
      <el-row :gutter="16" style="margin-top: 16px">
        <!-- 保证金使用情况 -->
        <el-col :span="12">
          <el-card title="保证金使用情况">
            <div class="margin-usage">
              <div class="margin-item">
                <span class="label">总权益:</span>
                <span class="value">{{ formatCurrency(account?.total_equity || 0) }}</span>
              </div>
              <div class="margin-item">
                <span class="label">已用保证金:</span>
                <span class="value used">{{ formatCurrency(account?.margin_used || 0) }}</span>
              </div>
              <div class="margin-item">
                <span class="label">可用保证金:</span>
                <span class="value available">{{ formatCurrency(account?.margin_available || 0) }}</span>
              </div>
              <div class="margin-item">
                <span class="label">维持保证金:</span>
                <span class="value maintenance">{{ formatCurrency(account?.maintenance_margin || 0) }}</span>
              </div>
              
              <div class="margin-progress">
                <el-progress
                  :percentage="getMarginUsagePercent()"
                  :color="getMarginProgressColor()"
                  :stroke-width="8"
                />
                <div class="progress-label">
                  保证金使用率: {{ formatPercent(getMarginUsagePercent() / 100) }}
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <!-- 持仓风险分布 -->
        <el-col :span="12">
          <el-card title="持仓风险分布">
            <div ref="positionRiskChartRef" class="chart-container"></div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 风险预警 -->
    <div class="risk-alerts">
      <el-card title="风险预警">
        <div class="alerts-list">
          <div
            v-for="alert in riskAlerts"
            :key="alert.id"
            class="alert-item"
            :class="alert.level"
          >
            <div class="alert-icon">
              <el-icon>
                <Warning v-if="alert.level === 'critical'" />
                <InfoFilled v-else-if="alert.level === 'high'" />
                <QuestionFilled v-else />
              </el-icon>
            </div>
            <div class="alert-content">
              <div class="alert-title">{{ alert.title }}</div>
              <div class="alert-message">{{ alert.message }}</div>
              <div class="alert-time">{{ formatDateTime(alert.timestamp) }}</div>
            </div>
            <div class="alert-actions">
              <el-button text size="small" @click="handleAlert(alert)">
                处理
              </el-button>
              <el-button text size="small" @click="dismissAlert(alert.id)">
                忽略
              </el-button>
            </div>
          </div>
          
          <div v-if="riskAlerts.length === 0" class="no-alerts">
            <el-empty description="暂无风险预警" />
          </div>
        </div>
      </el-card>
    </div>

    <!-- 风险限制设置 -->
    <div class="risk-limits">
      <el-card title="风险限制">
        <el-row :gutter="16">
          <el-col :span="8">
            <div class="limit-item">
              <div class="limit-label">最大持仓比例</div>
              <div class="limit-value">
                {{ formatPercent(riskLimits.max_position_ratio) }}
                <el-button text size="small" @click="showLimitDialog('max_position_ratio')">
                  修改
                </el-button>
              </div>
              <div class="limit-usage">
                当前: {{ formatPercent(getCurrentPositionRatio()) }}
              </div>
            </div>
          </el-col>
          
          <el-col :span="8">
            <div class="limit-item">
              <div class="limit-label">最大日损失</div>
              <div class="limit-value">
                {{ formatCurrency(riskLimits.max_daily_loss) }}
                <el-button text size="small" @click="showLimitDialog('max_daily_loss')">
                  修改
                </el-button>
              </div>
              <div class="limit-usage">
                当前: {{ formatCurrency(account?.day_pnl || 0) }}
              </div>
            </div>
          </el-col>
          
          <el-col :span="8">
            <div class="limit-item">
              <div class="limit-label">最大回撤</div>
              <div class="limit-value">
                {{ formatPercent(riskLimits.max_drawdown) }}
                <el-button text size="small" @click="showLimitDialog('max_drawdown')">
                  修改
                </el-button>
              </div>
              <div class="limit-usage">
                当前: {{ formatPercent(getCurrentDrawdown()) }}
              </div>
            </div>
          </el-col>
        </el-row>
      </el-card>
    </div>

    <!-- 风险限制修改对话框 -->
    <el-dialog v-model="showLimitEditDialog" title="修改风险限制" width="400px">
      <el-form :model="limitForm" label-width="120px">
        <el-form-item :label="getLimitLabel()">
          <el-input-number
            v-model="limitForm.value"
            :min="0"
            :max="getLimitMax()"
            :step="getLimitStep()"
            :precision="getLimitPrecision()"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="生效时间">
          <el-radio-group v-model="limitForm.effective_time">
            <el-radio label="immediate">立即生效</el-radio>
            <el-radio label="next_trading_day">下个交易日</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showLimitEditDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmLimitChange" :loading="loading">
          确认修改
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Warning,
  TrendCharts,
  PieChart,
  DataAnalysis,
  InfoFilled,
  QuestionFilled
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { useTradingStore } from '@/stores/trading'
import type { RiskMetrics, TradingAccount } from '@/types/trading'

const tradingStore = useTradingStore()

// 响应式数据
const loading = ref(false)
const showLimitEditDialog = ref(false)
const riskMetrics = ref<RiskMetrics | null>(null)
const riskAlerts = ref<any[]>([
  {
    id: 1,
    level: 'critical',
    title: '保证金不足警告',
    message: '当前保证金比率已接近维持保证金要求，请及时补充资金或减少持仓',
    timestamp: new Date().toISOString()
  },
  {
    id: 2,
    level: 'high',
    title: '集中度风险',
    message: '单一品种持仓占比过高，建议分散投资降低风险',
    timestamp: new Date(Date.now() - 3600000).toISOString()
  }
])

// 风险限制
const riskLimits = ref({
  max_position_ratio: 0.8,
  max_daily_loss: 50000,
  max_drawdown: 0.2
})

// 限制修改表单
const limitForm = ref({
  type: '',
  value: 0,
  effective_time: 'immediate'
})

// 图表实例
const varTrendChartRef = ref<HTMLElement>()
const riskDecompositionChartRef = ref<HTMLElement>()
const positionRiskChartRef = ref<HTMLElement>()

let varTrendChart: echarts.ECharts | null = null
let riskDecompositionChart: echarts.ECharts | null = null
let positionRiskChart: echarts.ECharts | null = null

// 计算属性
const account = computed(() => tradingStore.currentAccount)

// 方法
const initCharts = async () => {
  await nextTick()
  
  if (varTrendChartRef.value) {
    varTrendChart = echarts.init(varTrendChartRef.value)
    updateVarTrendChart()
  }
  
  if (riskDecompositionChartRef.value) {
    riskDecompositionChart = echarts.init(riskDecompositionChartRef.value)
    updateRiskDecompositionChart()
  }
  
  if (positionRiskChartRef.value) {
    positionRiskChart = echarts.init(positionRiskChartRef.value)
    updatePositionRiskChart()
  }
  
  window.addEventListener('resize', handleResize)
}

const updateVarTrendChart = () => {
  if (!varTrendChart) return
  
  // 模拟VaR趋势数据
  const dates = Array.from({ length: 30 }, (_, i) => {
    const date = new Date()
    date.setDate(date.getDate() - 29 + i)
    return date.toLocaleDateString('zh-CN')
  })
  
  const var1d = Array.from({ length: 30 }, () => Math.random() * 10000 + 5000)
  const var5d = Array.from({ length: 30 }, () => Math.random() * 20000 + 10000)
  
  const option = {
    title: {
      text: 'VaR趋势',
      textStyle: { fontSize: 14 }
    },
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['1日VaR', '5日VaR']
    },
    xAxis: {
      type: 'category',
      data: dates
    },
    yAxis: {
      type: 'value',
      name: 'VaR值'
    },
    series: [
      {
        name: '1日VaR',
        type: 'line',
        data: var1d,
        smooth: true,
        lineStyle: { color: '#f56c6c' }
      },
      {
        name: '5日VaR',
        type: 'line',
        data: var5d,
        smooth: true,
        lineStyle: { color: '#e6a23c' }
      }
    ]
  }
  
  varTrendChart.setOption(option)
}

const updateRiskDecompositionChart = () => {
  if (!riskDecompositionChart) return
  
  const riskData = [
    { name: '市场风险', value: 60 },
    { name: '信用风险', value: 20 },
    { name: '流动性风险', value: 15 },
    { name: '操作风险', value: 5 }
  ]
  
  const option = {
    title: {
      text: '风险分解',
      textStyle: { fontSize: 14 }
    },
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c}% ({d}%)'
    },
    series: [{
      name: '风险分解',
      type: 'pie',
      radius: '60%',
      data: riskData,
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }]
  }
  
  riskDecompositionChart.setOption(option)
}

const updatePositionRiskChart = () => {
  if (!positionRiskChart) return
  
  // 模拟持仓风险数据
  const positions = ['SHFE.cu2401', 'DCE.i2401', 'CZCE.MA401', 'CFFEX.IF2401']
  const riskValues = [25, 35, 20, 30]
  
  const option = {
    title: {
      text: '持仓风险分布',
      textStyle: { fontSize: 14 }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    xAxis: {
      type: 'category',
      data: positions
    },
    yAxis: {
      type: 'value',
      name: '风险值'
    },
    series: [{
      data: riskValues.map(value => ({
        value,
        itemStyle: {
          color: value > 30 ? '#f56c6c' : value > 20 ? '#e6a23c' : '#67c23a'
        }
      })),
      type: 'bar'
    }]
  }
  
  positionRiskChart.setOption(option)
}

const handleResize = () => {
  varTrendChart?.resize()
  riskDecompositionChart?.resize()
  positionRiskChart?.resize()
}

const loadRiskData = async () => {
  const accountId = account.value?.id
  if (!accountId) return
  
  try {
    // 加载风险指标
    // const response = await tradingApi.getRiskMetrics(accountId)
    // riskMetrics.value = response.data.metrics
    
    // 模拟数据
    riskMetrics.value = {
      account_id: accountId,
      margin_ratio: 0.75,
      maintenance_margin_ratio: 0.3,
      buying_power_ratio: 0.25,
      concentration_risk: 0.35,
      max_position_weight: 0.4,
      liquidity_risk: 0.15,
      var_1d: 8500,
      var_5d: 18000,
      stress_test_result: 0.12,
      last_updated: new Date().toISOString()
    }
  } catch (error) {
    ElMessage.error('加载风险数据失败')
  }
}

const getMarginRiskLevel = () => {
  const ratio = riskMetrics.value?.margin_ratio || 0
  if (ratio > 0.8) return 'critical'
  if (ratio > 0.6) return 'high'
  if (ratio > 0.4) return 'medium'
  return 'low'
}

const getMarginRiskText = () => {
  const level = getMarginRiskLevel()
  const textMap = {
    critical: '高风险',
    high: '中高风险',
    medium: '中等风险',
    low: '低风险'
  }
  return textMap[level]
}

const getLiquidityRiskText = () => {
  const risk = riskMetrics.value?.liquidity_risk || 0
  if (risk > 0.3) return '流动性不足'
  if (risk > 0.2) return '流动性一般'
  return '流动性充足'
}

const getMarginUsagePercent = () => {
  if (!account.value) return 0
  const total = account.value.total_equity
  const used = account.value.margin_used
  return total > 0 ? (used / total) * 100 : 0
}

const getMarginProgressColor = () => {
  const percent = getMarginUsagePercent()
  if (percent > 80) return '#f56c6c'
  if (percent > 60) return '#e6a23c'
  return '#67c23a'
}

const getCurrentPositionRatio = () => {
  // 模拟当前持仓比例
  return 0.65
}

const getCurrentDrawdown = () => {
  // 模拟当前回撤
  return 0.08
}

const handleAlert = (alert: any) => {
  ElMessage.info(`处理预警: ${alert.title}`)
}

const dismissAlert = (alertId: number) => {
  riskAlerts.value = riskAlerts.value.filter(alert => alert.id !== alertId)
}

const showLimitDialog = (type: string) => {
  limitForm.value.type = type
  limitForm.value.value = (riskLimits.value as any)[type]
  limitForm.value.effective_time = 'immediate'
  showLimitEditDialog.value = true
}

const getLimitLabel = () => {
  const labelMap: Record<string, string> = {
    max_position_ratio: '最大持仓比例',
    max_daily_loss: '最大日损失',
    max_drawdown: '最大回撤'
  }
  return labelMap[limitForm.value.type] || ''
}

const getLimitMax = () => {
  const maxMap: Record<string, number> = {
    max_position_ratio: 1,
    max_daily_loss: 1000000,
    max_drawdown: 1
  }
  return maxMap[limitForm.value.type] || 100
}

const getLimitStep = () => {
  const stepMap: Record<string, number> = {
    max_position_ratio: 0.01,
    max_daily_loss: 1000,
    max_drawdown: 0.01
  }
  return stepMap[limitForm.value.type] || 1
}

const getLimitPrecision = () => {
  const precisionMap: Record<string, number> = {
    max_position_ratio: 2,
    max_daily_loss: 0,
    max_drawdown: 2
  }
  return precisionMap[limitForm.value.type] || 0
}

const confirmLimitChange = async () => {
  try {
    loading.value = true
    
    // 更新风险限制
    (riskLimits.value as any)[limitForm.value.type] = limitForm.value.value
    
    ElMessage.success('风险限制更新成功')
    showLimitEditDialog.value = false
  } catch (error) {
    ElMessage.error('更新风险限制失败')
  } finally {
    loading.value = false
  }
}

// 格式化函数
const formatPercent = (value: number) => {
  return `${(value * 100).toFixed(1)}%`
}

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY'
  }).format(value)
}

const formatDateTime = (dateString: string) => {
  return new Date(dateString).toLocaleString('zh-CN')
}

// 生命周期
onMounted(() => {
  loadRiskData()
  initCharts()
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  
  varTrendChart?.dispose()
  riskDecompositionChart?.dispose()
  positionRiskChart?.dispose()
})
</script><style 
scoped lang="scss">
.risk-monitor-dashboard {
  .risk-overview {
    margin-bottom: 24px;
    
    .risk-card {
      display: flex;
      align-items: center;
      padding: 20px;
      background: #fff;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
      border-left: 4px solid;
      
      &.critical {
        border-left-color: #f56c6c;
        
        .risk-icon {
          background: #fef0f0;
          color: #f56c6c;
        }
      }
      
      &.high {
        border-left-color: #e6a23c;
        
        .risk-icon {
          background: #fdf6ec;
          color: #e6a23c;
        }
      }
      
      &.medium {
        border-left-color: #409eff;
        
        .risk-icon {
          background: #ecf5ff;
          color: #409eff;
        }
      }
      
      &.low {
        border-left-color: #67c23a;
        
        .risk-icon {
          background: #f0f9ff;
          color: #67c23a;
        }
      }
      
      .risk-icon {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        margin-right: 16px;
      }
      
      .risk-content {
        flex: 1;
        
        .risk-value {
          font-size: 24px;
          font-weight: 600;
          color: #303133;
          line-height: 1;
          margin-bottom: 4px;
        }
        
        .risk-label {
          font-size: 14px;
          color: #606266;
          margin-bottom: 4px;
        }
        
        .risk-status {
          font-size: 12px;
          color: #909399;
          
          &.critical {
            color: #f56c6c;
            font-weight: 600;
          }
          
          &.high {
            color: #e6a23c;
            font-weight: 600;
          }
        }
      }
    }
  }
  
  .risk-charts {
    margin-bottom: 24px;
    
    .chart-container {
      height: 300px;
    }
    
    .margin-usage {
      padding: 16px;
      
      .margin-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
        
        .label {
          font-size: 14px;
          color: #606266;
        }
        
        .value {
          font-size: 14px;
          font-weight: 600;
          color: #303133;
          
          &.used {
            color: #e6a23c;
          }
          
          &.available {
            color: #67c23a;
          }
          
          &.maintenance {
            color: #f56c6c;
          }
        }
      }
      
      .margin-progress {
        margin-top: 16px;
        
        .progress-label {
          text-align: center;
          margin-top: 8px;
          font-size: 12px;
          color: #909399;
        }
      }
    }
  }
  
  .risk-alerts {
    margin-bottom: 24px;
    
    .alerts-list {
      .alert-item {
        display: flex;
        align-items: flex-start;
        padding: 16px;
        margin-bottom: 12px;
        border-radius: 6px;
        border-left: 4px solid;
        
        &.critical {
          background: #fef0f0;
          border-left-color: #f56c6c;
          
          .alert-icon {
            color: #f56c6c;
          }
        }
        
        .alert-icon {
          margin-right: 12px;
          margin-top: 2px;
        }
        
        .alert-content {
          flex: 1;
          
          .alert-title {
            font-size: 14px;
            font-weight: 600;
            color: #303133;
            margin-bottom: 4px;
          }
          
          .alert-message {
            font-size: 13px;
            color: #606266;
            line-height: 1.4;
            margin-bottom: 4px;
          }
          
          .alert-time {
            font-size: 12px;
            color: #909399;
          }
        }
        
        .alert-actions {
          margin-left: 12px;
        }
        
        &.high {
          background: #fdf6ec;
          border-left-color: #e6a23c;
          
          .alert-icon {
            color: #e6a23c;
          }
        }
        
        &.medium {
          background: #ecf5ff;
          border-left-color: #409eff;
          
          .alert-icon {
            color: #409eff;
          }
        }
      }
      
      .no-alerts {
        text-align: center;
        padding: 40px 0;
      }
    }
  }
  
  .risk-limits {
    margin-bottom: 24px;
    
    .limit-item {
      text-align: center;
      padding: 16px;
      background: #f8f9fa;
      border-radius: 6px;
      
      .limit-label {
        font-size: 14px;
        color: #606266;
        margin-bottom: 8px;
      }
      
      .limit-value {
        font-size: 18px;
        font-weight: 600;
        color: #303133;
        margin-bottom: 4px;
        
        .el-button {
          margin-left: 8px;
          font-size: 12px;
        }
      }
      
      .limit-usage {
        font-size: 12px;
        color: #909399;
      }
    }
  }
}
</style>