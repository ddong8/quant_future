/**
 * 认证组件集成测试
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '@/views/auth/LoginView.vue'
import RegisterView from '@/views/auth/RegisterView.vue'
import { useAuthStore } from '@/stores/auth'
import * as authApi from '@/api/auth'

// Mock API
vi.mock('@/api/auth')

const mockAuthApi = authApi as any

// 创建测试路由
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: LoginView },
    { path: '/register', component: RegisterView },
    { path: '/dashboard', component: { template: '<div>Dashboard</div>' } }
  ]
})

describe('认证组件集成测试', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('LoginView', () => {
    it('应该正确渲染登录表单', () => {
      const wrapper = mount(LoginView, {
        global: {
          plugins: [router]
        }
      })

      expect(wrapper.find('form').exists()).toBe(true)
      expect(wrapper.find('input[type="text"]').exists()).toBe(true)
      expect(wrapper.find('input[type="password"]').exists()).toBe(true)
      expect(wrapper.find('button[type="submit"]').exists()).toBe(true)
    })

    it('应该验证必填字段', async () => {
      const wrapper = mount(LoginView, {
        global: {
          plugins: [router]
        }
      })

      // 提交空表单
      await wrapper.find('form').trigger('submit')

      // 应该显示验证错误
      expect(wrapper.text()).toContain('用户名不能为空')
      expect(wrapper.text()).toContain('密码不能为空')
    })

    it('应该处理成功登录', async () => {
      mockAuthApi.login.mockResolvedValue({
        access_token: 'test-token',
        user: { id: '1', username: 'testuser', email: 'test@example.com' }
      })

      const wrapper = mount(LoginView, {
        global: {
          plugins: [router]
        }
      })

      const authStore = useAuthStore()

      // 填写表单
      await wrapper.find('input[type="text"]').setValue('testuser')
      await wrapper.find('input[type="password"]').setValue('password123')

      // 提交表单
      await wrapper.find('form').trigger('submit')
      await wrapper.vm.$nextTick()

      // 验证API调用
      expect(mockAuthApi.login).toHaveBeenCalledWith({
        username: 'testuser',
        password: 'password123'
      })

      // 验证store状态
      expect(authStore.isAuthenticated).toBe(true)
      expect(authStore.user?.username).toBe('testuser')
    })

    it('应该处理登录失败', async () => {
      mockAuthApi.login.mockRejectedValue({
        response: { data: { detail: '用户名或密码错误' } }
      })

      const wrapper = mount(LoginView, {
        global: {
          plugins: [router]
        }
      })

      // 填写表单
      await wrapper.find('input[type="text"]').setValue('wronguser')
      await wrapper.find('input[type="password"]').setValue('wrongpass')

      // 提交表单
      await wrapper.find('form').trigger('submit')
      await wrapper.vm.$nextTick()

      // 应该显示错误消息
      expect(wrapper.text()).toContain('用户名或密码错误')
    })

    it('应该显示加载状态', async () => {
      let resolveLogin: (value: any) => void
      mockAuthApi.login.mockReturnValue(
        new Promise(resolve => {
          resolveLogin = resolve
        })
      )

      const wrapper = mount(LoginView, {
        global: {
          plugins: [router]
        }
      })

      // 填写并提交表单
      await wrapper.find('input[type="text"]').setValue('testuser')
      await wrapper.find('input[type="password"]').setValue('password123')
      await wrapper.find('form').trigger('submit')

      // 应该显示加载状态
      expect(wrapper.find('button[type="submit"]').attributes('disabled')).toBeDefined()
      expect(wrapper.text()).toContain('登录中')

      // 完成登录
      resolveLogin!({
        access_token: 'test-token',
        user: { id: '1', username: 'testuser' }
      })
      await wrapper.vm.$nextTick()

      // 加载状态应该消失
      expect(wrapper.find('button[type="submit"]').attributes('disabled')).toBeUndefined()
    })
  })

  describe('RegisterView', () => {
    it('应该正确渲染注册表单', () => {
      const wrapper = mount(RegisterView, {
        global: {
          plugins: [router]
        }
      })

      expect(wrapper.find('form').exists()).toBe(true)
      expect(wrapper.find('input[name="username"]').exists()).toBe(true)
      expect(wrapper.find('input[name="email"]').exists()).toBe(true)
      expect(wrapper.find('input[name="password"]').exists()).toBe(true)
      expect(wrapper.find('input[name="confirmPassword"]').exists()).toBe(true)
    })

    it('应该验证密码确认', async () => {
      const wrapper = mount(RegisterView, {
        global: {
          plugins: [router]
        }
      })

      // 填写不匹配的密码
      await wrapper.find('input[name="password"]').setValue('password123')
      await wrapper.find('input[name="confirmPassword"]').setValue('different')

      await wrapper.find('form').trigger('submit')

      expect(wrapper.text()).toContain('密码确认不匹配')
    })

    it('应该验证邮箱格式', async () => {
      const wrapper = mount(RegisterView, {
        global: {
          plugins: [router]
        }
      })

      await wrapper.find('input[name="email"]').setValue('invalid-email')
      await wrapper.find('form').trigger('submit')

      expect(wrapper.text()).toContain('邮箱格式不正确')
    })

    it('应该处理成功注册', async () => {
      mockAuthApi.register.mockResolvedValue({
        id: '1',
        username: 'newuser',
        email: 'new@example.com'
      })

      const wrapper = mount(RegisterView, {
        global: {
          plugins: [router]
        }
      })

      // 填写表单
      await wrapper.find('input[name="username"]').setValue('newuser')
      await wrapper.find('input[name="email"]').setValue('new@example.com')
      await wrapper.find('input[name="password"]').setValue('password123')
      await wrapper.find('input[name="confirmPassword"]').setValue('password123')

      // 提交表单
      await wrapper.find('form').trigger('submit')
      await wrapper.vm.$nextTick()

      // 验证API调用
      expect(mockAuthApi.register).toHaveBeenCalledWith({
        username: 'newuser',
        email: 'new@example.com',
        password: 'password123'
      })

      // 应该显示成功消息
      expect(wrapper.text()).toContain('注册成功')
    })

    it('应该处理注册失败', async () => {
      mockAuthApi.register.mockRejectedValue({
        response: { data: { detail: '用户名已存在' } }
      })

      const wrapper = mount(RegisterView, {
        global: {
          plugins: [router]
        }
      })

      // 填写表单
      await wrapper.find('input[name="username"]').setValue('existinguser')
      await wrapper.find('input[name="email"]').setValue('existing@example.com')
      await wrapper.find('input[name="password"]').setValue('password123')
      await wrapper.find('input[name="confirmPassword"]').setValue('password123')

      // 提交表单
      await wrapper.find('form').trigger('submit')
      await wrapper.vm.$nextTick()

      // 应该显示错误消息
      expect(wrapper.text()).toContain('用户名已存在')
    })
  })

  describe('认证流程集成', () => {
    it('应该完成完整的注册-登录流程', async () => {
      // 1. 注册用户
      mockAuthApi.register.mockResolvedValue({
        id: '1',
        username: 'flowuser',
        email: 'flow@example.com'
      })

      const registerWrapper = mount(RegisterView, {
        global: {
          plugins: [router]
        }
      })

      await registerWrapper.find('input[name="username"]').setValue('flowuser')
      await registerWrapper.find('input[name="email"]').setValue('flow@example.com')
      await registerWrapper.find('input[name="password"]').setValue('password123')
      await registerWrapper.find('input[name="confirmPassword"]').setValue('password123')

      await registerWrapper.find('form').trigger('submit')
      await registerWrapper.vm.$nextTick()

      expect(mockAuthApi.register).toHaveBeenCalled()

      // 2. 登录用户
      mockAuthApi.login.mockResolvedValue({
        access_token: 'test-token',
        user: { id: '1', username: 'flowuser', email: 'flow@example.com' }
      })

      const loginWrapper = mount(LoginView, {
        global: {
          plugins: [router]
        }
      })

      await loginWrapper.find('input[type="text"]').setValue('flowuser')
      await loginWrapper.find('input[type="password"]').setValue('password123')

      await loginWrapper.find('form').trigger('submit')
      await loginWrapper.vm.$nextTick()

      expect(mockAuthApi.login).toHaveBeenCalled()

      // 验证认证状态
      const authStore = useAuthStore()
      expect(authStore.isAuthenticated).toBe(true)
      expect(authStore.user?.username).toBe('flowuser')
    })

    it('应该处理token过期', async () => {
      const authStore = useAuthStore()
      
      // 设置初始认证状态
      authStore.setUser({
        id: '1',
        username: 'testuser',
        email: 'test@example.com'
      })
      authStore.setToken('expired-token')

      // Mock API返回401错误
      mockAuthApi.getCurrentUser.mockRejectedValue({
        response: { status: 401 }
      })

      // 尝试获取用户信息
      await authStore.fetchCurrentUser()

      // 应该清除认证状态
      expect(authStore.isAuthenticated).toBe(false)
      expect(authStore.user).toBeNull()
      expect(authStore.token).toBeNull()
    })
  })
})