<template>
  <div class="global-components">
    <!-- 全局加载指示器 -->
    <div v-if="globalLoading" class="global-loading-overlay">
      <div class="loading-content">
        <el-icon class="loading-icon" :size="40">
          <Loading />
        </el-icon>
        <div class="loading-text">{{ loadingText }}</div>
      </div>
    </div>

    <!-- 全局消息提示 -->
    <div class="global-messages">
      <!-- 这里可以添加自定义的全局消息组件 -->
    </div>

    <!-- 网络状态指示器 -->
    <div v-if="!isOnline" class="network-status offline">
      <el-icon><WifiOff /></el-icon>
      <span>网络连接已断开</span>
    </div>

    <!-- 更新提示 -->
    <div v-if="hasUpdate" class="update-notification">
      <div class="update-content">
        <el-icon><Refresh /></el-icon>
        <span>发现新版本</span>
        <el-button type="primary" size="small" @click="handleUpdate">
          更新
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { Loading, WifiOff, Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

// 全局状态
const globalLoading = ref(false)
const loadingText = ref('加载中...')
const isOnline = ref(navigator.onLine)
const hasUpdate = ref(false)

// 网络状态监听
const handleOnline = () => {
  isOnline.value = true
  ElMessage.success('网络连接已恢复')
}

const handleOffline = () => {
  isOnline.value = false
  ElMessage.warning('网络连接已断开')
}

// 更新处理
const handleUpdate = () => {
  window.location.reload()
}

// 生命周期
onMounted(() => {
  window.addEventListener('online', handleOnline)
  window.addEventListener('offline', handleOffline)
})

onUnmounted(() => {
  window.removeEventListener('online', handleOnline)
  window.removeEventListener('offline', handleOffline)
})
</script>

<style lang="scss" scoped>
.global-components {
  position: relative;
  z-index: 9999;
}

.global-loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  
  .loading-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 16px;
    
    .loading-icon {
      animation: spin 1s linear infinite;
      color: var(--el-color-primary);
    }
    
    .loading-text {
      font-size: 14px;
      color: var(--el-text-color-secondary);
    }
  }
}

.network-status {
  position: fixed;
  top: 70px;
  left: 50%;
  transform: translateX(-50%);
  background: var(--el-color-danger);
  color: white;
  padding: 8px 16px;
  border-radius: 20px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  z-index: 9998;
  
  &.offline {
    animation: slideDown 0.3s ease-out;
  }
}

.update-notification {
  position: fixed;
  bottom: 20px;
  right: 20px;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  z-index: 9998;
  
  .update-content {
    display: flex;
    align-items: center;
    gap: 12px;
    
    .el-icon {
      color: var(--el-color-primary);
    }
    
    span {
      font-size: 14px;
      color: var(--el-text-color-primary);
    }
  }
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@keyframes slideDown {
  from {
    transform: translateX(-50%) translateY(-100%);
    opacity: 0;
  }
  to {
    transform: translateX(-50%) translateY(0);
    opacity: 1;
  }
}

// 移动端优化
@media (max-width: 768px) {
  .network-status {
    top: 60px;
    font-size: 13px;
    padding: 6px 12px;
  }
  
  .update-notification {
    bottom: 80px;
    right: 16px;
    left: 16px;
    
    .update-content {
      justify-content: space-between;
    }
  }
}
</style>