<template>
  <el-dialog
    v-model="dialogVisible"
    title="入金"
    width="500px"
    :before-close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="100px"
      @submit.prevent="handleSubmit"
    >
      <el-form-item label="入金金额" prop="amount">
        <el-input
          v-model="form.amount"
          type="number"
          placeholder="请输入入金金额"
          :min="0"
          step="0.01"
        >
          <template #append>USD</template>
        </el-input>
      </el-form-item>

      <el-form-item label="入金方式" prop="method">
        <el-select v-model="form.method" placeholder="请选择入金方式" style="width: 100%">
          <el-option label="银行转账" value="bank_transfer" />
          <el-option label="支付宝" value="alipay" />
          <el-option label="微信支付" value="wechat" />
          <el-option label="信用卡" value="credit_card" />
        </el-select>
      </el-form-item>

      <el-form-item label="备注" prop="description">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="3"
          placeholder="请输入备注信息（可选）"
          maxlength="200"
          show-word-limit
        />
      </el-form-item>

      <!-- 银行转账信息 -->
      <div v-if="form.method === 'bank_transfer'" class="transfer-info">
        <el-alert
          title="银行转账信息"
          type="info"
          :closable="false"
          show-icon
        >
          <template #default>
            <div class="bank-info">
              <p><strong>收款银行：</strong>中国工商银行</p>
              <p><strong>收款账号：</strong>1234 5678 9012 3456</p>
              <p><strong>收款人：</strong>交易平台有限公司</p>
              <p><strong>备注：</strong>请在转账备注中填写您的账户号</p>
            </div>
          </template>
        </el-alert>
      </div>

      <!-- 手续费说明 -->
      <div class="fee-info">
        <el-descriptions title="费用说明" :column="1" size="small" border>
          <el-descriptions-item label="入金手续费">
            {{ getFeeInfo(form.method) }}
          </el-descriptions-item>
          <el-descriptions-item label="到账时间">
            {{ getArrivalTime(form.method) }}
          </el-descriptions-item>
          <el-descriptions-item label="单笔限额">
            {{ getLimitInfo(form.method) }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button
          type="primary"
          :loading="loading"
          @click="handleSubmit"
        >
          确认入金
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { accountApi } from '@/api/account'

interface Props {
  modelValue: boolean
  accountId: number | null
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

const form = ref({
  amount: '',
  method: '',
  description: ''
})

// 表单验证规则
const rules: FormRules = {
  amount: [
    { required: true, message: '请输入入金金额', trigger: 'blur' },
    { 
      validator: (rule, value, callback) => {
        const amount = parseFloat(value)
        if (isNaN(amount) || amount <= 0) {
          callback(new Error('入金金额必须大于0'))
        } else if (amount < 100) {
          callback(new Error('最小入金金额为100'))
        } else if (amount > 1000000) {
          callback(new Error('单笔入金金额不能超过100万'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ],
  method: [
    { required: true, message: '请选择入金方式', trigger: 'change' }
  ]
}

// 计算属性
const dialogVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// 监听对话框显示状态
watch(dialogVisible, (visible) => {
  if (visible) {
    resetForm()
  }
})

// 方法
const resetForm = () => {
  form.value = {
    amount: '',
    method: '',
    description: ''
  }
  formRef.value?.clearValidate()
}

const getFeeInfo = (method: string) => {
  const feeMap = {
    'bank_transfer': '免费',
    'alipay': '0.1%',
    'wechat': '0.1%',
    'credit_card': '2.5%'
  }
  return feeMap[method] || '请选择入金方式'
}

const getArrivalTime = (method: string) => {
  const timeMap = {
    'bank_transfer': '1-3个工作日',
    'alipay': '实时到账',
    'wechat': '实时到账',
    'credit_card': '实时到账'
  }
  return timeMap[method] || '请选择入金方式'
}

const getLimitInfo = (method: string) => {
  const limitMap = {
    'bank_transfer': '无限制',
    'alipay': '单笔最高5万',
    'wechat': '单笔最高5万',
    'credit_card': '单笔最高10万'
  }
  return limitMap[method] || '请选择入金方式'
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    const valid = await formRef.value.validate()
    if (!valid) return
    
    if (!props.accountId) {
      ElMessage.error('请先选择账户')
      return
    }

    // 确认对话框
    const confirmResult = await ElMessageBox.confirm(
      `确认入金 ${form.value.amount} USD 吗？`,
      '确认入金',
      {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: 'warning'
      }
    ).catch(() => false)

    if (!confirmResult) return

    loading.value = true

    const depositData = {
      amount: parseFloat(form.value.amount),
      description: form.value.description || `${getMethodName(form.value.method)}入金`,
      reference_id: generateReferenceId()
    }

    await accountApi.deposit(props.accountId, depositData)
    
    ElMessage.success('入金申请提交成功')
    emit('success')
    handleClose()
    
  } catch (error: any) {
    ElMessage.error(error.message || '入金失败')
  } finally {
    loading.value = false
  }
}

const getMethodName = (method: string) => {
  const nameMap = {
    'bank_transfer': '银行转账',
    'alipay': '支付宝',
    'wechat': '微信支付',
    'credit_card': '信用卡'
  }
  return nameMap[method] || method
}

const generateReferenceId = () => {
  return `DEP${Date.now()}${Math.random().toString(36).substr(2, 6).toUpperCase()}`
}

const handleClose = () => {
  dialogVisible.value = false
}
</script>

<style scoped>
.transfer-info {
  margin: 20px 0;
}

.bank-info p {
  margin: 5px 0;
  font-size: 14px;
}

.fee-info {
  margin-top: 20px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>