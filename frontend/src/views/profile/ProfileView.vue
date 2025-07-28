<template>
  <div class="profile-container">
    <div class="page-header">
      <h1 class="page-title">个人中心</h1>
      <p class="page-description">管理您的个人信息和账户设置</p>
    </div>

    <el-row :gutter="20">
      <!-- 左侧用户信息卡片 -->
      <el-col :xs="24" :lg="8">
        <el-card class="user-info-card">
          <div class="user-info-header">
            <UserAvatar
              :avatar-url="userInfo.avatar_url"
              :display-name="userInfo.full_name || userInfo.username"
              :role="userInfo.role"
              :size="80"
              :show-name="true"
              :show-role="true"
            />
            
            <el-button 
              type="primary" 
              size="small" 
              @click="showAvatarUpload = true"
              class="upload-avatar-btn"
            >
              更换头像
            </el-button>
          </div>
          
          <el-divider />
          
          <div class="user-stats">
            <div class="stat-item">
              <div class="stat-label">注册时间</div>
              <div class="stat-value">{{ formatDate(userInfo.created_at) }}</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">最后登录</div>
              <div class="stat-value">{{ formatDate(userInfo.last_login_at) }}</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">账户状态</div>
              <div class="stat-value">
                <el-tag :type="userInfo.is_active ? 'success' : 'danger'" size="small">
                  {{ userInfo.is_active ? '正常' : '禁用' }}
                </el-tag>
              </div>
            </div>
            <div class="stat-item">
              <div class="stat-label">邮箱验证</div>
              <div class="stat-value">
                <el-tag :type="userInfo.is_verified ? 'success' : 'warning'" size="small">
                  {{ userInfo.is_verified ? '已验证' : '未验证' }}
                </el-tag>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧设置表单 -->
      <el-col :xs="24" :lg="16">
        <el-tabs v-model="activeTab" class="profile-tabs">
          <!-- 基本信息 -->
          <el-tab-pane label="基本信息" name="basic">
            <el-card>
              <el-form
                ref="basicFormRef"
                :model="basicForm"
                :rules="basicRules"
                label-width="100px"
                size="default"
              >
                <el-form-item label="用户名" prop="username">
                  <el-input 
                    v-model="basicForm.username" 
                    disabled
                    placeholder="用户名不可修改"
                  />
                </el-form-item>

                <el-form-item label="邮箱" prop="email">
                  <el-input 
                    v-model="basicForm.email" 
                    type="email"
                    placeholder="请输入邮箱地址"
                  >
                    <template #append>
                      <el-button 
                        v-if="!userInfo.is_verified" 
                        type="primary" 
                        size="small"
                        @click="sendVerificationEmail"
                        :loading="verificationLoading"
                      >
                        验证邮箱
                      </el-button>
                    </template>
                  </el-input>
                </el-form-item>

                <el-form-item label="真实姓名" prop="full_name">
                  <el-input 
                    v-model="basicForm.full_name" 
                    placeholder="请输入真实姓名"
                  />
                </el-form-item>

                <el-form-item label="手机号码" prop="phone">
                  <el-input 
                    v-model="basicForm.phone" 
                    placeholder="请输入手机号码"
                  />
                </el-form-item>

                <el-form-item>
                  <el-button 
                    type="primary" 
                    @click="updateBasicInfo"
                    :loading="basicLoading"
                  >
                    保存修改
                  </el-button>
                  <el-button @click="resetBasicForm">
                    重置
                  </el-button>
                </el-form-item>
              </el-form>
            </el-card>
          </el-tab-pane>

          <!-- 安全设置 -->
          <el-tab-pane label="安全设置" name="security">
            <el-card>
              <el-form
                ref="passwordFormRef"
                :model="passwordForm"
                :rules="passwordRules"
                label-width="100px"
                size="default"
              >
                <el-form-item label="当前密码" prop="old_password">
                  <el-input 
                    v-model="passwordForm.old_password" 
                    type="password"
                    placeholder="请输入当前密码"
                    show-password
                  />
                </el-form-item>

                <el-form-item label="新密码" prop="new_password">
                  <el-input 
                    v-model="passwordForm.new_password" 
                    type="password"
                    placeholder="请输入新密码"
                    show-password
                  />
                </el-form-item>

                <el-form-item label="确认密码" prop="confirm_password">
                  <el-input 
                    v-model="passwordForm.confirm_password" 
                    type="password"
                    placeholder="请再次输入新密码"
                    show-password
                  />
                </el-form-item>

                <el-form-item>
                  <el-button 
                    type="primary" 
                    @click="changePassword"
                    :loading="passwordLoading"
                  >
                    修改密码
                  </el-button>
                  <el-button @click="resetPasswordForm">
                    重置
                  </el-button>
                </el-form-item>
              </el-form>
            </el-card>
          </el-tab-pane>

          <!-- 会话管理 -->
          <el-tab-pane label="会话管理" name="sessions">
            <el-card>
              <div class="sessions-header">
                <h3>活跃会话</h3>
                <el-button 
                  type="danger" 
                  size="small"
                  @click="logoutAllSessions"
                  :loading="sessionLoading"
                >
                  注销所有会话
                </el-button>
              </div>
              
              <el-table :data="sessions" style="width: 100%">
                <el-table-column prop="ip_address" label="IP地址" width="150" />
                <el-table-column prop="user_agent" label="设备信息" show-overflow-tooltip />
                <el-table-column prop="last_accessed_at" label="最后访问" width="180">
                  <template #default="{ row }">
                    {{ formatDate(row.last_accessed_at) }}
                  </template>
                </el-table-column>
                <el-table-column prop="is_current" label="状态" width="100">
                  <template #default="{ row }">
                    <el-tag :type="row.is_current ? 'success' : 'info'" size="small">
                      {{ row.is_current ? '当前' : '其他' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="100">
                  <template #default="{ row }">
                    <el-button 
                      v-if="!row.is_current"
                      type="danger" 
                      size="small"
                      @click="logoutSession(row.id)"
                    >
                      注销
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </el-tab-pane>
        </el-tabs>
      </el-col>
    </el-row>

    <!-- 头像上传对话框 -->
    <el-dialog
      v-model="showAvatarUpload"
      title="更换头像"
      width="400px"
      :close-on-click-modal="false"
    >
      <el-upload
        class="avatar-uploader"
        action="#"
        :show-file-list="false"
        :before-upload="beforeAvatarUpload"
        :http-request="uploadAvatar"
      >
        <img v-if="previewUrl" :src="previewUrl" class="avatar-preview" />
        <el-icon v-else class="avatar-uploader-icon">
          <Plus />
        </el-icon>
      </el-upload>
      
      <template #footer>
        <el-button @click="showAvatarUpload = false">取消</el-button>
        <el-button 
          type="primary" 
          @click="confirmAvatarUpload"
          :loading="avatarLoading"
          :disabled="!selectedFile"
        >
          确认上传
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import type { FormInstance, FormRules, UploadRequestOptions } from 'element-plus'
import dayjs from 'dayjs'
import UserAvatar from '@/components/UserAvatar.vue'

const authStore = useAuthStore()

// 响应式数据
const activeTab = ref('basic')
const basicLoading = ref(false)
const passwordLoading = ref(false)
const sessionLoading = ref(false)
const verificationLoading = ref(false)
const avatarLoading = ref(false)
const showAvatarUpload = ref(false)
const previewUrl = ref('')
const selectedFile = ref<File | null>(null)

// 表单引用
const basicFormRef = ref<FormInstance>()
const passwordFormRef = ref<FormInstance>()

// 用户信息
const userInfo = reactive({
  username: authStore.user?.username || '',
  email: authStore.user?.email || '',
  full_name: authStore.user?.full_name || '',
  phone: authStore.user?.phone || '',
  avatar_url: authStore.user?.avatar_url || '',
  role: authStore.user?.role || '',
  is_active: authStore.user?.is_active || false,
  is_verified: authStore.user?.is_verified || false,
  created_at: authStore.user?.created_at || '',
  last_login_at: authStore.user?.last_login_at || ''
})

// 基本信息表单
const basicForm = reactive({
  username: userInfo.username,
  email: userInfo.email,
  full_name: userInfo.full_name,
  phone: userInfo.phone
})

// 密码修改表单
const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

// 会话列表
const sessions = ref([
  {
    id: 1,
    ip_address: '192.168.1.100',
    user_agent: 'Chrome 120.0.0.0 on Windows 10',
    last_accessed_at: new Date().toISOString(),
    is_current: true
  },
  {
    id: 2,
    ip_address: '10.0.0.50',
    user_agent: 'Safari 17.0 on macOS',
    last_accessed_at: new Date(Date.now() - 3600000).toISOString(),
    is_current: false
  }
])

// 确认密码验证器
const validateConfirmPassword = (rule: any, value: string, callback: any) => {
  if (value === '') {
    callback(new Error('请再次输入密码'))
  } else if (value !== passwordForm.new_password) {
    callback(new Error('两次输入密码不一致'))
  } else {
    callback()
  }
}

// 表单验证规则
const basicRules: FormRules = {
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ],
  full_name: [
    { max: 50, message: '姓名长度不能超过 50 个字符', trigger: 'blur' }
  ],
  phone: [
    { pattern: /^1[3-9]\d{9}$/, message: '请输入有效的手机号码', trigger: 'blur' }
  ]
}

const passwordRules: FormRules = {
  old_password: [
    { required: true, message: '请输入当前密码', trigger: 'blur' }
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 8, max: 128, message: '密码长度至少 8 个字符', trigger: 'blur' },
    { pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/, message: '密码必须包含大小写字母和数字', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

// 格式化日期
const formatDate = (dateStr: string | undefined) => {
  if (!dateStr) return '未知'
  return dayjs(dateStr).format('YYYY-MM-DD HH:mm:ss')
}

// 更新基本信息
const updateBasicInfo = async () => {
  if (!basicFormRef.value) return

  try {
    const valid = await basicFormRef.value.validate()
    if (!valid) return

    basicLoading.value = true

    // 这里调用API更新用户信息
    // await userApi.updateProfile(basicForm)
    
    // 更新本地用户信息
    authStore.updateUser(basicForm)
    
    ElMessage.success('基本信息更新成功')
  } catch (error: any) {
    ElMessage.error(error.message || '更新失败')
  } finally {
    basicLoading.value = false
  }
}

// 重置基本信息表单
const resetBasicForm = () => {
  Object.assign(basicForm, {
    username: userInfo.username,
    email: userInfo.email,
    full_name: userInfo.full_name,
    phone: userInfo.phone
  })
}

// 修改密码
const changePassword = async () => {
  if (!passwordFormRef.value) return

  try {
    const valid = await passwordFormRef.value.validate()
    if (!valid) return

    passwordLoading.value = true

    // 这里调用API修改密码
    // await authApi.changePassword(passwordForm)
    
    ElMessage.success('密码修改成功')
    resetPasswordForm()
  } catch (error: any) {
    ElMessage.error(error.message || '密码修改失败')
  } finally {
    passwordLoading.value = false
  }
}

// 重置密码表单
const resetPasswordForm = () => {
  Object.assign(passwordForm, {
    old_password: '',
    new_password: '',
    confirm_password: ''
  })
}

// 发送验证邮件
const sendVerificationEmail = async () => {
  try {
    verificationLoading.value = true
    
    // 这里调用API发送验证邮件
    // await authApi.sendVerificationEmail()
    
    ElMessage.success('验证邮件已发送，请查收邮箱')
  } catch (error: any) {
    ElMessage.error(error.message || '发送验证邮件失败')
  } finally {
    verificationLoading.value = false
  }
}

// 注销所有会话
const logoutAllSessions = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要注销所有会话吗？这将强制所有设备重新登录。',
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    sessionLoading.value = true
    
    // 这里调用API注销所有会话
    // await authApi.logoutAllSessions()
    
    ElMessage.success('所有会话已注销')
    // 重新加载会话列表
    loadSessions()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '操作失败')
    }
  } finally {
    sessionLoading.value = false
  }
}

// 注销单个会话
const logoutSession = async (sessionId: number) => {
  try {
    await ElMessageBox.confirm(
      '确定要注销该会话吗？',
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    // 这里调用API注销会话
    // await authApi.logoutSession(sessionId)
    
    ElMessage.success('会话已注销')
    // 重新加载会话列表
    loadSessions()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '操作失败')
    }
  }
}

// 头像上传前检查
const beforeAvatarUpload = (file: File) => {
  const isImage = file.type.startsWith('image/')
  const isLt2M = file.size / 1024 / 1024 < 2

  if (!isImage) {
    ElMessage.error('只能上传图片文件!')
    return false
  }
  if (!isLt2M) {
    ElMessage.error('图片大小不能超过 2MB!')
    return false
  }

  // 预览图片
  const reader = new FileReader()
  reader.onload = (e) => {
    previewUrl.value = e.target?.result as string
  }
  reader.readAsDataURL(file)
  
  selectedFile.value = file
  return false // 阻止自动上传
}

// 自定义上传
const uploadAvatar = (options: UploadRequestOptions) => {
  // 这里不做实际上传，只是为了满足类型要求
  return Promise.resolve()
}

// 确认头像上传
const confirmAvatarUpload = async () => {
  if (!selectedFile.value) return

  try {
    avatarLoading.value = true

    // 这里调用API上传头像
    // const formData = new FormData()
    // formData.append('avatar', selectedFile.value)
    // const response = await userApi.uploadAvatar(formData)
    
    // 更新用户头像
    // authStore.updateUser({ avatar_url: response.data.avatar_url })
    
    ElMessage.success('头像更新成功')
    showAvatarUpload.value = false
    previewUrl.value = ''
    selectedFile.value = null
  } catch (error: any) {
    ElMessage.error(error.message || '头像上传失败')
  } finally {
    avatarLoading.value = false
  }
}

// 加载会话列表
const loadSessions = async () => {
  try {
    // 这里调用API加载会话列表
    // const response = await authApi.getSessions()
    // sessions.value = response.data
  } catch (error) {
    console.error('加载会话列表失败:', error)
  }
}

// 生命周期
onMounted(() => {
  loadSessions()
})
</script>

<style lang="scss" scoped>
.profile-container {
  padding: 20px;
}

.user-info-card {
  .user-info-header {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 16px;
    
    .upload-avatar-btn {
      margin-top: 8px;
    }
  }
  
  .user-stats {
    .stat-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px 0;
      border-bottom: 1px solid var(--el-border-color-lighter);
      
      &:last-child {
        border-bottom: none;
      }
      
      .stat-label {
        color: var(--el-text-color-secondary);
        font-size: 14px;
      }
      
      .stat-value {
        color: var(--el-text-color-primary);
        font-size: 14px;
        font-weight: 500;
      }
    }
  }
}

.profile-tabs {
  :deep(.el-tabs__content) {
    padding-top: 20px;
  }
}

.sessions-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  
  h3 {
    margin: 0;
    color: var(--el-text-color-primary);
  }
}

.avatar-uploader {
  :deep(.el-upload) {
    border: 1px dashed var(--el-border-color);
    border-radius: 6px;
    cursor: pointer;
    position: relative;
    overflow: hidden;
    transition: var(--el-transition-duration-fast);
    
    &:hover {
      border-color: var(--el-color-primary);
    }
  }
  
  .avatar-uploader-icon {
    font-size: 28px;
    color: #8c939d;
    width: 178px;
    height: 178px;
    text-align: center;
    line-height: 178px;
  }
  
  .avatar-preview {
    width: 178px;
    height: 178px;
    display: block;
    object-fit: cover;
  }
}

// 响应式设计
@media (max-width: 768px) {
  .profile-container {
    padding: 16px;
  }
  
  .user-info-card {
    margin-bottom: 20px;
  }
}
</style>