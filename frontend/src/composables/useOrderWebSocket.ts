/**
 * 订单WebSocket连接组合式函数
 */

import { ref, onUnmounted, computed } from 'vue'
import { ElMessage, ElNotification } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { useOrderStore } from '@/stores/order'

export interface OrderWebSocketMessage {
  type: string
  timestamp: string
  [key: string]: any
}

export interface OrderStatusChangedMessage extends OrderWebSocketMessage {
  type: 'order_status_changed'
  order_id: number
  order_uuid: string
  symbol: string
  side: string
  status: string
  old_status?: string
  filled_quantity: number
  remaining_quantity?: number
  fill_ratio: number
  is_active: boolean
  is_finished: boolean
}

export interface OrderCreatedMessage extends OrderWebSocketMessage {
  type: 'order_created'
  order_id: number
  order_uuid: string
  symbol: string
  side: string
  order_type: string
  quantity: number
  price?: number
  status: string
}

export interface OrderFilledMessage extends OrderWebSocketMessage {
  type: 'order_filled'
  order_id: number
  order_uuid: string
  symbol: string
  side: string
  fill_data: {
    fill_id: number
    quantity: number
    price: number
    value: number
    commission: number
    fill_time: string
  }
  order_status: {
    filled_quantity: number
    remaining_quantity?: number
    avg_fill_price?: number
    status: string
    fill_ratio: number
  }
}

export interface OrderCancelledMessage extends OrderWebSocketMessage {
  type: 'order_cancelled'
  order_id: number
  order_uuid: string
  symbol: string
  reason?: string
}

export interface RiskAlertMessage extends OrderWebSocketMessage {
  type: 'risk_alert'
  order_id: number
  alert_type: string
  message: string
  severity: 'info' | 'warning' | 'error' | 'critical'
}

export function useOrderWebSocket() {
  const authStore = useAuthStore()
  const orderStore = useOrderStore()
  
  const socket = ref<WebSocket | null>(null)
  const isConnected = ref(false)
  const reconnectAttempts = ref(0)
  const maxReconnectAttempts = 5
  const reconnectInterval = ref<NodeJS.Timeout | null>(null)
  const messageHandlers = ref<Map<string, Function>>(new Map())

  // 连接状态
  const connectionStatus = computed(() => {
    if (isConnected.value) return 'connected'
    if (reconnectAttempts.value > 0) return 'reconnecting'
    return 'disconnected'
  })

  // 连接WebSocket
  const connect = () => {
    if (!authStore.user?.id) {
      console.warn('用户未登录，无法建立订单WebSocket连接')
      return
    }

    const token = authStore.token
    const wsUrl = `${import.meta.env.VITE_WS_URL || 'ws://localhost:8000'}/api/v1/ws/orders/${authStore.user.id}${token ? `?token=${token}` : ''}`
    
    try {
      socket.value = new WebSocket(wsUrl)

      socket.value.onopen = () => {
        console.log('订单WebSocket连接已建立')
        isConnected.value = true
        reconnectAttempts.value = 0
        
        // 发送ping消息保持连接
        startHeartbeat()
        
        // 订阅订单更新
        subscribe('order_updates')
      }

      socket.value.onmessage = (event) => {
        try {
          const message: OrderWebSocketMessage = JSON.parse(event.data)
          handleMessage(message)
        } catch (error) {
          console.error('解析订单WebSocket消息失败:', error)
        }
      }

      socket.value.onclose = (event) => {
        console.log('订单WebSocket连接已关闭:', event.code, event.reason)
        isConnected.value = false
        stopHeartbeat()
        
        // 如果不是主动关闭，尝试重连
        if (event.code !== 1000 && reconnectAttempts.value < maxReconnectAttempts) {
          scheduleReconnect()
        }
      }

      socket.value.onerror = (error) => {
        console.error('订单WebSocket连接错误:', error)
        isConnected.value = false
      }

    } catch (error) {
      console.error('创建订单WebSocket连接失败:', error)
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
        console.error('发送订单WebSocket消息失败:', error)
        return false
      }
    }
    return false
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

  // 处理消息
  const handleMessage = (message: OrderWebSocketMessage) => {
    console.log('收到订单WebSocket消息:', message)
    
    // 调用注册的消息处理器
    const handler = messageHandlers.value.get(message.type)
    if (handler) {
      handler(message)
    }
    
    // 默认消息处理
    switch (message.type) {
      case 'order_status_changed':
        handleOrderStatusChanged(message as OrderStatusChangedMessage)
        break
      case 'order_created':
        handleOrderCreated(message as OrderCreatedMessage)
        break
      case 'order_filled':
        handleOrderFilled(message as OrderFilledMessage)
        break
      case 'order_cancelled':
        handleOrderCancelled(message as OrderCancelledMessage)
        break
      case 'order_updated':
        handleOrderUpdated(message)
        break
      case 'order_rejected':
        handleOrderRejected(message)
        break
      case 'order_expired':
        handleOrderExpired(message)
        break
      case 'order_error':
        handleOrderError(message)
        break
      case 'risk_alert':
        handleRiskAlert(message as RiskAlertMessage)
        break
      case 'batch_operation_result':
        handleBatchOperationResult(message)
        break
      case 'connection_established':
        console.log('订单WebSocket连接确认:', message.message)
        break
      case 'pong':
        // 心跳响应，不需要特殊处理
        break
      default:
        console.log('未处理的订单WebSocket消息类型:', message.type)
    }
  }

  // 注册消息处理器
  const onMessage = (messageType: string, handler: Function) => {
    messageHandlers.value.set(messageType, handler)
  }

  // 移除消息处理器
  const offMessage = (messageType: string) => {
    messageHandlers.value.delete(messageType)
  }

  // 处理订单状态变化
  const handleOrderStatusChanged = (message: OrderStatusChangedMessage) => {
    // 更新订单存储
    orderStore.updateOrderStatus(message.order_id, {
      status: message.status,
      filled_quantity: message.filled_quantity,
      remaining_quantity: message.remaining_quantity,
      fill_ratio: message.fill_ratio,
      is_active: message.is_active,
      is_finished: message.is_finished
    })
    
    // 显示通知
    const statusText = getStatusText(message.status)
    ElNotification({
      title: '订单状态更新',
      message: `${message.symbol} ${message.side.toUpperCase()} 订单状态变更为: ${statusText}`,
      type: getNotificationType(message.status),
      duration: 3000
    })
  }

  // 处理订单创建
  const handleOrderCreated = (message: OrderCreatedMessage) => {
    ElMessage.success(`订单创建成功: ${message.symbol} ${message.side.toUpperCase()}`)
  }

  // 处理订单成交
  const handleOrderFilled = (message: OrderFilledMessage) => {
    // 更新订单存储
    orderStore.updateOrderStatus(message.order_id, message.order_status)
    
    // 显示成交通知
    ElNotification({
      title: '订单成交',
      message: `${message.symbol} ${message.side.toUpperCase()} 成交 ${message.fill_data.quantity} @ ${message.fill_data.price}`,
      type: 'success',
      duration: 5000
    })
  }

  // 处理订单取消
  const handleOrderCancelled = (message: OrderCancelledMessage) => {
    ElNotification({
      title: '订单已取消',
      message: `${message.symbol} 订单已取消${message.reason ? `: ${message.reason}` : ''}`,
      type: 'warning',
      duration: 3000
    })
  }

  // 处理订单更新
  const handleOrderUpdated = (message: any) => {
    ElMessage.info(`订单 ${message.symbol} 已更新`)
  }

  // 处理订单拒绝
  const handleOrderRejected = (message: any) => {
    ElNotification({
      title: '订单被拒绝',
      message: `${message.symbol} 订单被拒绝: ${message.reason}`,
      type: 'error',
      duration: 5000
    })
  }

  // 处理订单过期
  const handleOrderExpired = (message: any) => {
    ElNotification({
      title: '订单已过期',
      message: `${message.symbol} 订单已过期`,
      type: 'warning',
      duration: 3000
    })
  }

  // 处理订单错误
  const handleOrderError = (message: any) => {
    ElNotification({
      title: '订单错误',
      message: `${message.symbol} 订单发生错误: ${message.error_message}`,
      type: 'error',
      duration: 5000
    })
  }

  // 处理风险警告
  const handleRiskAlert = (message: RiskAlertMessage) => {
    const typeMap = {
      info: 'info',
      warning: 'warning',
      error: 'error',
      critical: 'error'
    }
    
    ElNotification({
      title: '风险警告',
      message: message.message,
      type: typeMap[message.severity] as any,
      duration: message.severity === 'critical' ? 0 : 5000
    })
  }

  // 处理批量操作结果
  const handleBatchOperationResult = (message: any) => {
    const { operation, success_count, failed_count, total_count } = message
    
    ElNotification({
      title: '批量操作完成',
      message: `${operation}: 成功 ${success_count}/${total_count}，失败 ${failed_count}`,
      type: failed_count === 0 ? 'success' : 'warning',
      duration: 4000
    })
  }

  // 心跳机制
  let heartbeatInterval: NodeJS.Timeout | null = null

  const startHeartbeat = () => {
    stopHeartbeat()
    heartbeatInterval = setInterval(() => {
      if (isConnected.value) {
        send({
          type: 'ping',
          timestamp: new Date().toISOString()
        })
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
  const scheduleReconnect = () => {
    const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.value), 30000) // 指数退避，最大30秒
    
    console.log(`${delay / 1000}秒后尝试重连订单WebSocket (第${reconnectAttempts.value + 1}次)`)
    
    reconnectInterval.value = setTimeout(() => {
      reconnectAttempts.value++
      connect()
    }, delay)
  }

  // 辅助函数
  const getStatusText = (status: string) => {
    const statusMap: Record<string, string> = {
      pending: '待提交',
      submitted: '已提交',
      accepted: '已接受',
      partially_filled: '部分成交',
      filled: '完全成交',
      cancelled: '已取消',
      rejected: '已拒绝',
      expired: '已过期'
    }
    return statusMap[status] || status
  }

  const getNotificationType = (status: string) => {
    const typeMap: Record<string, string> = {
      filled: 'success',
      cancelled: 'warning',
      rejected: 'error',
      expired: 'warning'
    }
    return typeMap[status] || 'info'
  }

  // 组件卸载时自动断开连接
  onUnmounted(() => {
    disconnect()
  })

  return {
    socket,
    isConnected,
    connectionStatus,
    reconnectAttempts,
    connect,
    disconnect,
    send,
    subscribe,
    unsubscribe,
    onMessage,
    offMessage
  }
}