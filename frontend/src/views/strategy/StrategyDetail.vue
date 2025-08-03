<template>
  <div class="strategy-detail" v-loading="loading">
    <div v-if="strategy">
      <!-- 页面头部 -->
      <div class="page-header">
        <div class="header-left">
          <el-button @click="goBack" type="text" class="back-button">
            <el-icon><ArrowLeft /></el-icon>
            返回列表
          </el-button>
          <div class="header-info">
            <h2 class="strategy-title">{{ strategy.name }}</h2>
            <div class="strategy-meta">
              <StatusTag :status="strategy.status" />
              <el-tag
                v-if="strategy.is_running"
                type="success"
                effect="dark"
                style="margin-left: 8px"
              >
                运行中
              </el-tag>
              <el-tag
                v-if="strategy.is_public"
                type="info"
                effect="plain"
                style="margin-left: 8px"
              >
                公开
              </el-tag>
              <span class="version-info">v{{ strategy.version }}</span>
            </div>
          </div>
        </div>
        
        <div class="header-actions">
          <el-button @click="handleCopy">
            <el-icon><CopyDocument /></el-icon>
            复制
          </el-button>
          <el-button @click="handleEdit" type="primary">
            <el-icon><Edit /></el-icon>
            编辑
          </el-button>
          <el-dropdown @command="handleCommand">
            <el-button>
              更多操作
              <el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="start" v-if="!strategy.is_running">
                  <el-icon><VideoPlay /></el-icon>
                  启动策略
                </el-dropdown-item>
                <el-dropdown-item command="stop" v-if="strategy.is_running">
                  <el-icon><VideoPause /></el-icon>
                  停止策略
                </el-dropdown-item>
                <el-dropdown-item command="test" divided>
                  <el-icon><Cpu /></el-icon>
                  测试策略
                </el-dropdown-item>
                <el-dropdown-item command="backtest">
                  <el-icon><TrendCharts /></el-icon>
                  运行回测
                </el-dropdown-item>
                <el-dropdown-item command="export">
                  <el-icon><Download /></el-icon>
                  导出策略
                </el-dropdown-item>
                <el-dropdown-item command="delete" style="color: #f56c6c" divided>
                  <el-icon><Delete /></el-icon>
                  删除策略
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>

      <!-- 主要内容 -->
      <el-row :gutter="24">
        <!-- 左侧内容 -->
        <el-col :span="16">
          <!-- 基本信息 -->
          <el-card class="info-card" title="基本信息">
            <template #header>
              <span>基本信息</span>
            </template>
            
            <el-descriptions :column="2" border>
              <el-descriptions-item label="策略名称">
                {{ strategy.name }}
              </el-descriptions-item>
              <el-descriptions-item label="策略类型">
                {{ STRATEGY_TYPE_LABELS[strategy.strategy_type] }}
              </el-descriptions-item>
              <el-descriptions-item label="当前状态">
                <StatusTag :status="strategy.status" />
              </el-descriptions-item>
              <el-descriptions-item label="运行状态">
                <el-tag :type="strategy.is_running ? 'success' : 'info'">
                  {{ strategy.is_running ? '运行中' : '已停止' }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="编程语言">
                {{ strategy.language }}
              </el-descriptions-item>
              <el-descriptions-item label="入口函数">
                {{ strategy.entry_point }}
              </el-descriptions-item>
              <el-descriptions-item label="时间周期">
                {{ strategy.timeframe || '未设置' }}
              </el-descriptions-item>
              <el-descriptions-item label="交易标的">
                <el-tag
                  v-for="symbol in strategy.symbols"
                  :key="symbol"
                  size="small"
                  style="margin-right: 4px"
                >
                  {{ symbol }}
                </el-tag>
                <span v-if="!strategy.symbols || strategy.symbols.length === 0">
                  未设置
                </span>
              </el-descriptions-item>
              <el-descriptions-item label="创建时间">
                {{ formatDate(strategy.created_at) }}
              </el-descriptions-item>
              <el-descriptions-item label="更新时间">
                {{ formatDate(strategy.updated_at) }}
              </el-descriptions-item>
              <el-descriptions-item label="最后运行">
                {{ strategy.last_run_at ? formatDate(strategy.last_run_at) : '从未运行' }}
              </el-descriptions-item>
              <el-descriptions-item label="策略描述" :span="2">
                {{ strategy.description || '暂无描述' }}
              </el-descriptions-item>
            </el-descriptions>
          </el-card>

          <!-- 风险控制参数 -->
          <el-card class="risk-card" title="风险控制">
            <template #header>
              <span>风险控制参数</span>
            </template>
            
            <el-descriptions :column="2" border>
              <el-descriptions-item label="最大持仓规模">
                {{ strategy.max_position_size ? formatNumber(strategy.max_position_size) : '未限制' }}
              </el-descriptions-item>
              <el-descriptions-item label="最大回撤限制">
                {{ strategy.max_drawdown ? formatPercent(strategy.max_drawdown) : '未限制' }}
              </el-descriptions-item>
              <el-descriptions-item label="止损比例">
                {{ strategy.stop_loss ? formatPercent(strategy.stop_loss) : '未设置' }}
              </el-descriptions-item>
              <el-descriptions-item label="止盈比例">
                {{ strategy.take_profit ? formatPercent(strategy.take_profit) : '未设置' }}
              </el-descriptions-item>
            </el-descriptions>
          </el-card>

          <!-- 策略参数 -->
          <el-card class="params-card" title="策略参数" v-if="hasParameters">
            <template #header>
              <span>策略参数</span>
            </template>
            
            <div class="params-content">
              <el-descriptions :column="1" border>
                <el-descriptions-item
                  v-for="(value, key) in strategy.parameters"
                  :key="key"
                  :label="key"
                >
                  <code class="param-value">{{ formatParameterValue(value) }}</code>
                </el-descriptions-item>
              </el-descriptions>
            </div>
          </el-card>

          <!-- 策略代码 -->
          <el-card class="code-card" title="策略代码">
            <template #header>
              <div class="code-header">
                <span>策略代码</span>
                <div class="code-actions">
                  <el-button size="small" @click="copyCode">
                    <el-icon><CopyDocument /></el-icon>
                    复制代码
                  </el-button>
                  <el-button size="small" @click="downloadCode">
                    <el-icon><Download /></el-icon>
                    下载代码
                  </el-button>
                </div>
              </div>
            </template>
            
            <div class="code-content">
              <pre class="code-block"><code>{{ strategy.code }}</code></pre>
            </div>
          </el-card>
        </el-col>

        <!-- 右侧内容 -->
        <el-col :span="8">
          <!-- 性能统计 -->
          <el-card class="performance-card" title="性能统计">
            <template #header>
              <span>性能统计</span>
            </template>
            
            <div class="performance-metrics">
              <div class="metric-item">
                <div class="metric-value" :class="getReturnClass(strategy.total_returns)">
                  {{ formatPercent(strategy.total_returns) }}
                </div>
                <div class="metric-label">总收益率</div>
              </div>
              
              <div class="metric-item">
                <div class="metric-value">
                  {{ formatNumber(strategy.sharpe_ratio, 2) }}
                </div>
                <div class="metric-label">夏普比率</div>
              </div>
              
              <div class="metric-item">
                <div class="metric-value" :class="getReturnClass(strategy.max_drawdown_pct)">
                  {{ formatPercent(strategy.max_drawdown_pct) }}
                </div>
                <div class="metric-label">最大回撤</div>
              </div>
              
              <div class="metric-item">
                <div class="metric-value">
                  {{ formatPercent(strategy.win_rate) }}
                </div>
                <div class="metric-label">胜率</div>
              </div>
              
              <div class="metric-item">
                <div class="metric-value">
                  {{ strategy.total_trades }}
                </div>
                <div class="metric-label">总交易次数</div>
              </div>
            </div>
          </el-card>

          <!-- 版本控制 -->
          <el-card class="version-card" title="版本控制">
            <template #header>
              <div class="version-header">
                <span>版本控制</span>
                <el-dropdown @command="handleVersionCommand">
                  <el-button size="small">
                    版本操作
                    <el-icon class="el-icon--right"><ArrowDown /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="compare">
                        <el-icon><Compare /></el-icon>
                        版本比较
                      </el-dropdown-item>
                      <el-dropdown-item command="tree">
                        <el-icon><Share /></el-icon>
                        版本树
                      </el-dropdown-item>
                      <el-dropdown-item command="create">
                        <el-icon><Plus /></el-icon>
                        创建版本
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </template>
            
            <div class="version-list" v-loading="versionsLoading">
              <div
                v-for="version in strategyVersions"
                :key="version.id"
                class="version-item"
                :class="{ 'current': version.version_number === strategy.version }"
              >
                <div class="version-info">
                  <div class="version-number">
                    v{{ version.version_number }}
                    <el-tag v-if="version.version_number === strategy.version" size="small" type="success">
                      当前
                    </el-tag>
                    <el-tag v-if="version.is_major_version" size="small" type="warning" effect="plain">
                      主版本
                    </el-tag>
                  </div>
                  <div class="version-name">{{ version.version_name || '未命名版本' }}</div>
                  <div class="version-time">{{ formatDate(version.created_at) }}</div>
                </div>
                <div class="version-actions">
                  <el-button
                    size="small"
                    type="text"
                    @click="viewVersion(version)"
                  >
                    查看
                  </el-button>
                  <el-button
                    v-if="version.version_number !== strategy.version"
                    size="small"
                    type="text"
                    @click="restoreVersion(version)"
                  >
                    恢复
                  </el-button>
                </div>
              </div>
              
              <div v-if="strategyVersions.length === 0" class="no-versions">
                暂无版本历史
              </div>
            </div>
          </el-card>

          <!-- 标签 -->
          <el-card class="tags-card" title="标签" v-if="strategy.tags && strategy.tags.length > 0">
            <template #header>
              <span>标签</span>
            </template>
            
            <div class="tags-content">
              <el-tag
                v-for="tag in strategy.tags"
                :key="tag"
                style="margin-right: 8px; margin-bottom: 8px"
              >
                {{ tag }}
              </el-tag>
            </div>
          </el-card>

          <!-- 错误信息 -->
          <el-card
            class="error-card"
            title="错误信息"
            v-if="strategy.last_error"
          >
            <template #header>
              <span style="color: #f56c6c">错误信息</span>
            </template>
            
            <div class="error-content">
              <el-alert
                :title="strategy.last_error"
                type="error"
                :closable="false"
                show-icon
              />
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 空状态 -->
    <EmptyState
      v-else-if="!loading"
      type="error"
      title="策略不存在"
      description="请检查策略ID是否正确或您是否有权限访问此策略"
      :show-action="true"
      action-text="返回列表"
      @action="goBack"
    />

    <!-- 确认对话框 -->
    <ConfirmDialog
      v-model="showConfirmDialog"
      :type="confirmType"
      :title="confirmTitle"
      :content="confirmContent"
      @confirm="handleConfirm"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft, ArrowDown, Edit, CopyDocument, VideoPlay, VideoPause,
  Cpu, TrendCharts, Download, Delete, Refresh, Compare, Share, Plus
} from '@element-plus/icons-vue'

import { useStrategyStore } from '@/stores/strategy'
import { StatusTag, EmptyState, ConfirmDialog } from '@/components/common'
import {
  STRATEGY_TYPE_LABELS,
  type Strategy,
  type StrategyVersion
} from '@/types/strategy'
import { formatDate, formatNumber, formatPercent } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const strategyStore = useStrategyStore()

// 响应式数据
const versionsLoading = ref(false)
const showConfirmDialog = ref(false)
const confirmType = ref<'warning' | 'error'>('warning')
const confirmTitle = ref('')
const confirmContent = ref('')
const confirmAction = ref<() => void>(() => {})

// 计算属性
const strategyId = computed(() => parseInt(route.params.id as string))
const strategy = computed(() => strategyStore.currentStrategy)
const strategyVersions = computed(() => strategyStore.strategyVersions)
const loading = computed(() => strategyStore.loading)

const hasParameters = computed(() => {
  return strategy.value?.parameters && Object.keys(strategy.value.parameters).length > 0
})

// 方法
const goBack = () => {
  router.push('/strategy')
}

const handleEdit = () => {
  router.push(`/strategy/${strategyId.value}/edit`)
}

const handleCopy = async () => {
  if (!strategy.value) return
  
  try {
    const newName = await ElMessageBox.prompt(
      '请输入新策略名称',
      '复制策略',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputValue: `${strategy.value.name} - 副本`,
        inputValidator: (value) => {
          if (!value || !value.trim()) {
            return '策略名称不能为空'
          }
          return true
        }
      }
    )
    
    const newStrategy = await strategyStore.copyStrategy(strategyId.value, newName.value)
    if (newStrategy) {
      router.push(`/strategy/${newStrategy.id}`)
    }
  } catch (error) {
    // 用户取消操作
  }
}

const handleCommand = (command: string) => {
  if (!strategy.value) return
  
  switch (command) {
    case 'start':
      handleStartStrategy()
      break
    case 'stop':
      handleStopStrategy()
      break
    case 'test':
      handleTestStrategy()
      break
    case 'backtest':
      handleBacktest()
      break
    case 'export':
      handleExport()
      break
    case 'delete':
      handleDeleteStrategy()
      break
  }
}

const handleStartStrategy = () => {
  confirmType.value = 'warning'
  confirmTitle.value = '启动策略'
  confirmContent.value = `确定要启动策略 "${strategy.value?.name}" 吗？`
  confirmAction.value = () => {
    strategyStore.executeStrategy(strategyId.value, { action: 'start' })
  }
  showConfirmDialog.value = true
}

const handleStopStrategy = () => {
  confirmType.value = 'warning'
  confirmTitle.value = '停止策略'
  confirmContent.value = `确定要停止策略 "${strategy.value?.name}" 吗？`
  confirmAction.value = () => {
    strategyStore.executeStrategy(strategyId.value, { action: 'stop' })
  }
  showConfirmDialog.value = true
}

const handleTestStrategy = () => {
  // TODO: 实现策略测试功能
  ElMessage.info('策略测试功能开发中...')
}

const handleBacktest = () => {
  router.push(`/backtest/create?strategy_id=${strategyId.value}`)
}

const handleExport = () => {
  if (!strategy.value) return
  
  const content = `# ${strategy.value.name}\n\n${strategy.value.description || ''}\n\n\`\`\`python\n${strategy.value.code}\n\`\`\``
  const blob = new Blob([content], { type: 'text/markdown' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${strategy.value.name}.md`
  a.click()
  URL.revokeObjectURL(url)
  
  ElMessage.success('策略导出成功')
}

const handleDeleteStrategy = () => {
  confirmType.value = 'error'
  confirmTitle.value = '删除策略'
  confirmContent.value = `确定要删除策略 "${strategy.value?.name}" 吗？此操作不可恢复。`
  confirmAction.value = async () => {
    const success = await strategyStore.deleteStrategy(strategyId.value)
    if (success) {
      router.push('/strategy')
    }
  }
  showConfirmDialog.value = true
}

const handleConfirm = () => {
  confirmAction.value()
  showConfirmDialog.value = false
}

const fetchVersions = async () => {
  versionsLoading.value = true
  try {
    await strategyStore.fetchStrategyVersions(strategyId.value)
  } finally {
    versionsLoading.value = false
  }
}

const viewVersion = (version: StrategyVersion) => {
  // TODO: 实现版本查看功能
  ElMessage.info('版本查看功能开发中...')
}

const handleVersionCommand = (command: string) => {
  switch (command) {
    case 'compare':
      // 跳转到版本比较页面
      router.push(`/strategy/${strategyId.value}/versions/compare`)
      break
    case 'tree':
      // 跳转到版本树页面
      router.push(`/strategy/${strategyId.value}/versions/tree`)
      break
    case 'create':
      // 跳转到创建版本页面
      router.push(`/strategy/${strategyId.value}/versions/create`)
      break
  }
}

const restoreVersion = async (version: StrategyVersion) => {
  try {
    await ElMessageBox.confirm(
      `确定要恢复到版本 ${version.version_number} 吗？这将创建一个新的版本。`,
      '恢复版本',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await strategyStore.restoreStrategyVersion(strategyId.value, version.id)
  } catch (error) {
    // 用户取消操作
  }
}

const copyCode = async () => {
  if (!strategy.value) return
  
  try {
    await navigator.clipboard.writeText(strategy.value.code)
    ElMessage.success('代码已复制到剪贴板')
  } catch (error) {
    ElMessage.error('复制失败，请手动复制')
  }
}

const downloadCode = () => {
  if (!strategy.value) return
  
  const blob = new Blob([strategy.value.code], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${strategy.value.name}.py`
  a.click()
  URL.revokeObjectURL(url)
  
  ElMessage.success('代码下载成功')
}

const formatParameterValue = (value: any) => {
  if (typeof value === 'object') {
    return JSON.stringify(value, null, 2)
  }
  return String(value)
}

const getReturnClass = (returns: number | null | undefined) => {
  if (!returns) return 'neutral'
  if (returns > 0) return 'positive'
  if (returns < 0) return 'negative'
  return 'neutral'
}

// 生命周期
onMounted(async () => {
  await strategyStore.fetchStrategy(strategyId.value)
  await fetchVersions()
})
</script>

<style lang="scss" scoped>
.strategy-detail {
  padding: 20px;
  
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 24px;
    
    .header-left {
      .back-button {
        margin-bottom: 12px;
        color: var(--el-text-color-secondary);
        
        &:hover {
          color: var(--el-color-primary);
        }
      }
      
      .header-info {
        .strategy-title {
          margin: 0 0 8px 0;
          font-size: 24px;
          font-weight: 600;
          color: var(--el-text-color-primary);
        }
        
        .strategy-meta {
          display: flex;
          align-items: center;
          gap: 8px;
          
          .version-info {
            color: var(--el-text-color-secondary);
            font-size: 14px;
            margin-left: 8px;
          }
        }
      }
    }
    
    .header-actions {
      display: flex;
      gap: 12px;
    }
  }
  
  .el-card {
    margin-bottom: 24px;
    
    &:last-child {
      margin-bottom: 0;
    }
  }
  
  .code-card {
    .code-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      width: 100%;
    }
    
    .code-content {
      .code-block {
        background: var(--el-fill-color-light);
        border: 1px solid var(--el-border-color);
        border-radius: 4px;
        padding: 16px;
        margin: 0;
        overflow-x: auto;
        font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
        font-size: 13px;
        line-height: 1.5;
        
        code {
          background: none;
          padding: 0;
          color: var(--el-text-color-primary);
        }
      }
    }
  }
  
  .params-content {
    .param-value {
      background: var(--el-fill-color-light);
      padding: 4px 8px;
      border-radius: 4px;
      font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
      font-size: 12px;
    }
  }
  
  .performance-metrics {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
    
    .metric-item {
      text-align: center;
      padding: 16px;
      background: var(--el-fill-color-light);
      border-radius: 8px;
      
      .metric-value {
        font-size: 20px;
        font-weight: 600;
        margin-bottom: 8px;
        
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
      
      .metric-label {
        font-size: 12px;
        color: var(--el-text-color-secondary);
      }
    }
  }
  
  .version-card {
    .version-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      width: 100%;
    }
    
    .version-list {
      max-height: 300px;
      overflow-y: auto;
      
      .version-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px;
        border: 1px solid var(--el-border-color-light);
        border-radius: 4px;
        margin-bottom: 8px;
        transition: all 0.3s ease;
        
        &:hover {
          background: var(--el-fill-color-light);
        }
        
        &.current {
          border-color: var(--el-color-primary);
          background: var(--el-color-primary-light-9);
        }
        
        .version-info {
          flex: 1;
          
          .version-number {
            font-weight: 600;
            margin-bottom: 4px;
            display: flex;
            align-items: center;
            gap: 8px;
          }
          
          .version-name {
            font-size: 13px;
            color: var(--el-text-color-secondary);
            margin-bottom: 2px;
          }
          
          .version-time {
            font-size: 12px;
            color: var(--el-text-color-placeholder);
          }
        }
        
        .version-actions {
          display: flex;
          gap: 8px;
        }
      }
      
      .no-versions {
        text-align: center;
        color: var(--el-text-color-secondary);
        padding: 20px;
      }
    }
  }
  
  .tags-content {
    line-height: 2;
  }
  
  .error-content {
    :deep(.el-alert) {
      .el-alert__content {
        word-break: break-all;
      }
    }
  }
}
</style>