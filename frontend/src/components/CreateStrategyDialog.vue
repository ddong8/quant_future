<template>
  <el-dialog
    v-model="visible"
    title="创建策略"
    width="600px"
    :before-close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="100px"
      @submit.prevent
    >
      <el-form-item label="策略名称" prop="name">
        <el-input
          v-model="form.name"
          placeholder="请输入策略名称"
          maxlength="100"
          show-word-limit
        />
      </el-form-item>

      <el-form-item label="策略描述" prop="description">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="3"
          placeholder="请输入策略描述"
          maxlength="500"
          show-word-limit
        />
      </el-form-item>

      <el-form-item label="策略分类" prop="category">
        <el-select v-model="form.category" placeholder="请选择策略分类" style="width: 100%">
          <el-option
            v-for="category in categories"
            :key="category.id"
            :label="category.name"
            :value="category.id"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="标签">
        <el-select
          v-model="form.tags"
          multiple
          filterable
          allow-create
          placeholder="请选择或输入标签"
          style="width: 100%"
        >
          <el-option
            v-for="tag in commonTags"
            :key="tag"
            :label="tag"
            :value="tag"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="公开策略">
        <el-switch
          v-model="form.is_public"
          active-text="公开"
          inactive-text="私有"
        />
        <div class="form-tip">
          公开策略将在策略市场中展示，其他用户可以查看和使用
        </div>
      </el-form-item>

      <!-- 基础配置 -->
      <el-divider content-position="left">基础配置</el-divider>

      <el-form-item label="交易品种" prop="symbols">
        <el-select
          v-model="form.config.symbols"
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

      <el-form-item label="时间周期" prop="timeframe">
        <el-select v-model="form.config.timeframe" placeholder="请选择时间周期">
          <el-option label="1分钟" value="1m" />
          <el-option label="5分钟" value="5m" />
          <el-option label="15分钟" value="15m" />
          <el-option label="30分钟" value="30m" />
          <el-option label="1小时" value="1h" />
          <el-option label="4小时" value="4h" />
          <el-option label="1天" value="1d" />
        </el-select>
      </el-form-item>

      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="最大仓位" prop="max_position_size">
            <el-input-number
              v-model="form.config.max_position_size"
              :min="0"
              :max="1"
              :step="0.1"
              :precision="2"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="单笔风险" prop="risk_per_trade">
            <el-input-number
              v-model="form.config.risk_per_trade"
              :min="0"
              :max="0.1"
              :step="0.01"
              :precision="3"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <!-- 风险控制 -->
      <el-divider content-position="left">风险控制</el-divider>

      <el-row :gutter="16">
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
        <el-col :span="12">
          <el-form-item label="止损比例">
            <el-input-number
              v-model="form.config.risk_management.stop_loss"
              :min="0"
              :max="1"
              :step="0.01"
              :precision="3"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="止盈比例">
            <el-input-number
              v-model="form.config.risk_management.take_profit"
              :min="0"
              :max="5"
              :step="0.1"
              :precision="2"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="日最大交易">
            <el-input-number
              v-model="form.config.risk_management.max_daily_trades"
              :min="1"
              :max="100"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <!-- 交易时间 -->
      <el-divider content-position="left">交易时间</el-divider>

      <el-row :gutter="16">
        <el-col :span="8">
          <el-form-item label="开始时间">
            <el-time-picker
              v-model="form.config.trading_hours.start_time"
              format="HH:mm"
              value-format="HH:mm"
              placeholder="选择开始时间"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="结束时间">
            <el-time-picker
              v-model="form.config.trading_hours.end_time"
              format="HH:mm"
              value-format="HH:mm"
              placeholder="选择结束时间"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="时区">
            <el-select v-model="form.config.trading_hours.timezone">
              <el-option label="北京时间" value="Asia/Shanghai" />
              <el-option label="纽约时间" value="America/New_York" />
              <el-option label="伦敦时间" value="Europe/London" />
              <el-option label="东京时间" value="Asia/Tokyo" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" :loading="loading" @click="handleSubmit">
          创建策略
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { useStrategyStore } from '@/stores/strategy'
import type { CreateStrategyRequest } from '@/types/strategy'

interface Props {
  modelValue: boolean
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const strategyStore = useStrategyStore()
const formRef = ref<FormInstance>()
const loading = ref(false)

// 表单数据
const form = ref<CreateStrategyRequest>({
  name: '',
  description: '',
  category: '',
  tags: [],
  is_public: false,
  config: {
    symbols: [],
    timeframe: '1h',
    max_position_size: 0.1,
    risk_per_trade: 0.02,
    risk_management: {
      max_drawdown: 0.2,
      stop_loss: 0.02,
      take_profit: 0.06,
      max_daily_trades: 10
    },
    trading_hours: {
      start_time: '09:00',
      end_time: '15:00',
      timezone: 'Asia/Shanghai'
    },
    parameters: {}
  }
})

// 表单验证规则
const rules: FormRules = {
  name: [
    { required: true, message: '请输入策略名称', trigger: 'blur' },
    { min: 2, max: 100, message: '策略名称长度在 2 到 100 个字符', trigger: 'blur' }
  ],
  description: [
    { max: 500, message: '描述长度不能超过 500 个字符', trigger: 'blur' }
  ],
  category: [
    { required: true, message: '请选择策略分类', trigger: 'change' }
  ],
  symbols: [
    { required: true, message: '请选择至少一个交易品种', trigger: 'change' }
  ],
  timeframe: [
    { required: true, message: '请选择时间周期', trigger: 'change' }
  ],
  max_position_size: [
    { required: true, message: '请设置最大仓位', trigger: 'blur' }
  ],
  risk_per_trade: [
    { required: true, message: '请设置单笔风险', trigger: 'blur' }
  ]
}

// 计算属性
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const categories = computed(() => strategyStore.categories)

// 常用标签
const commonTags = ref([
  '趋势跟踪',
  '均值回归',
  '套利',
  '高频',
  '量化',
  '机器学习',
  '技术分析',
  '基本面分析'
])

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
    
    await strategyStore.createStrategy(form.value)
    
    ElMessage.success('策略创建成功')
    emit('success')
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
  
  // 重置表单数据
  form.value = {
    name: '',
    description: '',
    category: '',
    tags: [],
    is_public: false,
    config: {
      symbols: [],
      timeframe: '1h',
      max_position_size: 0.1,
      risk_per_trade: 0.02,
      risk_management: {
        max_drawdown: 0.2,
        stop_loss: 0.02,
        take_profit: 0.06,
        max_daily_trades: 10
      },
      trading_hours: {
        start_time: '09:00',
        end_time: '15:00',
        timezone: 'Asia/Shanghai'
      },
      parameters: {}
    }
  }
}

// 监听对话框显示状态
watch(visible, (newVal) => {
  if (newVal) {
    // 对话框打开时，确保分类数据已加载
    if (categories.value.length === 0) {
      strategyStore.fetchCategories()
    }
  }
})
</script>

<style scoped lang="scss">
.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.dialog-footer {
  text-align: right;
}

:deep(.el-divider__text) {
  font-weight: 600;
  color: #303133;
}
</style>