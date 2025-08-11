<template>
  <el-dialog
    v-model="visible"
    title="从模板创建策略"
    width="800px"
    :before-close="handleClose"
  >
    <!-- 模板筛选 -->
    <div class="template-filters">
      <el-row :gutter="16">
        <el-col :span="8">
          <el-select v-model="filters.category" placeholder="选择分类" clearable>
            <el-option
              v-for="category in categories"
              :key="category.id"
              :label="category.name"
              :value="category.id"
            />
          </el-select>
        </el-col>
        <el-col :span="8">
          <el-select v-model="filters.difficulty" placeholder="选择难度" clearable>
            <el-option label="初级" value="beginner" />
            <el-option label="中级" value="intermediate" />
            <el-option label="高级" value="advanced" />
          </el-select>
        </el-col>
        <el-col :span="8">
          <el-input
            v-model="filters.search"
            placeholder="搜索模板"
            clearable
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
      </el-row>
    </div>

    <!-- 模板列表 -->
    <div class="template-list" v-loading="loading">
      <el-row :gutter="16">
        <el-col
          v-for="template in templates"
          :key="template.id"
          :span="12"
        >
          <div
            class="template-card"
            :class="{ active: selectedTemplate?.id === template.id }"
            @click="selectTemplate(template)"
          >
            <div class="template-header">
              <h4 class="template-name">{{ template.name }}</h4>
              <el-tag :type="difficultyTagType(template.difficulty)" size="small">
                {{ difficultyText(template.difficulty) }}
              </el-tag>
            </div>
            
            <p class="template-description">{{ template.description }}</p>
            
            <div class="template-tags">
              <el-tag
                v-for="tag in template.tags.slice(0, 3)"
                :key="tag"
                size="small"
                effect="plain"
              >
                {{ tag }}
              </el-tag>
              <el-tag v-if="template.tags.length > 3" size="small" effect="plain">
                +{{ template.tags.length - 3 }}
              </el-tag>
            </div>
            
            <div class="template-footer">
              <span class="template-category">{{ template.category }}</span>
              <span class="template-date">{{ formatDate(template.created_at) }}</span>
            </div>
          </div>
        </el-col>
      </el-row>
      
      <el-empty v-if="!loading && templates.length === 0" description="暂无模板" />
    </div>

    <!-- 模板预览 -->
    <div class="template-preview" v-if="selectedTemplate">
      <el-divider content-position="left">代码预览</el-divider>
      <div class="code-preview">
        <pre><code>{{ selectedTemplate.preview_code }}</code></pre>
      </div>
    </div>

    <!-- 创建表单 -->
    <div class="create-form" v-if="selectedTemplate">
      <el-divider content-position="left">策略信息</el-divider>
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
      >
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="策略名称" prop="name">
              <el-input
                v-model="form.name"
                placeholder="请输入策略名称"
                maxlength="100"
                show-word-limit
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="策略描述">
              <el-input
                v-model="form.description"
                placeholder="请输入策略描述"
                maxlength="200"
                show-word-limit
              />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button
          type="primary"
          :disabled="!selectedTemplate"
          :loading="creating"
          @click="handleCreate"
        >
          创建策略
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { useStrategyStore } from '@/stores/strategy'
import type { StrategyTemplate } from '@/types/strategy'

interface Props {
  modelValue: boolean
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const strategyStore = useStrategyStore()
const formRef = ref<FormInstance>()
const loading = ref(false)
const creating = ref(false)
const selectedTemplate = ref<StrategyTemplate | null>(null)

// 筛选条件
const filters = ref({
  category: '',
  difficulty: '',
  search: ''
})

// 表单数据
const form = ref({
  name: '',
  description: ''
})

// 表单验证规则
const rules: FormRules = {
  name: [
    { required: true, message: '请输入策略名称', trigger: 'blur' },
    { min: 2, max: 100, message: '策略名称长度在 2 到 100 个字符', trigger: 'blur' }
  ]
}

// 计算属性
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const templates = computed(() => strategyStore.templates)
const categories = computed(() => strategyStore.categories)

// 方法
const handleSearch = () => {
  loadTemplates()
}

const loadTemplates = async () => {
  try {
    loading.value = true
    await strategyStore.fetchTemplates(filters.value)
  } finally {
    loading.value = false
  }
}

const selectTemplate = (template: StrategyTemplate) => {
  selectedTemplate.value = template
  form.value.name = `${template.name} - 副本`
  form.value.description = template.description
}

const difficultyTagType = (difficulty: string) => {
  const typeMap = {
    beginner: 'success',
    intermediate: 'warning',
    advanced: 'danger'
  }
  return typeMap[difficulty] || 'info'
}

const difficultyText = (difficulty: string) => {
  const textMap = {
    beginner: '初级',
    intermediate: '中级',
    advanced: '高级'
  }
  return textMap[difficulty] || '未知'
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('zh-CN')
}

const handleCreate = async () => {
  if (!formRef.value || !selectedTemplate.value) return
  
  try {
    await formRef.value.validate()
    creating.value = true
    
    await strategyStore.createFromTemplate(selectedTemplate.value.id, {
      name: form.value.name,
      description: form.value.description
    })
    
    ElMessage.success('从模板创建策略成功')
    emit('success')
    handleClose()
  } catch (error) {
    // 错误已在store中处理
  } finally {
    creating.value = false
  }
}

const handleClose = () => {
  visible.value = false
  resetForm()
}

const resetForm = () => {
  selectedTemplate.value = null
  form.value = {
    name: '',
    description: ''
  }
  
  filters.value = {
    category: '',
    difficulty: '',
    search: ''
  }
  
  if (formRef.value) {
    formRef.value.resetFields()
  }
}

// 监听筛选条件变化
watch(filters, () => {
  handleSearch()
}, { deep: true })

// 监听对话框显示状态
watch(visible, (newVal) => {
  if (newVal) {
    loadTemplates()
    if (categories.value.length === 0) {
      strategyStore.fetchCategories()
    }
  }
})
</script>

<style scoped lang="scss">
.template-filters {
  margin-bottom: 20px;
  padding: 16px;
  background: var(--el-bg-color-page);
  border-radius: 8px;
}

.template-list {
  max-height: 400px;
  overflow-y: auto;
  margin-bottom: 20px;
  
  .template-card {
    padding: 16px;
    border: 1px solid #ebeef5;
    border-radius: 8px;
    margin-bottom: 12px;
    cursor: pointer;
    transition: all 0.3s ease;
    
    &:hover {
      border-color: #409eff;
      box-shadow: 0 2px 8px rgba(64, 158, 255, 0.2);
    }
    
    &.active {
      border-color: #409eff;
      background: #ecf5ff;
    }
    
    .template-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
      
      .template-name {
        margin: 0;
        font-size: 16px;
        font-weight: 600;
        color: #303133;
      }
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
      margin-bottom: 12px;
      display: flex;
      flex-wrap: wrap;
      gap: 4px;
    }
    
    .template-footer {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 12px;
      color: #909399;
    }
  }
}

.template-preview {
  .code-preview {
    max-height: 200px;
    overflow-y: auto;
    background: var(--el-bg-color-page);
    border-radius: 4px;
    padding: 12px;
    
    pre {
      margin: 0;
      font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
      font-size: 12px;
      line-height: 1.5;
      color: #303133;
    }
  }
}

.create-form {
  margin-top: 20px;
}

.dialog-footer {
  text-align: right;
}

:deep(.el-divider__text) {
  font-weight: 600;
  color: #303133;
}
</style>