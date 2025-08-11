<template>
  <div class="risk-dashboard">
    <!-- 仪表板头部 -->
    <div class="dashboard-header">
      <div class="header-left">
        <h2 class="dashboard-title">风险监控仪表板</h2>
        <div class="last-updated">
          最后更新: {{ formatTime(dashboardData?.last_updated) }}
        </div>
      </div>
      <div class="header-right">
        <el-button @click="refreshDashboard" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button type="primary" @click="startMonitoring">
          <el-icon><Monitor /></el-icon>
          启动监控
        </el-button>
      </div>
    </div>

    <!-- 风险预警卡片 -->
    <div v-if="dashboardData?.alerts.has_high_risk" class="alert-banner">
      <el-alert
        title="高风险预警"
        type="error"
        :description="`检测到 ${dashboardData.alerts.count} 个风险预警，其中包含高风险项目，请立即处理！`"
        show-icon
        :closable="false"
      />
    </div>

    <!-- 风险指标卡片 -->
    <div class="metrics-grid">
      <!-- 账户风险指标 -->
      <div class="metric-card">
        <div class="card-header">
          <h3>账户风险</h3>
          <el-icon class="card-icon"><Wallet /></el-icon>
        </div>
        <div class="card-content">
          <div class="metric-item">
            <span class="label">保证金比率</span>
            <span class="value" :class="getMarginRatioClass(accountMetrics?.margin_ratio)">
              {{ formatPercent(accountMetrics?.margin_ratio) }}
            </span>
          </div>
          <div class="metric-item">
            <span class="label">可用余额比率</span>
            <span class="value">{{ formatPercent(accountMetrics?.free_margin_ratio) }}</span>
          </div>
          <div class="metric-item">
            <span class="label">总权益</span>
            <span class="value">{{ formatAmount(accountMetrics?.total_equity) }}</span>
          </div>
        </div>
      </div>

      <!-- 持仓风险指标 -->
      <div class="metric-card">
        <div class="card-header">
          <h3>持仓风险</h3>
          <el-icon class="card-icon"><PieChart /></el-icon>
        </div>
        <div class="card-content">
          <div class="metric-item">
            <span class="label">杠杆比率</span>
            <span class="value" :class="getLeverageRatioClass(riskIndicators?.leverage_ratio)">
              {{ formatNumber(riskIndicators?.leverage_ratio) }}x
            </span>
          </div>
          <div class="metric-item">
            <span class="label">持仓集中度</span>
            <span class="value">{{ formatPercent(positionMetrics?.position_concentration?.top3_concentration) }}</span>
          </div>
          <div class="metric-item">
            <span class="label">未实现盈亏</span>
            <span class="value" :class="getPnlClass(positionMetrics?.total_unrealized_pnl)">
              {{ formatAmount(positionMetrics?.total_unrealized_pnl) }}
            </span>
          </div>
        </div>
      </div>

      <!-- 风险指标 -->
      <div class="metric-card">
        <div class="card-header">
          <h3>风险指标</h3>
          <el-icon class="card-icon"><TrendCharts /></el-icon>
        </div>
        <div class="card-content">
          <div class="metric-item">
            <span class="label">回撤比率</span>
            <span class="value" :class="getDrawdownClass(riskIndicators?.drawdown_ratio)">
              {{ formatPercent(riskIndicators?.drawdown_ratio) }}
            </span>
          </div>
          <div class="metric-item">
            <span class="label">1日VaR</span>
            <span class="value">{{ formatAmount(riskIndicators?.var_1d) }}</span>
          </div>
          <div class="metric-item">
            <span class="label">夏普比率</span>
            <span class="value">{{ formatNumber(riskIndicators?.sharpe_ratio) }}</span>
          </div>
        </div>
      </div>

      <!-- 风险等级 -->
      <div class="metric-card">
        <div class="card-header">
          <h3>风险等级</h3>
          <el-icon class="card-icon"><Warning /></el-icon>
        </div>
        <div class="card-content">
          <div class="risk-level-display">
            <el-tag :type="getRiskLevelType(statistics?.current_risk_level)" size="large">
              {{ getRiskLevelText(statistics?.current_risk_level) }}
            </el-tag>
            <div class="risk-trend">
              <span class="trend-label">趋势:</span>
              <el-icon :class="getTrendIconClass(statistics?.risk_trend)">
                <component :is="getTrendIcon(statistics?.risk_trend)" />
              </el-icon>
              <span>{{ getTrendText(statistics?.risk_trend) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 风险预警列表 -->
    <div class="alerts-section">
      <div class="section-header">
        <h3>风险预警</h3>
        <el-badge :value="dashboardData?.alerts.count || 0" :hidden="!dashboardData?.alerts.count">
          <el-button size="small" @click="showAllAlerts">查看全部</el-button>
        </el-badge>
      </div>
      
      <div v-if="!dashboardData?.alerts.items.length" class="empty-state">
        <el-empty description="暂无风险预警" />
      </div>
      
      <div v-else class="alerts-list">
        <div
          v-for="alert in dashboardData.alerts.items.slice(0, 5)"
          :key="`${alert.type}-${alert.timestamp}`"
          class="alert-item"
          :class="alert.severity.toLowerCase()"
        >
          <div class="alert-icon">
            <el-icon>
              <Warning v-if="alert.severity === 'HIGH'" />
              <InfoFilled v-else-if="alert.severity === 'MEDIUM'" />
              <CircleCheck v-else />
            </el-icon>
          </div>
          <div class="alert-content">
            <div class="alert-title">{{ alert.title }}</div>
            <div class="alert-message">{{ alert.message }}</div>
            <div class="alert-time">{{ formatTime(alert.timestamp) }}</div>
          </div>
          <div class="alert-value">
            <span class="current-value">{{ formatAlertValue(alert.value, alert.type) }}</span>
            <span class="threshold">/ {{ formatAlertValue(alert.threshold, alert.type) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 最近风险事件 -->
    <div class="events-section">
      <div class="section-header">
        <h3>最近风险事件</h3>
        <el-button size="small" @click="showAllEvents">查看全部</el-button>
      </div>
      
      <div v-if="!dashboardData?.recent_events.items.length" class="empty-state">
        <el-empty description="暂无风险事件" />
      </div>
      
      <div v-else class="events-list">
        <div
          v-for="event in dashboardData.recent_events.items"
          :key="event.id"
          class="event-item"
          :class="{ 'resolved': event.is_resolved }"
        >
          <div class="event-severity">
            <el-tag :type="getSeverityType(event.severity)" size="small">
              {{ getSeverityText(event.severity) }}
            </el-tag>
          </div>
          <div class="event-content">
            <div class="event-title">{{ event.title }}</div>
            <div class="event-description">{{ event.description }}</div>
            <div class="event-time">{{ formatTime(event.created_at) }}</div>
          </div>
          <div class="event-status">
            <el-tag v-if="event.is_resolved" type="success" size="small">已解决</el-tag>
            <el-tag v-else type="warning" size="small">待处理</el-tag>
          </div>
        </div>
      </div>
    </div>

    <!-- 风险建议 -->
    <div v-if="statistics?.recommendations?.length" class="recommendations-section">
      <div class="section-header">
        <h3>风险建议</h3>
      </div>
      <div class="recommendations-list">
        <div
          v-for="(recommendation, index) in statistics.recommendations"
          :key="index"
          class="recommendation-item"
        >
          <el-icon class="recommendation-icon"><Lightbulb /></el-icon>
          <span class="recommendation-text">{{ recommendation }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Refresh, Monitor, Wallet, PieChart, TrendCharts, Warning,
  InfoFilled, CircleCheck, ArrowUp, ArrowDown, Minus, Lightbulb
} from '@element-plus/icons-vue'
import { getRiskDashboard, startRiskMonitoring, type RiskDashboard } from '@/api/riskMonitoring'
import { formatTime, formatPercent, formatAmount, formatNumber } from '@/utils/format'

// 响应式数据
const loading = ref(false)
const dashboardData = ref<RiskDashboard | null>(null)

// 定时器
let refreshTimer: NodeJS.Timeout | null = null

// 计算属性
const accountMetrics = computed(() => dashboardData.value?.metrics.account_metrics)
const positionMetrics = computed(() => dashboardData.value?.metrics.position_metrics)
const riskIndicators = computed(() => dashboardData.value?.metrics.risk_indicators)
const statistics = computed(() => dashboardData.value?.statistics)

// 加载仪表板数据
const loadDashboard = async () => {
  try {
    loading.value = true
    const response = await getRiskDashboard()
    dashboardData.value = response.data
  } catch (error) {
    console.error('加载风险仪表板失败:', error)
    ElMessage.error('加载风险仪表板失败')
  } finally {
    loading.value = false
  }
}

// 刷新仪表板
const refreshDashboard = () => {
  loadDashboard()
}

// 启动监控
const startMonitoring = async () => {
  try {
    await startRiskMonitoring()
    ElMessage.success('风险监控已启动')
  } catch (error) {
    console.error('启动风险监控失败:', error)
    ElMessage.error('启动风险监控失败')
  }
}

// 显示所有预警
const showAllAlerts = () => {
  // 这里可以跳转到预警详情页面
  ElMessage.info('跳转到预警详情页面')
}

// 显示所有事件
const showAllEvents = () => {
  // 这里可以跳转到事件详情页面
  ElMessage.info('跳转到事件详情页面')
}

// 样式类名获取函数
const getMarginRatioClass = (ratio?: number) => {
  if (!ratio) return ''
  if (ratio > 90) return 'danger'
  if (ratio > 80) return 'warning'
  return 'normal'
}

const getLeverageRatioClass = (ratio?: number) => {
  if (!ratio) return ''
  if (ratio > 10) return 'danger'
  if (ratio > 5) return 'warning'
  return 'normal'
}

const getDrawdownClass = (ratio?: number) => {
  if (!ratio) return ''
  if (ratio > 30) return 'danger'
  if (ratio > 20) return 'warning'
  return 'normal'
}

const getPnlClass = (pnl?: number) => {
  if (!pnl) return ''
  return pnl >= 0 ? 'profit' : 'loss'
}

const getRiskLevelType = (level?: string) => {
  switch (level) {
    case 'HIGH': return 'danger'
    case 'MEDIUM': return 'warning'
    case 'LOW': return 'primary'
    case 'MINIMAL': return 'success'
    default: return 'info'
  }
}

const getRiskLevelText = (level?: string) => {
  switch (level) {
    case 'HIGH': return '高风险'
    case 'MEDIUM': return '中风险'
    case 'LOW': return '低风险'
    case 'MINIMAL': return '极低风险'
    default: return '未知'
  }
}

const getTrendIcon = (trend?: string) => {
  switch (trend) {
    case 'INCREASING': return ArrowUp
    case 'DECREASING': return ArrowDown
    case 'STABLE': return Minus
    default: return Minus
  }
}

const getTrendIconClass = (trend?: string) => {
  switch (trend) {
    case 'INCREASING': return 'trend-up'
    case 'DECREASING': return 'trend-down'
    case 'STABLE': return 'trend-stable'
    default: return 'trend-stable'
  }
}

const getTrendText = (trend?: string) => {
  switch (trend) {
    case 'INCREASING': return '上升'
    case 'DECREASING': return '下降'
    case 'STABLE': return '稳定'
    default: return '未知'
  }
}

const getSeverityType = (severity: string) => {
  switch (severity) {
    case 'HIGH': return 'danger'
    case 'MEDIUM': return 'warning'
    case 'LOW': return 'primary'
    default: return 'info'
  }
}

const getSeverityText = (severity: string) => {
  switch (severity) {
    case 'HIGH': return '高'
    case 'MEDIUM': return '中'
    case 'LOW': return '低'
    default: return '未知'
  }
}

const formatAlertValue = (value: number, type: string) => {
  switch (type) {
    case 'MARGIN_WARNING':
    case 'CONCENTRATION_WARNING':
    case 'DRAWDOWN_WARNING':
    case 'VAR_WARNING':
      return formatPercent(value)
    case 'LEVERAGE_WARNING':
      return `${formatNumber(value)}x`
    default:
      return formatNumber(value)
  }
}

// 启动自动刷新
const startAutoRefresh = () => {
  refreshTimer = setInterval(() => {
    loadDashboard()
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
  loadDashboard()
  startAutoRefresh()
})

// 组件卸载
onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style scoped>
.risk-dashboard {
  padding: 20px;
  background: var(--el-bg-color-page);
  min-height: 100vh;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 20px;
  background: var(--el-bg-color);
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.dashboard-title {
  margin: 0 0 4px 0;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.last-updated {
  font-size: 12px;
  color: #909399;
}

.header-right {
  display: flex;
  gap: 12px;
}

.alert-banner {
  margin-bottom: 20px;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.metric-card {
  background: var(--el-bg-color);
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: var(--el-bg-color-page);
  border-bottom: 1px solid #e4e7ed;
}

.card-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.card-icon {
  font-size: 20px;
  color: #409eff;
}

.card-content {
  padding: 20px;
}

.metric-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.metric-item:last-child {
  margin-bottom: 0;
}

.metric-item .label {
  font-size: 14px;
  color: #606266;
}

.metric-item .value {
  font-size: 16px;
  font-weight: 600;
  font-family: 'Courier New', monospace;
}

.metric-item .value.normal {
  color: #67c23a;
}

.metric-item .value.warning {
  color: #e6a23c;
}

.metric-item .value.danger {
  color: #f56c6c;
}

.metric-item .value.profit {
  color: #67c23a;
}

.metric-item .value.loss {
  color: #f56c6c;
}

.risk-level-display {
  text-align: center;
}

.risk-trend {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 4px;
  margin-top: 12px;
  font-size: 14px;
  color: #606266;
}

.trend-up {
  color: #f56c6c;
}

.trend-down {
  color: #67c23a;
}

.trend-stable {
  color: #909399;
}

.alerts-section,
.events-section,
.recommendations-section {
  background: var(--el-bg-color);
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
  overflow: hidden;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: var(--el-bg-color-page);
  border-bottom: 1px solid #e4e7ed;
}

.section-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.empty-state {
  padding: 40px;
  text-align: center;
}

.alerts-list,
.events-list {
  padding: 20px;
}

.alert-item,
.event-item {
  display: flex;
  align-items: center;
  padding: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  margin-bottom: 12px;
  transition: all 0.2s;
}

.alert-item:hover,
.event-item:hover {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
}

.alert-item:last-child,
.event-item:last-child {
  margin-bottom: 0;
}

.alert-item.high {
  border-left: 4px solid #f56c6c;
}

.alert-item.medium {
  border-left: 4px solid #e6a23c;
}

.alert-item.low {
  border-left: 4px solid #409eff;
}

.event-item.resolved {
  opacity: 0.7;
  background-color: var(--el-fill-color-light);
}

.alert-icon,
.event-severity {
  margin-right: 12px;
}

.alert-content,
.event-content {
  flex: 1;
}

.alert-title,
.event-title {
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.alert-message,
.event-description {
  font-size: 14px;
  color: #606266;
  margin-bottom: 4px;
}

.alert-time,
.event-time {
  font-size: 12px;
  color: #909399;
}

.alert-value {
  text-align: right;
  font-family: 'Courier New', monospace;
}

.current-value {
  font-weight: 600;
  color: #303133;
}

.threshold {
  color: #909399;
}

.event-status {
  margin-left: 12px;
}

.recommendations-list {
  padding: 20px;
}

.recommendation-item {
  display: flex;
  align-items: center;
  padding: 12px;
  background: var(--el-color-primary-light-9);
  border-radius: 6px;
  margin-bottom: 12px;
}

.recommendation-item:last-child {
  margin-bottom: 0;
}

.recommendation-icon {
  color: #409eff;
  margin-right: 12px;
}

.recommendation-text {
  color: #303133;
  line-height: 1.5;
}
</style>