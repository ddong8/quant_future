<template>
  <el-form
    ref="formRef"
    :model="formData"
    :rules="formRules"
    :label-width="labelWidth"
    :label-position="labelPosition"
    :size="size"
    :disabled="disabled"
    :validate-on-rule-change="validateOnRuleChange"
    :hide-required-asterisk="hideRequiredAsterisk"
    :show-message="showMessage"
    :inline-message="inlineMessage"
    :status-icon="statusIcon"
    class="base-form"
  >
    <template v-for="field in fields" :key="field.prop">
      <!-- 分组标题 -->
      <div v-if="field.type === 'group'" class="form-group">
        <div class="group-title">{{ field.label }}</div>
        <div class="group-content">
          <template v-for="subField in field.fields" :key="subField.prop">
            <el-form-item
              :prop="subField.prop"
              :label="subField.label"
              :required="subField.required"
              :rules="getFieldRules(subField)"
              :error="getFieldError(subField.prop)"
              :show-message="subField.showMessage !== false"
              :inline-message="subField.inlineMessage"
              :size="subField.size || size"
            >
              <component
                :is="getFieldComponent(subField)"
                v-model="formData[subField.prop]"
                v-bind="getFieldProps(subField)"
                @change="handleFieldChange(subField.prop, $event)"
                @blur="handleFieldBlur(subField.prop)"
                @focus="handleFieldFocus(subField.prop)"
              />
            </el-form-item>
          </template>
        </div>
      </div>
      
      <!-- 普通字段 -->
      <el-form-item
        v-else
        :prop="field.prop"
        :label="field.label"
        :required="field.required"
        :rules="getFieldRules(field)"
        :error="getFieldError(field.prop)"
        :show-message="field.showMessage !== false"
        :inline-message="field.inlineMessage"
        :size="field.size || size"
        :class="getFieldClass(field)"
      >
        <!-- 插槽优先 -->
        <slot 
          :name="field.prop" 
          :field="field" 
          :value="formData[field.prop]"
          :setValue="(value: any) => setFieldValue(field.prop, value)"
        >
          <component
            :is="getFieldComponent(field)"
            v-model="formData[field.prop]"
            v-bind="getFieldProps(field)"
            @change="handleFieldChange(field.prop, $event)"
            @blur="handleFieldBlur(field.prop)"
            @focus="handleFieldFocus(field.prop)"
          >
            <!-- 选择器选项 -->
            <template v-if="field.type === 'select'" #default>
              <el-option
                v-for="option in field.options"
                :key="option.value"
                :label="option.label"
                :value="option.value"
                :disabled="option.disabled"
              />
            </template>
            
            <!-- 单选组选项 -->
            <template v-if="field.type === 'radio-group'" #default>
              <el-radio
                v-for="option in field.options"
                :key="option.value"
                :label="option.value"
                :disabled="option.disabled"
              >
                {{ option.label }}
              </el-radio>
            </template>
            
            <!-- 复选组选项 -->
            <template v-if="field.type === 'checkbox-group'" #default>
              <el-checkbox
                v-for="option in field.options"
                :key="option.value"
                :label="option.value"
                :disabled="option.disabled"
              >
                {{ option.label }}
              </el-checkbox>
            </template>
          </component>
        </slot>
        
        <!-- 字段帮助文本 -->
        <div v-if="field.help" class="field-help">
          {{ field.help }}
        </div>
      </el-form-item>
    </template>
    
    <!-- 表单操作按钮 -->
    <el-form-item v-if="showActions" class="form-actions">
      <slot name="actions" :loading="loading" :validate="validate" :reset="resetForm">
        <el-button
          type="primary"
          :loading="loading"
          @click="handleSubmit"
        >
          {{ submitText }}
        </el-button>
        <el-button @click="handleReset">
          {{ resetText }}
        </el-button>
        <el-button v-if="showCancel" @click="handleCancel">
          {{ cancelText }}
        </el-button>
      </slot>
    </el-form-item>
  </el-form>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import {
  ElForm,
  ElFormItem,
  ElInput,
  ElInputNumber,
  ElSelect,
  ElOption,
  ElRadio,
  ElRadioGroup,
  ElCheckbox,
  ElCheckboxGroup,
  ElSwitch,
  ElDatePicker,
  ElTimePicker,
  ElButton,
  ElUpload,
  ElSlider,
  ElRate,
  ElColorPicker,
  ElCascader,
  ElTransfer
} from 'element-plus'

// 字段类型定义
interface FormField {
  prop: string
  label: string
  type: string
  required?: boolean
  rules?: any[]
  placeholder?: string
  disabled?: boolean
  readonly?: boolean
  size?: 'large' | 'default' | 'small'
  showMessage?: boolean
  inlineMessage?: boolean
  help?: string
  span?: number
  offset?: number
  
  // 特定类型的配置
  options?: Array<{ label: string; value: any; disabled?: boolean }>
  multiple?: boolean
  clearable?: boolean
  filterable?: boolean
  remote?: boolean
  remoteMethod?: (query: string) => void
  
  // 数字输入
  min?: number
  max?: number
  step?: number
  precision?: number
  
  // 日期时间
  format?: string
  valueFormat?: string
  
  // 上传
  action?: string
  accept?: string
  listType?: string
  
  // 其他属性
  [key: string]: any
}

interface Props {
  fields: FormField[]
  modelValue: Record<string, any>
  rules?: Record<string, any>
  labelWidth?: string
  labelPosition?: 'left' | 'right' | 'top'
  size?: 'large' | 'default' | 'small'
  disabled?: boolean
  validateOnRuleChange?: boolean
  hideRequiredAsterisk?: boolean
  showMessage?: boolean
  inlineMessage?: boolean
  statusIcon?: boolean
  showActions?: boolean
  submitText?: string
  resetText?: string
  cancelText?: string
  showCancel?: boolean
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  labelWidth: '120px',
  labelPosition: 'right',
  size: 'default',
  disabled: false,
  validateOnRuleChange: true,
  hideRequiredAsterisk: false,
  showMessage: true,
  inlineMessage: false,
  statusIcon: false,
  showActions: true,
  submitText: '提交',
  resetText: '重置',
  cancelText: '取消',
  showCancel: false,
  loading: false
})

// 事件定义
const emit = defineEmits<{
  'update:modelValue': [value: Record<string, any>]
  'submit': [data: Record<string, any>]
  'reset': []
  'cancel': []
  'field-change': [prop: string, value: any]
  'field-blur': [prop: string]
  'field-focus': [prop: string]
  'validate': [prop: string, valid: boolean, message: string]
}>()

// 响应式数据
const formRef = ref<InstanceType<typeof ElForm>>()
const fieldErrors = ref<Record<string, string>>({})

// 计算属性
const formData = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const formRules = computed(() => {
  const rules: Record<string, any> = { ...props.rules }
  
  // 从字段配置生成规则
  props.fields.forEach(field => {
    if (field.rules) {
      rules[field.prop] = field.rules
    } else if (field.required) {
      rules[field.prop] = [
        { required: true, message: `请输入${field.label}`, trigger: 'blur' }
      ]
    }
  })
  
  return rules
})

// 获取字段组件
const getFieldComponent = (field: FormField) => {
  const componentMap: Record<string, any> = {
    'input': ElInput,
    'textarea': ElInput,
    'password': ElInput,
    'number': ElInputNumber,
    'select': ElSelect,
    'radio': ElRadio,
    'radio-group': ElRadioGroup,
    'checkbox': ElCheckbox,
    'checkbox-group': ElCheckboxGroup,
    'switch': ElSwitch,
    'date': ElDatePicker,
    'datetime': ElDatePicker,
    'time': ElTimePicker,
    'upload': ElUpload,
    'slider': ElSlider,
    'rate': ElRate,
    'color': ElColorPicker,
    'cascader': ElCascader,
    'transfer': ElTransfer
  }
  
  return componentMap[field.type] || ElInput
}

// 获取字段属性
const getFieldProps = (field: FormField) => {
  const baseProps: Record<string, any> = {
    placeholder: field.placeholder || `请输入${field.label}`,
    disabled: field.disabled,
    readonly: field.readonly,
    clearable: field.clearable !== false,
    size: field.size || props.size
  }
  
  // 根据类型添加特定属性
  switch (field.type) {
    case 'textarea':
      baseProps.type = 'textarea'
      baseProps.rows = field.rows || 3
      break
    case 'password':
      baseProps.type = 'password'
      baseProps.showPassword = true
      break
    case 'number':
      baseProps.min = field.min
      baseProps.max = field.max
      baseProps.step = field.step
      baseProps.precision = field.precision
      break
    case 'select':
      baseProps.multiple = field.multiple
      baseProps.filterable = field.filterable
      baseProps.remote = field.remote
      baseProps.remoteMethod = field.remoteMethod
      break
    case 'date':
      baseProps.type = 'date'
      baseProps.format = field.format || 'YYYY-MM-DD'
      baseProps.valueFormat = field.valueFormat || 'YYYY-MM-DD'
      break
    case 'datetime':
      baseProps.type = 'datetime'
      baseProps.format = field.format || 'YYYY-MM-DD HH:mm:ss'
      baseProps.valueFormat = field.valueFormat || 'YYYY-MM-DD HH:mm:ss'
      break
    case 'upload':
      baseProps.action = field.action
      baseProps.accept = field.accept
      baseProps.listType = field.listType
      break
  }
  
  // 合并自定义属性
  return { ...baseProps, ...field.props }
}

// 获取字段规则
const getFieldRules = (field: FormField) => {
  return field.rules || []
}

// 获取字段错误
const getFieldError = (prop: string) => {
  return fieldErrors.value[prop]
}

// 获取字段样式类
const getFieldClass = (field: FormField) => {
  const classes = []
  
  if (field.span) {
    classes.push(`field-span-${field.span}`)
  }
  
  if (field.type) {
    classes.push(`field-type-${field.type}`)
  }
  
  return classes.join(' ')
}

// 设置字段值
const setFieldValue = (prop: string, value: any) => {
  const newData = { ...formData.value }
  newData[prop] = value
  emit('update:modelValue', newData)
}

// 事件处理
const handleFieldChange = (prop: string, value: any) => {
  emit('field-change', prop, value)
}

const handleFieldBlur = (prop: string) => {
  emit('field-blur', prop)
}

const handleFieldFocus = (prop: string) => {
  emit('field-focus', prop)
}

const handleSubmit = async () => {
  const valid = await validate()
  if (valid) {
    emit('submit', formData.value)
  }
}

const handleReset = () => {
  resetForm()
  emit('reset')
}

const handleCancel = () => {
  emit('cancel')
}

// 表单方法
const validate = async (callback?: (valid: boolean) => void) => {
  if (!formRef.value) return false
  
  try {
    await formRef.value.validate()
    callback?.(true)
    return true
  } catch (error) {
    callback?.(false)
    return false
  }
}

const validateField = async (prop: string, callback?: (message: string) => void) => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validateField(prop)
    callback?.('')
  } catch (error: any) {
    callback?.(error.message)
  }
}

const resetForm = () => {
  formRef.value?.resetFields()
  fieldErrors.value = {}
}

const clearValidate = (props?: string | string[]) => {
  formRef.value?.clearValidate(props)
}

const scrollToField = (prop: string) => {
  formRef.value?.scrollToField(prop)
}

// 暴露方法
defineExpose({
  validate,
  validateField,
  resetForm,
  clearValidate,
  scrollToField
})
</script>

<style lang="scss" scoped>
.base-form {
  .form-group {
    margin-bottom: 24px;
    
    .group-title {
      font-size: 16px;
      font-weight: 600;
      color: var(--el-text-color-primary);
      margin-bottom: 16px;
      padding-bottom: 8px;
      border-bottom: 1px solid var(--el-border-color-light);
    }
    
    .group-content {
      padding-left: 16px;
    }
  }
  
  .field-help {
    font-size: 12px;
    color: var(--el-text-color-secondary);
    margin-top: 4px;
    line-height: 1.4;
  }
  
  .form-actions {
    margin-top: 32px;
    text-align: center;
    
    .el-button + .el-button {
      margin-left: 12px;
    }
  }
  
  // 字段跨度样式
  @for $i from 1 through 24 {
    .field-span-#{$i} {
      width: percentage($i / 24);
    }
  }
}
</style>