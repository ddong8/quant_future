<template>
  <div class="risk-control-config">
    <div class="header">
      <h3>风险控制配置</h3>
      <div class="actions">
        <el-button @click="loadConfig">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button type="primary" @click="saveConfig" :loading="saving">
          <el-icon><Check /></el-icon>
          保存配置
        </el-button>
      </div>
    </div>

    <el-card v-loading="loading">
      <el-form
        ref="formRef"
        :model="config"
        :rules="rules"
        label-width="180px"
        class="config-form"
      >
        <el-divider content-position="left">基础风险参数</el-divider>
        
        <el-form-item label="最大持仓占比" prop="max_position_size_ratio">
          <el-input-number
            v-model="config.max_position_size_ratio"
            :min="0.01"
            :max="1"
            :step="0.01"
            :precision="2"
            style="width: 200px"
          />
          <span class="form-help">单个标的持仓价值占总资产的最大比例</span>
        </el-form-item>

        <el-form-item label="最大日亏损比例" prop="max_daily_loss_ratio">
          <el-input-number
            v-model="config.max_daily_loss_ratio"
            :min="0.01"
            :max="0.5"
            :step="0.01"
            :precision="2"
            style="width: 200px"
          />
          <span class="form-help">单日最大亏损占总资产的比例</span>
        </el-form-item>

        <el-form-item label="最大订单价值比例" prop="max_order_value_ratio">
          <el-input-number
            v-model="config.max_order_value_ratio"
            :min="0.01"
            :max="1"
            :step="0.01"
            :precision="2"
            style="width: 200px"
          />
          <span class="form-help">单笔订单价值占总资产的最大比例</span>
        </el-form-item>

        <el-divider content-position="left">保证金管理</el-divider>

        <el-form-item label="保证金追缴比例" prop="margin_call_ratio">
          <el-input-number
            v-model="config.margin_call_ratio"
            :min="0.1"
            :max="0.8"
            :step="0.01"
            :precision="2"
            style="width: 200px"
          />
          <span class="form-help">触发保证金追缴的保证金比例阈值</span>
        </el-form-item>

        <el-form-item label="强制平仓比例" prop="liquidation_ratio">
          <el-input-number
            v-model="config.liquidation_ratio"
            :min="0.05"
            :max="0.5"
            :step="0.01"
            :precision="2"
            style="width: 200px"
          />
          <span class="form-help">触发强制平仓的保证金比例阈值</span>
        </el-form-item>

        <el-divider content-position="left">系统开关</el-divider>

        <el-form-item label="自动风险控制">
          <el-switch
            v-model="config.auto_risk_control_enabled"
            active-text="启用"
            inactive-text="禁用"
          />
          <span class="form-help">是否启用自动风险控制功能</span>
        </el-form-item>

        <el-form-item label="紧急风险控制">
          <el-switch
            v-model="config.emergency_control_enabled"
            active-text="启用"
            inactive-text="禁用"
          />
          <span class="form-help">是否启用紧急风险控制功能</span>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 配置预览 -->
    <el-card style="margin-top: 20px">
      <template #header>
        <div class="card-header">
          <span>配置预览</span>
        </div>
      </template>

      <div class="config-preview">
        <el-row :gutter="20">
          <el-col :span="12">
            <div class="preview-section">
              <h4>风险阈值</h4>
              <div class="preview-item">
                <span class="label">最大持仓占比:</span>
                <span class="value">{{ (config.max_position_size_ratio * 100).toFixed(1) }}%</span>
              </div>
              <div class="preview-item">
                <span class="label">最大日亏损:</span>
                <span class="value">{{ (config.max_daily_loss_ratio * 100).toFixed(1) }}%</span>
              </div>
              <div class="preview-item">
                <span class="label">最大订单占比:</span>
                <span class="value">{{ (config.max_order_value_ratio * 100).toFixed(1) }}%</span>
              </div>
            </div>
          </el-col>
          <el-col :span="12">
            <div class="preview-section">
              <h4>保证金管理</h4>
              <div class="preview-item">
                <span class="label">保证金追缴:</span>
                <span class="value">{{ (config.margin_call_ratio * 100).toFixed(1) }}%</span>
              </div>
              <div class="preview-item">
                <span class="label">强制平仓:</span>
                <span class="value">{{ (config.liquidation_ratio * 100).toFixed(1) }}%</span>
              </div>
              <div class="preview-item">
                <span class="label">系统状态:</span>
                <span class="value">
                  <el-tag :type="config.auto_risk_control_enabled ? 'success' : 'danger'" size="small">
                    {{ config.auto_risk_control_enabled ? '启用' : '禁用' }}
                  </el-tag>
                </span>
              </div>
            </div>
          </el-col>
        </el-row>
      </div>
    </el-card>

    <!-- 风险等级说明 -->
    <el-card style="margin-top: 20px">
      <template #header>
        <div class="card-header">
          <span>风险等级说明</span>
        </div>
      </template>

      <div class="risk-levels">
        <div class="risk-level-item">
          <el-tag type="success" size="small">低风险</el-tag>
          <span class="description">正常交易状态，所有指标在安全范围内</span>
        </div>
        <div class="risk-level-item">
          <el-tag type="warning" size="small">中风险</el-tag>
          <span class="description">部分指标接近阈值，需要关注</span>
        </div>
        <div class="risk-level-item">
          <el-tag type="danger" size="small">高风险</el-tag>
          <span class="description">风险指标超过阈值，可能触发风险控制措施</span>
        </div>
        <div class="risk-level-item">
          <el-tag type="danger" size="small">极高风险</el-tag>
          <span class="description">严重风险状态，将触发紧急风险控制</span>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { Refresh, Check } from '@element-plus/icons-vue'
import { riskControlApi, type RiskControlConfig } from '@/api/riskControl'

// 响应式数据
const formRef = ref<FormInstance>()
const loading = ref(false)
const saving = ref(false)

const config = ref<RiskControlConfig>({
  max_position_size_ratio: 0.1,
  max_daily_loss_ratio: 0.05,
  margin_call_ratio: 0.3,
  liquidation_ratio: 0.2,
  max_order_value_ratio: 0.2,
  auto_risk_control_enabled: true,
  emergency_control_enabled: true
})

// 表单验证规则
const rules: FormRules = {
  max_position_size_ratio: [
    { required: true, message: '请设置最大持仓占比', trigger: 'blur' },
    { type: 'number', min: 0.01, max: 1, message: '持仓占比必须在1%-100%之间', trigger: 'blur' }
  ],
  max_daily_loss_ratio: [
    { required: true, message: '请设置最大日亏损比例', trigger: 'blur' },
    { type: 'number', min: 0.01, max: 0.5, message: '日亏损比例必须在1%-50%之间', trigger: 'blur' }
  ],
  max_order_value_ratio: [
    { required: true, message: '请设置最大订单价值比例', trigger: 'blur' },
    { type: 'number', min: 0.01, max: 1, message: '订单价值比例必须在1%-100%之间', trigger: 'blur' }
  ],
  margin_call_ratio: [
    { required: true, message: '请设置保证金追缴比例', trigger: 'blur' },
    { type: 'number', min: 0.1, max: 0.8, message: '保证金追缴比例必须在10%-80%之间', trigger: 'blur' }
  ],
  liquidation_ratio: [
    { required: true, message: '请设置强制平仓比例', trigger: 'blur' },
    { type: 'number', min: 0.05, max: 0.5, message: '强制平仓比例必须在5%-50%之间', trigger: 'blur' }
  ]
}

// 方法
const loadConfig = async () => {
  try {
    loading.value = true
    config.value = await riskControlApi.getRiskControlConfig()
  } catch (error: any) {
    ElMessage.error(error.message || '加载配置失败')
  } finally {
    loading.value = false
  }
}

const saveConfig = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    
    saving.value = true
    await riskControlApi.updateRiskControlConfig(config.value)
    
    ElMessage.success('配置保存成功')
  } catch (error: any) {
    if (error.message) {
      ElMessage.error(error.message || '保存配置失败')
    }
  } finally {
    saving.value = false
  }
}

// 生命周期
onMounted(() => {
  loadConfig()
})
</script>

<style scoped>
.risk-control-config {
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

.config-form {
  padding: 20px 0;
}

.form-help {
  margin-left: 10px;
  color: #909399;
  font-size: 12px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.config-preview {
  padding: 10px 0;
}

.preview-section {
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
}

.preview-section h4 {
  margin: 0 0 12px 0;
  color: #303133;
  font-size: 16px;
}

.preview-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  padding: 8px 0;
  border-bottom: 1px solid #ebeef5;
}

.preview-item:last-child {
  border-bottom: none;
  margin-bottom: 0;
}

.preview-item .label {
  color: #606266;
  font-size: 14px;
}

.preview-item .value {
  font-weight: bold;
  color: #303133;
}

.risk-levels {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.risk-level-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
}

.risk-level-item .description {
  color: #606266;
  font-size: 14px;
}

:deep(.el-divider__text) {
  font-weight: bold;
  color: #409eff;
}

:deep(.el-input-number) {
  width: 200px;
}
</style>