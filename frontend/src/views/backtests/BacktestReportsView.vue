<template>
  <div class="reports-view">
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">📄 回测报告</h1>
        <p class="page-description">生成和管理回测分析报告</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" @click="showGenerateDialog = true">
          <el-icon><DocumentAdd /></el-icon>
          生成报告
        </el-button>
        <el-button @click="refreshReports" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 报告筛选 -->
    <el-card class="filter-card">
      <el-form :model="filterForm" :inline="true">
        <el-form-item label="报告类型">
          <el-select v-model="filterForm.reportType" placeholder="全部类型" clearable>
            <el-option label="单策略报告" value="single" />
            <el-option label="对比报告" value="comparison" />
            <el-option label="汇总报告" value="summary" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="filterForm.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        
        <el-form-item label="状态">
          <el-select v-model="filterForm.status" placeholder="全部状态" clearable>
            <el-option label="生成中" value="generating" />
            <el-option label="已完成" value="completed" />
            <el-option label="失败" value="failed" />
          </el-select>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="applyFilter">筛选</el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 报告列表 -->
    <el-card class="reports-list">
      <template #header>
        <div class="card-header">
          <span>报告列表</span>
          <el-tag size="small" type="info">{{ filteredReports.length }} 个报告</el-tag>
        </div>
      </template>

      <div v-if="filteredReports.length === 0" class="empty-state">
        <el-empty description="暂无报告">
          <el-button type="primary" @click="showGenerateDialog = true">生成第一个报告</el-button>
        </el-empty>
      </div>

      <div v-else class="reports-grid">
        <div v-for="report in filteredReports" :key="report.id" class="report-card">
          <div class="report-header">
            <div class="report-info">
              <h3 class="report-title">{{ report.title }}</h3>
              <div class="report-meta">
                <el-tag :type="getStatusType(report.status)" size="small">
                  {{ getStatusText(report.status) }}
                </el-tag>
                <span class="report-type">{{ getReportTypeText(report.type) }}</span>
                <span class="report-time">{{ formatTime(report.created_at) }}</span>
              </div>
            </div>
            <div class="report-actions">
              <el-dropdown @command="handleReportAction">
                <el-button size="small" type="primary" :disabled="report.status !== 'completed'">
                  操作 <el-icon><ArrowDown /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item :command="`view_${report.id}`">
                      <el-icon><View /></el-icon>
                      查看报告
                    </el-dropdown-item>
                    <el-dropdown-item :command="`download_${report.id}`">
                      <el-icon><Download /></el-icon>
                      下载PDF
                    </el-dropdown-item>
                    <el-dropdown-item :command="`share_${report.id}`">
                      <el-icon><Share /></el-icon>
                      分享报告
                    </el-dropdown-item>
                    <el-dropdown-item :command="`delete_${report.id}`" divided>
                      <el-icon><Delete /></el-icon>
                      删除报告
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>

          <div class="report-content">
            <div class="report-description">
              {{ report.description }}
            </div>
            
            <div v-if="report.status === 'completed'" class="report-summary">
              <div class="summary-item">
                <span class="summary-label">包含回测:</span>
                <span class="summary-value">{{ report.backtest_count }}个</span>
              </div>
              <div class="summary-item">
                <span class="summary-label">报告页数:</span>
                <span class="summary-value">{{ report.page_count }}页</span>
              </div>
              <div class="summary-item">
                <span class="summary-label">文件大小:</span>
                <span class="summary-value">{{ formatFileSize(report.file_size) }}</span>
              </div>
            </div>
            
            <div v-else-if="report.status === 'generating'" class="report-progress">
              <el-progress :percentage="report.progress || 0" :stroke-width="6" />
              <span class="progress-text">正在生成报告...</span>
            </div>
            
            <div v-else-if="report.status === 'failed'" class="report-error">
              <el-alert
                title="报告生成失败"
                :description="report.error_message || '未知错误'"
                type="error"
                :closable="false"
              />
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 生成报告对话框 -->
    <el-dialog v-model="showGenerateDialog" title="生成回测报告" width="600px">
      <el-form :model="generateForm" label-width="100px">
        <el-form-item label="报告标题">
          <el-input v-model="generateForm.title" placeholder="输入报告标题" />
        </el-form-item>
        
        <el-form-item label="报告类型">
          <el-radio-group v-model="generateForm.type">
            <el-radio label="single">单策略报告</el-radio>
            <el-radio label="comparison">对比报告</el-radio>
            <el-radio label="summary">汇总报告</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="选择回测">
          <el-select 
            v-model="generateForm.backtest_ids" 
            :multiple="generateForm.type !== 'single'"
            placeholder="选择回测"
            style="width: 100%"
          >
            <el-option 
              v-for="backtest in availableBacktests" 
              :key="backtest.backtest_id" 
              :label="backtest.name || backtest.strategy_name" 
              :value="backtest.backtest_id" 
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="报告内容">
          <el-checkbox-group v-model="generateForm.sections">
            <el-checkbox label="executive_summary">执行摘要</el-checkbox>
            <el-checkbox label="performance_analysis">绩效分析</el-checkbox>
            <el-checkbox label="risk_analysis">风险分析</el-checkbox>
            <el-checkbox label="trade_analysis">交易分析</el-checkbox>
            <el-checkbox label="charts">图表分析</el-checkbox>
            <el-checkbox label="recommendations">建议总结</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        
        <el-form-item label="报告描述">
          <el-input 
            v-model="generateForm.description" 
            type="textarea" 
            :rows="3"
            placeholder="输入报告描述"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showGenerateDialog = false">取消</el-button>
        <el-button type="primary" @click="generateReport" :loading="generating">
          生成报告
        </el-button>
      </template>
    </el-dialog>

    <!-- 报告预览对话框 -->
    <el-dialog v-model="showPreviewDialog" :title="`预览报告: ${selectedReport?.title}`" width="80%">
      <div v-if="selectedReport" class="report-preview">
        <div class="preview-header">
          <h2>{{ selectedReport.title }}</h2>
          <div class="preview-meta">
            <span>生成时间: {{ formatTime(selectedReport.created_at) }}</span>
            <span>报告类型: {{ getReportTypeText(selectedReport.type) }}</span>
          </div>
        </div>
        
        <div class="preview-content">
          <div class="preview-section">
            <h3>📋 执行摘要</h3>
            <p>本报告分析了{{ selectedReport.backtest_count }}个回测结果，涵盖了绩效分析、风险评估和交易统计等关键指标。</p>
          </div>
          
          <div class="preview-section">
            <h3>📊 关键指标</h3>
            <div class="key-metrics">
              <div class="metric-item">
                <span class="metric-label">平均收益率</span>
                <span class="metric-value positive">+12.5%</span>
              </div>
              <div class="metric-item">
                <span class="metric-label">平均夏普比率</span>
                <span class="metric-value">1.34</span>
              </div>
              <div class="metric-item">
                <span class="metric-label">平均最大回撤</span>
                <span class="metric-value negative">-8.2%</span>
              </div>
            </div>
          </div>
          
          <div class="preview-section">
            <h3>💡 主要发现</h3>
            <ul>
              <li>策略在趋势市场中表现较好，平均收益率达到15.8%</li>
              <li>风险控制有效，最大回撤控制在10%以内</li>
              <li>交易频率适中，避免了过度交易的风险</li>
            </ul>
          </div>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="showPreviewDialog = false">关闭</el-button>
        <el-button type="primary" @click="downloadReport(selectedReport)">
          下载完整报告
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  DocumentAdd, Refresh, ArrowDown, View, Download, Share, Delete 
} from '@element-plus/icons-vue'
import { getBacktestList } from '@/api/realTimeData'

const loading = ref(false)
const generating = ref(false)
const showGenerateDialog = ref(false)
const showPreviewDialog = ref(false)
const selectedReport = ref(null)

// 筛选表单
const filterForm = reactive({
  reportType: '',
  dateRange: [],
  status: ''
})

// 生成报告表单
const generateForm = reactive({
  title: '',
  type: 'single',
  backtest_ids: [],
  sections: ['executive_summary', 'performance_analysis', 'risk_analysis'],
  description: ''
})

// 可用回测列表
const availableBacktests = ref([])

// 报告列表
const reports = ref([
  {
    id: 'RPT_001',
    title: '双均线策略分析报告',
    type: 'single',
    status: 'completed',
    description: '基于双均线策略的详细回测分析报告',
    created_at: new Date().toISOString(),
    backtest_count: 1,
    page_count: 15,
    file_size: 2048576,
    progress: 100
  },
  {
    id: 'RPT_002',
    title: '多策略对比分析报告',
    type: 'comparison',
    status: 'completed',
    description: '对比分析双均线、RSI和布林带三种策略的表现',
    created_at: new Date(Date.now() - 86400000).toISOString(),
    backtest_count: 3,
    page_count: 28,
    file_size: 4194304,
    progress: 100
  },
  {
    id: 'RPT_003',
    title: '月度策略汇总报告',
    type: 'summary',
    status: 'generating',
    description: '本月所有策略的综合表现分析',
    created_at: new Date(Date.now() - 3600000).toISOString(),
    backtest_count: 8,
    page_count: 0,
    file_size: 0,
    progress: 65
  }
])

// 过滤后的报告
const filteredReports = computed(() => {
  let filtered = reports.value
  
  if (filterForm.reportType) {
    filtered = filtered.filter(report => report.type === filterForm.reportType)
  }
  
  if (filterForm.status) {
    filtered = filtered.filter(report => report.status === filterForm.status)
  }
  
  if (filterForm.dateRange && filterForm.dateRange.length === 2) {
    const startDate = new Date(filterForm.dateRange[0])
    const endDate = new Date(filterForm.dateRange[1])
    filtered = filtered.filter(report => {
      const reportDate = new Date(report.created_at)
      return reportDate >= startDate && reportDate <= endDate
    })
  }
  
  return filtered
})

// 加载可用回测
const loadAvailableBacktests = async () => {
  try {
    const response = await getBacktestList()
    if (response.success && response.data) {
      availableBacktests.value = response.data.filter(bt => bt.status === 'completed')
    }
    
    // 如果没有真实数据，使用模拟数据
    if (availableBacktests.value.length === 0) {
      availableBacktests.value = [
        {
          backtest_id: 'BT_001',
          name: '双均线策略回测',
          strategy_name: '双均线策略回测',
          status: 'completed'
        },
        {
          backtest_id: 'BT_002',
          name: 'RSI反转策略回测',
          strategy_name: 'RSI反转策略回测',
          status: 'completed'
        }
      ]
    }
  } catch (error) {
    console.error('加载回测列表失败:', error)
  }
}

// 刷新报告
const refreshReports = async () => {
  loading.value = true
  try {
    // 这里可以调用真实的API获取报告列表
    await new Promise(resolve => setTimeout(resolve, 1000))
    ElMessage.success('报告列表已刷新')
  } catch (error) {
    ElMessage.error('刷新失败')
  } finally {
    loading.value = false
  }
}

// 应用筛选
const applyFilter = () => {
  ElMessage.info('筛选已应用')
}

// 重置筛选
const resetFilter = () => {
  Object.assign(filterForm, {
    reportType: '',
    dateRange: [],
    status: ''
  })
}

// 生成报告
const generateReport = async () => {
  if (!generateForm.title) {
    ElMessage.warning('请输入报告标题')
    return
  }
  
  if (!generateForm.backtest_ids.length) {
    ElMessage.warning('请选择回测')
    return
  }
  
  generating.value = true
  try {
    // 这里可以调用真实的API生成报告
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    // 添加新报告到列表
    const newReport = {
      id: `RPT_${Date.now()}`,
      title: generateForm.title,
      type: generateForm.type,
      status: 'generating',
      description: generateForm.description,
      created_at: new Date().toISOString(),
      backtest_count: generateForm.backtest_ids.length,
      page_count: 0,
      file_size: 0,
      progress: 0
    }
    
    reports.value.unshift(newReport)
    
    // 模拟生成进度
    const progressInterval = setInterval(() => {
      newReport.progress += Math.random() * 20
      if (newReport.progress >= 100) {
        newReport.progress = 100
        newReport.status = 'completed'
        newReport.page_count = Math.floor(Math.random() * 20 + 10)
        newReport.file_size = Math.floor(Math.random() * 5000000 + 1000000)
        clearInterval(progressInterval)
      }
    }, 1000)
    
    showGenerateDialog.value = false
    ElMessage.success('报告生成任务已提交')
    
    // 重置表单
    Object.assign(generateForm, {
      title: '',
      type: 'single',
      backtest_ids: [],
      sections: ['executive_summary', 'performance_analysis', 'risk_analysis'],
      description: ''
    })
  } catch (error) {
    ElMessage.error('生成报告失败')
  } finally {
    generating.value = false
  }
}

// 处理报告操作
const handleReportAction = (command: string) => {
  const [action, reportId] = command.split('_')
  const report = reports.value.find(r => r.id === reportId)
  
  switch (action) {
    case 'view':
      viewReport(report)
      break
    case 'download':
      downloadReport(report)
      break
    case 'share':
      shareReport(report)
      break
    case 'delete':
      deleteReport(report)
      break
  }
}

// 查看报告
const viewReport = (report: any) => {
  selectedReport.value = report
  showPreviewDialog.value = true
}

// 下载报告
const downloadReport = (report: any) => {
  ElMessage.info(`正在下载报告: ${report.title}`)
  // 这里可以实现真实的下载逻辑
}

// 分享报告
const shareReport = (report: any) => {
  ElMessage.info(`分享报告: ${report.title}`)
  // 这里可以实现分享功能
}

// 删除报告
const deleteReport = async (report: any) => {
  try {
    await ElMessageBox.confirm(`确定要删除报告 "${report.title}" 吗？`, '确认删除', {
      type: 'warning'
    })
    
    const index = reports.value.findIndex(r => r.id === report.id)
    if (index > -1) {
      reports.value.splice(index, 1)
      ElMessage.success('报告已删除')
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除报告失败')
    }
  }
}

// 工具函数
const getStatusType = (status: string) => {
  switch (status) {
    case 'completed': return 'success'
    case 'generating': return 'warning'
    case 'failed': return 'danger'
    default: return 'info'
  }
}

const getStatusText = (status: string) => {
  switch (status) {
    case 'completed': return '已完成'
    case 'generating': return '生成中'
    case 'failed': return '失败'
    default: return '未知'
  }
}

const getReportTypeText = (type: string) => {
  switch (type) {
    case 'single': return '单策略报告'
    case 'comparison': return '对比报告'
    case 'summary': return '汇总报告'
    default: return '未知类型'
  }
}

const formatTime = (timestamp: string) => {
  return new Date(timestamp).toLocaleString()
}

const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 页面初始化
onMounted(() => {
  console.log('📄 回测报告页面已加载')
  loadAvailableBacktests()
})
</script>
<style scoped>
.reports-view {
  padding: 24px;
  background: var(--el-bg-color-page);
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  padding: 20px;
  background: var(--el-bg-color);
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.header-left h1 {
  margin: 0 0 8px 0;
  font-size: 28px;
  font-weight: 700;
  color: var(--el-text-color-primary);
}

.header-left p {
  margin: 0;
  font-size: 16px;
  color: var(--el-text-color-regular);
}

.header-actions {
  display: flex;
  gap: 12px;
}

.filter-card, .reports-list {
  margin-bottom: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

.reports-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 20px;
}

.report-card {
  background: var(--el-bg-color-page);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid var(--el-border-color-light);
  transition: all 0.3s ease;
}

.report-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.report-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.report-info {
  flex: 1;
}

.report-title {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.report-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.report-type, .report-time {
  font-size: 12px;
  color: var(--el-text-color-regular);
}

.report-content {
  margin-top: 16px;
}

.report-description {
  font-size: 14px;
  color: var(--el-text-color-regular);
  line-height: 1.5;
  margin-bottom: 16px;
}

.report-summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: var(--el-bg-color);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-lighter);
}

.summary-item {
  text-align: center;
}

.summary-label {
  display: block;
  font-size: 12px;
  color: var(--el-text-color-regular);
  margin-bottom: 4px;
}

.summary-value {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.report-progress {
  padding: 12px;
  background: var(--el-bg-color);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-lighter);
}

.progress-text {
  display: block;
  text-align: center;
  font-size: 12px;
  color: var(--el-text-color-regular);
  margin-top: 8px;
}

.report-error {
  margin-top: 12px;
}

.report-preview {
  max-height: 70vh;
  overflow-y: auto;
}

.preview-header {
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--el-border-color-light);
}

.preview-header h2 {
  margin: 0 0 8px 0;
  font-size: 20px;
  color: var(--el-text-color-primary);
}

.preview-meta {
  display: flex;
  gap: 24px;
  font-size: 14px;
  color: var(--el-text-color-regular);
}

.preview-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.preview-section {
  padding: 20px;
  background: var(--el-bg-color-page);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-light);
}

.preview-section h3 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.preview-section p {
  margin: 0;
  line-height: 1.6;
  color: var(--el-text-color-regular);
}

.preview-section ul {
  margin: 0;
  padding-left: 20px;
  color: var(--el-text-color-regular);
}

.preview-section li {
  margin-bottom: 8px;
  line-height: 1.5;
}

.key-metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
}

.metric-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: var(--el-bg-color);
  border-radius: 6px;
  border: 1px solid var(--el-border-color-lighter);
}

.metric-label {
  font-size: 12px;
  color: var(--el-text-color-regular);
}

.metric-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

.metric-value.positive {
  color: #27ae60;
}

.metric-value.negative {
  color: #e74c3c;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .reports-view {
    padding: 16px;
  }
  
  .page-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .header-actions {
    justify-content: center;
  }
  
  .reports-grid {
    grid-template-columns: 1fr;
  }
  
  .report-header {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .report-summary {
    flex-direction: column;
    gap: 12px;
  }
  
  .summary-item {
    text-align: left;
  }
  
  .key-metrics {
    grid-template-columns: 1fr;
  }
  
  .preview-meta {
    flex-direction: column;
    gap: 8px;
  }
}
</style>
