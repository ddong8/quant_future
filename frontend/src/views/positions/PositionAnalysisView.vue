<template>
  <div class="position-analysis-view">
    <div class="page-header">
      <h1 class="page-title">📈 持仓分析</h1>
      <p class="page-description">深度分析持仓表现和风险指标</p>
    </div>

    <!-- 分析图表 -->
    <div class="analysis-charts">
      <div class="chart-card">
        <h3>📊 持仓分布</h3>
        <div class="chart-placeholder">
          <p>持仓分布图表</p>
          <div class="mock-chart">
            <div class="chart-bar" style="height: 60%">BTC 40%</div>
            <div class="chart-bar" style="height: 45%">ETH 30%</div>
            <div class="chart-bar" style="height: 30%">ADA 20%</div>
            <div class="chart-bar" style="height: 15%">SOL 10%</div>
          </div>
        </div>
      </div>

      <div class="chart-card">
        <h3>📈 盈亏趋势</h3>
        <div class="chart-placeholder">
          <p>盈亏趋势图表</p>
          <div class="trend-line">
            <div class="trend-point positive"></div>
            <div class="trend-point positive"></div>
            <div class="trend-point negative"></div>
            <div class="trend-point positive"></div>
            <div class="trend-point positive"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- 分析指标 -->
    <div class="analysis-metrics">
      <h3>📊 分析指标</h3>
      <div class="metrics-grid">
        <div class="metric-card">
          <div class="metric-header">
            <span class="metric-name">夏普比率</span>
            <span class="metric-value">1.85</span>
          </div>
          <div class="metric-desc">风险调整后收益指标</div>
        </div>
        <div class="metric-card">
          <div class="metric-header">
            <span class="metric-name">最大回撤</span>
            <span class="metric-value negative">-8.5%</span>
          </div>
          <div class="metric-desc">历史最大亏损幅度</div>
        </div>
        <div class="metric-card">
          <div class="metric-header">
            <span class="metric-name">波动率</span>
            <span class="metric-value">12.3%</span>
          </div>
          <div class="metric-desc">收益率标准差</div>
        </div>
        <div class="metric-card">
          <div class="metric-header">
            <span class="metric-name">信息比率</span>
            <span class="metric-value">0.67</span>
          </div>
          <div class="metric-desc">超额收益与跟踪误差比</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'

onMounted(() => {
  console.log('📈 持仓分析页面已加载')
})
</script>

<style scoped>
.position-analysis-view {
  padding: 24px;
  background: var(--el-bg-color-page);
  min-height: 100vh;
}

.page-header {
  margin-bottom: 32px;
  text-align: center;
}

.page-title {
  margin: 0 0 8px 0;
  font-size: 32px;
  font-weight: 700;
  color: var(--el-text-color-primary);
}

.page-description {
  margin: 0;
  font-size: 18px;
  color: var(--el-text-color-regular);
}

.analysis-charts {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-bottom: 32px;
}

.chart-card, .analysis-metrics {
  background: var(--el-bg-color);
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.chart-card h3, .analysis-metrics h3 {
  margin: 0 0 20px 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.chart-placeholder {
  height: 200px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: var(--el-bg-color-page);
  border-radius: 8px;
  border: 2px dashed #dee2e6;
}

.mock-chart {
  display: flex;
  align-items: end;
  gap: 12px;
  height: 100px;
  margin-top: 20px;
}

.chart-bar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  text-align: center;
  min-width: 60px;
  display: flex;
  align-items: end;
  justify-content: center;
}

.trend-line {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-top: 20px;
}

.trend-point {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.trend-point.positive {
  background: #27ae60;
}

.trend-point.negative {
  background: #e74c3c;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
}

.metric-card {
  background: var(--el-bg-color-page);
  border-radius: 8px;
  padding: 16px;
  border: 1px solid #dee2e6;
}

.metric-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.metric-name {
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.metric-value {
  font-weight: 700;
  color: var(--el-text-color-primary);
  font-size: 18px;
}

.metric-value.negative {
  color: #e74c3c;
}

.metric-desc {
  font-size: 12px;
  color: var(--el-text-color-regular);
}

@media (max-width: 768px) {
  .position-analysis-view {
    padding: 16px;
  }
  
  .analysis-charts {
    grid-template-columns: 1fr;
  }
  
  .metrics-grid {
    grid-template-columns: 1fr;
  }
}
</style>