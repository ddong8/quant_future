<template>
  <div class="settings-preview">
    <el-card class="preview-card">
      <template #header>
        <div class="card-header">
          <el-icon><View /></el-icon>
          <span>实时预览</span>
          <div class="preview-controls">
            <el-button-group size="small">
              <el-button
                :type="previewMode === 'desktop' ? 'primary' : ''"
                @click="setPreviewMode('desktop')"
              >
                <el-icon><Monitor /></el-icon>
                桌面
              </el-button>
              <el-button
                :type="previewMode === 'tablet' ? 'primary' : ''"
                @click="setPreviewMode('tablet')"
              >
                <el-icon><Iphone /></el-icon>
                平板
              </el-button>
              <el-button
                :type="previewMode === 'mobile' ? 'primary' : ''"
                @click="setPreviewMode('mobile')"
              >
                <el-icon><Cellphone /></el-icon>
                手机
              </el-button>
            </el-button-group>
          </div>
        </div>
      </template>
      
      <div class="preview-container">
        <div
          class="preview-frame"
          :class="[`preview-${previewMode}`, { 'preview-loading': isLoading }]"
        >
          <div class="preview-content" :style="previewStyles">
            <!-- 预览头部 -->
            <div
              v-if="layoutConfig.headerStyle !== 'hidden'"
              class="preview-header"
              :style="headerStyles"
            >
              <div class="header-left">
                <div class="logo">Logo</div>
                <div class="nav-items">
                  <span class="nav-item active">仪表板</span>
                  <span class="nav-item">交易</span>
                  <span class="nav-item">分析</span>
                </div>
              </div>
              <div class="header-right">
                <div class="user-info">
                  <el-avatar size="small">U</el-avatar>
                  <span>用户</span>
                </div>
              </div>
            </div>
            
            <!-- 预览主体 -->
            <div class="preview-body" :style="bodyStyles">
              <!-- 侧边栏 -->
              <div
                v-if="showSidebar"
                class="preview-sidebar"
                :class="{ collapsed: layoutConfig.sidebarCollapsed }"
                :style="sidebarStyles"
              >
                <div class="sidebar-menu">
                  <div class="menu-item active">
                    <el-icon><House /></el-icon>
                    <span v-if="!layoutConfig.sidebarCollapsed">首页</span>
                  </div>
                  <div class="menu-item">
                    <el-icon><TrendCharts /></el-icon>
                    <span v-if="!layoutConfig.sidebarCollapsed">交易</span>
                  </div>
                  <div class="menu-item">
                    <el-icon><DataAnalysis /></el-icon>
                    <span v-if="!layoutConfig.sidebarCollapsed">分析</span>
                  </div>
                  <div class="menu-item">
                    <el-icon><Setting /></el-icon>
                    <span v-if="!layoutConfig.sidebarCollapsed">设置</span>
                  </div>
                </div>
              </div>
              
              <!-- 内容区域 -->
              <div class="preview-main" :style="mainStyles">
                <!-- 面包屑 -->
                <div v-if="layoutConfig.showBreadcrumb" class="preview-breadcrumb">
                  <span>首页</span>
                  <el-icon><ArrowRight /></el-icon>
                  <span>仪表板</span>
                </div>
                
                <!-- 标签页 -->
                <div v-if="layoutConfig.showTabs" class="preview-tabs">
                  <div class="tab-item active">仪表板</div>
                  <div class="tab-item">市场分析</div>
                  <div class="tab-item">
                    我的持仓
                    <el-icon><Close /></el-icon>
                  </div>
                </div>
                
                <!-- 内容卡片 -->
                <div class="preview-cards" :style="cardsStyles">
                  <div class="preview-card-item">
                    <h4>总资产</h4>
                    <div class="card-value">¥123,456.78</div>
                    <div class="card-change positive">+2.34%</div>
                  </div>
                  <div class="preview-card-item">
                    <h4>今日盈亏</h4>
                    <div class="card-value">¥1,234.56</div>
                    <div class="card-change positive">+0.98%</div>
                  </div>
                  <div class="preview-card-item">
                    <h4>持仓数量</h4>
                    <div class="card-value">8</div>
                    <div class="card-change">持仓</div>
                  </div>
                </div>
                
                <!-- 图表区域 -->
                <div class="preview-chart">
                  <div class="chart-header">
                    <h4>市场走势</h4>
                    <div class="chart-controls">
                      <el-button-group size="small">
                        <el-button type="primary">1D</el-button>
                        <el-button>1W</el-button>
                        <el-button>1M</el-button>
                      </el-button-group>
                    </div>
                  </div>
                  <div class="chart-content">
                    <div class="chart-placeholder">
                      <el-icon><TrendCharts /></el-icon>
                      <span>图表预览</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 预览底部 -->
            <div
              v-if="layoutConfig.footerStyle !== 'hidden'"
              class="preview-footer"
              :style="footerStyles"
            >
              <div class="footer-content">
                <span>© 2024 交易平台. All rights reserved.</span>
              </div>
            </div>
          </div>
          
          <!-- 加载遮罩 -->
          <div v-if="isLoading" class="preview-loading-mask">
            <el-icon class="loading-icon"><Loading /></el-icon>
            <span>应用设置中...</span>
          </div>
        </div>
        
        <!-- 预览信息 -->
        <div class="preview-info">
          <div class="info-item">
            <span class="info-label">预览模式:</span>
            <span class="info-value">{{ previewModeText }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">屏幕尺寸:</span>
            <span class="info-value">{{ previewSize }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">主题模式:</span>
            <span class="info-value">{{ themeConfig.mode }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">布局模式:</span>
            <span class="info-value">{{ layoutConfig.mode }}</span>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import {
  View, Monitor, Iphone, Cellphone, House, TrendCharts,
  DataAnalysis, Setting, ArrowRight, Close, Loading
} from '@element-plus/icons-vue'
import { useTheme } from '@/composables/useTheme'
import { useLayout } from '@/composables/useLayout'

const { themeConfig, themeColors } = useTheme()
const { layoutConfig } = useLayout()

// 预览模式
type PreviewMode = 'desktop' | 'tablet' | 'mobile'
const previewMode = ref<PreviewMode>('desktop')
const isLoading = ref(false)

// 预览模式文本
const previewModeText = computed(() => {
  const texts = {
    desktop: '桌面端',
    tablet: '平板端',
    mobile: '移动端'
  }
  return texts[previewMode.value]
})

// 预览尺寸
const previewSize = computed(() => {
  const sizes = {
    desktop: '1200x800',
    tablet: '768x1024',
    mobile: '375x667'
  }
  return sizes[previewMode.value]
})

// 是否显示侧边栏
const showSidebar = computed(() => {
  return previewMode.value !== 'mobile' || !layoutConfig.value.sidebarCollapsed
})

// 预览样式
const previewStyles = computed(() => {
  return {
    '--preview-primary': themeColors.value.primary,
    '--preview-background': themeColors.value.background,
    '--preview-surface': themeColors.value.surface,
    '--preview-text': themeColors.value.text,
    '--preview-text-secondary': themeColors.value.textSecondary,
    '--preview-border': themeColors.value.border,
    '--preview-shadow': themeColors.value.shadow,
    '--preview-font-size': `${themeConfig.value.fontSize}px`,
    '--preview-border-radius': `${themeConfig.value.borderRadius}px`,
    '--preview-spacing': themeConfig.value.compactMode ? '8px' : '16px'
  }
})

// 头部样式
const headerStyles = computed(() => {
  return {
    height: `${Math.round(layoutConfig.value.headerHeight * 0.6)}px`,
    position: layoutConfig.value.headerStyle === 'fixed' ? 'sticky' : 'static',
    top: layoutConfig.value.headerStyle === 'fixed' ? '0' : 'auto'
  }
})

// 主体样式
const bodyStyles = computed(() => {
  let marginTop = 0
  let marginBottom = 0
  
  if (layoutConfig.value.headerStyle === 'fixed') {
    marginTop = Math.round(layoutConfig.value.headerHeight * 0.6)
  }
  if (layoutConfig.value.footerStyle === 'fixed') {
    marginBottom = Math.round(layoutConfig.value.footerHeight * 0.6)
  }
  
  return {
    marginTop: `${marginTop}px`,
    marginBottom: `${marginBottom}px`
  }
})

// 侧边栏样式
const sidebarStyles = computed(() => {
  const width = layoutConfig.value.sidebarCollapsed 
    ? Math.round(layoutConfig.value.sidebarWidth * 0.25)
    : Math.round(layoutConfig.value.sidebarWidth * 0.4)
  
  return {
    width: `${width}px`,
    [layoutConfig.value.sidebarPosition]: '0'
  }
})

// 主内容样式
const mainStyles = computed(() => {
  const sidebarWidth = showSidebar.value 
    ? (layoutConfig.value.sidebarCollapsed 
        ? Math.round(layoutConfig.value.sidebarWidth * 0.25)
        : Math.round(layoutConfig.value.sidebarWidth * 0.4))
    : 0
  
  const padding = Math.round(layoutConfig.value.contentPadding * 0.5)
  
  return {
    marginLeft: layoutConfig.value.sidebarPosition === 'left' ? `${sidebarWidth}px` : '0',
    marginRight: layoutConfig.value.sidebarPosition === 'right' ? `${sidebarWidth}px` : '0',
    padding: `${padding}px`
  }
})

// 卡片样式
const cardsStyles = computed(() => {
  const gap = Math.round(themeConfig.value.compactMode ? 8 : 12)
  return {
    gap: `${gap}px`
  }
})

// 底部样式
const footerStyles = computed(() => {
  return {
    height: `${Math.round(layoutConfig.value.footerHeight * 0.6)}px`,
    position: layoutConfig.value.footerStyle === 'fixed' ? 'sticky' : 'static',
    bottom: layoutConfig.value.footerStyle === 'fixed' ? '0' : 'auto'
  }
})

// 设置预览模式
const setPreviewMode = (mode: PreviewMode) => {
  previewMode.value = mode
}

// 模拟加载效果
const simulateLoading = () => {
  isLoading.value = true
  setTimeout(() => {
    isLoading.value = false
  }, 800)
}

// 监听配置变化
watch([themeConfig, layoutConfig], () => {
  simulateLoading()
}, { deep: true })
</script>

<style scoped>
.settings-preview {
  position: sticky;
  top: 20px;
}

.preview-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
}

.card-header .el-icon {
  margin-right: 8px;
}

.preview-controls {
  display: flex;
  align-items: center;
}

.preview-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 预览框架 */
.preview-frame {
  position: relative;
  border: 2px solid var(--color-border);
  border-radius: 8px;
  overflow: hidden;
  background: #f0f0f0;
  transition: all var(--transition-duration);
}

.preview-frame.preview-loading {
  opacity: 0.7;
}

.preview-desktop {
  width: 100%;
  height: 500px;
}

.preview-tablet {
  width: 400px;
  height: 500px;
  margin: 0 auto;
}

.preview-mobile {
  width: 250px;
  height: 450px;
  margin: 0 auto;
}

/* 预览内容 */
.preview-content {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--preview-background);
  color: var(--preview-text);
  font-size: calc(var(--preview-font-size) * 0.8);
  position: relative;
}

/* 预览头部 */
.preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--preview-spacing);
  background: var(--preview-surface);
  border-bottom: 1px solid var(--preview-border);
  z-index: 10;
}

.header-left {
  display: flex;
  align-items: center;
  gap: calc(var(--preview-spacing) * 2);
}

.logo {
  font-weight: bold;
  color: var(--preview-primary);
}

.nav-items {
  display: flex;
  gap: var(--preview-spacing);
}

.nav-item {
  padding: 4px 8px;
  border-radius: var(--preview-border-radius);
  cursor: pointer;
  transition: all 0.2s;
}

.nav-item.active {
  background: var(--preview-primary);
  color: white;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
}

/* 预览主体 */
.preview-body {
  flex: 1;
  display: flex;
  position: relative;
  overflow: hidden;
}

/* 预览侧边栏 */
.preview-sidebar {
  position: absolute;
  top: 0;
  bottom: 0;
  background: var(--preview-surface);
  border-right: 1px solid var(--preview-border);
  z-index: 5;
  transition: width var(--transition-duration);
}

.preview-sidebar.collapsed {
  width: 40px !important;
}

.sidebar-menu {
  padding: var(--preview-spacing);
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: var(--preview-border-radius);
  cursor: pointer;
  transition: all 0.2s;
  font-size: 11px;
  white-space: nowrap;
}

.menu-item:hover {
  background: var(--preview-border);
}

.menu-item.active {
  background: var(--preview-primary);
  color: white;
}

.menu-item .el-icon {
  font-size: 14px;
  flex-shrink: 0;
}

/* 预览主内容 */
.preview-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--preview-spacing);
  overflow-y: auto;
}

/* 面包屑 */
.preview-breadcrumb {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--preview-text-secondary);
}

.preview-breadcrumb .el-icon {
  font-size: 10px;
}

/* 标签页 */
.preview-tabs {
  display: flex;
  gap: 2px;
  border-bottom: 1px solid var(--preview-border);
}

.tab-item {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  font-size: 11px;
  border-radius: var(--preview-border-radius) var(--preview-border-radius) 0 0;
  cursor: pointer;
  transition: all 0.2s;
}

.tab-item.active {
  background: var(--preview-surface);
  border-bottom: 2px solid var(--preview-primary);
}

.tab-item .el-icon {
  font-size: 10px;
}

/* 预览卡片 */
.preview-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
}

.preview-card-item {
  background: var(--preview-surface);
  border: 1px solid var(--preview-border);
  border-radius: var(--preview-border-radius);
  padding: var(--preview-spacing);
  text-align: center;
}

.preview-card-item h4 {
  margin: 0 0 4px 0;
  font-size: 10px;
  color: var(--preview-text-secondary);
}

.card-value {
  font-size: 14px;
  font-weight: bold;
  margin-bottom: 2px;
}

.card-change {
  font-size: 9px;
  color: var(--preview-text-secondary);
}

.card-change.positive {
  color: #67c23a;
}

/* 预览图表 */
.preview-chart {
  background: var(--preview-surface);
  border: 1px solid var(--preview-border);
  border-radius: var(--preview-border-radius);
  padding: var(--preview-spacing);
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--preview-spacing);
}

.chart-header h4 {
  margin: 0;
  font-size: 12px;
}

.chart-controls .el-button-group {
  transform: scale(0.8);
}

.chart-content {
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--preview-background);
  border-radius: var(--preview-border-radius);
}

.chart-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: var(--preview-text-secondary);
}

.chart-placeholder .el-icon {
  font-size: 24px;
}

.chart-placeholder span {
  font-size: 12px;
}

/* 预览底部 */
.preview-footer {
  background: var(--preview-surface);
  border-top: 1px solid var(--preview-border);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
}

.footer-content {
  font-size: 10px;
  color: var(--preview-text-secondary);
}

/* 加载遮罩 */
.preview-loading-mask {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  z-index: 100;
}

.loading-icon {
  font-size: 24px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 预览信息 */
.preview-info {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
  padding: 12px;
  background: var(--color-surface);
  border-radius: var(--border-radius);
  font-size: 12px;
}

.info-item {
  display: flex;
  justify-content: space-between;
}

.info-label {
  color: var(--color-text-secondary);
}

.info-value {
  font-weight: 500;
  color: var(--color-text);
}

/* 响应式 */
@media (max-width: 768px) {
  .preview-tablet,
  .preview-mobile {
    width: 100%;
  }
  
  .preview-info {
    grid-template-columns: 1fr;
  }
}
</style>