<template>
  <div class="responsive-demo">
    <!-- 使用响应式布局 -->
    <ResponsiveLayout
      title="响应式演示"
      :show-sidebar="!isMobile"
      :show-bottom-nav="isMobile"
      :show-performance-monitor="true"
    >
      <!-- 侧边栏内容 -->
      <template #sidebar>
        <div class="demo-sidebar">
          <h3>设备信息</h3>
          <div class="device-info">
            <div class="info-item">
              <span class="label">设备类型:</span>
              <span class="value">
                {{ deviceInfo.isMobile ? '移动端' : deviceInfo.isTablet ? '平板' : '桌面端' }}
              </span>
            </div>
            <div class="info-item">
              <span class="label">屏幕尺寸:</span>
              <span class="value">{{ windowWidth }} × {{ windowHeight }}</span>
            </div>
            <div class="info-item">
              <span class="label">当前断点:</span>
              <span class="value">{{ currentBreakpoint.toUpperCase() }}</span>
            </div>
            <div class="info-item">
              <span class="label">触摸支持:</span>
              <span class="value">{{ deviceInfo.isTouch ? '是' : '否' }}</span>
            </div>
            <div class="info-item">
              <span class="label">高DPI:</span>
              <span class="value">{{ deviceInfo.isRetina ? '是' : '否' }}</span>
            </div>
            <div class="info-item">
              <span class="label">屏幕方向:</span>
              <span class="value">{{ deviceInfo.orientation === 'portrait' ? '竖屏' : '横屏' }}</span>
            </div>
          </div>
        </div>
      </template>

      <!-- 主要内容 -->
      <div class="demo-content">
        <div class="container">
          <h1 class="demo-title">响应式设计演示</h1>
          <p class="demo-description">
            这个页面展示了量化交易平台的响应式设计能力，支持各种设备和屏幕尺寸。
          </p>

          <!-- 响应式网格 -->
          <div class="demo-section">
            <h2>响应式网格系统</h2>
            <div class="row">
              <div class="col col-12 col-md-6 col-lg-4">
                <div class="grid-item">
                  <h3>策略管理</h3>
                  <p>创建和管理您的交易策略</p>
                </div>
              </div>
              <div class="col col-12 col-md-6 col-lg-4">
                <div class="grid-item">
                  <h3>回测分析</h3>
                  <p>测试策略的历史表现</p>
                </div>
              </div>
              <div class="col col-12 col-md-12 col-lg-4">
                <div class="grid-item">
                  <h3>实时交易</h3>
                  <p>执行实时交易操作</p>
                </div>
              </div>
            </div>
          </div>

          <!-- 响应式表格 -->
          <div class="demo-section">
            <h2>响应式表格</h2>
            <ResponsiveTable
              :data="tableData"
              :columns="tableColumns"
              :use-card-view="true"
              :show-pagination="true"
              :total="100"
              card-title-prop="name"
            >
              <template #status="{ row }">
                <el-tag :type="getStatusType(row.status)">
                  {{ row.status }}
                </el-tag>
              </template>
              <template #actions="{ row }">
                <el-button size="small" type="primary">编辑</el-button>
                <el-button size="small" type="danger">删除</el-button>
              </template>
            </ResponsiveTable>
          </div>

          <!-- 响应式卡片 -->
          <div class="demo-section">
            <h2>响应式卡片</h2>
            <div class="card-grid">
              <div
                v-for="card in cardData"
                :key="card.id"
                class="demo-card card-responsive"
              >
                <div class="card-header">
                  <h3>{{ card.title }}</h3>
                  <el-icon :color="card.color"><component :is="card.icon" /></el-icon>
                </div>
                <div class="card-content">
                  <div class="card-value">{{ card.value }}</div>
                  <div class="card-change" :class="{ positive: card.change > 0, negative: card.change < 0 }">
                    {{ card.change > 0 ? '+' : '' }}{{ card.change }}%
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 响应式表单 -->
          <div class="demo-section">
            <h2>响应式表单</h2>
            <div class="form-responsive">
              <el-form :model="formData" label-width="120px">
                <div class="row">
                  <div class="col col-12 col-md-6">
                    <el-form-item label="策略名称">
                      <el-input v-model="formData.name" placeholder="请输入策略名称" />
                    </el-form-item>
                  </div>
                  <div class="col col-12 col-md-6">
                    <el-form-item label="策略类型">
                      <el-select v-model="formData.type" placeholder="请选择策略类型">
                        <el-option label="趋势跟踪" value="trend" />
                        <el-option label="均值回归" value="mean" />
                        <el-option label="套利策略" value="arbitrage" />
                      </el-select>
                    </el-form-item>
                  </div>
                </div>
                <div class="row">
                  <div class="col col-12">
                    <el-form-item label="策略描述">
                      <el-input
                        v-model="formData.description"
                        type="textarea"
                        :rows="4"
                        placeholder="请输入策略描述"
                      />
                    </el-form-item>
                  </div>
                </div>
                <div class="row">
                  <div class="col col-12">
                    <el-form-item>
                      <el-button type="primary">保存策略</el-button>
                      <el-button>重置</el-button>
                    </el-form-item>
                  </div>
                </div>
              </el-form>
            </div>
          </div>

          <!-- 性能指标 -->
          <div class="demo-section">
            <h2>性能指标</h2>
            <div class="performance-metrics">
              <div class="metric-card">
                <div class="metric-label">FPS</div>
                <div class="metric-value" :class="getFPSClass(performanceMetrics.fps)">
                  {{ performanceMetrics.fps }}
                </div>
              </div>
              <div class="metric-card">
                <div class="metric-label">内存使用</div>
                <div class="metric-value">
                  {{ Math.round(performanceMetrics.memoryUsage) }}MB
                </div>
              </div>
              <div class="metric-card">
                <div class="metric-label">加载时间</div>
                <div class="metric-value">
                  {{ Math.round(performanceMetrics.loadTime) }}ms
                </div>
              </div>
              <div class="metric-card">
                <div class="metric-label">网络延迟</div>
                <div class="metric-value">
                  {{ Math.round(performanceMetrics.networkLatency) }}ms
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 底部导航内容 -->
      <template #bottom-nav>
        <div class="demo-bottom-nav">
          <div class="nav-item active">
            <el-icon><House /></el-icon>
            <span>首页</span>
          </div>
          <div class="nav-item">
            <el-icon><TrendCharts /></el-icon>
            <span>交易</span>
          </div>
          <div class="nav-item">
            <el-icon><DataAnalysis /></el-icon>
            <span>分析</span>
          </div>
          <div class="nav-item">
            <el-icon><Setting /></el-icon>
            <span>设置</span>
          </div>
        </div>
      </template>
    </ResponsiveLayout>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useResponsive } from '@/composables/useResponsive'
import { useGlobalPerformanceMonitor } from '@/composables/usePerformanceOptimization'
import ResponsiveLayout from '@/components/layout/ResponsiveLayout.vue'
import ResponsiveTable from '@/components/common/ResponsiveTable.vue'
import {
  House,
  TrendCharts,
  DataAnalysis,
  Setting,
  Wallet,
  Monitor,
  Warning
} from '@element-plus/icons-vue'

// 响应式功能
const {
  windowWidth,
  windowHeight,
  currentBreakpoint,
  deviceInfo,
  isMobile
} = useResponsive()

// 性能监控
const { metrics: performanceMetrics } = useGlobalPerformanceMonitor()

// 表格数据
const tableData = ref([
  {
    id: 1,
    name: '趋势跟踪策略',
    type: '趋势',
    status: '运行中',
    profit: 15.6,
    drawdown: -3.2
  },
  {
    id: 2,
    name: '均值回归策略',
    type: '回归',
    status: '已停止',
    profit: -2.1,
    drawdown: -8.5
  },
  {
    id: 3,
    name: '套利策略',
    type: '套利',
    status: '运行中',
    profit: 8.9,
    drawdown: -1.8
  }
])

const tableColumns = ref([
  { prop: 'name', label: '策略名称', minWidth: 150 },
  { prop: 'type', label: '类型', width: 100, hideOnMobile: true },
  { prop: 'status', label: '状态', width: 100, slot: 'status' },
  { prop: 'profit', label: '收益率(%)', width: 120, hideOnMobile: true },
  { prop: 'drawdown', label: '最大回撤(%)', width: 120, hideOnMobile: true },
  { prop: 'actions', label: '操作', width: 150, slot: 'actions' }
])

// 卡片数据
const cardData = ref([
  {
    id: 1,
    title: '总资产',
    value: '¥1,234,567',
    change: 5.6,
    color: '#409EFF',
    icon: Wallet
  },
  {
    id: 2,
    title: '今日收益',
    value: '¥12,345',
    change: 2.3,
    color: '#67C23A',
    icon: TrendCharts
  },
  {
    id: 3,
    title: '运行策略',
    value: '8',
    change: 0,
    color: '#E6A23C',
    icon: Monitor
  },
  {
    id: 4,
    title: '风险等级',
    value: '中等',
    change: -1.2,
    color: '#F56C6C',
    icon: Warning
  }
])

// 表单数据
const formData = ref({
  name: '',
  type: '',
  description: ''
})

// 方法
const getStatusType = (status: string) => {
  switch (status) {
    case '运行中':
      return 'success'
    case '已停止':
      return 'info'
    case '错误':
      return 'danger'
    default:
      return 'info'
  }
}

const getFPSClass = (fps: number) => {
  if (fps >= 55) return 'excellent'
  if (fps >= 45) return 'good'
  if (fps >= 30) return 'fair'
  return 'poor'
}
</script>

<style lang="scss" scoped>
.responsive-demo {
  height: 100vh;
}

.demo-sidebar {
  padding: 20px;
  
  h3 {
    margin-bottom: 16px;
    color: var(--el-text-color-primary);
  }
  
  .device-info {
    .info-item {
      display: flex;
      justify-content: space-between;
      margin-bottom: 8px;
      font-size: 14px;
      
      .label {
        color: var(--el-text-color-secondary);
      }
      
      .value {
        color: var(--el-text-color-primary);
        font-weight: 600;
      }
    }
  }
}

.demo-content {
  padding: 20px;
  overflow-y: auto;
}

.demo-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  margin-bottom: 8px;
}

.demo-description {
  font-size: 16px;
  color: var(--el-text-color-secondary);
  margin-bottom: 32px;
  line-height: 1.6;
}

.demo-section {
  margin-bottom: 40px;
  
  h2 {
    font-size: 20px;
    font-weight: 600;
    color: var(--el-text-color-primary);
    margin-bottom: 20px;
    padding-bottom: 8px;
    border-bottom: 2px solid var(--el-color-primary);
  }
}

.grid-item {
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  padding: 20px;
  text-align: center;
  transition: all 0.3s ease;
  
  &:hover {
    border-color: var(--el-color-primary);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }
  
  h3 {
    font-size: 18px;
    font-weight: 600;
    color: var(--el-text-color-primary);
    margin-bottom: 8px;
  }
  
  p {
    font-size: 14px;
    color: var(--el-text-color-secondary);
    margin: 0;
  }
}

.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.demo-card {
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 12px;
  padding: 24px;
  transition: all 0.3s ease;
  
  &:hover {
    border-color: var(--el-color-primary-light-7);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  }
  
  .card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
    
    h3 {
      font-size: 16px;
      font-weight: 600;
      color: var(--el-text-color-primary);
      margin: 0;
    }
  }
  
  .card-content {
    .card-value {
      font-size: 24px;
      font-weight: 700;
      color: var(--el-text-color-primary);
      margin-bottom: 8px;
    }
    
    .card-change {
      font-size: 14px;
      font-weight: 600;
      
      &.positive {
        color: var(--el-color-success);
      }
      
      &.negative {
        color: var(--el-color-danger);
      }
    }
  }
}

.performance-metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
  
  .metric-card {
    background: var(--el-bg-color);
    border: 1px solid var(--el-border-color-lighter);
    border-radius: 8px;
    padding: 16px;
    text-align: center;
    
    .metric-label {
      font-size: 12px;
      color: var(--el-text-color-secondary);
      margin-bottom: 8px;
    }
    
    .metric-value {
      font-size: 20px;
      font-weight: 700;
      font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
      
      &.excellent {
        color: var(--el-color-success);
      }
      
      &.good {
        color: var(--el-color-primary);
      }
      
      &.fair {
        color: var(--el-color-warning);
      }
      
      &.poor {
        color: var(--el-color-danger);
      }
    }
  }
}

.demo-bottom-nav {
  display: flex;
  height: 100%;
  
  .nav-item {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    color: var(--el-text-color-secondary);
    transition: color 0.3s ease;
    
    &.active {
      color: var(--el-color-primary);
    }
    
    .el-icon {
      margin-bottom: 4px;
    }
    
    span {
      font-size: 12px;
    }
  }
}

// 移动端优化
@media (max-width: 768px) {
  .demo-content {
    padding: 16px;
  }
  
  .demo-title {
    font-size: 24px;
  }
  
  .demo-description {
    font-size: 14px;
    margin-bottom: 24px;
  }
  
  .demo-section {
    margin-bottom: 32px;
    
    h2 {
      font-size: 18px;
      margin-bottom: 16px;
    }
  }
  
  .grid-item {
    padding: 16px;
    
    h3 {
      font-size: 16px;
    }
    
    p {
      font-size: 13px;
    }
  }
  
  .card-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .demo-card {
    padding: 20px;
    
    .card-content {
      .card-value {
        font-size: 20px;
      }
    }
  }
  
  .performance-metrics {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
    
    .metric-card {
      padding: 12px;
      
      .metric-value {
        font-size: 18px;
      }
    }
  }
}

// 小屏幕优化
@media (max-width: 480px) {
  .demo-content {
    padding: 12px;
  }
  
  .demo-title {
    font-size: 20px;
  }
  
  .card-grid {
    gap: 12px;
  }
  
  .demo-card {
    padding: 16px;
    
    .card-content {
      .card-value {
        font-size: 18px;
      }
    }
  }
  
  .performance-metrics {
    .metric-card {
      padding: 10px;
      
      .metric-value {
        font-size: 16px;
      }
    }
  }
}
</style>