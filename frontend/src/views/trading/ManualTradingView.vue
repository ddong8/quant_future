<template>
  <div class="manual-trading-view">
    <div class="page-header">
      <h1>手动交易</h1>
      <div class="header-actions">
        <el-button @click="refreshData" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <el-row :gutter="24">
      <!-- 左侧：交易表单和快速交易 -->
      <el-col :span="16">
        <el-row :gutter="16">
          <!-- 手动下单表单 -->
          <el-col :span="14">
            <ManualTradingForm />
          </el-col>
          
          <!-- 快速交易按钮 -->
          <el-col :span="10">
            <QuickTradingButtons />
          </el-col>
        </el-row>
        
        <!-- 批量订单管理 -->
        <div style="margin-top: 24px">
          <BatchOrderManagement />
        </div>
      </el-col>
      
      <!-- 右侧：市场信息和持仓 -->
      <el-col :span="8">
        <!-- 市场行情 -->
        <el-card title="市场行情" style="margin-bottom: 16px">
          <MarketQuote :symbols="watchedSymbols" />
        </el-card>
        
        <!-- 当前持仓 -->
        <el-card title="当前持仓" style="margin-bottom: 16px">
          <PositionDisplay :positions="positions" />
        </el-card>
        
        <!-- 待成交订单 -->
        <el-card title="待成交订单">
          <OrderManagement 
            :orders="pendingOrders"
            :show-actions="true"
            @cancel="handleCancelOrder"
            @modify="handleModifyOrder"
          />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { useTradingStore } from '@/stores/trading'
import ManualTradingForm from '@/components/ManualTradingForm.vue'
import QuickTradingButtons from '@/components/QuickTradingButtons.vue'
import BatchOrderManagement from '@/components/BatchOrderManagement.vue'
import MarketQuote from '@/components/MarketQuote.vue'
import PositionDisplay from '@/components/PositionDisplay.vue'
import OrderManagement from '@/components/OrderManagement.vue'

const tradingStore = useTradingStore()

// 响应式数据
const loading = ref(false)

// 关注的合约
const watchedSymbols = ref([
  'SHFE.cu2401',
  'DCE.i2401',
  'CZCE.MA401',
  'CFFEX.IF2401'
])

// 计算属性
const positions = computed(() => tradingStore.positions)

const pendingOrders = computed(() => {
  return tradingStore.orders.filter(order => 
    ['pending', 'submitted', 'partially_filled'].includes(order.status)
  )
})

// 方法
const refreshData = async () => {
  try {
    loading.value = true
    
    // 刷新交易数据
    await Promise.all([
      tradingStore.loadPositions(),
      tradingStore.loadOrders(),
      tradingStore.loadAccount()
    ])
    
    ElMessage.success('数据刷新成功')
  } catch (error) {
    ElMessage.error('数据刷新失败')
  } finally {
    loading.value = false
  }
}

const handleCancelOrder = async (orderId: number) => {
  try {
    await tradingStore.cancelOrder(orderId)
    ElMessage.success('订单撤销成功')
  } catch (error: any) {
    ElMessage.error(error.message || '订单撤销失败')
  }
}

const handleModifyOrder = async (orderId: number, modifications: any) => {
  try {
    await tradingStore.modifyOrder(orderId, modifications)
    ElMessage.success('订单修改成功')
  } catch (error: any) {
    ElMessage.error(error.message || '订单修改失败')
  }
}

// 生命周期
onMounted(() => {
  refreshData()
})
</script>

<style scoped lang="scss">
.manual-trading-view {
  padding: 24px;
  
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
    
    h1 {
      margin: 0;
      font-size: 24px;
      font-weight: 600;
      color: #303133;
    }
    
    .header-actions {
      display: flex;
      gap: 12px;
    }
  }
}
</style>