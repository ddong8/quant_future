<template>
  <div v-if="hasError" class="error-boundary">
    <div class="error-container">
      <div class="error-icon">
        <el-icon size="48">
          <WarningFilled />
        </el-icon>
      </div>
      
      <div class="error-content">
        <h3 class="error-title">{{ errorTitle }}</h3>
        <p class="error-message">{{ errorMessage }}</p>
        
        <div v-if="showDetails && errorDetails" class="error-details">
          <el-collapse>
            <el-collapse-item title="错误详情" name="details">
              <pre class="error-stack">{{ errorDetails }}</pre>
            </el-collapse-item>
          </el-collapse>
        </div>
        
        <div class="error-actions">
          <el-button type="primary" @click="handleRetry">
            <el-icon><Refresh /></el-icon>
            重试
          </el-button>
          
          <el-button @click="handleReload">
            <el-icon><RefreshRight /></el-icon>
            刷新页面
          </el-button>
          
          <el-button 
            v-if="showReport" 
            type="warning" 
            @click="handleReport"
          >
            <el-icon><Warning /></el-icon>
            报告问题
          </el-button>
        </div>
      </div>
    </div>
  </div>
  
  <slot v-else />
</template>

<script setup lang="ts">
import { ref, onErrorCaptured, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { WarningFilled, Refresh, RefreshRight, Warning } from '@element-plus/icons-vue'

interface Props {
  fallbackTitle?: string
  fallbackMessage?: string
  showDetails?: boolean
  showReport?: boolean
  onError?: (error: Error, instance: any, info: string) => void
  onRetry?: () => void | Promise<void>
}

const props = withDefaults(defineProps<Props>(), {
  fallbackTitle: '页面出现错误',
  fallbackMessage: '抱歉，页面遇到了一些问题。请尝试刷新页面或联系技术支持。',
  showDetails: false,
  showReport: true
})

const emit = defineEmits<{
  error: [error: Error, instance: any, info: string]
  retry: []
  reload: []
  report: [error: Error, details: string]
}>()

const hasError = ref(false)
const errorTitle = ref('')
const errorMessage = ref('')
const errorDetails = ref('')
const retryCount = ref(0)
const maxRetries = 3

// 捕获子组件错误
onErrorCaptured((error: Error, instance: any, info: string) => {
  console.error('ErrorBoundary caught an error:', error)
  console.error('Component instance:', instance)
  console.error('Error info:', info)
  
  // 设置错误状态
  hasError.value = true
  errorTitle.value = getErrorTitle(error)
  errorMessage.value = getErrorMessage(error)
  errorDetails.value = getErrorDetails(error, info)
  
  // 调用错误回调
  if (props.onError) {
    props.onError(error, instance, info)
  }
  
  // 发送错误事件
  emit('error', error, instance, info)
  
  // 自动报告严重错误
  if (isCriticalError(error)) {
    reportError(error, errorDetails.value)
  }
  
  // 阻止错误继续向上传播
  return false
})

// 获取错误标题
const getErrorTitle = (error: Error): string => {
  if (error.name === 'ChunkLoadError') {
    return '资源加载失败'
  }
  if (error.name === 'NetworkError') {
    return '网络连接错误'
  }
  if (error.message.includes('timeout')) {
    return '请求超时'
  }
  if (error.message.includes('permission')) {
    return '权限不足'
  }
  return props.fallbackTitle
}

// 获取错误消息
const getErrorMessage = (error: Error): string => {
  if (error.name === 'ChunkLoadError') {
    return '页面资源加载失败，可能是网络问题或版本更新导致。请刷新页面重试。'
  }
  if (error.name === 'NetworkError') {
    return '网络连接出现问题，请检查网络连接后重试。'
  }
  if (error.message.includes('timeout')) {
    return '请求超时，请检查网络连接或稍后重试。'
  }
  if (error.message.includes('permission')) {
    return '您没有足够的权限执行此操作，请联系管理员。'
  }
  return props.fallbackMessage
}

// 获取错误详情
const getErrorDetails = (error: Error, info: string): string => {
  const details = []
  
  details.push(`错误类型: ${error.name}`)
  details.push(`错误消息: ${error.message}`)
  details.push(`组件信息: ${info}`)
  
  if (error.stack) {
    details.push(`错误堆栈:\n${error.stack}`)
  }
  
  details.push(`时间: ${new Date().toLocaleString()}`)
  details.push(`用户代理: ${navigator.userAgent}`)
  details.push(`页面URL: ${window.location.href}`)
  
  return details.join('\n\n')
}

// 判断是否为严重错误
const isCriticalError = (error: Error): boolean => {
  const criticalErrors = [
    'ChunkLoadError',
    'SecurityError',
    'ReferenceError'
  ]
  return criticalErrors.includes(error.name)
}

// 重试处理
const handleRetry = async () => {
  if (retryCount.value >= maxRetries) {
    ElMessage.warning(`已达到最大重试次数 (${maxRetries})，请刷新页面`)
    return
  }
  
  try {
    retryCount.value++
    
    // 调用自定义重试逻辑
    if (props.onRetry) {
      await props.onRetry()
    }
    
    // 重置错误状态
    hasError.value = false
    errorTitle.value = ''
    errorMessage.value = ''
    errorDetails.value = ''
    
    emit('retry')
    
    // 等待下一个渲染周期
    await nextTick()
    
    ElMessage.success('重试成功')
  } catch (retryError) {
    console.error('Retry failed:', retryError)
    ElMessage.error('重试失败，请刷新页面')
  }
}

// 刷新页面
const handleReload = () => {
  emit('reload')
  window.location.reload()
}

// 报告错误
const handleReport = () => {
  const error = new Error(errorMessage.value)
  emit('report', error, errorDetails.value)
  reportError(error, errorDetails.value)
}

// 自动报告错误
const reportError = async (error: Error, details: string) => {
  try {
    // 这里可以集成错误报告服务，如 Sentry、Bugsnag 等
    const errorReport = {
      message: error.message,
      stack: error.stack,
      details,
      url: window.location.href,
      userAgent: navigator.userAgent,
      timestamp: new Date().toISOString(),
      userId: localStorage.getItem('userId') || 'anonymous'
    }
    
    // 发送到错误报告服务
    console.log('Error report:', errorReport)
    
    // 示例：发送到后端API
    // await fetch('/api/error-reports', {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify(errorReport)
    // })
    
    ElMessage.success('错误报告已发送')
  } catch (reportError) {
    console.error('Failed to report error:', reportError)
    ElMessage.error('错误报告发送失败')
  }
}

// 重置错误状态的方法（供外部调用）
const resetError = () => {
  hasError.value = false
  errorTitle.value = ''
  errorMessage.value = ''
  errorDetails.value = ''
  retryCount.value = 0
}

// 暴露方法给父组件
defineExpose({
  resetError,
  hasError
})
</script>

<style scoped>
.error-boundary {
  min-height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.error-container {
  max-width: 600px;
  text-align: center;
  background: var(--el-bg-color);
  border-radius: 12px;
  padding: 40px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border: 1px solid var(--el-border-color-light);
}

.error-icon {
  color: var(--el-color-warning);
  margin-bottom: 24px;
}

.error-title {
  font-size: 24px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin: 0 0 16px 0;
}

.error-message {
  font-size: 16px;
  color: var(--el-text-color-regular);
  line-height: 1.6;
  margin: 0 0 24px 0;
}

.error-details {
  margin: 24px 0;
  text-align: left;
}

.error-stack {
  background: var(--el-fill-color-light);
  border-radius: 6px;
  padding: 16px;
  font-size: 12px;
  line-height: 1.4;
  color: var(--el-text-color-regular);
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 300px;
  overflow-y: auto;
}

.error-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  flex-wrap: wrap;
}

.error-actions .el-button {
  min-width: 100px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .error-container {
    padding: 24px;
    margin: 0 16px;
  }
  
  .error-title {
    font-size: 20px;
  }
  
  .error-message {
    font-size: 14px;
  }
  
  .error-actions {
    flex-direction: column;
    align-items: center;
  }
  
  .error-actions .el-button {
    width: 100%;
    max-width: 200px;
  }
}

/* 暗色主题适配 */
.dark .error-container {
  background: var(--el-bg-color-page);
  border-color: var(--el-border-color);
}

.dark .error-stack {
  background: var(--el-fill-color-darker);
}
</style>