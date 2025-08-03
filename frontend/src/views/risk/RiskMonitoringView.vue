<template>
  <div class="risk-monitoring">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">风险监控</h1>
        <p class="page-description">实时监控交易风险，及时预警和处理风险事件</p>
      </div>
      <div class="header-right">
        <el-button @click="exportReport">
          <el-icon><Download /></el-icon>
          导出报告
        </el-button>
        <el-button type="primary" @click="openSettings">
          <el-icon><Setting /></el-icon>
          监控设置
        </el-button>
      </div>
    </div>

    <!-- 标签页 -->
    <el-tabs v-model="activeTab" @tab-change="handleTabChange">
      <!-- 风险仪表板 -->
      <el-tab-pane label="风险仪表板" name="dashboard">
        <RiskDashboard />
      </el-tab-pane>

      <!-- 风险预警 -->
      <el-tab-pane label="风险预警" name="alerts">
        <RiskAlertsPanel 
          :alerts="alerts"
          :loading="alertsLoading"
          @refresh="loadAlerts"
        />
      </el-tab-pane>

      <!-- 风险事件 -->
      <el-tab-pane label="风险事件" name="events">
        <RiskEventsPanel 
          :events="events"
          :loading="eventsLoading"
          @refresh="loadEvents"
          @resolve="handleResolveEvent"
        />
      </el-tab-pane>

      <!-- 风险统计 -->
      <el-tab-pane label="风险统计" name="statistics">
        <RiskStatisticsPanel 
          :statistics="statistics"
          :loading="statisticsLoading"
          @refresh="loadStatistics"
        />
      </el-tab-pane>

      <!-- 风险控制配置 -->
      <el-tab-pane label="风险控制配置" name="control-config">
        <RiskControlConfig />
      </el-tab-pane>

      <!-- 控制历史 -->
      <el-tab-pane label="控制历史" name="control-history">
        <RiskControlHistory />
      </el-tab-pane>

      <!-- 系统测试 -->
      <el-tab-pane label="系统测试" name="control-test">
        <RiskControlTest />
      </el-tab-pane>
    </el-tabs>

    <!-- 监控设置对话框 -->
    <RiskMonitoringSettings 
      v-model="showSettings"
      @save="handleSettingsSave"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Download, Setting } from '@element-plus/icons-vue'
import { 
  getRiskAlerts, 
  getRiskEvents, 
  getRiskStatistics,
  resolveRiskEvent,
  type RiskAlert,
  type RiskEvent,
  type RiskStatistics
} from '@/api/riskMonitoring'
import RiskDashboard from '@/components/risk/RiskDashboard.vue'
import RiskAlertsPanel from '@/components/risk/RiskAlertsPanel.vue'
import RiskEventsPanel from '@/components/risk/RiskEventsPanel.vue'
import RiskStatisticsPanel from '@/components/risk/RiskStatisticsPanel.vue'
import RiskMonitoringSettings from '@/components/risk/RiskMonitoringSettings.vue'
import RiskControlConfig from '@/components/risk/RiskControlConfig.vue'
import RiskControlHistory from '@/components/risk/RiskControlHistory.vue'
import RiskControlTest from '@/components/risk/RiskControlTest.vue'

// 响应式数据
const activeTab = ref('dashboard')
const showSettings = ref(false)

// 预警数据
const alerts = ref<RiskAlert[]>([])
const alertsLoading = ref(false)

// 事件数据
const events = ref<RiskEvent[]>([])
const eventsLoading = ref(false)

// 统计数据
const statistics = ref<RiskStatistics | null>(null)
const statisticsLoading = ref(false)

// 加载预警数据
const loadAlerts = async () => {
  try {
    alertsLoading.value = true
    const response = await getRiskAlerts()
    alerts.value = response.data.alerts
  } catch (error) {
    console.error('加载风险预警失败:', error)
    ElMessage.error('加载风险预警失败')
  } finally {
    alertsLoading.value = false
  }
}

// 加载事件数据
const loadEvents = async () => {
  try {
    eventsLoading.value = true
    const response = await getRiskEvents({ days: 30 })
    events.value = response.data.events
  } catch (error) {
    console.error('加载风险事件失败:', error)
    ElMessage.error('加载风险事件失败')
  } finally {
    eventsLoading.value = false
  }
}

// 加载统计数据
const loadStatistics = async () => {
  try {
    statisticsLoading.value = true
    const response = await getRiskStatistics(30)
    statistics.value = response.data
  } catch (error) {
    console.error('加载风险统计失败:', error)
    ElMessage.error('加载风险统计失败')
  } finally {
    statisticsLoading.value = false
  }
}

// 标签页切换
const handleTabChange = (tabName: string) => {
  switch (tabName) {
    case 'alerts':
      if (alerts.value.length === 0) {
        loadAlerts()
      }
      break
    case 'events':
      if (events.value.length === 0) {
        loadEvents()
      }
      break
    case 'statistics':
      if (!statistics.value) {
        loadStatistics()
      }
      break
  }
}

// 解决风险事件
const handleResolveEvent = async (eventId: number, resolutionNote?: string) => {
  try {
    await resolveRiskEvent(eventId, resolutionNote)
    ElMessage.success('风险事件已解决')
    loadEvents()
  } catch (error) {
    console.error('解决风险事件失败:', error)
    ElMessage.error('解决风险事件失败')
  }
}

// 导出报告
const exportReport = () => {
  ElMessage.info('导出风险报告功能开发中')
}

// 打开设置
const openSettings = () => {
  showSettings.value = true
}

// 处理设置保存
const handleSettingsSave = (settings: any) => {
  ElMessage.success('监控设置已保存')
  showSettings.value = false
}

// 组件挂载
onMounted(() => {
  // 默认加载仪表板数据，其他标签页按需加载
})
</script>

<style scoped>
.risk-monitoring {
  padding: 20px;
  min-height: 100vh;
  background: #f5f7fa;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 20px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.header-left {
  flex: 1;
}

.page-title {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.page-description {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.header-right {
  display: flex;
  gap: 12px;
}

:deep(.el-tabs) {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

:deep(.el-tabs__header) {
  margin: 0;
  background: #f8f9fa;
  border-bottom: 1px solid #e4e7ed;
}

:deep(.el-tabs__nav-wrap) {
  padding: 0 20px;
}

:deep(.el-tabs__content) {
  padding: 0;
}

:deep(.el-tab-pane) {
  background: #f5f7fa;
  min-height: 600px;
}
</style>