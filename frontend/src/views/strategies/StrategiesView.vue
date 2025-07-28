<template>
  <div class="strategies-container">
    <div class="page-header">
      <h1 class="page-title">策略管理</h1>
      <div class="header-actions">
        <el-button type="primary" @click="showCreateDialog = true">
          <el-icon><Plus /></el-icon>
          创建策略
        </el-button>
        <el-button @click="showTemplateDialog = true">
          <el-icon><Document /></el-icon>
          从模板创建
        </el-button>
      </div>
    </div>

    <!-- 筛选和搜索 -->
    <div class="filters">
      <el-row :gutter="16">
        <el-col :span="6">
          <el-select v-model="filters.category" placeholder="选择分类" clearable>
            <el-option
              v-for="category in categories"
              :key="category.id"
              :label="category.name"
              :value="category.id"
            />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-select v-model="filters.status" placeholder="选择状态" clearable>
            <el-option label="草稿" value="draft" />
            <el-option label="活跃" value="active" />
            <el-option label="暂停" value="paused" />
            <el-option label="停止" value="stopped" />
            <el-option label="错误" value="error" />
          </el-select>
        </el-col>
        <el-col :span="8">
          <el-input
            v-model="filters.search"
            placeholder="搜索策略名称或描述"
            clearable
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
        <el-col :span="4">
          <el-button type="primary" @click="handleSearch">搜索</el-button>
        </el-col>
      </el-row>
    </div>

    <!-- 策略列表 -->
    <div class="strategies-grid">
      <el-row :gutter="16">
        <el-col
          v-for="strategy in strategies"
          :key="strategy.id"
          :xs="24"
          :sm="12"
          :md="8"
          :lg="6"
        >
          <StrategyCard
            :strategy="strategy"
            @edit="handleEdit"
            @delete="handleDelete"
            @clone="handleClone"
            @start="handleStart"
            @stop="handleStop"
            @view="handleView"
            @test="handleTest"
          />
        </el-col>
      </el-row>
    </div>

    <!-- 分页 -->
    <div class="pagination">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[12, 24, 48, 96]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>

    <!-- 创建策略对话框 -->
    <CreateStrategyDialog
      v-model="showCreateDialog"
      @success="handleCreateSuccess"
    />

    <!-- 模板选择对话框 -->
    <TemplateDialog
      v-model="showTemplateDialog"
      @success="handleCreateSuccess"
    />

    <!-- 策略详情对话框 -->
    <StrategyDetailDialog
      v-model="showDetailDialog"
      :strategy-id="selectedStrategyId"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Document, Search } from '@element-plus/icons-vue'
import { useStrategyStore } from '@/stores/strategy'
import StrategyCard from '@/components/StrategyCard.vue'
import CreateStrategyDialog from '@/components/CreateStrategyDialog.vue'
import TemplateDialog from '@/components/TemplateDialog.vue'
import StrategyDetailDialog from '@/components/StrategyDetailDialog.vue'
import type { Strategy } from '@/types/strategy'

const strategyStore = useStrategyStore()
const router = useRouter()

// 响应式数据
const showCreateDialog = ref(false)
const showTemplateDialog = ref(false)
const showDetailDialog = ref(false)
const selectedStrategyId = ref<number | null>(null)

const filters = ref({
  category: '',
  status: '',
  search: ''
})

// 计算属性
const strategies = computed(() => strategyStore.strategies)
const categories = computed(() => strategyStore.categories)
const loading = computed(() => strategyStore.loading)
const total = computed(() => strategyStore.total)
const currentPage = computed({
  get: () => strategyStore.currentPage,
  set: (value) => {
    // 这里需要通过store方法来更新
  }
})
const pageSize = computed({
  get: () => strategyStore.pageSize,
  set: (value) => {
    // 这里需要通过store方法来更新
  }
})

// 方法
const handleSearch = () => {
  loadStrategies()
}

const loadStrategies = () => {
  const params = {
    page: currentPage.value,
    page_size: pageSize.value,
    ...filters.value
  }
  strategyStore.fetchStrategies(params)
}

const handleSizeChange = (size: number) => {
  loadStrategies()
}

const handleCurrentChange = (page: number) => {
  loadStrategies()
}

const handleEdit = (strategy: Strategy) => {
  // 跳转到策略编辑页面
  router.push(`/strategies/${strategy.id}/edit`)
}

const handleDelete = async (strategy: Strategy) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除策略 "${strategy.name}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await strategyStore.deleteStrategy(strategy.id)
  } catch (error) {
    // 用户取消删除
  }
}

const handleClone = async (strategy: Strategy) => {
  try {
    const { value: name } = await ElMessageBox.prompt(
      '请输入新策略的名称',
      '克隆策略',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputValue: `${strategy.name} - 副本`,
        inputValidator: (value) => {
          if (!value || value.trim().length === 0) {
            return '策略名称不能为空'
          }
          return true
        }
      }
    )
    
    await strategyStore.cloneStrategy(strategy.id, name)
  } catch (error) {
    // 用户取消克隆
  }
}

const handleStart = async (strategy: Strategy) => {
  try {
    await strategyStore.startStrategy(strategy.id)
  } catch (error) {
    // 错误已在store中处理
  }
}

const handleStop = async (strategy: Strategy) => {
  try {
    await ElMessageBox.confirm(
      `确定要停止策略 "${strategy.name}" 吗？`,
      '确认停止',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await strategyStore.stopStrategy(strategy.id)
  } catch (error) {
    // 用户取消或错误已在store中处理
  }
}

const handleView = (strategy: Strategy) => {
  selectedStrategyId.value = strategy.id
  showDetailDialog.value = true
}

const handleTest = (strategy: Strategy) => {
  // 跳转到策略测试页面
  router.push(`/strategies/${strategy.id}/test`)
}

const handleCreateSuccess = () => {
  loadStrategies()
}

// 监听筛选条件变化
watch(filters, () => {
  handleSearch()
}, { deep: true })

// 生命周期
onMounted(() => {
  strategyStore.fetchCategories()
  loadStrategies()
})
</script>

<style scoped lang="scss">
.strategies-container {
  padding: 20px;
  
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    
    .page-title {
      margin: 0;
      font-size: 24px;
      font-weight: 600;
      color: #303133;
    }
    
    .header-actions {
      display: flex;
      gap: 12px;
    }
  }
  
  .filters {
    margin-bottom: 20px;
    padding: 16px;
    background: #fff;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }
  
  .strategies-grid {
    margin-bottom: 20px;
  }
  
  .pagination {
    display: flex;
    justify-content: center;
    padding: 20px 0;
  }
}
</style>