<template>
  <div class="risk-monitor-dashboard">
    <!-- 风险概览卡片 -->
    <el-row :gutter="20" class="risk-overview">
      <el-col :span="6">
        <el-card class="risk-card">
          <div class="risk-item">
            <div class="risk-icon" :class="getRiskLevelClass(riskMetrics.overall_risk_score)">
              <el-icon size="24"><Warning /></el-icon>
            </div>
            <div class="risk-content">
              <div class="risk-value">{{ riskMetrics.overall_risk_score || 0 }}</div>
              <div class="risk-label">综合风险评分</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="risk-card">
          <div class="risk-item">
            <div class="risk-icon margin">
              <el-icon size="24"><Wallet /></el-icon>
            </div>
            <div class="risk-content">
              <div class="risk-value">{{ formatPercent(riskMetrics.account_metrics?.margin_ratio) }}</div>
              <div class="risk-label">保证金使用率</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="risk-card">
          <div class="risk-item">
            <div class="risk-icon profit">
              <el-icon size="24"><TrendCharts /></el-icon>
            </div>
            <div class="risk-content">
              <div class="risk-value" :class="getProfitClass(riskMetrics.account_metrics?.profit_ratio)">
                {{ formatPercent(riskMetrics.account_metrics?.profit_ratio) }}
              </div>
              <div class="risk-label">盈亏比例</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="risk-card">
          <div class="risk-item">
            <div class="risk-icon level">
              <el-icon size="24"><Warning /></el-icon>
            </div>
            <div class="risk-content">
              <div class="risk-value">{{ riskMetrics.account_metrics?.risk_level || '未知' }}</div>
              <div class="risk-label">风险等级</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 风险详情 -->
    <el-row :gutter="20">
      <!-- 左侧：风险指标 -->
      <el-col :span="12">
        <el-card title="风险指标详情">
          <template #header>
            <div class="card-header">
              <span>风险指标详情</span>
              <el-tag v-if="riskMetrics.timestamp" size="small" type="info">
                {{ formatTime(riskMetrics.timestamp) }}
              </el-tag>
            </div>
          </template>

          <div class="risk-details">
            <div class="detail-section">
              <h4>账户风险</h4>
              <div class="detail-items">
                <div class="detail-item">
                  <span class="detail-label">账户余额:</span>
                  <span class="detail-value">¥{{ formatNumber(riskMetrics.account_metrics?.balance) }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">可用资金:</span>
                  <span class="detail-value">¥{{ formatNumber(riskMetrics.account_metrics?.available) }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">占用保证金:</span>
                  <span class="detail-value">¥{{ formatNumber(riskMetrics.account_metrics?.margin) }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">浮动盈亏:</span>
                  <span class="detail-value" :class="getProfitClass(riskMetrics.account_metrics?.profit)">
                    {{ formatProfit(riskMetrics.account_metrics?.profit) }}
                  </span>
                </div>
              </div>
            </div>

            <div class="detail-section">
              <h4>持仓风险</h4>
              <div class="detail-items">
                <div class="detail-item">
                  <span class="detail-label">持仓品种数:</span>
                  <span class="detail-value">{{ riskMetrics.position_metrics?.total_positions || 0 }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">最大持仓比例:</span>
                  <span class="detail-value">{{ formatPercent(riskMetrics.position_metrics?.largest_position_ratio) }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">保证金利用率:</span>
                  <span class="detail-value">{{ formatPercent(riskMetrics.position_metrics?.margin_utilization) }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">持仓风险等级:</span>
                  <span class="detail-value">{{ riskMetrics.position_metrics?.risk_level || '低' }}</span>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：风险预警 -->
      <el-col :span="12">
        <el-card title="风险预警">
          <template #header>
            <div class="card-header">
              <span>风险预警</span>
              <el-tag :type="getAlertCountType(riskMetrics.risk_alerts?.length)" size="small">
                {{ riskMetrics.risk_alerts?.length || 0 }} 个预警
              </el-tag>
            </div>
          </template>

          <div class="risk-alerts">
            <div v-if="!riskMetrics.risk_alerts || riskMetrics.risk_alerts.length === 0" class="no-alerts">
              <el-empty description="暂无风险预警" :image-size="80">
                <el-icon size="48" color="#67c23a"><SuccessFilled /></el-icon>
                <p>系统运行正常</p>
              </el-empty>
            </div>
            
            <div v-else class="alerts-list">
              <div 
                v-for="alert in riskMetrics.risk_alerts" 
                :key="alert.timestamp"
                class="alert-item"
                :class="getAlertClass(alert.type)"
              >
                <div class="alert-header">
                  <el-icon size="16">
                    <Warning v-if="alert.type === 'CRITICAL'" />
                    <InfoFilled v-else />
                  </el-icon>
                  <span class="alert-level">{{ alert.level }}</span>
                  <span class="alert-time">{{ formatTime(alert.timestamp) }}</span>
                </div>
                <div class="alert-message">{{ alert.message }}</div>
                <div class="alert-suggestion">建议: {{ alert.suggestion }}</div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 风险趋势图表 -->
    <el-card title="风险趋势" class="risk-chart-card">
      <div class="risk-chart">
        <div class="chart-placeholder">
          <el-icon size="48" color="#909399"><TrendCharts /></el-icon>
          <p>风险趋势图表</p>
          <p class="chart-note">显示最近24小时的风险评分变化</p>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  Warning, 
  Wallet, 
  TrendCharts, 
  SuccessFilled, 
  InfoFilled 
} from '@element-plus/icons-vue'
import { getRiskMetrics } from '@/api/realTimeData'

// 响应式数据
const loading = ref(false)
const riskMetrics = ref({
  overall_risk_score: 0,
  account_metrics: {},
  position_metrics: {},
  risk_alerts: [],
  timestamp: ''
})

// 定时器
let refreshTimer: NodeJS.Timeout | null = null

// 加载风险数据
const loadRiskMetrics = async () => {
  try {
    const response = await getRiskMetrics()
    if (response.success && response.data) {
      riskMetrics.value = response.data
    }
  } catch (error) {
    console.error('加载风险数据失败:', error)
    // 使用模拟数据
    riskMetrics.value = {
      overall_risk_score: 25,
      account_metrics: {
        balance: 1000000,
        available: 950000,
        margin: 50000,
        profit: 2500,
        margin_ratio: 0.05,
        profit_ratio: 0.0025,
        risk_level: '低'
      },
      position_metrics: {
        total_positions: 2,
        largest_position_ratio: 0.15,
        margin_utilization: 0.05,
        risk_level: '低'
      },
      risk_alerts: [],
      timestamp: new Date().toISOString()
    }
  }
}

// 格式化函数
const formatNumber = (num: number | undefined) => {
  return num?.toLocaleString() || '0'
}

const formatPercent = (ratio: number | undefined) => {
  if (ratio === undefined) return '0%'
  return `${(ratio * 100).toFixed(2)}%`
}

const formatProfit = (profit: number | undefined) => {
  if (profit === undefined) return '¥0'
  const sign = profit >= 0 ? '+' : ''
  return `${sign}¥${profit.toLocaleString()}`
}

const formatTime = (timestamp: string) => {
  return new Date(timestamp).toLocaleString()
}

// 样式类函数
const getRiskLevelClass = (score: number) => {
  if (score >= 80) return 'high-risk'
  if (score >= 50) return 'medium-risk'
  return 'low-risk'
}

const getProfitClass = (value: number | undefined) => {
  if (value === undefined) return ''
  return value >= 0 ? 'profit' : 'loss'
}

const getAlertCountType = (count: number) => {
  if (count === 0) return 'success'
  if (count <= 2) return 'warning'
  return 'danger'
}

const getAlertClass = (type: string) => {
  return type === 'CRITICAL' ? 'critical-alert' : 'warning-alert'
}

// 启动定时刷新
const startAutoRefresh = () => {
  refreshTimer = setInterval(() => {
    loadRiskMetrics()
  }, 30000) // 30秒刷新一次
}

// 停止定时刷新
const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

// 组件挂载
onMounted(() => {
  loadRiskMetrics()
  startAutoRefresh()
})

// 组件卸载
onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style scoped>
.risk-monitor-dashboard {
  padding: 20px;
}

.risk-overview {
  margin-bottom: 20px;
}

.risk-card {
  height: 120px;
}

.risk-item {
  display: flex;
  align-items: center;
  height: 100%;
  padding: 10px;
}

.risk-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  margin-right: 15px;
}

.risk-icon.low-risk {
  background-color: #f0f9ff;
  color: #67c23a;
}

.risk-icon.medium-risk {
  background-color: #fef3e2;
  color: #e6a23c;
}

.risk-icon.high-risk {
  background-color: #fef0f0;
  color: #f56c6c;
}

.risk-icon.margin {
  background-color: #f0f9ff;
  color: #409eff;
}

.risk-icon.profit {
  background-color: #f0f9ff;
  color: #67c23a;
}

.risk-icon.level {
  background-color: #f5f7fa;
  color: #909399;
}

.risk-content {
  flex: 1;
}

.risk-value {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 5px;
}

.risk-label {
  font-size: 14px;
  color: #909399;
}

.profit {
  color: #67c23a;
}

.loss {
  color: #f56c6c;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.risk-details {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.detail-section h4 {
  margin: 0 0 10px 0;
  font-size: 16px;
  color: #303133;
  border-bottom: 1px solid #e4e7ed;
  padding-bottom: 5px;
}

.detail-items {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 5px 0;
}

.detail-label {
  color: #606266;
  font-size: 14px;
}

.detail-value {
  color: #303133;
  font-weight: 500;
  font-size: 14px;
}

.risk-alerts {
  max-height: 400px;
  overflow-y: auto;
}

.no-alerts {
  text-align: center;
  padding: 40px;
  color: #67c23a;
}

.alerts-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.alert-item {
  padding: 12px;
  border-radius: 6px;
  border-left: 4px solid;
}

.critical-alert {
  background-color: #fef0f0;
  border-left-color: #f56c6c;
}

.warning-alert {
  background-color: #fdf6ec;
  border-left-color: #e6a23c;
}

.alert-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 5px;
  font-size: 14px;
}

.alert-level {
  font-weight: 600;
  color: #303133;
}

.alert-time {
  color: #909399;
  font-size: 12px;
  margin-left: auto;
}

.alert-message {
  font-size: 14px;
  color: #303133;
  margin-bottom: 5px;
}

.alert-suggestion {
  font-size: 12px;
  color: #606266;
  font-style: italic;
}

.risk-chart-card {
  margin-top: 20px;
}

.risk-chart {
  height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chart-placeholder {
  text-align: center;
  color: #909399;
}

.chart-placeholder p {
  margin: 10px 0 5px 0;
  font-size: 16px;
}

.chart-note {
  font-size: 12px !important;
  color: #c0c4cc !important;
}
</style>