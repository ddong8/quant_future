<template>
  <el-dialog
    v-model="dialogVisible"
    :title="title"
    :width="width"
    :center="true"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    :show-close="false"
    custom-class="confirm-dialog"
  >
    <div class="confirm-content">
      <!-- 图标 -->
      <div class="confirm-icon">
        <el-icon :size="48" :color="iconColor">
          <component :is="icon" />
        </el-icon>
      </div>
      
      <!-- 内容 -->
      <div class="confirm-text">
        <div class="confirm-title">{{ title }}</div>
        <div v-if="content" class="confirm-message">{{ content }}</div>
        
        <!-- 自定义内容 -->
        <div v-if="$slots.default" class="confirm-custom">
          <slot />
        </div>
      </div>
    </div>
    
    <template #footer>
      <div class="confirm-footer">
        <el-button 
          @click="handleCancel"
          :disabled="loading"
        >
          {{ cancelText }}
        </el-button>
        <el-button 
          :type="confirmType"
          @click="handleConfirm"
          :loading="loading"
        >
          {{ confirmText }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ElDialog, ElButton, ElIcon } from 'element-plus'
import { 
  QuestionFilled, 
  WarningFilled, 
  InfoFilled, 
  CircleCheckFilled,
  CircleCloseFilled 
} from '@element-plus/icons-vue'

interface Props {
  modelValue: boolean
  type?: 'info' | 'success' | 'warning' | 'error' | 'confirm'
  title?: string
  content?: string
  width?: string
  confirmText?: string
  cancelText?: string
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  type: 'confirm',
  title: '确认操作',
  width: '420px',
  confirmText: '确定',
  cancelText: '取消',
  loading: false
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'confirm': []
  'cancel': []
}>()

// 类型配置
const typeConfigs = {
  info: {
    icon: InfoFilled,
    color: '#409EFF',
    confirmType: 'primary' as const
  },
  success: {
    icon: CircleCheckFilled,
    color: '#67C23A',
    confirmType: 'success' as const
  },
  warning: {
    icon: WarningFilled,
    color: '#E6A23C',
    confirmType: 'warning' as const
  },
  error: {
    icon: CircleCloseFilled,
    color: '#F56C6C',
    confirmType: 'danger' as const
  },
  confirm: {
    icon: QuestionFilled,
    color: '#E6A23C',
    confirmType: 'primary' as const
  }
}

// 计算属性
const dialogVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const config = computed(() => {
  return typeConfigs[props.type]
})

const icon = computed(() => {
  return config.value.icon
})

const iconColor = computed(() => {
  return config.value.color
})

const confirmType = computed(() => {
  return config.value.confirmType
})

// 事件处理
const handleConfirm = () => {
  emit('confirm')
}

const handleCancel = () => {
  emit('cancel')
  dialogVisible.value = false
}
</script>

<style lang="scss" scoped>
:deep(.confirm-dialog) {
  .el-dialog__header {
    display: none;
  }
  
  .el-dialog__body {
    padding: 32px 24px 24px;
  }
  
  .el-dialog__footer {
    padding: 0 24px 32px;
    text-align: center;
  }
}

.confirm-content {
  text-align: center;
  
  .confirm-icon {
    margin-bottom: 16px;
  }
  
  .confirm-text {
    .confirm-title {
      font-size: 16px;
      font-weight: 600;
      color: var(--el-text-color-primary);
      margin-bottom: 8px;
      line-height: 1.5;
    }
    
    .confirm-message {
      font-size: 14px;
      color: var(--el-text-color-regular);
      line-height: 1.6;
      margin-bottom: 16px;
    }
    
    .confirm-custom {
      margin-top: 16px;
    }
  }
}

.confirm-footer {
  .el-button + .el-button {
    margin-left: 12px;
  }
}
</style>