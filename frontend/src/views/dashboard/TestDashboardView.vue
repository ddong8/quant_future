<template>
  <div class="test-dashboard">
    <h1>测试仪表板</h1>
    <p>如果你能看到这个页面，说明路由配置正确。</p>
    
    <div class="test-info">
      <h3>基本信息</h3>
      <p>用户名: {{ authStore.user?.username || '未知' }}</p>
      <p>认证状态: {{ authStore.isAuthenticated ? '已认证' : '未认证' }}</p>
      <p>当前时间: {{ currentTime }}</p>
    </div>
    
    <div class="test-actions">
      <button @click="testAPI">测试API</button>
      <button @click="refreshPage">刷新页面</button>
    </div>
    
    <div v-if="apiResult" class="api-result">
      <h3>API测试结果</h3>
      <pre>{{ apiResult }}</pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const currentTime = ref(new Date().toLocaleString())
const apiResult = ref('')

const testAPI = async () => {
  try {
    console.log('测试API调用...')
    const { dashboardApi } = await import('@/api/dashboard')
    const response = await dashboardApi.getSummary()
    apiResult.value = JSON.stringify(response, null, 2)
    console.log('API测试成功:', response)
  } catch (error) {
    apiResult.value = `API测试失败: ${error.message}`
    console.error('API测试失败:', error)
  }
}

const refreshPage = () => {
  window.location.reload()
}

onMounted(() => {
  console.log('测试仪表板组件已挂载')
  console.log('认证状态:', authStore.isAuthenticated)
  console.log('用户信息:', authStore.user)
  
  // 更新时间
  setInterval(() => {
    currentTime.value = new Date().toLocaleString()
  }, 1000)
})
</script>

<style scoped>
.test-dashboard {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.test-info {
  background: #f5f5f5;
  padding: 15px;
  border-radius: 5px;
  margin: 20px 0;
}

.test-actions {
  margin: 20px 0;
}

.test-actions button {
  background: #409EFF;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
  margin-right: 10px;
}

.test-actions button:hover {
  background: #337ecc;
}

.api-result {
  background: #f8f8f8;
  padding: 15px;
  border-radius: 5px;
  margin: 20px 0;
}

.api-result pre {
  white-space: pre-wrap;
  word-break: break-all;
  font-size: 12px;
}
</style>