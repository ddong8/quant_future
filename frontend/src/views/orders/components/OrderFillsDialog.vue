<template>
  <el-dialog
    v-model="visible"
    title="成交记录"
    width="800px"
    :close-on-click-modal="false"
  >
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="6" animated />
    </div>

    <div v-else>
      <!-- 成交汇总 -->
      <el-card class="summary-card" v-if="order">
        <template #header>
          <span>成交汇总</span>
        </template>
        <el-row :gutter="20">
          <el-col :span="6">
            <div class="summary-item">
              <div class="summary-value">{{ formatNumber(order.filled_quantity) }}</div>
              <div class="summary-label">已成交数量</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="summary-item">
              <div class="summary-value">
                {{ order.avg_fill_price ? formatPrice(order.avg_fill_price) : '-' }}
              </div>
              <div class="summary-label">平均成交价</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="summary-item">
              <div class="summary-value">{{ formatPrice(totalValue) }}</div>
              <div class="summary-label">成交金额</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="summary-item">
              <div class="summary-value">{{ formatPrice(totalCommission) }}</div>
              <div class="summary-label">总手续费</div>
            </div>
          </el-col>
        </el-row>
      </el-card>

      <!-- 成交记录表格 -->
      <el-card class="fills-card">
        <template #header>
          <div class="card-header">
            <span>成交明细</span>
            <div class="header-actions">
              <el-button size="small" @click="loadOrderFills">
                <el-icon><Refresh /></el-icon>
                刷新
              </el-button>
            </div>
          </div>
        </template>

        <el-table
          :data="fills"
          stripe
          style="width: 100%"
          empty-text="暂无成交记录"
        >
          <!-- 成交ID -->
          <el-table-column prop="id" label="成交ID" width="80" />

          <!-- 外部成交ID -->
          <el-table-column prop="fill_id_external" label="外部成交ID" width="120">
            <template #default="{ row }">
              <span v-if="row.fill_id_external">{{ row.fill_id_external }}</span>
              <span v-else class="no-data">-</span>
            </template>
          </el-table-column>

          <!-- 成交数量 -->
          <el-table-column prop="quantity" label="成交数量" width="120" align="right">
            <template #default="{ row }">
              <span class="quantity">{{ formatNumber(row.quantity) }}</span>
            </template>
          </el-table-column>

          <!-- 成交价格 -->
          <el-table-column prop="price" label="成交价格" width="120" align="right">
            <template #default="{ row }">
              <span class="price">{{ formatPrice(row.price) }}</span>
            </template>
          </el-table-column>

          <!-- 成交金额 -->
          <el-table-column prop="value" label="成交金额" width="140" align="right">
            <template #default="{ row }">
              <span class="value">{{ formatPrice(row.value) }}</span>
            </template>
          </el-table-column>

          <!-- 手续费 -->
          <el-table-column label="手续费" width="120" align="right">
            <template #default="{ row }">
              <div class="commission-cell">
                <span class="commission">{{ formatPrice(row.commission) }}</span>
                <span v-if="row.commission_asset" class="commission-asset">
                  {{ row.commission_asset }}
                </span>
              </div>
            </template>
          </el-table-column>

          <!-- 流动性 -->
          <el-table-column prop="liquidity" label="流动性" width="80">
            <template #default="{ row }">
              <el-tag
                v-if="row.liquidity"
                :type="row.liquidity === 'maker' ? 'success' : 'warning'"
                size="small"
              >
                {{ row.liquidity === 'maker' ? 'Maker' : 'Taker' }}
              </el-tag>
              <span v-else class="no-data">-</span>
            </template>
          </el-table-column>

          <!-- 对手方 -->
          <el-table-column prop="counterparty" label="对手方" width="100">
            <template #default="{ row }">
              <span v-if="row.counterparty">{{ row.counterparty }}</span>
              <span v-else class="no-data">-</span>
            </template>
          </el-table-column>

          <!-- 成交时间 -->
          <el-table-column prop="fill_time" label="成交时间" width="160">
            <template #default="{ row }">
              {{ formatDateTime(row.fill_time) }}
            </template>
          </el-table-column>

          <!-- 操作 -->
          <el-table-column label="操作" width="80" fixed="right">
            <template #default="{ row }">
              <el-button
                type="text"
                size="small"
                @click="handleViewFillDetail(row)"
              >
                详情
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <!-- 成交详情对话框 -->
    <el-dialog
      v-model="showFillDetail"
      title="成交详情"
      width="500px"
      append-to-body
    >
      <div v-if="selectedFill" class="fill-detail">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="成交ID">
            {{ selectedFill.id }}
          </el-descriptions-item>
          <el-descriptions-item label="UUID">
            <span class="uuid">{{ selectedFill.uuid }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="外部成交ID">
            {{ selectedFill.fill_id_external || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="成交数量">
            <span class="quantity">{{ formatNumber(selectedFill.quantity) }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="成交价格">
            <span class="price">{{ formatPrice(selectedFill.price) }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="成交金额">
            <span class="value">{{ formatPrice(selectedFill.value) }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="手续费">
            {{ formatPrice(selectedFill.commission) }}
            {{ selectedFill.commission_asset ? ` ${selectedFill.commission_asset}` : '' }}
          </el-descriptions-item>
          <el-descriptions-item label="流动性">
            <el-tag
              v-if="selectedFill.liquidity"
              :type="selectedFill.liquidity === 'maker' ? 'success' : 'warning'"
              size="small"
            >
              {{ selectedFill.liquidity === 'maker' ? 'Maker' : 'Taker' }}
            </el-tag>
            <span v-else>-</span>
          </el-descriptions-item>
          <el-descriptions-item label="对手方">
            {{ selectedFill.counterparty || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="成交时间">
            {{ formatDateTime(selectedFill.fill_time) }}
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ formatDateTime(selectedFill.created_at) }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- 元数据 -->
        <div v-if="selectedFill.metadata && Object.keys(selectedFill.metadata).length > 0" class="metadata-section">
          <h4>元数据</h4>
          <el-table
            :data="metadataEntries"
            size="small"
            style="width: 100%"
          >
            <el-table-column prop="key" label="键" width="150" />
            <el-table-column prop="value" label="值">
              <template #default="{ row }">
                <code>{{ JSON.stringify(row.value) }}</code>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>

      <template #footer>
        <el-button @click="showFillDetail = false">关闭</el-button>
      </template>
    </el-dialog>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="visible = false">关闭</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { orderApi, type Order, type OrderFill } from '@/api/order'
import { formatNumber, formatPrice, formatDateTime } from '@/utils/format'

// Props
const props = defineProps<{
  modelValue: boolean
  orderId?: number
}>()

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

// 响应式数据
const loading = ref(false)
const order = ref<Order | null>(null)
const fills = ref<OrderFill[]>([])
const showFillDetail = ref(false)
const selectedFill = ref<OrderFill | null>(null)

// 计算属性
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const totalValue = computed(() => {
  return fills.value.reduce((sum, fill) => sum + fill.value, 0)
})

const totalCommission = computed(() => {
  return fills.value.reduce((sum, fill) => sum + fill.commission, 0)
})

const metadataEntries = computed(() => {
  if (!selectedFill.value?.metadata) return []
  return Object.entries(selectedFill.value.metadata).map(([key, value]) => ({
    key,
    value
  }))
})

// 加载订单详情
const loadOrderDetail = async () => {
  if (!props.orderId) return

  try {
    const response = await orderApi.getOrder(props.orderId)
    order.value = response.data
  } catch (error) {
    console.error('加载订单详情失败:', error)
    ElMessage.error('加载订单详情失败')
  }
}

// 加载成交记录
const loadOrderFills = async () => {
  if (!props.orderId) return

  try {
    loading.value = true
    const response = await orderApi.getOrderFills(props.orderId)
    fills.value = response.data
  } catch (error) {
    console.error('加载成交记录失败:', error)
    ElMessage.error('加载成交记录失败')
  } finally {
    loading.value = false
  }
}

// 查看成交详情
const handleViewFillDetail = (fill: OrderFill) => {
  selectedFill.value = fill
  showFillDetail.value = true
}

// 监听订单ID变化
watch(() => props.orderId, () => {
  if (props.orderId && visible.value) {
    loadOrderDetail()
    loadOrderFills()
  }
})

// 监听对话框显示状态
watch(visible, (newVisible) => {
  if (newVisible && props.orderId) {
    loadOrderDetail()
    loadOrderFills()
  }
})
</script>

<style scoped>
.loading-container {
  padding: 20px;
}

.summary-card {
  margin-bottom: 16px;
}

.summary-item {
  text-align: center;
}

.summary-value {
  font-size: 24px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  line-height: 1;
}

.summary-label {
  font-size: 14px;
  color: var(--el-text-color-regular);
  margin-top: 4px;
}

.fills-card {
  margin-bottom: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.quantity,
.price,
.value,
.commission {
  font-weight: 500;
}

.commission-cell {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.commission-asset {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 2px;
}

.no-data {
  color: var(--el-text-color-secondary);
  font-style: italic;
}

.fill-detail {
  max-height: 60vh;
  overflow-y: auto;
}

.uuid {
  font-family: monospace;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.metadata-section {
  margin-top: 20px;
}

.metadata-section h4 {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
}

.metadata-section code {
  background-color: var(--el-fill-color-light);
  padding: 2px 4px;
  border-radius: 3px;
  font-size: 12px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
}

:deep(.el-descriptions-item__label) {
  font-weight: 500;
  width: 120px;
}
</style>