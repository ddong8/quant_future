import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    vue()
  ],
  
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  
  // 开发服务器配置
  server: {
    port: 3000,
    host: true,
    proxy: {
      '/api': {
        target: process.env.VITE_API_PROXY_TARGET || 'http://backend:8000',
        changeOrigin: true,
        secure: false,
        timeout: 30000,
        proxyTimeout: 30000
      },
      '/ws': {
        target: process.env.VITE_WS_PROXY_TARGET || 'ws://backend:8000',
        ws: true,
        changeOrigin: true,
        timeout: 30000
      }
    }
  },
  
  // 构建配置
  build: {
    target: 'es2015',
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false,
    minify: 'terser',
    
    // Terser配置
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
        pure_funcs: ['console.log', 'console.info', 'console.debug']
      }
    },
    
    // 代码分割配置
    rollupOptions: {
      output: {
        // 手动分块
        manualChunks: {
          // Vue核心
          'vue-vendor': ['vue', 'vue-router', 'pinia'],
          
          // UI组件库
          'ui-vendor': ['element-plus', '@element-plus/icons-vue'],
          
          // 图表库
          'chart-vendor': ['echarts', 'vue-echarts'],
          
          // 工具库
          'utils-vendor': ['axios', 'dayjs', 'lodash-es'],
          
          // 代码编辑器
          'editor-vendor': ['monaco-editor'],
          
          // 认证相关
          'auth': [
            './src/views/auth/LoginView.vue',
            './src/views/auth/RegisterView.vue',
            './src/stores/auth.ts',
            './src/api/auth.ts'
          ],
          
          // 策略相关
          'strategy': [
            './src/views/strategies/StrategiesView.vue',
            './src/views/strategies/StrategyEditorView.vue',
            './src/views/strategies/StrategyTestView.vue',
            './src/stores/strategy.ts',
            './src/api/strategy.ts'
          ],
          
          // 回测相关
          'backtest': [
            './src/views/backtests/BacktestResultView.vue',
            './src/stores/backtest.ts',
            './src/api/backtest.ts'
          ],
          
          // 交易相关
          'trading': [
            './src/views/trading/ManualTradingView.vue',
            './src/stores/trading.ts',
            './src/api/trading.ts'
          ],
          
          // 风险控制
          'risk': [
            './src/views/risk/RiskControlView.vue'
          ]
        },
        
        // 文件命名
        chunkFileNames: (chunkInfo) => {
          const facadeModuleId = chunkInfo.facadeModuleId
          if (facadeModuleId) {
            const fileName = facadeModuleId.split('/').pop()?.replace('.vue', '') || 'chunk'
            return `js/${fileName}-[hash].js`
          }
          return 'js/[name]-[hash].js'
        },
        
        entryFileNames: 'js/[name]-[hash].js',
        assetFileNames: (assetInfo) => {
          const info = assetInfo.name?.split('.') || []
          const ext = info[info.length - 1]
          
          if (/\.(mp4|webm|ogg|mp3|wav|flac|aac)$/.test(assetInfo.name || '')) {
            return `media/[name]-[hash].${ext}`
          }
          
          if (/\.(png|jpe?g|gif|svg|webp|avif)$/.test(assetInfo.name || '')) {
            return `images/[name]-[hash].${ext}`
          }
          
          if (/\.(woff2?|eot|ttf|otf)$/.test(assetInfo.name || '')) {
            return `fonts/[name]-[hash].${ext}`
          }
          
          return `assets/[name]-[hash].${ext}`
        }
      }
    },
    
    // 资源内联阈值
    assetsInlineLimit: 4096,
    
    // CSS代码分割
    cssCodeSplit: true,
    
    // 报告压缩后的大小
    reportCompressedSize: true,
    
    // 块大小警告限制
    chunkSizeWarningLimit: 1000
  },
  
  // CSS配置
  css: {
    // CSS模块化
    modules: {
      localsConvention: 'camelCase'
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
      'dayjs'
    ],
    exclude: [
      'monaco-editor'
    ]
  },
  
  // 预构建配置
  esbuild: {
    drop: ['console', 'debugger']
  }
})