<template>
  <div class="historical-data-selector">
    <div class="selector-header">
      <h3>历史数据选择</h3>
      <el-button size="small" @click="handleRefresh" :loading="loading">
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
    </div>

    <!-- 筛选条件 -->
    <div class="filters">
      <el-row :gutter="16">
        <el-col :span="6">
          <el-select v-model="filters.exchange" placeholder="交易所" clearable>
            <el-option label="上海期货交易所" value="SHFE" />
            <el-option label="大连商品交易所" value="DCE" />
            <el-option label="郑州商品交易所" value="CZCE" />
            <el-option label="中国金融期货交易所" value="CFFEX" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-select v-model="filters.category" placeholder="品种分类" clearable>
            <el-option label="有色金属" value="metals" />
            <el-option label="黑色金属" value="ferrous" />
            <el-option label="农产品" value="agriculture" />
            <el-option label="化工" value="chemical" />
            <el-option label="股指期货" value="index" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-date-picker
            v-model="filters.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            size="small"
          />
        </el-col>
        <el-col :span="6">
          <el-input
            v-model="filters.search"
            placeholder="搜索品种"
            clearable
            size="small"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
      </el-row>
    </div>

    <!-- 数据表格 -->
    <div class="data-table">
      <el-table
        :data="filteredData"
        v-loading="loading"
        @selection-change="handleSelectionChange"
        height="400"
      >
        <el-table-column type="selection" width="55" />
        
        <el-table-column prop="symbol" label="合约代码" width="120">
          <template #default="{ row }">
            <el-tag size="small">{{ row.symbol }}</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="name" label="合约名称" width="150" />
        
        <el-table-column prop="exchange" label="交易所" width="100">
          <template #default="{ row }">
            <el-tag :type="getExchangeTagType(row.exchange)" size="small">
              {{ row.exchange }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="category" label="分类" width="100" />
        
        <el-table-column prop="start_date" label="开始日期" width="120">
          <template #default="{ row }">
            {{ formatDate(row.start_date) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="end_date" label="结束日期" width="120">
          <template #default="{ row }">
            {{ formatDate(row.end_date) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="total_records" label="数据量" width="100">
          <template #default="{ row }">
            {{ formatNumber(row.total_records) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="data_quality" label="数据质量" width="120">
          <template #default="{ row }">
            <el-progress
              :percentage="row.data_quality * 100"
              :color="getQualityColor(row.data_quality)"
              :show-text="false"
              style="width: 80px"
            />
            <span style="margin-left: 8px">{{ (row.data_quality * 100).toFixed(1) }}%</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="missing_days" label="缺失天数" width="100">
          <template #default="{ row }">
            <span :class="row.missing_days.length > 0 ? 'text-warning' : 'text-success'">
              {{ row.missing_days.length }}
            </span>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button text size="small" @click="viewDataDetail(row)">
              详情
            </el-button>
            <el-button text size="small" @click="previewData(row)">
              预览
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 选中数据统计 -->
    <div class="selection-summary" v-if="selectedData.length > 0">
      <el-card>
        <div class="summary-content">
          <div class="summary-item">
            <span class="label">已选择:</span>
            <span class="value">{{ selectedData.length }} 个品种</span>
          </div>
          <div class="summary-item">
            <span class="label">时间范围:</span>
            <span class="value">{{ getDateRange() }}</span>
          </div>
          <div class="summary-item">
            <span class="label">总数据量:</span>
            <span class="value">{{ getTotalRecords() }}</span>
          </div>
          <div class="summary-item">
            <span class="label">平均质量:</span>
            <span class="value">{{ getAverageQuality() }}%</span>
          </div>
        </div>
        
        <div class="summary-actions">
          <el-button size="small" @click="clearSelection">清空选择</el-button>
          <el-button size="small" @click="selectAll">全选</el-button>
          <el-button type="primary" size="small" @click="confirmSelection">
            确认选择
          </el-button>
        </div>
      </el-card>
    </div>

    <!-- 数据详情对话框 -->
    <el-dialog v-model="showDetailDialog" title="数据详情" width="600px">
      <div v-if="selectedDataDetail" class="data-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="合约代码">
            {{ selectedDataDetail.symbol }}
          </el-descriptions-item>
          <el-descriptions-item label="合约名称">
            {{ selectedDataDetail.name }}
          </el-descriptions-item>
          <el-descriptions-item label="交易所">
            {{ selectedDataDetail.exchange }}
          </el-descriptions-item>
          <el-descriptions-item label="分类">
            {{ selectedDataDetail.category }}
          </el-descriptions-item>
          <el-descriptions-item label="开始日期">
            {{ formatDate(selectedDataDetail.start_date) }}
          </el-descriptions-item>
          <el-descriptions-item label="结束日期">
            {{ formatDate(selectedDataDetail.end_date) }}
          </el-descriptions-item>
          <el-descriptions-item label="总记录数">
            {{ formatNumber(selectedDataDetail.total_records) }}
          </el-descriptions-item>
          <el-descriptions-item label="数据质量">
            {{ (selectedDataDetail.data_quality * 100).toFixed(2) }}%
          </el-descriptions-item>
        </el-descriptions>
        
        <div v-if="selectedDataDetail.missing_days.length > 0" class="missing-days">
          <h4>缺失日期</h4>
          <div class="missing-dates">
            <el-tag
              v-for="date in selectedDataDetail.missing_days.slice(0, 10)"
              :key="date"
              size="small"
              type="warning"
              style="margin: 2px"
            >
              {{ date }}
            </el-tag>
            <span v-if="selectedDataDetail.missing_days.length > 10">
              ... 还有 {{ selectedDataDetail.missing_days.length - 10 }} 个
            </span>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- 数据预览对话框 -->
    <el-dialog v-model="showPreviewDialog" title="数据预览" width="800px">
      <div v-if="previewDataContent" class="data-preview">
        <el-table :data="previewDataContent" height="400">
          <el-table-column prop="date" label="日期" width="120" />
          <el-table-column prop="open" label="开盘价" width="100" />
          <el-table-column prop="high" label="最高价" width="100" />
          <el-table-column prop="low" label="最低价" width="100" />
          <el-table-column prop="close" label="收盘价" width="100" />
          <el-table-column prop="volume" label="成交量" width="120" />
          <el-table-column prop="amount" label="成交额" width="120" />
        </el-table>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh } from '@element-plus/icons-vue'
import type { HistoricalDataInfo } from '@/types/backtest'

interface Props {
  modelValue: string[]
  frequency?: string
  dateRange?: string[]
}

interface Emits {
  (e: 'update:modelValue', value: string[]): void
  (e: 'change', value: string[]): void
}

const props = withDefaults(defineProps<Props>(), {
  frequency: '1d',
  dateRange: () => []
})

const emit = defineEmits<Emits>()

// 响应式数据
const loading = ref(false)
const showDetailDialog = ref(false)
const showPreviewDialog = ref(false)
const selectedDataDetail = ref<HistoricalDataInfo | null>(null)
const previewDataContent = ref<any[]>([])

// 筛选条件
const filters = ref({
  exchange: '',
  category: '',
  dateRange: [],
  search: ''
})

// 选中的数据
const selectedData = ref<HistoricalDataInfo[]>([])

// 模拟历史数据信息
const historicalData = ref<HistoricalDataInfo[]>([
  {
    symbol: 'SHFE.cu2401',
    name: '沪铜2401',
    exchange: 'SHFE',
    category: '有色金属',
    start_date: '2020-01-01',
    end_date: '2024-01-15',
    frequency: '1d',
    total_records: 1000,
    missing_days: ['2023-10-01', '2023-10-02'],
    data_quality: 0.98
  },
  {
    symbol: 'DCE.i2401',
    name: '铁矿石2401',
    exchange: 'DCE',
    category: '黑色金属',
    start_date: '2020-01-01',
    end_date: '2024-01-15',
    frequency: '1d',
    total_records: 1000,
    missing_days: [],
    data_quality: 1.0
  },
  {
    symbol: 'CZCE.MA401',
    name: '甲醇401',
    exchange: 'CZCE',
    category: '化工',
    start_date: '2020-01-01',
    end_date: '2024-01-15',
    frequency: '1d',
    total_records: 980,
    missing_days: ['2023-05-01', '2023-05-02', '2023-05-03'],
    data_quality: 0.97
  },
  {
    symbol: 'CFFEX.IF2401',
    name: '沪深300股指2401',
    exchange: 'CFFEX',
    category: '股指期货',
    start_date: '2020-01-01',
    end_date: '2024-01-15',
    frequency: '1d',
    total_records: 1000,
    missing_days: [],
    data_quality: 1.0
  }
])

// 计算属性
const filteredData = computed(() => {
  let result = historicalData.value
  
  // 交易所筛选
  if (filters.value.exchange) {
    result = result.filter(item => item.exchange === filters.value.exchange)
  }
  
  // 分类筛选
  if (filters.value.category) {
    result = result.filter(item => item.category === filters.value.category)
  }
  
  // 搜索筛选
  if (filters.value.search) {
    const search = filters.value.search.toLowerCase()
    result = result.filter(item => 
      item.symbol.toLowerCase().includes(search) ||
      item.name.toLowerCase().includes(search)
    )
  }
  
  return result
})

// 方法
const handleRefresh = async () => {
  loading.value = true
  try {
    // 模拟刷新数据
    await new Promise(resolve => setTimeout(resolve, 1000))
    ElMessage.success('数据已刷新')
  } finally {
    loading.value = false
  }
}

const handleSelectionChange = (selection: HistoricalDataInfo[]) => {
  selectedData.value = selection
  const symbols = selection.map(item => item.symbol)
  emit('update:modelValue', symbols)
  emit('change', symbols)
}

const viewDataDetail = (data: HistoricalDataInfo) => {
  selectedDataDetail.value = data
  showDetailDialog.value = true
}

const previewData = async (data: HistoricalDataInfo) => {
  // 模拟获取预览数据
  previewDataContent.value = [
    {
      date: '2024-01-15',
      open: 72500,
      high: 72800,
      low: 72200,
      close: 72600,
      volume: 150000,
      amount: 1087500000
    },
    {
      date: '2024-01-14',
      open: 72300,
      high: 72600,
      low: 72100,
      close: 72500,
      volume: 140000,
      amount: 1015000000
    },
    {
      date: '2024-01-13',
      open: 72100,
      high: 72400,
      low: 71900,
      close: 72300,
      volume: 160000,
      amount: 1156800000
    }
  ]
  
  showPreviewDialog.value = true
}

const clearSelection = () => {
  selectedData.value = []
  emit('update:modelValue', [])
  emit('change', [])
}

const selectAll = () => {
  selectedData.value = [...filteredData.value]
  const symbols = filteredData.value.map(item => item.symbol)
  emit('update:modelValue', symbols)
  emit('change', symbols)
}

const confirmSelection = () => {
  if (selectedData.value.length === 0) {
    ElMessage.warning('请先选择数据')
    return
  }
  
  ElMessage.success(`已选择 ${selectedData.value.length} 个品种`)
}

const getDateRange = () => {
  if (selectedData.value.length === 0) return '-'
  
  const startDates = selectedData.value.map(item => new Date(item.start_date))
  const endDates = selectedData.value.map(item => new Date(item.end_date))
  
  const minStart = new Date(Math.min(...startDates.map(d => d.getTime())))
  const maxEnd = new Date(Math.max(...endDates.map(d => d.getTime())))
  
  return `${formatDate(minStart.toISOString())} ~ ${formatDate(maxEnd.toISOString())}`
}

const getTotalRecords = () => {
  const total = selectedData.value.reduce((sum, item) => sum + item.total_records, 0)
  return formatNumber(total)
}

const getAverageQuality = () => {
  if (selectedData.value.length === 0) return '0'
  
  const avgQuality = selectedData.value.reduce((sum, item) => sum + item.data_quality, 0) / selectedData.value.length
  return (avgQuality * 100).toFixed(1)
}

const getExchangeTagType = (exchange: string) => {
  const typeMap: Record<string, string> = {
    SHFE: 'primary',
    DCE: 'success',
    CZCE: 'warning',
    CFFEX: 'danger'
  }
  return typeMap[exchange] || 'info'
}

const getQualityColor = (quality: number) => {
  if (quality >= 0.95) return '#67c23a'
  if (quality >= 0.9) return '#e6a23c'
  return '#f56c6c'
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('zh-CN')
}

const formatNumber = (num: number) => {
  return new Intl.NumberFormat('zh-CN').format(num)
}

// 生命周期
onMounted(() => {
  // 根据props设置初始选择
  if (props.modelValue.length > 0) {
    selectedData.value = historicalData.value.filter(item => 
      props.modelValue.includes(item.symbol)
    )
  }
})
</script>

<style scoped lang="scss">
.historical-data-selector {
  .selector-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    
    h3 {
      margin: 0;
      font-size: 16px;
      font-weight: 600;
    }
  }
  
  .filters {
    margin-bottom: 16px;
    padding: 16px;
    background: var(--el-bg-color-page);
    border-radius: 8px;
  }
  
  .data-table {
    margin-bottom: 16px;
  }
  
  .selection-summary {
    .summary-content {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
      
      .summary-item {
        display: flex;
        align-items: center;
        gap: 4px;
        
        .label {
          font-size: 14px;
          color: #606266;
        }
        
        .value {
          font-size: 14px;
          font-weight: 600;
          color: #303133;
        }
      }
    }
    
    .summary-actions {
      display: flex;
      justify-content: flex-end;
      gap: 8px;
    }
  }
  
  .data-detail {
    .missing-days {
      margin-top: 16px;
      
      h4 {
        margin: 0 0 8px 0;
        font-size: 14px;
        color: #303133;
      }
      
      .missing-dates {
        line-height: 1.8;
      }
    }
  }
  
  .text-warning {
    color: #e6a23c;
  }
  
  .text-success {
    color: #67c23a;
  }
}
</style>