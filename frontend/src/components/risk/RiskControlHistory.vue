<template>
  <div class="risk-control-history">
    <div class="header">
      <h3>风险控制历史</h3>
      <div class="actions">
        <el-button @click="loadHistory">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button @click="exportHistory">
          <el-icon><Download /></el-icon>
          导出
        </el-button>
      </div>
    </div>

    <!-- 筛选条件 -->
    <div class="filters">
      <el-form :model="filters" inline>
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="dateRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DD HH:mm:ss"
            style="width: 350px"
          />
        </el-form-item>

        <el-form-item label="用户ID">
          <el-input
            v-model="filters.user_id"
            placeholder="用户ID"
            style="width: 120px"
            clearable
          />
        </el-form-item>

        <el-form-item label="动作类型">
          <el-select v-model="filters.action_type" placeholder="全部类型" clearable style="width: 150px">
            <el-option label="拒绝订单" value="reject_order" />
            <el-option label="减少订单" value="reduce_order_size" />
            <el-option label="强制平仓" value="force_close_position" />
            <el-option label="暂停交易" value="suspend_trading" />
            <el-option label="保证金追缴" value="margin_call" />
            <el-option label="强制清算" value="liquidation" />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="searchHistory">搜索</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 统计卡片 -->
    <div class="statistics-cards">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-value">{{ statistics.total_actions }}</div>
              <div class="stat-label">总动作数</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-value success">{{ (statistics.success_rate * 100).toFixed(1) }}%</div>
              <div class="stat-label">成功率</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-value warning">{{ statistics.most_common_action }}</div>
              <div class="stat-label">最常见动作</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-value info">{{ statistics.affected_users }}</div>
              <div class="stat-label">影响用户数</div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 历史记录表格 -->
    <el-table
      v-loading="loading"
      :data="historyData"
      stripe
      style="width: 100%"
      :row-class-name="getRowClassName"
    >
      <el-table-column prop="id" label="ID" width="80" />
      
      <el-table-column prop="user_id" label="用户ID" width="100" />

      <el-table-column label="动作类型" width="120">
        <template #default="{ row }">
          <el-tag :type="getActionTagType(row.action)" size="small">
            {{ getActionLabel(row.action) }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column label="执行状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.success ? 'success' : 'danger'" size="small">
            {{ row.success ? '成功' : '失败' }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column label="严重程度" width="100">
        <template #default="{ row }">
          <el-tag :type="getSeverityTagType(row.severity)" size="small">
            {{ getSeverityLabel(row.severity) }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />

      <el-table-column prop="created_at" label="执行时间" width="180">
        <template #default="{ row }">
          {{ formatDateTime(row.created_at) }}
        </template>
      </el-table-column>

      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }">
          <el-button type="text" size="small" @click="viewDetail(row)">
            <el-icon><View /></el-icon>
            详情
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="pagination">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.size"
        :total="pagination.total"
        :page-sizes="[20, 50, 100, 200]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="loadHistory"
        @current-change="loadHistory"
      />
    </div>

    <!-- 详情对话框 -->
    <el-dialog
      v-model="showDetailDialog"
      title="风险控制动作详情"
      width="800px"
      :close-on-click-modal="false"
    >
      <div v-if="selectedRecord" class="action-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="动作ID">{{ selectedRecord.id }}</el-descriptions-item>
          <el-descriptions-item label="用户ID">{{ selectedRecord.user_id }}</el-descriptions-item>
          <el-descriptions-item label="动作类型">
            <el-tag :type="getActionTagType(selectedRecord.action)">
              {{ getActionLabel(selectedRecord.action) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="执行状态">
            <el-tag :type="selectedRecord.success ? 'success' : 'danger'">
              {{ selectedRecord.success ? '成功' : '失败' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="严重程度">
            <el-tag :type="getSeverityTagType(selectedRecord.severity)">
              {{ getSeverityLabel(selectedRecord.severity) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="执行时间">
            {{ formatDateTime(selectedRecord.created_at) }}
          </el-descriptions-item>
        </el-descriptions>

        <div class="detail-section">
          <h4>描述信息</h4>
          <div class="description-content">
            {{ selectedRecord.description }}
          </div>
        </div>

        <div v-if="selectedRecord.context" class="detail-section">
          <h4>执行上下文</h4>
          <pre class="context-content">{{ JSON.stringify(selectedRecord.context, null, 2) }}</pre>
        </div>

        <div v-if="selectedRecord.error" class="detail-section">
          <h4>错误信息</h4>
          <el-alert type="error" :closable="false">
            {{ selectedRecord.error }}
          </el-alert>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Download, View } from '@element-plus/icons-vue'
import { riskControlApi, type RiskActionHistory } from '@/api/riskControl'
import { formatDateTime } from '@/utils/format'

// 响应式数据
const loading = ref(false)
const historyData = ref<RiskActionHistory[]>([])
const selectedRecord = ref<RiskActionHistory | null>(null)
const showDetailDialog = ref(false)
const dateRange = ref<[string, string] | null>(null)

const filters = ref({
  user_id: '',
  action_type: ''
})

const pagination = ref({
  page: 1,
  size: 50,
  total: 0
})

// 统计数据
const statistics = computed(() => {
  const total = historyData.value.length
  const successful = historyData.value.filter(item => item.success).length
  const successRate = total > 0 ? successful / total : 0
  
  // 统计最常见的动作类型
  const actionCounts: Record<string, number> = {}
  historyData.value.forEach(item => {
    actionCounts[item.action] = (actionCounts[item.action] || 0) + 1
  })
  
  const mostCommonAction = Object.keys(actionCounts).reduce((a, b) => 
    actionCounts[a] > actionCounts[b] ? a : b, ''
  )
  
  // 统计影响的用户数
  const affectedUsers = new Set(historyData.value.map(item => item.user_id)).size
  
  return {
    total_actions: total,
    success_rate: successRate,
    most_common_action: getActionLabel(mostCommonAction),
    affected_users: affectedUsers
  }
})

// 方法
const loadHistory = async () => {
  try {
    loading.value = true
    
    const params: any = {
      skip: (pagination.value.page - 1) * pagination.value.size,
      limit: pagination.value.size
    }
    
    if (filters.value.user_id) {
      params.user_id = parseInt(filters.value.user_id)
    }
    
    if (filters.value.action_type) {
      params.action_type = filters.value.action_type
    }
    
    if (dateRange.value) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }
    
    const response = await riskControlApi.getRiskActionsHistory(params)
    historyData.value = response.events
    pagination.value.total = response.total
    
  } catch (error: any) {
    ElMessage.error(error.message || '加载历史记录失败')
  } finally {
    loading.value = false
  }
}

const searchHistory = () => {
  pagination.value.page = 1
  loadHistory()
}

const resetFilters = () => {
  filters.value = {
    user_id: '',
    action_type: ''
  }
  dateRange.value = null
  pagination.value.page = 1
  loadHistory()
}

const exportHistory = () => {
  ElMessage.info('导出功能开发中...')
}

const viewDetail = (record: RiskActionHistory) => {
  selectedRecord.value = record
  showDetailDialog.value = true
}

const getActionLabel = (action: string): string => {
  const labels: Record<string, string> = {
    reject_order: '拒绝订单',
    reduce_order_size: '减少订单',
    force_close_position: '强制平仓',
    suspend_trading: '暂停交易',
    margin_call: '保证金追缴',
    liquidation: '强制清算',
    emergency_control: '紧急控制'
  }
  return labels[action] || action
}

const getActionTagType = (action: string): string => {
  const types: Record<string, string> = {
    reject_order: 'warning',
    reduce_order_size: 'info',
    force_close_position: 'danger',
    suspend_trading: 'danger',
    margin_call: 'warning',
    liquidation: 'danger',
    emergency_control: 'danger'
  }
  return types[action] || 'info'
}

const getSeverityLabel = (severity: string): string => {
  const labels: Record<string, string> = {
    low: '低',
    medium: '中',
    high: '高',
    critical: '极高'
  }
  return labels[severity] || severity
}

const getSeverityTagType = (severity: string): string => {
  const types: Record<string, string> = {
    low: 'success',
    medium: 'warning',
    high: 'danger',
    critical: 'danger'
  }
  return types[severity] || 'info'
}

const getRowClassName = ({ row }: { row: RiskActionHistory }): string => {
  if (!row.success) {
    return 'error-row'
  }
  if (row.severity === 'critical') {
    return 'critical-row'
  }
  return ''
}

// 生命周期
onMounted(() => {
  // 设置默认时间范围（最近7天）
  const now = new Date()
  const sevenDaysAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
  dateRange.value = [
    sevenDaysAgo.toISOString().slice(0, 19).replace('T', ' '),
    now.toISOString().slice(0, 19).replace('T', ' ')
  ]
  
  loadHistory()
})
</script>

<style scoped>
.risk-control-history {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header h3 {
  margin: 0;
  color: #303133;
}

.actions {
  display: flex;
  gap: 10px;
}

.filters {
  margin-bottom: 20px;
  padding: 16px;
  background: var(--el-bg-color-page);
  border-radius: 4px;
}

.statistics-cards {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
}

.stat-content {
  padding: 20px;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 8px;
}

.stat-value.success {
  color: #67c23a;
}

.stat-value.warning {
  color: #e6a23c;
}

.stat-value.info {
  color: #409eff;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.pagination {
  margin-top: 20px;
  text-align: right;
}

.action-detail {
  padding: 10px 0;
}

.detail-section {
  margin-top: 20px;
}

.detail-section h4 {
  margin-bottom: 10px;
  color: #303133;
}

.description-content {
  padding: 12px;
  background: var(--el-bg-color-page);
  border-radius: 4px;
  border-left: 4px solid #409eff;
  line-height: 1.6;
}

.context-content {
  padding: 12px;
  background: var(--el-bg-color-page);
  border-radius: 4px;
  border-left: 4px solid #67c23a;
  font-size: 12px;
  line-height: 1.4;
  overflow-x: auto;
}

/* 表格行样式 */
:deep(.error-row) {
  background-color: var(--el-color-danger-light-9) !important;
}

:deep(.critical-row) {
  background-color: #fdf2f2 !important;
}

:deep(.el-table__row:hover.error-row) {
  background-color: #fde2e2 !important;
}

:deep(.el-table__row:hover.critical-row) {
  background-color: #fce4e4 !important;
}
</style>