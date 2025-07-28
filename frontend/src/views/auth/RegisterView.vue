<template>
  <div class="register-container">
    <div class="register-form-container">
      <div class="register-header">
        <div class="logo">
          <el-icon size="32" color="var(--el-color-primary)">
            <TrendCharts />
          </el-icon>
          <h1>创建账户</h1>
        </div>
        <p class="subtitle">加入量化交易平台，开启智能交易之旅</p>
      </div>

      <el-form
        ref="registerFormRef"
        :model="registerForm"
        :rules="registerRules"
        class="register-form"
        size="large"
        @submit.prevent="handleRegister"
      >
        <el-form-item prop="username">
          <el-input
            v-model="registerForm.username"
            placeholder="用户名"
            prefix-icon="User"
            clearable
          />
        </el-form-item>

        <el-form-item prop="email">
          <el-input
            v-model="registerForm.email"
            placeholder="邮箱地址"
            prefix-icon="Message"
            clearable
          />
        </el-form-item>

        <el-form-item prop="full_name">
          <el-input
            v-model="registerForm.full_name"
            placeholder="真实姓名（可选）"
            prefix-icon="UserFilled"
            clearable
          />
        </el-form-item>

        <el-form-item prop="phone">
          <el-input
            v-model="registerForm.phone"
            placeholder="手机号码（可选）"
            prefix-icon="Phone"
            clearable
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="registerForm.password"
            type="password"
            placeholder="密码"
            prefix-icon="Lock"
            show-password
            clearable
          />
        </el-form-item>

        <el-form-item prop="confirm_password">
          <el-input
            v-model="registerForm.confirm_password"
            type="password"
            placeholder="确认密码"
            prefix-icon="Lock"
            show-password
            clearable
            @keyup.enter="handleRegister"
          />
        </el-form-item>

        <el-form-item prop="agreement">
          <el-checkbox v-model="registerForm.agreement">
            我已阅读并同意
            <el-link type="primary" @click="showTerms">用户协议</el-link>
            和
            <el-link type="primary" @click="showPrivacy">隐私政策</el-link>
          </el-checkbox>
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            class="register-button"
            :loading="authStore.loading"
            @click="handleRegister"
          >
            注册
          </el-button>
        </el-form-item>

        <el-form-item>
          <div class="login-link">
            已有账户？
            <el-link type="primary" @click="goToLogin">
              立即登录
            </el-link>
          </div>
        </el-form-item>
      </el-form>
    </div>

    <!-- 用户协议对话框 -->
    <el-dialog
      v-model="termsVisible"
      title="用户协议"
      width="600px"
      :close-on-click-modal="false"
    >
      <div class="terms-content">
        <h3>1. 服务条款</h3>
        <p>欢迎使用量化交易平台。在使用本平台前，请仔细阅读本用户协议。</p>
        
        <h3>2. 用户责任</h3>
        <p>用户应当对自己的交易行为负责，平台不承担因用户操作失误导致的损失。</p>
        
        <h3>3. 风险提示</h3>
        <p>量化交易存在风险，过往业绩不代表未来表现，请谨慎投资。</p>
        
        <h3>4. 免责声明</h3>
        <p>平台提供的信息仅供参考，不构成投资建议。</p>
      </div>
      
      <template #footer>
        <el-button @click="termsVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 隐私政策对话框 -->
    <el-dialog
      v-model="privacyVisible"
      title="隐私政策"
      width="600px"
      :close-on-click-modal="false"
    >
      <div class="privacy-content">
        <h3>1. 信息收集</h3>
        <p>我们会收集您提供的注册信息和使用平台时产生的数据。</p>
        
        <h3>2. 信息使用</h3>
        <p>收集的信息仅用于提供服务、改善用户体验和法律要求。</p>
        
        <h3>3. 信息保护</h3>
        <p>我们采用行业标准的安全措施保护您的个人信息。</p>
        
        <h3>4. 信息共享</h3>
        <p>除法律要求外，我们不会向第三方分享您的个人信息。</p>
      </div>
      
      <template #footer>
        <el-button @click="privacyVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { TrendCharts } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()

// 表单引用
const registerFormRef = ref<FormInstance>()

// 注册表单
const registerForm = reactive({
  username: '',
  email: '',
  full_name: '',
  phone: '',
  password: '',
  confirm_password: '',
  agreement: false
})

// 对话框状态
const termsVisible = ref(false)
const privacyVisible = ref(false)

// 确认密码验证器
const validateConfirmPassword = (rule: any, value: string, callback: any) => {
  if (value === '') {
    callback(new Error('请再次输入密码'))
  } else if (value !== registerForm.password) {
    callback(new Error('两次输入密码不一致'))
  } else {
    callback()
  }
}

// 协议验证器
const validateAgreement = (rule: any, value: boolean, callback: any) => {
  if (!value) {
    callback(new Error('请阅读并同意用户协议和隐私政策'))
  } else {
    callback()
  }
}

// 表单验证规则
const registerRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_]+$/, message: '用户名只能包含字母、数字和下划线', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ],
  full_name: [
    { max: 50, message: '姓名长度不能超过 50 个字符', trigger: 'blur' }
  ],
  phone: [
    { pattern: /^1[3-9]\d{9}$/, message: '请输入有效的手机号码', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, max: 128, message: '密码长度至少 8 个字符', trigger: 'blur' },
    { pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/, message: '密码必须包含大小写字母和数字', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, validator: validateConfirmPassword, trigger: 'blur' }
  ],
  agreement: [
    { required: true, validator: validateAgreement, trigger: 'change' }
  ]
}

// 处理注册
const handleRegister = async () => {
  if (!registerFormRef.value) return

  try {
    const valid = await registerFormRef.value.validate()
    if (!valid) return

    const success = await authStore.register({
      username: registerForm.username,
      email: registerForm.email,
      full_name: registerForm.full_name || undefined,
      phone: registerForm.phone || undefined,
      password: registerForm.password,
      confirm_password: registerForm.confirm_password
    })

    if (success) {
      // 注册成功，跳转到登录页面
      router.push('/login')
    }
  } catch (error) {
    console.error('注册失败:', error)
  }
}

// 显示用户协议
const showTerms = () => {
  termsVisible.value = true
}

// 显示隐私政策
const showPrivacy = () => {
  privacyVisible.value = true
}

// 跳转到登录页面
const goToLogin = () => {
  router.push('/login')
}
</script>

<style lang="scss" scoped>
.register-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.register-form-container {
  width: 100%;
  max-width: 450px;
  background: var(--el-bg-color);
  border-radius: 12px;
  padding: 40px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
}

.register-header {
  text-align: center;
  margin-bottom: 32px;

  .logo {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    margin-bottom: 16px;

    h1 {
      margin: 0;
      font-size: 24px;
      font-weight: 600;
      color: var(--el-text-color-primary);
    }
  }

  .subtitle {
    margin: 0;
    color: var(--el-text-color-secondary);
    font-size: 14px;
    line-height: 1.5;
  }
}

.register-form {
  .register-button {
    width: 100%;
    height: 44px;
    font-size: 16px;
    font-weight: 500;
  }

  .login-link {
    text-align: center;
    color: var(--el-text-color-secondary);
    font-size: 14px;
  }
}

.terms-content,
.privacy-content {
  max-height: 400px;
  overflow-y: auto;
  
  h3 {
    color: var(--el-text-color-primary);
    margin: 16px 0 8px 0;
    font-size: 16px;
  }
  
  p {
    color: var(--el-text-color-regular);
    line-height: 1.6;
    margin: 0 0 12px 0;
  }
}

// 响应式设计
@media (max-width: 480px) {
  .register-form-container {
    padding: 24px;
    margin: 0 16px;
  }

  .register-header {
    margin-bottom: 24px;

    .logo h1 {
      font-size: 20px;
    }
  }
}
</style>