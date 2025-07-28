<template>
  <div class="accounts-container">
    <div class="page-header">
      <h1 class="page-title">账户管理</h1>
      <p class="page-description">管理您的交易账户和资金</p>
    </div>
    
    <div class="coming-soon">
      <el-icon size="64" color="var(--el-color-primary)">
        <Wallet />
      </el-icon>
      <h2>账户管理界面开发中</h2>
      <p>敬请期待...</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Wallet } from '@element-plus/icons-vue'
</script>

<style lang="scss" scoped>
.accounts-container {
  padding: 20px;
}

.coming-soon {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  color: var(--el-text-color-secondary);
  
  h2 {
    margin: 20px 0 10px 0;
    color: var(--el-text-color-primary);
  }
  
  p {
    margin: 0;
  }
}
</style>