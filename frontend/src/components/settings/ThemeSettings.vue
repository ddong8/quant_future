<template>
  <div class="theme-settings">
    <el-card class="settings-card">
      <template #header>
        <div class="card-header">
          <el-icon><Palette /></el-icon>
          <span>主题设置</span>
        </div>
      </template>
      
      <div class="settings-content">
        <!-- 主题模式 -->
        <div class="setting-group">
          <h4 class="group-title">主题模式</h4>
          <el-radio-group v-model="themeConfig.mode" @change="handleThemeModeChange">
            <el-radio-button label="light">
              <el-icon><Sunny /></el-icon>
              浅色
            </el-radio-button>
            <el-radio-button label="dark">
              <el-icon><Moon /></el-icon>
              深色
            </el-radio-button>
            <el-radio-button label="auto">
              <el-icon><Monitor /></el-icon>
              自动
            </el-radio-button>
          </el-radio-group>
        </div>
        
        <!-- 颜色方案 -->
        <div class="setting-group">
          <h4 class="group-title">颜色方案</h4>
          <div class="color-schemes">
            <div
              v-for="(colors, scheme) in COLOR_SCHEMES"
              :key="scheme"
              class="color-scheme"
              :class="{ active: themeConfig.colorScheme === scheme }"
              @click="handleColorSchemeChange(scheme)"
            >
              <div class="scheme-preview">
                <div
                  class="color-dot primary"
                  :style="{ backgroundColor: colors.primary }"
                ></div>
                <div
                  class="color-dot secondary"
                  :style="{ backgroundColor: colors.secondary }"
                ></div>
                <div
                  class="color-dot success"
                  :style="{ backgroundColor: colors.success }"
                ></div>
              </div>
              <span class="scheme-name">{{ getSchemeDisplayName(scheme) }}</span>
            </div>
          </div>
        </div>
        
        <!-- 字体大小 -->
        <div class="setting-group">
          <h4 class="group-title">字体大小</h4>
          <div class="font-size-control">
            <el-slider
              v-model="themeConfig.fontSize"
              :min="12"
              :max="20"
              :step="1"
              :marks="fontSizeMarks"
              @change="handleFontSizeChange"
            />
            <div class="font-preview" :style="{ fontSize: themeConfig.fontSize + 'px' }">
              示例文字 Sample Text
            </div>
          </div>
        </div>
        
        <!-- 边框圆角 -->
        <div class="setting-group">
          <h4 class="group-title">边框圆角</h4>
          <el-slider
            v-model="themeConfig.borderRadius"
            :min="0"
            :max="12"
            :step="1"
            :marks="borderRadiusMarks"
            @change="handleBorderRadiusChange"
          />
          <div class="border-preview">
            <div
              class="preview-box"
              :style="{ borderRadius: themeConfig.borderRadius + 'px' }"
            >
              圆角预览
            </div>
          </div>
        </div>
        
        <!-- 界面选项 -->
        <div class="setting-group">
          <h4 class="group-title">界面选项</h4>
          <div class="interface-options">
            <el-switch
              v-model="themeConfig.compactMode"
              @change="handleCompactModeChange"
            >
              <template #active-text>紧凑模式</template>
            </el-switch>
            
            <el-switch
              v-model="themeConfig.highContrast"
              @change="handleHighContrastChange"
            >
              <template #active-text>高对比度</template>
            </el-switch>
            
            <el-switch
              v-model="themeConfig.reducedMotion"
              @change="handleReducedMotionChange"
            >
              <template #active-text>减少动画</template>
            </el-switch>
          </div>
        </div>
        
        <!-- 预览区域 -->
        <div class="setting-group">
          <h4 class="group-title">预览效果</h4>
          <div class="theme-preview">
            <div class="preview-header">
              <div class="preview-title">界面预览</div>
              <div class="preview-actions">
                <el-button size="small" type="primary">主要按钮</el-button>
                <el-button size="small">次要按钮</el-button>
              </div>
            </div>
            <div class="preview-content">
              <el-card class="preview-card">
                <p>这是一个示例卡片，展示当前主题的效果。</p>
                <el-tag type="success">成功</el-tag>
                <el-tag type="warning">警告</el-tag>
                <el-tag type="danger">错误</el-tag>
              </el-card>
            </div>
          </div>
        </div>
        
        <!-- 操作按钮 -->
        <div class="setting-actions">
          <el-button @click="handleReset">重置默认</el-button>
          <el-button @click="handleExport">导出配置</el-button>
          <el-button @click="handleImport">导入配置</el-button>
        </div>
      </div>
    </el-card>
    
    <!-- 导入配置对话框 -->
    <el-dialog
      v-model="importDialogVisible"
      title="导入主题配置"
      width="500px"
    >
      <el-input
        v-model="importConfigText"
        type="textarea"
        :rows="10"
        placeholder="请粘贴主题配置JSON"
      />
      <template #footer>
        <el-button @click="importDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmImport">确认导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Palette, Sunny, Moon, Monitor } from '@element-plus/icons-vue'
import { useTheme, type ColorScheme } from '@/composables/useTheme'

const {
  themeConfig,
  setThemeMode,
  setColorScheme,
  setFontSize,
  setBorderRadius,
  toggleCompactMode,
  toggleHighContrast,
  toggleReducedMotion,
  resetThemeConfig,
  exportThemeConfig,
  importThemeConfig,
  COLOR_SCHEMES
} = useTheme()

// 导入对话框
const importDialogVisible = ref(false)
const importConfigText = ref('')

// 字体大小标记
const fontSizeMarks = {
  12: '小',
  14: '中',
  16: '大',
  18: '特大',
  20: '超大'
}

// 边框圆角标记
const borderRadiusMarks = {
  0: '直角',
  4: '小圆角',
  8: '中圆角',
  12: '大圆角'
}

// 颜色方案显示名称
const getSchemeDisplayName = (scheme: string) => {
  const names: Record<string, string> = {
    default: '默认',
    blue: '蓝色',
    green: '绿色',
    purple: '紫色',
    orange: '橙色'
  }
  return names[scheme] || scheme
}

// 事件处理
const handleThemeModeChange = (mode: string) => {
  setThemeMode(mode as any)
}

const handleColorSchemeChange = (scheme: string) => {
  setColorScheme(scheme as ColorScheme)
}

const handleFontSizeChange = (size: number) => {
  setFontSize(size)
}

const handleBorderRadiusChange = (radius: number) => {
  setBorderRadius(radius)
}

const handleCompactModeChange = () => {
  toggleCompactMode()
}

const handleHighContrastChange = () => {
  toggleHighContrast()
}

const handleReducedMotionChange = () => {
  toggleReducedMotion()
}

const handleReset = async () => {
  try {
    await ElMessageBox.confirm('确定要重置为默认主题配置吗？', '确认重置', {
      type: 'warning'
    })
    await resetThemeConfig()
    ElMessage.success('主题配置已重置')
  } catch {
    // 用户取消
  }
}

const handleExport = () => {
  const config = exportThemeConfig()
  const configText = JSON.stringify(config, null, 2)
  
  // 创建下载链接
  const blob = new Blob([configText], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `theme-config-${new Date().toISOString().split('T')[0]}.json`
  link.click()
  URL.revokeObjectURL(url)
  
  ElMessage.success('主题配置已导出')
}

const handleImport = () => {
  importConfigText.value = ''
  importDialogVisible.value = true
}

const confirmImport = async () => {
  try {
    const config = JSON.parse(importConfigText.value)
    const success = await importThemeConfig(config)
    
    if (success) {
      ElMessage.success('主题配置导入成功')
      importDialogVisible.value = false
    } else {
      ElMessage.error('配置格式不正确或版本不兼容')
    }
  } catch (error) {
    ElMessage.error('配置格式错误，请检查JSON格式')
  }
}
</script>

<style scoped>
.theme-settings {
  max-width: 800px;
}

.settings-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.settings-content {
  padding: 0;
}

.setting-group {
  margin-bottom: 32px;
}

.group-title {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text);
}

/* 颜色方案 */
.color-schemes {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 16px;
}

.color-scheme {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px;
  border: 2px solid var(--color-border);
  border-radius: var(--border-radius);
  cursor: pointer;
  transition: all var(--transition-duration);
}

.color-scheme:hover {
  border-color: var(--color-primary);
  transform: translateY(-2px);
}

.color-scheme.active {
  border-color: var(--color-primary);
  background-color: var(--color-primary);
  color: white;
}

.scheme-preview {
  display: flex;
  gap: 4px;
  margin-bottom: 8px;
}

.color-dot {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  border: 1px solid rgba(0, 0, 0, 0.1);
}

.scheme-name {
  font-size: 14px;
  font-weight: 500;
}

/* 字体大小控制 */
.font-size-control {
  margin-top: 16px;
}

.font-preview {
  margin-top: 16px;
  padding: 12px;
  background: var(--color-surface);
  border-radius: var(--border-radius);
  text-align: center;
  transition: font-size var(--transition-duration);
}

/* 边框预览 */
.border-preview {
  margin-top: 16px;
  display: flex;
  justify-content: center;
}

.preview-box {
  width: 120px;
  height: 60px;
  background: var(--color-primary);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 500;
  transition: border-radius var(--transition-duration);
}

/* 界面选项 */
.interface-options {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 主题预览 */
.theme-preview {
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius);
  overflow: hidden;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
}

.preview-title {
  font-weight: 600;
  color: var(--color-text);
}

.preview-actions {
  display: flex;
  gap: 8px;
}

.preview-content {
  padding: 16px;
}

.preview-card {
  margin: 0;
}

.preview-card p {
  margin: 0 0 12px 0;
  color: var(--color-text-secondary);
}

.preview-card .el-tag {
  margin-right: 8px;
}

/* 操作按钮 */
.setting-actions {
  display: flex;
  gap: 12px;
  padding-top: 24px;
  border-top: 1px solid var(--color-border);
}

/* 响应式 */
@media (max-width: 768px) {
  .color-schemes {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .preview-header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
  
  .setting-actions {
    flex-direction: column;
  }
}
</style>