<template>
  <div class="settings-container">
    <div class="page-header">
      <h1 class="page-title">⚙️ 系统设置</h1>
      <p class="page-description">配置和管理您的交易平台</p>
    </div>

    <!-- 设置分类 -->
    <div class="settings-nav">
      <div class="nav-tabs">
        <button 
          v-for="tab in settingsTabs" 
          :key="tab.id"
          class="nav-tab"
          :class="{ active: activeTab === tab.id }"
          @click="activeTab = tab.id"
        >
          <span class="tab-icon">{{ tab.icon }}</span>
          <span class="tab-label">{{ tab.label }}</span>
        </button>
      </div>
    </div>

    <!-- 账户设置 -->
    <div v-if="activeTab === 'account'" class="settings-section">
      <h3>👤 账户设置</h3>
      <div class="settings-grid">
        <div class="setting-card">
          <div class="setting-header">
            <h4>基本信息</h4>
            <button class="edit-btn" @click="editProfile">✏️ 编辑</button>
          </div>
          <div class="setting-content">
            <div class="info-item">
              <span class="label">用户名:</span>
              <span class="value">{{ userProfile.username }}</span>
            </div>
            <div class="info-item">
              <span class="label">邮箱:</span>
              <span class="value">{{ userProfile.email }}</span>
            </div>
            <div class="info-item">
              <span class="label">注册时间:</span>
              <span class="value">{{ userProfile.registerTime }}</span>
            </div>
            <div class="info-item">
              <span class="label">最后登录:</span>
              <span class="value">{{ userProfile.lastLogin }}</span>
            </div>
          </div>
        </div>

        <div class="setting-card">
          <div class="setting-header">
            <h4>安全设置</h4>
          </div>
          <div class="setting-content">
            <div class="setting-item">
              <div class="setting-info">
                <span class="setting-name">修改密码</span>
                <span class="setting-desc">定期修改密码以保护账户安全</span>
              </div>
              <button class="action-btn" @click="changePassword">修改</button>
            </div>
            <div class="setting-item">
              <div class="setting-info">
                <span class="setting-name">双因素认证</span>
                <span class="setting-desc">启用2FA增强账户安全性</span>
              </div>
              <button class="action-btn" @click="setup2FA">设置</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 交易设置 -->
    <div v-if="activeTab === 'trading'" class="settings-section">
      <h3>📈 交易设置</h3>
      <div class="settings-grid">
        <div class="setting-card">
          <div class="setting-header">
            <h4>风险控制</h4>
          </div>
          <div class="setting-content">
            <div class="setting-item">
              <div class="setting-info">
                <span class="setting-name">最大持仓比例</span>
                <span class="setting-desc">单个品种最大持仓占总资金比例</span>
              </div>
              <div class="setting-control">
                <input v-model="tradingSettings.maxPositionRatio" type="number" min="1" max="100">
                <span>%</span>
              </div>
            </div>
            <div class="setting-item">
              <div class="setting-info">
                <span class="setting-name">止损比例</span>
                <span class="setting-desc">默认止损比例设置</span>
              </div>
              <div class="setting-control">
                <input v-model="tradingSettings.stopLossRatio" type="number" min="1" max="50">
                <span>%</span>
              </div>
            </div>
            <div class="setting-item">
              <div class="setting-info">
                <span class="setting-name">止盈比例</span>
                <span class="setting-desc">默认止盈比例设置</span>
              </div>
              <div class="setting-control">
                <input v-model="tradingSettings.takeProfitRatio" type="number" min="1" max="100">
                <span>%</span>
              </div>
            </div>
          </div>
        </div>

        <div class="setting-card">
          <div class="setting-header">
            <h4>交易偏好</h4>
          </div>
          <div class="setting-content">
            <div class="setting-item">
              <div class="setting-info">
                <span class="setting-name">确认订单</span>
                <span class="setting-desc">下单前显示确认对话框</span>
              </div>
              <div class="setting-control">
                <label class="switch">
                  <input v-model="tradingSettings.confirmOrders" type="checkbox">
                  <span class="slider"></span>
                </label>
              </div>
            </div>
            <div class="setting-item">
              <div class="setting-info">
                <span class="setting-name">声音提醒</span>
                <span class="setting-desc">交易成功时播放提示音</span>
              </div>
              <div class="setting-control">
                <label class="switch">
                  <input v-model="tradingSettings.soundAlerts" type="checkbox">
                  <span class="slider"></span>
                </label>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 通知设置 -->
    <div v-if="activeTab === 'notifications'" class="settings-section">
      <h3>🔔 通知设置</h3>
      <div class="settings-grid">
        <div class="setting-card">
          <div class="setting-header">
            <h4>推送通知</h4>
          </div>
          <div class="setting-content">
            <div class="setting-item">
              <div class="setting-info">
                <span class="setting-name">交易通知</span>
                <span class="setting-desc">订单成交、平仓等交易相关通知</span>
              </div>
              <div class="setting-control">
                <label class="switch">
                  <input v-model="notificationSettings.trading" type="checkbox">
                  <span class="slider"></span>
                </label>
              </div>
            </div>
            <div class="setting-item">
              <div class="setting-info">
                <span class="setting-name">价格提醒</span>
                <span class="setting-desc">价格达到设定值时的提醒</span>
              </div>
              <div class="setting-control">
                <label class="switch">
                  <input v-model="notificationSettings.priceAlert" type="checkbox">
                  <span class="slider"></span>
                </label>
              </div>
            </div>
            <div class="setting-item">
              <div class="setting-info">
                <span class="setting-name">系统通知</span>
                <span class="setting-desc">系统维护、更新等通知</span>
              </div>
              <div class="setting-control">
                <label class="switch">
                  <input v-model="notificationSettings.system" type="checkbox">
                  <span class="slider"></span>
                </label>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 系统设置 -->
    <div v-if="activeTab === 'system'" class="settings-section">
      <h3>🖥️ 系统设置</h3>
      <div class="settings-grid">
        <div class="setting-card">
          <div class="setting-header">
            <h4>界面设置</h4>
          </div>
          <div class="setting-content">
            <div class="setting-item">
              <div class="setting-info">
                <span class="setting-name">主题模式</span>
                <span class="setting-desc">选择浅色或深色主题</span>
              </div>
              <div class="setting-control">
                <select v-model="systemSettings.theme">
                  <option value="light">浅色主题</option>
                  <option value="dark">深色主题</option>
                  <option value="auto">跟随系统</option>
                </select>
              </div>
            </div>
            <div class="setting-item">
              <div class="setting-info">
                <span class="setting-name">语言设置</span>
                <span class="setting-desc">选择界面显示语言</span>
              </div>
              <div class="setting-control">
                <select v-model="systemSettings.language">
                  <option value="zh-CN">简体中文</option>
                  <option value="en-US">English</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        <div class="setting-card">
          <div class="setting-header">
            <h4>数据管理</h4>
          </div>
          <div class="setting-content">
            <div class="setting-item">
              <div class="setting-info">
                <span class="setting-name">导出数据</span>
                <span class="setting-desc">导出您的交易数据和设置</span>
              </div>
              <button class="action-btn" @click="exportData">导出</button>
            </div>
            <div class="setting-item">
              <div class="setting-info">
                <span class="setting-name">清除缓存</span>
                <span class="setting-desc">清除本地缓存数据</span>
              </div>
              <button class="action-btn" @click="clearCache">清除</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 保存按钮 -->
    <div class="save-section">
      <button class="save-btn" @click="saveSettings">
        💾 保存设置
      </button>
      <button class="reset-btn" @click="resetSettings">
        🔄 重置默认
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'

// 响应式数据
const activeTab = ref('account')

// 设置标签页
const settingsTabs = ref([
  { id: 'account', label: '账户设置', icon: '👤' },
  { id: 'trading', label: '交易设置', icon: '📈' },
  { id: 'notifications', label: '通知设置', icon: '🔔' },
  { id: 'system', label: '系统设置', icon: '🖥️' }
])

// 用户资料
const userProfile = reactive({
  username: 'admin',
  email: 'admin@example.com',
  registerTime: '2024-01-15',
  lastLogin: '2025-08-05 14:30:00'
})

// 交易设置
const tradingSettings = reactive({
  maxPositionRatio: 20,
  stopLossRatio: 5,
  takeProfitRatio: 15,
  confirmOrders: true,
  soundAlerts: true
})

// 通知设置
const notificationSettings = reactive({
  trading: true,
  priceAlert: true,
  system: false
})

// 系统设置
const systemSettings = reactive({
  theme: 'light',
  language: 'zh-CN'
})

// 页面操作
const editProfile = () => {
  console.log('✏️ 编辑用户资料')
  alert('编辑用户资料功能开发中...')
}

const changePassword = () => {
  console.log('🔒 修改密码')
  alert('修改密码功能开发中...')
}

const setup2FA = () => {
  console.log('🔐 设置双因素认证')
  alert('双因素认证设置功能开发中...')
}

const exportData = () => {
  console.log('📤 导出数据')
  alert('数据导出功能开发中...')
}

const clearCache = () => {
  console.log('🗑️ 清除缓存')
  if (confirm('确定要清除所有缓存数据吗？')) {
    alert('缓存已清除')
  }
}

const saveSettings = () => {
  console.log('💾 保存设置')
  console.log('交易设置:', tradingSettings)
  console.log('通知设置:', notificationSettings)
  console.log('系统设置:', systemSettings)
  alert('设置已保存')
}

const resetSettings = () => {
  console.log('🔄 重置设置')
  if (confirm('确定要重置所有设置为默认值吗？')) {
    // 重置为默认值
    tradingSettings.maxPositionRatio = 20
    tradingSettings.stopLossRatio = 5
    tradingSettings.takeProfitRatio = 15
    tradingSettings.confirmOrders = true
    tradingSettings.soundAlerts = true
    
    notificationSettings.trading = true
    notificationSettings.priceAlert = true
    notificationSettings.system = false
    
    systemSettings.theme = 'light'
    systemSettings.language = 'zh-CN'
    
    alert('设置已重置为默认值')
  }
}

// 生命周期
onMounted(() => {
  console.log('⚙️ 系统设置页面已加载')
})
</script>

<style scoped>
.settings-container {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
  background: #f8f9fa;
  min-height: 100vh;
}

.page-header {
  margin-bottom: 32px;
  text-align: center;
}

.page-title {
  margin: 0 0 8px 0;
  font-size: 32px;
  font-weight: 700;
  color: #2c3e50;
  text-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.page-description {
  margin: 0;
  font-size: 18px;
  color: #7f8c8d;
}

/* 设置导航 */
.settings-nav {
  background: white;
  border-radius: 12px;
  padding: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border: 1px solid #e9ecef;
  margin-bottom: 32px;
}

.nav-tabs {
  display: flex;
  gap: 4px;
}

.nav-tab {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 16px;
  background: transparent;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 14px;
  font-weight: 500;
  color: #7f8c8d;
}

.nav-tab:hover {
  background: #f8f9fa;
  color: #2c3e50;
}

.nav-tab.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

.tab-icon {
  font-size: 16px;
}

.tab-label {
  font-weight: 500;
}

/* 设置区域 */
.settings-section {
  margin-bottom: 32px;
}

.settings-section h3 {
  margin: 0 0 24px 0;
  font-size: 20px;
  font-weight: 600;
  color: #2c3e50;
  padding-bottom: 12px;
  border-bottom: 2px solid #ecf0f1;
}

.settings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 24px;
}

.setting-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border: 1px solid #e9ecef;
  transition: all 0.3s ease;
}

.setting-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.setting-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid #ecf0f1;
}

.setting-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
}

.edit-btn {
  background: #6c757d;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.edit-btn:hover {
  background: #5a6268;
  transform: translateY(-1px);
}

.setting-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 信息项 */
.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f8f9fa;
}

.info-item:last-child {
  border-bottom: none;
}

.info-item .label {
  font-weight: 500;
  color: #7f8c8d;
  font-size: 14px;
}

.info-item .value {
  font-weight: 600;
  color: #2c3e50;
  font-size: 14px;
}

/* 设置项 */
.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0;
  border-bottom: 1px solid #f8f9fa;
}

.setting-item:last-child {
  border-bottom: none;
}

.setting-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.setting-name {
  font-weight: 600;
  color: #2c3e50;
  font-size: 14px;
}

.setting-desc {
  font-size: 12px;
  color: #7f8c8d;
  line-height: 1.4;
}

.setting-control {
  display: flex;
  align-items: center;
  gap: 8px;
}

.setting-control input[type="number"] {
  width: 80px;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  text-align: center;
}

.setting-control select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  background: white;
  min-width: 120px;
}

.action-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.action-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

/* 开关样式 */
.switch {
  position: relative;
  display: inline-block;
  width: 50px;
  height: 24px;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #ccc;
  transition: .4s;
  border-radius: 24px;
}

.slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: .4s;
  border-radius: 50%;
}

input:checked + .slider {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

input:checked + .slider:before {
  transform: translateX(26px);
}

/* 保存区域 */
.save-section {
  display: flex;
  justify-content: center;
  gap: 16px;
  padding: 32px 0;
  border-top: 2px solid #ecf0f1;
  margin-top: 32px;
}

.save-btn {
  background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
  color: white;
  border: none;
  padding: 16px 32px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 16px;
  font-weight: 600;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}

.save-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(40, 167, 69, 0.3);
}

.reset-btn {
  background: #6c757d;
  color: white;
  border: none;
  padding: 16px 32px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 16px;
  font-weight: 600;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}

.reset-btn:hover {
  background: #5a6268;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(108, 117, 125, 0.3);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .settings-container {
    padding: 16px;
  }
  
  .nav-tabs {
    flex-direction: column;
  }
  
  .nav-tab {
    justify-content: flex-start;
  }
  
  .settings-grid {
    grid-template-columns: 1fr;
  }
  
  .setting-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .setting-control {
    align-self: flex-end;
  }
  
  .save-section {
    flex-direction: column;
    align-items: center;
  }
  
  .save-btn, .reset-btn {
    width: 100%;
    max-width: 300px;
    justify-content: center;
  }
  
  .page-title {
    font-size: 24px;
  }
  
  .page-description {
    font-size: 16px;
  }
}

@media (max-width: 480px) {
  .setting-card {
    padding: 16px;
  }
  
  .nav-tab {
    padding: 10px 12px;
    font-size: 12px;
  }
  
  .tab-icon {
    font-size: 14px;
  }
  
  .setting-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}
</style>