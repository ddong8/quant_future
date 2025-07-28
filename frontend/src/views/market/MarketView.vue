<template>
  <div class="market-container">
    <div class="page-header">
      <h1 class="page-title">市场数据</h1>
      <p class="page-description">实时市场行情和数据</p>
    </div>
    
    <div class="coming-soon">
      <el-icon size="64" color="var(--el-color-primary)">
        <Monitor />
      </el-icon>
      <h2>市场数据界面开发中</h2>
      <p>敬请期待...</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Monitor } from '@element-plus/icons-vue'
</script>

<style lang="scss" scoped>
.market-container {
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