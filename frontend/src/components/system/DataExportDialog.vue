<template>
  <el-dialog
    v-model="visible"
    title="数据导出"
    width="600px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="120px"
    >
      <el-form-item label="导出类型" prop="export_type">
        <el-select v-model="form.export_type" placeholder="请选择导出类型" style="width: 100%">
          <el-option label="订单数据" value="orders" />
          <el-option label="持仓数据" value="positions" />
          <el-option label="交易记录" value="transactions" />
          <el-option label="策略数据" value="strategies" />
          <el-option label="回测数据" value="backtests" />
          <el-option label="风险报告" value="risk_reports" />
          <el-option label="用户数据" value="user_data" />
          <el-option label="系统日志" value="system_logs" v-if="hasSystemPermission" />
          <el-option label="完整备份" value="full_backup" v-if="hasSystemPermission" />
        </el-select>
      </el-form-item>

      <el-form-item label="导出格式" prop="format">
        <el-select v-model="form.format" placeholder="请选择导出格式" style="width: 100%">
          <el-option label="CSV" value="csv" />
          <el-option label="Excel" value="excel" />
          <el-option label="JSON" value="json" />
          <el-option label="PDF" value="pdf" v-if="form.export_type === 'risk_reports'" />
        </el-select>
      </el-form-item>

      <el-form-item label="时间范围">
        <el-date-picker
          v-model="dateRange"
          type="datetimerange"
          range-separator="至"
          start-placeholder="开始时间"
          end-placeholder="结束时间"
          format="YYYY-MM-DD HH:mm:ss"
          value-format="YYYY-MM-DD HH:mm:ss"
          style="width: 100%"
        />
      </el-form-item>

      <el-form-item label="字段设置">
        <el-tabs v-model="fieldTab" type="card">
          <el-tab-pane label="包含字段" name="include">
            <el-select
              v-model="form.include_fields"
              multiple
              placeholder="选择要包含的字段（不选则包含所有）"
              style="width: 100%"
            >
              <el-option
                v-for="field in availableFields"
                :key="field.value"
                :label="field.label"
                :value="field.value"
              />
            </el-select>
          </el-tab-pane>
          <el-tab-pane label="排除字段" name="exclude">
            <el-select
              v-model="form.exclude_fields"
              multiple
              placeholder="选择要排除的字段"
              style="width: 100%"
            >
              <el-option
                v-for="field in availableFields"
                :key="field.value"
                :label="field.label"
                :value="field.value"
              />
            </el-select>
          </el-tab-pane>
        </el-tabs>
      </el-form-item>

      <el-form-item label="高级选项">
        <el-checkbox v-model="form.compress">压缩文件</el-checkbox>
        <el-checkbox v-model="form.password_protect" style="margin-left: 20px">密码保护</el-checkbox>
      </el-form-item>

      <el-form-item v-if="form.password_protect" label="保护密码" prop="password">
        <el-input
          v-model="form.password"
          type="password"
          placeholder="请输入保护密码"
          show-password
        />
      </el-form-item>

      <el-form-item label="筛选条件" v-if="showFilters">
        <el-input
          v-model="filtersJson"
          type="textarea"
          :rows="3"
          placeholder="请输入JSON格式的筛选条件"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="loading">
          开始导出
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { dataExportApi, type DataExportRequest } from '@/api/dataExport'

interface Props {
  modelValue: boolean
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 响应式数据
const formRef = ref<FormInstance>()
const loading = ref(false)
const fieldTab = ref('include')
const dateRange = ref<[string, string] | null>(null)
const filtersJson = ref('')

// 表单数据
const form = ref<DataExportRequest>({
  export_type: 'orders',
  format: 'csv',
  compress: false,
  password_protect: false
})

// 计算属性
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const hasSystemPermission = computed(() => {
  // 这里应该检查用户权限
  return true // 暂时返回true
})

const showFilters = computed(() => {
  return ['orders', 'positions', 'transactions'].includes(form.value.export_type)
})

const availableFields = computed(() => {
  const fieldMap: Record<string, Array<{label: string, value: string}>> = {
    orders: [
      { label: 'ID', value: 'id' },
      { label: '用户ID', value: 'user_id' },
      { label: '标的代码', value: 'symbol' },
      { label: '订单类型', value: 'order_type' },
      { label: '方向', value: 'side' },
      { label: '数量', value: 'quantity' },
      { label: '价格', value: 'price' },
      { label: '状态', value: 'status' },
      { label: '创建时间', value: 'created_at' },
      { label: '更新时间', value: 'updated_at' }
    ],
    positions: [
      { label: 'ID', value: 'id' },
      { label: '用户ID', value: 'user_id' },
      { label: '标的代码', value: 'symbol' },
      { label: '持仓数量', value: 'quantity' },
      { label: '平均成本', value: 'avg_cost' },
      { label: '当前价格', value: 'current_price' },
      { label: '未实现盈亏', value: 'unrealized_pnl' },
      { label: '创建时间', value: 'created_at' }
    ],
    transactions: [
      { label: 'ID', value: 'id' },
      { label: '用户ID', value: 'user_id' },
      { label: '类型', value: 'type' },
      { label: '金额', value: 'amount' },
      { label: '余额', value: 'balance' },
      { label: '描述', value: 'description' },
      { label: '创建时间', value: 'created_at' }
    ]
  }
  
  return fieldMap[form.value.export_type] || []
})

// 表单验证规则
const rules: FormRules = {
  export_type: [
    { required: true, message: '请选择导出类型', trigger: 'change' }
  ],
  format: [
    { required: true, message: '请选择导出格式', trigger: 'change' }
  ],
  password: [
    { required: true, message: '请输入保护密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' }
  ]
}

// 监听导出类型变化
watch(() => form.value.export_type, (newType) => {
  // 重置字段选择
  form.value.include_fields = undefined
  form.value.exclude_fields = undefined
  
  // 重置格式选择
  if (newType === 'risk_reports') {
    form.value.format = 'pdf'
  } else {
    form.value.format = 'csv'
  }
})

// 方法
const handleClose = () => {
  visible.value = false
  resetForm()
}

const resetForm = () => {
  form.value = {
    export_type: 'orders',
    format: 'csv',
    compress: false,
    password_protect: false
  }
  dateRange.value = null
  filtersJson.value = ''
  formRef.value?.resetFields()
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    
    loading.value = true
    
    // 准备请求数据
    const requestData: DataExportRequest = {
      ...form.value
    }
    
    // 设置时间范围
    if (dateRange.value) {
      requestData.start_date = dateRange.value[0]
      requestData.end_date = dateRange.value[1]
    }
    
    // 解析筛选条件
    if (filtersJson.value.trim()) {
      try {
        requestData.filters = JSON.parse(filtersJson.value)
      } catch (error) {
        ElMessage.error('筛选条件格式错误，请输入有效的JSON')
        return
      }
    }
    
    // 创建导出任务
    await dataExportApi.createExportTask(requestData)
    
    ElMessage.success('导出任务已创建，请在任务列表中查看进度')
    emit('success')
    handleClose()
    
  } catch (error: any) {
    ElMessage.error(error.message || '创建导出任务失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.dialog-footer {
  text-align: right;
}

:deep(.el-tabs__content) {
  padding-top: 10px;
}
</style>