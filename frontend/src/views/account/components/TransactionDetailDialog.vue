<template>
  <el-dialog
    v-model="visible"
    title="交易详情"
    width="800px"
    :before-close="handleClose"
  >
    <div v-if="transaction" class="transaction-detail">
      <!-- 基本信息 -->
      <el-card class="detail-card" shadow="never">
        <template #header>
          <span class="card-title">基本信息</span>
        </template>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <div class="detail-item">
              <label>交易ID:</label>
              <span class="value">{{ transaction.transaction_id }}</span>
              <el-button
                type="text"
                size="small"
                @click="copyToClipboard(transaction.transaction_id)"
              >
                复制
              </el-button>
            </div>
          </el-col>
          <el-col :span="12">
            <div class="detail-item">
              <label>交易时间:</label>
              <span class="value">{{ formatDateTime(transaction.transaction_time) }}</span>
            </div>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <div class="detail-item">
              <label>交易类型:</label>
              <el-tag :type="getTransactionTypeColor(transaction.transaction_type)">
                {{ TransactionTypeLabels[transaction.transaction_type] }}
              </el-tag>
            </div>
          </el-col>
          <el-col :span="12">
            <div class="detail-item">
              <label>交易状态:</label>
              <el-tag :type="TransactionStatusColors[transaction.status]">
                {{ TransactionStatusLabels[transaction.status] }}
              </el-tag>
            </div>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <div class="detail-item">
              <label>账户ID:</label>
              <span class="value">{{ transaction.account_id }}</span>
            </div>
          </el-col>
          <el-col :span="12">
            <div class="detail-item">
              <label>交易标的:</label>
              <span class="value">{{ transaction.symbol || '-' }}</span>
            </div>
          </el-col>
        </el-row>
      </el-card>

      <!-- 金额信息 -->
      <el-card class="detail-card" shadow="never">
        <template #header>
          <span class="card-title">金额信息</span>
        </template>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <div class="detail-item">
              <label>交易金额:</label>
              <span 
                class="value amount"
                :class="{ 
                  'amount-positive': transaction.amount > 0, 
                  'amount-negative': transaction.amount < 0 
                }"
              >
                {{ formatAmount(transaction.amount) }}
              </span>
            </div>
          </el-col>
          <el-col :span="12">
            <div class="detail-item">
              <label>货币类型:</label>
              <span class="value">{{ transaction.currency }}</span>
            </div>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <div class="detail-item">
              <label>汇率:</label>
              <span class="value">{{ transaction.exchange_rate }}</span>
            </div>
          </el-col>
          <el-col :span="12">
            <div class="detail-item">
              <label>手续费:</label>
              <span class="value">{{ formatAmount(transaction.fee_amount) }}</span>
            </div>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <div class="detail-item">
              <label>税费:</label>
              <span class="value">{{ formatAmount(transaction.tax_amount) }}</span>
            </div>
          </el-col>
        </el-row>
      </el-card>

      <!-- 余额信息 -->
      <el-card class="detail-card" shadow="never">
        <template #header>
          <span class="card-title">余额信息</span>
        </template>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <div class="detail-item">
              <label>交易前余额:</label>
              <span class="value">{{ formatAmount(transaction.balance_before || 0) }}</span>
            </div>
          </el-col>
          <el-col :span="12">
            <div class="detail-item">
              <label>交易后余额:</label>
              <span class="value">{{ formatAmount(transaction.balance_after || 0) }}</span>
            </div>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="24">
            <div class="detail-item">
              <label>余额变化:</label>
              <span 
                class="value amount"
                :class="{ 
                  'amount-positive': balanceChange > 0, 
                  'amount-negative': balanceChange < 0 
                }"
              >
                {{ balanceChange > 0 ? '+' : '' }}{{ formatAmount(balanceChange) }}
              </span>
            </div>
          </el-col>
        </el-row>
      </el-card>

      <!-- 关联信息 -->
      <el-card class="detail-card" shadow="never">
        <template #header>
          <span class="card-title">关联信息</span>
        </template>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <div class="detail-item">
              <label>关联订单:</label>
              <span class="value">
                <template v-if="transaction.order_id">
                  <el-link type="primary" @click="viewOrder(transaction.order_id)">
                    {{ transaction.order_id }}
                  </el-link>
                </template>
                <template v-else>-</template>
              </span>
            </div>
          </el-col>
          <el-col :span="12">
            <div class="detail-item">
              <label>关联持仓:</label>
              <span class="value">
                <template v-if="transaction.position_id">
                  <el-link type="primary" @click="viewPosition(transaction.position_id)">
                    {{ transaction.position_id }}
                  </el-link>
                </template>
                <template v-else>-</template>
              </span>
            </div>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="24">
            <div class="detail-item">
              <label>关联ID:</label>
              <span class="value">{{ transaction.reference_id || '-' }}</span>
            </div>
          </el-col>
        </el-row>
      </el-card>

      <!-- 描述信息 -->
      <el-card class="detail-card" shadow="never">
        <template #header>
          <span class="card-title">描述信息</span>
        </template>
        
        <div class="detail-item">
          <label>交易描述:</label>
          <div class="description-content">
            {{ transaction.description || '无描述' }}
          </div>
        </div>
      </el-card>

      <!-- 元数据 -->
      <el-card v-if="hasMetadata" class="detail-card" shadow="never">
        <template #header>
          <span class="card-title">元数据</span>
        </template>
        
        <div class="metadata-content">
          <pre>{{ JSON.stringify(transaction.metadata, null, 2) }}</pre>
        </div>
      </el-card>

      <!-- 时间信息 -->
      <el-card class="detail-card" shadow="never">
        <template #header>
          <span class="card-title">时间信息</span>
        </template>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <div class="detail-item">
              <label>创建时间:</label>
              <span class="value">{{ formatDateTime(transaction.created_at) }}</span>
            </div>
          </el-col>
          <el-col :span="12">
            <div class="detail-item">
              <label>更新时间:</label>
              <span class="value">{{ formatDateTime(transaction.updated_at) }}</span>
            </div>
          </el-col>
        </el-row>
      </el-card>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">关闭</el-button>
        <el-button 
          v-if="canUpdateStatus" 
          type="primary" 
          @click="handleUpdateStatus"
        >
          更新状态
        </el-button>
      </div>
    </template>

    <!-- 状态更新对话框 -->
    <TransactionStatusDialog
      v-model="statusDialogVisible"
      :transaction="transaction"
      @updated="handleStatusUpdated"
    />
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import {
  type Transaction,
  TransactionTypeLabels,
  TransactionStatusLabels,
  TransactionStatusColors,
  formatTransactionAmount,
  getTransactionTypeColor
} from '@/api/transaction'
import TransactionStatusDialog from './TransactionStatusDialog.vue'

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
const router = useRouter()

// 响应式数据
const statusDialogVisible = ref(false)

// 计算属性
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const balanceChange = computed(() => {
  if (!props.transaction || 
      props.transaction.balance_before === null || 
      props.transaction.balance_after === null) {
    return 0
  }
  return props.transaction.balance_after - props.transaction.balance_before
})

const hasMetadata = computed(() => {
  return props.transaction?.metadata && 
         Object.keys(props.transaction.metadata).length > 0
})

const canUpdateStatus = computed(() => {
  return props.transaction?.status === 'PENDING' || 
         props.transaction?.status === 'PROCESSING'
})

// 方法
const handleClose = () => {
  visible.value = false
}

const formatAmount = (amount: number) => {
  return formatTransactionAmount(amount)
}

const formatDateTime = (dateTime: string | undefined) => {
  if (!dateTime) return '-'
  return new Date(dateTime).toLocaleString('zh-CN')
}

const copyToClipboard = async (text: string) => {
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('已复制到剪贴板')
  } catch (error) {
    ElMessage.error('复制失败')
  }
}

const viewOrder = (orderId: number) => {
  router.push(`/orders/${orderId}`)
}

const viewPosition = (positionId: number) => {
  router.push(`/positions/${positionId}`)
}

const handleUpdateStatus = () => {
  statusDialogVisible.value = true
}

const handleStatusUpdated = () => {
  emit('updated')
  ElMessage.success('状态更新成功')
}
</script>

<style scoped>
.transaction-detail {
  max-height: 70vh;
  overflow-y: auto;
}

.detail-card {
  margin-bottom: 16px;
}

.detail-card:last-child {
  margin-bottom: 0;
}

.card-title {
  font-weight: 600;
  color: #303133;
}

.detail-item {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
  min-height: 32px;
}

.detail-item:last-child {
  margin-bottom: 0;
}

.detail-item label {
  width: 120px;
  color: #606266;
  font-weight: 500;
  flex-shrink: 0;
}

.detail-item .value {
  flex: 1;
  color: #303133;
}

.amount {
  font-weight: 600;
  font-size: 16px;
}

.amount-positive {
  color: #67c23a;
}

.amount-negative {
  color: #f56c6c;
}

.description-content {
  padding: 12px;
  background-color: var(--el-fill-color-light);
  border-radius: 4px;
  color: #606266;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}

.metadata-content {
  background-color: var(--el-fill-color-light);
  border-radius: 4px;
  padding: 12px;
}

.metadata-content pre {
  margin: 0;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
  color: #606266;
  white-space: pre-wrap;
  word-break: break-word;
}

.dialog-footer {
  text-align: right;
}
</style>