<template>
  <el-dialog
    v-model="visible"
    title="图表配置"
    width="600px"
    @close="handleClose"
  >
    <el-form :model="config" label-width="120px">
      <!-- 主图指标 -->
      <el-form-item label="主图指标">
        <el-checkbox-group v-model="config.indicators">
          <el-checkbox label="ma5">MA5</el-checkbox>
          <el-checkbox label="ma10">MA10</el-checkbox>
          <el-checkbox label="ma20">MA20</el-checkbox>
          <el-checkbox label="ma60">MA60</el-checkbox>
          <el-checkbox label="ema12">EMA12</el-checkbox>
          <el-checkbox label="ema26">EMA26</el-checkbox>
          <el-checkbox label="bollinger">布林带</el-checkbox>
        </el-checkbox-group>
      </el-form-item>

      <!-- 图表主题 -->
      <el-form-item label="图表主题">
        <el-radio-group v-model="config.theme">
          <el-radio label="light">浅色主题</el-radio>
          <el-radio label="dark">深色主题</el-radio>
        </el-radio-group>
      </el-form-item>

      <!-- 显示选项 -->
      <el-form-item label="显示选项">
        <el-checkbox v-model="config.showVolume">显示成交量</el-checkbox>
        <el-checkbox v-model="config.showGrid">显示网格</el-checkbox>
        <el-checkbox v-model="config.showCrosshair">显示十字线</el-checkbox>
        <el-checkbox v-model="config.showLegend">显示图例</el-checkbox>
      </el-form-item>

      <!-- 颜色配置 -->
      <el-form-item label="颜色配置">
        <div class="color-config">
          <div class="color-item">
            <span>上涨颜色:</span>
            <el-color-picker v-model="config.colors.up" />
          </div>
          <div class="color-item">
            <span>下跌颜色:</span>
            <el-color-picker v-model="config.colors.down" />
          </div>
          <div class="color-item">
            <span>背景颜色:</span>
            <el-color-picker v-model="config.colors.background" />
          </div>
        </div>
      </el-form-item>

      <!-- 预设配置 -->
      <el-form-item label="预设配置">
        <el-select v-model="selectedPreset" placeholder="选择预设配置" @change="handlePresetChange">
          <el-option label="默认配置" value="default" />
          <el-option label="简洁模式" value="simple" />
          <el-option label="专业模式" value="professional" />
          <el-option label="技术分析" value="technical" />
        </el-select>
      </el-form-item>

      <!-- 保存配置 -->
      <el-form-item label="保存配置">
        <el-input
          v-model="configName"
          placeholder="输入配置名称"
          style="width: 200px; margin-right: 12px"
        />
        <el-button type="primary" @click="handleSaveConfig">保存为预设</el-button>
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button @click="handleReset">重置</el-button>
        <el-button type="primary" @click="handleConfirm">确定</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { saveChartConfig } from '@/api/technicalAnalysis'

interface Props {
  modelValue: boolean
  currentConfig: any
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'save', config: any): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 响应式数据
const visible = ref(false)
const selectedPreset = ref('')
const configName = ref('')

// 默认配置
const defaultConfig = {
  indicators: ['ma5', 'ma10', 'ma20'],
  theme: 'light',
  showVolume: true,
  showGrid: true,
  showCrosshair: true,
  showLegend: true,
  colors: {
    up: '#ef232a',
    down: '#14b143',
    background: '#ffffff'
  }
}

const config = ref({ ...defaultConfig })

// 预设配置
const presetConfigs = {
  default: {
    indicators: ['ma5', 'ma10', 'ma20'],
    theme: 'light',
    showVolume: true,
    showGrid: true,
    showCrosshair: true,
    showLegend: true,
    colors: {
      up: '#ef232a',
      down: '#14b143',
      background: '#ffffff'
    }
  },
  simple: {
    indicators: ['ma20'],
    theme: 'light',
    showVolume: false,
    showGrid: false,
    showCrosshair: true,
    showLegend: false,
    colors: {
      up: '#ef232a',
      down: '#14b143',
      background: '#ffffff'
    }
  },
  professional: {
    indicators: ['ma5', 'ma10', 'ma20', 'ma60', 'bollinger'],
    theme: 'dark',
    showVolume: true,
    showGrid: true,
    showCrosshair: true,
    showLegend: true,
    colors: {
      up: '#ef232a',
      down: '#14b143',
      background: '#1e1e1e'
    }
  },
  technical: {
    indicators: ['ma5', 'ma10', 'ma20', 'ema12', 'ema26', 'bollinger'],
    theme: 'light',
    showVolume: true,
    showGrid: true,
    showCrosshair: true,
    showLegend: true,
    colors: {
      up: '#ef232a',
      down: '#14b143',
      background: '#ffffff'
    }
  }
}

// 监听 modelValue 变化
watch(() => props.modelValue, (newValue) => {
  visible.value = newValue
  if (newValue) {
    config.value = { ...props.currentConfig }
  }
})

// 监听 visible 变化
watch(visible, (newValue) => {
  emit('update:modelValue', newValue)
})

// 处理预设配置变化
const handlePresetChange = (preset: string) => {
  if (presetConfigs[preset as keyof typeof presetConfigs]) {
    config.value = { ...presetConfigs[preset as keyof typeof presetConfigs] }
  }
}

// 保存配置为预设
const handleSaveConfig = async () => {
  if (!configName.value.trim()) {
    ElMessage.warning('请输入配置名称')
    return
  }

  try {
    await saveChartConfig(configName.value, config.value)
    ElMessage.success('配置保存成功')
    configName.value = ''
  } catch (error) {
    console.error('保存配置失败:', error)
    ElMessage.error('保存配置失败')
  }
}

// 重置配置
const handleReset = () => {
  config.value = { ...defaultConfig }
  selectedPreset.value = ''
}

// 确认配置
const handleConfirm = () => {
  emit('save', { ...config.value })
  visible.value = false
}

// 关闭对话框
const handleClose = () => {
  visible.value = false
}
</script>

<style scoped>
.color-config {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.color-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.color-item span {
  width: 80px;
  font-size: 14px;
}

.dialog-footer {
  text-align: right;
}
</style>