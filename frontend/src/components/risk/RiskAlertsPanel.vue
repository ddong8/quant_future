<template>
  <div class="risk-alerts-panel">
    <div class="panel-content">
      <div v-if="loading" class="loading-state">
        <el-icon class="is-loading"><Loading /></el-icon>
        加载中...
      </div>
      
      <div v-else-if="!alerts.length" class="empty-state">
        <el-empty description="暂无风险预警">
          <el-button type="primary" @click="$emit('refresh')">
            刷新检查
          </el-button>
        </el-empty>
      </div>
      
      <div v-else class="alerts-content">
        <!-- 预警统计 -->
        <div class="alerts-summary">
          <div class="summary-item high">
            <div class="count">{{ getAlertCount('HIGH') }}</div>
            <div class="label">高风险</div>
          </div>
          <div class="summary-item medium">
            <div class="count">{{ getAlertCount('MEDIUM') }}</div>
            <div class="label">中风险</div>
          </div>
          <div class="summary-item low">
            <div class="count">{{ getAlertCount('LOW') }}</div>
            <div class="label">低风险</div>
          </div>
        </div>

        <!-- 预警列表 -->
        <div class="alerts-list">
          <div
            v-for="(alert, index) in alerts"
            :key="`${alert.type}-${index}`"
            class="alert-card"
            :class="alert.severity.toLowerCase()"
          >
            <div class="alert-header">
              <div class="alert-severity">
                <el-tag :type="getSeverityType(alert.severity)" size="small">
                  {{ getSeverityText(alert.severity) }}
                </el-tag>
              </div>
              <div class="alert-type">{{ getAlertTypeText(alert.type) }}</div>
              <div class="alert-time">{{ formatTime(alert.timestamp) }}</div>
            </div>
            
            <div class="alert-body">
              <div class="alert-title">{{ alert.title }}</div>
              <div class="alert-message">{{ alert.message }}</div>
            </div>
            
            <div class="alert-metrics">
              <div class="metric-item">
                <span class="label">当前值:</span>
                <span class="value current">{{ formatAlertValue(alert.value, alert.type) }}</span>
              </div>
              <div class="metric-item">
                <span class="label">阈值:</span>
                <span class="value threshold">{{ formatAlertValue(alert.threshold, alert.type) }}</span>
              </div>
              <div class="metric-item">
                <span class="label">超出:</span>
                <span class="value exceed" :class="getExceedClass(alert.value, alert.threshold)">
                  {{ formatExceedValue(alert.value, alert.threshold, alert.type) }}
                </span>
              </div>
            </div>
            
            <div class="alert-actions">
              <el-button size="small" @click="viewDetails(alert)">
                查看详情
              </el-button>
              <el-button size="small" type="primary" @click="handleAlert(alert)">
                处理预警
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import type { RiskAlert } from '@/api/riskMonitoring'
import { formatTime, formatPercent, formatNumber, formatAmount } from '@/utils/format'

interface Props {
  alerts: RiskAlert[]
  loading: boolean
}

interface Emits {
  (e: 'refresh'): void
}

defineProps<Props>()
defineEmits<Emits>()

// 获取预警数量统计
const getAlertCount = (severity: string) => {
  return props.alerts.filter(alert => alert.severity === severity).length
}

// 获取严重程度类型
const getSeverityType = (severity: string) => {
  switch (severity) {
    case 'HIGH': return 'danger'
    case 'MEDIUM': return 'warning'
    case 'LOW': return 'primary'
    default: return 'info'
  }
}

// 获取严重程度文本
const getSeverityText = (severity: string) => {
  switch (severity) {
    case 'HIGH': return '高'
    case 'MEDIUM': return '中'
    case 'LOW': return '低'
    default: return '未知'
  }
}

// 获取预警类型文本
const getAlertTypeText = (type: string) => {
  switch (type) {
    case 'MARGIN_WARNING': return '保证金预警'
    case 'LEVERAGE_WARNING': return '杠杆预警'
    case 'CONCENTRATION_WARNING': return '集中度预警'
    case 'DRAWDOWN_WARNING': return '回撤预警'
    case 'VAR_WARNING': return 'VaR预警'
    default: return type
  }
}

// 格式化预警值
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

// 格式化超出值
const formatExceedValue = (current: number, threshold: number, type: string) => {
  const exceed = current - threshold
  const exceedPercent = (exceed / threshold) * 100
  
  switch (type) {
    case 'MARGIN_WARNING':
    case 'CONCENTRATION_WARNING':
    case 'DRAWDOWN_WARNING':
    case 'VAR_WARNING':
      return `${formatPercent(exceed)} (${exceedPercent.toFixed(1)}%)`
    case 'LEVERAGE_WARNING':
      return `${formatNumber(exceed)}x (${exceedPercent.toFixed(1)}%)`
    default:
      return `${formatNumber(exceed)} (${exceedPercent.toFixed(1)}%)`
  }
}

// 获取超出值样式类
const getExceedClass = (current: number, threshold: number) => {
  const exceedPercent = ((current - threshold) / threshold) * 100
  if (exceedPercent > 50) return 'severe'
  if (exceedPercent > 20) return 'moderate'
  return 'mild'
}

// 查看详情
const viewDetails = (alert: RiskAlert) => {
  ElMessage.info(`查看 ${alert.title} 详情`)
}

// 处理预警
const handleAlert = (alert: RiskAlert) => {
  ElMessage.info(`处理 ${alert.title} 预警`)
}
</script>

<style scoped>
.risk-alerts-panel {
  padding: 20px;
  background: var(--el-bg-color-page);
}

.loading-state {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  padding: 60px;
  color: #909399;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.alerts-summary {
  display: flex;
  gap: 20px;
  margin-bottom: 30px;
}

.summary-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
  background: var(--el-bg-color);
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.summary-item.high {
  border-left: 4px solid #f56c6c;
}

.summary-item.medium {
  border-left: 4px solid #e6a23c;
}

.summary-item.low {
  border-left: 4px solid #409eff;
}

.summary-item .count {
  font-size: 32px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.summary-item .label {
  font-size: 14px;
  color: #606266;
}

.alerts-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.alert-card {
  background: var(--el-bg-color);
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  transition: all 0.2s;
}

.alert-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.alert-card.high {
  border-left: 4px solid #f56c6c;
}

.alert-card.medium {
  border-left: 4px solid #e6a23c;
}

.alert-card.low {
  border-left: 4px solid #409eff;
}

.alert-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: var(--el-bg-color-page);
  border-bottom: 1px solid #e4e7ed;
}

.alert-type {
  font-weight: 600;
  color: #303133;
}

.alert-time {
  font-size: 12px;
  color: #909399;
}

.alert-body {
  padding: 16px 20px;
}

.alert-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.alert-message {
  color: #606266;
  line-height: 1.5;
}

.alert-metrics {
  display: flex;
  gap: 24px;
  padding: 16px 20px;
  background: #fafafa;
  border-top: 1px solid #f0f0f0;
}

.metric-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.metric-item .label {
  font-size: 12px;
  color: #909399;
}

.metric-item .value {
  font-size: 14px;
  font-weight: 600;
  font-family: 'Courier New', monospace;
}

.metric-item .value.current {
  color: #f56c6c;
}

.metric-item .value.threshold {
  color: #909399;
}

.metric-item .value.exceed.mild {
  color: #e6a23c;
}

.metric-item .value.exceed.moderate {
  color: #f56c6c;
}

.metric-item .value.exceed.severe {
  color: #c45656;
}

.alert-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 16px 20px;
  border-top: 1px solid #f0f0f0;
}
</style>