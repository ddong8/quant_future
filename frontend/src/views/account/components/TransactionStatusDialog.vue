<template>
  <el-dialog
    v-model="visible"
    title="更新交易状态"
    width="500px"
    :before-close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="statusForm"
      :rules="rules"
      label-width="100px"
    >
      <el-form-item label="交易ID">
        <el-input :value="transaction?.transaction_id" disabled />
      </el-form-item>

      <el-form-item label="当前状态">
        <el-tag :type="TransactionStatusColors[transaction?.status || '']">
          {{ TransactionStatusLabels[transaction?.status || ''] }}
        </el-tag>
      </el-form-item>

      <el-form-item label="新状态" prop="status">
        <el-select
          v-model="statusForm.status"
          placeholder="选择新状态"
          style="width: 100%"
        >
          <el-option
            v-for="status in availableStatuses"
            :key="status"
            :label="TransactionStatusLabels[status]"
            :value="status"
          >
            <span style="float: left">{{ TransactionStatusLabels[status] }}</span>
            <el-tag
              :type="TransactionStatusColors[status]"
              size="small"
              style="float: right; margin-left: 8px"
            >
              {{ status }}
            </el-tag>
          </el-option>
        </el-select>
      </el-form-item>

      <el-form-item label="备注">
        <el-input
          v-model="statusForm.remark"
          type="textarea"
          :rows="3"
          placeholder="请输入状态更新备注（可选）"
        />
      </el-form-item>

      <el-form-item v-if="statusForm.status === 'FAILED'" label="失败原因" prop="failureReason">
        <el-input
          v-model="statusForm.failureReason"
          placeholder="请输入失败原因"
        />
      </el-form-item>

      <el-form-item v-if="statusForm.status === 'CANCELLED'" label="取消原因" prop="cancelReason">
        <el-input
          v-model="statusForm.cancelReason"
          placeholder="请输入取消原因"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button 
          type="primary" 
          :loading="updating"
          @click="handleUpdate"
        >
          {{ updating ? '更新中...' : '确认更新' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import {
  updateTransactionStatus,
  type Transaction,
  TransactionStatusLabels,
  TransactionStatusColors
} from '@/api/transaction'

interface Props {
  modelValue: boolean
  transaction: Transaction | null
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'updated'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 响应式数据
const formRef = ref<FormInstance>()
const updating = ref(false)

// 状态表单
const statusForm = reactive({
  status: '',
  remark: '',
  failureReason: '',
  cancelReason: ''
})

// 表单验证规则
const rules: FormRules = {
  status: [
    { required: true, message: '请选择新状态', trigger: 'change' }
  ],
  failureReason: [
    { required: true, message: '请输入失败原因', trigger: 'blur' }
  ],
  cancelReason: [
    { required: true, message: '请输入取消原因', trigger: 'blur' }
  ]
}

// 计算属性
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// 可用状态列表
const availableStatuses = computed(() => {
  if (!props.transaction) return []
  
  const currentStatus = props.transaction.status
  const statusTransitions: Record<string, string[]> = {
    'PENDING': ['PROCESSING', 'COMPLETED', 'FAILED', 'CANCELLED'],
    'PROCESSING': ['COMPLETED', 'FAILED', 'CANCELLED'],
    'COMPLETED': [], // 已完成的交易不能更改状态
    'FAILED': ['PENDING'], // 失败的交易可以重新处理
    'CANCELLED': ['PENDING'] // 取消的交易可以重新处理
  }
  
  return statusTransitions[currentStatus] || []
})

// 方法
const handleClose = () => {
  resetForm()
  visible.value = false
}

const resetForm = () => {
  statusForm.status = ''
  statusForm.remark = ''
  statusForm.failureReason = ''
  statusForm.cancelReason = ''
}

const handleUpdate = async () => {
  if (!formRef.value || !props.transaction) return

  try {
    await formRef.value.validate()
    
    updating.value = true

    // 构建元数据
    const metadata: Record<string, any> = {
      updated_by: 'user',
      updated_at: new Date().toISOString(),
      previous_status: props.transaction.status
    }

    if (statusForm.remark) {
      metadata.remark = statusForm.remark
    }

    if (statusForm.status === 'FAILED' && statusForm.failureReason) {
      metadata.failure_reason = statusForm.failureReason
    }

    if (statusForm.status === 'CANCELLED' && statusForm.cancelReason) {
      metadata.cancel_reason = statusForm.cancelReason
    }

    // 更新状态
    await updateTransactionStatus(
      props.transaction.transaction_id,
      statusForm.status,
      metadata
    )

    ElMessage.success('状态更新成功')
    emit('updated')
    handleClose()

  } catch (error: any) {
    console.error('更新状态失败:', error)
    ElMessage.error(error.message || '更新状态失败')
  } finally {
    updating.value = false
  }
}

// 监听对话框打开
watch(visible, (newVisible) => {
  if (newVisible && props.transaction) {
    resetForm()
  }
})
</script>

<style scoped>
.dialog-footer {
  text-align: right;
}
</style>