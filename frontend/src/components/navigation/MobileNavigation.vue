<template>
  <div class="mobile-navigation">
    <!-- 顶部导航栏 -->
    <div class="mobile-header" :class="{ 'header-scrolled': isScrolled }">
      <div class="header-content">
        <!-- 左侧菜单按钮 -->
        <el-button
          type="text"
          class="menu-button"
          @click="toggleSidebar"
        >
          <el-icon :size="20"><Menu /></el-icon>
        </el-button>

        <!-- 中间标题 -->
        <div class="header-title">
          <h1>{{ currentPageTitle }}</h1>
        </div>

        <!-- 右侧操作按钮 -->
        <div class="header-actions">
          <!-- 搜索按钮 -->
          <el-button
            v-if="showSearch"
            type="text"
            class="action-button"
            @click="toggleSearch"
          >
            <el-icon :size="18"><Search /></el-icon>
          </el-button>

          <!-- 通知按钮 -->
          <el-button
            v-if="showNotifications"
            type="text"
            class="action-button"
            @click="showNotificationDrawer"
          >
            <el-badge :value="notificationCount" :hidden="notificationCount === 0">
              <el-icon :size="18"><Bell /></el-icon>
            </el-badge>
          </el-button>

          <!-- 用户头像 -->
          <el-dropdown
            v-if="showUserMenu"
            trigger="click"
            @command="handleUserMenuCommand"
          >
            <div class="user-avatar">
              <el-avatar :size="32" :src="userInfo?.avatar">
                {{ userInfo?.name?.charAt(0) || 'U' }}
              </el-avatar>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">
                  <el-icon><User /></el-icon>
                  个人中心
                </el-dropdown-item>
                <el-dropdown-item command="settings">
                  <el-icon><Setting /></el-icon>
                  设置
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <el-icon><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>

      <!-- 搜索栏 -->
      <div v-if="searchVisible" class="search-bar">
        <el-input
          ref="searchInputRef"
          v-model="searchQuery"
          placeholder="搜索..."
          clearable
          @keyup.enter="handleSearch"
          @blur="handleSearchBlur"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>
    </div>

    <!-- 侧边栏 -->
    <el-drawer
      v-model="sidebarVisible"
      direction="ltr"
      :size="280"
      :with-header="false"
      :modal="true"
      class="mobile-sidebar"
    >
      <div class="sidebar-content">
        <!-- 用户信息 -->
        <div class="sidebar-user-info">
          <el-avatar :size="60" :src="userInfo?.avatar">
            {{ userInfo?.name?.charAt(0) || 'U' }}
          </el-avatar>
          <div class="user-details">
            <div class="user-name">{{ userInfo?.name || '未登录' }}</div>
            <div class="user-role">{{ userInfo?.role || '访客' }}</div>
          </div>
        </div>

        <!-- 导航菜单 -->
        <div class="sidebar-menu">
          <el-menu
            :default-active="activeMenu"
            mode="vertical"
            :collapse="false"
            @select="handleMenuSelect"
          >
            <template v-for="item in menuItems" :key="item.path">
              <!-- 有子菜单的项 -->
              <el-sub-menu
                v-if="item.children && item.children.length > 0"
                :index="item.path"
              >
                <template #title>
                  <el-icon v-if="item.icon">
                    <component :is="item.icon" />
                  </el-icon>
                  <span>{{ item.title }}</span>
                </template>
                <el-menu-item
                  v-for="child in item.children"
                  :key="child.path"
                  :index="child.path"
                >
                  <el-icon v-if="child.icon">
                    <component :is="child.icon" />
                  </el-icon>
                  <span>{{ child.title }}</span>
                </el-menu-item>
              </el-sub-menu>

              <!-- 普通菜单项 -->
              <el-menu-item v-else :index="item.path">
                <el-icon v-if="item.icon">
                  <component :is="item.icon" />
                </el-icon>
                <span>{{ item.title }}</span>
              </el-menu-item>
            </template>
          </el-menu>
        </div>

        <!-- 底部操作 -->
        <div class="sidebar-footer">
          <el-button type="text" @click="toggleTheme">
            <el-icon><Moon /></el-icon>
            {{ isDark ? '浅色模式' : '深色模式' }}
          </el-button>
        </div>
      </div>
    </el-drawer>

    <!-- 底部导航栏 -->
    <div v-if="showBottomNav" class="bottom-navigation">
      <div class="bottom-nav-content">
        <div
          v-for="item in bottomNavItems"
          :key="item.path"
          class="bottom-nav-item"
          :class="{ active: activeBottomNav === item.path }"
          @click="handleBottomNavClick(item)"
        >
          <el-icon :size="20">
            <component :is="item.icon" />
          </el-icon>
          <span class="nav-label">{{ item.title }}</span>
          <el-badge
            v-if="item.badge"
            :value="item.badge"
            :hidden="item.badge === 0"
            class="nav-badge"
          />
        </div>
      </div>
    </div>

    <!-- 通知抽屉 -->
    <el-drawer
      v-model="notificationDrawerVisible"
      direction="rtl"
      title="通知"
      :size="320"
    >
      <div class="notification-list">
        <div
          v-for="notification in notifications"
          :key="notification.id"
          class="notification-item"
          :class="{ unread: !notification.read }"
          @click="handleNotificationClick(notification)"
        >
          <div class="notification-icon">
            <el-icon :color="getNotificationColor(notification.type)">
              <component :is="getNotificationIcon(notification.type)" />
            </el-icon>
          </div>
          <div class="notification-content">
            <div class="notification-title">{{ notification.title }}</div>
            <div class="notification-message">{{ notification.message }}</div>
            <div class="notification-time">{{ formatTime(notification.time) }}</div>
          </div>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  Menu,
  Search,
  Bell,
  User,
  Setting,
  SwitchButton,
  Moon,
  Dashboard,
  TrendCharts,
  Monitor,
  DataAnalysis,
  Warning,
  Wallet,
  Document,
  List,
  Plus,
  Collection,
  Calendar,
  ChatDotRound,
  InfoFilled,
  WarningFilled,
  SuccessFilled,
  CircleCloseFilled
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'
import { useNotificationStore } from '@/stores/notification'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'

interface MenuItem {
  path: string
  title: string
  icon?: any
  children?: MenuItem[]
  badge?: number
}

interface BottomNavItem {
  path: string
  title: string
  icon: any
  badge?: number
}

interface Notification {
  id: string
  type: 'info' | 'success' | 'warning' | 'error'
  title: string
  message: string
  time: string
  read: boolean
}

const props = defineProps<{
  showSearch?: boolean
  showNotifications?: boolean
  showUserMenu?: boolean
  showBottomNav?: boolean
}>()

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const themeStore = useThemeStore()
const notificationStore = useNotificationStore()

// 响应式状态
const sidebarVisible = ref(false)
const searchVisible = ref(false)
const searchQuery = ref('')
const notificationDrawerVisible = ref(false)
const isScrolled = ref(false)
const searchInputRef = ref()

// 计算属性
const userInfo = computed(() => authStore.user)
const isDark = computed(() => themeStore.isDark)
const notifications = computed(() => notificationStore.notifications)
const notificationCount = computed(() => notificationStore.unreadCount)

// 当前页面标题
const currentPageTitle = computed(() => {
  return route.meta.title as string || '量化交易平台'
})

// 当前激活的菜单
const activeMenu = computed(() => route.path)

// 当前激活的底部导航
const activeBottomNav = computed(() => {
  const path = route.path
  if (path.startsWith('/trading')) return '/trading'
  if (path.startsWith('/strategies')) return '/strategies'
  if (path.startsWith('/backtests')) return '/backtests'
  if (path.startsWith('/market')) return '/market'
  return '/'
})

// 菜单项配置
const menuItems: MenuItem[] = [
  {
    path: '/',
    title: '仪表板',
    icon: Dashboard
  },
  {
    path: '/trading',
    title: '交易',
    icon: TrendCharts,
    children: [
      { path: '/trading', title: '交易面板', icon: Monitor },
      { path: '/trading/manual', title: '手动交易', icon: Plus },
      { path: '/trading/quick', title: '快速交易', icon: TrendCharts }
    ]
  },
  {
    path: '/strategies',
    title: '策略',
    icon: List,
    children: [
      { path: '/strategies', title: '策略列表', icon: List },
      { path: '/strategies/create', title: '创建策略', icon: Plus },
      { path: '/strategies/templates', title: '策略模板', icon: Collection }
    ]
  },
  {
    path: '/backtests',
    title: '回测',
    icon: DataAnalysis,
    children: [
      { path: '/backtests', title: '回测列表', icon: List },
      { path: '/backtests/create', title: '创建回测', icon: Plus },
      { path: '/backtests/comparison', title: '回测对比', icon: DataAnalysis }
    ]
  },
  {
    path: '/orders',
    title: '订单',
    icon: Document
  },
  {
    path: '/positions',
    title: '持仓',
    icon: Wallet
  },
  {
    path: '/accounts',
    title: '账户',
    icon: User
  },
  {
    path: '/risk',
    title: '风控',
    icon: Warning
  },
  {
    path: '/market',
    title: '行情',
    icon: Monitor,
    children: [
      { path: '/market', title: '实时行情', icon: TrendCharts },
      { path: '/market/technical', title: '技术分析', icon: DataAnalysis },
      { path: '/market/news', title: '市场资讯', icon: ChatDotRound },
      { path: '/market/calendar', title: '财经日历', icon: Calendar }
    ]
  }
]

// 底部导航项配置
const bottomNavItems: BottomNavItem[] = [
  {
    path: '/',
    title: '首页',
    icon: Dashboard
  },
  {
    path: '/trading',
    title: '交易',
    icon: TrendCharts
  },
  {
    path: '/strategies',
    title: '策略',
    icon: List
  },
  {
    path: '/market',
    title: '行情',
    icon: Monitor
  }
]

// 方法
const toggleSidebar = () => {
  sidebarVisible.value = !sidebarVisible.value
}

const toggleSearch = async () => {
  searchVisible.value = !searchVisible.value
  if (searchVisible.value) {
    await nextTick()
    searchInputRef.value?.focus()
  }
}

const handleSearch = () => {
  if (searchQuery.value.trim()) {
    // 执行搜索逻辑
    ElMessage.success(`搜索: ${searchQuery.value}`)
    searchVisible.value = false
    searchQuery.value = ''
  }
}

const handleSearchBlur = () => {
  setTimeout(() => {
    searchVisible.value = false
  }, 200)
}

const showNotificationDrawer = () => {
  notificationDrawerVisible.value = true
}

const handleUserMenuCommand = (command: string) => {
  switch (command) {
    case 'profile':
      router.push('/profile')
      break
    case 'settings':
      router.push('/settings')
      break
    case 'logout':
      authStore.logout()
      router.push('/login')
      break
  }
}

const handleMenuSelect = (path: string) => {
  router.push(path)
  sidebarVisible.value = false
}

const handleBottomNavClick = (item: BottomNavItem) => {
  router.push(item.path)
}

const toggleTheme = () => {
  themeStore.toggleTheme()
}

const handleNotificationClick = (notification: Notification) => {
  // 标记为已读
  notificationStore.markAsRead(notification.id)
  // 处理通知点击逻辑
  ElMessage.info(`点击了通知: ${notification.title}`)
}

const getNotificationIcon = (type: string) => {
  switch (type) {
    case 'success':
      return SuccessFilled
    case 'warning':
      return WarningFilled
    case 'error':
      return CircleCloseFilled
    default:
      return InfoFilled
  }
}

const getNotificationColor = (type: string) => {
  switch (type) {
    case 'success':
      return '#67C23A'
    case 'warning':
      return '#E6A23C'
    case 'error':
      return '#F56C6C'
    default:
      return '#409EFF'
  }
}

const formatTime = (time: string) => {
  return dayjs(time).fromNow()
}

// 滚动监听
const handleScroll = () => {
  isScrolled.value = window.scrollY > 10
}

// 监听路由变化，关闭侧边栏
watch(() => route.path, () => {
  sidebarVisible.value = false
})

onMounted(() => {
  window.addEventListener('scroll', handleScroll)
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})
</script>

<style lang="scss" scoped>
.mobile-navigation {
  position: relative;
  z-index: 1000;
}

// 顶部导航栏
.mobile-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color-lighter);
  z-index: 1001;
  transition: all 0.3s ease;
  
  &.header-scrolled {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }
  
  .header-content {
    display: flex;
    align-items: center;
    height: 56px;
    padding: 0 16px;
  }
  
  .menu-button {
    margin-right: 12px;
    color: var(--el-text-color-primary);
  }
  
  .header-title {
    flex: 1;
    
    h1 {
      margin: 0;
      font-size: 18px;
      font-weight: 600;
      color: var(--el-text-color-primary);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
  }
  
  .header-actions {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  .action-button {
    color: var(--el-text-color-primary);
    min-width: 40px;
    height: 40px;
  }
  
  .user-avatar {
    cursor: pointer;
  }
  
  .search-bar {
    padding: 8px 16px 12px;
    border-top: 1px solid var(--el-border-color-lighter);
  }
}

// 侧边栏
.mobile-sidebar {
  :deep(.el-drawer__body) {
    padding: 0;
  }
  
  .sidebar-content {
    height: 100%;
    display: flex;
    flex-direction: column;
  }
  
  .sidebar-user-info {
    padding: 24px 20px;
    background: var(--el-color-primary-light-9);
    display: flex;
    align-items: center;
    gap: 16px;
    
    .user-details {
      flex: 1;
      
      .user-name {
        font-size: 16px;
        font-weight: 600;
        color: var(--el-text-color-primary);
        margin-bottom: 4px;
      }
      
      .user-role {
        font-size: 14px;
        color: var(--el-text-color-secondary);
      }
    }
  }
  
  .sidebar-menu {
    flex: 1;
    overflow-y: auto;
    
    :deep(.el-menu) {
      border: none;
      
      .el-menu-item,
      .el-sub-menu__title {
        height: 48px;
        line-height: 48px;
        padding-left: 20px !important;
        
        .el-icon {
          margin-right: 12px;
          width: 20px;
        }
      }
      
      .el-sub-menu .el-menu-item {
        padding-left: 52px !important;
      }
    }
  }
  
  .sidebar-footer {
    padding: 16px 20px;
    border-top: 1px solid var(--el-border-color-lighter);
    
    .el-button {
      width: 100%;
      justify-content: flex-start;
      
      .el-icon {
        margin-right: 8px;
      }
    }
  }
}

// 底部导航栏
.bottom-navigation {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: var(--el-bg-color);
  border-top: 1px solid var(--el-border-color-lighter);
  z-index: 1001;
  
  .bottom-nav-content {
    display: flex;
    height: 60px;
  }
  
  .bottom-nav-item {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    position: relative;
    transition: all 0.3s ease;
    
    &:hover {
      background: var(--el-fill-color-light);
    }
    
    &.active {
      color: var(--el-color-primary);
      
      .nav-label {
        color: var(--el-color-primary);
      }
    }
    
    .nav-label {
      font-size: 12px;
      margin-top: 4px;
      color: var(--el-text-color-secondary);
      transition: color 0.3s ease;
    }
    
    .nav-badge {
      position: absolute;
      top: 8px;
      right: 50%;
      transform: translateX(10px);
    }
  }
}

// 通知列表
.notification-list {
  .notification-item {
    display: flex;
    padding: 16px;
    border-bottom: 1px solid var(--el-border-color-lighter);
    cursor: pointer;
    transition: background-color 0.3s ease;
    
    &:hover {
      background: var(--el-fill-color-light);
    }
    
    &.unread {
      background: var(--el-color-primary-light-9);
      
      &::before {
        content: '';
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        width: 3px;
        background: var(--el-color-primary);
      }
    }
    
    .notification-icon {
      margin-right: 12px;
      margin-top: 2px;
    }
    
    .notification-content {
      flex: 1;
      
      .notification-title {
        font-size: 14px;
        font-weight: 600;
        color: var(--el-text-color-primary);
        margin-bottom: 4px;
      }
      
      .notification-message {
        font-size: 13px;
        color: var(--el-text-color-secondary);
        margin-bottom: 8px;
        line-height: 1.4;
      }
      
      .notification-time {
        font-size: 12px;
        color: var(--el-text-color-placeholder);
      }
    }
  }
}

// 响应式优化
@media (max-width: 480px) {
  .mobile-header {
    .header-content {
      padding: 0 12px;
    }
    
    .header-title h1 {
      font-size: 16px;
    }
    
    .action-button {
      min-width: 36px;
      height: 36px;
    }
  }
  
  .bottom-navigation {
    .bottom-nav-item {
      .nav-label {
        font-size: 11px;
      }
    }
  }
}

// 横屏优化
@media (orientation: landscape) and (max-height: 500px) {
  .mobile-header {
    .header-content {
      height: 48px;
    }
  }
  
  .sidebar-user-info {
    padding: 16px 20px;
  }
  
  .bottom-navigation {
    .bottom-nav-content {
      height: 50px;
    }
  }
}

// 暗色主题优化
.dark {
  .mobile-header {
    &.header-scrolled {
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
    }
  }
  
  .sidebar-user-info {
    background: var(--el-color-primary-dark-2);
  }
}
</style>