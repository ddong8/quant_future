<template>
  <el-dialog
    v-model="visible"
    title="设置止损"
    width="500px"
    :before-close="handleClose"
  >
    <div v-if="position" class="stop-loss-dialog">
      <!-- 持仓信息 -->
      <div class="position-info">
        <div class="info-row">
          <span class="label">交易标的:</span>
          <span class="value">
            {{ position.symbol }}
            <el-tag 
              :type="position.position_type === 'LONG' ? 'success' : 'warning'"
              size="small"
            >
              {{ position.position_type === 'LONG' ? '多头' : '空头' }}
            </el-tag>
          </span>
        </div>
        <div class="info-row">
          <span class="label">持仓数量:</span>
          <span class="value">{{ formatNumber(position.quantity) }}</span>
        </div>
        <div class="info-row">
          <span class="label">平均成本:</span>
          <span class="value">{{ formatCurrency(position.average_cost) }}</span>
        </div>
        <div class="info-row" v-if="position.current_price">
          <span class="label">当前价格:</span>
          <span class="value">{{ formatCurrency(position.current_price) }}</span>
        </div>
        <div class="info-row" v-if="position.stop_loss_price">
          <span class="label">当前止损:</span>
          <span class="value current-stop-loss">{{ formatCurrency(position.stop_loss_price) }}</span>
        </div>
      </div>

      <!-- 止损设置表单 -->
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
        class="stop-loss-form"
      >
        <el-form-item label="止损价格" prop="stopPrice">
          <el-input-number
            v-model="form.stopPrice"
            :precision="2"
            :step="0.01"
            :min="0"
            placeholder="请输入止损价格"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="止损方式">
          <el-radio-group v-model="form.stopType">
            <el-radio label="price">价格止损</el-radio>
            <el-radio label="percent">百分比止损</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item v-if="form.stopType === 'percent'" label="止损比例" prop="stopPercent">
          <el-input-number
            v-model="form.stopPercent"
            :precision="2"
            :step="0.1"
            :min="0"
            :max="100"
            placeholder="请输入止损比例"
            style="width: 100%"
          />
          <span class="input-suffix">%</span>
        </el-form-item>

        <el-form-item label="关联订单">
          <el-input
            v-model="form.orderId"
            placeholder="可选：关联订单ID"
            type="number"
          />
        </el-form-item>
      </el-form>

      <!-- 风险提示 -->
      <div class="risk-warning">
        <el-alert
          :title="getRiskWarning()"
          type="warning"
          :closable="false"
          show-icon
        />
      </div>

      <!-- 预期损失计算 -->
      <div v-if="expectedLoss !== null" class="loss-calculation">
        <div class="calculation-title">预期损失计算</div>
        <div class="calculation-content">
          <div class="calculation-row">
            <span class="label">止损价格:</span>
            <span class="value">{{ formatCurrency(calculatedStopPrice) }}</span>
          </div>
          <div class="calculation-row">
            <span class="label">预期损失:</span>
            <span class="value loss">{{ formatCurrency(expectedLoss) }}</span>
          </div>
          <div class="calculation-row">
            <span class="label">损失比例:</span>
            <span class="value loss">{{ formatPercent(lossRatio) }}</span>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button 
          type="primary" 
          @click="handleConfirm"
          :loading="loading"
        >
          确认设置
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import type { Position } from '@/api/position'
import { formatCurrency, formatNumber, formatPercent } from '@/utils/format'

// Props
interface Props {
  modelValue: boolean
  position: Position | null
}

const props = defineProps<Props>()

// 事件定义
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'confirm': [data: { stopPrice: number; orderId?: number }]
}>()

// 响应式数据
const formRef = ref<FormInstance>()
const loading = ref(false)

const form = reactive({
  stopPrice: 0,
  stopType: 'price' as 'price' | 'percent',
  stopPercent: 5,
  orderId: undefined as number | undefined
})

// 表单验证规则
const rules: FormRules = {
  stopPrice: [
    { required: true, message: '请输入止损价格', trigger: 'blur' },
    { 
      validator: (rule, value, callback) => {
        if (!props.position) {
          callback()
          return
        }
        
        const isLong = props.position.position_type === 'LONG'
        const currentPrice = props.position.current_price || props.position.average_cost
        
        if (isLong && value >= currentPrice) {
          callback(new Error('多头止损价格应低于当前价格'))
        } else if (!isLong && value <= currentPrice) {
          callback(new Error('空头止损价格应高于当前价格'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ],
  stopPercent: [
    { required: true, message: '请输入止损比例', trigger: 'blur' },
    { type: 'number', min: 0.1, max: 50, message: '止损比例应在0.1%-50%之间', trigger: 'blur' }
  ]
}

// 计算属性
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const calculatedStopPrice = computed(() => {
  if (!props.position) return 0
  
  if (form.stopType === 'price') {
    return form.stopPrice
  } else {
    const currentPrice = props.position.current_price || props.position.average_cost
    const isLong = props.position.position_type === 'LONG'
    
    if (isLong) {
      return currentPrice * (1 - form.stopPercent / 100)
    } else {
      return currentPrice * (1 + form.stopPercent / 100)
    }
  }
})

const expectedLoss = computed(() => {
  if (!props.position || !calculatedStopPrice.value) return null
  
  const quantity = props.position.quantity
  const avgCost = props.position.average_cost
  const stopPrice = calculatedStopPrice.value
  const isLong = props.position.position_type === 'LONG'
  
  if (isLong) {
    return quantity * (avgCost - stopPrice)
  } else {
    return quantity * (stopPrice - avgCost)
  }
})

const lossRatio = computed(() => {
  if (!props.position || expectedLoss.value === null) return 0
  
  return expectedLoss.value / props.position.total_cost
})

// 监听持仓变化，初始化表单
watch(
  () => props.position,
  (newPosition) => {
    if (newPosition) {
      // 设置默认止损价格
      const currentPrice = newPosition.current_price || newPosition.average_cost
      const isLong = newPosition.position_type === 'LONG'
      
      if (newPosition.stop_loss_price) {
        form.stopPrice = newPosition.stop_loss_price
      } else {
        // 默认5%止损
        if (isLong) {
          form.stopPrice = currentPrice * 0.95
        } else {
          form.stopPrice = currentPrice * 1.05
        }
      }
      
      form.stopType = 'price'
      form.stopPercent = 5
      form.orderId = newPosition.stop_loss_order_id
    }
  },
  { immediate: true }
)

// 监听止损类型变化
watch(
  () => form.stopType,
  (newType) => {
    if (newType === 'percent' && props.position) {
      // 根据百分比计算价格
      const currentPrice = props.position.current_price || props.position.average_cost
      const isLong = props.position.position_type === 'LONG'
      
      if (isLong) {
        form.stopPrice = currentPrice * (1 - form.stopPercent / 100)
      } else {
        form.stopPrice = currentPrice * (1 + form.stopPercent / 100)
      }
    }
  }
)

// 监听止损比例变化
watch(
  () => form.stopPercent,
  (newPercent) => {
    if (form.stopType === 'percent' && props.position) {
      const currentPrice = props.position.current_price || props.position.average_cost
      const isLong = props.position.position_type === 'LONG'
      
      if (isLong) {
        form.stopPrice = currentPrice * (1 - newPercent / 100)
      } else {
        form.stopPrice = currentPrice * (1 + newPercent / 100)
      }
    }
  }
)

// 方法
const handleClose = () => {
  visible.value = false
  formRef.value?.resetFields()
}

const handleConfirm = async () => {
  if (!formRef.value || !props.position) return
  
  try {
    await formRef.value.validate()
    
    loading.value = true
    
    emit('confirm', {
      stopPrice: calculatedStopPrice.value,
      orderId: form.orderId
    })
  } catch (error) {
    // 验证失败
  } finally {
    loading.value = false
  }
}

const getRiskWarning = () => {
  if (!props.position) return ''
  
  const isLong = props.position.position_type === 'LONG'
  const currentPrice = props.position.current_price || props.position.average_cost
  const stopPrice = calculatedStopPrice.value
  
  if (isLong) {
    const lossPercent = ((currentPrice - stopPrice) / currentPrice * 100).toFixed(1)
    return `多头止损：当价格跌至 ${formatCurrency(stopPrice)} 时触发，预计损失 ${lossPercent}%`
  } else {
    const lossPercent = ((stopPrice - currentPrice) / currentPrice * 100).toFixed(1)
    return `空头止损：当价格涨至 ${formatCurrency(stopPrice)} 时触发，预计损失 ${lossPercent}%`
  }
}
</script>

<style scoped>
.stop-loss-dialog {
  padding: 8px 0;
}

.position-info {
  background: var(--el-fill-color-lighter);
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 20px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.info-row:last-child {
  margin-bottom: 0;
}

.info-row .label {
  font-size: 14px;
  color: #6b7280;
}

.info-row .value {
  font-size: 14px;
  color: #1f2937;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
}

.current-stop-loss {
  color: #ef4444;
}

.stop-loss-form {
  margin-bottom: 20px;
}

.input-suffix {
  margin-left: 8px;
  color: #6b7280;
  font-size: 14px;
}

.risk-warning {
  margin-bottom: 20px;
}

.loss-calculation {
  background: var(--el-color-warning-light-9);
  border: 1px solid #f59e0b;
  border-radius: 8px;
  padding: 16px;
}

.calculation-title {
  font-size: 14px;
  font-weight: 600;
  color: #92400e;
  margin-bottom: 12px;
}

.calculation-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.calculation-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.calculation-row .label {
  font-size: 13px;
  color: #92400e;
}

.calculation-row .value {
  font-size: 13px;
  font-weight: 500;
  color: #1f2937;
}

.calculation-row .value.loss {
  color: #ef4444;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .info-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
  
  .calculation-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 2px;
  }
}
</style>