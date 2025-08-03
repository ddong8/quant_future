/**
 * WebSocket客户端
 * 提供WebSocket连接管理、重连机制和消息处理
 */

import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'

// WebSocket连接状态
export enum WebSocketState {
  CONNECTING = 0,
  OPEN = 1,
  CLOSING = 2,
  CLOSED = 3
}

// 消息类型
export enum MessageType {
  // 连接相关
  CONNECTION_ESTABLISHED = 'connection_established',
  SUBSCRIPTION_CONFIRMED = 'subscription_confirmed',
  UNSUBSCRIPTION_CONFIRMED = 'unsubscription_confirmed',
  
  // 心跳
  PING = 'ping',
  PONG = 'pong',
  
  // 市场数据
  MARKET_DATA = 'market_data',
  PRICE_UPDATE = 'price_update',
  DEPTH_UPDATE = 'depth_update',
  
  // 订单相关
  ORDER_UPDATE = 'order_update',
  ORDER_FILLED = 'order_filled',
  ORDER_CANCELLED = 'order_cancelled',
  
  // 持仓相关
  POSITION_UPDATE = 'position_update',
  PNL_UPDATE = 'pnl_update',
  
  // 账户相关
  ACCOUNT_UPDATE = 'account_update',
  BALANCE_UPDATE = 'balance_update',
  
  // 策略相关
  STRATEGY_UPDATE = 'strategy_update',
  BACKTEST_UPDATE = 'backtest_update',
  
  // 风险控制
  RISK_ALERT = 'risk_alert',
  RISK_WARNING = 'risk_warning',
  
  // 系统通知
  SYSTEM_NOTIFICATION = 'system_notification',
  USER_NOTIFICATION = 'user_notification',
  
  // 错误和异常
  ERROR = 'error',
  WARNING = 'warning'
}

// 消息接口
export interface WebSocketMessage {
  type: string
  data?: any
  topic?: string
  timestamp?: string
  connection_id?: string
}

// 订阅回调函数类型
export type SubscriptionCallback = (message: WebSocketMessage) => void

// WebSocket客户端配置
export interface WebSocketClientConfig {
  url: string
  token?: string
  reconnectInterval?: number
  maxReconnectAttempts?: number
  heartbeatInterval?: number
  debug?: boolean
}

export class WebSocketClient {
  private ws: WebSocket | null = null
  private config: WebSocketClientConfig
  private reconnectAttempts = 0
  private reconnectTimer: number | null = null
  private heartbeatTimer: number | null = null
  private isManualClose = false
  
  // 响应式状态
  public state = ref<WebSocketState>(WebSocketState.CLOSED)
  public connected = ref(false)
  public connectionId = ref<string>('')
  public lastError = ref<string>('')
  
  // 订阅管理
  private subscriptions = new Map<string, Set<SubscriptionCallback>>()
  private globalCallbacks = new Set<SubscriptionCallback>()
  
  // 消息队列（连接断开时缓存消息）
  private messageQueue: WebSocketMessage[] = []
  
  constructor(config: WebSocketClientConfig) {\n    this.config = {\n      reconnectInterval: 3000,\n      maxReconnectAttempts: 10,\n      heartbeatInterval: 30000,\n      debug: false,\n      ...config\n    }\n  }\n  \n  /**\n   * 连接WebSocket\n   */\n  connect(): Promise<void> {\n    return new Promise((resolve, reject) => {\n      if (this.ws && this.ws.readyState === WebSocket.OPEN) {\n        resolve()\n        return\n      }\n      \n      this.isManualClose = false\n      \n      // 构建WebSocket URL\n      let wsUrl = this.config.url\n      if (this.config.token) {\n        const separator = wsUrl.includes('?') ? '&' : '?'\n        wsUrl += `${separator}token=${encodeURIComponent(this.config.token)}`\n      }\n      \n      this.log('正在连接WebSocket...', wsUrl)\n      \n      try {\n        this.ws = new WebSocket(wsUrl)\n        this.state.value = WebSocketState.CONNECTING\n        \n        this.ws.onopen = () => {\n          this.log('WebSocket连接已建立')\n          this.state.value = WebSocketState.OPEN\n          this.connected.value = true\n          this.reconnectAttempts = 0\n          this.lastError.value = ''\n          \n          // 启动心跳\n          this.startHeartbeat()\n          \n          // 发送队列中的消息\n          this.flushMessageQueue()\n          \n          resolve()\n        }\n        \n        this.ws.onmessage = (event) => {\n          this.handleMessage(event.data)\n        }\n        \n        this.ws.onclose = (event) => {\n          this.log('WebSocket连接已关闭', event.code, event.reason)\n          this.state.value = WebSocketState.CLOSED\n          this.connected.value = false\n          this.connectionId.value = ''\n          \n          // 停止心跳\n          this.stopHeartbeat()\n          \n          // 如果不是手动关闭，尝试重连\n          if (!this.isManualClose) {\n            this.scheduleReconnect()\n          }\n        }\n        \n        this.ws.onerror = (error) => {\n          this.log('WebSocket连接错误', error)\n          this.lastError.value = 'WebSocket连接错误'\n          reject(new Error('WebSocket连接失败'))\n        }\n        \n      } catch (error) {\n        this.log('创建WebSocket连接失败', error)\n        this.lastError.value = '创建WebSocket连接失败'\n        reject(error)\n      }\n    })\n  }\n  \n  /**\n   * 断开WebSocket连接\n   */\n  disconnect(): void {\n    this.isManualClose = true\n    \n    // 清除重连定时器\n    if (this.reconnectTimer) {\n      clearTimeout(this.reconnectTimer)\n      this.reconnectTimer = null\n    }\n    \n    // 停止心跳\n    this.stopHeartbeat()\n    \n    // 关闭连接\n    if (this.ws) {\n      this.state.value = WebSocketState.CLOSING\n      this.ws.close(1000, '手动关闭')\n      this.ws = null\n    }\n    \n    this.connected.value = false\n    this.connectionId.value = ''\n    this.log('WebSocket连接已手动关闭')\n  }\n  \n  /**\n   * 发送消息\n   */\n  send(message: WebSocketMessage): boolean {\n    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {\n      this.log('WebSocket未连接，消息已加入队列', message)\n      this.messageQueue.push(message)\n      return false\n    }\n    \n    try {\n      const messageStr = JSON.stringify(message)\n      this.ws.send(messageStr)\n      this.log('发送消息', message)\n      return true\n    } catch (error) {\n      this.log('发送消息失败', error)\n      return false\n    }\n  }\n  \n  /**\n   * 订阅主题\n   */\n  subscribe(topic: string, callback?: SubscriptionCallback): boolean {\n    // 添加回调函数\n    if (callback) {\n      if (!this.subscriptions.has(topic)) {\n        this.subscriptions.set(topic, new Set())\n      }\n      this.subscriptions.get(topic)!.add(callback)\n    }\n    \n    // 发送订阅消息\n    return this.send({\n      type: 'subscribe',\n      data: { topic }\n    })\n  }\n  \n  /**\n   * 取消订阅主题\n   */\n  unsubscribe(topic: string, callback?: SubscriptionCallback): boolean {\n    // 移除回调函数\n    if (callback && this.subscriptions.has(topic)) {\n      this.subscriptions.get(topic)!.delete(callback)\n      \n      // 如果没有回调函数了，删除主题\n      if (this.subscriptions.get(topic)!.size === 0) {\n        this.subscriptions.delete(topic)\n      }\n    } else if (!callback) {\n      // 如果没有指定回调函数，删除整个主题\n      this.subscriptions.delete(topic)\n    }\n    \n    // 发送取消订阅消息\n    return this.send({\n      type: 'unsubscribe',\n      data: { topic }\n    })\n  }\n  \n  /**\n   * 添加全局消息监听器\n   */\n  onMessage(callback: SubscriptionCallback): void {\n    this.globalCallbacks.add(callback)\n  }\n  \n  /**\n   * 移除全局消息监听器\n   */\n  offMessage(callback: SubscriptionCallback): void {\n    this.globalCallbacks.delete(callback)\n  }\n  \n  /**\n   * 处理接收到的消息\n   */\n  private handleMessage(data: string): void {\n    try {\n      const message: WebSocketMessage = JSON.parse(data)\n      this.log('收到消息', message)\n      \n      // 处理特殊消息类型\n      switch (message.type) {\n        case MessageType.CONNECTION_ESTABLISHED:\n          this.connectionId.value = message.connection_id || ''\n          break\n          \n        case MessageType.PONG:\n          // 心跳响应，不需要特殊处理\n          break\n          \n        case MessageType.ERROR:\n          this.lastError.value = message.data?.message || '未知错误'\n          ElMessage.error(this.lastError.value)\n          break\n          \n        case MessageType.WARNING:\n          ElMessage.warning(message.data?.message || '警告')\n          break\n      }\n      \n      // 调用主题订阅回调\n      if (message.topic && this.subscriptions.has(message.topic)) {\n        const callbacks = this.subscriptions.get(message.topic)!\n        callbacks.forEach(callback => {\n          try {\n            callback(message)\n          } catch (error) {\n            this.log('订阅回调执行错误', error)\n          }\n        })\n      }\n      \n      // 调用全局回调\n      this.globalCallbacks.forEach(callback => {\n        try {\n          callback(message)\n        } catch (error) {\n          this.log('全局回调执行错误', error)\n        }\n      })\n      \n    } catch (error) {\n      this.log('解析消息失败', error, data)\n    }\n  }\n  \n  /**\n   * 安排重连\n   */\n  private scheduleReconnect(): void {\n    if (this.reconnectAttempts >= this.config.maxReconnectAttempts!) {\n      this.log('达到最大重连次数，停止重连')\n      this.lastError.value = '连接失败，已达到最大重连次数'\n      return\n    }\n    \n    this.reconnectAttempts++\n    const delay = this.config.reconnectInterval! * Math.pow(1.5, this.reconnectAttempts - 1)\n    \n    this.log(`${delay}ms后进行第${this.reconnectAttempts}次重连`)\n    \n    this.reconnectTimer = window.setTimeout(() => {\n      this.connect().catch(error => {\n        this.log('重连失败', error)\n      })\n    }, delay)\n  }\n  \n  /**\n   * 启动心跳\n   */\n  private startHeartbeat(): void {\n    this.stopHeartbeat()\n    \n    this.heartbeatTimer = window.setInterval(() => {\n      this.send({\n        type: MessageType.PING,\n        timestamp: new Date().toISOString()\n      })\n    }, this.config.heartbeatInterval!)\n  }\n  \n  /**\n   * 停止心跳\n   */\n  private stopHeartbeat(): void {\n    if (this.heartbeatTimer) {\n      clearInterval(this.heartbeatTimer)\n      this.heartbeatTimer = null\n    }\n  }\n  \n  /**\n   * 发送队列中的消息\n   */\n  private flushMessageQueue(): void {\n    while (this.messageQueue.length > 0) {\n      const message = this.messageQueue.shift()!\n      this.send(message)\n    }\n  }\n  \n  /**\n   * 日志输出\n   */\n  private log(message: string, ...args: any[]): void {\n    if (this.config.debug) {\n      console.log(`[WebSocket] ${message}`, ...args)\n    }\n  }\n  \n  /**\n   * 获取连接状态\n   */\n  getState(): WebSocketState {\n    return this.state.value\n  }\n  \n  /**\n   * 是否已连接\n   */\n  isConnected(): boolean {\n    return this.connected.value\n  }\n  \n  /**\n   * 获取连接ID\n   */\n  getConnectionId(): string {\n    return this.connectionId.value\n  }\n  \n  /**\n   * 获取订阅列表\n   */\n  getSubscriptions(): string[] {\n    return Array.from(this.subscriptions.keys())\n  }\n  \n  /**\n   * 清空消息队列\n   */\n  clearMessageQueue(): void {\n    this.messageQueue = []\n  }\n}"