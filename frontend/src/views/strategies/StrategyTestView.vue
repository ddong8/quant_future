<template>
  <div class="strategy-test-view">
    <div class="page-header">
      <div class="header-left">
        <el-button @click="goBack" text>
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
        <el-divider direction="vertical" />
        <h2 class="page-title">
          {{ strategy?.name || '策略测试' }}
          <el-tag v-if="strategy" :type="statusTagType" size="small">
            {{ statusText }}
          </el-tag>
        </h2>
      </div>
      
      <div class="header-actions">
        <el-button @click="showTestDialog = true">
          <el-icon><Setting /></el-icon>
          新建测试
        </el-button>
        <el-button @click="showDeployDialog = true" type="primary">
          <el-icon><Upload /></el-icon>
          部署策略
        </el-button>
      </div>
    </div>

    <div class="content-tabs">
      <el-tabs v-model="activeTab" type="card">
        <!-- 性能监控 -->
        <el-tab-pane label="性能监控" name="performance">
          <StrategyPerformanceMonitor 
            v-if="strategy" 
            :strategy-id="strategy.id" 
          />
        </el-tab-pane>
        
        <!-- 测试管理 -->
        <el-tab-pane label="测试管理" name="tests">
          <div class="tests-section">
            <!-- 测试列表 -->
            <div class="tests-header">
              <h3>测试历史</h3>
              <el-button size="small" @click="loadTests">
                <el-icon><Refresh /></el-icon>
                刷新
              </el-button>
            </div>
            
            <el-table :data="tests" v-loading="testsLoading">
              <el-table-column prop="name" label="测试名称" />
              <el-table-column prop="test_type" label="测试类型">
                <template #default="{ row }">
                  <el-tag size="small">{{ getTestTypeText(row.test_type) }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="environment" label="环境" />
              <el-table-column prop="status" label="状态">
                <template #default="{ row }">
                  <el-tag :type="getTestStatusTagType(row.status)" size="small">
                    {{ getTestStatusText(row.status) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="duration" label="耗时">
                <template #default="{ row }">
                  {{ formatDuration(row.duration) }}
                </template>
              </el-table-column>
              <el-table-column prop="created_at" label="创建时间">
                <template #default="{ row }">
                  {{ formatDateTime(row.created_at) }}
                </template>
              </el-table-column>
              <el-table-column label="操作" width="200">
                <template #default="{ row }">
                  <el-button text size="small" @click="viewTestResult(row)">
                    查看结果
                  </el-button>
                  <el-button text size="small" @click="downloadTestReport(row)">
                    下载报告
                  </el-button>
                  <el-button 
                    text 
                    size="small" 
                    type="danger" 
                    @click="deleteTest(row)"
                  >
                    删除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>
        
        <!-- 部署管理 -->
        <el-tab-pane label="部署管理" name="deployments">
          <div class="deployments-section">
            <!-- 部署列表 -->
            <div class="deployments-header">
              <h3>部署历史</h3>
              <el-button size="small" @click="loadDeployments">
                <el-icon><Refresh /></el-icon>
                刷新
              </el-button>
            </div>
            
            <el-table :data="deployments" v-loading="deploymentsLoading">
              <el-table-column prop="name" label="部署名称" />
              <el-table-column prop="environment" label="环境">
                <template #default="{ row }">
                  <el-tag :type="getEnvTagType(row.environment)" size="small">
                    {{ getEnvText(row.environment) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="instances" label="实例数" />
              <el-table-column prop="status" label="状态">
                <template #default="{ row }">
                  <el-tag :type="getDeployStatusTagType(row.status)" size="small">
                    {{ getDeployStatusText(row.status) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="health" label="健康状态">
                <template #default="{ row }">
                  <el-progress 
                    :percentage="row.health" 
                    :color="getHealthColor(row.health)"
                    :show-text="false"
                    style="width: 100px"
                  />
                  <span style="margin-left: 8px">{{ row.health }}%</span>
                </template>
              </el-table-column>
              <el-table-column prop="created_at" label="部署时间">
                <template #default="{ row }">
                  {{ formatDateTime(row.created_at) }}
                </template>
              </el-table-column>
              <el-table-column label="操作" width="250">
                <template #default="{ row }">
                  <el-button 
                    text 
                    size="small" 
                    @click="viewDeploymentDetail(row)"
                  >
                    详情
                  </el-button>
                  <el-button 
                    text 
                    size="small" 
                    :type="row.status === 'running' ? 'warning' : 'success'"
                    @click="toggleDeployment(row)"
                  >
                    {{ row.status === 'running' ? '停止' : '启动' }}
                  </el-button>
                  <el-button 
                    text 
                    size="small" 
                    @click="scaleDeployment(row)"
                  >
                    扩缩容
                  </el-button>
                  <el-button 
                    text 
                    size="small" 
                    type="danger" 
                    @click="deleteDeployment(row)"
                  >
                    删除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>
        
        <!-- 运行日志 -->
        <el-tab-pane label="运行日志" name="logs">
          <StrategyLogViewer 
            v-if="strategy" 
            :strategy-id="strategy.id" 
            height="600px"
          />
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 测试配置对话框 -->
    <StrategyTestDialog
      v-model="showTestDialog"
      :strategy-id="strategy?.id"
      @success="handleTestSuccess"
    />

    <!-- 部署配置对话框 -->
    <StrategyDeployDialog
      v-model="showDeployDialog"
      :strategy-id="strategy?.id"
      @success="handleDeploySuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft,
  Setting,
  Upload,
  Refresh
} from '@element-plus/icons-vue'
import { useStrategyStore } from '@/stores/strategy'
import StrategyPerformanceMonitor from '@/components/StrategyPerformanceMonitor.vue'
import StrategyLogViewer from '@/components/StrategyLogViewer.vue'
import StrategyTestDialog from '@/components/StrategyTestDialog.vue'
import StrategyDeployDialog from '@/components/StrategyDeployDialog.vue'
import type { Strategy } from '@/types/strategy'

const route = useRoute()
const router = useRouter()
const strategyStore = useStrategyStore()

// 响应式数据
const strategy = ref<Strategy | null>(null)
const activeTab = ref('performance')
const showTestDialog = ref(false)
const showDeployDialog = ref(false)
const testsLoading = ref(false)
const deploymentsLoading = ref(false)

// 测试数据
const tests = ref([
  {
    id: 1,
    name: '单元测试-001',
    test_type: 'unit',
    environment: 'testing',
    status: 'completed',
    duration: 120,
    created_at: '2024-01-15 10:30:00'
  },
  {
    id: 2,
    name: '性能测试-001',
    test_type: 'performance',
    environment: 'staging',
    status: 'running',
    duration: 0,
    created_at: '2024-01-15 11:00:00'
  }
])

// 部署数据
const deployments = ref([
  {
    id: 1,
    name: '生产部署-v1.0',
    environment: 'production',
    instances: 3,
    status: 'running',
    health: 95,
    created_at: '2024-01-14 15:20:00'
  },
  {
    id: 2,
    name: '测试部署-v1.1',
    environment: 'testing',
    instances: 1,
    status: 'stopped',
    health: 0,
    created_at: '2024-01-15 09:15:00'
  }
])

// 计算属性
const statusTagType = computed(() => {
  if (!strategy.value) return 'info'
  
  const typeMap = {
    draft: 'info',
    active: 'success',
    paused: 'warning',
    stopped: 'info',
    error: 'danger'
  }
  return typeMap[strategy.value.status] || 'info'
})

const statusText = computed(() => {
  if (!strategy.value) return ''
  
  const textMap = {
    draft: '草稿',
    active: '活跃',
    paused: '暂停',
    stopped: '停止',
    error: '错误'
  }
  return textMap[strategy.value.status] || '未知'
})

// 方法
const loadStrategy = async () => {
  const strategyId = route.params.id as string
  if (strategyId) {
    try {
      strategy.value = await strategyStore.fetchStrategy(parseInt(strategyId))
    } catch (error) {
      ElMessage.error('加载策略失败')
      goBack()
    }
  }
}

const loadTests = async () => {
  testsLoading.value = true
  try {
    // 加载测试数据
    await new Promise(resolve => setTimeout(resolve, 500))
  } finally {
    testsLoading.value = false
  }
}

const loadDeployments = async () => {
  deploymentsLoading.value = true
  try {
    // 加载部署数据
    await new Promise(resolve => setTimeout(resolve, 500))
  } finally {
    deploymentsLoading.value = false
  }
}

const handleTestSuccess = (testId: number) => {
  ElMessage.success(`测试 ${testId} 已开始`)
  loadTests()
}

const handleDeploySuccess = (deploymentId: number) => {
  ElMessage.success(`部署 ${deploymentId} 已开始`)
  loadDeployments()
}

const viewTestResult = (test: any) => {
  // 查看测试结果
  ElMessage.info('查看测试结果功能开发中')
}

const downloadTestReport = (test: any) => {
  // 下载测试报告
  ElMessage.info('下载测试报告功能开发中')
}

const deleteTest = async (test: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除测试 "${test.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // 删除测试
    tests.value = tests.value.filter(t => t.id !== test.id)
    ElMessage.success('测试已删除')
  } catch (error) {
    // 用户取消
  }
}

const viewDeploymentDetail = (deployment: any) => {
  // 查看部署详情
  ElMessage.info('查看部署详情功能开发中')
}

const toggleDeployment = async (deployment: any) => {
  const action = deployment.status === 'running' ? '停止' : '启动'
  
  try {
    await ElMessageBox.confirm(
      `确定要${action}部署 "${deployment.name}" 吗？`,
      `确认${action}`,
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // 切换部署状态
    deployment.status = deployment.status === 'running' ? 'stopped' : 'running'
    deployment.health = deployment.status === 'running' ? 95 : 0
    
    ElMessage.success(`部署已${action}`)
  } catch (error) {
    // 用户取消
  }
}

const scaleDeployment = async (deployment: any) => {
  try {
    const { value: instances } = await ElMessageBox.prompt(
      '请输入目标实例数量',
      '扩缩容',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputValue: deployment.instances.toString(),
        inputValidator: (value) => {
          const num = parseInt(value)
          if (isNaN(num) || num < 1 || num > 10) {
            return '实例数量必须在1-10之间'
          }
          return true
        }
      }
    )
    
    deployment.instances = parseInt(instances)
    ElMessage.success('扩缩容操作已提交')
  } catch (error) {
    // 用户取消
  }
}

const deleteDeployment = async (deployment: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除部署 "${deployment.name}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // 删除部署
    deployments.value = deployments.value.filter(d => d.id !== deployment.id)
    ElMessage.success('部署已删除')
  } catch (error) {
    // 用户取消
  }
}

const goBack = () => {
  router.push('/strategies')
}

// 格式化函数
const formatDateTime = (dateString: string) => {
  return new Date(dateString).toLocaleString('zh-CN')
}

const formatDuration = (seconds: number) => {
  if (seconds === 0) return '-'
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  return `${minutes}分${remainingSeconds}秒`
}

const getTestTypeText = (type: string) => {
  const textMap: Record<string, string> = {
    unit: '单元测试',
    integration: '集成测试',
    performance: '性能测试',
    stress: '压力测试'
  }
  return textMap[type] || type
}

const getTestStatusTagType = (status: string) => {
  const typeMap: Record<string, string> = {
    pending: 'info',
    running: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return typeMap[status] || 'info'
}

const getTestStatusText = (status: string) => {
  const textMap: Record<string, string> = {
    pending: '等待中',
    running: '运行中',
    completed: '已完成',
    failed: '失败'
  }
  return textMap[status] || status
}

const getEnvTagType = (env: string) => {
  const typeMap: Record<string, string> = {
    development: 'info',
    testing: 'warning',
    staging: 'primary',
    production: 'success'
  }
  return typeMap[env] || 'info'
}

const getEnvText = (env: string) => {
  const textMap: Record<string, string> = {
    development: '开发',
    testing: '测试',
    staging: '预生产',
    production: '生产'
  }
  return textMap[env] || env
}

const getDeployStatusTagType = (status: string) => {
  const typeMap: Record<string, string> = {
    deploying: 'warning',
    running: 'success',
    stopped: 'info',
    failed: 'danger'
  }
  return typeMap[status] || 'info'
}

const getDeployStatusText = (status: string) => {
  const textMap: Record<string, string> = {
    deploying: '部署中',
    running: '运行中',
    stopped: '已停止',
    failed: '失败'
  }
  return textMap[status] || status
}

const getHealthColor = (health: number) => {
  if (health >= 80) return '#67c23a'
  if (health >= 60) return '#e6a23c'
  return '#f56c6c'
}

// 生命周期
onMounted(() => {
  loadStrategy()
})
</script>

<style scoped lang="scss">
.strategy-test-view {
  padding: 20px;
  
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    
    .header-left {
      display: flex;
      align-items: center;
      gap: 12px;
      
      .page-title {
        margin: 0;
        font-size: 20px;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 8px;
      }
    }
    
    .header-actions {
      display: flex;
      gap: 12px;
    }
  }
  
  .content-tabs {
    background: #fff;
    border-radius: 8px;
    overflow: hidden;
    
    .tests-section,
    .deployments-section {
      padding: 20px;
      
      .tests-header,
      .deployments-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
        
        h3 {
          margin: 0;
          font-size: 16px;
          font-weight: 600;
        }
      }
    }
  }
}

:deep(.el-tabs__content) {
  padding: 0;
}
</style>