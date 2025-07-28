<template>
  <div class="strategy-editor">
    <div class="editor-header">
      <div class="header-left">
        <el-button @click="goBack" text>
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
        <el-divider direction="vertical" />
        <h2 class="strategy-title">
          {{ strategy?.name || '新建策略' }}
          <el-tag v-if="strategy" :type="statusTagType" size="small">
            {{ statusText }}
          </el-tag>
        </h2>
      </div>
      
      <div class="header-actions">
        <el-button @click="handleSave" :loading="saving">
          <el-icon><Document /></el-icon>
          保存
        </el-button>
        <el-button @click="handleValidate" :loading="validating">
          <el-icon><CircleCheck /></el-icon>
          验证
        </el-button>
        <el-button 
          v-if="strategy && !strategy.runtime?.is_running" 
          type="success" 
          @click="handleRun"
        >
          <el-icon><VideoPlay /></el-icon>
          运行
        </el-button>
        <el-button 
          v-if="strategy?.runtime?.is_running" 
          type="warning" 
          @click="handleStop"
        >
          <el-icon><VideoPause /></el-icon>
          停止
        </el-button>
      </div>
    </div>

    <div class="editor-content">
      <!-- 左侧文件树 -->
      <div class="file-panel">
        <div class="panel-header">
          <span class="panel-title">文件</span>
          <el-dropdown @command="handleFileCommand">
            <el-button text size="small">
              <el-icon><Plus /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="new-file">新建文件</el-dropdown-item>
                <el-dropdown-item command="new-folder">新建文件夹</el-dropdown-item>
                <el-dropdown-item command="upload">上传文件</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
        
        <div class="file-tree">
          <el-tree
            ref="fileTreeRef"
            :data="fileTree"
            :props="treeProps"
            node-key="id"
            :expand-on-click-node="false"
            @node-click="handleFileClick"
          >
            <template #default="{ node, data }">
              <div class="file-node">
                <el-icon>
                  <Folder v-if="data.type === 'folder'" />
                  <Document v-else />
                </el-icon>
                <span class="file-name">{{ data.name }}</span>
                <div class="file-actions" v-if="!data.isRoot">
                  <el-button 
                    text 
                    size="small" 
                    @click.stop="handleRenameFile(data)"
                  >
                    <el-icon><Edit /></el-icon>
                  </el-button>
                  <el-button 
                    text 
                    size="small" 
                    @click.stop="handleDeleteFile(data)"
                  >
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </div>
              </div>
            </template>
          </el-tree>
        </div>
      </div>

      <!-- 中间代码编辑器 -->
      <div class="code-panel">
        <div class="editor-tabs">
          <el-tabs
            v-model="activeTab"
            type="card"
            closable
            @tab-remove="handleTabRemove"
          >
            <el-tab-pane
              v-for="tab in openTabs"
              :key="tab.id"
              :label="tab.name"
              :name="tab.id"
            >
              <template #label>
                <span class="tab-label">
                  <el-icon><Document /></el-icon>
                  {{ tab.name }}
                  <span v-if="tab.modified" class="modified-indicator">●</span>
                </span>
              </template>
            </el-tab-pane>
          </el-tabs>
        </div>
        
        <div class="editor-container" ref="editorContainer">
          <!-- Monaco Editor 将在这里挂载 -->
        </div>
      </div>

      <!-- 右侧属性面板 -->
      <div class="property-panel">
        <el-tabs v-model="rightPanelTab" type="card">
          <el-tab-pane label="属性" name="properties">
            <div class="properties-content">
              <el-form :model="strategyConfig" label-width="80px" size="small">
                <el-form-item label="策略名称">
                  <el-input v-model="strategyConfig.name" />
                </el-form-item>
                <el-form-item label="描述">
                  <el-input 
                    v-model="strategyConfig.description" 
                    type="textarea" 
                    :rows="3"
                  />
                </el-form-item>
                <el-form-item label="版本">
                  <el-input v-model="strategyConfig.version" />
                </el-form-item>
                <el-form-item label="分类">
                  <el-select v-model="strategyConfig.category">
                    <el-option
                      v-for="category in categories"
                      :key="category.id"
                      :label="category.name"
                      :value="category.id"
                    />
                  </el-select>
                </el-form-item>
              </el-form>
            </div>
          </el-tab-pane>
          
          <el-tab-pane label="参数" name="parameters">
            <div class="parameters-content">
              <div class="parameter-item" v-for="(param, key) in strategyParameters" :key="key">
                <label class="param-label">{{ key }}</label>
                <el-input 
                  v-model="strategyParameters[key]" 
                  size="small"
                  @change="handleParameterChange"
                />
              </div>
              <el-button 
                text 
                size="small" 
                @click="showAddParameterDialog = true"
              >
                <el-icon><Plus /></el-icon>
                添加参数
              </el-button>
            </div>
          </el-tab-pane>
          
          <el-tab-pane label="日志" name="logs">
            <div class="logs-content">
              <div class="log-controls">
                <el-select v-model="logLevel" size="small">
                  <el-option label="全部" value="" />
                  <el-option label="DEBUG" value="DEBUG" />
                  <el-option label="INFO" value="INFO" />
                  <el-option label="WARNING" value="WARNING" />
                  <el-option label="ERROR" value="ERROR" />
                </el-select>
                <el-button size="small" @click="clearLogs">清空</el-button>
              </div>
              <div class="log-list">
                <div 
                  v-for="log in filteredLogs" 
                  :key="log.id"
                  :class="['log-item', `log-${log.level.toLowerCase()}`]"
                >
                  <span class="log-time">{{ formatTime(log.timestamp) }}</span>
                  <span class="log-level">{{ log.level }}</span>
                  <span class="log-message">{{ log.message }}</span>
                </div>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>

    <!-- 新建文件对话框 -->
    <el-dialog v-model="showNewFileDialog" title="新建文件" width="400px">
      <el-form :model="newFileForm" label-width="80px">
        <el-form-item label="文件名">
          <el-input v-model="newFileForm.name" placeholder="请输入文件名" />
        </el-form-item>
        <el-form-item label="文件类型">
          <el-select v-model="newFileForm.type">
            <el-option label="Python文件" value="python" />
            <el-option label="配置文件" value="config" />
            <el-option label="数据文件" value="data" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showNewFileDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreateFile">创建</el-button>
      </template>
    </el-dialog>

    <!-- 添加参数对话框 -->
    <el-dialog v-model="showAddParameterDialog" title="添加参数" width="400px">
      <el-form :model="newParameterForm" label-width="80px">
        <el-form-item label="参数名">
          <el-input v-model="newParameterForm.name" placeholder="请输入参数名" />
        </el-form-item>
        <el-form-item label="默认值">
          <el-input v-model="newParameterForm.value" placeholder="请输入默认值" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="newParameterForm.description" placeholder="请输入参数描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddParameterDialog = false">取消</el-button>
        <el-button type="primary" @click="handleAddParameter">添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft,
  Document,
  CircleCheck,
  VideoPlay,
  VideoPause,
  Plus,
  Folder,
  Edit,
  Delete
} from '@element-plus/icons-vue'
import { useStrategyStore } from '@/stores/strategy'
import type { Strategy, StrategyFile, StrategyLog } from '@/types/strategy'

// Monaco Editor 相关
let monaco: any = null
let editor: any = null

const route = useRoute()
const router = useRouter()
const strategyStore = useStrategyStore()

// 响应式数据
const strategy = ref<Strategy | null>(null)
const saving = ref(false)
const validating = ref(false)
const activeTab = ref('')
const rightPanelTab = ref('properties')
const logLevel = ref('')

// 文件相关
const fileTreeRef = ref()
const editorContainer = ref()
const openTabs = ref<Array<{
  id: string
  name: string
  content: string
  modified: boolean
  file?: StrategyFile
}>>([])

const fileTree = ref([
  {
    id: 'root',
    name: '策略文件',
    type: 'folder',
    isRoot: true,
    children: []
  }
])

const treeProps = {
  children: 'children',
  label: 'name'
}

// 对话框
const showNewFileDialog = ref(false)
const showAddParameterDialog = ref(false)

const newFileForm = ref({
  name: '',
  type: 'python'
})

const newParameterForm = ref({
  name: '',
  value: '',
  description: ''
})

// 策略配置
const strategyConfig = ref({
  name: '',
  description: '',
  version: '1.0.0',
  category: ''
})

const strategyParameters = ref<Record<string, any>>({})

// 日志
const logs = ref<StrategyLog[]>([])

// 计算属性
const categories = computed(() => strategyStore.categories)

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

const filteredLogs = computed(() => {
  if (!logLevel.value) return logs.value
  return logs.value.filter(log => log.level === logLevel.value)
})

// 方法
const initMonacoEditor = async () => {
  try {
    // 动态导入 Monaco Editor
    monaco = await import('monaco-editor')
    
    // 配置 Monaco Editor
    monaco.languages.typescript.typescriptDefaults.setCompilerOptions({
      target: monaco.languages.typescript.ScriptTarget.ES2015,
      allowNonTsExtensions: true,
      moduleResolution: monaco.languages.typescript.ModuleResolutionKind.NodeJs,
      module: monaco.languages.typescript.ModuleKind.CommonJS,
      noEmit: true,
      typeRoots: ['node_modules/@types']
    })

    // 创建编辑器实例
    editor = monaco.editor.create(editorContainer.value, {
      value: '# 请选择或创建一个文件开始编辑',
      language: 'python',
      theme: 'vs-dark',
      automaticLayout: true,
      minimap: { enabled: true },
      scrollBeyondLastLine: false,
      fontSize: 14,
      tabSize: 4,
      insertSpaces: true,
      wordWrap: 'on'
    })

    // 监听内容变化
    editor.onDidChangeModelContent(() => {
      if (activeTab.value) {
        const tab = openTabs.value.find(t => t.id === activeTab.value)
        if (tab) {
          tab.content = editor.getValue()
          tab.modified = true
        }
      }
    })
  } catch (error) {
    console.error('Failed to initialize Monaco Editor:', error)
    ElMessage.error('代码编辑器初始化失败')
  }
}

const loadStrategy = async () => {
  const strategyId = route.params.id as string
  if (strategyId && strategyId !== 'new') {
    try {
      strategy.value = await strategyStore.fetchStrategy(parseInt(strategyId))
      if (strategy.value) {
        strategyConfig.value = {
          name: strategy.value.name,
          description: strategy.value.description,
          version: strategy.value.version,
          category: strategy.value.category
        }
        strategyParameters.value = strategy.value.config.parameters || {}
        
        // 加载策略文件
        await loadStrategyFiles()
      }
    } catch (error) {
      ElMessage.error('加载策略失败')
      goBack()
    }
  }
}

const loadStrategyFiles = async () => {
  if (!strategy.value) return
  
  try {
    const files = await strategyStore.fetchStrategyFiles(strategy.value.id)
    
    // 构建文件树
    const rootNode = fileTree.value[0]
    rootNode.children = files.map(file => ({
      id: file.id.toString(),
      name: file.filename,
      type: 'file',
      file: file
    }))
    
    // 如果有主文件，自动打开
    const mainFile = files.find(f => f.filename === 'main.py' || f.filename.endsWith('.py'))
    if (mainFile) {
      handleFileClick({ file: mainFile })
    }
  } catch (error) {
    ElMessage.error('加载策略文件失败')
  }
}

const handleFileClick = (data: any) => {
  if (data.type === 'folder' || !data.file) return
  
  const file = data.file as StrategyFile
  const existingTab = openTabs.value.find(tab => tab.id === file.id.toString())
  
  if (existingTab) {
    activeTab.value = existingTab.id
  } else {
    const newTab = {
      id: file.id.toString(),
      name: file.filename,
      content: file.content,
      modified: false,
      file: file
    }
    
    openTabs.value.push(newTab)
    activeTab.value = newTab.id
  }
  
  // 更新编辑器内容
  if (editor) {
    editor.setValue(file.content)
    
    // 设置语言模式
    const language = getLanguageFromFilename(file.filename)
    monaco.editor.setModelLanguage(editor.getModel(), language)
  }
}

const getLanguageFromFilename = (filename: string) => {
  const ext = filename.split('.').pop()?.toLowerCase()
  const languageMap: Record<string, string> = {
    'py': 'python',
    'js': 'javascript',
    'ts': 'typescript',
    'json': 'json',
    'yaml': 'yaml',
    'yml': 'yaml',
    'md': 'markdown',
    'txt': 'plaintext'
  }
  return languageMap[ext || ''] || 'plaintext'
}

const handleTabRemove = (tabId: string) => {
  const tabIndex = openTabs.value.findIndex(tab => tab.id === tabId)
  if (tabIndex === -1) return
  
  const tab = openTabs.value[tabIndex]
  
  if (tab.modified) {
    ElMessageBox.confirm(
      `文件 "${tab.name}" 已修改，是否保存？`,
      '确认关闭',
      {
        confirmButtonText: '保存并关闭',
        cancelButtonText: '不保存',
        distinguishCancelAndClose: true,
        type: 'warning'
      }
    ).then(() => {
      // 保存文件
      handleSaveFile(tab)
      removeTab(tabIndex)
    }).catch((action) => {
      if (action === 'cancel') {
        // 不保存直接关闭
        removeTab(tabIndex)
      }
    })
  } else {
    removeTab(tabIndex)
  }
}

const removeTab = (tabIndex: number) => {
  const removedTab = openTabs.value[tabIndex]
  openTabs.value.splice(tabIndex, 1)
  
  if (activeTab.value === removedTab.id) {
    if (openTabs.value.length > 0) {
      const newIndex = Math.min(tabIndex, openTabs.value.length - 1)
      activeTab.value = openTabs.value[newIndex].id
      handleFileClick({ file: openTabs.value[newIndex].file })
    } else {
      activeTab.value = ''
      if (editor) {
        editor.setValue('')
      }
    }
  }
}

const handleFileCommand = (command: string) => {
  switch (command) {
    case 'new-file':
      showNewFileDialog.value = true
      break
    case 'new-folder':
      // 创建文件夹逻辑
      break
    case 'upload':
      // 上传文件逻辑
      break
  }
}

const handleCreateFile = async () => {
  if (!newFileForm.value.name || !strategy.value) return
  
  try {
    const file = await strategyStore.createStrategyFile(strategy.value.id, {
      filename: newFileForm.value.name,
      content: getDefaultContent(newFileForm.value.type),
      file_type: newFileForm.value.type
    })
    
    // 更新文件树
    const rootNode = fileTree.value[0]
    rootNode.children.push({
      id: file.id.toString(),
      name: file.filename,
      type: 'file',
      file: file
    })
    
    // 打开新文件
    handleFileClick({ file: file })
    
    showNewFileDialog.value = false
    newFileForm.value = { name: '', type: 'python' }
  } catch (error) {
    ElMessage.error('创建文件失败')
  }
}

const getDefaultContent = (type: string) => {
  const templates: Record<string, string> = {
    python: `# -*- coding: utf-8 -*-
"""
策略文件
"""

def initialize(context):
    """
    策略初始化函数
    """
    pass

def handle_bar(context, bar_dict):
    """
    处理K线数据
    """
    pass
`,
    config: `{
  "name": "策略配置",
  "version": "1.0.0",
  "parameters": {}
}`,
    data: ''
  }
  return templates[type] || ''
}

const handleSave = async () => {
  if (!strategy.value) return
  
  saving.value = true
  try {
    // 保存所有修改的文件
    const savePromises = openTabs.value
      .filter(tab => tab.modified && tab.file)
      .map(tab => handleSaveFile(tab))
    
    await Promise.all(savePromises)
    
    // 更新策略配置
    await strategyStore.updateStrategy(strategy.value.id, {
      name: strategyConfig.value.name,
      description: strategyConfig.value.description,
      category: strategyConfig.value.category,
      config: {
        ...strategy.value.config,
        parameters: strategyParameters.value
      }
    })
    
    ElMessage.success('保存成功')
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

const handleSaveFile = async (tab: any) => {
  if (!tab.file || !strategy.value) return
  
  try {
    await strategyStore.updateStrategyFile(
      strategy.value.id,
      tab.file.id,
      { content: tab.content }
    )
    tab.modified = false
  } catch (error) {
    throw error
  }
}

const handleValidate = async () => {
  if (!strategy.value) return
  
  validating.value = true
  try {
    // 调用策略验证API
    // await strategyApi.validateStrategy(strategy.value.id)
    ElMessage.success('策略验证通过')
  } catch (error) {
    ElMessage.error('策略验证失败')
  } finally {
    validating.value = false
  }
}

const handleRun = async () => {
  if (!strategy.value) return
  
  try {
    await strategyStore.startStrategy(strategy.value.id)
    await loadStrategy() // 重新加载策略状态
  } catch (error) {
    // 错误已在store中处理
  }
}

const handleStop = async () => {
  if (!strategy.value) return
  
  try {
    await strategyStore.stopStrategy(strategy.value.id)
    await loadStrategy() // 重新加载策略状态
  } catch (error) {
    // 错误已在store中处理
  }
}

const handleParameterChange = () => {
  // 参数变化处理
}

const handleAddParameter = () => {
  if (!newParameterForm.value.name) return
  
  strategyParameters.value[newParameterForm.value.name] = newParameterForm.value.value
  
  showAddParameterDialog.value = false
  newParameterForm.value = { name: '', value: '', description: '' }
}

const clearLogs = () => {
  logs.value = []
}

const formatTime = (timestamp: string) => {
  return new Date(timestamp).toLocaleTimeString()
}

const goBack = () => {
  router.push('/strategies')
}

// 生命周期
onMounted(async () => {
  await nextTick()
  await initMonacoEditor()
  await loadStrategy()
  
  // 加载分类数据
  if (strategyStore.categories.length === 0) {
    strategyStore.fetchCategories()
  }
})

onUnmounted(() => {
  if (editor) {
    editor.dispose()
  }
})
</script>

<style scoped lang="scss">
.strategy-editor {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #1e1e1e;
  color: #d4d4d4;
  
  .editor-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    background: #2d2d30;
    border-bottom: 1px solid #3e3e42;
    
    .header-left {
      display: flex;
      align-items: center;
      gap: 12px;
      
      .strategy-title {
        margin: 0;
        font-size: 16px;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 8px;
      }
    }
    
    .header-actions {
      display: flex;
      gap: 8px;
    }
  }
  
  .editor-content {
    flex: 1;
    display: flex;
    overflow: hidden;
    
    .file-panel {
      width: 250px;
      background: #252526;
      border-right: 1px solid #3e3e42;
      display: flex;
      flex-direction: column;
      
      .panel-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 12px;
        background: #2d2d30;
        border-bottom: 1px solid #3e3e42;
        
        .panel-title {
          font-size: 12px;
          font-weight: 600;
          text-transform: uppercase;
        }
      }
      
      .file-tree {
        flex: 1;
        overflow-y: auto;
        padding: 8px;
        
        .file-node {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 2px 4px;
          border-radius: 4px;
          cursor: pointer;
          
          &:hover {
            background: #2a2d2e;
            
            .file-actions {
              opacity: 1;
            }
          }
          
          .file-name {
            flex: 1;
            font-size: 13px;
          }
          
          .file-actions {
            opacity: 0;
            display: flex;
            gap: 2px;
            transition: opacity 0.2s;
          }
        }
      }
    }
    
    .code-panel {
      flex: 1;
      display: flex;
      flex-direction: column;
      
      .editor-tabs {
        background: #2d2d30;
        border-bottom: 1px solid #3e3e42;
        
        .tab-label {
          display: flex;
          align-items: center;
          gap: 4px;
          
          .modified-indicator {
            color: #f0c674;
            font-weight: bold;
          }
        }
      }
      
      .editor-container {
        flex: 1;
        min-height: 0;
      }
    }
    
    .property-panel {
      width: 300px;
      background: #252526;
      border-left: 1px solid #3e3e42;
      
      .properties-content,
      .parameters-content,
      .logs-content {
        padding: 12px;
      }
      
      .parameter-item {
        margin-bottom: 12px;
        
        .param-label {
          display: block;
          font-size: 12px;
          margin-bottom: 4px;
          color: #cccccc;
        }
      }
      
      .logs-content {
        .log-controls {
          display: flex;
          gap: 8px;
          margin-bottom: 12px;
        }
        
        .log-list {
          max-height: 300px;
          overflow-y: auto;
          
          .log-item {
            padding: 4px 8px;
            margin-bottom: 2px;
            border-radius: 4px;
            font-size: 12px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            
            &.log-debug { background: #1e3a8a; }
            &.log-info { background: #065f46; }
            &.log-warning { background: #92400e; }
            &.log-error { background: #991b1b; }
            
            .log-time {
              color: #9ca3af;
              margin-right: 8px;
            }
            
            .log-level {
              font-weight: bold;
              margin-right: 8px;
              min-width: 50px;
              display: inline-block;
            }
            
            .log-message {
              word-break: break-all;
            }
          }
        }
      }
    }
  }
}

:deep(.el-tabs--card > .el-tabs__header) {
  background: #2d2d30;
  border-bottom: 1px solid #3e3e42;
  margin: 0;
}

:deep(.el-tabs--card > .el-tabs__header .el-tabs__nav) {
  border: none;
}

:deep(.el-tabs--card > .el-tabs__header .el-tabs__item) {
  background: #2d2d30;
  border: 1px solid #3e3e42;
  color: #cccccc;
  
  &.is-active {
    background: #1e1e1e;
    color: #ffffff;
  }
}

:deep(.el-tree) {
  background: transparent;
  color: #d4d4d4;
}

:deep(.el-tree-node__content) {
  background: transparent;
  
  &:hover {
    background: #2a2d2e;
  }
}

:deep(.el-form-item__label) {
  color: #cccccc;
}
</style>