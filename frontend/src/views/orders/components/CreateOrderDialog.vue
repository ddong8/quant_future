<template>
  <el-dialog
    v-model="visible"
    title="创建订单"
    width="800px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="100px"
      @submit.prevent
    >
      <el-row :gutter="20">
        <!-- 基本信息 -->
        <el-col :span="12">
          <el-form-item label="交易标的" prop="symbol" required>
            <el-input
              v-model="form.symbol"
              placeholder="请输入标的代码"
              @blur="handleSymbolBlur"
            />
          </el-form-item>
        </el-col>
        
        <el-col :span="12">
          <el-form-item label="订单方向" prop="side" required>
            <el-radio-group v-model="form.side">
              <el-radio-button label="buy">买入</el-radio-button>
              <el-radio-button label="sell">卖出</el-radio-button>
            </el-radio-group>
          </el-form-item>
        </el-col>

        <el-col :span="12">
          <el-form-item label="订单类型" prop="order_type" required>
            <el-select
              v-model="form.order_type"
              placeholder="选择订单类型"
              @change="handleOrderTypeChange"
            >
              <el-option
                v-for="type in orderTypes"
                :key="type.value"
                :label="type.label"
                :value="type.value"
              />
            </el-select>
          </el-form-item>
        </el-col>

        <el-col :span="12">
          <el-form-item label="数量" prop="quantity" required>
            <el-input-number
              v-model="form.quantity"
              :min="0"
              :precision="2"
              placeholder="请输入数量"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>

        <!-- 价格设置 -->
        <el-col :span="12" v-if="needPrice">
          <el-form-item label="价格" prop="price" :required="needPrice">
            <el-input-number
              v-model="form.price"
              :min="0"
              :precision="2"
              placeholder="请输入价格"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>

        <el-col :span="12" v-if="needStopPrice">
          <el-form-item label="止损价格" prop="stop_price" :required="needStopPrice">
            <el-input-number
              v-model="form.stop_price"
              :min="0"
              :precision="2"
              placeholder="请输入止损价格"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>

        <!-- 高级设置 -->
        <el-col :span="24">
          <el-divider content-position="left">高级设置</el-divider>
        </el-col>

        <el-col :span="12">
          <el-form-item label="有效期">
            <el-select v-model="form.time_in_force">
              <el-option label="当日有效" value="day" />
              <el-option label="撤销前有效" value="gtc" />
              <el-option label="立即成交或取消" value="ioc" />
              <el-option label="全部成交或取消" value="fok" />
              <el-option label="指定日期前有效" value="gtd" />
            </el-select>
          </el-form-item>
        </el-col>

        <el-col :span="12">
          <el-form-item label="优先级">
            <el-select v-model="form.priority">
              <el-option label="低" value="low" />
              <el-option label="普通" value="normal" />
              <el-option label="高" value="high" />
              <el-option label="紧急" value="urgent" />
            </el-select>
          </el-form-item>
        </el-col>

        <el-col :span="12" v-if="form.time_in_force === 'gtd'">
          <el-form-item label="过期时间" prop="expire_time">
            <el-date-picker
              v-model="form.expire_time"
              type="datetime"
              placeholder="选择过期时间"
              format="YYYY-MM-DD HH:mm:ss"
              value-format="YYYY-MM-DDTHH:mm:ss"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>

        <el-col :span="12" v-if="form.order_type === 'iceberg'">
          <el-form-item label="显示数量" prop="iceberg_quantity">
            <el-input-number
              v-model="form.iceberg_quantity"
              :min="0"
              :max="form.quantity"
              :precision="2"
              placeholder="冰山单显示数量"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>

        <el-col :span="12" v-if="form.order_type === 'trailing_stop'">
          <el-form-item label="跟踪金额">
            <el-input-number
              v-model="form.trailing_amount"
              :min="0"
              :precision="2"
              placeholder="跟踪止损金额"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>

        <el-col :span="12" v-if="form.order_type === 'trailing_stop'">
          <el-form-item label="跟踪百分比">
            <el-input-number
              v-model="form.trailing_percent"
              :min="0"
              :max="100"
              :precision="2"
              placeholder="跟踪止损百分比"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>

        <!-- 关联信息 -->
        <el-col :span="24">
          <el-divider content-position="left">关联信息</el-divider>
        </el-col>

        <el-col :span="12">
          <el-form-item label="关联策略">
            <el-select
              v-model="form.strategy_id"
              placeholder="选择策略"
              clearable
              filterable
            >
              <el-option
                v-for="strategy in strategies"
                :key="strategy.id"
                :label="strategy.name"
                :value="strategy.id"
              />
            </el-select>
          </el-form-item>
        </el-col>

        <el-col :span="12">
          <el-form-item label="券商账户">
            <el-input
              v-model="form.account_id"
              placeholder="请输入账户ID"
            />
          </el-form-item>
        </el-col>

        <el-col :span="24">
          <el-form-item label="标签">
            <el-select
              v-model="form.tags"
              multiple
              filterable
              allow-create
              placeholder="选择或输入标签"
              style="width: 100%"
            >
              <el-option
                v-for="tag in availableTags"
                :key="tag"
                :label="tag"
                :value="tag"
              />
            </el-select>
          </el-form-item>
        </el-col>

        <el-col :span="24">
          <el-form-item label="备注">
            <el-input
              v-model="form.notes"
              type="textarea"
              :rows="3"
              placeholder="请输入备注信息"
            />
          </el-form-item>
        </el-col>
      </el-row>
    </el-form>

    <!-- 风险检查结果 -->
    <div v-if="riskCheckResult" class="risk-check-result">
      <el-divider content-position="left">风险检查</el-divider>
      <el-alert
        :type="riskCheckResult.passed ? 'success' : 'error'"
        :title="riskCheckResult.passed ? '风险检查通过' : '风险检查未通过'"
        :closable="false"
      >
        <div v-if="riskCheckResult.warnings.length > 0">
          <p><strong>警告:</strong></p>
          <ul>
            <li v-for="warning in riskCheckResult.warnings" :key="warning">
              {{ warning }}
            </li>
          </ul>
        </div>
        <div v-if="riskCheckResult.errors.length > 0">
          <p><strong>错误:</strong></p>
          <ul>
            <li v-for="error in riskCheckResult.errors" :key="error">
              {{ error }}
            </li>
          </ul>
        </div>
        <div v-if="riskCheckResult.suggestions.length > 0">
          <p><strong>建议:</strong></p>
          <ul>
            <li v-for="suggestion in riskCheckResult.suggestions" :key="suggestion">
              {{ suggestion }}
            </li>
          </ul>
        </div>
      </el-alert>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button @click="handleRiskCheck" :loading="riskChecking">
          风险检查
        </el-button>
        <el-button
          type="primary"
          @click="handleSubmit"
          :loading="submitting"
          :disabled="riskCheckResult && !riskCheckResult.passed"
        >
          创建订单
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { orderApi, OrderType, OrderSide, OrderTimeInForce, OrderPriority, type OrderCreate, type OrderRiskCheckResult } from '@/api/order'
import { strategyApi } from '@/api/strategy'

// Props
const props = defineProps<{
  modelValue: boolean
}>()

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  success: []
}>()

// 响应式数据
const formRef = ref<FormInstance>()
const submitting = ref(false)
const riskChecking = ref(false)
const strategies = ref<any[]>([])
const availableTags = ref<string[]>([])
const riskCheckResult = ref<OrderRiskCheckResult | null>(null)

// 表单数据
const form = reactive<OrderCreate>({
  symbol: '',
  order_type: OrderType.LIMIT,
  side: OrderSide.BUY,
  quantity: 0,
  price: undefined,
  stop_price: undefined,
  time_in_force: OrderTimeInForce.DAY,
  priority: OrderPriority.NORMAL,
  iceberg_quantity: undefined,
  trailing_amount: undefined,
  trailing_percent: undefined,
  expire_time: undefined,
  strategy_id: undefined,
  account_id: undefined,
  tags: [],
  notes: undefined
})

// 订单类型选项
const orderTypes = [
  { label: '市价单', value: OrderType.MARKET },
  { label: '限价单', value: OrderType.LIMIT },
  { label: '止损单', value: OrderType.STOP },
  { label: '止损限价单', value: OrderType.STOP_LIMIT },
  { label: '跟踪止损单', value: OrderType.TRAILING_STOP },
  { label: '冰山单', value: OrderType.ICEBERG }
]

// 计算属性
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const needPrice = computed(() => {
  return [OrderType.LIMIT, OrderType.STOP_LIMIT].includes(form.order_type)
})

const needStopPrice = computed(() => {
  return [OrderType.STOP, OrderType.STOP_LIMIT, OrderType.TRAILING_STOP].includes(form.order_type)
})

// 表单验证规则
const rules: FormRules = {
  symbol: [
    { required: true, message: '请输入交易标的', trigger: 'blur' }
  ],
  side: [
    { required: true, message: '请选择订单方向', trigger: 'change' }
  ],
  order_type: [
    { required: true, message: '请选择订单类型', trigger: 'change' }
  ],
  quantity: [
    { required: true, message: '请输入数量', trigger: 'blur' },
    { type: 'number', min: 0.01, message: '数量必须大于0', trigger: 'blur' }
  ],
  price: [
    {
      validator: (rule, value, callback) => {
        if (needPrice.value && (!value || value <= 0)) {
          callback(new Error('请输入有效的价格'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ],
  stop_price: [
    {
      validator: (rule, value, callback) => {
        if (needStopPrice.value && (!value || value <= 0)) {
          callback(new Error('请输入有效的止损价格'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ],
  iceberg_quantity: [
    {
      validator: (rule, value, callback) => {
        if (form.order_type === OrderType.ICEBERG) {
          if (!value || value <= 0) {
            callback(new Error('请输入冰山单显示数量'))
          } else if (value >= form.quantity) {
            callback(new Error('显示数量必须小于总数量'))
          } else {
            callback()
          }
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ],
  expire_time: [
    {
      validator: (rule, value, callback) => {
        if (form.time_in_force === OrderTimeInForce.GTD && !value) {
          callback(new Error('GTD订单必须指定过期时间'))
        } else {
          callback()
        }
      },
      trigger: 'change'
    }
  ]
}

// 监听订单类型变化
const handleOrderTypeChange = () => {
  // 清除风险检查结果
  riskCheckResult.value = null
  
  // 根据订单类型清除不需要的字段
  if (form.order_type === OrderType.MARKET) {
    form.price = undefined
  }
  if (form.order_type !== OrderType.ICEBERG) {
    form.iceberg_quantity = undefined
  }
  if (form.order_type !== OrderType.TRAILING_STOP) {
    form.trailing_amount = undefined
    form.trailing_percent = undefined
  }
}

// 处理标的输入
const handleSymbolBlur = () => {
  if (form.symbol) {
    form.symbol = form.symbol.toUpperCase()
    // 清除风险检查结果
    riskCheckResult.value = null
  }
}

// 风险检查
const handleRiskCheck = async () => {
  try {
    await formRef.value?.validate()
    
    riskChecking.value = true
    const response = await orderApi.checkOrderRisk({
      symbol: form.symbol,
      side: form.side,
      quantity: form.quantity,
      price: form.price,
      order_type: form.order_type,
      strategy_id: form.strategy_id
    })
    
    riskCheckResult.value = response.data
    
    if (response.data.passed) {
      ElMessage.success('风险检查通过')
    } else {
      ElMessage.warning('风险检查未通过，请查看详细信息')
    }
  } catch (error: any) {
    if (error.errors) {
      // 表单验证错误
      return
    }
    console.error('风险检查失败:', error)
    ElMessage.error('风险检查失败')
  } finally {
    riskChecking.value = false
  }
}

// 提交表单
const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
    
    // 如果没有进行风险检查，先进行风险检查
    if (!riskCheckResult.value) {
      await handleRiskCheck()
      return
    }
    
    // 如果风险检查未通过，不允许提交
    if (!riskCheckResult.value.passed) {
      ElMessage.error('风险检查未通过，无法创建订单')
      return
    }
    
    submitting.value = true
    await orderApi.createOrder(form)
    
    ElMessage.success('订单创建成功')
    emit('success')
    handleClose()
  } catch (error) {
    console.error('创建订单失败:', error)
    ElMessage.error('创建订单失败')
  } finally {
    submitting.value = false
  }
}

// 关闭对话框
const handleClose = () => {
  visible.value = false
  resetForm()
}

// 重置表单
const resetForm = () => {
  formRef.value?.resetFields()
  riskCheckResult.value = null
  Object.assign(form, {
    symbol: '',
    order_type: OrderType.LIMIT,
    side: OrderSide.BUY,
    quantity: 0,
    price: undefined,
    stop_price: undefined,
    time_in_force: OrderTimeInForce.DAY,
    priority: OrderPriority.NORMAL,
    iceberg_quantity: undefined,
    trailing_amount: undefined,
    trailing_percent: undefined,
    expire_time: undefined,
    strategy_id: undefined,
    account_id: undefined,
    tags: [],
    notes: undefined
  })
}

// 加载策略列表
const loadStrategies = async () => {
  try {
    const response = await strategyApi.getStrategies({ page_size: 100 })
    strategies.value = response.data.data || []
  } catch (error) {
    console.error('加载策略列表失败:', error)
  }
}

// 加载可用标签
const loadAvailableTags = () => {
  availableTags.value = [
    '手动交易',
    '策略交易',
    '测试',
    '紧急',
    '重要',
    '日内',
    '隔夜'
  ]
}

// 监听表单变化，清除风险检查结果
watch([() => form.symbol, () => form.side, () => form.quantity, () => form.price, () => form.order_type], () => {
  riskCheckResult.value = null
})

// 初始化
onMounted(() => {
  loadStrategies()
  loadAvailableTags()
})
</script>

<style scoped>
.risk-check-result {
  margin-top: 20px;
}

.risk-check-result ul {
  margin: 8px 0;
  padding-left: 20px;
}

.risk-check-result li {
  margin: 4px 0;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
}

:deep(.el-radio-button__inner) {
  padding: 8px 15px;
}
</style>