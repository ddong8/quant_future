<template>
  <div class="dashboard-container">
    <div class="page-header">
      <h1 class="page-title">仪表板</h1>
      <p class="page-description">欢迎回来，{{ authStore.user?.full_name || authStore.userName }}</p>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card">
          <div class="stat-icon">
            <el-icon size="24" color="#409EFF">
              <Wallet />
            </el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">¥{{ formatNumber(accountBalance) }}</div>
            <div class="stat-label">账户余额</div>
          </div>
        </div>
      </el-col>

      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card">
          <div class="stat-icon">
            <el-icon size="24" color="#67C23A">
              <TrendCharts />
            </el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value" :class="todayPnl >= 0 ? 'positive' : 'negative'">
              {{ todayPnl >= 0 ? '+' : '' }}¥{{ formatNumber(todayPnl) }}
            </div>
            <div class="stat-label">今日盈亏</div>
          </div>
        </div>
      </el-col>

      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card">
          <div class="stat-icon">
            <el-icon size="24" color="#E6A23C">
              <List />
            </el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ activeOrders }}</div>
            <div class="stat-label">活跃订单</div>
          </div>
        </div>
      </el-col>

      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card">
          <div class="stat-icon">
            <el-icon size="24" color="#F56C6C">
              <PieChart />
            </el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ activePositions }}</div>
            <div class="stat-label">持仓品种</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20" class="charts-row">
      <el-col :xs="24" :lg="16">
        <RealTimeChart
          symbol="ACCOUNT_VALUE"
          title="账户净值曲线"
          chart-type="line"
          :height="300"
          :show-stats="false"
          @data-update="handleAccountValueUpdate"
        />
      </el-col>

      <el-col :xs="24" :lg="8">
        <el-card class="chart-card">
          <template #header>
            <span>持仓分布</span>
          </template>
          
          <div class="chart-container">
            <v-chart 
              :option="positionChartOption" 
              :loading="chartLoading"
              style="height: 300px;"
            />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 实时数据表格 -->
    <el-row :gutter="20" class="tables-row">
      <el-col :xs="24" :lg="12">
        <RealTimeTable
          title="最近订单"
          :columns="orderColumns"
          data-source="orders"
          :height="300"
          @row-click="handleOrderClick"
        >
          <template #actions="{ row }">
            <el-button size="small" type="primary" @click="goToOrders">
              查看全部
            </el-button>
          </template>
        </RealTimeTable>
      </el-col>

      <el-col :xs="24" :lg="12">
        <RealTimeTable
          title="当前持仓"
          :columns="positionColumns"
          data-source="positions"
          :height="300"
          @row-click="handlePositionClick"
        >
          <template #actions="{ row }">
            <el-button size="small" type="primary" @click="goToPositions">
              查看全部
            </el-button>
          </template>
        </RealTimeTable>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, provide } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import VChart, { THEME_KEY } from 'vue-echarts'
import dayjs from 'dayjs'
import {
  Wallet,
  TrendCharts,
  List,
  PieChart as PieChartIcon
} from '@element-plus/icons-vue'
import RealTimeChart from '@/components/RealTimeChart.vue'
import RealTimeTable from '@/components/RealTimeTable.vue'

// 提供主题
provide(THEME_KEY, 'light')

const router = useRouter()
const authStore = useAuthStore()

// 响应式数据
const accountBalance = ref(1000000)
const todayPnl = ref(12500)
const activeOrders = ref(8)
const activePositions = ref(5)
const timeRange = ref('1D')
const chartLoading = ref(false)

// 表格列定义
const orderColumns = [
  { prop: 'symbol', label: '品种', width: 120 },
  { prop: 'side', label: '方向', width: 80, type: 'status' },
  { prop: 'quantity', label: '数量', width: 100, type: 'volume' },
  { prop: 'price', label: '价格', width: 120, type: 'price' },
  { prop: 'status', label: '状态', width: 100, type: 'status' },
  { prop: 'created_at', label: '时间', width: 120, type: 'time' }
]

const positionColumns = [
  { prop: 'symbol', label: '品种', width: 120 },
  { prop: 'side', label: '方向', width: 80, type: 'status' },
  { prop: 'quantity', label: '数量', width: 100, type: 'volume' },
  { prop: 'average_price', label: '均价', width: 120, type: 'price' },
  { prop: 'unrealized_pnl', label: '浮动盈亏', width: 120, type: 'change' }
]

// 图表配置
const netValueChartOption = computed(() => ({
  tooltip: {
    trigger: 'axis',
    formatter: (params: any) => {
      const data = params[0]
      return `${data.name}<br/>净值: ¥${formatNumber(data.value)}`
    }
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    containLabel: true
  },
  xAxis: {
    type: 'category',
    data: generateTimeData()
  },
  yAxis: {
    type: 'value',
    axisLabel: {
      formatter: (value: number) => `¥${formatNumber(value)}`
    }
  },
  series: [
    {
      name: '净值',
      type: 'line',
      smooth: true,
      data: generateNetValueData(),
      itemStyle: {
        color: '#409EFF'
      },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
            { offset: 1, color: 'rgba(64, 158, 255, 0.1)' }
          ]
        }
      }
    }
  ]
}))

const positionChartOption = computed(() => ({
  tooltip: {
    trigger: 'item',
    formatter: '{a} <br/>{b}: {c} ({d}%)'
  },
  legend: {
    orient: 'vertical',
    left: 'left'
  },
  series: [
    {
      name: '持仓分布',
      type: 'pie',
      radius: '50%',
      data: [
        { value: 35, name: '铜' },
        { value: 25, name: '铝' },
        { value: 20, name: '铁矿石' },
        { value: 15, name: '螺纹钢' },
        { value: 5, name: '其他' }
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
}))

// 工具函数
const formatNumber = (num: number) => {
  return new Intl.NumberFormat('zh-CN', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2
  }).format(num)
}

const formatTime = (time: Date) => {
  return dayjs(time).format('MM-DD HH:mm')
}

const getOrderStatusType = (status: string) => {
  const statusMap: Record<string, string> = {
    pending: 'warning',
    filled: 'success',
    cancelled: 'info',
    rejected: 'danger'
  }
  return statusMap[status] || 'info'
}

const getOrderStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    pending: '待成交',
    filled: '已成交',
    cancelled: '已撤销',
    rejected: '已拒绝'
  }
  return statusMap[status] || status
}

const generateTimeData = () => {
  const data = []
  const now = dayjs()
  
  for (let i = 23; i >= 0; i--) {
    data.push(now.subtract(i, 'hour').format('HH:mm'))
  }
  
  return data
}

const generateNetValueData = () => {
  const data = []
  let baseValue = 1000000
  
  for (let i = 0; i < 24; i++) {
    baseValue += (Math.random() - 0.5) * 10000
    data.push(Math.round(baseValue))
  }
  
  return data
}

const changeTimeRange = (range: string) => {
  timeRange.value = range
  // 这里可以重新加载数据
}

const goToOrders = () => {
  router.push('/orders')
}

const goToPositions = () => {
  router.push('/positions')
}

// 处理账户净值更新
const handleAccountValueUpdate = (data: any) => {
  // 更新账户相关数据
  console.log('账户净值更新:', data)
}

// 处理订单点击
const handleOrderClick = (row: any) => {
  console.log('订单点击:', row)
  // 可以跳转到订单详情页面
}

// 处理持仓点击
const handlePositionClick = (row: any) => {
  console.log('持仓点击:', row)
  // 可以跳转到持仓详情页面
}

// 生命周期
onMounted(() => {
  // 加载仪表板数据
  loadDashboardData()
})

const loadDashboardData = async () => {
  try {
    // 加载仪表板摘要数据
    await loadDashboardSummary()
    // 加载用户资料数据
    await loadUserProfile()
  } catch (error) {
    console.error('加载仪表板数据失败:', error)
  }
}

const loadDashboardSummary = async () => {
  try {
    const { dashboardApi } = await import('@/api/dashboard')
    const response = await dashboardApi.getSummary()
    
    if (response.success && response.data) {
      const data = response.data
      // 更新统计数据
      accountBalance.value = data.stats.account_balance
      activeOrders.value = data.stats.total_orders
      activePositions.value = data.stats.active_positions
      
      console.log('仪表板摘要加载成功:', data)
    }
  } catch (error) {
    console.error('加载仪表板摘要失败:', error)
  }
}

const loadUserProfile = async () => {
  try {
    const { dashboardApi } = await import('@/api/dashboard')
    const response = await dashboardApi.getUserProfile()
    
    if (response.success && response.data) {
      const data = response.data
      // 更新用户信息到store
      authStore.updateUser(data)
      
      console.log('用户资料加载成功:', data)
    }
  } catch (error) {
    console.error('加载用户资料失败:', error)
  }
}
</script>

<style lang="scss" scoped>
.dashboard-container {
  padding: 20px;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-light);
  border-radius: var(--el-border-radius-base);
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  height: 80px;
  
  .stat-icon {
    flex-shrink: 0;
  }
  
  .stat-content {
    flex: 1;
    
    .stat-value {
      font-size: 24px;
      font-weight: 600;
      color: var(--el-text-color-primary);
      margin-bottom: 4px;
      
      &.positive {
        color: var(--el-color-success);
      }
      
      &.negative {
        color: var(--el-color-danger);
      }
    }
    
    .stat-label {
      font-size: 14px;
      color: var(--el-text-color-secondary);
    }
  }
}

.charts-row {
  margin-bottom: 20px;
}

.chart-card {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .chart-container {
    width: 100%;
  }
}

.tables-row {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
}

.positive {
  color: var(--el-color-success);
}

.negative {
  color: var(--el-color-danger);
}

// 响应式设计
@media (max-width: 768px) {
  .dashboard-container {
    padding: 16px;
  }
  
  .stats-row {
    .el-col {
      margin-bottom: 16px;
    }
  }
  
  .charts-row,
  .tables-row {
    .el-col {
      margin-bottom: 16px;
    }
  }
}
</style>