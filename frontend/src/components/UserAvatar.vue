<template>
  <div class="user-avatar" :class="{ clickable }" @click="handleClick">
    <el-avatar 
      :size="size" 
      :src="avatarUrl" 
      :style="{ backgroundColor: bgColor }"
    >
      <template v-if="!avatarUrl">
        <el-icon v-if="showIcon">
          <User />
        </el-icon>
        <span v-else-if="displayName" class="avatar-text">
          {{ getInitials(displayName) }}
        </span>
        <el-icon v-else>
          <User />
        </el-icon>
      </template>
    </el-avatar>
    
    <div v-if="showName" class="user-name">
      {{ displayName }}
    </div>
    
    <div v-if="showRole" class="user-role">
      {{ roleText }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { User } from '@element-plus/icons-vue'

interface Props {
  avatarUrl?: string
  displayName?: string
  role?: string
  size?: number | string
  showName?: boolean
  showRole?: boolean
  showIcon?: boolean
  clickable?: boolean
  bgColor?: string
}

const props = withDefaults(defineProps<Props>(), {
  size: 40,
  showName: false,
  showRole: false,
  showIcon: true,
  clickable: false,
  bgColor: 'var(--el-color-primary)'
})

const emit = defineEmits<{
  click: []
}>()

// 角色文本映射
const roleText = computed(() => {
  const roleMap: Record<string, string> = {
    admin: '管理员',
    trader: '交易员',
    viewer: '观察者'
  }
  return roleMap[props.role || ''] || props.role
})

// 获取姓名首字母
const getInitials = (name: string): string => {
  if (!name) return ''
  
  const words = name.trim().split(/\s+/)
  if (words.length === 1) {
    return words[0].charAt(0).toUpperCase()
  } else {
    return words.slice(0, 2).map(word => word.charAt(0).toUpperCase()).join('')
  }
}

// 处理点击事件
const handleClick = () => {
  if (props.clickable) {
    emit('click')
  }
}
</script>

<style lang="scss" scoped>
.user-avatar {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  
  &.clickable {
    cursor: pointer;
    transition: opacity 0.3s;
    
    &:hover {
      opacity: 0.8;
    }
  }
  
  .avatar-text {
    font-size: 14px;
    font-weight: 600;
    color: white;
  }
  
  .user-name {
    font-size: 14px;
    color: var(--el-text-color-primary);
    font-weight: 500;
    text-align: center;
  }
  
  .user-role {
    font-size: 12px;
    color: var(--el-text-color-secondary);
    text-align: center;
  }
}
</style>