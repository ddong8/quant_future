/**
 * 订单状态管理
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Order } from '@/api/order'

export const useOrderStore = defineStore('order', () => {
  // 状态
  const orders = ref<Map<number, Order>>(new Map())
  const activeOrders = ref<Set<number>>(new Set())
  const recentUpdates = ref<Map<number, string>>(new Map()) // order_id -> timestamp
  
  // 计算属性
  const orderList = computed(() => Array.from(orders.value.values()))
  
  const activeOrderList = computed(() => 
    orderList.value.filter(order => activeOrders.value.has(order.id))
  )
  
  const orderCount = computed(() => orders.value.size)
  
  const activeOrderCount = computed(() => activeOrders.value.size)
  
  const recentlyUpdatedOrders = computed(() => {
    const now = Date.now()
    const fiveMinutesAgo = now - 5 * 60 * 1000 // 5分钟前
    
    return orderList.value.filter(order => {
      const updateTime = recentUpdates.value.get(order.id)
      return updateTime && new Date(updateTime).getTime() > fiveMinutesAgo
    })
  })

  // 操作方法
  const setOrders = (orderList: Order[]) => {
    orders.value.clear()
    activeOrders.value.clear()
    
    orderList.forEach(order => {
      orders.value.set(order.id, order)
      if (order.is_active) {
        activeOrders.value.add(order.id)
      }
    })
  }

  const addOrder = (order: Order) => {
    orders.value.set(order.id, order)
    if (order.is_active) {
      activeOrders.value.add(order.id)
    }
    recentUpdates.value.set(order.id, new Date().toISOString())
  }

  const updateOrder = (orderId: number, updates: Partial<Order>) => {
    const existingOrder = orders.value.get(orderId)
    if (existingOrder) {
      const updatedOrder = { ...existingOrder, ...updates }
      orders.value.set(orderId, updatedOrder)
      
      // 更新活跃订单集合
      if (updatedOrder.is_active) {
        activeOrders.value.add(orderId)
      } else {
        activeOrders.value.delete(orderId)
      }
      
      recentUpdates.value.set(orderId, new Date().toISOString())
    }
  }

  const updateOrderStatus = (orderId: number, statusUpdate: {
    status: string
    filled_quantity?: number
    remaining_quantity?: number
    avg_fill_price?: number
    fill_ratio?: number
    is_active?: boolean
    is_finished?: boolean
  }) => {
    const existingOrder = orders.value.get(orderId)
    if (existingOrder) {
      const updatedOrder = { ...existingOrder, ...statusUpdate }
      orders.value.set(orderId, updatedOrder)
      
      // 更新活跃订单集合
      if (statusUpdate.is_active !== undefined) {
        if (statusUpdate.is_active) {
          activeOrders.value.add(orderId)
        } else {
          activeOrders.value.delete(orderId)
        }
      }
      
      recentUpdates.value.set(orderId, new Date().toISOString())
    }
  }

  const removeOrder = (orderId: number) => {
    orders.value.delete(orderId)
    activeOrders.value.delete(orderId)
    recentUpdates.value.delete(orderId)
  }

  const getOrder = (orderId: number): Order | undefined => {
    return orders.value.get(orderId)
  }

  const getOrdersBySymbol = (symbol: string): Order[] => {
    return orderList.value.filter(order => order.symbol === symbol)
  }

  const getOrdersByStatus = (status: string): Order[] => {
    return orderList.value.filter(order => order.status === status)
  }

  const getOrdersByStrategy = (strategyId: number): Order[] => {
    return orderList.value.filter(order => order.strategy_id === strategyId)
  }

  const isOrderRecentlyUpdated = (orderId: number, minutes: number = 5): boolean => {
    const updateTime = recentUpdates.value.get(orderId)
    if (!updateTime) return false
    
    const now = Date.now()
    const threshold = now - minutes * 60 * 1000
    return new Date(updateTime).getTime() > threshold
  }

  const clearRecentUpdates = () => {
    recentUpdates.value.clear()
  }

  const getOrderStats = () => {
    const stats = {
      total: 0,
      active: 0,
      filled: 0,
      cancelled: 0,
      rejected: 0,
      pending: 0
    }
    
    orderList.value.forEach(order => {
      stats.total++
      
      switch (order.status) {
        case 'filled':
          stats.filled++
          break
        case 'cancelled':
          stats.cancelled++
          break
        case 'rejected':
          stats.rejected++
          break
        case 'pending':
        case 'submitted':
        case 'accepted':
          stats.pending++
          break
      }
      
      if (order.is_active) {
        stats.active++
      }
    })
    
    return stats
  }

  // 批量操作
  const batchUpdateOrders = (updates: Array<{ orderId: number; updates: Partial<Order> }>) => {
    updates.forEach(({ orderId, updates }) => {
      updateOrder(orderId, updates)
    })
  }

  const batchRemoveOrders = (orderIds: number[]) => {
    orderIds.forEach(orderId => {
      removeOrder(orderId)
    })
  }

  // 清空所有数据
  const clear = () => {
    orders.value.clear()
    activeOrders.value.clear()
    recentUpdates.value.clear()
  }

  // 订单筛选和排序
  const filterOrders = (predicate: (order: Order) => boolean): Order[] => {
    return orderList.value.filter(predicate)
  }

  const sortOrders = (compareFn: (a: Order, b: Order) => number): Order[] => {
    return [...orderList.value].sort(compareFn)
  }

  // 订单搜索
  const searchOrders = (query: string): Order[] => {
    const lowerQuery = query.toLowerCase()
    return orderList.value.filter(order => 
      order.symbol.toLowerCase().includes(lowerQuery) ||
      order.status.toLowerCase().includes(lowerQuery) ||
      order.side.toLowerCase().includes(lowerQuery) ||
      order.order_type.toLowerCase().includes(lowerQuery) ||
      (order.notes && order.notes.toLowerCase().includes(lowerQuery)) ||
      order.tags.some(tag => tag.toLowerCase().includes(lowerQuery))
    )
  }

  return {
    // 状态
    orders,
    activeOrders,
    recentUpdates,
    
    // 计算属性
    orderList,
    activeOrderList,
    orderCount,
    activeOrderCount,
    recentlyUpdatedOrders,
    
    // 方法
    setOrders,
    addOrder,
    updateOrder,
    updateOrderStatus,
    removeOrder,
    getOrder,
    getOrdersBySymbol,
    getOrdersByStatus,
    getOrdersByStrategy,
    isOrderRecentlyUpdated,
    clearRecentUpdates,
    getOrderStats,
    batchUpdateOrders,
    batchRemoveOrders,
    clear,
    filterOrders,
    sortOrders,
    searchOrders
  }
})