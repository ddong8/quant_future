<template>
  <el-dialog
    v-model="visible"
    :title="dialogTitle"
    width="500px"
    @close="handleClose"
  >
    <!-- 移动平均线参数 -->
    <div v-if="indicatorType === 'ma'" class="params-form">
      <el-form :model="maParams" label-width="100px">
        <el-form-item label="周期">
          <el-input-number v-model="maParams.period" :min="1" :max="200" />
        </el-form-item>
        <el-form-item label="价格类型">
          <el-select v-model="maParams.priceType">
            <el-option label="收盘价" value="close" />
            <el-option label="开盘价" value="open" />
            <el-option label="最高价" value="high" />
            <el-option label="最低价" value="low" />
          </el-select>
        </el-form-item>
        <el-form-item label="线条颜色">
          <el-color-picker v-model="maParams.color" />
        </el-form-item>
      </el-form>
    </div>

    <!-- 布林带参数 -->
    <div v-else-if="indicatorType === 'bollinger'" class="params-form">
      <el-form :model="bollingerParams" label-width="100px">
        <el-form-item label="周期">
          <el-input-number v-model="bollingerParams.period" :min="1" :max="200" />
        </el-form-item>
        <el-form-item label="标准差倍数">
          <el-input-number v-model="bollingerParams.stdDev" :min="0.1" :max="5" :step="0.1" />
        </el-form-item>
        <el-form-item label="价格类型">
          <el-select v-model="bollingerParams.priceType">
            <el-option label="收盘价" value="close" />
            <el-option label="开盘价" value="open" />
            <el-option label="最高价" value="high" />
            <el-option label="最低价" value="low" />
          </el-select>
        </el-form-item>
        <el-form-item label="上轨颜色">
          <el-color-picker v-model="bollingerParams.upperColor" />
        </el-form-item>
        <el-form-item label="中轨颜色">
          <el-color-picker v-model="bollingerParams.middleColor" />
        </el-form-item>
        <el-form-item label="下轨颜色">
          <el-color-picker v-model="bollingerParams.lowerColor" />
        </el-form-item>
      </el-form>
    </div>

    <!-- RSI参数 -->
    <div v-else-if="indicatorType === 'rsi'" class="params-form">
      <el-form :model="rsiParams" label-width="100px">
        <el-form-item label="周期">
          <el-input-number v-model="rsiParams.period" :min="1" :max="100" />
        </el-form-item>
        <el-form-item label="价格类型">
          <el-select v-model="rsiParams.priceType">
            <el-option label="收盘价" value="close" />
            <el-option label="开盘价" value="open" />
            <el-option label="最高价" value="high" />
            <el-option label="最低价" value="low" />
          </el-select>
        </el-form-item>
        <el-form-item label="超买线">
          <el-input-number v-model="rsiParams.overbought" :min="50" :max="100" />
        </el-form-item>
        <el-form-item label="超卖线">
          <el-input-number v-model="rsiParams.oversold" :min="0" :max="50" />
        </el-form-item>
        <el-form-item label="线条颜色">
          <el-color-picker v-model="rsiParams.color" />
        </el-form-item>
      </el-form>
    </div>

    <!-- MACD参数 -->
    <div v-else-if="indicatorType === 'macd'" class="params-form">
      <el-form :model="macdParams" label-width="100px">
        <el-form-item label="快线周期">
          <el-input-number v-model="macdParams.fastPeriod" :min="1" :max="100" />
        </el-form-item>
        <el-form-item label="慢线周期">
          <el-input-number v-model="macdParams.slowPeriod" :min="1" :max="200" />
        </el-form-item>
        <el-form-item label="信号线周期">
          <el-input-number v-model="macdParams.signalPeriod" :min="1" :max="50" />
        </el-form-item>
        <el-form-item label="价格类型">
          <el-select v-model="macdParams.priceType">
            <el-option label="收盘价" value="close" />
            <el-option label="开盘价" value="open" />
            <el-option label="最高价" value="high" />
            <el-option label="最低价" value="low" />
          </el-select>
        </el-form-item>
        <el-form-item label="MACD颜色">
          <el-color-picker v-model="macdParams.macdColor" />
        </el-form-item>
        <el-form-item label="信号线颜色">
          <el-color-picker v-model="macdParams.signalColor" />
        </el-form-item>
        <el-form-item label="柱状图颜色">
          <div class="color-group">
            <span>正值:</span>
            <el-color-picker v-model="macdParams.histogramUpColor" />
            <span>负值:</span>
            <el-color-picker v-model="macdParams.histogramDownColor" />
          </div>
        </el-form-item>
      </el-form>
    </div>

    <!-- KDJ参数 -->
    <div v-else-if="indicatorType === 'kdj'" class="params-form">
      <el-form :model="kdjParams" label-width="100px">
        <el-form-item label="K周期">
          <el-input-number v-model="kdjParams.kPeriod" :min="1" :max="100" />
        </el-form-item>
        <el-form-item label="D周期">
          <el-input-number v-model="kdjParams.dPeriod" :min="1" :max="50" />
        </el-form-item>
        <el-form-item label="J周期">
          <el-input-number v-model="kdjParams.jPeriod" :min="1" :max="50" />
        </el-form-item>
        <el-form-item label="K线颜色">
          <el-color-picker v-model="kdjParams.kColor" />
        </el-form-item>
        <el-form-item label="D线颜色">
          <el-color-picker v-model="kdjParams.dColor" />
        </el-form-item>
        <el-form-item label="J线颜色">
          <el-color-picker v-model="kdjParams.jColor" />
        </el-form-item>
      </el-form>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button @click="handleReset">重置</el-button>
        <el-button type="primary" @click="handleConfirm">确定</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'

interface Props {
  modelValue: boolean
  indicatorType: string
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'confirm', params: any): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 响应式数据
const visible = ref(false)

// 各指标的默认参数
const defaultParams = {
  ma: {
    period: 20,
    priceType: 'close',
    color: '#409eff'
  },
  bollinger: {
    period: 20,
    stdDev: 2.0,
    priceType: 'close',
    upperColor: '#ff9f43',
    middleColor: '#feca57',
    lowerColor: '#ff9f43'
  },
  rsi: {
    period: 14,
    priceType: 'close',
    overbought: 70,
    oversold: 30,
    color: '#ff6b6b'
  },
  macd: {
    fastPeriod: 12,
    slowPeriod: 26,
    signalPeriod: 9,
    priceType: 'close',
    macdColor: '#409eff',
    signalColor: '#ff6b6b',
    histogramUpColor: '#ef232a',
    histogramDownColor: '#14b143'
  },
  kdj: {
    kPeriod: 9,
    dPeriod: 3,
    jPeriod: 3,
    kColor: '#409eff',
    dColor: '#ff6b6b',
    jColor: '#67c23a'
  }
}

// 各指标参数
const maParams = ref({ ...defaultParams.ma })
const bollingerParams = ref({ ...defaultParams.bollinger })
const rsiParams = ref({ ...defaultParams.rsi })
const macdParams = ref({ ...defaultParams.macd })
const kdjParams = ref({ ...defaultParams.kdj })

// 对话框标题
const dialogTitle = computed(() => {
  const titles: Record<string, string> = {
    ma: '移动平均线参数',
    bollinger: '布林带参数',
    rsi: 'RSI参数',
    macd: 'MACD参数',
    kdj: 'KDJ参数'
  }
  return titles[props.indicatorType] || '指标参数'
})

// 监听 modelValue 变化
watch(() => props.modelValue, (newValue) => {
  visible.value = newValue
})

// 监听 visible 变化
watch(visible, (newValue) => {
  emit('update:modelValue', newValue)
})

// 重置参数
const handleReset = () => {
  switch (props.indicatorType) {
    case 'ma':
      maParams.value = { ...defaultParams.ma }
      break
    case 'bollinger':
      bollingerParams.value = { ...defaultParams.bollinger }
      break
    case 'rsi':
      rsiParams.value = { ...defaultParams.rsi }
      break
    case 'macd':
      macdParams.value = { ...defaultParams.macd }
      break
    case 'kdj':
      kdjParams.value = { ...defaultParams.kdj }
      break
  }
}

// 确认参数
const handleConfirm = () => {
  let params = {}
  
  switch (props.indicatorType) {
    case 'ma':
      params = { ...maParams.value }
      break
    case 'bollinger':
      params = { ...bollingerParams.value }
      break
    case 'rsi':
      params = { ...rsiParams.value }
      break
    case 'macd':
      params = { ...macdParams.value }
      break
    case 'kdj':
      params = { ...kdjParams.value }
      break
  }
  
  emit('confirm', params)
  visible.value = false
}

// 关闭对话框
const handleClose = () => {
  visible.value = false
}
</script>

<style scoped>
.params-form {
  padding: 20px 0;
}

.color-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.color-group span {
  font-size: 14px;
  color: #606266;
}

.dialog-footer {
  text-align: right;
}
</style>