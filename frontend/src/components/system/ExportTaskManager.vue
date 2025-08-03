<template>
  <div class="export-task-manager">
    <div class="header">
      <h3>导出任务管理</h3>
      <el-button type="primary" @click="showExportDialog = true">
        <el-icon><Download /></el-icon>
        新建导出
      </el-button>
    </div>

    <div class="filters">
      <el-form :model="filters" inline>
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部状态" clearable style="width: 120px">
            <el-option label="等待中" value="pending" />
            <el-option label="处理中" value="processing" />
            <el-option label="已完成" value="completed" />
            <el-option label="失败" value="failed" />
            <el-option label="已取消" value="cancelled" />
          </el-select>
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="filters.export_type" placeholder="全部类型" clearable style="width: 120px">
            <el-option label="订单" value="orders" />
            <el-option label="持仓" value="positions" />
            <el-option label="交易记录" value="transactions" />
            <el-option label="策略" value="strategies" />
            <el-option label="回测" value="backtests" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button @click="loadTasks">刷新</el-button>
        </el-form-item>
      </el-form>
    </div>

    <el-table
      v-loading="loading"
      :data="filteredTasks"
      stripe
      style="width: 100%"
    >
      <el-table-column prop="id" label="ID" width="80" />
      
      <el-table-column label="导出类型" width="120">
        <template #default="{ row }">
          <el-tag :type="getExportTypeTagType(row.export_type)">
            {{ getExportTypeLabel(row.export_type) }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column prop="format" label="格式" width="80">
        <template #default="{ row }">
          <el-tag size="small">{{ row.format.toUpperCase() }}</el-tag>
        </template>
      </el-table-column>

      <el-table-column label="状态" width="120">
        <template #default="{ row }">
          <el-tag :type="getStatusTagType(row.status)">
            {{ getStatusLabel(row.status) }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column label="进度" width="120">
        <template #default="{ row }">
          <el-progress
            v-if="row.status === 'processing'"
            :percentage="row.progress"
            :stroke-width="6"
            :show-text="false"
          />
          <span v-else-if="row.status === 'completed'">100%</span>
          <span v-else>-</span>
        </template>
      </el-table-column>

      <el-table-column label="文件大小" width="100">
        <template #default="{ row }">
          <span v-if="row.file_size">{{ formatFileSize(row.file_size) }}</span>
          <span v-else>-</span>
        </template>
      </el-table-column>

      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">
          {{ formatDateTime(row.created_at) }}
        </template>
      </el-table-column>

      <el-table-column label="过期时间" width="180">
        <template #default="{ row }">
          <span v-if="row.expires_at" :class="{ 'text-danger': isExpiringSoon(row.expires_at) }">
            {{ formatDateTime(row.expires_at) }}
          </span>
          <span v-else>-</span>
        </template>
      </el-table-column>

      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button
            v-if="row.status === 'completed' && row.download_url"
            type="primary"
            size="small"
            @click="downloadFile(row)"
          >
            <el-icon><Download /></el-icon>
            下载
          </el-button>
          
          <el-button
            v-if="['pending', 'processing'].includes(row.status)"
            type="warning"
            size="small"
            @click="cancelTask(row)"
          >
            <el-icon><Close /></el-icon>
            取消
          </el-button>
          
          <el-button
            type="info"
            size="small"
            @click="viewTaskDetail(row)"
          >
            <el-icon><View /></el-icon>
            详情
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.size"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="loadTasks"
        @current-change="loadTasks"
      />
    </div>

    <!-- 导出对话框 -->
    <DataExportDialog
      v-model="showExportDialog"
      @success="loadTasks"
    />

    <!-- 任务详情对话框 -->
    <el-dialog
      v-model="showDetailDialog"
      title="任务详情"
      width="600px"
    >
      <div v-if="selectedTask" class="task-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="任务ID">{{ selectedTask.id }}</el-descriptions-item>
          <el-descriptions-item label="导出类型">{{ getExportTypeLabel(selectedTask.export_type) }}</el-descriptions-item>
          <el-descriptions-item label="导出格式">{{ selectedTask.format.toUpperCase() }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusTagType(selectedTask.status)">
              {{ getStatusLabel(selectedTask.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="进度">{{ selectedTask.progress }}%</el-descriptions-item>
          <el-descriptions-item label="文件大小">
            {{ selectedTask.file_size ? formatFileSize(selectedTask.file_size) : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatDateTime(selectedTask.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="开始时间">
            {{ selectedTask.started_at ? formatDateTime(selectedTask.started_at) : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="完成时间">
            {{ selectedTask.completed_at ? formatDateTime(selectedTask.completed_at) : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="过期时间">
            {{ selectedTask.expires_at ? formatDateTime(selectedTask.expires_at) : '-' }}
          </el-descriptions-item>
        </el-descriptions>
        
        <div v-if="selectedTask.error_message" class="error-message">
          <h4>错误信息：</h4>
          <el-alert type="error" :closable="false">
            {{ selectedTask.error_message }}
          </el-alert>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Download, Close, View } from '@element-plus/icons-vue'
import { dataExportApi, type DataExportTask } from '@/api/dataExport'
import { formatDateTime, formatFileSize } from '@/utils/format'
import DataExportDialog from './DataExportDialog.vue'

// 响应式数据
const loading = ref(false)
const tasks = ref<DataExportTask[]>([])
const showExportDialog = ref(false)
const showDetailDialog = ref(false)
const selectedTask = ref<DataExportTask | null>(null)

const filters = ref({
  status: '',
  export_type: ''
})

const pagination = ref({
  page: 1,
  size: 20,
  total: 0
})

// 计算属性
const filteredTasks = computed(() => {
  let result = tasks.value
  
  if (filters.value.status) {
    result = result.filter(task => task.status === filters.value.status)
  }
  
  if (filters.value.export_type) {
    result = result.filter(task => task.export_type === filters.value.export_type)
  }
  
  return result
})

// 方法
const loadTasks = async () => {
  try {
    loading.value = true
    const skip = (pagination.value.page - 1) * pagination.value.size
    const data = await dataExportApi.getExportTasks({
      skip,
      limit: pagination.value.size
    })
    tasks.value = data
    // 注意：这里需要后端返回总数，暂时使用数据长度
    pagination.value.total = data.length
  } catch (error: any) {
    ElMessage.error(error.message || '加载任务列表失败')
  } finally {
    loading.value = false
  }
}

const downloadFile = (task: DataExportTask) => {
  if (!task.download_url) {
    ElMessage.error('下载链接不可用')
    return
  }
  
  // 创建下载链接
  const downloadUrl = dataExportApi.downloadExportFile(task.id)
  const link = document.createElement('a')
  link.href = downloadUrl
  link.download = `export_${task.id}.${task.format}`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

const cancelTask = async (task: DataExportTask) => {
  try {
    await ElMessageBox.confirm(
      '确定要取消这个导出任务吗？',
      '确认取消',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await dataExportApi.cancelExportTask(task.id)
    ElMessage.success('任务已取消')
    loadTasks()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '取消任务失败')
    }
  }
}

const viewTaskDetail = (task: DataExportTask) => {
  selectedTask.value = task
  showDetailDialog.value = true
}

const getExportTypeLabel = (type: string): string => {
  const labels: Record<string, string> = {
    orders: '订单',
    positions: '持仓',
    transactions: '交易记录',
    strategies: '策略',
    backtests: '回测',
    risk_reports: '风险报告',
    system_logs: '系统日志',
    user_data: '用户数据',
    full_backup: '完整备份'
  }
  return labels[type] || type
}

const getExportTypeTagType = (type: string): string => {
  const types: Record<string, string> = {
    orders: 'primary',
    positions: 'success',
    transactions: 'info',
    strategies: 'warning',
    backtests: 'danger',
    risk_reports: 'primary',
    system_logs: 'info',
    user_data: 'success',
    full_backup: 'danger'
  }
  return types[type] || 'info'
}

const getStatusLabel = (status: string): string => {
  const labels: Record<string, string> = {
    pending: '等待中',
    processing: '处理中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消'
  }
  return labels[status] || status
}

const getStatusTagType = (status: string): string => {
  const types: Record<string, string> = {
    pending: 'info',
    processing: 'warning',
    completed: 'success',
    failed: 'danger',
    cancelled: 'info'
  }
  return types[status] || 'info'
}

const isExpiringSoon = (expiresAt: string): boolean => {
  const expireTime = new Date(expiresAt).getTime()
  const now = Date.now()
  const oneDayMs = 24 * 60 * 60 * 1000
  return expireTime - now < oneDayMs
}

// 生命周期
onMounted(() => {
  loadTasks()
  
  // 设置定时刷新
  const interval = setInterval(() => {
    // 只有当有进行中的任务时才自动刷新
    if (tasks.value.some(task => ['pending', 'processing'].includes(task.status))) {
      loadTasks()
    }
  }, 5000)
  
  // 组件卸载时清除定时器
  onUnmounted(() => {
    clearInterval(interval)
  })
})
</script>

<style scoped>
.export-task-manager {
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

.filters {
  margin-bottom: 20px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 4px;
}

.pagination {
  margin-top: 20px;
  text-align: right;
}

.task-detail {
  padding: 10px 0;
}

.error-message {
  margin-top: 20px;
}

.error-message h4 {
  margin-bottom: 10px;
  color: #f56c6c;
}

.text-danger {
  color: #f56c6c;
}

:deep(.el-progress-bar__outer) {
  background-color: #e4e7ed;
}

:deep(.el-progress-bar__inner) {
  background-color: #409eff;
}
</style>