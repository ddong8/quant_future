/**
 * WebSocket管理器
 * 提供全局的WebSocket实例和便捷方法
 */

import { ref, computed } from 'vue'
import { WebSocketClient, MessageType, type WebSocketMessage, type SubscriptionCallback } from './client'
import { useAuthStore } from '@/stores/auth'

// WebSocket配置
const WS_CONFIG = {
  url: import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws',
  reconnectInterval: 3000,
  maxReconnectAttempts: 10,
  heartbeatInterval: 30000,
  debug: import.meta.env.DEV
}

class WebSocketManager {
  private client: WebSocketClient | null = null
  private authStore = useAuthStore()
  
  // 响应式状态
  public connected = ref(false)
  public connecting = ref(false)
  public error = ref<string>('')
  
  /**
   * 初始化WebSocket连接
   */
  async init(): Promise<void> {
    if (this.client) {
      return
    }
    
    // 获取认证token
    const token = this.authStore.token
    
    // 创建WebSocket客户端
    this.client = new WebSocketClient({
      ...WS_CONFIG,
      token: token || undefined
    })
    
    // 监听连接状态变化
    this.client.connected.value && (this.connected.value = this.client.connected.value)
    this.client.lastError.value && (this.error.value = this.client.lastError.value)
    
    // 添加全局消息处理器
    this.client.onMessage(this.handleGlobalMessage.bind(this))
    
    try {\n      this.connecting.value = true\n      await this.client.connect()\n      this.connected.value = true\n      this.error.value = ''\n    } catch (error) {\n      this.error.value = error instanceof Error ? error.message : '连接失败'\n      throw error\n    } finally {\n      this.connecting.value = false\n    }\n  }\n  \n  /**\n   * 断开WebSocket连接\n   */\n  disconnect(): void {\n    if (this.client) {\n      this.client.disconnect()\n      this.client = null\n    }\n    this.connected.value = false\n    this.connecting.value = false\n    this.error.value = ''\n  }\n  \n  /**\n   * 重新连接\n   */\n  async reconnect(): Promise<void> {\n    this.disconnect()\n    await this.init()\n  }\n  \n  /**\n   * 发送消息\n   */\n  send(message: WebSocketMessage): boolean {\n    if (!this.client) {\n      console.warn('WebSocket未初始化')\n      return false\n    }\n    return this.client.send(message)\n  }\n  \n  /**\n   * 订阅主题\n   */\n  subscribe(topic: string, callback?: SubscriptionCallback): boolean {\n    if (!this.client) {\n      console.warn('WebSocket未初始化')\n      return false\n    }\n    return this.client.subscribe(topic, callback)\n  }\n  \n  /**\n   * 取消订阅主题\n   */\n  unsubscribe(topic: string, callback?: SubscriptionCallback): boolean {\n    if (!this.client) {\n      console.warn('WebSocket未初始化')\n      return false\n    }\n    return this.client.unsubscribe(topic, callback)\n  }\n  \n  /**\n   * 添加全局消息监听器\n   */\n  onMessage(callback: SubscriptionCallback): void {\n    if (!this.client) {\n      console.warn('WebSocket未初始化')\n      return\n    }\n    this.client.onMessage(callback)\n  }\n  \n  /**\n   * 移除全局消息监听器\n   */\n  offMessage(callback: SubscriptionCallback): void {\n    if (!this.client) {\n      console.warn('WebSocket未初始化')\n      return\n    }\n    this.client.offMessage(callback)\n  }\n  \n  /**\n   * 处理全局消息\n   */\n  private handleGlobalMessage(message: WebSocketMessage): void {\n    // 这里可以添加全局消息处理逻辑\n    // 比如更新全局状态、显示通知等\n    \n    switch (message.type) {\n      case MessageType.SYSTEM_NOTIFICATION:\n        // 处理系统通知\n        this.handleSystemNotification(message)\n        break\n        \n      case MessageType.USER_NOTIFICATION:\n        // 处理用户通知\n        this.handleUserNotification(message)\n        break\n        \n      case MessageType.RISK_ALERT:\n        // 处理风险警报\n        this.handleRiskAlert(message)\n        break\n        \n      case MessageType.ERROR:\n        // 处理错误消息\n        this.handleError(message)\n        break\n    }\n  }\n  \n  /**\n   * 处理系统通知\n   */\n  private handleSystemNotification(message: WebSocketMessage): void {\n    // TODO: 显示系统通知\n    console.log('系统通知:', message.data)\n  }\n  \n  /**\n   * 处理用户通知\n   */\n  private handleUserNotification(message: WebSocketMessage): void {\n    // TODO: 显示用户通知\n    console.log('用户通知:', message.data)\n  }\n  \n  /**\n   * 处理风险警报\n   */\n  private handleRiskAlert(message: WebSocketMessage): void {\n    // TODO: 显示风险警报\n    console.log('风险警报:', message.data)\n  }\n  \n  /**\n   * 处理错误消息\n   */\n  private handleError(message: WebSocketMessage): void {\n    console.error('WebSocket错误:', message.data)\n  }\n  \n  /**\n   * 获取连接状态\n   */\n  get isConnected(): boolean {\n    return this.connected.value\n  }\n  \n  /**\n   * 获取连接ID\n   */\n  get connectionId(): string {\n    return this.client?.getConnectionId() || ''\n  }\n  \n  /**\n   * 获取订阅列表\n   */\n  get subscriptions(): string[] {\n    return this.client?.getSubscriptions() || []\n  }\n}\n\n// 创建全局WebSocket管理器实例\nexport const wsManager = new WebSocketManager()\n\n// 便捷方法\nexport const useWebSocket = () => {\n  return {\n    // 状态\n    connected: computed(() => wsManager.connected.value),\n    connecting: computed(() => wsManager.connecting.value),\n    error: computed(() => wsManager.error.value),\n    connectionId: computed(() => wsManager.connectionId),\n    subscriptions: computed(() => wsManager.subscriptions),\n    \n    // 方法\n    init: wsManager.init.bind(wsManager),\n    disconnect: wsManager.disconnect.bind(wsManager),\n    reconnect: wsManager.reconnect.bind(wsManager),\n    send: wsManager.send.bind(wsManager),\n    subscribe: wsManager.subscribe.bind(wsManager),\n    unsubscribe: wsManager.unsubscribe.bind(wsManager),\n    onMessage: wsManager.onMessage.bind(wsManager),\n    offMessage: wsManager.offMessage.bind(wsManager)\n  }\n}\n\n// 主题订阅便捷方法\nexport const subscribeToMarketData = (symbol: string, callback: SubscriptionCallback) => {\n  return wsManager.subscribe(`market_data.${symbol}`, callback)\n}\n\nexport const subscribeToPrice = (symbol: string, callback: SubscriptionCallback) => {\n  return wsManager.subscribe(`price.${symbol}`, callback)\n}\n\nexport const subscribeToDepth = (symbol: string, callback: SubscriptionCallback) => {\n  return wsManager.subscribe(`depth.${symbol}`, callback)\n}\n\nexport const subscribeToOrders = (userId: number, callback: SubscriptionCallback) => {\n  return wsManager.subscribe(`orders.${userId}`, callback)\n}\n\nexport const subscribeToPositions = (userId: number, callback: SubscriptionCallback) => {\n  return wsManager.subscribe(`positions.${userId}`, callback)\n}\n\nexport const subscribeToStrategies = (userId: number, callback: SubscriptionCallback) => {\n  return wsManager.subscribe(`strategies.${userId}`, callback)\n}\n\nexport const subscribeToBacktests = (userId: number, callback: SubscriptionCallback) => {\n  return wsManager.subscribe(`backtests.${userId}`, callback)\n}\n\nexport const subscribeToRisk = (userId: number, callback: SubscriptionCallback) => {\n  return wsManager.subscribe(`risk.${userId}`, callback)\n}\n\nexport const subscribeToNotifications = (userId: number, callback: SubscriptionCallback) => {\n  return wsManager.subscribe(`notifications.${userId}`, callback)\n}\n\n// 取消订阅便捷方法\nexport const unsubscribeFromMarketData = (symbol: string, callback?: SubscriptionCallback) => {\n  return wsManager.unsubscribe(`market_data.${symbol}`, callback)\n}\n\nexport const unsubscribeFromPrice = (symbol: string, callback?: SubscriptionCallback) => {\n  return wsManager.unsubscribe(`price.${symbol}`, callback)\n}\n\nexport const unsubscribeFromDepth = (symbol: string, callback?: SubscriptionCallback) => {\n  return wsManager.unsubscribe(`depth.${symbol}`, callback)\n}\n\nexport const unsubscribeFromOrders = (userId: number, callback?: SubscriptionCallback) => {\n  return wsManager.unsubscribe(`orders.${userId}`, callback)\n}\n\nexport const unsubscribeFromPositions = (userId: number, callback?: SubscriptionCallback) => {\n  return wsManager.unsubscribe(`positions.${userId}`, callback)\n}\n\nexport const unsubscribeFromStrategies = (userId: number, callback?: SubscriptionCallback) => {\n  return wsManager.unsubscribe(`strategies.${userId}`, callback)\n}\n\nexport const unsubscribeFromBacktests = (userId: number, callback?: SubscriptionCallback) => {\n  return wsManager.unsubscribe(`backtests.${userId}`, callback)\n}\n\nexport const unsubscribeFromRisk = (userId: number, callback?: SubscriptionCallback) => {\n  return wsManager.unsubscribe(`risk.${userId}`, callback)\n}\n\nexport const unsubscribeFromNotifications = (userId: number, callback?: SubscriptionCallback) => {\n  return wsManager.unsubscribe(`notifications.${userId}`, callback)\n}"