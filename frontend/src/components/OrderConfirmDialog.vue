<template>
  <el-dialog
    v-model="visible"
    title="订单确认"
    width="500px"
    :before-close="handleClose"
  >
    <div class="order-confirm">
      <!-- 订单信息 -->
      <div class="order-summary">
        <h3>订单信息</h3>
        <div class="summary-grid">
          <div class="summary-item">
            <span class="label">交易合约:</span>
            <span class="value">{{ order.symbol }}</span>
          </div>
          <div class="summary-item">
            <span class="label">交易方向:</span>
            <span class="value" :class="order.side">
              {{ order.side === 'buy' ? '买入' : '卖出' }}
            </span>
          </div>
          <div class="summary-item">
            <span class="label">订单类型:</span>
            <span class="value">{{ getOrderTypeText(order.order_type) }}</span>
          </div>
          <div class="summary-item">
            <span class="label">交易数量:</span>
            <span class="value">{{ order.quantity }}手</span>
          </div>
          <div v-if="order.price" class="summary-item">
            <span class="label">委托价格:</span>
            <span class="value">{{ formatPrice(order.price) }}</span>
          </div>
          <div v-if="order.stop_price" class="summary-item">
            <span class="label">止损价格:</span>
            <span class="value">{{ formatPrice(order.stop_price) }}</span>
          </div>
          <div class="summary-item">
            <span class="label">有效期:</span>
            <span class="value">{{ getTimeInForceText(order.time_in_force) }}</span>
          </div>
        </div>
      </div>

      <!-- 费用明细 -->
      <div class="cost-breakdown">
        <h3>费用明细</h3>
        <div class="cost-grid">
          <div class="cost-item">
            <span class="label">交易金额:</span>
            <span class="value">{{ formatCurrency(estimatedAmount) }}</span>
          </div>
          <div class="cost-item">
            <span class="label">保证金:</span>
            <span class="value">{{ formatCurrency(estimatedMargin) }}</span>
          </div>
          <div class="cost-item">
            <span class="label">手续费:</span>
            <span class="value">{{ formatCurrency(estimatedFee) }}</span>
          </div>
          <div class="cost-item total">
            <span class="label">总计:</span>
            <span class="value">{{ formatCurrency(estimatedMargin + estimatedFee) }}</span>
          </div>
        </div>
      </div>

      <!-- 风险提示 -->
      <div v-if="riskWarnings.length > 0" class="risk-warnings">
        <h3>风险提示</h3>
        <el-alert
          v-for="warning in riskWarnings"
          :key="warning.type"
          :title="warning.title"
          :description="warning.message"
          :type="warning.level"
          :closable="false"
          style="margin-bottom: 8px"
        />
      </div>

      <!-- 确认选项 -->
      <div class="confirm-options">
        <el-checkbox v-model="confirmRisk">
          我已了解并接受上述风险
        </el-checkbox>
        <el-checkbox v-model="confirmTerms">
          我同意相关交易条款和条件
        </el-checkbox>
      </div>

      <!-- 密码确认 -->
      <div class="password-confirm">
        <el-form-item label="交易密码" required>
          <el-input
            v-model="tradingPassword"
            type="password"
            placeholder="请输入交易密码"
            show-password
            @keyup.enter="handleConfirm"
          />
        </el-form-item>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button
          type="primary"
          :disabled="!canConfirm"
          :loading="confirming"
          @click="handleConfirm"
        >
          确认下单
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import type { CreateOrderRequest, OrderType, TimeInForce } from '@/types/trading'

interface Props {
  modelValue: boolean
  order: CreateOrderRequest
  estimatedAmount: number
  estimatedMargin: number
  estimatedFee: number
  riskWarnings: any[]
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'confirm'): void
  (e: 'cancel'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 响应式数据
const confirming = ref(false)
const confirmRisk = ref(false)
const confirmTerms = ref(false)
const tradingPassword = ref('')

// 计算属性
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const canConfirm = computed(() => {
  return confirmRisk.value && confirmTerms.value && tradingPassword.value.length > 0
})

// 方法
const getOrderTypeText = (type: OrderType) => {
  const typeMap = {
    market: '市价单',
    limit: '限价单',
    stop: '止损单',
    stop_limit: '止损限价单',
    trailing_stop: '跟踪止损单'
  }
  return typeMap[type] || type
}

const getTimeInForceText = (tif: TimeInForce) => {
  const tifMap = {
    day: '当日有效',
    gtc: '撤销前有效',
    ioc: '立即成交或撤销',
    fok: '全部成交或撤销'
  }
  return tifMap[tif] || tif
}

const formatPrice = (price: number) => {
  return price?.toFixed(2) || '-'
}

const formatCurrency = (amount: number) => {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY'
  }).format(amount)
}

const handleConfirm = async () => {
  if (!canConfirm.value) {
    ElMessage.warning('请完成所有确认项')
    return
  }

  try {
    confirming.value = true
    
    // 验证交易密码
    // await authApi.verifyTradingPassword(tradingPassword.value)
    
    emit('confirm')
  } catch (error: any) {
    ElMessage.error(error.message || '交易密码验证失败')
  } finally {
    confirming.value = false
  }
}

const handleClose = () => {
  resetForm()
  emit('cancel')
}

const resetForm = () => {
  confirmRisk.value = false
  confirmTerms.value = false
  tradingPassword.value = ''
  confirming.value = false
}

// 监听器
watch(visible, (newVal) => {
  if (!newVal) {
    resetForm()
  }
})
</script>

<style scoped lang="scss">
.order-confirm {
  .order-summary,
  .cost-breakdown,
  .risk-warnings {
    margin-bottom: 24px;
    
    h3 {
      margin: 0 0 12px 0;
      font-size: 16px;
      font-weight: 600;
      color: #303133;
    }
  }
  
  .summary-grid,
  .cost-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    
    .summary-item,
    .cost-item {
      display: flex;
      justify-content: space-between;
      padding: 8px 0;
      border-bottom: 1px solid #f0f0f0;
      
      &:last-child {
        border-bottom: none;
      }
      
      &.total {
        grid-column: 1 / -1;
        border-top: 1px solid #e4e7ed;
        margin-top: 8px;
        padding-top: 12px;
        font-weight: 600;
        
        .value {
          color: #f56c6c;
          font-size: 16px;
        }
      }
      
      .label {
        color: #606266;
        font-size: 14px;
      }
      
      .value {
        font-weight: 600;
        color: #303133;
        
        &.buy {
          color: #f56c6c;
        }
        
        &.sell {
          color: #67c23a;
        }
      }
    }
  }
  
  .confirm-options {
    margin-bottom: 16px;
    
    .el-checkbox {
      display: block;
      margin-bottom: 8px;
    }
  }
  
  .password-confirm {
    .el-form-item {
      margin-bottom: 0;
    }
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>