<template>
  <div v-if="showMonitor" class="performance-monitor" :class="monitorClass">
    <div class="monitor-header" @click="toggleExpanded">
      <span class="monitor-title">性能监控</span>
      <el-icon class="toggle-icon" :class="{ expanded: isExpanded }">
        <ArrowDown />
      </el-icon>
    </div>
    
    <div v-show="isExpanded" class="monitor-content">
      <div class="metric-item">
        <span class="metric-label">FPS:</span>
        <span class="metric-value" :class="getFPSClass(metrics.fps)">
          {{ metrics.fps }}
        </span>
      </div>
      
      <div class="metric-item">
        <span class="metric-label">内存:</span>
        <span class="metric-value" :class="getMemoryClass(metrics.memoryUsage)">
          {{ Math.round(metrics.memoryUsage) }}MB
        </span>
      </div>
      
      <div class="metric-item">
        <span class="metric-label">加载:</span>
        <span class="metric-value">
          {{ Math.round(metrics.loadTime) }}ms
        </span>
      </div>
      
      <div class="metric-item">
        <span class="metric-label">网络:</span>
        <span class="metric-value" :class="getNetworkClass(metrics.networkLatency)">
          {{ Math.round(metrics.networkLatency) }}ms
        </span>
      </div>
      
      <div class="metric-item">
        <span class="metric-label">评分:</span>
        <span class="metric-value" :class="getScoreClass(performanceScore)">
          {{ performanceScore }} ({{ performanceGrade }})
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ArrowDown } from '@element-plus/icons-vue'
import { useGlobalPerformanceMonitor } from '@/composables/usePerformanceOptimization'

const props = defineProps<{
  showMonitor?: boolean
}>()

// 性能监控
const { metrics, performanceScore, performanceGrade } = useGlobalPerformanceMonitor()

// 状态
const isExpanded = ref(false)

// 计算属性
const showMonitor = computed(() => {
  return props.showMonitor && process.env.NODE_ENV === 'development'
})

const monitorClass = computed(() => {
  const score = performanceScore.value
  if (score >= 90) return 'excellent'
  if (score >= 80) return 'good'
  if (score >= 70) return 'fair'
  if (score >= 60) return 'poor'
  return 'critical'
})

// 方法
const toggleExpanded = () => {
  isExpanded.value = !isExpanded.value
}

const getFPSClass = (fps: number) => {
  if (fps >= 55) return 'excellent'
  if (fps >= 45) return 'good'
  if (fps >= 30) return 'fair'
  return 'poor'
}

const getMemoryClass = (memory: number) => {
  if (memory <= 50) return 'excellent'
  if (memory <= 100) return 'good'
  if (memory <= 200) return 'fair'
  return 'poor'
}

const getNetworkClass = (latency: number) => {
  if (latency <= 100) return 'excellent'
  if (latency <= 300) return 'good'
  if (latency <= 500) return 'fair'
  return 'poor'
}

const getScoreClass = (score: number) => {
  if (score >= 90) return 'excellent'
  if (score >= 80) return 'good'
  if (score >= 70) return 'fair'
  if (score >= 60) return 'poor'
  return 'critical'
}
</script>

<style lang="scss" scoped>
.performance-monitor {
  position: fixed;
  top: 10px;
  right: 10px;
  background: rgba(0, 0, 0, 0.9);
  color: white;
  border-radius: 6px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
  z-index: 9999;
  min-width: 200px;
  user-select: none;
  
  &.excellent {
    border-left: 4px solid #67C23A;
  }
  
  &.good {
    border-left: 4px solid #409EFF;
  }
  
  &.fair {
    border-left: 4px solid #E6A23C;
  }
  
  &.poor {
    border-left: 4px solid #F56C6C;
  }
  
  &.critical {
    border-left: 4px solid #F56C6C;
    animation: pulse 2s infinite;
  }
}

.monitor-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  cursor: pointer;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  
  .monitor-title {
    font-weight: 600;
  }
  
  .toggle-icon {
    transition: transform 0.3s ease;
    
    &.expanded {
      transform: rotate(180deg);
    }
  }
}

.monitor-content {
  padding: 8px 12px;
}

.metric-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
  
  &:last-child {
    margin-bottom: 0;
  }
  
  .metric-label {
    color: rgba(255, 255, 255, 0.8);
  }
  
  .metric-value {
    font-weight: 600;
    
    &.excellent {
      color: #67C23A;
    }
    
    &.good {
      color: #409EFF;
    }
    
    &.fair {
      color: #E6A23C;
    }
    
    &.poor {
      color: #F56C6C;
    }
    
    &.critical {
      color: #F56C6C;
      animation: blink 1s infinite;
    }
  }
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}

@keyframes blink {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

// 移动端优化
@media (max-width: 768px) {
  .performance-monitor {
    top: 60px;
    right: 8px;
    font-size: 11px;
    min-width: 180px;
  }
  
  .monitor-header,
  .monitor-content {
    padding: 6px 10px;
  }
}
</style>