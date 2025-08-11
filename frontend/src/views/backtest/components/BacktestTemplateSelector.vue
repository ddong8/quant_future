<template>
  <div class="template-selector">
    <div class="selector-header">
      <div class="search-bar">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索模板..."
          prefix-icon="el-icon-search"
          clearable
          @input="handleSearch"
        />
      </div>
      <div class="filter-bar">
        <el-select
          v-model="selectedCategory"
          placeholder="选择分类"
          clearable
          @change="handleCategoryChange"
        >
          <el-option
            v-for="category in categories"
            :key="category.key"
            :label="category.name"
            :value="category.key"
          />
        </el-select>
        <el-radio-group v-model="templateType" @change="handleTypeChange">
          <el-radio-button label="all">全部</el-radio-button>
          <el-radio-button label="official">官方</el-radio-button>
          <el-radio-button label="user">我的</el-radio-button>
        </el-radio-group>
      </div>
    </div>

    <div class="template-content">
      <div class="template-grid" v-loading="loading">
        <div
          v-for="template in filteredTemplates"
          :key="template.id"
          class="template-card"
          :class="{ 'selected': selectedTemplate?.id === template.id }"
          @click="selectTemplate(template)"
        >
          <div class="card-header">
            <div class="template-info">
              <h4 class="template-name">{{ template.name }}</h4>
              <div class="template-meta">
                <el-tag
                  :type="template.is_official ? 'success' : 'info'"
                  size="small"
                >
                  {{ template.is_official ? '官方' : '用户' }}
                </el-tag>
                <el-tag
                  v-if="template.category"
                  type="primary"
                  size="small"
                  effect="plain"
                >
                  {{ getCategoryName(template.category) }}
                </el-tag>
              </div>
            </div>
            <div class="template-stats">
              <div class="stat-item">
                <el-icon><View /></el-icon>
                <span>{{ template.usage_count || 0 }}</span>
              </div>
              <div class="stat-item" v-if="template.rating">
                <el-icon><Star /></el-icon>
                <span>{{ template.rating.toFixed(1) }}</span>
              </div>
            </div>
          </div>

          <div class="card-body">
            <p class="template-description">
              {{ template.description || '暂无描述' }}
            </p>
            
            <div class="template-tags" v-if="template.tags && template.tags.length > 0">
              <el-tag
                v-for="tag in template.tags.slice(0, 3)"
                :key="tag"
                size="small"
                effect="plain"
              >
                {{ tag }}
              </el-tag>
              <span v-if="template.tags.length > 3" class="more-tags">
                +{{ template.tags.length - 3 }}
              </span>
            </div>

            <div class="template-preview">
              <div class="preview-item">
                <span class="preview-label">初始资金:</span>
                <span class="preview-value">
                  {{ formatCurrency(template.config_template?.basic_settings?.initial_capital) }}
                </span>
              </div>
              <div class="preview-item">
                <span class="preview-label">数据频率:</span>
                <span class="preview-value">
                  {{ getFrequencyLabel(template.config_template?.basic_settings?.frequency) }}
                </span>
              </div>
              <div class="preview-item">
                <span class="preview-label">手续费率:</span>
                <span class="preview-value">
                  {{ formatPercent(template.config_template?.trading_settings?.commission_rate) }}
                </span>
              </div>
            </div>
          </div>

          <div class="card-footer">
            <div class="template-time">
              <el-icon><Clock /></el-icon>
              <span>{{ formatTime(template.created_at) }}</span>
            </div>
            <div class="template-actions">
              <el-button
                size="small"
                type="text"
                @click.stop="previewTemplate(template)"
              >
                预览
              </el-button>
              <el-button
                v-if="!template.is_official && template.author_id === currentUserId"
                size="small"
                type="text"
                @click.stop="editTemplate(template)"
              >
                编辑
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <div class="empty-state" v-if="!loading && filteredTemplates.length === 0">
        <el-empty description="暂无模板">
          <el-button type="primary" @click="createTemplate">创建模板</el-button>
        </el-empty>
      </div>
    </div>

    <div class="selector-footer">
      <div class="selected-info" v-if="selectedTemplate">
        <div class="selected-template">
          <h4>已选择: {{ selectedTemplate.name }}</h4>
          <p>{{ selectedTemplate.description }}</p>
        </div>
      </div>
      <div class="footer-actions">
        <el-button @click="$emit('close')">取消</el-button>
        <el-button
          type="primary"
          :disabled="!selectedTemplate"
          @click="confirmSelect"
        >
          使用此模板
        </el-button>
      </div>
    </div>

    <!-- 模板预览对话框 -->
    <el-dialog
      v-model="showPreviewDialog"
      title="模板预览"
      width="70%"
      :before-close="handlePreviewClose"
    >
      <BacktestTemplatePreview
        v-if="previewTemplate"
        :template="previewingTemplate"
        @close="showPreviewDialog = false"
      />
    </el-dialog>

    <!-- 模板编辑对话框 -->
    <el-dialog
      v-model="showEditDialog"
      title="编辑模板"
      width="80%"
      :before-close="handleEditClose"
    >
      <BacktestTemplateEditor
        v-if="editingTemplate"
        :template="editingTemplate"
        @save="handleTemplateSave"
        @close="showEditDialog = false"
      />
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { View, Star, Clock } from '@element-plus/icons-vue'
import BacktestTemplatePreview from './BacktestTemplatePreview.vue'
import BacktestTemplateEditor from './BacktestTemplateEditor.vue'
import { backtestApi } from '@/api/backtest'
import { useUserStore } from '@/stores/user'

export default {
  name: 'BacktestTemplateSelector',
  components: {
    BacktestTemplatePreview,
    BacktestTemplateEditor,
    View,
    Star,
    Clock
  },
  emits: ['select', 'close'],
  setup(props, { emit }) {
    const userStore = useUserStore()
    const loading = ref(false)
    const searchKeyword = ref('')
    const selectedCategory = ref('')
    const templateType = ref('all')
    const selectedTemplate = ref(null)
    const showPreviewDialog = ref(false)
    const showEditDialog = ref(false)
    const previewingTemplate = ref(null)
    const editingTemplate = ref(null)

    const templates = ref([])
    const categories = ref([])

    const currentUserId = computed(() => userStore.user?.id)

    // 过滤后的模板列表
    const filteredTemplates = computed(() => {
      let result = templates.value

      // 按类型筛选
      if (templateType.value === 'official') {
        result = result.filter(t => t.is_official)
      } else if (templateType.value === 'user') {
        result = result.filter(t => !t.is_official && t.author_id === currentUserId.value)
      }

      // 按分类筛选
      if (selectedCategory.value) {
        result = result.filter(t => t.category === selectedCategory.value)
      }

      // 按关键词搜索
      if (searchKeyword.value) {
        const keyword = searchKeyword.value.toLowerCase()
        result = result.filter(t => 
          t.name.toLowerCase().includes(keyword) ||
          (t.description && t.description.toLowerCase().includes(keyword)) ||
          (t.tags && t.tags.some(tag => tag.toLowerCase().includes(keyword)))
        )
      }

      return result
    })

    // 加载模板列表
    const loadTemplates = async () => {
      loading.value = true
      try {
        const response = await backtestApi.getConfigTemplates({
          page: 1,
          page_size: 100
        })
        templates.value = response.data.items || []
      } catch (error) {
        console.error('加载模板失败:', error)
        ElMessage.error('加载模板失败')
      } finally {
        loading.value = false
      }
    }

    // 加载分类列表
    const loadCategories = async () => {
      try {
        const response = await backtestApi.getConfigCategories()
        categories.value = response.data || []
      } catch (error) {
        console.error('加载分类失败:', error)
      }
    }

    // 处理搜索
    const handleSearch = () => {
      // 搜索逻辑在 computed 中处理
    }

    // 处理分类变化
    const handleCategoryChange = () => {
      // 筛选逻辑在 computed 中处理
    }

    // 处理类型变化
    const handleTypeChange = () => {
      // 筛选逻辑在 computed 中处理
    }

    // 选择模板
    const selectTemplate = (template) => {
      selectedTemplate.value = template
    }

    // 确认选择
    const confirmSelect = () => {
      if (selectedTemplate.value) {
        emit('select', selectedTemplate.value)
      }
    }

    // 预览模板
    const previewTemplate = (template) => {
      previewingTemplate.value = template
      showPreviewDialog.value = true
    }

    // 编辑模板
    const editTemplate = (template) => {
      editingTemplate.value = template
      showEditDialog.value = true
    }

    // 创建模板
    const createTemplate = () => {
      // 触发创建模板的逻辑
      emit('close')
      // 这里可以导航到创建模板页面
    }

    // 处理模板保存
    const handleTemplateSave = (updatedTemplate) => {
      const index = templates.value.findIndex(t => t.id === updatedTemplate.id)
      if (index > -1) {
        templates.value[index] = updatedTemplate
      }
      showEditDialog.value = false
      ElMessage.success('模板更新成功')
    }

    // 处理预览对话框关闭
    const handlePreviewClose = () => {
      showPreviewDialog.value = false
      previewingTemplate.value = null
    }

    // 处理编辑对话框关闭
    const handleEditClose = () => {
      showEditDialog.value = false
      editingTemplate.value = null
    }

    // 获取分类名称
    const getCategoryName = (categoryKey) => {
      const category = categories.value.find(c => c.key === categoryKey)
      return category ? category.name : categoryKey
    }

    // 格式化货币
    const formatCurrency = (amount) => {
      if (!amount) return '-'
      return new Intl.NumberFormat('zh-CN', {
        style: 'currency',
        currency: 'CNY',
        minimumFractionDigits: 0
      }).format(amount)
    }

    // 格式化百分比
    const formatPercent = (value) => {
      if (value === null || value === undefined) return '-'
      return (value * 100).toFixed(2) + '%'
    }

    // 获取频率标签
    const getFrequencyLabel = (frequency) => {
      const frequencyMap = {
        '1m': '1分钟',
        '5m': '5分钟',
        '15m': '15分钟',
        '30m': '30分钟',
        '1h': '1小时',
        '4h': '4小时',
        '1d': '1天',
        '1w': '1周',
        '1M': '1月'
      }
      return frequencyMap[frequency] || frequency || '-'
    }

    // 格式化时间
    const formatTime = (timeStr) => {
      if (!timeStr) return '-'
      const date = new Date(timeStr)
      return date.toLocaleDateString('zh-CN')
    }

    onMounted(() => {
      loadTemplates()
      loadCategories()
    })

    return {
      loading,
      searchKeyword,
      selectedCategory,
      templateType,
      selectedTemplate,
      showPreviewDialog,
      showEditDialog,
      previewingTemplate,
      editingTemplate,
      templates,
      categories,
      currentUserId,
      filteredTemplates,
      handleSearch,
      handleCategoryChange,
      handleTypeChange,
      selectTemplate,
      confirmSelect,
      previewTemplate,
      editTemplate,
      createTemplate,
      handleTemplateSave,
      handlePreviewClose,
      handleEditClose,
      getCategoryName,
      formatCurrency,
      formatPercent,
      getFrequencyLabel,
      formatTime
    }
  }
}
</script>

<style scoped>
.template-selector {
  height: 600px;
  display: flex;
  flex-direction: column;
}

.selector-header {
  margin-bottom: 20px;
}

.search-bar {
  margin-bottom: 15px;
}

.filter-bar {
  display: flex;
  gap: 15px;
  align-items: center;
}

.template-content {
  flex: 1;
  overflow: hidden;
}

.template-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
  height: 100%;
  overflow-y: auto;
  padding-right: 10px;
}

.template-card {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.3s;
  background: var(--el-bg-color);
  height: fit-content;
}

.template-card:hover {
  border-color: #409eff;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.template-card.selected {
  border-color: #409eff;
  background-color: var(--el-color-primary-light-9);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.template-info {
  flex: 1;
}

.template-name {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  line-height: 1.4;
}

.template-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.template-stats {
  display: flex;
  flex-direction: column;
  gap: 4px;
  align-items: flex-end;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #909399;
}

.card-body {
  margin-bottom: 12px;
}

.template-description {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #606266;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.template-tags {
  display: flex;
  gap: 6px;
  align-items: center;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.more-tags {
  font-size: 12px;
  color: #909399;
}

.template-preview {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.preview-item {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
}

.preview-label {
  color: #909399;
}

.preview-value {
  color: #303133;
  font-weight: 500;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.template-time {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #909399;
}

.template-actions {
  display: flex;
  gap: 8px;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
}

.selector-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e4e7ed;
}

.selected-info {
  flex: 1;
  margin-right: 20px;
}

.selected-template h4 {
  margin: 0 0 4px 0;
  font-size: 14px;
  color: #303133;
}

.selected-template p {
  margin: 0;
  font-size: 12px;
  color: #909399;
  line-height: 1.4;
}

.footer-actions {
  display: flex;
  gap: 10px;
}

/* 滚动条样式 */
.template-grid::-webkit-scrollbar {
  width: 6px;
}

.template-grid::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.template-grid::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.template-grid::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>