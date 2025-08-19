<template>
  <div class="accounts-container">
    <div class="page-header">
      <h1 class="page-title">账户管理</h1>
      <p class="page-description">管理您的交易账户和资金</p>
      <div class="header-actions">
        <el-button type="primary" @click="refreshData">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button @click="showCreateDialog = true">
          <el-icon><Plus /></el-icon>
          创建账户
        </el-button>
      </div>
    </div>

    <!-- 账户概览卡片 -->
    <div class="overview-cards">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="overview-card">
            <div class="card-header">
              <span class="card-title">总资产</span>
              <el-icon class="card-icon"><Money /></el-icon>
            </div>
            <div class="card-value">
              {{ formatCurrency(accountStore.totalBalance) }}
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
              {{ formatCurrency(accountStore.totalAvailableBalance) }}
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
              {{ formatCurrency(accountStore.totalMarketValue) }}
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="overview-card">
            <div class="card-header">
              <span class="card-title">总盈亏</span>
              <el-icon class="card-icon"><DataAnalysis /></el-icon>
            </div>
            <div class="card-value" :class="getPnLClass(accountStore.totalPnL)">
              {{ formatCurrency(accountStore.totalPnL) }}
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 账户列表 -->
    <el-card class="accounts-list">
      <template #header>
        <div class="card-header">
          <span>账户列表</span>
          <el-tag>{{ accounts.length }} 个账户</el-tag>
        </div>
      </template>
      
      <div v-loading="loading">
        <div v-if="accounts.length === 0" class="empty-state">
          <el-empty description="暂无账户数据" />
        </div>
        <div v-else class="accounts-grid">
          <ErrorBoundary 
            v-for="account in accounts" 
            :key="account.id"
            fallback-message="账户卡片加载失败"
            :show-retry="true"
            @error="onAccountCardError"
            @retry="onAccountCardRetry"
          >
            <div class="account-card">
            <div class="account-header">
              <div class="account-info">
                <h3>{{ account.account_name || account.name || '未命名账户' }}</h3>
                <p>{{ account.account_number || account.account_id || account.id || '-' }}</p>
              </div>
              <el-tag :type="getAccountTypeTag(account.account_type || 'CASH')">
                {{ getAccountTypeName(account.account_type || 'CASH') }}
              </el-tag>
            </div>
            
            <div class="account-stats">
              <div class="stat-item">
                <span class="stat-label">总资产</span>
                <span class="stat-value">{{ formatCurrency(account.total_assets || account.balance || 0) }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">可用资金</span>
                <span class="stat-value">{{ formatCurrency(account.available_cash || account.available || account.balance || 0) }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">总盈亏</span>
                <span class="stat-value" :class="getPnLClass(account.total_pnl || 0)">
                  {{ formatCurrency(account.total_pnl || 0) }}
                </span>
              </div>
            </div>
            
            <div class="account-actions">
              <el-button size="small" @click="viewAccount(account.id)">
                <el-icon><View /></el-icon>
                查看详情
              </el-button>
              <el-button size="small" @click="goToTransactions(account.id)">
                <el-icon><List /></el-icon>
                交易流水
              </el-button>
            </div>
            </div>
          </ErrorBoundary>
        </div>
      </div>
    </el-card>

    <!-- 创建账户对话框 -->
    <el-dialog v-model="showCreateDialog" title="创建账户" width="500px">
      <el-form :model="createForm" label-width="100px">
        <el-form-item label="账户名称">
          <el-input v-model="createForm.account_name" placeholder="请输入账户名称" />
        </el-form-item>
        <el-form-item label="账户类型">
          <el-select v-model="createForm.account_type" placeholder="选择账户类型">
            <el-option label="现金账户" value="CASH" />
            <el-option label="保证金账户" value="MARGIN" />
            <el-option label="期货账户" value="FUTURES" />
            <el-option label="期权账户" value="OPTIONS" />
          </el-select>
        </el-form-item>
        <el-form-item label="基础货币">
          <el-select v-model="createForm.base_currency" placeholder="选择基础货币">
            <el-option label="人民币 (CNY)" value="CNY" />
            <el-option label="美元 (USD)" value="USD" />
          </el-select>
        </el-form-item>
        <el-form-item label="初始资金">
          <el-input-number 
            v-model="createForm.initial_balance" 
            :min="0" 
            :precision="2"
            placeholder="初始资金"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createAccount">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { 
  Wallet, 
  Money, 
  TrendCharts, 
  DataAnalysis, 
  Refresh, 
  Plus, 
  View, 
  List 
} from '@element-plus/icons-vue'
import { useAccountStore } from '@/stores/account'
import { formatCurrency } from '@/utils/format'
import ErrorBoundary from '@/components/ErrorBoundary.vue'

const router = useRouter()
const accountStore = useAccountStore()

// 响应式数据
const loading = ref(false)
const showCreateDialog = ref(false)

// 创建账户表单
const createForm = ref({
  account_name: '',
  account_type: 'CASH',
  base_currency: 'CNY',
  initial_balance: 0
})

// 计算属性
const accounts = computed(() => accountStore.accounts)

// 方法
const refreshData = async () => {
  loading.value = true
  try {
    await accountStore.loadAccounts()
    ElMessage.success('账户数据已刷新')
  } catch (error) {
    ElMessage.error('刷新账户数据失败')
  } finally {
    loading.value = false
  }
}

const createAccount = async () => {
  try {
    // 这里调用创建账户API
    ElMessage.success('账户创建功能开发中')
    showCreateDialog.value = false
    // 重置表单
    createForm.value = {
      account_name: '',
      account_type: 'CASH',
      base_currency: 'CNY',
      initial_balance: 0
    }
  } catch (error) {
    ElMessage.error('创建账户失败')
  }
}

const viewAccount = (accountId: number) => {
  router.push(`/account/overview?accountId=${accountId}`)
}

const goToTransactions = (accountId: number) => {
  router.push(`/account/transactions?accountId=${accountId}`)
}

// 工具函数
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

const getPnLClass = (pnl: number) => {
  return pnl >= 0 ? 'positive' : 'negative'
}

// 错误处理函数
const onAccountCardError = (error: Error) => {
  console.error('🚨 账户卡片发生错误:', error)
  ElMessage.error('账户卡片加载失败，请刷新页面重试')
}

const onAccountCardRetry = () => {
  console.log('🔄 重试加载账户卡片...')
  refreshData()
}

// 生命周期
onMounted(async () => {
  console.log('💼 账户管理页面已加载')
  await refreshData()
})
</script>

<style lang="scss" scoped>
.accounts-container {
  padding: 24px;
  background: var(--el-bg-color-page);
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
  text-align: center;
}

.page-title {
  margin: 0 0 8px 0;
  font-size: 32px;
  font-weight: 700;
  color: var(--el-text-color-primary);
}

.page-description {
  margin: 0;
  font-size: 18px;
  color: var(--el-text-color-regular);
}

.header-actions {
  display: flex;
  gap: 12px;
}

.overview-cards {
  margin-bottom: 32px;
}

.overview-card {
  text-align: center;
  transition: all 0.3s ease;
}

.overview-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.card-title {
  font-size: 14px;
  color: var(--el-text-color-regular);
  font-weight: 500;
}

.card-icon {
  font-size: 24px;
  color: var(--el-color-primary);
}

.card-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  margin-bottom: 8px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

.positive {
  color: #67c23a;
}

.negative {
  color: #f56c6c;
}

.accounts-list {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.empty-state {
  padding: 60px 20px;
  text-align: center;
}

.accounts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 20px;
}

.account-card {
  background: var(--el-bg-color-page);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid var(--el-border-color-light);
  transition: all 0.3s ease;
}

.account-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.account-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.account-info h3 {
  margin: 0 0 4px 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.account-info p {
  margin: 0;
  font-size: 14px;
  color: var(--el-text-color-regular);
}

.account-stats {
  margin-bottom: 16px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.stat-item:last-child {
  border-bottom: none;
}

.stat-label {
  font-size: 14px;
  color: var(--el-text-color-regular);
  font-weight: 500;
}

.stat-value {
  font-size: 16px;
  color: var(--el-text-color-primary);
  font-weight: 600;
}

.account-actions {
  display: flex;
  gap: 8px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .accounts-container {
    padding: 16px;
  }
  
  .page-header {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }
  
  .overview-cards {
    margin-bottom: 24px;
  }
  
  .accounts-grid {
    grid-template-columns: 1fr;
  }
}
</style>