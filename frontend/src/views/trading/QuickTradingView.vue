<template>
  <div class="quick-trading-view">
    <div class="page-header">
      <h1 class="page-title">⚡ 快速交易</h1>
      <p class="page-description">一键快速交易，提高交易效率</p>
    </div>

    <!-- 快速交易面板 -->
    <div class="quick-panels">
      <div class="quick-panel">
        <h3>🟢 快速买入</h3>
        <div class="quick-buttons">
          <button class="quick-btn buy" @click="quickBuy('BTCUSDT', 0.1)">
            买入 0.1 BTC
          </button>
          <button class="quick-btn buy" @click="quickBuy('ETHUSDT', 1)">
            买入 1 ETH
          </button>
          <button class="quick-btn buy" @click="quickBuy('ADAUSDT', 1000)">
            买入 1000 ADA
          </button>
        </div>
      </div>

      <div class="quick-panel">
        <h3>🔴 快速卖出</h3>
        <div class="quick-buttons">
          <button class="quick-btn sell" @click="quickSell('BTCUSDT', 0.1)">
            卖出 0.1 BTC
          </button>
          <button class="quick-btn sell" @click="quickSell('ETHUSDT', 1)">
            卖出 1 ETH
          </button>
          <button class="quick-btn sell" @click="quickSell('ADAUSDT', 1000)">
            卖出 1000 ADA
          </button>
        </div>
      </div>
    </div>

    <!-- 预设交易 -->
    <div class="preset-trading">
      <h3>📋 预设交易</h3>
      <div class="preset-list">
        <div v-for="preset in presets" :key="preset.id" class="preset-item">
          <div class="preset-info">
            <span class="preset-name">{{ preset.name }}</span>
            <span class="preset-desc">{{ preset.description }}</span>
          </div>
          <button class="execute-btn" @click="executePreset(preset)">
            执行
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

// 预设交易配置
const presets = ref([
  {
    id: 1,
    name: '均衡组合',
    description: '50% BTC + 30% ETH + 20% ADA',
    config: { btc: 0.5, eth: 0.3, ada: 0.2 }
  },
  {
    id: 2,
    name: '保守组合',
    description: '70% BTC + 30% ETH',
    config: { btc: 0.7, eth: 0.3 }
  }
])

// 快速交易操作
const quickBuy = (symbol: string, amount: number) => {
  console.log(`⚡ 快速买入: ${amount} ${symbol}`)
  alert(`快速买入订单已提交: ${amount} ${symbol}`)
}

const quickSell = (symbol: string, amount: number) => {
  console.log(`⚡ 快速卖出: ${amount} ${symbol}`)
  alert(`快速卖出订单已提交: ${amount} ${symbol}`)
}

const executePreset = (preset: any) => {
  console.log('📋 执行预设交易:', preset)
  alert(`执行预设交易: ${preset.name}`)
}

onMounted(() => {
  console.log('⚡ 快速交易页面已加载')
})
</script>

<style scoped>
.quick-trading-view {
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

.quick-panels {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-bottom: 32px;
}

.quick-panel {
  background: var(--el-bg-color);
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.quick-panel h3 {
  margin: 0 0 20px 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.quick-buttons {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.quick-btn {
  padding: 16px;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.quick-btn.buy {
  background: #27ae60;
  color: white;
}

.quick-btn.sell {
  background: #e74c3c;
  color: white;
}

.quick-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.preset-trading {
  background: var(--el-bg-color);
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.preset-trading h3 {
  margin: 0 0 20px 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.preset-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.preset-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: var(--el-bg-color-page);
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.preset-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.preset-name {
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.preset-desc {
  font-size: 14px;
  color: var(--el-text-color-regular);
}

.execute-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.3s ease;
}

.execute-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

@media (max-width: 768px) {
  .quick-trading-view {
    padding: 16px;
  }
  
  .quick-panels {
    grid-template-columns: 1fr;
  }
}
</style>