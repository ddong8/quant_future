<template>
  <div class="backtest-config">
    <div class="config-header">
      <h3>回测配置</h3>
      <div class="config-actions">
        <el-button 
          type="primary" 
          icon="el-icon-folder-opened"
          @click="showTemplateDialog = true"
        >
          选择模板
        </el-button>
        <el-button 
          type="success" 
          icon="el-icon-document-add"
          @click="saveAsTemplate"
        >
          保存为模板
        </el-button>
        <el-button 
          type="warning" 
          icon="el-icon-refresh"
          @click="resetConfig"
        >
          重置配置
        </el-button>
      </div>
    </div>

    <el-form 
      ref="configForm" 
      :model="config" 
      :rules="configRules" 
      label-width="120px"
      class="config-form"
    >
      <!-- 基础设置 -->
      <el-card class="config-section" shadow="never">
        <template #header>
          <div class="section-header">
            <el-icon><Setting /></el-icon>
            <span>基础设置</span>
          </div>
        </template>
        
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="回测名称" prop="name">
              <el-input 
                v-model="config.name" 
                placeholder="请输入回测名称"
                maxlength="100"
                show-word-limit
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="回测类型" prop="backtest_type">
              <el-select v-model="config.backtest_type" placeholder="选择回测类型">
                <el-option 
                  v-for="type in backtestTypes" 
                  :key="type.value" 
                  :label="type.label" 
                  :value="type.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="初始资金" prop="initial_capital">
              <el-input-number 
                v-model="config.initial_capital" 
                :min="1000" 
                :max="100000000"
                :step="1000"
                controls-position="right"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="基准指数" prop="benchmark">
              <el-select 
                v-model="config.benchmark" 
                placeholder="选择基准指数"
                filterable
                allow-create
              >
                <el-option 
                  v-for="benchmark in benchmarks" 
                  :key="benchmark.value" 
                  :label="benchmark.label" 
                  :value="benchmark.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="数据频率" prop="frequency">
              <el-select v-model="config.frequency" placeholder="选择数据频率">
                <el-option 
                  v-for="freq in frequencies" 
                  :key="freq.value" 
                  :label="freq.label" 
                  :value="freq.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="数据源" prop="data_source">
              <el-select v-model="config.data_source" placeholder="选择数据源">
                <el-option 
                  v-for="source in dataSources" 
                  :key="source.value" 
                  :label="source.label" 
                  :value="source.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="回测描述" prop="description">
          <el-input 
            v-model="config.description" 
            type="textarea" 
            :rows="3"
            placeholder="请输入回测描述"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
      </el-card>

      <!-- 时间设置 -->
      <el-card class="config-section" shadow="never">
        <template #header>
          <div class="section-header">
            <el-icon><Calendar /></el-icon>
            <span>时间设置</span>
          </div>
        </template>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="开始日期" prop="start_date">
              <el-date-picker
                v-model="config.start_date"
                type="date"
                placeholder="选择开始日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="结束日期" prop="end_date">
              <el-date-picker
                v-model="config.end_date"
                type="date"
                placeholder="选择结束日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <div class="date-shortcuts">
          <el-button 
            v-for="shortcut in dateShortcuts" 
            :key="shortcut.text"
            size="small"
            @click="setDateRange(shortcut.value)"
          >
            {{ shortcut.text }}
          </el-button>
        </div>
      </el-card>

      <!-- 交易设置 -->
      <el-card class="config-section" shadow="never">
        <template #header>
          <div class="section-header">
            <el-icon><Money /></el-icon>
            <span>交易设置</span>
          </div>
        </template>
        
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="手续费率" prop="commission_rate">
              <el-input-number 
                v-model="config.commission_rate" 
                :min="0" 
                :max="0.1"
                :step="0.0001"
                :precision="4"
                controls-position="right"
                style="width: 100%"
              />
              <div class="form-tip">单位：%，如0.001表示0.1%</div>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="滑点率" prop="slippage_rate">
              <el-input-number 
                v-model="config.slippage_rate" 
                :min="0" 
                :max="0.1"
                :step="0.0001"
                :precision="4"
                controls-position="right"
                style="width: 100%"
              />
              <div class="form-tip">单位：%，如0.001表示0.1%</div>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="最小手续费" prop="min_commission">
              <el-input-number 
                v-model="config.min_commission" 
                :min="0" 
                :max="1000"
                :step="0.1"
                :precision="2"
                controls-position="right"
                style="width: 100%"
              />
              <div class="form-tip">单位：元</div>
            </el-form-item>
          </el-col>
        </el-row>
      </el-card>

      <!-- 风险控制 -->
      <el-card class="config-section" shadow="never">
        <template #header>
          <div class="section-header">
            <el-icon><Warning /></el-icon>
            <span>风险控制</span>
          </div>
        </template>
        
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="最大持仓比例" prop="max_position_size">
              <el-input-number 
                v-model="config.max_position_size" 
                :min="0.01" 
                :max="1"
                :step="0.01"
                :precision="2"
                controls-position="right"
                style="width: 100%"
              />
              <div class="form-tip">单位：%，如0.2表示20%</div>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="止损比例">
              <el-input-number 
                v-model="config.stop_loss" 
                :min="0" 
                :max="1"
                :step="0.01"
                :precision="2"
                controls-position="right"
                style="width: 100%"
                placeholder="不设置"
              />
              <div class="form-tip">可选，如0.1表示10%止损</div>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="止盈比例">
              <el-input-number 
                v-model="config.take_profit" 
                :min="0" 
                :max="10"
                :step="0.01"
                :precision="2"
                controls-position="right"
                style="width: 100%"
                placeholder="不设置"
              />
              <div class="form-tip">可选，如0.2表示20%止盈</div>
            </el-form-item>
          </el-col>
        </el-row>
      </el-card>

      <!-- 交易标的 -->
      <el-card class="config-section" shadow="never">
        <template #header>
          <div class="section-header">
            <el-icon><List /></el-icon>
            <span>交易标的</span>
          </div>
        </template>
        
        <el-form-item label="选择标的" prop="symbols">
          <div class="symbol-selector">
            <el-select
              v-model="selectedSymbol"
              placeholder="搜索并选择交易标的"
              filterable
              remote
              :remote-method="searchSymbols"
              :loading="symbolLoading"
              style="width: 300px; margin-right: 10px;"
            >
              <el-option
                v-for="symbol in symbolOptions"
                :key="symbol.code"
                :label="`${symbol.code} - ${symbol.name}`"
                :value="symbol.code"
              />
            </el-select>
            <el-button type="primary" @click="addSymbol">添加</el-button>
          </div>
          
          <div class="selected-symbols" v-if="config.symbols.length > 0">
            <el-tag
              v-for="symbol in config.symbols"
              :key="symbol"
              closable
              @close="removeSymbol(symbol)"
              style="margin: 5px 5px 0 0;"
            >
              {{ symbol }}
            </el-tag>
          </div>
          
          <div class="symbol-categories">
            <el-button 
              v-for="category in symbolCategories" 
              :key="category.key"
              size="small"
              @click="addSymbolCategory(category.symbols)"
            >
              {{ category.name }}
            </el-button>
          </div>
        </el-form-item>
      </el-card>

      <!-- 高级设置 -->
      <el-card class="config-section" shadow="never" v-if="showAdvancedSettings">
        <template #header>
          <div class="section-header">
            <el-icon><Tools /></el-icon>
            <span>高级设置</span>
          </div>
        </template>
        
        <!-- 滚动回测设置 -->
        <div v-if="config.backtest_type === 'walk_forward'">
          <h4>滚动回测参数</h4>
          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item label="训练期（天）">
                <el-input-number 
                  v-model="config.walk_forward_settings.training_period" 
                  :min="30" 
                  :max="1000"
                  controls-position="right"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="测试期（天）">
                <el-input-number 
                  v-model="config.walk_forward_settings.testing_period" 
                  :min="10" 
                  :max="365"
                  controls-position="right"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="步长（天）">
                <el-input-number 
                  v-model="config.walk_forward_settings.step_size" 
                  :min="1" 
                  :max="100"
                  controls-position="right"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
          </el-row>
        </div>

        <!-- 蒙特卡洛设置 -->
        <div v-if="config.backtest_type === 'monte_carlo'">
          <h4>蒙特卡洛参数</h4>
          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item label="模拟次数">
                <el-input-number 
                  v-model="config.monte_carlo_settings.simulation_count" 
                  :min="100" 
                  :max="10000"
                  :step="100"
                  controls-position="right"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="置信水平">
                <el-input-number 
                  v-model="config.monte_carlo_settings.confidence_level" 
                  :min="0.8" 
                  :max="0.99"
                  :step="0.01"
                  :precision="2"
                  controls-position="right"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="随机种子">
                <el-input-number 
                  v-model="config.monte_carlo_settings.random_seed" 
                  :min="1" 
                  :max="9999"
                  controls-position="right"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
          </el-row>
        </div>
      </el-card>

      <!-- 标签设置 -->
      <el-card class="config-section" shadow="never">
        <template #header>
          <div class="section-header">
            <el-icon><Collection /></el-icon>
            <span>标签设置</span>
          </div>
        </template>
        
        <el-form-item label="标签" prop="tags">
          <el-select
            v-model="config.tags"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="添加标签"
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

        <el-form-item>
          <el-checkbox v-model="config.is_public">公开此回测配置</el-checkbox>
        </el-form-item>
      </el-card>
    </el-form>

    <div class="config-footer">
      <el-button @click="toggleAdvancedSettings">
        {{ showAdvancedSettings ? '隐藏' : '显示' }}高级设置
      </el-button>
      <div class="footer-actions">
        <el-button @click="validateConfig">验证配置</el-button>
        <el-button type="primary" @click="saveConfig">保存配置</el-button>
        <el-button type="success" @click="startBacktest">开始回测</el-button>
      </div>
    </div>

    <!-- 模板选择对话框 -->
    <el-dialog
      v-model="showTemplateDialog"
      title="选择配置模板"
      width="80%"
      :before-close="handleTemplateDialogClose"
    >
      <BacktestTemplateSelector
        @select="handleTemplateSelect"
        @close="showTemplateDialog = false"
      />
    </el-dialog>

    <!-- 保存模板对话框 -->
    <el-dialog
      v-model="showSaveTemplateDialog"
      title="保存为模板"
      width="500px"
    >
      <el-form :model="templateForm" label-width="80px">
        <el-form-item label="模板名称" required>
          <el-input v-model="templateForm.name" placeholder="请输入模板名称" />
        </el-form-item>
        <el-form-item label="模板描述">
          <el-input 
            v-model="templateForm.description" 
            type="textarea" 
            :rows="3"
            placeholder="请输入模板描述"
          />
        </el-form-item>
        <el-form-item label="模板分类">
          <el-select v-model="templateForm.category" placeholder="选择分类">
            <el-option
              v-for="category in templateCategories"
              :key="category.key"
              :label="category.name"
              :value="category.key"
            />
          </el-select>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showSaveTemplateDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmSaveTemplate">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Setting, Calendar, Money, Warning, List, Tools, Collection } from '@element-plus/icons-vue'
import BacktestTemplateSelector from './BacktestTemplateSelector.vue'
import { backtestApi } from '@/api/backtest'
import { marketApi } from '@/api/market'

export default {
  name: 'BacktestConfig',
  components: {
    BacktestTemplateSelector,
    Setting,
    Calendar,
    Money,
    Warning,
    List,
    Tools,
    Collection
  },
  props: {
    strategyId: {
      type: Number,
      required: true
    },
    initialConfig: {
      type: Object,
      default: () => ({})
    }
  },
  emits: ['config-change', 'start-backtest'],
  setup(props, { emit }) {
    const configForm = ref(null)
    const showAdvancedSettings = ref(false)
    const showTemplateDialog = ref(false)
    const showSaveTemplateDialog = ref(false)
    const symbolLoading = ref(false)
    const selectedSymbol = ref('')
    const symbolOptions = ref([])

    // 配置数据
    const config = reactive({
      name: '',
      description: '',
      backtest_type: 'simple',
      strategy_id: props.strategyId,
      start_date: '',
      end_date: '',
      initial_capital: 100000,
      benchmark: '000300.SH',
      commission_rate: 0.001,
      slippage_rate: 0.001,
      min_commission: 5.0,
      max_position_size: 1.0,
      stop_loss: null,
      take_profit: null,
      data_source: 'default',
      symbols: [],
      frequency: '1d',
      tags: [],
      is_public: false,
      walk_forward_settings: {
        training_period: 252,
        testing_period: 63,
        step_size: 21
      },
      monte_carlo_settings: {
        simulation_count: 1000,
        confidence_level: 0.95,
        random_seed: 42
      }
    })

    // 模板表单
    const templateForm = reactive({
      name: '',
      description: '',
      category: 'user_custom'
    })

    // 配置验证规则
    const configRules = {
      name: [
        { required: true, message: '请输入回测名称', trigger: 'blur' },
        { min: 1, max: 100, message: '长度在 1 到 100 个字符', trigger: 'blur' }
      ],
      backtest_type: [
        { required: true, message: '请选择回测类型', trigger: 'change' }
      ],
      start_date: [
        { required: true, message: '请选择开始日期', trigger: 'change' }
      ],
      end_date: [
        { required: true, message: '请选择结束日期', trigger: 'change' }
      ],
      initial_capital: [
        { required: true, message: '请输入初始资金', trigger: 'blur' },
        { type: 'number', min: 1000, message: '初始资金不能少于1000', trigger: 'blur' }
      ],
      symbols: [
        { required: true, message: '请至少选择一个交易标的', trigger: 'change' }
      ]
    }

    // 回测类型选项
    const backtestTypes = [
      { value: 'simple', label: '简单回测' },
      { value: 'walk_forward', label: '滚动回测' },
      { value: 'monte_carlo', label: '蒙特卡洛回测' },
      { value: 'cross_validation', label: '交叉验证回测' }
    ]

    // 基准指数选项
    const benchmarks = [
      { value: '000300.SH', label: '沪深300' },
      { value: '000905.SH', label: '中证500' },
      { value: '000852.SH', label: '中证1000' },
      { value: '399006.SZ', label: '创业板指' },
      { value: '000001.SH', label: '上证指数' },
      { value: '399001.SZ', label: '深证成指' }
    ]

    // 数据频率选项
    const frequencies = [
      { value: '1m', label: '1分钟' },
      { value: '5m', label: '5分钟' },
      { value: '15m', label: '15分钟' },
      { value: '30m', label: '30分钟' },
      { value: '1h', label: '1小时' },
      { value: '4h', label: '4小时' },
      { value: '1d', label: '1天' },
      { value: '1w', label: '1周' },
      { value: '1M', label: '1月' }
    ]

    // 数据源选项
    const dataSources = [
      { value: 'default', label: '默认数据源' },
      { value: 'tushare', label: 'Tushare' },
      { value: 'akshare', label: 'AKShare' },
      { value: 'wind', label: 'Wind' },
      { value: 'custom', label: '自定义' }
    ]

    // 日期快捷选项
    const dateShortcuts = [
      {
        text: '最近1年',
        value: () => {
          const end = new Date()
          const start = new Date()
          start.setFullYear(start.getFullYear() - 1)
          return [start, end]
        }
      },
      {
        text: '最近2年',
        value: () => {
          const end = new Date()
          const start = new Date()
          start.setFullYear(start.getFullYear() - 2)
          return [start, end]
        }
      },
      {
        text: '最近3年',
        value: () => {
          const end = new Date()
          const start = new Date()
          start.setFullYear(start.getFullYear() - 3)
          return [start, end]
        }
      },
      {
        text: '最近5年',
        value: () => {
          const end = new Date()
          const start = new Date()
          start.setFullYear(start.getFullYear() - 5)
          return [start, end]
        }
      }
    ]

    // 标的分类
    const symbolCategories = [
      {
        key: 'hs300',
        name: '沪深300',
        symbols: ['000001.SZ', '000002.SZ', '000858.SZ', '002415.SZ', '600000.SH']
      },
      {
        key: 'zz500',
        name: '中证500',
        symbols: ['002027.SZ', '002142.SZ', '002304.SZ', '002352.SZ', '002410.SZ']
      },
      {
        key: 'cyb',
        name: '创业板',
        symbols: ['300015.SZ', '300059.SZ', '300124.SZ', '300142.SZ', '300144.SZ']
      }
    ]

    // 常用标签
    const commonTags = [
      '股票', '期货', '基金', '债券', '期权',
      '趋势跟踪', '均值回归', '动量策略', '套利策略',
      '短线', '中线', '长线', '高频', '量化'
    ]

    // 模板分类
    const templateCategories = [
      { key: 'trend_following', name: '趋势跟踪' },
      { key: 'mean_reversion', name: '均值回归' },
      { key: 'arbitrage', name: '套利策略' },
      { key: 'market_making', name: '做市策略' },
      { key: 'momentum', name: '动量策略' },
      { key: 'statistical', name: '统计套利' },
      { key: 'user_custom', name: '用户自定义' }
    ]

    // 初始化配置
    const initConfig = () => {
      // 设置默认日期
      const endDate = new Date()
      const startDate = new Date()
      startDate.setFullYear(startDate.getFullYear() - 1)
      
      config.start_date = startDate.toISOString().split('T')[0]
      config.end_date = endDate.toISOString().split('T')[0]
      
      // 合并初始配置
      Object.assign(config, props.initialConfig)
    }

    // 设置日期范围
    const setDateRange = (dateRange) => {
      const [start, end] = dateRange()
      config.start_date = start.toISOString().split('T')[0]
      config.end_date = end.toISOString().split('T')[0]
    }

    // 搜索交易标的
    const searchSymbols = async (query) => {
      if (!query) {
        symbolOptions.value = []
        return
      }
      
      symbolLoading.value = true
      try {
        const response = await marketApi.searchSymbols(query)
        symbolOptions.value = response.data || []
      } catch (error) {
        console.error('搜索标的失败:', error)
        symbolOptions.value = []
      } finally {
        symbolLoading.value = false
      }
    }

    // 添加交易标的
    const addSymbol = () => {
      if (selectedSymbol.value && !config.symbols.includes(selectedSymbol.value)) {
        config.symbols.push(selectedSymbol.value)
        selectedSymbol.value = ''
        emit('config-change', config)
      }
    }

    // 移除交易标的
    const removeSymbol = (symbol) => {
      const index = config.symbols.indexOf(symbol)
      if (index > -1) {
        config.symbols.splice(index, 1)
        emit('config-change', config)
      }
    }

    // 添加标的分类
    const addSymbolCategory = (symbols) => {
      symbols.forEach(symbol => {
        if (!config.symbols.includes(symbol)) {
          config.symbols.push(symbol)
        }
      })
      emit('config-change', config)
    }

    // 切换高级设置
    const toggleAdvancedSettings = () => {
      showAdvancedSettings.value = !showAdvancedSettings.value
    }

    // 验证配置
    const validateConfig = async () => {
      try {
        await configForm.value.validate()
        
        // 自定义验证
        if (new Date(config.start_date) >= new Date(config.end_date)) {
          throw new Error('开始日期必须早于结束日期')
        }
        
        if (config.symbols.length === 0) {
          throw new Error('请至少选择一个交易标的')
        }
        
        ElMessage.success('配置验证通过')
        return true
      } catch (error) {
        ElMessage.error('配置验证失败: ' + error.message)
        return false
      }
    }

    // 保存配置
    const saveConfig = async () => {
      if (await validateConfig()) {
        emit('config-change', config)
        ElMessage.success('配置保存成功')
      }
    }

    // 开始回测
    const startBacktest = async () => {
      if (await validateConfig()) {
        emit('start-backtest', config)
      }
    }

    // 重置配置
    const resetConfig = () => {
      ElMessageBox.confirm('确定要重置配置吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        initConfig()
        ElMessage.success('配置已重置')
      })
    }

    // 保存为模板
    const saveAsTemplate = () => {
      templateForm.name = config.name + '_模板'
      templateForm.description = config.description
      showSaveTemplateDialog.value = true
    }

    // 确认保存模板
    const confirmSaveTemplate = async () => {
      if (!templateForm.name) {
        ElMessage.error('请输入模板名称')
        return
      }
      
      try {
        await backtestApi.saveConfigTemplate({
          name: templateForm.name,
          description: templateForm.description,
          category: templateForm.category,
          config_template: config
        })
        
        showSaveTemplateDialog.value = false
        ElMessage.success('模板保存成功')
      } catch (error) {
        ElMessage.error('模板保存失败: ' + error.message)
      }
    }

    // 处理模板选择
    const handleTemplateSelect = (template) => {
      Object.assign(config, template.config_template)
      showTemplateDialog.value = false
      ElMessage.success('模板加载成功')
      emit('config-change', config)
    }

    // 处理模板对话框关闭
    const handleTemplateDialogClose = () => {
      showTemplateDialog.value = false
    }

    onMounted(() => {
      initConfig()
    })

    return {
      configForm,
      config,
      configRules,
      templateForm,
      showAdvancedSettings,
      showTemplateDialog,
      showSaveTemplateDialog,
      symbolLoading,
      selectedSymbol,
      symbolOptions,
      backtestTypes,
      benchmarks,
      frequencies,
      dataSources,
      dateShortcuts,
      symbolCategories,
      commonTags,
      templateCategories,
      setDateRange,
      searchSymbols,
      addSymbol,
      removeSymbol,
      addSymbolCategory,
      toggleAdvancedSettings,
      validateConfig,
      saveConfig,
      startBacktest,
      resetConfig,
      saveAsTemplate,
      confirmSaveTemplate,
      handleTemplateSelect,
      handleTemplateDialogClose
    }
  }
}
</script>

<style scoped>
.backtest-config {
  padding: 20px;
}

.config-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.config-header h3 {
  margin: 0;
  color: #303133;
}

.config-actions {
  display: flex;
  gap: 10px;
}

.config-form {
  max-width: 1200px;
}

.config-section {
  margin-bottom: 20px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #303133;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.date-shortcuts {
  margin-top: 10px;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.symbol-selector {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.selected-symbols {
  margin-bottom: 10px;
}

.symbol-categories {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.config-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}

.footer-actions {
  display: flex;
  gap: 10px;
}

:deep(.el-card__header) {
  padding: 15px 20px;
  background-color: #fafafa;
}

:deep(.el-card__body) {
  padding: 20px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
}

:deep(.el-input-number) {
  width: 100%;
}
</style>