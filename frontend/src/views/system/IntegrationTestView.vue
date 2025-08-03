<template>
  <div class="integration-test-view">
    <div class="page-header">
      <h1 class="page-title">集成测试管理</h1>
      <p class="page-description">系统模块间集成测试和数据一致性验证</p>
    </div>
    
    <!-- 测试控制面板 -->
    <el-card class="test-control-panel" shadow="never">
      <template #header>
        <div class="card-header">
          <span>测试控制</span>
          <div class="header-actions">
            <el-button 
              type="primary" 
              :loading="isRunningTest"
              @click="runFullIntegrationTest"
            >
              <el-icon><Play /></el-icon>
              运行完整测试
            </el-button>
            <el-button @click="refreshTestData">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </div>
      </template>
      
      <div class="control-grid">
        <el-button-group>
          <el-button 
            :loading="isValidatingData"
            @click="validateDataConsistency"
          >
            数据一致性检查
          </el-button>
          <el-button 
            :loading="isSimulatingTrading"
            @click="simulateTradingScenario"
          >
            交易场景模拟
          </el-button>
          <el-button 
            :loading="isTestingExceptions"
            @click="testExceptionHandling"
          >
            异常处理测试
          </el-button>
          <el-button 
            :loading="isRunningStressTest"
            @click="showStressTestDialog"
          >
            压力测试
          </el-button>
        </el-button-group>
      </div>
    </el-card>
    
    <!-- 测试摘要 -->
    <el-card class="test-summary" shadow="never">
      <template #header>
        <span>测试摘要</span>
      </template>
      
      <div class="summary-grid">
        <div class="summary-item">
          <div class="summary-value">{{ testSummary.total_suites || 0 }}</div>
          <div class="summary-label">测试套件</div>
        </div>
        <div class="summary-item">
          <div class="summary-value">{{ testSummary.total_tests || 0 }}</div>
          <div class="summary-label">测试用例</div>
        </div>
        <div class="summary-item">
          <div class="summary-value success">{{ testSummary.total_passed || 0 }}</div>
          <div class="summary-label">通过</div>
        </div>
        <div class="summary-item">
          <div class="summary-value danger">{{ testSummary.total_failed || 0 }}</div>
          <div class="summary-label">失败</div>
        </div>
        <div class="summary-item">
          <div class="summary-value">{{ Math.round(testSummary.overall_success_rate || 0) }}%</div>
          <div class="summary-label">成功率</div>
        </div>
      </div>
    </el-card>
    
    <!-- 测试套件列表 -->
    <el-card class="test-suites" shadow="never">
      <template #header>
        <span>测试套件</span>
      </template>
      
      <el-table 
        :data="testSuites" 
        v-loading="isLoadingTestSuites"
        empty-text="暂无测试套件"
      >
        <el-table-column prop="suite_name" label="套件名称" />
        <el-table-column prop="total_tests" label="测试数量" width="100" />
        <el-table-column label="通过率" width="120">
          <template #default="{ row }">
            <el-progress 
              :percentage="Math.round(row.passed_tests / row.total_tests * 100)"
              :color="getProgressColor(row.passed_tests / row.total_tests * 100)"
              :show-text="false"
              style="width: 80px"
            />
            <span class="progress-text">
              {{ Math.round(row.passed_tests / row.total_tests * 100) }}%
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="start_time" label="开始时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.start_time) }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag 
              :type="getStatusType(row)"
              size="small"
            >
              {{ getStatusText(row) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button 
              type="primary" 
              size="small" 
              @click="viewTestDetails(row)"
            >
              查看详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <!-- 健康检查 -->
    <el-card class="health-check" shadow="never">
      <template #header>
        <div class="card-header">
          <span>系统健康检查</span>
          <el-button 
            size="small" 
            @click="runHealthCheck"
            :loading="isRunningHealthCheck"
          >
            检查
          </el-button>
        </div>
      </template>
      
      <div class="health-grid" v-if="healthStatus">
        <div 
          v-for="(status, service) in healthStatus.services" 
          :key="service"
          class="health-item"
          :class="status"
        >
          <div class="health-icon">
            <el-icon v-if="status === 'healthy'"><CircleCheckFilled /></el-icon>
            <el-icon v-else><CircleCloseFilled /></el-icon>
          </div>
          <div class="health-label">{{ getServiceName(service) }}</div>
        </div>
      </div>
    </el-card>
    
    <!-- 测试详情对话框 -->
    <el-dialog
      v-model="showTestDetailsDialog"
      title="测试详情"
      width="80%"
      :close-on-click-modal="false"
    >
      <div v-if="selectedTestSuite" class="test-details">
        <div class="suite-info">
          <h3>{{ selectedTestSuite.suite_name }}</h3>
          <p>开始时间: {{ formatDateTime(selectedTestSuite.start_time) }}</p>
          <p>结束时间: {{ formatDateTime(selectedTestSuite.end_time) }}</p>
          <p>总耗时: {{ calculateDuration(selectedTestSuite.start_time, selectedTestSuite.end_time) }}</p>
        </div>
        
        <el-table :data="selectedTestSuite.tests" max-height="400">
          <el-table-column prop="test_name" label="测试名称" />
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag 
                :type="getTestStatusType(row.status)"
                size="small"
              >
                {{ row.status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="duration" label="耗时(秒)" width="100">
            <template #default="{ row }">
              {{ row.duration ? row.duration.toFixed(2) : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="详情" width="100">
            <template #default="{ row }">
              <el-button 
                v-if="row.details || row.error_message"
                type="text" 
                size="small"
                @click="showTestResult(row)"
              >
                查看
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>
    
    <!-- 测试结果对话框 -->
    <el-dialog
      v-model="showTestResultDialog"
      title="测试结果"
      width="60%"
    >
      <div v-if="selectedTestResult">
        <h4>{{ selectedTestResult.test_name }}</h4>
        
        <div v-if="selectedTestResult.error_message" class="error-message">
          <h5>错误信息:</h5>
          <pre>{{ selectedTestResult.error_message }}</pre>
        </div>
        
        <div v-if="selectedTestResult.details" class="test-details-content">
          <h5>测试详情:</h5>
          <pre>{{ JSON.stringify(selectedTestResult.details, null, 2) }}</pre>
        </div>
      </div>
    </el-dialog>
    
    <!-- 压力测试配置对话框 -->
    <el-dialog
      v-model="showStressTestConfigDialog"
      title="压力测试配置"
      width="500px"
    >
      <el-form :model="stressTestConfig" label-width="120px">
        <el-form-item label="并发用户数">
          <el-input-number 
            v-model="stressTestConfig.concurrent_users"
            :min="1"
            :max="100"
          />
        </el-form-item>
        <el-form-item label="每用户操作数">
          <el-input-number 
            v-model="stressTestConfig.operations_per_user"
            :min="1"
            :max="1000"
          />
        </el-form-item>
        <el-form-item label="测试时长(秒)">
          <el-input-number 
            v-model="stressTestConfig.test_duration"
            :min="60"
            :max="3600"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showStressTestConfigDialog = false">取消</el-button>
        <el-button 
          type="primary" 
          @click="runStressTest"
          :loading="isRunningStressTest"
        >
          开始测试
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Play, 
  Refresh, 
  CircleCheckFilled, 
  CircleCloseFilled 
} from '@element-plus/icons-vue'
import { integrationTestApi } from '@/api/integrationTest'
import { formatDateTime } from '@/utils/format'

// 响应式数据
const isRunningTest = ref(false)
const isValidatingData = ref(false)
const isSimulatingTrading = ref(false)
const isTestingExceptions = ref(false)
const isRunningStressTest = ref(false)
const isLoadingTestSuites = ref(false)
const isRunningHealthCheck = ref(false)

const testSummary = ref<any>({})
const testSuites = ref<any[]>([])
const healthStatus = ref<any>(null)

const showTestDetailsDialog = ref(false)
const showTestResultDialog = ref(false)
const showStressTestConfigDialog = ref(false)

const selectedTestSuite = ref<any>(null)
const selectedTestResult = ref<any>(null)

const stressTestConfig = ref({
  concurrent_users: 10,
  operations_per_user: 100,
  test_duration: 300
})

// 计算属性
const getProgressColor = (percentage: number) => {
  if (percentage >= 90) return '#67c23a'
  if (percentage >= 70) return '#e6a23c'
  return '#f56c6c'
}

// 方法
const runFullIntegrationTest = async () => {
  try {
    isRunningTest.value = true
    
    const result = await integrationTestApi.runIntegrationTests()
    
    ElMessage.success('集成测试已开始运行，请稍后查看结果')
    
    // 延迟刷新数据
    setTimeout(() => {
      refreshTestData()
    }, 5000)
    
  } catch (error: any) {
    ElMessage.error(error.message || '运行集成测试失败')
  } finally {
    isRunningTest.value = false
  }
}

const validateDataConsistency = async () => {
  try {
    isValidatingData.value = true
    
    const result = await integrationTestApi.validateDataConsistency()
    
    ElMessageBox.alert(
      `数据一致性检查完成\n检查项目: ${Object.keys(result.consistency_checks).length}`,
      '检查结果',
      { type: 'success' }
    )
    
  } catch (error: any) {
    ElMessage.error(error.message || '数据一致性检查失败')
  } finally {
    isValidatingData.value = false
  }
}

const simulateTradingScenario = async () => {
  try {
    isSimulatingTrading.value = true
    
    const result = await integrationTestApi.simulateTradingScenario({})
    
    ElMessage.success('交易场景模拟完成')
    
  } catch (error: any) {
    ElMessage.error(error.message || '交易场景模拟失败')
  } finally {
    isSimulatingTrading.value = false
  }
}

const testExceptionHandling = async () => {
  try {
    isTestingExceptions.value = true
    
    const result = await integrationTestApi.testExceptionHandling()
    
    ElMessage.success('异常处理测试完成')
    
  } catch (error: any) {
    ElMessage.error(error.message || '异常处理测试失败')
  } finally {
    isTestingExceptions.value = false
  }
}

const showStressTestDialog = () => {
  showStressTestConfigDialog.value = true
}

const runStressTest = async () => {
  try {
    isRunningStressTest.value = true
    
    const result = await integrationTestApi.runStressTest(stressTestConfig.value)
    
    ElMessage.success('压力测试已开始运行')
    showStressTestConfigDialog.value = false
    
  } catch (error: any) {
    ElMessage.error(error.message || '启动压力测试失败')
  } finally {
    isRunningStressTest.value = false
  }
}

const runHealthCheck = async () => {
  try {
    isRunningHealthCheck.value = true
    
    const result = await integrationTestApi.healthCheck()
    healthStatus.value = result
    
    const status = result.overall_status === 'healthy' ? 'success' : 'warning'
    ElMessage({
      type: status,
      message: `系统健康检查完成，状态: ${result.overall_status}`
    })
    
  } catch (error: any) {
    ElMessage.error(error.message || '健康检查失败')
  } finally {
    isRunningHealthCheck.value = false
  }
}

const refreshTestData = async () => {
  await Promise.all([
    loadTestSummary(),
    loadTestSuites()
  ])
}

const loadTestSummary = async () => {
  try {
    const result = await integrationTestApi.getTestSummary()
    testSummary.value = result
  } catch (error: any) {
    console.error('加载测试摘要失败:', error)
  }
}

const loadTestSuites = async () => {
  try {
    isLoadingTestSuites.value = true
    const result = await integrationTestApi.getTestSuites()
    testSuites.value = result
  } catch (error: any) {
    console.error('加载测试套件失败:', error)
  } finally {
    isLoadingTestSuites.value = false
  }
}

const viewTestDetails = (suite: any) => {
  selectedTestSuite.value = suite
  showTestDetailsDialog.value = true
}

const showTestResult = (testResult: any) => {
  selectedTestResult.value = testResult
  showTestResultDialog.value = true
}

const getStatusType = (suite: any) => {
  if (!suite.end_time) return 'warning'
  const successRate = suite.passed_tests / suite.total_tests
  if (successRate === 1) return 'success'
  if (successRate >= 0.8) return 'warning'
  return 'danger'
}

const getStatusText = (suite: any) => {
  if (!suite.end_time) return '运行中'
  const successRate = suite.passed_tests / suite.total_tests
  if (successRate === 1) return '全部通过'
  if (successRate >= 0.8) return '部分通过'
  return '失败'
}

const getTestStatusType = (status: string) => {
  switch (status) {
    case 'passed': return 'success'
    case 'failed': return 'danger'
    case 'running': return 'warning'
    case 'skipped': return 'info'
    default: return 'info'
  }
}

const getServiceName = (service: string) => {
  const names: Record<string, string> = {
    'database': '数据库',
    'strategy_service': '策略服务',
    'backtest_service': '回测服务',
    'order_service': '订单服务',
    'position_service': '持仓服务',
    'transaction_service': '交易服务'
  }
  return names[service] || service
}

const calculateDuration = (startTime: string, endTime: string) => {
  if (!endTime) return '-'
  const start = new Date(startTime)
  const end = new Date(endTime)
  const duration = (end.getTime() - start.getTime()) / 1000
  return `${duration.toFixed(2)}秒`
}

// 生命周期
onMounted(() => {
  refreshTestData()
  runHealthCheck()
})
</script>

<style scoped>
.integration-test-view {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  margin: 0 0 8px 0;
  color: var(--el-text-color-primary);
}

.page-description {
  color: var(--el-text-color-regular);
  margin: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.test-control-panel {
  margin-bottom: 20px;
}

.control-grid {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.test-summary {
  margin-bottom: 20px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 20px;
}

.summary-item {
  text-align: center;
  padding: 16px;
  background: var(--el-fill-color-lighter);
  border-radius: 8px;
}

.summary-value {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 4px;
}

.summary-value.success {
  color: var(--el-color-success);
}

.summary-value.danger {
  color: var(--el-color-danger);
}

.summary-label {
  font-size: 14px;
  color: var(--el-text-color-regular);
}

.test-suites {
  margin-bottom: 20px;
}

.progress-text {
  margin-left: 8px;
  font-size: 12px;
  color: var(--el-text-color-regular);
}

.health-check {
  margin-bottom: 20px;
}

.health-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
}

.health-item {
  display: flex;
  align-items: center;
  padding: 12px;
  border-radius: 8px;
  background: var(--el-fill-color-lighter);
}

.health-item.healthy {
  background: var(--el-color-success-light-9);
  color: var(--el-color-success);
}

.health-item.unhealthy {
  background: var(--el-color-danger-light-9);
  color: var(--el-color-danger);
}

.health-icon {
  margin-right: 8px;
}

.health-label {
  font-weight: 500;
}

.test-details {
  max-height: 600px;
  overflow-y: auto;
}

.suite-info {
  margin-bottom: 20px;
  padding: 16px;
  background: var(--el-fill-color-lighter);
  border-radius: 8px;
}

.suite-info h3 {
  margin: 0 0 12px 0;
  color: var(--el-text-color-primary);
}

.suite-info p {
  margin: 4px 0;
  color: var(--el-text-color-regular);
}

.error-message {
  margin-bottom: 20px;
}

.error-message h5 {
  color: var(--el-color-danger);
  margin-bottom: 8px;
}

.error-message pre {
  background: var(--el-color-danger-light-9);
  padding: 12px;
  border-radius: 4px;
  color: var(--el-color-danger);
  white-space: pre-wrap;
  word-break: break-all;
}

.test-details-content h5 {
  color: var(--el-text-color-primary);
  margin-bottom: 8px;
}

.test-details-content pre {
  background: var(--el-fill-color-lighter);
  padding: 12px;
  border-radius: 4px;
  color: var(--el-text-color-regular);
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 300px;
  overflow-y: auto;
}
</style>