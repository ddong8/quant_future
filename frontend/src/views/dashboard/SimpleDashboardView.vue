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

    <!-- 简化的信息卡片 -->
    <el-row :gutter="20" class="info-row">
      <el-col :xs="24" :lg="12">
        <el-card class="info-card">
          <template #header>
            <span>用户信息</span>
          </template>
          
          <div class="user-info">
            <div class="info-item">
              <span class="label">用户名:</span>
              <span class="value">{{ authStore.user?.username || '未知' }}</span>
            </div>
            <div class="info-item">
              <span class="label">全名:</span>
              <span class="value">{{ authStore.user?.full_name || '未设置' }}</span>
            </div>
            <div class="info-item">
              <span class="label">邮箱:</span>
              <span class="value">{{ authStore.user?.email || '未设置' }}</span>
            </div>
            <div class="info-item">
              <span class="label">角色:</span>
              <span class="value">{{ getRoleText(authStore.user?.role) }}</span>
            </div>
            <div class="info-item">
              <span class="label">状态:</span>
              <el-tag :type="authStore.user?.is_active ? 'success' : 'danger'" size="small">
                {{ authStore.user?.is_active ? '活跃' : '非活跃' }}
              </el-tag>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="12">
        <el-card class="info-card">
          <template #header>
            <span>系统状态</span>
          </template>
          
          <div class="system-info">
            <div class="info-item">
              <span class="label">市场状态:</span>
              <el-tag :type="marketStatus === 'open' ? 'success' : 'info'" size="small">
                {{ marketStatus === 'open' ? '开市' : '闭市' }}
              </el-tag>
            </div>
            <div class="info-item">
              <span class="label">连接状态:</span>
              <el-tag type="success" size="small">正常</el-tag>
            </div>
            <div class="info-item">
              <span class="label">最后更新:</span>
              <span class="value">{{ formatTime(lastUpdateTime) }}</span>
            </div>
            <div class="info-item">
              <span class="label">数据加载:</span>
              <el-tag :type="dataLoaded ? 'success' : 'warning'" size="small">
                {{ dataLoaded ? '已完成' : '加载中' }}
              </el-tag>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 操作按钮 -->
    <el-row :gutter="20" class="actions-row">
      <el-col :span="24">
        <el-card class="actions-card">
          <template #header>
            <span>快速操作</span>
          </template>
          
          <div class="actions">
            <el-button type="primary" @click="refreshData">
              <el-icon><Refresh /></el-icon>
              刷新数据
            </el-button>
            <el-button @click="goToOrders">
              <el-icon><List /></el-icon>
              查看订单
            </el-button>
            <el-button @click="goToPositions">
              <el-icon><PieChart /></el-icon>
              查看持仓
            </el-button>
            <el-button @click="goToSettings">
              <el-icon><Setting /></el-icon>
              系统设置
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import dayjs from 'dayjs'
import {
  Wallet,
  TrendCharts,
  List,
  PieChart,
  Refresh,
  Setting
} from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()

// 响应式数据
const accountBalance = ref(0)
const todayPnl = ref(0)
const activeOrders = ref(0)
const activePositions = ref(0)
const marketStatus = ref('closed')
const lastUpdateTime = ref(new Date())
const dataLoaded = ref(false)

// 计算属性
const isAuthenticated = computed(() => authStore.isAuthenticated)

// 工具函数
const formatNumber = (num: number) => {
  return new Intl.NumberFormat('zh-CN', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2
  }).format(num)
}

const formatTime = (time: Date) => {
  return dayjs(time).format('YYYY-MM-DD HH:mm:ss')
}

const getRoleText = (role?: string) => {
  const roleMap: Record<string, string> = {
    admin: '管理员',
    trader: '交易员',
    viewer: '观察者'
  }
  return roleMap[role || ''] || '未知'
}

// 页面操作
const refreshData = async () => {
  console.log('🔄 刷新仪表板数据...')
  await loadDashboardData()
}

const goToOrders = () => {
  router.push('/orders')
}

const goToPositions = () => {
  router.push('/positions')
}

const goToSettings = () => {
  router.push('/settings')
}

// 数据加载
const loadDashboardData = async () => {
  try {
    console.log('📊 开始加载仪表板数据...')
    dataLoaded.value = false
    
    // 加载仪表板摘要数据
    await loadDashboardSummary()
    
    // 加载用户资料数据
    await loadUserProfile()
    
    dataLoaded.value = true
    lastUpdateTime.value = new Date()
    console.log('✅ 仪表板数据加载完成')
  } catch (error) {
    console.error('❌ 加载仪表板数据失败:', error)
  }
}

const loadDashboardSummary = async () => {
  try {
    console.log('📊 开始加载仪表板摘要...')
    const { dashboardApi } = await import('@/api/dashboard')
    const response = await dashboardApi.getSummary()
    
    console.log('📊 仪表板摘要API响应:', response)
    
    if (response.success && response.data) {
      const data = response.data
      // 更新统计数据
      accountBalance.value = data.stats.account_balance || 0
      activeOrders.value = data.stats.total_orders || 0
      activePositions.value = data.stats.active_positions || 0
      marketStatus.value = data.market_status || 'closed'
      
      // 模拟今日盈亏数据
      todayPnl.value = Math.random() * 10000 - 5000
      
      console.log('✅ 仪表板摘要加载成功:', data)
    } else {
      console.warn('⚠️ 仪表板摘要响应格式异常:', response)
    }
  } catch (error) {
    console.error('❌ 加载仪表板摘要失败:', error)
  }
}

const loadUserProfile = async () => {
  try {
    console.log('👤 开始加载用户资料...')
    const { dashboardApi } = await import('@/api/dashboard')
    const response = await dashboardApi.getUserProfile()
    
    console.log('👤 用户资料API响应:', response)
    
    if (response.success && response.data) {
      const data = response.data
      // 更新用户信息到store
      authStore.updateUser(data)
      
      console.log('✅ 用户资料加载成功:', data)
    } else {
      console.warn('⚠️ 用户资料响应格式异常:', response)
    }
  } catch (error) {
    console.error('❌ 加载用户资料失败:', error)
  }
}

// 生命周期
onMounted(async () => {
  console.log('🎯 简化仪表板组件已挂载')
  
  if (isAuthenticated.value) {
    await loadDashboardData()
  } else {
    console.warn('⚠️ 用户未认证，无法加载仪表板数据')
  }
})
</script>

<style lang="scss" scoped>
.dashboard-container {
  padding: 20px;
}

.page-header {
  margin-bottom: 24px;
  
  .page-title {
    margin: 0 0 8px 0;
    font-size: 28px;
    font-weight: 600;
    color: var(--el-text-color-primary);
  }
  
  .page-description {
    margin: 0;
    font-size: 16px;
    color: var(--el-text-color-secondary);
  }
}

.stats-row {
  margin-bottom: 24px;
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
  transition: all 0.3s ease;
  
  &:hover {
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  }
  
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

.info-row {
  margin-bottom: 24px;
}

.info-card {
  .user-info,
  .system-info {
    .info-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px 0;
      border-bottom: 1px solid var(--el-border-color-lighter);
      
      &:last-child {
        border-bottom: none;
      }
      
      .label {
        font-weight: 500;
        color: var(--el-text-color-secondary);
      }
      
      .value {
        color: var(--el-text-color-primary);
      }
    }
  }
}

.actions-row {
  margin-bottom: 24px;
}

.actions-card {
  .actions {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
  }
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
  
  .info-row,
  .actions-row {
    .el-col {
      margin-bottom: 16px;
    }
  }
  
  .actions {
    justify-content: center;
  }
}
</style>