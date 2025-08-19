<template>
  <div class="transaction-history">
    <!-- 筛选器 -->
    <el-card class="filter-card">
      <template #header>
        <span>筛选条件</span>
      </template>
      <div class="filters">
        <div class="filter-group">
          <label>交易类型:</label>
          <el-select v-model="filters.transaction_type" placeholder="全部类型" clearable>
            <el-option label="入金" value="DEPOSIT" />
            <el-option label="出金" value="WITHDRAW" />
            <el-option label="交易" value="TRADE" />
            <el-option label="手续费" value="FEE" />
            <el-option label="利息" value="INTEREST" />
            <el-option label="转账" value="TRANSFER" />
          </el-select>
        </div>
        <div class="filter-group">
          <label>状态:</label>
          <el-select v-model="filters.status" placeholder="全部状态" clearable>
            <el-option label="待处理" value="PENDING" />
            <el-option label="已完成" value="COMPLETED" />
            <el-option label="失败" value="FAILED" />
            <el-option label="已取消" value="CANCELLED" />
          </el-select>
        </div>
        <div class="filter-group">
          <label>时间范围:</label>
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
          />
        </div>
        <el-button type="primary" @click="applyFilters">应用筛选</el-button>
      </div>
    </el-card>

    <!-- 交易流水列表 -->
    <el-card class="transactions-card">
      <template #header>
        <div class="card-header">
          <span>交易流水</span>
          <div class="header-actions">
            <el-button size="small" @click="exportTransactions">
              <el-icon><Download /></el-icon>
              导出
            </el-button>
            <el-button size="small" @click="refreshTransactions">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </div>
      </template>
      
      <div v-loading="loading">
        <div v-if="transactions.length === 0" class="empty-state">
          <el-empty description="暂无交易记录" />
        </div>
        <div v-else class="transactions-list">
          <div v-for="transaction in transactions" :key="transaction.id" class="transaction-item">
            <div class="transaction-header">
              <div class="transaction-type">
                <el-tag :type="getTransactionTypeTag(transaction.transaction_type)">
                  {{ getTransactionTypeName(transaction.transaction_type) }}
                </el-tag>
              </div>
              <div class="transaction-time">
                {{ formatDateTime(transaction.created_at) }}
              </div>
            </div>
            
            <div class="transaction-content">
              <div class="transaction-info">
                <div class="info-row">
                  <span class="label">金额:</span>
                  <span class="value" :class="getAmountClass(transaction.transaction_type, transaction.amount)">
                    {{ formatTransactionAmount(transaction.transaction_type, transaction.amount) }}
                  </span>
                </div>
                <div class="info-row" v-if="transaction.symbol">
                  <span class="label">品种:</span>
                  <span class="value">{{ transaction.symbol }}</span>
                </div>
                <div class="info-row">
                  <span class="label">余额变化:</span>
                  <span class="value">
                    {{ formatCurrency(transaction.balance_before) }} → {{ formatCurrency(transaction.balance_after) }}
                  </span>
                </div>
                <div class="info-row" v-if="transaction.description">
                  <span class="label">说明:</span>
                  <span class="value">{{ transaction.description }}</span>
                </div>
              </div>
              <div class="transaction-status">
                <el-tag :type="getStatusTag(transaction.status)">
                  {{ getStatusName(transaction.status) }}
                </el-tag>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 分页 -->
        <div v-if="pagination.total > 0" class="pagination">
          <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.page_size"
            :total="pagination.total"
            :page-sizes="[20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Download, Refresh } from '@element-plus/icons-vue'
import { useAccountStore } from '@/stores/account'
import { formatCurrency, formatDateTime } from '@/utils/format'
import type { AccountTransaction } from '@/api/account'

// Props
const props = defineProps<{
  accountId?: number | null
}>()

const accountStore = useAccountStore()

// 响应式数据
const loading = ref(false)
const transactions = ref<AccountTransaction[]>([])
const dateRange = ref<[string, string] | null>(null)

// 筛选条件
const filters = reactive({
  transaction_type: '',
  status: ''
})

// 分页
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

// 方法
const loadTransactions = async () => {
  if (!props.accountId) return
  
  loading.value = true
  try {
    const params = {
      transaction_type: filters.transaction_type || undefined,
      status: filters.status || undefined,
      start_date: dateRange.value?.[0] || undefined,
      end_date: dateRange.value?.[1] || undefined,
      page: pagination.page,
      page_size: pagination.page_size
    }
    
    const result = await accountStore.loadTransactions(props.accountId.toString(), params)
    
    if (result && result.data) {
      transactions.value = result.data
      if (result.meta) {
        pagination.total = result.meta.total || 0
      }
    }
    
    console.log(`✅ 加载了 ${transactions.value.length} 条交易记录`)
  } catch (error) {
    console.error('❌ 加载交易记录失败:', error)
    ElMessage.error('加载交易记录失败')
    // 使用模拟数据
    loadMockTransactions()
  } finally {
    loading.value = false
  }
}

const loadMockTransactions = () => {
  transactions.value = [
    {
      id: 1,
      account_id: props.accountId || 1,
      transaction_type: 'DEPOSIT',
      amount: 100000,
      balance_before: 0,
      balance_after: 100000,
      currency: 'CNY',
      description: '初始入金',
      status: 'COMPLETED',
      created_at: '2025-01-10T10:00:00Z',
      updated_at: '2025-01-10T10:00:00Z'
    },
    {
      id: 2,
      account_id: props.accountId || 1,
      transaction_type: 'TRADE',
      amount: -5000,
      balance_before: 100000,
      balance_after: 95000,
      currency: 'CNY',
      symbol: 'SHFE.cu2601',
      description: '沪铜交易手续费',
      status: 'COMPLETED',
      created_at: '2025-01-12T14:30:00Z',
      updated_at: '2025-01-12T14:30:00Z'
    },
    {
      id: 3,
      account_id: props.accountId || 1,
      transaction_type: 'WITHDRAW',
      amount: -20000,
      balance_before: 95000,
      balance_after: 75000,
      currency: 'CNY',
      description: '提取资金',
      status: 'PENDING',
      created_at: '2025-01-14T09:15:00Z',
      updated_at: '2025-01-14T09:15:00Z'
    }
  ]
  pagination.total = transactions.value.length
}

const applyFilters = () => {
  pagination.page = 1
  loadTransactions()
}

const refreshTransactions = () => {
  loadTransactions()
}

const exportTransactions = () => {
  try {
    const exportData = {
      account_id: props.accountId,
      transactions: transactions.value,
      export_time: new Date().toISOString(),
      filters: filters
    }
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: 'application/json'
    })
    
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `transactions_${props.accountId}_${new Date().toISOString().split('T')[0]}.json`
    a.click()
    
    URL.revokeObjectURL(url)
    ElMessage.success('交易记录导出成功')
  } catch (error) {
    ElMessage.error('导出失败')
  }
}

const handleSizeChange = (size: number) => {
  pagination.page_size = size
  loadTransactions()
}

const handleCurrentChange = (page: number) => {
  pagination.page = page
  loadTransactions()
}

// 工具函数
const getTransactionTypeTag = (type: string) => {
  const tagMap = {
    'DEPOSIT': 'success',
    'WITHDRAW': 'warning',
    'TRADE': 'info',
    'FEE': 'danger',
    'INTEREST': 'success',
    'TRANSFER': 'primary'
  }
  return tagMap[type] || 'info'
}

const getTransactionTypeName = (type: string) => {
  const nameMap = {
    'DEPOSIT': '入金',
    'WITHDRAW': '出金',
    'TRADE': '交易',
    'FEE': '手续费',
    'INTEREST': '利息',
    'DIVIDEND': '分红',
    'TRANSFER': '转账',
    'FREEZE': '冻结',
    'UNFREEZE': '解冻'
  }
  return nameMap[type] || type
}

const getStatusTag = (status: string) => {
  const tagMap = {
    'PENDING': 'warning',
    'COMPLETED': 'success',
    'FAILED': 'danger',
    'CANCELLED': 'info'
  }
  return tagMap[status] || 'info'
}

const getStatusName = (status: string) => {
  const nameMap = {
    'PENDING': '待处理',
    'COMPLETED': '已完成',
    'FAILED': '失败',
    'CANCELLED': '已取消'
  }
  return nameMap[status] || status
}

const getAmountClass = (type: string, amount: number) => {
  if (type === 'DEPOSIT' || type === 'INTEREST' || type === 'DIVIDEND') {
    return 'positive'
  } else if (type === 'WITHDRAW' || type === 'FEE') {
    return 'negative'
  }
  return amount >= 0 ? 'positive' : 'negative'
}

const formatTransactionAmount = (type: string, amount: number) => {
  const sign = getAmountClass(type, amount) === 'positive' ? '+' : ''
  return `${sign}${formatCurrency(Math.abs(amount))}`
}

// 监听账户ID变化
watch(() => props.accountId, () => {
  if (props.accountId) {
    loadTransactions()
  }
}, { immediate: true })

// 生命周期
onMounted(() => {
  console.log('💳 交易流水组件已加载, 账户ID:', props.accountId)
  if (props.accountId) {
    loadTransactions()
  }
})
</script>

<style scoped>
.transaction-history {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.filter-card {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.filters {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
  align-items: end;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filter-group label {
  font-size: 14px;
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.transactions-card {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.empty-state {
  padding: 60px 20px;
  text-align: center;
}

.transactions-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.transaction-item {
  background: var(--el-bg-color-page);
  border-radius: 8px;
  padding: 16px;
  border: 1px solid var(--el-border-color-light);
  transition: all 0.3s ease;
}

.transaction-item:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.transaction-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.transaction-time {
  font-size: 14px;
  color: var(--el-text-color-regular);
}

.transaction-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.transaction-info {
  flex: 1;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
}

.label {
  font-size: 14px;
  color: var(--el-text-color-regular);
  font-weight: 500;
}

.value {
  font-size: 14px;
  color: var(--el-text-color-primary);
  font-weight: 600;
}

.positive {
  color: #67c23a;
}

.negative {
  color: #f56c6c;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .filters {
    flex-direction: column;
    gap: 16px;
  }
  
  .filter-group {
    width: 100%;
  }
  
  .transaction-content {
    flex-direction: column;
    gap: 12px;
  }
  
  .transaction-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}
</style>