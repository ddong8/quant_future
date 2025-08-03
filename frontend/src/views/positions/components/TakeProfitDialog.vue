<template>
  <el-dialog
    v-model="visible"
    title="设置止盈"
    width="500px"
    :before-close="handleClose"
  >
    <div v-if="position" class="take-profit-dialog">
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
        <div class="info-row" v-if="position.take_profit_price">
          <span class="label">当前止盈:</span>
          <span class="value current-take-profit">{{ formatCurrency(position.take_profit_price) }}</span>
        </div>
      </div>

      <!-- 止盈设置表单 -->
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
        class="take-profit-form"
      >
        <el-form-item label="止盈价格" prop="profitPrice">
          <el-input-number
            v-model="form.profitPrice"
            :precision="2"
            :step="0.01"
            :min="0"
            placeholder="请输入止盈价格"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="止盈方式">
          <el-radio-group v-model="form.profitType">
            <el-radio label="price">价格止盈</el-radio>
            <el-radio label="percent">百分比止盈</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item v-if="form.profitType === 'percent'" label="止盈比例" prop="profitPercent">
          <el-input-number
            v-model="form.profitPercent"
            :precision="2"
            :step="0.1"
            :min="0"
            :max="1000"
            placeholder="请输入止盈比例"
            style="width: 100%"
          />
          <span class="input-suffix">%</span>
        </el-form-item>

        <el-form-item label="止盈策略">
          <el-select v-model="form.profitStrategy" placeholder="选择止盈策略" style="width: 100%">
            <el-option label="固定价格止盈" value="fixed" />
            <el-option label="移动止盈" value="trailing" />
            <el-option label="分批止盈" value="partial" />
          </el-select>
        </el-form-item>

        <el-form-item v-if="form.profitStrategy === 'trailing'" label="移动幅度" prop="trailingPercent">
          <el-input-number
            v-model="form.trailingPercent"
            :precision="2"
            :step="0.1"
            :min="0.1"
            :max="20"
            placeholder="移动止盈幅度"
            style="width: 100%"
          />
          <span class="input-suffix">%</span>
        </el-form-item>

        <el-form-item v-if="form.profitStrategy === 'partial'" label="分批比例" prop="partialPercent">
          <el-input-number
            v-model="form.partialPercent"
            :precision="0"
            :step="10"
            :min="10"
            :max="100"
            placeholder="每次止盈比例"
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

      <!-- 收益提示 -->
      <div class="profit-info">
        <el-alert
          :title="getProfitInfo()"
          type="success"
          :closable="false"
          show-icon
        />
      </div>

      <!-- 预期收益计算 -->
      <div v-if="expectedProfit !== null" class="profit-calculation">
        <div class="calculation-title">预期收益计算</div>
        <div class="calculation-content">
          <div class="calculation-row">
            <span class="label">止盈价格:</span>
            <span class="value">{{ formatCurrency(calculatedProfitPrice) }}</span>
          </div>
          <div class="calculation-row">
            <span class="label">预期收益:</span>
            <span class="value profit">{{ formatCurrency(expectedProfit) }}</span>
          </div>
          <div class="calculation-row">
            <span class="label">收益比例:</span>
            <span class="value profit">{{ formatPercent(profitRatio) }}</span>
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
  'confirm': [data: { profitPrice: number; orderId?: number }]
}>()

// 响应式数据
const formRef = ref<FormInstance>()
const loading = ref(false)

const form = reactive({
  profitPrice: 0,
  profitType: 'price' as 'price' | 'percent',
  profitPercent: 10,
  profitStrategy: 'fixed' as 'fixed' | 'trailing' | 'partial',
  trailingPercent: 2,
  partialPercent: 50,
  orderId: undefined as number | undefined
})

// 表单验证规则
const rules: FormRules = {
  profitPrice: [
    { required: true, message: '请输入止盈价格', trigger: 'blur' },
    { 
      validator: (rule, value, callback) => {
        if (!props.position) {
          callback()
          return
        }
        
        const isLong = props.position.position_type === 'LONG'
        const currentPrice = props.position.current_price || props.position.average_cost
        
        if (isLong && value <= currentPrice) {
          callback(new Error('多头止盈价格应高于当前价格'))
        } else if (!isLong && value >= currentPrice) {
          callback(new Error('空头止盈价格应低于当前价格'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ],
  profitPercent: [
    { required: true, message: '请输入止盈比例', trigger: 'blur' },
    { type: 'number', min: 1, max: 1000, message: '止盈比例应在1%-1000%之间', trigger: 'blur' }
  ],
  trailingPercent: [
    { required: true, message: '请输入移动幅度', trigger: 'blur' },
    { type: 'number', min: 0.1, max: 20, message: '移动幅度应在0.1%-20%之间', trigger: 'blur' }
  ],
  partialPercent: [
    { required: true, message: '请输入分批比例', trigger: 'blur' },
    { type: 'number', min: 10, max: 100, message: '分批比例应在10%-100%之间', trigger: 'blur' }
  ]
}

// 计算属性
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const calculatedProfitPrice = computed(() => {
  if (!props.position) return 0
  
  if (form.profitType === 'price') {
    return form.profitPrice
  } else {
    const currentPrice = props.position.current_price || props.position.average_cost
    const isLong = props.position.position_type === 'LONG'
    
    if (isLong) {
      return currentPrice * (1 + form.profitPercent / 100)
    } else {
      return currentPrice * (1 - form.profitPercent / 100)
    }
  }
})

const expectedProfit = computed(() => {
  if (!props.position || !calculatedProfitPrice.value) return null
  
  const quantity = props.position.quantity
  const avgCost = props.position.average_cost
  const profitPrice = calculatedProfitPrice.value
  const isLong = props.position.position_type === 'LONG'
  
  if (isLong) {
    return quantity * (profitPrice - avgCost)
  } else {
    return quantity * (avgCost - profitPrice)
  }
})

const profitRatio = computed(() => {
  if (!props.position || expectedProfit.value === null) return 0
  
  return expectedProfit.value / props.position.total_cost
})

// 监听持仓变化，初始化表单
watch(
  () => props.position,
  (newPosition) => {
    if (newPosition) {
      // 设置默认止盈价格
      const currentPrice = newPosition.current_price || newPosition.average_cost
      const isLong = newPosition.position_type === 'LONG'
      
      if (newPosition.take_profit_price) {
        form.profitPrice = newPosition.take_profit_price
      } else {
        // 默认10%止盈
        if (isLong) {
          form.profitPrice = currentPrice * 1.1
        } else {
          form.profitPrice = currentPrice * 0.9
        }
      }
      
      form.profitType = 'price'
      form.profitPercent = 10
      form.profitStrategy = 'fixed'
      form.orderId = newPosition.take_profit_order_id
    }
  },
  { immediate: true }
)

// 监听止盈类型变化
watch(
  () => form.profitType,
  (newType) => {
    if (newType === 'percent' && props.position) {
      // 根据百分比计算价格
      const currentPrice = props.position.current_price || props.position.average_cost
      const isLong = props.position.position_type === 'LONG'
      
      if (isLong) {
        form.profitPrice = currentPrice * (1 + form.profitPercent / 100)
      } else {
        form.profitPrice = currentPrice * (1 - form.profitPercent / 100)
      }
    }
  }
)

// 监听止盈比例变化
watch(
  () => form.profitPercent,
  (newPercent) => {
    if (form.profitType === 'percent' && props.position) {
      const currentPrice = props.position.current_price || props.position.average_cost
      const isLong = props.position.position_type === 'LONG'
      
      if (isLong) {
        form.profitPrice = currentPrice * (1 + newPercent / 100)
      } else {
        form.profitPrice = currentPrice * (1 - newPercent / 100)
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
      profitPrice: calculatedProfitPrice.value,
      orderId: form.orderId
    })
  } catch (error) {
    // 验证失败
  } finally {
    loading.value = false
  }
}

const getProfitInfo = () => {
  if (!props.position) return ''
  
  const isLong = props.position.position_type === 'LONG'
  const currentPrice = props.position.current_price || props.position.average_cost
  const profitPrice = calculatedProfitPrice.value
  
  if (isLong) {
    const profitPercent = ((profitPrice - currentPrice) / currentPrice * 100).toFixed(1)
    return `多头止盈：当价格涨至 ${formatCurrency(profitPrice)} 时触发，预计收益 ${profitPercent}%`
  } else {
    const profitPercent = ((currentPrice - profitPrice) / currentPrice * 100).toFixed(1)
    return `空头止盈：当价格跌至 ${formatCurrency(profitPrice)} 时触发，预计收益 ${profitPercent}%`
  }
}
</script>

<style scoped>
.take-profit-dialog {
  padding: 8px 0;
}

.position-info {
  background: #f9fafb;
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

.current-take-profit {
  color: #10b981;
}

.take-profit-form {
  margin-bottom: 20px;
}

.input-suffix {
  margin-left: 8px;
  color: #6b7280;
  font-size: 14px;
}

.profit-info {
  margin-bottom: 20px;
}

.profit-calculation {
  background: #ecfdf5;
  border: 1px solid #10b981;
  border-radius: 8px;
  padding: 16px;
}

.calculation-title {
  font-size: 14px;
  font-weight: 600;
  color: #047857;
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
  color: #047857;
}

.calculation-row .value {
  font-size: 13px;
  font-weight: 500;
  color: #1f2937;
}

.calculation-row .value.profit {
  color: #10b981;
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