<template>
  <el-dialog
    v-model="visible"
    title="持仓详情"
    width="800px"
    :before-close="handleClose"
  >
    <div v-if="position" class="position-detail">
      <!-- 基本信息 -->
      <div class="detail-section">
        <h3 class="section-title">基本信息</h3>
        <div class="info-grid">
          <div class="info-item">
            <label>交易标的</label>
            <div class="info-value">
              <span class="symbol">{{ position.symbol }}</span>
              <el-tag 
                :type="position.position_type === 'LONG' ? 'success' : 'warning'"
                size="small"
              >
                {{ position.position_type === 'LONG' ? '多头' : '空头' }}
              </el-tag>
            </div>
          </div>
          <div class="info-item">
            <label>持仓状态</label>
            <div class="info-value">
              <el-tag :type="getStatusType(position.status)">
                {{ getStatusText(position.status) }}
              </el-tag>
            </div>
          </div>
          <div class="info-item">
            <label>开仓时间</label>
            <div class="info-value">{{ formatDateTime(position.opened_at) }}</div>
          </div>
          <div class="info-item" v-if="position.closed_at">
            <label>平仓时间</label>
            <div class="info-value">{{ formatDateTime(position.closed_at) }}</div>
          </div>
        </div>
      </div>

      <!-- 持仓数据 -->
      <div class="detail-section">
        <h3 class="section-title">持仓数据</h3>
        <div class="info-grid">
          <div class="info-item">
            <label>持仓数量</label>
            <div class="info-value">{{ formatNumber(position.quantity) }}</div>
          </div>
          <div class="info-item">
            <label>可用数量</label>
            <div class="info-value">{{ formatNumber(position.available_quantity) }}</div>
          </div>
          <div class="info-item" v-if="position.frozen_quantity > 0">
            <label>冻结数量</label>
            <div class="info-value frozen">{{ formatNumber(position.frozen_quantity) }}</div>
          </div>
          <div class="info-item">
            <label>平均成本</label>
            <div class="info-value">{{ formatCurrency(position.average_cost) }}</div>
          </div>
          <div class="info-item">
            <label>总成本</label>
            <div class="info-value">{{ formatCurrency(position.total_cost) }}</div>
          </div>
          <div class="info-item" v-if="position.current_price">
            <label>当前价格</label>
            <div class="info-value">{{ formatCurrency(position.current_price) }}</div>
          </div>
          <div class="info-item" v-if="position.market_value">
            <label>市值</label>
            <div class="info-value">{{ formatCurrency(position.market_value) }}</div>
          </div>
        </div>
      </div>

      <!-- 盈亏分析 -->
      <div class="detail-section">
        <h3 class="section-title">盈亏分析</h3>
        <div class="pnl-cards">
          <div class="pnl-card">
            <div class="pnl-label">总盈亏</div>
            <div class="pnl-value" :class="getPnLClass(position.total_pnl)">
              {{ formatCurrency(position.total_pnl) }}
            </div>
            <div class="pnl-rate" :class="getPnLClass(position.total_pnl)">
              {{ formatPercent(position.return_rate) }}
            </div>
          </div>
          <div class="pnl-card">
            <div class="pnl-label">已实现盈亏</div>
            <div class="pnl-value" :class="getPnLClass(position.realized_pnl)">
              {{ formatCurrency(position.realized_pnl) }}
            </div>
          </div>
          <div class="pnl-card">
            <div class="pnl-label">未实现盈亏</div>
            <div class="pnl-value" :class="getPnLClass(position.unrealized_pnl)">
              {{ formatCurrency(position.unrealized_pnl) }}
            </div>
            <div class="pnl-rate" :class="getPnLClass(position.unrealized_pnl)">
              {{ formatPercent(position.unrealized_return_rate) }}
            </div>
          </div>
        </div>
      </div>

      <!-- 风险指标 -->
      <div class="detail-section">
        <h3 class="section-title">风险指标</h3>
        <div class="info-grid">
          <div class="info-item">
            <label>最大盈利</label>
            <div class="info-value profit">{{ formatCurrency(position.max_profit) }}</div>
          </div>
          <div class="info-item">
            <label>最大回撤</label>
            <div class="info-value loss">{{ formatCurrency(position.max_drawdown) }}</div>
          </div>
          <div class="info-item" v-if="position.stop_loss_price">
            <label>止损价格</label>
            <div class="info-value">{{ formatCurrency(position.stop_loss_price) }}</div>
          </div>
          <div class="info-item" v-if="position.take_profit_price">
            <label>止盈价格</label>
            <div class="info-value">{{ formatCurrency(position.take_profit_price) }}</div>
          </div>
        </div>
      </div>

      <!-- 关联信息 -->
      <div class="detail-section" v-if="position.strategy_id || position.backtest_id">
        <h3 class="section-title">关联信息</h3>
        <div class="info-grid">
          <div class="info-item" v-if="position.strategy_id">
            <label>关联策略</label>
            <div class="info-value">
              <el-link type="primary" @click="viewStrategy(position.strategy_id)">
                策略 #{{ position.strategy_id }}
              </el-link>
            </div>
          </div>
          <div class="info-item" v-if="position.backtest_id">
            <label>关联回测</label>
            <div class="info-value">
              <el-link type="primary" @click="viewBacktest(position.backtest_id)">
                回测 #{{ position.backtest_id }}
              </el-link>
            </div>
          </div>
          <div class="info-item">
            <label>持仓来源</label>
            <div class="info-value">{{ getSourceText(position.source) }}</div>
          </div>
        </div>
      </div>

      <!-- 备注和标签 -->
      <div class="detail-section" v-if="position.notes || position.tags.length > 0">
        <h3 class="section-title">备注信息</h3>
        <div class="notes-section">
          <div v-if="position.tags.length > 0" class="tags-container">
            <label>标签</label>
            <div class="tags">
              <el-tag
                v-for="tag in position.tags"
                :key="tag"
                size="small"
                class="tag-item"
              >
                {{ tag }}
              </el-tag>
            </div>
          </div>
          <div v-if="position.notes" class="notes-container">
            <label>备注</label>
            <div class="notes">{{ position.notes }}</div>
          </div>
        </div>
      </div>

      <!-- 操作历史 -->
      <div class="detail-section">
        <div class="section-header">
          <h3 class="section-title">操作历史</h3>
          <el-button size="small" @click="loadHistory">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
        <div class="history-container">
          <el-table
            :data="history"
            :loading="historyLoading"
            size="small"
            max-height="300"
          >
            <el-table-column prop="action" label="操作" width="100">
              <template #default="{ row }">
                <el-tag size="small">{{ getActionText(row.action) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="details" label="详情">
              <template #default="{ row }">
                <div class="history-details">
                  {{ formatHistoryDetails(row.details) }}
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="时间" width="150">
              <template #default="{ row }">
                {{ formatDateTime(row.created_at) }}
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">关闭</el-button>
        <el-button v-if="position?.is_open" type="primary" @click="handleEdit">
          编辑
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { usePositionStore } from '@/stores/position'
import { positionApi, type Position, type PositionHistory } from '@/api/position'
import { formatCurrency, formatNumber, formatPercent, formatDateTime } from '@/utils/format'
import { ElMessage } from 'element-plus'

// Props
interface Props {
  modelValue: boolean
  positionId: number | null
}

const props = defineProps<Props>()

// 事件定义
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

// 状态管理
const positionStore = usePositionStore()

// 响应式数据
const position = ref<Position | null>(null)
const history = ref<PositionHistory[]>([])
const historyLoading = ref(false)
const loading = ref(false)

// 计算属性
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// 监听持仓ID变化
watch(
  () => props.positionId,
  async (newId) => {
    if (newId && visible.value) {
      await loadPosition(newId)
      await loadHistory()
    }
  },
  { immediate: true }
)

// 监听对话框显示状态
watch(visible, async (show) => {
  if (show && props.positionId) {
    await loadPosition(props.positionId)
    await loadHistory()
  }
})

// 方法
const loadPosition = async (id: number) => {
  try {
    loading.value = true
    await positionStore.fetchPosition(id)
    position.value = positionStore.currentPosition
  } catch (error) {
    ElMessage.error('加载持仓详情失败')
  } finally {
    loading.value = false
  }
}

const loadHistory = async () => {
  if (!props.positionId) return
  
  try {
    historyLoading.value = true
    const response = await positionApi.getPositionHistory(props.positionId, {
      size: 50
    })
    
    if (response.success) {
      history.value = response.data.items
    }
  } catch (error) {
    ElMessage.error('加载操作历史失败')
  } finally {
    historyLoading.value = false
  }
}

const handleClose = () => {
  visible.value = false
  position.value = null
  history.value = []
}

const handleEdit = () => {
  // 这里可以打开编辑对话框
  ElMessage.info('编辑功能待实现')
}

const viewStrategy = (strategyId: number) => {
  // 跳转到策略详情页
  ElMessage.info(`查看策略 #${strategyId}`)
}

const viewBacktest = (backtestId: number) => {
  // 跳转到回测详情页
  ElMessage.info(`查看回测 #${backtestId}`)
}

const getStatusType = (status: string) => {
  switch (status) {
    case 'OPEN':
      return 'success'
    case 'CLOSED':
      return 'info'
    case 'SUSPENDED':
      return 'warning'
    default:
      return 'info'
  }
}

const getStatusText = (status: string) => {
  switch (status) {
    case 'OPEN':
      return '持仓中'
    case 'CLOSED':
      return '已平仓'
    case 'SUSPENDED':
      return '暂停'
    default:
      return status
  }
}

const getPnLClass = (value: number) => {
  if (value > 0) return 'profit'
  if (value < 0) return 'loss'
  return 'neutral'
}

const getSourceText = (source: string) => {
  switch (source) {
    case 'manual':
      return '手动创建'
    case 'strategy':
      return '策略执行'
    case 'algorithm':
      return '算法交易'
    default:
      return source
  }
}

const getActionText = (action: string) => {
  switch (action) {
    case 'trade':
      return '交易'
    case 'price_update':
      return '价格更新'
    case 'freeze':
      return '冻结'
    case 'unfreeze':
      return '解冻'
    case 'set_stop_loss':
      return '设置止损'
    case 'set_take_profit':
      return '设置止盈'
    default:
      return action
  }
}

const formatHistoryDetails = (details: any) => {
  if (!details) return ''
  
  const parts = []
  if (details.quantity) {
    parts.push(`数量: ${formatNumber(details.quantity)}`)
  }
  if (details.price) {
    parts.push(`价格: ${formatCurrency(details.price)}`)
  }
  if (details.stop_price) {
    parts.push(`止损价: ${formatCurrency(details.stop_price)}`)
  }
  if (details.profit_price) {
    parts.push(`止盈价: ${formatCurrency(details.profit_price)}`)
  }
  
  return parts.join(', ')
}
</script>

<style scoped>
.position-detail {
  max-height: 70vh;
  overflow-y: auto;
}

.detail-section {
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e5e7eb;
}

.detail-section:last-child {
  border-bottom: none;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 16px 0;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-item label {
  font-size: 12px;
  color: #6b7280;
  font-weight: 500;
}

.info-value {
  font-size: 14px;
  color: #1f2937;
  display: flex;
  align-items: center;
  gap: 8px;
}

.symbol {
  font-weight: 600;
  font-size: 16px;
}

.frozen {
  color: #f59e0b;
}

.pnl-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
}

.pnl-card {
  background: var(--el-fill-color-lighter);
  border-radius: 8px;
  padding: 16px;
  text-align: center;
}

.pnl-label {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 8px;
}

.pnl-value {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 4px;
}

.pnl-rate {
  font-size: 12px;
}

.notes-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.tags-container,
.notes-container {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tags-container label,
.notes-container label {
  font-size: 12px;
  color: #6b7280;
  font-weight: 500;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.notes {
  background: var(--el-fill-color-lighter);
  border-radius: 6px;
  padding: 12px;
  font-size: 14px;
  color: #374151;
  line-height: 1.5;
}

.history-container {
  background: var(--el-fill-color-lighter);
  border-radius: 8px;
  padding: 16px;
}

.history-details {
  font-size: 12px;
  color: #6b7280;
}

.profit {
  color: #10b981;
}

.loss {
  color: #ef4444;
}

.neutral {
  color: #6b7280;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .info-grid {
    grid-template-columns: 1fr;
  }
  
  .pnl-cards {
    grid-template-columns: 1fr;
  }
}
</style>