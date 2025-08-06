<template>
  <div class="positions-view">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">持仓管理</h1>
        <p class="page-description">查看和管理您的投资组合持仓</p>
      </div>
      <div class="header-right">
        <el-button 
          type="primary" 
          :icon="Refresh" 
          @click="refreshData"
          :loading="positionStore.loading"
        >
          刷新
        </el-button>
        <el-button 
          :icon="Download" 
          @click="handleExport"
        >
          导出
        </el-button>
      </div>
    </div>

    <!-- 投资组合摘要 -->
    <PortfolioSummary />

    <!-- 筛选器 -->
    <PositionFilter @filter-change="handleFilterChange" />

    <!-- 持仓表格 -->
    <div class="positions-table-container">
      <PositionTable 
        :positions="positionStore.positions"
        :loading="positionStore.loading"
        @position-click="handlePositionClick"
        @set-stop-loss="handleSetStopLoss"
        @set-take-profit="handleSetTakeProfit"
        @close-position="handleClosePosition"
      />

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="positionStore.pagination.page"
          v-model:page-size="positionStore.pagination.size"
          :page-sizes="[10, 20, 50, 100]"
          :total="positionStore.pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </div>

    <!-- 持仓详情对话框 -->
    <PositionDetailDialog
      v-model="showDetailDialog"
      :position-id="selectedPositionId"
    />

    <!-- 止损设置对话框 -->
    <StopLossDialog
      v-model="showStopLossDialog"
      :position="selectedPosition"
      @confirm="handleStopLossConfirm"
    />

    <!-- 止盈设置对话框 -->
    <TakeProfitDialog
      v-model="showTakeProfitDialog"
      :position="selectedPosition"
      @confirm="handleTakeProfitConfirm"
    />

    <!-- 平仓对话框 -->
    <ClosePositionDialog
      v-model="showCloseDialog"
      :position="selectedPosition"
      @confirm="handleCloseConfirm"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { Refresh, Download } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { usePositionStore } from '@/stores/position'
import type { Position } from '@/api/position'

// 组件导入
import PortfolioSummary from './components/PortfolioSummary.vue'
import PositionFilter from './components/PositionFilter.vue'
import PositionTable from './components/PositionTable.vue'
import PositionDetailDialog from './components/PositionDetailDialog.vue'
import StopLossDialog from './components/StopLossDialog.vue'
import TakeProfitDialog from './components/TakeProfitDialog.vue'
import ClosePositionDialog from './components/ClosePositionDialog.vue'

// 状态管理
const positionStore = usePositionStore()

// 响应式数据
const showDetailDialog = ref(false)
const showStopLossDialog = ref(false)
const showTakeProfitDialog = ref(false)
const showCloseDialog = ref(false)
const selectedPositionId = ref<number | null>(null)
const selectedPosition = ref<Position | null>(null)

// 生命周期
onMounted(() => {
  loadData()
})

// 监听分页变化
watch(
  () => [positionStore.pagination.page, positionStore.pagination.size],
  () => {
    positionStore.fetchPositions()
  }
)

// 方法
const loadData = async () => {
  await Promise.all([
    positionStore.fetchPositions(),
    positionStore.fetchPortfolioSummary(),
    positionStore.fetchStatistics()
  ])
}

const refreshData = async () => {
  await loadData()
  ElMessage.success('数据刷新成功')
}

const handleFilterChange = (filter: any) => {
  positionStore.setFilter(filter)
  positionStore.fetchPositions()
}

const handlePageChange = (page: number) => {
  positionStore.setPage(page)
}

const handleSizeChange = (size: number) => {
  positionStore.setPageSize(size)
}

const handlePositionClick = (position: Position) => {
  selectedPositionId.value = position.id
  showDetailDialog.value = true
}

const handleSetStopLoss = (position: Position) => {
  selectedPosition.value = position
  showStopLossDialog.value = true
}

const handleSetTakeProfit = (position: Position) => {
  selectedPosition.value = position
  showTakeProfitDialog.value = true
}

const handleClosePosition = (position: Position) => {
  selectedPosition.value = position
  showCloseDialog.value = true
}

const handleStopLossConfirm = async (data: { stopPrice: number; orderId?: number }) => {
  if (!selectedPosition.value) return

  try {
    await positionStore.setStopLoss(
      selectedPosition.value.id,
      data.stopPrice,
      data.orderId
    )
    showStopLossDialog.value = false
  } catch (error) {
    // 错误已在store中处理
  }
}

const handleTakeProfitConfirm = async (data: { profitPrice: number; orderId?: number }) => {
  if (!selectedPosition.value) return

  try {
    await positionStore.setTakeProfit(
      selectedPosition.value.id,
      data.profitPrice,
      data.orderId
    )
    showTakeProfitDialog.value = false
  } catch (error) {
    // 错误已在store中处理
  }
}

const handleCloseConfirm = async (data: { closePrice: number; reason?: string }) => {
  if (!selectedPosition.value) return

  try {
    await ElMessageBox.confirm(
      `确定要以价格 ${data.closePrice} 平仓 ${selectedPosition.value.symbol} 吗？`,
      '确认平仓',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await positionStore.closePosition(
      selectedPosition.value.id,
      data.closePrice,
      data.reason
    )
    showCloseDialog.value = false
  } catch (error) {
    if (error !== 'cancel') {
      // 错误已在store中处理
    }
  }
}

const handleExport = async () => {
  try {
    await positionStore.exportPositions(positionStore.filter)
  } catch (error) {
    // 错误已在store中处理
  }
}
</script>

<style scoped>
.positions-view {
  padding: 24px;
  background-color: #f5f5f5;
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  background: white;
  padding: 24px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.header-left {
  flex: 1;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 8px 0;
}

.page-description {
  font-size: 14px;
  color: #6b7280;
  margin: 0;
}

.header-right {
  display: flex;
  gap: 12px;
}

.positions-table-container {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.pagination-container {
  padding: 16px 24px;
  border-top: 1px solid #e5e7eb;
  display: flex;
  justify-content: center;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .positions-view {
    padding: 16px;
  }

  .page-header {
    flex-direction: column;
    gap: 16px;
    padding: 16px;
  }

  .header-right {
    width: 100%;
    justify-content: flex-end;
  }

  .page-title {
    font-size: 20px;
  }
}
</style>