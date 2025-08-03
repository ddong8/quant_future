<template>
  <div class="personalization-settings">
    <el-card class="settings-card">
      <template #header>
        <div class="card-header">
          <el-icon><User /></el-icon>
          <span>个性化设置</span>
        </div>
      </template>
      
      <div class="settings-content">
        <!-- 仪表板配置 -->
        <div class="setting-group">
          <h4 class="group-title">仪表板配置</h4>
          
          <div class="setting-item">
            <label class="setting-label">网格列数</label>
            <el-slider
              v-model="dashboardLayout.columns"
              :min="6"
              :max="24"
              :step="2"
              :marks="columnMarks"
              @change="handleColumnsChange"
            />
          </div>
          
          <div class="setting-item">
            <label class="setting-label">组件间距: {{ dashboardLayout.gap }}px</label>
            <el-slider
              v-model="dashboardLayout.gap"
              :min="8"
              :max="32"
              :step="4"
              @change="handleGapChange"
            />
          </div>
          
          <div class="setting-item">
            <label class="setting-label">自动高度</label>
            <el-switch
              v-model="dashboardLayout.autoHeight"
              @change="handleAutoHeightChange"
              active-text="启用"
              inactive-text="禁用"
            />
          </div>
        </div>
        
        <!-- 快捷操作 -->
        <div class="setting-group">
          <h4 class="group-title">快捷操作</h4>
          <div class="quick-actions-config">
            <div class="available-actions">
              <h5>可用操作</h5>
              <div class="action-list">
                <div
                  v-for="action in availableActions"
                  :key="action.key"
                  class="action-item"
                  :class="{ disabled: isActionSelected(action.key) }"
                  @click="addQuickAction(action)"
                >
                  <el-icon><component :is="action.icon" /></el-icon>
                  <span>{{ action.label }}</span>
                </div>
              </div>
            </div>
            
            <div class="selected-actions">
              <h5>已选操作</h5>
              <div class="action-list">
                <div
                  v-for="(actionKey, index) in quickActions"
                  :key="actionKey"
                  class="action-item selected"
                >
                  <el-icon><component :is="getActionIcon(actionKey)" /></el-icon>
                  <span>{{ getActionLabel(actionKey) }}</span>
                  <el-button
                    size="small"
                    type="danger"
                    text
                    @click="removeQuickAction(index)"
                  >
                    <el-icon><Close /></el-icon>
                  </el-button>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 收藏标的 -->
        <div class="setting-group">
          <h4 class="group-title">收藏标的</h4>
          <div class="favorite-symbols">
            <el-input
              v-model="newSymbol"
              placeholder="输入标的代码，如 AAPL"
              @keyup.enter="addFavoriteSymbol"
            >
              <template #append>
                <el-button @click="addFavoriteSymbol">添加</el-button>
              </template>
            </el-input>
            
            <div class="symbol-list">
              <el-tag
                v-for="(symbol, index) in favoriteSymbols"
                :key="symbol"
                closable
                @close="removeFavoriteSymbol(index)"
                class="symbol-tag"
              >
                {{ symbol }}
              </el-tag>
            </div>
          </div>
        </div>
        
        <!-- 自选列表 -->
        <div class="setting-group">
          <h4 class="group-title">自选列表</h4>
          <div class="watchlists-config">
            <div class="watchlist-header">
              <el-button @click="showCreateWatchlistDialog = true">
                <el-icon><Plus /></el-icon>
                创建列表
              </el-button>
            </div>
            
            <div class="watchlist-list">
              <div
                v-for="(watchlist, index) in watchlists"
                :key="watchlist.id"
                class="watchlist-item"
              >
                <div class="watchlist-info">
                  <h5 class="watchlist-name">{{ watchlist.name }}</h5>
                  <p class="watchlist-description">{{ watchlist.description }}</p>
                  <div class="watchlist-symbols">
                    <el-tag
                      v-for="symbol in watchlist.symbols.slice(0, 5)"
                      :key="symbol"
                      size="small"
                      class="symbol-tag"
                    >
                      {{ symbol }}
                    </el-tag>
                    <span v-if="watchlist.symbols.length > 5" class="more-symbols">
                      +{{ watchlist.symbols.length - 5 }}
                    </span>
                  </div>
                </div>
                <div class="watchlist-actions">
                  <el-button size="small" @click="editWatchlist(watchlist)">编辑</el-button>
                  <el-button size="small" type="danger" @click="removeWatchlist(index)">删除</el-button>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 图表设置 -->
        <div class="setting-group">
          <h4 class="group-title">图表设置</h4>
          
          <div class="setting-item">
            <label class="setting-label">默认图表类型</label>
            <el-select v-model="chartSettings.defaultType" @change="handleChartSettingsChange">
              <el-option label="K线图" value="candlestick" />
              <el-option label="折线图" value="line" />
              <el-option label="面积图" value="area" />
            </el-select>
          </div>
          
          <div class="setting-item">
            <label class="setting-label">默认时间周期</label>
            <el-select v-model="chartSettings.defaultPeriod" @change="handleChartSettingsChange">
              <el-option label="1分钟" value="1m" />
              <el-option label="5分钟" value="5m" />
              <el-option label="15分钟" value="15m" />
              <el-option label="1小时" value="1h" />
              <el-option label="1天" value="1d" />
              <el-option label="1周" value="1w" />
            </el-select>
          </div>
          
          <div class="setting-item">
            <label class="setting-label">显示技术指标</label>
            <el-checkbox-group v-model="chartSettings.indicators" @change="handleChartSettingsChange">
              <el-checkbox label="MA">移动平均线</el-checkbox>
              <el-checkbox label="MACD">MACD</el-checkbox>
              <el-checkbox label="RSI">RSI</el-checkbox>
              <el-checkbox label="BOLL">布林带</el-checkbox>
            </el-checkbox-group>
          </div>
          
          <div class="setting-item">
            <label class="setting-label">图表主题</label>
            <el-radio-group v-model="chartSettings.theme" @change="handleChartSettingsChange">
              <el-radio-button label="light">浅色</el-radio-button>
              <el-radio-button label="dark">深色</el-radio-button>
            </el-radio-group>
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
    
    <!-- 创建自选列表对话框 -->
    <el-dialog
      v-model="showCreateWatchlistDialog"
      title="创建自选列表"
      width="500px"
    >
      <el-form :model="newWatchlist" label-width="80px">
        <el-form-item label="列表名称">
          <el-input v-model="newWatchlist.name" placeholder="请输入列表名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="newWatchlist.description"
            type="textarea"
            :rows="3"
            placeholder="请输入列表描述"
          />
        </el-form-item>
        <el-form-item label="标的代码">
          <el-input
            v-model="newWatchlist.symbolsText"
            type="textarea"
            :rows="4"
            placeholder="请输入标的代码，用逗号分隔，如：AAPL,GOOGL,MSFT"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateWatchlistDialog = false">取消</el-button>
        <el-button type="primary" @click="createWatchlist">创建</el-button>
      </template>
    </el-dialog>
    
    <!-- 导入配置对话框 -->
    <el-dialog
      v-model="importDialogVisible"
      title="导入个性化配置"
      width="500px"
    >
      <el-input
        v-model="importConfigText"
        type="textarea"
        :rows="10"
        placeholder="请粘贴个性化配置JSON"
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
import {
  User, Plus, Close, TrendCharts, ShoppingCart, 
  Position, Bell, Setting, DataAnalysis
} from '@element-plus/icons-vue'
import { useLayout } from '@/composables/useLayout'
import { updateUserSettings } from '@/api/userSettings'

const { dashboardLayout } = useLayout()

// 快捷操作配置
const quickActions = ref<string[]>(['create_order', 'view_positions', 'market_analysis'])

// 收藏标的
const favoriteSymbols = ref<string[]>(['AAPL', 'GOOGL', 'MSFT', 'TSLA'])
const newSymbol = ref('')

// 自选列表
const watchlists = ref([
  {
    id: '1',
    name: '科技股',
    description: '主要的科技公司股票',
    symbols: ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'META', 'NFLX']
  },
  {
    id: '2',
    name: '新能源',
    description: '新能源相关股票',
    symbols: ['TSLA', 'NIO', 'XPEV', 'LI']
  }
])

// 图表设置
const chartSettings = ref({
  defaultType: 'candlestick',
  defaultPeriod: '1d',
  indicators: ['MA', 'MACD'],
  theme: 'light'
})

// 对话框状态
const showCreateWatchlistDialog = ref(false)
const importDialogVisible = ref(false)
const importConfigText = ref('')

// 新建自选列表
const newWatchlist = ref({
  name: '',
  description: '',
  symbolsText: ''
})

// 网格列数标记
const columnMarks = {
  6: '6',
  12: '12',
  18: '18',
  24: '24'
}

// 可用的快捷操作
const availableActions = [
  { key: 'create_order', label: '创建订单', icon: 'Plus' },
  { key: 'view_positions', label: '查看持仓', icon: 'Position' },
  { key: 'market_analysis', label: '市场分析', icon: 'TrendCharts' },
  { key: 'order_history', label: '订单历史', icon: 'ShoppingCart' },
  { key: 'notifications', label: '通知中心', icon: 'Bell' },
  { key: 'settings', label: '系统设置', icon: 'Setting' },
  { key: 'data_export', label: '数据导出', icon: 'DataAnalysis' }
]

// 检查操作是否已选择
const isActionSelected = (actionKey: string) => {
  return quickActions.value.includes(actionKey)
}

// 获取操作图标
const getActionIcon = (actionKey: string) => {
  const action = availableActions.find(a => a.key === actionKey)
  return action?.icon || 'Setting'
}

// 获取操作标签
const getActionLabel = (actionKey: string) => {
  const action = availableActions.find(a => a.key === actionKey)
  return action?.label || actionKey
}

// 事件处理
const handleColumnsChange = () => {
  savePersonalizationSettings()
}

const handleGapChange = () => {
  savePersonalizationSettings()
}

const handleAutoHeightChange = () => {
  savePersonalizationSettings()
}

const addQuickAction = (action: any) => {
  if (!isActionSelected(action.key)) {
    quickActions.value.push(action.key)
    savePersonalizationSettings()
  }
}

const removeQuickAction = (index: number) => {
  quickActions.value.splice(index, 1)
  savePersonalizationSettings()
}

const addFavoriteSymbol = () => {
  const symbol = newSymbol.value.trim().toUpperCase()
  if (symbol && !favoriteSymbols.value.includes(symbol)) {
    favoriteSymbols.value.push(symbol)
    newSymbol.value = ''
    savePersonalizationSettings()
  }
}

const removeFavoriteSymbol = (index: number) => {
  favoriteSymbols.value.splice(index, 1)
  savePersonalizationSettings()
}

const createWatchlist = () => {
  if (!newWatchlist.value.name.trim()) {
    ElMessage.error('请输入列表名称')
    return
  }
  
  const symbols = newWatchlist.value.symbolsText
    .split(',')
    .map(s => s.trim().toUpperCase())
    .filter(s => s)
  
  const watchlist = {
    id: Date.now().toString(),
    name: newWatchlist.value.name.trim(),
    description: newWatchlist.value.description.trim(),
    symbols
  }
  
  watchlists.value.push(watchlist)
  showCreateWatchlistDialog.value = false
  
  // 重置表单
  newWatchlist.value = {
    name: '',
    description: '',
    symbolsText: ''
  }
  
  savePersonalizationSettings()
  ElMessage.success('自选列表创建成功')
}

const editWatchlist = (watchlist: any) => {
  // 这里可以实现编辑功能
  ElMessage.info('编辑功能待实现')
}

const removeWatchlist = async (index: number) => {
  try {
    await ElMessageBox.confirm('确定要删除这个自选列表吗？', '确认删除', {
      type: 'warning'
    })
    watchlists.value.splice(index, 1)
    savePersonalizationSettings()
    ElMessage.success('自选列表已删除')
  } catch {
    // 用户取消
  }
}

const handleChartSettingsChange = () => {
  savePersonalizationSettings()
}

const handleReset = async () => {
  try {
    await ElMessageBox.confirm('确定要重置为默认个性化配置吗？', '确认重置', {
      type: 'warning'
    })
    
    // 重置所有配置
    quickActions.value = ['create_order', 'view_positions', 'market_analysis']
    favoriteSymbols.value = ['AAPL', 'GOOGL', 'MSFT', 'TSLA']
    watchlists.value = []
    chartSettings.value = {
      defaultType: 'candlestick',
      defaultPeriod: '1d',
      indicators: ['MA', 'MACD'],
      theme: 'light'
    }
    dashboardLayout.value.columns = 12
    dashboardLayout.value.gap = 16
    dashboardLayout.value.autoHeight = true
    
    await savePersonalizationSettings()
    ElMessage.success('个性化配置已重置')
  } catch {
    // 用户取消
  }
}

const handleExport = () => {
  const config = {
    quickActions: quickActions.value,
    favoriteSymbols: favoriteSymbols.value,
    watchlists: watchlists.value,
    chartSettings: chartSettings.value,
    dashboardLayout: dashboardLayout.value,
    exportTime: new Date().toISOString(),
    version: '1.0'
  }
  
  const configText = JSON.stringify(config, null, 2)
  
  // 创建下载链接
  const blob = new Blob([configText], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `personalization-config-${new Date().toISOString().split('T')[0]}.json`
  link.click()
  URL.revokeObjectURL(url)
  
  ElMessage.success('个性化配置已导出')
}

const handleImport = () => {
  importConfigText.value = ''
  importDialogVisible.value = true
}

const confirmImport = async () => {
  try {
    const config = JSON.parse(importConfigText.value)
    
    if (config.version === '1.0') {
      if (config.quickActions) quickActions.value = config.quickActions
      if (config.favoriteSymbols) favoriteSymbols.value = config.favoriteSymbols
      if (config.watchlists) watchlists.value = config.watchlists
      if (config.chartSettings) chartSettings.value = config.chartSettings
      if (config.dashboardLayout) Object.assign(dashboardLayout.value, config.dashboardLayout)
      
      await savePersonalizationSettings()
      ElMessage.success('个性化配置导入成功')
      importDialogVisible.value = false
    } else {
      ElMessage.error('配置版本不兼容')
    }
  } catch (error) {
    ElMessage.error('配置格式错误，请检查JSON格式')
  }
}

// 保存个性化设置
const savePersonalizationSettings = async () => {
  try {
    await updateUserSettings({
      quick_actions: quickActions.value,
      favorite_symbols: favoriteSymbols.value,
      watchlists: watchlists.value,
      chart_settings: chartSettings.value,
      dashboard_layout: dashboardLayout.value
    })
  } catch (error) {
    console.error('保存个性化设置失败:', error)
  }
}
</script>

<style scoped>
.personalization-settings {
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

/* 快捷操作配置 */
.quick-actions-config {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.quick-actions-config h5 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
}

.action-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 200px;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius);
  padding: 12px;
}

.action-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: var(--border-radius-small);
  cursor: pointer;
  transition: all var(--transition-duration);
}

.action-item:hover:not(.disabled) {
  background: var(--color-surface);
}

.action-item.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.action-item.selected {
  background: var(--color-primary);
  color: white;
  justify-content: space-between;
}

.action-item.selected:hover {
  background: var(--color-primary-hover);
}

/* 收藏标的 */
.favorite-symbols {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.symbol-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.symbol-tag {
  margin: 0;
}

/* 自选列表 */
.watchlists-config {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.watchlist-header {
  display: flex;
  justify-content: flex-start;
}

.watchlist-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.watchlist-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 16px;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius);
  background: var(--color-surface);
}

.watchlist-info {
  flex: 1;
}

.watchlist-name {
  margin: 0 0 4px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text);
}

.watchlist-description {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: var(--color-text-secondary);
}

.watchlist-symbols {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  align-items: center;
}

.more-symbols {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.watchlist-actions {
  display: flex;
  gap: 8px;
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
  .quick-actions-config {
    grid-template-columns: 1fr;
  }
  
  .watchlist-item {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .setting-actions {
    flex-direction: column;
  }
}
</style>