<template>
  <div class="backtest-result-view">
    <div class="page-header">
      <div class="header-left">
        <el-button @click="goBack" text>
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
        <el-divider direction="vertical" />
        <h2 class="page-title">
          回测结果
          <el-tag v-if="backtest" :type="statusTagType" size="small">
            {{ statusText }}
          </el-tag>
        </h2>
      </div>
      
      <div class="header-actions">
        <el-button @click="handleRefresh" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button @click="handleClone">
          <el-icon><DocumentCopy /></el-icon>
          克隆回测
        </el-button>
        <el-button @click="handleShare">
          <el-icon><Share /></el-icon>
          分享结果
        </el-button>
      </div>
    </div>

    <div v-if="backtest?.status === 'running'" class="progress-section">
      <BacktestProgressMonitor :backtest-id="backtestId" />
    </div>

    <div v-else-if="backtest?.status === 'completed'" class="result-content">
      <el-tabs v-model="activeTab" type="card">
        <!-- 结果报告 -->
        <el-tab-pane label="结果报告" name="report">
          <BacktestResultReport :backtest="backtest" :result="result" />
        </el-tab-pane>
        
        <!-- 交易记录 -->
        <el-tab-pane label="交易记录" name="trades">
          <BacktestTradeRecords :trades="result?.trades || []" />
        </el-tab-pane>
        
        <!-- 持仓分析 -->
        <el-tab-pane label="持仓分析" name="positions">
          <div class="positions-analysis">
            <el-card title="持仓记录">
              <el-table :data="result?.positions || []" height="400">
                <el-table-column prop="date" label="日期" width="120">
                  <template #default="{ row }">
                    {{ formatDate(row.date) }}
                  </template>
                </el-table-column>
                <el-table-column prop="symbol" label="品种" width="120">
                  <template #default="{ row }">
                    <el-tag size="small">{{ row.symbol }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="quantity" label="数量" width="100" align="right">
                  <template #default="{ row }">
                    {{ formatNumber(row.quantity) }}
                  </template>
                </el-table-column>
                <el-table-column prop="market_value" label="市值" width="120" align="right">
                  <template #default="{ row }">
                    {{ formatCurrency(row.market_value) }}
                  </template>
                </el-table-column>
                <el-table-column prop="weight" label="权重" width="100" align="right">
                  <template #default="{ row }">
                    {{ formatPercent(row.weight) }}
                  </template>
                </el-table-column>
                <el-table-column prop="unrealized_pnl" label="浮动盈亏" width="120" align="right">
                  <template #default="{ row }">
                    <span :class="getPnlClass(row.unrealized_pnl)">
                      {{ formatCurrency(row.unrealized_pnl) }}
                    </span>
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </div>
        </el-tab-pane>
        
        <!-- 风险分析 -->
        <el-tab-pane label="风险分析" name="risk">
          <div class="risk-analysis">
            <el-row :gutter="16">
              <el-col :span="12">
                <el-card title="风险指标">
                  <el-descriptions :column="1" border>
                    <el-descriptions-item label="95% VaR">
                      {{ formatPercent(result?.risk_metrics?.var_95) }}
                    </el-descriptions-item>
                    <el-descriptions-item label="99% VaR">
                      {{ formatPercent(result?.risk_metrics?.var_99) }}
                    </el-descriptions-item>
                    <el-descriptions-item label="95% CVaR">
                      {{ formatPercent(result?.risk_metrics?.cvar_95) }}
                    </el-descriptions-item>
                    <el-descriptions-item label="99% CVaR">
                      {{ formatPercent(result?.risk_metrics?.cvar_99) }}
                    </el-descriptions-item>
                    <el-descriptions-item label="偏度">
                      {{ result?.risk_metrics?.skewness?.toFixed(3) || '-' }}
                    </el-descriptions-item>
                    <el-descriptions-item label="峰度">
                      {{ result?.risk_metrics?.kurtosis?.toFixed(3) || '-' }}
                    </el-descriptions-item>
                  </el-descriptions>
                </el-card>
              </el-col>
              
              <el-col :span="12">
                <el-card title="风险分解">
                  <div ref="riskDecompositionChartRef" class="chart-container"></div>
                </el-card>
              </el-col>
            </el-row>
          </div>
        </el-tab-pane>
        
        <!-- 对比分析 -->
        <el-tab-pane label="对比分析" name="comparison">
          <BacktestComparison />
        </el-tab-pane>
      </el-tabs>
    </div>

    <div v-else-if="backtest?.status === 'failed'" class="error-section">
      <el-result
        icon="error"
        title="回测失败"
        :sub-title="backtest.progress?.error_message || '回测执行过程中发生错误'"
      >
        <template #extra>
          <el-button type="primary" @click="handleRetry">重新运行</el-button>
          <el-button @click="goBack">返回列表</el-button>
        </template>
      </el-result>
    </div>

    <div v-else class="loading-section">
      <el-skeleton :rows="10" animated />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft,
  Refresh,
  DocumentCopy,
  Share
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { useBacktestStore } from '@/stores/backtest'
import BacktestProgressMonitor from '@/components/BacktestProgressMonitor.vue'
import BacktestResultReport from '@/components/BacktestResultReport.vue'
import BacktestTradeRecords from '@/components/BacktestTradeRecords.vue'
import BacktestComparison from '@/components/BacktestComparison.vue'
import type { Backtest, BacktestResult } from '@/types/backtest'

const route = useRoute()
const router = useRouter()
const backtestStore = useBacktestStore()

// 响应式数据
const loading = ref(false)
const activeTab = ref('report')
const riskDecompositionChartRef = ref<HTMLElement>()

let riskDecompositionChart: echarts.ECharts | null = null

// 计算属性
const backtestId = computed(() => parseInt(route.params.id as string))
const backtest = computed(() => backtestStore.currentBacktest)
const result = computed(() => backtestStore.currentResult)

const statusTagType = computed(() => {
  if (!backtest.value) return 'info'
  
  const typeMap = {
    pending: 'info',
    running: 'warning',
    completed: 'success',
    failed: 'danger',
    cancelled: 'info'
  }
  return typeMap[backtest.value.status] || 'info'
})

const statusText = computed(() => {
  if (!backtest.value) return ''
  
  const textMap = {
    pending: '等待中',
    running: '运行中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消'
  }
  return textMap[backtest.value.status] || '未知'
})

// 方法
const loadBacktestData = async () => {
  try {
    loading.value = true
    
    await backtestStore.fetchBacktest(backtestId.value)
    
    if (backtest.value?.status === 'completed') {
      await backtestStore.fetchBacktestResult(backtestId.value)
    }
  } catch (error) {
    ElMessage.error('加载回测数据失败')
    goBack()
  } finally {
    loading.value = false
  }
}

const initRiskChart = async () => {
  await nextTick()
  
  if (riskDecompositionChartRef.value) {
    riskDecompositionChart = echarts.init(riskDecompositionChartRef.value)
    updateRiskChart()
  }
}

const updateRiskChart = () => {
  if (!riskDecompositionChart) return
  
  // 模拟风险分解数据
  const riskData = [
    { name: '市场风险', value: 60 },
    { name: '流动性风险', value: 20 },
    { name: '信用风险', value: 10 },
    { name: '操作风险', value: 10 }
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

const handleRefresh = () => {
  loadBacktestData()
}

const handleClone = async () => {
  if (!backtest.value) return
  
  try {
    const { value: name } = await ElMessageBox.prompt(
      '请输入新回测的名称',
      '克隆回测',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputValue: `${backtest.value.name} - 副本`,
        inputValidator: (value) => {
          if (!value || value.trim().length === 0) {
            return '回测名称不能为空'
          }
          return true
        }
      }
    )
    
    await backtestStore.cloneBacktest(backtest.value.id, name)
    ElMessage.success('回测克隆成功')
  } catch (error) {
    // 用户取消或错误已在store中处理
  }
}

const handleShare = () => {
  // 生成分享链接
  const shareUrl = `${window.location.origin}/backtests/${backtestId.value}/share`
  
  navigator.clipboard.writeText(shareUrl).then(() => {
    ElMessage.success('分享链接已复制到剪贴板')
  }).catch(() => {
    ElMessage.error('复制失败')
  })
}

const handleRetry = async () => {
  if (!backtest.value) return
  
  try {
    await backtestStore.startBacktest(backtest.value.id)
    ElMessage.success('回测已重新启动')
    await loadBacktestData()
  } catch (error) {
    // 错误已在store中处理
  }
}

const goBack = () => {
  router.push('/backtests')
}

// 格式化函数
const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('zh-CN')
}

const formatNumber = (num: number) => {
  return new Intl.NumberFormat('zh-CN').format(num)
}

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY'
  }).format(value)
}

const formatPercent = (value?: number) => {
  if (value === undefined || value === null) return '-'
  return `${(value * 100).toFixed(2)}%`
}

const getPnlClass = (pnl: number) => {
  if (pnl > 0) return 'profit'
  if (pnl < 0) return 'loss'
  return 'neutral'
}

// 生命周期
onMounted(() => {
  loadBacktestData()
  
  // 监听标签页切换，初始化图表
  nextTick(() => {
    if (activeTab.value === 'risk') {
      initRiskChart()
    }
  })
})

onUnmounted(() => {
  riskDecompositionChart?.dispose()
  backtestStore.clearCurrentBacktest()
})
</script>

<style scoped lang="scss">
.backtest-result-view {
  padding: 20px;
  
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    
    .header-left {
      display: flex;
      align-items: center;
      gap: 12px;
      
      .page-title {
        margin: 0;
        font-size: 20px;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 8px;
      }
    }
    
    .header-actions {
      display: flex;
      gap: 12px;
    }
  }
  
  .progress-section {
    margin-bottom: 20px;
  }
  
  .result-content {
    background: var(--el-bg-color);
    border-radius: 8px;
    overflow: hidden;
    
    .positions-analysis,
    .risk-analysis {
      padding: 20px;
      
      .chart-container {
        height: 300px;
      }
    }
    
    .profit {
      color: #67c23a;
      font-weight: 600;
    }
    
    .loss {
      color: #f56c6c;
      font-weight: 600;
    }
    
    .neutral {
      color: #909399;
    }
  }
  
  .error-section {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 400px;
  }
  
  .loading-section {
    padding: 40px;
  }
}

:deep(.el-tabs__content) {
  padding: 0;
}
</style>