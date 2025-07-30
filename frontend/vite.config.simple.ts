import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// 简化的vite配置，用于Docker构建
export default defineConfig({
  plugins: [vue()],
  
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  
  // 构建配置
  build: {
    target: 'es2015',
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false,
    minify: 'esbuild',
    
    // 资源内联阈值
    assetsInlineLimit: 4096,
    
    // CSS代码分割
    cssCodeSplit: true,
    
    // 报告压缩后的大小
    reportCompressedSize: false,
    
    // 块大小警告限制
    chunkSizeWarningLimit: 1000
  },
  
  // CSS配置
  css: {
    preprocessorOptions: {
      scss: {}
    }
  },
  
  // 优化配置
  optimizeDeps: {
    include: [
      'vue',
      'vue-router',
      'pinia',
      'element-plus',
      'axios',
      'dayjs',
      'echarts',
      'vue-echarts'
    ]
  }
})