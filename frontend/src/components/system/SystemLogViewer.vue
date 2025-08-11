<template>
  <div class="system-log-viewer">
    <div class="header">
      <h3>系统日志</h3>
      <div class="actions">
        <el-button @click="refreshLogs">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button type="primary" @click="exportLogs">
          <el-icon><Download /></el-icon>
          导出日志
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

        <el-form-item label="日志级别">
          <el-select v-model="filters.level" placeholder="全部级别" clearable style="width: 120px">
            <el-option label="DEBUG" value="DEBUG" />
            <el-option label="INFO" value="INFO" />
            <el-option label="WARNING" value="WARNING" />
            <el-option label="ERROR" value="ERROR" />
            <el-option label="CRITICAL" value="CRITICAL" />
          </el-select>
        </el-form-item>

        <el-form-item label="模块">
          <el-select v-model="filters.module" placeholder="全部模块" clearable style="width: 150px">
            <el-option
              v-for="module in availableModules"
              :key="module"
              :label="module"
              :value="module"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="用户ID">
          <el-input
            v-model="filters.user_id"
            placeholder="用户ID"
            style="width: 100px"
            clearable
          />
        </el-form-item>

        <el-form-item label="关键词">
          <el-input
            v-model="filters.message_contains"
            placeholder="搜索日志内容"
            style="width: 200px"
            clearable
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="searchLogs">搜索</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 日志表格 -->
    <el-table
      v-loading="loading"
      :data="logs"
      stripe
      style="width: 100%"
      :row-class-name="getRowClassName"
      @row-click="viewLogDetail"
    >
      <el-table-column prop="timestamp" label="时间" width="180" sortable>
        <template #default="{ row }">
          {{ formatDateTime(row.timestamp) }}
        </template>
      </el-table-column>

      <el-table-column prop="level" label="级别" width="100">
        <template #default="{ row }">
          <el-tag :type="getLevelTagType(row.level)" size="small">
            {{ row.level }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column prop="module" label="模块" width="150" show-overflow-tooltip />

      <el-table-column prop="message" label="消息" min-width="300" show-overflow-tooltip />

      <el-table-column prop="user_id" label="用户ID" width="100">
        <template #default="{ row }">
          <span v-if="row.user_id">{{ row.user_id }}</span>
          <span v-else class="text-muted">-</span>
        </template>
      </el-table-column>

      <el-table-column prop="ip_address" label="IP地址" width="140">
        <template #default="{ row }">
          <span v-if="row.ip_address">{{ row.ip_address }}</span>
          <span v-else class="text-muted">-</span>
        </template>
      </el-table-column>

      <el-table-column prop="request_id" label="请求ID" width="120" show-overflow-tooltip>
        <template #default="{ row }">
          <span v-if="row.request_id" class="request-id">{{ row.request_id.slice(-8) }}</span>
          <span v-else class="text-muted">-</span>
        </template>
      </el-table-column>

      <el-table-column label="操作" width="100" fixed="right">
        <template #default="{ row }">
          <el-button type="text" size="small" @click.stop="viewLogDetail(row)">
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
        @size-change="loadLogs"
        @current-change="loadLogs"
      />
    </div>

    <!-- 日志详情对话框 -->
    <el-dialog
      v-model="showDetailDialog"
      title="日志详情"
      width="800px"
      :close-on-click-modal="false"
    >
      <div v-if="selectedLog" class="log-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="时间">
            {{ formatDateTime(selectedLog.timestamp) }}
          </el-descriptions-item>
          <el-descriptions-item label="级别">
            <el-tag :type="getLevelTagType(selectedLog.level)">
              {{ selectedLog.level }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="模块">{{ selectedLog.module }}</el-descriptions-item>
          <el-descriptions-item label="用户ID">
            {{ selectedLog.user_id || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="IP地址">
            {{ selectedLog.ip_address || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="请求ID">
            {{ selectedLog.request_id || '-' }}
          </el-descriptions-item>
        </el-descriptions>

        <div class="log-message">
          <h4>消息内容：</h4>
          <div class="message-content">
            {{ selectedLog.message }}
          </div>
        </div>

        <div v-if="selectedLog.user_agent" class="user-agent">
          <h4>User Agent：</h4>
          <div class="user-agent-content">
            {{ selectedLog.user_agent }}
          </div>
        </div>

        <div v-if="selectedLog.extra_data" class="extra-data">
          <h4>额外数据：</h4>
          <pre class="json-content">{{ JSON.stringify(selectedLog.extra_data, null, 2) }}</pre>
        </div>
      </div>
    </el-dialog>

    <!-- 实时日志开关 -->
    <div class="realtime-controls">
      <el-switch
        v-model="realtimeEnabled"
        active-text="实时日志"
        inactive-text="停止实时"
        @change="toggleRealtime"
      />
      <span v-if="realtimeEnabled" class="realtime-status">
        <el-icon class="is-loading"><Loading /></el-icon>
        实时监控中...
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Download, View, Loading } from '@element-plus/icons-vue'
import { dataExportApi, type SystemLogEntry, type SystemLogQuery } from '@/api/dataExport'
import { formatDateTime } from '@/utils/format'

// 响应式数据
const loading = ref(false)
const logs = ref<SystemLogEntry[]>([])
const selectedLog = ref<SystemLogEntry | null>(null)
const showDetailDialog = ref(false)
const realtimeEnabled = ref(false)
const dateRange = ref<[string, string] | null>(null)

const filters = ref<SystemLogQuery>({
  level: undefined,
  module: undefined,
  user_id: undefined,
  message_contains: undefined,
  limit: 50,
  offset: 0
})

const pagination = ref({
  page: 1,
  size: 50,
  total: 0
})

const availableModules = ref<string[]>([
  'auth', 'orders', 'positions', 'strategies', 'backtests', 
  'market_data', 'risk', 'notifications', 'system'
])

let realtimeTimer: NodeJS.Timeout | null = null

// 计算属性
const currentFilters = computed(() => {
  const result: SystemLogQuery = {
    ...filters.value,
    limit: pagination.value.size,
    offset: (pagination.value.page - 1) * pagination.value.size
  }

  if (dateRange.value) {
    result.start_date = dateRange.value[0]
    result.end_date = dateRange.value[1]
  }

  return result
})

// 方法
const loadLogs = async () => {
  try {
    loading.value = true
    const data = await dataExportApi.getSystemLogs(currentFilters.value)
    logs.value = data
    // 注意：这里需要后端返回总数
    pagination.value.total = data.length
  } catch (error: any) {
    ElMessage.error(error.message || '加载日志失败')
  } finally {
    loading.value = false
  }
}

const refreshLogs = () => {
  loadLogs()
}

const searchLogs = () => {
  pagination.value.page = 1
  loadLogs()
}

const resetFilters = () => {
  filters.value = {
    level: undefined,
    module: undefined,
    user_id: undefined,
    message_contains: undefined,
    limit: 50,
    offset: 0
  }
  dateRange.value = null
  pagination.value.page = 1
  loadLogs()
}

const exportLogs = () => {
  // 创建导出任务
  ElMessage.info('功能开发中...')
}

const viewLogDetail = (log: SystemLogEntry) => {
  selectedLog.value = log
  showDetailDialog.value = true
}

const getLevelTagType = (level: string): string => {
  const types: Record<string, string> = {
    DEBUG: 'info',
    INFO: 'success',
    WARNING: 'warning',
    ERROR: 'danger',
    CRITICAL: 'danger'
  }
  return types[level] || 'info'
}

const getRowClassName = ({ row }: { row: SystemLogEntry }): string => {
  if (row.level === 'ERROR' || row.level === 'CRITICAL') {
    return 'error-row'
  }
  if (row.level === 'WARNING') {
    return 'warning-row'
  }
  return ''
}

const toggleRealtime = (enabled: boolean) => {
  if (enabled) {
    startRealtime()
  } else {
    stopRealtime()
  }
}

const startRealtime = () => {
  // 每5秒刷新一次日志
  realtimeTimer = setInterval(() => {
    loadLogs()
  }, 5000)
  ElMessage.success('已开启实时日志监控')
}

const stopRealtime = () => {
  if (realtimeTimer) {
    clearInterval(realtimeTimer)
    realtimeTimer = null
  }
  ElMessage.info('已停止实时日志监控')
}

// 生命周期
onMounted(() => {
  // 设置默认时间范围（最近1小时）
  const now = new Date()
  const oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000)
  dateRange.value = [
    oneHourAgo.toISOString().slice(0, 19).replace('T', ' '),
    now.toISOString().slice(0, 19).replace('T', ' ')
  ]
  
  loadLogs()
})

onUnmounted(() => {
  stopRealtime()
})
</script>

<style scoped>
.system-log-viewer {
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

.pagination {
  margin-top: 20px;
  text-align: right;
}

.log-detail {
  padding: 10px 0;
}

.log-message,
.user-agent,
.extra-data {
  margin-top: 20px;
}

.log-message h4,
.user-agent h4,
.extra-data h4 {
  margin-bottom: 10px;
  color: #303133;
}

.message-content,
.user-agent-content {
  padding: 12px;
  background: var(--el-bg-color-page);
  border-radius: 4px;
  border-left: 4px solid #409eff;
  word-break: break-all;
  line-height: 1.6;
}

.json-content {
  padding: 12px;
  background: var(--el-bg-color-page);
  border-radius: 4px;
  border-left: 4px solid #67c23a;
  font-size: 12px;
  line-height: 1.4;
  overflow-x: auto;
}

.text-muted {
  color: #c0c4cc;
}

.request-id {
  font-family: monospace;
  font-size: 12px;
  background: var(--el-fill-color-light);
  padding: 2px 4px;
  border-radius: 2px;
}

.realtime-controls {
  position: fixed;
  bottom: 20px;
  right: 20px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: var(--el-bg-color);
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  z-index: 1000;
}

.realtime-status {
  display: flex;
  align-items: center;
  gap: 5px;
  color: #67c23a;
  font-size: 14px;
}

/* 表格行样式 */
:deep(.error-row) {
  background-color: var(--el-color-danger-light-9) !important;
}

:deep(.warning-row) {
  background-color: #fdf6ec !important;
}

:deep(.el-table__row:hover.error-row) {
  background-color: #fde2e2 !important;
}

:deep(.el-table__row:hover.warning-row) {
  background-color: #faecd8 !important;
}
</style>