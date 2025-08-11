<template>
  <el-dialog
    v-model="visible"
    title="平仓操作"
    width="500px"
    :before-close="handleClose"
  >
    <div v-if="position" class="close-position-dialog">
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
          <span class="label">可用数量:</span>
          <span class="value">{{ formatNumber(position.available_quantity) }}</span>
        </div>
        <div class="info-row">
          <span class="label">平均成本:</span>
          <span class="value">{{ formatCurrency(position.average_cost) }}</span>
        </div>
        <div class="info-row" v-if="position.current_price">
          <span class="label">当前价格:</span>
          <span class="value">{{ formatCurrency(position.current_price) }}</span>
        </div>
        <div class="info-row">
          <span class="label">当前盈亏:</span>
          <span class="value" :class="getPnLClass(position.total_pnl)">
            {{ formatCurrency(position.total_pnl) }}
            ({{ formatPercent(position.return_rate) }})
          </span>
        </div>
      </div>

      <!-- 平仓设置表单 -->
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
        class="close-form"
      >
        <el-form-item label="平仓类型">
          <el-radio-group v-model="form.closeType">
            <el-radio label="full">全部平仓</el-radio>
            <el-radio label="partial">部分平仓</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item v-if="form.closeType === 'partial'" label="平仓数量" prop="closeQuantity">
          <el-input-number
            v-model="form.closeQuantity"
            :precision="0"
            :step="1"
            :min="1"
            :max="position.available_quantity"
            placeholder="请输入平仓数量"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="平仓价格" prop="closePrice">
          <div class="price-input-group">
            <el-input-number
              v-model="form.closePrice"
              :precision="2"
              :step="0.01"
              :min="0"
              placeholder="请输入平仓价格"
              style="flex: 1"
            />
            <el-button 
              v-if="position.current_price"
              type="primary" 
              size="small"
              @click="useCurrentPrice"
            >
              使用现价
            </el-button>
          </div>
        </el-form-item>

        <el-form-item label="平仓方式">
          <el-select v-model="form.closeMethod" placeholder="选择平仓方式" style="width: 100%">
            <el-option label="市价平仓" value="market" />
            <el-option label="限价平仓" value="limit" />
            <el-option label="止损平仓" value="stop" />
          </el-select>
        </el-form-item>

        <el-form-item label="平仓原因">
          <el-select 
            v-model="form.reason" 
            placeholder="选择平仓原因" 
            style="width: 100%"
            allow-create
            filterable
          >
            <el-option label="止盈平仓" value="take_profit" />
            <el-option label="止损平仓" value="stop_loss" />
            <el-option label="主动平仓" value="manual" />
            <el-option label="风控平仓" value="risk_control" />
            <el-option label="策略平仓" value="strategy" />
            <el-option label="其他原因" value="other" />
          </el-select>
        </el-form-item>

        <el-form-item label="备注说明">
          <el-input
            v-model="form.notes"
            type="textarea"
            :rows="3"
            placeholder="可选：输入平仓备注"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
      </el-form>

      <!-- 平仓预览 -->
      <div class="close-preview">
        <div class="preview-title">平仓预览</div>
        <div class="preview-content">
          <div class="preview-row">
            <span class="label">平仓数量:</span>
            <span class="value">{{ formatNumber(closeQuantity) }}</span>
          </div>
          <div class="preview-row">
            <span class="label">平仓价格:</span>
            <span class="value">{{ formatCurrency(form.closePrice || 0) }}</span>
          </div>
          <div class="preview-row">
            <span class="label">平仓金额:</span>
            <span class="value">{{ formatCurrency(closeAmount) }}</span>
          </div>
          <div class="preview-row">
            <span class="label">预计盈亏:</span>
            <span class="value" :class="getPnLClass(expectedPnL)">
              {{ formatCurrency(expectedPnL) }}
            </span>
          </div>
          <div class="preview-row">
            <span class="label">剩余数量:</span>
            <span class="value">{{ formatNumber(remainingQuantity) }}</span>
          </div>
        </div>
      </div>

      <!-- 风险提示 -->
      <div class="risk-warning">
        <el-alert
          :title="getRiskWarning()"
          :type="expectedPnL >= 0 ? 'success' : 'warning'"
          :closable="false"
          show-icon
        />
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button 
          type="danger" 
          @click="handleConfirm"
          :loading="loading"
        >
          确认平仓
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
  'confirm': [data: { closePrice: number; reason?: string }]
}>()

// 响应式数据
const formRef = ref<FormInstance>()
const loading = ref(false)

const form = reactive({
  closeType: 'full' as 'full' | 'partial',
  closeQuantity: 0,
  closePrice: 0,
  closeMethod: 'market' as 'market' | 'limit' | 'stop',
  reason: '',
  notes: ''
})

// 表单验证规则
const rules: FormRules = {
  closeQuantity: [
    { required: true, message: '请输入平仓数量', trigger: 'blur' },
    { 
      validator: (rule, value, callback) => {
        if (!props.position) {
          callback()
          return
        }
        
        if (value <= 0) {
          callback(new Error('平仓数量必须大于0'))
        } else if (value > props.position.available_quantity) {
          callback(new Error('平仓数量不能超过可用数量'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ],
  closePrice: [
    { required: true, message: '请输入平仓价格', trigger: 'blur' },
    { type: 'number', min: 0.01, message: '平仓价格必须大于0', trigger: 'blur' }
  ]
}

// 计算属性
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const closeQuantity = computed(() => {
  if (!props.position) return 0
  
  return form.closeType === 'full' 
    ? props.position.available_quantity 
    : form.closeQuantity
})

const closeAmount = computed(() => {
  return closeQuantity.value * (form.closePrice || 0)
})

const expectedPnL = computed(() => {
  if (!props.position || !form.closePrice) return 0
  
  const quantity = closeQuantity.value
  const avgCost = props.position.average_cost
  const closePrice = form.closePrice
  const isLong = props.position.position_type === 'LONG'
  
  if (isLong) {
    return quantity * (closePrice - avgCost)
  } else {
    return quantity * (avgCost - closePrice)
  }
})

const remainingQuantity = computed(() => {
  if (!props.position) return 0
  
  return props.position.quantity - closeQuantity.value
})

// 监听持仓变化，初始化表单
watch(
  () => props.position,
  (newPosition) => {
    if (newPosition) {
      form.closeType = 'full'
      form.closeQuantity = newPosition.available_quantity
      form.closePrice = newPosition.current_price || newPosition.average_cost
      form.closeMethod = 'market'
      form.reason = 'manual'
      form.notes = ''
    }
  },
  { immediate: true }
)

// 监听平仓类型变化
watch(
  () => form.closeType,
  (newType) => {
    if (newType === 'full' && props.position) {
      form.closeQuantity = props.position.available_quantity
    } else if (newType === 'partial' && props.position) {
      form.closeQuantity = Math.floor(props.position.available_quantity / 2)
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
    
    const reason = form.reason ? `${form.reason}${form.notes ? ': ' + form.notes : ''}` : form.notes
    
    emit('confirm', {
      closePrice: form.closePrice,
      reason
    })
  } catch (error) {
    // 验证失败
  } finally {
    loading.value = false
  }
}

const useCurrentPrice = () => {
  if (props.position?.current_price) {
    form.closePrice = props.position.current_price
  }
}

const getPnLClass = (value: number) => {
  if (value > 0) return 'profit'
  if (value < 0) return 'loss'
  return 'neutral'
}

const getRiskWarning = () => {
  if (!props.position) return ''
  
  const isProfit = expectedPnL.value >= 0
  const pnlPercent = Math.abs(expectedPnL.value / (props.position.total_cost || 1) * 100).toFixed(1)
  
  if (isProfit) {
    return `预计盈利 ${formatCurrency(expectedPnL.value)}，收益率 ${pnlPercent}%`
  } else {
    return `预计亏损 ${formatCurrency(Math.abs(expectedPnL.value))}，亏损率 ${pnlPercent}%`
  }
}
</script>

<style scoped>
.close-position-dialog {
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

.close-form {
  margin-bottom: 20px;
}

.price-input-group {
  display: flex;
  gap: 8px;
  align-items: center;
}

.close-preview {
  background: var(--el-fill-color-lighter);
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 20px;
}

.preview-title {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 12px;
}

.preview-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.preview-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.preview-row .label {
  font-size: 13px;
  color: #6b7280;
}

.preview-row .value {
  font-size: 13px;
  font-weight: 500;
  color: #1f2937;
}

.risk-warning {
  margin-bottom: 20px;
}

.profit {
  color: #10b981;
}

.loss {
  color: #ef4444;
}

.neutral {
  color: #6b7280;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .info-row,
  .preview-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
  
  .price-input-group {
    flex-direction: column;
    width: 100%;
  }
  
  .price-input-group .el-input-number {
    width: 100%;
  }
}
</style>