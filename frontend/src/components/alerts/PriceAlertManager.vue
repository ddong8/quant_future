<template>
  <div class="price-alert-manager">
    <!-- 头部工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <h3>价格提醒</h3>
      </div>
      <div class="toolbar-right">
        <el-button type="primary" @click="showCreateDialog = true">
          <el-icon><Plus /></el-icon>
          新建提醒
        </el-button>
        <el-button @click="refreshAlerts" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 筛选器 -->
    <div class="filter-bar">
      <el-form :model="filters" inline>
        <el-form-item label="状态">
          <el-select v-model="filters.isActive" placeholder="全部" clearable style="width: 120px" @change="loadAlerts">
            <el-option label="全部" :value="null" />
            <el-option label="启用" :value="true" />
            <el-option label="停用" :value="false" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="类型">
          <el-select v-model="filters.alertType" placeholder="全部" clearable style="width: 150px" @change="loadAlerts">
            <el-option label="全部" value="" />
            <el-option label="价格突破" value="PRICE_ABOVE" />
            <el-option label="价格跌破" value="PRICE_BELOW" />
            <el-option label="涨跌幅" value="CHANGE_PERCENT" />
            <el-option label="成交量" value="VOLUME" />
          </el-select>
        </el-form-item>
      </el-form>
    </div>

    <!-- 提醒列表 -->
    <el-table :data="filteredAlerts" :loading="loading" stripe>
      <!-- 标的 -->
      <el-table-column label="标的" width="120">
        <template #default="{ row }">
          <div class="symbol-info">
            <div class="symbol-code">{{ row.symbol.symbol }}</div>
            <div class="symbol-name">{{ row.symbol.name }}</div>
          </div>
        </template>
      </el-table-column>

      <!-- 提醒条件 -->
      <el-table-column label="提醒条件" width="200">
        <template #default="{ row }">
          <div class="condition-info">
            <span class="condition-text">
              {{ getAlertTypeText(row.alert_type) }}
              {{ row.comparison_operator }}
              {{ formatConditionValue(row.condition_value, row.alert_type) }}
            </span>
          </div>
        </template>
      </el-table-column>

      <!-- 状态 -->
      <el-table-column label="状态" width="80" align="center">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
            {{ row.is_active ? '启用' : '停用' }}
          </el-tag>
        </template>
      </el-table-column>

      <!-- 触发信息 -->
      <el-table-column label="触发信息" width="150">
        <template #default="{ row }">
          <div v-if="row.triggered_at" class="trigger-info">
            <div class="trigger-price">{{ formatPrice(row.triggered_price) }}</div>
            <div class="trigger-time">{{ formatTime(row.triggered_at) }}</div>
            <div class="trigger-count">触发 {{ row.trigger_count }} 次</div>
          </div>
          <span v-else class="no-trigger">未触发</span>
        </template>
      </el-table-column>

      <!-- 通知方式 -->
      <el-table-column label="通知方式" width="120">
        <template #default="{ row }">
          <div class="notification-methods">
            <el-tag
              v-for="method in row.notification_methods"
              :key="method"
              size="small"
              style="margin-right: 4px"
            >
              {{ getNotificationMethodText(method) }}
            </el-tag>
          </div>
        </template>
      </el-table-column>

      <!-- 过期时间 -->
      <el-table-column label="过期时间" width="120">
        <template #default="{ row }">
          <span v-if="row.expires_at" class="expire-time">
            {{ formatTime(row.expires_at) }}
          </span>
          <span v-else class="no-expire">永不过期</span>
        </template>
      </el-table-column>

      <!-- 备注 -->
      <el-table-column label="备注" min-width="150">
        <template #default="{ row }">
          <span class="note">{{ row.note || '--' }}</span>
        </template>
      </el-table-column>

      <!-- 操作 -->
      <el-table-column label="操作" width="150" align="center" fixed="right">
        <template #default="{ row }">
          <el-button size="small" text @click="editAlert(row)">
            编辑
          </el-button>
          <el-button 
            size="small" 
            text 
            :type="row.is_active ? 'warning' : 'success'"
            @click="toggleAlert(row)"
          >
            {{ row.is_active ? '停用' : '启用' }}
          </el-button>
          <el-button size="small" text type="danger" @click="deleteAlert(row)">
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 创建/编辑提醒对话框 -->
    <PriceAlertDialog
      v-model="showCreateDialog"
      :alert-data="editingAlert"
      @save="handleAlertSave"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'
import { getUserAlerts, updatePriceAlert, deletePriceAlert, type PriceAlert } from '@/api/marketDepth'
import { formatPrice, formatTime } from '@/utils/format'
import PriceAlertDialog from './PriceAlertDialog.vue'

// 响应式数据
const loading = ref(false)
const showCreateDialog = ref(false)
const editingAlert = ref<PriceAlert | null>(null)
const alerts = ref<PriceAlert[]>([])

// 筛选条件
const filters = ref({
  isActive: null as boolean | null,
  alertType: ''
})

// 筛选后的提醒列表
const filteredAlerts = computed(() => {
  let result = alerts.value

  if (filters.value.alertType) {
    result = result.filter(alert => alert.alert_type === filters.value.alertType)
  }

  return result
})

// 加载提醒列表
const loadAlerts = async () => {
  try {
    loading.value = true
    const response = await getUserAlerts(filters.value.isActive)
    alerts.value = response.data.alerts
  } catch (error) {
    console.error('加载价格提醒失败:', error)
    ElMessage.error('加载价格提醒失败')
  } finally {
    loading.value = false
  }
}

// 刷新提醒列表
const refreshAlerts = () => {
  loadAlerts()
}

// 编辑提醒
const editAlert = (alert: PriceAlert) => {
  editingAlert.value = alert
  showCreateDialog.value = true
}

// 切换提醒状态
const toggleAlert = async (alert: PriceAlert) => {
  try {
    await updatePriceAlert(alert.id, {
      is_active: !alert.is_active
    })
    
    ElMessage.success(`提醒已${alert.is_active ? '停用' : '启用'}`)
    loadAlerts()
  } catch (error) {
    console.error('更新提醒状态失败:', error)
    ElMessage.error('更新提醒状态失败')
  }
}

// 删除提醒
const deleteAlert = async (alert: PriceAlert) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除 ${alert.symbol.symbol} 的价格提醒吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await deletePriceAlert(alert.id)
    ElMessage.success('提醒删除成功')
    loadAlerts()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除提醒失败:', error)
      ElMessage.error('删除提醒失败')
    }
  }
}

// 处理提醒保存
const handleAlertSave = () => {
  showCreateDialog.value = false
  editingAlert.value = null
  loadAlerts()
}

// 获取提醒类型文本
const getAlertTypeText = (type: string) => {
  switch (type) {
    case 'PRICE_ABOVE': return '价格突破'
    case 'PRICE_BELOW': return '价格跌破'
    case 'CHANGE_PERCENT': return '涨跌幅'
    case 'VOLUME': return '成交量'
    default: return type
  }
}

// 获取通知方式文本
const getNotificationMethodText = (method: string) => {
  switch (method) {
    case 'websocket': return '站内'
    case 'email': return '邮件'
    case 'sms': return '短信'
    case 'push': return '推送'
    default: return method
  }
}

// 格式化条件值
const formatConditionValue = (value: number, type: string) => {
  switch (type) {
    case 'PRICE_ABOVE':
    case 'PRICE_BELOW':
      return formatPrice(value)
    case 'CHANGE_PERCENT':
      return `${value}%`
    case 'VOLUME':
      return value.toLocaleString()
    default:
      return value.toString()
  }
}

// 组件挂载
onMounted(() => {
  loadAlerts()
})
</script>

<style scoped>
.price-alert-manager {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #e4e7ed;
}

.toolbar h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.toolbar-right {
  display: flex;
  gap: 8px;
}

.filter-bar {
  padding: 16px;
  background: #f8f9fa;
  border-bottom: 1px solid #e4e7ed;
}

.symbol-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.symbol-code {
  font-weight: 600;
  color: #303133;
}

.symbol-name {
  font-size: 12px;
  color: #909399;
}

.condition-info {
  font-size: 14px;
}

.condition-text {
  color: #303133;
  font-weight: 500;
}

.trigger-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.trigger-price {
  font-weight: 600;
  color: #409eff;
  font-family: 'Courier New', monospace;
}

.trigger-time {
  font-size: 12px;
  color: #909399;
}

.trigger-count {
  font-size: 12px;
  color: #67c23a;
}

.no-trigger {
  color: #c0c4cc;
  font-size: 12px;
}

.notification-methods {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.expire-time {
  font-size: 12px;
  color: #909399;
}

.no-expire {
  color: #c0c4cc;
  font-size: 12px;
}

.note {
  color: #606266;
  font-size: 12px;
}

:deep(.el-table__row:hover) {
  background-color: #f5f7fa;
}
</style>