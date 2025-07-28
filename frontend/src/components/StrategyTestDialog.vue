<template>
  <el-dialog
    v-model="visible"
    title="策略测试配置"
    width="700px"
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
      
      <el-form-item label="测试名称" prop="name">
        <el-input
          v-model="form.name"
          placeholder="请输入测试名称"
          maxlength="100"
          show-word-limit
        />
      </el-form-item>

      <el-form-item label="测试类型" prop="test_type">
        <el-radio-group v-model="form.test_type">
          <el-radio label="unit">单元测试</el-radio>
          <el-radio label="integration">集成测试</el-radio>
          <el-radio label="performance">性能测试</el-radio>
          <el-radio label="stress">压力测试</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item label="测试环境" prop="environment">
        <el-select v-model="form.environment" placeholder="请选择测试环境">
          <el-option label="开发环境" value="development" />
          <el-option label="测试环境" value="testing" />
          <el-option label="预生产环境" value="staging" />
          <el-option label="模拟环境" value="simulation" />
        </el-select>
      </el-form-item>

      <!-- 数据配置 -->
      <el-divider content-position="left">数据配置</el-divider>

      <el-form-item label="数据源" prop="data_source">
        <el-select v-model="form.data_source" placeholder="请选择数据源">
          <el-option label="历史数据" value="historical" />
          <el-option label="模拟数据" value="simulated" />
          <el-option label="实时数据" value="realtime" />
        </el-select>
      </el-form-item>

      <el-form-item label="测试时间范围" prop="time_range" v-if="form.data_source === 'historical'">
        <el-date-picker
          v-model="form.time_range"
          type="datetimerange"
          range-separator="至"
          start-placeholder="开始时间"
          end-placeholder="结束时间"
          format="YYYY-MM-DD HH:mm:ss"
          value-format="YYYY-MM-DD HH:mm:ss"
        />
      </el-form-item>

      <el-form-item label="交易品种" prop="symbols">
        <el-select
          v-model="form.symbols"
          multiple
          filterable
          placeholder="请选择交易品种"
          style="width: 100%"
        >
          <el-option
            v-for="symbol in availableSymbols"
            :key="symbol"
            :label="symbol"
            :value="symbol"
          />
        </el-select>
      </el-form-item>

      <!-- 资金配置 -->
      <el-divider content-position="left">资金配置</el-divider>

      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="初始资金" prop="initial_capital">
            <el-input-number
              v-model="form.initial_capital"
              :min="10000"
              :max="10000000"
              :step="10000"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="手续费率" prop="commission_rate">
            <el-input-number
              v-model="form.commission_rate"
              :min="0"
              :max="0.01"
              :step="0.0001"
              :precision="4"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="滑点设置" prop="slippage">
            <el-input-number
              v-model="form.slippage"
              :min="0"
              :max="0.01"
              :step="0.0001"
              :precision="4"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="最大持仓" prop="max_position">
            <el-input-number
              v-model="form.max_position"
              :min="0"
              :max="1"
              :step="0.1"
              :precision="2"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <!-- 风险控制 -->
      <el-divider content-position="left">风险控制</el-divider>

      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="止损比例" prop="stop_loss">
            <el-input-number
              v-model="form.stop_loss"
              :min="0"
              :max="0.2"
              :step="0.01"
              :precision="3"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="止盈比例" prop="take_profit">
            <el-input-number
              v-model="form.take_profit"
              :min="0"
              :max="1"
              :step="0.01"
              :precision="3"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="最大回撤" prop="max_drawdown">
        <el-input-number
          v-model="form.max_drawdown"
          :min="0"
          :max="0.5"
          :step="0.05"
          :precision="2"
          style="width: 100%"
        />
      </el-form-item>

      <!-- 高级配置 -->
      <el-divider content-position="left">高级配置</el-divider>

      <el-form-item label="并发数" prop="concurrency">
        <el-input-number
          v-model="form.concurrency"
          :min="1"
          :max="10"
          style="width: 100%"
        />
      </el-form-item>

      <el-form-item label="超时时间(秒)" prop="timeout">
        <el-input-number
          v-model="form.timeout"
          :min="30"
          :max="3600"
          :step="30"
          style="width: 100%"
        />
      </el-form-item>

      <el-form-item label="日志级别" prop="log_level">
        <el-select v-model="form.log_level">
          <el-option label="DEBUG" value="DEBUG" />
          <el-option label="INFO" value="INFO" />
          <el-option label="WARNING" value="WARNING" />
          <el-option label="ERROR" value="ERROR" />
        </el-select>
      </el-form-item>

      <el-form-item label="保存结果" prop="save_results">
        <el-switch
          v-model="form.save_results"
          active-text="保存"
          inactive-text="不保存"
        />
      </el-form-item>

      <el-form-item label="发送通知" prop="send_notification">
        <el-switch
          v-model="form.send_notification"
          active-text="发送"
          inactive-text="不发送"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" :loading="loading" @click="handleSubmit">
          开始测试
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'

interface Props {
  modelValue: boolean
  strategyId?: number
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'success', testId: number): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const formRef = ref<FormInstance>()
const loading = ref(false)

// 表单数据
const form = ref({
  name: '',
  test_type: 'unit',
  environment: 'testing',
  data_source: 'historical',
  time_range: [],
  symbols: [],
  initial_capital: 100000,
  commission_rate: 0.0003,
  slippage: 0.0001,
  max_position: 0.3,
  stop_loss: 0.02,
  take_profit: 0.06,
  max_drawdown: 0.2,
  concurrency: 1,
  timeout: 300,
  log_level: 'INFO',
  save_results: true,
  send_notification: false
})

// 表单验证规则
const rules: FormRules = {
  name: [
    { required: true, message: '请输入测试名称', trigger: 'blur' },
    { min: 2, max: 100, message: '测试名称长度在 2 到 100 个字符', trigger: 'blur' }
  ],
  test_type: [
    { required: true, message: '请选择测试类型', trigger: 'change' }
  ],
  environment: [
    { required: true, message: '请选择测试环境', trigger: 'change' }
  ],
  data_source: [
    { required: true, message: '请选择数据源', trigger: 'change' }
  ],
  time_range: [
    { required: true, message: '请选择测试时间范围', trigger: 'change' }
  ],
  symbols: [
    { required: true, message: '请选择至少一个交易品种', trigger: 'change' }
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

// 方法
const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    loading.value = true
    
    // 构建测试配置
    const testConfig = {
      strategy_id: props.strategyId,
      name: form.value.name,
      test_type: form.value.test_type,
      environment: form.value.environment,
      config: {
        data_source: form.value.data_source,
        time_range: form.value.time_range,
        symbols: form.value.symbols,
        initial_capital: form.value.initial_capital,
        commission_rate: form.value.commission_rate,
        slippage: form.value.slippage,
        max_position: form.value.max_position,
        risk_management: {
          stop_loss: form.value.stop_loss,
          take_profit: form.value.take_profit,
          max_drawdown: form.value.max_drawdown
        },
        advanced: {
          concurrency: form.value.concurrency,
          timeout: form.value.timeout,
          log_level: form.value.log_level,
          save_results: form.value.save_results,
          send_notification: form.value.send_notification
        }
      }
    }
    
    // 调用测试API
    // const response = await strategyApi.runTest(testConfig)
    // if (response.success) {
    //   emit('success', response.data.test_id)
    //   ElMessage.success('测试已开始')
    //   handleClose()
    // }
    
    // 模拟成功
    setTimeout(() => {
      emit('success', Math.floor(Math.random() * 1000))
      ElMessage.success('测试已开始')
      handleClose()
    }, 1000)
    
  } catch (error) {
    ElMessage.error('测试配置验证失败')
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
  
  form.value = {
    name: '',
    test_type: 'unit',
    environment: 'testing',
    data_source: 'historical',
    time_range: [],
    symbols: [],
    initial_capital: 100000,
    commission_rate: 0.0003,
    slippage: 0.0001,
    max_position: 0.3,
    stop_loss: 0.02,
    take_profit: 0.06,
    max_drawdown: 0.2,
    concurrency: 1,
    timeout: 300,
    log_level: 'INFO',
    save_results: true,
    send_notification: false
  }
}
</script>

<style scoped lang="scss">
.dialog-footer {
  text-align: right;
}

:deep(.el-divider__text) {
  font-weight: 600;
  color: #303133;
}
</style>