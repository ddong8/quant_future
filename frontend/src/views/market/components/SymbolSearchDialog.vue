<template>
  <el-dialog
    v-model="visible"
    title="搜索标的"
    width="800px"
    @close="handleClose"
  >
    <!-- 搜索框 -->
    <div class="search-section">
      <el-input
        v-model="searchQuery"
        placeholder="输入标的代码或名称进行搜索"
        clearable
        @input="handleSearch"
        @keyup.enter="handleSearch"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
    </div>

    <!-- 热门标的 -->
    <div v-if="!searchQuery && popularSymbols.length > 0" class="popular-section">
      <h4>热门标的</h4>
      <div class="symbol-grid">
        <div
          v-for="symbol in popularSymbols"
          :key="symbol.id"
          class="symbol-card"
          @click="handleAddSymbol(symbol)"
        >
          <div class="symbol-info">
            <div class="symbol-code">{{ symbol.symbol }}</div>
            <div class="symbol-name">{{ symbol.name }}</div>
            <div class="symbol-exchange">{{ symbol.exchange }}</div>
          </div>
          <el-button type="primary" size="small" text>
            添加
          </el-button>
        </div>
      </div>
    </div>

    <!-- 搜索结果 -->
    <div v-if="searchQuery" class="search-results">
      <div v-if="searching" class="loading-state">
        <el-icon class="is-loading"><Loading /></el-icon>
        搜索中...
      </div>
      
      <div v-else-if="searchResults.length === 0" class="empty-state">
        <el-empty description="未找到相关标的" />
      </div>
      
      <div v-else class="results-list">
        <div
          v-for="symbol in searchResults"
          :key="symbol.id"
          class="result-item"
          @click="handleAddSymbol(symbol)"
        >
          <div class="symbol-info">
            <div class="symbol-code">{{ symbol.symbol }}</div>
            <div class="symbol-name">{{ symbol.name }}</div>
            <div class="symbol-meta">
              <span class="exchange">{{ symbol.exchange }}</span>
              <span class="asset-type">{{ getAssetTypeText(symbol.asset_type) }}</span>
              <span class="currency">{{ symbol.currency }}</span>
            </div>
          </div>
          <el-button type="primary" size="small">
            添加到自选股
          </el-button>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">关闭</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Loading } from '@element-plus/icons-vue'
import { searchSymbols, getPopularSymbols, type Symbol } from '@/api/marketQuotes'
import { debounce } from 'lodash-es'

interface Props {
  modelValue: boolean
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'add-to-watchlist', symbolCode: string): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 响应式数据
const visible = ref(false)
const searchQuery = ref('')
const searching = ref(false)
const searchResults = ref<Symbol[]>([])
const popularSymbols = ref<Symbol[]>([])

// 监听 modelValue 变化
watch(() => props.modelValue, (newValue) => {
  visible.value = newValue
  if (newValue) {
    loadPopularSymbols()
  }
})

// 监听 visible 变化
watch(visible, (newValue) => {
  emit('update:modelValue', newValue)
})

// 加载热门标的
const loadPopularSymbols = async () => {
  try {
    const response = await getPopularSymbols(20)
    popularSymbols.value = response.data
  } catch (error) {
    console.error('加载热门标的失败:', error)
  }
}

// 搜索标的（防抖）
const handleSearch = debounce(async () => {
  if (!searchQuery.value.trim()) {
    searchResults.value = []
    return
  }

  try {
    searching.value = true
    const response = await searchSymbols({
      q: searchQuery.value.trim(),
      limit: 50
    })
    searchResults.value = response.data
  } catch (error) {
    console.error('搜索标的失败:', error)
    ElMessage.error('搜索失败')
  } finally {
    searching.value = false
  }
}, 300)

// 获取资产类型文本
const getAssetTypeText = (assetType: string) => {
  switch (assetType) {
    case 'stock': return '股票'
    case 'etf': return 'ETF'
    case 'crypto': return '加密货币'
    case 'forex': return '外汇'
    case 'commodity': return '商品'
    default: return assetType
  }
}

// 添加标的到自选股
const handleAddSymbol = async (symbol: Symbol) => {
  try {
    emit('add-to-watchlist', symbol.symbol)
    ElMessage.success(`已添加 ${symbol.symbol} 到自选股`)
    handleClose()
  } catch (error) {
    console.error('添加自选股失败:', error)
  }
}

// 关闭对话框
const handleClose = () => {
  visible.value = false
  searchQuery.value = ''
  searchResults.value = []
}

// 组件挂载
onMounted(() => {
  visible.value = props.modelValue
})
</script>

<style scoped>
.search-section {
  margin-bottom: 20px;
}

.popular-section {
  margin-bottom: 20px;
}

.popular-section h4 {
  margin: 0 0 12px 0;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
}

.symbol-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
}

.symbol-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.symbol-card:hover {
  border-color: #409eff;
  background-color: var(--el-color-primary-light-9);
}

.search-results {
  min-height: 200px;
}

.loading-state {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  padding: 40px;
  color: #909399;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

.results-list {
  max-height: 400px;
  overflow-y: auto;
}

.result-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  transition: background-color 0.2s;
}

.result-item:hover {
  background-color: var(--el-fill-color-light);
}

.result-item:last-child {
  border-bottom: none;
}

.symbol-info {
  flex: 1;
}

.symbol-code {
  font-weight: 600;
  color: #303133;
  font-size: 16px;
  margin-bottom: 4px;
}

.symbol-name {
  color: #606266;
  font-size: 14px;
  margin-bottom: 4px;
}

.symbol-exchange {
  color: #909399;
  font-size: 12px;
}

.symbol-meta {
  display: flex;
  gap: 8px;
  font-size: 12px;
}

.exchange {
  background: #e1f3d8;
  color: #67c23a;
  padding: 2px 6px;
  border-radius: 3px;
}

.asset-type {
  background: #ecf5ff;
  color: #409eff;
  padding: 2px 6px;
  border-radius: 3px;
}

.currency {
  background: var(--el-color-warning-light-9);
  color: #e6a23c;
  padding: 2px 6px;
  border-radius: 3px;
}

.dialog-footer {
  text-align: right;
}
</style>