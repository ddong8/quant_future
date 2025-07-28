<template>
  <div class="code-editor">
    <div ref="editorContainer" class="editor-container"></div>
    <div v-if="!editorLoaded" class="fallback-editor">
      <el-input
        v-model="content"
        type="textarea"
        :rows="20"
        placeholder="代码编辑器加载中..."
        @input="handleInput"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'

interface Props {
  modelValue: string
  language?: string
  theme?: string
  readonly?: boolean
}

interface Emits {
  (e: 'update:modelValue', value: string): void
  (e: 'change', value: string): void
}

const props = withDefaults(defineProps<Props>(), {
  language: 'python',
  theme: 'vs-dark',
  readonly: false
})

const emit = defineEmits<Emits>()

const editorContainer = ref<HTMLElement>()
const editorLoaded = ref(false)
const content = ref(props.modelValue)

let monaco: any = null
let editor: any = null

const initMonacoEditor = async () => {
  try {
    // 动态导入 Monaco Editor
    monaco = await import('monaco-editor')
    
    if (!editorContainer.value) return
    
    // 创建编辑器实例
    editor = monaco.editor.create(editorContainer.value, {
      value: props.modelValue,
      language: props.language,
      theme: props.theme,
      readOnly: props.readonly,
      automaticLayout: true,
      minimap: { enabled: true },
      scrollBeyondLastLine: false,
      fontSize: 14,
      tabSize: 4,
      insertSpaces: true,
      wordWrap: 'on',
      lineNumbers: 'on',
      glyphMargin: true,
      folding: true,
      lineDecorationsWidth: 10,
      lineNumbersMinChars: 3
    })

    // 监听内容变化
    editor.onDidChangeModelContent(() => {
      const value = editor.getValue()
      emit('update:modelValue', value)
      emit('change', value)
    })
    
    editorLoaded.value = true
  } catch (error) {
    console.error('Failed to load Monaco Editor:', error)
    editorLoaded.value = false
  }
}

const handleInput = (value: string) => {
  emit('update:modelValue', value)
  emit('change', value)
}

// 监听props变化
watch(() => props.modelValue, (newValue) => {
  if (editor && editor.getValue() !== newValue) {
    editor.setValue(newValue)
  }
  content.value = newValue
})

watch(() => props.language, (newLanguage) => {
  if (editor && monaco) {
    monaco.editor.setModelLanguage(editor.getModel(), newLanguage)
  }
})

watch(() => props.theme, (newTheme) => {
  if (editor && monaco) {
    monaco.editor.setTheme(newTheme)
  }
})

// 暴露方法
const setValue = (value: string) => {
  if (editor) {
    editor.setValue(value)
  } else {
    content.value = value
  }
}

const getValue = () => {
  return editor ? editor.getValue() : content.value
}

const focus = () => {
  if (editor) {
    editor.focus()
  }
}

defineExpose({
  setValue,
  getValue,
  focus
})

onMounted(async () => {
  await nextTick()
  await initMonacoEditor()
})

onUnmounted(() => {
  if (editor) {
    editor.dispose()
  }
})
</script>

<style scoped lang="scss">
.code-editor {
  position: relative;
  width: 100%;
  height: 100%;
  
  .editor-container {
    width: 100%;
    height: 100%;
  }
  
  .fallback-editor {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: #1e1e1e;
    
    :deep(.el-textarea__inner) {
      background: #1e1e1e;
      color: #d4d4d4;
      border: none;
      font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
      font-size: 14px;
      line-height: 1.5;
      resize: none;
    }
  }
}
</style>