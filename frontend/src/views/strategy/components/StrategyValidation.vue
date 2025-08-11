<template>
  <div class="strategy-validation">
    <div class="validation-header">
      <h3>策略代码验证</h3>
      <div class="validation-actions">
        <el-button 
          type="primary" 
          :loading="validating" 
          @click="validateCode"
          icon="el-icon-check"
        >
          验证代码
        </el-button>
        <el-button 
          type="success" 
          :loading="testing" 
          @click="runTests"
          icon="el-icon-cpu"
        >
          运行测试
        </el-button>
        <el-button 
          type="warning" 
          :loading="analyzing" 
          @click="analyzeQuality"
          icon="el-icon-data-analysis"
        >
          质量分析
        </el-button>
        <el-button 
          type="danger" 
          :loading="scanning" 
          @click="securityScan"
          icon="el-icon-lock"
        >
          安全扫描
        </el-button>
      </div>
    </div>

    <!-- 验证结果概览 -->
    <div v-if="validationResult" class="validation-overview">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="metric-card">
            <div class="metric">
              <div class="metric-value" :class="validationResult.is_valid ? 'success' : 'error'">
                {{ validationResult.is_valid ? '通过' : '失败' }}
              </div>
              <div class="metric-label">验证状态</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="metric-card">
            <div class="metric">
              <div class="metric-value">{{ validationResult.issues.length }}</div>
              <div class="metric-label">问题总数</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="metric-card">
            <div class="metric">
              <div class="metric-value">{{ validationResult.dependencies.length }}</div>
              <div class="metric-label">依赖数量</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="metric-card">
            <div class="metric">
              <div class="metric-value">{{ validationResult.execution_time.toFixed(3) }}s</div>
              <div class="metric-label">验证耗时</div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 详细结果标签页 -->
    <el-tabs v-model="activeTab" class="validation-tabs">
      <!-- 验证问题 -->
      <el-tab-pane label="验证问题" name="issues">
        <div v-if="validationResult && validationResult.issues.length > 0">
          <el-table :data="validationResult.issues" style="width: 100%">
            <el-table-column prop="level" label="级别" width="80">
              <template #default="scope">
                <el-tag 
                  :type="getIssueTagType(scope.row.level)"
                  size="small"
                >
                  {{ scope.row.level }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="category" label="分类" width="100">
              <template #default="scope">
                <el-tag 
                  :type="getCategoryTagType(scope.row.category)"
                  size="small"
                  effect="plain"
                >
                  {{ getCategoryLabel(scope.row.category) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="message" label="问题描述" min-width="200" />
            <el-table-column prop="line_number" label="行号" width="80" />
            <el-table-column prop="suggestion" label="建议" min-width="200" />
          </el-table>
        </div>
        <el-empty v-else description="暂无验证问题" />
      </el-tab-pane>

      <!-- 代码指标 -->
      <el-tab-pane label="代码指标" name="metrics">
        <div v-if="validationResult">
          <el-row :gutter="20">
            <el-col :span="12">
              <el-card title="基础指标">
                <div class="metrics-grid">
                  <div class="metric-item">
                    <span class="metric-name">代码行数</span>
                    <span class="metric-value">{{ validationResult.code_metrics.lines_of_code }}</span>
                  </div>
                  <div class="metric-item">
                    <span class="metric-name">注释行数</span>
                    <span class="metric-value">{{ validationResult.code_metrics.lines_of_comments }}</span>
                  </div>
                  <div class="metric-item">
                    <span class="metric-name">空白行数</span>
                    <span class="metric-value">{{ validationResult.code_metrics.blank_lines }}</span>
                  </div>
                  <div class="metric-item">
                    <span class="metric-name">函数数量</span>
                    <span class="metric-value">{{ validationResult.code_metrics.functions_count }}</span>
                  </div>
                  <div class="metric-item">
                    <span class="metric-name">类数量</span>
                    <span class="metric-value">{{ validationResult.code_metrics.classes_count }}</span>
                  </div>
                  <div class="metric-item">
                    <span class="metric-name">复杂度评分</span>
                    <span class="metric-value">{{ validationResult.code_metrics.complexity_score }}</span>
                  </div>
                </div>
              </el-card>
            </el-col>
            <el-col :span="12">
              <el-card title="质量指标">
                <div class="quality-indicators">
                  <div class="quality-item">
                    <span class="quality-name">可维护性指数</span>
                    <el-progress 
                      :percentage="validationResult.code_metrics.maintainability_index" 
                      :color="getProgressColor(validationResult.code_metrics.maintainability_index)"
                    />
                  </div>
                  <div class="quality-item">
                    <span class="quality-name">注释覆盖率</span>
                    <el-progress 
                      :percentage="getCommentCoverage()" 
                      :color="getProgressColor(getCommentCoverage())"
                    />
                  </div>
                </div>
              </el-card>
            </el-col>
          </el-row>
        </div>
      </el-tab-pane>

      <!-- 依赖信息 -->
      <el-tab-pane label="依赖信息" name="dependencies">
        <div v-if="validationResult && validationResult.dependencies.length > 0">
          <el-table :data="getDependencyTableData()" style="width: 100%">
            <el-table-column prop="name" label="依赖名称" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="scope">
                <el-tag 
                  :type="scope.row.available ? 'success' : 'danger'"
                  size="small"
                >
                  {{ scope.row.available ? '可用' : '缺失' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="category" label="分类" width="120">
              <template #default="scope">
                <el-tag size="small" effect="plain">
                  {{ getDependencyCategory(scope.row.name) }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </div>
        <el-empty v-else description="暂无依赖信息" />
      </el-tab-pane>

      <!-- 入口点 -->
      <el-tab-pane label="入口点" name="entry-points">
        <div v-if="validationResult && validationResult.entry_points.length > 0">
          <el-table :data="getEntryPointsTableData()" style="width: 100%">
            <el-table-column prop="name" label="函数名称" />
            <el-table-column prop="type" label="类型" width="100">
              <template #default="scope">
                <el-tag size="small" effect="plain">
                  {{ scope.row.type }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="required" label="是否必需" width="100">
              <template #default="scope">
                <el-tag 
                  :type="scope.row.required ? 'warning' : 'info'"
                  size="small"
                >
                  {{ scope.row.required ? '必需' : '可选' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="description" label="描述" />
          </el-table>
        </div>
        <el-empty v-else description="暂无入口点信息" />
      </el-tab-pane>

      <!-- 测试结果 -->
      <el-tab-pane label="测试结果" name="test-results">
        <div v-if="testResult">
          <div class="test-summary">
            <el-row :gutter="20">
              <el-col :span="6">
                <el-statistic title="总测试数" :value="testResult.total_tests" />
              </el-col>
              <el-col :span="6">
                <el-statistic title="通过测试" :value="testResult.passed_tests" />
              </el-col>
              <el-col :span="6">
                <el-statistic title="失败测试" :value="testResult.failed_tests" />
              </el-col>
              <el-col :span="6">
                <el-statistic title="执行时间" :value="testResult.total_execution_time" suffix="s" />
              </el-col>
            </el-row>
          </div>
          
          <el-table :data="testResult.test_results" style="width: 100%; margin-top: 20px;">
            <el-table-column prop="name" label="测试名称" />
            <el-table-column prop="passed" label="状态" width="100">
              <template #default="scope">
                <el-tag 
                  :type="scope.row.passed ? 'success' : 'danger'"
                  size="small"
                >
                  {{ scope.row.passed ? '通过' : '失败' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="execution_time" label="执行时间" width="120">
              <template #default="scope">
                {{ scope.row.execution_time.toFixed(3) }}s
              </template>
            </el-table-column>
            <el-table-column prop="output" label="输出" min-width="200" />
            <el-table-column prop="error" label="错误信息" min-width="200" />
          </el-table>
        </div>
        <el-empty v-else description="暂无测试结果" />
      </el-tab-pane>

      <!-- 质量分析 -->
      <el-tab-pane label="质量分析" name="quality">
        <div v-if="qualityAnalysis">
          <div class="quality-overview">
            <el-row :gutter="20">
              <el-col :span="8">
                <el-card>
                  <div class="quality-score">
                    <div class="score-circle">
                      <el-progress 
                        type="circle" 
                        :percentage="qualityAnalysis.quality_score"
                        :color="getQualityColor(qualityAnalysis.quality_score)"
                        :width="120"
                      >
                        <span class="score-text">{{ qualityAnalysis.grade }}</span>
                      </el-progress>
                    </div>
                    <div class="score-label">代码质量评分</div>
                  </div>
                </el-card>
              </el-col>
              <el-col :span="16">
                <el-card title="问题统计">
                  <el-row :gutter="20">
                    <el-col :span="12">
                      <el-statistic title="错误数量" :value="qualityAnalysis.error_count" />
                    </el-col>
                    <el-col :span="12">
                      <el-statistic title="警告数量" :value="qualityAnalysis.warning_count" />
                    </el-col>
                  </el-row>
                  <div class="suggestions" style="margin-top: 20px;">
                    <h4>改进建议</h4>
                    <ul>
                      <li v-for="suggestion in qualityAnalysis.suggestions" :key="suggestion">
                        {{ suggestion }}
                      </li>
                    </ul>
                  </div>
                </el-card>
              </el-col>
            </el-row>
          </div>
        </div>
        <el-empty v-else description="暂无质量分析结果" />
      </el-tab-pane>

      <!-- 安全扫描 -->
      <el-tab-pane label="安全扫描" name="security">
        <div v-if="securityScanResult">
          <div class="security-overview">
            <el-row :gutter="20">
              <el-col :span="8">
                <el-card>
                  <div class="security-score">
                    <div class="score-circle">
                      <el-progress 
                        type="circle" 
                        :percentage="securityScanResult.security_score"
                        :color="getSecurityColor(securityScanResult.security_score)"
                        :width="120"
                      >
                        <span class="score-text">{{ securityScanResult.risk_level.toUpperCase() }}</span>
                      </el-progress>
                    </div>
                    <div class="score-label">安全评分</div>
                  </div>
                </el-card>
              </el-col>
              <el-col :span="16">
                <el-card title="安全问题统计">
                  <el-row :gutter="20">
                    <el-col :span="12">
                      <el-statistic title="严重问题" :value="securityScanResult.critical_issues" />
                    </el-col>
                    <el-col :span="12">
                      <el-statistic title="警告问题" :value="securityScanResult.warning_issues" />
                    </el-col>
                  </el-row>
                  <div class="recommendations" style="margin-top: 20px;">
                    <h4>安全建议</h4>
                    <ul>
                      <li v-for="recommendation in securityScanResult.recommendations" :key="recommendation">
                        {{ recommendation }}
                      </li>
                    </ul>
                  </div>
                </el-card>
              </el-col>
            </el-row>
          </div>
          
          <el-table 
            v-if="securityScanResult.security_issues.length > 0"
            :data="securityScanResult.security_issues" 
            style="width: 100%; margin-top: 20px;"
          >
            <el-table-column prop="level" label="级别" width="80">
              <template #default="scope">
                <el-tag 
                  :type="getIssueTagType(scope.row.level)"
                  size="small"
                >
                  {{ scope.row.level }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="message" label="安全问题" min-width="200" />
            <el-table-column prop="line_number" label="行号" width="80" />
            <el-table-column prop="suggestion" label="修复建议" min-width="200" />
          </el-table>
        </div>
        <el-empty v-else description="暂无安全扫描结果" />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { strategyApi } from '@/api/strategy'

export default {
  name: 'StrategyValidation',
  props: {
    strategyId: {
      type: Number,
      required: true
    },
    code: {
      type: String,
      required: true
    }
  },
  setup(props) {
    const activeTab = ref('issues')
    const validating = ref(false)
    const testing = ref(false)
    const analyzing = ref(false)
    const scanning = ref(false)
    
    const validationResult = ref(null)
    const testResult = ref(null)
    const qualityAnalysis = ref(null)
    const securityScanResult = ref(null)

    // 验证代码
    const validateCode = async () => {
      validating.value = true
      try {
        const response = await strategyApi.validateCode(props.strategyId, {
          code: props.code
        })
        validationResult.value = response.data
        activeTab.value = 'issues'
        ElMessage.success('代码验证完成')
      } catch (error) {
        ElMessage.error('代码验证失败: ' + error.message)
      } finally {
        validating.value = false
      }
    }

    // 运行测试
    const runTests = async () => {
      testing.value = true
      try {
        const response = await strategyApi.runTests(props.strategyId, {
          code: props.code,
          test_type: 'default'
        })
        testResult.value = response.data
        activeTab.value = 'test-results'
        ElMessage.success('测试执行完成')
      } catch (error) {
        ElMessage.error('测试执行失败: ' + error.message)
      } finally {
        testing.value = false
      }
    }

    // 质量分析
    const analyzeQuality = async () => {
      analyzing.value = true
      try {
        const response = await strategyApi.analyzeQuality(props.strategyId, {
          code: props.code
        })
        qualityAnalysis.value = response.data
        activeTab.value = 'quality'
        ElMessage.success('质量分析完成')
      } catch (error) {
        ElMessage.error('质量分析失败: ' + error.message)
      } finally {
        analyzing.value = false
      }
    }

    // 安全扫描
    const securityScan = async () => {
      scanning.value = true
      try {
        const response = await strategyApi.securityScan(props.strategyId, {
          code: props.code
        })
        securityScanResult.value = response.data
        activeTab.value = 'security'
        ElMessage.success('安全扫描完成')
      } catch (error) {
        ElMessage.error('安全扫描失败: ' + error.message)
      } finally {
        scanning.value = false
      }
    }

    // 获取问题标签类型
    const getIssueTagType = (level) => {
      const typeMap = {
        'error': 'danger',
        'warning': 'warning',
        'info': 'info'
      }
      return typeMap[level] || 'info'
    }

    // 获取分类标签类型
    const getCategoryTagType = (category) => {
      const typeMap = {
        'syntax': 'danger',
        'security': 'danger',
        'performance': 'warning',
        'style': 'info',
        'dependency': 'warning',
        'logic': 'warning'
      }
      return typeMap[category] || 'info'
    }

    // 获取分类标签
    const getCategoryLabel = (category) => {
      const labelMap = {
        'syntax': '语法',
        'security': '安全',
        'performance': '性能',
        'style': '风格',
        'dependency': '依赖',
        'logic': '逻辑'
      }
      return labelMap[category] || category
    }

    // 获取进度条颜色
    const getProgressColor = (percentage) => {
      if (percentage >= 80) return '#67c23a'
      if (percentage >= 60) return '#e6a23c'
      return '#f56c6c'
    }

    // 获取质量颜色
    const getQualityColor = (score) => {
      if (score >= 90) return '#67c23a'
      if (score >= 80) return '#95d475'
      if (score >= 70) return '#e6a23c'
      if (score >= 60) return '#f78989'
      return '#f56c6c'
    }

    // 获取安全颜色
    const getSecurityColor = (score) => {
      if (score >= 80) return '#67c23a'
      if (score >= 60) return '#e6a23c'
      return '#f56c6c'
    }

    // 获取注释覆盖率
    const getCommentCoverage = () => {
      if (!validationResult.value) return 0
      const { lines_of_code, lines_of_comments } = validationResult.value.code_metrics
      if (lines_of_code === 0) return 0
      return Math.round((lines_of_comments / (lines_of_code + lines_of_comments)) * 100)
    }

    // 获取依赖表格数据
    const getDependencyTableData = () => {
      if (!validationResult.value) return []
      return validationResult.value.dependencies.map(dep => ({
        name: dep,
        available: true, // 这里需要从后端获取实际状态
        category: getDependencyCategory(dep)
      }))
    }

    // 获取依赖分类
    const getDependencyCategory = (depName) => {
      const categories = {
        'numpy': '数值计算',
        'pandas': '数据处理',
        'matplotlib': '数据可视化',
        'seaborn': '数据可视化',
        'scipy': '科学计算',
        'sklearn': '机器学习',
        'talib': '技术分析',
        'math': '数学函数',
        'datetime': '日期时间',
        'time': '时间处理',
        'json': '数据格式',
        'collections': '数据结构',
        'itertools': '迭代工具',
        'functools': '函数工具',
        'operator': '操作符',
        'statistics': '统计函数',
        'random': '随机数',
        'decimal': '精确小数',
        'fractions': '分数'
      }
      return categories[depName] || '其他'
    }

    // 获取入口点表格数据
    const getEntryPointsTableData = () => {
      if (!validationResult.value) return []
      const requiredFunctions = ['initialize', 'handle_data', 'before_trading_start', 'after_trading_end']
      return validationResult.value.entry_points.map(func => ({
        name: func,
        type: '函数',
        required: requiredFunctions.includes(func),
        description: getFunctionDescription(func)
      }))
    }

    // 获取函数描述
    const getFunctionDescription = (funcName) => {
      const descriptions = {
        'initialize': '策略初始化函数，在策略开始时调用',
        'handle_data': '数据处理函数，每个交易周期调用',
        'before_trading_start': '交易开始前调用的函数',
        'after_trading_end': '交易结束后调用的函数'
      }
      return descriptions[funcName] || '用户自定义函数'
    }

    return {
      activeTab,
      validating,
      testing,
      analyzing,
      scanning,
      validationResult,
      testResult,
      qualityAnalysis,
      securityScanResult,
      validateCode,
      runTests,
      analyzeQuality,
      securityScan,
      getIssueTagType,
      getCategoryTagType,
      getCategoryLabel,
      getProgressColor,
      getQualityColor,
      getSecurityColor,
      getCommentCoverage,
      getDependencyTableData,
      getDependencyCategory,
      getEntryPointsTableData,
      getFunctionDescription
    }
  }
}
</script>

<style scoped>
.strategy-validation {
  padding: 20px;
}

.validation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.validation-header h3 {
  margin: 0;
  color: #303133;
}

.validation-actions {
  display: flex;
  gap: 10px;
}

.validation-overview {
  margin-bottom: 20px;
}

.metric-card {
  text-align: center;
}

.metric {
  padding: 10px;
}

.metric-value {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 5px;
}

.metric-value.success {
  color: #67c23a;
}

.metric-value.error {
  color: #f56c6c;
}

.metric-label {
  color: #909399;
  font-size: 14px;
}

.validation-tabs {
  margin-top: 20px;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
}

.metric-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  background: var(--el-bg-color-page);
  border-radius: 4px;
}

.metric-name {
  color: #606266;
}

.metric-value {
  font-weight: bold;
  color: #303133;
}

.quality-indicators {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.quality-item {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.quality-name {
  color: #606266;
  font-size: 14px;
}

.test-summary {
  margin-bottom: 20px;
}

.quality-overview,
.security-overview {
  margin-bottom: 20px;
}

.quality-score,
.security-score {
  text-align: center;
}

.score-circle {
  margin-bottom: 10px;
}

.score-text {
  font-size: 18px;
  font-weight: bold;
}

.score-label {
  color: #909399;
  font-size: 14px;
}

.suggestions,
.recommendations {
  margin-top: 15px;
}

.suggestions h4,
.recommendations h4 {
  margin: 0 0 10px 0;
  color: #303133;
}

.suggestions ul,
.recommendations ul {
  margin: 0;
  padding-left: 20px;
}

.suggestions li,
.recommendations li {
  margin-bottom: 5px;
  color: #606266;
}
</style>