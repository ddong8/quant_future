<template>
  <div class="error-boundary">
    <div v-if="hasError" class="error-display">
      <div class="error-icon">⚠️</div>
      <h3>组件加载出错</h3>
      <p class="error-message">{{ errorMessage }}</p>
      <div class="error-actions">
        <button @click="retry" class="retry-btn">重试</button>
        <button @click="hideError" class="hide-btn">隐藏</button>
      </div>
    </div>
    <div v-else>
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onErrorCaptured } from 'vue'

interface Props {
  fallbackMessage?: string
  showRetry?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  fallbackMessage: '组件渲染时发生错误',
  showRetry: true
})

const emit = defineEmits<{
  error: [error: Error]
  retry: []
}>()

const hasError = ref(false)
const errorMessage = ref('')

// 捕获子组件错误
onErrorCaptured((error: Error) => {
  console.error('ErrorBoundary 捕获到错误:', error)
  
  hasError.value = true
  errorMessage.value = error.message || props.fallbackMessage
  
  emit('error', error)
  
  // 阻止错误继续向上传播
  return false
})

// 重试功能
const retry = () => {
  hasError.value = false
  errorMessage.value = ''
  emit('retry')
}

// 隐藏错误
const hideError = () => {
  hasError.value = false
}
</script>

<style scoped>
.error-boundary {
  width: 100%;
}

.error-display {
  padding: 20px;
  margin: 10px 0;
  background: #fff5f5;
  border: 1px solid #fed7d7;
  border-radius: 8px;
  text-align: center;
}

.error-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.error-display h3 {
  color: #e53e3e;
  margin: 0 0 12px 0;
  font-size: 18px;
}

.error-message {
  color: #742a2a;
  margin: 0 0 20px 0;
  font-size: 14px;
}

.error-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.retry-btn, .hide-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.retry-btn {
  background: #3182ce;
  color: white;
}

.retry-btn:hover {
  background: #2c5aa0;
}

.hide-btn {
  background: #e2e8f0;
  color: #4a5568;
}

.hide-btn:hover {
  background: #cbd5e0;
}
</style>