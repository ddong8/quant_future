<template>
  <el-dialog
    v-model="dialogVisible"
    title="账户设置"
    width="600px"
    :before-close="handleClose"
  >
    <el-tabs v-model="activeTab" type="card">
      <!-- 基本信息 -->
      <el-tab-pane label="基本信息" name="basic">
        <el-form
          ref="basicFormRef"
          :model="basicForm"
          :rules="basicRules"
          label-width="120px"
        >
          <el-form-item label="账户名称" prop="account_name">
            <el-input
              v-model="basicForm.account_name"
              placeholder="请输入账户名称"
              maxlength="50"
              show-word-limit
            />
          </el-form-item>

          <el-form-item label="风险等级" prop="risk_level">
            <el-select v-model="basicForm.risk_level" placeholder="请选择风险等级">
              <el-option label="低风险" value="LOW" />
              <el-option label="中等风险" value="MEDIUM" />
              <el-option label="高风险" value="HIGH" />
            </el-select>
            <div class="form-tip">
              风险等级将影响系统的风险控制策略
            </div>
          </el-form-item>

          <el-form-item label="最大持仓价值" prop="max_position_value">
            <el-input
              v-model="basicForm.max_position_value"
              type="number"
              placeholder="请输入最大持仓价值限制"
              :min="0"
            >
              <template #append>USD</template>
            </el-input>
            <div class="form-tip">
              设置0表示无限制
            </div>
          </el-form-item>

          <el-form-item label="最大日亏损" prop="max_daily_loss">
            <el-input
              v-model="basicForm.max_daily_loss"
              type="number"
              placeholder="请输入最大日亏损限制"
              :min="0"
            >
              <template #append>USD</template>
            </el-input>
            <div class="form-tip">
              设置0表示无限制
            </div>
          </el-form-item>
        </el-form>

        <div class="form-actions">
          <el-button @click="resetBasicForm">重置</el-button>
          <el-button type="primary" :loading="basicLoading" @click="saveBasicSettings">
            保存设置
          </el-button>
        </div>
      </el-tab-pane>

      <!-- 安全设置 -->
      <el-tab-pane label="安全设置" name="security">
        <div class="security-section">
          <h4>密码管理</h4>
          <el-form
            ref="passwordFormRef"
            :model="passwordForm"
            :rules="passwordRules"
            label-width="120px"
          >
            <el-form-item label="当前密码" prop="current_password">
              <el-input
                v-model="passwordForm.current_password"
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

            <el-form-item label="确认新密码" prop="confirm_password">
              <el-input
                v-model="passwordForm.confirm_password"
                type="password"
                placeholder="请再次输入新密码"
                show-password
              />
            </el-form-item>

            <div class="form-actions">
              <el-button @click="resetPasswordForm">重置</el-button>
              <el-button type="primary" :loading="passwordLoading" @click="changePassword">
                修改密码
              </el-button>
            </div>
          </el-form>
        </div>

        <el-divider />

        <div class="security-section">
          <h4>双因子认证</h4>
          <div class="two-factor-auth">
            <div class="auth-status">
              <el-icon :class="twoFactorEnabled ? 'enabled' : 'disabled'">
                <CircleCheck v-if="twoFactorEnabled" />
                <CircleClose v-else />
              </el-icon>
              <span>双因子认证{{ twoFactorEnabled ? '已启用' : '未启用' }}</span>
            </div>
            
            <el-button
              :type="twoFactorEnabled ? 'danger' : 'primary'"
              @click="toggleTwoFactor"
              :loading="twoFactorLoading"
            >
              {{ twoFactorEnabled ? '关闭' : '启用' }}双因子认证
            </el-button>
          </div>
          
          <div class="form-tip">
            启用双因子认证可以大大提高账户安全性，建议开启
          </div>
        </div>

        <el-divider />

        <div class="security-section">
          <h4>登录设备管理</h4>
          <div class="device-list">
            <div
              v-for="device in loginDevices"
              :key="device.id"
              class="device-item"
            >
              <div class="device-info">
                <div class="device-name">
                  <el-icon><Monitor /></el-icon>
                  {{ device.device_name }}
                </div>
                <div class="device-details">
                  <span>{{ device.location }}</span>
                  <span>{{ formatDate(device.last_login) }}</span>
                </div>
              </div>
              <div class="device-actions">
                <el-tag v-if="device.is_current" type="success">当前设备</el-tag>
                <el-button
                  v-else
                  type="danger"
                  size="small"
                  @click="removeDevice(device.id)"
                >
                  移除
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- 通知设置 -->
      <el-tab-pane label="通知设置" name="notification">
        <el-form label-width="150px">
          <el-form-item label="邮件通知">
            <el-switch
              v-model="notificationSettings.email_enabled"
              active-text="开启"
              inactive-text="关闭"
            />
          </el-form-item>

          <el-form-item label="短信通知">
            <el-switch
              v-model="notificationSettings.sms_enabled"
              active-text="开启"
              inactive-text="关闭"
            />
          </el-form-item>

          <el-form-item label="交易通知">
            <el-checkbox-group v-model="notificationSettings.trade_notifications">
              <el-checkbox label="order_filled">订单成交</el-checkbox>
              <el-checkbox label="position_closed">持仓平仓</el-checkbox>
              <el-checkbox label="stop_loss_triggered">止损触发</el-checkbox>
              <el-checkbox label="take_profit_triggered">止盈触发</el-checkbox>
            </el-checkbox-group>
          </el-form-item>

          <el-form-item label="风险通知">
            <el-checkbox-group v-model="notificationSettings.risk_notifications">
              <el-checkbox label="margin_call">保证金不足</el-checkbox>
              <el-checkbox label="large_loss">大额亏损</el-checkbox>
              <el-checkbox label="position_limit">持仓限制</el-checkbox>
              <el-checkbox label="daily_loss_limit">日亏损限制</el-checkbox>
            </el-checkbox-group>
          </el-form-item>

          <el-form-item label="系统通知">
            <el-checkbox-group v-model="notificationSettings.system_notifications">
              <el-checkbox label="maintenance">系统维护</el-checkbox>
              <el-checkbox label="security_alert">安全提醒</el-checkbox>
              <el-checkbox label="feature_update">功能更新</el-checkbox>
            </el-checkbox-group>
          </el-form-item>

          <div class="form-actions">
            <el-button @click="resetNotificationSettings">重置</el-button>
            <el-button type="primary" :loading="notificationLoading" @click="saveNotificationSettings">
              保存设置
            </el-button>
          </div>
        </el-form>
      </el-tab-pane>
    </el-tabs>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import {
  CircleCheck,
  CircleClose,
  Monitor
} from '@element-plus/icons-vue'
import { accountApi } from '@/api/account'
import { formatDate } from '@/utils/format'

interface Props {
  modelValue: boolean
  account: any
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 响应式数据
const activeTab = ref('basic')
const basicFormRef = ref<FormInstance>()
const passwordFormRef = ref<FormInstance>()
const basicLoading = ref(false)
const passwordLoading = ref(false)
const twoFactorLoading = ref(false)
const notificationLoading = ref(false)

const basicForm = ref({
  account_name: '',
  risk_level: '',
  max_position_value: '',
  max_daily_loss: ''
})

const passwordForm = ref({
  current_password: '',
  new_password: '',
  confirm_password: ''
})

const twoFactorEnabled = ref(false)

const loginDevices = ref([
  {
    id: 1,
    device_name: 'Chrome on Windows',
    location: '北京市',
    last_login: new Date(),
    is_current: true
  },
  {
    id: 2,
    device_name: 'Safari on iPhone',
    location: '上海市',
    last_login: new Date(Date.now() - 86400000),
    is_current: false
  }
])

const notificationSettings = ref({
  email_enabled: true,
  sms_enabled: false,
  trade_notifications: ['order_filled', 'position_closed'],
  risk_notifications: ['margin_call', 'large_loss'],
  system_notifications: ['maintenance', 'security_alert']
})

// 表单验证规则
const basicRules: FormRules = {
  account_name: [
    { required: true, message: '请输入账户名称', trigger: 'blur' },
    { min: 2, max: 50, message: '账户名称长度在2-50个字符', trigger: 'blur' }
  ],
  risk_level: [
    { required: true, message: '请选择风险等级', trigger: 'change' }
  ]
}

const passwordRules: FormRules = {
  current_password: [
    { required: true, message: '请输入当前密码', trigger: 'blur' }
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 8, message: '密码长度至少8位', trigger: 'blur' },
    {
      pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]/,
      message: '密码必须包含大小写字母、数字和特殊字符',
      trigger: 'blur'
    }
  ],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== passwordForm.value.new_password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// 计算属性
const dialogVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// 监听对话框显示状态
watch(dialogVisible, (visible) => {
  if (visible && props.account) {
    initForms()
  }
})

// 方法
const initForms = () => {
  basicForm.value = {
    account_name: props.account.account_name || '',
    risk_level: props.account.risk_level || '',
    max_position_value: props.account.max_position_value?.toString() || '',
    max_daily_loss: props.account.max_daily_loss?.toString() || ''
  }
  
  // 重置密码表单
  resetPasswordForm()
  
  // 加载其他设置
  loadSecuritySettings()
  loadNotificationSettings()
}

const resetBasicForm = () => {
  if (props.account) {
    initForms()
  }
  basicFormRef.value?.clearValidate()
}

const resetPasswordForm = () => {
  passwordForm.value = {
    current_password: '',
    new_password: '',
    confirm_password: ''
  }
  passwordFormRef.value?.clearValidate()
}

const saveBasicSettings = async () => {
  if (!basicFormRef.value) return
  
  try {
    const valid = await basicFormRef.value.validate()
    if (!valid) return
    
    basicLoading.value = true
    
    const updateData = {
      account_name: basicForm.value.account_name,
      risk_level: basicForm.value.risk_level,
      max_position_value: basicForm.value.max_position_value ? 
        parseFloat(basicForm.value.max_position_value) : null,
      max_daily_loss: basicForm.value.max_daily_loss ? 
        parseFloat(basicForm.value.max_daily_loss) : null
    }
    
    await accountApi.updateAccount(props.account.id, updateData)
    
    ElMessage.success('基本设置保存成功')
    emit('success')
    
  } catch (error: any) {
    ElMessage.error(error.message || '保存设置失败')
  } finally {
    basicLoading.value = false
  }
}

const changePassword = async () => {
  if (!passwordFormRef.value) return
  
  try {
    const valid = await passwordFormRef.value.validate()
    if (!valid) return
    
    passwordLoading.value = true
    
    // 这里调用修改密码的API
    // await userApi.changePassword(passwordForm.value)
    
    ElMessage.success('密码修改成功')
    resetPasswordForm()
    
  } catch (error: any) {
    ElMessage.error(error.message || '密码修改失败')
  } finally {
    passwordLoading.value = false
  }
}

const toggleTwoFactor = async () => {
  try {
    const action = twoFactorEnabled.value ? '关闭' : '启用'
    const confirmResult = await ElMessageBox.confirm(
      `确认${action}双因子认证吗？`,
      `${action}双因子认证`,
      {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: 'warning'
      }
    ).catch(() => false)

    if (!confirmResult) return

    twoFactorLoading.value = true
    
    // 这里调用启用/关闭双因子认证的API
    // await userApi.toggleTwoFactor(!twoFactorEnabled.value)
    
    twoFactorEnabled.value = !twoFactorEnabled.value
    ElMessage.success(`双因子认证${action}成功`)
    
  } catch (error: any) {
    ElMessage.error(error.message || '操作失败')
  } finally {
    twoFactorLoading.value = false
  }
}

const removeDevice = async (deviceId: number) => {
  try {
    const confirmResult = await ElMessageBox.confirm(
      '确认移除此设备吗？该设备将需要重新登录。',
      '移除设备',
      {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: 'warning'
      }
    ).catch(() => false)

    if (!confirmResult) return

    // 这里调用移除设备的API
    // await userApi.removeDevice(deviceId)
    
    loginDevices.value = loginDevices.value.filter(device => device.id !== deviceId)
    ElMessage.success('设备移除成功')
    
  } catch (error: any) {
    ElMessage.error(error.message || '移除设备失败')
  }
}

const loadSecuritySettings = async () => {
  try {
    // 这里加载安全设置
    // const settings = await userApi.getSecuritySettings()
    // twoFactorEnabled.value = settings.two_factor_enabled
  } catch (error) {
    console.error('加载安全设置失败:', error)
  }
}

const loadNotificationSettings = async () => {
  try {
    // 这里加载通知设置
    // const settings = await userApi.getNotificationSettings()
    // notificationSettings.value = settings
  } catch (error) {
    console.error('加载通知设置失败:', error)
  }
}

const resetNotificationSettings = () => {
  notificationSettings.value = {
    email_enabled: true,
    sms_enabled: false,
    trade_notifications: ['order_filled', 'position_closed'],
    risk_notifications: ['margin_call', 'large_loss'],
    system_notifications: ['maintenance', 'security_alert']
  }
}

const saveNotificationSettings = async () => {
  try {
    notificationLoading.value = true
    
    // 这里调用保存通知设置的API
    // await userApi.updateNotificationSettings(notificationSettings.value)
    
    ElMessage.success('通知设置保存成功')
    
  } catch (error: any) {
    ElMessage.error(error.message || '保存通知设置失败')
  } finally {
    notificationLoading.value = false
  }
}

const handleClose = () => {
  dialogVisible.value = false
}
</script>

<style scoped>
.form-tip {
  font-size: 12px;
  color: #999;
  margin-top: 5px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #eee;
}

.security-section {
  margin-bottom: 30px;
}

.security-section h4 {
  margin: 0 0 15px 0;
  font-size: 16px;
  font-weight: 600;
}

.two-factor-auth {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  background: var(--el-bg-color-page);
  border-radius: 6px;
  margin-bottom: 10px;
}

.auth-status {
  display: flex;
  align-items: center;
  gap: 8px;
}

.auth-status .enabled {
  color: #67C23A;
}

.auth-status .disabled {
  color: #F56C6C;
}

.device-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.device-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  background: var(--el-bg-color-page);
  border-radius: 6px;
}

.device-info {
  flex: 1;
}

.device-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  margin-bottom: 5px;
}

.device-details {
  display: flex;
  gap: 15px;
  font-size: 13px;
  color: #666;
}

.device-actions {
  display: flex;
  align-items: center;
}
</style>