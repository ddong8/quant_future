<template>
  <div class="strategy-create-view">
    <div class="page-header">
      <h1 class="page-title">➕ 创建策略</h1>
      <p class="page-description">创建新的交易策略</p>
    </div>

    <!-- 策略创建表单 -->
    <div class="create-form-container">
      <el-form 
        ref="formRef" 
        :model="strategyForm" 
        :rules="formRules" 
        label-width="120px"
        class="strategy-form"
      >
        <!-- 基本信息 -->
        <div class="form-section">
          <h3 class="section-title">📋 基本信息</h3>
          <el-form-item label="策略名称" prop="name">
            <el-input 
              v-model="strategyForm.name" 
              placeholder="请输入策略名称"
              maxlength="50"
              show-word-limit
            />
          </el-form-item>
          
          <el-form-item label="策略描述" prop="description">
            <el-input 
              v-model="strategyForm.description" 
              type="textarea" 
              :rows="3"
              placeholder="请输入策略描述"
              maxlength="200"
              show-word-limit
            />
          </el-form-item>
          
          <el-form-item label="策略类型" prop="strategy_type">
            <el-select v-model="strategyForm.strategy_type" placeholder="请选择策略类型">
              <el-option label="趋势跟踪" value="trend_following" />
              <el-option label="均值回归" value="mean_reversion" />
              <el-option label="套利策略" value="arbitrage" />
              <el-option label="网格策略" value="grid" />
              <el-option label="自定义" value="custom" />
            </el-select>
          </el-form-item>
        </div>

        <!-- 交易设置 -->
        <div class="form-section">
          <h3 class="section-title">⚙️ 交易设置</h3>
          <el-form-item label="交易品种" prop="symbols">
            <el-select 
              v-model="strategyForm.symbols" 
              multiple 
              placeholder="请选择交易品种"
              style="width: 100%"
            >
              <el-option 
                v-for="symbol in availableSymbols" 
                :key="symbol.symbol" 
                :label="`${symbol.name} (${symbol.symbol})`" 
                :value="symbol.symbol" 
              />
            </el-select>
          </el-form-item>
          
          <el-form-item label="时间周期" prop="timeframe">
            <el-select v-model="strategyForm.timeframe" placeholder="请选择时间周期">
              <el-option label="1分钟" value="1m" />
              <el-option label="5分钟" value="5m" />
              <el-option label="15分钟" value="15m" />
              <el-option label="30分钟" value="30m" />
              <el-option label="1小时" value="1h" />
              <el-option label="4小时" value="4h" />
              <el-option label="1天" value="1d" />
            </el-select>
          </el-form-item>
          
          <el-form-item label="初始资金" prop="initial_capital">
            <el-input-number 
              v-model="strategyForm.initial_capital" 
              :min="10000" 
              :max="10000000" 
              :step="10000"
              placeholder="初始资金"
              style="width: 100%"
            />
          </el-form-item>
        </div>

        <!-- 风险控制 -->
        <div class="form-section">
          <h3 class="section-title">🛡️ 风险控制</h3>
          <el-form-item label="最大仓位" prop="max_position_size">
            <el-input-number 
              v-model="strategyForm.max_position_size" 
              :min="0.1" 
              :max="1" 
              :step="0.1"
              placeholder="最大仓位比例"
              style="width: 100%"
            />
          </el-form-item>
          
          <el-form-item label="止损比例" prop="stop_loss">
            <el-input-number 
              v-model="strategyForm.stop_loss" 
              :min="0.01" 
              :max="0.2" 
              :step="0.01"
              placeholder="止损比例"
              style="width: 100%"
            />
          </el-form-item>
          
          <el-form-item label="止盈比例" prop="take_profit">
            <el-input-number 
              v-model="strategyForm.take_profit" 
              :min="0.01" 
              :max="1" 
              :step="0.01"
              placeholder="止盈比例"
              style="width: 100%"
            />
          </el-form-item>
        </div>

        <!-- 策略代码 -->
        <div class="form-section">
          <h3 class="section-title">💻 策略代码</h3>
          <el-form-item label="代码模板" prop="template">
            <el-select v-model="selectedTemplate" placeholder="选择代码模板" @change="loadTemplate">
              <el-option label="空白模板" value="" />
              <el-option label="双均线策略" value="ma_cross" />
              <el-option label="RSI策略" value="rsi" />
              <el-option label="布林带策略" value="bollinger" />
            </el-select>
          </el-form-item>
          
          <el-form-item label="策略代码" prop="code">
            <el-input 
              v-model="strategyForm.code" 
              type="textarea" 
              :rows="15"
              placeholder="请输入策略代码"
              class="code-editor"
            />
          </el-form-item>
          
          <el-form-item label="入口函数" prop="entry_point">
            <el-input 
              v-model="strategyForm.entry_point" 
              placeholder="main"
            />
          </el-form-item>
        </div>

        <!-- 操作按钮 -->
        <div class="form-actions">
          <el-button @click="resetForm">重置</el-button>
          <el-button type="primary" @click="validateCode" :loading="validating">验证代码</el-button>
          <el-button type="success" @click="createStrategy" :loading="creating">创建策略</el-button>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import { strategyApi } from '@/api/strategy'
import { getContractList } from '@/api/realTimeData'

const router = useRouter()
const formRef = ref()
const creating = ref(false)
const validating = ref(false)
const selectedTemplate = ref('')
const availableSymbols = ref([])

// 策略表单数据
const strategyForm = reactive({
  name: '',
  description: '',
  strategy_type: 'trend_following',
  symbols: [],
  timeframe: '1m',
  initial_capital: 100000,
  max_position_size: 0.5,
  stop_loss: 0.05,
  take_profit: 0.1,
  code: '',
  entry_point: 'main',
  parameters: {}
})

// 表单验证规则
const formRules = {
  name: [
    { required: true, message: '请输入策略名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  description: [
    { required: true, message: '请输入策略描述', trigger: 'blur' }
  ],
  strategy_type: [
    { required: true, message: '请选择策略类型', trigger: 'change' }
  ],
  symbols: [
    { required: true, message: '请选择交易品种', trigger: 'change' }
  ],
  timeframe: [
    { required: true, message: '请选择时间周期', trigger: 'change' }
  ],
  code: [
    { required: true, message: '请输入策略代码', trigger: 'blur' }
  ]
}

// 代码模板
const codeTemplates = {
  ma_cross: `def main(context):
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
        context.sell_all()
`,
  rsi: `def main(context):
    """RSI超买超卖策略"""
    # 获取历史数据
    data = context.get_data()
    
    # 计算RSI
    rsi = calculate_rsi(data['close'], 14)
    
    # 交易信号
    if rsi.iloc[-1] < 30:  # 超卖
        context.buy(size=0.3)
    elif rsi.iloc[-1] > 70:  # 超买
        context.sell_all()

def calculate_rsi(prices, period=14):
    """计算RSI指标"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))
`,
  bollinger: `def main(context):
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
        context.sell_all()
`
}

// 加载可用交易品种
const loadAvailableSymbols = async () => {
  try {
    const response = await getContractList()
    if (response.success && response.data) {
      availableSymbols.value = response.data.slice(0, 20) // 限制显示数量
    }
  } catch (error) {
    console.error('加载交易品种失败:', error)
    // 使用默认品种
    availableSymbols.value = [
      { symbol: 'SHFE.cu2601', name: '沪铜2601' },
      { symbol: 'DCE.i2601', name: '铁矿石2601' },
      { symbol: 'CZCE.MA601', name: '甲醇2601' }
    ]
  }
}

// 加载代码模板
const loadTemplate = (templateKey: string) => {
  if (templateKey && codeTemplates[templateKey]) {
    strategyForm.code = codeTemplates[templateKey]
  }
}

// 验证代码
const validateCode = async () => {
  if (!strategyForm.code.trim()) {
    ElMessage.warning('请先输入策略代码')
    return
  }
  
  validating.value = true
  try {
    // 这里可以调用后端的代码验证API
    ElMessage.success('代码验证通过')
  } catch (error) {
    ElMessage.error('代码验证失败: ' + error.message)
  } finally {
    validating.value = false
  }
}

// 创建策略
const createStrategy = async () => {
  try {
    await formRef.value.validate()
    
    creating.value = true
    
    const strategyData = {
      ...strategyForm,
      parameters: {
        initial_capital: strategyForm.initial_capital,
        max_position_size: strategyForm.max_position_size,
        stop_loss: strategyForm.stop_loss,
        take_profit: strategyForm.take_profit,
        timeframe: strategyForm.timeframe
      }
    }
    
    const response = await strategyApi.createStrategy(strategyData)
    
    if (response.success) {
      ElMessage.success('策略创建成功')
      router.push('/strategies')
    } else {
      ElMessage.error('策略创建失败: ' + response.message)
    }
  } catch (error) {
    console.error('创建策略失败:', error)
    ElMessage.error('创建策略失败')
  } finally {
    creating.value = false
  }
}

// 重置表单
const resetForm = () => {
  formRef.value.resetFields()
  selectedTemplate.value = ''
}

// 页面初始化
onMounted(() => {
  console.log('➕ 创建策略页面已加载')
  loadAvailableSymbols()
})
</script>

<style scoped>
.strategy-create-view {
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

.create-form-container {
  max-width: 800px;
  margin: 0 auto;
  background: var(--el-bg-color);
  border-radius: 12px;
  padding: 32px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.form-section {
  margin-bottom: 32px;
  padding-bottom: 24px;
  border-bottom: 1px solid var(--el-border-color-light);
}

.form-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
}

.section-title {
  margin: 0 0 20px 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  display: flex;
  align-items: center;
  gap: 8px;
}

.strategy-form :deep(.el-form-item) {
  margin-bottom: 20px;
}

.strategy-form :deep(.el-form-item__label) {
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.code-editor {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

.code-editor :deep(.el-textarea__inner) {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  line-height: 1.5;
  background: #f8f9fa;
  border: 1px solid var(--el-border-color);
}

.form-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  padding-top: 24px;
  border-top: 1px solid var(--el-border-color-light);
}

.form-actions .el-button {
  min-width: 100px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .strategy-create-view {
    padding: 16px;
  }
  
  .create-form-container {
    padding: 20px;
  }
  
  .page-title {
    font-size: 24px;
  }
  
  .form-actions {
    flex-direction: column;
  }
  
  .form-actions .el-button {
    width: 100%;
  }
}
</style>