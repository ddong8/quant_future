<template>
  <el-dialog
    v-model="visible"
    :title="strategy?.name || '策略详情'"
    width="900px"
    :before-close="handleClose"
  >
    <div v-if="strategy" class="strategy-detail">
      <!-- 基本信息 -->
      <div class="detail-section">
        <h3 class="section-title">基本信息</h3>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="策略名称">
            {{ strategy.name }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="statusTagType">{{ statusText }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="分类">
            {{ strategy.category }}
          </el-descriptions-item>
          <el-descriptions-item label="作者">
            {{ strategy.author }}
          </el-descriptions-item>
          <el-descriptions-item label="版本">
            {{ strategy.version }}
          </el-descriptions-item>
          <el-descriptions-item label="公开状态">
            <el-tag :type="strategy.is_public ? 'success' : 'info'">
              {{ strategy.is_public ? '公开' : '私有' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ formatDateTime(strategy.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="更新时间">
            {{ formatDateTime(strategy.updated_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">
            {{ strategy.description || '暂无描述' }}
          </el-descriptions-item>
          <el-descriptions-item label="标签" :span="2">
            <el-tag
              v-for="tag in strategy.tags"
              :key="tag"
              size="small"
              style="margin-right: 8px;"
            >
              {{ tag }}
            </el-tag>
            <span v-if="!strategy.tags?.length" class="text-muted">暂无标签</span>
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <!-- 配置信息 -->
      <div class="detail-section">
        <h3 class="section-title">配置信息</h3>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="交易品种">
            <el-tag
              v-for="symbol in strategy.config.symbols"
              :key="symbol"
              size="small"
              style="margin-right: 4px;"
            >
              {{ symbol }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="时间周期">
            {{ strategy.config.timeframe }}
          </el-descriptions-item>
          <el-descriptions-item label="最大仓位">
            {{ formatPercent(strategy.config.max_position_size) }}
          </el-descriptions-item>
          <el-descriptions-item label="单笔风险">
            {{ formatPercent(strategy.config.risk_per_trade) }}
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <!-- 风险控制 -->
      <div class="detail-section">
        <h3 class="section-title">风险控制</h3>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="最大回撤">
            {{ formatPercent(strategy.config.risk_management.max_drawdown) }}
          </el-descriptions-item>
          <el-descriptions-item label="止损比例">
            {{ formatPercent(strategy.config.risk_management.stop_loss) }}
          </el-descriptions-item>
          <el-descriptions-item label="止盈比例">
            {{ formatPercent(strategy.config.risk_management.take_profit) }}
          </el-descriptions-item>
          <el-descriptions-item label="日最大交易">
            {{ strategy.config.risk_management.max_daily_trades }}
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <!-- 交易时间 -->
      <div class="detail-section">
        <h3 class="section-title">交易时间</h3>
        <el-descriptions :column="3" border>
          <el-descriptions-item label="开始时间">
            {{ strategy.config.trading_hours.start_time }}
          </el-descriptions-item>
          <el-descriptions-item label="结束时间">
            {{ strategy.config.trading_hours.end_time }}
          </el-descriptions-item>
          <el-descriptions-item label="时区">
            {{ strategy.config.trading_hours.timezone }}
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <!-- 运行状态 -->
      <div class="detail-section" v-if="strategy.runtime">
        <h3 class="section-title">运行状态</h3>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="运行状态">
            <el-tag :type="strategy.runtime.is_running ? 'success' : 'info'">
              {{ strategy.runtime.is_running ? '运行中' : '已停止' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="启动时间">
            {{ strategy.runtime.start_time ? formatDateTime(strategy.runtime.start_time) : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="最后信号时间">
            {{ strategy.runtime.last_signal_time ? formatDateTime(strategy.runtime.last_signal_time) : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="当前持仓">
            {{ strategy.runtime.current_positions }}
          </el-descriptions-item>
          <el-descriptions-item label="当日盈亏">
            <span :class="['pnl', strategy.runtime.daily_pnl >= 0 ? 'profit' : 'loss']">
              {{ formatCurrency(strategy.runtime.daily_pnl) }}
            </span>
          </el-descriptions-item>
          <el-descriptions-item label="错误信息">
            <span v-if="strategy.runtime.error_message" class="error-message">
              {{ strategy.runtime.error_message }}
            </span>
            <span v-else class="text-muted">无</span>
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <!-- 性能指标 -->
      <div class="detail-section" v-if="strategy.stats">
        <h3 class="section-title">性能指标</h3>
        <el-descriptions :column="3" border>
          <el-descriptions-item label="总交易次数">
            {{ strategy.stats.total_trades }}
          </el-descriptions-item>
          <el-descriptions-item label="盈利交易">
            {{ strategy.stats.winning_trades }}
          </el-descriptions-item>
          <el-descriptions-item label="亏损交易">
            {{ strategy.stats.losing_trades }}
          </el-descriptions-item>
          <el-descriptions-item label="胜率">
            {{ formatPercent(strategy.stats.win_rate) }}
          </el-descriptions-item>
          <el-descriptions-item label="总盈亏">
            <span :class="['pnl', strategy.stats.total_pnl >= 0 ? 'profit' : 'loss']">
              {{ formatCurrency(strategy.stats.total_pnl) }}
            </span>
          </el-descriptions-item>
          <el-descriptions-item label="最大回撤">
            <span class="loss">{{ formatPercent(strategy.stats.max_drawdown) }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="夏普比率">
            {{ strategy.stats.sharpe_ratio?.toFixed(2) || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="索提诺比率">
            {{ strategy.stats.sortino_ratio?.toFixed(2) || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="盈亏比">
            {{ strategy.stats.profit_factor?.toFixed(2) || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="平均持仓时间">
            {{ formatDuration(strategy.stats.avg_trade_duration) }}
          </el-descriptions-item>
          <el-descriptions-item label="最后更新">
            {{ formatDateTime(strategy.stats.last_updated) }}
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <!-- 操作按钮 -->
      <div class="detail-actions">
        <el-button
          v-if="!strategy.runtime?.is_running && strategy.status !== 'error'"
          type="success"
          @click="handleStart"
        >
          启动策略
        </el-button>
        <el-button
          v-if="strategy.runtime?.is_running"
          type="warning"
          @click="handleStop"
        >
          停止策略
        </el-button>
        <el-button @click="handleEdit">编辑策略</el-button>
        <el-button @click="handleClone">克隆策略</el-button>
        <el-button @click="handleExport">导出策略</el-button>
      </div>
    </div>

    <div v-else-if="loading" class="loading-container">
      <el-skeleton :rows="10" animated />
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">关闭</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useStrategyStore } from '@/stores/strategy'
import type { Strategy } from '@/types/strategy'

interface Props {
  modelValue: boolean
  strategyId: number | null
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const strategyStore = useStrategyStore()
const router = useRouter()
const loading = ref(false)
const strategy = ref<Strategy | null>(null)

// 计算属性
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const statusTagType = computed(() => {
  if (!strategy.value) return 'info'
  
  const typeMap = {
    draft: 'info',
    active: 'success',
    paused: 'warning',
    stopped: 'info',
    error: 'danger'
  }
  return typeMap[strategy.value.status] || 'info'
})

const statusText = computed(() => {
  if (!strategy.value) return ''
  
  const textMap = {
    draft: '草稿',
    active: '活跃',
    paused: '暂停',
    stopped: '停止',
    error: '错误'
  }
  return textMap[strategy.value.status] || '未知'
})

// 方法
const loadStrategy = async () => {
  if (!props.strategyId) return
  
  try {
    loading.value = true
    strategy.value = await strategyStore.fetchStrategy(props.strategyId)
  } finally {
    loading.value = false
  }
}

const handleStart = async () => {
  if (!strategy.value) return
  
  try {
    await strategyStore.startStrategy(strategy.value.id)
    await loadStrategy() // 重新加载策略信息
  } catch (error) {
    // 错误已在store中处理
  }
}

const handleStop = async () => {
  if (!strategy.value) return
  
  try {
    await ElMessageBox.confirm(
      `确定要停止策略 "${strategy.value.name}" 吗？`,
      '确认停止',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await strategyStore.stopStrategy(strategy.value.id)
    await loadStrategy() // 重新加载策略信息
  } catch (error) {
    // 用户取消或错误已在store中处理
  }
}

const handleEdit = () => {
  // 跳转到编辑页面
  if (strategy.value) {
    router.push(`/strategies/${strategy.value.id}/edit`)
    handleClose()
  }
}

const handleClone = async () => {
  if (!strategy.value) return
  
  try {
    const { value: name } = await ElMessageBox.prompt(
      '请输入新策略的名称',
      '克隆策略',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputValue: `${strategy.value.name} - 副本`,
        inputValidator: (value) => {
          if (!value || value.trim().length === 0) {
            return '策略名称不能为空'
          }
          return true
        }
      }
    )
    
    await strategyStore.cloneStrategy(strategy.value.id, name)
    ElMessage.success('策略克隆成功')
  } catch (error) {
    // 用户取消或错误已在store中处理
  }
}

const handleExport = () => {
  // 导出策略
  if (strategy.value) {
    // strategyApi.exportStrategy(strategy.value.id, 'json')
  }
}

const handleClose = () => {
  visible.value = false
  strategy.value = null
}

// 格式化函数
const formatDateTime = (dateString: string) => {
  return new Date(dateString).toLocaleString('zh-CN')
}

const formatPercent = (value: number) => {
  return `${(value * 100).toFixed(1)}%`
}

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY'
  }).format(value)
}

const formatDuration = (minutes: number) => {
  if (minutes < 60) {
    return `${minutes.toFixed(0)}分钟`
  } else if (minutes < 1440) {
    return `${(minutes / 60).toFixed(1)}小时`
  } else {
    return `${(minutes / 1440).toFixed(1)}天`
  }
}

// 监听对话框显示状态和策略ID变化
watch([visible, () => props.strategyId], ([newVisible, newStrategyId]) => {
  if (newVisible && newStrategyId) {
    loadStrategy()
  }
})
</script>

<style scoped lang="scss">
.strategy-detail {
  .detail-section {
    margin-bottom: 24px;
    
    .section-title {
      margin: 0 0 12px 0;
      font-size: 16px;
      font-weight: 600;
      color: #303133;
      border-left: 4px solid #409eff;
      padding-left: 8px;
    }
  }
  
  .detail-actions {
    display: flex;
    gap: 12px;
    justify-content: center;
    padding: 20px 0;
    border-top: 1px solid #ebeef5;
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
  
  .error-message {
    color: #f56c6c;
    font-size: 12px;
  }
  
  .text-muted {
    color: #909399;
  }
}

.loading-container {
  padding: 20px;
}

.dialog-footer {
  text-align: right;
}

:deep(.el-descriptions__label) {
  font-weight: 600;
}
</style>