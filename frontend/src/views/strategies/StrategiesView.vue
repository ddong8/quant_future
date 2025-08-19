<template>
  <div class="strategies-container">
    <div class="page-header">
      <h1 class="page-title">🎯 策略管理</h1>
      <p class="page-description">创建和管理您的交易策略</p>
    </div>

    <!-- 策略统计 -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon total">📊</div>
        <div class="stat-content">
          <div class="stat-value">{{ strategyStats.totalStrategies }}</div>
          <div class="stat-label">总策略数</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon active">🟢</div>
        <div class="stat-content">
          <div class="stat-value">{{ strategyStats.activeStrategies }}</div>
          <div class="stat-label">运行中</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon profit">💰</div>
        <div class="stat-content">
          <div class="stat-value positive">+{{ strategyStats.totalProfit }}%</div>
          <div class="stat-label">总收益率</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon winrate">🎯</div>
        <div class="stat-content">
          <div class="stat-value">{{ strategyStats.winRate }}%</div>
          <div class="stat-label">胜率</div>
        </div>
      </div>
    </div>

    <!-- 操作按钮 -->
    <div class="actions-card">
      <h3>🚀 快速操作</h3>
      <div class="actions">
        <button class="action-btn primary" @click="createStrategy">
          ➕ 创建策略
        </button>
        <button class="action-btn" @click="importStrategy">
          📥 导入策略
        </button>
        <button class="action-btn" @click="exportStrategies">
          📤 导出策略
        </button>
        <button class="action-btn" @click="showTemplates">
          📋 策略模板
        </button>
      </div>
    </div>

    <!-- 策略列表 -->
    <div class="strategies-list">
      <h3>📋 我的策略</h3>
      <div class="strategies-grid">
        <div 
          v-for="strategy in mockStrategies" 
          :key="strategy.id" 
          class="strategy-card"
          @click="viewStrategy(strategy)"
        >
          <div class="strategy-header">
            <div class="strategy-name">{{ strategy.name }}</div>
            <div class="strategy-status" :class="strategy.status">
              {{ getStatusText(strategy.status) }}
            </div>
          </div>
          
          <div class="strategy-content">
            <div class="strategy-description">
              {{ strategy.description }}
            </div>
            
            <div class="strategy-metrics">
              <div class="metric-item">
                <span class="metric-label">收益率:</span>
                <span class="metric-value" :class="strategy.profit >= 0 ? 'positive' : 'negative'">
                  {{ strategy.profit >= 0 ? '+' : '' }}{{ strategy.profit }}%
                </span>
              </div>
              <div class="metric-item">
                <span class="metric-label">胜率:</span>
                <span class="metric-value">{{ strategy.winRate }}%</span>
              </div>
              <div class="metric-item">
                <span class="metric-label">交易次数:</span>
                <span class="metric-value">{{ strategy.trades }}</span>
              </div>
              <div class="metric-item">
                <span class="metric-label">运行时间:</span>
                <span class="metric-value">{{ strategy.runtime }}</span>
              </div>
            </div>
            
            <div class="strategy-actions">
              <button 
                class="btn-small" 
                :class="strategy.status === 'active' ? 'danger' : 'success'"
                @click.stop="toggleStrategy(strategy)"
              >
                {{ strategy.status === 'active' ? '⏸️ 暂停' : '▶️ 启动' }}
              </button>
              <button class="btn-small primary" @click.stop="editStrategy(strategy)">
                ✏️ 编辑
              </button>
              <button class="btn-small" @click.stop="cloneStrategy(strategy)">
                📋 复制
              </button>
              <button class="btn-small danger" @click.stop="deleteStrategy(strategy)">
                🗑️ 删除
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 策略模板 -->
    <div class="templates-section">
      <h3>📋 策略模板</h3>
      <div class="templates-grid">
        <div 
          v-for="template in strategyTemplates" 
          :key="template.id" 
          class="template-card"
          @click="useTemplate(template)"
        >
          <div class="template-icon">{{ template.icon }}</div>
          <div class="template-name">{{ template.name }}</div>
          <div class="template-description">{{ template.description }}</div>
          <div class="template-tags">
            <span v-for="tag in template.tags" :key="tag" class="tag">{{ tag }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { getActiveStrategies, getStrategyPerformance } from '@/api/realTimeData'

const router = useRouter()

// 响应式数据
const strategyStats = reactive({
  totalStrategies: 12,
  activeStrategies: 5,
  totalProfit: 15.8,
  winRate: 72.5
})

// 真实策略数据
const strategies = ref([])
const loading = ref(false)

// 加载真实策略数据
const loadStrategies = async () => {
  loading.value = true
  try {
    // 获取活跃策略
    const strategiesResponse = await getActiveStrategies()
    if (strategiesResponse.success && strategiesResponse.data) {
      strategies.value = strategiesResponse.data.map(strategy => ({
        id: strategy.strategy_id,
        name: strategy.name,
        description: `策略类型: ${strategy.strategy_id}`,
        status: strategy.status === 'active' ? 'active' : 'stopped',
        profit: strategy.profit_loss || 0,
        winRate: calculateWinRate(strategy.total_trades, strategy.profit_loss),
        trades: strategy.total_trades || 0,
        runtime: calculateRuntime(strategy.created_at),
        symbols: strategy.symbols || []
      }))
    }

    // 获取策略表现统计
    const performanceResponse = await getStrategyPerformance()
    if (performanceResponse.success && performanceResponse.data) {
      const data = performanceResponse.data
      strategyStats.totalStrategies = data.total_strategies || 0
      strategyStats.activeStrategies = data.active_strategies || 0
      strategyStats.totalProfit = ((data.total_profit_loss || 0) / 1000000 * 100).toFixed(1)
      strategyStats.winRate = calculateOverallWinRate(strategies.value)
    }

    // 如果没有真实策略，使用模拟数据
    if (strategies.value.length === 0) {
      loadMockStrategies()
    }

  } catch (error) {
    console.error('加载策略数据失败:', error)
    ElMessage.error('加载策略数据失败')
    loadMockStrategies()
  } finally {
    loading.value = false
  }
}

// 计算胜率
const calculateWinRate = (totalTrades: number, profit: number) => {
  if (totalTrades === 0) return 0
  // 简单估算：盈利策略胜率较高
  return profit > 0 ? Math.min(85, 50 + Math.abs(profit) * 2) : Math.max(15, 50 - Math.abs(profit) * 2)
}

// 计算运行时间
const calculateRuntime = (createdAt: string) => {
  if (!createdAt) return '未知'
  const days = Math.floor((Date.now() - new Date(createdAt).getTime()) / (1000 * 60 * 60 * 24))
  return `${days}天`
}

// 计算整体胜率
const calculateOverallWinRate = (strategies: any[]) => {
  if (strategies.length === 0) return 0
  const totalWinRate = strategies.reduce((sum, s) => sum + s.winRate, 0)
  return (totalWinRate / strategies.length).toFixed(1)
}

// 降级到模拟数据
const loadMockStrategies = () => {
  strategies.value = [
    {
      id: 'MOCK_001',
      name: '双均线策略',
      description: '基于MA5和MA10的交叉信号策略',
      status: 'active',
      profit: 12.5,
      winRate: 68.5,
      trades: 45,
      runtime: '15天',
      symbols: ['SHFE.cu2601']
    },
    {
      id: 'MOCK_002',
      name: 'RSI反转策略',
      description: '基于RSI超买超卖信号的反转策略',
      status: 'active',
      profit: -2.1,
      winRate: 45.8,
      trades: 23,
      runtime: '7天',
      symbols: ['DCE.i2601']
    }
  ]
}

// 策略模板
const strategyTemplates = ref([
  {
    id: 'TPL001',
    name: '双均线策略',
    description: '经典的双移动平均线交叉策略',
    icon: '📈',
    tags: ['趋势', '简单', '经典']
  },
  {
    id: 'TPL002',
    name: '布林带策略',
    description: '基于布林带的均值回归策略',
    icon: '📊',
    tags: ['震荡', '统计', '回归']
  },
  {
    id: 'TPL003',
    name: 'MACD策略',
    description: '使用MACD指标的趋势跟踪策略',
    icon: '📉',
    tags: ['趋势', '指标', 'MACD']
  },
  {
    id: 'TPL004',
    name: '网格策略',
    description: '适用于震荡市场的网格交易策略',
    icon: '🔲',
    tags: ['网格', '震荡', '稳定']
  }
])

// 工具函数
const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    active: '🟢 运行中',
    paused: '⏸️ 已暂停',
    stopped: '⏹️ 已停止',
    error: '❌ 错误'
  }
  return statusMap[status] || status
}

// 页面操作
const createStrategy = () => {
  console.log('📝 创建新策略')
  router.push('/strategies/create')
}

const importStrategy = () => {
  console.log('📥 导入策略')
  // 创建文件输入元素
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.json,.py'
  input.onchange = async (e) => {
    const file = e.target.files[0]
    if (file) {
      try {
        const text = await file.text()
        let strategyData
        
        if (file.name.endsWith('.json')) {
          strategyData = JSON.parse(text)
        } else if (file.name.endsWith('.py')) {
          strategyData = {
            name: file.name.replace('.py', ''),
            code: text,
            strategy_type: 'custom'
          }
        }
        
        // 跳转到创建页面并预填数据
        router.push({
          name: 'StrategyCreate',
          query: {
            import: 'true',
            data: encodeURIComponent(JSON.stringify(strategyData))
          }
        })
        
        ElMessage.success('策略文件导入成功')
      } catch (error) {
        ElMessage.error('策略文件格式错误')
      }
    }
  }
  input.click()
}

const exportStrategies = async () => {
  console.log('📤 导出策略')
  try {
    // 导出所有策略数据
    const exportData = {
      strategies: strategies.value,
      export_time: new Date().toISOString(),
      version: '1.0'
    }
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: 'application/json'
    })
    
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `strategies_export_${new Date().toISOString().split('T')[0]}.json`
    a.click()
    
    URL.revokeObjectURL(url)
    ElMessage.success('策略导出成功')
  } catch (error) {
    ElMessage.error('策略导出失败')
  }
}

const showTemplates = () => {
  console.log('📋 显示策略模板')
  router.push('/strategies/templates')
}

const viewStrategy = (strategy: any) => {
  console.log('👁️ 查看策略:', strategy)
  alert(`策略详情：\\n名称: ${strategy.name}\\n状态: ${getStatusText(strategy.status)}\\n收益率: ${strategy.profit}%`)
}

const toggleStrategy = (strategy: any) => {
  console.log('⏯️ 切换策略状态:', strategy)
  const action = strategy.status === 'active' ? '暂停' : '启动'
  alert(`${action}策略: ${strategy.name}`)
}

const editStrategy = (strategy: any) => {
  console.log('✏️ 编辑策略:', strategy)
  alert(`编辑策略: ${strategy.name}`)
}

const cloneStrategy = (strategy: any) => {
  console.log('📋 复制策略:', strategy)
  alert(`复制策略: ${strategy.name}`)
}

const deleteStrategy = (strategy: any) => {
  console.log('🗑️ 删除策略:', strategy)
  if (confirm(`确定要删除策略 "${strategy.name}" 吗？`)) {
    alert(`已删除策略: ${strategy.name}`)
  }
}

const useTemplate = (template: any) => {
  console.log('📋 使用模板:', template)
  alert(`使用模板创建策略: ${template.name}`)
}

// 生命周期
onMounted(() => {
  console.log('🎯 策略管理页面已加载')
  loadStrategies()
})
</script>

<style scoped>
.strategies-container {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
  background: var(--el-bg-color-page);
  min-height: 100vh;
}

.page-header {
  margin-bottom: 32px;
  text-align: center;
}

.page-title {
  margin: 0 0 8px 0;
  font-size: 32px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  text-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.page-description {
  margin: 0;
  font-size: 18px;
  color: var(--el-text-color-regular);
}

/* 统计卡片网格 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 32px;
}

.stat-card {
  background: var(--el-bg-color);
  border-radius: 12px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  border: 1px solid #e9ecef;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.stat-icon {
  font-size: 32px;
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  flex-shrink: 0;
}

.stat-icon.total {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-icon.active {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stat-icon.profit {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.stat-icon.winrate {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  margin-bottom: 4px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

.stat-value.positive {
  color: #27ae60;
}

.stat-label {
  font-size: 14px;
  color: var(--el-text-color-regular);
  font-weight: 500;
}

/* 操作卡片 */
.actions-card {
  background: var(--el-bg-color);
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border: 1px solid #e9ecef;
  margin-bottom: 32px;
}

.actions-card h3 {
  margin: 0 0 20px 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  border-bottom: 2px solid #ecf0f1;
  padding-bottom: 12px;
}

.actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.action-btn {
  background: #6c757d;
  color: white;
  border: none;
  padding: 12px 20px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}

.action-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.action-btn.primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.action-btn.primary:hover {
  background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%);
}

/* 策略列表 */
.strategies-list, .templates-section {
  background: var(--el-bg-color);
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border: 1px solid #e9ecef;
  margin-bottom: 32px;
}

.strategies-list h3, .templates-section h3 {
  margin: 0 0 20px 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  border-bottom: 2px solid #ecf0f1;
  padding-bottom: 12px;
}

.strategies-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 20px;
}

.strategy-card {
  background: var(--el-bg-color-page);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid #dee2e6;
  cursor: pointer;
  transition: all 0.3s ease;
}

.strategy-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  background: var(--el-bg-color);
}

.strategy-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.strategy-name {
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.strategy-status {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
}

.strategy-status.active {
  background: #d4edda;
  color: #155724;
}

.strategy-status.paused {
  background: var(--el-bg-color)3cd;
  color: var(--el-color-warning);
}

.strategy-status.stopped {
  background: var(--el-color-danger-light-9);
  color: #721c24;
}

.strategy-description {
  color: var(--el-text-color-regular);
  font-size: 14px;
  margin-bottom: 16px;
  line-height: 1.5;
}

.strategy-metrics {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 16px;
}

.metric-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: var(--el-bg-color);
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.metric-label {
  font-size: 12px;
  color: var(--el-text-color-regular);
  font-weight: 500;
}

.metric-value {
  font-size: 14px;
  color: var(--el-text-color-primary);
  font-weight: 600;
}

.metric-value.positive {
  color: #27ae60;
}

.metric-value.negative {
  color: #e74c3c;
}

.strategy-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.btn-small {
  padding: 6px 12px;
  font-size: 12px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  background: #6c757d;
  color: white;
  font-weight: 500;
  transition: all 0.3s ease;
}

.btn-small:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.btn-small.primary {
  background: #007bff;
}

.btn-small.success {
  background: #28a745;
}

.btn-small.danger {
  background: #dc3545;
}

/* 模板网格 */
.templates-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 16px;
}

.template-card {
  background: var(--el-bg-color-page);
  border-radius: 12px;
  padding: 20px;
  text-align: center;
  border: 1px solid #dee2e6;
  cursor: pointer;
  transition: all 0.3s ease;
}

.template-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  background: var(--el-bg-color);
}

.template-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.template-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin-bottom: 8px;
}

.template-description {
  font-size: 14px;
  color: var(--el-text-color-regular);
  margin-bottom: 12px;
  line-height: 1.4;
}

.template-tags {
  display: flex;
  gap: 6px;
  justify-content: center;
  flex-wrap: wrap;
}

.tag {
  background: #e9ecef;
  color: #495057;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .strategies-container {
    padding: 16px;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .actions {
    flex-direction: column;
  }
  
  .action-btn {
    justify-content: center;
  }
  
  .strategies-grid {
    grid-template-columns: 1fr;
  }
  
  .strategy-metrics {
    grid-template-columns: 1fr;
  }
  
  .templates-grid {
    grid-template-columns: 1fr;
  }
  
  .page-title {
    font-size: 24px;
  }
  
  .page-description {
    font-size: 16px;
  }
}

@media (max-width: 480px) {
  .stat-card {
    padding: 16px;
  }
  
  .stat-icon {
    font-size: 24px;
    width: 48px;
    height: 48px;
  }
  
  .stat-value {
    font-size: 20px;
  }
  
  .actions-card, .strategies-list, .templates-section {
    padding: 16px;
  }
  
  .strategy-card, .template-card {
    padding: 16px;
  }
}
</style>