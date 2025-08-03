/**
 * WebSocket连接组合式函数
 */

import { ref, onUnmounted } from 'vue'
import { useUserStore } from '@/stores/user'

export function useWebSocket() {
  const userStore = useUserStore()
  const socket = ref<WebSocket | null>(null)
  const isConnected = ref(false)
  const reconnectAttempts = ref(0)
  const maxReconnectAttempts = 5
  const reconnectInterval = ref<NodeJS.Timeout | null>(null)

  // 连接WebSocket
  const connect = (onMessage?: (event: MessageEvent) => void) => {
    if (!userStore.user?.id) {
      console.warn('用户未登录，无法建立WebSocket连接')
      return
    }

    const wsUrl = `${import.meta.env.VITE_WS_URL || 'ws://localhost:8000'}/api/v1/backtests/ws/${userStore.user.id}`
    
    try {
      socket.value = new WebSocket(wsUrl)

      socket.value.onopen = () => {
        console.log('WebSocket连接已建立')
        isConnected.value = true
        reconnectAttempts.value = 0
        
        // 发送ping消息保持连接
        startHeartbeat()
      }

      socket.value.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          
          // 处理系统消息
          if (data.type === 'pong') {
            // 心跳响应，不需要特殊处理
            return
          }
          
          // 调用外部消息处理器
          if (onMessage) {
            onMessage(event)
          }
        } catch (error) {
          console.error('解析WebSocket消息失败:', error)
        }
      }

      socket.value.onclose = (event) => {
        console.log('WebSocket连接已关闭:', event.code, event.reason)
        isConnected.value = false
        stopHeartbeat()
        
        // 如果不是主动关闭，尝试重连
        if (event.code !== 1000 && reconnectAttempts.value < maxReconnectAttempts) {
          scheduleReconnect(onMessage)
        }
      }

      socket.value.onerror = (error) => {
        console.error('WebSocket连接错误:', error)
        isConnected.value = false
      }

    } catch (error) {
      console.error('创建WebSocket连接失败:', error)
    }
  }

  // 断开连接
  const disconnect = () => {
    if (socket.value) {
      socket.value.close(1000, '主动断开连接')
      socket.value = null
    }
    isConnected.value = false
    stopHeartbeat()
    
    if (reconnectInterval.value) {
      clearTimeout(reconnectInterval.value)
      reconnectInterval.value = null
    }
  }

  // 发送消息
  const send = (message: any) => {
    if (socket.value && isConnected.value) {
      try {
        const messageStr = typeof message === 'string' ? message : JSON.stringify(message)
        socket.value.send(messageStr)
        return true
      } catch (error) {
        console.error('发送WebSocket消息失败:', error)
        return false
      }
    }
    return false
  }

  // 发送ping消息
  const ping = () => {
    send({
      type: 'ping',
      timestamp: new Date().toISOString()
    })
  }

  // 订阅主题
  const subscribe = (topic: string) => {
    send({
      type: 'subscribe',
      topic: topic
    })
  }

  // 取消订阅
  const unsubscribe = (topic: string) => {
    send({
      type: 'unsubscribe',
      topic: topic
    })
  }

  // 获取连接状态
  const getStatus = () => {
    send({
      type: 'get_status'
    })
  }

  // 心跳机制
  let heartbeatInterval: NodeJS.Timeout | null = null

  const startHeartbeat = () => {
    stopHeartbeat()
    heartbeatInterval = setInterval(() => {
      if (isConnected.value) {
        ping()
      }
    }, 30000) // 每30秒发送一次心跳
  }

  const stopHeartbeat = () => {
    if (heartbeatInterval) {
      clearInterval(heartbeatInterval)
      heartbeatInterval = null
    }
  }

  // 重连机制
  const scheduleReconnect = (onMessage?: (event: MessageEvent) => void) => {
    const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.value), 30000) // 指数退避，最大30秒
    
    console.log(`${delay / 1000}秒后尝试重连 (第${reconnectAttempts.value + 1}次)`)
    
    reconnectInterval.value = setTimeout(() => {
      reconnectAttempts.value++
      connect(onMessage)
    }, delay)
  }

  // 组件卸载时自动断开连接
  onUnmounted(() => {
    disconnect()
  })

  return {
    socket,
    isConnected,
    reconnectAttempts,
    connect,
    disconnect,
    send,
    ping,
    subscribe,
    unsubscribe,
    getStatus
  }
}

// WebSocket消息类型定义
export interface WebSocketMessage {
  type: string
  timestamp: string
  [key: string]: any
}

// 回测相关消息类型
export interface BacktestProgressMessage extends WebSocketMessage {
  type: 'backtest_progress'
  task_id: string
  backtest_id: number
  progress: number
  status: string
}

export interface BacktestCompletedMessage extends WebSocketMessage {
  type: 'backtest_completed'
  task_id: string
  backtest_id: number
  status: string
  actual_duration: number
}

export interface BacktestFailedMessage extends WebSocketMessage {
  type: 'backtest_failed'
  task_id: string
  backtest_id: number
  status: string
  error_message: string
  retry_count: number
}

// 系统通知消息
export interface SystemNotificationMessage extends WebSocketMessage {
  type: 'system_notification'
  level: 'info' | 'warning' | 'error' | 'success'
  message: string
}

// 连接状态消息
export interface StatusResponseMessage extends WebSocketMessage {
  type: 'status_response'
  data: {
    total_connections: number
    online_users: number
    connections_per_user: Record<string, number>
  }
}