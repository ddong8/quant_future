import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

export interface WebSocketMessage {
  type: string
  data: any
  timestamp: string
}

export interface WebSocketOptions {
  url: string
  protocols?: string | string[]
  reconnectInterval?: number
  maxReconnectAttempts?: number
  heartbeatInterval?: number
  onOpen?: (event: Event) => void
  onMessage?: (message: WebSocketMessage) => void
  onError?: (event: Event) => void
  onClose?: (event: CloseEvent) => void
}

export type ConnectionState = 'connecting' | 'connected' | 'disconnected' | 'error'

export class WebSocketClient {
  private ws: WebSocket | null = null
  private options: Required<WebSocketOptions>
  private reconnectAttempts = 0
  private heartbeatTimer: number | null = null
  private reconnectTimer: number | null = null
  private connectionTimeout: number | null = null
  private messageQueue: Array<{type: string, data: any}> = []
  
  // 响应式状态
  public connected = ref(false)
  public connecting = ref(false)
  public error = ref<string | null>(null)
  public lastMessage = ref<WebSocketMessage | null>(null)
  public messageHistory = reactive<WebSocketMessage[]>([])
  public connectionState = ref<ConnectionState>('disconnected')

  constructor(options: WebSocketOptions) {
    this.options = {
      protocols: [],
      reconnectInterval: 3000,
      maxReconnectAttempts: 5,
      heartbeatInterval: 30000,
      onOpen: () => {},
      onMessage: () => {},
      onError: () => {},
      onClose: () => {},
      ...options
    }
  }

  // 检查是否已连接
  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN && this.connected.value
  }

  // 获取连接状态
  getConnectionState(): ConnectionState {
    return this.connectionState.value
  }

  // 强制重连
  forceReconnect(): void {
    this.disconnect()
    this.reconnectAttempts = 0
    this.connect()
  }

  // 连接WebSocket
  connect(): void {
    // 如果已经连接或正在连接，直接返回
    if (this.isConnected() || this.connecting.value) {
      return
    }

    // 清理之前的连接
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }

    this.connecting.value = true
    this.connectionState.value = 'connecting'
    this.error.value = null

    try {
      // 添加认证token到URL
      const authStore = useAuthStore()
      const url = new URL(this.options.url)
      if (authStore.token) {
        url.searchParams.set('token', authStore.token)
      }

      this.ws = new WebSocket(url.toString(), this.options.protocols)
      
      // 设置连接超时
      this.connectionTimeout = window.setTimeout(() => {
        if (this.connecting.value) {
          this.handleConnectionTimeout()
        }
      }, 10000) // 10秒超时
      
      this.ws.onopen = this.handleOpen.bind(this)
      this.ws.onmessage = this.handleMessage.bind(this)
      this.ws.onerror = this.handleError.bind(this)
      this.ws.onclose = this.handleClose.bind(this)
    } catch (error) {
      this.handleConnectionError(error)
    }
  }

  // 处理连接超时
  private handleConnectionTimeout(): void {
    console.warn('WebSocket连接超时')
    this.connecting.value = false
    this.connectionState.value = 'error'
    this.error.value = 'WebSocket连接超时'
    
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    
    // 尝试重连
    if (this.reconnectAttempts < this.options.maxReconnectAttempts) {
      this.scheduleReconnect()
    }
  }

  // 处理连接错误
  private handleConnectionError(error: any): void {
    console.error('WebSocket连接失败:', error)
    this.connecting.value = false
    this.connectionState.value = 'error'
    this.error.value = `连接失败: ${error}`
    
    // 尝试重连
    if (this.reconnectAttempts < this.options.maxReconnectAttempts) {
      this.scheduleReconnect()
    }
  }

  // 断开连接
  disconnect(): void {
    this.clearTimers()
    
    if (this.ws) {
      this.ws.close(1000, '主动断开连接')
      this.ws = null
    }
    
    this.connected.value = false
    this.connecting.value = false
    this.connectionState.value = 'disconnected'
    this.reconnectAttempts = 0
    this.messageQueue = [] // 清空消息队列
  }

  // 发送消息（改进版本，支持Promise和消息队列）
  async send(type: string, data: any): Promise<boolean> {
    const message = {
      type,
      data,
      timestamp: new Date().toISOString()
    }

    // 如果未连接，尝试连接并将消息加入队列
    if (!this.isConnected()) {
      console.warn('WebSocket未连接，消息已加入队列')
      this.messageQueue.push({ type, data })
      
      // 如果没有在连接中，尝试连接
      if (!this.connecting.value) {
        this.connect()
      }
      
      return false
    }

    try {
      this.ws!.send(JSON.stringify(message))
      return true
    } catch (error) {
      console.error('发送WebSocket消息失败:', error)
      // 将失败的消息加入队列，等待重连后发送
      this.messageQueue.push({ type, data })
      return false
    }
  }

  // 发送队列中的消息
  private async sendQueuedMessages(): Promise<void> {
    if (!this.isConnected() || this.messageQueue.length === 0) {
      return
    }

    const messages = [...this.messageQueue]
    this.messageQueue = []

    for (const message of messages) {
      try {
        await this.send(message.type, message.data)
      } catch (error) {
        console.error('发送队列消息失败:', error)
        // 如果发送失败，重新加入队列
        this.messageQueue.push(message)
      }
    }
  }

  // 订阅数据
  subscribe(channel: string, params?: any): boolean {
    return this.send('subscribe', { channel, params })
  }

  // 取消订阅
  unsubscribe(channel: string): boolean {
    return this.send('unsubscribe', { channel })
  }

  // 处理连接打开
  private handleOpen(event: Event): void {
    console.log('WebSocket连接已建立')
    
    // 清除连接超时
    if (this.connectionTimeout) {
      clearTimeout(this.connectionTimeout)
      this.connectionTimeout = null
    }
    
    this.connected.value = true
    this.connecting.value = false
    this.connectionState.value = 'connected'
    this.error.value = null
    this.reconnectAttempts = 0
    
    // 启动心跳
    this.startHeartbeat()
    
    // 发送队列中的消息
    this.sendQueuedMessages()
    
    // 调用用户回调
    this.options.onOpen(event)
  }

  // 处理消息
  private handleMessage(event: MessageEvent): void {
    try {
      const message: WebSocketMessage = JSON.parse(event.data)
      
      // 处理心跳响应
      if (message.type === 'pong') {
        return
      }
      
      // 更新状态
      this.lastMessage.value = message
      this.messageHistory.push(message)
      
      // 限制历史消息数量
      if (this.messageHistory.length > 100) {
        this.messageHistory.splice(0, this.messageHistory.length - 100)
      }
      
      // 调用用户回调
      this.options.onMessage(message)
    } catch (error) {
      console.error('解析WebSocket消息失败:', error)
    }
  }

  // 处理错误
  private handleError(event: Event): void {
    console.error('WebSocket错误:', event)
    
    this.error.value = 'WebSocket连接错误'
    this.connecting.value = false
    this.connectionState.value = 'error'
    
    // 清除连接超时
    if (this.connectionTimeout) {
      clearTimeout(this.connectionTimeout)
      this.connectionTimeout = null
    }
    
    // 调用用户回调
    this.options.onError(event)
  }

  // 处理连接关闭
  private handleClose(event: CloseEvent): void {
    console.log('WebSocket连接已关闭:', event.code, event.reason)
    
    this.connected.value = false
    this.connecting.value = false
    this.connectionState.value = 'disconnected'
    this.clearTimers()
    
    // 调用用户回调
    this.options.onClose(event)
    
    // 自动重连（除非是主动关闭）
    if (event.code !== 1000 && this.reconnectAttempts < this.options.maxReconnectAttempts) {
      this.connectionState.value = 'error'
      this.scheduleReconnect()
    } else if (this.reconnectAttempts >= this.options.maxReconnectAttempts) {
      this.connectionState.value = 'error'
      this.error.value = '重连次数已达上限，请检查网络连接'
      console.error('WebSocket重连次数已达上限')
    }
  }

  // 启动心跳
  private startHeartbeat(): void {
    this.heartbeatTimer = window.setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.send('ping', {})
      }
    }, this.options.heartbeatInterval)
  }

  // 安排重连
  private scheduleReconnect(): void {
    this.reconnectAttempts++
    
    console.log(`准备重连 (${this.reconnectAttempts}/${this.options.maxReconnectAttempts})`)
    
    this.reconnectTimer = window.setTimeout(() => {
      this.connect()
    }, this.options.reconnectInterval)
  }

  // 清理定时器
  private clearTimers(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
    
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    
    if (this.connectionTimeout) {
      clearTimeout(this.connectionTimeout)
      this.connectionTimeout = null
    }
  }
}

// 创建全局WebSocket实例
let globalWebSocket: WebSocketClient | null = null

export const useWebSocket = (options?: Partial<WebSocketOptions>) => {
  if (!globalWebSocket) {
    const defaultOptions: WebSocketOptions = {
      url: `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/v1/ws`,
      reconnectInterval: 3000,
      maxReconnectAttempts: 5,
      heartbeatInterval: 30000,
      ...options
    }
    
    globalWebSocket = new WebSocketClient(defaultOptions)
  }
  
  return globalWebSocket
}

// 市场数据WebSocket
export const useMarketWebSocket = () => {
  const ws = useWebSocket({
    url: `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/v1/ws/market`
  })
  
  // 订阅市场数据（改进版本，检查连接状态）
  const subscribeQuote = async (symbol: string) => {
    if (!ws.isConnected()) {
      console.warn('WebSocket未连接，尝试连接后订阅行情数据')
      ws.connect()
      // 等待连接建立
      await new Promise(resolve => {
        const checkConnection = () => {
          if (ws.isConnected()) {
            resolve(true)
          } else if (ws.getConnectionState() === 'error') {
            resolve(false)
          } else {
            setTimeout(checkConnection, 100)
          }
        }
        checkConnection()
      })
    }
    return ws.subscribe('quote', { symbol })
  }
  
  // 订阅K线数据
  const subscribeKline = async (symbol: string, interval: string) => {
    if (!ws.isConnected()) {
      console.warn('WebSocket未连接，尝试连接后订阅K线数据')
      ws.connect()
      await new Promise(resolve => {
        const checkConnection = () => {
          if (ws.isConnected()) {
            resolve(true)
          } else if (ws.getConnectionState() === 'error') {
            resolve(false)
          } else {
            setTimeout(checkConnection, 100)
          }
        }
        checkConnection()
      })
    }
    return ws.subscribe('kline', { symbol, interval })
  }
  
  // 订阅深度数据
  const subscribeDepth = async (symbol: string) => {
    if (!ws.isConnected()) {
      console.warn('WebSocket未连接，尝试连接后订阅深度数据')
      ws.connect()
      await new Promise(resolve => {
        const checkConnection = () => {
          if (ws.isConnected()) {
            resolve(true)
          } else if (ws.getConnectionState() === 'error') {
            resolve(false)
          } else {
            setTimeout(checkConnection, 100)
          }
        }
        checkConnection()
      })
    }
    return ws.subscribe('depth', { symbol })
  }
  
  return {
    ws,
    subscribeQuote,
    subscribeKline,
    subscribeDepth
  }
}

// 交易数据WebSocket
export const useTradingWebSocket = () => {
  const ws = useWebSocket({
    url: `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/v1/ws/trading`
  })
  
  // 订阅订单更新
  const subscribeOrders = () => {
    return ws.subscribe('orders', {})
  }
  
  // 订阅持仓更新
  const subscribePositions = () => {
    return ws.subscribe('positions', {})
  }
  
  // 订阅账户更新
  const subscribeAccount = () => {
    return ws.subscribe('account', {})
  }
  
  return {
    ws,
    subscribeOrders,
    subscribePositions,
    subscribeAccount
  }
}