<template>
  <div class="strategy-log-viewer">
    <!-- 工具栏 -->
    <div class="log-toolbar">
      <div class="toolbar-left">
        <el-select v-model="filters.level" placeholder="日志级别" size="small" style="width: 120px">
          <el-option label="全部" value="" />
          <el-option label="DEBUG" value="DEBUG" />
          <el-option label="INFO" value="INFO" />
          <el-option label="WARNING" value="WARNING" />
          <el-option label="ERROR" value="ERROR" />
        </el-select>
        
        <el-date-picker
          v-model="filters.dateRange"
          type="datetimerange"
          range-separator="至"
          start-placeholder="开始时间"
          end-placeholder="结束时间"
          size="small"
          style="width: 300px"
          @change="handleDateRangeChange"
        />
        
        <el-input
          v-model="filters.keyword"
          placeholder="搜索关键词"
          size="small"
          style="width: 200px"
          clearable
          @keyup.enter="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        
        <el-button size="small" type="primary" @click="handleSearch">
          <el-icon><Search /></el-icon>
          搜索
        </el-button>
      </div>
      
      <div class="toolbar-right">
        <el-button size="small" @click="handleRefresh" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        
        <el-button size="small" @click="handleClear">
          <el-icon><Delete /></el-icon>
          清空
        </el-button>
        
        <el-button size="small" @click="handleExport">
          <el-icon><Download /></el-icon>
          导出
        </el-button>
        
        <el-switch
          v-model="autoRefresh"
          active-text="自动刷新"
          inactive-text="手动刷新"
          size="small"
          @change="handleAutoRefreshChange"
        />
      </div>
    </div>

    <!-- 日志内容 -->
    <div class="log-content" ref="logContainer">
      <div class="log-stats">
        <el-row :gutter="16">
          <el-col :span="6">
            <el-statistic title="总日志数" :value="stats.total" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="错误数" :value="stats.error" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="警告数" :value="stats.warning" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="最后更新" :value="stats.lastUpdate" />
          </el-col>
        </el-row>
      </div>

      <div class="log-list" v-loading="loading">
        <div
          v-for="log in filteredLogs"
          :key="log.id"
          :class="['log-item', `log-${log.level.toLowerCase()}`]"
        >
          <div class="log-header">
            <span class="log-time">{{ formatTime(log.timestamp) }}</span>
            <el-tag :type="getLevelTagType(log.level)" size="small">
              {{ log.level }}
            </el-tag>
            <span class="log-source" v-if="log.source">{{ log.source }}</span>
          </div>
          
          <div class="log-message">
            <span v-html="highlightKeyword(log.message)"></span>
          </div>
          
          <div class="log-metadata" v-if="log.metadata && Object.keys(log.metadata).length > 0">
            <el-collapse>
              <el-collapse-item title="详细信息" name="metadata">
                <pre class="metadata-content">{{ JSON.stringify(log.metadata, null, 2) }}</pre>
              </el-collapse-item>
            </el-collapse>
          </div>
          
          <div class="log-actions">
            <el-button text size="small" @click="copyLog(log)">
              <el-icon><DocumentCopy /></el-icon>
              复制
            </el-button>
            <el-button text size="small" @click="showLogDetail(log)">
              <el-icon><View /></el-icon>
              详情
            </el-button>
          </div>
        </div>
        
        <div v-if="!loading && filteredLogs.length === 0" class="empty-logs">
          <el-empty description="暂无日志数据" />
        </div>
      </div>

      <!-- 分页 -->
      <div class="log-pagination">
        <el-pagination
          v-model:current-page="pagination.current"
          v-model:page-size="pagination.size"
          :total="pagination.total"
          :page-sizes="[50, 100, 200, 500]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>

    <!-- 日志详情对话框 -->
    <el-dialog
      v-model="showDetailDialog"
      title="日志详情"
      width="800px"
    >
      <div v-if="selectedLog" class="log-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="时间">
            {{ formatDateTime(selectedLog.timestamp) }}
          </el-descriptions-item>
          <el-descriptions-item label="级别">
            <el-tag :type="getLevelTagType(selectedLog.level)">
              {{ selectedLog.level }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="来源" v-if="selectedLog.source">
            {{ selectedLog.source }}
          </el-descriptions-item>
          <el-descriptions-item label="线程" v-if="selectedLog.thread">
            {{ selectedLog.thread }}
          </el-descriptions-item>
          <el-descriptions-item label="消息" :span="2">
            <div class="log-message-detail">{{ selectedLog.message }}</div>
          </el-descriptions-item>
        </el-descriptions>
        
        <div v-if="selectedLog.metadata" class="log-metadata-detail">
          <h4>元数据</h4>
          <pre class="metadata-content">{{ JSON.stringify(selectedLog.metadata, null, 2) }}</pre>
        </div>
        
        <div v-if="selectedLog.stack_trace" class="log-stack-trace">
          <h4>堆栈跟踪</h4>
          <pre class="stack-trace-content">{{ selectedLog.stack_trace }}</pre>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="showDetailDialog = false">关闭</el-button>
        <el-button type="primary" @click="copyLog(selectedLog)">复制</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Search,
  Refresh,
  Delete,
  Download,
  DocumentCopy,
  View
} from '@element-plus/icons-vue'
import type { StrategyLog } from '@/types/strategy'

interface Props {
  strategyId: number
  height?: string
}

const props = withDefaults(defineProps<Props>(), {
  height: '600px'
})

// 响应式数据
const loading = ref(false)
const autoRefresh = ref(false)
const showDetailDialog = ref(false)
const selectedLog = ref<StrategyLog | null>(null)
const logContainer = ref<HTMLElement>()

let refreshTimer: NodeJS.Timeout | null = null

// 筛选条件
const filters = ref({
  level: '',
  dateRange: [],
  keyword: ''
})

// 分页
const pagination = ref({
  current: 1,
  size: 100,
  total: 0
})

// 日志数据
const logs = ref<StrategyLog[]>([])

// 统计信息
const stats = ref({
  total: 0,
  error: 0,
  warning: 0,
  lastUpdate: ''
})

// 计算属性
const filteredLogs = computed(() => {
  let result = logs.value
  
  // 级别筛选
  if (filters.value.level) {
    result = result.filter(log => log.level === filters.value.level)
  }
  
  // 关键词搜索
  if (filters.value.keyword) {
    const keyword = filters.value.keyword.toLowerCase()
    result = result.filter(log => 
      log.message.toLowerCase().includes(keyword) ||
      (log.source && log.source.toLowerCase().includes(keyword))
    )
  }
  
  return result
})

// 方法
const loadLogs = async () => {
  try {
    loading.value = true
    
    const params = {
      strategy_id: props.strategyId,
      page: pagination.value.current,
      page_size: pagination.value.size,
      level: filters.value.level,
      start_date: filters.value.dateRange[0],
      end_date: filters.value.dateRange[1],
      keyword: filters.value.keyword
    }
    
    // 调用API获取日志
    // const response = await strategyApi.getStrategyLogs(props.strategyId, params)
    // if (response.success) {
    //   logs.value = response.data.logs
    //   pagination.value.total = response.data.total
    //   updateStats()
    // }
    
    // 模拟数据
    const mockLogs: StrategyLog[] = [
      {
        id: 1,
        strategy_id: props.strategyId,
        level: 'INFO',
        message: '策略初始化完成',
        timestamp: new Date().toISOString(),
        metadata: { module: 'strategy', function: 'initialize' }
      },
      {
        id: 2,
        strategy_id: props.strategyId,
        level: 'DEBUG',
        message: '接收到新的K线数据',
        timestamp: new Date(Date.now() - 60000).toISOString(),
        metadata: { symbol: 'SHFE.cu2401', price: 72500 }
      },
      {
        id: 3,
        strategy_id: props.strategyId,
        level: 'WARNING',
        message: '持仓接近风险阈值',
        timestamp: new Date(Date.now() - 120000).toISOString(),
        metadata: { position: 0.85, threshold: 0.9 }
      },
      {
        id: 4,
        strategy_id: props.strategyId,
        level: 'ERROR',
        message: '订单提交失败',
        timestamp: new Date(Date.now() - 180000).toISOString(),
        metadata: { order_id: 'ORD001', error: 'Insufficient margin' }
      }
    ]
    
    logs.value = mockLogs
    pagination.value.total = mockLogs.length
    updateStats()
    
  } catch (error) {
    ElMessage.error('加载日志失败')
  } finally {
    loading.value = false
  }
}

const updateStats = () => {
  stats.value.total = logs.value.length
  stats.value.error = logs.value.filter(log => log.level === 'ERROR').length
  stats.value.warning = logs.value.filter(log => log.level === 'WARNING').length
  stats.value.lastUpdate = new Date().toLocaleTimeString()
}

const handleSearch = () => {
  pagination.value.current = 1
  loadLogs()
}

const handleRefresh = () => {
  loadLogs()
}

const handleClear = () => {
  logs.value = []
  stats.value = {
    total: 0,
    error: 0,
    warning: 0,
    lastUpdate: ''
  }
}

const handleExport = () => {
  // 导出日志逻辑
  const logText = logs.value.map(log => 
    `[${log.timestamp}] ${log.level}: ${log.message}`
  ).join('\n')
  
  const blob = new Blob([logText], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `strategy_${props.strategyId}_logs.txt`
  a.click()
  URL.revokeObjectURL(url)
}

const handleAutoRefreshChange = (enabled: boolean) => {
  if (enabled) {
    refreshTimer = setInterval(() => {
      loadLogs()
    }, 5000) // 每5秒刷新一次
  } else {
    if (refreshTimer) {
      clearInterval(refreshTimer)
      refreshTimer = null
    }
  }
}

const handleDateRangeChange = () => {
  handleSearch()
}

const handleSizeChange = () => {
  loadLogs()
}

const handleCurrentChange = () => {
  loadLogs()
}

const getLevelTagType = (level: string) => {
  const typeMap: Record<string, string> = {
    DEBUG: 'info',
    INFO: 'success',
    WARNING: 'warning',
    ERROR: 'danger'
  }
  return typeMap[level] || 'info'
}

const formatTime = (timestamp: string) => {
  return new Date(timestamp).toLocaleTimeString()
}

const formatDateTime = (timestamp: string) => {
  return new Date(timestamp).toLocaleString()
}

const highlightKeyword = (message: string) => {
  if (!filters.value.keyword) return message
  
  const keyword = filters.value.keyword
  const regex = new RegExp(`(${keyword})`, 'gi')
  return message.replace(regex, '<mark>$1</mark>')
}

const copyLog = (log: StrategyLog | null) => {
  if (!log) return
  
  const logText = `[${log.timestamp}] ${log.level}: ${log.message}`
  navigator.clipboard.writeText(logText).then(() => {
    ElMessage.success('日志已复制到剪贴板')
  }).catch(() => {
    ElMessage.error('复制失败')
  })
}

const showLogDetail = (log: StrategyLog) => {
  selectedLog.value = log
  showDetailDialog.value = true
}

// 监听筛选条件变化
watch(filters, () => {
  handleSearch()
}, { deep: true })

// 生命周期
onMounted(() => {
  loadLogs()
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})
</script>

<style scoped lang="scss">
.strategy-log-viewer {
  height: v-bind(height);
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  
  .log-toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    background: #f5f7fa;
    border-bottom: 1px solid #ebeef5;
    
    .toolbar-left,
    .toolbar-right {
      display: flex;
      align-items: center;
      gap: 12px;
    }
  }
  
  .log-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    
    .log-stats {
      padding: 16px;
      background: #fafbfc;
      border-bottom: 1px solid #ebeef5;
    }
    
    .log-list {
      flex: 1;
      overflow-y: auto;
      padding: 8px;
      
      .log-item {
        margin-bottom: 8px;
        padding: 12px;
        border-radius: 6px;
        border-left: 4px solid #ddd;
        background: #fff;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        
        &.log-debug {
          border-left-color: #909399;
          background: #f4f4f5;
        }
        
        &.log-info {
          border-left-color: #409eff;
          background: #ecf5ff;
        }
        
        &.log-warning {
          border-left-color: #e6a23c;
          background: #fdf6ec;
        }
        
        &.log-error {
          border-left-color: #f56c6c;
          background: #fef0f0;
        }
        
        .log-header {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 8px;
          
          .log-time {
            font-size: 12px;
            color: #909399;
            font-family: monospace;
          }
          
          .log-source {
            font-size: 12px;
            color: #606266;
            background: #f0f2f5;
            padding: 2px 6px;
            border-radius: 3px;
          }
        }
        
        .log-message {
          font-size: 14px;
          line-height: 1.5;
          color: #303133;
          margin-bottom: 8px;
          word-break: break-all;
          
          :deep(mark) {
            background: #ffeb3b;
            padding: 0 2px;
          }
        }
        
        .log-metadata {
          margin-bottom: 8px;
          
          .metadata-content {
            font-size: 12px;
            color: #606266;
            background: #f5f7fa;
            padding: 8px;
            border-radius: 4px;
            margin: 0;
            overflow-x: auto;
          }
        }
        
        .log-actions {
          display: flex;
          gap: 8px;
          opacity: 0;
          transition: opacity 0.2s;
        }
        
        &:hover .log-actions {
          opacity: 1;
        }
      }
      
      .empty-logs {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 200px;
      }
    }
    
    .log-pagination {
      padding: 16px;
      border-top: 1px solid #ebeef5;
      display: flex;
      justify-content: center;
    }
  }
}

.log-detail {
  .log-message-detail {
    font-family: monospace;
    background: #f5f7fa;
    padding: 8px;
    border-radius: 4px;
    white-space: pre-wrap;
    word-break: break-all;
  }
  
  .log-metadata-detail,
  .log-stack-trace {
    margin-top: 16px;
    
    h4 {
      margin: 0 0 8px 0;
      font-size: 14px;
      color: #303133;
    }
    
    .metadata-content,
    .stack-trace-content {
      font-size: 12px;
      color: #606266;
      background: #f5f7fa;
      padding: 12px;
      border-radius: 4px;
      margin: 0;
      overflow-x: auto;
      max-height: 300px;
      overflow-y: auto;
    }
  }
}
</style>