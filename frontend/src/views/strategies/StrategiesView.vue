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

// 响应式数据
const strategyStats = reactive({
  totalStrategies: 12,
  activeStrategies: 5,
  totalProfit: 15.8,
  winRate: 72.5
})

// 模拟策略数据
const mockStrategies = ref([
  {
    id: 'STR001',
    name: '均线突破策略',
    description: '基于移动平均线的突破交易策略，适用于趋势市场',
    status: 'active',
    profit: 12.5,
    winRate: 68.5,
    trades: 45,
    runtime: '15天'
  },
  {
    id: 'STR002',
    name: '网格交易策略',
    description: '在震荡市场中通过网格交易获取稳定收益',
    status: 'paused',
    profit: 8.3,
    winRate: 75.2,
    trades: 128,
    runtime: '30天'
  },
  {
    id: 'STR003',
    name: 'RSI反转策略',
    description: '利用RSI指标识别超买超卖区域进行反转交易',
    status: 'active',
    profit: -2.1,
    winRate: 45.8,
    trades: 23,
    runtime: '7天'
  },
  {
    id: 'STR004',
    name: '动量追踪策略',
    description: '追踪市场动量，在强势趋势中获取收益',
    status: 'stopped',
    profit: 25.7,
    winRate: 82.1,
    trades: 67,
    runtime: '45天'
  }
])

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
  alert('创建策略功能开发中...')
}

const importStrategy = () => {
  console.log('📥 导入策略')
  alert('导入策略功能开发中...')
}

const exportStrategies = () => {
  console.log('📤 导出策略')
  alert('导出策略功能开发中...')
}

const showTemplates = () => {
  console.log('📋 显示策略模板')
  alert('策略模板功能开发中...')
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