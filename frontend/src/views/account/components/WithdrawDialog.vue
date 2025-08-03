<template>
  <el-dialog
    v-model="dialogVisible"
    title="出金"
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
      <el-form-item label="可用余额">
        <div class="balance-info">
          <span class="balance-amount">{{ formatCurrency(availableBalance) }}</span>
          <el-button type="text" @click="setMaxAmount">全部提取</el-button>
        </div>
      </el-form-item>

      <el-form-item label="出金金额" prop="amount">
        <el-input
          v-model="form.amount"
          type="number"
          placeholder="请输入出金金额"
          :min="0"
          step="0.01"
        >
          <template #append>USD</template>
        </el-input>
      </el-form-item>

      <el-form-item label="出金方式" prop="method">
        <el-select v-model="form.method" placeholder="请选择出金方式" style="width: 100%">
          <el-option label="银行转账" value="bank_transfer" />
          <el-option label="支付宝" value="alipay" />
          <el-option label="微信支付" value="wechat" />
        </el-select>
      </el-form-item>

      <!-- 银行卡信息 -->
      <div v-if="form.method === 'bank_transfer'">
        <el-form-item label="银行名称" prop="bankName">
          <el-input v-model="form.bankName" placeholder="请输入银行名称" />
        </el-form-item>
        
        <el-form-item label="银行卡号" prop="bankAccount">
          <el-input v-model="form.bankAccount" placeholder="请输入银行卡号" />
        </el-form-item>
        
        <el-form-item label="持卡人姓名" prop="accountHolder">
          <el-input v-model="form.accountHolder" placeholder="请输入持卡人姓名" />
        </el-form-item>
      </div>

      <!-- 支付宝信息 -->
      <div v-if="form.method === 'alipay'">
        <el-form-item label="支付宝账号" prop="alipayAccount">
          <el-input v-model="form.alipayAccount" placeholder="请输入支付宝账号" />
        </el-form-item>
        
        <el-form-item label="真实姓名" prop="realName">
          <el-input v-model="form.realName" placeholder="请输入支付宝实名" />
        </el-form-item>
      </div>

      <!-- 微信信息 -->
      <div v-if="form.method === 'wechat'">
        <el-form-item label="微信号" prop="wechatAccount">
          <el-input v-model="form.wechatAccount" placeholder="请输入微信号" />
        </el-form-item>
        
        <el-form-item label="真实姓名" prop="realName">
          <el-input v-model="form.realName" placeholder="请输入微信实名" />
        </el-form-item>
      </div>

      <el-form-item label="资金密码" prop="fundPassword">
        <el-input
          v-model="form.fundPassword"
          type="password"
          placeholder="请输入资金密码"
          show-password
        />
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

      <!-- 手续费说明 -->
      <div class="fee-info">
        <el-descriptions title="费用说明" :column="1" size="small" border>
          <el-descriptions-item label="出金手续费">
            {{ getFeeInfo(form.method) }}
          </el-descriptions-item>
          <el-descriptions-item label="到账时间">
            {{ getArrivalTime(form.method) }}
          </el-descriptions-item>
          <el-descriptions-item label="单笔限额">
            {{ getLimitInfo(form.method) }}
          </el-descriptions-item>
          <el-descriptions-item label="实际到账">
            {{ getActualAmount() }}
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <!-- 风险提示 -->
      <el-alert
        title="出金提示"
        type="warning"
        :closable="false"
        show-icon
      >
        <template #default>
          <ul class="risk-tips">
            <li>请确保收款信息准确无误，错误信息可能导致资金损失</li>
            <li>出金申请提交后不可撤销，请谨慎操作</li>
            <li>首次出金需要进行身份验证，可能需要额外时间</li>
            <li>大额出金可能需要人工审核，请耐心等待</li>
          </ul>
        </template>
      </el-alert>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button
          type="primary"
          :loading="loading"
          @click="handleSubmit"
        >
          确认出金
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
import { formatCurrency } from '@/utils/format'

interface Props {
  modelValue: boolean
  accountId: number | null
  availableBalance?: number
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'success'): void
}

const props = withDefaults(defineProps<Props>(), {
  availableBalance: 0
})
const emit = defineEmits<Emits>()

// 响应式数据
const formRef = ref<FormInstance>()
const loading = ref(false)

const form = ref({
  amount: '',
  method: '',
  bankName: '',
  bankAccount: '',
  accountHolder: '',
  alipayAccount: '',
  wechatAccount: '',
  realName: '',
  fundPassword: '',
  description: ''
})

// 动态验证规则
const rules = computed<FormRules>(() => {
  const baseRules: FormRules = {
    amount: [
      { required: true, message: '请输入出金金额', trigger: 'blur' },
      { 
        validator: (rule, value, callback) => {
          const amount = parseFloat(value)
          if (isNaN(amount) || amount <= 0) {
            callback(new Error('出金金额必须大于0'))
          } else if (amount < 100) {
            callback(new Error('最小出金金额为100'))
          } else if (amount > props.availableBalance) {
            callback(new Error('出金金额不能超过可用余额'))
          } else {
            callback()
          }
        },
        trigger: 'blur'
      }
    ],
    method: [
      { required: true, message: '请选择出金方式', trigger: 'change' }
    ],
    fundPassword: [
      { required: true, message: '请输入资金密码', trigger: 'blur' },
      { min: 6, message: '资金密码至少6位', trigger: 'blur' }
    ]
  }

  // 根据出金方式添加相应的验证规则
  if (form.value.method === 'bank_transfer') {
    baseRules.bankName = [
      { required: true, message: '请输入银行名称', trigger: 'blur' }
    ]
    baseRules.bankAccount = [
      { required: true, message: '请输入银行卡号', trigger: 'blur' },
      { pattern: /^\d{16,19}$/, message: '请输入正确的银行卡号', trigger: 'blur' }
    ]
    baseRules.accountHolder = [
      { required: true, message: '请输入持卡人姓名', trigger: 'blur' }
    ]
  } else if (form.value.method === 'alipay') {
    baseRules.alipayAccount = [
      { required: true, message: '请输入支付宝账号', trigger: 'blur' }
    ]
    baseRules.realName = [
      { required: true, message: '请输入真实姓名', trigger: 'blur' }
    ]
  } else if (form.value.method === 'wechat') {
    baseRules.wechatAccount = [
      { required: true, message: '请输入微信号', trigger: 'blur' }
    ]
    baseRules.realName = [
      { required: true, message: '请输入真实姓名', trigger: 'blur' }
    ]
  }

  return baseRules
})

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
    bankName: '',
    bankAccount: '',
    accountHolder: '',
    alipayAccount: '',
    wechatAccount: '',
    realName: '',
    fundPassword: '',
    description: ''
  }
  formRef.value?.clearValidate()
}

const setMaxAmount = () => {
  form.value.amount = props.availableBalance.toString()
}

const getFeeInfo = (method: string) => {
  const feeMap = {
    'bank_transfer': '5 USD',
    'alipay': '0.5%',
    'wechat': '0.5%'
  }
  return feeMap[method] || '请选择出金方式'
}

const getArrivalTime = (method: string) => {
  const timeMap = {
    'bank_transfer': '1-3个工作日',
    'alipay': '2小时内',
    'wechat': '2小时内'
  }
  return timeMap[method] || '请选择出金方式'
}

const getLimitInfo = (method: string) => {
  const limitMap = {
    'bank_transfer': '单笔最高50万',
    'alipay': '单笔最高5万',
    'wechat': '单笔最高5万'
  }
  return limitMap[method] || '请选择出金方式'
}

const getActualAmount = () => {
  if (!form.value.amount || !form.value.method) {
    return '请输入金额和选择方式'
  }
  
  const amount = parseFloat(form.value.amount)
  let fee = 0
  
  if (form.value.method === 'bank_transfer') {
    fee = 5
  } else if (form.value.method === 'alipay' || form.value.method === 'wechat') {
    fee = amount * 0.005
  }
  
  const actualAmount = amount - fee
  return `${formatCurrency(actualAmount)} (扣除手续费 ${formatCurrency(fee)})`
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
      `确认出金 ${form.value.amount} USD 吗？\n实际到账：${getActualAmount()}`,
      '确认出金',
      {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: 'warning'
      }
    ).catch(() => false)

    if (!confirmResult) return

    loading.value = true

    const withdrawData = {
      amount: parseFloat(form.value.amount),
      description: form.value.description || `${getMethodName(form.value.method)}出金`,
      reference_id: generateReferenceId()
    }

    await accountApi.withdraw(props.accountId, withdrawData)
    
    ElMessage.success('出金申请提交成功，请等待审核')
    emit('success')
    handleClose()
    
  } catch (error: any) {
    ElMessage.error(error.message || '出金失败')
  } finally {
    loading.value = false
  }
}

const getMethodName = (method: string) => {
  const nameMap = {
    'bank_transfer': '银行转账',
    'alipay': '支付宝',
    'wechat': '微信支付'
  }
  return nameMap[method] || method
}

const generateReferenceId = () => {
  return `WTH${Date.now()}${Math.random().toString(36).substr(2, 6).toUpperCase()}`
}

const handleClose = () => {
  dialogVisible.value = false
}
</script>

<style scoped>
.balance-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.balance-amount {
  font-size: 18px;
  font-weight: 600;
  color: #409EFF;
}

.fee-info {
  margin: 20px 0;
}

.risk-tips {
  margin: 0;
  padding-left: 20px;
}

.risk-tips li {
  margin: 5px 0;
  font-size: 13px;
  line-height: 1.4;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>