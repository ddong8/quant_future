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

export interface Quote {
  id: number
  symbol_id: number
  symbol?: Symbol
  price: number
  bid_price?: number
  ask_price?: number
  bid_size?: number
  ask_size?: number
  change?: number
  change_percent?: number
  volume?: number
  turnover?: number
  open_price?: number
  high_price?: number
  low_price?: number
  prev_close?: number
  data_provider: string
  data_status: string
  delay_seconds: number
  quote_time: string
  received_at: string
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

// 获取市场行情
export function getMarketQuotes(symbols?: string, limit?: number) {
  const params: any = {}
  if (symbols) params.symbols = symbols
  if (limit) params.limit = limit
  
  return request<Quote[]>({
    url: '/market/quotes',
    method: 'GET',
    params
  })
}

// 获取单个标的行情
export function getSymbolQuote(symbolCode: string) {
  return request<Quote>({
    url: `/market/quotes/${symbolCode}`,
    method: 'GET'
  })
}

// 搜索标的
export function searchSymbols(params: SymbolSearchParams) {
  return request<Symbol[]>({
    url: '/market/symbols/search',
    method: 'GET',
    params
  })
}

// 获取热门标的
export function getPopularSymbols(limit?: number) {
  return request<Symbol[]>({
    url: '/market/symbols/popular',
    method: 'GET',
    params: { limit }
  })
}

// 获取自选股列表
export function getWatchlist() {
  return request<WatchlistItem[]>({
    url: '/market/watchlist',
    method: 'GET'
  })
}

// 添加到自选股
export function addToWatchlist(symbolCode: string) {
  return request<WatchlistItem>({
    url: '/market/watchlist',
    method: 'POST',
    data: { symbol_code: symbolCode }
  })
}

// 从自选股移除
export function removeFromWatchlist(watchlistId: number) {
  return request({
    url: `/market/watchlist/${watchlistId}`,
    method: 'DELETE'
  })
}

// 更新自选股排序
export function updateWatchlistItem(watchlistId: number, sortOrder: number) {
  return request<WatchlistItem>({
    url: `/market/watchlist/${watchlistId}`,
    method: 'PUT',
    data: { sort_order: sortOrder }
  })
}

// 重新排序自选股
export function reorderWatchlist(watchlistIds: number[]) {
  return request({
    url: '/market/watchlist/reorder',
    method: 'POST',
    data: watchlistIds
  })
}