/**
 * 策略组件集成测试
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import StrategiesView from '@/views/strategies/StrategiesView.vue'
import StrategyEditorView from '@/views/strategies/StrategyEditorView.vue'
import CreateStrategyDialog from '@/components/CreateStrategyDialog.vue'
import StrategyCard from '@/components/StrategyCard.vue'
import { useStrategyStore } from '@/stores/strategy'
import * as strategyApi from '@/api/strategy'

// Mock API
vi.mock('@/api/strategy')
vi.mock('@/components/CodeEditor.vue', () => ({
  default: {
    name: 'CodeEditor',
    template: '<div class="code-editor"><textarea v-model="modelValue" /></div>',
    props: ['modelValue'],
    emits: ['update:modelValue']
  }
}))

const mockStrategyApi = strategyApi as any

// 测试数据
const mockStrategies = [
  {
    id: '1',
    name: '测试策略1',
    description: '这是一个测试策略',
    status: 'draft',
    created_at: '2023-01-01T00:00:00Z',
    updated_at: '2023-01-01T00:00:00Z'
  },
  {
    id: '2',
    name: '测试策略2',
    description: '这是另一个测试策略',
    status: 'active',
    created_at: '2023-01-02T00:00:00Z',
    updated_at: '2023-01-02T00:00:00Z'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/strategies', component: StrategiesView },
    { path: '/strategies/:id/edit', component: StrategyEditorView }
  ]
})

describe('策略组件集成测试', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('StrategiesView', () => {
    it('应该正确加载和显示策略列表', async () => {
      mockStrategyApi.getStrategies.mockResolvedValue(mockStrategies)

      const wrapper = mount(StrategiesView, {
        global: {
          plugins: [router]
        }
      })

      // 等待数据加载
      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 100))

      expect(mockStrategyApi.getStrategies).toHaveBeenCalled()
      expect(wrapper.findAllComponents(StrategyCard)).toHaveLength(2)
    })

    it('应该处理加载错误', async () => {
      mockStrategyApi.getStrategies.mockRejectedValue(new Error('网络错误'))

      const wrapper = mount(StrategiesView, {
        global: {
          plugins: [router]
        }
      })

      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 100))

      expect(wrapper.text()).toContain('加载失败')
    })

    it('应该支持策略搜索', async () => {
      mockStrategyApi.getStrategies.mockResolvedValue(mockStrategies)

      const wrapper = mount(StrategiesView, {
        global: {
          plugins: [router]
        }
      })

      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 100))

      // 搜索策略
      const searchInput = wrapper.find('input[placeholder*="搜索"]')
      await searchInput.setValue('测试策略1')
      await searchInput.trigger('input')

      // 应该只显示匹配的策略
      const strategyCards = wrapper.findAllComponents(StrategyCard)
      expect(strategyCards).toHaveLength(1)
      expect(strategyCards[0].props('strategy').name).toBe('测试策略1')
    })

    it('应该支持按状态过滤', async () => {
      mockStrategyApi.getStrategies.mockResolvedValue(mockStrategies)

      const wrapper = mount(StrategiesView, {
        global: {
          plugins: [router]
        }
      })

      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 100))

      // 选择状态过滤
      const statusFilter = wrapper.find('select')
      await statusFilter.setValue('active')

      // 应该只显示活跃策略
      const strategyCards = wrapper.findAllComponents(StrategyCard)
      expect(strategyCards).toHaveLength(1)
      expect(strategyCards[0].props('strategy').status).toBe('active')
    })

    it('应该打开创建策略对话框', async () => {
      mockStrategyApi.getStrategies.mockResolvedValue([])

      const wrapper = mount(StrategiesView, {
        global: {
          plugins: [router]
        }
      })

      // 点击创建按钮
      const createButton = wrapper.find('button[data-test="create-strategy"]')
      await createButton.trigger('click')

      // 应该显示创建对话框
      expect(wrapper.findComponent(CreateStrategyDialog).exists()).toBe(true)
    })
  })

  describe('StrategyCard', () => {
    it('应该正确显示策略信息', () => {
      const strategy = mockStrategies[0]
      const wrapper = mount(StrategyCard, {
        props: { strategy },
        global: {
          plugins: [router]
        }
      })

      expect(wrapper.text()).toContain(strategy.name)
      expect(wrapper.text()).toContain(strategy.description)
      expect(wrapper.text()).toContain('草稿') // draft状态的中文显示
    })

    it('应该处理策略删除', async () => {
      mockStrategyApi.deleteStrategy.mockResolvedValue({})

      const strategy = mockStrategies[0]
      const wrapper = mount(StrategyCard, {
        props: { strategy },
        global: {
          plugins: [router]
        }
      })

      // 点击删除按钮
      const deleteButton = wrapper.find('button[data-test="delete-strategy"]')
      await deleteButton.trigger('click')

      // 确认删除
      const confirmButton = wrapper.find('button[data-test="confirm-delete"]')
      await confirmButton.trigger('click')

      expect(mockStrategyApi.deleteStrategy).toHaveBeenCalledWith(strategy.id)
      expect(wrapper.emitted('deleted')).toBeTruthy()
    })

    it('应该处理策略部署', async () => {
      mockStrategyApi.deployStrategy.mockResolvedValue({ status: 'active' })

      const strategy = mockStrategies[0]
      const wrapper = mount(StrategyCard, {
        props: { strategy },
        global: {
          plugins: [router]
        }
      })

      // 点击部署按钮
      const deployButton = wrapper.find('button[data-test="deploy-strategy"]')
      await deployButton.trigger('click')

      expect(mockStrategyApi.deployStrategy).toHaveBeenCalledWith(strategy.id)
      expect(wrapper.emitted('deployed')).toBeTruthy()
    })
  })

  describe('CreateStrategyDialog', () => {
    it('应该正确渲染创建表单', () => {
      const wrapper = mount(CreateStrategyDialog, {
        props: { visible: true },
        global: {
          plugins: [router]
        }
      })

      expect(wrapper.find('input[name="name"]').exists()).toBe(true)
      expect(wrapper.find('textarea[name="description"]').exists()).toBe(true)
      expect(wrapper.find('.code-editor').exists()).toBe(true)
    })

    it('应该验证必填字段', async () => {
      const wrapper = mount(CreateStrategyDialog, {
        props: { visible: true },
        global: {
          plugins: [router]
        }
      })

      // 提交空表单
      const submitButton = wrapper.find('button[type="submit"]')
      await submitButton.trigger('click')

      expect(wrapper.text()).toContain('策略名称不能为空')
      expect(wrapper.text()).toContain('策略代码不能为空')
    })

    it('应该创建新策略', async () => {
      const newStrategy = {
        id: '3',
        name: '新策略',
        description: '新创建的策略',
        code: 'def initialize(context): pass',
        status: 'draft'
      }

      mockStrategyApi.createStrategy.mockResolvedValue(newStrategy)

      const wrapper = mount(CreateStrategyDialog, {
        props: { visible: true },
        global: {
          plugins: [router]
        }
      })

      // 填写表单
      await wrapper.find('input[name="name"]').setValue(newStrategy.name)
      await wrapper.find('textarea[name="description"]').setValue(newStrategy.description)
      
      // 模拟代码编辑器输入
      const codeEditor = wrapper.find('.code-editor textarea')
      await codeEditor.setValue(newStrategy.code)

      // 提交表单
      const submitButton = wrapper.find('button[type="submit"]')
      await submitButton.trigger('click')

      expect(mockStrategyApi.createStrategy).toHaveBeenCalledWith({
        name: newStrategy.name,
        description: newStrategy.description,
        code: newStrategy.code
      })

      expect(wrapper.emitted('created')).toBeTruthy()
    })

    it('应该处理创建失败', async () => {
      mockStrategyApi.createStrategy.mockRejectedValue({
        response: { data: { detail: '策略名称已存在' } }
      })

      const wrapper = mount(CreateStrategyDialog, {
        props: { visible: true },
        global: {
          plugins: [router]
        }
      })

      // 填写表单
      await wrapper.find('input[name="name"]').setValue('重复名称')
      await wrapper.find('textarea[name="description"]').setValue('描述')
      
      const codeEditor = wrapper.find('.code-editor textarea')
      await codeEditor.setValue('def initialize(context): pass')

      // 提交表单
      const submitButton = wrapper.find('button[type="submit"]')
      await submitButton.trigger('click')

      await wrapper.vm.$nextTick()

      expect(wrapper.text()).toContain('策略名称已存在')
    })
  })

  describe('StrategyEditorView', () => {
    it('应该加载并显示策略详情', async () => {
      const strategy = {
        id: '1',
        name: '编辑策略',
        description: '正在编辑的策略',
        code: 'def initialize(context):\n    pass\n\ndef handle_bar(context, bar_dict):\n    pass',
        status: 'draft'
      }

      mockStrategyApi.getStrategy.mockResolvedValue(strategy)

      const wrapper = mount(StrategyEditorView, {
        global: {
          plugins: [router]
        }
      })

      // 模拟路由参数
      wrapper.vm.$route.params.id = '1'

      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 100))

      expect(mockStrategyApi.getStrategy).toHaveBeenCalledWith('1')
      expect(wrapper.find('input[name="name"]').element.value).toBe(strategy.name)
      expect(wrapper.find('textarea[name="description"]').element.value).toBe(strategy.description)
    })

    it('应该保存策略修改', async () => {
      const strategy = {
        id: '1',
        name: '原始策略',
        description: '原始描述',
        code: 'def initialize(context): pass',
        status: 'draft'
      }

      const updatedStrategy = {
        ...strategy,
        name: '修改后的策略',
        description: '修改后的描述'
      }

      mockStrategyApi.getStrategy.mockResolvedValue(strategy)
      mockStrategyApi.updateStrategy.mockResolvedValue(updatedStrategy)

      const wrapper = mount(StrategyEditorView, {
        global: {
          plugins: [router]
        }
      })

      wrapper.vm.$route.params.id = '1'

      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 100))

      // 修改策略信息
      await wrapper.find('input[name="name"]').setValue(updatedStrategy.name)
      await wrapper.find('textarea[name="description"]').setValue(updatedStrategy.description)

      // 保存修改
      const saveButton = wrapper.find('button[data-test="save-strategy"]')
      await saveButton.trigger('click')

      expect(mockStrategyApi.updateStrategy).toHaveBeenCalledWith('1', {
        name: updatedStrategy.name,
        description: updatedStrategy.description,
        code: strategy.code
      })
    })

    it('应该验证策略代码', async () => {
      const strategy = {
        id: '1',
        name: '测试策略',
        description: '测试描述',
        code: 'def initialize(context): pass',
        status: 'draft'
      }

      mockStrategyApi.getStrategy.mockResolvedValue(strategy)
      mockStrategyApi.validateStrategy.mockResolvedValue({
        valid: true,
        errors: []
      })

      const wrapper = mount(StrategyEditorView, {
        global: {
          plugins: [router]
        }
      })

      wrapper.vm.$route.params.id = '1'

      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 100))

      // 点击验证按钮
      const validateButton = wrapper.find('button[data-test="validate-strategy"]')
      await validateButton.trigger('click')

      expect(mockStrategyApi.validateStrategy).toHaveBeenCalledWith({
        code: strategy.code
      })

      expect(wrapper.text()).toContain('代码验证通过')
    })

    it('应该处理代码验证错误', async () => {
      const strategy = {
        id: '1',
        name: '测试策略',
        description: '测试描述',
        code: 'invalid python code',
        status: 'draft'
      }

      mockStrategyApi.getStrategy.mockResolvedValue(strategy)
      mockStrategyApi.validateStrategy.mockResolvedValue({
        valid: false,
        errors: ['语法错误：第1行']
      })

      const wrapper = mount(StrategyEditorView, {
        global: {
          plugins: [router]
        }
      })

      wrapper.vm.$route.params.id = '1'

      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 100))

      // 点击验证按钮
      const validateButton = wrapper.find('button[data-test="validate-strategy"]')
      await validateButton.trigger('click')

      await wrapper.vm.$nextTick()

      expect(wrapper.text()).toContain('语法错误：第1行')
    })
  })

  describe('策略管理集成流程', () => {
    it('应该完成完整的策略创建-编辑-部署流程', async () => {
      const strategyStore = useStrategyStore()

      // 1. 创建策略
      const newStrategy = {
        id: '1',
        name: '集成测试策略',
        description: '用于集成测试的策略',
        code: 'def initialize(context): pass',
        status: 'draft'
      }

      mockStrategyApi.createStrategy.mockResolvedValue(newStrategy)
      
      await strategyStore.createStrategy({
        name: newStrategy.name,
        description: newStrategy.description,
        code: newStrategy.code
      })

      expect(strategyStore.strategies).toContainEqual(newStrategy)

      // 2. 编辑策略
      const updatedStrategy = {
        ...newStrategy,
        description: '更新后的描述',
        code: 'def initialize(context):\n    context.symbol = "SHFE.cu2401"'
      }

      mockStrategyApi.updateStrategy.mockResolvedValue(updatedStrategy)

      await strategyStore.updateStrategy(newStrategy.id, {
        description: updatedStrategy.description,
        code: updatedStrategy.code
      })

      const strategy = strategyStore.strategies.find(s => s.id === newStrategy.id)
      expect(strategy?.description).toBe(updatedStrategy.description)

      // 3. 部署策略
      const deployedStrategy = {
        ...updatedStrategy,
        status: 'active'
      }

      mockStrategyApi.deployStrategy.mockResolvedValue(deployedStrategy)

      await strategyStore.deployStrategy(newStrategy.id)

      const finalStrategy = strategyStore.strategies.find(s => s.id === newStrategy.id)
      expect(finalStrategy?.status).toBe('active')
    })
  })
})