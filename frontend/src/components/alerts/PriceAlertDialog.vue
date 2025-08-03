<template>
  <el-dialog
    v-model="visible"
    :title="isEdit ? '编辑价格提醒' : '创建价格提醒'"
    width="600px"
    @close="handleClose"
  >
    <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
      <!-- 标的选择 -->
      <el-form-item label="标的代码" prop="symbol_code">
        <el-select
          v-model="form.symbol_code"
          placeholder="请选择标的"
          filterable
          remote
          :remote-method="searchSymbols"
          :loading="symbolLoading"
          style="width: 100%"
          :disabled="isEdit"
        >
          <el-option
            v-for="symbol in symbolOptions"
            :key="symbol.value"
            :label="`${symbol.value} - ${symbol.label}`"
            :value="symbol.value"
          />
        </el-select>
      </el-form-item>

      <!-- 提醒类型 -->
      <el-form-item label="提醒类型" prop="alert_type">
        <el-select v-model="form.alert_type" placeholder="请选择提醒类型" style="width: 100%">
          <el-option label="价格突破" value="PRICE_ABOVE" />
          <el-option label="价格跌破" value="PRICE_BELOW" />
          <el-option label="涨跌幅达到" value="CHANGE_PERCENT" />
          <el-option label="成交量达到" value="VOLUME" />
        </el-select>
      </el-form-item>

      <!-- 条件设置 -->
      <el-form-item label="条件设置" prop="condition_value">
        <div class="condition-setting">
          <el-select v-model="form.comparison_operator" style="width: 80px">
            <el-option label=">" value=">" />
            <el-option label="<" value="<" />
            <el-option label=">=" value=">=" />
            <el-option label="<=" value="<=" />
            <el-option label="=" value="=" />
          </el-select>
          <el-input-number
            v-model="form.condition_value"
            :precision="getPrecision(form.alert_type)"
            :step="getStep(form.alert_type)"
            :min="0"
            style="width: 200px; margin-left: 8px"
          />
          <span class="unit">{{ getUnit(form.alert_type) }}</span>
        </div>
      </el-form-item>

      <!-- 通知方式 -->
      <el-form-item label="通知方式" prop="notification_methods">
        <el-checkbox-group v-model="form.notification_methods">
          <el-checkbox label="websocket">站内通知</el-checkbox>
          <el-checkbox label="email">邮件通知</el-checkbox>
          <el-checkbox label="sms">短信通知</el-checkbox>
          <el-checkbox label="push">推送通知</el-checkbox>
        </el-checkbox-group>
      </el-form-item>

      <!-- 高级设置 -->
      <el-form-item label="高级设置">
        <div class="advanced-settings">
          <el-checkbox v-model="form.is_repeatable">可重复触发</el-checkbox>
          <el-checkbox v-model="showExpireTime">设置过期时间</el-checkbox>
        </div>
      </el-form-item>

      <!-- 过期时间 -->
      <el-form-item v-if="showExpireTime" label="过期时间" prop="expires_at">
        <el-date-picker
          v-model="form.expires_at"
          type="datetime"
          placeholder="选择过期时间"
          format="YYYY-MM-DD HH:mm:ss"
          value-format="YYYY-MM-DD HH:mm:ss"
          style="width: 100%"
        />
      </el-form-item>

      <!-- 备注 -->
      <el-form-item label="备注">
        <el-input
          v-model="form.note"
          type="textarea"
          :rows="3"
          placeholder="请输入备注信息"
          maxlength="200"
          show-word-limit
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          {{ isEdit ? '更新' : '创建' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { createPriceAlert, updatePriceAlert, type PriceAlert } from '@/api/marketDepth'
import { searchSymbols as searchSymbolsAPI } from '@/api/marketQuotes'

interface Props {
  modelValue: boolean
  alertData?: PriceAlert | null
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'save'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 响应式数据
const visible = ref(false)
const submitting = ref(false)
const symbolLoading = ref(false)
const showExpireTime = ref(false)
const formRef = ref<FormInstance>()

// 表单数据
const form = ref({
  symbol_code: '',
  alert_type: 'PRICE_ABOVE',
  condition_value: 0,
  comparison_operator: '>',
  is_active: true,
  is_repeatable: false,
  notification_methods: ['websocket'],
  expires_at: '',
  note: ''
})

// 标的选项
const symbolOptions = ref([
  { label: 'Apple Inc.', value: 'AAPL' },
  { label: 'Alphabet Inc.', value: 'GOOGL' },
  { label: 'Microsoft Corporation', value: 'MSFT' },
  { label: 'Tesla, Inc.', value: 'TSLA' },
  { label: 'Amazon.com, Inc.', value: 'AMZN' }
])

// 是否为编辑模式
const isEdit = computed(() => !!props.alertData)

// 表单验证规则
const rules: FormRules = {
  symbol_code: [
    { required: true, message: '请选择标的', trigger: 'change' }
  ],
  alert_type: [
    { required: true, message: '请选择提醒类型', trigger: 'change' }
  ],
  condition_value: [
    { required: true, message: '请输入条件值', trigger: 'blur' },
    { type: 'number', min: 0, message: '条件值必须大于0', trigger: 'blur' }
  ],
  notification_methods: [
    { required: true, message: '请选择至少一种通知方式', trigger: 'change' }
  ]
}

// 监听 modelValue 变化
watch(() => props.modelValue, (newValue) => {
  visible.value = newValue
  if (newValue) {
    resetForm()
    if (props.alertData) {
      loadAlertData()
    }
  }
})

// 监听 visible 变化
watch(visible, (newValue) => {
  emit('update:modelValue', newValue)
})

// 重置表单
const resetForm = () => {
  form.value = {
    symbol_code: '',
    alert_type: 'PRICE_ABOVE',
    condition_value: 0,
    comparison_operator: '>',
    is_active: true,
    is_repeatable: false,
    notification_methods: ['websocket'],
    expires_at: '',
    note: ''
  }
  showExpireTime.value = false
  formRef.value?.clearValidate()
}

// 加载提醒数据
const loadAlertData = () => {
  if (!props.alertData) return
  
  const alert = props.alertData
  form.value = {
    symbol_code: alert.symbol.symbol,
    alert_type: alert.alert_type,
    condition_value: alert.condition_value,
    comparison_operator: alert.comparison_operator,
    is_active: alert.is_active,
    is_repeatable: alert.is_repeatable,
    notification_methods: [...alert.notification_methods],
    expires_at: alert.expires_at || '',
    note: alert.note || ''
  }
  
  showExpireTime.value = !!alert.expires_at
}

// 搜索标的
const searchSymbols = async (query: string) => {
  if (!query) return
  
  try {
    symbolLoading.value = true
    const response = await searchSymbolsAPI({ q: query, limit: 20 })
    symbolOptions.value = response.data.map(symbol => ({
      label: symbol.name,
      value: symbol.symbol
    }))
  } catch (error) {
    console.error('搜索标的失败:', error)
  } finally {
    symbolLoading.value = false
  }
}

// 获取精度
const getPrecision = (alertType: string) => {
  switch (alertType) {
    case 'PRICE_ABOVE':
    case 'PRICE_BELOW':
      return 2
    case 'CHANGE_PERCENT':
      return 2
    case 'VOLUME':
      return 0
    default:
      return 2
  }
}

// 获取步长
const getStep = (alertType: string) => {
  switch (alertType) {
    case 'PRICE_ABOVE':
    case 'PRICE_BELOW':
      return 0.01
    case 'CHANGE_PERCENT':
      return 0.1
    case 'VOLUME':
      return 1000
    default:
      return 0.01
  }
}

// 获取单位
const getUnit = (alertType: string) => {
  switch (alertType) {
    case 'PRICE_ABOVE':
    case 'PRICE_BELOW':
      return ''
    case 'CHANGE_PERCENT':
      return '%'
    case 'VOLUME':
      return '股'
    default:
      return ''
  }
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    
    submitting.value = true
    
    const submitData = {
      ...form.value,
      expires_at: showExpireTime.value ? form.value.expires_at : undefined
    }
    
    if (isEdit.value && props.alertData) {
      // 更新提醒
      await updatePriceAlert(props.alertData.id, submitData)
      ElMessage.success('价格提醒更新成功')
    } else {
      // 创建提醒
      await createPriceAlert(submitData)
      ElMessage.success('价格提醒创建成功')
    }
    
    emit('save')
    handleClose()
    
  } catch (error: any) {
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error(isEdit.value ? '更新提醒失败' : '创建提醒失败')
    }
  } finally {
    submitting.value = false
  }
}

// 关闭对话框
const handleClose = () => {
  visible.value = false
}
</script>

<style scoped>
.condition-setting {
  display: flex;
  align-items: center;
}

.unit {
  margin-left: 8px;
  color: #909399;
  font-size: 14px;
}

.advanced-settings {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.dialog-footer {
  text-align: right;
}
</style>