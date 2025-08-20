<template>
  <div class="manual-trading-view">
    <div class="page-header">
      <h1>手动交易</h1>
      <div class="header-status">
        <div class="status-group">
          <el-tag 
            v-if="networkStatus === 'online'" 
            type="success" 
            size="small"
          >
            API在线
          </el-tag>
          <el-tag 
            v-else-if="networkStatus === 'offline'" 
            type="danger" 
            size="small"
          >
            API离线
          </el-tag>
          <el-tag 
            v-else 
            type="warning" 
            size="small"
          >
            API检测中
          </el-tag>
          
          <WebSocketStatus :show-text="true" :show-reconnect-button="false" />
        </div>
      </div>
      <div class="header-actions">
        <el-button @click="refreshData" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button 
          v-if="error || networkStatus === 'offline'"
          type="primary"
          @click="retryDataLoad"
        >
          重试
        </el-button>
      </div>
    </div>

    <!-- 错误提示 -->
    <div v-if="error" class="error-banner">
      <el-alert
        :title="error"
        type="error"
        :closable="false"
        show-icon
      >
        <template #default>
          <p>{{ error }}</p>
          <el-button type="primary" size="small" @click="retryDataLoad">
            重新加载
          </el-button>
        </template>
      </el-alert>
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
import WebSocketStatus from '@/components/WebSocketStatus.vue'

const tradingStore = useTradingStore()

// 响应式数据
const loading = ref(false)
const error = ref<string | null>(null)
const networkStatus = ref<'online' | 'offline' | 'checking'>('checking')

// 关注的合约
const watchedSymbols = ref([
  'SHFE.cu2601',
  'DCE.i2601',
  'CZCE.MA2601',
  'CFFEX.IF2601'
])

// 计算属性（添加数据验证）
const positions = computed(() => {
  const pos = tradingStore.positions || []
  return Array.isArray(pos) ? pos : []
})

const pendingOrders = computed(() => {
  // 确保orders是数组且有some方法
  const orders = tradingStore.orders || []
  if (!Array.isArray(orders)) {
    console.warn('orders不是数组:', orders)
    return []
  }
  
  return orders.filter(order => 
    order && order.status && ['pending', 'submitted', 'partially_filled'].includes(order.status)
  )
})

// 方法
const refreshData = async () => {
  try {
    loading.value = true
    error.value = null
    
    // 刷新交易数据（添加错误处理）
    const promises = [
      tradingStore.fetchPositions().catch(err => {
        console.error('获取持仓失败:', err)
        return { error: '获取持仓失败' }
      }),
      tradingStore.fetchOrders().catch(err => {
        console.error('获取订单失败:', err)
        return { error: '获取订单失败' }
      })
    ]
    
    const results = await Promise.allSettled(promises)
    
    // 检查是否有错误
    const errors = results
      .filter(result => result.status === 'rejected' || (result.status === 'fulfilled' && result.value?.error))
      .map(result => result.status === 'rejected' ? result.reason : result.value.error)
    
    if (errors.length === 0) {
      ElMessage.success('数据刷新完成')
    } else if (errors.length < promises.length) {
      ElMessage.warning('部分数据刷新失败，但其他数据已更新')
    } else {
      error.value = '数据加载失败，请检查网络连接'
      ElMessage.error('数据刷新失败，请稍后重试')
    }
  } catch (err: any) {
    console.error('数据刷新失败:', err)
    error.value = '数据加载失败，请检查网络连接'
    ElMessage.error('数据刷新失败，请稍后重试')
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

// 网络状态检测
const checkNetworkStatus = async () => {
  try {
    networkStatus.value = 'checking'
    // 简单的网络检测
    const response = await fetch('/api/health', { 
      method: 'HEAD',
      cache: 'no-cache'
    })
    networkStatus.value = response.ok ? 'online' : 'offline'
  } catch (err) {
    networkStatus.value = 'offline'
  }
}

// 重试数据加载
const retryDataLoad = async () => {
  error.value = null
  await checkNetworkStatus()
  if (networkStatus.value === 'online') {
    await refreshData()
  }
}

// 生命周期
onMounted(async () => {
  await checkNetworkStatus()
  await refreshData()
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
    
    .header-status {
      flex: 1;
      display: flex;
      justify-content: center;
      
      .status-group {
        display: flex;
        align-items: center;
        gap: 12px;
      }
    }
    
    .header-actions {
      display: flex;
      gap: 12px;
    }
  }
  
  .error-banner {
    margin-bottom: 24px;
  }
}
</style>