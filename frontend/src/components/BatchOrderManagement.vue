<template>
  <div class="batch-order-management">
    <el-card title="批量订单管理">
      <template #header>
        <div class="card-header">
          <span>批量订单管理</span>
          <div class="header-actions">
            <el-button @click="importOrders">
              <el-icon><Upload /></el-icon>
              导入
            </el-button>
            <el-button @click="exportTemplate">
              <el-icon><Download /></el-icon>
              模板
            </el-button>
            <el-button type="primary" @click="addOrder">
              <el-icon><Plus /></el-icon>
              添加订单
            </el-button>
          </div>
        </div>
      </template>

      <!-- 批量操作工具栏 -->
      <div class="batch-toolbar">
        <div class="toolbar-left">
          <el-checkbox
            v-model="selectAll"
            :indeterminate="isIndeterminate"
            @change="handleSelectAll"
          >
            全选
          </el-checkbox>
          <span class="selected-count">
            已选择 {{ selectedOrders.length }} / {{ batchOrders.length }} 项
          </span>
        </div>
        
        <div class="toolbar-right">
          <el-button
            size="small"
            :disabled="selectedOrders.length === 0"
            @click="duplicateSelected"
          >
            复制选中
          </el-button>
          <el-button
            size="small"
            type="danger"
            :disabled="selectedOrders.length === 0"
            @click="deleteSelected"
          >
            删除选中
          </el-button>
        </div>
      </div>

      <!-- 订单列表 -->
      <div class="order-list">
        <el-table
          :data="batchOrders"
          @selection-change="handleSelectionChange"
          max-height="400"
        >
          <el-table-column type="selection" width="55" />
          
          <el-table-column label="序号" width="60">
            <template #default="{ $index }">
              {{ $index + 1 }}
            </template>
          </el-table-column>
          
          <el-table-column label="合约" prop="symbol" width="120">
            <template #default="{ row, $index }">
              <el-select
                v-model="row.symbol"
                placeholder="选择合约"
                filterable
                size="small"
                @change="validateOrder($index)"
              >
                <el-option
                  v-for="symbol in symbolOptions"
                  :key="symbol.code"
                  :label="symbol.name"
                  :value="symbol.code"
                />
              </el-select>
            </template>
          </el-table-column>
          
          <el-table-column label="方向" width="80">
            <template #default="{ row, $index }">
              <el-select
                v-model="row.side"
                size="small"
                @change="validateOrder($index)"
              >
                <el-option label="买入" value="buy" />
                <el-option label="卖出" value="sell" />
              </el-select>
            </template>
          </el-table-column>
          
          <el-table-column label="类型" width="100">
            <template #default="{ row, $index }">
              <el-select
                v-model="row.order_type"
                size="small"
                @change="validateOrder($index)"
              >
                <el-option label="市价" value="market" />
                <el-option label="限价" value="limit" />
                <el-option label="止损" value="stop" />
              </el-select>
            </template>
          </el-table-column>
          
          <el-table-column label="数量" width="100">
            <template #default="{ row, $index }">
              <el-input-number
                v-model="row.quantity"
                :min="1"
                :max="1000"
                size="small"
                @change="validateOrder($index)"
              />
            </template>
          </el-table-column>
          
          <el-table-column label="价格" width="120">
            <template #default="{ row, $index }">
              <el-input-number
                v-model="row.price"
                :disabled="row.order_type === 'market'"
                :min="0"
                :precision="2"
                size="small"
                @change="validateOrder($index)"
              />
            </template>
          </el-table-column>
          
          <el-table-column label="有效期" width="120">
            <template #default="{ row }">
              <el-select v-model="row.time_in_force" size="small">
                <el-option label="当日" value="day" />
                <el-option label="GTC" value="gtc" />
                <el-option label="IOC" value="ioc" />
                <el-option label="FOK" value="fok" />
              </el-select>
            </template>
          </el-table-column>
          
          <el-table-column label="状态" width="80">
            <template #default="{ row }">
              <el-tag
                :type="getStatusType(row.status)"
                size="small"
              >
                {{ getStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="{ row, $index }">
              <el-button
                text
                size="small"
                @click="duplicateOrder($index)"
              >
                复制
              </el-button>
              <el-button
                text
                size="small"
                type="danger"
                @click="deleteOrder($index)"
              >
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 批量设置 -->
      <div class="batch-settings">
        <el-collapse v-model="activeSettings">
          <el-collapse-item title="批量设置" name="settings">
            <el-row :gutter="16">
              <el-col :span="8">
                <el-form-item label="统一合约">
                  <el-select
                    v-model="batchSettings.symbol"
                    placeholder="选择合约"
                    clearable
                    @change="applyBatchSetting('symbol')"
                  >
                    <el-option
                      v-for="symbol in symbolOptions"
                      :key="symbol.code"
                      :label="symbol.name"
                      :value="symbol.code"
                    />
                  </el-select>
                </el-form-item>
              </el-col>
              
              <el-col :span="8">
                <el-form-item label="统一方向">
                  <el-select
                    v-model="batchSettings.side"
                    placeholder="选择方向"
                    clearable
                    @change="applyBatchSetting('side')"
                  >
                    <el-option label="买入" value="buy" />
                    <el-option label="卖出" value="sell" />
                  </el-select>
                </el-form-item>
              </el-col>
              
              <el-col :span="8">
                <el-form-item label="统一类型">
                  <el-select
                    v-model="batchSettings.order_type"
                    placeholder="选择类型"
                    clearable
                    @change="applyBatchSetting('order_type')"
                  >
                    <el-option label="市价" value="market" />
                    <el-option label="限价" value="limit" />
                    <el-option label="止损" value="stop" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
          </el-collapse-item>
        </el-collapse>
      </div>

      <!-- 提交设置 -->
      <div class="submit-settings">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="提交模式">
              <el-radio-group v-model="submitSettings.mode">
                <el-radio label="parallel">并行提交</el-radio>
                <el-radio label="sequential">顺序提交</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
          
          <el-col :span="12">
            <el-form-item label="失败处理">
              <el-checkbox v-model="submitSettings.stopOnError">
                遇到错误时停止
              </el-checkbox>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="最大失败数">
              <el-input-number
                v-model="submitSettings.maxFailures"
                :min="0"
                :max="batchOrders.length"
              />
            </el-form-item>
          </el-col>
          
          <el-col :span="12">
            <el-form-item label="提交间隔(ms)">
              <el-input-number
                v-model="submitSettings.interval"
                :min="0"
                :max="5000"
                :step="100"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </div>

      <!-- 提交按钮 -->
      <div class="submit-actions">
        <div class="validation-summary">
          <span class="valid-count">有效: {{ validOrders.length }}</span>
          <span class="invalid-count">无效: {{ invalidOrders.length }}</span>
          <span class="total-count">总计: {{ batchOrders.length }}</span>
        </div>
        
        <div class="action-buttons">
          <el-button @click="clearAll">清空全部</el-button>
          <el-button @click="validateAll">验证全部</el-button>
          <el-button
            type="primary"
            :disabled="validOrders.length === 0"
            :loading="submitting"
            @click="submitBatchOrders"
          >
            提交订单 ({{ validOrders.length }})
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 导入对话框 -->
    <el-dialog v-model="showImport" title="导入订单" width="500px">
      <el-upload
        ref="uploadRef"
        :auto-upload="false"
        :on-change="handleFileChange"
        :show-file-list="false"
        accept=".csv,.xlsx,.xls"
        drag
      >
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">
          将文件拖到此处，或<em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持 CSV、Excel 格式，请使用标准模板
          </div>
        </template>
      </el-upload>
      
      <template #footer>
        <el-button @click="showImport = false">取消</el-button>
        <el-button type="primary" @click="processImport" :loading="importing">
          导入
        </el-button>
      </template>
    </el-dialog>

    <!-- 提交进度对话框 -->
    <el-dialog v-model="showProgress" title="提交进度" width="400px" :close-on-click-modal="false">
      <div class="submit-progress">
        <el-progress
          :percentage="submitProgress.percentage"
          :status="submitProgress.status"
        />
        <div class="progress-info">
          <p>{{ submitProgress.message }}</p>
          <p>成功: {{ submitProgress.success }} / 失败: {{ submitProgress.failed }} / 总计: {{ submitProgress.total }}</p>
        </div>
        
        <div v-if="submitProgress.errors.length > 0" class="error-list">
          <h4>错误信息:</h4>
          <ul>
            <li v-for="(error, index) in submitProgress.errors" :key="index">
              {{ error }}
            </li>
          </ul>
        </div>
      </div>
      
      <template #footer>
        <el-button
          v-if="submitProgress.status === 'success' || submitProgress.status === 'exception'"
          @click="showProgress = false"
        >
          关闭
        </el-button>
        <el-button
          v-else
          type="danger"
          @click="cancelSubmit"
        >
          取消提交
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Upload,
  Download,
  Plus,
  UploadFilled
} from '@element-plus/icons-vue'
import { useTradingStore } from '@/stores/trading'
import type { CreateOrderRequest, OrderSide, OrderType, TimeInForce } from '@/types/trading'

const tradingStore = useTradingStore()

// 响应式数据
const selectAll = ref(false)
const selectedOrders = ref<any[]>([])
const submitting = ref(false)
const importing = ref(false)
const showImport = ref(false)
const showProgress = ref(false)
const activeSettings = ref<string[]>([])
const uploadRef = ref()
const importFile = ref<File | null>(null)

// 批量订单数据
const batchOrders = ref<(CreateOrderRequest & { 
  id: string
  status: 'valid' | 'invalid' | 'pending'
  errors: string[]
})[]>([])

// 批量设置
const batchSettings = ref({
  symbol: '',
  side: '',
  order_type: ''
})

// 提交设置
const submitSettings = ref({
  mode: 'parallel' as 'parallel' | 'sequential',
  stopOnError: true,
  maxFailures: 5,
  interval: 100
})

// 提交进度
const submitProgress = ref({
  percentage: 0,
  status: '' as '' | 'success' | 'exception',
  message: '',
  success: 0,
  failed: 0,
  total: 0,
  errors: [] as string[]
})

// 合约选项
const symbolOptions = ref([
  { code: 'SHFE.cu2601', name: '沪铜2601' },
  { code: 'DCE.i2601', name: '铁矿石2601' },
  { code: 'CZCE.MA2601', name: '甲醇2601' },
  { code: 'CFFEX.IF2601', name: '沪深300' }
])

// 计算属性
const isIndeterminate = computed(() => {
  const selected = selectedOrders.value.length
  const total = batchOrders.value.length
  return selected > 0 && selected < total
})

const validOrders = computed(() => {
  return batchOrders.value.filter(order => order.status === 'valid')
})

const invalidOrders = computed(() => {
  return batchOrders.value.filter(order => order.status === 'invalid')
})

// 方法
const addOrder = () => {
  const newOrder = {
    id: Date.now().toString(),
    symbol: '',
    side: 'buy' as OrderSide,
    order_type: 'limit' as OrderType,
    quantity: 1,
    price: undefined,
    time_in_force: 'day' as TimeInForce,
    risk_check: true,
    status: 'pending' as 'valid' | 'invalid' | 'pending',
    errors: []
  }
  
  batchOrders.value.push(newOrder)
}

const deleteOrder = (index: number) => {
  batchOrders.value.splice(index, 1)
  validateAll()
}

const duplicateOrder = (index: number) => {
  const original = batchOrders.value[index]
  const duplicate = {
    ...original,
    id: Date.now().toString(),
    status: 'pending' as 'valid' | 'invalid' | 'pending',
    errors: []
  }
  
  batchOrders.value.splice(index + 1, 0, duplicate)
  validateOrder(index + 1)
}

const handleSelectAll = (checked: boolean) => {
  selectedOrders.value = checked ? [...batchOrders.value] : []
}

const handleSelectionChange = (selection: any[]) => {
  selectedOrders.value = selection
  selectAll.value = selection.length === batchOrders.value.length
}

const duplicateSelected = () => {
  const duplicates = selectedOrders.value.map(order => ({
    ...order,
    id: Date.now().toString() + Math.random(),
    status: 'pending' as 'valid' | 'invalid' | 'pending',
    errors: []
  }))
  
  batchOrders.value.push(...duplicates)
  validateAll()
}

const deleteSelected = async () => {
  try {
    await ElMessageBox.confirm(`确定要删除选中的 ${selectedOrders.value.length} 个订单吗？`, '确认删除', {
      type: 'warning'
    })
    
    const selectedIds = selectedOrders.value.map(order => order.id)
    batchOrders.value = batchOrders.value.filter(order => !selectedIds.includes(order.id))
    selectedOrders.value = []
    selectAll.value = false
    
    validateAll()
  } catch (error) {
    // 用户取消
  }
}

const validateOrder = (index: number) => {
  const order = batchOrders.value[index]
  const errors: string[] = []
  
  if (!order.symbol) {
    errors.push('请选择交易合约')
  }
  
  if (!order.quantity || order.quantity <= 0) {
    errors.push('请输入有效的交易数量')
  }
  
  if (order.order_type !== 'market' && (!order.price || order.price <= 0)) {
    errors.push('请输入有效的委托价格')
  }
  
  order.errors = errors
  order.status = errors.length === 0 ? 'valid' : 'invalid'
}

const validateAll = () => {
  batchOrders.value.forEach((_, index) => {
    validateOrder(index)
  })
}

const applyBatchSetting = (field: string) => {
  const value = (batchSettings.value as any)[field]
  if (!value) return
  
  selectedOrders.value.forEach(order => {
    (order as any)[field] = value
  })
  
  validateAll()
}

const clearAll = async () => {
  try {
    await ElMessageBox.confirm('确定要清空所有订单吗？', '确认清空', {
      type: 'warning'
    })
    
    batchOrders.value = []
    selectedOrders.value = []
    selectAll.value = false
  } catch (error) {
    // 用户取消
  }
}

const importOrders = () => {
  showImport.value = true
}

const exportTemplate = () => {
  // 创建模板数据
  const template = [
    ['合约代码', '交易方向', '订单类型', '交易数量', '委托价格', '有效期'],
    ['SHFE.cu2601', 'buy', 'limit', '1', '68500', 'day'],
    ['DCE.i2601', 'sell', 'market', '2', '', 'ioc']
  ]
  
  // 转换为CSV格式
  const csvContent = template.map(row => row.join(',')).join('\n')
  const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' })
  
  // 下载文件
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = '批量订单模板.csv'
  link.click()
  
  URL.revokeObjectURL(link.href)
}

const handleFileChange = (file: any) => {
  importFile.value = file.raw
}

const processImport = async () => {
  if (!importFile.value) {
    ElMessage.error('请选择要导入的文件')
    return
  }
  
  try {
    importing.value = true
    
    // 这里应该解析文件内容
    // const orders = await parseImportFile(importFile.value)
    
    // 模拟导入数据
    const importedOrders = [
      {
        id: Date.now().toString(),
        symbol: 'SHFE.cu2601',
        side: 'buy' as OrderSide,
        order_type: 'limit' as OrderType,
        quantity: 1,
        price: 68500,
        time_in_force: 'day' as TimeInForce,
        risk_check: true,
        status: 'pending' as 'valid' | 'invalid' | 'pending',
        errors: []
      }
    ]
    
    batchOrders.value.push(...importedOrders)
    validateAll()
    
    showImport.value = false
    importFile.value = null
    
    ElMessage.success(`成功导入 ${importedOrders.length} 个订单`)
  } catch (error: any) {
    ElMessage.error(error.message || '导入失败')
  } finally {
    importing.value = false
  }
}

const submitBatchOrders = async () => {
  if (validOrders.value.length === 0) {
    ElMessage.error('没有有效的订单可以提交')
    return
  }
  
  try {
    await ElMessageBox.confirm(`确定要提交 ${validOrders.value.length} 个订单吗？`, '确认提交', {
      type: 'warning'
    })
    
    submitting.value = true
    showProgress.value = true
    
    // 重置进度
    submitProgress.value = {
      percentage: 0,
      status: '',
      message: '开始提交订单...',
      success: 0,
      failed: 0,
      total: validOrders.value.length,
      errors: []
    }
    
    if (submitSettings.value.mode === 'parallel') {
      await submitParallel()
    } else {
      await submitSequential()
    }
    
    submitProgress.value.status = submitProgress.value.failed === 0 ? 'success' : 'exception'
    submitProgress.value.message = `提交完成！成功: ${submitProgress.value.success}, 失败: ${submitProgress.value.failed}`
    
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('提交失败')
    }
  } finally {
    submitting.value = false
  }
}

const submitParallel = async () => {
  const promises = validOrders.value.map(async (order, index) => {
    try {
      await tradingStore.createOrder(order)
      submitProgress.value.success++
      submitProgress.value.percentage = Math.round(((submitProgress.value.success + submitProgress.value.failed) / submitProgress.value.total) * 100)
      submitProgress.value.message = `正在提交订单... (${submitProgress.value.success + submitProgress.value.failed}/${submitProgress.value.total})`
    } catch (error: any) {
      submitProgress.value.failed++
      submitProgress.value.errors.push(`订单 ${index + 1}: ${error.message}`)
      
      if (submitSettings.value.stopOnError || submitProgress.value.failed >= submitSettings.value.maxFailures) {
        throw new Error('达到最大失败数或遇到错误停止')
      }
    }
  })
  
  await Promise.allSettled(promises)
}

const submitSequential = async () => {
  for (let i = 0; i < validOrders.value.length; i++) {
    const order = validOrders.value[i]
    
    try {
      await tradingStore.createOrder(order)
      submitProgress.value.success++
    } catch (error: any) {
      submitProgress.value.failed++
      submitProgress.value.errors.push(`订单 ${i + 1}: ${error.message}`)
      
      if (submitSettings.value.stopOnError || submitProgress.value.failed >= submitSettings.value.maxFailures) {
        break
      }
    }
    
    submitProgress.value.percentage = Math.round(((submitProgress.value.success + submitProgress.value.failed) / submitProgress.value.total) * 100)
    submitProgress.value.message = `正在提交订单... (${submitProgress.value.success + submitProgress.value.failed}/${submitProgress.value.total})`
    
    // 添加间隔
    if (i < validOrders.value.length - 1 && submitSettings.value.interval > 0) {
      await new Promise(resolve => setTimeout(resolve, submitSettings.value.interval))
    }
  }
}

const cancelSubmit = () => {
  submitting.value = false
  showProgress.value = false
  ElMessage.info('提交已取消')
}

const getStatusType = (status: string) => {
  const typeMap = {
    valid: 'success',
    invalid: 'danger',
    pending: 'warning'
  }
  return typeMap[status as keyof typeof typeMap] || 'info'
}

const getStatusText = (status: string) => {
  const textMap = {
    valid: '有效',
    invalid: '无效',
    pending: '待验证'
  }
  return textMap[status as keyof typeof textMap] || status
}

// 监听器
watch(selectedOrders, (newVal) => {
  selectAll.value = newVal.length === batchOrders.value.length && batchOrders.value.length > 0
})

// 初始化
addOrder()
</script>

<style scoped lang="scss">
.batch-order-management {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .header-actions {
      display: flex;
      gap: 8px;
    }
  }
  
  .batch-toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 0;
    border-bottom: 1px solid #e4e7ed;
    margin-bottom: 16px;
    
    .toolbar-left {
      display: flex;
      align-items: center;
      gap: 16px;
      
      .selected-count {
        color: #606266;
        font-size: 14px;
      }
    }
    
    .toolbar-right {
      display: flex;
      gap: 8px;
    }
  }
  
  .order-list {
    margin-bottom: 16px;
    
    .el-table {
      .el-select,
      .el-input-number {
        width: 100%;
      }
    }
  }
  
  .batch-settings {
    margin-bottom: 16px;
  }
  
  .submit-settings {
    margin-bottom: 16px;
    padding: 16px;
    background: var(--el-bg-color-page);
    border-radius: 6px;
  }
  
  .submit-actions {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .validation-summary {
      display: flex;
      gap: 16px;
      
      .valid-count {
        color: #67c23a;
        font-weight: 600;
      }
      
      .invalid-count {
        color: #f56c6c;
        font-weight: 600;
      }
      
      .total-count {
        color: #606266;
        font-weight: 600;
      }
    }
    
    .action-buttons {
      display: flex;
      gap: 8px;
    }
  }
  
  .submit-progress {
    .progress-info {
      margin-top: 16px;
      text-align: center;
      
      p {
        margin: 8px 0;
        color: #606266;
      }
    }
    
    .error-list {
      margin-top: 16px;
      max-height: 200px;
      overflow-y: auto;
      
      h4 {
        margin: 0 0 8px 0;
        color: #f56c6c;
      }
      
      ul {
        margin: 0;
        padding-left: 20px;
        
        li {
          color: #f56c6c;
          font-size: 12px;
          line-height: 1.4;
          margin-bottom: 4px;
        }
      }
    }
  }
}
</style>