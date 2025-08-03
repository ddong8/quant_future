<template>
  <div class="data-integrity-checker">
    <div class="header">
      <h3>数据完整性检查</h3>
      <el-button type="primary" @click="startIntegrityCheck" :loading="checking">
        <el-icon><Search /></el-icon>
        开始检查
      </el-button>
    </div>

    <div class="check-status" v-if="currentCheck">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>检查状态</span>
            <el-tag :type="getStatusTagType(currentCheck.status)">
              {{ getStatusLabel(currentCheck.status) }}
            </el-tag>
          </div>
        </template>

        <div class="check-info">
          <el-row :gutter="20">
            <el-col :span="6">
              <div class="info-item">
                <div class="info-label">检查ID</div>
                <div class="info-value">{{ currentCheck.check_id }}</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="info-item">
                <div class="info-label">开始时间</div>
                <div class="info-value">{{ formatDateTime(currentCheck.started_at) }}</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="info-item">
                <div class="info-label">完成时间</div>
                <div class="info-value">
                  {{ currentCheck.completed_at ? formatDateTime(currentCheck.completed_at) : '-' }}
                </div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="info-item">
                <div class="info-label">发现问题</div>
                <div class="info-value" :class="{ 'text-danger': currentCheck.issues_found > 0 }">
                  {{ currentCheck.issues_found }} 个
                </div>
              </div>
            </el-col>
          </el-row>

          <div class="progress-info" v-if="currentCheck.status === 'running'">
            <div class="progress-label">
              检查进度: {{ currentCheck.checked_tables }} / {{ currentCheck.total_tables }} 个表
            </div>
            <el-progress
              :percentage="getProgressPercentage()"
              :stroke-width="8"
              :show-text="false"
            />
          </div>
        </div>
      </el-card>
    </div>

    <!-- 问题列表 -->
    <div class="issues-section" v-if="currentCheck && currentCheck.issues && currentCheck.issues.length > 0">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>发现的问题</span>
            <el-tag type="danger">{{ currentCheck.issues.length }} 个问题</el-tag>
          </div>
        </template>

        <div class="issues-list">
          <div
            v-for="(issue, index) in currentCheck.issues"
            :key="index"
            class="issue-item"
          >
            <div class="issue-header">
              <el-tag :type="getIssueTagType(issue.type)" size="small">
                {{ getIssueTypeLabel(issue.type) }}
              </el-tag>
              <span v-if="issue.table" class="issue-table">表: {{ issue.table }}</span>
              <span v-if="issue.count" class="issue-count">数量: {{ issue.count }}</span>
            </div>
            <div class="issue-description">
              {{ issue.description }}
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 修复建议 -->
    <div class="recommendations-section" v-if="currentCheck && currentCheck.recommendations && currentCheck.recommendations.length > 0">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>修复建议</span>
          </div>
        </template>

        <div class="recommendations-list">
          <el-alert
            v-for="(recommendation, index) in currentCheck.recommendations"
            :key="index"
            :title="recommendation"
            type="info"
            :closable="false"
            style="margin-bottom: 10px"
          />
        </div>
      </el-card>
    </div>

    <!-- 历史检查记录 -->
    <div class="history-section">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>检查历史</span>
            <el-button size="small" @click="loadCheckHistory">刷新</el-button>
          </div>
        </template>

        <el-table :data="checkHistory" stripe style="width: 100%">
          <el-table-column prop="check_id" label="检查ID" width="200" />
          
          <el-table-column prop="started_at" label="开始时间" width="180">
            <template #default="{ row }">
              {{ formatDateTime(row.started_at) }}
            </template>
          </el-table-column>

          <el-table-column prop="completed_at" label="完成时间" width="180">
            <template #default="{ row }">
              {{ row.completed_at ? formatDateTime(row.completed_at) : '-' }}
            </template>
          </el-table-column>

          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getStatusTagType(row.status)" size="small">
                {{ getStatusLabel(row.status) }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column prop="total_tables" label="检查表数" width="100" />
          
          <el-table-column prop="issues_found" label="发现问题" width="100">
            <template #default="{ row }">
              <span :class="{ 'text-danger': row.issues_found > 0 }">
                {{ row.issues_found }}
              </span>
            </template>
          </el-table-column>

          <el-table-column label="耗时" width="100">
            <template #default="{ row }">
              <span v-if="row.completed_at">
                {{ getDuration(row.started_at, row.completed_at) }}
              </span>
              <span v-else>-</span>
            </template>
          </el-table-column>

          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <el-button
                type="text"
                size="small"
                @click="viewCheckDetail(row)"
              >
                查看详情
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <!-- 检查详情对话框 -->
    <el-dialog
      v-model="showDetailDialog"
      title="检查详情"
      width="800px"
      :close-on-click-modal="false"
    >
      <div v-if="selectedCheck" class="check-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="检查ID">{{ selectedCheck.check_id }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusTagType(selectedCheck.status)">
              {{ getStatusLabel(selectedCheck.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="开始时间">{{ formatDateTime(selectedCheck.started_at) }}</el-descriptions-item>
          <el-descriptions-item label="完成时间">
            {{ selectedCheck.completed_at ? formatDateTime(selectedCheck.completed_at) : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="检查表数">{{ selectedCheck.total_tables }}</el-descriptions-item>
          <el-descriptions-item label="已检查">{{ selectedCheck.checked_tables }}</el-descriptions-item>
          <el-descriptions-item label="发现问题">{{ selectedCheck.issues_found }}</el-descriptions-item>
          <el-descriptions-item label="耗时">
            {{ selectedCheck.completed_at ? getDuration(selectedCheck.started_at, selectedCheck.completed_at) : '-' }}
          </el-descriptions-item>
        </el-descriptions>

        <div v-if="selectedCheck.issues && selectedCheck.issues.length > 0" class="detail-issues">
          <h4>问题详情：</h4>
          <div class="issues-list">
            <div
              v-for="(issue, index) in selectedCheck.issues"
              :key="index"
              class="issue-item"
            >
              <div class="issue-header">
                <el-tag :type="getIssueTagType(issue.type)" size="small">
                  {{ getIssueTypeLabel(issue.type) }}
                </el-tag>
                <span v-if="issue.table" class="issue-table">表: {{ issue.table }}</span>
                <span v-if="issue.count" class="issue-count">数量: {{ issue.count }}</span>
              </div>
              <div class="issue-description">
                {{ issue.description }}
              </div>
            </div>
          </div>
        </div>

        <div v-if="selectedCheck.recommendations && selectedCheck.recommendations.length > 0" class="detail-recommendations">
          <h4>修复建议：</h4>
          <ul>
            <li v-for="(recommendation, index) in selectedCheck.recommendations" :key="index">
              {{ recommendation }}
            </li>
          </ul>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { dataExportApi, type DataIntegrityCheck } from '@/api/dataExport'
import { formatDateTime } from '@/utils/format'

// 响应式数据
const checking = ref(false)
const currentCheck = ref<DataIntegrityCheck | null>(null)
const checkHistory = ref<DataIntegrityCheck[]>([])
const selectedCheck = ref<DataIntegrityCheck | null>(null)
const showDetailDialog = ref(false)

let checkTimer: NodeJS.Timeout | null = null

// 方法
const startIntegrityCheck = async () => {
  try {
    checking.value = true
    currentCheck.value = await dataExportApi.checkDataIntegrity()
    
    // 如果检查正在进行，启动轮询
    if (currentCheck.value.status === 'running') {
      startPolling()
    }
    
    ElMessage.success('数据完整性检查已开始')
  } catch (error: any) {
    ElMessage.error(error.message || '启动检查失败')
  } finally {
    checking.value = false
  }
}

const startPolling = () => {
  checkTimer = setInterval(async () => {
    if (!currentCheck.value) return
    
    try {
      // 这里需要一个获取检查状态的API
      // const updatedCheck = await dataExportApi.getIntegrityCheckStatus(currentCheck.value.check_id)
      // currentCheck.value = updatedCheck
      
      // 如果检查完成，停止轮询
      if (currentCheck.value.status !== 'running') {
        stopPolling()
        loadCheckHistory()
      }
    } catch (error) {
      console.error('轮询检查状态失败:', error)
    }
  }, 3000)
}

const stopPolling = () => {
  if (checkTimer) {
    clearInterval(checkTimer)
    checkTimer = null
  }
}

const loadCheckHistory = () => {
  // 这里需要一个获取检查历史的API
  // 暂时使用模拟数据
  checkHistory.value = []
}

const viewCheckDetail = (check: DataIntegrityCheck) => {
  selectedCheck.value = check
  showDetailDialog.value = true
}

const getProgressPercentage = (): number => {
  if (!currentCheck.value || currentCheck.value.total_tables === 0) return 0
  return Math.round((currentCheck.value.checked_tables / currentCheck.value.total_tables) * 100)
}

const getStatusLabel = (status: string): string => {
  const labels: Record<string, string> = {
    running: '检查中',
    completed: '已完成',
    failed: '失败'
  }
  return labels[status] || status
}

const getStatusTagType = (status: string): string => {
  const types: Record<string, string> = {
    running: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return types[status] || 'info'
}

const getIssueTypeLabel = (type: string): string => {
  const labels: Record<string, string> = {
    duplicate_records: '重复记录',
    orphan_records: '孤立记录',
    check_error: '检查错误',
    constraint_violation: '约束违反',
    data_inconsistency: '数据不一致'
  }
  return labels[type] || type
}

const getIssueTagType = (type: string): string => {
  const types: Record<string, string> = {
    duplicate_records: 'warning',
    orphan_records: 'danger',
    check_error: 'danger',
    constraint_violation: 'danger',
    data_inconsistency: 'warning'
  }
  return types[type] || 'info'
}

const getDuration = (startTime: string, endTime: string): string => {
  const start = new Date(startTime).getTime()
  const end = new Date(endTime).getTime()
  const duration = Math.round((end - start) / 1000)
  
  if (duration < 60) {
    return `${duration}秒`
  } else if (duration < 3600) {
    return `${Math.round(duration / 60)}分钟`
  } else {
    return `${Math.round(duration / 3600)}小时`
  }
}

// 生命周期
onMounted(() => {
  loadCheckHistory()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.data-integrity-checker {
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

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.check-status,
.issues-section,
.recommendations-section,
.history-section {
  margin-bottom: 20px;
}

.check-info {
  padding: 10px 0;
}

.info-item {
  text-align: center;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
}

.info-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.info-value {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}

.info-value.text-danger {
  color: #f56c6c;
}

.progress-info {
  margin-top: 20px;
}

.progress-label {
  margin-bottom: 10px;
  color: #606266;
  font-size: 14px;
}

.issues-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.issue-item {
  padding: 16px;
  background: #fef0f0;
  border-radius: 8px;
  border-left: 4px solid #f56c6c;
}

.issue-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.issue-table,
.issue-count {
  font-size: 12px;
  color: #909399;
  background: #f0f2f5;
  padding: 2px 6px;
  border-radius: 4px;
}

.issue-description {
  color: #606266;
  line-height: 1.6;
}

.recommendations-list {
  padding: 10px 0;
}

.text-danger {
  color: #f56c6c;
}

.check-detail {
  padding: 10px 0;
}

.detail-issues,
.detail-recommendations {
  margin-top: 20px;
}

.detail-issues h4,
.detail-recommendations h4 {
  margin-bottom: 12px;
  color: #303133;
}

.detail-recommendations ul {
  margin: 0;
  padding-left: 20px;
}

.detail-recommendations li {
  margin-bottom: 8px;
  color: #606266;
  line-height: 1.6;
}
</style>