<template>
  <div class="account-overview">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1>账户概览</h1>
      <div class="header-actions">
        <el-button type="primary" @click="refreshData">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button @click="showAccountSettings = true">
          <el-icon><Setting /></el-icon>
          账户设置
        </el-button>
      </div>
    </div>

    <!-- 账户选择 -->
    <div class="account-selector" v-if="accounts.length > 1">
      <el-select v-model="selectedAccountId" @change="onAccountChange" placeholder="选择账户">
        <el-option
          v-for="account in accounts"
          :key="account.id"
          :label="`${account.account_name} (${account.account_number})`"
          :value="account.id"
        />
      </el-select>
    </div>

    <!-- 资金状况卡片 -->
    <div class="overview-cards">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="overview-card">
            <div class="card-header">
              <span class="card-title">总资产</span>
              <el-icon class="card-icon"><Money /></el-icon>
            </div>
            <div class="card-value">
              {{ formatCurrency(currentAccount?.total_assets || 0) }}
            </div>
            <div class="card-change" :class="getChangeClass(totalAssetsChange)">
              {{ formatChange(totalAssetsChange) }}
            </div>
          </el-card>
        </el-col>

        <el-col :span="6">
          <el-card class="overview-card">
            <div class="card-header">
              <span class="card-title">可用资金</span>
              <el-icon class="card-icon"><Wallet /></el-icon>
            </div>
            <div class="card-value">
              {{ formatCurrency(currentAccount?.available_cash || 0) }}
            </div>
            <div class="card-subtitle">
              冻结: {{ formatCurrency(currentAccount?.frozen_cash || 0) }}
            </div>
          </el-card>
        </el-col>

        <el-col :span="6">
          <el-card class="overview-card">
            <div class="card-header">
              <span class="card-title">持仓市值</span>
              <el-icon class="card-icon"><TrendCharts /></el-icon>
            </div>
            <div class="card-value">
              {{ formatCurrency(currentAccount?.market_value || 0) }}
            </div>
            <div class="card-subtitle">
              购买力: {{ formatCurrency(currentAccount?.buying_power || 0) }}
            </div>
          </el-card>
        </el-col>

        <el-col :span="6">
          <el-card class="overview-card">
            <div class="card-header">
              <span class="card-title">总盈亏</span>
              <el-icon class="card-icon"><DataAnalysis /></el-icon>
            </div>
            <div class="card-value" :class="getPnLClass(currentAccount?.total_pnl || 0)">
              {{ formatCurrency(currentAccount?.total_pnl || 0) }}
            </div>
            <div class="card-subtitle">
              已实现: {{ formatCurrency(currentAccount?.realized_pnl || 0) }}
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 账户详细信息 -->
    <el-row :gutter="20" class="detail-section">
      <el-col :span="16">
        <!-- 资产分布图表 -->
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>资产分布</span>
              <el-radio-group v-model="chartPeriod" size="small">
                <el-radio-button label="1d">日</el-radio-button>
                <el-radio-button label="1w">周</el-radio-button>
                <el-radio-button label="1m">月</el-radio-button>
                <el-radio-button label="3m">季</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <div ref="assetChartRef" class="chart-container"></div>
        </el-card>

        <!-- 盈亏趋势图表 -->
        <el-card class="chart-card">
          <template #header>
            <span>盈亏趋势</span>
          </template>
          <div ref="pnlChartRef" class="chart-container"></div>
        </el-card>
      </el-col>

      <el-col :span="8">
        <!-- 账户基本信息 -->
        <el-card class="info-card">
          <template #header>
            <span>账户信息</span>
          </template>
          <div class="account-info">
            <div class="info-item">
              <span class="info-label">账户号:</span>
              <span class="info-value">{{ currentAccount?.account_number }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">账户类型:</span>
              <el-tag :type="getAccountTypeTag(currentAccount?.account_type)">
                {{ getAccountTypeName(currentAccount?.account_type) }}
              </el-tag>
            </div>
            <div class="info-item">
              <span class="info-label">状态:</span>
              <el-tag :type="getStatusTag(currentAccount?.status)">
                {{ getStatusName(currentAccount?.status) }}
              </el-tag>
            </div>
            <div class="info-item">
              <span class="info-label">基础货币:</span>
              <span class="info-value">{{ currentAccount?.base_currency }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">风险等级:</span>
              <el-tag :type="getRiskLevelTag(currentAccount?.risk_level)">
                {{ currentAccount?.risk_level }}
              </el-tag>
            </div>
            <div class="info-item">
              <span class="info-label">创建时间:</span>
              <span class="info-value">{{ formatDate(currentAccount?.created_at) }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">最后活动:</span>
              <span class="info-value">{{ formatDate(currentAccount?.last_activity_at) }}</span>
            </div>
          </div>
        </el-card>

        <!-- 快速操作 -->
        <el-card class="action-card">
          <template #header>
            <span>快速操作</span>
          </template>
          <div class="quick-actions">
            <el-button type="primary" @click="showDepositDialog = true" block>
              <el-icon><Plus /></el-icon>
              入金
            </el-button>
            <el-button @click="showWithdrawDialog = true" block>
              <el-icon><Minus /></el-icon>
              出金
            </el-button>
            <el-button @click="goToTransactions" block>
              <el-icon><List /></el-icon>
              交易流水
            </el-button>
            <el-button @click="downloadStatement" block>
              <el-icon><Download /></el-icon>
              下载对账单
            </el-button>
          </div>
        </el-card>

        <!-- 风险提醒 -->
        <el-card class="risk-card" v-if="riskAlerts.length > 0">
          <template #header>
            <span>风险提醒</span>
          </template>
          <div class="risk-alerts">
            <el-alert
              v-for="alert in riskAlerts"
              :key="alert.id"
              :title="alert.title"
              :description="alert.message"
              :type="alert.type"
              :closable="false"
              show-icon
              class="risk-alert"
            />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 入金对话框 -->
    <DepositDialog
      v-model="showDepositDialog"
      :account-id="selectedAccountId"
      @success="onDepositSuccess"
    />

    <!-- 出金对话框 -->
    <WithdrawDialog
      v-model="showWithdrawDialog"
      :account-id="selectedAccountId"
      @success="onWithdrawSuccess"
    />

    <!-- 账户设置对话框 -->
    <AccountSettingsDialog
      v-model="showAccountSettings"
      :account="currentAccount"
      @success="onSettingsUpdate"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import {
  Refresh,
  Setting,
  Money,
  Wallet,
  TrendCharts,
  DataAnalysis,
  Plus,
  Minus,
  List,
  Download
} from '@element-plus/icons-vue'

import { useAccountStore } from '@/stores/account'
import { formatCurrency, formatDate, formatPercent } from '@/utils/format'
import DepositDialog from './components/DepositDialog.vue'
import WithdrawDialog from './components/WithdrawDialog.vue'
import AccountSettingsDialog from './components/AccountSettingsDialog.vue'

const router = useRouter()
const accountStore = useAccountStore()

// 响应式数据
const loading = ref(false)
const selectedAccountId = ref<number | null>(null)
const chartPeriod = ref('1m')
const showDepositDialog = ref(false)
const showWithdrawDialog = ref(false)
const showAccountSettings = ref(false)

// 图表引用
const assetChartRef = ref<HTMLElement>()
const pnlChartRef = ref<HTMLElement>()
let assetChart: echarts.ECharts | null = null
let pnlChart: echarts.ECharts | null = null

// 计算属性
const accounts = computed(() => accountStore.accounts)
const currentAccount = computed(() => 
  accounts.value.find(acc => acc.id === selectedAccountId.value)
)

const totalAssetsChange = ref(0) // 这里应该从API获取变化数据
const riskAlerts = ref([]) // 风险提醒数据

// 生命周期
onMounted(async () => {
  await loadData()
  await nextTick()
  initCharts()
})

// 监听图表周期变化
watch(chartPeriod, () => {
  updateAssetChart()
})

// 监听账户变化
watch(selectedAccountId, () => {
  updateCharts()
})

// 方法
const loadData = async () => {
  try {
    loading.value = true
    await accountStore.loadAccounts()
    
    if (accounts.value.length > 0 && !selectedAccountId.value) {
      selectedAccountId.value = accounts.value[0].id
    }
    
    if (selectedAccountId.value) {
      await loadAccountDetails()
    }
  } catch (error) {
    ElMessage.error('加载账户数据失败')
  } finally {
    loading.value = false
  }
}

const loadAccountDetails = async () => {
  if (!selectedAccountId.value) return
  
  try {
    // 加载账户详细信息
    await accountStore.fetchAccountDetails(selectedAccountId.value)
    // 加载账户统计数据
    await loadAccountStats()
    // 加载风险提醒
    await loadRiskAlerts()
  } catch (error) {
    console.error('❌ 加载账户详情失败:', error)
  }
}

const loadAccountStats = async () => {
  if (!selectedAccountId.value) return
  
  try {
    // 这里可以调用账户统计API
    // const stats = await accountApi.getAccountStats(selectedAccountId.value.toString())
    // 暂时使用模拟数据
    totalAssetsChange.value = Math.random() * 10000 - 5000
  } catch (error) {
    console.error('❌ 加载账户统计失败:', error)
  }
}

const loadRiskAlerts = async () => {
  if (!selectedAccountId.value) return
  
  try {
    // 这里可以调用风险提醒API
    // 暂时使用模拟数据
    const account = currentAccount.value
    if (account && account.risk_level === 'HIGH') {
      riskAlerts.value = [
        {
          id: 1,
          type: 'warning',
          title: '高风险提醒',
          message: '当前账户风险等级较高，请注意控制仓位'
        }
      ]
    } else {
      riskAlerts.value = []
    }
  } catch (error) {
    console.error('❌ 加载风险提醒失败:', error)
  }
}

const refreshData = async () => {
  await loadData()
  updateCharts()
  ElMessage.success('数据已刷新')
}

const onAccountChange = () => {
  loadAccountDetails()
}

// 格式化方法
const formatChange = (change: number) => {
  const sign = change >= 0 ? '+' : ''
  return `${sign}${formatCurrency(change)} (${sign}${formatPercent(change / 100000)})`
}

const getChangeClass = (change: number) => {
  return change >= 0 ? 'positive' : 'negative'
}

const getPnLClass = (pnl: number) => {
  return pnl >= 0 ? 'positive' : 'negative'
}

const getAccountTypeTag = (type: string) => {
  const tagMap = {
    'CASH': 'success',
    'MARGIN': 'warning',
    'FUTURES': 'danger',
    'OPTIONS': 'info'
  }
  return tagMap[type] || 'info'
}

const getAccountTypeName = (type: string) => {
  const nameMap = {
    'CASH': '现金账户',
    'MARGIN': '保证金账户',
    'FUTURES': '期货账户',
    'OPTIONS': '期权账户'
  }
  return nameMap[type] || type
}

const getStatusTag = (status: string) => {
  const tagMap = {
    'ACTIVE': 'success',
    'INACTIVE': 'info',
    'SUSPENDED': 'warning',
    'CLOSED': 'danger'
  }
  return tagMap[status] || 'info'
}

const getStatusName = (status: string) => {
  const nameMap = {
    'ACTIVE': '活跃',
    'INACTIVE': '非活跃',
    'SUSPENDED': '暂停',
    'CLOSED': '关闭'
  }
  return nameMap[status] || status
}

const getRiskLevelTag = (level: string) => {
  const tagMap = {
    'LOW': 'success',
    'MEDIUM': 'warning',
    'HIGH': 'danger'
  }
  return tagMap[level] || 'info'
}

// 图表初始化
const initCharts = () => {
  if (assetChartRef.value) {
    assetChart = echarts.init(assetChartRef.value)
    updateAssetChart()
  }
  
  if (pnlChartRef.value) {
    pnlChart = echarts.init(pnlChartRef.value)
    updatePnLChart()
  }
}

const updateCharts = () => {
  updateAssetChart()
  updatePnLChart()
}

const updateAssetChart = () => {
  if (!assetChart || !currentAccount.value) return
  
  const option = {
    title: {
      text: '资产分布',
      left: 'center'
    },
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)'
    },
    series: [
      {
        name: '资产分布',
        type: 'pie',
        radius: '50%',
        data: [
          { value: currentAccount.value.available_cash, name: '可用现金' },
          { value: currentAccount.value.frozen_cash, name: '冻结资金' },
          { value: currentAccount.value.market_value, name: '持仓市值' }
        ],
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }
    ]
  }
  
  assetChart.setOption(option)
}

const updatePnLChart = () => {
  if (!pnlChart || !currentAccount.value) return
  
  // 模拟盈亏趋势数据
  const dates = []
  const pnlData = []
  const today = new Date()
  
  for (let i = 29; i >= 0; i--) {
    const date = new Date(today)
    date.setDate(date.getDate() - i)
    dates.push(date.toISOString().split('T')[0])
    pnlData.push(Math.random() * 10000 - 5000) // 模拟数据
  }
  
  const option = {
    title: {
      text: '盈亏趋势',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis'
    },
    xAxis: {
      type: 'category',
      data: dates
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: (value: number) => formatCurrency(value)
      }
    },
    series: [
      {
        name: '盈亏',
        type: 'line',
        data: pnlData,
        smooth: true,
        itemStyle: {
          color: '#409EFF'
        },
        areaStyle: {
          opacity: 0.3
        }
      }
    ]
  }
  
  pnlChart.setOption(option)
}

// 事件处理
const onDepositSuccess = () => {
  ElMessage.success('入金成功')
  refreshData()
}

const onWithdrawSuccess = () => {
  ElMessage.success('出金成功')
  refreshData()
}

const onSettingsUpdate = () => {
  ElMessage.success('设置更新成功')
  refreshData()
}

const goToTransactions = () => {
  router.push(`/account/transactions?accountId=${selectedAccountId.value}`)
}

const downloadStatement = async () => {
  try {
    // 这里调用下载对账单的API
    ElMessage.success('对账单下载成功')
  } catch (error) {
    ElMessage.error('下载对账单失败')
  }
}
</script>

<style scoped>
.account-overview {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.account-selector {
  margin-bottom: 20px;
}

.overview-cards {
  margin-bottom: 20px;
}

.overview-card {
  text-align: center;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.card-title {
  font-size: 14px;
  color: #666;
}

.card-icon {
  font-size: 20px;
  color: #409EFF;
}

.card-value {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 5px;
}

.card-change {
  font-size: 12px;
}

.card-subtitle {
  font-size: 12px;
  color: #999;
}

.positive {
  color: #67C23A;
}

.negative {
  color: #F56C6C;
}

.detail-section {
  margin-top: 20px;
}

.chart-card {
  margin-bottom: 20px;
}

.chart-container {
  height: 300px;
}

.info-card,
.action-card,
.risk-card {
  margin-bottom: 20px;
}

.account-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-label {
  font-weight: 500;
  color: #666;
}

.info-value {
  color: #333;
}

.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.risk-alerts {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.risk-alert {
  margin: 0;
}
</style>