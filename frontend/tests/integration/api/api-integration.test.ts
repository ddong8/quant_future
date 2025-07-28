/**
 * API调用和状态管理集成测试
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'
import { useStrategyStore } from '@/stores/strategy'
import { useBacktestStore } from '@/stores/backtest'
import { useTradingStore } from '@/stores/trading'
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

describe('API调用和状态管理集成测试', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('认证状态管理', () => {
    it('应该正确处理登录流程', async () => {
      const authStore = useAuthStore()

      const loginResponse = {
        access_token: 'test-token',
        refresh_token: 'refresh-token',
        user: {
          id: '1',
          username: 'testuser',
          email: 'test@example.com'
        }
      }

      mockAuthApi.login.mockResolvedValue(loginResponse)

      // 执行登录
      await authStore.login({
        username: 'testuser',
        password: 'password123'
      })

      // 验证API调用
      expect(mockAuthApi.login).toHaveBeenCalledWith({
        username: 'testuser',
        password: 'password123'
      })

      // 验证状态更新
      expect(authStore.isAuthenticated).toBe(true)
      expect(authStore.user).toEqual(loginResponse.user)
      expect(authStore.token).toBe(loginResponse.access_token)

      // 验证localStorage
      expect(localStorage.setItem).toHaveBeenCalledWith('token', loginResponse.access_token)
      expect(localStorage.setItem).toHaveBeenCalledWith('refreshToken', loginResponse.refresh_token)
    })

    it('应该正确处理登录失败', async () => {
      const authStore = useAuthStore()

      const loginError = {
        response: {
          status: 401,
          data: { detail: '用户名或密码错误' }
        }
      }

      mockAuthApi.login.mockRejectedValue(loginError)

      // 执行登录
      try {
        await authStore.login({
          username: 'wronguser',
          password: 'wrongpass'
        })
      } catch (error) {
        expect(error).toEqual(loginError)
      }

      // 验证状态未改变
      expect(authStore.isAuthenticated).toBe(false)
      expect(authStore.user).toBeNull()
      expect(authStore.token).toBeNull()
    })

    it('应该正确处理token刷新', async () => {
      const authStore = useAuthStore()

      // 设置初始状态
      authStore.setToken('old-token')
      authStore.setRefreshToken('refresh-token')

      const refreshResponse = {
        access_token: 'new-token'
      }

      mockAuthApi.refreshToken.mockResolvedValue(refreshResponse)

      // 执行token刷新
      await authStore.refreshToken()

      // 验证API调用
      expect(mockAuthApi.refreshToken).toHaveBeenCalledWith('refresh-token')

      // 验证状态更新
      expect(authStore.token).toBe('new-token')
    })

    it('应该正确处理登出', async () => {
      const authStore = useAuthStore()

      // 设置初始状态
      authStore.setUser({
        id: '1',
        username: 'testuser',
        email: 'test@example.com'
      })
      authStore.setToken('test-token')

      mockAuthApi.logout.mockResolvedValue({})

      // 执行登出
      await authStore.logout()

      // 验证API调用
      expect(mockAuthApi.logout).toHaveBeenCalled()

      // 验证状态清除
      expect(authStore.isAuthenticated).toBe(false)
      expect(authStore.user).toBeNull()
      expect(authStore.token).toBeNull()

      // 验证localStorage清除
      expect(localStorage.removeItem).toHaveBeenCalledWith('token')
      expect(localStorage.removeItem).toHaveBeenCalledWith('refreshToken')
    })
  })

  describe('策略状态管理', () => {
    it('应该正确加载策略列表', async () => {
      const strategyStore = useStrategyStore()

      const strategies = [
        {
          id: '1',
          name: '策略1',
          description: '描述1',
          status: 'draft'
        },
        {
          id: '2',
          name: '策略2',
          description: '描述2',
          status: 'active'
        }
      ]

      mockStrategyApi.getStrategies.mockResolvedValue(strategies)

      // 加载策略
      await strategyStore.fetchStrategies()

      // 验证API调用
      expect(mockStrategyApi.getStrategies).toHaveBeenCalled()

      // 验证状态更新
      expect(strategyStore.strategies).toEqual(strategies)
      expect(strategyStore.loading).toBe(false)
    })

    it('应该正确创建策略', async () => {
      const strategyStore = useStrategyStore()

      const newStrategy = {
        id: '1',
        name: '新策略',
        description: '新策略描述',
        code: 'def initialize(context): pass',
        status: 'draft'
      }

      mockStrategyApi.createStrategy.mockResolvedValue(newStrategy)

      // 创建策略
      await strategyStore.createStrategy({
        name: newStrategy.name,
        description: newStrategy.description,
        code: newStrategy.code
      })

      // 验证API调用
      expect(mockStrategyApi.createStrategy).toHaveBeenCalledWith({
        name: newStrategy.name,
        description: newStrategy.description,
        code: newStrategy.code
      })

      // 验证状态更新
      expect(strategyStore.strategies).toContainEqual(newStrategy)
    })

    it('应该正确更新策略', async () => {
      const strategyStore = useStrategyStore()

      // 设置初始状态
      const originalStrategy = {
        id: '1',
        name: '原始策略',
        description: '原始描述',
        code: 'def initialize(context): pass',
        status: 'draft'
      }

      strategyStore.strategies = [originalStrategy]

      const updatedStrategy = {
        ...originalStrategy,
        name: '更新后的策略',
        description: '更新后的描述'
      }

      mockStrategyApi.updateStrategy.mockResolvedValue(updatedStrategy)

      // 更新策略
      await strategyStore.updateStrategy('1', {
        name: updatedStrategy.name,
        description: updatedStrategy.description
      })

      // 验证API调用
      expect(mockStrategyApi.updateStrategy).toHaveBeenCalledWith('1', {
        name: updatedStrategy.name,
        description: updatedStrategy.description
      })

      // 验证状态更新
      const strategy = strategyStore.strategies.find(s => s.id === '1')
      expect(strategy?.name).toBe(updatedStrategy.name)
      expect(strategy?.description).toBe(updatedStrategy.description)
    })

    it('应该正确删除策略', async () => {
      const strategyStore = useStrategyStore()

      // 设置初始状态
      strategyStore.strategies = [
        { id: '1', name: '策略1', description: '描述1', status: 'draft' },
        { id: '2', name: '策略2', description: '描述2', status: 'draft' }
      ]

      mockStrategyApi.deleteStrategy.mockResolvedValue({})

      // 删除策略
      await strategyStore.deleteStrategy('1')

      // 验证API调用
      expect(mockStrategyApi.deleteStrategy).toHaveBeenCalledWith('1')

      // 验证状态更新
      expect(strategyStore.strategies).toHaveLength(1)
      expect(strategyStore.strategies.find(s => s.id === '1')).toBeUndefined()
    })

    it('应该正确处理策略部署', async () => {
      const strategyStore = useStrategyStore()

      // 设置初始状态
      const strategy = {
        id: '1',
        name: '测试策略',
        description: '测试描述',
        status: 'draft'
      }

      strategyStore.strategies = [strategy]

      const deployedStrategy = { ...strategy, status: 'active' }
      mockStrategyApi.deployStrategy.mockResolvedValue(deployedStrategy)

      // 部署策略
      await strategyStore.deployStrategy('1')

      // 验证API调用
      expect(mockStrategyApi.deployStrategy).toHaveBeenCalledWith('1')

      // 验证状态更新
      const updatedStrategy = strategyStore.strategies.find(s => s.id === '1')
      expect(updatedStrategy?.status).toBe('active')
    })
  })

  describe('回测状态管理', () => {
    it('应该正确创建和启动回测', async () => {
      const backtestStore = useBacktestStore()

      const newBacktest = {
        id: '1',
        name: '测试回测',
        strategy_id: '1',
        start_date: '2023-01-01',
        end_date: '2023-12-31',
        initial_capital: 100000,
        status: 'pending'
      }

      mockBacktestApi.createBacktest.mockResolvedValue(newBacktest)

      // 创建回测
      await backtestStore.createBacktest({
        name: newBacktest.name,
        strategy_id: newBacktest.strategy_id,
        start_date: newBacktest.start_date,
        end_date: newBacktest.end_date,
        initial_capital: newBacktest.initial_capital
      })

      // 验证API调用
      expect(mockBacktestApi.createBacktest).toHaveBeenCalled()

      // 验证状态更新
      expect(backtestStore.backtests).toContainEqual(newBacktest)

      // 启动回测
      const runningBacktest = { ...newBacktest, status: 'running' }
      mockBacktestApi.startBacktest.mockResolvedValue(runningBacktest)

      await backtestStore.startBacktest('1')

      // 验证API调用
      expect(mockBacktestApi.startBacktest).toHaveBeenCalledWith('1')

      // 验证状态更新
      const backtest = backtestStore.backtests.find(b => b.id === '1')
      expect(backtest?.status).toBe('running')
    })

    it('应该正确获取回测结果', async () => {
      const backtestStore = useBacktestStore()

      const backtestResults = {
        performance_metrics: {
          total_return: 0.15,
          sharpe_ratio: 1.2,
          max_drawdown: -0.08,
          win_rate: 0.65
        },
        equity_curve: [
          { date: '2023-01-01', value: 100000 },
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
      }

      mockBacktestApi.getBacktestResults.mockResolvedValue(backtestResults)

      // 获取回测结果
      await backtestStore.fetchBacktestResults('1')

      // 验证API调用
      expect(mockBacktestApi.getBacktestResults).toHaveBeenCalledWith('1')

      // 验证状态更新
      expect(backtestStore.results['1']).toEqual(backtestResults)
    })

    it('应该正确比较多个回测', async () => {
      const backtestStore = useBacktestStore()

      const comparisonResult = {
        comparison_metrics: [
          {
            backtest_id: '1',
            strategy_name: '策略1',
            total_return: 0.15,
            sharpe_ratio: 1.2
          },
          {
            backtest_id: '2',
            strategy_name: '策略2',
            total_return: 0.12,
            sharpe_ratio: 1.0
          }
        ],
        performance_chart: {}
      }

      mockBacktestApi.compareBacktests.mockResolvedValue(comparisonResult)

      // 比较回测
      await backtestStore.compareBacktests(['1', '2'])

      // 验证API调用
      expect(mockBacktestApi.compareBacktests).toHaveBeenCalledWith({
        backtest_ids: ['1', '2']
      })

      // 验证状态更新
      expect(backtestStore.comparison).toEqual(comparisonResult)
    })
  })

  describe('交易状态管理', () => {
    it('应该正确管理订单状态', async () => {
      const tradingStore = useTradingStore()

      // 创建订单
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

      // 验证状态更新
      expect(tradingStore.orders).toContainEqual(newOrder)

      // 取消订单
      const cancelledOrder = { ...newOrder, status: 'cancelled' }
      mockTradingApi.cancelOrder.mockResolvedValue(cancelledOrder)

      await tradingStore.cancelOrder('1')

      // 验证状态更新
      const order = tradingStore.orders.find(o => o.id === '1')
      expect(order?.status).toBe('cancelled')
    })

    it('应该正确管理持仓状态', async () => {
      const tradingStore = useTradingStore()

      const positions = [
        {
          symbol: 'SHFE.cu2401',
          quantity: 1,
          avg_price: 70000,
          current_price: 70500,
          unrealized_pnl: 500
        }
      ]

      mockTradingApi.getPositions.mockResolvedValue(positions)

      // 获取持仓
      await tradingStore.fetchPositions()

      // 验证状态更新
      expect(tradingStore.positions).toEqual(positions)

      // 更新价格
      tradingStore.updatePrice('SHFE.cu2401', 71000)

      // 验证价格和盈亏更新
      const position = tradingStore.positions.find(p => p.symbol === 'SHFE.cu2401')
      expect(position?.current_price).toBe(71000)
      expect(position?.unrealized_pnl).toBe(1000) // (71000 - 70000) * 1
    })

    it('应该正确管理账户信息', async () => {
      const tradingStore = useTradingStore()

      const accountInfo = {
        balance: 100000,
        available: 80000,
        margin_used: 20000,
        unrealized_pnl: 1500
      }

      mockTradingApi.getAccountInfo.mockResolvedValue(accountInfo)

      // 获取账户信息
      await tradingStore.fetchAccountInfo()

      // 验证状态更新
      expect(tradingStore.account).toEqual(accountInfo)
    })
  })

  describe('跨store状态同步', () => {
    it('应该在策略部署时同步相关状态', async () => {
      const strategyStore = useStrategyStore()
      const tradingStore = useTradingStore()

      // 设置初始状态
      const strategy = {
        id: '1',
        name: '测试策略',
        description: '测试描述',
        status: 'draft'
      }

      strategyStore.strategies = [strategy]

      // 部署策略
      const deployedStrategy = { ...strategy, status: 'active' }
      mockStrategyApi.deployStrategy.mockResolvedValue(deployedStrategy)

      await strategyStore.deployStrategy('1')

      // 验证策略状态更新
      const updatedStrategy = strategyStore.strategies.find(s => s.id === '1')
      expect(updatedStrategy?.status).toBe('active')

      // 模拟交易store监听策略状态变化
      tradingStore.activeStrategies = strategyStore.strategies.filter(s => s.status === 'active')

      expect(tradingStore.activeStrategies).toHaveLength(1)
      expect(tradingStore.activeStrategies[0].id).toBe('1')
    })

    it('应该在用户登出时清除所有状态', async () => {
      const authStore = useAuthStore()
      const strategyStore = useStrategyStore()
      const backtestStore = useBacktestStore()
      const tradingStore = useTradingStore()

      // 设置初始状态
      authStore.setUser({ id: '1', username: 'test', email: 'test@example.com' })
      strategyStore.strategies = [{ id: '1', name: '策略1', description: '描述1', status: 'draft' }]
      backtestStore.backtests = [{ id: '1', name: '回测1', strategy_id: '1', status: 'completed' }]
      tradingStore.orders = [{ id: '1', symbol: 'SHFE.cu2401', side: 'buy', status: 'pending' }]

      mockAuthApi.logout.mockResolvedValue({})

      // 执行登出
      await authStore.logout()

      // 验证所有状态被清除
      expect(authStore.user).toBeNull()
      
      // 模拟其他store监听认证状态变化并清除状态
      strategyStore.$reset()
      backtestStore.$reset()
      tradingStore.$reset()

      expect(strategyStore.strategies).toHaveLength(0)
      expect(backtestStore.backtests).toHaveLength(0)
      expect(tradingStore.orders).toHaveLength(0)
    })
  })

  describe('错误处理和重试机制', () => {
    it('应该正确处理API错误', async () => {
      const strategyStore = useStrategyStore()

      const apiError = {
        response: {
          status: 500,
          data: { detail: '服务器内部错误' }
        }
      }

      mockStrategyApi.getStrategies.mockRejectedValue(apiError)

      // 尝试加载策略
      try {
        await strategyStore.fetchStrategies()
      } catch (error) {
        expect(error).toEqual(apiError)
      }

      // 验证错误状态
      expect(strategyStore.error).toBeTruthy()
      expect(strategyStore.loading).toBe(false)
    })

    it('应该支持请求重试', async () => {
      const strategyStore = useStrategyStore()

      // 第一次请求失败
      mockStrategyApi.getStrategies
        .mockRejectedValueOnce(new Error('Network Error'))
        .mockResolvedValueOnce([])

      // 第一次尝试
      try {
        await strategyStore.fetchStrategies()
      } catch (error) {
        expect(error.message).toBe('Network Error')
      }

      // 重试
      await strategyStore.fetchStrategies()

      // 验证重试成功
      expect(mockStrategyApi.getStrategies).toHaveBeenCalledTimes(2)
      expect(strategyStore.strategies).toEqual([])
      expect(strategyStore.error).toBeNull()
    })

    it('应该正确处理认证过期', async () => {
      const authStore = useAuthStore()
      const strategyStore = useStrategyStore()

      // 设置初始认证状态
      authStore.setToken('expired-token')

      // 模拟API返回401错误
      const authError = {
        response: { status: 401, data: { detail: 'Token expired' } }
      }

      mockStrategyApi.getStrategies.mockRejectedValue(authError)

      // 尝试获取策略
      try {
        await strategyStore.fetchStrategies()
      } catch (error) {
        expect(error.response.status).toBe(401)
      }

      // 模拟自动登出
      authStore.logout()

      // 验证认证状态被清除
      expect(authStore.isAuthenticated).toBe(false)
      expect(authStore.token).toBeNull()
    })
  })
})