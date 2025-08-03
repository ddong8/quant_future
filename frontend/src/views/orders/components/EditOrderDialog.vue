<template>
  <el-dialog
    v-model="visible"
    title="编辑订单"
    width="600px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="6" animated />
    </div>

    <el-form
      v-else-if="order"
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="100px"
      @submit.prevent
    >
      <!-- 只读信息 -->
      <el-card class="readonly-info">
        <template #header>
          <span>订单信息</span>
        </template>
        <el-row :gutter="20">
          <el-col :span="8">
            <div class="info-item">
              <label>标的:</label>
              <span class="symbol">{{ order.symbol }}</span>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="info-item">
              <label>方向:</label>
              <el-tag
                :type="order.side === 'buy' ? 'success' : 'danger'"
                size="small"
              >
                {{ order.side === 'buy' ? '买入' : '卖出' }}
              </el-tag>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="info-item">
              <label>类型:</label>
              <span>{{ getOrderTypeLabel(order.order_type) }}</span>
            </div>
          </el-col>
        </el-row>
      </el-card>

      <!-- 可编辑字段 -->
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="数量" prop="quantity" required>
            <el-input-number
              v-model="form.quantity"
              :min="0"
              :precision="2"
              placeholder="请输入数量"
              style="width: 100%"
            />
            <div class="field-hint">
              原数量: {{ formatNumber(order.quantity) }}
            </div>
          </el-form-item>
        </el-col>

        <el-col :span="12" v-if="needPrice">
          <el-form-item label="价格" prop="price" :required="needPrice">
            <el-input-number
              v-model="form.price"
              :min="0"
              :precision="2"
              placeholder="请输入价格"
              style="width: 100%"
            />
            <div class="field-hint" v-if="order.price">
              原价格: {{ formatPrice(order.price) }}
            </div>
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
            <div class="field-hint" v-if="order.stop_price">
              原止损价格: {{ formatPrice(order.stop_price) }}
            </div>
          </el-form-item>
        </el-col>

        <el-col :span="12">
          <el-form-item label="有效期">
            <el-select v-model="form.time_in_force" style="width: 100%">
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
            <el-select v-model="form.priority" style="width: 100%">
              <el-option label="低" value="low" />
              <el-option label="普通" value="normal" />
              <el-option label="高" value="high" />
              <el-option label="紧急" value="urgent" />
            </el-select>
          </el-form-item>
        </el-col>

        <el-col :span="24" v-if="form.time_in_force === 'gtd'">
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

      <!-- 修改限制提示 -->
      <el-alert
        type="info"
        :closable="false"
        show-icon
      >
        <template #title>
          修改说明
        </template>
        <ul class="modification-rules">
          <li>只能修改未成交或部分成交的订单</li>
          <li>不能修改订单的标的、方向和类型</li>
          <li>修改数量时，新数量不能小于已成交数量</li>
          <li>修改后的订单将重新进行风险检查</li>
        </ul>
      </el-alert>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button
          type="primary"
          @click="handleSubmit"
          :loading="submitting"
          :disabled="!hasChanges"
        >
          保存修改
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { orderApi, OrderTimeInForce, OrderPriority, type Order, type OrderUpdate } from '@/api/order'
import { formatNumber, formatPrice } from '@/utils/format'

// Props
const props = defineProps<{
  modelValue: boolean
  orderId?: number
}>()

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  success: []
}>()

// 响应式数据
const formRef = ref<FormInstance>()
const loading = ref(false)
const submitting = ref(false)
const order = ref<Order | null>(null)
const availableTags = ref<string[]>([])

// 表单数据
const form = reactive<OrderUpdate>({
  quantity: undefined,
  price: undefined,
  stop_price: undefined,
  time_in_force: undefined,
  priority: undefined,
  expire_time: undefined,
  tags: undefined,
  notes: undefined
})

// 计算属性
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const needPrice = computed(() => {
  if (!order.value) return false
  return ['limit', 'stop_limit'].includes(order.value.order_type)
})

const needStopPrice = computed(() => {
  if (!order.value) return false
  return ['stop', 'stop_limit', 'trailing_stop'].includes(order.value.order_type)
})

const hasChanges = computed(() => {
  if (!order.value) return false
  
  return (
    form.quantity !== order.value.quantity ||
    form.price !== order.value.price ||
    form.stop_price !== order.value.stop_price ||
    form.time_in_force !== order.value.time_in_force ||
    form.priority !== order.value.priority ||
    form.expire_time !== order.value.expire_time ||
    JSON.stringify(form.tags) !== JSON.stringify(order.value.tags) ||
    form.notes !== order.value.notes
  )
})

// 表单验证规则
const rules: FormRules = {
  quantity: [
    { required: true, message: '请输入数量', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (!order.value) {
          callback()
          return
        }
        if (value <= 0) {
          callback(new Error('数量必须大于0'))
        } else if (value < order.value.filled_quantity) {
          callback(new Error(`数量不能小于已成交数量 ${formatNumber(order.value.filled_quantity)}`))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
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

// 加载订单详情
const loadOrderDetail = async () => {
  if (!props.orderId) return

  try {
    loading.value = true
    const response = await orderApi.getOrder(props.orderId)
    order.value = response.data
    
    // 初始化表单数据
    Object.assign(form, {
      quantity: order.value.quantity,
      price: order.value.price,
      stop_price: order.value.stop_price,
      time_in_force: order.value.time_in_force,
      priority: order.value.priority,
      expire_time: order.value.expire_time,
      tags: [...order.value.tags],
      notes: order.value.notes
    })
  } catch (error) {
    console.error('加载订单详情失败:', error)
    ElMessage.error('加载订单详情失败')
  } finally {
    loading.value = false
  }
}

// 获取订单类型标签
const getOrderTypeLabel = (type: string) => {
  const typeMap: Record<string, string> = {
    market: '市价单',
    limit: '限价单',
    stop: '止损单',
    stop_limit: '止损限价单',
    trailing_stop: '跟踪止损单',
    iceberg: '冰山单',
    twap: 'TWAP单',
    vwap: 'VWAP单'
  }
  return typeMap[type] || type
}

// 提交表单
const handleSubmit = async () => {
  if (!order.value) return

  try {
    await formRef.value?.validate()
    
    submitting.value = true
    
    // 只提交有变化的字段
    const updateData: OrderUpdate = {}
    if (form.quantity !== order.value.quantity) updateData.quantity = form.quantity
    if (form.price !== order.value.price) updateData.price = form.price
    if (form.stop_price !== order.value.stop_price) updateData.stop_price = form.stop_price
    if (form.time_in_force !== order.value.time_in_force) updateData.time_in_force = form.time_in_force
    if (form.priority !== order.value.priority) updateData.priority = form.priority
    if (form.expire_time !== order.value.expire_time) updateData.expire_time = form.expire_time
    if (JSON.stringify(form.tags) !== JSON.stringify(order.value.tags)) updateData.tags = form.tags
    if (form.notes !== order.value.notes) updateData.notes = form.notes
    
    await orderApi.updateOrder(order.value.id, updateData)
    
    ElMessage.success('订单修改成功')
    emit('success')
    handleClose()
  } catch (error) {
    console.error('修改订单失败:', error)
    ElMessage.error('修改订单失败')
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
  order.value = null
  Object.assign(form, {
    quantity: undefined,
    price: undefined,
    stop_price: undefined,
    time_in_force: undefined,
    priority: undefined,
    expire_time: undefined,
    tags: undefined,
    notes: undefined
  })
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

// 监听订单ID变化
watch(() => props.orderId, () => {
  if (props.orderId && visible.value) {
    loadOrderDetail()
  }
})

// 监听对话框显示状态
watch(visible, (newVisible) => {
  if (newVisible && props.orderId) {
    loadOrderDetail()
  }
})

// 初始化
onMounted(() => {
  loadAvailableTags()
})
</script>

<style scoped>
.loading-container {
  padding: 20px;
}

.readonly-info {
  margin-bottom: 20px;
}

.info-item {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.info-item label {
  width: 60px;
  font-weight: 500;
  color: var(--el-text-color-regular);
}

.symbol {
  font-weight: 600;
  font-size: 16px;
}

.field-hint {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
}

.modification-rules {
  margin: 8px 0;
  padding-left: 20px;
}

.modification-rules li {
  margin: 4px 0;
  font-size: 14px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
}

:deep(.el-card__body) {
  padding: 16px;
}
</style>