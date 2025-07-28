<template>
  <div class="auth-status" :class="statusClass">
    <el-icon :size="iconSize">
      <component :is="statusIcon" />
    </el-icon>
    <span v-if="showText" class="status-text">{{ statusText }}</span>
    <el-tooltip v-if="showTooltip" :content="tooltipContent" placement="top">
      <el-icon class="info-icon">
        <InfoFilled />
      </el-icon>
    </el-tooltip>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import {
  CircleCheckFilled,
  CircleCloseFilled,
  WarningFilled,
  Loading,
  InfoFilled
} from '@element-plus/icons-vue'

interface Props {
  showText?: boolean
  showTooltip?: boolean
  iconSize?: number
  type?: 'authentication' | 'verification' | 'activity'
}

const props = withDefaults(defineProps<Props>(), {
  showText: true,
  showTooltip: false,
  iconSize: 16,
  type: 'authentication'
})

const authStore = useAuthStore()

// 计算状态
const status = computed(() => {
  const user = authStore.user
  
  if (!authStore.isAuthenticated || !user) {
    return {
      type: 'unauthenticated',
      text: '未登录',
      class: 'unauthenticated',
      icon: CircleCloseFilled,
      tooltip: '用户未登录或登录已过期'
    }
  }

  switch (props.type) {
    case 'verification':
      if (user.is_verified) {
        return {
          type: 'verified',
          text: '已验证',
          class: 'verified',
          icon: CircleCheckFilled,
          tooltip: '邮箱已验证'
        }
      } else {
        return {
          type: 'unverified',
          text: '未验证',
          class: 'unverified',
          icon: WarningFilled,
          tooltip: '邮箱未验证，请前往个人中心验证邮箱'
        }
      }

    case 'activity':
      if (user.is_active) {
        return {
          type: 'active',
          text: '正常',
          class: 'active',
          icon: CircleCheckFilled,
          tooltip: '账户状态正常'
        }
      } else {
        return {
          type: 'inactive',
          text: '已禁用',
          class: 'inactive',
          icon: CircleCloseFilled,
          tooltip: '账户已被禁用，请联系管理员'
        }
      }

    case 'authentication':
    default:
      if (authStore.loading) {
        return {
          type: 'loading',
          text: '验证中',
          class: 'loading',
          icon: Loading,
          tooltip: '正在验证用户身份'
        }
      } else {
        return {
          type: 'authenticated',
          text: '已登录',
          class: 'authenticated',
          icon: CircleCheckFilled,
          tooltip: `已登录为 ${user.username}`
        }
      }
  }
})

// 计算属性
const statusClass = computed(() => status.value.class)
const statusText = computed(() => status.value.text)
const statusIcon = computed(() => status.value.icon)
const tooltipContent = computed(() => status.value.tooltip)
</script>

<style lang="scss" scoped>
.auth-status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  
  .status-text {
    font-weight: 500;
  }
  
  .info-icon {
    font-size: 12px;
    color: var(--el-text-color-secondary);
    cursor: help;
  }
  
  // 不同状态的样式
  &.authenticated {
    color: var(--el-color-success);
  }
  
  &.unauthenticated {
    color: var(--el-color-danger);
  }
  
  &.verified {
    color: var(--el-color-success);
  }
  
  &.unverified {
    color: var(--el-color-warning);
  }
  
  &.active {
    color: var(--el-color-success);
  }
  
  &.inactive {
    color: var(--el-color-danger);
  }
  
  &.loading {
    color: var(--el-color-primary);
    
    .el-icon {
      animation: rotate 1s linear infinite;
    }
  }
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>