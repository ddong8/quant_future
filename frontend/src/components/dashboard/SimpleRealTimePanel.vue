<template>
  <div class="simple-realtime-panel">
    <el-card>
      <template #header>
        <div class="panel-header">
          <span>实时数据状态</span>
          <div class="header-actions">
            <el-tag type="success" size="small">简化模式</el-tag>
            <el-button size="small" @click="refreshData" :loading="loading">
              <el-icon><Refresh /></el-icon>
            </el-button>
          </div>
        </div>
      </template>

      <!-- 系统状态概览 -->
      <div class="status-overview">
        <div class="status-item">
          <div class="status-icon">
            <el-icon size="24" color="#67c23a">
              <Connection />
            </el-icon>
          </div>
          <div class="status-info">
            <div class="status-title">市场数据</div>
            <div class="status-desc">已连接</div>
          </div>
        </div>

        <div class="status-item">
          <div class="status-icon">
            <el-icon size="24" color="#67c23a">
              <Cpu />
            </el-icon>
          </div>
          <div class="status-info">
            <div class="status-title">算法引擎</div>
            <div class="status-desc">运行中</div>
          </div>
        </div>

        <div class="status-item">
          <div class="status-icon">
            <el-icon size="24" color="#67c23a">
              <Warning />
            </el-icon>
          </div>
          <div class="status-info">
            <div class="status-title">风险监控</div>
            <div class="status-desc">风险等级: 低</div>
          </div>
        </div>
      </div>

      <!-- 实时数据统计 -->
      <div class="data-stats">
        <el-row :gutter="16">
          <el-col :span="6">
            <div class="stat-item">
              <div class="stat-value">{{ stats.activeStrategies }}</div>
              <div class="stat-label">活跃策略</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-item">
              <div class="stat-value">{{ stats.pendingOrders }}</div>
              <div class="stat-label">待处理订单</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-item">
              <div class="stat-value">{{ stats.contractsCount }}</div>
              <div class="stat-label">可交易合约</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-item">
              <div class="stat-value">{{ stats.riskScore }}</div>
              <div class="stat-label">风险评分</div>
            </div>
          </el-col>
        </el-row>
      </div>

      <!-- 最新交易信号 -->
      <div class="recent-signals">
        <h4>最新交易信号</h4>
        <div v-if="signals.length === 0" class="empty-signals">
          <el-empty description="暂无交易信号" :image-size="60" />
        </div>
        <div v-else class="signals-list">
          <div 
            v-for="(signal, index) in signals" 
            :key="index"
            class="signal-item"
          >
            <div class="signal-symbol">{{ signal.symbol }}</div>
            <el-tag :type="signal.type" size="small">
              {{ signal.action }}
            </el-tag>
            <div class="signal-time">{{ signal.time }}</div>
          </div>
        </div>
      </div>

      <!-- 热门合约行情 -->
      <div class="popular-quotes">
        <h4>热门合约</h4>
        <div v-if="quotes.length === 0" class="empty-quotes">
          <el-empty description="暂无行情数据" :image-size="60" />
        </div>
        <div v-else class="quotes-list">
          <div 
            v-for="(quote, index) in quotes" 
            :key="index"
            class="quote-item"
          >
            <div class="quote-symbol">{{ quote.symbol }}</div>
            <div class="quote-price">{{ quote.price }}</div>
            <div class="quote-change" :class="quote.changeClass">
              {{ quote.change }}
            </div>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Refresh, Connection, Cpu, Warning } from '@element-plus/icons-vue'

// 响应式数据
const loading = ref(false)

// 统计数据
const stats = ref({
  activeStrategies: 3,
  pendingOrders: 5,
  contractsCount: 128,
  riskScore: 75
})

// 模拟信号数据
const signals = ref([
  {
    symbol: 'SHFE.cu2601',
    action: 'BUY',
    type: 'success',
    time: '14:23:15'
  },
  {
    symbol: 'DCE.i2601',
    action: 'SELL',
    type: 'danger',
    time: '14:20:32'
  },
  {
    symbol: 'CZCE.MA601',
    action: 'HOLD',
    type: 'info',
    time: '14:18:45'
  }
])

// 模拟行情数据
const quotes = ref([
  {
    symbol: 'SHFE.cu2601',
    price: '71,520',
    change: '+0.17%',
    changeClass: 'positive'
  },
  {
    symbol: 'DCE.i2601',
    price: '820',
    change: '-0.61%',
    changeClass: 'negative'
  },
  {
    symbol: 'CZCE.MA601',
    price: '2,845',
    change: '+0.35%',
    changeClass: 'positive'
  },
  {
    symbol: 'SHFE.al2601',
    price: '19,250',
    change: '-0.12%',
    changeClass: 'negative'
  },
  {
    symbol: 'DCE.j2601',
    price: '2,156',
    change: '+0.89%',
    changeClass: 'positive'
  }
])

// 刷新数据
const refreshData = async () => {
  loading.value = true
  try {
    console.log('🔄 刷新简化实时数据面板...')
    
    // 模拟API调用延迟
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // 更新统计数据
    stats.value = {
      activeStrategies: Math.floor(Math.random() * 10) + 1,
      pendingOrders: Math.floor(Math.random() * 20) + 1,
      contractsCount: 128 + Math.floor(Math.random() * 10),
      riskScore: 70 + Math.floor(Math.random() * 20)
    }
    
    // 更新信号时间
    const now = new Date()
    signals.value.forEach(signal => {
      const randomMinutes = Math.floor(Math.random() * 30)
      const time = new Date(now.getTime() - randomMinutes * 60000)
      signal.time = time.toLocaleTimeString('zh-CN', { 
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      })
    })
    
    console.log('✅ 简化实时数据面板刷新完成')
  } catch (error) {
    console.error('❌ 刷新简化实时数据面板失败:', error)
  } finally {
    loading.value = false
  }
}

// 组件挂载
onMounted(() => {
  console.log('🔄 SimpleRealTimePanel 组件已挂载')
  refreshData()
})
</script>

<style scoped>
.simple-realtime-panel {
  height: 100%;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.status-overview {
  display: flex;
  justify-content: space-around;
  margin-bottom: 20px;
  padding: 15px 0;
  border-bottom: 1px solid #f0f0f0;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.status-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: #f5f7fa;
}

.status-info {
  display: flex;
  flex-direction: column;
}

.status-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 2px;
}

.status-desc {
  font-size: 12px;
  color: #909399;
}

.data-stats {
  margin-bottom: 20px;
  padding: 15px 0;
  border-bottom: 1px solid #f0f0f0;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 12px;
  color: #909399;
}

.recent-signals, .popular-quotes {
  margin-bottom: 15px;
}

.recent-signals h4, .popular-quotes h4 {
  margin: 0 0 10px 0;
  font-size: 14px;
  color: #606266;
}

.empty-signals, .empty-quotes {
  text-align: center;
  padding: 20px;
}

.signals-list, .quotes-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.signal-item, .quote-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background-color: #f8f9fa;
  border-radius: 4px;
  font-size: 12px;
}

.signal-symbol, .quote-symbol {
  font-weight: 600;
  color: #303133;
}

.signal-time {
  color: #909399;
}

.quote-price {
  font-weight: 600;
  color: #303133;
}

.quote-change {
  font-weight: 600;
}

.positive {
  color: #67c23a;
}

.negative {
  color: #f56c6c;
}
</style>