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

export class WebSocketClient {
  private ws: WebSocket | null = null
  private options: Required<WebSocketOptions>
  private reconnectAttempts = 0
  private heartbeatTimer: number | null = null
  private reconnectTimer: number | null = null
  
  // 响应式状态
  public connected = ref(false)
  public connecting = ref(false)
  public error = ref<string | null>(null)
  public lastMessage = ref<WebSocketMessage | null>(null)
  public messageHistory = reactive<WebSocketMessage[]>([])

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

  // 连接WebSocket
  connect(): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      return
    }

    this.connecting.value = true
    this.error.value = null

    try {
      // 添加认证token到URL
      const authStore = useAuthStore()
      const url = new URL(this.options.url)
      if (authStore.token) {
        url.searchParams.set('token', authStore.token)
      }

      this.ws = new WebSocket(url.toString(), this.options.protocols)
      
      this.ws.onopen = this.handleOpen.bind(this)
      this.ws.onmessage = this.handleMessage.bind(this)
      this.ws.onerror = this.handleError.bind(this)
      this.ws.onclose = this.handleClose.bind(this)
    } catch (error) {
      this.connecting.value = false
      this.error.value = `连接失败: ${error}`
      console.error('WebSocket连接失败:', error)
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
    this.reconnectAttempts = 0
  }

  // 发送消息
  send(type: string, data: any): boolean {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.warn('WebSocket未连接，无法发送消息')
      return false
    }

    try {
      const message = {
        type,
        data,
        timestamp: new Date().toISOString()
      }
      
      this.ws.send(JSON.stringify(message))
      return true
    } catch (error) {
      console.error('发送WebSocket消息失败:', error)
      return false
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
    
    this.connected.value = true
    this.connecting.value = false
    this.error.value = null
    this.reconnectAttempts = 0
    
    // 启动心跳
    this.startHeartbeat()
    
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
    
    // 调用用户回调
    this.options.onError(event)
  }

  // 处理连接关闭
  private handleClose(event: CloseEvent): void {
    console.log('WebSocket连接已关闭:', event.code, event.reason)
    
    this.connected.value = false
    this.connecting.value = false
    this.clearTimers()
    
    // 调用用户回调
    this.options.onClose(event)
    
    // 自动重连
    if (event.code !== 1000 && this.reconnectAttempts < this.options.maxReconnectAttempts) {
      this.scheduleReconnect()
    } else if (this.reconnectAttempts >= this.options.maxReconnectAttempts) {
      this.error.value = '重连次数已达上限'
      ElMessage.error('WebSocket连接失败，请刷新页面重试')
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
  
  // 订阅市场数据
  const subscribeQuote = (symbol: string) => {
    return ws.subscribe('quote', { symbol })
  }
  
  // 订阅K线数据
  const subscribeKline = (symbol: string, interval: string) => {
    return ws.subscribe('kline', { symbol, interval })
  }
  
  // 订阅深度数据
  const subscribeDepth = (symbol: string) => {
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