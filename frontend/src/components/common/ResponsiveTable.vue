<template>
  <div class="responsive-table-container" :class="containerClasses">
    <!-- 移动端卡片视图 -->
    <div v-if="isMobile && useCardView" class="mobile-card-view">
      <div
        v-for="(item, index) in data"
        :key="getRowKey(item, index)"
        class="mobile-card"
        @click="handleRowClick(item, index)"
      >
        <div class="card-header">
          <div class="card-title">
            {{ getCardTitle(item) }}
          </div>
          <div v-if="showCardActions" class="card-actions">
            <slot name="card-actions" :row="item" :index="index"></slot>
          </div>
        </div>
        
        <div class="card-content">
          <div
            v-for="column in visibleColumns"
            :key="column.prop"
            class="card-field"
          >
            <div class="field-label">{{ column.label }}</div>
            <div class="field-value" :class="getFieldClass(column, item)">
              <slot
                v-if="column.slot"
                :name="column.slot"
                :row="item"
                :column="column"
                :index="index"
              >
                {{ getFieldValue(item, column.prop) }}
              </slot>
              <template v-else>
                {{ formatFieldValue(item, column) }}
              </template>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 空状态 -->
      <div v-if="data.length === 0" class="empty-state">
        <el-empty :description="emptyText" />
      </div>
    </div>

    <!-- 桌面端表格视图 -->
    <div v-else class="desktop-table-view">
      <el-table
        ref="tableRef"
        :data="data"
        :height="tableHeight"
        :max-height="maxHeight"
        :stripe="stripe"
        :border="border"
        :size="tableSize"
        :fit="fit"
        :show-header="showHeader"
        :highlight-current-row="highlightCurrentRow"
        :row-class-name="rowClassName"
        :row-style="rowStyle"
        :cell-class-name="cellClassName"
        :cell-style="cellStyle"
        :header-row-class-name="headerRowClassName"
        :header-row-style="headerRowStyle"
        :header-cell-class-name="headerCellClassName"
        :header-cell-style="headerCellStyle"
        :row-key="rowKey"
        :empty-text="emptyText"
        :default-expand-all="defaultExpandAll"
        :expand-row-keys="expandRowKeys"
        :default-sort="defaultSort"
        :tooltip-effect="tooltipEffect"
        :show-summary="showSummary"
        :sum-text="sumText"
        :summary-method="summaryMethod"
        :span-method="spanMethod"
        :select-on-indeterminate="selectOnIndeterminate"
        :indent="indent"
        :lazy="lazy"
        :load="load"
        :tree-props="treeProps"
        @select="handleSelect"
        @select-all="handleSelectAll"
        @selection-change="handleSelectionChange"
        @cell-mouse-enter="handleCellMouseEnter"
        @cell-mouse-leave="handleCellMouseLeave"
        @cell-click="handleCellClick"
        @cell-dblclick="handleCellDblclick"
        @row-click="handleRowClick"
        @row-contextmenu="handleRowContextmenu"
        @row-dblclick="handleRowDblclick"
        @header-click="handleHeaderClick"
        @header-contextmenu="handleHeaderContextmenu"
        @sort-change="handleSortChange"
        @filter-change="handleFilterChange"
        @current-change="handleCurrentChange"
        @header-dragend="handleHeaderDragend"
        @expand-change="handleExpandChange"
      >
        <el-table-column
          v-for="column in visibleColumns"
          :key="column.prop"
          :prop="column.prop"
          :label="column.label"
          :width="getColumnWidth(column)"
          :min-width="column.minWidth"
          :fixed="column.fixed"
          :render-header="column.renderHeader"
          :sortable="column.sortable"
          :sort-method="column.sortMethod"
          :sort-by="column.sortBy"
          :sort-orders="column.sortOrders"
          :resizable="column.resizable"
          :formatter="column.formatter"
          :show-overflow-tooltip="column.showOverflowTooltip"
          :align="column.align"
          :header-align="column.headerAlign"
          :class-name="column.className"
          :label-class-name="column.labelClassName"
          :selectable="column.selectable"
          :reserve-selection="column.reserveSelection"
          :filters="column.filters"
          :filter-placement="column.filterPlacement"
          :filter-multiple="column.filterMultiple"
          :filter-method="column.filterMethod"
          :filtered-value="column.filteredValue"
        >
          <template v-if="column.slot" #default="scope">
            <slot
              :name="column.slot"
              :row="scope.row"
              :column="scope.column"
              :index="scope.$index"
            ></slot>
          </template>
          <template v-if="column.headerSlot" #header="scope">
            <slot
              :name="column.headerSlot"
              :column="scope.column"
              :index="scope.$index"
            ></slot>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 分页 -->
    <div v-if="showPagination" class="table-pagination">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="pageSizes"
        :size="paginationSize"
        :disabled="paginationDisabled"
        :hide-on-single-page="hideOnSinglePage"
        :total="total"
        :layout="paginationLayout"
        @size-change="handleSizeChange"
        @current-change="handleCurrentPageChange"
      />
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="table-loading">
      <el-skeleton :rows="skeletonRows" animated />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useResponsive } from '@/composables/useResponsive'
import type { TableColumnCtx } from 'element-plus'

interface Column {
  prop: string
  label: string
  width?: string | number
  minWidth?: string | number
  fixed?: boolean | string
  renderHeader?: Function
  sortable?: boolean | string
  sortMethod?: Function
  sortBy?: Function | string | Array<string | Function>
  sortOrders?: Array<string>
  resizable?: boolean
  formatter?: Function
  showOverflowTooltip?: boolean
  align?: string
  headerAlign?: string
  className?: string
  labelClassName?: string
  selectable?: Function
  reserveSelection?: boolean
  filters?: Array<{ text: string; value: any }>
  filterPlacement?: string
  filterMultiple?: boolean
  filterMethod?: Function
  filteredValue?: Array<any>
  slot?: string
  headerSlot?: string
  hideOnMobile?: boolean
  mobileOrder?: number
}

interface Props {
  data: Array<any>
  columns: Array<Column>
  height?: string | number
  maxHeight?: string | number
  stripe?: boolean
  border?: boolean
  size?: 'large' | 'default' | 'small'
  fit?: boolean
  showHeader?: boolean
  highlightCurrentRow?: boolean
  rowClassName?: string | Function
  rowStyle?: object | Function
  cellClassName?: string | Function
  cellStyle?: object | Function
  headerRowClassName?: string | Function
  headerRowStyle?: object | Function
  headerCellClassName?: string | Function
  headerCellStyle?: object | Function
  rowKey?: string | Function
  emptyText?: string
  defaultExpandAll?: boolean
  expandRowKeys?: Array<any>
  defaultSort?: object
  tooltipEffect?: string
  showSummary?: boolean
  sumText?: string
  summaryMethod?: Function
  spanMethod?: Function
  selectOnIndeterminate?: boolean
  indent?: number
  lazy?: boolean
  load?: Function
  treeProps?: object
  useCardView?: boolean
  showCardActions?: boolean
  cardTitleProp?: string
  showPagination?: boolean
  total?: number
  pageSize?: number
  pageSizes?: Array<number>
  currentPage?: number
  paginationLayout?: string
  hideOnSinglePage?: boolean
  loading?: boolean
  skeletonRows?: number
}

const props = withDefaults(defineProps<Props>(), {
  data: () => [],
  columns: () => [],
  stripe: true,
  border: false,
  size: 'default',
  fit: true,
  showHeader: true,
  highlightCurrentRow: false,
  emptyText: '暂无数据',
  defaultExpandAll: false,
  tooltipEffect: 'dark',
  showSummary: false,
  sumText: '合计',
  selectOnIndeterminate: true,
  indent: 16,
  lazy: false,
  useCardView: true,
  showCardActions: true,
  cardTitleProp: 'name',
  showPagination: false,
  total: 0,
  pageSize: 20,
  pageSizes: () => [10, 20, 50, 100],
  currentPage: 1,
  paginationLayout: 'total, sizes, prev, pager, next, jumper',
  hideOnSinglePage: false,
  loading: false,
  skeletonRows: 5
})

const emit = defineEmits([
  'select',
  'select-all',
  'selection-change',
  'cell-mouse-enter',
  'cell-mouse-leave',
  'cell-click',
  'cell-dblclick',
  'row-click',
  'row-contextmenu',
  'row-dblclick',
  'header-click',
  'header-contextmenu',
  'sort-change',
  'filter-change',
  'current-change',
  'header-dragend',
  'expand-change',
  'size-change',
  'current-page-change'
])

// 响应式功能
const { isMobile, isTablet, currentBreakpoint } = useResponsive()

// 引用
const tableRef = ref()

// 响应式状态
const currentPage = ref(props.currentPage)
const pageSize = ref(props.pageSize)

// 计算属性
const containerClasses = computed(() => [
  'responsive-table',
  `breakpoint-${currentBreakpoint.value}`,
  {
    'mobile-view': isMobile.value,
    'tablet-view': isTablet.value,
    'card-view': isMobile.value && props.useCardView,
    'table-view': !isMobile.value || !props.useCardView
  }
])

const visibleColumns = computed(() => {
  if (isMobile.value) {
    return props.columns
      .filter(col => !col.hideOnMobile)
      .sort((a, b) => (a.mobileOrder || 0) - (b.mobileOrder || 0))
  }
  return props.columns
})

const tableHeight = computed(() => {
  if (isMobile.value) return undefined
  return props.height
})

const tableSize = computed(() => {
  if (isMobile.value) return 'small'
  if (isTablet.value) return 'default'
  return props.size
})

const paginationSize = computed(() => {
  if (isMobile.value) return 'small'
  return 'default'
})

const paginationDisabled = computed(() => props.loading)

// 方法
const getRowKey = (row: any, index: number) => {
  if (typeof props.rowKey === 'function') {
    return props.rowKey(row)
  }
  if (typeof props.rowKey === 'string') {
    return row[props.rowKey]
  }
  return index
}

const getCardTitle = (item: any) => {
  return item[props.cardTitleProp] || '未命名'
}

const getFieldValue = (item: any, prop: string) => {
  return prop.split('.').reduce((obj, key) => obj?.[key], item)
}

const formatFieldValue = (item: any, column: Column) => {
  const value = getFieldValue(item, column.prop)
  if (column.formatter) {
    return column.formatter(item, column, value)
  }
  return value
}

const getFieldClass = (column: Column, item: any) => {
  const value = getFieldValue(item, column.prop)
  const classes = []
  
  // 数字类型的样式
  if (typeof value === 'number') {
    classes.push('number-field')
    if (value > 0) classes.push('positive')
    else if (value < 0) classes.push('negative')
    else classes.push('neutral')
  }
  
  // 状态类型的样式
  if (column.prop.includes('status')) {
    classes.push('status-field', `status-${value}`)
  }
  
  return classes
}

const getColumnWidth = (column: Column) => {
  if (isMobile.value) return undefined
  return column.width
}

// 事件处理
const handleSelect = (...args: any[]) => emit('select', ...args)
const handleSelectAll = (...args: any[]) => emit('select-all', ...args)
const handleSelectionChange = (...args: any[]) => emit('selection-change', ...args)
const handleCellMouseEnter = (...args: any[]) => emit('cell-mouse-enter', ...args)
const handleCellMouseLeave = (...args: any[]) => emit('cell-mouse-leave', ...args)
const handleCellClick = (...args: any[]) => emit('cell-click', ...args)
const handleCellDblclick = (...args: any[]) => emit('cell-dblclick', ...args)
const handleRowClick = (...args: any[]) => emit('row-click', ...args)
const handleRowContextmenu = (...args: any[]) => emit('row-contextmenu', ...args)
const handleRowDblclick = (...args: any[]) => emit('row-dblclick', ...args)
const handleHeaderClick = (...args: any[]) => emit('header-click', ...args)
const handleHeaderContextmenu = (...args: any[]) => emit('header-contextmenu', ...args)
const handleSortChange = (...args: any[]) => emit('sort-change', ...args)
const handleFilterChange = (...args: any[]) => emit('filter-change', ...args)
const handleCurrentChange = (...args: any[]) => emit('current-change', ...args)
const handleHeaderDragend = (...args: any[]) => emit('header-dragend', ...args)
const handleExpandChange = (...args: any[]) => emit('expand-change', ...args)

const handleSizeChange = (size: number) => {
  pageSize.value = size
  emit('size-change', size)
}

const handleCurrentPageChange = (page: number) => {
  currentPage.value = page
  emit('current-page-change', page)
}

// 公开方法
const clearSelection = () => tableRef.value?.clearSelection()
const toggleRowSelection = (row: any, selected?: boolean) => 
  tableRef.value?.toggleRowSelection(row, selected)
const toggleAllSelection = () => tableRef.value?.toggleAllSelection()
const toggleRowExpansion = (row: any, expanded?: boolean) => 
  tableRef.value?.toggleRowExpansion(row, expanded)
const setCurrentRow = (row: any) => tableRef.value?.setCurrentRow(row)
const clearSort = () => tableRef.value?.clearSort()
const clearFilter = (columnKeys?: string[]) => tableRef.value?.clearFilter(columnKeys)
const doLayout = () => tableRef.value?.doLayout()
const sort = (prop: string, order: string) => tableRef.value?.sort(prop, order)

defineExpose({
  clearSelection,
  toggleRowSelection,
  toggleAllSelection,
  toggleRowExpansion,
  setCurrentRow,
  clearSort,
  clearFilter,
  doLayout,
  sort
})
</script>

<style lang="scss" scoped>
.responsive-table-container {
  position: relative;
  
  &.mobile-view {
    .desktop-table-view {
      display: none;
    }
  }
  
  &.table-view {
    .mobile-card-view {
      display: none;
    }
  }
}

// 移动端卡片视图
.mobile-card-view {
  .mobile-card {
    background: var(--el-bg-color);
    border: 1px solid var(--el-border-color-lighter);
    border-radius: 8px;
    margin-bottom: 12px;
    padding: 16px;
    cursor: pointer;
    transition: all 0.3s ease;
    
    &:hover {
      border-color: var(--el-color-primary-light-7);
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
    
    &:last-child {
      margin-bottom: 0;
    }
  }
  
  .card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--el-border-color-lighter);
    
    .card-title {
      font-size: 16px;
      font-weight: 600;
      color: var(--el-text-color-primary);
    }
    
    .card-actions {
      display: flex;
      gap: 8px;
    }
  }
  
  .card-content {
    .card-field {
      display: flex;
      align-items: center;
      margin-bottom: 8px;
      
      &:last-child {
        margin-bottom: 0;
      }
      
      .field-label {
        flex: 0 0 80px;
        font-size: 13px;
        color: var(--el-text-color-secondary);
        margin-right: 12px;
      }
      
      .field-value {
        flex: 1;
        font-size: 14px;
        color: var(--el-text-color-primary);
        
        &.number-field {
          font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
          font-weight: 600;
          
          &.positive {
            color: var(--el-color-success);
          }
          
          &.negative {
            color: var(--el-color-danger);
          }
          
          &.neutral {
            color: var(--el-text-color-primary);
          }
        }
        
        &.status-field {
          &.status-active {
            color: var(--el-color-success);
          }
          
          &.status-inactive {
            color: var(--el-color-info);
          }
          
          &.status-error {
            color: var(--el-color-danger);
          }
          
          &.status-warning {
            color: var(--el-color-warning);
          }
        }
      }
    }
  }
  
  .empty-state {
    padding: 40px 20px;
    text-align: center;
  }
}

// 桌面端表格视图
.desktop-table-view {
  :deep(.el-table) {
    .number-field {
      font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
      font-weight: 600;
      
      &.positive {
        color: var(--el-color-success);
      }
      
      &.negative {
        color: var(--el-color-danger);
      }
      
      &.neutral {
        color: var(--el-text-color-primary);
      }
    }
    
    .status-field {
      &.status-active {
        color: var(--el-color-success);
      }
      
      &.status-inactive {
        color: var(--el-color-info);
      }
      
      &.status-error {
        color: var(--el-color-danger);
      }
      
      &.status-warning {
        color: var(--el-color-warning);
      }
    }
  }
}

// 分页
.table-pagination {
  margin-top: 16px;
  display: flex;
  justify-content: center;
  
  :deep(.el-pagination) {
    .el-pagination__total,
    .el-pagination__sizes,
    .el-pagination__jump {
      @media (max-width: 768px) {
        display: none;
      }
    }
  }
}

// 加载状态
.table-loading {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.9);
  z-index: 10;
  padding: 20px;
}

// 平板优化
.tablet-view {
  .mobile-card-view {
    .mobile-card {
      padding: 20px;
      margin-bottom: 16px;
    }
    
    .card-field {
      .field-label {
        flex: 0 0 100px;
      }
    }
  }
}

// 响应式断点优化
@media (max-width: 480px) {
  .mobile-card-view {
    .mobile-card {
      padding: 12px;
      margin-bottom: 8px;
    }
    
    .card-header {
      margin-bottom: 8px;
      
      .card-title {
        font-size: 14px;
      }
    }
    
    .card-field {
      flex-direction: column;
      align-items: flex-start;
      margin-bottom: 6px;
      
      .field-label {
        flex: none;
        margin-right: 0;
        margin-bottom: 2px;
        font-size: 12px;
      }
      
      .field-value {
        font-size: 13px;
      }
    }
  }
  
  .table-pagination {
    margin-top: 12px;
  }
}

// 暗色主题优化
.dark {
  .mobile-card-view {
    .mobile-card {
      &:hover {
        border-color: var(--el-color-primary-light-3);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
      }
    }
  }
  
  .table-loading {
    background: rgba(0, 0, 0, 0.9);
  }
}
</style>