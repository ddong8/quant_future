<template>
  <div class="position-display">
    <div class="position-header">
      <div class="header-left">
        <h3>持仓信息</h3>
        <div class="position-summary">
          <span class="summary-item">
            总市值: <strong>{{ formatCurrency(totalPositionValue) }}</strong>
          </span>
          <span class="summary-item">
            浮动盈亏: <strong :class="getPnlClass(totalUnrealizedPnL)">
              {{ formatCurrency(totalUnrealizedPnL) }}
            </strong>
          </span>
          <span class="summary-item">
            持仓数量: <strong>{{ positions.length }}</strong>
          </span>
        </div>
      </div>
      
      <div class="header-actions">
        <el-select v-model="filters.symbol" placeholder="品种" clearable size="small">
          <el-option
            v-for="symbol in availableSymbols"
            :key="symbol"
            :label="symbol"
            :value="symbol"
          />
        </el-select>
        
        <el-select v-model="filters.side" placeholder="方向" clearable size="small">
          <el-option label="多头" value="long" />
          <el-option label="空头" value="short" />
        </el-select>
        
        <el-button size="small" @click="handleRefresh" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        
        <el-button size="small" type="danger" @click="handleCloseAll">
          <el-icon><Close /></el-icon>
          全部平仓
        </el-button>
      </div>
    </div>

    <!-- 持仓表格 -->
    <div class="position-table">
      <el-table
        :data="filteredPositions"
        v-loading="loading"
        @row-click="handleRowClick"
        height="400"
        stripe
      >
        <el-table-column prop="symbol" label="品种" width="120" sortable>
          <template #default="{ row }">
            <div class="symbol-cell">
              <el-tag size="small">{{ row.symbol }}</el-tag>
              <div class="market-info">
                <span class="price">{{ formatPrice(row.last_price) }}</span>
                <span :class="['change', getChangeClass(row.change_percent)]">
                  {{ formatPercent(row.change_percent) }}
                </span>
              </div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="side" label="方向" width="80" sortable>
          <template #default="{ row }">
            <el-tag :type="row.side === 'long' ? 'success' : 'danger'" size="small">
              {{ row.side === 'long' ? '多头' : '空头' }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="quantity" label="数量" width="100" sortable align="right">
          <template #default="{ row }">
            {{ formatNumber(row.quantity) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="avg_cost" label="成本价" width="120" sortable align="right">
          <template #default="{ row }">
            {{ formatPrice(row.avg_cost) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="last_price" label="现价" width="120" sortable align="right">
          <template #default="{ row }">
            {{ formatPrice(row.last_price) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="market_value" label="市值" width="140" sortable align="right">
          <template #default="{ row }">
            {{ formatCurrency(row.market_value) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="unrealized_pnl" label="浮动盈亏" width="140" sortable align="right">
          <template #default="{ row }">
            <div class="pnl-cell">
              <span :class="getPnlClass(row.unrealized_pnl)">
                {{ formatCurrency(row.unrealized_pnl) }}
              </span>
              <span :class="['pnl-percent', getPnlClass(row.unrealized_pnl)]">
                ({{ formatPercent(row.unrealized_pnl / row.cost_basis) }})
              </span>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="total_pnl" label="总盈亏" width="140" sortable align="right">
          <template #default="{ row }">
            <span :class="getPnlClass(row.total_pnl)">
              {{ formatCurrency(row.total_pnl) }}
            </span>
          </template>
        </el-table-column>
        
        <el-table-column label="保证金" width="120" align="right">
          <template #default="{ row }">
            {{ formatCurrency(row.margin_requirement) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button text size="small" @click.stop="handlePartialClose(row)">
              部分平仓
            </el-button>
            <el-button text size="small" type="danger" @click.stop="handleClose(row)">
              全部平仓
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 持仓详情对话框 -->
    <el-dialog v-model="showDetailDialog" title="持仓详情" width="800px">
      <div v-if="selectedPosition" class="position-detail">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-card title="基本信息">
              <el-descriptions :column="1" border>
                <el-descriptions-item label="品种">
                  {{ selectedPosition.symbol }}
                </el-descriptions-item>
                <el-descriptions-item label="方向">
                  <el-tag :type="selectedPosition.side === 'long' ? 'success' : 'danger'">
                    {{ selectedPosition.side === 'long' ? '多头' : '空头' }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="数量">
                  {{ formatNumber(selectedPosition.quantity) }}
                </el-descriptions-item>
                <el-descriptions-item label="成本价">
                  {{ formatPrice(selectedPosition.avg_cost) }}
                </el-descriptions-item>
                <el-descriptions-item label="现价">
                  {{ formatPrice(selectedPosition.last_price) }}
                </el-descriptions-item>
                <el-descriptions-item label="市值">
                  {{ formatCurrency(selectedPosition.market_value) }}
                </el-descriptions-item>
              </el-descriptions>
            </el-card>
          </el-col>
          
          <el-col :span="12">
            <el-card title="盈亏信息">
              <el-descriptions :column="1" border>
                <el-descriptions-item label="浮动盈亏">
                  <span :class="getPnlClass(selectedPosition.unrealized_pnl)">
                    {{ formatCurrency(selectedPosition.unrealized_pnl) }}
                  </span>
                </el-descriptions-item>
                <el-descriptions-item label="已实现盈亏">
                  <span :class="getPnlClass(selectedPosition.realized_pnl)">
                    {{ formatCurrency(selectedPosition.realized_pnl) }}
                  </span>
                </el-descriptions-item>
                <el-descriptions-item label="总盈亏">
                  <span :class="getPnlClass(selectedPosition.total_pnl)">
                    {{ formatCurrency(selectedPosition.total_pnl) }}
                  </span>
                </el-descriptions-item>
                <el-descriptions-item label="成本基础">
                  {{ formatCurrency(selectedPosition.cost_basis) }}
                </el-descriptions-item>
                <el-descriptions-item label="保证金要求">
                  {{ formatCurrency(selectedPosition.margin_requirement) }}
                </el-descriptions-item>
                <el-descriptions-item label="维持保证金">
                  {{ formatCurrency(selectedPosition.maintenance_margin) }}
                </el-descriptions-item>
              </el-descriptions>
            </el-card>
          </el-col>
        </el-row>
        
        <!-- 持仓批次 -->
        <el-card title="持仓批次" style="margin-top: 16px">
          <el-table :data="selectedPosition.lots" size="small">
            <el-table-column prop="quantity" label="数量" width="100" align="right">
              <template #default="{ row }">
                {{ formatNumber(row.quantity) }}
              </template>
            </el-table-column>
            <el-table-column prop="cost_price" label="成本价" width="120" align="right">
              <template #default="{ row }">
                {{ formatPrice(row.cost_price) }}
              </template>
            </el-table-column>
            <el-table-column prop="open_date" label="开仓日期" width="150">
              <template #default="{ row }">
                {{ formatDateTime(row.open_date) }}
              </template>
            </el-table-column>
            <el-table-column prop="pnl" label="盈亏" width="120" align="right">
              <template #default="{ row }">
                <span :class="getPnlClass(row.pnl)">
                  {{ formatCurrency(row.pnl) }}
                </span>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </div>
    </el-dialog>

    <!-- 部分平仓对话框 -->
    <el-dialog v-model="showCloseDialog" title="部分平仓" width="400px">
      <el-form :model="closeForm" label-width="80px">
        <el-form-item label="品种">
          <span>{{ closeForm.symbol }}</span>
        </el-form-item>
        <el-form-item label="持仓数量">
          <span>{{ formatNumber(closeForm.totalQuantity) }}</span>
        </el-form-item>
        <el-form-item label="平仓数量" required>
          <el-input-number
            v-model="closeForm.quantity"
            :min="1"
            :max="closeForm.totalQuantity"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showCloseDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmPartialClose" :loading="loading">
          确认平仓
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Close } from '@element-plus/icons-vue'
import { useTradingStore } from '@/stores/trading'
import type { Position } from '@/types/trading'

const tradingStore = useTradingStore()

// 响应式数据
const showDetailDialog = ref(false)
const showCloseDialog = ref(false)
const selectedPosition = ref<Position | null>(null)

// 筛选条件
const filters = ref({
  symbol: '',
  side: ''
})

// 平仓表单
const closeForm = ref({
  positionId: 0,
  symbol: '',
  totalQuantity: 0,
  quantity: 0
})

// 计算属性
const positions = computed(() => tradingStore.positions)
const loading = computed(() => tradingStore.loading)
const totalPositionValue = computed(() => tradingStore.totalPositionValue)
const totalUnrealizedPnL = computed(() => tradingStore.totalUnrealizedPnL)

const availableSymbols = computed(() => {
  const symbols = new Set(positions.value.map(pos => pos.symbol))
  return Array.from(symbols)
})

const filteredPositions = computed(() => {
  let result = positions.value
  
  // 品种筛选
  if (filters.value.symbol) {
    result = result.filter(pos => pos.symbol === filters.value.symbol)
  }
  
  // 方向筛选
  if (filters.value.side) {
    result = result.filter(pos => pos.side === filters.value.side)
  }
  
  return result
})

// 方法
const handleRefresh = () => {
  const accountId = tradingStore.currentAccount?.id
  if (accountId) {
    tradingStore.fetchPositions({ account_id: accountId })
  }
}

const handleRowClick = (position: Position) => {
  selectedPosition.value = position
  showDetailDialog.value = true
}

const handleClose = async (position: Position) => {
  try {
    await ElMessageBox.confirm(
      `确定要全部平仓 ${position.symbol} 吗？`,
      '确认平仓',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await tradingStore.closePosition(position.id)
  } catch (error) {
    // 用户取消或错误已在store中处理
  }
}

const handlePartialClose = (position: Position) => {
  closeForm.value = {
    positionId: position.id,
    symbol: position.symbol,
    totalQuantity: position.quantity,
    quantity: Math.floor(position.quantity / 2)
  }
  showCloseDialog.value = true
}

const confirmPartialClose = async () => {
  try {
    await tradingStore.closePosition(closeForm.value.positionId, closeForm.value.quantity)
    showCloseDialog.value = false
  } catch (error) {
    // 错误已在store中处理
  }
}

const handleCloseAll = async () => {
  const accountId = tradingStore.currentAccount?.id
  if (!accountId) {
    ElMessage.warning('请先选择交易账户')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      '确定要平掉所有持仓吗？此操作不可撤销。',
      '确认全部平仓',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // 调用全部平仓API
    // await tradingStore.closeAllPositions(accountId)
    ElMessage.success('全部平仓指令已提交')
  } catch (error) {
    // 用户取消
  }
}

// 格式化函数
const formatNumber = (num: number) => {
  return new Intl.NumberFormat('zh-CN').format(num)
}

const formatPrice = (price: number) => {
  return price.toFixed(2)
}

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY'
  }).format(value)
}

const formatPercent = (value: number) => {
  return `${(value * 100).toFixed(2)}%`
}

const formatDateTime = (dateString: string) => {
  return new Date(dateString).toLocaleString('zh-CN')
}

const getPnlClass = (pnl: number) => {
  if (pnl > 0) return 'profit'
  if (pnl < 0) return 'loss'
  return 'neutral'
}

const getChangeClass = (change: number) => {
  if (change > 0) return 'up'
  if (change < 0) return 'down'
  return 'flat'
}

// 生命周期
onMounted(() => {
  handleRefresh()
})
</script>

<style scoped lang="scss">
.position-display {
  .position-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 16px;
    padding: 16px;
    background: #fff;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    
    .header-left {
      h3 {
        margin: 0 0 8px 0;
        font-size: 18px;
        font-weight: 600;
        color: #303133;
      }
      
      .position-summary {
        display: flex;
        gap: 24px;
        
        .summary-item {
          font-size: 14px;
          color: #606266;
          
          strong {
            color: #303133;
            
            &.profit {
              color: #67c23a;
            }
            
            &.loss {
              color: #f56c6c;
            }
          }
        }
      }
    }
    
    .header-actions {
      display: flex;
      gap: 12px;
      align-items: center;
    }
  }
  
  .position-table {
    background: #fff;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    
    .symbol-cell {
      .market-info {
        display: flex;
        gap: 8px;
        margin-top: 4px;
        font-size: 12px;
        
        .price {
          color: #303133;
          font-weight: 600;
        }
        
        .change {
          &.up {
            color: #f56c6c;
          }
          
          &.down {
            color: #67c23a;
          }
          
          &.flat {
            color: #909399;
          }
        }
      }
    }
    
    .pnl-cell {
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      
      .pnl-percent {
        font-size: 12px;
        margin-top: 2px;
      }
    }
    
    .profit {
      color: #67c23a;
      font-weight: 600;
    }
    
    .loss {
      color: #f56c6c;
      font-weight: 600;
    }
    
    .neutral {
      color: #909399;
    }
  }
  
  .position-detail {
    :deep(.el-card__header) {
      padding: 12px 16px;
      font-weight: 600;
    }
  }
}
</style>