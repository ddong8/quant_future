<template>
  <div class="not-found-container">
    <div class="not-found-content">
      <div class="error-code">404</div>
      <h1>页面不存在</h1>
      <p>抱歉，您访问的页面不存在或已被移除。</p>
      
      <div class="actions">
        <el-button type="primary" @click="goHome">
          返回首页
        </el-button>
        <el-button @click="goBack">
          返回上页
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const goHome = () => {
  router.push('/')
}

const goBack = () => {
  router.go(-1)
}
</script>

<style lang="scss" scoped>
.not-found-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--el-bg-color-page);
}

.not-found-content {
  text-align: center;
  max-width: 500px;
  padding: 40px;
  
  .error-code {
    font-size: 120px;
    font-weight: bold;
    color: var(--el-color-primary);
    line-height: 1;
    margin-bottom: 20px;
  }
  
  h1 {
    font-size: 32px;
    color: var(--el-text-color-primary);
    margin: 0 0 16px 0;
  }
  
  p {
    font-size: 16px;
    color: var(--el-text-color-secondary);
    margin: 0 0 32px 0;
    line-height: 1.6;
  }
  
  .actions {
    display: flex;
    gap: 16px;
    justify-content: center;
  }
}

// 响应式设计
@media (max-width: 768px) {
  .not-found-content {
    padding: 20px;
    
    .error-code {
      font-size: 80px;
    }
    
    h1 {
      font-size: 24px;
    }
    
    .actions {
      flex-direction: column;
      align-items: center;
      
      .el-button {
        width: 200px;
      }
    }
  }
}
</style>