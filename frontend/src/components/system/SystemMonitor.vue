<template>
  <div class="system-monitor">
    <div class="header">
      <h3>系统监控</h3>
      <div class="actions">
        <el-button @click="refreshMetrics">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button type="primary" @click="generateReport">
          <el-icon><Document /></el-icon>
          生成报告
        </el-button>
      </div>
    </div>

    <!-- 系统指标卡片 -->
    <div class="metrics-cards">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="metric-card">
            <div class="metric-content">
              <div class="metric-icon cpu">
                <el-icon><Cpu /></el-icon>
              </div>
              <div class="metric-info">
                <div class="metric-value">{{ metrics?.cpu_usage?.toFixed(1) || 0 }}%</div>
                <div class="metric-label">CPU使用率</div>
              </div>
            </div>
            <el-progress
              :percentage="metrics?.cpu_usage || 0"
              :stroke-width="6"
              :show-text="false"
              :color="getProgressColor(metrics?.cpu_usage || 0)"
            />
          </el-card>
        </el-col>

        <el-col :span="6">
          <el-card class="metric-card">
            <div class="metric-content">
              <div class="metric-icon memory">
                <el-icon><Monitor /></el-icon>
              </div>
              <div class="metric-info">
                <div class="metric-value">{{ metrics?.memory_usage?.toFixed(1) || 0 }}%</div>
                <div class="metric-label">内存使用率</div>
              </div>
            </div>
            <el-progress
              :percentage="metrics?.memory_usage || 0"
              :stroke-width="6"
              :show-text="false"
              :color="getProgressColor(metrics?.memory_usage || 0)"
            />
          </el-card>
        </el-col>

        <el-col :span="6">
          <el-card class="metric-card">
            <div class="metric-content">
              <div class="metric-icon disk">
                <el-icon><FolderOpened /></el-icon>
              </div>
              <div class="metric-info">
                <div class="metric-value">{{ metrics?.disk_usage?.toFixed(1) || 0 }}%</div>
                <div class="metric-label">磁盘使用率</div>
              </div>
            </div>
            <el-progress
              :percentage="metrics?.disk_usage || 0"
              :stroke-width="6"
              :show-text="false"
              :color="getProgressColor(metrics?.disk_usage || 0)"
            />
          </el-card>
        </el-col>

        <el-col :span="6">
          <el-card class="metric-card">
            <div class="metric-content">
              <div class="metric-icon connections">
                <el-icon><Connection /></el-icon>
              </div>
              <div class="metric-info">
                <div class="metric-value">{{ metrics?.active_connections || 0 }}</div>
                <div class="metric-label">活跃连接</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 性能统计 -->
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>请求统计</span>
            </div>
          </template>
          <div class="stats-grid">
            <div class="stat-item">
              <div class="stat-value">{{ metrics?.request_count || 0 }}</div>
              <div class="stat-label">总请求数</div>
            </div>
            <div class="stat-item">
              <div class="stat-value error">{{ metrics?.error_count || 0 }}</div>
              <div class="stat-label">错误数量</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ metrics?.response_time_avg || 0 }}ms</div>
              <div class="stat-label">平均响应时间</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ errorRate }}%</div>
              <div class="stat-label">错误率</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>存储使用情况</span>
              <el-button size="small" @click="loadStorageUsage">刷新</el-button>
            </div>
          </template>
          <div v-if="storageUsage" class="storage-info">
            <div class="storage-item">
              <div class="storage-label">磁盘总容量</div>
              <div class="storage-value">{{ formatFileSize(storageUsage.disk_total) }}</div>
            </div>
            <div class="storage-item">
              <div class="storage-label">已使用</div>
              <div class="storage-value">{{ formatFileSize(storageUsage.disk_used) }}</div>
            </div>
            <div class="storage-item">
              <div class="storage-label">可用空间</div>
              <div class="storage-value">{{ formatFileSize(storageUsage.disk_free) }}</div>
            </div>
            <div class="storage-item">
              <div class="storage-label">数据库大小</div>
              <div class="storage-value">{{ formatFileSize(storageUsage.database_size) }}</div>
            </div>
            <div class="storage-item">
              <div class="storage-label">上传文件</div>
              <div class="storage-value">{{ formatFileSize(storageUsage.upload_files_size) }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 系统信息 -->
    <el-card style="margin-top: 20px">
      <template #header>
        <div class="card-header">
          <span>系统信息</span>
          <el-button size="small" @click="loadSystemInfo">刷新</el-button>
        </div>
      </template>
      <div v-if="systemInfo" class="system-info">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-descriptions :column="1" size="small">
              <el-descriptions-item label="操作系统">{{ systemInfo.platform }}</el-descriptions-item>
              <el-descriptions-item label="Python版本">{{ systemInfo.python_version }}</el-descriptions-item>
              <el-descriptions-item label="CPU核心数">{{ systemInfo.cpu_count }}</el-descriptions-item>
              <el-descriptions-item label="总内存">{{ formatFileSize(systemInfo.memory_total) }}</el-descriptions-item>
              <el-descriptions-item label="启动时间">{{ formatDateTime(systemInfo.boot_time) }}</el-descriptions-item>
            </el-descriptions>
          </el-col>
          <el-col :span="12">
            <el-descriptions :column="1" size="small">
              <el-descriptions-item label="应用版本">{{ systemInfo.application_version }}</el-descriptions-item>
              <el-descriptions-item label="运行环境">{{ systemInfo.environment }}</el-descriptions-item>
              <el-descriptions-item label="数据库">{{ systemInfo.database_url }}</el-descriptions-item>
              <el-descriptions-item label="Redis">{{ systemInfo.redis_url }}</el-descriptions-item>
            </el-descriptions>
          </el-col>
        </el-row>
        
        <div v-if="systemInfo.database_stats" style="margin-top: 20px">
          <h4>数据库统计</h4>
          <el-row :gutter="20">
            <el-col :span="4" v-for="(count, table) in systemInfo.database_stats" :key="table">
              <div class="db-stat">
                <div class="db-stat-value">{{ count }}</div>
                <div class="db-stat-label">{{ getTableLabel(table) }}</div>
              </div>
            </el-col>
          </el-row>
        </div>
      </div>
    </el-card>

    <!-- 性能报告对话框 -->
    <el-dialog
      v-model="showReportDialog"
      title="生成性能报告"
      width="500px"
    >
      <el-form :model="reportForm" label-width="100px">
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="reportDateRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DD HH:mm:ss"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showReportDialog = false">取消</el-button>
          <el-button type="primary" @click="handleGenerateReport" :loading="reportLoading">
            生成报告
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 性能报告显示对话框 -->
    <el-dialog
      v-model="showReportResultDialog"
      title="性能报告"
      width="800px"
      :close-on-click-modal="false"
    >
      <div v-if="performanceReport" class="performance-report">
        <div class="report-header">
          <h3>{{ performanceReport.report_id }}</h3>
          <p>生成时间: {{ formatDateTime(performanceReport.generated_at) }}</p>
          <p>时间范围: {{ formatDateTime(performanceReport.time_range.start) }} - {{ formatDateTime(performanceReport.time_range.end) }}</p>
        </div>

        <el-tabs>
          <el-tab-pane label="系统指标" name="metrics">
            <div class="report-metrics">
              <el-row :gutter="20">
                <el-col :span="8">
                  <div class="metric-box">
                    <div class="metric-title">CPU使用率</div>
                    <div class="metric-value">{{ performanceReport.metrics.cpu_usage.toFixed(1) }}%</div>
                  </div>
                </el-col>
                <el-col :span="8">
                  <div class="metric-box">
                    <div class="metric-title">内存使用率</div>
                    <div class="metric-value">{{ performanceReport.metrics.memory_usage.toFixed(1) }}%</div>
                  </div>
                </el-col>
                <el-col :span="8">
                  <div class="metric-box">
                    <div class="metric-title">平均响应时间</div>
                    <div class="metric-value">{{ performanceReport.metrics.response_time_avg }}ms</div>
                  </div>
                </el-col>
              </el-row>
            </div>
          </el-tab-pane>

          <el-tab-pane label="慢查询" name="slow-queries">
            <el-table :data="performanceReport.slow_queries" size="small">
              <el-table-column prop="query" label="查询语句" show-overflow-tooltip />
              <el-table-column prop="duration" label="耗时(s)" width="100" />
              <el-table-column prop="count" label="次数" width="80" />
              <el-table-column prop="avg_duration" label="平均耗时(s)" width="120" />
            </el-table>
          </el-tab-pane>

          <el-tab-pane label="错误统计" name="errors">
            <div class="error-summary">
              <div v-for="(count, module) in performanceReport.error_summary" :key="module" class="error-item">
                <span class="error-module">{{ module }}</span>
                <span class="error-count">{{ count }} 次</span>
              </div>
            </div>
          </el-tab-pane>

          <el-tab-pane label="优化建议" name="recommendations">
            <div class="recommendations">
              <el-alert
                v-for="(recommendation, index) in performanceReport.recommendations"
                :key="index"
                :title="recommendation"
                type="info"
                :closable="false"
                style="margin-bottom: 10px"
              />
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Refresh, Document, Cpu, Monitor, FolderOpened, Connection
} from '@element-plus/icons-vue'
import { dataExportApi, type SystemMetrics, type StorageUsage, type SystemInfo, type PerformanceReport } from '@/api/dataExport'
import { formatDateTime, formatFileSize } from '@/utils/format'

// 响应式数据
const metrics = ref<SystemMetrics | null>(null)
const storageUsage = ref<StorageUsage | null>(null)
const systemInfo = ref<SystemInfo | null>(null)
const performanceReport = ref<PerformanceReport | null>(null)

const showReportDialog = ref(false)
const showReportResultDialog = ref(false)
const reportLoading = ref(false)
const reportDateRange = ref<[string, string] | null>(null)
const reportForm = ref({})

let refreshTimer: NodeJS.Timeout | null = null

// 计算属性
const errorRate = computed(() => {
  if (!metrics.value || metrics.value.request_count === 0) return 0
  return ((metrics.value.error_count / metrics.value.request_count) * 100).toFixed(2)
})

// 方法
const refreshMetrics = async () => {
  try {
    metrics.value = await dataExportApi.getSystemMetrics()
  } catch (error: any) {
    ElMessage.error(error.message || '获取系统指标失败')
  }
}

const loadStorageUsage = async () => {
  try {
    storageUsage.value = await dataExportApi.getStorageUsage()
  } catch (error: any) {
    ElMessage.error(error.message || '获取存储使用情况失败')
  }
}

const loadSystemInfo = async () => {
  try {
    systemInfo.value = await dataExportApi.getSystemInfo()
  } catch (error: any) {
    ElMessage.error(error.message || '获取系统信息失败')
  }
}

const generateReport = () => {
  // 设置默认时间范围（最近24小时）
  const now = new Date()
  const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000)
  reportDateRange.value = [
    yesterday.toISOString().slice(0, 19).replace('T', ' '),
    now.toISOString().slice(0, 19).replace('T', ' ')
  ]
  showReportDialog.value = true
}

const handleGenerateReport = async () => {
  if (!reportDateRange.value) {
    ElMessage.error('请选择时间范围')
    return
  }

  try {
    reportLoading.value = true
    performanceReport.value = await dataExportApi.generatePerformanceReport(
      reportDateRange.value[0],
      reportDateRange.value[1]
    )
    showReportDialog.value = false
    showReportResultDialog.value = true
  } catch (error: any) {
    ElMessage.error(error.message || '生成性能报告失败')
  } finally {
    reportLoading.value = false
  }
}

const getProgressColor = (percentage: number): string => {
  if (percentage < 60) return '#67c23a'
  if (percentage < 80) return '#e6a23c'
  return '#f56c6c'
}

const getTableLabel = (table: string): string => {
  const labels: Record<string, string> = {
    users_count: '用户',
    orders_count: '订单',
    positions_count: '持仓',
    transactions_count: '交易记录',
    strategies_count: '策略',
    backtests_count: '回测'
  }
  return labels[table] || table
}

// 生命周期
onMounted(() => {
  // 初始加载
  refreshMetrics()
  loadStorageUsage()
  loadSystemInfo()
  
  // 设置定时刷新（每30秒）
  refreshTimer = setInterval(() => {
    refreshMetrics()
  }, 30000)
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})
</script>

<style scoped>
.system-monitor {
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

.metrics-cards {
  margin-bottom: 20px;
}

.metric-card {
  height: 120px;
}

.metric-content {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.metric-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12px;
  font-size: 24px;
  color: white;
}

.metric-icon.cpu {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.metric-icon.memory {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.metric-icon.disk {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.metric-icon.connections {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.metric-info {
  flex: 1;
}

.metric-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
  line-height: 1;
}

.metric-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.stat-item {
  text-align: center;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 8px;
}

.stat-value.error {
  color: #f56c6c;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.storage-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.storage-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #ebeef5;
}

.storage-item:last-child {
  border-bottom: none;
}

.storage-label {
  color: #606266;
}

.storage-value {
  font-weight: bold;
  color: #303133;
}

.system-info {
  padding: 10px 0;
}

.db-stat {
  text-align: center;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
}

.db-stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 8px;
}

.db-stat-label {
  font-size: 14px;
  color: #909399;
}

.performance-report {
  padding: 10px 0;
}

.report-header {
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #ebeef5;
}

.report-header h3 {
  margin: 0 0 10px 0;
  color: #303133;
}

.report-header p {
  margin: 5px 0;
  color: #606266;
}

.report-metrics {
  padding: 20px 0;
}

.metric-box {
  text-align: center;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.metric-title {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.metric-box .metric-value {
  font-size: 24px;
  font-weight: bold;
  color: #409eff;
}

.error-summary {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.error-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #fef0f0;
  border-radius: 4px;
  border-left: 4px solid #f56c6c;
}

.error-module {
  font-weight: bold;
  color: #303133;
}

.error-count {
  color: #f56c6c;
  font-weight: bold;
}

.recommendations {
  padding: 10px 0;
}

.dialog-footer {
  text-align: right;
}
</style>