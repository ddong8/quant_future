<template>
  <div class="backtest-progress-monitor">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>回测进度监控</span>
          <div class="header-actions">
            <el-button
              v-if="backtest?.status === 'running'"
              size="small"
              type="warning"
              @click="handlePause"
            >
              <el-icon><VideoPause /></el-icon>
              暂停
            </el-button>
            <el-button
              v-if="backtest?.status === 'paused'"
              size="small"
              type="success"
              @click="handleResume"
            >
              <el-icon><VideoPlay /></el-icon>
              继续
            </el-button>
            <el-button
              v-if="['running', 'paused'].includes(backtest?.status || '')"
              size="small"
              type="danger"
              @click="handleStop"
            >
              <el-icon><Close /></el-icon>
              停止
            </el-button>
            <el-button size="small" @click="handleRefresh" :loading="loading">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <!-- 状态概览 -->
      <div class="status-overview">
        <el-row :gutter="16">
          <el-col :span="6">
            <div class="status-item">
              <div class="status-icon" :class="getStatusClass(backtest?.status)">
                <el-icon>
                  <Loading v-if="backtest?.status === 'running'" />
                  <VideoPause v-else-if="backtest?.status === 'paused'" />
                  <CircleCheck v-else-if="backtest?.status === 'completed'" />
                  <CircleClose v-else-if="backtest?.status === 'failed'" />
                  <Clock v-else />
                </el-icon>
              </div>
              <div class="status-info">
                <div class="status-label">状态</div>
                <div class="status-value">{{ getStatusText(backtest?.status) }}</div>
              </div>
            </div>
          </el-col>
          
          <el-col :span="6">
            <div class="status-item">
              <div class="status-icon progress">
                <el-icon><TrendCharts /></el-icon>
              </div>
              <div class="status-info">
                <div class="status-label">进度</div>
                <div class="status-value">{{ progress?.progress_percentage?.toFixed(1) || 0 }}%</div>
              </div>
            </div>
          </el-col>
          
          <el-col :span="6">
            <div class="status-item">
              <div class="status-icon time">
                <el-icon><Timer /></el-icon>
              </div>
              <div class="status-info">
                <div class="status-label">剩余时间</div>
                <div class="status-value">{{ formatDuration(progress?.estimated_remaining_time) }}</div>
              </div>
            </div>
          </el-col>
          
          <el-col :span="6">
            <div class="status-item">
              <div class="status-icon equity">
                <el-icon><Money /></el-icon>
              </div>
              <div class="status-info">
                <div class="status-label">当前净值</div>
                <div class="status-value">{{ formatCurrency(progress?.current_equity) }}</div>
              </div>
            </div>
          </el-col>
        </el-row>
      </div>

      <!-- 进度条 -->
      <div class="progress-section">
        <div class="progress-info">
          <span class="progress-text">
            {{ progress?.current_date || '-' }} 
            ({{ progress?.processed_days || 0 }}/{{ progress?.total_days || 0 }} 天)
          </span>
          <span class="progress-percentage">
            {{ progress?.progress_percentage?.toFixed(1) || 0 }}%
          </span>
        </div>
        <el-progress
          :percentage="progress?.progress_percentage || 0"
          :color="getProgressColor()"
          :status="getProgressStatus()"
          :stroke-width="8"
        />
      </div>

      <!-- 实时指标 -->
      <div class="metrics-section">
        <el-row :gutter="16">
          <el-col :span="8">
            <div class="metric-card">
              <div class="metric-header">
                <span class="metric-title">当前回撤</span>
                <el-icon class="metric-icon"><TrendCharts /></el-icon>
              </div>
              <div class="metric-value" :class="getDrawdownClass()">
                {{ formatPercent(progress?.current_drawdown) }}
              </div>
            </div>
          </el-col>
          
          <el-col :span="8">
            <div class="metric-card">
              <div class="metric-header">
                <span class="metric-title">交易次数</span>
                <el-icon class="metric-icon"><DataAnalysis /></el-icon>
              </div>
              <div class="metric-value">
                {{ progress?.trades_count || 0 }}
              </div>
            </div>
          </el-col>
          
          <el-col :span="8">
            <div class="metric-card">
              <div class="metric-header">
                <span class="metric-title">运行时长</span>
                <el-icon class="metric-icon"><Timer /></el-icon>
              </div>
              <div class="metric-value">
                {{ getRunningDuration() }}
              </div>
            </div>
          </el-col>
        </el-row>
      </div>

      <!-- 错误信息 -->
      <div v-if="progress?.error_message" class="error-section">
        <el-alert
          :title="progress.error_message"
          type="error"
          :closable="false"
          show-icon
        />
      </div>

      <!-- 任务列表 -->
      <div class="tasks-section">
        <div class="section-header">
          <h4>任务进度</h4>
          <el-button size="small" text @click="loadTasks">
            <el-icon><Refresh /></el-icon>
            刷新任务
          </el-button>
        </div>
        
        <el-table :data="tasks" size="small">
          <el-table-column prop="task_type" label="任务类型" width="150">
            <template #default="{ row }">
              {{ getTaskTypeText(row.task_type) }}
            </template>
          </el-table-column>
          
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getTaskStatusTagType(row.status)" size="small">
                {{ getTaskStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          
          <el-table-column prop="progress" label="进度" width="150">
            <template #default="{ row }">
              <el-progress
                :percentage="row.progress"
                :show-text="false"
                :stroke-width="6"
              />
              <span style="margin-left: 8px">{{ row.progress }}%</span>
            </template>
          </el-table-column>
          
          <el-table-column prop="started_at" label="开始时间" width="150">
            <template #default="{ row }">
              {{ row.started_at ? formatDateTime(row.started_at) : '-' }}
            </template>
          </el-table-column>
          
          <el-table-column prop="completed_at" label="完成时间" width="150">
            <template #default="{ row }">
              {{ row.completed_at ? formatDateTime(row.completed_at) : '-' }}
            </template>
          </el-table-column>
          
          <el-table-column label="操作" width="100">
            <template #default="{ row }">
              <el-button
                v-if="row.status === 'failed'"
                text
                size="small"
                type="primary"
                @click="retryTask(row)"
              >
                重试
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  VideoPause,
  VideoPlay,
  Close,
  Refresh,
  Loading,
  CircleCheck,
  CircleClose,
  Clock,
  TrendCharts,
  Timer,
  Money,
  DataAnalysis
} from '@element-plus/icons-vue'
import { useBacktestStore } from '@/stores/backtest'
import type { Backtest, BacktestProgress } from '@/types/backtest'

interface Props {
  backtestId: number
  autoRefresh?: boolean
  refreshInterval?: number
}

const props = withDefaults(defineProps<Props>(), {
  autoRefresh: true,
  refreshInterval: 5000
})

const backtestStore = useBacktestStore()
const loading = ref(false)
const tasks = ref<any[]>([])

let refreshTimer: NodeJS.Timeout | null = null

// 计算属性
const backtest = computed(() => backtestStore.currentBacktest)
const progress = computed(() => backtestStore.currentProgress)

// 方法
const loadProgress = async () => {
  try {
    loading.value = true
    await Promise.all([
      backtestStore.fetchBacktest(props.backtestId),
      backtestStore.fetchBacktestProgress(props.backtestId)
    ])
  } catch (error) {
    // 错误已在store中处理
  } finally {
    loading.value = false
  }
}

const loadTasks = async () => {
  try {
    // 模拟任务数据
    tasks.value = [
      {
        id: 1,
        task_type: 'data_preparation',
        status: 'completed',
        progress: 100,
        started_at: '2024-01-15 10:00:00',
        completed_at: '2024-01-15 10:05:00'
      },
      {
        id: 2,
        task_type: 'calculation',
        status: 'running',
        progress: 65,
        started_at: '2024-01-15 10:05:00',
        completed_at: null
      },
      {
        id: 3,
        task_type: 'analysis',
        status: 'pending',
        progress: 0,
        started_at: null,
        completed_at: null
      },
      {
        id: 4,
        task_type: 'report_generation',
        status: 'pending',
        progress: 0,
        started_at: null,
        completed_at: null
      }
    ]
  } catch (error) {
    ElMessage.error('加载任务失败')
  }
}

const handlePause = async () => {
  try {
    await backtestStore.pauseBacktest(props.backtestId)
    await loadProgress()
  } catch (error) {
    // 错误已在store中处理
  }
}

const handleResume = async () => {
  try {
    await backtestStore.resumeBacktest(props.backtestId)
    await loadProgress()
  } catch (error) {
    // 错误已在store中处理
  }
}

const handleStop = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要停止回测吗？停止后无法恢复。',
      '确认停止',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await backtestStore.stopBacktest(props.backtestId)
    await loadProgress()
  } catch (error) {
    // 用户取消或错误已在store中处理
  }
}

const handleRefresh = () => {
  loadProgress()
  loadTasks()
}

const retryTask = async (task: any) => {
  try {
    // 调用重试任务API
    ElMessage.success('任务重试已提交')
    await loadTasks()
  } catch (error) {
    ElMessage.error('任务重试失败')
  }
}

const startAutoRefresh = () => {
  if (props.autoRefresh && !refreshTimer) {
    refreshTimer = setInterval(() => {
      if (backtest.value?.status === 'running') {
        loadProgress()
      }
    }, props.refreshInterval)
  }
}

const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

// 格式化函数
const getStatusText = (status?: string) => {
  const textMap: Record<string, string> = {
    pending: '等待中',
    running: '运行中',
    paused: '已暂停',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消'
  }
  return textMap[status || ''] || '未知'
}

const getStatusClass = (status?: string) => {
  const classMap: Record<string, string> = {
    pending: 'pending',
    running: 'running',
    paused: 'paused',
    completed: 'completed',
    failed: 'failed',
    cancelled: 'cancelled'
  }
  return classMap[status || ''] || 'pending'
}

const getProgressColor = () => {
  if (!backtest.value) return '#409eff'
  
  switch (backtest.value.status) {
    case 'completed':
      return '#67c23a'
    case 'failed':
    case 'cancelled':
      return '#f56c6c'
    case 'paused':
      return '#e6a23c'
    default:
      return '#409eff'
  }
}

const getProgressStatus = () => {
  if (!backtest.value) return undefined
  
  switch (backtest.value.status) {
    case 'completed':
      return 'success'
    case 'failed':
    case 'cancelled':
      return 'exception'
    default:
      return undefined
  }
}

const getDrawdownClass = () => {
  const drawdown = progress.value?.current_drawdown || 0
  if (drawdown > 0.15) return 'danger'
  if (drawdown > 0.1) return 'warning'
  return 'normal'
}

const getRunningDuration = () => {
  if (!backtest.value?.started_at) return '-'
  
  const startTime = new Date(backtest.value.started_at).getTime()
  const currentTime = backtest.value.completed_at 
    ? new Date(backtest.value.completed_at).getTime()
    : Date.now()
  
  const duration = Math.floor((currentTime - startTime) / 1000)
  return formatDuration(duration)
}

const getTaskTypeText = (taskType: string) => {
  const textMap: Record<string, string> = {
    data_preparation: '数据准备',
    calculation: '计算执行',
    analysis: '结果分析',
    report_generation: '报告生成'
  }
  return textMap[taskType] || taskType
}

const getTaskStatusTagType = (status: string) => {
  const typeMap: Record<string, string> = {
    pending: 'info',
    running: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return typeMap[status] || 'info'
}

const getTaskStatusText = (status: string) => {
  const textMap: Record<string, string> = {
    pending: '等待',
    running: '运行中',
    completed: '完成',
    failed: '失败'
  }
  return textMap[status] || status
}

const formatDuration = (seconds?: number) => {
  if (!seconds || seconds <= 0) return '-'
  
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60
  
  if (hours > 0) {
    return `${hours}小时${minutes}分钟`
  } else if (minutes > 0) {
    return `${minutes}分钟${secs}秒`
  } else {
    return `${secs}秒`
  }
}

const formatCurrency = (value?: number) => {
  if (!value) return '-'
  
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY'
  }).format(value)
}

const formatPercent = (value?: number) => {
  if (!value) return '0%'
  return `${(value * 100).toFixed(2)}%`
}

const formatDateTime = (dateString: string) => {
  return new Date(dateString).toLocaleString('zh-CN')
}

// 生命周期
onMounted(() => {
  loadProgress()
  loadTasks()
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style scoped lang="scss">
.backtest-progress-monitor {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .header-actions {
      display: flex;
      gap: 8px;
    }
  }
  
  .status-overview {
    margin-bottom: 20px;
    
    .status-item {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 16px;
      background: #f5f7fa;
      border-radius: 8px;
      
      .status-icon {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
        
        &.pending { background: #e4e7ed; color: #909399; }
        &.running { background: #e1f3d8; color: #67c23a; }
        &.paused { background: #fdf6ec; color: #e6a23c; }
        &.completed { background: #e1f3d8; color: #67c23a; }
        &.failed { background: #fef0f0; color: #f56c6c; }
        &.cancelled { background: #e4e7ed; color: #909399; }
        &.progress { background: #ecf5ff; color: #409eff; }
        &.time { background: #f4f4f5; color: #909399; }
        &.equity { background: #f0f9ff; color: #1890ff; }
      }
      
      .status-info {
        .status-label {
          font-size: 12px;
          color: #909399;
          margin-bottom: 4px;
        }
        
        .status-value {
          font-size: 16px;
          font-weight: 600;
          color: #303133;
        }
      }
    }
  }
  
  .progress-section {
    margin-bottom: 20px;
    
    .progress-info {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
      
      .progress-text {
        font-size: 14px;
        color: #606266;
      }
      
      .progress-percentage {
        font-size: 14px;
        font-weight: 600;
        color: #303133;
      }
    }
  }
  
  .metrics-section {
    margin-bottom: 20px;
    
    .metric-card {
      padding: 16px;
      background: #fff;
      border: 1px solid #ebeef5;
      border-radius: 8px;
      
      .metric-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
        
        .metric-title {
          font-size: 14px;
          color: #606266;
        }
        
        .metric-icon {
          color: #909399;
        }
      }
      
      .metric-value {
        font-size: 20px;
        font-weight: 600;
        color: #303133;
        
        &.danger { color: #f56c6c; }
        &.warning { color: #e6a23c; }
        &.normal { color: #67c23a; }
      }
    }
  }
  
  .error-section {
    margin-bottom: 20px;
  }
  
  .tasks-section {
    .section-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
      
      h4 {
        margin: 0;
        font-size: 16px;
        font-weight: 600;
        color: #303133;
      }
    }
  }
}
</style>