<template>
  <div class="empty-state" :class="{ 'is-small': size === 'small' }">
    <div class="empty-content">
      <!-- 图标 -->
      <div class="empty-icon">
        <slot name="icon">
          <el-icon :size="iconSize">
            <component :is="icon" />
          </el-icon>
        </slot>
      </div>
      
      <!-- 标题 -->
      <div v-if="title" class="empty-title">
        {{ title }}
      </div>
      
      <!-- 描述 -->
      <div v-if="description" class="empty-description">
        {{ description }}
      </div>
      
      <!-- 操作按钮 -->
      <div v-if="showAction" class="empty-actions">
        <slot name="actions">
          <el-button 
            v-if="actionText"
            :type="actionType"
            :size="actionSize"
            @click="handleAction"
          >
            {{ actionText }}
          </el-button>
        </slot>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ElIcon, ElButton } from 'element-plus'
import { 
  DocumentDelete, 
  FolderOpened, 
  Search, 
  Connection, 
  Warning,
  InfoFilled,
  CircleClose
} from '@element-plus/icons-vue'

interface Props {
  type?: 'default' | 'no-data' | 'no-search' | 'network-error' | 'error' | 'info'
  title?: string
  description?: string
  icon?: any
  size?: 'default' | 'small'
  showAction?: boolean
  actionText?: string
  actionType?: 'primary' | 'success' | 'warning' | 'danger' | 'info'
  actionSize?: 'large' | 'default' | 'small'
}

const props = withDefaults(defineProps<Props>(), {
  type: 'default',
  size: 'default',
  showAction: false,
  actionType: 'primary',
  actionSize: 'default'
})

const emit = defineEmits<{
  action: []
}>()

// 预设配置
const presetConfigs = {
  'default': {
    icon: FolderOpened,
    title: '暂无数据',
    description: '当前没有可显示的内容'
  },
  'no-data': {
    icon: DocumentDelete,
    title: '暂无数据',
    description: '当前列表为空，请添加数据'
  },
  'no-search': {
    icon: Search,
    title: '无搜索结果',
    description: '没有找到符合条件的数据，请尝试其他搜索条件'
  },
  'network-error': {
    icon: Connection,
    title: '网络连接失败',
    description: '请检查网络连接后重试'
  },
  'error': {
    icon: CircleClose,
    title: '出现错误',
    description: '系统出现异常，请稍后重试'
  },
  'info': {
    icon: InfoFilled,
    title: '提示信息',
    description: '这里是一些提示信息'
  }
}

// 计算属性
const config = computed(() => {
  return presetConfigs[props.type] || presetConfigs.default
})

const icon = computed(() => {
  return props.icon || config.value.icon
})

const title = computed(() => {
  return props.title || config.value.title
})

const description = computed(() => {
  return props.description || config.value.description
})

const iconSize = computed(() => {
  return props.size === 'small' ? 48 : 64
})

// 事件处理
const handleAction = () => {
  emit('action')
}
</script>

<style lang="scss" scoped>
.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  padding: 40px 20px;
  
  &.is-small {
    min-height: 200px;
    padding: 20px;
  }
  
  .empty-content {
    text-align: center;
    max-width: 400px;
    
    .empty-icon {
      margin-bottom: 16px;
      
      .el-icon {
        color: var(--el-text-color-placeholder);
      }
    }
    
    .empty-title {
      font-size: 16px;
      font-weight: 500;
      color: var(--el-text-color-primary);
      margin-bottom: 8px;
      line-height: 1.5;
    }
    
    .empty-description {
      font-size: 14px;
      color: var(--el-text-color-secondary);
      margin-bottom: 24px;
      line-height: 1.6;
    }
    
    .empty-actions {
      .el-button + .el-button {
        margin-left: 12px;
      }
    }
  }
  
  // 小尺寸样式
  &.is-small {
    .empty-content {
      .empty-title {
        font-size: 14px;
        margin-bottom: 6px;
      }
      
      .empty-description {
        font-size: 12px;
        margin-bottom: 16px;
      }
    }
  }
}
</style>