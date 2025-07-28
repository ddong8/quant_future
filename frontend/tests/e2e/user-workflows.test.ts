/**
 * 用户工作流E2E测试
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import App from '@/App.vue'
import { routes } from '@/router'
import * as authApi from '@/api/auth'
import * as strategyApi from '@/api/strategy'
import * as backtestApi from '@/api/backtest'
import * as tradingApi from '@/api/trading'

// Mock所有API
vi.mock('@/api/auth')
vi.mock('@/api/strategy')
vi.mock('@/api/backtest')
vi.mock('@/api/trading')

const mockAuthApi = authApi as any
const mockStrategyApi = strategyApi as any
const mockBacktestApi = backtestApi as any
const mockTradingApi = tradingApi as any

// 创建完整的应用实例
const createApp = () => {
  const router = createRouter({
    history: createWebHistory(),
    routes
  })

  const wrapper = mount(App, {
    global: {
      plugins: [createPinia(), router]
    }
  })

  return { wrapper, router }
}

describe('用户工作流E2E测试', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('新用户注册和首次使用流程', () => {
    it('应该完成新用户注册到创建第一个策略的完整流程', async () => {
      const { wrapper, router } = createApp()

      // 1. 访问首页，应该重定向到登录页
      await router.push('/')
      await wrapper.vm.$nextTick()

      expect(router.currentRoute.value.path).toBe('/login')

      // 2. 点击注册链接
      const registerLink = wrapper.find('a[href="/register"]')
      await registerLink.trigger('click')
      await wrapper.vm.$nextTick()

      expect(router.currentRoute.value.path).toBe('/register')

      // 3. 填写注册表单
      mockAuthApi.register.mockResolvedValue({
        id: '1',
        username: 'newuser',
        email: 'new@example.com'
      })

      await wrapper.find('input[name="username"]').setValue('newuser')
      await wrapper.find('input[name="email"]').setValue('new@example.com')
      await wrapper.find('input[name="password"]').setValue('password123')
      await wrapper.find('input[name="confirmPassword"]').setValue('password123')

      await wrapper.find('form').trigger('submit')
      await wrapper.vm.$nextTick()

      expect(mockAuthApi.register).toHaveBeenCalled()

      // 4. 注册成功后自动跳转到登录页
      expect(router.currentRoute.value.path).toBe('/login')
      expect(wrapper.text()).toContain('注册成功')

      // 5. 登录
      mockAuthApi.login.mockResolvedValue({
        access_token: 'test-token',
        user: { id: '1', username: 'newuser', email: 'new@example.com' }
      })

      await wrapper.find('input[type="text"]').setValue('newuser')
      await wrapper.find('input[type="password"]').setValue('password123')

      await wrapper.find('form').trigger('submit')
      await wrapper.vm.$nextTick()

      // 6. 登录成功后跳转到仪表板
      expect(router.currentRoute.value.path).toBe('/dashboard')

      // 7. 导航到策略页面
      const strategiesLink = wrapper.find('a[href="/strategies"]')
      await strategiesLink.trigger('click')
      await wrapper.vm.$nextTick()

      expect(router.currentRoute.value.path).toBe('/strategies')

      // 8. 创建第一个策略
      mockStrategyApi.getStrategies.mockResolvedValue([])

      const createButton = wrapper.find('button[data-test="create-strategy"]')
      await createButton.trigger('click')

      // 填写策略信息
      const newStrategy = {
        id: '1',
        name: '我的第一个策略',
        description: '这是我创建的第一个量化交易策略',
        code: 'def initialize(context):\n    context.symbol = "SHFE.cu2401"\n\ndef handle_bar(context, bar_dict):\n    pass',
        status: 'draft'
      }

      mockStrategyApi.createStrategy.mockResolvedValue(newStrategy)

      await wrapper.find('input[name="name"]').setValue(newStrategy.name)
      await wrapper.find('textarea[name="description"]').setValue(newStrategy.description)
      await wrapper.find('.code-editor textarea').setValue(newStrategy.code)

      await wrapper.find('button[type="submit"]').trigger('click')
      await wrapper.vm.$nextTick()

      expect(mockStrategyApi.createStrategy).toHaveBeenCalled()
      expect(wrapper.text()).toContain('策略创建成功')
    })
  })

  describe('策略开发和回测流程', () => {
    it('应该完成策略开发-回测-分析的完整流程', async () => {
      const { wrapper, router } = createApp()

      // 模拟已登录状态
      mockAuthApi.getCurrentUser.mockResolvedValue({
        id: '1',
        username: 'developer',
        email: 'dev@example.com'
      })

      // 1. 直接访问策略页面
      await router.push('/strategies')
      await wrapper.vm.$nextTick()

      // 2. 加载现有策略
      const existingStrategy = {
        id: '1',
        name: '测试策略',
        description: '用于测试的策略',
        code: 'def initialize(context):\n    context.symbol = "SHFE.cu2401"\n\ndef handle_bar(context, bar_dict):\n    if context.portfolio.available_cash > 100000:\n        context.order_target_percent(context.symbol, 0.5)',
        status: 'draft'
      }

      mockStrategyApi.getStrategies.mockResolvedValue([existingStrategy])

      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 100))

      // 3. 编辑策略
      const editButton = wrapper.find('button[data-test="edit-strategy"]')
      await editButton.trigger('click')

      expect(router.currentRoute.value.path).toBe('/strategies/1/edit')

      // 4. 修改策略代码
      mockStrategyApi.getStrategy.mockResolvedValue(existingStrategy)

      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 100))

      const updatedCode = existingStrategy.code + '\n    # 添加风险控制\n    if context.portfolio.total_value < 90000:\n        context.close_all_positions()'

      await wrapper.find('.code-editor textarea').setValue(updatedCode)

      // 5. 验证策略代码
      mockStrategyApi.validateStrategy.mockResolvedValue({
        valid: true,
        errors: []
      })

      const validateButton = wrapper.find('button[data-test="validate-strategy"]')
      await validateButton.trigger('click')

      await wrapper.vm.$nextTick()

      expect(wrapper.text()).toContain('代码验证通过')

      // 6. 保存策略
      const updatedStrategy = { ...existingStrategy, code: updatedCode }
      mockStrategyApi.updateStrategy.mockResolvedValue(updatedStrategy)

      const saveButton = wrapper.find('button[data-test="save-strategy"]')
      await saveButton.trigger('click')

      await wrapper.vm.$nextTick()

      expect(mockStrategyApi.updateStrategy).toHaveBeenCalled()

      // 7. 创建回测
      const backtestButton = wrapper.find('button[data-test="create-backtest"]')
      await backtestButton.trigger('click')

      const newBacktest = {
        id: '1',
        name: '策略回测1',
        strategy_id: '1',
        start_date: '2023-01-01',
        end_date: '2023-12-31',
        initial_capital: 100000,
        status: 'pending'
      }

      mockBacktestApi.createBacktest.mockResolvedValue(newBacktest)

      // 填写回测配置
      await wrapper.find('input[name="backtest-name"]').setValue(newBacktest.name)
      await wrapper.find('input[name="start-date"]').setValue(newBacktest.start_date)
      await wrapper.find('input[name="end-date"]').setValue(newBacktest.end_date)
      await wrapper.find('input[name="initial-capital"]').setValue(newBacktest.initial_capital.toString())

      await wrapper.find('button[data-test="start-backtest"]').trigger('click')

      await wrapper.vm.$nextTick()

      expect(mockBacktestApi.createBacktest).toHaveBeenCalled()

      // 8. 启动回测
      mockBacktestApi.startBacktest.mockResolvedValue({ status: 'running' })

      const startButton = wrapper.find('button[data-test="confirm-start"]')
      await startButton.trigger('click')

      await wrapper.vm.$nextTick()

      expect(mockBacktestApi.startBacktest).toHaveBeenCalledWith('1')

      // 9. 模拟回测完成，查看结果
      const completedBacktest = {
        ...newBacktest,
        status: 'completed',
        total_return: 0.15,
        sharpe_ratio: 1.2,
        max_drawdown: -0.08
      }

      mockBacktestApi.getBacktest.mockResolvedValue(completedBacktest)
      mockBacktestApi.getBacktestResults.mockResolvedValue({
        performance_metrics: {
          total_return: 0.15,
          sharpe_ratio: 1.2,
          max_drawdown: -0.08,
          win_rate: 0.65
        },
        equity_curve: [
          { date: '2023-01-01', value: 100000 },
          { date: '2023-06-01', value: 110000 },
          { date: '2023-12-31', value: 115000 }
        ],
        trades: [
          {
            symbol: 'SHFE.cu2401',
            side: 'buy',
            quantity: 1,
            price: 70000,
            timestamp: '2023-01-15T09:00:00Z'
          }
        ]
      })

      // 导航到回测结果页面
      await router.push('/backtests/1/results')
      await wrapper.vm.$nextTick()

      expect(wrapper.text()).toContain('15.00%') // 总收益
      expect(wrapper.text()).toContain('1.20')   // 夏普比率
      expect(wrapper.text()).toContain('-8.00%') // 最大回撤
    })
  })

  describe('实盘交易流程', () => {
    it('应该完成策略部署到实盘交易的完整流程', async () => {
      const { wrapper, router } = createApp()

      // 模拟已登录状态
      mockAuthApi.getCurrentUser.mockResolvedValue({
        id: '1',
        username: 'trader',
        email: 'trader@example.com'
      })

      // 1. 访问策略页面
      await router.push('/strategies')
      await wrapper.vm.$nextTick()

      // 2. 加载已验证的策略
      const strategy = {
        id: '1',
        name: '实盘策略',
        description: '准备用于实盘交易的策略',
        code: 'def initialize(context):\n    context.symbol = "SHFE.cu2401"\n\ndef handle_bar(context, bar_dict):\n    # 实盘交易逻辑',
        status: 'draft'
      }

      mockStrategyApi.getStrategies.mockResolvedValue([strategy])

      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 100))

      // 3. 部署策略
      mockStrategyApi.deployStrategy.mockResolvedValue({
        ...strategy,
        status: 'active'
      })

      const deployButton = wrapper.find('button[data-test="deploy-strategy"]')
      await deployButton.trigger('click')

      // 确认部署
      const confirmButton = wrapper.find('button[data-test="confirm-deploy"]')
      await confirmButton.trigger('click')

      await wrapper.vm.$nextTick()

      expect(mockStrategyApi.deployStrategy).toHaveBeenCalledWith('1')
      expect(wrapper.text()).toContain('策略部署成功')

      // 4. 访问交易页面
      await router.push('/trading')
      await wrapper.vm.$nextTick()

      // 5. 查看账户信息
      mockTradingApi.getAccountInfo.mockResolvedValue({
        balance: 100000,
        available: 80000,
        margin_used: 20000,
        unrealized_pnl: 1500
      })

      mockTradingApi.getOrders.mockResolvedValue([])
      mockTradingApi.getPositions.mockResolvedValue([])

      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 100))

      expect(wrapper.text()).toContain('100,000') // 账户余额

      // 6. 手动下单
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

      // 填写交易表单
      await wrapper.find('select[name="symbol"]').setValue('SHFE.cu2401')
      await wrapper.find('select[name="side"]').setValue('buy')
      await wrapper.find('select[name="order_type"]').setValue('limit')
      await wrapper.find('input[name="quantity"]').setValue('1')
      await wrapper.find('input[name="price"]').setValue('70000')

      // 提交订单
      const submitButton = wrapper.find('button[type="submit"]')
      await submitButton.trigger('click')

      await wrapper.vm.$nextTick()

      expect(mockTradingApi.createOrder).toHaveBeenCalled()
      expect(wrapper.text()).toContain('订单提交成功')

      // 7. 监控订单状态
      const filledOrder = { ...newOrder, status: 'filled' }
      mockTradingApi.getOrders.mockResolvedValue([filledOrder])

      // 模拟订单成交
      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 100))

      expect(wrapper.text()).toContain('已成交')

      // 8. 查看持仓
      const position = {
        symbol: 'SHFE.cu2401',
        quantity: 1,
        avg_price: 70000,
        current_price: 70500,
        unrealized_pnl: 500
      }

      mockTradingApi.getPositions.mockResolvedValue([position])

      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 100))

      expect(wrapper.text()).toContain('SHFE.cu2401')
      expect(wrapper.text()).toContain('500') // 浮动盈亏

      // 9. 平仓
      mockTradingApi.closePosition.mockResolvedValue({ order_id: 'close_1' })

      const closeButton = wrapper.find('button[data-test="close-position"]')
      await closeButton.trigger('click')

      const confirmCloseButton = wrapper.find('button[data-test="confirm-close"]')
      await confirmCloseButton.trigger('click')

      await wrapper.vm.$nextTick()

      expect(mockTradingApi.closePosition).toHaveBeenCalledWith('SHFE.cu2401', {
        quantity: 1
      })
    })
  })

  describe('多策略管理流程', () => {
    it('应该完成多策略创建-比较-优化的完整流程', async () => {
      const { wrapper, router } = createApp()

      // 模拟已登录状态
      mockAuthApi.getCurrentUser.mockResolvedValue({
        id: '1',
        username: 'manager',
        email: 'manager@example.com'
      })

      // 1. 创建多个策略
      const strategies = [
        {
          id: '1',
          name: '趋势跟踪策略',
          description: '基于移动平均线的趋势跟踪',
          status: 'draft'
        },
        {
          id: '2',
          name: '均值回归策略',
          description: '基于价格均值回归的交易策略',
          status: 'draft'
        },
        {
          id: '3',
          name: '套利策略',
          description: '跨品种套利策略',
          status: 'draft'
        }
      ]

      mockStrategyApi.getStrategies.mockResolvedValue(strategies)

      await router.push('/strategies')
      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 100))

      expect(wrapper.findAll('[data-test="strategy-card"]')).toHaveLength(3)

      // 2. 为每个策略创建回测
      const backtests = strategies.map((strategy, index) => ({
        id: (index + 1).toString(),
        name: `${strategy.name}回测`,
        strategy_id: strategy.id,
        start_date: '2023-01-01',
        end_date: '2023-12-31',
        initial_capital: 100000,
        status: 'completed',
        total_return: 0.1 + index * 0.05, // 不同的收益率
        sharpe_ratio: 1.0 + index * 0.2,
        max_drawdown: -0.05 - index * 0.02
      }))

      mockBacktestApi.getBacktests.mockResolvedValue(backtests)

      // 3. 访问回测页面
      await router.push('/backtests')
      await wrapper.vm.$nextTick()

      // 4. 比较回测结果
      mockBacktestApi.compareBacktests.mockResolvedValue({
        comparison_metrics: backtests.map(bt => ({
          backtest_id: bt.id,
          strategy_name: strategies.find(s => s.id === bt.strategy_id)?.name,
          total_return: bt.total_return,
          sharpe_ratio: bt.sharpe_ratio,
          max_drawdown: bt.max_drawdown
        })),
        performance_chart: {
          // 图表数据
        }
      })

      const compareButton = wrapper.find('button[data-test="compare-backtests"]')
      await compareButton.trigger('click')

      // 选择要比较的回测
      const checkboxes = wrapper.findAll('input[type="checkbox"]')
      await checkboxes[0].setChecked(true)
      await checkboxes[1].setChecked(true)
      await checkboxes[2].setChecked(true)

      const confirmCompareButton = wrapper.find('button[data-test="confirm-compare"]')
      await confirmCompareButton.trigger('click')

      await wrapper.vm.$nextTick()

      expect(mockBacktestApi.compareBacktests).toHaveBeenCalled()
      expect(wrapper.text()).toContain('趋势跟踪策略')
      expect(wrapper.text()).toContain('均值回归策略')
      expect(wrapper.text()).toContain('套利策略')

      // 5. 选择最佳策略进行部署
      // 根据比较结果，选择夏普比率最高的策略
      const bestStrategy = strategies[2] // 套利策略

      mockStrategyApi.deployStrategy.mockResolvedValue({
        ...bestStrategy,
        status: 'active'
      })

      const deployBestButton = wrapper.find(`button[data-strategy-id="${bestStrategy.id}"][data-test="deploy-strategy"]`)
      await deployBestButton.trigger('click')

      const confirmDeployButton = wrapper.find('button[data-test="confirm-deploy"]')
      await confirmDeployButton.trigger('click')

      await wrapper.vm.$nextTick()

      expect(mockStrategyApi.deployStrategy).toHaveBeenCalledWith(bestStrategy.id)
      expect(wrapper.text()).toContain('策略部署成功')
    })
  })

  describe('错误处理和恢复流程', () => {
    it('应该正确处理网络错误和系统异常', async () => {
      const { wrapper, router } = createApp()

      // 1. 模拟网络错误
      mockAuthApi.login.mockRejectedValue(new Error('Network Error'))

      await router.push('/login')
      await wrapper.vm.$nextTick()

      // 尝试登录
      await wrapper.find('input[type="text"]').setValue('testuser')
      await wrapper.find('input[type="password"]').setValue('password123')
      await wrapper.find('form').trigger('submit')

      await wrapper.vm.$nextTick()

      expect(wrapper.text()).toContain('网络连接失败')

      // 2. 恢复网络连接，重试登录
      mockAuthApi.login.mockResolvedValue({
        access_token: 'test-token',
        user: { id: '1', username: 'testuser', email: 'test@example.com' }
      })

      const retryButton = wrapper.find('button[data-test="retry-login"]')
      await retryButton.trigger('click')

      await wrapper.vm.$nextTick()

      expect(router.currentRoute.value.path).toBe('/dashboard')

      // 3. 模拟API错误
      mockStrategyApi.getStrategies.mockRejectedValue({
        response: { status: 500, data: { detail: '服务器内部错误' } }
      })

      await router.push('/strategies')
      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 100))

      expect(wrapper.text()).toContain('服务器内部错误')

      // 4. 刷新页面恢复
      mockStrategyApi.getStrategies.mockResolvedValue([])

      const refreshButton = wrapper.find('button[data-test="refresh-page"]')
      await refreshButton.trigger('click')

      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 100))

      expect(wrapper.text()).toContain('暂无策略')
    })
  })
})