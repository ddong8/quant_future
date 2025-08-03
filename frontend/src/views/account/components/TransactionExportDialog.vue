<template>
  <el-dialog
    v-model="visible"
    title="导出交易流水"
    width="600px"
    :before-close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="exportForm"
      :rules="rules"
      label-width="120px"
    >
      <el-form-item label="导出格式" prop="format">
        <el-radio-group v-model="exportForm.format">
          <el-radio label="csv">CSV</el-radio>
          <el-radio label="excel">Excel</el-radio>
          <el-radio label="json">JSON</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item label="时间范围" prop="dateRange">
        <el-date-picker
          v-model="exportForm.dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          style="width: 100%"
        />
      </el-form-item>

      <el-form-item label="交易类型">
        <el-select
          v-model="exportForm.transactionTypes"
          multiple
          placeholder="选择交易类型（不选则导出全部）"
          style="width: 100%"
          collapse-tags
          collapse-tags-tooltip
        >
          <el-option
            v-for="(label, value) in TransactionTypeLabels"
            :key="value"
            :label="label"
            :value="value"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="交易状态">
        <el-select
          v-model="exportForm.statusList"
          multiple
          placeholder="选择交易状态（不选则导出全部）"
          style="width: 100%"
          collapse-tags
          collapse-tags-tooltip
        >
          <el-option
            v-for="(label, value) in TransactionStatusLabels"
            :key="value"
            :label="label"
            :value="value"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="账户筛选">
        <el-select
          v-model="exportForm.accountIds"
          multiple
          placeholder="选择账户（不选则导出全部账户）"
          style="width: 100%"
          collapse-tags
          collapse-tags-tooltip
        >
          <el-option
            v-for="account in accounts"
            :key="account.id"
            :label="`${account.account_name} (${account.account_number})`"
            :value="account.id"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="金额范围">
        <el-row :gutter="12">
          <el-col :span="12">
            <el-input-number
              v-model="exportForm.minAmount"
              placeholder="最小金额"
              :precision="2"
              controls-position="right"
              style="width: 100%"
            />
          </el-col>
          <el-col :span="12">
            <el-input-number
              v-model="exportForm.maxAmount"
              placeholder="最大金额"
              :precision="2"
              controls-position="right"
              style="width: 100%"
            />
          </el-col>
        </el-row>
      </el-form-item>

      <el-form-item label="交易标的">
        <el-input
          v-model="exportForm.symbol"
          placeholder="输入交易标的代码"
        />
      </el-form-item>

      <el-form-item label="导出限制">
        <el-alert
          title="导出限制说明"
          type="info"
          :closable="false"
          show-icon
        >
          <template #default>
            <ul class="export-limits">
              <li>单次最多导出50,000条记录</li>
              <li>Excel格式建议不超过10,000条记录以确保性能</li>
              <li>大量数据建议使用CSV格式</li>
              <li>导出文件将包含所有交易详细信息</li>
            </ul>
          </template>
        </el-alert>
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button 
          type="primary" 
          :loading="exporting"
          @click="handleExport"
        >
          {{ exporting ? '导出中...' : '开始导出' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import {
  exportTransactions,
  type TransactionSearchParams,
  TransactionTypeLabels,
  TransactionStatusLabels
} from '@/api/transaction'
import { getAccounts, type Account } from '@/api/account'

interface Props {
  modelValue: boolean
  searchParams?: TransactionSearchParams
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 响应式数据
const formRef = ref<FormInstance>()
const exporting = ref(false)
const accounts = ref<Account[]>([])

// 导出表单
const exportForm = reactive({
  format: 'csv',
  dateRange: null as [string, string] | null,
  transactionTypes: [] as string[],
  statusList: [] as string[],
  accountIds: [] as number[],
  minAmount: undefined as number | undefined,
  maxAmount: undefined as number | undefined,
  symbol: ''
})

// 表单验证规则
const rules: FormRules = {
  format: [
    { required: true, message: '请选择导出格式', trigger: 'change' }
  ]
}

// 计算属性
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// 方法
const handleClose = () => {
  visible.value = false
}

const loadAccounts = async () => {
  try {
    const result = await getAccounts()
    accounts.value = result
  } catch (error) {
    console.error('加载账户列表失败:', error)
  }
}

const handleExport = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    
    // 确认导出
    await ElMessageBox.confirm(
      '确定要导出交易流水吗？大量数据可能需要较长时间。',
      '确认导出',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    exporting.value = true

    // 构建导出参数
    const params: any = {}
    
    if (exportForm.accountIds.length > 0) {
      params.account_ids = exportForm.accountIds
    }
    
    if (exportForm.transactionTypes.length > 0) {
      params.transaction_types = exportForm.transactionTypes
    }
    
    if (exportForm.dateRange) {
      params.start_date = exportForm.dateRange[0]
      params.end_date = exportForm.dateRange[1]
    }
    
    if (exportForm.minAmount !== undefined) {
      params.min_amount = exportForm.minAmount
    }
    
    if (exportForm.maxAmount !== undefined) {
      params.max_amount = exportForm.maxAmount
    }
    
    if (exportForm.symbol) {
      params.symbol = exportForm.symbol
    }

    // 执行导出
    const blob = await exportTransactions(exportForm.format, params)
    
    // 创建下载链接
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    
    // 生成文件名
    const timestamp = new Date().toISOString().slice(0, 19).replace(/[:-]/g, '')
    const extension = exportForm.format === 'excel' ? 'xlsx' : exportForm.format
    link.download = `transactions_${timestamp}.${extension}`
    
    // 触发下载
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('导出成功')
    handleClose()
    
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('导出失败:', error)
      ElMessage.error(error.message || '导出失败')
    }
  } finally {
    exporting.value = false
  }
}

// 初始化表单数据
const initializeForm = () => {
  if (props.searchParams) {
    // 从搜索参数初始化表单
    if (props.searchParams.account_ids) {
      exportForm.accountIds = [...props.searchParams.account_ids]
    }
    
    if (props.searchParams.transaction_types) {
      exportForm.transactionTypes = [...props.searchParams.transaction_types]
    }
    
    if (props.searchParams.status_list) {
      exportForm.statusList = [...props.searchParams.status_list]
    }
    
    if (props.searchParams.start_date && props.searchParams.end_date) {
      exportForm.dateRange = [props.searchParams.start_date, props.searchParams.end_date]
    }
    
    if (props.searchParams.min_amount !== undefined) {
      exportForm.minAmount = props.searchParams.min_amount
    }
    
    if (props.searchParams.max_amount !== undefined) {
      exportForm.maxAmount = props.searchParams.max_amount
    }
    
    if (props.searchParams.symbol) {
      exportForm.symbol = props.searchParams.symbol
    }
  }
}

// 监听对话框打开
const handleDialogOpen = () => {
  initializeForm()
}

// 生命周期
onMounted(() => {
  loadAccounts()
})

// 监听visible变化
computed(() => {
  if (visible.value) {
    handleDialogOpen()
  }
})
</script>

<style scoped>
.export-limits {
  margin: 0;
  padding-left: 20px;
}

.export-limits li {
  margin-bottom: 4px;
  color: #606266;
  font-size: 13px;
}

.export-limits li:last-child {
  margin-bottom: 0;
}

.dialog-footer {
  text-align: right;
}
</style>