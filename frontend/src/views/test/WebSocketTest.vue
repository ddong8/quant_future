<template>
  <div class="websocket-test">
    <el-card class="connection-card">
      <template #header>
        <div class="card-header">
          <span>WebSocket连接状态</span>
          <el-tag :type="connectionStatusType" size="small">
            {{ connectionStatusText }}
          </el-tag>
        </div>
      </template>
      
      <div class="connection-info">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="连接状态">
            <el-tag :type="connectionStatusType" size="small">
              {{ connectionStatusText }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="连接ID">
            {{ connectionId || '未连接' }}
          </el-descriptions-item>
          <el-descriptions-item label="错误信息">
            {{ error || '无' }}
          </el-descriptions-item>
          <el-descriptions-item label="订阅数量">
            {{ subscriptions.length }}
          </el-descriptions-item>
        </el-descriptions>
        
        <div class="connection-actions">
          <el-button 
            v-if="!connected" 
            type="primary" 
            @click="connect"
            :loading="connecting"
          >
            连接
          </el-button>
          <el-button 
            v-if="connected" 
            type="danger" 
            @click="disconnect"
          >
            断开
          </el-button>
          <el-button 
            type="warning" 
            @click="reconnect"
            :loading="connecting"
          >
            重连
          </el-button>
        </div>
      </div>
    </el-card>
    
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card class="subscription-card">
          <template #header>
            <span>主题订阅</span>
          </template>
          
          <div class="subscription-form">
            <el-input
              v-model="newTopic"
              placeholder="输入主题名称"
              @keyup.enter="subscribe"
            >
              <template #append>
                <el-button 
                  type="primary" 
                  @click="subscribe"
                  :disabled="!connected || !newTopic"
                >
                  订阅
                </el-button>
              </template>
            </el-input>
          </div>
          
          <div class="subscription-list">
            <el-tag
              v-for="topic in subscriptions"
              :key="topic"
              closable
              @close="unsubscribe(topic)"
              style="margin: 4px;"
            >
              {{ topic }}
            </el-tag>
            <div v-if="subscriptions.length === 0" class="empty-subscriptions">
              暂无订阅
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card class="message-card">
          <template #header>
            <div class="card-header">
              <span>发送消息</span>
              <el-button size="small" @click="clearMessages">
                清空消息
              </el-button>
            </div>
          </template>
          
          <div class="message-form">
            <el-form :model="messageForm" label-width="80px">
              <el-form-item label="消息类型">
                <el-select v-model="messageForm.type" placeholder="选择消息类型">
                  <el-option label="Ping" value="ping" />
                  <el-option label="订阅" value="subscribe" />
                  <el-option label="取消订阅" value="unsubscribe" />
                  <el-option label="获取订阅" value="get_subscriptions" />
                  <el-option label="自定义" value="custom" />
                </el-select>
              </el-form-item>
              
              <el-form-item v-if="messageForm.type === 'subscribe' || messageForm.type === 'unsubscribe'" label="主题">
                <el-input v-model="messageForm.topic" placeholder="输入主题名称" />
              </el-form-item>
              
              <el-form-item v-if="messageForm.type === 'custom'" label="自定义数据">
                <el-input
                  v-model="messageForm.customData"
                  type="textarea"
                  :rows="3"
                  placeholder="输入JSON格式的数据"
                />
              </el-form-item>
              
              <el-form-item>
                <el-button 
                  type="primary" 
                  @click="sendMessage"
                  :disabled="!connected"
                >
                  发送消息
                </el-button>
              </el-form-item>
            </el-form>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-card class="messages-card">
      <template #header>
        <div class="card-header">
          <span>消息日志 ({{ messages.length }})</span>
          <div>
            <el-switch
              v-model="autoScroll"
              active-text="自动滚动"
              inactive-text=""
            />
            <el-button size="small" @click="clearMessages" style="margin-left: 10px;">
              清空
            </el-button>
          </div>
        </div>
      </template>
      
      <div class="messages-container" ref="messagesContainer">
        <div
          v-for="(message, index) in messages"
          :key="index"
          class="message-item"
          :class="{ 'sent': message.direction === 'sent', 'received': message.direction === 'received' }"
        >
          <div class="message-header">
            <el-tag :type="message.direction === 'sent' ? 'warning' : 'success'" size="small">
              {{ message.direction === 'sent' ? '发送' : '接收' }}
            </el-tag>
            <span class="message-time">{{ formatTime(message.timestamp) }}</span>
            <el-tag v-if="message.data.type" size="small" effect="plain">
              {{ message.data.type }}
            </el-tag>
          </div>
          <div class="message-content">
            <pre>{{ JSON.stringify(message.data, null, 2) }}</pre>
          </div>
        </div>
        
        <div v-if="messages.length === 0" class="empty-messages">
          暂无消息
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useWebSocket } from '@/composables/useWebSocket'
import type { WebSocketMessage } from '@/utils/websocket/client'

// WebSocket相关
const ws = useWebSocket()
const { connected, connecting, error, connectionId, subscriptions } = ws

// 连接状态
const connectionStatusType = computed(() => {
  if (connected.value) return 'success'
  if (connecting.value) return 'warning'
  if (error.value) return 'danger'
  return 'info'
})

const connectionStatusText = computed(() => {
  if (connected.value) return '已连接'
  if (connecting.value) return '连接中'
  if (error.value) return '连接失败'
  return '未连接'
})

// 订阅相关
const newTopic = ref('')

// 消息相关
const messageForm = ref({
  type: 'ping',
  topic: '',
  customData: ''
})

interface MessageLog {
  direction: 'sent' | 'received'
  timestamp: Date
  data: any
}

const messages = ref<MessageLog[]>([])
const messagesContainer = ref<HTMLElement>()
const autoScroll = ref(true)

// 方法
const connect = async () => {
  try {
    await ws.init()
    ElMessage.success('WebSocket连接成功')
  } catch (error) {
    ElMessage.error('WebSocket连接失败')
  }
}

const disconnect = () => {
  ws.disconnect()
  ElMessage.info('WebSocket连接已断开')
}

const reconnect = async () => {
  try {
    await ws.reconnect()
    ElMessage.success('WebSocket重连成功')
  } catch (error) {
    ElMessage.error('WebSocket重连失败')
  }
}

const subscribe = () => {
  if (!newTopic.value.trim()) {
    ElMessage.warning('请输入主题名称')
    return
  }
  
  ws.subscribe(newTopic.value.trim())
  newTopic.value = ''
}

const unsubscribe = (topic: string) => {
  ws.unsubscribe(topic)
}

const sendMessage = () => {
  if (!connected.value) {
    ElMessage.warning('WebSocket未连接')
    return
  }
  
  let message: WebSocketMessage
  
  switch (messageForm.value.type) {
    case 'ping':
      message = {
        type: 'ping',
        timestamp: new Date().toISOString()
      }
      break
      
    case 'subscribe':
      if (!messageForm.value.topic) {
        ElMessage.warning('请输入主题名称')
        return
      }
      message = {
        type: 'subscribe',
        data: { topic: messageForm.value.topic }
      }
      break
      
    case 'unsubscribe':
      if (!messageForm.value.topic) {
        ElMessage.warning('请输入主题名称')
        return
      }
      message = {
        type: 'unsubscribe',
        data: { topic: messageForm.value.topic }
      }
      break
      
    case 'get_subscriptions':
      message = {
        type: 'get_subscriptions'
      }
      break
      
    case 'custom':
      try {
        const customData = messageForm.value.customData ? JSON.parse(messageForm.value.customData) : {}
        message = {
          type: 'custom',
          data: customData
        }
      } catch (error) {
        ElMessage.error('自定义数据格式错误')
        return
      }
      break
      
    default:
      ElMessage.warning('请选择消息类型')
      return
  }
  
  const success = ws.send(message)
  if (success) {
    addMessage('sent', message)
  } else {
    ElMessage.error('消息发送失败')
  }
}

const addMessage = (direction: 'sent' | 'received', data: any) => {
  messages.value.push({
    direction,
    timestamp: new Date(),
    data
  })
  
  // 限制消息数量
  if (messages.value.length > 1000) {
    messages.value = messages.value.slice(-1000)
  }
  
  // 自动滚动到底部
  if (autoScroll.value) {
    nextTick(() => {
      if (messagesContainer.value) {
        messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
      }
    })
  }
}

const clearMessages = () => {
  messages.value = []
}

const formatTime = (date: Date) => {
  return date.toLocaleTimeString()
}

// 监听WebSocket消息
onMounted(() => {
  ws.onMessage((message: WebSocketMessage) => {
    addMessage('received', message)
  })
})
</script>

<style lang="scss" scoped>
.websocket-test {
  padding: 20px;
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .connection-card {
    margin-bottom: 20px;
    
    .connection-info {
      .connection-actions {
        margin-top: 16px;
        text-align: center;
        
        .el-button + .el-button {
          margin-left: 12px;
        }
      }
    }
  }
  
  .subscription-card,
  .message-card {
    height: 400px;
    
    .subscription-form {
      margin-bottom: 16px;
    }
    
    .subscription-list {
      max-height: 280px;
      overflow-y: auto;
      
      .empty-subscriptions {
        text-align: center;
        color: var(--el-text-color-secondary);
        padding: 20px;
      }
    }
    
    .message-form {
      height: 320px;
      overflow-y: auto;
    }
  }
  
  .messages-card {
    margin-top: 20px;
    
    .messages-container {
      height: 400px;
      overflow-y: auto;
      border: 1px solid var(--el-border-color);
      border-radius: 4px;
      padding: 8px;
      
      .message-item {
        margin-bottom: 12px;
        padding: 8px;
        border-radius: 4px;
        border-left: 3px solid var(--el-color-primary);
        
        &.sent {
          background-color: var(--el-color-warning-light-9);
          border-left-color: var(--el-color-warning);
        }
        
        &.received {
          background-color: var(--el-color-success-light-9);
          border-left-color: var(--el-color-success);
        }
        
        .message-header {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 8px;
          
          .message-time {
            font-size: 12px;
            color: var(--el-text-color-secondary);
          }
        }
        
        .message-content {
          pre {
            margin: 0;
            font-size: 12px;
            line-height: 1.4;
            white-space: pre-wrap;
            word-break: break-all;
            background-color: var(--el-fill-color-light);
            padding: 8px;
            border-radius: 4px;
          }
        }
      }
      
      .empty-messages {
        text-align: center;
        color: var(--el-text-color-secondary);
        padding: 40px;
      }
    }
  }
}
</style>