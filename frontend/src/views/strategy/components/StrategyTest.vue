<template>
  <div class="strategy-test">
    <el-card>
      <template #header>
        <div class="test-header">
          <span>策略测试</span>
          <div class="test-actions">
            <el-button-group>
              <el-button
                @click="runUnitTests"
                :loading="testing.unit"
                type="primary"
                size="small"
              >
                <el-icon><Cpu /></el-icon>
                单元测试
              </el-button>
              <el-button
                @click="runIntegrationTests"
                :loading="testing.integration"
                type="success"
                size="small"
              >
                <el-icon><Connection /></el-icon>
                集成测试
              </el-button>
              <el-button
                @click="runPerformanceTest"
                :loading="testing.performance"
                type="warning"
                size="small"
              >
                <el-icon><Timer /></el-icon>
                性能测试
              </el-button>
              <el-button
                @click="runFullTestSuite"
                :loading="testing.full"
                type="info"
                size="small"
              >
                <el-icon><List /></el-icon>
                完整测试
              </el-button>
            </el-button-group>
          </div>
        </div>
      </template>
      
      <!-- 测试配置 -->
      <div class="test-config" v-if="showConfig">
        <el-form :model="testConfig" label-width="100px" size="small">
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="测试代码">
                <el-radio-group v-model="testConfig.codeSource">
                  <el-radio label="current">当前代码</el-radio>
                  <el-radio label="custom">自定义代码</el-radio>
                </el-radio-group>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="入口函数">
                <el-input v-model="testConfig.entryPoint" placeholder="main" />
              </el-form-item>
            </el-col>
          </el-row>
          
          <el-form-item v-if="testConfig.codeSource === 'custom'" label="自定义代码">
            <el-input
              v-model="testConfig.customCode"
              type="textarea"
              :rows="10"
              placeholder="请输入要测试的策略代码"
            />
          </el-form-item>
        </el-form>
      </div>
      
      <!-- 测试结果 -->
      <div class="test-results" v-if="hasResults">
        <!-- 测试概览 -->
        <div class="test-overview" v-if="testReport">
          <el-row :gutter="20">
            <el-col :span="6">
              <div class="overview-item">
                <div class="overview-value">{{ testReport.summary.total_tests }}</div>
                <div class="overview-label">总测试数</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="overview-item success">
                <div class="overview-value">{{ testReport.summary.passed_tests }}</div>
                <div class="overview-label">通过测试</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="overview-item danger">
                <div class="overview-value">{{ testReport.summary.failed_tests }}</div>
                <div class="overview-label">失败测试</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="overview-item">
                <div class="overview-value">{{ formatPercent(testReport.summary.success_rate) }}</div>
                <div class="overview-label">成功率</div>
              </div>
            </el-col>
          </el-row>
        </div>
        
        <!-- 测试套件结果 -->
        <div class="test-suites" v-if="testSuites.length > 0">
          <el-collapse v-model="activeCollapse">
            <el-collapse-item
              v-for="(suite, index) in testSuites"
              :key="index"
              :name="index.toString()"
            >
              <template #title>
                <div class="suite-title">
                  <span class="suite-name">{{ suite.name }}</span>
                  <div class="suite-stats">
                    <el-tag
                      :type="suite.failed_tests === 0 ? 'success' : 'danger'"
                      size="small"
                    >
                      {{ suite.passed_tests }}/{{ suite.total_tests }}
                    </el-tag>
                    <span class="suite-time">{{ formatTime(suite.total_time) }}</span>
                  </div>
                </div>
              </template>
              
              <div class="suite-content">
                <p class="suite-description">{{ suite.description }}</p>
                
                <!-- 测试用例列表 -->
                <div class="test-cases">
                  <div
                    v-for="(test, testIndex) in suite.tests"
                    :key="testIndex"
                    class="test-case"
                    :class="{ 'passed': test.passed, 'failed': !test.passed }"
                  >
                    <div class="test-case-header">
                      <div class="test-case-title">
                        <el-icon class="test-status-icon">
                          <Check v-if="test.passed" />
                          <Close v-else />
                        </el-icon>
                        <span class="test-name">{{ test.test_name }}</span>
                      </div>
                      <div class="test-case-meta">
                        <span class="test-time">{{ formatTime(test.execution_time) }}</span>
                      </div>
                    </div>
                    
                    <!-- 测试输出 -->
                    <div v-if="test.output" class="test-output">
                      <el-text type="success" size="small">{{ test.output }}</el-text>
                    </div>
                    
                    <!-- 错误信息 -->
                    <div v-if="test.error_message" class="test-error">
                      <el-alert
                        :title="test.error_message"
                        type="error"
                        :closable="false"
                        show-icon
                      />
                    </div>
                  </div>
                </div>
              </div>
            </el-collapse-item>
          </el-collapse>
        </div>
        
        <!-- 性能指标 -->
        <div class="performance-metrics" v-if="performanceMetrics">
          <el-card>
            <template #header>
              <span>性能指标</span>
            </template>
            
            <el-row :gutter="20">
              <el-col :span="6">
                <div class="metric-item">
                  <div class="metric-value">{{ formatTime(performanceMetrics.execution_time) }}</div>
                  <div class="metric-label">平均执行时间</div>
                </div>
              </el-col>
              <el-col :span="6">
                <div class="metric-item">
                  <div class="metric-value">{{ performanceMetrics.function_calls }}</div>
                  <div class="metric-label">函数调用数</div>
                </div>
              </el-col>
              <el-col :span="6">
                <div class="metric-item">
                  <div class="metric-value">{{ performanceMetrics.complexity_score }}</div>
                  <div class="metric-label">复杂度分数</div>
                </div>
              </el-col>
              <el-col :span="6">
                <div class="metric-item">
                  <div class="metric-value">{{ formatMemory(performanceMetrics.memory_usage) }}</div>
                  <div class="metric-label">内存使用</div>
                </div>
              </el-col>
            </el-row>
          </el-card>
        </div>
        
        <!-- 改进建议 -->
        <div class="recommendations" v-if="testReport && testReport.recommendations.length > 0">
          <el-card>
            <template #header>
              <span>改进建议</span>
            </template>
            
            <ul class="recommendation-list">
              <li
                v-for="(recommendation, index) in testReport.recommendations"
                :key="index"
                class="recommendation-item"
              >
                <el-icon class="recommendation-icon"><InfoFilled /></el-icon>
                {{ recommendation }}
              </li>
            </ul>
          </el-card>
        </div>
      </div>
      
      <!-- 空状态 -->
      <EmptyState
        v-else
        type="info"
        title="开始测试策略"
        description="选择上方的测试类型来验证您的策略代码"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Cpu, Connection, Timer, List, Check, Close, InfoFilled
} from '@element-plus/icons-vue'

import { EmptyState } from '@/components/common'
import { StrategyApi } from '@/api/strategy'
import { formatPercent } from '@/utils/format'

interface Props {
  strategyId: number
  currentCode?: string
  entryPoint?: string
}

interface TestCase {
  test_name: string
  passed: boolean
  execution_time: number
  error_message?: string
  output?: string
}

interface TestSuite {
  name: string
  description: string
  total_tests: number
  passed_tests: number
  failed_tests: number
  total_time: number
  coverage: number
  tests: TestCase[]
}

interface PerformanceMetrics {
  execution_time: number
  memory_usage: number
  cpu_usage: number
  function_calls: number
  complexity_score: number
}

interface TestReport {
  summary: {
    total_tests: number
    passed_tests: number
    failed_tests: number
    success_rate: number
    total_execution_time: number
  }
  test_suites: TestSuite[]
  performance_metrics: PerformanceMetrics
  recommendations: string[]
}

const props = defineProps<Props>()

// 响应式数据
const showConfig = ref(false)
const testConfig = ref({
  codeSource: 'current' as 'current' | 'custom',
  customCode: '',
  entryPoint: props.entryPoint || 'main'
})

const testing = ref({
  unit: false,
  integration: false,
  performance: false,
  full: false
})

const testSuites = ref<TestSuite[]>([])
const performanceMetrics = ref<PerformanceMetrics>()
const testReport = ref<TestReport>()
const activeCollapse = ref<string[]>([])

// 计算属性
const hasResults = computed(() => {
  return testSuites.value.length > 0 || performanceMetrics.value || testReport.value
})

// 方法
const getTestData = () => {
  return {
    code: testConfig.value.codeSource === 'custom' ? testConfig.value.customCode : props.currentCode,
    entry_point: testConfig.value.entryPoint
  }
}

const runUnitTests = async () => {
  try {
    testing.value.unit = true
    
    const response = await StrategyApi.runUnitTests(props.strategyId, getTestData())
    
    if (response.success) {
      testSuites.value = [response.data]
      activeCollapse.value = ['0']
      ElMessage.success('单元测试完成')
    } else {
      ElMessage.error(response.message || '单元测试失败')
    }
  } catch (error) {
    console.error('单元测试失败:', error)
    ElMessage.error('单元测试失败')
  } finally {
    testing.value.unit = false
  }
}

const runIntegrationTests = async () => {
  try {
    testing.value.integration = true
    
    const response = await StrategyApi.runIntegrationTests(props.strategyId, getTestData())
    
    if (response.success) {
      testSuites.value = [response.data]
      activeCollapse.value = ['0']
      ElMessage.success('集成测试完成')
    } else {
      ElMessage.error(response.message || '集成测试失败')
    }
  } catch (error) {
    console.error('集成测试失败:', error)
    ElMessage.error('集成测试失败')
  } finally {
    testing.value.integration = false
  }
}

const runPerformanceTest = async () => {
  try {
    testing.value.performance = true
    
    const response = await StrategyApi.runPerformanceTest(props.strategyId, getTestData())
    
    if (response.success) {
      performanceMetrics.value = response.data
      testSuites.value = []
      testReport.value = undefined
      ElMessage.success('性能测试完成')
    } else {
      ElMessage.error(response.message || '性能测试失败')
    }
  } catch (error) {
    console.error('性能测试失败:', error)
    ElMessage.error('性能测试失败')
  } finally {
    testing.value.performance = false
  }
}

const runFullTestSuite = async () => {
  try {
    testing.value.full = true
    
    const response = await StrategyApi.runFullTestSuite(props.strategyId, getTestData())
    
    if (response.success) {
      testReport.value = response.data
      testSuites.value = response.data.test_suites
      performanceMetrics.value = response.data.performance_metrics
      
      // 默认展开所有测试套件
      activeCollapse.value = testSuites.value.map((_, index) => index.toString())
      
      ElMessage.success('完整测试套件执行完成')
    } else {
      ElMessage.error(response.message || '测试套件执行失败')
    }
  } catch (error) {
    console.error('测试套件执行失败:', error)
    ElMessage.error('测试套件执行失败')
  } finally {
    testing.value.full = false
  }
}

const formatTime = (seconds: number) => {
  if (seconds < 1) {
    return `${Math.round(seconds * 1000)}ms`
  }
  return `${seconds.toFixed(2)}s`
}

const formatMemory = (bytes: number) => {
  if (bytes === 0) return '0 B'
  
  const units = ['B', 'KB', 'MB', 'GB']
  const k = 1024
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return `${(bytes / Math.pow(k, i)).toFixed(2)} ${units[i]}`
}
</script>

<style lang="scss" scoped>
.strategy-test {
  .test-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
  }
  
  .test-config {
    margin-bottom: 24px;
    padding: 16px;
    background: var(--el-fill-color-light);
    border-radius: 4px;
  }
  
  .test-results {
    .test-overview {
      margin-bottom: 24px;
      
      .overview-item {
        text-align: center;
        padding: 16px;
        background: var(--el-fill-color-light);
        border-radius: 8px;
        
        .overview-value {
          font-size: 24px;
          font-weight: 600;
          margin-bottom: 8px;
          color: var(--el-text-color-primary);
        }
        
        .overview-label {
          font-size: 12px;
          color: var(--el-text-color-secondary);
        }
        
        &.success .overview-value {
          color: var(--el-color-success);
        }
        
        &.danger .overview-value {
          color: var(--el-color-danger);
        }
      }
    }
    
    .test-suites {
      margin-bottom: 24px;
      
      .suite-title {
        display: flex;
        justify-content: space-between;
        align-items: center;
        width: 100%;
        
        .suite-name {
          font-weight: 600;
        }
        
        .suite-stats {
          display: flex;
          align-items: center;
          gap: 8px;
          
          .suite-time {
            font-size: 12px;
            color: var(--el-text-color-secondary);
          }
        }
      }
      
      .suite-content {
        .suite-description {
          margin: 0 0 16px 0;
          color: var(--el-text-color-secondary);
          font-size: 14px;
        }
        
        .test-cases {
          .test-case {
            margin-bottom: 12px;
            padding: 12px;
            border-radius: 4px;
            border-left: 3px solid var(--el-border-color);
            
            &.passed {
              background: var(--el-color-success-light-9);
              border-left-color: var(--el-color-success);
            }
            
            &.failed {
              background: var(--el-color-danger-light-9);
              border-left-color: var(--el-color-danger);
            }
            
            .test-case-header {
              display: flex;
              justify-content: space-between;
              align-items: center;
              margin-bottom: 8px;
              
              .test-case-title {
                display: flex;
                align-items: center;
                gap: 8px;
                
                .test-status-icon {
                  font-size: 16px;
                  
                  .passed & {
                    color: var(--el-color-success);
                  }
                  
                  .failed & {
                    color: var(--el-color-danger);
                  }
                }
                
                .test-name {
                  font-weight: 500;
                }
              }
              
              .test-case-meta {
                .test-time {
                  font-size: 12px;
                  color: var(--el-text-color-secondary);
                }
              }
            }
            
            .test-output {
              margin-top: 8px;
              padding: 8px;
              background: var(--el-fill-color-lighter);
              border-radius: 4px;
              font-size: 12px;
            }
            
            .test-error {
              margin-top: 8px;
            }
          }
        }
      }
    }
    
    .performance-metrics {
      margin-bottom: 24px;
      
      .metric-item {
        text-align: center;
        
        .metric-value {
          font-size: 18px;
          font-weight: 600;
          color: var(--el-text-color-primary);
          margin-bottom: 4px;
        }
        
        .metric-label {
          font-size: 12px;
          color: var(--el-text-color-secondary);
        }
      }
    }
    
    .recommendations {
      .recommendation-list {
        margin: 0;
        padding: 0;
        list-style: none;
        
        .recommendation-item {
          display: flex;
          align-items: flex-start;
          gap: 8px;
          margin-bottom: 12px;
          padding: 8px;
          background: var(--el-color-info-light-9);
          border-radius: 4px;
          
          .recommendation-icon {
            color: var(--el-color-info);
            margin-top: 2px;
            flex-shrink: 0;
          }
        }
      }
    }
  }
}
</style>