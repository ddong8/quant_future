<template>
  <div class="view-container">
    <div class="page-header">
      <h1 class="page-title">📝 策略模板</h1>
      <p class="page-description">选择模板快速创建策略</p>
    </div>

    <!-- 模板分类 -->
    <div class="template-categories">
      <el-tabs v-model="activeCategory" @tab-change="handleCategoryChange">
        <el-tab-pane label="全部模板" name="all" />
        <el-tab-pane label="趋势策略" name="trend" />
        <el-tab-pane label="震荡策略" name="oscillation" />
        <el-tab-pane label="套利策略" name="arbitrage" />
        <el-tab-pane label="自定义" name="custom" />
      </el-tabs>
    </div>

    <!-- 模板网格 -->
    <div class="templates-grid" v-loading="loading">
      <div 
        v-for="template in filteredTemplates" 
        :key="template.id" 
        class="template-card"
        @click="selectTemplate(template)"
      >
        <div class="template-header">
          <div class="template-icon">{{ template.icon }}</div>
          <div class="template-badge" :class="template.difficulty">
            {{ getDifficultyText(template.difficulty) }}
          </div>
        </div>
        
        <div class="template-content">
          <h3 class="template-name">{{ template.name }}</h3>
          <p class="template-description">{{ template.description }}</p>
          
          <div class="template-features">
            <div class="feature-item">
              <span class="feature-label">策略类型:</span>
              <span class="feature-value">{{ template.strategy_type }}</span>
            </div>
            <div class="feature-item">
              <span class="feature-label">适用品种:</span>
              <span class="feature-value">{{ template.suitable_symbols.join(', ') }}</span>
            </div>
            <div class="feature-item">
              <span class="feature-label">预期收益:</span>
              <span class="feature-value positive">{{ template.expected_return }}%</span>
            </div>
          </div>
          
          <div class="template-tags">
            <span v-for="tag in template.tags" :key="tag" class="tag">{{ tag }}</span>
          </div>
        </div>
        
        <div class="template-actions">
          <el-button size="small" @click.stop="previewTemplate(template)">
            👁️ 预览
          </el-button>
          <el-button type="primary" size="small" @click.stop="useTemplate(template)">
            🚀 使用模板
          </el-button>
        </div>
      </div>
    </div>

    <!-- 模板预览对话框 -->
    <el-dialog 
      v-model="previewVisible" 
      :title="`预览模板: ${selectedTemplate?.name}`"
      width="80%"
      class="template-preview-dialog"
    >
      <div v-if="selectedTemplate" class="template-preview">
        <div class="preview-header">
          <div class="template-info">
            <h3>{{ selectedTemplate.name }}</h3>
            <p>{{ selectedTemplate.description }}</p>
          </div>
          <div class="template-stats">
            <div class="stat-item">
              <span class="stat-label">策略类型</span>
              <span class="stat-value">{{ selectedTemplate.strategy_type }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">难度等级</span>
              <span class="stat-value">{{ getDifficultyText(selectedTemplate.difficulty) }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">预期收益</span>
              <span class="stat-value positive">{{ selectedTemplate.expected_return }}%</span>
            </div>
          </div>
        </div>
        
        <div class="preview-code">
          <h4>策略代码预览:</h4>
          <pre class="code-block">{{ selectedTemplate.code }}</pre>
        </div>
        
        <div class="preview-parameters">
          <h4>默认参数:</h4>
          <div class="parameters-grid">
            <div 
              v-for="(value, key) in selectedTemplate.default_parameters" 
              :key="key" 
              class="param-item"
            >
              <span class="param-name">{{ key }}:</span>
              <span class="param-value">{{ value }}</span>
            </div>
          </div>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="previewVisible = false">关闭</el-button>
        <el-button type="primary" @click="useTemplate(selectedTemplate)">
          使用此模板
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { strategyApi } from '@/api/strategy'

const router = useRouter()
const loading = ref(false)
const activeCategory = ref('all')
const previewVisible = ref(false)
const selectedTemplate = ref(null)

// 策略模板数据
const templates = ref([
  {
    id: 'TPL001',
    name: '双均线交叉策略',
    description: '基于快慢均线交叉的经典趋势跟踪策略，适合趋势明显的市场',
    icon: '📈',
    category: 'trend',
    difficulty: 'beginner',
    strategy_type: '趋势跟踪',
    suitable_symbols: ['期货', '股票'],
    expected_return: 15.8,
    tags: ['趋势', '均线', '经典'],
    code: `def main(context):
    """双均线交叉策略"""
    # 获取历史数据
    data = context.get_data()
    
    # 计算移动平均线
    ma5 = data['close'].rolling(5).mean()
    ma20 = data['close'].rolling(20).mean()
    
    # 交易信号
    if ma5.iloc[-1] > ma20.iloc[-1] and ma5.iloc[-2] <= ma20.iloc[-2]:
        # 金叉买入
        context.buy(size=0.5)
    elif ma5.iloc[-1] < ma20.iloc[-1] and ma5.iloc[-2] >= ma20.iloc[-2]:
        # 死叉卖出
        context.sell_all()`,
    default_parameters: {
      fast_period: 5,
      slow_period: 20,
      position_size: 0.5
    }
  },
  {
    id: 'TPL002',
    name: 'RSI反转策略',
    description: '基于RSI指标的超买超卖反转策略，适合震荡市场',
    icon: '📊',
    category: 'oscillation',
    difficulty: 'intermediate',
    strategy_type: '均值回归',
    suitable_symbols: ['期货', '外汇'],
    expected_return: 12.3,
    tags: ['RSI', '反转', '震荡'],
    code: `def main(context):
    """RSI超买超卖策略"""
    # 获取历史数据
    data = context.get_data()
    
    # 计算RSI
    rsi = calculate_rsi(data['close'], 14)
    
    # 交易信号
    if rsi.iloc[-1] < 30:  # 超卖
        context.buy(size=0.3)
    elif rsi.iloc[-1] > 70:  # 超买
        context.sell_all()`,
    default_parameters: {
      rsi_period: 14,
      oversold_level: 30,
      overbought_level: 70,
      position_size: 0.3
    }
  },
  {
    id: 'TPL003',
    name: '布林带策略',
    description: '基于布林带的均值回归策略，利用价格回归特性',
    icon: '📉',
    category: 'oscillation',
    difficulty: 'intermediate',
    strategy_type: '均值回归',
    suitable_symbols: ['期货', '股票'],
    expected_return: 18.5,
    tags: ['布林带', '回归', '统计'],
    code: `def main(context):
    """布林带策略"""
    # 获取历史数据
    data = context.get_data()
    
    # 计算布林带
    ma20 = data['close'].rolling(20).mean()
    std20 = data['close'].rolling(20).std()
    upper = ma20 + 2 * std20
    lower = ma20 - 2 * std20
    
    current_price = data['close'].iloc[-1]
    
    # 交易信号
    if current_price < lower.iloc[-1]:  # 价格触及下轨
        context.buy(size=0.4)
    elif current_price > upper.iloc[-1]:  # 价格触及上轨
        context.sell_all()`,
    default_parameters: {
      period: 20,
      std_multiplier: 2,
      position_size: 0.4
    }
  },
  {
    id: 'TPL004',
    name: '网格交易策略',
    description: '适用于震荡市场的网格交易策略，通过多次买卖获利',
    icon: '🔲',
    category: 'oscillation',
    difficulty: 'advanced',
    strategy_type: '网格交易',
    suitable_symbols: ['期货', '数字货币'],
    expected_return: 22.1,
    tags: ['网格', '震荡', '高频'],
    code: `def main(context):
    """网格交易策略"""
    # 获取当前价格
    current_price = context.get_current_price()
    
    # 网格参数
    grid_size = 0.02  # 网格间距2%
    max_grids = 10    # 最大网格数
    
    # 计算网格价位
    base_price = context.get_base_price()
    
    for i in range(1, max_grids + 1):
        buy_price = base_price * (1 - grid_size * i)
        sell_price = base_price * (1 + grid_size * i)
        
        if current_price <= buy_price:
            context.buy(size=0.1)
        elif current_price >= sell_price:
            context.sell(size=0.1)`,
    default_parameters: {
      grid_size: 0.02,
      max_grids: 10,
      position_size: 0.1
    }
  }
])

// 过滤后的模板
const filteredTemplates = computed(() => {
  if (activeCategory.value === 'all') {
    return templates.value
  }
  return templates.value.filter(template => template.category === activeCategory.value)
})

// 获取难度等级文本
const getDifficultyText = (difficulty: string) => {
  const difficultyMap = {
    beginner: '初级',
    intermediate: '中级',
    advanced: '高级'
  }
  return difficultyMap[difficulty] || difficulty
}

// 处理分类切换
const handleCategoryChange = (category: string) => {
  activeCategory.value = category
}

// 选择模板
const selectTemplate = (template: any) => {
  selectedTemplate.value = template
}

// 预览模板
const previewTemplate = (template: any) => {
  selectedTemplate.value = template
  previewVisible.value = true
}

// 使用模板
const useTemplate = (template: any) => {
  if (!template) return
  
  // 跳转到创建策略页面，并传递模板数据
  router.push({
    name: 'StrategyCreate',
    query: {
      template: template.id,
      name: template.name,
      code: encodeURIComponent(template.code)
    }
  })
  
  ElMessage.success(`已选择模板: ${template.name}`)
}

// 加载模板数据
const loadTemplates = async () => {
  loading.value = true
  try {
    // 这里可以调用真实的API获取模板数据
    // const response = await strategyApi.getStrategyTemplates()
    // if (response.success) {
    //   templates.value = response.data
    // }
    
    // 目前使用模拟数据
    await new Promise(resolve => setTimeout(resolve, 500))
  } catch (error) {
    console.error('加载模板失败:', error)
    ElMessage.error('加载模板失败')
  } finally {
    loading.value = false
  }
}

// 页面初始化
onMounted(() => {
  console.log('📝 策略模板页面已加载')
  loadTemplates()
})
</script>
<style scoped>
.view-container {
  padding: 24px;
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
}

.page-description {
  margin: 0;
  font-size: 18px;
  color: var(--el-text-color-regular);
}

.template-categories {
  background: var(--el-bg-color);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.templates-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 24px;
}

.template-card {
  background: var(--el-bg-color);
  border-radius: 12px;
  padding: 24px;
  border: 1px solid var(--el-border-color-light);
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
}

.template-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.15);
  border-color: var(--el-color-primary);
}

.template-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.template-icon {
  font-size: 32px;
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: white;
}

.template-badge {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
}

.template-badge.beginner {
  background: #d4edda;
  color: #155724;
}

.template-badge.intermediate {
  background: #fff3cd;
  color: #856404;
}

.template-badge.advanced {
  background: #f8d7da;
  color: #721c24;
}

.template-content {
  margin-bottom: 20px;
}

.template-name {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.template-description {
  margin: 0 0 16px 0;
  font-size: 14px;
  color: var(--el-text-color-regular);
  line-height: 1.5;
}

.template-features {
  margin-bottom: 16px;
}

.feature-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.feature-item:last-child {
  border-bottom: none;
}

.feature-label {
  font-size: 12px;
  color: var(--el-text-color-regular);
  font-weight: 500;
}

.feature-value {
  font-size: 12px;
  color: var(--el-text-color-primary);
  font-weight: 600;
}

.feature-value.positive {
  color: #27ae60;
}

.template-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}

.tag {
  background: #e9ecef;
  color: #495057;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
}

.template-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

/* 预览对话框样式 */
.template-preview-dialog :deep(.el-dialog__body) {
  padding: 20px;
}

.template-preview {
  max-height: 70vh;
  overflow-y: auto;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--el-border-color-light);
}

.template-info h3 {
  margin: 0 0 8px 0;
  font-size: 20px;
  color: var(--el-text-color-primary);
}

.template-info p {
  margin: 0;
  color: var(--el-text-color-regular);
}

.template-stats {
  display: flex;
  gap: 24px;
}

.stat-item {
  text-align: center;
}

.stat-label {
  display: block;
  font-size: 12px;
  color: var(--el-text-color-regular);
  margin-bottom: 4px;
}

.stat-value {
  display: block;
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.stat-value.positive {
  color: #27ae60;
}

.preview-code {
  margin-bottom: 24px;
}

.preview-code h4 {
  margin: 0 0 12px 0;
  font-size: 16px;
  color: var(--el-text-color-primary);
}

.code-block {
  background: #f8f9fa;
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  padding: 16px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  line-height: 1.5;
  overflow-x: auto;
  white-space: pre-wrap;
  color: var(--el-text-color-primary);
}

.preview-parameters h4 {
  margin: 0 0 12px 0;
  font-size: 16px;
  color: var(--el-text-color-primary);
}

.parameters-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.param-item {
  background: var(--el-bg-color-page);
  padding: 12px;
  border-radius: 8px;
  border: 1px solid var(--el-border-color-light);
}

.param-name {
  font-weight: 500;
  color: var(--el-text-color-regular);
  margin-right: 8px;
}

.param-value {
  font-weight: 600;
  color: var(--el-text-color-primary);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .view-container {
    padding: 16px;
  }
  
  .templates-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .template-card {
    padding: 16px;
  }
  
  .template-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .preview-header {
    flex-direction: column;
    gap: 16px;
  }
  
  .template-stats {
    flex-direction: column;
    gap: 12px;
  }
  
  .parameters-grid {
    grid-template-columns: 1fr;
  }
}
</style>
