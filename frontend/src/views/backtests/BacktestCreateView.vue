<template>
  <div class="backtest-create-view">
    <div class="page-header">
      <h1 class="page-title">➕ 创建回测</h1>
      <p class="page-description">基于真实历史数据创建策略回测</p>
    </div>

    <!-- 回测配置表单 -->
    <div class="create-form-container">
      <el-form 
        ref="formRef" 
        :model="backtestForm" 
        :rules="formRules" 
        label-width="120px"
        class="backtest-form"
      >
        <!-- 基本信息 -->
        <div class="form-section">
          <h3 class="section-title">📋 基本信息</h3>
          <el-form-item label="回测名称" prop="name">
            <el-input 
              v-model="backtestForm.name" 
              placeholder="请输入回测名称"
              maxlength="50"
              show-word-limit
            />
          </el-form-item>
          
          <el-form-item label="回测描述" prop="description">
            <el-input 
              v-model="backtestForm.description" 
              type="textarea" 
              :rows="3"
              placeholder="请输入回测描述"
              maxlength="200"
              show-word-limit
            />
          </el-form-item>
        </div>

        <!-- 策略配置 -->
        <div class="form-section">
          <h3 class="section-title">🤖 策略配置</h3>
          <el-form-item label="策略类型" prop="strategy_type">
            <el-select v-model="backtestForm.strategy_type" placeholder="请选择策略类型" @change="onStrategyTypeChange">
              <el-option label="双均线策略" value="dual_ma" />
              <el-option label="RSI反转策略" value="rsi_reversal" />
              <el-option label="布林带策略" value="bollinger_bands" />
              <el-option label="MACD策略" value="macd" />
              <el-option label="自定义策略" value="custom" />
            </el-select>
          </el-form-item>
          
          <el-form-item v-if="backtestForm.strategy_type === 'custom'" label="策略代码" prop="strategy_code">
            <el-input 
              v-model="backtestForm.strategy_code" 
              type="textarea" 
              :rows="10"
              placeholder="请输入策略代码"
              class="code-editor"
            />
          </el-form-item>
          
          <!-- 策略参数 -->
          <div v-if="strategyParams.length > 0" class="strategy-params">
            <h4>策略参数</h4>
            <div class="params-grid">
              <el-form-item 
                v-for="param in strategyParams" 
                :key="param.name"
                :label="param.label"
              >
                <el-input-number 
                  v-model="backtestForm.strategy_params[param.name]"
                  :min="param.min"
                  :max="param.max"
                  :step="param.step"
                  :precision="param.precision"
                  style="width: 100%"
                />
              </el-form-item>
            </div>
          </div>
        </div>

        <!-- 交易配置 -->
        <div class="form-section">
          <h3 class="section-title">📊 交易配置</h3>
          <el-form-item label="交易品种" prop="symbols">
            <el-select 
              v-model="backtestForm.symbols" 
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
          
          <el-form-item label="初始资金" prop="initial_capital">
            <el-input-number 
              v-model="backtestForm.initial_capital" 
              :min="10000" 
              :max="100000000" 
              :step="10000"
              placeholder="初始资金"
              style="width: 100%"
            />
          </el-form-item>
          
          <el-form-item label="手续费率" prop="commission_rate">
            <el-input-number 
              v-model="backtestForm.commission_rate" 
              :min="0" 
              :max="0.01" 
              :step="0.0001"
              :precision="4"
              placeholder="手续费率"
              style="width: 100%"
            />
          </el-form-item>
        </div>

        <!-- 时间配置 -->
        <div class="form-section">
          <h3 class="section-title">⏰ 时间配置</h3>
          <el-form-item label="回测时间" prop="date_range">
            <el-date-picker
              v-model="backtestForm.date_range"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
          
          <el-form-item label="数据频率" prop="frequency">
            <el-select v-model="backtestForm.frequency" placeholder="请选择数据频率">
              <el-option label="1分钟" value="1m" />
              <el-option label="5分钟" value="5m" />
              <el-option label="15分钟" value="15m" />
              <el-option label="30分钟" value="30m" />
              <el-option label="1小时" value="1h" />
              <el-option label="1天" value="1d" />
            </el-select>
          </el-form-item>
        </div>

        <!-- 风险控制 -->
        <div class="form-section">
          <h3 class="section-title">🛡️ 风险控制</h3>
          <el-form-item label="最大仓位" prop="max_position">
            <el-input-number 
              v-model="backtestForm.max_position" 
              :min="0.1" 
              :max="1" 
              :step="0.1"
              :precision="1"
              placeholder="最大仓位比例"
              style="width: 100%"
            />
          </el-form-item>
          
          <el-form-item label="止损比例" prop="stop_loss">
            <el-input-number 
              v-model="backtestForm.stop_loss" 
              :min="0" 
              :max="0.5" 
              :step="0.01"
              :precision="2"
              placeholder="止损比例"
              style="width: 100%"
            />
          </el-form-item>
          
          <el-form-item label="止盈比例" prop="take_profit">
            <el-input-number 
              v-model="backtestForm.take_profit" 
              :min="0" 
              :max="2" 
              :step="0.01"
              :precision="2"
              placeholder="止盈比例"
              style="width: 100%"
            />
          </el-form-item>
        </div>

        <!-- 操作按钮 -->
        <div class="form-actions">
          <el-button @click="resetForm">重置</el-button>
          <el-button @click="saveAsDraft" :loading="saving">保存草稿</el-button>
          <el-button type="primary" @click="createAndRun" :loading="creating">创建并运行</el-button>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { getContractList, createBacktest, runQuickBacktest } from '@/api/realTimeData'

const router = useRouter()
const formRef = ref()
const creating = ref(false)
const saving = ref(false)
const availableSymbols = ref([])

// 回测表单数据
const backtestForm = reactive({
  name: '',
  description: '',
  strategy_type: 'dual_ma',
  strategy_code: '',
  strategy_params: {},
  symbols: [],
  initial_capital: 1000000,
  commission_rate: 0.0003,
  date_range: [],
  frequency: '1m',
  max_position: 0.8,
  stop_loss: 0.05,
  take_profit: 0.1
})

// 表单验证规则
const formRules = {
  name: [
    { required: true, message: '请输入回测名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  strategy_type: [
    { required: true, message: '请选择策略类型', trigger: 'change' }
  ],
  symbols: [
    { required: true, message: '请选择交易品种', trigger: 'change' }
  ],
  date_range: [
    { required: true, message: '请选择回测时间范围', trigger: 'change' }
  ],
  frequency: [
    { required: true, message: '请选择数据频率', trigger: 'change' }
  ]
}

// 策略参数配置
const strategyParamsConfig = {
  dual_ma: [
    { name: 'fast_period', label: '快线周期', min: 1, max: 50, step: 1, precision: 0, default: 5 },
    { name: 'slow_period', label: '慢线周期', min: 1, max: 200, step: 1, precision: 0, default: 20 }
  ],
  rsi_reversal: [
    { name: 'rsi_period', label: 'RSI周期', min: 1, max: 50, step: 1, precision: 0, default: 14 },
    { name: 'oversold', label: '超卖线', min: 10, max: 40, step: 1, precision: 0, default: 30 },
    { name: 'overbought', label: '超买线', min: 60, max: 90, step: 1, precision: 0, default: 70 }
  ],
  bollinger_bands: [
    { name: 'period', label: '周期', min: 1, max: 50, step: 1, precision: 0, default: 20 },
    { name: 'std_dev', label: '标准差倍数', min: 1, max: 3, step: 0.1, precision: 1, default: 2 }
  ],
  macd: [
    { name: 'fast_period', label: '快线周期', min: 1, max: 50, step: 1, precision: 0, default: 12 },
    { name: 'slow_period', label: '慢线周期', min: 1, max: 100, step: 1, precision: 0, default: 26 },
    { name: 'signal_period', label: '信号线周期', min: 1, max: 50, step: 1, precision: 0, default: 9 }
  ]
}

// 当前策略参数
const strategyParams = computed(() => {
  return strategyParamsConfig[backtestForm.strategy_type] || []
})

// 策略类型变化处理
const onStrategyTypeChange = (strategyType: string) => {
  backtestForm.strategy_params = {}
  const params = strategyParamsConfig[strategyType] || []
  params.forEach(param => {
    backtestForm.strategy_params[param.name] = param.default
  })
}

// 加载可用交易品种
const loadAvailableSymbols = async () => {
  try {
    const response = await getContractList()
    if (response.success && response.data) {
      availableSymbols.value = response.data.slice(0, 20)
    }
  } catch (error) {
    console.error('加载交易品种失败:', error)
    // 使用默认品种
    availableSymbols.value = [
      { symbol: 'SHFE.cu2601', name: '沪铜2601' },
      { symbol: 'DCE.i2601', name: '铁矿石2601' },
      { symbol: 'CZCE.MA601', name: '甲醇2601' },
      { symbol: 'SHFE.rb2601', name: '螺纹钢2601' }
    ]
  }
}

// 创建并运行回测
const createAndRun = async () => {
  try {
    await formRef.value.validate()
    
    creating.value = true
    
    const backtestConfig = {
      name: backtestForm.name,
      description: backtestForm.description,
      strategy_type: backtestForm.strategy_type,
      strategy_code: backtestForm.strategy_code,
      strategy_params: backtestForm.strategy_params,
      symbols: backtestForm.symbols,
      initial_capital: backtestForm.initial_capital,
      commission_rate: backtestForm.commission_rate,
      start_date: backtestForm.date_range[0],
      end_date: backtestForm.date_range[1],
      frequency: backtestForm.frequency,
      max_position: backtestForm.max_position,
      stop_loss: backtestForm.stop_loss,
      take_profit: backtestForm.take_profit
    }
    
    const response = await createBacktest(backtestConfig)
    
    if (response.success) {
      ElMessage.success('回测创建成功，正在运行...')
      router.push('/backtests')
    } else {
      ElMessage.error('回测创建失败: ' + response.message)
    }
  } catch (error) {
    console.error('创建回测失败:', error)
    ElMessage.error('创建回测失败')
  } finally {
    creating.value = false
  }
}

// 保存草稿
const saveAsDraft = async () => {
  saving.value = true
  try {
    // 这里可以保存到本地存储或后端
    localStorage.setItem('backtest_draft', JSON.stringify(backtestForm))
    ElMessage.success('草稿已保存')
  } catch (error) {
    ElMessage.error('保存草稿失败')
  } finally {
    saving.value = false
  }
}

// 重置表单
const resetForm = () => {
  formRef.value.resetFields()
  backtestForm.strategy_params = {}
  onStrategyTypeChange(backtestForm.strategy_type)
}

// 加载草稿
const loadDraft = () => {
  try {
    const draft = localStorage.getItem('backtest_draft')
    if (draft) {
      const draftData = JSON.parse(draft)
      Object.assign(backtestForm, draftData)
    }
  } catch (error) {
    console.error('加载草稿失败:', error)
  }
}

// 页面初始化
onMounted(() => {
  console.log('➕ 创建回测页面已加载')
  loadAvailableSymbols()
  loadDraft()
  onStrategyTypeChange(backtestForm.strategy_type)
})
</script>
<style scoped>
.backtest-create-view {
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

.backtest-form :deep(.el-form-item) {
  margin-bottom: 20px;
}

.backtest-form :deep(.el-form-item__label) {
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

.strategy-params {
  margin-top: 20px;
  padding: 20px;
  background: var(--el-bg-color-page);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-light);
}

.strategy-params h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.params-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
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
  .backtest-create-view {
    padding: 16px;
  }
  
  .create-form-container {
    padding: 20px;
  }
  
  .page-title {
    font-size: 24px;
  }
  
  .params-grid {
    grid-template-columns: 1fr;
  }
  
  .form-actions {
    flex-direction: column;
  }
  
  .form-actions .el-button {
    width: 100%;
  }
}
</style>
