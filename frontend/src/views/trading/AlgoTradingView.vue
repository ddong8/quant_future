<template>
  <div class="algo-trading">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">算法交易引擎</h1>
        <p class="page-description">基于tqsdk的实时算法交易系统</p>
      </div>
      <div class="header-right">
        <el-button 
          :type="engineStatus.status === 'running' ? 'danger' : 'primary'"
          @click="toggleEngine"
          :loading="engineLoading"
        >
          <el-icon><VideoPlay v-if="engineStatus.status !== 'running'" /><VideoPause v-else /></el-icon>
          {{ engineStatus.status === 'running' ? '停止引擎' : '启动引擎' }}
        </el-button>
        <el-button @click="refreshData" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 引擎状态卡片 -->
    <div class="status-cards">
      <el-card class="status-card">
        <div class="status-item">
          <div class="status-label">引擎状态</div>
          <div class="status-value">
            <el-tag :type="getStatusType(engineStatus.status)">
              {{ getStatusText(engineStatus.status) }}
            </el-tag>
          </div>
        </div>
      </el-card>
      
      <el-card class="status-card">
        <div class="status-item">
          <div class="status-label">活跃策略</div>
          <div class="status-value">{{ engineStatus.active_strategies || 0 }}</div>
        </div>
      </el-card>
      
      <el-card class="status-card">
        <div class="status-item">
          <div class="status-label">待处理订单</div>
          <div class="status-value">{{ engineStatus.pending_orders || 0 }}</div>
        </div>
      </el-card>
      
      <el-card class="status-card">
        <div class="status-item">
          <div class="status-label">持仓数量</div>
          <div class="status-value">{{ engineStatus.total_positions || 0 }}</div>
        </div>
      </el-card>
    </div>

    <!-- 主要内容区域 -->
    <el-row :gutter="20">
      <!-- 左侧：策略管理 -->
      <el-col :span="12">
        <el-card title="策略管理">
          <template #header>
            <div class="card-header">
              <span>策略管理</span>
              <el-button type="primary" size="small" @click="showAddStrategyDialog = true">
                <el-icon><Plus /></el-icon>
                添加策略
              </el-button>
            </div>
          </template>
          
          <div class="strategies-list">
            <div v-if="strategies.length === 0" class="empty-state">
              <el-empty description="暂无活跃策略" />
            </div>
            <div v-else>
              <div 
                v-for="strategy in strategies" 
                :key="strategy.strategy_id"
                class="strategy-item"
              >
                <div class="strategy-info">
                  <div class="strategy-name">{{ strategy.name }}</div>
                  <div class="strategy-details">
                    <span class="strategy-type">{{ strategy.strategy_id }}</span>
                    <el-tag size="small" :type="strategy.status === 'active' ? 'success' : 'info'">
                      {{ strategy.status }}
                    </el-tag>
                  </div>
                  <div class="strategy-symbols">
                    <el-tag v-for="symbol in strategy.symbols" :key="symbol" size="small" effect="plain">
                      {{ symbol }}
                    </el-tag>
                  </div>
                  <div class="strategy-stats">
                    <span>交易次数: {{ strategy.total_trades }}</span>
                    <span :class="strategy.profit_loss >= 0 ? 'profit' : 'loss'">
                      盈亏: {{ strategy.profit_loss.toFixed(2) }}
                    </span>
                  </div>
                </div>
                <div class="strategy-actions">
                  <el-button size="small" type="danger" @click="removeStrategy(strategy.strategy_id)">
                    移除
                  </el-button>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：交易信号和订单 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <el-tabs v-model="rightTabActive">
              <el-tab-pane label="交易信号" name="signals" />
              <el-tab-pane label="订单历史" name="orders" />
              <el-tab-pane label="策略表现" name="performance" />
            </el-tabs>
          </template>

          <!-- 交易信号 -->
          <div v-if="rightTabActive === 'signals'" class="signals-panel">
            <div v-if="signals.length === 0" class="empty-state">
              <el-empty description="暂无交易信号" />
            </div>
            <div v-else class="signals-list">
              <div v-for="signal in signals" :key="signal.timestamp" class="signal-item">
                <div class="signal-header">
                  <span class="signal-symbol">{{ signal.symbol }}</span>
                  <el-tag :type="signal.signal_type === 'buy' ? 'success' : 'danger'" size="small">
                    {{ signal.signal_type.toUpperCase() }}
                  </el-tag>
                  <span class="signal-time">{{ formatTime(signal.timestamp) }}</span>
                </div>
                <div class="signal-details">
                  <span>策略: {{ signal.strategy_id }}</span>
                  <span>价格: {{ signal.price }}</span>
                  <span>置信度: {{ (signal.confidence * 100).toFixed(1) }}%</span>
                </div>
                <div class="signal-reason">{{ signal.reason }}</div>
              </div>
            </div>
          </div>

          <!-- 订单历史 -->
          <div v-if="rightTabActive === 'orders'" class="orders-panel">
            <div v-if="orders.length === 0" class="empty-state">
              <el-empty description="暂无订单记录" />
            </div>
            <div v-else class="orders-list">
              <div v-for="order in orders" :key="order.order_id" class="order-item">
                <div class="order-header">
                  <span class="order-symbol">{{ order.symbol }}</span>
                  <el-tag :type="getOrderStatusType(order.status)" size="small">
                    {{ order.status }}
                  </el-tag>
                  <span class="order-time">{{ formatTime(order.created_at) }}</span>
                </div>
                <div class="order-details">
                  <span>方向: {{ order.direction }}</span>
                  <span>数量: {{ order.volume }}</span>
                  <span>价格: {{ order.price }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 策略表现 -->
          <div v-if="rightTabActive === 'performance'" class="performance-panel">
            <div class="performance-summary">
              <div class="perf-item">
                <div class="perf-label">总策略数</div>
                <div class="perf-value">{{ performance.total_strategies || 0 }}</div>
              </div>
              <div class="perf-item">
                <div class="perf-label">总交易次数</div>
                <div class="perf-value">{{ performance.total_trades || 0 }}</div>
              </div>
              <div class="perf-item">
                <div class="perf-label">总盈亏</div>
                <div class="perf-value" :class="(performance.total_profit_loss || 0) >= 0 ? 'profit' : 'loss'">
                  {{ (performance.total_profit_loss || 0).toFixed(2) }}
                </div>
              </div>
              <div class="perf-item">
                <div class="perf-label">活跃策略</div>
                <div class="perf-value">{{ performance.active_strategies || 0 }}</div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 添加策略对话框 -->
    <el-dialog v-model="showAddStrategyDialog" title="添加交易策略" width="600px">
      <el-form :model="newStrategy" label-width="100px">
        <el-form-item label="策略ID">
          <el-input v-model="newStrategy.strategy_id" placeholder="输入策略ID" />
        </el-form-item>
        <el-form-item label="策略类型">
          <el-select v-model="newStrategy.strategy_type" placeholder="选择策略类型">
            <el-option label="双均线策略" value="dual_ma" />
            <el-option label="RSI反转策略" value="rsi_reversal" />
          </el-select>
        </el-form-item>
        <el-form-item label="策略名称">
          <el-input v-model="newStrategy.name" placeholder="输入策略名称" />
        </el-form-item>
        <el-form-item label="交易品种">
          <el-select v-model="newStrategy.symbols" multiple placeholder="选择交易品种">
            <el-option label="沪铜主力" value="SHFE.cu2601" />
            <el-option label="沪金主力" value="SHFE.au2612" />
            <el-option label="螺纹钢主力" value="SHFE.rb2601" />
          </el-select>
        </el-form-item>
        <el-form-item label="参数配置">
          <el-input 
            v-model="parametersJson" 
            type="textarea" 
            :rows="3"
            placeholder='{"ma_short": 5, "ma_long": 10}'
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddStrategyDialog = false">取消</el-button>
        <el-button type="primary" @click="addStrategy" :loading="addStrategyLoading">
          添加策略
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { VideoPlay, VideoPause, Refresh, Plus } from '@element-plus/icons-vue'
import {
  getAlgoTradingStatus,
  getActiveStrategies,
  getSignalHistory,
  getOrderHistory,
  getStrategyPerformance
} from '@/api/realTimeData'

// 响应式数据
const loading = ref(false)
const engineLoading = ref(false)
const rightTabActive = ref('signals')
const showAddStrategyDialog = ref(false)
const addStrategyLoading = ref(false)

// 引擎状态
const engineStatus = ref({
  status: 'stopped',
  is_initialized: false,
  active_strategies: 0,
  pending_orders: 0,
  total_positions: 0,
  uptime: '',
  last_update: ''
})

// 策略列表
const strategies = ref([])

// 交易信号
const signals = ref([])

// 订单历史
const orders = ref([])

// 策略表现
const performance = ref({
  total_strategies: 0,
  total_trades: 0,
  total_profit_loss: 0,
  active_strategies: 0
})

// 新策略表单
const newStrategy = ref({
  strategy_id: '',
  strategy_type: '',
  name: '',
  symbols: [],
  parameters: {}
})

const parametersJson = ref('{"ma_short": 5, "ma_long": 10}')

// 定时器
let refreshTimer: NodeJS.Timeout | null = null

// 计算属性
const getStatusType = (status: string) => {
  switch (status) {
    case 'running': return 'success'
    case 'stopped': return 'info'
    case 'error': return 'danger'
    default: return 'warning'
  }
}

const getStatusText = (status: string) => {
  switch (status) {
    case 'running': return '运行中'
    case 'stopped': return '已停止'
    case 'starting': return '启动中'
    case 'error': return '错误'
    default: return '未知'
  }
}

const getOrderStatusType = (status: string) => {
  switch (status) {
    case 'filled': return 'success'
    case 'cancelled': return 'info'
    case 'rejected': return 'danger'
    default: return 'warning'
  }
}

// 格式化时间
const formatTime = (timestamp: string) => {
  return new Date(timestamp).toLocaleString()
}

// 加载引擎状态
const loadEngineStatus = async () => {
  try {
    const response = await getAlgoTradingStatus()
    if (response.success) {
      engineStatus.value = response.data
    }
  } catch (error) {
    console.error('加载引擎状态失败:', error)
  }
}

// 加载策略列表
const loadStrategies = async () => {
  try {
    const response = await getActiveStrategies()
    if (response.success) {
      strategies.value = response.data
    }
  } catch (error) {
    console.error('加载策略列表失败:', error)
  }
}

// 加载交易信号
const loadSignals = async () => {
  try {
    const response = await getSignalHistory()
    if (response.success) {
      signals.value = response.data.signals || []
    }
  } catch (error) {
    console.error('加载交易信号失败:', error)
  }
}

// 加载订单历史
const loadOrders = async () => {
  try {
    const response = await getOrderHistory()
    if (response.success) {
      orders.value = response.data.orders || []
    }
  } catch (error) {
    console.error('加载订单历史失败:', error)
  }
}

// 加载策略表现
const loadPerformance = async () => {
  try {
    const response = await getStrategyPerformance()
    if (response.success) {
      performance.value = response.data
    }
  } catch (error) {
    console.error('加载策略表现失败:', error)
  }
}

// 刷新所有数据
const refreshData = async () => {
  loading.value = true
  try {
    await Promise.all([
      loadEngineStatus(),
      loadStrategies(),
      loadSignals(),
      loadOrders(),
      loadPerformance()
    ])
  } finally {
    loading.value = false
  }
}

// 切换引擎状态
const toggleEngine = async () => {
  engineLoading.value = true
  try {
    const action = engineStatus.value.status === 'running' ? 'stop' : 'start'
    
    // 这里需要调用控制引擎的API
    // const response = await controlEngine({ action })
    
    ElMessage.success(`引擎${action === 'start' ? '启动' : '停止'}成功`)
    await loadEngineStatus()
  } catch (error) {
    console.error('控制引擎失败:', error)
    ElMessage.error('操作失败')
  } finally {
    engineLoading.value = false
  }
}

// 添加策略
const addStrategy = async () => {
  addStrategyLoading.value = true
  try {
    const strategyData = {
      ...newStrategy.value,
      parameters: JSON.parse(parametersJson.value)
    }
    
    // 这里需要调用添加策略的API
    // const response = await addTradingStrategy(strategyData)
    
    ElMessage.success('策略添加成功')
    showAddStrategyDialog.value = false
    await loadStrategies()
  } catch (error) {
    console.error('添加策略失败:', error)
    ElMessage.error('添加策略失败')
  } finally {
    addStrategyLoading.value = false
  }
}

// 移除策略
const removeStrategy = async (strategyId: string) => {
  try {
    await ElMessageBox.confirm('确定要移除这个策略吗？', '确认', {
      type: 'warning'
    })
    
    // 这里需要调用移除策略的API
    // const response = await removeTradingStrategy(strategyId)
    
    ElMessage.success('策略移除成功')
    await loadStrategies()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('移除策略失败:', error)
      ElMessage.error('移除策略失败')
    }
  }
}

// 启动定时刷新
const startAutoRefresh = () => {
  refreshTimer = setInterval(() => {
    refreshData()
  }, 10000) // 10秒刷新一次
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
  refreshData()
  startAutoRefresh()
})

// 组件卸载
onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style scoped>
.algo-trading {
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

.status-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 20px;
}

.status-card {
  text-align: center;
}

.status-item {
  padding: 10px;
}

.status-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.status-value {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.strategies-list {
  max-height: 400px;
  overflow-y: auto;
}

.strategy-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 15px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  margin-bottom: 10px;
}

.strategy-info {
  flex: 1;
}

.strategy-name {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
}

.strategy-details {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.strategy-type {
  font-size: 12px;
  color: #909399;
}

.strategy-symbols {
  margin-bottom: 8px;
}

.strategy-symbols .el-tag {
  margin-right: 5px;
}

.strategy-stats {
  display: flex;
  gap: 15px;
  font-size: 12px;
  color: #606266;
}

.profit {
  color: #67c23a;
}

.loss {
  color: #f56c6c;
}

.signals-list, .orders-list {
  max-height: 400px;
  overflow-y: auto;
}

.signal-item, .order-item {
  padding: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  margin-bottom: 8px;
}

.signal-header, .order-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.signal-symbol, .order-symbol {
  font-weight: 600;
}

.signal-time, .order-time {
  font-size: 12px;
  color: #909399;
}

.signal-details, .order-details {
  display: flex;
  gap: 15px;
  font-size: 12px;
  color: #606266;
  margin-bottom: 5px;
}

.signal-reason {
  font-size: 12px;
  color: #909399;
  font-style: italic;
}

.performance-summary {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.perf-item {
  text-align: center;
  padding: 20px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
}

.perf-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.perf-value {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.empty-state {
  text-align: center;
  padding: 40px;
}
</style>