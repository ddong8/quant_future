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
      <div class="templates-grid">
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
                <span class="value">{{ template.price ? '¥' + formatNumber(template.price) : '市价' }}</span>
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

// 模拟模板数据
const templates = ref([
  {
    id: 'TPL001',
    name: 'BTC定投模板',
    symbol: 'BTCUSDT',
    side: 'buy',
    type: 'market',
    quantity: 0.1,
    price: null,
    description: '每周定投BTC'
  },
  {
    id: 'TPL002',
    name: 'ETH限价买入',
    symbol: 'ETHUSDT',
    side: 'buy',
    type: 'limit',
    quantity: 1,
    price: 3000,
    description: 'ETH跌到3000时买入'
  },
  {
    id: 'TPL003',
    name: 'ADA止盈模板',
    symbol: 'ADAUSDT',
    side: 'sell',
    type: 'limit',
    quantity: 1000,
    price: 0.5,
    description: 'ADA涨到0.5时卖出'
  }
])

// 工具函数
const formatNumber = (num: number) => {
  return new Intl.NumberFormat('zh-CN', {
    minimumFractionDigits: 2,
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
  alert('创建模板功能开发中...')
}

const importTemplate = () => {
  console.log('📥 导入模板')
  alert('导入模板功能开发中...')
}

const exportTemplates = () => {
  console.log('📤 导出模板')
  alert('导出模板功能开发中...')
}

const useTemplate = (template: any) => {
  console.log('🚀 使用模板:', template)
  alert(`使用模板下单: ${template.name}`)
}

const editTemplate = (template: any) => {
  console.log('✏️ 编辑模板:', template)
  alert(`编辑模板: ${template.name}`)
}

const deleteTemplate = (template: any) => {
  console.log('🗑️ 删除模板:', template)
  if (confirm(`确定要删除模板 "${template.name}" 吗？`)) {
    alert(`已删除模板: ${template.name}`)
  }
}

onMounted(() => {
  console.log('📝 订单模板页面已加载')
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

.templates-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 16px;
}

.template-card {
  background: var(--el-bg-color-page);
  border-radius: 8px;
  padding: 16px;
  border: 1px solid #dee2e6;
  transition: all 0.3s ease;
}

.template-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  background: var(--el-bg-color);
}

.template-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.template-name {
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.template-type {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.template-type.market {
  background: #d1ecf1;
  color: #0c5460;
}

.template-type.limit {
  background: var(--el-bg-color)3cd;
  color: var(--el-color-warning);
}

.template-type.stop {
  background: var(--el-color-danger-light-9);
  color: #721c24;
}

.template-content {
  display: flex;
  justify-content: space-between;
  align-items: end;
}

.template-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-row {
  display: flex;
  gap: 8px;
}

.info-row .label {
  font-size: 12px;
  color: var(--el-text-color-regular);
  font-weight: 500;
  min-width: 40px;
}

.info-row .value {
  font-size: 14px;
  color: var(--el-text-color-primary);
  font-weight: 600;
}

.info-row .value.buy {
  color: #27ae60;
}

.info-row .value.sell {
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

@media (max-width: 768px) {
  .order-templates-view {
    padding: 16px;
  }
  
  .actions {
    flex-direction: column;
  }
  
  .templates-grid {
    grid-template-columns: 1fr;
  }
}
</style>