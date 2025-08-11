<template>
  <div class="market-anomaly-monitor">
    <!-- 头部工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <h3>市场异动监控</h3>
      </div>
      <div class="toolbar-right">
        <el-select v-model="timeRange" style="width: 120px; margin-right: 12px" @change="loadAnomalies">
          <el-option label="1小时" :value="1" />
          <el-option label="6小时" :value="6" />
          <el-option label="24小时" :value="24" />
          <el-option label="3天" :value="72" />
          <el-option label="7天" :value="168" />
        </el-select>
        
        <el-select v-model="severityFilter" placeholder="严重程度" clearable style="width: 120px; margin-right: 12px" @change="loadAnomalies">
          <el-option label="全部" value="" />
          <el-option label="严重" value="CRITICAL" />
          <el-option label="高" value="HIGH" />
          <el-option label="中" value="MEDIUM" />
          <el-option label="低" value="LOW" />
        </el-select>
        
        <el-button @click="loadAnomalies" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <div class="stat-card critical">
        <div class="stat-number">{{ getAnomalyCount('CRITICAL') }}</div>
        <div class="stat-label">严重异动</div>
      </div>
      <div class="stat-card high">
        <div class="stat-number">{{ getAnomalyCount('HIGH') }}</div>
        <div class="stat-label">高级异动</div>
      </div>
      <div class="stat-card medium">
        <div class="stat-number">{{ getAnomalyCount('MEDIUM') }}</div>
        <div class="stat-label">中级异动</div>
      </div>
      <div class="stat-card low">
        <div class="stat-number">{{ getAnomalyCount('LOW') }}</div>
        <div class="stat-label">低级异动</div>
      </div>
    </div>

    <!-- 异动列表 -->
    <div class="anomaly-list">
      <div v-if="loading" class="loading-state">
        <el-icon class="is-loading"><Loading /></el-icon>
        加载中...
      </div>
      
      <div v-else-if="anomalies.length === 0" class="empty-state">
        <el-empty description="暂无市场异动" />
      </div>
      
      <div v-else class="anomaly-items">
        <div
          v-for="anomaly in anomalies"
          :key="anomaly.id"
          class="anomaly-item"
          :class="{ 'processed': anomaly.is_processed }"
        >
          <!-- 异动头部 -->
          <div class="anomaly-header">
            <div class="anomaly-title">
              <el-tag :type="getSeverityType(anomaly.severity)" size="small">
                {{ getSeverityText(anomaly.severity) }}
              </el-tag>
              <span class="title-text">{{ anomaly.title }}</span>
            </div>
            <div class="anomaly-time">
              {{ formatTime(anomaly.detected_at) }}
            </div>
          </div>

          <!-- 异动内容 -->
          <div class="anomaly-content">
            <div class="anomaly-symbol">
              <span class="symbol-code">{{ anomaly.symbol.symbol }}</span>
              <span class="symbol-name">{{ anomaly.symbol.name }}</span>
            </div>
            <div class="anomaly-description">
              {{ anomaly.description }}
            </div>
          </div>

          <!-- 异动数据 -->
          <div class="anomaly-data">
            <div v-if="anomaly.trigger_price" class="data-item">
              <span class="label">触发价格:</span>
              <span class="value price">{{ formatPrice(anomaly.trigger_price) }}</span>
            </div>
            <div v-if="anomaly.price_change_percent" class="data-item">
              <span class="label">涨跌幅:</span>
              <span class="value" :class="getChangeClass(anomaly.price_change_percent)">
                {{ formatPercent(anomaly.price_change_percent) }}
              </span>
            </div>
            <div v-if="anomaly.volume_ratio > 1" class="data-item">
              <span class="label">成交量倍数:</span>
              <span class="value volume">{{ anomaly.volume_ratio.toFixed(1) }}x</span>
            </div>
          </div>

          <!-- 异动操作 -->
          <div class="anomaly-actions">
            <el-button size="small" text @click="viewSymbolDetail(anomaly.symbol.symbol)">
              查看详情
            </el-button>
            <el-button size="small" text @click="createAlert(anomaly.symbol.symbol)">
              设置提醒
            </el-button>
            <el-button 
              v-if="!anomaly.is_processed" 
              size="small" 
              text 
              type="primary"
              @click="markAsProcessed(anomaly)"
            >
              标记已处理
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 分页 -->
    <div v-if="anomalies.length > 0" class="pagination">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="totalCount"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Loading } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { getMarketAnomalies, type MarketAnomaly } from '@/api/marketDepth'
import { formatPrice, formatPercent, formatTime } from '@/utils/format'

const router = useRouter()

// 响应式数据
const loading = ref(false)
const timeRange = ref(24)
const severityFilter = ref('')
const anomalies = ref<MarketAnomaly[]>([])
const currentPage = ref(1)
const pageSize = ref(20)
const totalCount = ref(0)

// 定时器
let refreshTimer: NodeJS.Timeout | null = null

// 分页后的异动列表
const paginatedAnomalies = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return anomalies.value.slice(start, end)
})

// 获取异动数量统计
const getAnomalyCount = (severity: string) => {
  return anomalies.value.filter(anomaly => anomaly.severity === severity).length
}

// 加载异动数据
const loadAnomalies = async () => {
  try {
    loading.value = true
    const response = await getMarketAnomalies(timeRange.value, severityFilter.value)
    anomalies.value = response.data.anomalies
    totalCount.value = response.data.count
  } catch (error) {
    console.error('加载市场异动失败:', error)
    ElMessage.error('加载市场异动失败')
  } finally {
    loading.value = false
  }
}

// 获取严重程度类型
const getSeverityType = (severity: string) => {
  switch (severity) {
    case 'CRITICAL': return 'danger'
    case 'HIGH': return 'warning'
    case 'MEDIUM': return 'primary'
    case 'LOW': return 'info'
    default: return 'info'
  }
}

// 获取严重程度文本
const getSeverityText = (severity: string) => {
  switch (severity) {
    case 'CRITICAL': return '严重'
    case 'HIGH': return '高'
    case 'MEDIUM': return '中'
    case 'LOW': return '低'
    default: return '未知'
  }
}

// 获取涨跌颜色类名
const getChangeClass = (value: number) => {
  if (value > 0) return 'price-up'
  if (value < 0) return 'price-down'
  return 'price-neutral'
}

// 查看标的详情
const viewSymbolDetail = (symbolCode: string) => {
  router.push(`/market/technical?symbol=${symbolCode}`)
}

// 创建提醒
const createAlert = (symbolCode: string) => {
  // 这里可以打开价格提醒对话框
  ElMessage.info(`为 ${symbolCode} 创建价格提醒功能待实现`)
}

// 标记为已处理
const markAsProcessed = (anomaly: MarketAnomaly) => {
  // 这里应该调用API标记异动为已处理
  anomaly.is_processed = true
  ElMessage.success('已标记为已处理')
}

// 分页大小改变
const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
}

// 当前页改变
const handleCurrentChange = (page: number) => {
  currentPage.value = page
}

// 启动自动刷新
const startAutoRefresh = () => {
  refreshTimer = setInterval(() => {
    loadAnomalies()
  }, 30000) // 30秒刷新一次
}

// 停止自动刷新
const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

// 组件挂载
onMounted(() => {
  loadAnomalies()
  startAutoRefresh()
})

// 组件卸载
onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style scoped>
.market-anomaly-monitor {
  background: var(--el-bg-color);
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #e4e7ed;
}

.toolbar h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.toolbar-right {
  display: flex;
  align-items: center;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  padding: 16px;
  background: var(--el-bg-color-page);
  border-bottom: 1px solid #e4e7ed;
}

.stat-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px;
  background: var(--el-bg-color);
  border-radius: 6px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.stat-card.critical {
  border-left: 4px solid #f56c6c;
}

.stat-card.high {
  border-left: 4px solid #e6a23c;
}

.stat-card.medium {
  border-left: 4px solid #409eff;
}

.stat-card.low {
  border-left: 4px solid #909399;
}

.stat-number {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 12px;
  color: #909399;
}

.anomaly-list {
  min-height: 400px;
}

.loading-state {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  padding: 40px;
  color: #909399;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

.anomaly-items {
  padding: 16px;
}

.anomaly-item {
  padding: 16px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  margin-bottom: 12px;
  transition: all 0.2s;
}

.anomaly-item:hover {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
}

.anomaly-item.processed {
  opacity: 0.7;
  background-color: var(--el-fill-color-light);
}

.anomaly-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.anomaly-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.title-text {
  font-weight: 600;
  color: #303133;
}

.anomaly-time {
  font-size: 12px;
  color: #909399;
}

.anomaly-content {
  margin-bottom: 12px;
}

.anomaly-symbol {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.symbol-code {
  font-weight: 600;
  color: #409eff;
  font-size: 16px;
}

.symbol-name {
  color: #606266;
  font-size: 14px;
}

.anomaly-description {
  color: #606266;
  line-height: 1.5;
}

.anomaly-data {
  display: flex;
  gap: 24px;
  margin-bottom: 12px;
  padding: 8px 0;
  border-top: 1px solid #f0f0f0;
}

.data-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.data-item .label {
  font-size: 12px;
  color: #909399;
}

.data-item .value {
  font-weight: 600;
  font-family: 'Courier New', monospace;
}

.data-item .value.price {
  color: #303133;
}

.data-item .value.volume {
  color: #409eff;
}

.price-up {
  color: #f56c6c;
}

.price-down {
  color: #67c23a;
}

.price-neutral {
  color: #909399;
}

.anomaly-actions {
  display: flex;
  gap: 8px;
  padding-top: 8px;
  border-top: 1px solid #f0f0f0;
}

.pagination {
  display: flex;
  justify-content: center;
  padding: 16px;
  border-top: 1px solid #e4e7ed;
}
</style>