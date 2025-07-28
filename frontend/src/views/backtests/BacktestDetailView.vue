<template>
  <div class="backtest-detail-container">
    <div class="page-header">
      <h1 class="page-title">回测详情</h1>
      <p class="page-description">回测结果详细分析</p>
    </div>
    
    <div class="coming-soon">
      <el-icon size="64" color="var(--el-color-primary)">
        <DataAnalysis />
      </el-icon>
      <h2>回测详情界面开发中</h2>
      <p>敬请期待...</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { DataAnalysis } from '@element-plus/icons-vue'
</script>

<style lang="scss" scoped>
.backtest-detail-container {
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