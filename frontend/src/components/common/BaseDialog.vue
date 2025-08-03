<template>
  <el-dialog
    v-model="dialogVisible"
    :title="title"
    :width="width"
    :fullscreen="fullscreen"
    :top="top"
    :modal="modal"
    :modal-class="modalClass"
    :append-to-body="appendToBody"
    :lock-scroll="lockScroll"
    :custom-class="customClass"
    :open-delay="openDelay"
    :close-delay="closeDelay"
    :close-on-click-modal="closeOnClickModal"
    :close-on-press-escape="closeOnPressEscape"
    :show-close="showClose"
    :before-close="handleBeforeClose"
    :center="center"
    :align-center="alignCenter"
    :destroy-on-close="destroyOnClose"
    @open="handleOpen"
    @opened="handleOpened"
    @close="handleClose"
    @closed="handleClosed"
  >
    <!-- 自定义标题 -->
    <template v-if="$slots.title" #title>
      <slot name="title" />
    </template>
    
    <!-- 对话框内容 -->
    <div class="dialog-content">
      <!-- 加载状态 -->
      <LoadingState 
        v-if="loading" 
        :text="loadingText"
        :overlay="true"
      />
      
      <!-- 主要内容 -->
      <slot :loading="loading" />
    </div>
    
    <!-- 自定义底部 -->
    <template #footer>
      <slot name="footer" :loading="loading" :confirm="handleConfirm" :cancel="handleCancel">
        <div class="dialog-footer">
          <el-button 
            v-if="showCancel"
            @click="handleCancel"
            :disabled="loading"
          >
            {{ cancelText }}
          </el-button>
          <el-button 
            v-if="showConfirm"
            type="primary" 
            @click="handleConfirm"
            :loading="loading"
          >
            {{ confirmText }}
          </el-button>
        </div>
      </slot>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ElDialog, ElButton } from 'element-plus'
import LoadingState from './LoadingState.vue'

interface Props {
  modelValue: boolean
  title?: string
  width?: string | number
  fullscreen?: boolean
  top?: string
  modal?: boolean
  modalClass?: string
  appendToBody?: boolean
  lockScroll?: boolean
  customClass?: string
  openDelay?: number
  closeDelay?: number
  closeOnClickModal?: boolean
  closeOnPressEscape?: boolean
  showClose?: boolean
  center?: boolean
  alignCenter?: boolean
  destroyOnClose?: boolean
  loading?: boolean
  loadingText?: string
  showCancel?: boolean
  showConfirm?: boolean
  cancelText?: string
  confirmText?: string
  beforeClose?: (done: () => void) => void
}

const props = withDefaults(defineProps<Props>(), {
  width: '50%',
  fullscreen: false,
  top: '15vh',
  modal: true,
  appendToBody: false,
  lockScroll: true,
  openDelay: 0,
  closeDelay: 0,
  closeOnClickModal: true,
  closeOnPressEscape: true,
  showClose: true,
  center: false,
  alignCenter: false,
  destroyOnClose: false,
  loading: false,
  loadingText: '处理中...',
  showCancel: true,
  showConfirm: true,
  cancelText: '取消',
  confirmText: '确定'
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'open': []
  'opened': []
  'close': []
  'closed': []
  'confirm': []
  'cancel': []
}>()

// 计算属性
const dialogVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// 事件处理
const handleBeforeClose = (done: () => void) => {
  if (props.beforeClose) {
    props.beforeClose(done)
  } else {
    done()
  }
}

const handleOpen = () => {
  emit('open')
}

const handleOpened = () => {
  emit('opened')
}

const handleClose = () => {
  emit('close')
}

const handleClosed = () => {
  emit('closed')
}

const handleConfirm = () => {
  emit('confirm')
}

const handleCancel = () => {
  emit('cancel')
  dialogVisible.value = false
}
</script>

<style lang="scss" scoped>
.dialog-content {
  position: relative;
  min-height: 100px;
}

.dialog-footer {
  text-align: right;
  
  .el-button + .el-button {
    margin-left: 12px;
  }
}

:deep(.el-dialog) {
  border-radius: 8px;
  
  .el-dialog__header {
    padding: 20px 20px 10px;
    border-bottom: 1px solid var(--el-border-color-lighter);
    
    .el-dialog__title {
      font-size: 16px;
      font-weight: 600;
    }
  }
  
  .el-dialog__body {
    padding: 20px;
  }
  
  .el-dialog__footer {
    padding: 10px 20px 20px;
    border-top: 1px solid var(--el-border-color-lighter);
  }
}
</style>