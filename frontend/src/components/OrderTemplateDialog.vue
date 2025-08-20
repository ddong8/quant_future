<template>
  <el-dialog
    v-model="visible"
    title="订单模板"
    width="600px"
    :before-close="handleClose"
  >
    <div class="order-template">
      <el-tabs v-model="activeTab">
        <!-- 使用模板 -->
        <el-tab-pane label="使用模板" name="use">
          <div class="template-list">
            <div
              v-for="template in templates"
              :key="template.id"
              class="template-item"
              @click="selectTemplate(template)"
            >
              <div class="template-header">
                <span class="template-name">{{ template.name }}</span>
                <div class="template-actions">
                  <el-button text size="small" @click.stop="editTemplate(template)">
                    <el-icon><Edit /></el-icon>
                  </el-button>
                  <el-button text size="small" @click.stop="deleteTemplate(template.id)">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </div>
              </div>
              <div class="template-content">
                <div class="template-info">
                  <span class="info-item">
                    <span class="label">合约:</span>
                    <span class="value">{{ template.symbol || '未设置' }}</span>
                  </span>
                  <span class="info-item">
                    <span class="label">方向:</span>
                    <span class="value" :class="template.side">
                      {{ template.side === 'buy' ? '买入' : '卖出' }}
                    </span>
                  </span>
                  <span class="info-item">
                    <span class="label">类型:</span>
                    <span class="value">{{ getOrderTypeText(template.order_type) }}</span>
                  </span>
                  <span class="info-item">
                    <span class="label">数量:</span>
                    <span class="value">{{ template.quantity }}手</span>
                  </span>
                </div>
                <div class="template-description">
                  {{ template.description || '无描述' }}
                </div>
              </div>
            </div>
            
            <div v-if="templates.length === 0" class="empty-templates">
              <el-empty description="暂无订单模板" />
            </div>
          </div>
        </el-tab-pane>
        
        <!-- 创建模板 -->
        <el-tab-pane label="创建模板" name="create">
          <el-form
            ref="templateFormRef"
            :model="templateForm"
            :rules="templateRules"
            label-width="100px"
          >
            <el-form-item label="模板名称" prop="name">
              <el-input
                v-model="templateForm.name"
                placeholder="请输入模板名称"
                maxlength="50"
              />
            </el-form-item>
            
            <el-form-item label="模板描述">
              <el-input
                v-model="templateForm.description"
                type="textarea"
                placeholder="请输入模板描述（可选）"
                :rows="3"
                maxlength="200"
              />
            </el-form-item>
            
            <el-form-item label="交易合约" prop="symbol">
              <el-input
                v-model="templateForm.symbol"
                placeholder="请输入合约代码，留空表示使用时选择"
              />
            </el-form-item>
            
            <el-form-item label="交易方向" prop="side">
              <el-radio-group v-model="templateForm.side">
                <el-radio label="buy">买入</el-radio>
                <el-radio label="sell">卖出</el-radio>
              </el-radio-group>
            </el-form-item>
            
            <el-form-item label="订单类型" prop="order_type">
              <el-select v-model="templateForm.order_type">
                <el-option label="市价单" value="market" />
                <el-option label="限价单" value="limit" />
                <el-option label="止损单" value="stop" />
                <el-option label="止损限价单" value="stop_limit" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="交易数量" prop="quantity">
              <el-input-number
                v-model="templateForm.quantity"
                :min="1"
                :max="1000"
                style="width: 100%"
              />
            </el-form-item>
            
            <el-form-item label="委托价格">
              <el-input-number
                v-model="templateForm.price"
                :min="0"
                :precision="2"
                placeholder="留空表示使用时设置"
                style="width: 100%"
              />
            </el-form-item>
            
            <el-form-item label="有效期" prop="time_in_force">
              <el-select v-model="templateForm.time_in_force">
                <el-option label="当日有效" value="day" />
                <el-option label="撤销前有效" value="gtc" />
                <el-option label="立即成交或撤销" value="ioc" />
                <el-option label="全部成交或撤销" value="fok" />
              </el-select>
            </el-form-item>
            
            <el-form-item>
              <el-checkbox v-model="templateForm.risk_check">
                启用风险检查
              </el-checkbox>
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="saveTemplate" :loading="saving">
                保存模板
              </el-button>
              <el-button @click="resetTemplateForm">重置</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">关闭</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Edit, Delete } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import type { OrderType, TimeInForce } from '@/types/trading'

interface OrderTemplate {
  id: number
  name: string
  description?: string
  symbol?: string
  side: 'buy' | 'sell'
  order_type: OrderType
  quantity: number
  price?: number
  time_in_force: TimeInForce
  risk_check: boolean
  created_at: string
}

interface Props {
  modelValue: boolean
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'select', template: Partial<OrderTemplate>): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 响应式数据
const activeTab = ref('use')
const saving = ref(false)
const templates = ref<OrderTemplate[]>([])
const templateFormRef = ref<FormInstance>()

// 模板表单
const templateForm = ref({
  name: '',
  description: '',
  symbol: '',
  side: 'buy' as 'buy' | 'sell',
  order_type: 'limit' as OrderType,
  quantity: 1,
  price: undefined as number | undefined,
  time_in_force: 'day' as TimeInForce,
  risk_check: true
})

// 表单验证规则
const templateRules: FormRules = {
  name: [
    { required: true, message: '请输入模板名称', trigger: 'blur' },
    { min: 2, max: 50, message: '模板名称长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  side: [
    { required: true, message: '请选择交易方向', trigger: 'change' }
  ],
  order_type: [
    { required: true, message: '请选择订单类型', trigger: 'change' }
  ],
  quantity: [
    { required: true, message: '请输入交易数量', trigger: 'blur' },
    { type: 'number', min: 1, message: '数量必须大于0', trigger: 'blur' }
  ],
  time_in_force: [
    { required: true, message: '请选择有效期', trigger: 'change' }
  ]
}

// 计算属性
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// 方法
const loadTemplates = async () => {
  try {
    // 加载订单模板
    // const response = await tradingApi.getOrderTemplates()
    // templates.value = response.data
    
    // 模拟数据
    templates.value = [
      {
        id: 1,
        name: '沪铜买入模板',
        description: '沪铜期货买入限价单模板',
        symbol: 'SHFE.cu2601',
        side: 'buy',
        order_type: 'limit',
        quantity: 1,
        time_in_force: 'day',
        risk_check: true,
        created_at: new Date().toISOString()
      },
      {
        id: 2,
        name: '快速市价单',
        description: '快速市价交易模板',
        side: 'buy',
        order_type: 'market',
        quantity: 1,
        time_in_force: 'ioc',
        risk_check: true,
        created_at: new Date().toISOString()
      }
    ]
  } catch (error) {
    ElMessage.error('加载模板失败')
  }
}

const selectTemplate = (template: OrderTemplate) => {
  const { id, name, description, created_at, ...orderData } = template
  emit('select', orderData)
  handleClose()
}

const editTemplate = (template: OrderTemplate) => {
  const { id, created_at, ...formData } = template
  Object.assign(templateForm.value, formData)
  activeTab.value = 'create'
}

const deleteTemplate = async (templateId: number) => {
  try {
    await ElMessageBox.confirm('确定要删除这个模板吗？', '确认删除', {
      type: 'warning'
    })
    
    // 删除模板
    // await tradingApi.deleteOrderTemplate(templateId)
    
    templates.value = templates.value.filter(t => t.id !== templateId)
    ElMessage.success('模板删除成功')
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除模板失败')
    }
  }
}

const saveTemplate = async () => {
  if (!templateFormRef.value) return
  
  try {
    await templateFormRef.value.validate()
    saving.value = true
    
    // 保存模板
    // await tradingApi.createOrderTemplate(templateForm.value)
    
    ElMessage.success('模板保存成功')
    resetTemplateForm()
    loadTemplates()
    activeTab.value = 'use'
  } catch (error: any) {
    if (error !== 'validation') {
      ElMessage.error('保存模板失败')
    }
  } finally {
    saving.value = false
  }
}

const resetTemplateForm = () => {
  templateForm.value = {
    name: '',
    description: '',
    symbol: '',
    side: 'buy',
    order_type: 'limit',
    quantity: 1,
    price: undefined,
    time_in_force: 'day',
    risk_check: true
  }
  templateFormRef.value?.clearValidate()
}

const getOrderTypeText = (type: OrderType) => {
  const typeMap = {
    market: '市价单',
    limit: '限价单',
    stop: '止损单',
    stop_limit: '止损限价单',
    trailing_stop: '跟踪止损单'
  }
  return typeMap[type] || type
}

const handleClose = () => {
  visible.value = false
  resetTemplateForm()
  activeTab.value = 'use'
}

// 生命周期
onMounted(() => {
  loadTemplates()
})
</script>

<style scoped lang="scss">
.order-template {
  .template-list {
    max-height: 400px;
    overflow-y: auto;
    
    .template-item {
      border: 1px solid #e4e7ed;
      border-radius: 6px;
      padding: 16px;
      margin-bottom: 12px;
      cursor: pointer;
      transition: all 0.3s;
      
      &:hover {
        border-color: #409eff;
        box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
      }
      
      &:last-child {
        margin-bottom: 0;
      }
      
      .template-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
        
        .template-name {
          font-size: 16px;
          font-weight: 600;
          color: #303133;
        }
        
        .template-actions {
          display: flex;
          gap: 4px;
        }
      }
      
      .template-content {
        .template-info {
          display: flex;
          flex-wrap: wrap;
          gap: 16px;
          margin-bottom: 8px;
          
          .info-item {
            display: flex;
            align-items: center;
            gap: 4px;
            
            .label {
              color: #909399;
              font-size: 12px;
            }
            
            .value {
              color: #303133;
              font-size: 12px;
              font-weight: 600;
              
              &.buy {
                color: #f56c6c;
              }
              
              &.sell {
                color: #67c23a;
              }
            }
          }
        }
        
        .template-description {
          color: #606266;
          font-size: 12px;
          line-height: 1.4;
        }
      }
    }
    
    .empty-templates {
      text-align: center;
      padding: 40px 0;
    }
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
}
</style>