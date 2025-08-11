<template>
  <div class="technical-analysis">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">技术分析</h1>
        <p class="page-description">专业的技术分析图表和指标工具</p>
      </div>
      <div class="header-right">
        <el-button @click="showFullscreen = !showFullscreen">
          <el-icon><FullScreen /></el-icon>
          {{ showFullscreen ? '退出全屏' : '全屏显示' }}
        </el-button>
      </div>
    </div>

    <!-- 图表容器 -->
    <div class="chart-wrapper" :class="{ 'fullscreen': showFullscreen }">
      <TechnicalChart 
        :symbol="selectedSymbol"
        :height="chartHeight"
        @symbol-change="handleSymbolChange"
      />
    </div>

    <!-- 快捷工具栏 -->
    <div v-if="!showFullscreen" class="quick-tools">
      <div class="tools-section">
        <h3>常用指标</h3>
        <div class="indicator-buttons">
          <el-button 
            v-for="indicator in commonIndicators"
            :key="indicator.key"
            size="small"
            :type="activeIndicators.includes(indicator.key) ? 'primary' : 'default'"
            @click="toggleIndicator(indicator.key)"
          >
            {{ indicator.name }}
          </el-button>
        </div>
      </div>

      <div class="tools-section">
        <h3>时间周期</h3>
        <div class="interval-buttons">
          <el-button-group>
            <el-button 
              v-for="interval in timeIntervals"
              :key="interval.value"
              size="small"
              :type="selectedInterval === interval.value ? 'primary' : 'default'"
              @click="setInterval(interval.value)"
            >
              {{ interval.label }}
            </el-button>
          </el-button-group>
        </div>
      </div>

      <div class="tools-section">
        <h3>热门标的</h3>
        <div class="symbol-buttons">
          <el-button 
            v-for="symbol in popularSymbols"
            :key="symbol.code"
            size="small"
            :type="selectedSymbol === symbol.code ? 'primary' : 'default'"
            @click="setSymbol(symbol.code)"
          >
            {{ symbol.code }}
          </el-button>
        </div>
      </div>
    </div>

    <!-- 指标说明面板 -->
    <div v-if="!showFullscreen" class="indicator-info">
      <el-collapse v-model="activeInfoPanels">
        <el-collapse-item title="移动平均线 (MA)" name="ma">
          <div class="indicator-description">
            <p>移动平均线是技术分析中最基本的指标之一，通过计算一定周期内的平均价格来平滑价格波动。</p>
            <ul>
              <li><strong>MA5:</strong> 5日移动平均线，反映短期趋势</li>
              <li><strong>MA10:</strong> 10日移动平均线，反映中短期趋势</li>
              <li><strong>MA20:</strong> 20日移动平均线，反映中期趋势</li>
              <li><strong>MA60:</strong> 60日移动平均线，反映长期趋势</li>
            </ul>
          </div>
        </el-collapse-item>

        <el-collapse-item title="布林带 (BOLL)" name="bollinger">
          <div class="indicator-description">
            <p>布林带由三条线组成：中轨（移动平均线）、上轨和下轨（标准差线）。</p>
            <ul>
              <li><strong>上轨:</strong> 中轨 + 2倍标准差，通常作为阻力位</li>
              <li><strong>中轨:</strong> 20日移动平均线</li>
              <li><strong>下轨:</strong> 中轨 - 2倍标准差，通常作为支撑位</li>
            </ul>
          </div>
        </el-collapse-item>

        <el-collapse-item title="相对强弱指数 (RSI)" name="rsi">
          <div class="indicator-description">
            <p>RSI是衡量价格变动速度和变化的动量振荡器，取值范围0-100。</p>
            <ul>
              <li><strong>超买区:</strong> RSI > 70，可能出现回调</li>
              <li><strong>超卖区:</strong> RSI < 30，可能出现反弹</li>
              <li><strong>中性区:</strong> 30 ≤ RSI ≤ 70，趋势延续</li>
            </ul>
          </div>
        </el-collapse-item>

        <el-collapse-item title="MACD指标" name="macd">
          <div class="indicator-description">
            <p>MACD由快线、慢线和柱状图组成，用于判断趋势变化。</p>
            <ul>
              <li><strong>MACD线:</strong> 12日EMA - 26日EMA</li>
              <li><strong>信号线:</strong> MACD线的9日EMA</li>
              <li><strong>柱状图:</strong> MACD线 - 信号线</li>
            </ul>
          </div>
        </el-collapse-item>

        <el-collapse-item title="KDJ指标" name="kdj">
          <div class="indicator-description">
            <p>KDJ是随机指标，由K、D、J三条线组成，用于判断超买超卖。</p>
            <ul>
              <li><strong>K线:</strong> 快速随机值</li>
              <li><strong>D线:</strong> K线的移动平均</li>
              <li><strong>J线:</strong> 3K - 2D，更敏感的指标</li>
            </ul>
          </div>
        </el-collapse-item>
      </el-collapse>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { FullScreen } from '@element-plus/icons-vue'
import TechnicalChart from '@/components/charts/TechnicalChart.vue'

// 响应式数据
const selectedSymbol = ref('AAPL')
const selectedInterval = ref('1d')
const showFullscreen = ref(false)
const activeIndicators = ref(['ma5', 'ma10', 'ma20'])
const activeInfoPanels = ref(['ma'])

// 常用指标
const commonIndicators = [
  { key: 'ma5', name: 'MA5' },
  { key: 'ma10', name: 'MA10' },
  { key: 'ma20', name: 'MA20' },
  { key: 'ma60', name: 'MA60' },
  { key: 'bollinger', name: '布林带' },
  { key: 'rsi', name: 'RSI' },
  { key: 'macd', name: 'MACD' },
  { key: 'kdj', name: 'KDJ' }
]

// 时间周期
const timeIntervals = [
  { label: '1分', value: '1m' },
  { label: '5分', value: '5m' },
  { label: '15分', value: '15m' },
  { label: '1小时', value: '1h' },
  { label: '1天', value: '1d' },
  { label: '1周', value: '1w' }
]

// 热门标的
const popularSymbols = [
  { code: 'AAPL', name: '苹果' },
  { code: 'GOOGL', name: '谷歌' },
  { code: 'MSFT', name: '微软' },
  { code: 'TSLA', name: '特斯拉' },
  { code: 'AMZN', name: '亚马逊' },
  { code: 'NVDA', name: '英伟达' },
  { code: 'META', name: 'Meta' },
  { code: 'NFLX', name: '奈飞' }
]

// 图表高度
const chartHeight = computed(() => {
  return showFullscreen.value ? window.innerHeight - 100 : 600
})

// 切换指标
const toggleIndicator = (indicator: string) => {
  const index = activeIndicators.value.indexOf(indicator)
  if (index > -1) {
    activeIndicators.value.splice(index, 1)
  } else {
    activeIndicators.value.push(indicator)
  }
}

// 设置时间周期
const setInterval = (interval: string) => {
  selectedInterval.value = interval
}

// 设置标的
const setSymbol = (symbol: string) => {
  selectedSymbol.value = symbol
}

// 处理标的变化
const handleSymbolChange = (symbol: string) => {
  selectedSymbol.value = symbol
}

// 组件挂载
onMounted(() => {
  // 监听ESC键退出全屏
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && showFullscreen.value) {
      showFullscreen.value = false
    }
  })
})
</script>

<style scoped>
.technical-analysis {
  padding: 20px;
  min-height: 100vh;
  background: var(--el-bg-color-page);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 20px;
  background: var(--el-bg-color);
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.header-left {
  flex: 1;
}

.page-title {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.page-description {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.header-right {
  display: flex;
  gap: 12px;
}

.chart-wrapper {
  margin-bottom: 20px;
  transition: all 0.3s ease;
}

.chart-wrapper.fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9999;
  background: var(--el-bg-color);
  padding: 20px;
  margin: 0;
}

.quick-tools {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.tools-section {
  padding: 20px;
  background: var(--el-bg-color);
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.tools-section h3 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.indicator-buttons,
.symbol-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.interval-buttons {
  display: flex;
  justify-content: flex-start;
}

.indicator-info {
  background: var(--el-bg-color);
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.indicator-description {
  padding: 16px;
  color: #606266;
  line-height: 1.6;
}

.indicator-description p {
  margin: 0 0 12px 0;
}

.indicator-description ul {
  margin: 0;
  padding-left: 20px;
}

.indicator-description li {
  margin-bottom: 8px;
}

.indicator-description strong {
  color: #303133;
}

:deep(.el-collapse-item__header) {
  padding: 0 20px;
  font-weight: 600;
}

:deep(.el-collapse-item__content) {
  padding: 0;
}
</style>