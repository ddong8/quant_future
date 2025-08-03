<template>
  <div class="data-table">
    <!-- 表格工具栏 -->
    <div v-if="showToolbar" class="table-toolbar">
      <div class="toolbar-left">
        <slot name="toolbar-left">
          <el-input
            v-if="searchable"
            v-model="searchQuery"
            :placeholder="searchPlaceholder"
            prefix-icon="Search"
            clearable
            class="search-input"
            @input="handleSearch"
          />
        </slot>
      </div>
      <div class="toolbar-right">
        <slot name="toolbar-right">
          <el-button
            v-if="exportable"
            type="primary"
            :icon="Download"
            @click="handleExport"
          >
            导出
          </el-button>
          <el-button
            v-if="refreshable"
            :icon="Refresh"
            @click="handleRefresh"
          >
            刷新
          </el-button>
        </slot>
      </div>
    </div>

    <!-- 数据表格 -->
    <el-table
      ref="tableRef"
      :data="filteredData"
      :loading="loading"
      :height="height"
      :max-height="maxHeight"
      :stripe="stripe"
      :border="border"
      :size="size"
      :row-key="rowKey"
      :default-sort="defaultSort"
      :selection-type="selectionType"
      @selection-change="handleSelectionChange"
      @sort-change="handleSortChange"
      @row-click="handleRowClick"
      @row-dblclick="handleRowDblClick"
    >
      <!-- 选择列 -->
      <el-table-column
        v-if="selectable"
        type="selection"
        width="55"
        align="center"
      />

      <!-- 序号列 -->
      <el-table-column
        v-if="showIndex"
        type="index"
        label="序号"
        width="60"
        align="center"
      />

      <!-- 动态列 -->
      <el-table-column
        v-for="column in columns"
        :key="column.prop"
        :prop="column.prop"
        :label="column.label"
        :width="column.width"
        :min-width="column.minWidth"
        :fixed="column.fixed"
        :sortable="column.sortable"
        :align="column.align || 'left'"
        :show-overflow-tooltip="column.showOverflowTooltip !== false"
      >
        <template #default="{ row, column: col, $index }">
          <slot
            :name="column.prop"
            :row="row"
            :column="col"
            :index="$index"
            :value="row[column.prop]"
          >
            <!-- 默认渲染 -->
            <span v-if="column.type === 'text'">
              {{ formatValue(row[column.prop], column) }}
            </span>
            
            <!-- 数字类型 -->
            <span v-else-if="column.type === 'number'" class="number-cell">
              {{ formatNumber(row[column.prop], column) }}
            </span>
            
            <!-- 货币类型 -->
            <span v-else-if="column.type === 'currency'" class="currency-cell">
              {{ formatCurrency(row[column.prop], column) }}
            </span>
            
            <!-- 百分比类型 -->
            <span v-else-if="column.type === 'percentage'" class="percentage-cell">
              {{ formatPercentage(row[column.prop], column) }}
            </span>
            
            <!-- 日期时间类型 -->
            <span v-else-if="column.type === 'datetime'" class="datetime-cell">
              {{ formatDateTime(row[column.prop], column) }}
            </span>
            
            <!-- 状态类型 -->
            <el-tag
              v-else-if="column.type === 'status'"
              :type="getStatusType(row[column.prop], column)"
              size="small"
            >
              {{ getStatusText(row[column.prop], column) }}
            </el-tag>
            
            <!-- 操作按钮 -->
            <div v-else-if="column.type === 'actions'" class="action-buttons">
              <el-button
                v-for="action in column.actions"
                :key="action.key"
                :type="action.type || 'primary'"
                :size="action.size || 'small'"
                :icon="action.icon"
                :disabled="isActionDisabled(action, row)"
                @click="handleAction(action, row, $index)"
              >
                {{ action.label }}
              </el-button>
            </div>
            
            <!-- 默认文本 -->
            <span v-else>
              {{ row[column.prop] }}
            </span>
          </slot>
        </template>
      </el-table-column>

      <!-- 空数据 -->
      <template #empty>
        <div class="empty-data">
          <el-empty :description="emptyText" />
        </div>
      </template>
    </el-table>

    <!-- 分页器 -->
    <div v-if="pagination && total > 0" class="table-pagination">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="pageSizes"
        :layout="paginationLayout"
        :background="true"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { ElTable, ElTableColumn, ElInput, ElButton, ElTag, ElPagination, ElEmpty } from 'element-plus'
import { Download, Refresh, Search } from '@element-plus/icons-vue'
import dayjs from 'dayjs'

// 类型定义
interface TableColumn {
  prop: string
  label: string
  width?: number | string
  minWidth?: number | string
  fixed?: boolean | string
  sortable?: boolean | string
  align?: 'left' | 'center' | 'right'
  showOverflowTooltip?: boolean
  type?: 'text' | 'number' | 'currency' | 'percentage' | 'datetime' | 'status' | 'actions'
  format?: string
  precision?: number
  statusMap?: Record<string, { text: string; type: string }>
  actions?: Array<{
    key: string
    label: string
    type?: string
    size?: string
    icon?: any
    disabled?: (row: any) => boolean
  }>
}

interface Props {
  data: any[]
  columns: TableColumn[]
  loading?: boolean
  height?: number | string
  maxHeight?: number | string
  stripe?: boolean
  border?: boolean
  size?: 'large' | 'default' | 'small'
  rowKey?: string
  defaultSort?: { prop: string; order: 'ascending' | 'descending' }
  
  // 功能开关
  selectable?: boolean
  showIndex?: boolean
  searchable?: boolean
  exportable?: boolean
  refreshable?: boolean
  pagination?: boolean
  showToolbar?: boolean
  
  // 搜索配置
  searchPlaceholder?: string
  searchFields?: string[]
  
  // 分页配置
  total?: number
  pageSize?: number
  pageSizes?: number[]
  paginationLayout?: string
  
  // 其他配置
  emptyText?: string
  selectionType?: 'single' | 'multiple'
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  stripe: true,
  border: true,
  size: 'default',
  selectable: false,
  showIndex: false,
  searchable: true,
  exportable: false,
  refreshable: true,
  pagination: true,
  showToolbar: true,
  searchPlaceholder: '请输入搜索关键词',
  total: 0,
  pageSize: 20,
  pageSizes: () => [10, 20, 50, 100],
  paginationLayout: 'total, sizes, prev, pager, next, jumper',
  emptyText: '暂无数据',
  selectionType: 'multiple'
})

// 事件定义
const emit = defineEmits<{
  'selection-change': [selection: any[]]
  'sort-change': [sort: { prop: string; order: string }]
  'row-click': [row: any, column: any, event: Event]
  'row-dblclick': [row: any, column: any, event: Event]
  'action-click': [action: string, row: any, index: number]
  'search': [query: string]
  'refresh': []
  'export': []
  'size-change': [size: number]
  'current-change': [page: number]
}>()

// 响应式数据
const tableRef = ref<InstanceType<typeof ElTable>>()
const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(props.pageSize)

// 计算属性
const filteredData = computed(() => {
  if (!props.searchable || !searchQuery.value) {
    return props.data
  }
  
  const query = searchQuery.value.toLowerCase()
  const searchFields = props.searchFields || props.columns.map(col => col.prop)
  
  return props.data.filter(row => {
    return searchFields.some(field => {
      const value = row[field]
      return value && String(value).toLowerCase().includes(query)
    })
  })
})

// 事件处理
const handleSelectionChange = (selection: any[]) => {
  emit('selection-change', selection)
}

const handleSortChange = (sort: { prop: string; order: string }) => {
  emit('sort-change', sort)
}

const handleRowClick = (row: any, column: any, event: Event) => {
  emit('row-click', row, column, event)
}

const handleRowDblClick = (row: any, column: any, event: Event) => {
  emit('row-dblclick', row, column, event)
}

const handleAction = (action: any, row: any, index: number) => {
  emit('action-click', action.key, row, index)
}

const handleSearch = (query: string) => {
  emit('search', query)
}

const handleRefresh = () => {
  emit('refresh')
}

const handleExport = () => {
  emit('export')
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  emit('size-change', size)
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
  emit('current-change', page)
}

// 格式化函数
const formatValue = (value: any, column: TableColumn) => {
  if (value === null || value === undefined) return '-'
  return String(value)
}

const formatNumber = (value: any, column: TableColumn) => {
  if (value === null || value === undefined) return '-'
  const num = Number(value)
  if (isNaN(num)) return '-'
  
  const precision = column.precision ?? 2
  return num.toFixed(precision)
}

const formatCurrency = (value: any, column: TableColumn) => {
  if (value === null || value === undefined) return '-'
  const num = Number(value)
  if (isNaN(num)) return '-'
  
  const precision = column.precision ?? 2
  return `¥${num.toFixed(precision)}`
}

const formatPercentage = (value: any, column: TableColumn) => {
  if (value === null || value === undefined) return '-'
  const num = Number(value)
  if (isNaN(num)) return '-'
  
  const precision = column.precision ?? 2
  return `${(num * 100).toFixed(precision)}%`
}

const formatDateTime = (value: any, column: TableColumn) => {
  if (!value) return '-'
  const format = column.format || 'YYYY-MM-DD HH:mm:ss'
  return dayjs(value).format(format)
}

const getStatusType = (value: any, column: TableColumn) => {
  const statusMap = column.statusMap || {}
  return statusMap[value]?.type || 'info'
}

const getStatusText = (value: any, column: TableColumn) => {
  const statusMap = column.statusMap || {}
  return statusMap[value]?.text || value
}

const isActionDisabled = (action: any, row: any) => {
  return action.disabled ? action.disabled(row) : false
}

// 公开方法
const clearSelection = () => {
  tableRef.value?.clearSelection()
}

const toggleRowSelection = (row: any, selected?: boolean) => {
  tableRef.value?.toggleRowSelection(row, selected)
}

const toggleAllSelection = () => {
  tableRef.value?.toggleAllSelection()
}

const setCurrentRow = (row: any) => {
  tableRef.value?.setCurrentRow(row)
}

defineExpose({
  clearSelection,
  toggleRowSelection,
  toggleAllSelection,
  setCurrentRow
})
</script>

<style lang="scss" scoped>
.data-table {
  .table-toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    
    .toolbar-left {
      display: flex;
      align-items: center;
      gap: 12px;
      
      .search-input {
        width: 300px;
      }
    }
    
    .toolbar-right {
      display: flex;
      align-items: center;
      gap: 8px;
    }
  }
  
  .number-cell {
    font-family: 'Monaco', 'Menlo', monospace;
    text-align: right;
  }
  
  .currency-cell {
    font-family: 'Monaco', 'Menlo', monospace;
    text-align: right;
    color: var(--el-color-success);
  }
  
  .percentage-cell {
    font-family: 'Monaco', 'Menlo', monospace;
    text-align: right;
  }
  
  .datetime-cell {
    font-family: 'Monaco', 'Menlo', monospace;
    color: var(--el-text-color-secondary);
  }
  
  .action-buttons {
    display: flex;
    gap: 4px;
    flex-wrap: wrap;
  }
  
  .empty-data {
    padding: 40px 0;
  }
  
  .table-pagination {
    display: flex;
    justify-content: flex-end;
    margin-top: 16px;
  }
}
</style>