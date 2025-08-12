<template>
  <div class="transaction-history-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1>交易流水</h1>
      <div class="header-actions">
        <el-button @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
        <el-button type="primary" @click="refreshData">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 账户选择器 -->
    <div class="account-selector" v-if="accounts.length > 1">
      <el-select 
        v-model="selectedAccountId" 
        @change="handleAccountChange"
        placeholder="选择账户"
        style="width: 300px"
      >
        <el-option
          v-for="account in accounts"
          :key="account.id"
          :label="`${account.account_name} (${account.account_number})`"
          :value="account.id"
        />
      </el-select>
    </div>

    <!-- 交易流水组件 -->
    <TransactionHistoryComponent 
      :key="selectedAccountId"
      :account-id="selectedAccountId"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ArrowLeft, Refresh } from '@element-plus/icons-vue'
import { useAccountStore } from '@/stores/account'
import TransactionHistoryComponent from './components/TransactionHistory.vue'

const router = useRouter()
const route = useRoute()
const accountStore = useAccountStore()

// 响应式数据
const selectedAccountId = ref<number | null>(null)

// 计算属性
const accounts = computed(() => accountStore.accounts)

// 方法
const goBack = () => {
  router.back()
}

const refreshData = () => {
  // 刷新账户数据
  accountStore.loadAccounts()
}

const handleAccountChange = () => {
  // 更新URL参数
  router.replace({
    query: { ...route.query, accountId: selectedAccountId.value }
  })
}

// 初始化
onMounted(async () => {
  // 加载账户列表
  await accountStore.loadAccounts()
  
  // 从URL参数获取账户ID
  const accountIdFromQuery = route.query.accountId
  if (accountIdFromQuery) {
    selectedAccountId.value = Number(accountIdFromQuery)
  } else if (accounts.value.length > 0) {
    selectedAccountId.value = accounts.value[0].id
  }
})
</script>

<style scoped>
.transaction-history-page {
  padding: 20px;
  min-height: 100vh;
  background-color: var(--el-fill-color-light);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 20px;
  background-color: var(--el-bg-color);
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.page-header h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.account-selector {
  margin-bottom: 20px;
  padding: 16px 20px;
  background-color: var(--el-bg-color);
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}
</style>