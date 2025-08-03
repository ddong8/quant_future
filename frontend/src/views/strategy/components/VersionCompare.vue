<template>
  <div class="version-compare">
    <!-- 版本选择器 -->
    <div class="version-selector">
      <el-card>
        <template #header>
          <span>版本比较</span>
        </template>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="旧版本">
              <el-select
                v-model="selectedVersion1"
                placeholder="选择旧版本"
                style="width: 100%"
                @change="handleVersionChange"
              >
                <el-option
                  v-for="version in versions"
                  :key="version.id"
                  :label="`v${version.version_number} - ${version.version_name}`"
                  :value="version.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
          
          <el-col :span="12">
            <el-form-item label="新版本">
              <el-select
                v-model="selectedVersion2"
                placeholder="选择新版本"
                style="width: 100%"
                @change="handleVersionChange"
              >
                <el-option
                  v-for="version in versions"
                  :key="version.id"
                  :label="`v${version.version_number} - ${version.version_name}`"
                  :value="version.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <div class="selector-actions">
          <el-button
            @click="compareVersions"
            type="primary"
            :disabled="!selectedVersion1 || !selectedVersion2 || selectedVersion1 === selectedVersion2"
            :loading="comparing"
          >
            <el-icon><Compare /></el-icon>
            比较版本
          </el-button>
          
          <el-button
            @click="swapVersions"
            :disabled="!selectedVersion1 || !selectedVersion2"
          >
            <el-icon><Sort /></el-icon>
            交换版本
          </el-button>
          
          <el-button
            @click="exportDiff"
            :disabled="!diffResult"
          >
            <el-icon><Download /></el-icon>
            导出差异
          </el-button>
        </div>
      </el-card>
    </div>

    <!-- 比较结果 -->
    <div class="compare-result" v-if="diffResult">
      <!-- 统计信息 -->
      <el-card class="stats-card">
        <template #header>
          <span>差异统计</span>
        </template>
        
        <el-row :gutter="20">
          <el-col :span="6">
            <div class="stat-item added">
              <div class="stat-value">{{ diffResult.stats.added }}</div>
              <div class="stat-label">新增行</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-item removed">
              <div class="stat-value">{{ diffResult.stats.removed }}</div>
              <div class="stat-label">删除行</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-item modified">
              <div class="stat-value">{{ diffResult.stats.modified }}</div>
              <div class="stat-label">修改行</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-item unchanged">
              <div class="stat-value">{{ diffResult.stats.unchanged }}</div>
              <div class="stat-label">未变更行</div>
            </div>
          </el-col>
        </el-row>
      </el-card>

      <!-- 版本信息 -->
      <el-row :gutter="20">
        <el-col :span="12">
          <el-card class="version-info-card">
            <template #header>
              <span>旧版本信息</span>
            </template>
            
            <el-descriptions :column="1" size="small">
              <el-descriptions-item label="版本号">
                v{{ diffResult.old_version.version_number }}
              </el-descriptions-item>
              <el-descriptions-item label="版本名称">
                {{ diffResult.old_version.version_name }}
              </el-descriptions-item>
              <el-descriptions-item label="创建时间">
                {{ formatDate(diffResult.old_version.created_at) }}
              </el-descriptions-item>
            </el-descriptions>
          </el-card>
        </el-col>
        
        <el-col :span="12">
          <el-card class="version-info-card">
            <template #header>
              <span>新版本信息</span>
            </template>
            
            <el-descriptions :column="1" size="small">
              <el-descriptions-item label="版本号">
                v{{ diffResult.new_version.version_number }}
              </el-descriptions-item>
              <el-descriptions-item label="版本名称">
                {{ diffResult.new_version.version_name }}
              </el-descriptions-item>
              <el-descriptions-item label="创建时间">
                {{ formatDate(diffResult.new_version.created_at) }}
              </el-descriptions-item>
            </el-descriptions>
          </el-card>
        </el-col>
      </el-row>

      <!-- 差异显示 -->
      <el-card class="diff-card">
        <template #header>
          <div class="diff-header">
            <span>代码差异</span>
            <div class="diff-actions">
              <el-radio-group v-model="viewMode" size="small">
                <el-radio-button label="unified">统一视图</el-radio-button>
                <el-radio-button label="split">分屏视图</el-radio-button>
              </el-radio-group>
            </div>
          </div>
        </template>
        
        <div class="diff-content">
          <!-- 统一视图 -->
          <div v-if="viewMode === 'unified'" class="unified-diff">
            <div
              v-for="(block, blockIndex) in diffResult.diff_blocks"
              :key="blockIndex"
              class="diff-block"
            >
              <div class="block-header">
                @@ -{{ block.old_start }},{{ block.old_count }} +{{ block.new_start }},{{ block.new_count }} @@
              </div>
              
              <div
                v-for="(line, lineIndex) in block.lines"
                :key="lineIndex"
                class="diff-line"
                :class="line.type"
              >
                <span class="line-number old-line-number">
                  {{ line.old_line_number || '' }}
                </span>
                <span class="line-number new-line-number">
                  {{ line.new_line_number || '' }}
                </span>
                <span class="line-prefix">{{ getLinePrefix(line.type) }}</span>
                <span class="line-content">{{ line.content }}</span>
              </div>
            </div>
          </div>
          
          <!-- 分屏视图 -->
          <div v-else class="split-diff">
            <div class="split-container">
              <div class="split-pane old-pane">
                <div class="pane-header">
                  旧版本 (v{{ diffResult.old_version.version_number }})
                </div>
                <div class="pane-content">
                  <div
                    v-for="(block, blockIndex) in diffResult.diff_blocks"
                    :key="blockIndex"
                    class="diff-block"
                  >
                    <div
                      v-for="(line, lineIndex) in block.lines"
                      :key="lineIndex"
                      class="diff-line"
                      :class="{ 'removed': line.type === 'removed', 'unchanged': line.type === 'unchanged' }"
                      v-show="line.type !== 'added'"
                    >
                      <span class="line-number">{{ line.old_line_number || '' }}</span>
                      <span class="line-content">{{ line.content }}</span>
                    </div>
                  </div>
                </div>
              </div>
              
              <div class="split-pane new-pane">
                <div class="pane-header">
                  新版本 (v{{ diffResult.new_version.version_number }})
                </div>
                <div class="pane-content">
                  <div
                    v-for="(block, blockIndex) in diffResult.diff_blocks"
                    :key="blockIndex"
                    class="diff-block"
                  >
                    <div
                      v-for="(line, lineIndex) in block.lines"
                      :key="lineIndex"
                      class="diff-line"
                      :class="{ 'added': line.type === 'added', 'unchanged': line.type === 'unchanged' }"
                      v-show="line.type !== 'removed'"
                    >
                      <span class="line-number">{{ line.new_line_number || '' }}</span>
                      <span class="line-content">{{ line.content }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 空状态 -->
    <EmptyState
      v-else-if="!comparing"
      type="info"
      title="选择版本进行比较"
      description="请选择两个不同的版本来查看它们之间的差异"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Compare, Sort, Download } from '@element-plus/icons-vue'

import { EmptyState } from '@/components/common'
import { StrategyApi } from '@/api/strategy'
import type { StrategyVersion } from '@/types/strategy'
import { formatDate } from '@/utils/format'

interface Props {
  strategyId: number
  versions: StrategyVersion[]
}

interface DiffLine {
  line_number: number
  content: string
  type: 'added' | 'removed' | 'unchanged' | 'modified'
  old_line_number?: number
  new_line_number?: number
}

interface DiffBlock {
  old_start: number
  old_count: number
  new_start: number
  new_count: number
  lines: DiffLine[]
}

interface DiffResult {
  old_version: {
    id: number
    version_number: number
    version_name: string
    created_at: string
  }
  new_version: {
    id: number
    version_number: number
    version_name: string
    created_at: string
  }
  diff_blocks: DiffBlock[]
  stats: {
    added: number
    removed: number
    modified: number
    unchanged: number
  }
}

const props = defineProps<Props>()

// 响应式数据
const selectedVersion1 = ref<number>()
const selectedVersion2 = ref<number>()
const comparing = ref(false)
const diffResult = ref<DiffResult>()
const viewMode = ref<'unified' | 'split'>('unified')

// 方法
const handleVersionChange = () => {
  // 清空之前的比较结果
  diffResult.value = undefined
}

const swapVersions = () => {
  const temp = selectedVersion1.value
  selectedVersion1.value = selectedVersion2.value
  selectedVersion2.value = temp
  
  // 如果已经有比较结果，重新比较
  if (diffResult.value) {
    compareVersions()
  }
}

const compareVersions = async () => {
  if (!selectedVersion1.value || !selectedVersion2.value) {
    ElMessage.warning('请选择两个版本进行比较')
    return
  }
  
  if (selectedVersion1.value === selectedVersion2.value) {
    ElMessage.warning('请选择两个不同的版本')
    return
  }
  
  try {
    comparing.value = true
    
    const response = await StrategyApi.compareVersions(
      props.strategyId,
      selectedVersion1.value,
      selectedVersion2.value
    )
    
    if (response.success) {
      diffResult.value = response.data
    } else {
      ElMessage.error(response.message || '版本比较失败')
    }
  } catch (error) {
    console.error('版本比较失败:', error)
    ElMessage.error('版本比较失败')
  } finally {
    comparing.value = false
  }
}

const exportDiff = async () => {
  if (!diffResult.value) return
  
  try {
    const response = await StrategyApi.exportVersionDiff(
      props.strategyId,
      selectedVersion1.value!,
      selectedVersion2.value!,
      'unified'
    )
    
    if (response.success) {
      // 创建下载链接
      const blob = new Blob([response.data.diff_content], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = response.data.filename
      a.click()
      URL.revokeObjectURL(url)
      
      ElMessage.success('差异文件导出成功')
    } else {
      ElMessage.error(response.message || '导出失败')
    }
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败')
  }
}

const getLinePrefix = (type: string) => {
  switch (type) {
    case 'added':
      return '+'
    case 'removed':
      return '-'
    case 'unchanged':
      return ' '
    default:
      return ' '
  }
}

// 生命周期
onMounted(() => {
  // 如果有版本数据，默认选择最新的两个版本
  if (props.versions.length >= 2) {
    selectedVersion2.value = props.versions[0].id // 最新版本
    selectedVersion1.value = props.versions[1].id // 次新版本
  }
})
</script>

<style lang="scss" scoped>
.version-compare {
  .version-selector {
    margin-bottom: 24px;
    
    .selector-actions {
      margin-top: 16px;
      text-align: center;
      
      .el-button + .el-button {
        margin-left: 12px;
      }
    }
  }
  
  .compare-result {
    .stats-card {
      margin-bottom: 20px;
      
      .stat-item {
        text-align: center;
        padding: 16px;
        border-radius: 8px;
        
        .stat-value {
          font-size: 24px;
          font-weight: 600;
          margin-bottom: 8px;
        }
        
        .stat-label {
          font-size: 12px;
          color: var(--el-text-color-secondary);
        }
        
        &.added {
          background: var(--el-color-success-light-9);
          .stat-value {
            color: var(--el-color-success);
          }
        }
        
        &.removed {
          background: var(--el-color-danger-light-9);
          .stat-value {
            color: var(--el-color-danger);
          }
        }
        
        &.modified {
          background: var(--el-color-warning-light-9);
          .stat-value {
            color: var(--el-color-warning);
          }
        }
        
        &.unchanged {
          background: var(--el-color-info-light-9);
          .stat-value {
            color: var(--el-color-info);
          }
        }
      }
    }
    
    .version-info-card {
      margin-bottom: 20px;
    }
    
    .diff-card {
      .diff-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        width: 100%;
      }
      
      .diff-content {
        font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
        font-size: 13px;
        line-height: 1.5;
        
        .unified-diff {
          .diff-block {
            margin-bottom: 16px;
            border: 1px solid var(--el-border-color);
            border-radius: 4px;
            overflow: hidden;
            
            .block-header {
              background: var(--el-fill-color-light);
              padding: 8px 12px;
              font-weight: 600;
              color: var(--el-text-color-secondary);
              border-bottom: 1px solid var(--el-border-color);
            }
            
            .diff-line {
              display: flex;
              align-items: center;
              min-height: 20px;
              
              &.added {
                background: var(--el-color-success-light-9);
                border-left: 3px solid var(--el-color-success);
              }
              
              &.removed {
                background: var(--el-color-danger-light-9);
                border-left: 3px solid var(--el-color-danger);
              }
              
              &.unchanged {
                background: var(--el-bg-color);
              }
              
              .line-number {
                display: inline-block;
                width: 50px;
                padding: 2px 8px;
                text-align: right;
                color: var(--el-text-color-placeholder);
                background: var(--el-fill-color-lighter);
                border-right: 1px solid var(--el-border-color-light);
                user-select: none;
                
                &.old-line-number {
                  border-right: none;
                }
              }
              
              .line-prefix {
                display: inline-block;
                width: 20px;
                text-align: center;
                font-weight: 600;
                
                .added & {
                  color: var(--el-color-success);
                }
                
                .removed & {
                  color: var(--el-color-danger);
                }
              }
              
              .line-content {
                flex: 1;
                padding: 2px 8px;
                white-space: pre;
                overflow-x: auto;
              }
            }
          }
        }
        
        .split-diff {
          .split-container {
            display: flex;
            border: 1px solid var(--el-border-color);
            border-radius: 4px;
            overflow: hidden;
            
            .split-pane {
              flex: 1;
              
              .pane-header {
                background: var(--el-fill-color-light);
                padding: 8px 12px;
                font-weight: 600;
                color: var(--el-text-color-secondary);
                border-bottom: 1px solid var(--el-border-color);
                text-align: center;
              }
              
              .pane-content {
                max-height: 600px;
                overflow-y: auto;
                
                .diff-line {
                  display: flex;
                  align-items: center;
                  min-height: 20px;
                  
                  &.added {
                    background: var(--el-color-success-light-9);
                  }
                  
                  &.removed {
                    background: var(--el-color-danger-light-9);
                  }
                  
                  &.unchanged {
                    background: var(--el-bg-color);
                  }
                  
                  .line-number {
                    display: inline-block;
                    width: 50px;
                    padding: 2px 8px;
                    text-align: right;
                    color: var(--el-text-color-placeholder);
                    background: var(--el-fill-color-lighter);
                    border-right: 1px solid var(--el-border-color-light);
                    user-select: none;
                  }
                  
                  .line-content {
                    flex: 1;
                    padding: 2px 8px;
                    white-space: pre;
                    overflow-x: auto;
                  }
                }
              }
              
              &.new-pane {
                border-left: 1px solid var(--el-border-color);
              }
            }
          }
        }
      }
    }
  }
}
</style>