<template>
  <el-tag
    :type="tagType"
    :size="size"
    :effect="effect"
    :round="round"
    :hit="hit"
    :color="customColor"
    :closable="closable"
    :disable-transitions="disableTransitions"
    @close="handleClose"
    @click="handleClick"
    :class="['status-tag', statusClass]"
  >
    <el-icon v-if="icon" class="tag-icon">
      <component :is="icon" />
    </el-icon>
    <span class="tag-text">{{ displayText }}</span>
  </el-tag>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ElTag, ElIcon } from 'element-plus'

// 状态配置接口
interface StatusConfig {
  text: string
  type: 'success' | 'info' | 'warning' | 'danger'
  color?: string
  icon?: any
  class?: string
}

interface Props {
  status: string | number
  statusMap?: Record<string | number, StatusConfig>
  size?: 'large' | 'default' | 'small'
  effect?: 'dark' | 'light' | 'plain'
  round?: boolean
  hit?: boolean
  closable?: boolean
  disableTransitions?: boolean
  customColor?: string
  icon?: any
  text?: string
}

const props = withDefaults(defineProps<Props>(), {
  statusMap: () => ({}),
  size: 'default',
  effect: 'light',
  round: false,
  hit: false,
  closable: false,
  disableTransitions: false
})

const emit = defineEmits<{
  close: [event: Event]
  click: [event: Event]
}>()

// 默认状态映射
const defaultStatusMap: Record<string | number, StatusConfig> = {
  // 通用状态
  'active': { text: '激活', type: 'success' },
  'inactive': { text: '未激活', type: 'info' },
  'pending': { text: '待处理', type: 'warning' },
  'processing': { text: '处理中', type: 'warning' },
  'completed': { text: '已完成', type: 'success' },
  'failed': { text: '失败', type: 'danger' },
  'cancelled': { text: '已取消', type: 'info' },
  'expired': { text: '已过期', type: 'danger' },
  
  // 订单状态
  'new': { text: '新建', type: 'info' },
  'submitted': { text: '已提交', type: 'warning' },
  'partial_filled': { text: '部分成交', type: 'warning' },
  'filled': { text: '已成交', type: 'success' },
  'rejected': { text: '已拒绝', type: 'danger' },
  
  // 交易状态
  'buy': { text: '买入', type: 'success' },
  'sell': { text: '卖出', type: 'danger' },
  'long': { text: '做多', type: 'success' },
  'short': { text: '做空', type: 'danger' },
  
  // 数字状态
  0: { text: '禁用', type: 'info' },
  1: { text: '启用', type: 'success' },
  2: { text: '暂停', type: 'warning' },
  3: { text: '错误', type: 'danger' }
}\n\n// 计算属性\nconst statusConfig = computed(() => {\n  const allStatusMap = { ...defaultStatusMap, ...props.statusMap }\n  return allStatusMap[props.status] || {\n    text: String(props.status),\n    type: 'info' as const\n  }\n})\n\nconst displayText = computed(() => {\n  return props.text || statusConfig.value.text\n})\n\nconst tagType = computed(() => {\n  return statusConfig.value.type\n})\n\nconst customColor = computed(() => {\n  return props.customColor || statusConfig.value.color\n})\n\nconst icon = computed(() => {\n  return props.icon || statusConfig.value.icon\n})\n\nconst statusClass = computed(() => {\n  const classes = [`status-${props.status}`]\n  if (statusConfig.value.class) {\n    classes.push(statusConfig.value.class)\n  }\n  return classes.join(' ')\n})\n\n// 事件处理\nconst handleClose = (event: Event) => {\n  emit('close', event)\n}\n\nconst handleClick = (event: Event) => {\n  emit('click', event)\n}\n</script>\n\n<style lang=\"scss\" scoped>\n.status-tag {\n  .tag-icon {\n    margin-right: 4px;\n    font-size: 12px;\n  }\n  \n  .tag-text {\n    font-weight: 500;\n  }\n  \n  // 特定状态的自定义样式\n  &.status-buy {\n    --el-tag-text-color: #67c23a;\n    --el-tag-bg-color: #f0f9ff;\n    --el-tag-border-color: #67c23a;\n  }\n  \n  &.status-sell {\n    --el-tag-text-color: #f56c6c;\n    --el-tag-bg-color: #fef0f0;\n    --el-tag-border-color: #f56c6c;\n  }\n  \n  &.status-long {\n    --el-tag-text-color: #67c23a;\n    --el-tag-bg-color: #f0f9ff;\n    --el-tag-border-color: #67c23a;\n  }\n  \n  &.status-short {\n    --el-tag-text-color: #f56c6c;\n    --el-tag-bg-color: #fef0f0;\n    --el-tag-border-color: #f56c6c;\n  }\n}\n</style>"