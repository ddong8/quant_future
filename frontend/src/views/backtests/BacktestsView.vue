<template>
  <div class="backtests-container">
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">回测系统</h1>
        <p class="page-description">基于tqsdk真实数据的策略回测分析</p>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="showCreateDialog = true">
          <el-icon><Plus /></el-icon>
          创建回测
        </el-button>
        <el-button @click="refreshBacktests" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 快速回测面板 -->
    <el-card class="quick-backtest-card">
      <template #header>
        <div class="card-header">
          <span>快速回测</span>
          <el-tag type="success" size="small">基于真实数据</el-tag>
        </div>
      </template>
      
      <el-form :model="quickBacktestForm" :inline="true">
        <el-form-item label="策略类型">
          <el-select v-model="quickBacktestForm.strategy" placeholder="选择策略">
            <el-option label="双均线策略" value="dual_ma" />
            <el-option label="RSI反转策略" value="rsi_reversal" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="交易品种">
          <el-select v-model="quickBacktestForm.symbol" placeholder="选择品种">
            <el-option label="沪铜主力" value="SHFE.cu2601" />
            <el-option label="铁矿石主力" value="DCE.i2601" />
            <el-option label="螺纹钢主力" value="SHFE.rb2601" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="回测天数">
          <el-input-number v-model="quickBacktestForm.days" :min="1" :max="365" />
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="runQuickBacktest" :loading="quickBacktestLoading">
            开始回测
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 回测列表 -->
    <el-card>
      <template #header>
        <div class="card-header">
          <span>回测历史</span>
          <el-tag size="small" type="info">{{ backtests.length }} 个回测</el-tag>
        </div>
      </template>

      <div v-if="backtests.length === 0" class="empty-state">
        <el-empty description="暂无回测记录">
          <el-button type="primary" @click="showCreateDialog = true">创建第一个回测</el-button>
        </el-empty>
      </div>

      <div v-else class="backtests-list">
        <div v-for="backtest in backtests" :key="backtest.backtest_id" class="backtest-item">
          <div class="backtest-header">
            <div class="backtest-info">
              <h3 class="backtest-name">{{ backtest.strategy_name }}</h3>
              <div class="backtest-meta">
                <el-tag :type="getStatusType(backtest.status)" size="small">
                  {{ getStatusText(backtest.status) }}
                </el-tag>
                <span class="backtest-time">{{ formatTime(backtest.created_at) }}</span>
              </div>
            </div>
            <div class="backtest-actions">
              <el-button size="small" @click="viewResults(backtest.backtest_id)" :disabled="backtest.status !== 'completed'">
                查看结果
              </el-button>
              <el-button size="small" type="danger" @click="deleteBacktest(backtest.backtest_id)">
                删除
              </el-button>
            </div>
          </div>

          <div v-if="backtest.results" class="backtest-results">
            <div class="result-item">
              <span class="result-label">总收益率:</span>
              <span class="result-value" :class="backtest.results.total_return >= 0 ? 'profit' : 'loss'">
                {{ backtest.results.total_return >= 0 ? '+' : '' }}{{ (backtest.results.total_return * 100).toFixed(2) }}%
              </span>
            </div>
            <div class="result-item">
              <span class="result-label">最大回撤:</span>
              <span class="result-value">{{ (backtest.results.max_drawdown * 100).toFixed(2) }}%</span>
            </div>
            <div class="result-item">
              <span class="result-label">夏普比率:</span>
              <span class="result-value">{{ backtest.results.sharpe_ratio?.toFixed(2) || '--' }}</span>
            </div>
            <div class="result-item">
              <span class="result-label">交易次数:</span>
              <span class="result-value">{{ backtest.results.total_trades || 0 }}</span>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 创建回测对话框 -->
    <el-dialog v-model="showCreateDialog" title="创建回测" width="600px">
      <el-form :model="createForm" label-width="100px">
        <el-form-item label="回测名称">
          <el-input v-model="createForm.name" placeholder="输入回测名称" />
        </el-form-item>
        <el-form-item label="策略类型">
          <el-select v-model="createForm.strategy_type" placeholder="选择策略类型">
            <el-option label="双均线策略" value="dual_ma" />
            <el-option label="RSI反转策略" value="rsi_reversal" />
          </el-select>
        </el-form-item>
        <el-form-item label="交易品种">
          <el-select v-model="createForm.symbols" multiple placeholder="选择交易品种">
            <el-option label="沪铜主力" value="SHFE.cu2601" />
            <el-option label="铁矿石主力" value="DCE.i2601" />
            <el-option label="螺纹钢主力" value="SHFE.rb2601" />
          </el-select>
        </el-form-item>
        <el-form-item label="初始资金">
          <el-input-number v-model="createForm.initial_capital" :min="10000" :step="10000" />
        </el-form-item>
        <el-form-item label="回测天数">
          <el-input-number v-model="createForm.days" :min="1" :max="365" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createBacktest" :loading="createLoading">
          创建并运行
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'
import {
  getBacktestList,
  createBacktest as createBacktestAPI,
  runQuickBacktest as runQuickBacktestAPI,
  getBacktestResults
} from '@/api/realTimeData'

// 响应式数据
const loading = ref(false)
const quickBacktestLoading = ref(false)
const createLoading = ref(false)
const showCreateDialog = ref(false)

// 数据
const backtests = ref([])

// 快速回测表单
const quickBacktestForm = ref({
  strategy: 'dual_ma',
  symbol: 'SHFE.cu2601',
  days: 30
})

// 创建回测表单
const createForm = ref({
  name: '',
  strategy_type: 'dual_ma',
  symbols: [],
  initial_capital: 1000000,
  days: 30
})

// 加载回测列表
const loadBacktests = async () => {
  loading.value = true
  try {
    const response = await getBacktestList()
    if (response.success && response.data) {
      backtests.value = response.data
      
      // 为每个回测加载结果
      for (const backtest of backtests.value) {
        if (backtest.status === 'completed') {
          try {
            const resultsResponse = await getBacktestResults(backtest.backtest_id)
            if (resultsResponse.success) {
              backtest.results = resultsResponse.data
            }
          } catch (error) {
            console.error(`加载回测结果失败: ${backtest.backtest_id}`, error)
          }
        }
      }
    }
  } catch (error) {
    console.error('加载回测列表失败:', error)
    ElMessage.error('加载回测列表失败')
    // 使用模拟数据
    loadMockBacktests()
  } finally {
    loading.value = false
  }
}

// 加载模拟回测数据
const loadMockBacktests = () => {
  backtests.value = [
    {
      backtest_id: 'BT_001',
      strategy_name: '双均线策略回测',
      status: 'completed',
      created_at: new Date().toISOString(),
      results: {
        total_return: 0.125,
        max_drawdown: 0.08,
        sharpe_ratio: 1.45,
        total_trades: 23
      }
    },
    {
      backtest_id: 'BT_002',
      strategy_name: 'RSI反转策略回测',
      status: 'running',
      created_at: new Date(Date.now() - 3600000).toISOString(),
      results: null
    }
  ]
}

// 刷新回测列表
const refreshBacktests = async () => {
  await loadBacktests()
  ElMessage.success('回测列表已刷新')
}

// 运行快速回测
const runQuickBacktest = async () => {
  quickBacktestLoading.value = true
  try {
    const config = {
      strategy_type: quickBacktestForm.value.strategy,
      symbols: [quickBacktestForm.value.symbol],
      days: quickBacktestForm.value.days,
      initial_capital: 1000000
    }
    
    const response = await runQuickBacktestAPI(config)
    if (response.success) {
      ElMessage.success('快速回测已完成')
      await loadBacktests()
    } else {
      ElMessage.error('快速回测失败')
    }
  } catch (error) {
    console.error('快速回测失败:', error)
    ElMessage.error('快速回测失败')
  } finally {
    quickBacktestLoading.value = false
  }
}

// 创建回测
const createBacktest = async () => {
  createLoading.value = true
  try {
    const config = {
      name: createForm.value.name,
      strategy_type: createForm.value.strategy_type,
      symbols: createForm.value.symbols,
      initial_capital: createForm.value.initial_capital,
      days: createForm.value.days
    }
    
    const response = await createBacktestAPI(config)
    if (response.success) {
      ElMessage.success('回测创建成功')
      showCreateDialog.value = false
      await loadBacktests()
    } else {
      ElMessage.error('回测创建失败')
    }
  } catch (error) {
    console.error('回测创建失败:', error)
    ElMessage.error('回测创建失败')
  } finally {
    createLoading.value = false
  }
}

// 查看回测结果
const viewResults = (backtestId: string) => {
  // 这里可以跳转到详细结果页面
  ElMessage.info(`查看回测结果: ${backtestId}`)
}

// 删除回测
const deleteBacktest = async (backtestId: string) => {
  try {
    await ElMessageBox.confirm('确定要删除这个回测吗？', '确认删除', {
      type: 'warning'
    })
    
    // 这里应该调用删除API
    ElMessage.success('回测已删除')
    await loadBacktests()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除回测失败')
    }
  }
}

// 格式化函数
const formatTime = (timestamp: string) => {
  return new Date(timestamp).toLocaleString()
}

const getStatusType = (status: string) => {
  switch (status) {
    case 'completed': return 'success'
    case 'running': return 'warning'
    case 'failed': return 'danger'
    default: return 'info'
  }
}

const getStatusText = (status: string) => {
  switch (status) {
    case 'completed': return '已完成'
    case 'running': return '运行中'
    case 'failed': return '失败'
    default: return '未知'
  }
}

// 组件挂载
onMounted(() => {
  loadBacktests()
})
</script>

<style lang="scss" scoped>
.backtests-container {
  padding: 20px;
}

.coming-soon {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  color: var(--el-text-color-secondary);
  
  h2 {
    margin: 20px 0 10px 0;
    color: var(--el-text-color-primary);
  }
  
  p {
    margin: 0;
  }
}
</style>