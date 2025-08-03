<template>
  <div class="order-execution-panel">
    <!-- 执行服务状态 -->
    <el-card class="service-status-card">
      <template #header>
        <div class="card-header">
          <span>订单执行服务</span>
          <div class="header-actions">
            <el-tag
              :type="serviceStatus.is_running ? 'success' : 'danger'"
              size="small"
            >
              {{ serviceStatus.is_running ? '运行中' : '已停止' }}
            </el-tag>
            <el-button
              v-if="!serviceStatus.is_running"
              type="success"
              size="small"
              @click="startExecutionService"
              :loading="serviceLoading"
            >
              启动服务
            </el-button>
            <el-button
              v-else
              type="danger"
              size="small"
              @click="stopExecutionService"
              :loading="serviceLoading"
            >
              停止服务
            </el-button>
          </div>
        </div>
      </template>

      <el-row :gutter="20">
        <el-col :span="6">
          <div class="status-item">
            <div class="status-value">{{ serviceStatus.active_executions || 0 }}</div>
            <div class="status-label">活跃执行</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="status-item">
            <div class="status-value">{{ executionStats.total_submitted || 0 }}</div>
            <div class="status-label">总提交数</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="status-item">
            <div class="status-value">{{ executionStats.total_executed || 0 }}</div>
            <div class="status-label">已执行</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="status-item">
            <div class="status-value">{{ (executionStats.success_rate * 100).toFixed(1) }}%</div>
            <div class="status-label">成功率</div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 交易系统状态 -->
    <el-card class="trading-systems-card">
      <template #header>
        <span>交易系统连接状态</span>
      </template>

      <div class="trading-systems-list">
        <div
          v-for="(system, name) in tradingSystems"
          :key="name"
          class="trading-system-item"
        >
          <div class="system-info">
            <div class="system-name">{{ getSystemDisplayName(name) }}</div>
            <div class="system-details">
              <el-tag
                :type="system.connected ? 'success' : 'danger'"
                size="small"
              >
                {{ system.connected ? '已连接' : '未连接' }}
              </el-tag>
              <span v-if="system.connection_info?.account_id" class="account-id">
                账户: {{ system.connection_info.account_id }}
              </span>
            </div>
          </div>
          <div class="system-actions">
            <el-button
              v-if="!system.connected"
              type="primary"
              size="small"
              @click="connectTradingSystem(name)"
            >
              连接
            </el-button>
            <el-button
              v-else
              type="danger"
              size="small"
              @click="disconnectTradingSystem(name)"
            >
              断开
            </el-button>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 执行统计图表 -->
    <el-card class="execution-chart-card">
      <template #header>
        <span>执行统计</span>
      </template>

      <div class="chart-container">
        <div ref="executionChart" class="execution-chart"></div>
      </div>
    </el-card>

    <!-- 活跃执行列表 -->
    <el-card class="active-executions-card">
      <template #header>
        <div class="card-header">
          <span>活跃执行订单</span>
          <el-button
            size="small"
            @click="refreshActiveExecutions"
            :loading="activeExecutionsLoading"
          >
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>

      <el-table
        :data="activeExecutions"
        :loading="activeExecutionsLoading"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="order_id" label="订单ID" width="100" />
        <el-table-column prop="symbol" label="标的" width="100" />
        <el-table-column prop="side" label="方向" width="80">
          <template #default="{ row }">
            <el-tag
              :type="row.side === 'buy' ? 'success' : 'danger'"
              size="small"
            >
              {{ row.side === 'buy' ? '买入' : '卖出' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="quantity" label="数量" width="120" align="right">
          <template #default="{ row }">
            {{ formatNumber(row.quantity) }}
          </template>
        </el-table-column>
        <el-table-column prop="filled_quantity" label="已成交" width="120" align="right">
          <template #default="{ row }">
            {{ formatNumber(row.filled_quantity) }}
          </template>
        </el-table-column>
        <el-table-column label="执行进度" width="150">
          <template #default="{ row }">
            <div class="progress-cell">
              <el-progress
                :percentage="row.fill_ratio * 100"
                :stroke-width="6"
                :show-text="false"
              />
              <span class="progress-text">{{ (row.fill_ratio * 100).toFixed(1) }}%</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="internal_status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag size="small">
              {{ getStatusLabel(row.internal_status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button
              type="text"
              size="small"
              @click="viewExecutionDetails(row)"
            >
              详情
            </el-button>
            <el-button
              type="text"
              size="small"
              @click="cancelExecution(row)"
              class="cancel-btn"
            >
              取消
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 执行详情对话框 -->
    <el-dialog
      v-model="showExecutionDetails"
      title="执行详情"
      width="600px"
    >
      <div v-if="selectedExecution" class="execution-details">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="订单ID">
            {{ selectedExecution.order_id }}
          </el-descriptions-item>
          <el-descriptions-item label="内部状态">
            {{ getStatusLabel(selectedExecution.internal_status) }}
          </el-descriptions-item>
          <el-descriptions-item label="是否活跃">
            {{ selectedExecution.is_active ? '是' : '否' }}
          </el-descriptions-item>
          <el-descriptions-item label="已成交数量">
            {{ formatNumber(selectedExecution.filled_quantity) }}
          </el-descriptions-item>
          <el-descriptions-item label="剩余数量">
            {{ formatNumber(selectedExecution.remaining_quantity) }}
          </el-descriptions-item>
          <el-descriptions-item label="成交比例">
            {{ (selectedExecution.fill_ratio * 100).toFixed(2) }}%
          </el-descriptions-item>
        </el-descriptions>

        <div v-if="selectedExecution.external_status" class="external-status">
          <h4>外部系统状态</h4>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="外部状态">
              {{ selectedExecution.external_status.status }}
            </el-descriptions-item>
            <el-descriptions-item label="外部成交数量">
              {{ selectedExecution.external_status.filled_quantity || 0 }}
            </el-descriptions-item>
            <el-descriptions-item label="最后成交价">
              {{ selectedExecution.external_status.last_fill_price || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="手续费">
              {{ selectedExecution.external_status.commission || 0 }}
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </div>

      <template #footer>
        <el-button @click="showExecutionDetails = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { orderApi } from '@/api/order'
import { formatNumber } from '@/utils/format'

// 响应式数据
const serviceLoading = ref(false)
const activeExecutionsLoading = ref(false)
const serviceStatus = ref<any>({})
const executionStats = ref<any>({})
const tradingSystems = ref<any>({})
const activeExecutions = ref<any[]>([])
const showExecutionDetails = ref(false)
const selectedExecution = ref<any>(null)

// 图表相关
const executionChart = ref<HTMLElement>()
let chartInstance: echarts.ECharts | null = null

// 定时器
let statusTimer: NodeJS.Timeout | null = null

// 加载服务状态
const loadServiceStatus = async () => {
  try {
    const response = await orderApi.getExecutionServiceStatus()
    serviceStatus.value = response.data
    executionStats.value = response.data.execution_stats || {}
    tradingSystems.value = response.data.trading_systems || {}
  } catch (error) {
    console.error('加载执行服务状态失败:', error)
  }
}

// 加载活跃执行
const loadActiveExecutions = async () => {
  try {
    activeExecutionsLoading.value = true
    
    // 获取活跃订单
    const response = await orderApi.getActiveOrders()
    const activeOrders = response.data
    
    // 获取每个订单的执行状态
    const executionPromises = activeOrders.map(async (order: any) => {
      try {
        const statusResponse = await orderApi.getOrderExecutionStatus(order.id)
        return statusResponse.data
      } catch (error) {
        return {
          order_id: order.id,
          symbol: order.symbol,
          side: order.side,
          quantity: order.quantity,
          filled_quantity: order.filled_quantity,
          fill_ratio: order.fill_ratio,
          internal_status: order.status,
          is_active: order.is_active
        }
      }
    })
    
    activeExecutions.value = await Promise.all(executionPromises)
  } catch (error) {
    console.error('加载活跃执行失败:', error)
  } finally {
    activeExecutionsLoading.value = false
  }
}

// 启动执行服务
const startExecutionService = async () => {
  try {
    serviceLoading.value = true
    await orderApi.startExecutionService()
    ElMessage.success('执行服务启动成功')
    await loadServiceStatus()
  } catch (error) {
    console.error('启动执行服务失败:', error)
    ElMessage.error('启动执行服务失败')
  } finally {
    serviceLoading.value = false
  }
}

// 停止执行服务
const stopExecutionService = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要停止订单执行服务吗？这将停止所有正在执行的订单。',
      '停止执行服务',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    serviceLoading.value = true
    await orderApi.stopExecutionService()
    ElMessage.success('执行服务停止成功')
    await loadServiceStatus()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('停止执行服务失败:', error)
      ElMessage.error('停止执行服务失败')
    }
  } finally {
    serviceLoading.value = false
  }
}

// 连接交易系统
const connectTradingSystem = async (systemName: string) => {
  ElMessage.info(`连接交易系统: ${systemName}`)
  // 这里可以实现具体的连接逻辑
}

// 断开交易系统
const disconnectTradingSystem = async (systemName: string) => {
  ElMessage.info(`断开交易系统: ${systemName}`)
  // 这里可以实现具体的断开逻辑
}

// 刷新活跃执行
const refreshActiveExecutions = () => {
  loadActiveExecutions()
}

// 查看执行详情
const viewExecutionDetails = (execution: any) => {
  selectedExecution.value = execution
  showExecutionDetails.value = true
}

// 取消执行
const cancelExecution = async (execution: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要取消订单 ${execution.order_id} 的执行吗？`,
      '取消执行',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await orderApi.cancelOrder(execution.order_id)
    ElMessage.success('取消执行成功')
    await loadActiveExecutions()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('取消执行失败:', error)
      ElMessage.error('取消执行失败')
    }
  }
}

// 获取系统显示名称
const getSystemDisplayName = (systemName: string) => {
  const nameMap: Record<string, string> = {
    mock: '模拟交易系统',
    interactive_brokers: '盈透证券',
    alpaca: 'Alpaca',
    td_ameritrade: 'TD Ameritrade',
    binance: '币安'
  }
  return nameMap[systemName] || systemName
}

// 获取状态标签
const getStatusLabel = (status: string) => {
  const statusMap: Record<string, string> = {
    pending: '待提交',
    submitted: '已提交',
    accepted: '已接受',
    partially_filled: '部分成交',
    filled: '完全成交',
    cancelled: '已取消',
    rejected: '已拒绝'
  }
  return statusMap[status] || status
}

// 初始化图表
const initChart = () => {
  if (!executionChart.value) return
  
  chartInstance = echarts.init(executionChart.value)
  
  const option = {
    title: {
      text: '执行统计',
      left: 'center'
    },
    tooltip: {
      trigger: 'item'
    },
    legend: {
      orient: 'vertical',
      left: 'left'
    },
    series: [
      {
        name: '执行统计',
        type: 'pie',
        radius: '50%',
        data: [
          { value: executionStats.value.total_executed || 0, name: '已执行' },
          { value: executionStats.value.total_cancelled || 0, name: '已取消' },
          { value: executionStats.value.total_rejected || 0, name: '已拒绝' }
        ],
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
  
  chartInstance.setOption(option)
}

// 更新图表
const updateChart = () => {
  if (!chartInstance) return
  
  const option = {
    series: [
      {
        data: [
          { value: executionStats.value.total_executed || 0, name: '已执行' },
          { value: executionStats.value.total_cancelled || 0, name: '已取消' },
          { value: executionStats.value.total_rejected || 0, name: '已拒绝' }
        ]
      }
    ]
  }
  
  chartInstance.setOption(option)
}

// 启动定时刷新
const startAutoRefresh = () => {
  statusTimer = setInterval(async () => {
    await loadServiceStatus()
    await loadActiveExecutions()
    updateChart()
  }, 10000) // 每10秒刷新一次
}

// 停止定时刷新
const stopAutoRefresh = () => {
  if (statusTimer) {
    clearInterval(statusTimer)
    statusTimer = null
  }
}

// 初始化
onMounted(async () => {
  await loadServiceStatus()
  await loadActiveExecutions()
  
  nextTick(() => {
    initChart()
    updateChart()
  })
  
  startAutoRefresh()
})

// 清理
onUnmounted(() => {
  stopAutoRefresh()
  if (chartInstance) {
    chartInstance.dispose()
  }
})
</script>

<style scoped>
.order-execution-panel {
  padding: 20px;
}

.service-status-card,
.trading-systems-card,
.execution-chart-card,
.active-executions-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-item {
  text-align: center;
}

.status-value {
  font-size: 24px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  line-height: 1;
}

.status-label {
  font-size: 14px;
  color: var(--el-text-color-regular);
  margin-top: 4px;
}

.trading-systems-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.trading-system-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 6px;
}

.system-info {
  flex: 1;
}

.system-name {
  font-weight: 500;
  margin-bottom: 4px;
}

.system-details {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.account-id {
  font-family: monospace;
}

.chart-container {
  height: 300px;
}

.execution-chart {
  width: 100%;
  height: 100%;
}

.progress-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.progress-text {
  font-size: 12px;
  color: var(--el-text-color-regular);
  min-width: 40px;
}

.cancel-btn {
  color: var(--el-color-danger);
}

.execution-details {
  max-height: 60vh;
  overflow-y: auto;
}

.external-status {
  margin-top: 20px;
}

.external-status h4 {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
}

:deep(.el-progress-bar__outer) {
  background-color: var(--el-border-color-lighter);
}
</style>