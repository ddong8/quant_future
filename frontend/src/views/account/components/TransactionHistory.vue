<template>
  <div class="transaction-history">
    <!-- 搜索和筛选 -->
    <el-card class="filter-card" shadow="never">
      <div class="filter-section">
        <el-row :gutter="16">
          <el-col :span="6">
            <el-select
              v-model="searchParams.transaction_types"
              multiple
              placeholder="交易类型"
              clearable
              collapse-tags
            >
              <el-option
                v-for="(label, value) in TransactionTypeLabels"
                :key="value"
                :label="label"
                :value="value"
              />
            </el-select>
          </el-col>
          <el-col :span="6">
            <el-select
              v-model="searchParams.status_list"
              multiple
              placeholder="交易状态"
              clearable
              collapse-tags
            >
              <el-option
                v-for="(label, value) in TransactionStatusLabels"
                :key="value"
                :label="label"
                :value="value"
              />
            </el-select>
          </el-col>
          <el-col :span="6">
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              @change="handleDateRangeChange"
            />
          </el-col>
          <el-col :span="6">
            <el-input
              v-model="searchParams.keyword"
              placeholder="搜索交易ID、描述等"
              clearable
              @keyup.enter="handleSearch"
            >
              <template #append>
                <el-button icon="Search" @click="handleSearch" />
              </template>
            </el-input>
          </el-col>
        </el-row>
        
        <el-row :gutter="16" class="mt-4">
          <el-col :span="6">
            <el-input-number
              v-model="searchParams.min_amount"
              placeholder="最小金额"
              :precision="2"
              controls-position="right"
              style="width: 100%"
            />
          </el-col>
          <el-col :span="6">
            <el-input-number
              v-model="searchParams.max_amount"
              placeholder="最大金额"
              :precision="2"
              controls-position="right"
              style="width: 100%"
            />
          </el-col>
          <el-col :span="6">
            <el-input
              v-model="searchParams.symbol"
              placeholder="交易标的"
              clearable
            />
          </el-col>
          <el-col :span="6">
            <div class="filter-actions">
              <el-button type="primary" @click="handleSearch">
                <el-icon><Search /></el-icon>
                搜索
              </el-button>
              <el-button @click="handleReset">
                <el-icon><Refresh /></el-icon>
                重置
              </el-button>
              <el-button @click="handleExport">
                <el-icon><Download /></el-icon>
                导出
              </el-button>
            </div>
          </el-col>
        </el-row>
      </div>
    </el-card>

    <!-- 统计卡片 -->
    <el-row :gutter="16" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-value income">{{ formatAmount(statistics.summary?.total_income || 0) }}</div>
            <div class="stat-label">总收入</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-value expense">{{ formatAmount(statistics.summary?.total_expense || 0) }}</div>
            <div class="stat-label">总支出</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-value net">{{ formatAmount(statistics.summary?.net_flow || 0) }}</div>
            <div class="stat-label">净流量</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-value">{{ statistics.summary?.total_transactions || 0 }}</div>
            <div class="stat-label">交易笔数</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 交易列表 -->
    <el-card class="table-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span>交易流水</span>
          <div class="header-actions">
            <el-button-group>
              <el-button
                :type="viewMode === 'table' ? 'primary' : 'default'"
                @click="viewMode = 'table'"
              >
                <el-icon><List /></el-icon>
                列表
              </el-button>
              <el-button
                :type="viewMode === 'chart' ? 'primary' : 'default'"
                @click="viewMode = 'chart'"
              >
                <el-icon><TrendCharts /></el-icon>
                图表
              </el-button>
            </el-button-group>
          </div>
        </div>
      </template>

      <!-- 表格视图 -->
      <div v-if="viewMode === 'table'">
        <el-table
          v-loading="loading"
          :data="transactions"
          stripe
          @sort-change="handleSortChange"
        >
          <el-table-column prop="transaction_id" label="交易ID" width="180" />
          <el-table-column prop="transaction_time" label="交易时间" width="160" sortable="custom">
            <template #default="{ row }">
              {{ formatDateTime(row.transaction_time) }}
            </template>
          </el-table-column>
          <el-table-column prop="transaction_type" label="类型" width="100">
            <template #default="{ row }">
              <el-tag :type="getTransactionTypeColor(row.transaction_type)">
                {{ TransactionTypeLabels[row.transaction_type] }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="amount" label="金额" width="120" sortable="custom" align="right">
            <template #default="{ row }">
              <span :class="{ 'amount-positive': row.amount > 0, 'amount-negative': row.amount < 0 }">
                {{ formatAmount(row.amount) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="symbol" label="标的" width="100" />
          <el-table-column prop="description" label="描述" min-width="150" show-overflow-tooltip />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="TransactionStatusColors[row.status]">
                {{ TransactionStatusLabels[row.status] }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="fee_amount" label="手续费" width="100" align="right">
            <template #default="{ row }">
              {{ formatAmount(row.fee_amount) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <el-button
                type="text"
                size="small"
                @click="handleViewDetail(row)"
              >
                详情
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <!-- 分页 -->
        <div class="pagination-wrapper">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :total="totalCount"
            :page-sizes="[20, 50, 100, 200]"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handlePageSizeChange"
            @current-change="handlePageChange"
          />
        </div>
      </div>

      <!-- 图表视图 -->
      <div v-else-if="viewMode === 'chart'" class="chart-view">
        <TransactionChart :statistics="statistics" />
      </div>
    </el-card>

    <!-- 交易详情对话框 -->
    <TransactionDetailDialog
      v-model="detailDialogVisible"
      :transaction="selectedTransaction"
    />

    <!-- 导出对话框 -->
    <TransactionExportDialog
      v-model="exportDialogVisible"
      :search-params="searchParams"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Download, List, TrendCharts } from '@element-plus/icons-vue'
import {
  searchTransactions,
  getTransactionStatistics,
  type Transaction,
  type TransactionSearchParams,
  type TransactionStatistics,
  TransactionTypeLabels,
  TransactionStatusLabels,
  TransactionStatusColors,
  formatTransactionAmount,
  getTransactionTypeColor
} from '@/api/transaction'
import TransactionDetailDialog from './TransactionDetailDialog.vue'
import TransactionExportDialog from './TransactionExportDialog.vue'
import TransactionChart from './TransactionChart.vue'

// 响应式数据
const loading = ref(false)
const transactions = ref<Transaction[]>([])
const totalCount = ref(0)
const currentPage = ref(1)
const pageSize = ref(50)
const viewMode = ref<'table' | 'chart'>('table')

// 搜索参数
const searchParams = reactive<TransactionSearchParams>({
  transaction_types: [],
  status_list: [],
  keyword: '',
  min_amount: undefined,
  max_amount: undefined,
  symbol: '',
  sort_field: 'transaction_time',
  sort_order: 'desc',
  skip: 0,
  limit: 50
})

// 日期范围
const dateRange = ref<[string, string] | null>(null)

// 统计数据
const statistics = ref<TransactionStatistics>({} as TransactionStatistics)

// 对话框状态
const detailDialogVisible = ref(false)
const exportDialogVisible = ref(false)
const selectedTransaction = ref<Transaction | null>(null)

// 计算属性
const skip = computed(() => (currentPage.value - 1) * pageSize.value)

// 加载交易数据
const loadTransactions = async () => {
  try {
    loading.value = true
    
    const params = {
      ...searchParams,
      skip: skip.value,
      limit: pageSize.value
    }
    
    const result = await searchTransactions(params)
    transactions.value = result.transactions
    totalCount.value = result.total_count
    
  } catch (error) {
    console.error('加载交易数据失败:', error)
    ElMessage.error('加载交易数据失败')
  } finally {
    loading.value = false
  }
}

// 加载统计数据
const loadStatistics = async () => {
  try {
    const stats = await getTransactionStatistics('month')
    statistics.value = stats
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

// 处理搜索
const handleSearch = () => {
  currentPage.value = 1
  loadTransactions()
}

// 处理重置
const handleReset = () => {
  Object.assign(searchParams, {
    transaction_types: [],
    status_list: [],
    keyword: '',
    min_amount: undefined,
    max_amount: undefined,
    symbol: '',
    sort_field: 'transaction_time',
    sort_order: 'desc'
  })
  dateRange.value = null
  currentPage.value = 1
  loadTransactions()
}

// 处理日期范围变化
const handleDateRangeChange = (dates: [string, string] | null) => {
  if (dates) {
    searchParams.start_date = dates[0]
    searchParams.end_date = dates[1]
  } else {
    searchParams.start_date = undefined
    searchParams.end_date = undefined
  }
}

// 处理排序变化
const handleSortChange = ({ prop, order }: { prop: string; order: string | null }) => {
  if (order) {
    searchParams.sort_field = prop
    searchParams.sort_order = order === 'ascending' ? 'asc' : 'desc'
  } else {
    searchParams.sort_field = 'transaction_time'
    searchParams.sort_order = 'desc'
  }
  loadTransactions()
}

// 处理页码变化
const handlePageChange = (page: number) => {
  currentPage.value = page
  loadTransactions()
}

// 处理页大小变化
const handlePageSizeChange = (size: number) => {
  pageSize.value = size
  searchParams.limit = size
  currentPage.value = 1
  loadTransactions()
}

// 查看详情
const handleViewDetail = (transaction: Transaction) => {
  selectedTransaction.value = transaction
  detailDialogVisible.value = true
}

// 处理导出
const handleExport = () => {
  exportDialogVisible.value = true
}

// 格式化金额
const formatAmount = (amount: number) => {
  return formatTransactionAmount(amount)
}

// 格式化日期时间
const formatDateTime = (dateTime: string | undefined) => {
  if (!dateTime) return '-'
  return new Date(dateTime).toLocaleString('zh-CN')
}

// 初始化
onMounted(() => {
  loadTransactions()
  loadStatistics()
})
</script>

<style scoped>
.transaction-history {
  padding: 20px;
}

.filter-card {
  margin-bottom: 20px;
}

.filter-section {
  padding: 10px 0;
}

.filter-actions {
  display: flex;
  gap: 8px;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
}

.stat-content {
  padding: 10px 0;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 8px;
}

.stat-value.income {
  color: #67c23a;
}

.stat-value.expense {
  color: #f56c6c;
}

.stat-value.net {
  color: #409eff;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.table-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.amount-positive {
  color: #67c23a;
}

.amount-negative {
  color: #f56c6c;
}

.pagination-wrapper {
  margin-top: 20px;
  text-align: right;
}

.chart-view {
  min-height: 400px;
}

.mt-4 {
  margin-top: 16px;
}
</style>