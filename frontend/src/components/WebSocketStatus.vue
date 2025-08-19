<template>
  <div class="websocket-status">
    <el-tooltip :content="tooltipContent" placement="bottom">
      <div class="status-indicator" :class="statusClass">
        <el-icon class="status-icon">
          <component :is="statusIcon" />
        </el-icon>
        <span class="status-text">{{ statusText }}</span>
        <el-button 
          v-if="showReconnectButton"
          size="small"
          type="primary"
          @click="handleReconnect"
          :loading="reconnecting"
        >
          重连
        </el-button>
      </div>
    </el-tooltip>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  Connection, 
  Close, 
  Loading, 
  Warning 
} from '@element-plus/icons-vue'
import { useMarketWebSocket } from '@/utils/websocket'
import type { ConnectionState } from '@/utils/websocket'

interface Props {
  showText?: boolean
  showReconnectButton?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showText: true,
  showReconnectButton: true
})

const { ws } = useMarketWebSocket()
const reconnecting = ref(false)

// 计算属性
const connectionState = computed<ConnectionState>(() => ws.getConnectionState())
const connected = computed(() => ws.connected.value)
const connecting = computed(() => ws.connecting.value)
const error = computed(() => ws.error.value)

const statusClass = computed(() => {
  switch (connectionState.value) {
    case 'connected':
      return 'status-connected'
    case 'connecting':
      return 'status-connecting'
    case 'error':
      return 'status-error'
    default:
      return 'status-disconnected'
  }
})

const statusIcon = computed(() => {
  switch (connectionState.value) {
    case 'connected':
      return Connection
    case 'connecting':
      return Loading
    case 'error':
      return Warning
    default:
      return Close
  }
})

const statusText = computed(() => {
  if (!props.showText) return ''
  
  switch (connectionState.value) {
    case 'connected':
      return '已连接'
    case 'connecting':
      return '连接中'
    case 'error':
      return '连接失败'
    default:
      return '未连接'
  }
})

const tooltipContent = computed(() => {
  const baseInfo = `WebSocket状态: ${statusText.value}`
  
  if (error.value) {
    return `${baseInfo}\n错误: ${error.value}`
  }
  
  if (connected.value) {
    return `${baseInfo}\n实时数据连接正常`
  }
  
  return baseInfo
})

const showReconnectButton = computed(() => {
  return props.showReconnectButton && 
         (connectionState.value === 'error' || connectionState.value === 'disconnected')
})

// 方法
const handleReconnect = async () => {
  try {
    reconnecting.value = true
    ElMessage.info('正在重新连接...')
    
    ws.forceReconnect()
    
    // 等待连接结果
    let attempts = 0
    const maxAttempts = 30 // 3秒超时
    
    while (attempts < maxAttempts) {
      if (ws.isConnected()) {
        ElMessage.success('WebSocket重连成功')
        break
      } else if (ws.getConnectionState() === 'error') {
        ElMessage.error('WebSocket重连失败')
        break
      }
      
      await new Promise(resolve => setTimeout(resolve, 100))
      attempts++
    }
    
    if (attempts >= maxAttempts) {
      ElMessage.warning('WebSocket连接超时，请稍后重试')
    }
    
  } catch (err: any) {
    console.error('WebSocket重连失败:', err)
    ElMessage.error('WebSocket重连失败')
  } finally {
    reconnecting.value = false
  }
}
</script>

<style scoped lang="scss">
.websocket-status {
  .status-indicator {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
    transition: all 0.3s ease;
    
    .status-icon {
      font-size: 14px;
    }
    
    .status-text {
      font-weight: 500;
    }
    
    &.status-connected {
      color: #67c23a;
      background-color: rgba(103, 194, 58, 0.1);
      
      .status-icon {
        animation: pulse 2s infinite;
      }
    }
    
    &.status-connecting {
      color: #e6a23c;
      background-color: rgba(230, 162, 60, 0.1);
      
      .status-icon {
        animation: spin 1s linear infinite;
      }
    }
    
    &.status-error {
      color: #f56c6c;
      background-color: rgba(245, 108, 108, 0.1);
      
      .status-icon {
        animation: shake 0.5s ease-in-out;
      }
    }
    
    &.status-disconnected {
      color: #909399;
      background-color: rgba(144, 147, 153, 0.1);
    }
  }
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
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

@keyframes shake {
  0%, 100% {
    transform: translateX(0);
  }
  25% {
    transform: translateX(-2px);
  }
  75% {
    transform: translateX(2px);
  }
}
</style>