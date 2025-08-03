<template>
  <div class="system-maintenance">
    <div class="header">
      <h3>系统维护</h3>
      <p>系统清理、备份管理和维护操作</p>
    </div>

    <!-- 快速操作 -->
    <div class="quick-actions">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="action-card" @click="cleanupExpiredExports">
            <div class="action-content">
              <div class="action-icon cleanup">
                <el-icon><Delete /></el-icon>
              </div>
              <div class="action-info">
                <div class="action-title">清理过期文件</div>
                <div class="action-desc">清理过期的导出文件</div>
              </div>
            </div>
          </el-card>
        </el-col>

        <el-col :span="6">
          <el-card class="action-card" @click="showBackupDialog = true">
            <div class="action-content">
              <div class="action-icon backup">
                <el-icon><FolderAdd /></el-icon>
              </div>
              <div class="action-info">
                <div class="action-title">创建备份</div>
                <div class="action-desc">创建系统数据备份</div>
              </div>
            </div>
          </el-card>
        </el-col>

        <el-col :span="6">
          <el-card class="action-card" @click="checkDataIntegrity">
            <div class="action-content">
              <div class="action-icon integrity">
                <el-icon><Search /></el-icon>
              </div>
              <div class="action-info">
                <div class="action-title">数据完整性</div>
                <div class="action-desc">检查数据完整性</div>
              </div>
            </div>
          </el-card>
        </el-col>

        <el-col :span="6">
          <el-card class="action-card" @click="optimizeDatabase">
            <div class="action-content">
              <div class="action-icon optimize">
                <el-icon><Tools /></el-icon>
              </div>
              <div class="action-info">
                <div class="action-title">数据库优化</div>
                <div class="action-desc">优化数据库性能</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 存储管理 -->
    <el-card class="storage-management">
      <template #header>
        <div class="card-header">
          <span>存储管理</span>
          <el-button size="small" @click="loadStorageInfo">刷新</el-button>
        </div>
      </template>

      <div v-if="storageInfo" class="storage-content">
        <div class="storage-overview">
          <el-row :gutter="20">
            <el-col :span="8">
              <div class="storage-item">
                <div class="storage-label">磁盘总容量</div>
                <div class="storage-value">{{ formatFileSize(storageInfo.disk_total) }}</div>
                <div class="storage-bar">
                  <el-progress
                    :percentage="storageInfo.disk_percent"
                    :stroke-width="8"
                    :color="getStorageColor(storageInfo.disk_percent)"
                  />
                </div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="storage-item">
                <div class="storage-label">数据库大小</div>
                <div class="storage-value">{{ formatFileSize(storageInfo.database_size) }}</div>
                <div class="storage-desc">
                  占总容量 {{ ((storageInfo.database_size / storageInfo.disk_total) * 100).toFixed(2) }}%
                </div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="storage-item">
                <div class="storage-label">上传文件</div>
                <div class="storage-value">{{ formatFileSize(storageInfo.upload_files_size) }}</div>
                <div class="storage-desc">
                  占总容量 {{ ((storageInfo.upload_files_size / storageInfo.disk_total) * 100).toFixed(2) }}%
                </div>
              </div>
            </el-col>
          </el-row>
        </div>

        <div class="storage-actions">
          <el-button @click="cleanupExpiredExports" :loading="cleanupLoading">
            <el-icon><Delete /></el-icon>
            清理过期文件
          </el-button>
          <el-button @click="analyzeStorageUsage">
            <el-icon><PieChart /></el-icon>
            存储分析
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 维护任务 -->
    <el-card class="maintenance-tasks">
      <template #header>
        <div class="card-header">
          <span>维护任务</span>
        </div>
      </template>

      <div class="tasks-list">
        <div class="task-item" v-for="task in maintenanceTasks" :key="task.id">
          <div class="task-info">
            <div class="task-name">{{ task.name }}</div>
            <div class="task-desc">{{ task.description }}</div>
            <div class="task-schedule">{{ task.schedule }}</div>
          </div>
          <div class="task-status">
            <el-tag :type="getTaskStatusType(task.status)">
              {{ task.status }}
            </el-tag>
          </div>
          <div class="task-actions">
            <el-button size="small" @click="runTask(task)">
              立即执行
            </el-button>
            <el-button size="small" type="text" @click="viewTaskLog(task)">
              查看日志
            </el-button>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 系统备份对话框 -->
    <el-dialog
      v-model="showBackupDialog"
      title="创建系统备份"
      width="500px"
    >
      <el-form :model="backupForm" label-width="120px">
        <el-form-item label="备份内容">
          <el-checkbox-group v-model="backupForm.includes">
            <el-checkbox label="user_data">用户数据</el-checkbox>
            <el-checkbox label="system_logs">系统日志</el-checkbox>
            <el-checkbox label="market_data">市场数据</el-checkbox>
          </el-checkbox-group>
        </el-form-item>

        <el-form-item label="压缩备份">
          <el-switch v-model="backupForm.compress" />
        </el-form-item>

        <el-form-item label="加密备份">
          <el-switch v-model="backupForm.encrypt" />
        </el-form-item>

        <el-form-item v-if="backupForm.encrypt" label="加密密码">
          <el-input
            v-model="backupForm.password"
            type="password"
            placeholder="请输入加密密码"
            show-password
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showBackupDialog = false">取消</el-button>
          <el-button type="primary" @click="createBackup" :loading="backupLoading">
            创建备份
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 清理结果对话框 -->
    <el-dialog
      v-model="showCleanupResult"
      title="清理结果"
      width="400px"
    >
      <div v-if="cleanupResult" class="cleanup-result">
        <div class="result-item">
          <span class="result-label">清理文件数:</span>
          <span class="result-value">{{ cleanupResult.cleaned_files }}</span>
        </div>
        <div class="result-item">
          <span class="result-label">释放空间:</span>
          <span class="result-value">{{ cleanupResult.freed_space_mb }} MB</span>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Delete, FolderAdd, Search, Tools, PieChart
} from '@element-plus/icons-vue'
import { dataExportApi, type StorageUsage, type SystemBackupRequest } from '@/api/dataExport'
import { formatFileSize } from '@/utils/format'

interface MaintenanceTask {
  id: string
  name: string
  description: string
  schedule: string
  status: 'idle' | 'running' | 'completed' | 'failed'
  lastRun?: string
}

// 响应式数据
const storageInfo = ref<StorageUsage | null>(null)
const showBackupDialog = ref(false)
const showCleanupResult = ref(false)
const backupLoading = ref(false)
const cleanupLoading = ref(false)

const backupForm = ref({
  includes: ['user_data'],
  compress: true,
  encrypt: false,
  password: ''
})

const cleanupResult = ref<{
  cleaned_files: number
  freed_space_bytes: number
  freed_space_mb: number
} | null>(null)

const maintenanceTasks = ref<MaintenanceTask[]>([
  {
    id: 'cleanup_logs',
    name: '日志清理',
    description: '清理30天前的系统日志',
    schedule: '每天 02:00',
    status: 'idle'
  },
  {
    id: 'backup_database',
    name: '数据库备份',
    description: '创建数据库增量备份',
    schedule: '每天 03:00',
    status: 'idle'
  },
  {
    id: 'optimize_database',
    name: '数据库优化',
    description: '优化数据库索引和统计信息',
    schedule: '每周日 04:00',
    status: 'idle'
  },
  {
    id: 'cleanup_temp_files',
    name: '临时文件清理',
    description: '清理临时文件和缓存',
    schedule: '每天 01:00',
    status: 'idle'
  }
])

// 方法
const loadStorageInfo = async () => {
  try {
    storageInfo.value = await dataExportApi.getStorageUsage()
  } catch (error: any) {
    ElMessage.error(error.message || '获取存储信息失败')
  }
}

const cleanupExpiredExports = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清理过期的导出文件吗？此操作不可撤销。',
      '确认清理',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    cleanupLoading.value = true
    cleanupResult.value = await dataExportApi.cleanupExpiredExports()
    showCleanupResult.value = true
    
    // 刷新存储信息
    loadStorageInfo()
    
    ElMessage.success('清理完成')
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '清理失败')
    }
  } finally {
    cleanupLoading.value = false
  }
}

const createBackup = async () => {
  try {
    if (backupForm.value.encrypt && !backupForm.value.password) {
      ElMessage.error('请输入加密密码')
      return
    }

    backupLoading.value = true
    
    const request: SystemBackupRequest = {
      include_user_data: backupForm.value.includes.includes('user_data'),
      include_system_logs: backupForm.value.includes.includes('system_logs'),
      include_market_data: backupForm.value.includes.includes('market_data'),
      compress: backupForm.value.compress,
      encrypt: backupForm.value.encrypt,
      password: backupForm.value.encrypt ? backupForm.value.password : undefined
    }

    await dataExportApi.createSystemBackup(request)
    
    ElMessage.success('备份任务已创建')
    showBackupDialog.value = false
    
    // 重置表单
    backupForm.value = {
      includes: ['user_data'],
      compress: true,
      encrypt: false,
      password: ''
    }
  } catch (error: any) {
    ElMessage.error(error.message || '创建备份失败')
  } finally {
    backupLoading.value = false
  }
}

const checkDataIntegrity = async () => {
  try {
    await dataExportApi.checkDataIntegrity()
    ElMessage.success('数据完整性检查已开始，请在数据完整性页面查看结果')
  } catch (error: any) {
    ElMessage.error(error.message || '启动检查失败')
  }
}

const optimizeDatabase = async () => {
  try {
    await ElMessageBox.confirm(
      '数据库优化可能需要较长时间，期间可能影响系统性能。确定要继续吗？',
      '确认优化',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    ElMessage.info('数据库优化功能开发中...')
  } catch (error) {
    // 用户取消
  }
}

const analyzeStorageUsage = () => {
  ElMessage.info('存储分析功能开发中...')
}

const runTask = async (task: MaintenanceTask) => {
  try {
    await ElMessageBox.confirm(
      `确定要立即执行"${task.name}"任务吗？`,
      '确认执行',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info'
      }
    )

    task.status = 'running'
    ElMessage.success(`任务"${task.name}"已开始执行`)
    
    // 模拟任务执行
    setTimeout(() => {
      task.status = 'completed'
      task.lastRun = new Date().toISOString()
      ElMessage.success(`任务"${task.name}"执行完成`)
    }, 3000)
  } catch (error) {
    // 用户取消
  }
}

const viewTaskLog = (task: MaintenanceTask) => {
  ElMessage.info(`查看"${task.name}"任务日志功能开发中...`)
}

const getStorageColor = (percentage: number): string => {
  if (percentage < 70) return '#67c23a'
  if (percentage < 85) return '#e6a23c'
  return '#f56c6c'
}

const getTaskStatusType = (status: string): string => {
  const types: Record<string, string> = {
    idle: 'info',
    running: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return types[status] || 'info'
}

// 生命周期
onMounted(() => {
  loadStorageInfo()
})
</script>

<style scoped>
.system-maintenance {
  padding: 20px;
}

.header {
  margin-bottom: 30px;
}

.header h3 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 24px;
}

.header p {
  margin: 0;
  color: #606266;
  font-size: 14px;
}

.quick-actions {
  margin-bottom: 30px;
}

.action-card {
  cursor: pointer;
  transition: all 0.3s;
  height: 120px;
}

.action-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.action-content {
  display: flex;
  align-items: center;
  height: 100%;
}

.action-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
  font-size: 24px;
  color: white;
}

.action-icon.cleanup {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.action-icon.backup {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.action-icon.integrity {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.action-icon.optimize {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.action-info {
  flex: 1;
}

.action-title {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 4px;
}

.action-desc {
  font-size: 14px;
  color: #909399;
}

.storage-management,
.maintenance-tasks {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.storage-content {
  padding: 10px 0;
}

.storage-overview {
  margin-bottom: 20px;
}

.storage-item {
  text-align: center;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.storage-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.storage-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 8px;
}

.storage-desc {
  font-size: 12px;
  color: #909399;
}

.storage-bar {
  margin-top: 12px;
}

.storage-actions {
  display: flex;
  gap: 12px;
}

.tasks-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.task-item {
  display: flex;
  align-items: center;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #409eff;
}

.task-info {
  flex: 1;
}

.task-name {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 4px;
}

.task-desc {
  font-size: 14px;
  color: #606266;
  margin-bottom: 4px;
}

.task-schedule {
  font-size: 12px;
  color: #909399;
}

.task-status {
  margin: 0 20px;
}

.task-actions {
  display: flex;
  gap: 8px;
}

.dialog-footer {
  text-align: right;
}

.cleanup-result {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.result-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #f0f9ff;
  border-radius: 4px;
}

.result-label {
  color: #606266;
}

.result-value {
  font-weight: bold;
  color: #409eff;
}
</style>