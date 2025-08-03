<template>
  <teleport to="body">
    <transition name="loading-fade">
      <div v-if="isLoading" class="global-loading-overlay">
        <div class="loading-container">
          <div class="loading-spinner">
            <div class="spinner-ring"></div>
            <div class="spinner-ring"></div>
            <div class="spinner-ring"></div>
          </div>
          <div class="loading-text">{{ loadingText }}</div>
          <div v-if="showProgress" class="loading-progress">
            <div class="progress-bar">
              <div 
                class="progress-fill" 
                :style="{ width: `${progress}%` }"
              ></div>
            </div>
            <div class="progress-text">{{ progress }}%</div>
          </div>
        </div>
      </div>
    </transition>
  </teleport>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useAppStore } from '@/stores/app'

interface Props {
  showProgress?: boolean
  progress?: number
}

const props = withDefaults(defineProps<Props>(), {
  showProgress: false,
  progress: 0
})

const appStore = useAppStore()

const isLoading = computed(() => appStore.isLoading)
const loadingText = computed(() => {
  const loadingStates = appStore.loadingStates
  const activeLoadings = Object.keys(loadingStates).filter(key => loadingStates[key])
  if (activeLoadings.length === 0) return '加载中...'
  
  const loadingMessages: Record<string, string> = {
    'user_login': '正在登录...',
    'data_loading': '正在加载数据...',
    'order_processing': '正在处理订单...',
    'position_updating': '正在更新持仓...',
    'market_data': '正在获取市场数据...',
    'chart_rendering': '正在渲染图表...',
    'performance_optimization': '正在优化性能...',
    'file_upload': '正在上传文件...',
    'data_export': '正在导出数据...',
    'system_maintenance': '系统维护中...'
  }
  
  return loadingMessages[activeLoadings[0]] || '处理中...'
})
</script>

<style scoped>
.global-loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.loading-container {
  background: var(--el-bg-color);
  border-radius: 12px;
  padding: 32px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  text-align: center;
  min-width: 200px;
}

.loading-spinner {
  position: relative;
  width: 60px;
  height: 60px;
  margin: 0 auto 20px;
}

.spinner-ring {
  position: absolute;
  width: 100%;
  height: 100%;
  border: 3px solid transparent;
  border-top: 3px solid var(--el-color-primary);
  border-radius: 50%;
  animation: spin 1.2s linear infinite;
}

.spinner-ring:nth-child(2) {
  width: 80%;
  height: 80%;
  top: 10%;
  left: 10%;
  border-top-color: var(--el-color-success);
  animation-duration: 1.5s;
  animation-direction: reverse;
}

.spinner-ring:nth-child(3) {
  width: 60%;
  height: 60%;
  top: 20%;
  left: 20%;
  border-top-color: var(--el-color-warning);
  animation-duration: 1.8s;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-text {
  font-size: 16px;
  color: var(--el-text-color-primary);
  margin-bottom: 16px;
  font-weight: 500;
}

.loading-progress {
  margin-top: 20px;
}

.progress-bar {
  width: 100%;
  height: 6px;
  background: var(--el-border-color-light);
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 8px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--el-color-primary), var(--el-color-success));
  border-radius: 3px;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 14px;
  color: var(--el-text-color-regular);
}

.loading-fade-enter-active,
.loading-fade-leave-active {
  transition: opacity 0.3s ease;
}

.loading-fade-enter-from,
.loading-fade-leave-to {
  opacity: 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .loading-container {
    padding: 24px;
    min-width: 160px;
  }
  
  .loading-spinner {
    width: 48px;
    height: 48px;
  }
  
  .loading-text {
    font-size: 14px;
  }
}

/* 减少动画偏好 */
@media (prefers-reduced-motion: reduce) {
  .spinner-ring {
    animation: none;
  }
  
  .loading-fade-enter-active,
  .loading-fade-leave-active {
    transition: none;
  }
}
</style>