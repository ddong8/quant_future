/**
 * 交易组件集成测试
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import ManualTradingView from '@/views/trading/ManualTradingView.vue'
import ManualTradingForm from '@/components/ManualTradingForm.vue'
import OrderManagement from '@/components/OrderManagement.vue'
import PositionDisplay from '@/components/PositionDisplay.vue'
import { useTradingStore } from '@/stores/trading'
import * as tradingApi from '@/api/trading'

// Mock API
vi.mock('@/api/trading')

const mockTradingApi = tradingApi as any

// 测试数据
const mockOrders = [
  {
    id: '1',
    symbol: 'SHFE.cu2401',
    side: 'buy',
    order_type: 'limit',
    quantity: 1,
    price: 70000,
    status: 'pending',
    created_at: '2023-01-01T09:00:00Z'
  },
  {
    id: '2',
    symbol: 'DCE.i2401',
    side: 'sell',
    order_type: 'market',
    quantity: 2,
    status: 'filled',
    created_at: '2023-01-01T09:30:00Z'
  }
]

const mockPositions = [
  {
    symbol: 'SHFE.cu2401',
    quantity: 1,
    avg_price: 70000,
    current_price: 70500,
    unrealized_pnl: 500,
    updated_at: '2023-01-01T09:00:00Z'
  },
  {
    symbol: 'DCE.i2401',
    quantity: -2,
    avg_price: 800,
    current_price: 790,
    unrealized_pnl: 20,
    updated_at: '2023-01-01T09:30:00Z'
  }
]

const mockAccountInfo = {
  balance: 100000,
  available: 80000,
  margin_used: 20000,
  unrealized_pnl: 520
}

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/trading', component: ManualTradingView }
  ]
})

describe('交易组件集成测试', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('ManualTradingView', () => {
    it('应该正确加载交易页面', async () => {
      mockTradingApi.getOrders.mockResolvedValue(mockOrders)
      mockTradingApi.getPositions.mockResolvedValue(mockPositions)
      mockTradingApi.getAccountInfo.mockResolvedValue(mockAccountInfo)

      const wrapper = mount(ManualTradingView, {
        global: {
          plugins: [router]
        }
      })

      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 100))

      expect(wrapper.findComponent(ManualTradingForm).exists()).toBe(true)
      expect(wrapper.findComponent(OrderManagement).exists()).toBe(true)
      expect(wrapper.findComponent(PositionDisplay).exists()).toBe(true)
    })

    it('应该显示账户信息', async () => {
      mockTradingApi.getAccountInfo.mockResolvedValue(mockAccountInfo)

      const wrapper = mount(ManualTradingView, {
        global: {
          plugins: [router]
        }
      })

      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 100))

      expect(wrapper.text()).toContain('100,000') // 余额
      expect(wrapper.text()).toContain('80,000')  // 可用资金
      expect(wrapper.text()).toContain('20,000')  // 已用保证金
      expect(wrapper.text()).toContain('520')     // 浮动盈亏
    })
  })

  describe('ManualTradingForm', () => {
    it('应该正确渲染交易表单', () => {
      const wrapper = mount(ManualTradingForm, {
        global: {
          plugins: [router]
        }
      })

      expect(wrapper.find('select[name="symbol"]').exists()).toBe(true)
      expect(wrapper.find('select[name="side"]').exists()).toBe(true)
      expect(wrapper.find('select[name="order_type"]').exists()).toBe(true)
      expect(wrapper.find('input[name="quantity"]').exists()).toBe(true)
      expect(wrapper.find('input[name="price"]').exists()).toBe(true)
    })

    it('应该验证表单字段', async () => {
      const wrapper = mount(ManualTradingForm, {
        global: {
          plugins: [router]
        }
      })

      // 提交空表单
      const submitButton = wrapper.find('button[type="submit"]')
      await submitButton.trigger('click')

      expect(wrapper.text()).toContain('请选择合约')
      expect(wrapper.text()).toContain('请输入数量')
    })

    it('应该根据订单类型显示/隐藏价格字段', async () => {
      const wrapper = mount(ManualTradingForm, {
        global: {
          plugins: [router]
        }
      })

      // 选择限价单
      const orderTypeSelect = wrapper.find('select[name="order_type"]')
      await orderTypeSelect.setValue('limit')

      expect(wrapper.find('input[name="price"]').isVisible()).toBe(true)

      // 选择市价单
      await orderTypeSelect.setValue('market')

      expect(wrapper.find('input[name="price"]').isVisible()).toBe(false)
    })

    it('应该提交买入订单', async () => {
      const newOrder = {
        id: '3',
        symbol: 'SHFE.cu2401',
        side: 'buy',
        order_type: 'limit',
        quantity: 1,
        price: 70000,
        status: 'pending'
      }

      mockTradingApi.createOrder.mockResolvedValue(newOrder)

      const wrapper = mount(ManualTradingForm, {
        global: {
          plugins: [router]
        }
      })

      // 填写表单
      await wrapper.find('select[name="symbol"]').setValue('SHFE.cu2401')
      await wrapper.find('select[name="side"]').setValue('buy')
      await wrapper.find('select[name="order_type"]').setValue('limit')
      await wrapper.find('input[name="quantity"]').setValue('1')
      await wrapper.find('input[name="price"]').setValue('70000')

      // 提交表单
      const submitButton = wrapper.find('button[type="submit"]')
      await submitButton.trigger('click')

      expect(mockTradingApi.createOrder).toHaveBeenCalledWith({
        symbol: 'SHFE.cu2401',
        side: 'buy',
        order_type: 'limit',
        quantity: 1,
        price: 70000
      })

      expect(wrapper.emitted('order-created')).toBeTruthy()
    })

    it('应该提交市价卖出订单', async () => {
      const newOrder = {
        id: '4',
        symbol: 'DCE.i2401',
        side: 'sell',
        order_type: 'market',
        quantity: 2,
        status: 'pending'
      }

      mockTradingApi.createOrder.mockResolvedValue(newOrder)

      const wrapper = mount(ManualTradingForm, {
        global: {
          plugins: [router]
        }
      })

      // 填写表单
      await wrapper.find('select[name="symbol"]').setValue('DCE.i2401')
      await wrapper.find('select[name="side"]').setValue('sell')
      await wrapper.find('select[name="order_type"]').setValue('market')
      await wrapper.find('input[name="quantity"]').setValue('2')

      // 提交表单
      const submitButton = wrapper.find('button[type="submit"]')
      await submitButton.trigger('click')

      expect(mockTradingApi.createOrder).toHaveBeenCalledWith({
        symbol: 'DCE.i2401',
        side: 'sell',
        order_type: 'market',
        quantity: 2
      })
    })

    it('应该处理下单失败', async () => {
      mockTradingApi.createOrder.mockRejectedValue({
        response: { data: { detail: '资金不足' } }
      })

      const wrapper = mount(ManualTradingForm, {
        global: {
          plugins: [router]
        }
      })

      // 填写表单
      await wrapper.find('select[name="symbol"]').setValue('SHFE.cu2401')
      await wrapper.find('select[name="side"]').setValue('buy')
      await wrapper.find('select[name="order_type"]').setValue('limit')
      await wrapper.find('input[name="quantity"]').setValue('100')
      await wrapper.find('input[name="price"]').setValue('70000')

      // 提交表单
      const submitButton = wrapper.find('button[type="submit"]')
      await submitButton.trigger('click')

      await wrapper.vm.$nextTick()

      expect(wrapper.text()).toContain('资金不足')
    })
  })

  describe('OrderManagement', () => {
    it('应该显示订单列表', async () => {
      const wrapper = mount(OrderManagement, {
        props: { orders: mockOrders },
        global: {
          plugins: [router]
        }
      })

      expect(wrapper.text()).toContain('SHFE.cu2401')
      expect(wrapper.text()).toContain('DCE.i2401')
      expect(wrapper.text()).toContain('买入')
      expect(wrapper.text()).toContain('卖出')
      expect(wrapper.text()).toContain('待成交')
      expect(wrapper.text()).toContain('已成交')
    })

    it('应该支持订单筛选', async () => {
      const wrapper = mount(OrderManagement, {
        props: { orders: mockOrders },
        global: {
          plugins: [router]
        }
      })

      // 筛选待成交订单
      const statusFilter = wrapper.find('select[name="status"]')
      await statusFilter.setValue('pending')

      const orderRows = wrapper.findAll('tr[data-test="order-row"]')
      expect(orderRows).toHaveLength(1)
      expect(orderRows[0].text()).toContain('待成交')
    })

    it('应该取消订单', async () => {
      mockTradingApi.cancelOrder.mockResolvedValue({ status: 'cancelled' })

      const wrapper = mount(OrderManagement, {
        props: { orders: mockOrders },
        global: {
          plugins: [router]
        }
      })

      // 点击取消按钮
      const cancelButton = wrapper.find('button[data-test="cancel-order"]')
      await cancelButton.trigger('click')

      // 确认取消
      const confirmButton = wrapper.find('button[data-test="confirm-cancel"]')
      await confirmButton.trigger('click')

      expect(mockTradingApi.cancelOrder).toHaveBeenCalledWith('1')
      expect(wrapper.emitted('order-cancelled')).toBeTruthy()
    })

    it('应该修改订单', async () => {
      const updatedOrder = {
        ...mockOrders[0],
        quantity: 2,
        price: 69500
      }

      mockTradingApi.updateOrder.mockResolvedValue(updatedOrder)

      const wrapper = mount(OrderManagement, {
        props: { orders: mockOrders },
        global: {
          plugins: [router]
        }
      })

      // 点击修改按钮
      const editButton = wrapper.find('button[data-test="edit-order"]')
      await editButton.trigger('click')

      // 修改订单信息
      await wrapper.find('input[name="edit-quantity"]').setValue('2')
      await wrapper.find('input[name="edit-price"]').setValue('69500')

      // 确认修改
      const confirmButton = wrapper.find('button[data-test="confirm-edit"]')
      await confirmButton.trigger('click')

      expect(mockTradingApi.updateOrder).toHaveBeenCalledWith('1', {
        quantity: 2,
        price: 69500
      })
    })
  })

  describe('PositionDisplay', () => {
    it('应该显示持仓列表', () => {
      const wrapper = mount(PositionDisplay, {
        props: { positions: mockPositions },
        global: {
          plugins: [router]
        }
      })

      expect(wrapper.text()).toContain('SHFE.cu2401')
      expect(wrapper.text()).toContain('DCE.i2401')
      expect(wrapper.text()).toContain('1') // 多头数量
      expect(wrapper.text()).toContain('-2') // 空头数量
      expect(wrapper.text()).toContain('500') // 浮动盈亏
    })

    it('应该显示盈亏颜色', () => {
      const wrapper = mount(PositionDisplay, {
        props: { positions: mockPositions },
        global: {
          plugins: [router]
        }
      })

      const pnlCells = wrapper.findAll('[data-test="pnl-cell"]')
      
      // 盈利显示绿色
      expect(pnlCells[0].classes()).toContain('text-green')
      
      // 盈利显示绿色
      expect(pnlCells[1].classes()).toContain('text-green')
    })

    it('应该平仓', async () => {
      mockTradingApi.closePosition.mockResolvedValue({ order_id: 'close_1' })

      const wrapper = mount(PositionDisplay, {
        props: { positions: mockPositions },
        global: {
          plugins: [router]
        }
      })

      // 点击平仓按钮
      const closeButton = wrapper.find('button[data-test="close-position"]')
      await closeButton.trigger('click')

      // 确认平仓
      const confirmButton = wrapper.find('button[data-test="confirm-close"]')
      await confirmButton.trigger('click')

      expect(mockTradingApi.closePosition).toHaveBeenCalledWith('SHFE.cu2401', {
        quantity: 1
      })
    })

    it('应该部分平仓', async () => {
      mockTradingApi.closePosition.mockResolvedValue({ order_id: 'close_2' })

      const wrapper = mount(PositionDisplay, {
        props: { positions: mockPositions },
        global: {
          plugins: [router]
        }
      })

      // 点击部分平仓按钮
      const partialCloseButton = wrapper.find('button[data-test="partial-close"]')
      await partialCloseButton.trigger('click')

      // 输入平仓数量
      await wrapper.find('input[name="close-quantity"]').setValue('0.5')

      // 确认平仓
      const confirmButton = wrapper.find('button[data-test="confirm-close"]')
      await confirmButton.trigger('click')

      expect(mockTradingApi.closePosition).toHaveBeenCalledWith('SHFE.cu2401', {
        quantity: 0.5
      })
    })
  })

  describe('交易流程集成', () => {
    it('应该完成完整的下单-成交-持仓流程', async () => {
      const tradingStore = useTradingStore()

      // 1. 下单
      const newOrder = {
        id: '1',
        symbol: 'SHFE.cu2401',
        side: 'buy',
        order_type: 'limit',
        quantity: 1,
        price: 70000,
        status: 'pending'
      }

      mockTradingApi.createOrder.mockResolvedValue(newOrder)
      
      await tradingStore.createOrder({
        symbol: 'SHFE.cu2401',
        side: 'buy',
        order_type: 'limit',
        quantity: 1,
        price: 70000
      })

      expect(tradingStore.orders).toContainEqual(newOrder)

      // 2. 模拟订单成交
      const filledOrder = { ...newOrder, status: 'filled' }
      mockTradingApi.getOrders.mockResolvedValue([filledOrder])

      await tradingStore.fetchOrders()

      const order = tradingStore.orders.find(o => o.id === '1')
      expect(order?.status).toBe('filled')

      // 3. 检查持仓
      const newPosition = {
        symbol: 'SHFE.cu2401',
        quantity: 1,
        avg_price: 70000,
        current_price: 70000,
        unrealized_pnl: 0
      }

      mockTradingApi.getPositions.mockResolvedValue([newPosition])

      await tradingStore.fetchPositions()

      expect(tradingStore.positions).toContainEqual(newPosition)

      // 4. 平仓
      mockTradingApi.closePosition.mockResolvedValue({ order_id: 'close_1' })

      await tradingStore.closePosition('SHFE.cu2401', { quantity: 1 })

      expect(mockTradingApi.closePosition).toHaveBeenCalledWith('SHFE.cu2401', {
        quantity: 1
      })
    })

    it('应该处理风险控制', async () => {
      const tradingStore = useTradingStore()

      // 模拟风险控制拒绝
      mockTradingApi.createOrder.mockRejectedValue({
        response: { data: { detail: '超过最大持仓限制' } }
      })

      try {
        await tradingStore.createOrder({
          symbol: 'SHFE.cu2401',
          side: 'buy',
          order_type: 'limit',
          quantity: 100, // 大量订单
          price: 70000
        })
      } catch (error: any) {
        expect(error.response.data.detail).toBe('超过最大持仓限制')
      }

      // 订单不应该被添加到store
      expect(tradingStore.orders).toHaveLength(0)
    })

    it('应该实时更新价格和盈亏', async () => {
      const tradingStore = useTradingStore()

      // 初始持仓
      const position = {
        symbol: 'SHFE.cu2401',
        quantity: 1,
        avg_price: 70000,
        current_price: 70000,
        unrealized_pnl: 0
      }

      tradingStore.positions = [position]

      // 模拟价格更新
      tradingStore.updatePrice('SHFE.cu2401', 70500)

      const updatedPosition = tradingStore.positions.find(p => p.symbol === 'SHFE.cu2401')
      expect(updatedPosition?.current_price).toBe(70500)
      expect(updatedPosition?.unrealized_pnl).toBe(500) // (70500 - 70000) * 1
    })
  })
})