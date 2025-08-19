<template>
  <div class="account-settings-view">
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">
          <el-icon><User /></el-icon>
          账户设置
        </h1>
        <p class="page-description">管理您的个人信息和账户偏好设置</p>
      </div>
    </div>

    <div class="settings-content">
      <el-row :gutter="24">
        <el-col :lg="8" :md="24">
          <!-- 个人信息卡片 -->
          <el-card class="profile-card" shadow="hover">
            <div class="profile-header">
              <div class="avatar-section">
                <el-avatar :size="80" :src="userProfile.avatar" class="user-avatar">
                  <el-icon><User /></el-icon>
                </el-avatar>
                <el-button 
                  type="primary" 
                  size="small" 
                  @click="showAvatarUpload = true"
                  class="change-avatar-btn"
                >
                  更换头像
                </el-button>
              </div>
              <div class="profile-info">
                <h3 class="username">{{ userProfile.username }}</h3>
                <p class="user-role">{{ getRoleText(userProfile.role) }}</p>
                <el-tag :type="getStatusType(userProfile.status)" size="small">
                  {{ getStatusText(userProfile.status) }}
                </el-tag>
              </div>
            </div>
            
            <div class="profile-stats">
              <div class="stat-item">
                <div class="stat-value">{{ userProfile.loginCount }}</div>
                <div class="stat-label">登录次数</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">{{ formatDate(userProfile.lastLogin) }}</div>
                <div class="stat-label">最后登录</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">{{ formatDate(userProfile.createdAt) }}</div>
                <div class="stat-label">注册时间</div>
              </div>
            </div>
          </el-card>

          <!-- 快速操作 -->
          <el-card class="quick-actions-card" shadow="hover">
            <template #header>
              <span class="card-title">
                <el-icon><Lightning /></el-icon>
                快速操作
              </span>
            </template>
            <div class="quick-actions">
              <el-button @click="showChangePassword = true" :icon="Lock">
                修改密码
              </el-button>
              <el-button @click="show2FASetup = true" :icon="Key">
                双因子认证
              </el-button>
              <el-button @click="exportData" :icon="Download">
                导出数据
              </el-button>
              <el-button @click="showDeleteAccount = true" type="danger" :icon="Delete">
                删除账户
              </el-button>
            </div>
          </el-card>
        </el-col>

        <el-col :lg="16" :md="24">
          <!-- 设置表单 -->
          <el-card class="settings-form-card" shadow="hover">
            <template #header>
              <span class="card-title">
                <el-icon><Setting /></el-icon>
                基本信息
              </span>
            </template>
            
            <el-form 
              ref="formRef" 
              :model="formData" 
              :rules="formRules" 
              label-width="120px"
              @submit.prevent="saveSettings"
            >
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="用户名" prop="username">
                    <el-input 
                      v-model="formData.username" 
                      placeholder="请输入用户名"
                      :disabled="!editMode"
                    />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="真实姓名" prop="fullName">
                    <el-input 
                      v-model="formData.fullName" 
                      placeholder="请输入真实姓名"
                      :disabled="!editMode"
                    />
                  </el-form-item>
                </el-col>
              </el-row>

              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="邮箱地址" prop="email">
                    <el-input 
                      v-model="formData.email" 
                      placeholder="请输入邮箱地址"
                      :disabled="!editMode"
                    >
                      <template #suffix>
                        <el-tag v-if="userProfile.emailVerified" type="success" size="small">
                          已验证
                        </el-tag>
                        <el-tag v-else type="warning" size="small">
                          未验证
                        </el-tag>
                      </template>
                    </el-input>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="手机号码" prop="phone">
                    <el-input 
                      v-model="formData.phone" 
                      placeholder="请输入手机号码"
                      :disabled="!editMode"
                    >
                      <template #suffix>
                        <el-tag v-if="userProfile.phoneVerified" type="success" size="small">
                          已验证
                        </el-tag>
                        <el-tag v-else type="warning" size="small">
                          未验证
                        </el-tag>
                      </template>
                    </el-input>
                  </el-form-item>
                </el-col>
              </el-row>

              <el-form-item label="个人简介" prop="bio">
                <el-input 
                  v-model="formData.bio" 
                  type="textarea" 
                  :rows="3"
                  placeholder="请输入个人简介"
                  :disabled="!editMode"
                  maxlength="200"
                  show-word-limit
                />
              </el-form-item>

              <el-form-item label="时区设置" prop="timezone">
                <el-select 
                  v-model="formData.timezone" 
                  placeholder="请选择时区"
                  :disabled="!editMode"
                  style="width: 100%"
                >
                  <el-option 
                    v-for="tz in timezones" 
                    :key="tz.value" 
                    :label="tz.label" 
                    :value="tz.value" 
                  />
                </el-select>
              </el-form-item>

              <el-form-item label="语言设置" prop="language">
                <el-select 
                  v-model="formData.language" 
                  placeholder="请选择语言"
                  :disabled="!editMode"
                  style="width: 100%"
                >
                  <el-option label="简体中文" value="zh-CN" />
                  <el-option label="English" value="en-US" />
                  <el-option label="繁體中文" value="zh-TW" />
                </el-select>
              </el-form-item>

              <el-form-item>
                <div class="form-actions">
                  <el-button v-if="!editMode" @click="editMode = true" type="primary">
                    <el-icon><Edit /></el-icon>
                    编辑信息
                  </el-button>
                  <template v-else>
                    <el-button @click="cancelEdit">取消</el-button>
                    <el-button type="primary" @click="saveSettings" :loading="saving">
                      <el-icon><Check /></el-icon>
                      保存更改
                    </el-button>
                  </template>
                </div>
              </el-form-item>
            </el-form>
          </el-card>

          <!-- 隐私设置 -->
          <el-card class="privacy-settings-card" shadow="hover">
            <template #header>
              <span class="card-title">
                <el-icon><Lock /></el-icon>
                隐私设置
              </span>
            </template>
            
            <div class="privacy-options">
              <div class="privacy-item">
                <div class="privacy-info">
                  <h4>个人资料可见性</h4>
                  <p>控制其他用户是否可以查看您的个人资料</p>
                </div>
                <el-switch 
                  v-model="privacySettings.profileVisible" 
                  @change="updatePrivacySetting('profileVisible', $event)"
                />
              </div>
              
              <div class="privacy-item">
                <div class="privacy-info">
                  <h4>在线状态显示</h4>
                  <p>是否向其他用户显示您的在线状态</p>
                </div>
                <el-switch 
                  v-model="privacySettings.showOnlineStatus" 
                  @change="updatePrivacySetting('showOnlineStatus', $event)"
                />
              </div>
              
              <div class="privacy-item">
                <div class="privacy-info">
                  <h4>交易记录可见</h4>
                  <p>是否允许其他用户查看您的交易统计</p>
                </div>
                <el-switch 
                  v-model="privacySettings.tradingStatsVisible" 
                  @change="updatePrivacySetting('tradingStatsVisible', $event)"
                />
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 修改密码对话框 -->
    <el-dialog v-model="showChangePassword" title="修改密码" width="400px">
      <el-form ref="passwordFormRef" :model="passwordForm" :rules="passwordRules" label-width="100px">
        <el-form-item label="当前密码" prop="currentPassword">
          <el-input 
            v-model="passwordForm.currentPassword" 
            type="password" 
            show-password
            placeholder="请输入当前密码"
          />
        </el-form-item>
        <el-form-item label="新密码" prop="newPassword">
          <el-input 
            v-model="passwordForm.newPassword" 
            type="password" 
            show-password
            placeholder="请输入新密码"
          />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input 
            v-model="passwordForm.confirmPassword" 
            type="password" 
            show-password
            placeholder="请再次输入新密码"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showChangePassword = false">取消</el-button>
        <el-button type="primary" @click="changePassword" :loading="changingPassword">
          确认修改
        </el-button>
      </template>
    </el-dialog>

    <!-- 头像上传对话框 -->
    <el-dialog v-model="showAvatarUpload" title="更换头像" width="400px">
      <el-upload
        class="avatar-uploader"
        action="#"
        :show-file-list="false"
        :before-upload="beforeAvatarUpload"
        :http-request="uploadAvatar"
      >
        <img v-if="newAvatarUrl" :src="newAvatarUrl" class="avatar-preview" />
        <el-icon v-else class="avatar-uploader-icon"><Plus /></el-icon>
      </el-upload>
      <template #footer>
        <el-button @click="showAvatarUpload = false">取消</el-button>
        <el-button type="primary" @click="saveAvatar" :disabled="!newAvatarUrl">
          保存头像
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  User, 
  Lightning, 
  Setting, 
  Lock, 
  Download, 
  Delete, 
  Edit, 
  Check,
  Plus,
  Key
} from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

interface UserProfile {
  id: string
  username: string
  fullName: string
  email: string
  phone: string
  bio: string
  avatar: string
  role: string
  status: string
  timezone: string
  language: string
  emailVerified: boolean
  phoneVerified: boolean
  loginCount: number
  lastLogin: string
  createdAt: string
}

interface PrivacySettings {
  profileVisible: boolean
  showOnlineStatus: boolean
  tradingStatsVisible: boolean
}

const editMode = ref(false)
const saving = ref(false)
const showChangePassword = ref(false)
const showAvatarUpload = ref(false)
const show2FASetup = ref(false)
const showDeleteAccount = ref(false)
const changingPassword = ref(false)
const newAvatarUrl = ref('')

const formRef = ref()
const passwordFormRef = ref()

// 用户资料
const userProfile = ref<UserProfile>({
  id: '1',
  username: 'trader001',
  fullName: '张三',
  email: 'trader001@example.com',
  phone: '13800138000',
  bio: '专业量化交易员，专注于股票和期货市场',
  avatar: '',
  role: 'trader',
  status: 'active',
  timezone: 'Asia/Shanghai',
  language: 'zh-CN',
  emailVerified: true,
  phoneVerified: false,
  loginCount: 156,
  lastLogin: dayjs().subtract(2, 'hour').toISOString(),
  createdAt: dayjs().subtract(6, 'month').toISOString()
})

// 表单数据
const formData = reactive({
  username: '',
  fullName: '',
  email: '',
  phone: '',
  bio: '',
  timezone: '',
  language: ''
})

// 隐私设置
const privacySettings = reactive<PrivacySettings>({
  profileVisible: true,
  showOnlineStatus: true,
  tradingStatsVisible: false
})

// 密码表单
const passwordForm = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

// 时区选项
const timezones = [
  { label: '北京时间 (UTC+8)', value: 'Asia/Shanghai' },
  { label: '东京时间 (UTC+9)', value: 'Asia/Tokyo' },
  { label: '纽约时间 (UTC-5)', value: 'America/New_York' },
  { label: '伦敦时间 (UTC+0)', value: 'Europe/London' },
  { label: '悉尼时间 (UTC+10)', value: 'Australia/Sydney' }
]

// 表单验证规则
const formRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  fullName: [
    { required: true, message: '请输入真实姓名', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ],
  phone: [
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号码', trigger: 'blur' }
  ]
}

// 密码验证规则
const passwordRules = {
  currentPassword: [
    { required: true, message: '请输入当前密码', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 8, message: '密码长度不能少于8位', trigger: 'blur' },
    { pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/, message: '密码必须包含大小写字母和数字', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (rule: any, value: string, callback: Function) => {
        if (value !== passwordForm.newPassword) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// 获取角色文本
const getRoleText = (role: string) => {
  const roles: Record<string, string> = {
    admin: '管理员',
    trader: '交易员',
    analyst: '分析师',
    viewer: '观察者'
  }
  return roles[role] || '未知'
}

// 获取状态类型
const getStatusType = (status: string) => {
  const types: Record<string, string> = {
    active: 'success',
    inactive: 'info',
    suspended: 'warning',
    banned: 'danger'
  }
  return types[status] || 'info'
}

// 获取状态文本
const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    active: '正常',
    inactive: '未激活',
    suspended: '暂停',
    banned: '禁用'
  }
  return texts[status] || '未知'
}

// 格式化日期
const formatDate = (date: string) => {
  return dayjs(date).format('YYYY-MM-DD')
}

// 初始化表单数据
const initFormData = () => {
  Object.assign(formData, {
    username: userProfile.value.username,
    fullName: userProfile.value.fullName,
    email: userProfile.value.email,
    phone: userProfile.value.phone,
    bio: userProfile.value.bio,
    timezone: userProfile.value.timezone,
    language: userProfile.value.language
  })
}

// 取消编辑
const cancelEdit = () => {
  editMode.value = false
  initFormData()
}

// 保存设置
const saveSettings = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    saving.value = true
    
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // 更新用户资料
    Object.assign(userProfile.value, formData)
    
    editMode.value = false
    ElMessage.success('设置保存成功')
  } catch (error) {
    ElMessage.error('保存失败，请检查输入信息')
  } finally {
    saving.value = false
  }
}

// 更新隐私设置
const updatePrivacySetting = async (key: keyof PrivacySettings, value: boolean) => {
  try {
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 500))
    ElMessage.success('隐私设置已更新')
  } catch (error) {
    // 回滚设置
    privacySettings[key] = !value
    ElMessage.error('设置更新失败')
  }
}

// 修改密码
const changePassword = async () => {
  if (!passwordFormRef.value) return
  
  try {
    await passwordFormRef.value.validate()
    changingPassword.value = true
    
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    showChangePassword.value = false
    Object.assign(passwordForm, {
      currentPassword: '',
      newPassword: '',
      confirmPassword: ''
    })
    
    ElMessage.success('密码修改成功')
  } catch (error) {
    ElMessage.error('密码修改失败')
  } finally {
    changingPassword.value = false
  }
}

// 头像上传前检查
const beforeAvatarUpload = (file: File) => {
  const isJPG = file.type === 'image/jpeg' || file.type === 'image/png'
  const isLt2M = file.size / 1024 / 1024 < 2

  if (!isJPG) {
    ElMessage.error('头像图片只能是 JPG/PNG 格式!')
    return false
  }
  if (!isLt2M) {
    ElMessage.error('头像图片大小不能超过 2MB!')
    return false
  }
  return true
}

// 上传头像
const uploadAvatar = (options: any) => {
  const file = options.file
  const reader = new FileReader()
  reader.onload = (e) => {
    newAvatarUrl.value = e.target?.result as string
  }
  reader.readAsDataURL(file)
}

// 保存头像
const saveAvatar = async () => {
  try {
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    userProfile.value.avatar = newAvatarUrl.value
    showAvatarUpload.value = false
    newAvatarUrl.value = ''
    
    ElMessage.success('头像更新成功')
  } catch (error) {
    ElMessage.error('头像更新失败')
  }
}

// 导出数据
const exportData = async () => {
  try {
    const result = await ElMessageBox.confirm(
      '确定要导出您的账户数据吗？这将包括您的个人信息和交易记录。',
      '导出数据',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info'
      }
    )
    
    if (result === 'confirm') {
      // 模拟数据导出
      const data = {
        profile: userProfile.value,
        exportTime: new Date().toISOString()
      }
      
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `account-data-${dayjs().format('YYYY-MM-DD')}.json`
      a.click()
      URL.revokeObjectURL(url)
      
      ElMessage.success('数据导出成功')
    }
  } catch (error) {
    // 用户取消
  }
}

onMounted(() => {
  initFormData()
})
</script>

<style lang="scss" scoped>
.account-settings-view {
  padding: 24px;
  background: var(--el-bg-color-page);
  min-height: 100vh;
}

.page-header {
  margin-bottom: 24px;

  .header-content {
    .page-title {
      display: flex;
      align-items: center;
      gap: 12px;
      margin: 0 0 8px 0;
      font-size: 28px;
      font-weight: 700;
      color: var(--el-text-color-primary);

      .el-icon {
        font-size: 32px;
        color: var(--el-color-primary);
      }
    }

    .page-description {
      margin: 0;
      font-size: 16px;
      color: var(--el-text-color-regular);
    }
  }
}

.settings-content {
  .card-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;

    .el-icon {
      color: var(--el-color-primary);
    }
  }
}

.profile-card {
  margin-bottom: 20px;

  .profile-header {
    text-align: center;
    margin-bottom: 24px;

    .avatar-section {
      margin-bottom: 16px;

      .user-avatar {
        margin-bottom: 12px;
      }

      .change-avatar-btn {
        font-size: 12px;
      }
    }

    .profile-info {
      .username {
        margin: 0 0 8px 0;
        font-size: 20px;
        font-weight: 600;
        color: var(--el-text-color-primary);
      }

      .user-role {
        margin: 0 0 8px 0;
        color: var(--el-text-color-secondary);
      }
    }
  }

  .profile-stats {
    display: flex;
    justify-content: space-around;
    padding-top: 20px;
    border-top: 1px solid var(--el-border-color-lighter);

    .stat-item {
      text-align: center;

      .stat-value {
        font-size: 18px;
        font-weight: 600;
        color: var(--el-color-primary);
        margin-bottom: 4px;
      }

      .stat-label {
        font-size: 12px;
        color: var(--el-text-color-secondary);
      }
    }
  }
}

.quick-actions-card {
  .quick-actions {
    display: flex;
    flex-direction: column;
    gap: 12px;

    .el-button {
      justify-content: flex-start;
    }
  }
}

.settings-form-card {
  margin-bottom: 20px;

  .form-actions {
    display: flex;
    gap: 12px;
  }
}

.privacy-settings-card {
  .privacy-options {
    .privacy-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 16px 0;
      border-bottom: 1px solid var(--el-border-color-lighter);

      &:last-child {
        border-bottom: none;
      }

      .privacy-info {
        flex: 1;

        h4 {
          margin: 0 0 4px 0;
          font-size: 16px;
          font-weight: 600;
          color: var(--el-text-color-primary);
        }

        p {
          margin: 0;
          font-size: 14px;
          color: var(--el-text-color-secondary);
        }
      }
    }
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
    width: 178px;
    height: 178px;
    display: flex;
    align-items: center;
    justify-content: center;

    &:hover {
      border-color: var(--el-color-primary);
    }
  }

  .avatar-uploader-icon {
    font-size: 28px;
    color: var(--el-text-color-placeholder);
  }

  .avatar-preview {
    width: 178px;
    height: 178px;
    object-fit: cover;
  }
}

// 响应式设计
@media (max-width: 768px) {
  .account-settings-view {
    padding: 16px;
  }

  .profile-stats {
    flex-direction: column;
    gap: 16px;
  }

  .quick-actions {
    .el-button {
      width: 100%;
    }
  }
}
</style>
