/**
 * 集成测试API
 */
import { request } from '@/utils/request'

export interface TestSuite {
  suite_id: string
  suite_name: string
  start_time: string
  end_time?: string
  total_tests: number
  passed_tests: number
  failed_tests: number
  skipped_tests: number
  success_rate: number
  tests: TestResult[]
}

export interface TestResult {
  test_id: string
  test_name: string
  status: 'pending' | 'running' | 'passed' | 'failed' | 'skipped'
  start_time: string
  end_time?: string
  duration?: number
  error_message?: string
  details?: any
}

export interface TestSummary {
  total_suites: number
  total_tests: number
  total_passed: number
  total_failed: number
  overall_success_rate: number
  latest_suite?: TestSuite
}

export interface HealthStatus {
  overall_status: 'healthy' | 'unhealthy'
  services: Record<string, 'healthy' | 'unhealthy'>
  timestamp: string
}

export interface StressTestConfig {
  concurrent_users: number
  operations_per_user: number
  test_duration: number
}

export const integrationTestApi = {
  /**
   * 运行完整集成测试
   */
  async runIntegrationTests(): Promise<{ message: string; status: string }> {
    return request.post('/v1/integration-tests/run')
  },

  /**
   * 获取所有测试套件
   */
  async getTestSuites(): Promise<TestSuite[]> {
    return request.get('/v1/integration-tests/suites')
  },

  /**
   * 获取指定测试套件
   */
  async getTestSuite(suiteId: string): Promise<TestSuite> {
    return request.get(`/v1/integration-tests/suites/${suiteId}`)
  },

  /**
   * 获取测试摘要
   */
  async getTestSummary(): Promise<TestSummary> {
    return request.get('/v1/integration-tests/summary')
  },

  /**
   * 验证数据一致性
   */
  async validateDataConsistency(): Promise<{
    status: string
    consistency_checks: any
    timestamp: string
  }> {
    return request.post('/v1/integration-tests/validate-data-consistency')
  },

  /**
   * 模拟交易场景
   */
  async simulateTradingScenario(config: any): Promise<{
    status: string
    scenario: string
    results: any
    timestamp: string
  }> {
    return request.post('/v1/integration-tests/simulate-trading-scenario', config)
  },

  /**
   * 测试异常处理
   */
  async testExceptionHandling(): Promise<{
    status: string
    exception_tests: any
    timestamp: string
  }> {
    return request.post('/v1/integration-tests/test-exception-handling')
  },

  /**
   * 健康检查
   */
  async healthCheck(): Promise<HealthStatus> {
    return request.get('/v1/integration-tests/health-check')
  },

  /**
   * 运行压力测试
   */
  async runStressTest(config: StressTestConfig): Promise<{
    message: string
    status: string
    config: StressTestConfig
  }> {
    return request.post('/v1/integration-tests/stress-test', config)
  }
}