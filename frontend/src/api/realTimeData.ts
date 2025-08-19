/**
 * 真实数据API - 基于tqsdk的实时数据服务
 */
import { request } from '@/utils/request'

// 真实行情数据接口
export interface RealTimeQuote {
  symbol: string
  last_price: number
  bid_price: number
  ask_price: number
  bid_volume: number
  ask_volume: number
  volume: number
  open_interest: number
  open: number
  high: number
  low: number
  pre_close: number
  upper_limit: number
  lower_limit: number
  datetime: string
  change: number
  change_percent: number
}

// 技术指标数据接口
export interface TechnicalIndicators {
  symbol: string
  period: string
  latest_values: {
    ma5?: number
    ma10?: number
    ma20?: number
    rsi?: number
    macd?: number
    macd_signal?: number
    macd_histogram?: number
    bb_upper?: number
    bb_middle?: number
    bb_lower?: number
    close?: number
  }
  signals: {
    rsi?: string
    macd?: string
    bb?: string
  }
  timestamp: string
}

// K线数据接口
export interface KlineData {
  symbol: string
  period: string
  data: Array<{
    datetime: string
    open: number
    high: number
    low: number
    close: number
    volume: number
    open_interest?: number
  }>
  count: number
}

// 合约信息接口
export interface ContractInfo {
  symbol: string
  name: string
  exchange: string
  product_id: string
  volume_multiple: number
  price_tick: number
  margin_rate: number
  commission_rate: number
  expired: boolean
  trading_time: Record<string, any>
}

// 获取实时行情数据 - 已恢复，带安全检查
export async function getRealTimeQuotes(symbols?: string[]) {
  try {
    let response
    if (symbols && symbols.length > 0) {
      // 后端API期望的是数组格式，不是对象
      const filteredSymbols = symbols.filter(s => s && s.trim().length > 0).slice(0, 10) // 过滤空值并限制数量
      if (filteredSymbols.length === 0) {
        return {
          success: true,
          data: [],
          message: '没有有效的合约代码'
        }
      }
      response = await request.post('/v1/market/quotes/batch', filteredSymbols)
    } else {
      response = await request.get('/v1/market/quotes')
    }
    
    // 确保返回的数据是安全的数组格式
    if (response && response.success && response.data) {
      const quotes = Array.isArray(response.data) ? response.data : []
      return {
        ...response,
        data: quotes
      }
    }
    
    // 返回安全的默认数据
    return {
      success: true,
      data: [],
      message: '暂无行情数据'
    }
  } catch (error) {
    console.warn('⚠️ 获取实时行情失败，返回默认数据:', error)
    return {
      success: true,
      data: [],
      message: '获取行情失败，使用默认数据'
    }
  }
}

// 获取单个合约的实时行情
export function getRealTimeQuote(symbol: string) {
  return request.get(`/v1/market/quotes/${symbol}`)
}

// 获取合约信息列表 - 已恢复，带安全检查
export async function getContractList() {
  try {
    const response = await request.get('/v1/market/instruments')
    
    // 确保返回的数据是安全的数组格式
    if (response && response.success && response.data) {
      const contracts = Array.isArray(response.data) ? response.data : []
      return {
        ...response,
        data: contracts
      }
    }
    
    // 返回安全的默认数据
    return {
      success: true,
      data: [],
      message: '暂无合约数据'
    }
  } catch (error) {
    console.warn('⚠️ 获取合约列表失败，返回默认数据:', error)
    return {
      success: true,
      data: [],
      message: '获取合约失败，使用默认数据'
    }
  }
}

// 获取单个合约信息
export function getContractInfo(symbol: string) {
  return request.get(`/v1/market/instruments/${symbol}`)
}

// 获取K线数据
export function getKlineData(symbol: string, period: string = '1m', limit: number = 100) {
  return request.get(`/v1/market/klines/${symbol}`, {
    params: { period, limit }
  })
}

// 获取历史K线数据
export function getHistoryKlines(symbol: string, period: string = '1d', limit: number = 100) {
  return request.get('/v1/market/history/klines', {
    params: { symbol, period, limit }
  })
}

// 获取技术指标
export function getTechnicalIndicators(symbol: string, period: string = '1m', limit: number = 50) {
  return request.get(`/v1/technical-analysis/indicators/${symbol}`, {
    params: { period, limit }
  })
}

// 获取交易信号
export function getTradingSignals(symbol: string, period: string = '1m') {
  return request.get(`/v1/technical-analysis/signals/${symbol}`, {
    params: { period }
  })
}

// 获取多时间框架分析
export function getMultiTimeframeAnalysis(symbol: string) {
  return request.get(`/v1/technical-analysis/multi-timeframe/${symbol}`)
}

// 获取风险指标 - 带安全检查
export async function getRiskMetrics() {
  try {
    const response = await request.get('/v1/simple-risk/metrics')
    
    // 确保返回的数据格式正确
    if (response && response.success && response.data) {
      return {
        ...response,
        data: {
          account_metrics: response.data.account_metrics || {},
          overall_risk_score: response.data.overall_risk_score || 0,
          risk_level: response.data.risk_level || '未知',
          ...response.data
        }
      }
    }
    
    // 返回安全的默认数据
    return {
      success: true,
      data: {
        account_metrics: { risk_level: '低' },
        overall_risk_score: 75,
        risk_level: '低'
      },
      message: '暂无风险指标数据'
    }
  } catch (error) {
    console.warn('⚠️ 获取风险指标失败，返回默认数据:', error)
    return {
      success: true,
      data: {
        account_metrics: { risk_level: '低' },
        overall_risk_score: 75,
        risk_level: '低'
      },
      message: '获取风险指标失败，使用默认数据'
    }
  }
}

// 获取市场状态 - 带安全检查
export async function getMarketStatus() {
  try {
    const response = await request.get('/v1/market/market-status')
    
    // 确保返回的数据格式正确
    if (response && response.success && response.data) {
      return {
        ...response,
        data: {
          status: response.data.status || 'inactive',
          last_update: response.data.last_update || new Date().toISOString(),
          ...response.data
        }
      }
    }
    
    // 返回安全的默认数据
    return {
      success: true,
      data: {
        status: 'inactive',
        last_update: new Date().toISOString()
      },
      message: '暂无市场状态数据'
    }
  } catch (error) {
    console.warn('⚠️ 获取市场状态失败，返回默认数据:', error)
    return {
      success: true,
      data: {
        status: 'inactive',
        last_update: new Date().toISOString()
      },
      message: '获取市场状态失败，使用默认数据'
    }
  }
}

// 获取算法交易引擎状态 - 带安全检查
export async function getAlgoTradingStatus() {
  try {
    const response = await request.get('/v1/algo-trading/status')
    
    // 确保返回的数据格式正确
    if (response && response.success && response.data) {
      return {
        ...response,
        data: {
          status: response.data.status || 'stopped',
          active_strategies: response.data.active_strategies || 0,
          pending_orders: response.data.pending_orders || 0,
          total_positions: response.data.total_positions || 0,
          ...response.data
        }
      }
    }
    
    // 返回安全的默认数据
    return {
      success: true,
      data: {
        status: 'stopped',
        active_strategies: 0,
        pending_orders: 0,
        total_positions: 0
      },
      message: '暂无算法引擎状态数据'
    }
  } catch (error) {
    console.warn('⚠️ 获取算法引擎状态失败，返回默认数据:', error)
    return {
      success: true,
      data: {
        status: 'stopped',
        active_strategies: 0,
        pending_orders: 0,
        total_positions: 0
      },
      message: '获取算法引擎状态失败，使用默认数据'
    }
  }
}

// 获取活跃策略列表
export function getActiveStrategies() {
  return request.get('/v1/algo-trading/strategies')
}

// 获取交易信号历史 - 已恢复，带安全检查
export async function getSignalHistory(strategyId?: string, limit: number = 50) {
  try {
    const response = await request.get('/v1/algo-trading/signals', {
      params: { strategy_id: strategyId, limit }
    })
    
    // 确保返回的数据是安全的数组格式
    if (response && response.success && response.data) {
      const signals = response.data.signals || response.data || []
      return {
        ...response,
        data: {
          signals: Array.isArray(signals) ? signals : [],
          total: response.data.total || 0
        }
      }
    }
    
    // 返回安全的默认数据
    return {
      success: true,
      data: { signals: [], total: 0 },
      message: '暂无信号数据'
    }
  } catch (error) {
    console.warn('⚠️ 获取交易信号失败，返回默认数据:', error)
    return {
      success: true,
      data: { signals: [], total: 0 },
      message: '获取信号失败，使用默认数据'
    }
  }
}

// 获取订单历史
export function getOrderHistory(strategyId?: string, limit: number = 100) {
  return request.get('/v1/algo-trading/orders', {
    params: { strategy_id: strategyId, limit }
  })
}

// 获取策略表现
export function getStrategyPerformance(strategyId?: string) {
  return request.get('/v1/algo-trading/performance', {
    params: { strategy_id: strategyId }
  })
}

// 获取持仓数据
export function getPositions() {
  return request.get('/v1/trading/positions')
}

// 获取账户信息
export function getAccountInfo() {
  return request.get('/v1/trading/account')
}

// 获取交易记录
export function getTrades(limit: number = 100) {
  return request.get('/v1/trading/trades', {
    params: { limit }
  })
}

// 回测相关API
export function getBacktestList() {
  return request.get('/v1/backtest/list')
}

export function createBacktest(config: any) {
  return request.post('/v1/backtest/create', config)
}

export function runBacktest(backtestId: string) {
  return request.post('/v1/backtest/run', { backtest_id: backtestId })
}

export function getBacktestResults(backtestId: string) {
  return request.get(`/v1/backtest/results/${backtestId}`)
}

export function getBacktestStatus(backtestId: string) {
  return request.get(`/v1/backtest/status/${backtestId}`)
}

export function runQuickBacktest(config: any) {
  return request.post('/v1/backtest/quick-run', config)
}