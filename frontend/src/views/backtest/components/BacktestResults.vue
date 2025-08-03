<template>
  <div class="backtest-results">
    <div class="results-header">
      <div class="header-info">
        <h3>{{ backtest.name }}</h3>
        <div class="header-meta">
          <el-tag :type="getStatusType(backtest.status)">
            {{ getStatusText(backtest.status) }}
          </el-tag>
          <span class="meta-item">
            <el-icon><Calendar /></el-icon>
            {{ formatDateRange(backtest.start_date, backtest.end_date) }}
          </span>
          <span class="meta-item">
            <el-icon><Money /></el-icon>
            初始资金: {{ formatCurrency(backtest.initial_capital) }}
          </span>
        </div>
      </div>
      <div class="header-actions">
        <el-button 
          type="primary" 
          icon="el-icon-download"
          @click="exportReport"
        >
          导出报告
        </el-button>
        <el-button 
          type="success" 
          icon="el-icon-share"
          @click="shareResults"
        >
          分享结果
        </el-button>
        <el-button 
          type="warning" 
          icon="el-icon-copy-document"
          @click="copyBacktest"
        >
          复制回测
        </el-button>
      </div>
    </div>

    <!-- 核心指标概览 -->
    <div class="metrics-overview">
      <el-row :gutter="20">
        <el-col :span="6">
          <div class="metric-card primary">
            <div class="metric-icon">
              <el-icon><TrendCharts /></el-icon>
            </div>
            <div class="metric-content">
              <div class="metric-value" :class="getReturnClass(backtest.total_return)">
                {{ formatPercent(backtest.total_return) }}
              </div>
              <div class="metric-label">总收益率</div>
              <div class="metric-sub">
                年化: {{ formatPercent(backtest.annual_return) }}
              </div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="metric-card success">
            <div class="metric-icon">
              <el-icon><DataAnalysis /></el-icon>
            </div>
            <div class="metric-content">
              <div class="metric-value">{{ formatNumber(backtest.sharpe_ratio, 2) }}</div>
              <div class="metric-label">夏普比率</div>
              <div class="metric-sub">
                索提诺: {{ formatNumber(backtest.sortino_ratio, 2) }}
              </div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="metric-card warning">
            <div class="metric-icon">
              <el-icon><Warning /></el-icon>
            </div>
            <div class="metric-content">
              <div class="metric-value danger">{{ formatPercent(backtest.max_drawdown) }}</div>
              <div class="metric-label">最大回撤</div>
              <div class="metric-sub">
                波动率: {{ formatPercent(backtest.volatility) }}
              </div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="metric-card info">
            <div class="metric-icon">
              <el-icon><DataBoard /></el-icon>
            </div>
            <div class="metric-content">
              <div class="metric-value">{{ formatPercent(backtest.win_rate) }}</div>
              <div class="metric-label">胜率</div>
              <div class="metric-sub">
                交易次数: {{ backtest.total_trades }}
              </div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 图表展示区域 -->
    <div class="charts-section">
      <el-tabs v-model="activeChartTab" class="charts-tabs">
        <!-- 净值曲线 -->
        <el-tab-pane label="净值曲线" name="equity">
          <div class="chart-container">
            <div class="chart-header">
              <h4>净值曲线</h4>
              <div class="chart-controls">
                <el-radio-group v-model="equityChartType" size="small">
                  <el-radio-button label="absolute">绝对净值</el-radio-button>
                  <el-radio-button label="relative">相对收益</el-radio-button>
                  <el-radio-button label="comparison">基准对比</el-radio-button>
                </el-radio-group>
              </div>
            </div>
            <div ref="equityChart" class="chart" style="height: 400px;"></div>
          </div>
        </el-tab-pane>

        <!-- 回撤分析 -->
        <el-tab-pane label="回撤分析" name="drawdown">
          <div class="chart-container">
            <div class="chart-header">
              <h4>回撤分析</h4>
              <div class="chart-stats">
                <span class="stat-item">
                  最大回撤: <strong class="danger">{{ formatPercent(backtest.max_drawdown) }}</strong>
                </span>
                <span class="stat-item">
                  回撤次数: <strong>{{ drawdownStats.periods }}</strong>
                </span>
                <span class="stat-item">
                  平均回撤: <strong>{{ formatPercent(drawdownStats.average) }}</strong>
                </span>
              </div>
            </div>
            <div ref="drawdownChart" class="chart" style="height: 400px;"></div>
          </div>
        </el-tab-pane>

        <!-- 收益分析 -->
        <el-tab-pane label="收益分析" name="returns">
          <el-row :gutter="20">
            <el-col :span="12">
              <div class="chart-container">
                <div class="chart-header">
                  <h4>日收益率分布</h4>
                </div>
                <div ref="returnsDistChart" class="chart" style="height: 300px;"></div>
              </div>
            </el-col>
            <el-col :span="12">
              <div class="chart-container">
                <div class="chart-header">
                  <h4>月度收益热力图</h4>
                </div>
                <div ref="monthlyHeatmap" class="chart" style="height: 300px;"></div>
              </div>
            </el-col>
          </el-row>
        </el-tab-pane>

        <!-- 交易分析 -->
        <el-tab-pane label="交易分析" name="trades">
          <el-row :gutter="20">
            <el-col :span="12">
              <div class="chart-container">
                <div class="chart-header">
                  <h4>交易盈亏分布</h4>
                </div>
                <div ref="tradePnlChart" class="chart" style="height: 300px;"></div>
              </div>
            </el-col>
            <el-col :span="12">
              <div class="chart-container">
                <div class="chart-header">
                  <h4>持仓时间分析</h4>
                </div>
                <div ref="holdingTimeChart" class="chart" style="height: 300px;"></div>
              </div>
            </el-col>
          </el-row>
        </el-tab-pane>

        <!-- 风险分析 -->
        <el-tab-pane label="风险分析" name="risk">
          <el-row :gutter="20">
            <el-col :span="8">
              <div class="risk-metrics">
                <h4>风险指标</h4>
                <div class="risk-item">
                  <span class="risk-label">波动率</span>
                  <span class="risk-value">{{ formatPercent(backtest.volatility) }}</span>
                </div>
                <div class="risk-item">
                  <span class="risk-label">VaR (95%)</span>
                  <span class="risk-value">{{ formatPercent(riskMetrics.var_95) }}</span>
                </div>
                <div class="risk-item">
                  <span class="risk-label">CVaR (95%)</span>
                  <span class="risk-value">{{ formatPercent(riskMetrics.cvar_95) }}</span>
                </div>
                <div class="risk-item">
                  <span class="risk-label">偏度</span>
                  <span class="risk-value">{{ formatNumber(riskMetrics.skewness, 3) }}</span>
                </div>
                <div class="risk-item">
                  <span class="risk-label">峰度</span>
                  <span class="risk-value">{{ formatNumber(riskMetrics.kurtosis, 3) }}</span>
                </div>
              </div>
            </el-col>
            <el-col :span="16">
              <div class="chart-container">
                <div class="chart-header">
                  <h4>风险收益散点图</h4>
                </div>
                <div ref="riskReturnChart" class="chart" style="height: 300px;"></div>
              </div>
            </el-col>
          </el-row>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 详细数据表格 -->
    <div class="data-tables">
      <el-tabs v-model="activeDataTab" class="data-tabs">
        <!-- 交易记录 -->
        <el-tab-pane label="交易记录" name="trades">
          <div class="table-container">
            <div class="table-header">
              <h4>交易明细</h4>
              <div class="table-controls">
                <el-input
                  v-model="tradeSearch"
                  placeholder="搜索交易记录"
                  prefix-icon="el-icon-search"
                  size="small"
                  style="width: 200px; margin-right: 10px;"
                />
                <el-select
                  v-model="tradeFilter"
                  placeholder="筛选类型"
                  size="small"
                  style="width: 120px;"
                >
                  <el-option label="全部" value="all" />
                  <el-option label="买入" value="buy" />
                  <el-option label="卖出" value="sell" />
                  <el-option label="盈利" value="profit" />
                  <el-option label="亏损" value="loss" />
                </el-select>
              </div>
            </div>
            <el-table
              :data="filteredTrades"
              style="width: 100%"
              :default-sort="{ prop: 'timestamp', order: 'descending' }"
              max-height="400"
            >
              <el-table-column prop="timestamp" label="时间" width="180" sortable>
                <template #default="scope">
                  {{ formatDateTime(scope.row.timestamp) }}
                </template>
              </el-table-column>
              <el-table-column prop="symbol" label="标的" width="100" />
              <el-table-column prop="side" label="方向" width="80">
                <template #default="scope">
                  <el-tag :type="scope.row.side === 'buy' ? 'success' : 'danger'" size="small">
                    {{ scope.row.side === 'buy' ? '买入' : '卖出' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="quantity" label="数量" width="100" align="right">
                <template #default="scope">
                  {{ formatNumber(scope.row.quantity, 0) }}
                </template>
              </el-table-column>
              <el-table-column prop="price" label="价格" width="100" align="right">
                <template #default="scope">
                  {{ formatNumber(scope.row.price, 2) }}
                </template>
              </el-table-column>
              <el-table-column prop="commission" label="手续费" width="100" align="right">
                <template #default="scope">
                  {{ formatNumber(scope.row.commission, 2) }}
                </template>
              </el-table-column>
              <el-table-column prop="pnl" label="盈亏" width="120" align="right">
                <template #default="scope">
                  <span :class="getPnlClass(scope.row.pnl)">
                    {{ formatNumber(scope.row.pnl, 2) }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="position_after" label="持仓" width="100" align="right">
                <template #default="scope">
                  {{ formatNumber(scope.row.position_after, 0) }}
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>

        <!-- 持仓记录 -->
        <el-tab-pane label="持仓记录" name="positions">
          <div class="table-container">
            <div class="table-header">
              <h4>持仓变化</h4>
            </div>
            <el-table
              :data="backtest.positions || []"
              style="width: 100%"
              max-height="400"
            >
              <el-table-column prop="symbol" label="标的" width="100" />
              <el-table-column prop="quantity" label="持仓数量" width="120" align="right">
                <template #default="scope">
                  {{ formatNumber(scope.row.quantity, 0) }}
                </template>
              </el-table-column>
              <el-table-column prop="avg_price" label="平均成本" width="120" align="right">
                <template #default="scope">
                  {{ formatNumber(scope.row.avg_price, 2) }}
                </template>
              </el-table-column>
              <el-table-column prop="current_price" label="当前价格" width="120" align="right">
                <template #default="scope">
                  {{ formatNumber(scope.row.current_price, 2) }}
                </template>
              </el-table-column>
              <el-table-column prop="unrealized_pnl" label="浮动盈亏" width="120" align="right">
                <template #default="scope">
                  <span :class="getPnlClass(scope.row.unrealized_pnl)">
                    {{ formatNumber(scope.row.unrealized_pnl, 2) }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="realized_pnl" label="已实现盈亏" width="120" align="right">
                <template #default="scope">
                  <span :class="getPnlClass(scope.row.realized_pnl)">
                    {{ formatNumber(scope.row.realized_pnl, 2) }}
                  </span>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>

        <!-- 日收益率 -->
        <el-tab-pane label="日收益率" name="daily-returns">
          <div class="table-container">
            <div class="table-header">
              <h4>日收益率明细</h4>
            </div>
            <el-table
              :data="backtest.daily_returns || []"
              style="width: 100%"
              :default-sort="{ prop: 'date', order: 'descending' }"
              max-height="400"
            >
              <el-table-column prop="date" label="日期" width="120" sortable />
              <el-table-column prop="return" label="日收益率" width="120" align="right" sortable>
                <template #default="scope">
                  <span :class="getReturnClass(scope.row.return)">
                    {{ formatPercent(scope.row.return) }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="cumulative_return" label="累计收益率" width="140" align="right">
                <template #default="scope">
                  <span :class="getReturnClass(scope.row.cumulative_return)">
                    {{ formatPercent(scope.row.cumulative_return) }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="benchmark_return" label="基准收益率" width="140" align="right">
                <template #default="scope">
                  <span :class="getReturnClass(scope.row.benchmark_return)">
                    {{ formatPercent(scope.row.benchmark_return) }}
                  </span>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 导出对话框 -->
    <el-dialog
      v-model="showExportDialog"
      title="导出报告"
      width="500px"
    >
      <el-form :model="exportForm" label-width="100px">
        <el-form-item label="导出格式">
          <el-radio-group v-model="exportForm.format">
            <el-radio label="json">JSON</el-radio>
            <el-radio label="csv">CSV</el-radio>
            <el-radio label="excel">Excel</el-radio>
            <el-radio label="pdf">PDF</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="包含内容">
          <el-checkbox-group v-model="exportForm.includes">
            <el-checkbox label="metrics">性能指标</el-checkbox>
            <el-checkbox label="charts">图表数据</el-checkbox>
            <el-checkbox label="trades">交易记录</el-checkbox>
            <el-checkbox label="positions">持仓记录</el-checkbox>
            <el-checkbox label="analysis">分析报告</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="文件名">
          <el-input v-model="exportForm.filename" placeholder="自动生成" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showExportDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmExport" :loading="exporting">
          导出
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Calendar, Money, TrendCharts, DataAnalysis, Warning, DataBoard 
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { backtestApi } from '@/api/backtest'

export default {
  name: 'BacktestResults',
  components: {
    Calendar,
    Money,
    TrendCharts,
    DataAnalysis,
    Warning,
    DataBoard
  },
  props: {
    backtest: {
      type: Object,
      required: true
    }
  },
  setup(props) {
    const activeChartTab = ref('equity')
    const activeDataTab = ref('trades')
    const equityChartType = ref('absolute')
    const tradeSearch = ref('')
    const tradeFilter = ref('all')
    const showExportDialog = ref(false)
    const exporting = ref(false)

    // 图表引用
    const equityChart = ref(null)
    const drawdownChart = ref(null)
    const returnsDistChart = ref(null)
    const monthlyHeatmap = ref(null)
    const tradePnlChart = ref(null)
    const holdingTimeChart = ref(null)
    const riskReturnChart = ref(null)

    // 图表实例
    let equityChartInstance = null
    let drawdownChartInstance = null
    let returnsDistChartInstance = null
    let monthlyHeatmapInstance = null
    let tradePnlChartInstance = null
    let holdingTimeChartInstance = null
    let riskReturnChartInstance = null

    // 导出表单
    const exportForm = reactive({
      format: 'json',
      includes: ['metrics', 'charts', 'trades'],
      filename: ''
    })

    // 模拟数据
    const drawdownStats = reactive({
      periods: 12,
      average: -0.05,
      duration: 15
    })

    const riskMetrics = reactive({
      var_95: -0.025,
      cvar_95: -0.035,
      skewness: -0.15,
      kurtosis: 2.8
    })

    // 过滤后的交易记录
    const filteredTrades = computed(() => {
      let trades = props.backtest.trades_detail || []
      
      // 搜索过滤
      if (tradeSearch.value) {
        const keyword = tradeSearch.value.toLowerCase()
        trades = trades.filter(trade => 
          trade.symbol?.toLowerCase().includes(keyword) ||
          trade.side?.toLowerCase().includes(keyword)
        )
      }
      
      // 类型过滤
      if (tradeFilter.value !== 'all') {
        if (tradeFilter.value === 'buy' || tradeFilter.value === 'sell') {
          trades = trades.filter(trade => trade.side === tradeFilter.value)
        } else if (tradeFilter.value === 'profit') {
          trades = trades.filter(trade => trade.pnl > 0)
        } else if (tradeFilter.value === 'loss') {
          trades = trades.filter(trade => trade.pnl < 0)
        }
      }
      
      return trades
    })

    // 初始化图表
    const initCharts = async () => {
      await nextTick()
      
      // 净值曲线图
      if (equityChart.value) {
        equityChartInstance = echarts.init(equityChart.value)
        updateEquityChart()
      }
      
      // 回撤图
      if (drawdownChart.value) {
        drawdownChartInstance = echarts.init(drawdownChart.value)
        updateDrawdownChart()
      }
      
      // 收益率分布图
      if (returnsDistChart.value) {
        returnsDistChartInstance = echarts.init(returnsDistChart.value)
        updateReturnsDistChart()
      }
      
      // 月度热力图
      if (monthlyHeatmap.value) {
        monthlyHeatmapInstance = echarts.init(monthlyHeatmap.value)
        updateMonthlyHeatmap()
      }
      
      // 交易盈亏图
      if (tradePnlChart.value) {
        tradePnlChartInstance = echarts.init(tradePnlChart.value)
        updateTradePnlChart()
      }
      
      // 持仓时间图
      if (holdingTimeChart.value) {
        holdingTimeChartInstance = echarts.init(holdingTimeChart.value)
        updateHoldingTimeChart()
      }
      
      // 风险收益散点图
      if (riskReturnChart.value) {
        riskReturnChartInstance = echarts.init(riskReturnChart.value)
        updateRiskReturnChart()
      }
    }

    // 更新净值曲线图
    const updateEquityChart = () => {
      if (!equityChartInstance || !props.backtest.equity_curve) return
      
      const data = props.backtest.equity_curve.map(point => [
        point.date,
        point.equity
      ])
      
      const option = {
        title: {
          text: '净值曲线',
          left: 'center'
        },
        tooltip: {
          trigger: 'axis',
          formatter: function(params) {
            const point = params[0]
            return `${point.axisValue}<br/>净值: ${formatCurrency(point.value[1])}`
          }
        },
        xAxis: {
          type: 'time'
        },
        yAxis: {
          type: 'value',
          axisLabel: {
            formatter: value => formatCurrency(value)
          }
        },
        series: [{
          name: '净值',
          type: 'line',
          data: data,
          smooth: true,
          lineStyle: {
            color: '#409EFF',
            width: 2
          },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [{
                offset: 0,
                color: 'rgba(64, 158, 255, 0.3)'
              }, {
                offset: 1,
                color: 'rgba(64, 158, 255, 0.1)'
              }]
            }
          }
        }]
      }
      
      equityChartInstance.setOption(option)
    }

    // 更新回撤图
    const updateDrawdownChart = () => {
      if (!drawdownChartInstance || !props.backtest.drawdown_curve) return
      
      const data = props.backtest.drawdown_curve.map(point => [
        point.date,
        point.drawdown * 100
      ])
      
      const option = {
        title: {
          text: '回撤曲线',
          left: 'center'
        },
        tooltip: {
          trigger: 'axis',
          formatter: function(params) {
            const point = params[0]
            return `${point.axisValue}<br/>回撤: ${point.value[1].toFixed(2)}%`
          }
        },
        xAxis: {
          type: 'time'
        },
        yAxis: {
          type: 'value',
          axisLabel: {
            formatter: value => `${value.toFixed(1)}%`
          }
        },
        series: [{
          name: '回撤',
          type: 'line',
          data: data,
          smooth: true,
          lineStyle: {
            color: '#F56C6C',
            width: 2
          },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [{
                offset: 0,
                color: 'rgba(245, 108, 108, 0.3)'
              }, {
                offset: 1,
                color: 'rgba(245, 108, 108, 0.1)'
              }]
            }
          }
        }]
      }
      
      drawdownChartInstance.setOption(option)
    }

    // 更新收益率分布图
    const updateReturnsDistChart = () => {
      if (!returnsDistChartInstance || !props.backtest.daily_returns) return
      
      const returns = props.backtest.daily_returns.map(point => point.return * 100)
      
      const option = {
        title: {
          text: '日收益率分布',
          left: 'center'
        },
        tooltip: {
          trigger: 'axis'
        },
        xAxis: {
          type: 'value',
          axisLabel: {
            formatter: value => `${value.toFixed(1)}%`
          }
        },
        yAxis: {
          type: 'value'
        },
        series: [{
          name: '频次',
          type: 'bar',
          data: generateHistogramData(returns),
          itemStyle: {
            color: '#67C23A'
          }
        }]
      }
      
      returnsDistChartInstance.setOption(option)
    }

    // 更新月度热力图
    const updateMonthlyHeatmap = () => {
      if (!monthlyHeatmapInstance) return
      
      // 生成模拟的月度收益数据
      const monthlyData = generateMonthlyData()
      
      const option = {
        title: {
          text: '月度收益热力图',
          left: 'center'
        },
        tooltip: {
          position: 'top',
          formatter: function(params) {
            return `${params.value[0]}年${params.value[1]}月<br/>收益率: ${params.value[2].toFixed(2)}%`
          }
        },
        grid: {
          height: '50%',
          top: '10%'
        },
        xAxis: {
          type: 'category',
          data: ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'],
          splitArea: {
            show: true
          }
        },
        yAxis: {
          type: 'category',
          data: ['2023', '2024'],
          splitArea: {
            show: true
          }
        },
        visualMap: {
          min: -10,
          max: 10,
          calculable: true,
          orient: 'horizontal',
          left: 'center',
          bottom: '15%',
          inRange: {
            color: ['#FF6B6B', '#FFFFFF', '#4ECDC4']
          }
        },
        series: [{
          name: '月度收益',
          type: 'heatmap',
          data: monthlyData,
          label: {
            show: true,
            formatter: function(params) {
              return `${params.value[2].toFixed(1)}%`
            }
          },
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          }
        }]
      }
      
      monthlyHeatmapInstance.setOption(option)
    }

    // 更新交易盈亏图
    const updateTradePnlChart = () => {
      if (!tradePnlChartInstance || !props.backtest.trades_detail) return
      
      const trades = props.backtest.trades_detail
      const data = trades.map((trade, index) => ({
        name: `交易${index + 1}`,
        value: trade.pnl,
        itemStyle: {
          color: trade.pnl >= 0 ? '#67C23A' : '#F56C6C'
        }
      }))
      
      const option = {
        title: {
          text: '交易盈亏分布',
          left: 'center'
        },
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'shadow'
          }
        },
        xAxis: {
          type: 'category',
          data: data.map(item => item.name)
        },
        yAxis: {
          type: 'value',
          axisLabel: {
            formatter: value => formatNumber(value, 0)
          }
        },
        series: [{
          name: '盈亏',
          type: 'bar',
          data: data
        }]
      }
      
      tradePnlChartInstance.setOption(option)
    }

    // 更新持仓时间图
    const updateHoldingTimeChart = () => {
      if (!holdingTimeChartInstance) return
      
      // 生成模拟的持仓时间数据
      const data = [
        { name: '1-3天', value: 25 },
        { name: '4-7天', value: 35 },
        { name: '1-2周', value: 20 },
        { name: '2-4周', value: 15 },
        { name: '1个月以上', value: 5 }
      ]
      
      const option = {
        title: {
          text: '持仓时间分布',
          left: 'center'
        },
        tooltip: {
          trigger: 'item',
          formatter: '{a} <br/>{b}: {c}%'
        },
        series: [{
          name: '持仓时间',
          type: 'pie',
          radius: '50%',
          data: data,
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          }
        }]
      }
      
      holdingTimeChartInstance.setOption(option)
    }

    // 更新风险收益散点图
    const updateRiskReturnChart = () => {
      if (!riskReturnChartInstance) return
      
      // 生成模拟的风险收益数据
      const data = [
        [props.backtest.volatility * 100, props.backtest.annual_return * 100, '当前策略']
      ]
      
      const option = {
        title: {
          text: '风险收益分析',
          left: 'center'
        },
        tooltip: {
          trigger: 'item',
          formatter: function(params) {
            return `${params.value[2]}<br/>风险: ${params.value[0].toFixed(2)}%<br/>收益: ${params.value[1].toFixed(2)}%`
          }
        },
        xAxis: {
          type: 'value',
          name: '年化波动率 (%)',
          axisLabel: {
            formatter: value => `${value.toFixed(1)}%`
          }
        },
        yAxis: {
          type: 'value',
          name: '年化收益率 (%)',
          axisLabel: {
            formatter: value => `${value.toFixed(1)}%`
          }
        },
        series: [{
          name: '策略',
          type: 'scatter',
          data: data,
          symbolSize: 20,
          itemStyle: {
            color: '#409EFF'
          }
        }]
      }
      
      riskReturnChartInstance.setOption(option)
    }

    // 导出报告
    const exportReport = () => {
      exportForm.filename = `${props.backtest.name}_回测报告_${new Date().toISOString().split('T')[0]}`
      showExportDialog.value = true
    }

    // 确认导出
    const confirmExport = async () => {
      exporting.value = true
      try {
        const response = await backtestApi.exportReport(props.backtest.id, {
          format: exportForm.format,
          includes: exportForm.includes,
          filename: exportForm.filename
        })
        
        // 下载文件
        const blob = new Blob([response.data])
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = `${exportForm.filename}.${exportForm.format}`
        link.click()
        window.URL.revokeObjectURL(url)
        
        showExportDialog.value = false
        ElMessage.success('报告导出成功')
      } catch (error) {
        ElMessage.error('导出失败: ' + error.message)
      } finally {
        exporting.value = false
      }
    }

    // 分享结果
    const shareResults = () => {
      const url = `${window.location.origin}/backtest/${props.backtest.uuid}`
      navigator.clipboard.writeText(url).then(() => {
        ElMessage.success('分享链接已复制到剪贴板')
      }).catch(() => {
        ElMessage.error('复制失败，请手动复制链接')
      })
    }

    // 复制回测
    const copyBacktest = () => {
      ElMessageBox.confirm('确定要复制此回测配置吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info'
      }).then(() => {
        // 实现复制逻辑
        ElMessage.success('回测配置已复制')
      })
    }

    // 工具函数
    const getStatusType = (status) => {
      const typeMap = {
        'pending': 'info',
        'running': 'warning',
        'completed': 'success',
        'failed': 'danger',
        'cancelled': 'info',
        'paused': 'warning'
      }
      return typeMap[status] || 'info'
    }

    const getStatusText = (status) => {
      const textMap = {
        'pending': '等待中',
        'running': '运行中',
        'completed': '已完成',
        'failed': '失败',
        'cancelled': '已取消',
        'paused': '已暂停'
      }
      return textMap[status] || status
    }

    const getReturnClass = (value) => {
      if (value > 0) return 'positive'
      if (value < 0) return 'negative'
      return 'neutral'
    }

    const getPnlClass = (value) => {
      if (value > 0) return 'profit'
      if (value < 0) return 'loss'
      return 'neutral'
    }

    const formatCurrency = (value) => {
      if (!value) return '¥0'
      return new Intl.NumberFormat('zh-CN', {
        style: 'currency',
        currency: 'CNY',
        minimumFractionDigits: 0
      }).format(value)
    }

    const formatPercent = (value) => {
      if (value === null || value === undefined) return '-'
      return (value * 100).toFixed(2) + '%'
    }

    const formatNumber = (value, decimals = 2) => {
      if (value === null || value === undefined) return '-'
      return Number(value).toFixed(decimals)
    }

    const formatDateTime = (dateStr) => {
      if (!dateStr) return '-'
      return new Date(dateStr).toLocaleString('zh-CN')
    }

    const formatDateRange = (startDate, endDate) => {
      return `${startDate} 至 ${endDate}`
    }

    // 生成直方图数据
    const generateHistogramData = (data) => {
      const bins = 20
      const min = Math.min(...data)
      const max = Math.max(...data)
      const binWidth = (max - min) / bins
      
      const histogram = new Array(bins).fill(0)
      const binCenters = []
      
      for (let i = 0; i < bins; i++) {
        binCenters.push(min + (i + 0.5) * binWidth)
      }
      
      data.forEach(value => {
        const binIndex = Math.min(Math.floor((value - min) / binWidth), bins - 1)
        histogram[binIndex]++
      })
      
      return binCenters.map((center, index) => [center, histogram[index]])
    }

    // 生成月度数据
    const generateMonthlyData = () => {
      const data = []
      const years = ['2023', '2024']
      const months = Array.from({ length: 12 }, (_, i) => i)
      
      years.forEach((year, yearIndex) => {
        months.forEach(month => {
          const value = (Math.random() - 0.5) * 20 // -10% 到 10%
          data.push([yearIndex, month, value])
        })
      })
      
      return data
    }

    onMounted(() => {
      initCharts()
      
      // 监听窗口大小变化
      window.addEventListener('resize', () => {
        if (equityChartInstance) equityChartInstance.resize()
        if (drawdownChartInstance) drawdownChartInstance.resize()
        if (returnsDistChartInstance) returnsDistChartInstance.resize()
        if (monthlyHeatmapInstance) monthlyHeatmapInstance.resize()
        if (tradePnlChartInstance) tradePnlChartInstance.resize()
        if (holdingTimeChartInstance) holdingTimeChartInstance.resize()
        if (riskReturnChartInstance) riskReturnChartInstance.resize()
      })
    })

    return {
      activeChartTab,
      activeDataTab,
      equityChartType,
      tradeSearch,
      tradeFilter,
      showExportDialog,
      exporting,
      exportForm,
      drawdownStats,
      riskMetrics,
      filteredTrades,
      equityChart,
      drawdownChart,
      returnsDistChart,
      monthlyHeatmap,
      tradePnlChart,
      holdingTimeChart,
      riskReturnChart,
      exportReport,
      confirmExport,
      shareResults,
      copyBacktest,
      getStatusType,
      getStatusText,
      getReturnClass,
      getPnlClass,
      formatCurrency,
      formatPercent,
      formatNumber,
      formatDateTime,
      formatDateRange
    }
  }
}
</script>

<style scoped>
.backtest-results {
  padding: 20px;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 1px solid #ebeef5;
}

.header-info h3 {
  margin: 0 0 10px 0;
  color: #303133;
  font-size: 24px;
}

.header-meta {
  display: flex;
  gap: 20px;
  align-items: center;
  flex-wrap: wrap;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 5px;
  color: #606266;
  font-size: 14px;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.metrics-overview {
  margin-bottom: 30px;
}

.metric-card {
  display: flex;
  align-items: center;
  padding: 20px;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s;
}

.metric-card:hover {
  transform: translateY(-2px);
}

.metric-card.primary {
  border-left: 4px solid #409eff;
}

.metric-card.success {
  border-left: 4px solid #67c23a;
}

.metric-card.warning {
  border-left: 4px solid #e6a23c;
}

.metric-card.info {
  border-left: 4px solid #909399;
}

.metric-icon {
  font-size: 32px;
  margin-right: 15px;
  opacity: 0.8;
}

.metric-content {
  flex: 1;
}

.metric-value {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 5px;
}

.metric-value.positive {
  color: #67c23a;
}

.metric-value.negative {
  color: #f56c6c;
}

.metric-value.danger {
  color: #f56c6c;
}

.metric-label {
  color: #909399;
  font-size: 14px;
  margin-bottom: 3px;
}

.metric-sub {
  color: #606266;
  font-size: 12px;
}

.charts-section {
  margin-bottom: 30px;
}

.chart-container {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.chart-header h4 {
  margin: 0;
  color: #303133;
}

.chart-controls {
  display: flex;
  gap: 10px;
  align-items: center;
}

.chart-stats {
  display: flex;
  gap: 20px;
  align-items: center;
}

.stat-item {
  font-size: 14px;
  color: #606266;
}

.stat-item strong {
  color: #303133;
}

.stat-item strong.danger {
  color: #f56c6c;
}

.chart {
  width: 100%;
}

.risk-metrics {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.risk-metrics h4 {
  margin: 0 0 20px 0;
  color: #303133;
}

.risk-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #f0f0f0;
}

.risk-item:last-child {
  border-bottom: none;
}

.risk-label {
  color: #606266;
}

.risk-value {
  font-weight: 500;
  color: #303133;
}

.data-tables {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.table-container {
  margin-top: 20px;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.table-header h4 {
  margin: 0;
  color: #303133;
}

.table-controls {
  display: flex;
  gap: 10px;
  align-items: center;
}

.profit {
  color: #67c23a;
  font-weight: 500;
}

.loss {
  color: #f56c6c;
  font-weight: 500;
}

.neutral {
  color: #909399;
}

.positive {
  color: #67c23a;
  font-weight: 500;
}

.negative {
  color: #f56c6c;
  font-weight: 500;
}

:deep(.el-tabs__header) {
  margin-bottom: 20px;
}

:deep(.el-tabs__nav-wrap::after) {
  height: 1px;
}

:deep(.el-table) {
  font-size: 14px;
}

:deep(.el-table th) {
  background-color: #fafafa;
}
</style>