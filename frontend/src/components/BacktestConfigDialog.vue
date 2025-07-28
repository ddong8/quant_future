<template>
  <el-dialog
    v-model="visible"
    title="回测配置"
    width="800px"
    :before-close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="120px"
      @submit.prevent
    >
      <!-- 基础配置 -->
      <el-divider content-position="left">基础配置</el-divider>
      
      <el-form-item label="回测名称" prop="name">
        <el-input
          v-model="form.name"
          placeholder="请输入回测名称"
          maxlength="100"
          show-word-limit
        />
      </el-form-item>

      <el-form-item label="回测描述">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="3"
          placeholder="请输入回测描述"
          maxlength="500"
          show-word-limit
        />
      </el-form-item>

      <el-form-item label="策略选择" prop="strategy_id">
        <el-select v-model="form.strategy_id" placeholder="请选择策略" style="width: 100%">
          <el-option
            v-for="strategy in strategies"
            :key="strategy.id"
            :label="strategy.name"
            :value="strategy.id"
          />
        </el-select>
      </el-form-item>

      <!-- 时间配置 -->
      <el-divider content-position="left">时间配置</el-divider>

      <el-form-item label="回测时间范围" prop="dateRange">
        <el-date-picker
          v-model="form.dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          style="width: 100%"
          @change="handleDateRangeChange"
        />
      </el-form-item>

      <el-form-item label="数据频率" prop="data_frequency">
        <el-select v-model="form.config.data_frequency" placeholder="请选择数据频率">
          <el-option label="1分钟" value="1m" />
          <el-option label="5分钟" value="5m" />
          <el-option label="15分钟" value="15m" />
          <el-option label="30分钟" value="30m" />
          <el-option label="1小时" value="1h" />
          <el-option label="4小时" value="4h" />
          <el-option label="1天" value="1d" />
        </el-select>
      </el-form-item>

      <!-- 交易品种 -->
      <el-divider content-position="left">交易品种</el-divider>

      <el-form-item label="交易品种" prop="symbols">
        <el-select
          v-model="form.config.symbols"
          multiple
          filterable
          placeholder="请选择交易品种"
          style="width: 100%"
          @change="handleSymbolsChange"
        >
          <el-option
            v-for="symbol in availableSymbols"
            :key="symbol"
            :label="symbol"
            :value="symbol"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="基准指数">
        <el-select v-model="form.config.benchmark" placeholder="请选择基准指数" clearable>
          <el-option
            v-for="benchmark in availableBenchmarks"
            :key="benchmark.symbol"
            :label="benchmark.name"
            :value="benchmark.symbol"
          />
        </el-select>
      </el-form-item>

      <!-- 资金配置 -->
      <el-divider content-position="left">资金配置</el-divider>

      <el-form-item label="初始资金" prop="initial_capital">
        <el-input-number
          v-model="form.config.initial_capital"
          :min="10000"
          :max="100000000"
          :step="10000"
          style="width: 100%"
        />
      </el-form-item>

      <!-- 交易成本 -->
      <el-divider content-position="left">交易成本</el-divider>

      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="手续费率">
            <el-input-number
              v-model="form.config.commission.rate"
              :min="0"
              :max="0.01"
              :step="0.0001"
              :precision="4"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="最小手续费">
            <el-input-number
              v-model="form.config.commission.min_commission"
              :min="0"
              :max="100"
              :step="1"
              :precision="2"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="按股收费">
        <el-switch
          v-model="form.config.commission.per_share"
          active-text="是"
          inactive-text="否"
        />
      </el-form-item>

      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="滑点类型">
            <el-select v-model="form.config.slippage.type">
              <el-option label="固定金额" value="fixed" />
              <el-option label="百分比" value="percentage" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="滑点值">
            <el-input-number
              v-model="form.config.slippage.value"
              :min="0"
              :max="form.config.slippage.type === 'fixed' ? 100 : 0.01"
              :step="form.config.slippage.type === 'fixed' ? 1 : 0.0001"
              :precision="form.config.slippage.type === 'fixed' ? 2 : 4"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <!-- 风险管理 -->
      <el-divider content-position="left">风险管理</el-divider>

      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="最大持仓比例">
            <el-input-number
              v-model="form.config.risk_management.max_position_size"
              :min="0"
              :max="1"
              :step="0.1"
              :precision="2"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="最大回撤">
            <el-input-number
              v-model="form.config.risk_management.max_drawdown"
              :min="0"
              :max="1"
              :step="0.05"
              :precision="2"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="止损比例">
            <el-input-number
              v-model="form.config.risk_management.stop_loss"
              :min="0"
              :max="0.5"
              :step="0.01"
              :precision="3"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="止盈比例">
            <el-input-number
              v-model="form.config.risk_management.take_profit"
              :min="0"
              :max="2"
              :step="0.1"
              :precision="2"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <!-- 高级配置 -->
      <el-divider content-position="left">高级配置</el-divider>

      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="预热期(天)">
            <el-input-number
              v-model="form.config.advanced.warm_up_period"
              :min="0"
              :max="365"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="回望窗口(天)">
            <el-input-number
              v-model="form.config.advanced.lookback_window"
              :min="1"
              :max="1000"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="再平衡频率">
        <el-select v-model="form.config.advanced.rebalance_frequency">
          <el-option label="每日" value="daily" />
          <el-option label="每周" value="weekly" />
          <el-option label="每月" value="monthly" />
        </el-select>
      </el-form-item>

      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="市场冲击">
            <el-switch
              v-model="form.config.advanced.market_impact"
              active-text="考虑"
              inactive-text="忽略"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="交易成本">
            <el-switch
              v-model="form.config.advanced.transaction_cost"
              active-text="考虑"
              inactive-text="忽略"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <!-- 数据验证结果 -->
      <div v-if="dataValidation" class="data-validation">
        <el-divider content-position="left">数据验证结果</el-divider>
        <el-alert
          :title="dataValidation.valid ? '数据验证通过' : '数据验证失败'"
          :type="dataValidation.valid ? 'success' : 'error'"
          :closable="false"
          show-icon
        >
          <div v-if="!dataValidation.valid">
            <p v-for="error in dataValidation.errors" :key="error">{{ error }}</p>
          </div>
          <div v-else>
            <p>数据完整性: {{ (dataValidation.completeness * 100).toFixed(1) }}%</p>
            <p>数据质量评分: {{ (dataValidation.quality_score * 100).toFixed(1) }}分</p>
          </div>
        </el-alert>
      </div>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button @click="handleValidateData" :loading="validating">
          验证数据
        </el-button>
        <el-button type="primary" :loading="loading" @click="handleSubmit">
          创建回测
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { useStrategyStore } from '@/stores/strategy'
import { useBacktestStore } from '@/stores/backtest'
import type { CreateBacktestRequest, BacktestConfig } from '@/types/backtest'

interface Props {
  modelValue: boolean
  strategyId?: number
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'success', backtest: any): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const strategyStore = useStrategyStore()
const backtestStore = useBacktestStore()
const formRef = ref<FormInstance>()
const loading = ref(false)
const validating = ref(false)
const dataValidation = ref<any>(null)

// 表单数据
const form = ref<CreateBacktestRequest>({
  name: '',
  description: '',
  strategy_id: props.strategyId || 0,
  config: {
    start_date: '',
    end_date: '',
    initial_capital: 1000000,
    symbols: [],
    data_frequency: '1d',
    benchmark: '',
    commission: {
      rate: 0.0003,
      min_commission: 5,
      per_share: false
    },
    slippage: {
      type: 'percentage',
      value: 0.0001
    },
    risk_management: {
      max_position_size: 0.3,
      max_drawdown: 0.2,
      stop_loss: 0.02,
      take_profit: 0.06
    },
    advanced: {
      warm_up_period: 30,
      lookback_window: 252,
      rebalance_frequency: 'daily',
      market_impact: true,
      transaction_cost: true
    }
  },
  dateRange: []
})

// 表单验证规则
const rules: FormRules = {
  name: [
    { required: true, message: '请输入回测名称', trigger: 'blur' },
    { min: 2, max: 100, message: '回测名称长度在 2 到 100 个字符', trigger: 'blur' }
  ],
  strategy_id: [
    { required: true, message: '请选择策略', trigger: 'change' }
  ],
  dateRange: [
    { required: true, message: '请选择回测时间范围', trigger: 'change' }
  ],
  symbols: [
    { required: true, message: '请选择至少一个交易品种', trigger: 'change' }
  ],
  data_frequency: [
    { required: true, message: '请选择数据频率', trigger: 'change' }
  ],
  initial_capital: [
    { required: true, message: '请设置初始资金', trigger: 'blur' }
  ]
}

// 计算属性
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const strategies = computed(() => strategyStore.strategies)

// 可用交易品种
const availableSymbols = ref([
  'SHFE.cu2401',
  'SHFE.al2401',
  'DCE.i2401',
  'CZCE.MA401',
  'CFFEX.IF2401',
  'CFFEX.IC2401',
  'CFFEX.IH2401'
])

// 可用基准指数
const availableBenchmarks = ref([
  { symbol: 'CSI300', name: '沪深300', description: '沪深300指数' },
  { symbol: 'CSI500', name: '中证500', description: '中证500指数' },
  { symbol: 'SSE50', name: '上证50', description: '上证50指数' },
  { symbol: 'SZSE100', name: '深证100', description: '深证100指数' }
])

// 方法
const handleDateRangeChange = (dateRange: string[]) => {
  if (dateRange && dateRange.length === 2) {
    form.value.config.start_date = dateRange[0]
    form.value.config.end_date = dateRange[1]
  } else {
    form.value.config.start_date = ''
    form.value.config.end_date = ''
  }
  
  // 清空之前的验证结果
  dataValidation.value = null
}

const handleSymbolsChange = () => {
  // 清空之前的验证结果
  dataValidation.value = null
}

const handleValidateData = async () => {
  if (!form.value.config.symbols.length || !form.value.config.start_date || !form.value.config.end_date) {
    ElMessage.warning('请先选择交易品种和时间范围')
    return
  }
  
  try {
    validating.value = true
    
    const result = await backtestStore.validateHistoricalData({
      symbols: form.value.config.symbols,
      start_date: form.value.config.start_date,
      end_date: form.value.config.end_date,
      frequency: form.value.config.data_frequency
    })
    
    dataValidation.value = result
    
    if (result.valid) {
      ElMessage.success('数据验证通过')
    } else {
      ElMessage.warning('数据验证发现问题，请检查验证结果')
    }
  } catch (error) {
    ElMessage.error('数据验证失败')
  } finally {
    validating.value = false
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    
    if (!dataValidation.value) {
      ElMessage.warning('请先验证数据')
      return
    }
    
    if (!dataValidation.value.valid) {
      ElMessage.error('数据验证未通过，无法创建回测')
      return
    }
    
    loading.value = true
    
    const backtest = await backtestStore.createBacktest(form.value)
    
    ElMessage.success('回测创建成功')
    emit('success', backtest)
    handleClose()
  } catch (error) {
    // 错误已在store中处理
  } finally {
    loading.value = false
  }
}

const handleClose = () => {
  visible.value = false
  resetForm()
}

const resetForm = () => {
  if (formRef.value) {
    formRef.value.resetFields()
  }
  
  dataValidation.value = null
  
  form.value = {
    name: '',
    description: '',
    strategy_id: props.strategyId || 0,
    config: {
      start_date: '',
      end_date: '',
      initial_capital: 1000000,
      symbols: [],
      data_frequency: '1d',
      benchmark: '',
      commission: {
        rate: 0.0003,
        min_commission: 5,
        per_share: false
      },
      slippage: {
        type: 'percentage',
        value: 0.0001
      },
      risk_management: {
        max_position_size: 0.3,
        max_drawdown: 0.2,
        stop_loss: 0.02,
        take_profit: 0.06
      },
      advanced: {
        warm_up_period: 30,
        lookback_window: 252,
        rebalance_frequency: 'daily',
        market_impact: true,
        transaction_cost: true
      }
    },
    dateRange: []
  }
}

// 生命周期
onMounted(() => {
  // 加载策略列表
  if (strategies.value.length === 0) {
    strategyStore.fetchStrategies()
  }
})
</script>

<style scoped lang="scss">
.dialog-footer {
  text-align: right;
}

.data-validation {
  margin-top: 16px;
}

:deep(.el-divider__text) {
  font-weight: 600;
  color: #303133;
}
</style>