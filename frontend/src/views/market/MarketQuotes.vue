<template>
  <div class="market-quotes">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">市场行情</h1>
        <p class="page-description">实时查看市场行情数据和管理自选股</p>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="showSearchDialog = true">
          <el-icon><Search /></el-icon>
          搜索标的
        </el-button>
        <el-button @click="refreshQuotes" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button type="primary" @click="goToTechnicalAnalysis">
          <el-icon><TrendCharts /></el-icon>
          技术分析
        </el-button>
      </div>
    </div>

    <!-- 标签页 -->
    <el-tabs v-model="activeTab" @tab-change="handleTabChange">
      <!-- 自选股 -->
      <el-tab-pane label="自选股" name="watchlist">
        <WatchlistPanel 
          :watchlist="watchlist"
          :loading="watchlistLoading"
          @refresh="loadWatchlist"
          @remove="handleRemoveFromWatchlist"
          @reorder="handleReorderWatchlist"
        />
      </el-tab-pane>

      <!-- 热门标的 -->
      <el-tab-pane label="热门标的" name="popular">
        <PopularQuotesPanel 
          :quotes="popularQuotes"
          :loading="popularLoading"
          @refresh="loadPopularQuotes"
          @add-to-watchlist="handleAddToWatchlist"
        />
      </el-tab-pane>

      <!-- 全部行情 -->
      <el-tab-pane label="全部行情" name="all">
        <AllQuotesPanel 
          :quotes="allQuotes"
          :loading="allLoading"
          @refresh="loadAllQuotes"
          @add-to-watchlist="handleAddToWatchlist"
        />
      </el-tab-pane>
    </el-tabs>

    <!-- 搜索对话框 -->
    <SymbolSearchDialog 
      v-model="showSearchDialog"
      @add-to-watchlist="handleAddToWatchlist"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search, Refresh, TrendCharts } from '@element-plus/icons-vue'
import { 
  getWatchlist, 
  addToWatchlist, 
  removeFromWatchlist,
  reorderWatchlist,
  type WatchlistItem,
  type Quote
} from '@/api/marketQuotes'
import {
  getRealTimeQuotes,
  getContractList,
  getTechnicalIndicators,
  getMarketStatus,
  type RealTimeQuote,
  type ContractInfo
} from '@/api/realTimeData'
import WatchlistPanel from './components/WatchlistPanel.vue'
import PopularQuotesPanel from './components/PopularQuotesPanel.vue'
import AllQuotesPanel from './components/AllQuotesPanel.vue'
import SymbolSearchDialog from './components/SymbolSearchDialog.vue'

const router = useRouter()

// 响应式数据
const activeTab = ref('watchlist')
const loading = ref(false)
const showSearchDialog = ref(false)

// 自选股数据
const watchlist = ref<WatchlistItem[]>([])
const watchlistLoading = ref(false)

// 热门行情数据
const popularQuotes = ref<Quote[]>([])
const popularLoading = ref(false)

// 全部行情数据
const allQuotes = ref<Quote[]>([])
const allLoading = ref(false)

// 定时器
let refreshTimer: NodeJS.Timeout | null = null

// 加载自选股
const loadWatchlist = async () => {
  try {
    watchlistLoading.value = true
    const response = await getWatchlist()
    watchlist.value = response.data
  } catch (error) {
    console.error('加载自选股失败:', error)
    ElMessage.error('加载自选股失败')
  } finally {
    watchlistLoading.value = false
  }
}

// 加载热门行情 - 使用真实数据
const loadPopularQuotes = async () => {
  try {
    popularLoading.value = true
    
    // 获取合约列表
    const contractsResponse = await getContractList()
    if (contractsResponse.success && contractsResponse.data) {
      const contractsData = Array.isArray(contractsResponse.data) ? contractsResponse.data : []
      const contracts = contractsData.slice(0, 10) // 取前10个作为热门
      
      // 获取这些合约的实时行情
      const symbols = contracts.map((contract: ContractInfo) => contract.symbol)
      const quotesResponse = await getRealTimeQuotes(symbols)
      
      if (quotesResponse.success && quotesResponse.data) {
        const quotesData = Array.isArray(quotesResponse.data) ? quotesResponse.data : []
        popularQuotes.value = quotesData.map((quote: RealTimeQuote) => {
          const contract = contracts.find((c: ContractInfo) => c.symbol === quote.symbol)
          return {
            symbol: {
              symbol: quote.symbol,
              name: contract?.name || quote.symbol,
              exchange: contract?.exchange || 'UNKNOWN',
              asset_type: 'future'
            },
            price: quote.last_price,
            change: quote.change,
            change_percent: quote.change_percent,
            volume: quote.volume,
            turnover: quote.volume * quote.last_price,
            open_price: quote.open,
            high_price: quote.high,
            low_price: quote.low,
            data_status: 'ACTIVE',
            quote_time: quote.datetime,
            bid_price: quote.bid_price,
            ask_price: quote.ask_price,
            open_interest: quote.open_interest
          }
        })
      }
    }
  } catch (error) {
    console.error('加载热门行情失败:', error)
    ElMessage.error('加载热门行情失败')
  } finally {
    popularLoading.value = false
  }
}

// 加载全部行情 - 使用真实数据
const loadAllQuotes = async () => {
  try {
    allLoading.value = true
    
    // 获取合约列表
    const contractsResponse = await getContractList()
    if (contractsResponse.success && contractsResponse.data) {
      const contractsData = Array.isArray(contractsResponse.data) ? contractsResponse.data : []
      const contracts = contractsData
      
      // 获取所有合约的实时行情
      const symbols = contracts.map((contract: ContractInfo) => contract.symbol)
      const quotesResponse = await getRealTimeQuotes(symbols)
      
      if (quotesResponse.success && quotesResponse.data) {
        const quotesData = Array.isArray(quotesResponse.data) ? quotesResponse.data : []
        allQuotes.value = quotesData.map((quote: RealTimeQuote) => {
          const contract = contracts.find((c: ContractInfo) => c.symbol === quote.symbol)
          return {
            symbol: {
              symbol: quote.symbol,
              name: contract?.name || quote.symbol,
              exchange: contract?.exchange || 'UNKNOWN',
              asset_type: 'future'
            },
            price: quote.last_price,
            change: quote.change,
            change_percent: quote.change_percent,
            volume: quote.volume,
            turnover: quote.volume * quote.last_price,
            open_price: quote.open,
            high_price: quote.high,
            low_price: quote.low,
            data_status: 'ACTIVE',
            quote_time: quote.datetime,
            bid_price: quote.bid_price,
            ask_price: quote.ask_price,
            open_interest: quote.open_interest
          }
        })
      }
    }
  } catch (error) {
    console.error('加载全部行情失败:', error)
    ElMessage.error('加载全部行情失败')
  } finally {
    allLoading.value = false
  }
}

// 刷新当前标签页数据
const refreshQuotes = () => {
  switch (activeTab.value) {
    case 'watchlist':
      loadWatchlist()
      break
    case 'popular':
      loadPopularQuotes()
      break
    case 'all':
      loadAllQuotes()
      break
  }
}

// 标签页切换
const handleTabChange = (tabName: string) => {
  switch (tabName) {
    case 'watchlist':
      if (watchlist.value.length === 0) {
        loadWatchlist()
      }
      break
    case 'popular':
      if (popularQuotes.value.length === 0) {
        loadPopularQuotes()
      }
      break
    case 'all':
      if (allQuotes.value.length === 0) {
        loadAllQuotes()
      }
      break
  }
}

// 添加到自选股
const handleAddToWatchlist = async (symbolCode: string) => {
  try {
    await addToWatchlist(symbolCode)
    ElMessage.success('已添加到自选股')
    // 如果当前在自选股标签页，刷新数据
    if (activeTab.value === 'watchlist') {
      loadWatchlist()
    }
  } catch (error: any) {
    console.error('添加自选股失败:', error)
    ElMessage.error(error.response?.data?.detail || '添加自选股失败')
  }
}

// 从自选股移除
const handleRemoveFromWatchlist = async (watchlistId: number) => {
  try {
    await removeFromWatchlist(watchlistId)
    ElMessage.success('已从自选股移除')
    loadWatchlist()
  } catch (error) {
    console.error('移除自选股失败:', error)
    ElMessage.error('移除自选股失败')
  }
}

// 重新排序自选股
const handleReorderWatchlist = async (watchlistIds: number[]) => {
  try {
    await reorderWatchlist(watchlistIds)
    ElMessage.success('排序已更新')
    loadWatchlist()
  } catch (error) {
    console.error('更新排序失败:', error)
    ElMessage.error('更新排序失败')
  }
}

// 启动定时刷新
const startAutoRefresh = () => {
  refreshTimer = setInterval(() => {
    refreshQuotes()
  }, 30000) // 30秒刷新一次
}

// 停止定时刷新
const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

// 组件挂载
onMounted(() => {
  loadWatchlist()
  startAutoRefresh()
})

// 跳转到技术分析页面
const goToTechnicalAnalysis = () => {
  router.push('/market/technical')
}

// 组件卸载
onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style scoped>
.market-quotes {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #e4e7ed;
}

.header-left {
  flex: 1;
}

.page-title {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.page-description {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.header-right {
  display: flex;
  gap: 12px;
}

:deep(.el-tabs__header) {
  margin-bottom: 20px;
}

:deep(.el-tabs__nav-wrap::after) {
  height: 1px;
}
</style>