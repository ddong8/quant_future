<template>
  <div class="order-templates-view">
    <div class="page-header">
      <h1 class="page-title">📝 订单模板</h1>
      <p class="page-description">管理和使用订单模板，提高交易效率</p>
    </div>

    <!-- 操作按钮 -->
    <div class="actions-card">
      <h3>🚀 快速操作</h3>
      <div class="actions">
        <button class="action-btn primary" @click="createTemplate">
          ➕ 创建模板
        </button>
        <button class="action-btn" @click="importTemplate">
          📥 导入模板
        </button>
        <button class="action-btn" @click="exportTemplates">
          📤 导出模板
        </button>
      </div>
    </div>

    <!-- 模板列表 -->
    <div class="templates-list">
      <h3>📋 模板列表</h3>
      <div v-if="templates.length === 0" class="empty-state">
        <div class="empty-icon">📝</div>
        <div class="empty-text">暂无订单模板</div>
        <button class="create-first-btn" @click="createTemplate">创建第一个模板</button>
      </div>
      <div v-else class="templates-grid">
        <div v-for="template in templates" :key="template.id" class="template-card">
          <div class="template-header">
            <span class="template-name">{{ template.name }}</span>
            <span class="template-type" :class="template.type">
              {{ getTypeText(template.type) }}
            </span>
          </div>
          <div class="template-content">
            <div class="template-info">
              <div class="info-row">
                <span class="label">品种:</span>
                <span class="value">{{ template.symbol }}</span>
              </div>
              <div class="info-row">
                <span class="label">方向:</span>
                <span class="value" :class="template.side">
                  {{ template.side === 'buy' ? '买入' : '卖出' }}
                </span>
              </div>
              <div class="info-row">
                <span class="label">数量:</span>
                <span class="value">{{ template.quantity }}</span>
              </div>
              <div class="info-row">
                <span class="label">价格:</span>
                <span class="value">{{ template.price ? formatNumber(template.price) : '市价' }}</span>
              </div>
            </div>
            <div class="template-actions">
              <button class="btn-small primary" @click="useTemplate(template)">
                🚀 使用
              </button>
              <button class="btn-small" @click="editTemplate(template)">
                ✏️ 编辑
              </button>
              <button class="btn-small danger" @click="deleteTemplate(template)">
                🗑️ 删除
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { request } from '@/utils/request'

// 订单模板数据
const templates = ref([])

// 加载订单模板
const loadTemplates = async () => {
  try {
    // 这里可以调用真实的API获取模板数据
    // 目前使用本地存储的模板数据
    const savedTemplates = localStorage.getItem('order_templates')
    if (savedTemplates) {
      templates.value = JSON.parse(savedTemplates)
    } else {
      loadDefaultTemplates()
    }
  } catch (error) {
    console.error('加载模板失败:', error)
    loadDefaultTemplates()
  }
}

// 加载默认模板
const loadDefaultTemplates = () => {
  templates.value = [
    {
      id: 'TPL001',
      name: '沪铜买入模板',
      symbol: 'SHFE.cu2601',
      side: 'buy',
      type: 'limit',
      quantity: 1,
      price: 71000,
      description: '沪铜限价买入模板'
    },
    {
      id: 'TPL002',
      name: '铁矿石卖出模板',
      symbol: 'DCE.i2601',
      side: 'sell',
      type: 'limit',
      quantity: 2,
      price: 850,
      description: '铁矿石限价卖出模板'
    },
    {
      id: 'TPL003',
      name: '甲醇市价买入',
      symbol: 'CZCE.MA601',
      side: 'buy',
      type: 'market',
      quantity: 1,
      price: null,
      description: '甲醇市价买入模板'
    }
  ]
  saveTemplates()
}

// 保存模板到本地存储
const saveTemplates = () => {
  try {
    localStorage.setItem('order_templates', JSON.stringify(templates.value))
  } catch (error) {
    console.error('保存模板失败:', error)
  }
}

// 工具函数
const formatNumber = (num: number) => {
  return new Intl.NumberFormat('zh-CN', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2
  }).format(num)
}

const getTypeText = (type: string) => {
  const typeMap: Record<string, string> = {
    market: '市价单',
    limit: '限价单',
    stop: '止损单'
  }
  return typeMap[type] || type
}

// 页面操作
const createTemplate = () => {
  console.log('📝 创建订单模板')
  const name = prompt('请输入模板名称:')
  if (!name) return
  
  const symbol = prompt('请输入交易品种 (如: SHFE.cu2601):')
  if (!symbol) return
  
  const side = prompt('请输入交易方向 (buy/sell):')
  if (!side || !['buy', 'sell'].includes(side)) return
  
  const type = prompt('请输入订单类型 (market/limit):')
  if (!type || !['market', 'limit'].includes(type)) return
  
  const quantity = prompt('请输入交易数量:')
  if (!quantity || isNaN(Number(quantity))) return
  
  let price = null
  if (type === 'limit') {
    const priceStr = prompt('请输入限价价格:')
    if (!priceStr || isNaN(Number(priceStr))) return
    price = Number(priceStr)
  }
  
  const newTemplate = {
    id: `TPL${Date.now()}`,
    name,
    symbol,
    side,
    type,
    quantity: Number(quantity),
    price,
    description: `${name} - ${symbol} ${side === 'buy' ? '买入' : '卖出'}`
  }
  
  templates.value.push(newTemplate)
  saveTemplates()
  ElMessage.success(`模板 "${name}" 创建成功！`)
}

const importTemplate = () => {
  console.log('📥 导入模板')
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.json'
  input.onchange = async (e) => {
    const file = e.target.files[0]
    if (file) {
      try {
        const text = await file.text()
        const importedTemplates = JSON.parse(text)
        
        if (Array.isArray(importedTemplates)) {
          templates.value.push(...importedTemplates)
          saveTemplates()
          ElMessage.success(`成功导入 ${importedTemplates.length} 个模板`)
        } else {
          ElMessage.error('文件格式错误')
        }
      } catch (error) {
        ElMessage.error('导入失败，文件格式错误')
      }
    }
  }
  input.click()
}

const exportTemplates = () => {
  console.log('📤 导出模板')
  try {
    const exportData = {
      templates: templates.value,
      export_time: new Date().toISOString(),
      version: '1.0'
    }
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: 'application/json'
    })
    
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `order_templates_${new Date().toISOString().split('T')[0]}.json`
    a.click()
    
    URL.revokeObjectURL(url)
    ElMessage.success('模板导出成功')
  } catch (error) {
    ElMessage.error('导出失败')
  }
}

const useTemplate = async (template: any) => {
  console.log('🚀 使用模板:', template)
  
  if (!confirm(`确定要使用模板 "${template.name}" 下单吗？`)) {
    return
  }
  
  try {
    // 尝试多个下单API路径
    const orderApis = [
      {
        path: '/v1/simple-trading/orders',
        data: {
          symbol: template.symbol,
          direction: template.side.toUpperCase(),
          volume: template.quantity,
          price: template.price,
          order_type: template.type.toUpperCase()
        }
      },
      {
        path: '/v1/orders',
        data: {
          symbol: template.symbol,
          side: template.side.toLowerCase(),
          quantity: template.quantity,
          price: template.price,
          order_type: template.type.toLowerCase(),
          time_in_force: 'gtc'
        }
      }
    ]
    
    let success = false
    for (const apiConfig of orderApis) {
      try {
        const result = await request.post(apiConfig.path, apiConfig.data)
        
        if (result.success) {
          ElMessage.success(`使用模板 "${template.name}" 下单成功！订单ID: ${result.data?.order_id || result.data?.id || '未知'}`)
          success = true
          break
        }
      } catch (apiError) {
        console.log(`下单API ${apiConfig.path} 失败:`, apiError)
        continue
      }
    }
    
    if (!success) {
      throw new Error('所有下单API都无法访问')
    }
  } catch (error) {
    console.error('❌ 使用模板下单失败:', error)
    ElMessage.error(`使用模板下单失败: ${error.message || error}`)
  }
}

const editTemplate = (template: any) => {
  console.log('✏️ 编辑模板:', template)
  
  const name = prompt('请输入模板名称:', template.name)
  if (!name) return
  
  const symbol = prompt('请输入交易品种:', template.symbol)
  if (!symbol) return
  
  const side = prompt('请输入交易方向 (buy/sell):', template.side)
  if (!side || !['buy', 'sell'].includes(side)) return
  
  const type = prompt('请输入订单类型 (market/limit):', template.type)
  if (!type || !['market', 'limit'].includes(type)) return
  
  const quantity = prompt('请输入交易数量:', template.quantity.toString())
  if (!quantity || isNaN(Number(quantity))) return
  
  let price = template.price
  if (type === 'limit') {
    const priceStr = prompt('请输入限价价格:', price?.toString() || '')
    if (!priceStr || isNaN(Number(priceStr))) return
    price = Number(priceStr)
  } else {
    price = null
  }
  
  // 更新模板
  const index = templates.value.findIndex(t => t.id === template.id)
  if (index > -1) {
    templates.value[index] = {
      ...template,
      name,
      symbol,
      side,
      type,
      quantity: Number(quantity),
      price,
      description: `${name} - ${symbol} ${side === 'buy' ? '买入' : '卖出'}`
    }
    saveTemplates()
    ElMessage.success(`模板 "${name}" 更新成功！`)
  }
}

const deleteTemplate = (template: any) => {
  console.log('🗑️ 删除模板:', template)
  if (confirm(`确定要删除模板 "${template.name}" 吗？`)) {
    const index = templates.value.findIndex(t => t.id === template.id)
    if (index > -1) {
      templates.value.splice(index, 1)
      saveTemplates()
      ElMessage.success(`模板 "${template.name}" 已删除`)
    }
  }
}

// 页面初始化
onMounted(() => {
  console.log('📝 订单模板页面已加载')
  loadTemplates()
})
</script>

<style scoped>
.order-templates-view {
  padding: 24px;
  background: var(--el-bg-color-page);
  min-height: 100vh;
}

.page-header {
  margin-bottom: 32px;
  text-align: center;
}

.page-title {
  margin: 0 0 8px 0;
  font-size: 32px;
  font-weight: 700;
  color: var(--el-text-color-primary);
}

.page-description {
  margin: 0;
  font-size: 18px;
  color: var(--el-text-color-regular);
}

.actions-card, .templates-list {
  background: var(--el-bg-color);
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  margin-bottom: 24px;
}

.actions-card h3, .templates-list h3 {
  margin: 0 0 20px 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.action-btn {
  background: #6c757d;
  color: white;
  border: none;
  padding: 12px 20px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.action-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.action-btn.primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--el-text-color-secondary);
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.empty-text {
  font-size: 16px;
  margin-bottom: 20px;
}

.create-first-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.create-first-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.templates-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
}

.template-card {
  background: var(--el-bg-color-page);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid var(--el-border-color-light);
  transition: all 0.3s ease;
}

.template-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.template-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.template-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.template-type {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
}

.template-type.market {
  background: #fff3cd;
  color: #856404;
}

.template-type.limit {
  background: #d4edda;
  color: #155724;
}

.template-type.stop {
  background: #f8d7da;
  color: #721c24;
}

.template-info {
  margin-bottom: 16px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
}

.label {
  font-size: 13px;
  color: var(--el-text-color-regular);
  font-weight: 500;
}

.value {
  font-size: 14px;
  color: var(--el-text-color-primary);
  font-weight: 600;
}

.value.buy {
  color: #27ae60;
}

.value.sell {
  color: #e74c3c;
}

.template-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.btn-small {
  padding: 6px 12px;
  font-size: 12px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  background: #6c757d;
  color: white;
  font-weight: 500;
  transition: all 0.3s ease;
}

.btn-small:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.btn-small.primary {
  background: #007bff;
}

.btn-small.danger {
  background: #dc3545;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .order-templates-view {
    padding: 16px;
  }
  
  .page-title {
    font-size: 24px;
  }
  
  .actions {
    flex-direction: column;
  }
  
  .templates-grid {
    grid-template-columns: 1fr;
  }
  
  .template-actions {
    justify-content: center;
  }
}
</style>