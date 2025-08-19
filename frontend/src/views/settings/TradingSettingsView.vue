<template>
  <div class="trading-settings-view">
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">
          <el-icon><TrendCharts /></el-icon>
          交易设置
        </h1>
        <p class="page-description">配置您的交易偏好和风险控制参数</p>
      </div>
      <div class="header-actions">
        <el-button @click="resetToDefault" :icon="RefreshLeft">
          恢复默认
        </el-button>
        <el-button type="primary" @click="saveAllSettings" :loading="saving" :icon="Check">
          保存所有设置
        </el-button>
      </div>
    </div>

    <div class="settings-content">
      <el-row :gutter="24">
        <el-col :lg="12" :md="24">
          <!-- 基础交易设置 -->
          <el-card class="settings-card" shadow="hover">
            <template #header>
              <span class="card-title">
                <el-icon><Setting /></el-icon>
                基础交易设置
              </span>
            </template>
            
            <el-form :model="basicSettings" label-width="140px">
              <el-form-item label="默认交易模式">
                <el-radio-group v-model="basicSettings.defaultTradingMode">
                  <el-radio label="manual">手动交易</el-radio>
                  <el-radio label="semi-auto">半自动交易</el-radio>
                  <el-radio label="auto">全自动交易</el-radio>
                </el-radio-group>
              </el-form-item>

              <el-form-item label="默认订单类型">
                <el-select v-model="basicSettings.defaultOrderType" style="width: 100%">
                  <el-option label="市价单" value="market" />
                  <el-option label="限价单" value="limit" />
                  <el-option label="止损单" value="stop" />
                  <el-option label="止盈单" value="take-profit" />
                </el-select>
              </el-form-item>

              <el-form-item label="默认交易数量">
                <el-input-number 
                  v-model="basicSettings.defaultQuantity" 
                  :min="1" 
                  :max="10000"
                  style="width: 100%"
                />
              </el-form-item>

              <el-form-item label="价格精度">
                <el-select v-model="basicSettings.priceDecimalPlaces" style="width: 100%">
                  <el-option label="1位小数" :value="1" />
                  <el-option label="2位小数" :value="2" />
                  <el-option label="3位小数" :value="3" />
                  <el-option label="4位小数" :value="4" />
                </el-select>
              </el-form-item>

              <el-form-item label="自动刷新间隔">
                <el-select v-model="basicSettings.refreshInterval" style="width: 100%">
                  <el-option label="1秒" :value="1000" />
                  <el-option label="3秒" :value="3000" />
                  <el-option label="5秒" :value="5000" />
                  <el-option label="10秒" :value="10000" />
                </el-select>
              </el-form-item>

              <el-form-item label="交易确认">
                <el-switch 
                  v-model="basicSettings.requireConfirmation"
                  active-text="需要确认"
                  inactive-text="直接执行"
                />
              </el-form-item>
            </el-form>
          </el-card>

          <!-- 风险控制设置 -->
          <el-card class="settings-card" shadow="hover">
            <template #header>
              <span class="card-title">
                <el-icon><Warning /></el-icon>
                风险控制设置
              </span>
            </template>
            
            <el-form :model="riskSettings" label-width="140px">
              <el-form-item label="启用风险控制">
                <el-switch 
                  v-model="riskSettings.enabled"
                  active-text="启用"
                  inactive-text="禁用"
                />
              </el-form-item>

              <el-form-item label="单笔最大金额" v-if="riskSettings.enabled">
                <el-input-number 
                  v-model="riskSettings.maxSingleOrderAmount" 
                  :min="0" 
                  :max="1000000"
                  :precision="2"
                  style="width: 100%"
                >
                  <template #append>元</template>
                </el-input-number>
              </el-form-item>

              <el-form-item label="日最大交易额" v-if="riskSettings.enabled">
                <el-input-number 
                  v-model="riskSettings.maxDailyTradingAmount" 
                  :min="0" 
                  :max="10000000"
                  :precision="2"
                  style="width: 100%"
                >
                  <template #append>元</template>
                </el-input-number>
              </el-form-item>

              <el-form-item label="最大持仓比例" v-if="riskSettings.enabled">
                <el-slider 
                  v-model="riskSettings.maxPositionRatio" 
                  :min="0" 
                  :max="100"
                  :step="5"
                  show-stops
                  show-input
                  input-size="small"
                >
                  <template #default="{ value }">{{ value }}%</template>
                </el-slider>
              </el-form-item>

              <el-form-item label="止损比例" v-if="riskSettings.enabled">
                <el-slider 
                  v-model="riskSettings.stopLossRatio" 
                  :min="1" 
                  :max="20"
                  :step="0.5"
                  show-stops
                  show-input
                  input-size="small"
                >
                  <template #default="{ value }">{{ value }}%</template>
                </el-slider>
              </el-form-item>

              <el-form-item label="止盈比例" v-if="riskSettings.enabled">
                <el-slider 
                  v-model="riskSettings.takeProfitRatio" 
                  :min="1" 
                  :max="50"
                  :step="1"
                  show-stops
                  show-input
                  input-size="small"
                >
                  <template #default="{ value }">{{ value }}%</template>
                </el-slider>
              </el-form-item>

              <el-form-item label="风险等级评估" v-if="riskSettings.enabled">
                <el-radio-group v-model="riskSettings.riskLevel">
                  <el-radio label="conservative">保守型</el-radio>
                  <el-radio label="moderate">稳健型</el-radio>
                  <el-radio label="aggressive">激进型</el-radio>
                </el-radio-group>
              </el-form-item>
            </el-form>
          </el-card>
        </el-col>

        <el-col :lg="12" :md="24">
          <!-- 通知设置 -->
          <el-card class="settings-card" shadow="hover">
            <template #header>
              <span class="card-title">
                <el-icon><Bell /></el-icon>
                通知设置
              </span>
            </template>
            
            <div class="notification-settings">
              <div class="notification-item">
                <div class="notification-info">
                  <h4>订单执行通知</h4>
                  <p>订单成交时发送通知</p>
                </div>
                <el-switch v-model="notificationSettings.orderExecution" />
              </div>
              
              <div class="notification-item">
                <div class="notification-info">
                  <h4>价格预警通知</h4>
                  <p>价格达到预设条件时通知</p>
                </div>
                <el-switch v-model="notificationSettings.priceAlert" />
              </div>
              
              <div class="notification-item">
                <div class="notification-info">
                  <h4>风险预警通知</h4>
                  <p>触发风险控制时通知</p>
                </div>
                <el-switch v-model="notificationSettings.riskAlert" />
              </div>
              
              <div class="notification-item">
                <div class="notification-info">
                  <h4>系统维护通知</h4>
                  <p>系统维护和更新通知</p>
                </div>
                <el-switch v-model="notificationSettings.systemMaintenance" />
              </div>

              <div class="notification-methods" v-if="hasAnyNotificationEnabled">
                <h4>通知方式</h4>
                <el-checkbox-group v-model="notificationSettings.methods">
                  <el-checkbox label="browser">浏览器通知</el-checkbox>
                  <el-checkbox label="email">邮件通知</el-checkbox>
                  <el-checkbox label="sms">短信通知</el-checkbox>
                  <el-checkbox label="wechat">微信通知</el-checkbox>
                </el-checkbox-group>
              </div>
            </div>
          </el-card>

          <!-- 界面设置 -->
          <el-card class="settings-card" shadow="hover">
            <template #header>
              <span class="card-title">
                <el-icon><Monitor /></el-icon>
                界面设置
              </span>
            </template>
            
            <el-form :model="uiSettings" label-width="120px">
              <el-form-item label="主题模式">
                <el-radio-group v-model="uiSettings.theme">
                  <el-radio label="light">浅色主题</el-radio>
                  <el-radio label="dark">深色主题</el-radio>
                  <el-radio label="auto">跟随系统</el-radio>
                </el-radio-group>
              </el-form-item>

              <el-form-item label="图表类型">
                <el-select v-model="uiSettings.defaultChartType" style="width: 100%">
                  <el-option label="K线图" value="candlestick" />
                  <el-option label="折线图" value="line" />
                  <el-option label="面积图" value="area" />
                  <el-option label="柱状图" value="bar" />
                </el-select>
              </el-form-item>

              <el-form-item label="时间周期">
                <el-select v-model="uiSettings.defaultTimeframe" style="width: 100%">
                  <el-option label="1分钟" value="1m" />
                  <el-option label="5分钟" value="5m" />
                  <el-option label="15分钟" value="15m" />
                  <el-option label="30分钟" value="30m" />
                  <el-option label="1小时" value="1h" />
                  <el-option label="4小时" value="4h" />
                  <el-option label="1天" value="1d" />
                </el-select>
              </el-form-item>

              <el-form-item label="显示网格线">
                <el-switch v-model="uiSettings.showGridLines" />
              </el-form-item>

              <el-form-item label="显示成交量">
                <el-switch v-model="uiSettings.showVolume" />
              </el-form-item>

              <el-form-item label="自动保存布局">
                <el-switch v-model="uiSettings.autoSaveLayout" />
              </el-form-item>
            </el-form>
          </el-card>

          <!-- API设置 -->
          <el-card class="settings-card" shadow="hover">
            <template #header>
              <span class="card-title">
                <el-icon><Link /></el-icon>
                API设置
              </span>
            </template>
            
            <el-form :model="apiSettings" label-width="120px">
              <el-form-item label="API密钥">
                <el-input 
                  v-model="apiSettings.apiKey" 
                  type="password" 
                  show-password
                  placeholder="请输入API密钥"
                />
              </el-form-item>

              <el-form-item label="API密钥状态">
                <el-tag :type="apiSettings.apiKey ? 'success' : 'warning'">
                  {{ apiSettings.apiKey ? '已配置' : '未配置' }}
                </el-tag>
              </el-form-item>

              <el-form-item label="连接超时">
                <el-input-number 
                  v-model="apiSettings.timeout" 
                  :min="1000" 
                  :max="30000"
                  :step="1000"
                  style="width: 100%"
                >
                  <template #append>毫秒</template>
                </el-input-number>
              </el-form-item>

              <el-form-item label="重试次数">
                <el-input-number 
                  v-model="apiSettings.retryCount" 
                  :min="0" 
                  :max="10"
                  style="width: 100%"
                />
              </el-form-item>

              <el-form-item label="启用调试模式">
                <el-switch v-model="apiSettings.debugMode" />
              </el-form-item>

              <el-form-item>
                <el-button @click="testApiConnection" :loading="testingApi">
                  <el-icon><Link /></el-icon>
                  测试连接
                </el-button>
              </el-form-item>
            </el-form>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 设置预览对话框 -->
    <el-dialog v-model="showPreview" title="设置预览" width="60%">
      <div class="settings-preview">
        <el-descriptions title="当前设置概览" :column="2" border>
          <el-descriptions-item label="交易模式">
            {{ getTradingModeText(basicSettings.defaultTradingMode) }}
          </el-descriptions-item>
          <el-descriptions-item label="订单类型">
            {{ getOrderTypeText(basicSettings.defaultOrderType) }}
          </el-descriptions-item>
          <el-descriptions-item label="风险控制">
            {{ riskSettings.enabled ? '已启用' : '已禁用' }}
          </el-descriptions-item>
          <el-descriptions-item label="风险等级">
            {{ getRiskLevelText(riskSettings.riskLevel) }}
          </el-descriptions-item>
          <el-descriptions-item label="通知方式">
            {{ notificationSettings.methods.join(', ') || '无' }}
          </el-descriptions-item>
          <el-descriptions-item label="主题模式">
            {{ getThemeText(uiSettings.theme) }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
      <template #footer>
        <el-button @click="showPreview = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  TrendCharts, 
  RefreshLeft, 
  Check, 
  Setting, 
  Warning, 
  Bell, 
  Monitor, 
  Link 
} from '@element-plus/icons-vue'

const saving = ref(false)
const testingApi = ref(false)
const showPreview = ref(false)

// 基础交易设置
const basicSettings = reactive({
  defaultTradingMode: 'manual',
  defaultOrderType: 'limit',
  defaultQuantity: 100,
  priceDecimalPlaces: 2,
  refreshInterval: 3000,
  requireConfirmation: true
})

// 风险控制设置
const riskSettings = reactive({
  enabled: true,
  maxSingleOrderAmount: 50000,
  maxDailyTradingAmount: 200000,
  maxPositionRatio: 30,
  stopLossRatio: 5,
  takeProfitRatio: 10,
  riskLevel: 'moderate'
})

// 通知设置
const notificationSettings = reactive({
  orderExecution: true,
  priceAlert: true,
  riskAlert: true,
  systemMaintenance: false,
  methods: ['browser', 'email']
})

// 界面设置
const uiSettings = reactive({
  theme: 'light',
  defaultChartType: 'candlestick',
  defaultTimeframe: '15m',
  showGridLines: true,
  showVolume: true,
  autoSaveLayout: true
})

// API设置
const apiSettings = reactive({
  apiKey: '',
  timeout: 5000,
  retryCount: 3,
  debugMode: false
})

// 是否有任何通知启用
const hasAnyNotificationEnabled = computed(() => {
  return notificationSettings.orderExecution || 
         notificationSettings.priceAlert || 
         notificationSettings.riskAlert || 
         notificationSettings.systemMaintenance
})

// 获取交易模式文本
const getTradingModeText = (mode: string) => {
  const modes: Record<string, string> = {
    manual: '手动交易',
    'semi-auto': '半自动交易',
    auto: '全自动交易'
  }
  return modes[mode] || '未知'
}

// 获取订单类型文本
const getOrderTypeText = (type: string) => {
  const types: Record<string, string> = {
    market: '市价单',
    limit: '限价单',
    stop: '止损单',
    'take-profit': '止盈单'
  }
  return types[type] || '未知'
}

// 获取风险等级文本
const getRiskLevelText = (level: string) => {
  const levels: Record<string, string> = {
    conservative: '保守型',
    moderate: '稳健型',
    aggressive: '激进型'
  }
  return levels[level] || '未知'
}

// 获取主题文本
const getThemeText = (theme: string) => {
  const themes: Record<string, string> = {
    light: '浅色主题',
    dark: '深色主题',
    auto: '跟随系统'
  }
  return themes[theme] || '未知'
}

// 保存所有设置
const saveAllSettings = async () => {
  try {
    saving.value = true
    
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 1500))
    
    ElMessage.success('所有设置已保存')
  } catch (error) {
    ElMessage.error('保存设置失败')
  } finally {
    saving.value = false
  }
}

// 恢复默认设置
const resetToDefault = async () => {
  try {
    const result = await ElMessageBox.confirm(
      '确定要恢复所有设置到默认值吗？此操作不可撤销。',
      '恢复默认设置',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    if (result === 'confirm') {
      // 重置所有设置
      Object.assign(basicSettings, {
        defaultTradingMode: 'manual',
        defaultOrderType: 'limit',
        defaultQuantity: 100,
        priceDecimalPlaces: 2,
        refreshInterval: 3000,
        requireConfirmation: true
      })
      
      Object.assign(riskSettings, {
        enabled: true,
        maxSingleOrderAmount: 50000,
        maxDailyTradingAmount: 200000,
        maxPositionRatio: 30,
        stopLossRatio: 5,
        takeProfitRatio: 10,
        riskLevel: 'moderate'
      })
      
      Object.assign(notificationSettings, {
        orderExecution: true,
        priceAlert: true,
        riskAlert: true,
        systemMaintenance: false,
        methods: ['browser', 'email']
      })
      
      Object.assign(uiSettings, {
        theme: 'light',
        defaultChartType: 'candlestick',
        defaultTimeframe: '15m',
        showGridLines: true,
        showVolume: true,
        autoSaveLayout: true
      })
      
      Object.assign(apiSettings, {
        apiKey: '',
        timeout: 5000,
        retryCount: 3,
        debugMode: false
      })
      
      ElMessage.success('已恢复默认设置')
    }
  } catch (error) {
    // 用户取消
  }
}

// 测试API连接
const testApiConnection = async () => {
  if (!apiSettings.apiKey) {
    ElMessage.warning('请先配置API密钥')
    return
  }
  
  try {
    testingApi.value = true
    
    // 模拟API连接测试
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    // 随机成功或失败
    if (Math.random() > 0.3) {
      ElMessage.success('API连接测试成功')
    } else {
      ElMessage.error('API连接测试失败，请检查密钥和网络')
    }
  } catch (error) {
    ElMessage.error('连接测试失败')
  } finally {
    testingApi.value = false
  }
}
</script>

<style lang="scss" scoped>
.trading-settings-view {
  padding: 24px;
  background: var(--el-bg-color-page);
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  gap: 20px;

  .header-content {
    .page-title {
      display: flex;
      align-items: center;
      gap: 12px;
      margin: 0 0 8px 0;
      font-size: 28px;
      font-weight: 700;
      color: var(--el-text-color-primary);

      .el-icon {
        font-size: 32px;
        color: var(--el-color-primary);
      }
    }

    .page-description {
      margin: 0;
      font-size: 16px;
      color: var(--el-text-color-regular);
    }
  }

  .header-actions {
    display: flex;
    gap: 12px;
    align-items: center;
  }
}

.settings-content {
  .card-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;

    .el-icon {
      color: var(--el-color-primary);
    }
  }

  .settings-card {
    margin-bottom: 20px;

    :deep(.el-form-item) {
      margin-bottom: 20px;
    }

    :deep(.el-slider) {
      margin: 12px 0;
    }
  }
}

.notification-settings {
  .notification-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 0;
    border-bottom: 1px solid var(--el-border-color-lighter);

    &:last-child {
      border-bottom: none;
    }

    .notification-info {
      flex: 1;

      h4 {
        margin: 0 0 4px 0;
        font-size: 16px;
        font-weight: 600;
        color: var(--el-text-color-primary);
      }

      p {
        margin: 0;
        font-size: 14px;
        color: var(--el-text-color-secondary);
      }
    }
  }

  .notification-methods {
    margin-top: 20px;
    padding-top: 20px;
    border-top: 1px solid var(--el-border-color-lighter);

    h4 {
      margin: 0 0 12px 0;
      font-size: 16px;
      font-weight: 600;
      color: var(--el-text-color-primary);
    }

    :deep(.el-checkbox-group) {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
  }
}

.settings-preview {
  :deep(.el-descriptions__title) {
    margin-bottom: 20px;
    font-size: 18px;
    font-weight: 600;
  }
}

// 响应式设计
@media (max-width: 768px) {
  .trading-settings-view {
    padding: 16px;
  }

  .page-header {
    flex-direction: column;
    align-items: stretch;
    gap: 16px;

    .header-actions {
      flex-direction: column;
      gap: 8px;
    }
  }

  .settings-content {
    :deep(.el-form-item__label) {
      width: 100px !important;
    }
  }

  .notification-methods {
    :deep(.el-checkbox-group) {
      flex-direction: column;
    }
  }
}
</style>
