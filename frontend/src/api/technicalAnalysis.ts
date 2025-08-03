/**
 * 技术分析API
 */
import { request } from '@/utils/request'

export interface KlineData {
  timestamp: number
  open: number
  high: number
  low: number
  close: number
  volume: number
  turnover: number
  trade_count: number
  vwap: number
}

export interface TechnicalIndicators {
  symbol: string
  interval: string
  kline_data: KlineData[]
  indicators: {
    ma5?: number[]
    ma10?: number[]
    ma20?: number[]
    ma60?: number[]
    ema12?: number[]
    ema26?: number[]
    bollinger?: {
      upper: number[]
      middle: number[]
      lower: number[]
    }
    rsi?: number[]
    macd?: {
      macd: number[]
      signal: number[]
      histogram: number[]
    }
    kdj?: {
      k: number[]
      d: number[]
      j: number[]
    }
  }
}

export interface ChartConfig {
  id: number
  name: string
  config: {
    indicators: string[]
    chart_type: string
    theme: string
  }
}

// 获取K线数据
export function getKlineData(
  symbolCode: string,
  interval: string = '1d',
  startTime?: string,
  endTime?: string,
  limit: number = 500
) {
  const params: any = { interval, limit }
  if (startTime) params.start_time = startTime
  if (endTime) params.end_time = endTime

  return request<{
    symbol: string
    interval: string
    data: KlineData[]
    count: number
  }>({
    url: `/technical/kline/${symbolCode}`,
    method: 'GET',
    params
  })
}

// 获取技术指标数据
export function getTechnicalIndicators(
  symbolCode: string,
  interval: string = '1d',
  indicators?: string[],
  limit: number = 500
) {
  const params: any = { interval, limit }
  if (indicators && indicators.length > 0) {
    params.indicators = indicators.join(',')
  }

  return request<TechnicalIndicators>({
    url: `/technical/indicators/${symbolCode}`,
    method: 'GET',
    params
  })
}

// 获取移动平均线
export function getMovingAverage(
  symbolCode: string,
  period: number = 20,
  interval: string = '1d',
  priceType: string = 'close',
  limit: number = 500
) {
  return request<{
    symbol: string
    indicator: string
    period: number
    price_type: string
    data: number[]
  }>({
    url: `/technical/indicators/ma/${symbolCode}`,
    method: 'GET',
    params: { period, interval, price_type: priceType, limit }
  })
}

// 获取布林带
export function getBollingerBands(
  symbolCode: string,
  period: number = 20,
  stdDev: number = 2.0,
  interval: string = '1d',
  priceType: string = 'close',
  limit: number = 500
) {
  return request<{
    symbol: string
    indicator: string
    period: number
    std_dev: number
    price_type: string
    data: {
      upper: number[]
      middle: number[]
      lower: number[]
    }
  }>({
    url: `/technical/indicators/bollinger/${symbolCode}`,
    method: 'GET',
    params: { period, std_dev: stdDev, interval, price_type: priceType, limit }
  })
}

// 获取RSI指标
export function getRSI(
  symbolCode: string,
  period: number = 14,
  interval: string = '1d',
  priceType: string = 'close',
  limit: number = 500
) {
  return request<{
    symbol: string
    indicator: string
    period: number
    price_type: string
    data: number[]
  }>({
    url: `/technical/indicators/rsi/${symbolCode}`,
    method: 'GET',
    params: { period, interval, price_type: priceType, limit }
  })
}

// 获取MACD指标
export function getMACD(
  symbolCode: string,
  fastPeriod: number = 12,
  slowPeriod: number = 26,
  signalPeriod: number = 9,
  interval: string = '1d',
  priceType: string = 'close',
  limit: number = 500
) {
  return request<{
    symbol: string
    indicator: string
    fast_period: number
    slow_period: number
    signal_period: number
    price_type: string
    data: {
      macd: number[]
      signal: number[]
      histogram: number[]
    }
  }>({
    url: `/technical/indicators/macd/${symbolCode}`,
    method: 'GET',
    params: { 
      fast_period: fastPeriod, 
      slow_period: slowPeriod, 
      signal_period: signalPeriod, 
      interval, 
      price_type: priceType, 
      limit 
    }
  })
}

// 保存图表配置
export function saveChartConfig(configName: string, configData: any) {
  return request({
    url: '/technical/chart-config',
    method: 'POST',
    data: {
      config_name: configName,
      config_data: configData
    }
  })
}

// 获取图表配置
export function getChartConfigs() {
  return request<{
    configs: ChartConfig[]
    count: number
  }>({
    url: '/technical/chart-configs',
    method: 'GET'
  })
}