<template>
  <div class="task-manager">
    <div class="manager-header">
      <h3>回测任务管理</h3>
      <div class="header-actions">
        <el-button 
          type="primary" 
          icon="el-icon-refresh"
          @click="refreshTasks"
          :loading="loading"
        >
          刷新
        </el-button>
        <el-button 
          type="success" 
          icon="el-icon-data-analysis"
          @click="showQueueStats = true"
        >
          队列统计
        </el-button>
        <el-button 
          type="info" 
          icon="el-icon-time"
          @click="showTaskHistory = true"
        >
          历史记录
        </el-button>
      </div>
    </div>

    <!-- 队列状态概览 -->
    <div class="queue-overview" v-if="queueStats">
      <el-row :gutter="20">
        <el-col :span="6">
          <div class="stat-card pending">
            <div class="stat-icon">
              <el-icon><Clock /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ queueStats.pending_count }}</div>
              <div class="stat-label">等待中</div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card running">
            <div class="stat-icon">
              <el-icon><Loading /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ queueStats.running_count }}</div>
              <div class="stat-label">运行中</div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card completed">
            <div class="stat-icon">
              <el-icon><Check /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ queueStats.completed_count }}</div>
              <div class="stat-label">已完成</div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card failed">
            <div class="stat-icon">
              <el-icon><Close /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ queueStats.failed_count }}</div>
              <div class="stat-label">失败</div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 任务列表 -->
    <div class="task-list">
      <div class="list-header">
        <div class="filter-controls">
          <el-select
            v-model="statusFilter"
            placeholder="状态筛选"
            clearable
            @change="handleStatusFilter"
          >
            <el-option label="全部" value="" />
            <el-option label="等待中" value="pending" />
            <el-option label="运行中" value="running" />
            <el-option label="已完成" value="completed" />
            <el-option label="失败" value="failed" />
            <el-option label="已暂停" value="paused" />
            <el-option label="已取消" value="cancelled" />
          </el-select>
          <el-input
            v-model="searchKeyword"
            placeholder="搜索任务..."
            prefix-icon="el-icon-search"
            clearable
            @input="handleSearch"
            style="width: 200px; margin-left: 10px;"
          />
        </div>
        <div class="list-actions">
          <el-button 
            size="small"
            @click="pauseAllTasks"
            :disabled="!hasRunningTasks"
          >
            暂停全部
          </el-button>
          <el-button 
            size="small"
            @click="resumeAllTasks"
            :disabled="!hasPausedTasks"
          >
            恢复全部
          </el-button>
        </div>
      </div>

      <el-table
        :data="filteredTasks"
        v-loading="loading"
        style="width: 100%"
        :default-sort="{ prop: 'created_at', order: 'descending' }"
      >
        <el-table-column prop="id" label="任务ID" width="120">
          <template #default="scope">
            <el-tooltip :content="scope.row.id" placement="top">
              <span class="task-id">{{ scope.row.id.substring(0, 8) }}...</span>
            </el-tooltip>
          </template>
        </el-table-column>
        
        <el-table-column prop="backtest_name" label="回测名称" min-width="150">
          <template #default="scope">
            <el-link 
              type="primary" 
              @click="viewBacktest(scope.row.backtest_id)"
            >
              {{ scope.row.backtest_name || `回测 ${scope.row.backtest_id}` }}
            </el-link>
          </template>
        </el-table-column>
        
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)" size="small">
              {{ getStatusText(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="priority" label="优先级" width="80">
          <template #default="scope">
            <el-tag 
              :type="getPriorityType(scope.row.priority)" 
              size="small"
              effect="plain"
            >
              {{ getPriorityText(scope.row.priority) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="progress" label="进度" width="120">
          <template #default="scope">
            <el-progress 
              :percentage="scope.row.progress" 
              :status="getProgressStatus(scope.row.status)"
              :stroke-width="6"
            />
          </template>
        </el-table-column>
        
        <el-table-column prop="created_at" label="创建时间" width="160" sortable>
          <template #default="scope">
            {{ formatDateTime(scope.row.created_at) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="duration" label="执行时间" width="100">
          <template #default="scope">
            {{ formatDuration(scope.row) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="scope">
            <div class="task-actions">
              <el-button
                v-if="scope.row.status === 'running'"
                size="small"
                type="warning"
                @click="pauseTask(scope.row.id)"
              >
                暂停
              </el-button>
              <el-button
                v-if="scope.row.status === 'paused'"
                size="small"
                type="success"
                @click="resumeTask(scope.row.id)"
              >
                恢复
              </el-button>
              <el-button
                v-if="['running', 'paused', 'pending'].includes(scope.row.status)"
                size="small"
                type="danger"
                @click="stopTask(scope.row.id)"
              >
                停止
              </el-button>
              <el-button
                v-if="['failed', 'cancelled'].includes(scope.row.status)"
                size="small"
                type="primary"
                @click="restartTask(scope.row.id)"
              >
                重启
              </el-button>
              <el-button
                size="small"
                @click="viewTaskDetails(scope.row)"
              >
                详情
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Clock, Loading, Check, Close } from '@element-plus/icons-vue'
import { backtestApi } from '@/api/backtest'
import { useWebSocket } from '@/composables/useWebSocket'

export default {
  name: 'BacktestTaskManager',
  components: {
    Clock,
    Loading,
    Check,
    Close
  },
  setup() {
    const loading = ref(false)
    const tasks = ref([])
    const queueStats = ref(null)
    const statusFilter = ref('')
    const searchKeyword = ref('')
    const showQueueStats = ref(false)
    const showTaskHistory = ref(false)

    // WebSocket连接
    const { connect, disconnect, isConnected } = useWebSocket()

    // 过滤后的任务列表
    const filteredTasks = computed(() => {
      let result = tasks.value

      // 状态筛选
      if (statusFilter.value) {
        result = result.filter(task => task.status === statusFilter.value)
      }

      // 关键词搜索
      if (searchKeyword.value) {
        const keyword = searchKeyword.value.toLowerCase()
        result = result.filter(task => 
          task.id.toLowerCase().includes(keyword) ||
          (task.backtest_name && task.backtest_name.toLowerCase().includes(keyword))
        )
      }

      return result
    })

    // 是否有运行中的任务
    const hasRunningTasks = computed(() => {
      return tasks.value.some(task => task.status === 'running')
    })

    // 是否有暂停的任务
    const hasPausedTasks = computed(() => {
      return tasks.value.some(task => task.status === 'paused')
    })

    // 加载任务列表
    const loadTasks = async () => {
      loading.value = true
      try {
        const response = await backtestApi.getUserTasks()
        tasks.value = response.data || []
      } catch (error) {
        console.error('加载任务列表失败:', error)
        ElMessage.error('加载任务列表失败')
      } finally {
        loading.value = false
      }
    }

    // 加载队列统计
    const loadQueueStats = async () => {
      try {
        const response = await backtestApi.getQueueStatistics()
        queueStats.value = response.data
      } catch (error) {
        console.error('加载队列统计失败:', error)
      }
    }

    // 刷新任务
    const refreshTasks = async () => {
      await Promise.all([loadTasks(), loadQueueStats()])
    }

    // 暂停任务
    const pauseTask = async (taskId) => {
      try {
        await backtestApi.controlTask(taskId, { action: 'pause' })
        ElMessage.success('任务已暂停')
        await refreshTasks()
      } catch (error) {
        ElMessage.error('暂停任务失败: ' + error.message)
      }
    }

    // 恢复任务
    const resumeTask = async (taskId) => {
      try {
        await backtestApi.controlTask(taskId, { action: 'resume' })
        ElMessage.success('任务已恢复')
        await refreshTasks()
      } catch (error) {
        ElMessage.error('恢复任务失败: ' + error.message)
      }
    }

    // 停止任务
    const stopTask = async (taskId) => {
      try {
        await ElMessageBox.confirm('确定要停止此任务吗？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })

        await backtestApi.controlTask(taskId, { action: 'stop' })
        ElMessage.success('任务已停止')
        await refreshTasks()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('停止任务失败: ' + error.message)
        }
      }
    }

    // 重启任务
    const restartTask = async (taskId) => {
      try {
        await backtestApi.controlTask(taskId, { action: 'restart' })
        ElMessage.success('任务已重启')
        await refreshTasks()
      } catch (error) {
        ElMessage.error('重启任务失败: ' + error.message)
      }
    }

    // 暂停全部任务
    const pauseAllTasks = async () => {
      try {
        await ElMessageBox.confirm('确定要暂停所有运行中的任务吗？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })

        const runningTasks = tasks.value.filter(task => task.status === 'running')
        const promises = runningTasks.map(task => 
          backtestApi.controlTask(task.id, { action: 'pause' })
        )

        await Promise.all(promises)
        ElMessage.success(`已暂停 ${runningTasks.length} 个任务`)
        await refreshTasks()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('暂停任务失败: ' + error.message)
        }
      }
    }

    // 恢复全部任务
    const resumeAllTasks = async () => {
      try {
        const pausedTasks = tasks.value.filter(task => task.status === 'paused')
        const promises = pausedTasks.map(task => 
          backtestApi.controlTask(task.id, { action: 'resume' })
        )

        await Promise.all(promises)
        ElMessage.success(`已恢复 ${pausedTasks.length} 个任务`)
        await refreshTasks()
      } catch (error) {
        ElMessage.error('恢复任务失败: ' + error.message)
      }
    }

    // 查看回测
    const viewBacktest = (backtestId) => {
      // 导航到回测详情页面
      console.log('查看回测:', backtestId)
    }

    // 查看任务详情
    const viewTaskDetails = (task) => {
      // 显示任务详情对话框
      console.log('查看任务详情:', task)
    }

    // 处理状态筛选
    const handleStatusFilter = () => {
      // 筛选逻辑在 computed 中处理
    }

    // 处理搜索
    const handleSearch = () => {
      // 搜索逻辑在 computed 中处理
    }

    // 获取状态类型
    const getStatusType = (status) => {
      const typeMap = {
        'pending': 'info',
        'running': 'warning',
        'completed': 'success',
        'failed': 'danger',
        'paused': 'warning',
        'cancelled': 'info'
      }
      return typeMap[status] || 'info'
    }

    // 获取状态文本
    const getStatusText = (status) => {
      const textMap = {
        'pending': '等待中',
        'running': '运行中',
        'completed': '已完成',
        'failed': '失败',
        'paused': '已暂停',
        'cancelled': '已取消'
      }
      return textMap[status] || status
    }

    // 获取优先级类型
    const getPriorityType = (priority) => {
      const typeMap = {
        1: 'info',     // 低
        2: '',         // 普通
        3: 'warning',  // 高
        4: 'danger'    // 紧急
      }
      return typeMap[priority] || ''
    }

    // 获取优先级文本
    const getPriorityText = (priority) => {
      const textMap = {
        1: '低',
        2: '普通',
        3: '高',
        4: '紧急'
      }
      return textMap[priority] || '普通'
    }

    // 获取进度状态
    const getProgressStatus = (status) => {
      if (status === 'completed') return 'success'
      if (status === 'failed') return 'exception'
      return null
    }

    // 格式化日期时间
    const formatDateTime = (dateStr) => {
      if (!dateStr) return '-'
      return new Date(dateStr).toLocaleString('zh-CN')
    }

    // 格式化执行时间
    const formatDuration = (task) => {
      if (task.actual_duration) {
        return formatSeconds(task.actual_duration)
      }
      if (task.started_at && task.status === 'running') {
        const elapsed = Math.floor((Date.now() - new Date(task.started_at).getTime()) / 1000)
        return formatSeconds(elapsed)
      }
      if (task.estimated_duration) {
        return `~${formatSeconds(task.estimated_duration)}`
      }
      return '-'
    }

    // 格式化秒数
    const formatSeconds = (seconds) => {
      if (seconds < 60) return `${seconds}秒`
      if (seconds < 3600) return `${Math.floor(seconds / 60)}分${seconds % 60}秒`
      return `${Math.floor(seconds / 3600)}时${Math.floor((seconds % 3600) / 60)}分`
    }

    // WebSocket消息处理
    const handleWebSocketMessage = (message) => {
      const data = JSON.parse(message.data)
      
      if (data.type === 'backtest_progress') {
        // 更新任务进度
        const task = tasks.value.find(t => t.id === data.task_id)
        if (task) {
          task.progress = data.progress
          task.status = data.status
        }
      } else if (data.type === 'backtest_completed' || data.type === 'backtest_failed') {
        // 刷新任务列表
        refreshTasks()
      }
    }

    onMounted(async () => {
      await refreshTasks()
      
      // 建立WebSocket连接
      connect(handleWebSocketMessage)
      
      // 定期刷新
      const interval = setInterval(refreshTasks, 30000) // 30秒刷新一次
      
      onUnmounted(() => {
        clearInterval(interval)
        disconnect()
      })
    })

    return {
      loading,
      tasks,
      queueStats,
      statusFilter,
      searchKeyword,
      showQueueStats,
      showTaskHistory,
      filteredTasks,
      hasRunningTasks,
      hasPausedTasks,
      refreshTasks,
      pauseTask,
      resumeTask,
      stopTask,
      restartTask,
      pauseAllTasks,
      resumeAllTasks,
      viewBacktest,
      viewTaskDetails,
      handleStatusFilter,
      handleSearch,
      getStatusType,
      getStatusText,
      getPriorityType,
      getPriorityText,
      getProgressStatus,
      formatDateTime,
      formatDuration
    }
  }
}
</script>