<template>
  <div class="layout-settings">
    <el-card class="settings-card">
      <template #header>
        <div class="card-header">
          <el-icon><Grid /></el-icon>
          <span>布局设置</span>
        </div>
      </template>
      
      <div class="settings-content">
        <!-- 布局模式 -->
        <div class="setting-group">
          <h4 class="group-title">布局模式</h4>
          <el-radio-group v-model="layoutConfig.mode" @change="handleLayoutModeChange">
            <el-radio-button label="fluid">
              <el-icon><FullScreen /></el-icon>
              流式布局
            </el-radio-button>
            <el-radio-button label="boxed">
              <el-icon><Monitor /></el-icon>
              盒式布局
            </el-radio-button>
            <el-radio-button label="fixed">
              <el-icon><Lock /></el-icon>
              固定布局
            </el-radio-button>
          </el-radio-group>
          <p class="setting-description">
            流式布局适应屏幕宽度，盒式布局有最大宽度限制，固定布局宽度不变
          </p>
        </div>
        
        <!-- 侧边栏设置 -->
        <div class="setting-group">
          <h4 class="group-title">侧边栏设置</h4>
          
          <div class="setting-item">
            <label class="setting-label">侧边栏位置</label>
            <el-radio-group v-model="layoutConfig.sidebarPosition" @change="handleSidebarPositionChange">
              <el-radio-button label="left">左侧</el-radio-button>
              <el-radio-button label="right">右侧</el-radio-button>
            </el-radio-group>
          </div>
          
          <div class="setting-item">
            <label class="setting-label">默认状态</label>
            <el-switch
              v-model="layoutConfig.sidebarCollapsed"
              @change="handleSidebarCollapsedChange"
              active-text="折叠"
              inactive-text="展开"
            />
          </div>
          
          <div class="setting-item">
            <label class="setting-label">侧边栏宽度: {{ layoutConfig.sidebarWidth }}px</label>
            <el-slider
              v-model="layoutConfig.sidebarWidth"
              :min="200"
              :max="400"
              :step="20"
              @change="handleSidebarWidthChange"
            />
          </div>
        </div>
        
        <!-- 头部设置 -->
        <div class="setting-group">
          <h4 class="group-title">头部设置</h4>
          
          <div class="setting-item">
            <label class="setting-label">头部样式</label>
            <el-radio-group v-model="layoutConfig.headerStyle" @change="handleHeaderStyleChange">
              <el-radio-button label="fixed">固定</el-radio-button>
              <el-radio-button label="static">静态</el-radio-button>
              <el-radio-button label="hidden">隐藏</el-radio-button>
            </el-radio-group>
          </div>
          
          <div class="setting-item" v-if="layoutConfig.headerStyle !== 'hidden'">
            <label class="setting-label">头部高度: {{ layoutConfig.headerHeight }}px</label>
            <el-slider
              v-model="layoutConfig.headerHeight"
              :min="50"
              :max="80"
              :step="5"
              @change="handleHeaderHeightChange"
            />
          </div>
        </div>
        
        <!-- 底部设置 -->
        <div class="setting-group">
          <h4 class="group-title">底部设置</h4>
          
          <div class="setting-item">
            <label class="setting-label">底部样式</label>
            <el-radio-group v-model="layoutConfig.footerStyle" @change="handleFooterStyleChange">
              <el-radio-button label="fixed">固定</el-radio-button>
              <el-radio-button label="static">静态</el-radio-button>
              <el-radio-button label="hidden">隐藏</el-radio-button>
            </el-radio-group>
          </div>
          
          <div class="setting-item" v-if="layoutConfig.footerStyle !== 'hidden'">
            <label class="setting-label">底部高度: {{ layoutConfig.footerHeight }}px</label>
            <el-slider
              v-model="layoutConfig.footerHeight"
              :min="30"
              :max="60"
              :step="5"
              @change="handleFooterHeightChange"
            />
          </div>
        </div>
        
        <!-- 内容区域设置 -->
        <div class="setting-group">
          <h4 class="group-title">内容区域</h4>
          
          <div class="setting-item">
            <label class="setting-label">内容边距: {{ layoutConfig.contentPadding }}px</label>
            <el-slider
              v-model="layoutConfig.contentPadding"
              :min="8"
              :max="32"
              :step="4"
              @change="handleContentPaddingChange"
            />
          </div>
          
          <div class="setting-item" v-if="layoutConfig.mode === 'boxed'">
            <label class="setting-label">最大宽度: {{ layoutConfig.maxWidth }}px</label>
            <el-slider
              v-model="layoutConfig.maxWidth"
              :min="1000"
              :max="1800"
              :step="100"
              @change="handleMaxWidthChange"
            />
          </div>
          
          <div class="setting-item">
            <label class="setting-label">显示面包屑</label>
            <el-switch
              v-model="layoutConfig.showBreadcrumb"
              @change="handleShowBreadcrumbChange"
            />
          </div>
          
          <div class="setting-item">
            <label class="setting-label">显示标签页</label>
            <el-switch
              v-model="layoutConfig.showTabs"
              @change="handleShowTabsChange"
            />
          </div>
        </div>
        
        <!-- 布局模板 -->
        <div class="setting-group">
          <h4 class="group-title">布局模板</h4>
          <div class="layout-templates">
            <div
              v-for="(template, name) in LAYOUT_TEMPLATES"
              :key="name"
              class="layout-template"
              @click="handleApplyTemplate(name)"
            >
              <div class="template-preview">
                <div class="template-layout">
                  <div class="template-header" :style="getTemplateHeaderStyle(template)"></div>
                  <div class="template-body">
                    <div class="template-sidebar" :style="getTemplateSidebarStyle(template)"></div>
                    <div class="template-content"></div>
                  </div>
                  <div class="template-footer" :style="getTemplateFooterStyle(template)"></div>
                </div>
              </div>
              <div class="template-info">
                <h5 class="template-name">{{ getTemplateName(name) }}</h5>
                <p class="template-description">{{ getTemplateDescription(name) }}</p>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 布局预览 -->
        <div class="setting-group">
          <h4 class="group-title">布局预览</h4>
          <div class="layout-preview">
            <div class="preview-layout" :style="getPreviewStyle()">
              <div class="preview-header" v-if="layoutConfig.headerStyle !== 'hidden'">
                Header
              </div>
              <div class="preview-body">
                <div class="preview-sidebar" v-if="!isMobile">
                  {{ layoutConfig.sidebarCollapsed ? 'S' : 'Sidebar' }}
                </div>
                <div class="preview-content">
                  <div v-if="layoutConfig.showBreadcrumb" class="preview-breadcrumb">
                    面包屑导航
                  </div>
                  <div v-if="layoutConfig.showTabs" class="preview-tabs">
                    标签页
                  </div>
                  <div class="preview-main">
                    主要内容区域
                  </div>
                </div>
              </div>
              <div class="preview-footer" v-if="layoutConfig.footerStyle !== 'hidden'">
                Footer
              </div>
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
      title="导入布局配置"
      width="500px"
    >
      <el-input
        v-model="importConfigText"
        type="textarea"
        :rows="10"
        placeholder="请粘贴布局配置JSON"
      />
      <template #footer>
        <el-button @click="importDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmImport">确认导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Grid, FullScreen, Monitor, Lock } from '@element-plus/icons-vue'
import { useLayout, type LayoutMode, type SidebarPosition, type HeaderStyle, type FooterStyle } from '@/composables/useLayout'

const {
  layoutConfig,
  isMobile,
  setLayoutMode,
  setSidebarPosition,
  setSidebarWidth,
  setHeaderStyle,
  setFooterStyle,
  applyLayoutTemplate,
  resetLayoutConfig,
  exportLayoutConfig,
  importLayoutConfig,
  LAYOUT_TEMPLATES
} = useLayout()

// 导入对话框
const importDialogVisible = ref(false)
const importConfigText = ref('')

// 模板名称映射
const getTemplateName = (name: string) => {
  const names: Record<string, string> = {
    default: '默认布局',
    compact: '紧凑布局',
    wide: '宽屏布局'
  }
  return names[name] || name
}

// 模板描述映射
const getTemplateDescription = (name: string) => {
  const descriptions: Record<string, string> = {
    default: '标准的布局配置，适合大多数用户',
    compact: '紧凑的布局，节省屏幕空间',
    wide: '宽屏优化的布局，适合大屏幕'
  }
  return descriptions[name] || ''
}

// 获取模板预览样式
const getTemplateHeaderStyle = (template: any) => {
  return {
    height: template.headerStyle === 'hidden' ? '0' : '12px',
    display: template.headerStyle === 'hidden' ? 'none' : 'block'
  }
}

const getTemplateSidebarStyle = (template: any) => {
  return {
    width: template.sidebarCollapsed ? '8px' : '24px',
    left: template.sidebarPosition === 'right' ? 'auto' : '0',
    right: template.sidebarPosition === 'right' ? '0' : 'auto'
  }
}

const getTemplateFooterStyle = (template: any) => {
  return {
    height: template.footerStyle === 'hidden' ? '0' : '8px',
    display: template.footerStyle === 'hidden' ? 'none' : 'block'
  }
}

// 获取预览样式
const getPreviewStyle = () => {
  return {
    maxWidth: layoutConfig.value.mode === 'boxed' ? `${Math.min(layoutConfig.value.maxWidth, 400)}px` : '100%'
  }
}

// 事件处理
const handleLayoutModeChange = (mode: LayoutMode) => {
  setLayoutMode(mode)
}

const handleSidebarPositionChange = (position: SidebarPosition) => {
  setSidebarPosition(position)
}

const handleSidebarCollapsedChange = () => {
  // 这个在useLayout中已经处理
}

const handleSidebarWidthChange = (width: number) => {
  setSidebarWidth(width)
}

const handleHeaderStyleChange = (style: HeaderStyle) => {
  setHeaderStyle(style)
}

const handleHeaderHeightChange = () => {
  // 自动保存
}

const handleFooterStyleChange = (style: FooterStyle) => {
  setFooterStyle(style)
}

const handleFooterHeightChange = () => {
  // 自动保存
}

const handleContentPaddingChange = () => {
  // 自动保存
}

const handleMaxWidthChange = () => {
  // 自动保存
}

const handleShowBreadcrumbChange = () => {
  // 自动保存
}

const handleShowTabsChange = () => {
  // 自动保存
}

const handleApplyTemplate = async (templateName: string) => {
  try {
    await ElMessageBox.confirm(`确定要应用"${getTemplateName(templateName)}"布局模板吗？`, '确认应用', {
      type: 'info'
    })
    await applyLayoutTemplate(templateName as any)
    ElMessage.success('布局模板已应用')
  } catch {
    // 用户取消
  }
}

const handleReset = async () => {
  try {
    await ElMessageBox.confirm('确定要重置为默认布局配置吗？', '确认重置', {
      type: 'warning'
    })
    await resetLayoutConfig()
    ElMessage.success('布局配置已重置')
  } catch {
    // 用户取消
  }
}

const handleExport = () => {
  const config = exportLayoutConfig()
  const configText = JSON.stringify(config, null, 2)
  
  // 创建下载链接
  const blob = new Blob([configText], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `layout-config-${new Date().toISOString().split('T')[0]}.json`
  link.click()
  URL.revokeObjectURL(url)
  
  ElMessage.success('布局配置已导出')
}

const handleImport = () => {
  importConfigText.value = ''
  importDialogVisible.value = true
}

const confirmImport = async () => {
  try {
    const config = JSON.parse(importConfigText.value)
    const success = await importLayoutConfig(config)
    
    if (success) {
      ElMessage.success('布局配置导入成功')
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
.layout-settings {
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

.setting-item {
  margin-bottom: 20px;
}

.setting-label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: var(--color-text);
}

.setting-description {
  margin: 8px 0 0 0;
  font-size: 12px;
  color: var(--color-text-secondary);
}

/* 布局模板 */
.layout-templates {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.layout-template {
  border: 2px solid var(--color-border);
  border-radius: var(--border-radius);
  padding: 16px;
  cursor: pointer;
  transition: all var(--transition-duration);
}

.layout-template:hover {
  border-color: var(--color-primary);
  transform: translateY(-2px);
}

.template-preview {
  margin-bottom: 12px;
}

.template-layout {
  width: 100%;
  height: 80px;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.template-header {
  background: var(--color-primary);
  opacity: 0.8;
}

.template-body {
  flex: 1;
  display: flex;
  position: relative;
}

.template-sidebar {
  background: var(--color-secondary);
  opacity: 0.6;
  position: absolute;
  top: 0;
  bottom: 0;
}

.template-content {
  flex: 1;
  background: var(--color-surface);
  margin-left: 24px;
}

.template-footer {
  background: var(--color-info);
  opacity: 0.6;
}

.template-info {
  text-align: center;
}

.template-name {
  margin: 0 0 4px 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
}

.template-description {
  margin: 0;
  font-size: 12px;
  color: var(--color-text-secondary);
}

/* 布局预览 */
.layout-preview {
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius);
  padding: 16px;
  background: var(--color-surface);
}

.preview-layout {
  width: 100%;
  height: 200px;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  margin: 0 auto;
}

.preview-header {
  height: 30px;
  background: var(--color-primary);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 500;
}

.preview-body {
  flex: 1;
  display: flex;
  position: relative;
}

.preview-sidebar {
  width: 60px;
  background: var(--color-secondary);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 500;
}

.preview-content {
  flex: 1;
  background: var(--color-background);
  display: flex;
  flex-direction: column;
}

.preview-breadcrumb {
  height: 20px;
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  padding: 0 8px;
  font-size: 10px;
  color: var(--color-text-secondary);
}

.preview-tabs {
  height: 24px;
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  padding: 0 8px;
  font-size: 10px;
  color: var(--color-text-secondary);
}

.preview-main {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  color: var(--color-text-secondary);
}

.preview-footer {
  height: 20px;
  background: var(--color-info);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 500;
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
  .layout-templates {
    grid-template-columns: 1fr;
  }
  
  .setting-actions {
    flex-direction: column;
  }
}
</style>