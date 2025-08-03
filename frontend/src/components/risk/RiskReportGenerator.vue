<template>
  <div class="risk-report-generator">
    <div class="header">
      <h3>风险报告生成</h3>
      <p>生成详细的风险分析报告，帮助您了解投资组合的风险状况</p>
    </div>

    <el-card>
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="120px"
        class="report-form"
      >
        <el-form-item label="报告类型" prop="report_type">
          <el-select v-model="form.report_type" placeholder="请选择报告类型" style="width: 300px">
            <el-option
              v-for="template in templates"
              :key="template.id"
              :label="template.name"
              :value="template.report_type"
            >
              <div class="template-option">
                <div class="template-name">{{ template.name }}</div>
                <div class="template-desc">{{ template.description }}</div>
              </div>
            </el-option>
          </el-select>
        </el-form-item>

        <el-form-item label="时间范围" prop="dateRange">
          <el-date-picker
            v-model="dateRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DD HH:mm:ss"
            style="width: 400px"
          />
        </el-form-item>

        <el-form-item label="报告内容">
          <el-checkbox-group v-model="form.sections">
            <el-checkbox label="executive_summary">执行摘要</el-checkbox>
            <el-checkbox label="risk_metrics">风险指标分析</el-checkbox>
            <el-checkbox label="risk_events">风险事件分析</el-checkbox>
            <el-checkbox label="position_analysis">持仓风险分析</el-checkbox>
            <el-checkbox label="risk_attribution">风险归因分析</el-checkbox>
            <el-checkbox label="trend_analysis">趋势分析</el-checkbox>
            <el-checkbox label="recommendations">改进建议</el-checkbox>
          </el-checkbox-group>
        </el-form-item>

        <el-form-item label="自定义配置">
          <el-switch
            v-model="showCustomConfig"
            active-text="启用"
            inactive-text="禁用"
          />
        </el-form-item>

        <el-form-item v-if="showCustomConfig" label="配置参数">
          <el-input
            v-model="customConfigJson"
            type="textarea"
            :rows="4"
            placeholder="请输入JSON格式的自定义配置"
            style="width: 500px"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="generateReport" :loading="generating">
            <el-icon><Document /></el-icon>
            生成报告
          </el-button>
          <el-button @click="resetForm">重置</el-button>
          <el-button @click="previewReport" :disabled="!canPreview">
            <el-icon><View /></el-icon>
            预览配置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 报告预览 -->
    <el-card v-if="showPreview" style="margin-top: 20px">
      <template #header>
        <div class="card-header">
          <span>报告配置预览</span>
          <el-button size="small" @click="showPreview = false">
            <el-icon><Close /></el-icon>
            关闭
          </el-button>
        </div>
      </template>

      <div class="preview-content">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="报告类型">
            {{ getReportTypeName(form.report_type) }}
          </el-descriptions-item>
          <el-descriptions-item label="时间范围">
            {{ dateRange ? `${dateRange[0]} 至 ${dateRange[1]}` : '未设置' }}
          </el-descriptions-item>
          <el-descriptions-item label="包含内容" :span="2">
            <el-tag
              v-for="section in form.sections"
              :key="section"
              size="small"
              style="margin-right: 8px"
            >
              {{ getSectionName(section) }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <div v-if="showCustomConfig && customConfigJson" class="custom-config-preview">
          <h4>自定义配置：</h4>
          <pre class="config-json">{{ formatJson(customConfigJson) }}</pre>
        </div>
      </div>
    </el-card>

    <!-- 生成进度 -->
    <el-card v-if="generating" style="margin-top: 20px">
      <div class="generation-progress">
        <div class="progress-header">
          <h4>正在生成报告...</h4>
          <el-progress :percentage="progress" :stroke-width="8" />
        </div>
        <div class="progress-steps">
          <div
            v-for="(step, index) in generationSteps"
            :key="index"
            class="step-item"
            :class="{ active: currentStep >= index, completed: currentStep > index }"
          >
            <el-icon>
              <Check v-if="currentStep > index" />
              <Loading v-else-if="currentStep === index" />
              <Clock v-else />
            </el-icon>
            <span>{{ step }}</span>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 生成结果 -->
    <el-card v-if="generatedReport" style="margin-top: 20px">
      <template #header>
        <div class="card-header">
          <span>报告生成完成</span>
          <div class="header-actions">
            <el-button size="small" @click="viewReport">
              <el-icon><View /></el-icon>
              查看报告
            </el-button>
            <el-dropdown @command="handleExport">
              <el-button size="small">
                <el-icon><Download /></el-icon>
                导出报告
                <el-icon><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="pdf">导出为PDF</el-dropdown-item>
                  <el-dropdown-item command="excel">导出为Excel</el-dropdown-item>
                  <el-dropdown-item command="json">导出为JSON</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </template>

      <div class="report-summary">
        <el-row :gutter="20">
          <el-col :span="8">
            <div class="summary-item">
              <div class="summary-label">报告ID</div>
              <div class="summary-value">{{ generatedReport.report_id }}</div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="summary-item">
              <div class="summary-label">风险评分</div>
              <div class="summary-value" :class="getRiskScoreClass(generatedReport.executive_summary.risk_score)">
                {{ generatedReport.executive_summary.risk_score.toFixed(1) }}
              </div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="summary-item">
              <div class="summary-label">风险等级</div>
              <div class="summary-value">
                <el-tag :type="getRiskLevelTagType(generatedReport.executive_summary.risk_level)">
                  {{ generatedReport.executive_summary.risk_level }}
                </el-tag>
              </div>
            </div>
          </el-col>
        </el-row>

        <div class="key-findings">
          <h4>关键发现：</h4>
          <ul>
            <li v-for="(finding, index) in generatedReport.executive_summary.key_findings" :key="index">
              {{ finding }}
            </li>
          </ul>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import {
  Document, View, Close, Check, Loading, Clock, Download, ArrowDown
} from '@element-plus/icons-vue'
import { riskReportsApi, type RiskReport, type ReportTemplate } from '@/api/riskReports'
import { useUserStore } from '@/stores/user'

// 响应式数据
const formRef = ref<FormInstance>()
const generating = ref(false)
const showPreview = ref(false)
const showCustomConfig = ref(false)
const progress = ref(0)
const currentStep = ref(0)

const templates = ref<ReportTemplate[]>([])
const generatedReport = ref<RiskReport | null>(null)
const dateRange = ref<[string, string] | null>(null)
const customConfigJson = ref('')

const userStore = useUserStore()

// 表单数据
const form = ref({
  report_type: 'daily',
  sections: ['executive_summary', 'risk_metrics', 'recommendations']
})

// 生成步骤
const generationSteps = [
  '收集基础数据',
  '分析风险指标',
  '分析风险事件',
  '执行风险归因',
  '生成改进建议',
  '生成图表数据',
  '完成报告'
]

// 表单验证规则
const rules: FormRules = {
  report_type: [
    { required: true, message: '请选择报告类型', trigger: 'change' }
  ],
  dateRange: [
    { required: true, message: '请选择时间范围', trigger: 'change' }
  ]
}

// 计算属性
const canPreview = computed(() => {
  return form.value.report_type && dateRange.value && form.value.sections.length > 0
})

// 方法
const loadTemplates = async () => {
  try {
    const response = await riskReportsApi.getReportTemplates()
    templates.value = response.templates
  } catch (error: any) {
    ElMessage.error(error.message || '加载报告模板失败')
  }
}

const generateReport = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()

    if (!dateRange.value) {
      ElMessage.error('请选择时间范围')
      return
    }

    generating.value = true
    progress.value = 0
    currentStep.value = 0
    generatedReport.value = null

    // 模拟生成进度
    const progressInterval = setInterval(() => {
      if (progress.value < 90) {
        progress.value += Math.random() * 15
        currentStep.value = Math.floor((progress.value / 100) * generationSteps.length)
      }
    }, 500)

    // 准备请求数据
    let customConfig = undefined
    if (showCustomConfig.value && customConfigJson.value.trim()) {
      try {
        customConfig = JSON.parse(customConfigJson.value)
      } catch (e) {
        ElMessage.error('自定义配置格式错误，请输入有效的JSON')
        generating.value = false
        clearInterval(progressInterval)
        return
      }
    }

    const requestData = {
      user_id: userStore.user?.id || 1,
      report_type: form.value.report_type as any,
      start_date: dateRange.value[0],
      end_date: dateRange.value[1],
      custom_config: customConfig
    }

    // 生成报告
    const report = await riskReportsApi.generateReport(requestData)

    // 完成进度
    clearInterval(progressInterval)
    progress.value = 100
    currentStep.value = generationSteps.length

    generatedReport.value = report
    ElMessage.success('报告生成成功')

  } catch (error: any) {
    ElMessage.error(error.message || '生成报告失败')
  } finally {
    generating.value = false
  }
}

const resetForm = () => {
  form.value = {
    report_type: 'daily',
    sections: ['executive_summary', 'risk_metrics', 'recommendations']
  }
  dateRange.value = null
  customConfigJson.value = ''
  showCustomConfig.value = false
  showPreview.value = false
  generatedReport.value = null
  formRef.value?.resetFields()
}

const previewReport = () => {
  showPreview.value = true
}

const viewReport = () => {
  if (generatedReport.value) {
    // 这里可以跳转到报告详情页面
    ElMessage.info('跳转到报告详情页面')
  }
}

const handleExport = (format: string) => {
  if (generatedReport.value) {
    const exportUrl = riskReportsApi.exportReport(generatedReport.value.report_id, format as any)
    window.open(exportUrl, '_blank')
  }
}

const getReportTypeName = (type: string): string => {
  const template = templates.value.find(t => t.report_type === type)
  return template?.name || type
}

const getSectionName = (section: string): string => {
  const names: Record<string, string> = {
    executive_summary: '执行摘要',
    risk_metrics: '风险指标',
    risk_events: '风险事件',
    position_analysis: '持仓分析',
    risk_attribution: '风险归因',
    trend_analysis: '趋势分析',
    recommendations: '改进建议'
  }
  return names[section] || section
}

const formatJson = (jsonStr: string): string => {
  try {
    return JSON.stringify(JSON.parse(jsonStr), null, 2)
  } catch (e) {
    return jsonStr
  }
}

const getRiskScoreClass = (score: number): string => {
  if (score >= 80) return 'risk-critical'
  if (score >= 60) return 'risk-high'
  if (score >= 40) return 'risk-medium'
  return 'risk-low'
}

const getRiskLevelTagType = (level: string): string => {
  const types: Record<string, string> = {
    '极低': 'success',
    '低': 'success',
    '中': 'warning',
    '高': 'danger',
    '极高': 'danger'
  }
  return types[level] || 'info'
}

// 生命周期
onMounted(() => {
  loadTemplates()
  
  // 设置默认时间范围（最近30天）
  const now = new Date()
  const thirtyDaysAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
  dateRange.value = [
    thirtyDaysAgo.toISOString().slice(0, 19).replace('T', ' '),
    now.toISOString().slice(0, 19).replace('T', ' ')
  ]
})
</script>

<style scoped>
.risk-report-generator {
  padding: 20px;
}

.header {
  margin-bottom: 30px;
}

.header h3 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 24px;
}

.header p {
  margin: 0;
  color: #606266;
  font-size: 14px;
}

.report-form {
  padding: 20px 0;
}

.template-option {
  padding: 4px 0;
}

.template-name {
  font-weight: bold;
  color: #303133;
}

.template-desc {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
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

.preview-content {
  padding: 10px 0;
}

.custom-config-preview {
  margin-top: 20px;
}

.custom-config-preview h4 {
  margin: 0 0 10px 0;
  color: #303133;
}

.config-json {
  padding: 12px;
  background: #f5f7fa;
  border-radius: 4px;
  border-left: 4px solid #409eff;
  font-size: 12px;
  line-height: 1.4;
  overflow-x: auto;
}

.generation-progress {
  padding: 20px 0;
}

.progress-header {
  margin-bottom: 20px;
}

.progress-header h4 {
  margin: 0 0 12px 0;
  color: #303133;
}

.progress-steps {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.step-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  border-radius: 4px;
  transition: all 0.3s;
}

.step-item.active {
  background: #e1f3d8;
  color: #67c23a;
}

.step-item.completed {
  background: #f0f9ff;
  color: #409eff;
}

.report-summary {
  padding: 10px 0;
}

.summary-item {
  text-align: center;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
}

.summary-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.summary-value {
  font-size: 20px;
  font-weight: bold;
  color: #303133;
}

.summary-value.risk-low {
  color: #67c23a;
}

.summary-value.risk-medium {
  color: #e6a23c;
}

.summary-value.risk-high {
  color: #f56c6c;
}

.summary-value.risk-critical {
  color: #f56c6c;
  animation: pulse 2s infinite;
}

.key-findings {
  margin-top: 20px;
}

.key-findings h4 {
  margin: 0 0 12px 0;
  color: #303133;
}

.key-findings ul {
  margin: 0;
  padding-left: 20px;
}

.key-findings li {
  margin-bottom: 8px;
  color: #606266;
  line-height: 1.6;
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.7; }
  100% { opacity: 1; }
}

:deep(.el-checkbox-group) {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}
</style>