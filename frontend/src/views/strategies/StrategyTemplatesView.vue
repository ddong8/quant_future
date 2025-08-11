<template>
  <div class="view-container">
    <div class="page-header">
      <h1 class="page-title">📝 策略模板</h1>
      <p class="page-description">策略模板管理</p>
    </div>
    <div class="content-placeholder">
      <h3>🚧 功能开发中</h3>
      <p>策略模板功能正在开发中，敬请期待...</p>
    </div>
  </div>
</template>
<script setup lang="ts">
import { onMounted } from 'vue'
onMounted(() => console.log('📝 策略模板页面已加载'))
</script>
<style scoped>
.view-container { padding: 24px; background: var(--el-bg-color-page); min-height: 100vh; }
.page-header { margin-bottom: 32px; text-align: center; }
.page-title { margin: 0 0 8px 0; font-size: 32px; font-weight: 700; color: var(--el-text-color-primary); }
.page-description { margin: 0; font-size: 18px; color: var(--el-text-color-regular); }
.content-placeholder { background: var(--el-bg-color); border-radius: 12px; padding: 60px; text-align: center; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); }
.content-placeholder h3 { margin: 0 0 16px 0; font-size: 24px; color: var(--el-text-color-primary); }
.content-placeholder p { margin: 0; color: var(--el-text-color-regular); font-size: 16px; }
</style>
