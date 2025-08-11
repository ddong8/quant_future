<template>
  <div class="dashboard-container">
    <div class="page-header">
      <h1 class="page-title">仪表板</h1>
      <p class="page-description">欢迎回来，{{ authStore.user?.full_name || authStore.user?.username || '用户' }}</p>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon wallet">💰</div>
        <div class="stat-content">
          <div class="stat-value">¥{{ formatNumber(dashboardData.accountBalance) }}</div>
          <div class="stat-label">账户余额</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon trend" :class="dashboardData.todayPnl >= 0 ? 'positive' : 'negative'">
          {{ dashboardData.todayPnl >= 0 ? '📈' : '📉' }}
        </div>
        <div class="stat-content">
          <div class="stat-value" :class="dashboardData.todayPnl >= 0 ? 'positive' : 'negative'">
            {{ dashboardData.todayPnl >= 0 ? '+' : '' }}¥{{ formatNumber(dashboardData.todayPnl) }}
          </div>
          <div class="stat-label">今日盈亏</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon orders">📋</div>
        <div class="stat-content">
          <div class="stat-value">{{ dashboardData.activeOrders }}</div>
          <div class="stat-label">活跃订单</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon positions">📊</div>
        <div class="stat-content">
          <div class="stat-value">{{ dashboardData.activePositions }}</div>
          <div class="stat-label">持仓品种</div>
        </div>
      </div>
    </div>

    <!-- 用户信息和系统状态 -->
    <div class="info-grid">
      <div class="info-card">
        <h3>👤 用户信息</h3>
        <div class="info-content">
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
            <span class="value role" :class="authStore.user?.role">{{ getRoleText(authStore.user?.role) }}</span>
          </div>
          <div class="info-item">
            <span class="label">状态:</span>
            <span class="status" :class="authStore.user?.is_active ? 'active' : 'inactive'">
              {{ authStore.user?.is_active ? '✅ 活跃' : '❌ 非活跃' }}
            </span>
          </div>
        </div>
      </div>

      <div class="info-card">
        <h3>🖥️ 系统状态</h3>
        <div class="info-content">
          <div class="info-item">
            <span class="label">市场状态:</span>
            <span class="status" :class="dashboardData.marketStatus === 'open' ? 'active' : 'inactive'">
              {{ dashboardData.marketStatus === 'open' ? '🟢 开市' : '🔴 闭市' }}
            </span>
          </div>
          <div class="info-item">
            <span class="label">连接状态:</span>
            <span class="status active">🟢 正常</span>
          </div>
          <div class="info-item">
            <span class="label">最后更新:</span>
            <span class="value">{{ formatTime(lastUpdateTime) }}</span>
          </div>
          <div class="info-item">
            <span class="label">数据加载:</span>
            <span class="status" :class="dataLoaded ? 'active' : 'inactive'">
              {{ dataLoaded ? '✅ 已完成' : '⏳ 加载中' }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- 操作按钮 -->
    <div class="actions-card">
      <h3>🚀 快速操作</h3>
      <div class="actions">
        <button class="action-btn primary" @click="refreshData">
          🔄 刷新数据
        </button>
        <button class="action-btn" @click="testAPI">
          🧪 测试API
        </button>
        <button class="action-btn" @click="goToOrders">
          📋 查看订单
        </button>
        <button class="action-btn" @click="goToPositions">
          📊 查看持仓
        </button>
      </div>
    </div>
    
    <!-- API测试结果 -->
    <div v-if="apiResult" class="api-result">
      <h3>🧪 API测试结果</h3>
      <pre>{{ apiResult }}</pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

// 响应式数据
const lastUpdateTime = ref(new Date())
const dataLoaded = ref(false)
const apiResult = ref('')

// 仪表板数据
const dashboardData = reactive({
  accountBalance: 0,
  todayPnl: 0,
  activeOrders: 0,
  activePositions: 0,
  marketStatus: 'closed'
})

// 工具函数
const formatNumber = (num: number) => {
  return new Intl.NumberFormat('zh-CN', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2
  }).format(num)
}

const formatTime = (time: Date) => {
  return time.toLocaleString('zh-CN')
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

const testAPI = async () => {
  try {
    console.log('🧪 测试API调用...')
    const { dashboardApi } = await import('@/api/dashboard')
    const response = await dashboardApi.getSummary()
    apiResult.value = JSON.stringify(response, null, 2)
    console.log('✅ API测试成功:', response)
  } catch (error: any) {
    apiResult.value = `❌ API测试失败: ${error.message}`
    console.error('❌ API测试失败:', error)
  }
}

const goToOrders = () => {
  router.push('/orders')
}

const goToPositions = () => {
  router.push('/positions')
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
    dataLoaded.value = true // 即使失败也标记为完成，避免一直显示加载中
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
      dashboardData.accountBalance = data.stats.account_balance || 0
      dashboardData.activeOrders = data.stats.total_orders || 0
      dashboardData.activePositions = data.stats.active_positions || 0
      dashboardData.marketStatus = data.market_status || 'closed'
      
      // 模拟今日盈亏数据（实际项目中应该从API获取）
      dashboardData.todayPnl = Math.random() * 20000 - 10000
      
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
  console.log('🎯 仪表板组件已挂载')
  console.log('认证状态:', authStore.isAuthenticated)
  console.log('用户信息:', authStore.user)
  
  if (authStore.isAuthenticated) {
    await loadDashboardData()
  } else {
    console.warn('⚠️ 用户未认证，无法加载仪表板数据')
  }
})
</script>

<style scoped>
.dashboard-container {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
  background: var(--el-bg-color-page);
  min-height: 100vh;
}

.page-header {
  margin-bottom: 32px;
  text-align: center;
}

.page-title {
  margin: 0 0 8px 0;
  font-size: 32px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  text-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.page-description {
  margin: 0;
  font-size: 18px;
  color: var(--el-text-color-regular);
}

/* 统计卡片网格 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 32px;
}

.stat-card {
  background: var(--el-bg-color);
  border-radius: 12px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  border: 1px solid #e9ecef;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.stat-icon {
  font-size: 32px;
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  flex-shrink: 0;
}

.stat-icon.wallet {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-icon.trend {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-icon.trend.positive {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stat-icon.trend.negative {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
}

.stat-icon.orders {
  background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
}

.stat-icon.positions {
  background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  margin-bottom: 4px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

.stat-value.positive {
  color: #27ae60;
}

.stat-value.negative {
  color: #e74c3c;
}

.stat-label {
  font-size: 14px;
  color: var(--el-text-color-regular);
  font-weight: 500;
}

/* 信息卡片网格 */
.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 20px;
  margin-bottom: 32px;
}

.info-card {
  background: var(--el-bg-color);
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border: 1px solid #e9ecef;
}

.info-card h3 {
  margin: 0 0 20px 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  border-bottom: 2px solid #ecf0f1;
  padding-bottom: 12px;
}

.info-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
}

.info-item .label {
  font-weight: 500;
  color: var(--el-text-color-regular);
  min-width: 80px;
}

.info-item .value {
  color: var(--el-text-color-primary);
  font-weight: 500;
}

.info-item .status {
  font-weight: 600;
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 14px;
}

.status.active {
  color: #27ae60;
  background: #d5f4e6;
}

.status.inactive {
  color: #e74c3c;
  background: #fdeaea;
}

.value.role {
  padding: 4px 12px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
}

.value.role.admin {
  color: #8e44ad;
  background: #f4ecf7;
}

.value.role.trader {
  color: #2980b9;
  background: #ebf3fd;
}

.value.role.viewer {
  color: #f39c12;
  background: #fef9e7;
}

/* 操作卡片 */
.actions-card {
  background: var(--el-bg-color);
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border: 1px solid #e9ecef;
  margin-bottom: 32px;
}

.actions-card h3 {
  margin: 0 0 20px 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  border-bottom: 2px solid #ecf0f1;
  padding-bottom: 12px;
}

.actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.action-btn {
  background: #6c757d;
  color: white;
  border: none;
  padding: 12px 20px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}

.action-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.action-btn.primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.action-btn.primary:hover {
  background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%);
}

/* API结果 */
.api-result {
  background: var(--el-bg-color);
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border: 1px solid #e9ecef;
}

.api-result h3 {
  margin: 0 0 16px 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.api-result pre {
  background: var(--el-bg-color-page);
  border-radius: 8px;
  padding: 16px;
  font-size: 12px;
  line-height: 1.4;
  color: #495057;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid #dee2e6;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .dashboard-container {
    padding: 20px;
  }
  
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
  }
  
  .info-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
}

@media (max-width: 768px) {
  .dashboard-container {
    padding: 16px;
  }
  
  .page-header {
    margin-bottom: 24px;
  }
  
  .page-title {
    font-size: 28px;
  }
  
  .page-description {
    font-size: 16px;
  }
  
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
    margin-bottom: 24px;
  }
  
  .stat-card {
    padding: 16px;
    flex-direction: column;
    text-align: center;
    gap: 12px;
  }
  
  .stat-icon {
    font-size: 28px;
    width: 56px;
    height: 56px;
    margin: 0 auto;
  }
  
  .stat-value {
    font-size: 24px;
  }
  
  .stat-label {
    font-size: 13px;
  }
  
  .info-grid {
    grid-template-columns: 1fr;
    gap: 16px;
    margin-bottom: 24px;
  }
  
  .info-card {
    padding: 20px;
  }
  
  .info-card h3 {
    font-size: 16px;
    margin-bottom: 16px;
  }
  
  .info-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
    padding: 6px 0;
  }
  
  .info-item .label {
    font-size: 13px;
    min-width: auto;
  }
  
  .info-item .value,
  .info-item .status {
    font-size: 14px;
  }
  
  .actions-card {
    padding: 20px;
  }
  
  .actions-card h3 {
    font-size: 16px;
    margin-bottom: 16px;
  }
  
  .actions {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }
  
  .action-btn {
    justify-content: center;
    padding: 14px 16px;
    font-size: 13px;
  }
  
  .api-result {
    padding: 20px;
  }
  
  .api-result h3 {
    font-size: 16px;
  }
  
  .api-result pre {
    font-size: 11px;
    padding: 12px;
    max-height: 300px;
  }
}

@media (max-width: 480px) {
  .dashboard-container {
    padding: 12px;
  }
  
  .page-header {
    margin-bottom: 20px;
  }
  
  .page-title {
    font-size: 24px;
  }
  
  .page-description {
    font-size: 14px;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
    gap: 12px;
    margin-bottom: 20px;
  }
  
  .stat-card {
    padding: 16px;
    flex-direction: row;
    text-align: left;
    gap: 16px;
  }
  
  .stat-icon {
    font-size: 24px;
    width: 48px;
    height: 48px;
    flex-shrink: 0;
  }
  
  .stat-content {
    flex: 1;
  }
  
  .stat-value {
    font-size: 20px;
  }
  
  .stat-label {
    font-size: 12px;
  }
  
  .info-grid {
    gap: 12px;
    margin-bottom: 20px;
  }
  
  .info-card, .actions-card {
    padding: 16px;
  }
  
  .info-card h3, .actions-card h3 {
    font-size: 15px;
    margin-bottom: 12px;
  }
  
  .info-item {
    padding: 4px 0;
  }
  
  .info-item .label {
    font-size: 12px;
  }
  
  .info-item .value,
  .info-item .status {
    font-size: 13px;
  }
  
  .actions {
    grid-template-columns: 1fr;
    gap: 10px;
  }
  
  .action-btn {
    padding: 12px 16px;
    font-size: 13px;
  }
  
  .api-result {
    padding: 16px;
  }
  
  .api-result h3 {
    font-size: 15px;
    margin-bottom: 12px;
  }
  
  .api-result pre {
    font-size: 10px;
    padding: 10px;
    max-height: 250px;
  }
}

@media (max-width: 360px) {
  .dashboard-container {
    padding: 8px;
  }
  
  .page-title {
    font-size: 20px;
  }
  
  .page-description {
    font-size: 13px;
  }
  
  .stat-card {
    padding: 12px;
    gap: 12px;
  }
  
  .stat-icon {
    font-size: 20px;
    width: 40px;
    height: 40px;
  }
  
  .stat-value {
    font-size: 18px;
  }
  
  .stat-label {
    font-size: 11px;
  }
  
  .info-card, .actions-card {
    padding: 12px;
  }
  
  .info-card h3, .actions-card h3 {
    font-size: 14px;
    margin-bottom: 10px;
  }
  
  .action-btn {
    padding: 10px 12px;
    font-size: 12px;
  }
}
</style>