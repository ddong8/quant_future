<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'

const authStore = useAuthStore()
const themeStore = useThemeStore()

onMounted(() => {
  // 初始化认证状态
  authStore.initAuth()
  
  // 初始化主题
  themeStore.initTheme()
})
</script>

<style lang="scss">
#app {
  height: 100vh;
  width: 100vw;
}
</style>