/**
 * 行情数据API
 */
import { request } from '@/utils/request'

export interface Symbol {
  id: number
  symbol: string
  name: string
  exchange: string
  market?: string
  asset_type: string
  currency: string
  is_tradable: boolean
  is_active: boolean
}

// 合约信息（来自后端 InstrumentInfo）
export interface InstrumentInfo {
  symbol: string
  exchange: string
  name: string
  product_id: string
  volume_multiple: number
  price_tick: number
  margin_rate: number
  commission_rate: number
  expired: boolean
  trading_time: Record<string, any>
}

// 行情数据（来自后端 QuoteData）
export interface Quote {
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
  
  // 计算字段
  change?: number
  change_percent?: number
  turnover?: number
  data_status?: string
}

export interface WatchlistItem {
  id: number
  symbol: Symbol
  quote?: Quote
  sort_order: number
  created_at: string
}

export interface SymbolSearchParams {
  q: string
  limit?: number
}

// 获取合约信息列表（用于市场行情页面）
export function getMarketQuotes(symbols?: string, limit?: number) {
  return request.get('/v1/market/instruments')
}

// 批量获取行情数据
export async function getQuotesBatch(symbols: string[]) {
  try {
    // 过滤和验证输入数据
    const filteredSymbols = symbols.filter(s => s && s.trim().length > 0).slice(0, 10)
    
    if (filteredSymbols.length === 0) {
      return {
        success: true,
        data: [],
        message: '没有有效的合约代码'
      }
    }
    
    const response = await request.post('/v1/market/quotes/batch', filteredSymbols)
    
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
    console.warn('⚠️ 批量获取行情失败，返回默认数据:', error)
    return {
      success: true,
      data: [],
      message: '获取行情失败，使用默认数据'
    }
  }
}

// 获取单个标的行情
export function getSymbolQuote(symbolCode: string) {
  return request.get(`/v1/market/quotes/${symbolCode}`)
}

// 搜索标的
export function searchSymbols(params: SymbolSearchParams) {
  return request.get('/v1/market/symbols/search', { params })
}

// 获取热门标的
export function getPopularSymbols(limit?: number) {
  return request.get('/v1/market/symbols/popular', { params: { limit } })
}

// 获取自选股列表（暂时返回模拟数据）
export function getWatchlist() {
  // 暂时返回基于合约信息的模拟自选股数据
  return getMarketQuotes().then(response => {
    if (response.success && response.data) {
      // 将前3个合约作为自选股
      const mockWatchlist = response.data.slice(0, 3).map((instrument: any, index: number) => ({
        id: index + 1,
        symbol: {
          id: index + 1,
          symbol: instrument.symbol,
          name: instrument.name,
          exchange: instrument.exchange,
          asset_type: 'future',
          currency: 'CNY',
          is_tradable: true,
          is_active: true
        },
        quote: null, // 稍后可以获取实时行情
        sort_order: index + 1,
        created_at: new Date().toISOString()
      }))
      
      return {
        success: true,
        data: mockWatchlist
      }
    }
    return response
  })
}

// 添加到自选股
export function addToWatchlist(symbolCode: string) {
  return request.post('/v1/market/watchlist', { symbol_code: symbolCode })
}

// 从自选股移除
export function removeFromWatchlist(watchlistId: number) {
  return request.delete(`/v1/market/watchlist/${watchlistId}`)
}

// 更新自选股排序
export function updateWatchlistItem(watchlistId: number, sortOrder: number) {
  return request.put(`/v1/market/watchlist/${watchlistId}`, { sort_order: sortOrder })
}

// 重新排序自选股
export function reorderWatchlist(watchlistIds: number[]) {
  return request.post('/v1/market/watchlist/reorder', watchlistIds)
}
