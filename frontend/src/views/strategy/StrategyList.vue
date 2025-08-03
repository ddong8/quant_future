<template>
  <div class="strategy-list">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h2>策略管理</h2>
        <p class="header-desc">管理和监控您的交易策略</p>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="showCreateDialog = true">
          <el-icon><Plus /></el-icon>
          创建策略
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards" v-if="strategyStats">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-value">{{ strategyStats.total_strategies }}</div>
              <div class="stat-label">总策略数</div>
            </div>
            <el-icon class="stat-icon" color="#409EFF"><Document /></el-icon>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-value">{{ strategyStats.running_strategies }}</div>
              <div class="stat-label">运行中</div>
            </div>
            <el-icon class="stat-icon" color="#67C23A"><VideoPlay /></el-icon>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-value">{{ formatPercent(strategyStats.avg_returns) }}</div>
              <div class="stat-label">平均收益率</div>
            </div>
            <el-icon class="stat-icon" color="#E6A23C"><TrendCharts /></el-icon>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-value">{{ formatNumber(strategyStats.avg_sharpe_ratio, 2) }}</div>
              <div class="stat-label">平均夏普比率</div>
            </div>
            <el-icon class="stat-icon" color="#F56C6C"><DataAnalysis /></el-icon>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 搜索和筛选 -->
    <el-card class="filter-card">
      <div class="filter-content">
        <div class="filter-left">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索策略名称或描述"
            style="width: 300px"
            clearable
            @input="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
        
        <div class="filter-right">
          <el-select
            v-model="filterStatus"
            placeholder="策略状态"
            style="width: 120px"
            clearable
            @change="handleFilter"
          >
            <el-option
              v-for="option in STRATEGY_STATUS_OPTIONS"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
          
          <el-select
            v-model="filterType"
            placeholder="策略类型"
            style="width: 120px; margin-left: 10px"
            clearable
            @change="handleFilter"
          >
            <el-option
              v-for="option in STRATEGY_TYPE_OPTIONS"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
          
          <el-select
            v-model="filterRunning"
            placeholder="运行状态"
            style="width: 120px; margin-left: 10px"
            clearable
            @change="handleFilter"
          >
            <el-option label="运行中" :value="true" />
            <el-option label="已停止" :value="false" />
          </el-select>
          
          <el-button @click="resetFilters" style="margin-left: 10px">
            重置
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 策略列表 -->
    <div class="strategy-grid">
      <el-row :gutter="20" v-loading="loading">
        <el-col
          v-for="strategy in strategies"
          :key="strategy.id"
          :span="8"
          style="margin-bottom: 20px"
        >
          <el-card class="strategy-card" :class="{ 'running': strategy.is_running }">
            <!-- 卡片头部 -->
            <template #header>
              <div class="card-header">
                <div class="header-left">
                  <h3 class="strategy-name">{{ strategy.name }}</h3>
                  <div class="strategy-meta">
                    <StatusTag :status="strategy.status" size="small" />
                    <el-tag
                      v-if="strategy.is_running"
                      type="success"
                      size="small"
                      effect="dark"
                      style="margin-left: 8px"
                    >
                      运行中
                    </el-tag>
                  </div>
                </div>
                <div class="header-right">
                  <el-dropdown @command="handleCommand">
                    <el-button type="text" size="small">
                      <el-icon><MoreFilled /></el-icon>
                    </el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item :command="{ action: 'view', strategy }">
                          <el-icon><View /></el-icon>
                          查看详情
                        </el-dropdown-item>
                        <el-dropdown-item :command="{ action: 'edit', strategy }">
                          <el-icon><Edit /></el-icon>
                          编辑策略
                        </el-dropdown-item>
                        <el-dropdown-item :command="{ action: 'copy', strategy }">
                          <el-icon><CopyDocument /></el-icon>
                          复制策略
                        </el-dropdown-item>
                        <el-dropdown-item
                          :command="{ action: strategy.is_running ? 'stop' : 'start', strategy }"
                          :divided="true"
                        >
                          <el-icon>
                            <VideoPlay v-if="!strategy.is_running" />
                            <VideoPause v-else />
                          </el-icon>
                          {{ strategy.is_running ? '停止运行' : '启动运行' }}
                        </el-dropdown-item>
                        <el-dropdown-item
                          :command="{ action: 'delete', strategy }"
                          style="color: #f56c6c"
                        >
                          <el-icon><Delete /></el-icon>
                          删除策略
                        </el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </div>
              </div>
            </template>

            <!-- 卡片内容 -->
            <div class="card-content">
              <!-- 策略描述 -->
              <p class="strategy-description">
                {{ strategy.description || '暂无描述' }}
              </p>

              <!-- 策略信息 -->
              <div class="strategy-info">
                <div class="info-item">
                  <span class="info-label">类型:</span>
                  <span class="info-value">{{ STRATEGY_TYPE_LABELS[strategy.strategy_type] }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">版本:</span>
                  <span class="info-value">v{{ strategy.version }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">更新时间:</span>
                  <span class="info-value">{{ formatDate(strategy.updated_at) }}</span>
                </div>
              </div>

              <!-- 性能指标 -->
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
                  <div class="metric-value">
                    {{ formatPercent(strategy.win_rate) }}
                  </div>
                  <div class="metric-label">胜率</div>
                </div>
                <div class="metric-item">
                  <div class="metric-value">
                    {{ strategy.total_trades }}
                  </div>
                  <div class="metric-label">交易次数</div>
                </div>
              </div>

              <!-- 标签 -->
              <div class="strategy-tags" v-if="strategy.tags && strategy.tags.length > 0">
                <el-tag
                  v-for="tag in strategy.tags"
                  :key="tag"
                  size="small"
                  effect="plain"
                  style="margin-right: 4px; margin-bottom: 4px"
                >
                  {{ tag }}
                </el-tag>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 空状态 -->
      <EmptyState
        v-if="!loading && !hasStrategies"
        type="no-data"
        title="暂无策略"
        description="您还没有创建任何策略，点击上方按钮创建您的第一个策略"
        :show-action="true"
        action-text="创建策略"
        @action="showCreateDialog = true"
      />
    </div>

    <!-- 分页 -->
    <div class="pagination-wrapper" v-if="hasStrategies">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[12, 24, 48, 96]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
      />
    </div>

    <!-- 创建策略对话框 -->
    <StrategyCreateDialog
      v-model="showCreateDialog"
      @success="handleCreateSuccess"
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
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, Search, Document, VideoPlay, VideoPause, TrendCharts, DataAnalysis,
  View, Edit, CopyDocument, Delete, MoreFilled
} from '@element-plus/icons-vue'

import { useStrategyStore } from '@/stores/strategy'
import { StatusTag, EmptyState, ConfirmDialog } from '@/components/common'
import StrategyCreateDialog from './components/StrategyCreateDialog.vue'
import {
  STRATEGY_TYPE_OPTIONS,
  STRATEGY_STATUS_OPTIONS,
  STRATEGY_TYPE_LABELS,
  type StrategyListItem,
  type StrategyStatus,
  type StrategyType
} from '@/types/strategy'
import { formatDate, formatNumber, formatPercent } from '@/utils/format'

const router = useRouter()
const strategyStore = useStrategyStore()

// 响应式数据
const searchKeyword = ref('')
const filterStatus = ref<StrategyStatus | ''>('')
const filterType = ref<StrategyType | ''>('')
const filterRunning = ref<boolean | ''>('')
const showCreateDialog = ref(false)
const showConfirmDialog = ref(false)
const confirmType = ref<'warning' | 'error'>('warning')
const confirmTitle = ref('')
const confirmContent = ref('')
const confirmAction = ref<() => void>(() => {})

// 计算属性
const {
  strategies,
  strategyStats,
  loading,
  hasStrategies,
  total,
  searchParams
} = strategyStore

const currentPage = computed({
  get: () => searchParams.page || 1,
  set: (value) => {
    searchParams.page = value
  }
})

const pageSize = computed({
  get: () => searchParams.page_size || 12,
  set: (value) => {
    searchParams.page_size = value
  }
})

// 方法
const handleSearch = () => {
  strategyStore.searchStrategies(searchKeyword.value)
}

const handleFilter = () => {
  const filters: any = {}
  
  if (filterStatus.value) {
    filters.status = filterStatus.value
  }
  
  if (filterType.value) {
    filters.strategy_type = filterType.value
  }
  
  if (filterRunning.value !== '') {
    filters.is_running = filterRunning.value
  }
  
  strategyStore.filterStrategies(filters)
}

const resetFilters = () => {
  searchKeyword.value = ''
  filterStatus.value = ''
  filterType.value = ''
  filterRunning.value = ''
  
  strategyStore.fetchMyStrategies()
}

const handlePageChange = (page: number) => {
  strategyStore.changePage(page)
}

const handleSizeChange = (size: number) => {
  strategyStore.changePageSize(size)
}

const handleCommand = ({ action, strategy }: { action: string; strategy: StrategyListItem }) => {
  switch (action) {
    case 'view':
      router.push(`/strategy/${strategy.id}`)
      break
      
    case 'edit':
      router.push(`/strategy/${strategy.id}/edit`)
      break
      
    case 'copy':
      handleCopyStrategy(strategy)
      break
      
    case 'start':
      handleStartStrategy(strategy)
      break
      
    case 'stop':
      handleStopStrategy(strategy)
      break
      
    case 'delete':
      handleDeleteStrategy(strategy)
      break
  }
}

const handleCopyStrategy = async (strategy: StrategyListItem) => {
  try {
    const newName = await ElMessageBox.prompt(
      '请输入新策略名称',
      '复制策略',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputValue: `${strategy.name} - 副本`,
        inputValidator: (value) => {
          if (!value || !value.trim()) {
            return '策略名称不能为空'
          }
          return true
        }
      }
    )
    
    await strategyStore.copyStrategy(strategy.id, newName.value)
  } catch (error) {
    // 用户取消操作
  }
}

const handleStartStrategy = (strategy: StrategyListItem) => {
  confirmType.value = 'warning'
  confirmTitle.value = '启动策略'
  confirmContent.value = `确定要启动策略 "${strategy.name}" 吗？`
  confirmAction.value = () => {
    strategyStore.executeStrategy(strategy.id, { action: 'start' })
  }
  showConfirmDialog.value = true
}

const handleStopStrategy = (strategy: StrategyListItem) => {
  confirmType.value = 'warning'
  confirmTitle.value = '停止策略'
  confirmContent.value = `确定要停止策略 "${strategy.name}" 吗？`
  confirmAction.value = () => {
    strategyStore.executeStrategy(strategy.id, { action: 'stop' })
  }
  showConfirmDialog.value = true
}

const handleDeleteStrategy = (strategy: StrategyListItem) => {
  confirmType.value = 'error'
  confirmTitle.value = '删除策略'
  confirmContent.value = `确定要删除策略 "${strategy.name}" 吗？此操作不可恢复。`
  confirmAction.value = () => {
    strategyStore.deleteStrategy(strategy.id)
  }
  showConfirmDialog.value = true
}

const handleConfirm = () => {
  confirmAction.value()
  showConfirmDialog.value = false
}

const handleCreateSuccess = () => {
  showCreateDialog.value = false
  strategyStore.fetchMyStrategies()
}

const getReturnClass = (returns: number) => {
  if (returns > 0) return 'positive'
  if (returns < 0) return 'negative'
  return 'neutral'
}

// 生命周期
onMounted(async () => {
  await Promise.all([
    strategyStore.fetchMyStrategies(),
    strategyStore.fetchStrategyStats()
  ])
})
</script>

<style lang="scss" scoped>
.strategy-list {
  padding: 20px;
  
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 24px;
    
    .header-left {
      h2 {
        margin: 0 0 8px 0;
        font-size: 24px;
        font-weight: 600;
        color: var(--el-text-color-primary);
      }
      
      .header-desc {
        margin: 0;
        color: var(--el-text-color-secondary);
        font-size: 14px;
      }
    }
  }
  
  .stats-cards {
    margin-bottom: 24px;
    
    .stat-card {
      .el-card__body {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 20px;
      }
      
      .stat-content {
        .stat-value {
          font-size: 28px;
          font-weight: 600;
          color: var(--el-text-color-primary);
          line-height: 1;
          margin-bottom: 8px;
        }
        
        .stat-label {
          font-size: 14px;
          color: var(--el-text-color-secondary);
        }
      }
      
      .stat-icon {
        font-size: 32px;
        opacity: 0.8;
      }
    }
  }
  
  .filter-card {
    margin-bottom: 24px;
    
    .filter-content {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
  }
  
  .strategy-grid {
    min-height: 400px;
  }
  
  .strategy-card {
    height: 100%;
    transition: all 0.3s ease;
    
    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
    }
    
    &.running {
      border-left: 4px solid var(--el-color-success);
    }
    
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      
      .header-left {
        flex: 1;
        
        .strategy-name {
          margin: 0 0 8px 0;
          font-size: 16px;
          font-weight: 600;
          color: var(--el-text-color-primary);
          line-height: 1.4;
        }
        
        .strategy-meta {
          display: flex;
          align-items: center;
        }
      }
    }
    
    .card-content {
      .strategy-description {
        margin: 0 0 16px 0;
        color: var(--el-text-color-secondary);
        font-size: 14px;
        line-height: 1.5;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
      }
      
      .strategy-info {
        margin-bottom: 16px;
        
        .info-item {
          display: flex;
          justify-content: space-between;
          margin-bottom: 4px;
          font-size: 13px;
          
          .info-label {
            color: var(--el-text-color-secondary);
          }
          
          .info-value {
            color: var(--el-text-color-primary);
            font-weight: 500;
          }
        }
      }
      
      .performance-metrics {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 12px;
        margin-bottom: 16px;
        
        .metric-item {
          text-align: center;
          padding: 8px;
          background: var(--el-fill-color-light);
          border-radius: 4px;
          
          .metric-value {
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 4px;
            
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
      
      .strategy-tags {
        margin-top: 12px;
      }
    }
  }
  
  .pagination-wrapper {
    display: flex;
    justify-content: center;
    margin-top: 32px;
  }
}
</style>