<template>
  <div class="monaco-editor-container">
    <div class="editor-toolbar" v-if="showToolbar">
      <div class="toolbar-left">
        <el-select
          v-model="currentLanguage"
          size="small"
          style="width: 120px"
          @change="handleLanguageChange"
        >
          <el-option
            v-for="lang in supportedLanguages"
            :key="lang.value"
            :label="lang.label"
            :value="lang.value"
          />
        </el-select>
        
        <el-select
          v-model="currentTheme"
          size="small"
          style="width: 120px; margin-left: 8px"
          @change="handleThemeChange"
        >
          <el-option label="浅色主题" value="vs" />
          <el-option label="深色主题" value="vs-dark" />
          <el-option label="高对比度" value="hc-black" />
        </el-select>
      </div>
      
      <div class="toolbar-right">
        <el-button-group size="small">
          <el-button @click="formatCode" :disabled="!canFormat">
            <el-icon><MagicStick /></el-icon>
            格式化
          </el-button>
          <el-button @click="findAndReplace">
            <el-icon><Search /></el-icon>
            查找替换
          </el-button>
          <el-button @click="toggleMinimap">
            <el-icon><Grid /></el-icon>
            {{ showMinimap ? '隐藏' : '显示' }}缩略图
          </el-button>
        </el-button-group>
        
        <el-dropdown @command="handleCommand" style="margin-left: 8px">
          <el-button size="small">
            更多
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="undo">
                <el-icon><RefreshLeft /></el-icon>
                撤销
              </el-dropdown-item>
              <el-dropdown-item command="redo">
                <el-icon><RefreshRight /></el-icon>
                重做
              </el-dropdown-item>
              <el-dropdown-item command="selectAll" divided>
                <el-icon><Select /></el-icon>
                全选
              </el-dropdown-item>
              <el-dropdown-item command="copy">
                <el-icon><CopyDocument /></el-icon>
                复制
              </el-dropdown-item>
              <el-dropdown-item command="paste">
                <el-icon><DocumentCopy /></el-icon>
                粘贴
              </el-dropdown-item>
              <el-dropdown-item command="toggleWordWrap" divided>
                <el-icon><Sort /></el-icon>
                切换自动换行
              </el-dropdown-item>
              <el-dropdown-item command="toggleWhitespace">
                <el-icon><View /></el-icon>
                显示空白字符
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>
    
    <div
      ref="editorContainer"
      class="editor-container"
      :style="{ height: editorHeight }"
    ></div>
    
    <div class="editor-status" v-if="showStatus">
      <div class="status-left">
        <span class="status-item">
          行 {{ cursorPosition.lineNumber }}, 列 {{ cursorPosition.column }}
        </span>
        <span class="status-item" v-if="selectedText">
          已选择 {{ selectedText.length }} 个字符
        </span>
      </div>
      
      <div class="status-right">
        <span class="status-item">{{ currentLanguage.toUpperCase() }}</span>
        <span class="status-item">{{ encoding }}</span>
        <span class="status-item">{{ lineEnding }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick, computed } from 'vue'
import * as monaco from 'monaco-editor'
import {
  MagicStick, Search, Grid, ArrowDown, RefreshLeft, RefreshRight,
  Select, CopyDocument, DocumentCopy, Sort, View
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

// Props
interface Props {
  modelValue: string
  language?: string
  theme?: string
  height?: string
  readonly?: boolean
  showToolbar?: boolean
  showStatus?: boolean
  showMinimap?: boolean
  fontSize?: number
  tabSize?: number
  insertSpaces?: boolean
  wordWrap?: 'on' | 'off' | 'wordWrapColumn' | 'bounded'
  lineNumbers?: 'on' | 'off' | 'relative' | 'interval'
  folding?: boolean
  autoIndent?: 'none' | 'keep' | 'brackets' | 'advanced' | 'full'
  formatOnPaste?: boolean
  formatOnType?: boolean
  autoClosingBrackets?: 'always' | 'languageDefined' | 'beforeWhitespace' | 'never'
  autoClosingQuotes?: 'always' | 'languageDefined' | 'beforeWhitespace' | 'never'
  autoSurround?: 'languageDefined' | 'quotes' | 'brackets' | 'never'
  snippetSuggestions?: 'top' | 'bottom' | 'inline' | 'none'
}

const props = withDefaults(defineProps<Props>(), {
  language: 'python',
  theme: 'vs',
  height: '400px',
  readonly: false,
  showToolbar: true,
  showStatus: true,
  showMinimap: true,
  fontSize: 14,
  tabSize: 4,
  insertSpaces: true,
  wordWrap: 'on',
  lineNumbers: 'on',
  folding: true,
  autoIndent: 'advanced',
  formatOnPaste: true,
  formatOnType: true,
  autoClosingBrackets: 'languageDefined',
  autoClosingQuotes: 'languageDefined',
  autoSurround: 'languageDefined',
  snippetSuggestions: 'top'
})

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: string]
  'change': [value: string, event: monaco.editor.IModelContentChangedEvent]
  'focus': [event: monaco.editor.IEditorFocusEvent]
  'blur': [event: monaco.editor.IEditorBlurEvent]
  'cursorPositionChange': [position: monaco.Position]
  'selectionChange': [selection: monaco.Selection]
}>()

// 响应式数据
const editorContainer = ref<HTMLElement>()
let editor: monaco.editor.IStandaloneCodeEditor | null = null

const currentLanguage = ref(props.language)
const currentTheme = ref(props.theme)
const cursorPosition = ref({ lineNumber: 1, column: 1 })
const selectedText = ref('')
const encoding = ref('UTF-8')
const lineEnding = ref('LF')

// 支持的语言
const supportedLanguages = [
  { label: 'Python', value: 'python' },
  { label: 'JavaScript', value: 'javascript' },
  { label: 'TypeScript', value: 'typescript' },
  { label: 'JSON', value: 'json' },
  { label: 'SQL', value: 'sql' },
  { label: 'HTML', value: 'html' },
  { label: 'CSS', value: 'css' },
  { label: 'Markdown', value: 'markdown' },
  { label: 'YAML', value: 'yaml' },
  { label: 'XML', value: 'xml' }
]

// 计算属性
const editorHeight = computed(() => {
  if (props.showToolbar && props.showStatus) {
    return `calc(${props.height} - 72px)`
  } else if (props.showToolbar || props.showStatus) {
    return `calc(${props.height} - 36px)`
  }
  return props.height
})

const canFormat = computed(() => {
  return ['python', 'javascript', 'typescript', 'json', 'html', 'css'].includes(currentLanguage.value)
})

// 方法
const initEditor = async () => {
  if (!editorContainer.value) return

  // 配置Monaco Editor
  monaco.editor.defineTheme('custom-dark', {
    base: 'vs-dark',
    inherit: true,
    rules: [
      { token: 'comment', foreground: '6A9955' },
      { token: 'keyword', foreground: '569CD6' },
      { token: 'string', foreground: 'CE9178' },
      { token: 'number', foreground: 'B5CEA8' },
      { token: 'regexp', foreground: 'D16969' },
      { token: 'operator', foreground: 'D4D4D4' },
      { token: 'namespace', foreground: '4EC9B0' },
      { token: 'type', foreground: '4EC9B0' },
      { token: 'struct', foreground: '4EC9B0' },
      { token: 'class', foreground: '4EC9B0' },
      { token: 'interface', foreground: '4EC9B0' },
      { token: 'parameter', foreground: '9CDCFE' },
      { token: 'variable', foreground: '9CDCFE' },
      { token: 'property', foreground: '9CDCFE' },
      { token: 'enumMember', foreground: '4FC1FF' },
      { token: 'function', foreground: 'DCDCAA' },
      { token: 'member', foreground: 'DCDCAA' }
    ],
    colors: {
      'editor.background': '#1E1E1E',
      'editor.foreground': '#D4D4D4',
      'editorLineNumber.foreground': '#858585',
      'editorCursor.foreground': '#AEAFAD',
      'editor.selectionBackground': '#264F78',
      'editor.inactiveSelectionBackground': '#3A3D41'
    }
  })

  // 创建编辑器
  editor = monaco.editor.create(editorContainer.value, {
    value: props.modelValue,
    language: currentLanguage.value,
    theme: currentTheme.value,
    readOnly: props.readonly,
    fontSize: props.fontSize,
    tabSize: props.tabSize,
    insertSpaces: props.insertSpaces,
    wordWrap: props.wordWrap,
    lineNumbers: props.lineNumbers,
    folding: props.folding,
    autoIndent: props.autoIndent,
    formatOnPaste: props.formatOnPaste,
    formatOnType: props.formatOnType,
    autoClosingBrackets: props.autoClosingBrackets,
    autoClosingQuotes: props.autoClosingQuotes,
    autoSurround: props.autoSurround,
    snippetSuggestions: props.snippetSuggestions,
    minimap: {
      enabled: props.showMinimap
    },
    scrollBeyondLastLine: false,
    automaticLayout: true,
    contextmenu: true,
    mouseWheelZoom: true,
    smoothScrolling: true,
    cursorBlinking: 'blink',
    cursorSmoothCaretAnimation: 'on',
    renderWhitespace: 'selection',
    renderControlCharacters: false,
    renderIndentGuides: true,
    highlightActiveIndentGuide: true,
    bracketPairColorization: {
      enabled: true
    },
    guides: {
      bracketPairs: true,
      bracketPairsHorizontal: true,
      highlightActiveBracketPair: true,
      indentation: true,
      highlightActiveIndentation: true
    },
    suggest: {
      showKeywords: true,
      showSnippets: true,
      showClasses: true,
      showFunctions: true,
      showVariables: true,
      showModules: true,
      showProperties: true,
      showEvents: true,
      showOperators: true,
      showUnits: true,
      showValues: true,
      showConstants: true,
      showEnums: true,
      showEnumMembers: true,
      showColors: true,
      showFiles: true,
      showReferences: true,
      showFolders: true,
      showTypeParameters: true,
      showIssues: true,
      showUsers: true,
      showStructs: true
    }
  })

  // 绑定事件
  bindEvents()

  // 配置Python语言特性
  if (currentLanguage.value === 'python') {
    configurePythonLanguage()
  }
}

const bindEvents = () => {
  if (!editor) return

  // 内容变化事件
  editor.onDidChangeModelContent((event) => {
    const value = editor!.getValue()
    emit('update:modelValue', value)
    emit('change', value, event)
  })

  // 焦点事件
  editor.onDidFocusEditorWidget((event) => {
    emit('focus', event)
  })

  editor.onDidBlurEditorWidget((event) => {
    emit('blur', event)
  })

  // 光标位置变化
  editor.onDidChangeCursorPosition((event) => {
    cursorPosition.value = {
      lineNumber: event.position.lineNumber,
      column: event.position.column
    }
    emit('cursorPositionChange', event.position)
  })

  // 选择变化
  editor.onDidChangeCursorSelection((event) => {
    const selection = editor!.getModel()?.getValueInRange(event.selection) || ''
    selectedText.value = selection
    emit('selectionChange', event.selection)
  })
}

const configurePythonLanguage = () => {
  // 配置Python语言的自动补全
  monaco.languages.registerCompletionItemProvider('python', {
    provideCompletionItems: (model, position) => {
      const suggestions: monaco.languages.CompletionItem[] = [
        // 内置函数
        {
          label: 'print',
          kind: monaco.languages.CompletionItemKind.Function,
          insertText: 'print(${1:value})',
          insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          documentation: 'Print values to stdout'
        },
        {
          label: 'len',
          kind: monaco.languages.CompletionItemKind.Function,
          insertText: 'len(${1:obj})',
          insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          documentation: 'Return the length of an object'
        },
        {
          label: 'range',
          kind: monaco.languages.CompletionItemKind.Function,
          insertText: 'range(${1:stop})',
          insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          documentation: 'Create a range object'
        },
        // 常用关键字
        {
          label: 'def',
          kind: monaco.languages.CompletionItemKind.Keyword,
          insertText: 'def ${1:function_name}(${2:args}):\n    ${3:pass}',
          insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          documentation: 'Define a function'
        },
        {
          label: 'class',
          kind: monaco.languages.CompletionItemKind.Keyword,
          insertText: 'class ${1:ClassName}:\n    ${2:pass}',
          insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          documentation: 'Define a class'
        },
        {
          label: 'if',
          kind: monaco.languages.CompletionItemKind.Keyword,
          insertText: 'if ${1:condition}:\n    ${2:pass}',
          insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          documentation: 'Conditional statement'
        },
        {
          label: 'for',
          kind: monaco.languages.CompletionItemKind.Keyword,
          insertText: 'for ${1:item} in ${2:iterable}:\n    ${3:pass}',
          insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          documentation: 'For loop'
        },
        {
          label: 'while',
          kind: monaco.languages.CompletionItemKind.Keyword,
          insertText: 'while ${1:condition}:\n    ${2:pass}',
          insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          documentation: 'While loop'
        },
        {
          label: 'try',
          kind: monaco.languages.CompletionItemKind.Keyword,
          insertText: 'try:\n    ${1:pass}\nexcept ${2:Exception} as ${3:e}:\n    ${4:pass}',
          insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          documentation: 'Try-except block'
        },
        // 量化交易相关
        {
          label: 'import pandas',
          kind: monaco.languages.CompletionItemKind.Module,
          insertText: 'import pandas as pd',
          documentation: 'Import pandas library'
        },
        {
          label: 'import numpy',
          kind: monaco.languages.CompletionItemKind.Module,
          insertText: 'import numpy as np',
          documentation: 'Import numpy library'
        },
        {
          label: 'import matplotlib',
          kind: monaco.languages.CompletionItemKind.Module,
          insertText: 'import matplotlib.pyplot as plt',
          documentation: 'Import matplotlib library'
        }
      ]

      return { suggestions }
    }
  })

  // 配置Python语法检查
  monaco.languages.registerCodeLensProvider('python', {
    provideCodeLenses: (model) => {
      const lenses: monaco.languages.CodeLens[] = []
      const lines = model.getLinesContent()
      
      lines.forEach((line, index) => {
        // 检查函数定义
        if (line.trim().startsWith('def ')) {
          lenses.push({
            range: {
              startLineNumber: index + 1,
              startColumn: 1,
              endLineNumber: index + 1,
              endColumn: line.length + 1
            },
            command: {
              id: 'editor.action.showHover',
              title: '函数定义',
              arguments: []
            }
          })
        }
      })
      
      return { lenses }
    }
  })
}

// 工具栏方法
const handleLanguageChange = (language: string) => {
  if (editor) {
    monaco.editor.setModelLanguage(editor.getModel()!, language)
    
    if (language === 'python') {
      configurePythonLanguage()
    }
  }
}

const handleThemeChange = (theme: string) => {
  if (editor) {
    monaco.editor.setTheme(theme)
  }
}

const formatCode = async () => {
  if (!editor || !canFormat.value) return
  
  try {
    await editor.getAction('editor.action.formatDocument')?.run()
    ElMessage.success('代码格式化完成')
  } catch (error) {
    ElMessage.error('代码格式化失败')
  }
}

const findAndReplace = () => {
  if (editor) {
    editor.getAction('actions.find')?.run()
  }
}

const toggleMinimap = () => {
  if (editor) {
    const currentOptions = editor.getOptions()
    const minimapEnabled = currentOptions.get(monaco.editor.EditorOption.minimap).enabled
    
    editor.updateOptions({
      minimap: {
        enabled: !minimapEnabled
      }
    })
  }
}

const handleCommand = (command: string) => {
  if (!editor) return
  
  switch (command) {
    case 'undo':
      editor.getAction('undo')?.run()
      break
    case 'redo':
      editor.getAction('redo')?.run()
      break
    case 'selectAll':
      editor.getAction('editor.action.selectAll')?.run()
      break
    case 'copy':
      editor.getAction('editor.action.clipboardCopyAction')?.run()
      break
    case 'paste':
      editor.getAction('editor.action.clipboardPasteAction')?.run()
      break
    case 'toggleWordWrap':
      editor.getAction('editor.action.toggleWordWrap')?.run()
      break
    case 'toggleWhitespace':
      editor.getAction('editor.action.toggleRenderWhitespace')?.run()
      break
  }
}

// 公开方法
const getValue = () => {
  return editor?.getValue() || ''
}

const setValue = (value: string) => {
  if (editor) {
    editor.setValue(value)
  }
}

const insertText = (text: string) => {
  if (editor) {
    const selection = editor.getSelection()
    if (selection) {
      editor.executeEdits('', [{
        range: selection,
        text: text
      }])
    }
  }
}

const focus = () => {
  if (editor) {
    editor.focus()
  }
}

const resize = () => {
  if (editor) {
    editor.layout()
  }
}

const dispose = () => {
  if (editor) {
    editor.dispose()
    editor = null
  }
}

// 暴露方法
defineExpose({
  getValue,
  setValue,
  insertText,
  focus,
  resize,
  dispose,
  editor: () => editor
})

// 生命周期
onMounted(async () => {
  await nextTick()
  await initEditor()
})

onUnmounted(() => {
  dispose()
})

// 监听属性变化
watch(() => props.modelValue, (newValue) => {
  if (editor && editor.getValue() !== newValue) {
    editor.setValue(newValue)
  }
})

watch(() => props.language, (newLanguage) => {
  currentLanguage.value = newLanguage
  handleLanguageChange(newLanguage)
})

watch(() => props.theme, (newTheme) => {
  currentTheme.value = newTheme
  handleThemeChange(newTheme)
})

watch(() => props.readonly, (readonly) => {
  if (editor) {
    editor.updateOptions({ readOnly: readonly })
  }
})
</script>

<style lang="scss" scoped>
.monaco-editor-container {
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  overflow: hidden;
  
  .editor-toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 12px;
    background: var(--el-fill-color-light);
    border-bottom: 1px solid var(--el-border-color);
    
    .toolbar-left {
      display: flex;
      align-items: center;
    }
    
    .toolbar-right {
      display: flex;
      align-items: center;
    }
  }
  
  .editor-container {
    width: 100%;
    overflow: hidden;
  }
  
  .editor-status {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 4px 12px;
    background: var(--el-fill-color-light);
    border-top: 1px solid var(--el-border-color);
    font-size: 12px;
    color: var(--el-text-color-secondary);
    
    .status-left,
    .status-right {
      display: flex;
      align-items: center;
    }
    
    .status-item {
      margin-right: 16px;
      
      &:last-child {
        margin-right: 0;
      }
    }
  }
}

// Monaco Editor 样式覆盖
:deep(.monaco-editor) {
  .margin {
    background-color: var(--el-fill-color-lighter);
  }
  
  .monaco-editor-background {
    background-color: var(--el-bg-color);
  }
  
  .mtk1 {
    color: var(--el-text-color-primary);
  }
}
</style>