<template>
  <div class="strategy-card">
    <div class="card-header">
      <div class="strategy-info">
        <h3 class="strategy-name">{{ strategy.name }}</h3>
        <div class="strategy-meta">
          <el-tag :type="statusTagType" size="small">
            {{ statusText }}
          </el-tag>
          <span class="category">{{ strategy.category }}</span>
        </div>
      </div>
      <div class="card-actions">
        <el-dropdown @command="handleCommand">
          <el-button text>
            <el-icon><MoreFilled /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="view">查看详情</el-dropdown-item>
              <el-dropdown-item command="edit">编辑</el-dropdown-item>
              <el-dropdown-item command="test">测试部署</el-dropdown-item>
              <el-dropdown-item command="clone">克隆</el-dropdown-item>
              <el-dropdown-item command="export">导出</el-dropdown-item>
              <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <div class="card-content">
      <p class="strategy-description">{{ strategy.description || '暂无描述' }}</p>
      
      <div class="strategy-tags" v-if="strategy.tags?.length">
        <el-tag
          v-for="tag in strategy.tags.slice(0, 3)"
          :key="tag"
          size="small"
          effect="plain"
        >
          {{ tag }}
        </el-tag>
        <el-tag v-if="strategy.tags.length > 3" size="small" effect="plain">
          +{{ strategy.tags.length - 3 }}
        </el-tag>
      </div>

      <!-- 运行状态 -->
      <div class="runtime-info" v-if="strategy.runtime">
        <div class="runtime-item">
          <span class="label">运行状态:</span>
          <el-tag :type="strategy.runtime.is_running ? 'success' : 'info'" size="small">
            {{ strategy.runtime.is_running ? '运行中' : '已停止' }}
          </el-tag>
        </div>
        <div class="runtime-item" v-if="strategy.runtime.is_running">
          <span class="label">当日盈亏:</span>
          <span :class="['pnl', strategy.runtime.daily_pnl >= 0 ? 'profit' : 'loss']">
            {{ formatCurrency(strategy.runtime.daily_pnl) }}
          </span>
        </div>
      </div>

      <!-- 统计信息 -->
      <div class="stats-info" v-if="strategy.stats">
        <div class="stats-grid">
          <div class="stat-item">
            <span class="stat-label">总交易</span>
            <span class="stat-value">{{ strategy.stats.total_trades }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">胜率</span>
            <span class="stat-value">{{ formatPercent(strategy.stats.win_rate) }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">总盈亏</span>
            <span :class="['stat-value', strategy.stats.total_pnl >= 0 ? 'profit' : 'loss']">
              {{ formatCurrency(strategy.stats.total_pnl) }}
            </span>
          </div>
          <div class="stat-item">
            <span class="stat-label">夏普比率</span>
            <span class="stat-value">{{ strategy.stats.sharpe_ratio?.toFixed(2) || '-' }}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="card-footer">
      <div class="footer-info">
        <span class="author">作者: {{ strategy.author }}</span>
        <span class="update-time">{{ formatDate(strategy.updated_at) }}</span>
      </div>
      <div class="footer-actions">
        <el-button
          v-if="!strategy.runtime?.is_running && strategy.status !== 'error'"
          type="success"
          size="small"
          @click="$emit('start', strategy)"
        >
          启动
        </el-button>
        <el-button
          v-if="strategy.runtime?.is_running"
          type="warning"
          size="small"
          @click="$emit('stop', strategy)"
        >
          停止
        </el-button>
        <el-button
          v-if="strategy.status === 'error'"
          type="danger"
          size="small"
          disabled
        >
          错误
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { MoreFilled } from '@element-plus/icons-vue'
import type { Strategy } from '@/types/strategy'

interface Props {
  strategy: Strategy
}

interface Emits {
  (e: 'edit', strategy: Strategy): void
  (e: 'delete', strategy: Strategy): void
  (e: 'clone', strategy: Strategy): void
  (e: 'start', strategy: Strategy): void
  (e: 'stop', strategy: Strategy): void
  (e: 'view', strategy: Strategy): void
  (e: 'test', strategy: Strategy): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 计算属性
const statusTagType = computed(() => {
  const typeMap = {
    draft: 'info',
    active: 'success',
    paused: 'warning',
    stopped: 'info',
    error: 'danger'
  }
  return typeMap[props.strategy.status] || 'info'
})

const statusText = computed(() => {
  const textMap = {
    draft: '草稿',
    active: '活跃',
    paused: '暂停',
    stopped: '停止',
    error: '错误'
  }
  return textMap[props.strategy.status] || '未知'
})

// 方法
const handleCommand = (command: string) => {
  switch (command) {
    case 'view':
      emit('view', props.strategy)
      break
    case 'edit':
      emit('edit', props.strategy)
      break
    case 'test':
      emit('test', props.strategy)
      break
    case 'clone':
      emit('clone', props.strategy)
      break
    case 'delete':
      emit('delete', props.strategy)
      break
    case 'export':
      // 导出功能
      break
  }
}

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY'
  }).format(value)
}

const formatPercent = (value: number) => {
  return `${(value * 100).toFixed(1)}%`
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('zh-CN')
}
</script>

<style scoped lang="scss">
.strategy-card {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  margin-bottom: 16px;
  
  &:hover {
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
    transform: translateY(-2px);
  }
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    padding: 16px 16px 0;
    
    .strategy-info {
      flex: 1;
      
      .strategy-name {
        margin: 0 0 8px 0;
        font-size: 16px;
        font-weight: 600;
        color: #303133;
        line-height: 1.4;
      }
      
      .strategy-meta {
        display: flex;
        align-items: center;
        gap: 8px;
        
        .category {
          font-size: 12px;
          color: #909399;
        }
      }
    }
    
    .card-actions {
      flex-shrink: 0;
    }
  }
  
  .card-content {
    padding: 12px 16px;
    
    .strategy-description {
      margin: 0 0 12px 0;
      font-size: 14px;
      color: #606266;
      line-height: 1.5;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }
    
    .strategy-tags {
      margin-bottom: 12px;
      display: flex;
      flex-wrap: wrap;
      gap: 4px;
    }
    
    .runtime-info {
      margin-bottom: 12px;
      
      .runtime-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 4px;
        font-size: 12px;
        
        .label {
          color: #909399;
        }
        
        .pnl {
          font-weight: 600;
          
          &.profit {
            color: #67c23a;
          }
          
          &.loss {
            color: #f56c6c;
          }
        }
      }
    }
    
    .stats-info {
      .stats-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 8px;
        
        .stat-item {
          display: flex;
          flex-direction: column;
          align-items: center;
          padding: 8px;
          background: #f5f7fa;
          border-radius: 4px;
          
          .stat-label {
            font-size: 12px;
            color: #909399;
            margin-bottom: 2px;
          }
          
          .stat-value {
            font-size: 14px;
            font-weight: 600;
            color: #303133;
            
            &.profit {
              color: #67c23a;
            }
            
            &.loss {
              color: #f56c6c;
            }
          }
        }
      }
    }
  }
  
  .card-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px 16px;
    border-top: 1px solid #ebeef5;
    
    .footer-info {
      display: flex;
      flex-direction: column;
      gap: 4px;
      font-size: 12px;
      color: #909399;
    }
    
    .footer-actions {
      display: flex;
      gap: 8px;
    }
  }
}
</style>