<template>
  <div class="backtest-view">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">策略回测</h1>
        <p class="page-description">基于历史数据验证交易策略的有效性</p>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="showCreateDialog = true">
          <el-icon><Plus /></el-icon>
          新建回测
        </el-button>
        <el-button @click="runDemoBacktest" :loading="demoLoading">
          <el-icon><VideoPlay /></el-icon>
          演示回测
        </el-button>
        <el-button @click="loadBacktests" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 回测列表 -->
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>回测任务</span>
          <el-tag type="info">{{ backtests.length }} 个任务</el-tag>
        </div>
      </template>

      <div v-if="backtests.length === 0" class="empty-state">
        <el-empty description="暂无回测任务">
          <el-button type="primary" @click="showCreateDialog = true">
            创建第一个回测
          </el-button>
        </el-empty>
      </div>

      <div v-else class="backtest-list">
        <div
          v-for="backtest in backtests"
          :key="backtest.backtest_id"
          class="backtest-item"
          @click="viewBacktestResults(backtest)"
        >
          <div class="backtest-header">
            <div class="backtest-info">
              <h3 class="backtest-title">{{ backtest.strategy_name || '未命名策略' }}</h3>
              <div class="backtest-meta">
                <span class="symbols">{{ backtest.symbols?.join(', ') }}</span>
                <span class="capital">初始资金: {{ formatCurrency(backtest.initial_capital) }}</span>
              </div>
            </div>
            <div class="backtest-status">
              <el-tag
                :type="getStatusType(backtest.status)"
                :effect="backtest.status === 'RUNNING' ? 'light' : 'plain'"
              >
                {{ getStatusText(backtest.status) }}
              </el-tag>
              <div v-if="backtest.status === 'RUNNING'" class="progress">
                <el-progress
                  :percentage="backtest.progress || 0"
                  :stroke-width="6"
                  :show-text="false"
                />
              </div>
            </div>
          </div>

          <div v-if="backtest.results" class="backtest-results">
            <div class="result-item">
              <span class="label">总收益率:</span>
              <span :class="getPnlClass(backtest.results.summary.total_return_pct)">
                {{ backtest.results.summary.total_return_pct.toFixed(2) }}%
              </span>
            </div>
            <div class="result-item">
              <span class="label">最大回撤:</span>
              <span class="value">{{ backtest.results.summary.max_drawdown_pct.toFixed(2) }}%</span>
            </div>
            <div class="result-item">
              <span class="label">夏普比率:</span>
              <span class="value">{{ backtest.results.summary.sharpe_ratio.toFixed(3) }}</span>
            </div>
            <div class="result-item">
              <span class="label">交易次数:</span>
              <span class="value">{{ backtest.results.summary.total_trades }}</span>
            </div>
          </div>

          <div class="backtest-time">
            创建时间: {{ formatTime(backtest.created_time) }}
          </div>
        </div>
      </div>
    </el-card>

    <!-- 创建回测对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      title="创建回测任务"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="createFormRef"
        :model="createForm"
        :rules="createRules"
        label-width="100px"
      >
        <el-form-item label="策略名称" prop="strategy_name">
          <el-input
            v-model="createForm.strategy_name"
            placeholder="请输入策略名称"
          />
        </el-form-item>

        <el-form-item label="交易标的" prop="symbols">
          <el-select
            v-model="createForm.symbols"
            multiple
            placeholder="选择交易标的"
            style="width: 100%"
          >
            <el-option
              v-for="instrument in instruments"
              :key="instrument.symbol"
              :label="`${instrument.name} (${instrument.symbol})`"
              :value="instrument.symbol"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="回测时间">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="初始资金" prop="initial_capital">
          <el-input-number
            v-model="createForm.initial_capital"
            :min="10000"
            :max="100000000"
            :step="10000"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="手续费率" prop="commission_rate">
          <el-input-number
            v-model="createForm.commission_rate"
            :min="0"
            :max="0.01"
            :step="0.0001"
            :precision="4"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="策略代码" prop="strategy_code">
          <el-input
            v-model="createForm.strategy_code"
            type="textarea"
            :rows="6"
            placeholder="请输入策略代码或描述"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showCreateDialog = false">取消</el-button>
          <el-button type="primary" @click="createBacktest" :loading="createLoading">
            创建并运行
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 回测结果对话框 -->
    <el-dialog
      v-model="showResultsDialog"
      title="回测结果"
      width="800px"
      :close-on-click-modal="false"
    >
      <div v-if="selectedBacktest && selectedBacktest.results" class="results-content">
        <!-- 概要统计 -->
        <div class="results-summary">
          <h3>回测概要</h3>
          <el-row :gutter="20">
            <el-col :span="8">
              <div class="summary-item">
                <div class="summary-label">初始资金</div>
                <div class="summary-value">
                  {{ formatCurrency(selectedBacktest.results.summary.initial_capital) }}
                </div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="summary-item">
                <div class="summary-label">最终资产</div>
                <div class="summary-value">
                  {{ formatCurrency(selectedBacktest.results.summary.final_value) }}
                </div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="summary-item">
                <div class="summary-label">总收益率</div>
                <div class="summary-value" :class="getPnlClass(selectedBacktest.results.summary.total_return_pct)">
                  {{ selectedBacktest.results.summary.total_return_pct.toFixed(2) }}%
                </div>
              </div>
            </el-col>
          </el-row>

          <el-row :gutter="20" style="margin-top: 20px">
            <el-col :span="8">
              <div class="summary-item">
                <div class="summary-label">最大回撤</div>
                <div class="summary-value">
                  {{ selectedBacktest.results.summary.max_drawdown_pct.toFixed(2) }}%
                </div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="summary-item">
                <div class="summary-label">夏普比率</div>
                <div class="summary-value">
                  {{ selectedBacktest.results.summary.sharpe_ratio.toFixed(3) }}
                </div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="summary-item">
                <div class="summary-label">交易次数</div>
                <div class="summary-value">
                  {{ selectedBacktest.results.summary.total_trades }}
                </div>
              </div>
            </el-col>
          </el-row>
        </div>

        <!-- 权益曲线 -->
        <div class="equity-curve" style="margin-top: 30px">
          <h3>权益曲线</h3>
          <div class="chart-container">
            <div v-if="selectedBacktest.results.equity_curve.length > 0" class="simple-chart">
              <div
                v-for="(point, index) in selectedBacktest.results.equity_curve"
                :key="index"
                class="chart-point"
                :style="{
                  left: `${(index / (selectedBacktest.results.equity_curve.length - 1)) * 100}%`,
                  bottom: `${((point.total_value - selectedBacktest.results.summary.initial_capital) / selectedBacktest.results.summary.initial_capital) * 100 + 50}%`
                }"
              />
            </div>
          </div>
        </div>

        <!-- 交易记录 -->
        <div class="trades-list" style="margin-top: 30px">
          <h3>交易记录</h3>
          <el-table
            :data="selectedBacktest.results.trades.slice(0, 10)"
            size="small"
            max-height="300"
          >
            <el-table-column prop="time" label="时间" width="120">
              <template #default="{ row }">
                {{ formatTime(row.time) }}
              </template>
            </el-table-column>
            <el-table-column prop="symbol" label="标的" width="120" />
            <el-table-column prop="side" label="方向" width="80">
              <template #default="{ row }">
                <span :class="row.side === 'BUY' ? 'buy' : 'sell'">
                  {{ row.side === 'BUY' ? '买入' : '卖出' }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="quantity" label="数量" width="80" />
            <el-table-column prop="price" label="价格" width="100">
              <template #default="{ row }">
                {{ row.price.toFixed(2) }}
              </template>
            </el-table-column>
            <el-table-column prop="signal" label="信号" />
          </el-table>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showResultsDialog = false">关闭</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, VideoPlay, Refresh } from '@element-plus/icons-vue'
import { request } from '@/utils/request'

// 响应式数据
const loading = ref(false)
const createLoading = ref(false)
const demoLoading = ref(false)
const showCreateDialog = ref(false)
const showResultsDialog = ref(false)

// 回测列表
const backtests = ref([])

// 合约列表
const instruments = ref([])

// 选中的回测
const selectedBacktest = ref(null)

// 创建表单
const createForm = ref({
  strategy_name: '',
  symbols: [],
  initial_capital: 1000000,
  commission_rate: 0.0001,
  strategy_code: '# 双均线策略示例\n# 当短期均线上穿长期均线时买入\n# 当短期均线下穿长期均线时卖出'
})

// 日期范围
const dateRange = ref(['2024-01-01', '2024-06-30'])

// 表单验证规则
const createRules = {
  strategy_name: [
    { required: true, message: '请输入策略名称', trigger: 'blur' }
  ],
  symbols: [
    { required: true, message: '请选择交易标的', trigger: 'change' }
  ],
  initial_capital: [
    { required: true, message: '请输入初始资金', trigger: 'blur' }
  ]
}

// 方法
const formatCurrency = (amount: number) => {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY',
    minimumFractionDigits: 0
  }).format(amount)
}

const formatTime = (timeStr: string) => {
  return new Date(timeStr).toLocaleString('zh-CN')
}

const getPnlClass = (value: number) => {
  if (value > 0) return 'profit'
  if (value < 0) return 'loss'
  return 'neutral'
}

const getStatusType = (status: string) => {
  const statusMap = {
    'CREATED': 'info',
    'RUNNING': 'warning',
    'COMPLETED': 'success',
    'FAILED': 'danger'
  }
  return statusMap[status] || 'info'
}

const getStatusText = (status: string) => {
  const statusMap = {
    'CREATED': '已创建',
    'RUNNING': '运行中',
    'COMPLETED': '已完成',
    'FAILED': '失败'
  }
  return statusMap[status] || status
}

// API 调用方法
const loadInstruments = async () => {
  try {
    const response = await request.get('/v1/market/instruments')
    if (response.success) {
      instruments.value = response.data
    }
  } catch (error) {
    console.error('获取合约信息失败:', error)
  }
}

const loadBacktests = async () => {
  try {
    loading.value = true
    const response = await request.get('/v1/backtest/list')
    if (response.success) {
      backtests.value = response.data
    }
  } catch (error) {
    console.error('获取回测列表失败:', error)
    ElMessage.error('获取回测列表失败')
  } finally {
    loading.value = false
  }
}

const createBacktest = async () => {
  try {
    createLoading.value = true
    
    if (!dateRange.value || dateRange.value.length !== 2) {
      ElMessage.error('请选择回测时间范围')
      return
    }
    
    const requestData = {
      ...createForm.value,
      start_date: new Date(dateRange.value[0]).toISOString(),
      end_date: new Date(dateRange.value[1]).toISOString()
    }
    
    const response = await request.post('/v1/backtest/quick-run', requestData)
    
    if (response.success) {
      ElMessage.success('回测创建并运行成功')
      showCreateDialog.value = false
      
      // 重置表单
      createForm.value = {
        strategy_name: '',
        symbols: [],
        initial_capital: 1000000,
        commission_rate: 0.0001,
        strategy_code: '# 双均线策略示例\n# 当短期均线上穿长期均线时买入\n# 当短期均线下穿长期均线时卖出'
      }
      dateRange.value = ['2024-01-01', '2024-06-30']
      
      // 刷新列表
      await loadBacktests()
      
      // 显示结果
      if (response.data.results) {
        selectedBacktest.value = {
          ...response.data,
          strategy_name: requestData.strategy_name
        }
        showResultsDialog.value = true
      }
    } else {
      ElMessage.error('回测创建失败')
    }
  } catch (error) {
    console.error('创建回测失败:', error)
    ElMessage.error('创建回测失败')
  } finally {
    createLoading.value = false
  }
}

const runDemoBacktest = async () => {
  try {
    demoLoading.value = true
    
    const response = await request.post('/v1/backtest/demo')
    
    if (response.success) {
      ElMessage.success('演示回测完成')
      
      // 刷新列表
      await loadBacktests()
      
      // 显示结果
      selectedBacktest.value = response.data
      showResultsDialog.value = true
    } else {
      ElMessage.error('演示回测失败')
    }
  } catch (error) {
    console.error('演示回测失败:', error)
    ElMessage.error('演示回测失败')
  } finally {
    demoLoading.value = false
  }
}

const viewBacktestResults = async (backtest: any) => {
  try {
    if (backtest.status === 'COMPLETED') {
      const response = await request.get(`/v1/backtest/results/${backtest.backtest_id}`)
      if (response.success) {
        selectedBacktest.value = {
          ...backtest,
          results: response.data
        }
        showResultsDialog.value = true
      }
    } else {
      selectedBacktest.value = backtest
      showResultsDialog.value = true
    }
  } catch (error) {
    console.error('获取回测结果失败:', error)
    ElMessage.error('获取回测结果失败')
  }
}

// 初始化
onMounted(async () => {
  await loadInstruments()
  await loadBacktests()
})
</script>

<style scoped>
.backtest-view {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--el-border-color-light);
}

.header-left {
  flex: 1;
}

.page-title {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.page-description {
  margin: 0;
  color: var(--el-text-color-regular);
  font-size: 14px;
}

.header-right {
  display: flex;
  gap: 12px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

.backtest-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.backtest-item {
  padding: 20px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.backtest-item:hover {
  border-color: var(--el-color-primary);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.backtest-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.backtest-info {
  flex: 1;
}

.backtest-title {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.backtest-meta {
  display: flex;
  gap: 16px;
  font-size: 14px;
  color: var(--el-text-color-regular);
}

.backtest-status {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
}

.progress {
  width: 120px;
}

.backtest-results {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
  margin-bottom: 12px;
}

.result-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
}

.label {
  color: var(--el-text-color-regular);
}

.value {
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.profit {
  color: #f56c6c;
}

.loss {
  color: #67c23a;
}

.neutral {
  color: var(--el-text-color-regular);
}

.backtest-time {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
}

.results-content {
  max-height: 600px;
  overflow-y: auto;
}

.results-summary {
  padding: 20px;
  background: var(--el-bg-color-page);
  border-radius: 8px;
}

.summary-item {
  text-align: center;
}

.summary-label {
  font-size: 14px;
  color: var(--el-text-color-regular);
  margin-bottom: 8px;
}

.summary-value {
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.chart-container {
  height: 200px;
  background: var(--el-bg-color-page);
  border-radius: 8px;
  position: relative;
  overflow: hidden;
}

.simple-chart {
  position: relative;
  width: 100%;
  height: 100%;
}

.chart-point {
  position: absolute;
  width: 2px;
  height: 2px;
  background: var(--el-color-primary);
  border-radius: 50%;
}

.buy {
  color: #f56c6c;
}

.sell {
  color: #67c23a;
}

@media (max-width: 768px) {
  .backtest-view {
    padding: 10px;
  }
  
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .header-right {
    width: 100%;
    justify-content: flex-end;
  }
  
  .backtest-header {
    flex-direction: column;
    gap: 12px;
  }
  
  .backtest-results {
    grid-template-columns: 1fr;
  }
}
</style>