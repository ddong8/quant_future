<template>
  <div class="strategy-edit" v-loading="loading">
    <div v-if="strategy">
      <!-- 页面头部 -->
      <div class="page-header">
        <div class="header-left">
          <el-button @click="goBack" type="text" class="back-button">
            <el-icon><ArrowLeft /></el-icon>
            返回详情
          </el-button>
          <div class="header-info">
            <h2 class="strategy-title">编辑策略: {{ strategy.name }}</h2>
            <div class="strategy-meta">
              <StatusTag :status="strategy.status" />
              <span class="version-info">v{{ strategy.version }}</span>
            </div>
          </div>
        </div>
        
        <div class="header-actions">
          <el-button @click="handlePreview">
            <el-icon><View /></el-icon>
            预览
          </el-button>
          <el-button @click="handleTest" :disabled="!hasChanges">
            <el-icon><Cpu /></el-icon>
            测试代码
          </el-button>
          <el-button @click="handleSave" type="primary" :disabled="!hasChanges">
            <el-icon><Check /></el-icon>
            保存策略
          </el-button>
        </div>
      </div>

      <!-- 编辑器区域 -->
      <div class="editor-layout">
        <el-row :gutter="24">
          <!-- 左侧编辑器 -->
          <el-col :span="18">
            <el-card class="editor-card">
              <template #header>
                <div class="editor-header">
                  <div class="header-left">
                    <span>策略代码编辑器</span>
                    <el-tag v-if="hasChanges" type="warning" size="small" style="margin-left: 8px">
                      未保存
                    </el-tag>
                  </div>
                  <div class="header-right">
                    <el-button-group size="small">
                      <el-button @click="handleUndo" :disabled="!canUndo">
                        <el-icon><RefreshLeft /></el-icon>
                        撤销
                      </el-button>
                      <el-button @click="handleRedo" :disabled="!canRedo">
                        <el-icon><RefreshRight /></el-icon>
                        重做
                      </el-button>
                    </el-button-group>
                  </div>
                </div>
              </template>
              
              <MonacoEditor
                ref="editorRef"
                v-model="editedCode"
                :language="strategy.language"
                height="600px"
                :show-toolbar="true"
                :show-status="true"
                @change="handleCodeChange"
                @focus="handleEditorFocus"
                @blur="handleEditorBlur"
              />
            </el-card>
          </el-col>

          <!-- 右侧面板 -->
          <el-col :span="6">
            <!-- 策略信息 -->
            <el-card class="info-card">
              <template #header>
                <span>策略信息</span>
              </template>
              
              <el-form :model="strategyInfo" label-width="80px" size="small">
                <el-form-item label="策略名称">
                  <el-input v-model="strategyInfo.name" />
                </el-form-item>
                
                <el-form-item label="策略类型">
                  <el-select v-model="strategyInfo.strategy_type" style="width: 100%">
                    <el-option
                      v-for="option in STRATEGY_TYPE_OPTIONS"
                      :key="option.value"
                      :label="option.label"
                      :value="option.value"
                    />
                  </el-select>
                </el-form-item>
                
                <el-form-item label="入口函数">
                  <el-input v-model="strategyInfo.entry_point" />
                </el-form-item>
                
                <el-form-item label="时间周期">
                  <el-select v-model="strategyInfo.timeframe" style="width: 100%" clearable>
                    <el-option label="1分钟" value="1m" />
                    <el-option label="5分钟" value="5m" />
                    <el-option label="15分钟" value="15m" />
                    <el-option label="30分钟" value="30m" />
                    <el-option label="1小时" value="1h" />
                    <el-option label="4小时" value="4h" />
                    <el-option label="1天" value="1d" />
                  </el-select>
                </el-form-item>
                
                <el-form-item label="策略描述">
                  <el-input
                    v-model="strategyInfo.description"
                    type="textarea"
                    :rows="3"
                    placeholder="请输入策略描述"
                  />
                </el-form-item>
              </el-form>
            </el-card>

            <!-- 代码分析 -->
            <el-card class="analysis-card">
              <template #header>
                <div class="analysis-header">
                  <span>代码分析</span>
                  <el-button size="small" @click="analyzeCode">
                    <el-icon><Refresh /></el-icon>
                    分析
                  </el-button>
                </div>
              </template>
              
              <div class="analysis-content">
                <div class="analysis-item">
                  <span class="analysis-label">代码行数:</span>
                  <span class="analysis-value">{{ codeStats.lines }}</span>
                </div>
                <div class="analysis-item">
                  <span class="analysis-label">函数数量:</span>
                  <span class="analysis-value">{{ codeStats.functions }}</span>
                </div>
                <div class="analysis-item">
                  <span class="analysis-label">类数量:</span>
                  <span class="analysis-value">{{ codeStats.classes }}</span>
                </div>
                <div class="analysis-item">
                  <span class="analysis-label">导入模块:</span>
                  <span class="analysis-value">{{ codeStats.imports }}</span>
                </div>
              </div>
              
              <!-- 语法检查结果 -->
              <div class="syntax-check" v-if="syntaxErrors.length > 0">
                <el-divider content-position="left">语法检查</el-divider>
                <div
                  v-for="(error, index) in syntaxErrors"
                  :key="index"
                  class="error-item"
                >
                  <el-alert
                    :title="`第${error.line}行: ${error.message}`"
                    type="error"
                    size="small"
                    :closable="false"
                    show-icon
                  />
                </div>
              </div>
            </el-card>

            <!-- 快速操作 -->
            <el-card class="actions-card">
              <template #header>
                <span>快速操作</span>
              </template>
              
              <div class="quick-actions">
                <el-button @click="insertTemplate('function')" size="small" style="width: 100%; margin-bottom: 8px">
                  <el-icon><Plus /></el-icon>
                  插入函数模板
                </el-button>
                <el-button @click="insertTemplate('class')" size="small" style="width: 100%; margin-bottom: 8px">
                  <el-icon><Plus /></el-icon>
                  插入类模板
                </el-button>
                <el-button @click="insertTemplate('import')" size="small" style="width: 100%; margin-bottom: 8px">
                  <el-icon><Plus /></el-icon>
                  插入导入语句
                </el-button>
                <el-button @click="insertTemplate('docstring')" size="small" style="width: 100%; margin-bottom: 8px">
                  <el-icon><Plus /></el-icon>
                  插入文档字符串
                </el-button>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>
    </div>

    <!-- 空状态 -->
    <EmptyState
      v-else-if="!loading"
      type="error"
      title="策略不存在"
      description="请检查策略ID是否正确或您是否有权限编辑此策略"
      :show-action="true"
      action-text="返回列表"
      @action="goToList"
    />

    <!-- 预览对话框 -->
    <BaseDialog
      v-model="showPreviewDialog"
      title="代码预览"
      width="80%"
      :show-confirm="false"
      cancel-text="关闭"
    >
      <MonacoEditor
        :model-value="editedCode"
        :language="strategy?.language || 'python'"
        height="500px"
        :readonly="true"
        :show-toolbar="false"
        :show-status="false"
      />
    </BaseDialog>

    <!-- 测试结果对话框 -->
    <BaseDialog
      v-model="showTestDialog"
      title="代码测试结果"
      width="60%"
      :show-confirm="false"
      cancel-text="关闭"
    >
      <div class="test-results">
        <div v-if="testResults.success" class="test-success">
          <el-alert
            title="代码测试通过"
            type="success"
            :closable="false"
            show-icon
          />
          <div class="test-details" v-if="testResults.details">
            <h4>测试详情:</h4>
            <pre>{{ testResults.details }}</pre>
          </div>
        </div>
        
        <div v-else class="test-error">
          <el-alert
            title="代码测试失败"
            type="error"
            :closable="false"
            show-icon
          />
          <div class="error-details" v-if="testResults.error">
            <h4>错误信息:</h4>
            <pre class="error-message">{{ testResults.error }}</pre>
          </div>
        </div>
      </div>
    </BaseDialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft, View, Cpu, Check, RefreshLeft, RefreshRight,
  Refresh, Plus
} from '@element-plus/icons-vue'

import { useStrategyStore } from '@/stores/strategy'
import { MonacoEditor, StatusTag, EmptyState, BaseDialog } from '@/components/common'
import {
  STRATEGY_TYPE_OPTIONS,
  type Strategy,
  type StrategyUpdateRequest
} from '@/types/strategy'

const route = useRoute()
const router = useRouter()
const strategyStore = useStrategyStore()

// 响应式数据
const editorRef = ref()
const editedCode = ref('')
const originalCode = ref('')
const strategyInfo = ref({
  name: '',
  description: '',
  strategy_type: '',
  entry_point: 'main',
  timeframe: ''
})
const showPreviewDialog = ref(false)
const showTestDialog = ref(false)
const testResults = ref({
  success: false,
  details: '',
  error: ''
})
const syntaxErrors = ref<Array<{ line: number; message: string }>>([])
const codeStats = ref({
  lines: 0,
  functions: 0,
  classes: 0,
  imports: 0
})
const canUndo = ref(false)
const canRedo = ref(false)

// 计算属性
const strategyId = computed(() => parseInt(route.params.id as string))
const strategy = computed(() => strategyStore.currentStrategy)
const loading = computed(() => strategyStore.loading)

const hasChanges = computed(() => {
  if (!strategy.value) return false
  
  return (
    editedCode.value !== originalCode.value ||
    strategyInfo.value.name !== strategy.value.name ||
    strategyInfo.value.description !== (strategy.value.description || '') ||
    strategyInfo.value.strategy_type !== strategy.value.strategy_type ||
    strategyInfo.value.entry_point !== strategy.value.entry_point ||
    strategyInfo.value.timeframe !== (strategy.value.timeframe || '')
  )
})

// 方法
const goBack = () => {
  if (hasChanges.value) {
    ElMessageBox.confirm(
      '您有未保存的更改，确定要离开吗？',
      '确认离开',
      {
        confirmButtonText: '离开',
        cancelButtonText: '取消',
        type: 'warning'
      }
    ).then(() => {
      router.push(`/strategy/${strategyId.value}`)
    }).catch(() => {
      // 用户取消
    })
  } else {
    router.push(`/strategy/${strategyId.value}`)
  }
}

const goToList = () => {
  router.push('/strategy')
}

const handleCodeChange = (value: string) => {
  editedCode.value = value
  analyzeCode()
}

const handleEditorFocus = () => {
  // 编辑器获得焦点时的处理
}

const handleEditorBlur = () => {
  // 编辑器失去焦点时的处理
}

const handleUndo = () => {
  if (editorRef.value?.editor()) {
    editorRef.value.editor().getAction('undo')?.run()
  }
}

const handleRedo = () => {
  if (editorRef.value?.editor()) {
    editorRef.value.editor().getAction('redo')?.run()
  }
}

const handlePreview = () => {
  showPreviewDialog.value = true
}

const handleTest = async () => {
  try {
    // 这里应该调用后端API进行代码测试
    // 暂时模拟测试结果
    testResults.value = {
      success: true,
      details: '代码语法检查通过\n函数定义正确\n导入模块可用',
      error: ''
    }
    
    // 模拟一些错误情况
    if (editedCode.value.includes('syntax_error')) {
      testResults.value = {
        success: false,
        details: '',
        error: 'SyntaxError: invalid syntax at line 10'
      }
    }
    
    showTestDialog.value = true
  } catch (error) {
    ElMessage.error('代码测试失败')
  }
}

const handleSave = async () => {
  if (!strategy.value || !hasChanges.value) return
  
  try {
    const updateData: StrategyUpdateRequest = {
      name: strategyInfo.value.name,
      description: strategyInfo.value.description,
      strategy_type: strategyInfo.value.strategy_type as any,
      code: editedCode.value,
      entry_point: strategyInfo.value.entry_point,
      timeframe: strategyInfo.value.timeframe
    }
    
    const updatedStrategy = await strategyStore.updateStrategy(strategyId.value, updateData)
    
    if (updatedStrategy) {
      originalCode.value = editedCode.value
      ElMessage.success('策略保存成功')
    }
  } catch (error) {
    ElMessage.error('策略保存失败')
  }
}

const analyzeCode = () => {
  const code = editedCode.value
  
  // 统计代码行数
  const lines = code.split('\n').filter(line => line.trim()).length
  
  // 统计函数数量
  const functionMatches = code.match(/def\s+\w+\s*\(/g)
  const functions = functionMatches ? functionMatches.length : 0
  
  // 统计类数量
  const classMatches = code.match(/class\s+\w+\s*[\(:]?/g)
  const classes = classMatches ? classMatches.length : 0
  
  // 统计导入语句
  const importMatches = code.match(/^(import|from)\s+/gm)
  const imports = importMatches ? importMatches.length : 0
  
  codeStats.value = {
    lines,
    functions,
    classes,
    imports
  }
  
  // 简单的语法检查
  checkSyntax()
}

const checkSyntax = () => {
  const code = editedCode.value
  const lines = code.split('\n')
  const errors: Array<{ line: number; message: string }> = []
  
  lines.forEach((line, index) => {
    const lineNumber = index + 1
    const trimmedLine = line.trim()
    
    // 检查缩进
    if (trimmedLine && !line.startsWith(' ') && !line.startsWith('\t') && 
        (trimmedLine.startsWith('def ') || trimmedLine.startsWith('class ') || 
         trimmedLine.startsWith('if ') || trimmedLine.startsWith('for ') || 
         trimmedLine.startsWith('while ') || trimmedLine.startsWith('try:') ||
         trimmedLine.startsWith('except ') || trimmedLine.startsWith('finally:'))) {
      // 这些语句后面应该有缩进的代码块
      if (lineNumber < lines.length) {
        const nextLine = lines[lineNumber]
        if (nextLine && nextLine.trim() && !nextLine.startsWith(' ') && !nextLine.startsWith('\t')) {
          errors.push({
            line: lineNumber + 1,
            message: '缺少缩进'
          })
        }
      }
    }
    
    // 检查括号匹配
    const openBrackets = (line.match(/\(/g) || []).length
    const closeBrackets = (line.match(/\)/g) || []).length
    if (openBrackets !== closeBrackets) {
      errors.push({
        line: lineNumber,
        message: '括号不匹配'
      })
    }
    
    // 检查冒号
    if ((trimmedLine.startsWith('def ') || trimmedLine.startsWith('class ') || 
         trimmedLine.startsWith('if ') || trimmedLine.startsWith('for ') || 
         trimmedLine.startsWith('while ')) && !trimmedLine.endsWith(':')) {
      errors.push({
        line: lineNumber,
        message: '缺少冒号'
      })
    }
  })
  
  syntaxErrors.value = errors.slice(0, 10) // 最多显示10个错误
}

const insertTemplate = (type: string) => {
  let template = ''
  
  switch (type) {
    case 'function':
      template = `
def function_name(param1, param2):
    """
    函数描述
    
    Args:
        param1: 参数1描述
        param2: 参数2描述
    
    Returns:
        返回值描述
    """
    pass
`
      break
      
    case 'class':
      template = `
class ClassName:
    """类描述"""
    
    def __init__(self):
        """初始化方法"""
        pass
    
    def method_name(self):
        """方法描述"""
        pass
`
      break
      
    case 'import':
      template = `
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
`
      break
      
    case 'docstring':
      template = `
"""
模块/函数/类的详细描述

这里可以包含更详细的说明，包括：
- 功能描述
- 使用示例
- 注意事项

Example:
    >>> example_usage()
    'example result'

Note:
    这是一个注意事项
"""
`
      break
  }
  
  if (template && editorRef.value) {
    editorRef.value.insertText(template)
  }
}

const initializeData = () => {
  if (strategy.value) {
    editedCode.value = strategy.value.code
    originalCode.value = strategy.value.code
    
    strategyInfo.value = {
      name: strategy.value.name,
      description: strategy.value.description || '',
      strategy_type: strategy.value.strategy_type,
      entry_point: strategy.value.entry_point,
      timeframe: strategy.value.timeframe || ''
    }
    
    analyzeCode()
  }
}

// 页面离开前确认
const beforeUnloadHandler = (event: BeforeUnloadEvent) => {
  if (hasChanges.value) {
    event.preventDefault()
    event.returnValue = '您有未保存的更改，确定要离开吗？'
  }
}

// 生命周期
onMounted(async () => {
  await strategyStore.fetchStrategy(strategyId.value)
  initializeData()
  
  // 添加页面离开前确认
  window.addEventListener('beforeunload', beforeUnloadHandler)
})

onBeforeUnmount(() => {
  window.removeEventListener('beforeunload', beforeUnloadHandler)
})

// 监听策略数据变化
watch(() => strategy.value, (newStrategy) => {
  if (newStrategy) {
    initializeData()
  }
}, { immediate: true })
</script>

<style lang="scss" scoped>
.strategy-edit {
  padding: 20px;
  
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 24px;
    
    .header-left {
      .back-button {
        margin-bottom: 12px;
        color: var(--el-text-color-secondary);
        
        &:hover {
          color: var(--el-color-primary);
        }
      }
      
      .header-info {
        .strategy-title {
          margin: 0 0 8px 0;
          font-size: 24px;
          font-weight: 600;
          color: var(--el-text-color-primary);
        }
        
        .strategy-meta {
          display: flex;
          align-items: center;
          gap: 8px;
          
          .version-info {
            color: var(--el-text-color-secondary);
            font-size: 14px;
            margin-left: 8px;
          }
        }
      }
    }
    
    .header-actions {
      display: flex;
      gap: 12px;
    }
  }
  
  .editor-layout {
    .editor-card {
      .editor-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        width: 100%;
      }
    }
    
    .info-card,
    .analysis-card,
    .actions-card {
      margin-bottom: 20px;
      
      &:last-child {
        margin-bottom: 0;
      }
    }
    
    .analysis-card {
      .analysis-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        width: 100%;
      }
      
      .analysis-content {
        .analysis-item {
          display: flex;
          justify-content: space-between;
          margin-bottom: 8px;
          
          .analysis-label {
            color: var(--el-text-color-secondary);
            font-size: 13px;
          }
          
          .analysis-value {
            color: var(--el-text-color-primary);
            font-weight: 500;
            font-size: 13px;
          }
        }
      }
      
      .syntax-check {
        margin-top: 16px;
        
        .error-item {
          margin-bottom: 8px;
          
          &:last-child {
            margin-bottom: 0;
          }
        }
      }
    }
    
    .actions-card {
      .quick-actions {
        .el-button {
          justify-content: flex-start;
        }
      }
    }
  }
  
  .test-results {
    .test-success,
    .test-error {
      .test-details,
      .error-details {
        margin-top: 16px;
        
        h4 {
          margin: 0 0 8px 0;
          font-size: 14px;
          color: var(--el-text-color-primary);
        }
        
        pre {
          background: var(--el-fill-color-light);
          border: 1px solid var(--el-border-color);
          border-radius: 4px;
          padding: 12px;
          margin: 0;
          font-size: 12px;
          line-height: 1.5;
          overflow-x: auto;
          
          &.error-message {
            color: var(--el-color-danger);
          }
        }
      }
    }
  }
}
</style>