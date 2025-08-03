<template>
  <div class="version-tree">
    <el-card>
      <template #header>
        <div class="tree-header">
          <span>版本历史树</span>
          <div class="tree-actions">
            <el-button size="small" @click="refreshTree">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
            <el-button size="small" @click="showCreateBranch = true">
              <el-icon><Plus /></el-icon>
              创建分支
            </el-button>
          </div>
        </div>
      </template>
      
      <div class="tree-content" v-loading="loading">
        <div v-if="versionTree" class="tree-container">
          <!-- 树形图 -->
          <div class="tree-graph">
            <div
              v-for="version in sortedVersions"
              :key="version.id"
              class="version-node"
              :class="{
                'major-version': version.is_major_version,
                'current-version': version.version_number === currentVersion
              }"
              @click="selectVersion(version)"
            >
              <div class="node-content">
                <div class="node-header">
                  <span class="version-number">v{{ version.version_number }}</span>
                  <el-tag
                    v-if="version.is_major_version"
                    type="warning"
                    size="small"
                    effect="plain"
                  >
                    主版本
                  </el-tag>
                  <el-tag
                    v-if="version.version_number === currentVersion"
                    type="success"
                    size="small"
                  >
                    当前
                  </el-tag>
                </div>
                
                <div class="node-title">{{ version.version_name }}</div>
                
                <div class="node-meta">
                  <span class="create-time">{{ formatDate(version.created_at) }}</span>
                </div>
                
                <div class="node-description" v-if="version.description">
                  {{ version.description }}
                </div>
              </div>
              
              <!-- 连接线 -->
              <div
                v-if="version.parent_version"
                class="connection-line"
              ></div>
            </div>
          </div>
          
          <!-- 版本详情面板 -->
          <div class="version-details" v-if="selectedVersion">
            <el-card>
              <template #header>
                <div class="details-header">
                  <span>版本详情</span>
                  <el-button-group size="small">
                    <el-button @click="compareWithPrevious" :disabled="!canCompareWithPrevious">
                      <el-icon><Compare /></el-icon>
                      与上一版本比较
                    </el-button>
                    <el-button @click="rollbackToVersion" :disabled="!canRollback">
                      <el-icon><RefreshLeft /></el-icon>
                      回滚到此版本
                    </el-button>
                  </el-button-group>
                </div>
              </template>
              
              <el-descriptions :column="1" border>
                <el-descriptions-item label="版本号">
                  v{{ selectedVersion.version_number }}
                </el-descriptions-item>
                <el-descriptions-item label="版本名称">
                  {{ selectedVersion.version_name }}
                </el-descriptions-item>
                <el-descriptions-item label="版本描述">
                  {{ selectedVersion.description || '无描述' }}
                </el-descriptions-item>
                <el-descriptions-item label="变更日志">
                  <pre class="change-log">{{ selectedVersion.change_log || '无变更日志' }}</pre>
                </el-descriptions-item>
                <el-descriptions-item label="版本类型">
                  <el-tag :type="selectedVersion.is_major_version ? 'warning' : 'info'">
                    {{ selectedVersion.is_major_version ? '主版本' : '次版本' }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="创建时间">
                  {{ formatDate(selectedVersion.created_at) }}
                </el-descriptions-item>
              </el-descriptions>
            </el-card>
          </div>
        </div>
        
        <!-- 空状态 -->
        <EmptyState
          v-else-if="!loading"
          type="no-data"
          title="暂无版本历史"
          description="该策略还没有版本历史记录"
        />
      </div>
    </el-card>

    <!-- 创建分支对话框 -->
    <BaseDialog
      v-model="showCreateBranch"
      title="创建版本分支"
      width="500px"
      @confirm="createBranch"
    >
      <el-form :model="branchForm" :rules="branchRules" ref="branchFormRef" label-width="100px">
        <el-form-item label="基础版本" prop="base_version_id" required>
          <el-select
            v-model="branchForm.base_version_id"
            placeholder="选择基础版本"
            style="width: 100%"
          >
            <el-option
              v-for="version in sortedVersions"
              :key="version.id"
              :label="`v${version.version_number} - ${version.version_name}`"
              :value="version.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="分支名称" prop="branch_name" required>
          <el-input
            v-model="branchForm.branch_name"
            placeholder="请输入分支名称"
            maxlength="50"
            show-word-limit
          />
        </el-form-item>
        
        <el-form-item label="分支描述" prop="description">
          <el-input
            v-model="branchForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入分支描述"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
      </el-form>
    </BaseDialog>

    <!-- 确认对话框 -->
    <ConfirmDialog
      v-model="showConfirmDialog"
      :type="confirmType"
      :title="confirmTitle"
      :content="confirmContent"
      @confirm="handleConfirm"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Plus, Compare, RefreshLeft } from '@element-plus/icons-vue'

import { BaseDialog, ConfirmDialog, EmptyState } from '@/components/common'
import { StrategyApi } from '@/api/strategy'
import { formatDate } from '@/utils/format'

interface Props {
  strategyId: number
  currentVersion?: number
}

interface VersionNode {
  id: number
  version_number: number
  version_name: string
  description?: string
  is_major_version: boolean
  created_at: string
  change_log?: string
  parent_version?: number
}

interface VersionTree {
  strategy_id: number
  versions: VersionNode[]
  branches: any[]
  total_versions: number
}

const props = defineProps<Props>()
const emit = defineEmits<{
  compare: [version1Id: number, version2Id: number]
  rollback: [versionId: number]
}>()

// 响应式数据
const loading = ref(false)
const versionTree = ref<VersionTree>()
const selectedVersion = ref<VersionNode>()
const showCreateBranch = ref(false)
const showConfirmDialog = ref(false)
const confirmType = ref<'warning' | 'error'>('warning')
const confirmTitle = ref('')
const confirmContent = ref('')
const confirmAction = ref<() => void>(() => {})

const branchFormRef = ref()
const branchForm = ref({
  base_version_id: null as number | null,
  branch_name: '',
  description: ''
})

const branchRules = {
  base_version_id: [
    { required: true, message: '请选择基础版本', trigger: 'change' }
  ],
  branch_name: [
    { required: true, message: '请输入分支名称', trigger: 'blur' },
    { min: 1, max: 50, message: '分支名称长度在1到50个字符', trigger: 'blur' }
  ]
}

// 计算属性
const sortedVersions = computed(() => {
  if (!versionTree.value) return []
  return [...versionTree.value.versions].sort((a, b) => b.version_number - a.version_number)
})

const canCompareWithPrevious = computed(() => {
  if (!selectedVersion.value) return false
  return selectedVersion.value.version_number > 1
})

const canRollback = computed(() => {
  if (!selectedVersion.value || !props.currentVersion) return false
  return selectedVersion.value.version_number !== props.currentVersion
})

// 方法
const refreshTree = async () => {
  await fetchVersionTree()
}

const fetchVersionTree = async () => {
  try {
    loading.value = true
    
    const response = await StrategyApi.getVersionTree(props.strategyId)
    
    if (response.success) {
      versionTree.value = response.data
      
      // 默认选择最新版本
      if (sortedVersions.value.length > 0) {
        selectedVersion.value = sortedVersions.value[0]
      }
    } else {
      ElMessage.error(response.message || '获取版本树失败')
    }
  } catch (error) {
    console.error('获取版本树失败:', error)
    ElMessage.error('获取版本树失败')
  } finally {
    loading.value = false
  }
}

const selectVersion = (version: VersionNode) => {
  selectedVersion.value = version
}

const compareWithPrevious = () => {
  if (!selectedVersion.value || !canCompareWithPrevious.value) return
  
  const currentVersionNumber = selectedVersion.value.version_number
  const previousVersion = sortedVersions.value.find(v => v.version_number === currentVersionNumber - 1)
  
  if (previousVersion) {
    emit('compare', previousVersion.id, selectedVersion.value.id)
  }
}

const rollbackToVersion = () => {
  if (!selectedVersion.value || !canRollback.value) return
  
  confirmType.value = 'warning'
  confirmTitle.value = '确认回滚'
  confirmContent.value = `确定要回滚到版本 v${selectedVersion.value.version_number} 吗？这将创建一个新的版本。`
  confirmAction.value = () => {
    emit('rollback', selectedVersion.value!.id)
  }
  showConfirmDialog.value = true
}

const createBranch = async () => {
  try {
    await branchFormRef.value?.validate()
    
    const response = await StrategyApi.createBranch(props.strategyId, {
      base_version_id: branchForm.value.base_version_id!,
      branch_name: branchForm.value.branch_name,
      description: branchForm.value.description
    })
    
    if (response.success) {
      ElMessage.success('分支创建成功')
      showCreateBranch.value = false
      resetBranchForm()
      await refreshTree()
    } else {
      ElMessage.error(response.message || '分支创建失败')
    }
  } catch (error) {
    console.error('分支创建失败:', error)
    ElMessage.error('分支创建失败')
  }
}

const resetBranchForm = () => {
  branchForm.value = {
    base_version_id: null,
    branch_name: '',
    description: ''
  }
  branchFormRef.value?.clearValidate()
}

const handleConfirm = () => {
  confirmAction.value()
  showConfirmDialog.value = false
}

// 生命周期
onMounted(() => {
  fetchVersionTree()
})
</script>

<style lang="scss" scoped>
.version-tree {
  .tree-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
  }
  
  .tree-content {
    min-height: 400px;
    
    .tree-container {
      display: flex;
      gap: 24px;
      
      .tree-graph {
        flex: 2;
        position: relative;
        
        .version-node {
          position: relative;
          margin-bottom: 20px;
          padding: 16px;
          border: 2px solid var(--el-border-color);
          border-radius: 8px;
          background: var(--el-bg-color);
          cursor: pointer;
          transition: all 0.3s ease;
          
          &:hover {
            border-color: var(--el-color-primary);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
          }
          
          &.major-version {
            border-color: var(--el-color-warning);
            background: var(--el-color-warning-light-9);
          }
          
          &.current-version {
            border-color: var(--el-color-success);
            background: var(--el-color-success-light-9);
          }
          
          .node-content {
            .node-header {
              display: flex;
              align-items: center;
              gap: 8px;
              margin-bottom: 8px;
              
              .version-number {
                font-size: 16px;
                font-weight: 600;
                color: var(--el-text-color-primary);
              }
            }
            
            .node-title {
              font-size: 14px;
              font-weight: 500;
              color: var(--el-text-color-primary);
              margin-bottom: 4px;
            }
            
            .node-meta {
              font-size: 12px;
              color: var(--el-text-color-secondary);
              margin-bottom: 8px;
            }
            
            .node-description {
              font-size: 12px;
              color: var(--el-text-color-regular);
              line-height: 1.4;
              display: -webkit-box;
              -webkit-line-clamp: 2;
              -webkit-box-orient: vertical;
              overflow: hidden;
            }
          }
          
          .connection-line {
            position: absolute;
            top: -20px;
            left: 50%;
            width: 2px;
            height: 20px;
            background: var(--el-border-color);
            transform: translateX(-50%);
            
            &::before {
              content: '';
              position: absolute;
              top: -4px;
              left: -3px;
              width: 8px;
              height: 8px;
              border-radius: 50%;
              background: var(--el-border-color);
            }
          }
        }
      }
      
      .version-details {
        flex: 1;
        
        .details-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          width: 100%;
        }
        
        .change-log {
          margin: 0;
          padding: 8px;
          background: var(--el-fill-color-light);
          border-radius: 4px;
          font-size: 12px;
          line-height: 1.4;
          white-space: pre-wrap;
          word-break: break-all;
        }
      }
    }
  }
}

@media (max-width: 768px) {
  .version-tree {
    .tree-content {
      .tree-container {
        flex-direction: column;
        
        .tree-graph {
          flex: none;
        }
        
        .version-details {
          flex: none;
        }
      }
    }
  }
}
</style>