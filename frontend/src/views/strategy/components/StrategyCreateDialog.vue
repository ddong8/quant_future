<template>
  <BaseDialog
    v-model="dialogVisible"
    title="创建策略"
    width="800px"
    :loading="loading"
    @confirm="handleSubmit"
    @cancel="handleCancel"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-width="120px"
      @submit.prevent="handleSubmit"
    >
      <el-tabs v-model="activeTab" type="border-card">
        <!-- 基本信息 -->
        <el-tab-pane label="基本信息" name="basic">
          <el-form-item label="策略名称" prop="name" required>
            <el-input
              v-model="formData.name"
              placeholder="请输入策略名称"
              maxlength="100"
              show-word-limit
            />
          </el-form-item>

          <el-form-item label="策略描述" prop="description">
            <el-input
              v-model="formData.description"
              type="textarea"
              :rows="3"
              placeholder="请输入策略描述"
              maxlength="500"
              show-word-limit
            />
          </el-form-item>

          <el-form-item label="策略类型" prop="strategy_type" required>
            <el-select
              v-model="formData.strategy_type"
              placeholder="请选择策略类型"
              style="width: 100%"
            >
              <el-option
                v-for="option in STRATEGY_TYPE_OPTIONS"
                :key="option.value"
                :label="option.label"
                :value="option.value"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="编程语言" prop="language">
            <el-select
              v-model="formData.language"
              placeholder="请选择编程语言"
              style="width: 100%"
            >
              <el-option label="Python" value="python" />
              <el-option label="JavaScript" value="javascript" />
            </el-select>
          </el-form-item>

          <el-form-item label="入口函数" prop="entry_point">
            <el-input
              v-model="formData.entry_point"
              placeholder="请输入入口函数名"
            />
          </el-form-item>

          <el-form-item label="时间周期" prop="timeframe">
            <el-select
              v-model="formData.timeframe"
              placeholder="请选择时间周期"
              style="width: 100%"
              clearable
            >
              <el-option label="1分钟" value="1m" />
              <el-option label="5分钟" value="5m" />
              <el-option label="15分钟" value="15m" />
              <el-option label="30分钟" value="30m" />
              <el-option label="1小时" value="1h" />
              <el-option label="4小时" value="4h" />
              <el-option label="1天" value="1d" />
              <el-option label="1周" value="1w" />
            </el-select>
          </el-form-item>

          <el-form-item label="交易标的" prop="symbols">
            <el-select
              v-model="formData.symbols"
              multiple
              filterable
              allow-create
              placeholder="请输入或选择交易标的"
              style="width: 100%"
            >
              <el-option
                v-for="symbol in commonSymbols"
                :key="symbol"
                :label="symbol"
                :value="symbol"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="策略标签" prop="tags">
            <el-select
              v-model="formData.tags"
              multiple
              filterable
              allow-create
              placeholder="请输入策略标签"
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
              v-model="formData.is_public"
              active-text="公开"
              inactive-text="私有"
            />
            <div class="form-tip">
              公开的策略可以被其他用户查看和复制
            </div>
          </el-form-item>
        </el-tab-pane>

        <!-- 风险控制 -->
        <el-tab-pane label="风险控制" name="risk">
          <el-form-item label="最大持仓规模" prop="max_position_size">
            <el-input-number
              v-model="formData.max_position_size"
              :min="0"
              :precision="2"
              placeholder="最大持仓规模"
              style="width: 100%"
            />
            <div class="form-tip">
              限制策略的最大持仓规模，0表示不限制
            </div>
          </el-form-item>

          <el-form-item label="最大回撤限制" prop="max_drawdown">
            <el-input-number
              v-model="formData.max_drawdown"
              :min="0"
              :max="1"
              :step="0.01"
              :precision="2"
              placeholder="最大回撤限制"
              style="width: 100%"
            />
            <div class="form-tip">
              当回撤超过此比例时自动停止策略，范围0-1
            </div>
          </el-form-item>

          <el-form-item label="止损比例" prop="stop_loss">
            <el-input-number
              v-model="formData.stop_loss"
              :min="0"
              :max="1"
              :step="0.01"
              :precision="2"
              placeholder="止损比例"
              style="width: 100%"
            />
            <div class="form-tip">
              单笔交易的止损比例，范围0-1
            </div>
          </el-form-item>

          <el-form-item label="止盈比例" prop="take_profit">
            <el-input-number
              v-model="formData.take_profit"
              :min="0"
              :step="0.01"
              :precision="2"
              placeholder="止盈比例"
              style="width: 100%"
            />
            <div class="form-tip">
              单笔交易的止盈比例
            </div>
          </el-form-item>
        </el-tab-pane>

        <!-- 策略代码 -->
        <el-tab-pane label="策略代码" name="code">
          <el-form-item label="策略代码" prop="code" required>
            <div class="code-editor-container">
              <MonacoEditor
                v-model="formData.code"
                :language="formData.language"
                height="400px"
                :show-toolbar="true"
                :show-status="false"
                placeholder="请输入策略代码"
              />
              <div class="code-actions">
                <el-button size="small" @click="loadTemplate">
                  加载模板
                </el-button>
              </div>
            </div>
          </el-form-item>
        </el-tab-pane>

        <!-- 策略参数 -->
        <el-tab-pane label="策略参数" name="parameters">
          <div class="parameters-section">
            <div class="section-header">
              <span>策略参数配置</span>
              <el-button size="small" @click="addParameter">
                <el-icon><Plus /></el-icon>
                添加参数
              </el-button>
            </div>

            <div class="parameters-list">
              <div
                v-for="(param, index) in parameterList"
                :key="index"
                class="parameter-item"
              >
                <el-input
                  v-model="param.key"
                  placeholder="参数名"
                  style="width: 200px"
                />
                <el-select
                  v-model="param.type"
                  placeholder="类型"
                  style="width: 100px; margin-left: 10px"
                >
                  <el-option label="字符串" value="string" />
                  <el-option label="数字" value="number" />
                  <el-option label="布尔" value="boolean" />
                </el-select>
                <el-input
                  v-model="param.value"
                  placeholder="参数值"
                  style="width: 200px; margin-left: 10px"
                />
                <el-button
                  type="danger"
                  size="small"
                  @click="removeParameter(index)"
                  style="margin-left: 10px"
                >
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>

              <div v-if="parameterList.length === 0" class="no-parameters">
                暂无参数，点击上方按钮添加参数
              </div>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-form>
  </BaseDialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Delete } from '@element-plus/icons-vue'

import { BaseDialog, MonacoEditor } from '@/components/common'
import { useStrategyStore } from '@/stores/strategy'
import {
  STRATEGY_TYPE_OPTIONS,
  StrategyType,
  type StrategyCreateRequest
} from '@/types/strategy'

interface Props {
  modelValue: boolean
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'success', strategy: any): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const strategyStore = useStrategyStore()

// 响应式数据
const formRef = ref()
const activeTab = ref('basic')
const loading = ref(false)

const formData = ref<StrategyCreateRequest>({
  name: '',
  description: '',
  strategy_type: StrategyType.CUSTOM,
  code: '',
  entry_point: 'main',
  language: 'python',
  timeframe: '',
  symbols: [],
  tags: [],
  is_public: false,
  max_position_size: undefined,
  max_drawdown: undefined,
  stop_loss: undefined,
  take_profit: undefined,
  parameters: {}
})

interface Parameter {
  key: string
  type: 'string' | 'number' | 'boolean'
  value: string
}

const parameterList = ref<Parameter[]>([])

// 计算属性
const dialogVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// 常用选项
const commonSymbols = [
  'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'DOTUSDT',
  'XRPUSDT', 'LTCUSDT', 'LINKUSDT', 'BCHUSDT', 'XLMUSDT'
]

const commonTags = [
  '趋势跟踪', '均值回归', '套利', '高频', '量化',
  '机器学习', '技术分析', '基本面', '多因子', '风险平价'
]

// 表单验证规则
const formRules = {
  name: [
    { required: true, message: '请输入策略名称', trigger: 'blur' },
    { min: 1, max: 100, message: '策略名称长度在1到100个字符', trigger: 'blur' }
  ],
  strategy_type: [
    { required: true, message: '请选择策略类型', trigger: 'change' }
  ],
  code: [
    { required: true, message: '请输入策略代码', trigger: 'blur' },
    { min: 10, message: '策略代码至少需要10个字符', trigger: 'blur' }
  ],
  entry_point: [
    { required: true, message: '请输入入口函数名', trigger: 'blur' }
  ],
  language: [
    { required: true, message: '请选择编程语言', trigger: 'change' }
  ]
}

// 方法
const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
    
    loading.value = true
    
    // 处理参数
    const parameters: Record<string, any> = {}
    parameterList.value.forEach(param => {
      if (param.key && param.value) {
        let value: any = param.value
        
        // 类型转换
        if (param.type === 'number') {
          value = Number(param.value)
        } else if (param.type === 'boolean') {
          value = param.value.toLowerCase() === 'true'
        }
        
        parameters[param.key] = value
      }
    })
    
    const requestData: StrategyCreateRequest = {
      ...formData.value,
      parameters
    }
    
    const strategy = await strategyStore.createStrategy(requestData)
    
    if (strategy) {
      emit('success', strategy)
      resetForm()
    }
  } catch (error) {
    console.error('创建策略失败:', error)
  } finally {
    loading.value = false
  }
}

const handleCancel = () => {
  resetForm()
  dialogVisible.value = false
}

const resetForm = () => {
  formData.value = {
    name: '',
    description: '',
    strategy_type: StrategyType.CUSTOM,
    code: '',
    entry_point: 'main',
    language: 'python',
    timeframe: '',
    symbols: [],
    tags: [],
    is_public: false,
    max_position_size: undefined,
    max_drawdown: undefined,
    stop_loss: undefined,
    take_profit: undefined,
    parameters: {}
  }
  
  parameterList.value = []
  activeTab.value = 'basic'
  formRef.value?.clearValidate()
}

const addParameter = () => {
  parameterList.value.push({
    key: '',
    type: 'string',
    value: ''
  })
}

const removeParameter = (index: number) => {
  parameterList.value.splice(index, 1)
}



const loadTemplate = () => {
  // 简单的策略模板
  const template = `def main(context):
    """
    策略主函数
    
    Args:
        context: 策略上下文对象
    """
    # 获取当前价格
    current_price = context.get_current_price()
    
    # 获取历史数据
    history_data = context.get_history_data(period=20)
    
    # 计算移动平均线
    ma_short = history_data.close.rolling(5).mean().iloc[-1]
    ma_long = history_data.close.rolling(20).mean().iloc[-1]
    
    # 交易逻辑
    if ma_short > ma_long:
        # 买入信号
        context.buy(size=1000)
    elif ma_short < ma_long:
        # 卖出信号
        context.sell(size=1000)
`
  
  formData.value.code = template
  ElMessage.success('模板加载成功')
}

// 监听对话框关闭
watch(dialogVisible, (visible) => {
  if (!visible) {
    resetForm()
  }
})
</script>

<style lang="scss" scoped>
.form-tip {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
  line-height: 1.4;
}

.code-editor-container {
  position: relative;
  
  .code-textarea {
    :deep(.el-textarea__inner) {
      font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
      font-size: 13px;
      line-height: 1.5;
    }
  }
  
  .code-actions {
    position: absolute;
    top: 8px;
    right: 8px;
    display: flex;
    gap: 8px;
  }
}

.parameters-section {
  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--el-border-color-light);
    
    span {
      font-weight: 600;
      color: var(--el-text-color-primary);
    }
  }
  
  .parameters-list {
    .parameter-item {
      display: flex;
      align-items: center;
      margin-bottom: 12px;
      padding: 12px;
      background: var(--el-fill-color-light);
      border-radius: 4px;
    }
    
    .no-parameters {
      text-align: center;
      color: var(--el-text-color-secondary);
      padding: 40px;
      background: var(--el-fill-color-light);
      border-radius: 4px;
    }
  }
}

:deep(.el-tabs--border-card) {
  .el-tabs__content {
    padding: 20px;
  }
}
</style>