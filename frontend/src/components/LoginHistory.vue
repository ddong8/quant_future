<template>
  <div class="login-history">
    <div class="history-header">
      <h3>登录历史</h3>
      <el-button 
        size="small" 
        @click="refreshHistory"
        :loading="loading"
      >
        刷新
      </el-button>
    </div>
    
    <el-timeline>
      <el-timeline-item
        v-for="record in loginRecords"
        :key="record.id"
        :timestamp="formatTime(record.login_time)"
        :type="getTimelineType(record.status)"
      >
        <div class="login-record">
          <div class="record-header">
            <div class="record-info">
              <el-icon :color="getStatusColor(record.status)">
                <component :is="getStatusIcon(record.status)" />
              </el-icon>
              <span class="status-text">{{ getStatusText(record.status) }}</span>
            </div>
            <el-tag :type="getTagType(record.status)" size="small">
              {{ record.status }}
            </el-tag>
          </div>
          
          <div class="record-details">
            <div class="detail-item">
              <el-icon><Monitor /></el-icon>
              <span>IP: {{ record.ip_address }}</span>
            </div>
            <div class="detail-item">
              <el-icon><Cellphone /></el-icon>
              <span>{{ formatUserAgent(record.user_agent) }}</span>
            </div>
            <div v-if="record.location" class="detail-item">
              <el-icon><Location /></el-icon>
              <span>{{ record.location }}</span>
            </div>
          </div>
          
          <div v-if="record.failure_reason" class="failure-reason">
            <el-alert
              :title="record.failure_reason"
              type="error"
              :closable="false"
              show-icon
            />
          </div>
        </div>
      </el-timeline-item>
    </el-timeline>
    
    <div v-if="hasMore" class="load-more">
      <el-button 
        @click="loadMore"
        :loading="loadingMore"
        size="small"
      >
        加载更多
      </el-button>
    </div>
    
    <el-empty v-if="!loading && loginRecords.length === 0" description="暂无登录记录" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import dayjs from 'dayjs'
import {
  CircleCheckFilled,
  CircleCloseFilled,
  WarningFilled,
  Monitor,
  Cellphone,
  Location
} from '@element-plus/icons-vue'

interface LoginRecord {
  id: number
  login_time: string
  ip_address: string
  user_agent: string
  location?: string
  status: 'success' | 'failed' | 'blocked'
  failure_reason?: string
}

// 响应式数据
const loading = ref(false)
const loadingMore = ref(false)
const hasMore = ref(true)
const currentPage = ref(1)
const loginRecords = ref<LoginRecord[]>([])

// 格式化时间
const formatTime = (timeStr: string) => {
  return dayjs(timeStr).format('YYYY-MM-DD HH:mm:ss')
}

// 获取状态图标
const getStatusIcon = (status: string) => {
  const iconMap: Record<string, any> = {
    success: CircleCheckFilled,
    failed: CircleCloseFilled,
    blocked: WarningFilled
  }
  return iconMap[status] || CircleCheckFilled
}

// 获取状态颜色
const getStatusColor = (status: string) => {
  const colorMap: Record<string, string> = {
    success: 'var(--el-color-success)',
    failed: 'var(--el-color-danger)',
    blocked: 'var(--el-color-warning)'
  }
  return colorMap[status] || 'var(--el-color-info)'
}

// 获取状态文本
const getStatusText = (status: string) => {
  const textMap: Record<string, string> = {
    success: '登录成功',
    failed: '登录失败',
    blocked: '登录被阻止'
  }
  return textMap[status] || status
}

// 获取标签类型
const getTagType = (status: string) => {
  const typeMap: Record<string, string> = {
    success: 'success',
    failed: 'danger',
    blocked: 'warning'
  }
  return typeMap[status] || 'info'
}

// 获取时间线类型
const getTimelineType = (status: string) => {
  const typeMap: Record<string, string> = {
    success: 'success',
    failed: 'danger',
    blocked: 'warning'
  }
  return typeMap[status] || 'primary'
}

// 格式化用户代理
const formatUserAgent = (userAgent: string) => {
  // 简化用户代理字符串显示
  if (userAgent.includes('Chrome')) {
    return 'Chrome 浏览器'
  } else if (userAgent.includes('Firefox')) {
    return 'Firefox 浏览器'
  } else if (userAgent.includes('Safari')) {
    return 'Safari 浏览器'
  } else if (userAgent.includes('Edge')) {
    return 'Edge 浏览器'
  } else {
    return '未知浏览器'
  }
}

// 加载登录历史
const loadLoginHistory = async (page = 1) => {
  try {
    if (page === 1) {
      loading.value = true
    } else {
      loadingMore.value = true
    }

    // 这里调用API加载登录历史
    // const response = await authApi.getLoginHistory({ page, page_size: 10 })
    
    // 模拟数据
    const mockData: LoginRecord[] = [
      {
        id: 1,
        login_time: new Date().toISOString(),
        ip_address: '192.168.1.100',
        user_agent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        location: '北京市',
        status: 'success'
      },
      {
        id: 2,
        login_time: new Date(Date.now() - 3600000).toISOString(),
        ip_address: '10.0.0.50',
        user_agent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        location: '上海市',
        status: 'success'
      },
      {
        id: 3,
        login_time: new Date(Date.now() - 7200000).toISOString(),
        ip_address: '203.0.113.1',
        user_agent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
        location: '广州市',
        status: 'failed',
        failure_reason: '密码错误'
      }
    ]

    if (page === 1) {
      loginRecords.value = mockData
    } else {
      loginRecords.value.push(...mockData)
    }

    // 模拟分页
    hasMore.value = page < 3
  } catch (error) {
    console.error('加载登录历史失败:', error)
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

// 刷新历史
const refreshHistory = () => {
  currentPage.value = 1
  loadLoginHistory(1)
}

// 加载更多
const loadMore = () => {
  currentPage.value++
  loadLoginHistory(currentPage.value)
}

// 生命周期
onMounted(() => {
  loadLoginHistory()
})
</script>

<style lang="scss" scoped>
.login-history {
  .history-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    
    h3 {
      margin: 0;
      color: var(--el-text-color-primary);
    }
  }
  
  .login-record {
    .record-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
      
      .record-info {
        display: flex;
        align-items: center;
        gap: 8px;
        
        .status-text {
          font-weight: 500;
          color: var(--el-text-color-primary);
        }
      }
    }
    
    .record-details {
      margin-bottom: 8px;
      
      .detail-item {
        display: flex;
        align-items: center;
        gap: 6px;
        margin-bottom: 4px;
        font-size: 13px;
        color: var(--el-text-color-secondary);
        
        .el-icon {
          font-size: 14px;
        }
      }
    }
    
    .failure-reason {
      margin-top: 8px;
    }
  }
  
  .load-more {
    text-align: center;
    margin-top: 20px;
  }
}

:deep(.el-timeline-item__timestamp) {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
</style>