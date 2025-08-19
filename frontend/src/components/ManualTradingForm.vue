<template>
  <div class="manual-trading-form">
    <el-card title="手动下单">
      <template #header>
        <div class="card-header">
          <span>手动下单</span>
          <div class="header-actions">
            <el-button text @click="resetForm">
              <el-icon><Refresh /></el-icon>
              重置
            </el-button>
            <el-button text @click="loadTemplate">
              <el-icon><Document /></el-icon>
              模板
            </el-button>
          </div>
        </div>
      </template>

      <el-form
        ref="formRef"
        :model="orderForm"
        :rules="formRules"
        label-width="100px"
        @submit.prevent="submitOrder"
      >
        <!-- 合约选择 -->
        <el-form-item label="交易合约" prop="symbol">
          <el-select
            v-model="orderForm.symbol"
            placeholder="请选择合约"
            filterable
            remote
            :remote-method="searchSymbols"
            :loading="symbolLoading"
            style="width: 100%"
            @change="onSymbolChange"
          >
            <el-option
              v-for="symbol in symbolOptions"
              :key="symbol.code"
              :label="`${symbol.name} (${symbol.code})`"
              :value="symbol.code"
            >
              <div class="symbol-option">
                <span class="symbol-name">{{ symbol.name }}</span>
                <span class="symbol-code">{{ symbol.code }}</span>
                <span class="symbol-price">{{ formatPrice(symbol.last_price) }}</span>
              </div>
            </el-option>
          </el-select>
        </el-form-item>

        <!-- 交易方向 -->
        <el-form-item label="交易方向" prop="side">
          <el-radio-group v-model="orderForm.side">
            <el-radio-button label="buy" class="buy-button">买入</el-radio-button>
            <el-radio-button label="sell" class="sell-button">卖出</el-radio-button>
          </el-radio-group>
        </el-form-item>

        <!-- 订单类型 -->
        <el-form-item label="订单类型" prop="order_type">
          <el-select v-model="orderForm.order_type" @change="onOrderTypeChange">
            <el-option label="市价单" value="market" />
            <el-option label="限价单" value="limit" />
            <el-option label="止损单" value="stop" />
            <el-option label="止损限价单" value="stop_limit" />
            <el-option label="跟踪止损单" value="trailing_stop" />
          </el-select>
        </el-form-item>

        <!-- 数量 -->
        <el-form-item label="交易数量" prop="quantity">
          <el-input-number
            v-model="orderForm.quantity"
            :min="1"
            :max="maxQuantity"
            :step="1"
            style="width: 100%"
            @change="calculateAmount"
          />
          <div class="quantity-info">
            <span>最小单位: 1手</span>
            <span>最大数量: {{ maxQuantity }}手</span>
          </div>
        </el-form-item>

        <!-- 价格 (限价单/止损限价单) -->
        <el-form-item
          v-if="needPrice"
          label="委托价格"
          prop="price"
        >
          <el-input-number
            v-model="orderForm.price"
            :min="0"
            :precision="pricePrecision"
            :step="priceStep"
            style="width: 100%"
            @change="calculateAmount"
          />
          <div class="price-info">
            <span>当前价: {{ formatPrice(currentPrice) }}</span>
            <span v-if="priceDeviation">偏离: {{ priceDeviation }}</span>
          </div>
        </el-form-item>

        <!-- 止损价格 (止损单/止损限价单) -->
        <el-form-item
          v-if="needStopPrice"
          label="止损价格"
          prop="stop_price"
        >
          <el-input-number
            v-model="orderForm.stop_price"
            :min="0"
            :precision="pricePrecision"
            :step="priceStep"
            style="width: 100%"
          />
        </el-form-item>

        <!-- 有效期 -->
        <el-form-item label="有效期" prop="time_in_force">
          <el-select v-model="orderForm.time_in_force">
            <el-option label="当日有效" value="day" />
            <el-option label="撤销前有效" value="gtc" />
            <el-option label="立即成交或撤销" value="ioc" />
            <el-option label="全部成交或撤销" value="fok" />
          </el-select>
        </el-form-item>

        <!-- 交易金额预估 -->
        <el-form-item label="预估金额">
          <div class="amount-info">
            <div class="amount-row">
              <span class="label">交易金额:</span>
              <span class="value">{{ formatCurrency(estimatedAmount) }}</span>
            </div>
            <div class="amount-row">
              <span class="label">保证金:</span>
              <span class="value">{{ formatCurrency(estimatedMargin) }}</span>
            </div>
            <div class="amount-row">
              <span class="label">手续费:</span>
              <span class="value">{{ formatCurrency(estimatedFee) }}</span>
            </div>
            <div class="amount-row total">
              <span class="label">总计:</span>
              <span class="value">{{ formatCurrency(totalCost) }}</span>
            </div>
          </div>
        </el-form-item>

        <!-- 风险提示 -->
        <el-form-item v-if="riskWarnings.length > 0">
          <el-alert
            v-for="warning in riskWarnings"
            :key="warning.type"
            :title="warning.title"
            :description="warning.message"
            :type="warning.level"
            :closable="false"
            style="margin-bottom: 8px"
          />
        </el-form-item>

        <!-- 高级选项 -->
        <el-collapse v-model="activeAdvanced">
          <el-collapse-item title="高级选项" name="advanced">
            <el-form-item label="客户订单号">
              <el-input
                v-model="orderForm.client_order_id"
                placeholder="可选，用于订单跟踪"
                maxlength="32"
              />
            </el-form-item>
            
            <el-form-item label="关联策略">
              <el-select
                v-model="orderForm.strategy_id"
                placeholder="选择关联策略（可选）"
                clearable
              >
                <el-option
                  v-for="strategy in strategies"
                  :key="strategy.id"
                  :label="strategy.name"
                  :value="strategy.id"
                />
              </el-select>
            </el-form-item>
            
            <el-form-item>
              <el-checkbox v-model="orderForm.risk_check">
                启用风险检查
              </el-checkbox>
            </el-form-item>
          </el-collapse-item>
        </el-collapse>

        <!-- 提交按钮 -->
        <el-form-item>
          <div class="submit-buttons">
            <el-button
              type="primary"
              :class="orderForm.side === 'buy' ? 'buy-button' : 'sell-button'"
              :loading="submitting"
              @click="showConfirmDialog"
            >
              {{ orderForm.side === 'buy' ? '买入' : '卖出' }}
              {{ orderForm.symbol }}
            </el-button>
            <el-button @click="resetForm">重置</el-button>
          </div>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 订单确认对话框 -->
    <OrderConfirmDialog
      v-model="showConfirm"
      :order="orderForm"
      :estimated-amount="estimatedAmount"
      :estimated-margin="estimatedMargin"
      :estimated-fee="estimatedFee"
      :risk-warnings="riskWarnings"
      @confirm="submitOrder"
      @cancel="showConfirm = false"
    />

    <!-- 模板选择对话框 -->
    <OrderTemplateDialog
      v-model="showTemplate"
      @select="applyTemplate"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Document } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import { useTradingStore } from '@/stores/trading'
import { useStrategyStore } from '@/stores/strategy'
import type { CreateOrderRequest, OrderSide, OrderType, TimeInForce } from '@/types/trading'
import OrderConfirmDialog from './OrderConfirmDialog.vue'
import OrderTemplateDialog from './OrderTemplateDialog.vue'

const tradingStore = useTradingStore()
const strategyStore = useStrategyStore()

// 响应式数据
const formRef = ref<FormInstance>()
const submitting = ref(false)
const symbolLoading = ref(false)
const showConfirm = ref(false)
const showTemplate = ref(false)
const activeAdvanced = ref<string[]>([])

// 表单数据
const orderForm = ref<CreateOrderRequest>({
  symbol: '',
  side: 'buy' as OrderSide,
  order_type: 'limit' as OrderType,
  quantity: 1,
  price: undefined,
  stop_price: undefined,
  time_in_force: 'day' as TimeInForce,
  client_order_id: '',
  strategy_id: undefined,
  risk_check: true
})

// 合约选项
const symbolOptions = ref<any[]>([])

// 风险警告
const riskWarnings = ref<any[]>([])

// 表单验证规则
const formRules: FormRules = {
  symbol: [
    { required: true, message: '请选择交易合约', trigger: 'change' }
  ],
  side: [
    { required: true, message: '请选择交易方向', trigger: 'change' }
  ],
  order_type: [
    { required: true, message: '请选择订单类型', trigger: 'change' }
  ],
  quantity: [
    { required: true, message: '请输入交易数量', trigger: 'blur' },
    { type: 'number', min: 1, message: '数量必须大于0', trigger: 'blur' }
  ],
  price: [
    {
      validator: (rule, value, callback) => {
        if (needPrice.value && (!value || value <= 0)) {
          callback(new Error('请输入有效的委托价格'))
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
  ]
}

// 计算属性
const needPrice = computed(() => {
  return ['limit', 'stop_limit'].includes(orderForm.value.order_type)
})

const needStopPrice = computed(() => {
  return ['stop', 'stop_limit', 'trailing_stop'].includes(orderForm.value.order_type)
})

const currentSymbol = computed(() => {
  return symbolOptions.value.find(s => s.code === orderForm.value.symbol)
})

const currentPrice = computed(() => {
  return currentSymbol.value?.last_price || 0
})

const pricePrecision = computed(() => {
  return currentSymbol.value?.price_precision || 2
})

const priceStep = computed(() => {
  return currentSymbol.value?.price_step || 0.01
})

const maxQuantity = computed(() => {
  // 根据可用资金和保证金要求计算最大数量
  const account = tradingStore.currentAccount
  if (!account || !currentSymbol.value) return 1000
  
  const availableCash = Number(account.available_cash) || 0
  const marginRatio = Number(currentSymbol.value.margin_ratio) || 0.1
  const price = Number(orderForm.value.price) || Number(currentPrice.value) || 0
  const multiplier = Number(currentSymbol.value.multiplier) || 1
  
  if (price > 0 && availableCash > 0) {
    const maxByMargin = Math.floor(availableCash / (price * marginRatio * multiplier))
    return Math.max(1, Math.min(maxByMargin, 1000))
  }
  
  return 1000
})

const priceDeviation = computed(() => {
  if (!orderForm.value.price || !currentPrice.value) return ''
  
  const deviation = ((orderForm.value.price - currentPrice.value) / currentPrice.value) * 100
  const sign = deviation > 0 ? '+' : ''
  return `${sign}${deviation.toFixed(2)}%`
})

const estimatedAmount = computed(() => {
  const price = orderForm.value.price || currentPrice.value
  const multiplier = currentSymbol.value?.multiplier || 1
  return price * orderForm.value.quantity * multiplier
})

const estimatedMargin = computed(() => {
  const marginRatio = currentSymbol.value?.margin_ratio || 0.1
  return estimatedAmount.value * marginRatio
})

const estimatedFee = computed(() => {
  const feeRate = currentSymbol.value?.fee_rate || 0.0001
  return estimatedAmount.value * feeRate
})

const totalCost = computed(() => {
  return estimatedMargin.value + estimatedFee.value
})

const strategies = computed(() => {
  const strats = strategyStore.strategies || []
  return Array.isArray(strats) ? strats : []
})

// 方法
const searchSymbols = async (query: string) => {
  if (!query) return
  
  try {
    symbolLoading.value = true
    // 搜索合约
    // const response = await tradingApi.searchSymbols(query)
    // symbolOptions.value = response.data
    
    // 模拟数据
    symbolOptions.value = [
      {
        code: 'SHFE.cu2401',
        name: '沪铜2401',
        last_price: 68500,
        multiplier: 5,
        margin_ratio: 0.08,
        fee_rate: 0.0001,
        price_precision: 0,
        price_step: 10
      },
      {
        code: 'DCE.i2401',
        name: '铁矿石2401',
        last_price: 850,
        multiplier: 100,
        margin_ratio: 0.1,
        fee_rate: 0.0001,
        price_precision: 1,
        price_step: 0.5
      }
    ].filter(s => s.name.includes(query) || s.code.includes(query))
  } catch (error) {
    ElMessage.error('搜索合约失败')
  } finally {
    symbolLoading.value = false
  }
}

const onSymbolChange = () => {
  // 重新计算风险
  checkRisk()
  calculateAmount()
}

const onOrderTypeChange = () => {
  // 根据订单类型调整表单
  if (orderForm.value.order_type === 'market') {
    orderForm.value.price = undefined
  } else if (needPrice.value && !orderForm.value.price) {
    orderForm.value.price = currentPrice.value
  }
  
  checkRisk()
}

const calculateAmount = () => {
  // 触发计算属性更新
  checkRisk()
}

const checkRisk = () => {
  riskWarnings.value = []
  
  const account = tradingStore.currentAccount
  if (!account) return
  
  // 安全地获取数值
  const availableCash = Number(account.available_cash) || 0
  const marginRatio = Number(account.margin_ratio) || 0
  const totalCostValue = Number(totalCost.value) || 0
  
  // 检查可用资金
  if (totalCostValue > availableCash) {
    riskWarnings.value.push({
      type: 'insufficient_funds',
      level: 'error',
      title: '资金不足',
      message: `所需资金 ${formatCurrency(totalCostValue)} 超过可用资金 ${formatCurrency(availableCash)}`
    })
  }
  
  // 检查保证金比率
  if (marginRatio > 0.8) {
    riskWarnings.value.push({
      type: 'high_margin',
      level: 'warning',
      title: '保证金比率过高',
      message: '当前保证金使用率较高，建议谨慎交易'
    })
  }
  
  // 检查价格偏离
  const orderPrice = Number(orderForm.value.price) || 0
  const currentPriceValue = Number(currentPrice.value) || 0
  
  if (orderPrice > 0 && currentPriceValue > 0) {
    const deviation = Math.abs((orderPrice - currentPriceValue) / currentPriceValue)
    if (deviation > 0.05) {
      riskWarnings.value.push({
        type: 'price_deviation',
        level: 'warning',
        title: '价格偏离较大',
        message: `委托价格偏离市价 ${(deviation * 100).toFixed(1)}%`
      })
    }
  }
}

const showConfirmDialog = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    showConfirm.value = true
  } catch (error) {
    ElMessage.error('请检查表单输入')
  }
}

const submitOrder = async () => {
  try {
    submitting.value = true
    
    // 提交订单
    await tradingStore.createOrder(orderForm.value)
    
    ElMessage.success('订单提交成功')
    showConfirm.value = false
    resetForm()
  } catch (error: any) {
    ElMessage.error(error.message || '订单提交失败')
  } finally {
    submitting.value = false
  }
}

const resetForm = () => {
  orderForm.value = {
    symbol: '',
    side: 'buy' as OrderSide,
    order_type: 'limit' as OrderType,
    quantity: 1,
    price: undefined,
    stop_price: undefined,
    time_in_force: 'day' as TimeInForce,
    client_order_id: '',
    strategy_id: undefined,
    risk_check: true
  }
  
  riskWarnings.value = []
  formRef.value?.clearValidate()
}

const loadTemplate = () => {
  showTemplate.value = true
}

const applyTemplate = (template: any) => {
  Object.assign(orderForm.value, template)
  showTemplate.value = false
  checkRisk()
}

// 格式化函数
const formatPrice = (price: number) => {
  return price?.toFixed(pricePrecision.value) || '-'
}

const formatCurrency = (amount: number) => {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY'
  }).format(amount)
}

// 监听器
watch(() => orderForm.value.quantity, calculateAmount)
watch(() => orderForm.value.price, calculateAmount)

// 生命周期
onMounted(() => {
  // 加载策略列表
  strategyStore.loadStrategies()
})
</script>

<style scoped lang="scss">
.manual-trading-form {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .header-actions {
      display: flex;
      gap: 8px;
    }
  }
  
  .symbol-option {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .symbol-name {
      font-weight: 600;
    }
    
    .symbol-code {
      color: #909399;
      font-size: 12px;
    }
    
    .symbol-price {
      color: #f56c6c;
      font-weight: 600;
    }
  }
  
  .buy-button {
    &.is-active {
      background-color: #f56c6c;
      border-color: #f56c6c;
      color: white;
    }
  }
  
  .sell-button {
    &.is-active {
      background-color: #67c23a;
      border-color: #67c23a;
      color: white;
    }
  }
  
  .quantity-info,
  .price-info {
    display: flex;
    justify-content: space-between;
    margin-top: 4px;
    font-size: 12px;
    color: #909399;
  }
  
  .amount-info {
    background: var(--el-bg-color-page);
    padding: 12px;
    border-radius: 4px;
    
    .amount-row {
      display: flex;
      justify-content: space-between;
      margin-bottom: 4px;
      
      &:last-child {
        margin-bottom: 0;
      }
      
      &.total {
        border-top: 1px solid #e4e7ed;
        padding-top: 8px;
        margin-top: 8px;
        font-weight: 600;
        
        .value {
          color: #f56c6c;
        }
      }
      
      .label {
        color: #606266;
      }
      
      .value {
        font-weight: 600;
        color: #303133;
      }
    }
  }
  
  .submit-buttons {
    display: flex;
    gap: 12px;
    
    .buy-button {
      background-color: #f56c6c;
      border-color: #f56c6c;
      
      &:hover {
        background-color: #f78989;
        border-color: #f78989;
      }
    }
    
    .sell-button {
      background-color: #67c23a;
      border-color: #67c23a;
      
      &:hover {
        background-color: #85ce61;
        border-color: #85ce61;
      }
    }
  }
}
</style>