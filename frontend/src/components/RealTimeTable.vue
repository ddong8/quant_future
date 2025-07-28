<template>
  <div class="realtime-table">
    <div class="table-header">
      <div class="table-title">
        <span>{{ title }}</span>
        <el-tag v-if="connected" type="success" size="small">实时</el-tag>
        <el-tag v-else type="danger" size="small">离线</el-tag>
      </div>
      
      <div class="table-controls">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索..."
          size="small"
          style="width: 200px"
          clearable
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        
        <el-button 
          size="small" 
          :icon="autoUpdate ? 'VideoPause' : 'VideoPlay'"
          @click="toggleAutoUpdate"
        >
          {{ autoUpdate ? '暂停' : '开始' }}
        </el-button>
        
        <el-button 
          size="small" 
          :icon="'Refresh'"
          @click="refreshData"
          :loading="loading"
        >
          刷新
        </el-button>
      </div>
    </div>
    
    <el-table
      :data="filteredData"
      :loading="loading"
      :height="height"
      stripe
      @row-click="handleRowClick"
      @selection-change="handleSelectionChange"
    >
      <el-table-column
        v-if="selectable"
        type="selection"
        width="55"
      />
      
      <el-table-column
        v-for="column in columns"
        :key="column.prop"
        :prop="column.prop"
        :label="column.label"
        :width="column.width"
        :min-width="column.minWidth"
        :sortable="column.sortable"
        :formatter="column.formatter"
        :show-overflow-tooltip="column.showOverflowTooltip !== false"
      >
        <template v-if="column.slot" #default="scope">
          <slot :name="column.slot" :row="scope.row" :column="column" :index="scope.$index" />
        </template>
        
        <template v-else-if="column.type === 'price'" #default="{ row }">
          <span 
            class="price-cell"
            :class="getPriceChangeClass(row[column.prop], row[column.compareProp || 'prev_price'])"
          >
            {{ formatPrice(row[column.prop]) }}
          </span>
        </template>
        
        <template v-else-if="column.type === 'change'" #default="{ row }">
          <span 
            class="change-cell"
            :class="getPriceChangeClass(row[column.prop], 0)"
          >
            {{ row[column.prop] >= 0 ? '+' : '' }}{{ formatPrice(row[column.prop]) }}
          </span>
        </template>
        
        <template v-else-if="column.type === 'percent'" #default="{ row }">
          <span 
            class="percent-cell"
            :class="getPriceChangeClass(row[column.prop], 0)"
          >
            {{ row[column.prop] >= 0 ? '+' : '' }}{{ row[column.prop].toFixed(2) }}%
          </span>
        </template>
        
        <template v-else-if="column.type === 'volume'" #default="{ row }">
          <span class="volume-cell">
            {{ formatVolume(row[column.prop]) }}
          </span>
        </template>
        
        <template v-else-if="column.type === 'time'" #default="{ row }">
          <span class="time-cell">
            {{ formatTime(row[column.prop]) }}
          </span>
        </template>
        
        <template v-else-if="column.type === 'status'" #default="{ row }">
          <el-tag 
            :type="getStatusType(row[column.prop])" 
            size="small"
          >
            {{ getStatusText(row[column.prop]) }}
          </el-tag>
        </template>
      </el-table-column>
      
      <el-table-column
        v-if="showActions"
        label="操作"
        width="120"
        fixed="right"
      >
        <template #default="{ row, $index }">
          <slot name="actions" :row="row" :index="$index">
            <el-button size="small" type="primary" @click="handleAction('view', row)">
              查看
            </el-button>
          </slot>
        </template>
      </el-table-column>
    </el-table>
    
    <div v-if="showPagination" class="table-pagination">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="totalCount"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { useTradingWebSocket } from '@/utils/websocket'
import type { WebSocketMessage } from '@/utils/websocket'
import dayjs from 'dayjs'

interface TableColumn {
  prop: string
  label: string
  width?: number
  minWidth?: number
  sortable?: boolean
  formatter?: (row: any, column: any, cellValue: any, index: number) => string
  showOverflowTooltip?: boolean
  type?: 'price' | 'change' | 'percent' | 'volume' | 'time' | 'status'
  compareProp?: string
  slot?: string
}

interface Props {
  title?: string
  columns: TableColumn[]
  data?: any[]
  height?: number | string
  selectable?: boolean
  showActions?: boolean
  showPagination?: boolean
  autoStart?: boolean
  dataSource?: 'orders' | 'positions' | 'account' | 'custom'
}

const props = withDefaults(defineProps<Props>(), {
  title: '实时数据',
  data: () => [],
  height: 400,
  selectable: false,
  showActions: false,
  showPagination: false,
  autoStart: true,
  dataSource: 'custom'
})

const emit = defineEmits<{
  rowClick: [row: any]
  selectionChange: [selection: any[]]
  action: [action: string, row: any]
  dataUpdate: [data: any[]]
}>()

// 响应式数据
const loading = ref(false)
const autoUpdate = ref(props.autoStart)
const searchKeyword = ref('')
const tableData = ref<any[]>(props.data || [])
const currentPage = ref(1)
const pageSize = ref(20)
const totalCount = ref(0)

// WebSocket连接
const { ws, subscribeOrders, subscribePositions, subscribeAccount } = useTradingWebSocket()
const connected = computed(() => ws.connected.value)

// 过滤后的数据
const filteredData = computed(() => {
  let data = tableData.value
  
  // 搜索过滤
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    data = data.filter(row => {
      return props.columns.some(column => {
        const value = row[column.prop]
        return value && value.toString().toLowerCase().includes(keyword)
      })
    })
  }
  
  // 分页
  if (props.showPagination) {
    const start = (currentPage.value - 1) * pageSize.value
    const end = start + pageSize.value
    totalCount.value = data.length
    return data.slice(start, end)
  }
  
  return data
})

// 格式化价格
const formatPrice = (price: number) => {
  if (typeof price !== 'number') return '-'
  return new Intl.NumberFormat('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(price)
}

// 格式化成交量
const formatVolume = (volume: number) => {
  if (typeof volume !== 'number') return '-'
  if (volume >= 10000) {
    return `${(volume / 10000).toFixed(1)}万`
  }
  return volume.toString()
}

// 格式化时间
const formatTime = (time: string | Date) => {
  if (!time) return '-'
  return dayjs(time).format('HH:mm:ss')
}

// 获取价格变化样式类
const getPriceChangeClass = (current: number, previous: number) => {
  if (typeof current !== 'number' || typeof previous !== 'number') return ''
  if (current > previous) return 'price-up'
  if (current < previous) return 'price-down'
  return 'price-neutral'
}

// 获取状态类型
const getStatusType = (status: string) => {
  const statusMap: Record<string, string> = {
    pending: 'warning',
    filled: 'success',
    cancelled: 'info',
    rejected: 'danger',
    active: 'success',
    inactive: 'danger'
  }
  return statusMap[status] || 'info'
}

// 获取状态文本
const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    pending: '待成交',
    filled: '已成交',
    cancelled: '已撤销',
    rejected: '已拒绝',
    active: '活跃',
    inactive: '非活跃'
  }
  return statusMap[status] || status
}

// 切换自动更新
const toggleAutoUpdate = () => {
  autoUpdate.value = !autoUpdate.value
  if (autoUpdate.value) {
    startRealTimeUpdate()
  } else {
    stopRealTimeUpdate()
  }
}

// 刷新数据
const refreshData = async () => {
  loading.value = true
  try {
    // 这里可以调用API刷新数据
    await new Promise(resolve => setTimeout(resolve, 1000)) // 模拟加载
  } finally {
    loading.value = false
  }
}

// 开始实时更新
const startRealTimeUpdate = () => {
  if (!ws.connected.value) {
    ws.connect()
  }
  
  // 根据数据源订阅相应的数据
  switch (props.dataSource) {
    case 'orders':
      subscribeOrders()
      break
    case 'positions':
      subscribePositions()
      break
    case 'account':
      subscribeAccount()
      break
  }
}

// 停止实时更新
const stopRealTimeUpdate = () => {
  // 取消订阅
  ws.unsubscribe('orders')
  ws.unsubscribe('positions')
  ws.unsubscribe('account')
}

// 处理WebSocket消息
const handleWebSocketMessage = (message: WebSocketMessage) => {
  if (!autoUpdate.value) return
  
  switch (message.type) {
    case 'orders':
      if (props.dataSource === 'orders') {
        tableData.value = message.data
        emit('dataUpdate', message.data)
      }
      break
    case 'positions':
      if (props.dataSource === 'positions') {
        tableData.value = message.data
        emit('dataUpdate', message.data)
      }
      break
    case 'account':
      if (props.dataSource === 'account') {
        tableData.value = [message.data] // 账户数据通常是单个对象
        emit('dataUpdate', [message.data])
      }
      break
  }
}

// 处理行点击
const handleRowClick = (row: any) => {
  emit('rowClick', row)
}

// 处理选择变化
const handleSelectionChange = (selection: any[]) => {
  emit('selectionChange', selection)
}

// 处理操作
const handleAction = (action: string, row: any) => {
  emit('action', action, row)
}

// 处理分页大小变化
const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
}

// 处理当前页变化
const handleCurrentChange = (page: number) => {
  currentPage.value = page
}

// 监听WebSocket消息
watch(() => ws.lastMessage.value, (message) => {
  if (message) {
    handleWebSocketMessage(message)
  }
})

// 监听数据变化
watch(() => props.data, (newData) => {
  if (newData) {
    tableData.value = newData
  }
}, { deep: true, immediate: true })

// 生命周期
onMounted(() => {
  if (props.autoStart && props.dataSource !== 'custom') {
    startRealTimeUpdate()
  }
})

onUnmounted(() => {
  stopRealTimeUpdate()
})
</script>

<style lang="scss" scoped>
.realtime-table {
  border: 1px solid var(--el-border-color-light);
  border-radius: var(--el-border-radius-base);
  overflow: hidden;
  
  .table-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    background: var(--el-bg-color-page);
    border-bottom: 1px solid var(--el-border-color-lighter);
    
    .table-title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: 500;
      color: var(--el-text-color-primary);
    }
    
    .table-controls {
      display: flex;
      align-items: center;
      gap: 12px;
    }
  }
  
  .table-pagination {
    padding: 16px;
    background: var(--el-bg-color-page);
    border-top: 1px solid var(--el-border-color-lighter);
    display: flex;
    justify-content: center;
  }
}

// 表格单元格样式
:deep(.el-table) {
  .price-cell,
  .change-cell,
  .percent-cell {
    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
    font-weight: 600;
    
    &.price-up {
      color: var(--el-color-success);
    }
    
    &.price-down {
      color: var(--el-color-danger);
    }
    
    &.price-neutral {
      color: var(--el-text-color-primary);
    }
  }
  
  .volume-cell {
    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
    color: var(--el-text-color-secondary);
  }
  
  .time-cell {
    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
    color: var(--el-text-color-secondary);
    font-size: 12px;
  }
}

// 响应式设计
@media (max-width: 768px) {
  .realtime-table {
    .table-header {
      flex-direction: column;
      gap: 12px;
      align-items: stretch;
      
      .table-controls {
        justify-content: center;
        flex-wrap: wrap;
      }
    }
  }
}
</style>