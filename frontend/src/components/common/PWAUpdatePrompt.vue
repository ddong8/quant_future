<template>
  <div v-if="showUpdatePrompt" class="pwa-update-prompt">
    <div class="update-content">
      <div class="update-icon">
        <el-icon :size="24"><Refresh /></el-icon>
      </div>
      <div class="update-text">
        <div class="update-title">发现新版本</div>
        <div class="update-description">
          应用已更新，点击刷新以获取最新功能
        </div>
      </div>
      <div class="update-actions">
        <el-button size="small" @click="dismissUpdate">
          稍后
        </el-button>
        <el-button type="primary" size="small" @click="updateApp">
          立即更新
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

// 状态
const showUpdatePrompt = ref(false)
const registration = ref<ServiceWorkerRegistration | null>(null)

// 检查更新
const checkForUpdates = async () => {
  if ('serviceWorker' in navigator) {
    try {
      const reg = await navigator.serviceWorker.getRegistration()
      if (reg) {
        registration.value = reg
        
        // 监听更新
        reg.addEventListener('updatefound', () => {
          const newWorker = reg.installing
          if (newWorker) {
            newWorker.addEventListener('statechange', () => {
              if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                showUpdatePrompt.value = true
              }
            })
          }
        })
        
        // 检查是否有等待的更新
        if (reg.waiting) {
          showUpdatePrompt.value = true
        }
      }
    } catch (error) {
      console.warn('Service Worker registration failed:', error)
    }
  }
}

// 更新应用
const updateApp = () => {
  if (registration.value?.waiting) {
    registration.value.waiting.postMessage({ type: 'SKIP_WAITING' })
    
    // 监听控制器变化
    navigator.serviceWorker.addEventListener('controllerchange', () => {
      window.location.reload()
    })
  } else {
    window.location.reload()
  }
  
  showUpdatePrompt.value = false
}

// 忽略更新
const dismissUpdate = () => {
  showUpdatePrompt.value = false
  ElMessage.info('您可以稍后在设置中手动更新')
}

// 生命周期
onMounted(() => {
  checkForUpdates()
  
  // 定期检查更新
  setInterval(checkForUpdates, 60000) // 每分钟检查一次
})
</script>

<style lang="scss" scoped>
.pwa-update-prompt {
  position: fixed;
  bottom: 20px;
  left: 20px;
  right: 20px;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  z-index: 9998;
  animation: slideUp 0.3s ease-out;
  
  @media (min-width: 768px) {
    left: auto;
    right: 20px;
    width: 400px;
  }
}

.update-content {
  display: flex;
  align-items: flex-start;
  padding: 20px;
  gap: 16px;
}

.update-icon {
  flex-shrink: 0;
  color: var(--el-color-primary);
  margin-top: 2px;
}

.update-text {
  flex: 1;
  
  .update-title {
    font-size: 16px;
    font-weight: 600;
    color: var(--el-text-color-primary);
    margin-bottom: 4px;
  }
  
  .update-description {
    font-size: 14px;
    color: var(--el-text-color-secondary);
    line-height: 1.4;
  }
}

.update-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
  margin-top: 4px;
}

@keyframes slideUp {
  from {
    transform: translateY(100%);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

// 移动端优化
@media (max-width: 768px) {
  .pwa-update-prompt {
    bottom: 80px; // 为底部导航留出空间
    left: 16px;
    right: 16px;
  }
  
  .update-content {
    padding: 16px;
    gap: 12px;
  }
  
  .update-text {
    .update-title {
      font-size: 15px;
    }
    
    .update-description {
      font-size: 13px;
    }
  }
  
  .update-actions {
    flex-direction: column;
    width: 80px;
    
    .el-button {
      width: 100%;
    }
  }
}

// 暗色主题优化
.dark {
  .pwa-update-prompt {
    background: var(--el-bg-color-page);
    border-color: var(--el-border-color-light);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
  }
}
</style>