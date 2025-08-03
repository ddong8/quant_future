<template>
  <div class="loading-state" :class="{ 'is-overlay': overlay }">
    <div class="loading-content">
      <!-- 自定义加载图标 -->
      <slot name="icon">
        <el-icon class="loading-icon" :size="iconSize">
          <Loading />
        </el-icon>
      </slot>
      
      <!-- 加载文本 -->
      <div v-if="text" class="loading-text">
        {{ text }}
      </div>
      
      <!-- 加载描述 -->
      <div v-if="description" class="loading-description">
        {{ description }}
      </div>
      
      <!-- 进度条 -->
      <div v-if="showProgress" class="loading-progress">
        <el-progress 
          :percentage="progress" 
          :status="progressStatus"
          :stroke-width="progressStrokeWidth"
          :show-text="showProgressText"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ElIcon, ElProgress } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'

interface Props {
  text?: string
  description?: string
  overlay?: boolean
  iconSize?: number
  showProgress?: boolean
  progress?: number
  progressStatus?: 'success' | 'exception' | 'warning'
  progressStrokeWidth?: number
  showProgressText?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  text: '加载中...',
  overlay: false,
  iconSize: 24,
  showProgress: false,
  progress: 0,
  progressStrokeWidth: 6,
  showProgressText: true
})
</script>

<style lang="scss" scoped>
.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  
  &.is-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(255, 255, 255, 0.9);
    z-index: 1000;
  }
  
  .loading-content {
    text-align: center;
    
    .loading-icon {
      color: var(--el-color-primary);
      animation: rotate 2s linear infinite;
      margin-bottom: 16px;
    }
    
    .loading-text {
      font-size: 14px;
      color: var(--el-text-color-primary);
      margin-bottom: 8px;
    }
    
    .loading-description {
      font-size: 12px;
      color: var(--el-text-color-secondary);
      margin-bottom: 16px;
    }
    
    .loading-progress {
      width: 200px;
      margin: 0 auto;
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