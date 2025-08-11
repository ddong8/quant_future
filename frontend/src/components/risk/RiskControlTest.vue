<template>
  <div class="risk-control-test">
    <div class="header">
      <h3>风险控制测试</h3>
      <p>测试各种风险控制场景，验证系统响应</p>
    </div>

    <el-tabs v-model="activeTab" type="card">
      <!-- 订单风险检查测试 -->
      <el-tab-pane label="订单风险检查" name="order-check">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>订单风险检查测试</span>
            </div>
          </template>

          <el-form :model="orderTestForm" label-width="120px">
            <el-form-item label="用户ID">
              <el-input-number v-model="orderTestForm.user_id" :min="1" style="width: 200px" />
            </el-form-item>

            <el-form-item label="标的代码">
              <el-input v-model="orderTestForm.symbol" placeholder="如: AAPL" style="width: 200px" />
            </el-form-item>

            <el-form-item label="订单方向">
              <el-select v-model="orderTestForm.side" style="width: 200px">
                <el-option label="买入" value="buy" />
                <el-option label="卖出" value="sell" />
              </el-select>
            </el-form-item>

            <el-form-item label="数量">
              <el-input-number v-model="orderTestForm.quantity" :min="1" style="width: 200px" />
            </el-form-item>

            <el-form-item label="价格">
              <el-input-number v-model="orderTestForm.price" :min="0.01" :precision="2" style="width: 200px" />
            </el-form-item>

            <el-form-item label="订单类型">
              <el-select v-model="orderTestForm.order_type" style="width: 200px">
                <el-option label="市价单" value="market" />
                <el-option label="限价单" value="limit" />
                <el-option label="止损单" value="stop" />
              </el-select>
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="testOrderRisk" :loading="orderTesting">
                <el-icon><PlayArrow /></el-icon>
                执行测试
              </el-button>
              <el-button @click="resetOrderForm">重置</el-button>
            </el-form-item>
          </el-form>

          <div v-if="orderTestResult" class="test-result">
            <h4>测试结果</h4>
            <el-alert
              :type="orderTestResult.passed ? 'success' : 'error'"
              :title="orderTestResult.passed ? '风险检查通过' : '风险检查未通过'"
              :description="orderTestResult.message"
              :closable="false"
              show-icon
            />
            
            <div v-if="orderTestResult.actions && orderTestResult.actions.length > 0" class="risk-actions">
              <h5>建议的风险控制动作：</h5>
              <div v-for="(action, index) in orderTestResult.actions" :key="index" class="action-item">
                <el-tag :type="getActionTagType(action.action_type)" size="small">
                  {{ getActionLabel(action.action_type) }}
                </el-tag>
                <span class="action-reason">{{ action.reason }}</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-tab-pane>

      <!-- 风险控制动作测试 -->
      <el-tab-pane label="风险控制动作" name="action-test">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>风险控制动作测试</span>
            </div>
          </template>

          <el-form :model="actionTestForm" label-width="120px">
            <el-form-item label="用户ID">
              <el-input-number v-model="actionTestForm.user_id" :min="1" style="width: 200px" />
            </el-form-item>

            <el-form-item label="动作类型">
              <el-select v-model="actionTestForm.action" style="width: 200px">
                <el-option label="拒绝订单" value="reject_order" />
                <el-option label="减少订单数量" value="reduce_order_size" />
                <el-option label="强制平仓" value="force_close_position" />
                <el-option label="暂停交易" value="suspend_trading" />
                <el-option label="保证金追缴" value="margin_call" />
                <el-option label="强制清算" value="liquidation" />
              </el-select>
            </el-form-item>

            <el-form-item label="测试原因">
              <el-input v-model="actionTestForm.reason" placeholder="测试原因" style="width: 300px" />
            </el-form-item>

            <el-form-item label="附加参数">
              <el-input
                v-model="actionTestParams"
                type="textarea"
                :rows="3"
                placeholder="JSON格式的附加参数"
                style="width: 400px"
              />
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="testRiskAction" :loading="actionTesting">
                <el-icon><PlayArrow /></el-icon>
                执行测试
              </el-button>
              <el-button @click="resetActionForm">重置</el-button>
            </el-form-item>
          </el-form>

          <div v-if="actionTestResult" class="test-result">
            <h4>测试结果</h4>
            <el-alert
              :type="actionTestResult.success ? 'success' : 'error'"
              :title="actionTestResult.success ? '动作执行成功' : '动作执行失败'"
              :description="actionTestResult.message"
              :closable="false"
              show-icon
            />
          </div>
        </el-card>
      </el-tab-pane>

      <!-- 紧急风险控制测试 -->
      <el-tab-pane label="紧急风险控制" name="emergency-test">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>紧急风险控制测试</span>
              <el-tag type="danger" size="small">谨慎使用</el-tag>
            </div>
          </template>

          <el-alert
            type="warning"
            title="警告"
            description="紧急风险控制会立即暂停用户交易并可能触发强制平仓，请谨慎使用！"
            :closable="false"
            show-icon
            style="margin-bottom: 20px"
          />

          <el-form :model="emergencyTestForm" label-width="120px">
            <el-form-item label="用户ID">
              <el-input-number v-model="emergencyTestForm.user_id" :min="1" style="width: 200px" />
            </el-form-item>

            <el-form-item label="触发原因">
              <el-input v-model="emergencyTestForm.reason" placeholder="紧急风险控制原因" style="width: 400px" />
            </el-form-item>

            <el-form-item>
              <el-button type="danger" @click="testEmergencyControl" :loading="emergencyTesting">
                <el-icon><Warning /></el-icon>
                执行紧急控制测试
              </el-button>
              <el-button @click="resetEmergencyForm">重置</el-button>
            </el-form-item>
          </el-form>

          <div v-if="emergencyTestResult" class="test-result">
            <h4>测试结果</h4>
            <el-alert
              :type="emergencyTestResult.success ? 'success' : 'error'"
              :title="emergencyTestResult.success ? '紧急控制执行成功' : '紧急控制执行失败'"
              :description="emergencyTestResult.message"
              :closable="false"
              show-icon
            />
          </div>
        </el-card>
      </el-tab-pane>

      <!-- 系统健康检查 -->
      <el-tab-pane label="系统健康检查" name="health-check">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>系统健康检查</span>
              <el-button size="small" @click="checkSystemHealth" :loading="healthChecking">
                <el-icon><Refresh /></el-icon>
                检查
              </el-button>
            </div>
          </template>

          <div v-if="healthStatus" class="health-status">
            <div class="status-overview">
              <el-tag :type="healthStatus.status === 'healthy' ? 'success' : 'danger'" size="large">
                {{ healthStatus.status === 'healthy' ? '系统健康' : '系统异常' }}
              </el-tag>
              <span class="check-time">检查时间: {{ formatDateTime(healthStatus.timestamp) }}</span>
            </div>

            <div v-if="healthStatus.components" class="components-status">
              <h4>组件状态</h4>
              <el-row :gutter="20">
                <el-col :span="6" v-for="(status, component) in healthStatus.components" :key="component">
                  <div class="component-item">
                    <div class="component-name">{{ getComponentLabel(component) }}</div>
                    <el-tag :type="status === 'healthy' ? 'success' : 'danger'" size="small">
                      {{ status === 'healthy' ? '正常' : '异常' }}
                    </el-tag>
                  </div>
                </el-col>
              </el-row>
            </div>

            <div v-if="healthStatus.config" class="config-status">
              <h4>配置信息</h4>
              <el-descriptions :column="2" size="small" border>
                <el-descriptions-item label="自动风险控制">
                  <el-tag :type="healthStatus.config.auto_risk_control_enabled ? 'success' : 'danger'" size="small">
                    {{ healthStatus.config.auto_risk_control_enabled ? '启用' : '禁用' }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="紧急风险控制">
                  <el-tag :type="healthStatus.config.emergency_control_enabled ? 'success' : 'danger'" size="small">
                    {{ healthStatus.config.emergency_control_enabled ? '启用' : '禁用' }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="最大持仓占比">
                  {{ (healthStatus.config.max_position_size_ratio * 100).toFixed(1) }}%
                </el-descriptions-item>
                <el-descriptions-item label="最大日亏损">
                  {{ (healthStatus.config.max_daily_loss_ratio * 100).toFixed(1) }}%
                </el-descriptions-item>
                <el-descriptions-item label="保证金追缴">
                  {{ (healthStatus.config.margin_call_ratio * 100).toFixed(1) }}%
                </el-descriptions-item>
                <el-descriptions-item label="强制平仓">
                  {{ (healthStatus.config.liquidation_ratio * 100).toFixed(1) }}%
                </el-descriptions-item>
              </el-descriptions>
            </div>

            <div v-if="healthStatus.error" class="error-info">
              <h4>错误信息</h4>
              <el-alert type="error" :title="healthStatus.error" :closable="false" />
            </div>
          </div>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { PlayArrow, Warning, Refresh } from '@element-plus/icons-vue'
import { 
  riskControlApi, 
  type RiskCheckResult, 
  type RiskControlActionResult,
  type RiskControlHealth
} from '@/api/riskControl'
import { formatDateTime } from '@/utils/format'

// 响应式数据
const activeTab = ref('order-check')
const orderTesting = ref(false)
const actionTesting = ref(false)
const emergencyTesting = ref(false)
const healthChecking = ref(false)

// 订单风险检查测试表单
const orderTestForm = ref({
  user_id: 1,
  symbol: 'AAPL',
  side: 'buy',
  quantity: 100,
  price: 150.00,
  order_type: 'limit'
})

const orderTestResult = ref<RiskCheckResult | null>(null)

// 风险控制动作测试表单
const actionTestForm = ref({
  user_id: 1,
  action: 'margin_call',
  reason: '测试保证金追缴功能'
})

const actionTestParams = ref('{}')
const actionTestResult = ref<RiskControlActionResult | null>(null)

// 紧急风险控制测试表单
const emergencyTestForm = ref({
  user_id: 1,
  reason: '测试紧急风险控制功能'
})

const emergencyTestResult = ref<RiskControlActionResult | null>(null)

// 系统健康状态
const healthStatus = ref<RiskControlHealth | null>(null)

// 方法
const testOrderRisk = async () => {
  try {
    orderTesting.value = true
    
    const requestData = {
      user_id: orderTestForm.value.user_id,
      order_data: {
        symbol: orderTestForm.value.symbol,
        side: orderTestForm.value.side,
        quantity: orderTestForm.value.quantity,
        price: orderTestForm.value.price,
        order_type: orderTestForm.value.order_type
      }
    }
    
    orderTestResult.value = await riskControlApi.checkOrderRisk(requestData)
    
  } catch (error: any) {
    ElMessage.error(error.message || '订单风险检查测试失败')
  } finally {
    orderTesting.value = false
  }
}

const testRiskAction = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要执行风险控制动作测试吗？这可能会影响指定用户的交易状态。',
      '确认测试',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    actionTesting.value = true
    
    let context: any = { test: true, reason: actionTestForm.value.reason }
    
    try {
      if (actionTestParams.value.trim()) {
        const additionalParams = JSON.parse(actionTestParams.value)
        context = { ...context, ...additionalParams }
      }
    } catch (e) {
      ElMessage.error('附加参数格式错误，请输入有效的JSON')
      return
    }
    
    const requestData = {
      user_id: actionTestForm.value.user_id,
      action: actionTestForm.value.action,
      context
    }
    
    actionTestResult.value = await riskControlApi.executeRiskAction(requestData)
    
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '风险控制动作测试失败')
    }
  } finally {
    actionTesting.value = false
  }
}

const testEmergencyControl = async () => {
  try {
    await ElMessageBox.confirm(
      '警告：紧急风险控制会立即暂停用户交易并可能触发强制平仓！确定要继续测试吗？',
      '紧急风险控制确认',
      {
        confirmButtonText: '确定执行',
        cancelButtonText: '取消',
        type: 'error'
      }
    )
    
    emergencyTesting.value = true
    
    const requestData = {
      user_id: emergencyTestForm.value.user_id,
      reason: `测试: ${emergencyTestForm.value.reason}`
    }
    
    emergencyTestResult.value = await riskControlApi.emergencyRiskControl(requestData)
    
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '紧急风险控制测试失败')
    }
  } finally {
    emergencyTesting.value = false
  }
}

const checkSystemHealth = async () => {
  try {
    healthChecking.value = true
    healthStatus.value = await riskControlApi.healthCheck()
  } catch (error: any) {
    ElMessage.error(error.message || '系统健康检查失败')
  } finally {
    healthChecking.value = false
  }
}

const resetOrderForm = () => {
  orderTestForm.value = {
    user_id: 1,
    symbol: 'AAPL',
    side: 'buy',
    quantity: 100,
    price: 150.00,
    order_type: 'limit'
  }
  orderTestResult.value = null
}

const resetActionForm = () => {
  actionTestForm.value = {
    user_id: 1,
    action: 'margin_call',
    reason: '测试保证金追缴功能'
  }
  actionTestParams.value = '{}'
  actionTestResult.value = null
}

const resetEmergencyForm = () => {
  emergencyTestForm.value = {
    user_id: 1,
    reason: '测试紧急风险控制功能'
  }
  emergencyTestResult.value = null
}

const getActionLabel = (action: string): string => {
  const labels: Record<string, string> = {
    reject_order: '拒绝订单',
    reduce_order_size: '减少订单',
    force_close_position: '强制平仓',
    suspend_trading: '暂停交易',
    margin_call: '保证金追缴',
    liquidation: '强制清算'
  }
  return labels[action] || action
}

const getActionTagType = (action: string): string => {
  const types: Record<string, string> = {
    reject_order: 'warning',
    reduce_order_size: 'info',
    force_close_position: 'danger',
    suspend_trading: 'danger',
    margin_call: 'warning',
    liquidation: 'danger'
  }
  return types[action] || 'info'
}

const getComponentLabel = (component: string): string => {
  const labels: Record<string, string> = {
    risk_engine: '风险引擎',
    notification_service: '通知服务',
    websocket_manager: 'WebSocket管理器',
    database: '数据库'
  }
  return labels[component] || component
}

// 生命周期
onMounted(() => {
  checkSystemHealth()
})
</script>

<style scoped>
.risk-control-test {
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

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.test-result {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}

.test-result h4 {
  margin: 0 0 12px 0;
  color: #303133;
}

.risk-actions {
  margin-top: 16px;
}

.risk-actions h5 {
  margin: 0 0 8px 0;
  color: #606266;
  font-size: 14px;
}

.action-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  padding: 8px;
  background: var(--el-bg-color-page);
  border-radius: 4px;
}

.action-reason {
  color: #606266;
  font-size: 14px;
}

.health-status {
  padding: 10px 0;
}

.status-overview {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.check-time {
  color: #909399;
  font-size: 14px;
}

.components-status,
.config-status {
  margin-bottom: 20px;
}

.components-status h4,
.config-status h4 {
  margin: 0 0 12px 0;
  color: #303133;
}

.component-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px;
  background: var(--el-bg-color-page);
  border-radius: 8px;
  text-align: center;
}

.component-name {
  font-size: 14px;
  color: #606266;
}

.error-info {
  margin-top: 20px;
}

.error-info h4 {
  margin: 0 0 12px 0;
  color: #f56c6c;
}

:deep(.el-tabs__content) {
  padding-top: 20px;
}
</style>