<template>
  <div class="risk-control-view">
    <div class="page-header">
      <h1>风险控制</h1>
      <div class="header-actions">
        <el-button @click="refreshData" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新数据
        </el-button>
        <el-button type="primary" @click="showRiskSettingsDialog = true">
          <el-icon><Setting /></el-icon>
          风险设置
        </el-button>
      </div>
    </div>

    <!-- 风险监控仪表板 -->
    <RiskMonitorDashboard />

    <!-- 风险设置对话框 -->
    <el-dialog v-model="showRiskSettingsDialog" title="风险设置" width="600px">
      <el-tabs v-model="activeSettingsTab">
        <el-tab-pane label="基础设置" name="basic">
          <el-form :model="riskSettings" label-width="120px">
            <el-form-item label="风险等级">
              <el-radio-group v-model="riskSettings.risk_level">
                <el-radio label="conservative">保守</el-radio>
                <el-radio label="moderate">稳健</el-radio>
                <el-radio label="aggressive">激进</el-radio>
              </el-radio-group>
            </el-form-item>
            
            <el-form-item label="自动止损">
              <el-switch v-model="riskSettings.auto_stop_loss" />
            </el-form-item>
            
            <el-form-item label="自动止盈">
              <el-switch v-model="riskSettings.auto_take_profit" />
            </el-form-item>
            
            <el-form-item label="风险预警">
              <el-switch v-model="riskSettings.risk_alert_enabled" />
            </el-form-item>
          </el-form>
        </el-tab-pane>
        
        <el-tab-pane label="限制设置" name="limits">
          <el-form :model="riskSettings" label-width="120px">
            <el-form-item label="单笔最大金额">
              <el-input-number
                v-model="riskSettings.max_order_amount"
                :min="0"
                :step="1000"
                style="width: 100%"
              />
            </el-form-item>
            
            <el-form-item label="日内最大交易次数">
              <el-input-number
                v-model="riskSettings.max_daily_trades"
                :min="1"
                :max="1000"
                style="width: 100%"
              />
            </el-form-item>
            
            <el-form-item label="最大持仓品种数">
              <el-input-number
                v-model="riskSettings.max_positions"
                :min="1"
                :max="50"
                style="width: 100%"
              />
            </el-form-item>
            
            <el-form-item label="强制平仓时间">
              <el-time-picker
                v-model="riskSettings.force_close_time"
                format="HH:mm"
                placeholder="选择时间"
                style="width: 100%"
              />
            </el-form-item>
          </el-form>
        </el-tab-pane>
        
        <el-tab-pane label="通知设置" name="notifications">
          <el-form :model="riskSettings" label-width="120px">
            <el-form-item label="邮件通知">
              <el-switch v-model="riskSettings.email_notifications" />
            </el-form-item>
            
            <el-form-item label="短信通知">
              <el-switch v-model="riskSettings.sms_notifications" />
            </el-form-item>
            
            <el-form-item label="微信通知">
              <el-switch v-model="riskSettings.wechat_notifications" />
            </el-form-item>
            
            <el-form-item label="通知级别">
              <el-checkbox-group v-model="riskSettings.notification_levels">
                <el-checkbox label="critical">严重</el-checkbox>
                <el-checkbox label="high">高</el-checkbox>
                <el-checkbox label="medium">中等</el-checkbox>
                <el-checkbox label="low">低</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
      
      <template #footer>
        <el-button @click="showRiskSettingsDialog = false">取消</el-button>
        <el-button type="primary" @click="saveRiskSettings" :loading="loading">
          保存设置
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Setting } from '@element-plus/icons-vue'
import { getRiskMetrics } from '@/api/realTimeData'
import RiskMonitorDashboard from '@/components/RiskMonitorDashboard.vue'

// 响应式数据
const loading = ref(false)
const showRiskSettingsDialog = ref(false)
const activeSettingsTab = ref('basic')

// 风险设置
const riskSettings = ref({
  risk_level: 'moderate',
  auto_stop_loss: true,
  auto_take_profit: false,
  risk_alert_enabled: true,
  max_order_amount: 100000,
  max_daily_trades: 50,
  max_positions: 10,
  force_close_time: null,
  email_notifications: true,
  sms_notifications: false,
  wechat_notifications: true,
  notification_levels: ['critical', 'high']
})

// 方法
const refreshData = async () => {
  try {
    loading.value = true
    // 刷新风险数据
    await new Promise(resolve => setTimeout(resolve, 1000))
    ElMessage.success('数据刷新成功')
  } catch (error) {
    ElMessage.error('数据刷新失败')
  } finally {
    loading.value = false
  }
}

const saveRiskSettings = async () => {
  try {
    loading.value = true
    
    // 保存风险设置
    // await riskApi.updateRiskSettings(riskSettings.value)
    
    ElMessage.success('风险设置保存成功')
    showRiskSettingsDialog.value = false
  } catch (error) {
    ElMessage.error('保存风险设置失败')
  } finally {
    loading.value = false
  }
}

const loadRiskSettings = async () => {
  try {
    // 加载风险设置
    // const response = await riskApi.getRiskSettings()
    // riskSettings.value = response.data
  } catch (error) {
    ElMessage.error('加载风险设置失败')
  }
}

// 生命周期
onMounted(() => {
  loadRiskSettings()
})
</script>

<style scoped lang="scss">
.risk-control-view {
  padding: 24px;
  
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
    
    h1 {
      margin: 0;
      font-size: 24px;
      font-weight: 600;
      color: #303133;
    }
    
    .header-actions {
      display: flex;
      gap: 12px;
    }
  }
}
</style>