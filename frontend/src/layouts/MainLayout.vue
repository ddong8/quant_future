<template>
  <el-container class="main-layout">
    <!-- 移动端遮罩 -->
    <div v-if="isMobile() && mobileMenuOpen" class="mobile-overlay" @click="closeMobileMenu"></div>

    <!-- 侧边栏 -->
    <el-aside
      :width="sidebarCollapsed ? '64px' : '260px'"
      class="sidebar"
      :class="{ 'mobile-open': mobileMenuOpen }"
    >
      <div class="logo-container">
        <div class="logo">
          <el-icon v-if="sidebarCollapsed" size="24">
            <TrendCharts />
          </el-icon>
          <template v-else>
            <el-icon size="24">
              <TrendCharts />
            </el-icon>
            <span class="logo-text">量化交易平台</span>
          </template>
        </div>
      </div>

      <el-menu
        :default-active="activeMenu"
        :collapse="sidebarCollapsed"
        :unique-opened="true"
        router
        class="sidebar-menu"
        @select="handleMenuSelect"
      >
        <template v-for="menuItem in menuRoutes" :key="menuItem.path">
          <!-- 没有子菜单的菜单项（如仪表板） -->
          <el-menu-item
            v-if="!menuItem.children || menuItem.children.length === 0"
            :index="menuItem.path"
            :disabled="!hasPermission(menuItem.meta?.roles)"
          >
            <el-icon v-if="menuItem.meta?.icon">
              <component :is="getIconComponent(menuItem.meta.icon)" />
            </el-icon>
            <template #title>{{ menuItem.meta?.title }}</template>
          </el-menu-item>

          <!-- 有子菜单的菜单项 -->
          <el-sub-menu
            v-else
            :index="menuItem.path"
            :disabled="!hasPermission(menuItem.meta?.roles)"
          >
            <template #title>
              <el-icon v-if="menuItem.meta?.icon">
                <component :is="getIconComponent(menuItem.meta.icon)" />
              </el-icon>
              <span>{{ menuItem.meta?.title }}</span>
            </template>

            <el-menu-item
              v-for="child in menuItem.children"
              :key="child.path"
              :index="child.path"
              :disabled="!hasPermission(child.meta?.roles)"
            >
              <el-icon v-if="child.meta?.icon">
                <component :is="getIconComponent(child.meta.icon)" />
              </el-icon>
              <template #title>{{ child.meta?.title }}</template>
            </el-menu-item>
          </el-sub-menu>
        </template>
      </el-menu>
    </el-aside>

    <el-container class="main-container">
      <!-- 顶部导航 -->
      <el-header class="header">
        <div class="header-left">
          <el-button text @click="toggleSidebar" class="sidebar-toggle">
            <el-icon :size="isMobile() ? 16 : 20">
              <Expand v-if="sidebarCollapsed || (isMobile() && !mobileMenuOpen)" />
              <Fold v-else />
            </el-icon>
          </el-button>

          <el-breadcrumb separator="/" class="breadcrumb">
            <el-breadcrumb-item v-for="item in breadcrumbs" :key="item.path" :to="item.path">
              {{ item.title }}
            </el-breadcrumb-item>
          </el-breadcrumb>
        </div>

        <div class="header-right">
          <!-- 主题切换 -->
          <el-button text @click="themeStore.toggleTheme()" class="theme-toggle">
            <el-icon :size="isMobile() ? 16 : 18">
              <Sunny v-if="themeStore.isDark" />
              <Moon v-else />
            </el-icon>
          </el-button>

          <!-- 通知 -->
          <el-badge :value="notificationCount" :hidden="notificationCount === 0">
            <el-button text class="notification-btn">
              <el-icon :size="isMobile() ? 16 : 18">
                <Bell />
              </el-icon>
            </el-button>
          </el-badge>

          <!-- 认证状态 -->
          <AuthStatus
            type="verification"
            :show-text="false"
            :show-tooltip="true"
            class="auth-status-indicator"
          />

          <!-- 用户菜单 -->
          <el-dropdown @command="handleUserCommand" class="user-dropdown">
            <div class="user-info">
              <UserAvatar
                :avatar-url="authStore.user?.avatar_url"
                :display-name="authStore.user?.full_name || authStore.userName"
                :size="isMobile() ? 28 : 32"
              />
              <span class="username">{{ authStore.userName }}</span>
              <el-icon class="dropdown-icon"><ArrowDown /></el-icon>
            </div>

            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">
                  <el-icon><User /></el-icon>
                  个人中心
                </el-dropdown-item>
                <el-dropdown-item command="settings" v-if="authStore.hasPermission('admin')">
                  <el-icon><Setting /></el-icon>
                  系统设置
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <el-icon><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <!-- 主内容区 -->
      <el-main class="main-content">
        <router-view v-slot="{ Component, route }">
          <transition name="fade" mode="out-in">
            <keep-alive :include="cachedViews">
              <component :is="Component" :key="route.path" />
            </keep-alive>
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed, ref, watch, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'
import {
  TrendCharts,
  Expand,
  Fold,
  Sunny,
  Moon,
  Bell,
  User,
  ArrowDown,
  Setting,
  SwitchButton,
  Odometer,
  List,
  Plus,
  Collection,
  DataAnalysis,
  DataBoard,
  Document,
  Monitor,
  Edit,
  Lightning,
  Clock,
  Wallet,
  Money,
  ChatDotRound,
  Calendar,
  Warning
} from '@element-plus/icons-vue'
import UserAvatar from '@/components/UserAvatar.vue'
import AuthStatus from '@/components/AuthStatus.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const themeStore = useThemeStore()

// 检查是否为移动端
const isMobile = () => window.innerWidth <= 768

// 侧边栏状态
const sidebarCollapsed = ref(false)
const mobileMenuOpen = ref(false)

// 初始化移动端状态
const initMobileState = () => {
  if (isMobile()) {
    sidebarCollapsed.value = true // 移动端默认折叠
    mobileMenuOpen.value = false // 移动端菜单默认关闭
  }
}

// 通知数量
const notificationCount = ref(0)

// 缓存的视图
const cachedViews = ref<string[]>([])

// 当前激活的菜单
const activeMenu = computed(() => route.path)

// 面包屑导航
const breadcrumbs = computed(() => {
  const matched = route.matched.filter((item) => item.meta?.title)
  return matched.map((item) => ({
    title: item.meta?.title,
    path: item.path
  }))
})

// 菜单路由
const menuRoutes = computed(() => {
  // 根据spec文档定义的核心功能模块构建菜单
  const menuStructure = [
    {
      path: '/',
      meta: { title: '仪表板', icon: 'Dashboard' },
      children: []
    },
    {
      path: '/strategies',
      meta: { title: '策略管理', icon: 'List' },
      children: [
        { path: '/strategies', meta: { title: '策略列表', icon: 'List' } },
        { path: '/strategies/create', meta: { title: '创建策略', icon: 'Plus' } },
        { path: '/strategies/templates', meta: { title: '策略模板', icon: 'Collection' } },
        { path: '/strategies/performance', meta: { title: '策略绩效', icon: 'TrendCharts' } }
      ]
    },
    {
      path: '/backtests',
      meta: { title: '回测系统', icon: 'DataAnalysis' },
      children: [
        { path: '/backtests', meta: { title: '回测列表', icon: 'List' } },
        { path: '/backtests/create', meta: { title: '创建回测', icon: 'Plus' } },
        { path: '/backtests/comparison', meta: { title: '回测对比', icon: 'DataBoard' } },
        { path: '/backtests/reports', meta: { title: '回测报告', icon: 'Document' } }
      ]
    },
    {
      path: '/trading',
      meta: { title: '交易中心', icon: 'Monitor' },
      children: [
        { path: '/trading', meta: { title: '交易面板', icon: 'Monitor' } },
        { path: '/trading/manual', meta: { title: '手动交易', icon: 'Edit' } },
        { path: '/trading/quick', meta: { title: '快速交易', icon: 'Lightning' } }
      ]
    },
    {
      path: '/orders',
      meta: { title: '订单管理', icon: 'Document' },
      children: [
        { path: '/orders', meta: { title: '订单列表', icon: 'Document' } },
        { path: '/orders/history', meta: { title: '历史订单', icon: 'Clock' } },
        { path: '/orders/templates', meta: { title: '订单模板', icon: 'Collection' } }
      ]
    },
    {
      path: '/positions',
      meta: { title: '持仓管理', icon: 'Wallet' },
      children: [
        { path: '/positions', meta: { title: '当前持仓', icon: 'Wallet' } },
        { path: '/positions/history', meta: { title: '持仓历史', icon: 'Clock' } },
        { path: '/positions/analysis', meta: { title: '持仓分析', icon: 'DataAnalysis' } }
      ]
    },
    {
      path: '/accounts',
      meta: { title: '账户管理', icon: 'User' },
      children: [
        { path: '/accounts', meta: { title: '账户概览', icon: 'User' } },
        { path: '/account/transactions', meta: { title: '资金流水', icon: 'Money' } }
      ]
    },
    {
      path: '/market',
      meta: { title: '市场数据', icon: 'TrendCharts' },
      children: [
        { path: '/market', meta: { title: '实时行情', icon: 'TrendCharts' } },
        { path: '/market/technical', meta: { title: '技术分析', icon: 'DataAnalysis' } },
        { path: '/market/news', meta: { title: '市场资讯', icon: 'ChatDotRound' } },
        { path: '/market/calendar', meta: { title: '财经日历', icon: 'Calendar' } }
      ]
    },
    {
      path: '/risk',
      meta: { title: '风险控制', icon: 'Warning' },
      children: [
        { path: '/risk', meta: { title: '风险监控', icon: 'Warning' } },
        { path: '/risk/rules', meta: { title: '风险规则', icon: 'Setting' } },
        { path: '/risk/reports', meta: { title: '风险报告', icon: 'Document' } }
      ]
    },
    {
      path: '/settings',
      meta: { title: '系统设置', icon: 'Setting' },
      children: [
        { path: '/settings', meta: { title: '通用设置', icon: 'Setting' } },
        { path: '/settings/account', meta: { title: '账户设置', icon: 'User' } },
        { path: '/settings/trading', meta: { title: '交易设置', icon: 'TrendCharts' } },
        { path: '/settings/notifications', meta: { title: '通知设置', icon: 'Bell' } }
      ]
    }
  ]

  // 过滤掉没有对应路由的菜单项
  const allRoutes = router.getRoutes()
  const routePaths = new Set(allRoutes.map((route) => route.path))

  return menuStructure.filter((menu) => {
    // 过滤子菜单，只保留存在的路由
    if (menu.children && menu.children.length > 0) {
      menu.children = menu.children.filter((child) => routePaths.has(child.path))
      return menu.children.length > 0 // 只有当有子菜单时才显示父菜单
    }
    return routePaths.has(menu.path) // 单独菜单项需要路由存在
  })
})

// 切换侧边栏
const toggleSidebar = () => {
  if (isMobile()) {
    mobileMenuOpen.value = !mobileMenuOpen.value
  } else {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }
}

// 关闭移动端菜单
const closeMobileMenu = () => {
  mobileMenuOpen.value = false
}

// 处理菜单选择
const handleMenuSelect = () => {
  // 在移动端点击菜单项后自动关闭菜单
  if (isMobile()) {
    closeMobileMenu()
  }
}

// 监听窗口大小变化
const handleResize = () => {
  if (isMobile()) {
    // 切换到移动端时
    sidebarCollapsed.value = true
    mobileMenuOpen.value = false
  } else {
    // 切换到桌面端时关闭移动端菜单
    mobileMenuOpen.value = false
    sidebarCollapsed.value = false
  }
}

// 图标组件映射
const iconComponents = {
  Dashboard: Odometer, // 使用Odometer代替Dashboard
  List,
  Plus,
  Collection,
  TrendCharts,
  DataAnalysis,
  DataBoard,
  Document,
  Monitor,
  Edit,
  Lightning,
  Clock,
  Wallet,
  Money,
  User,
  ChatDotRound,
  Calendar,
  Warning,
  Setting,
  Bell
}

// 获取图标组件
const getIconComponent = (iconName: string) => {
  return iconComponents[iconName as keyof typeof iconComponents] || Document
}

// 检查权限
const hasPermission = (roles?: string[]) => {
  if (!roles || roles.length === 0) return true
  return authStore.hasPermission(roles)
}

// 处理用户菜单命令
const handleUserCommand = (command: string) => {
  switch (command) {
    case 'profile':
      router.push('/profile')
      break
    case 'settings':
      router.push('/settings')
      break
    case 'logout':
      authStore.logout().then(() => {
        router.push('/login')
      })
      break
  }
}

// 监听路由变化，更新缓存视图
watch(
  () => route.name,
  (newName) => {
    if (newName && typeof newName === 'string') {
      if (!cachedViews.value.includes(newName)) {
        cachedViews.value.push(newName)
      }
    }
  },
  { immediate: true }
)

// 组件挂载时初始化
onMounted(() => {
  // 初始化移动端状态
  initMobileState()

  // 添加窗口大小变化监听
  window.addEventListener('resize', handleResize)
})

// 组件卸载时清理
onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style lang="scss" scoped>
.main-layout {
  height: 100vh;
}

.sidebar {
  background: var(--el-bg-color);
  border-right: 1px solid var(--el-border-color-light);
  transition: width 0.3s ease;

  .logo-container {
    height: 64px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-bottom: 1px solid var(--el-border-color-lighter);
    padding: 0 20px;

    .logo {
      display: flex;
      align-items: center;
      gap: 14px;
      color: var(--el-color-primary);
      font-weight: 600;
      font-size: 17px;
      padding: 10px 16px;
      border-radius: 10px;
      transition: all 0.3s ease;
      cursor: pointer;
      width: 100%;
      justify-content: center;

      &:hover {
        background: var(--el-color-primary-light-9);
        transform: scale(1.02);
      }

      .el-icon {
        font-size: 26px;
        transition: all 0.3s ease;
      }

      .logo-text {
        white-space: nowrap;
        background: linear-gradient(
          135deg,
          var(--el-color-primary),
          var(--el-color-primary-light-3)
        );
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: 0.5px;
      }
    }
  }

  .sidebar-menu {
    border: none;
    height: calc(100vh - 60px);
    overflow-y: auto;

    // 美化菜单项样式
    :deep(.el-menu-item) {
      height: 52px;
      line-height: 52px;
      padding: 0 24px;
      margin: 3px 12px;
      border-radius: 10px;
      transition: all 0.3s ease;

      .el-icon {
        margin-right: 14px;
        font-size: 20px;
        width: 20px;
        text-align: center;
        transition: all 0.3s ease;
      }

      span {
        font-size: 15px;
        font-weight: 500;
        transition: all 0.3s ease;
        letter-spacing: 0.3px;
      }

      &:hover {
        background: var(--el-color-primary-light-9);
        color: var(--el-color-primary);

        .el-icon {
          color: var(--el-color-primary);
          transform: scale(1.1);
        }
      }

      &.is-active {
        background: var(--el-color-primary-light-8);
        color: var(--el-color-primary);
        font-weight: 600;

        .el-icon {
          color: var(--el-color-primary);
          transform: scale(1.1);
        }

        &::before {
          content: '';
          position: absolute;
          left: 0;
          top: 50%;
          transform: translateY(-50%);
          width: 3px;
          height: 24px;
          background: var(--el-color-primary);
          border-radius: 0 2px 2px 0;
        }
      }
    }

    // 子菜单样式
    :deep(.el-sub-menu) {
      margin: 3px 12px;
      border-radius: 10px;

      .el-sub-menu__title {
        height: 52px;
        line-height: 52px;
        padding: 0 24px;
        border-radius: 10px;
        transition: all 0.3s ease;

        .el-icon {
          margin-right: 14px;
          font-size: 20px;
          width: 20px;
          text-align: center;
          transition: all 0.3s ease;
        }

        span {
          font-size: 15px;
          font-weight: 500;
          letter-spacing: 0.3px;
        }

        .el-sub-menu__icon-arrow {
          margin-left: auto;
          transition: transform 0.3s ease;
        }

        &:hover {
          background: var(--el-color-primary-light-9);
          color: var(--el-color-primary);

          .el-icon {
            color: var(--el-color-primary);
            transform: scale(1.1);
          }
        }
      }

      &.is-opened {
        .el-sub-menu__title {
          background: var(--el-color-primary-light-9);
          color: var(--el-color-primary);

          .el-icon {
            color: var(--el-color-primary);
          }

          .el-sub-menu__icon-arrow {
            transform: rotateZ(180deg);
          }
        }
      }

      .el-menu {
        background: transparent;

        .el-menu-item {
          height: 44px;
          line-height: 44px;
          padding-left: 58px;
          margin: 2px 0;
          font-size: 14px;

          .el-icon {
            margin-right: 12px;
            font-size: 17px;
            width: 17px;
          }

          &:hover {
            background: var(--el-color-primary-light-9);
            color: var(--el-color-primary);
          }

          &.is-active {
            background: var(--el-color-primary-light-8);
            color: var(--el-color-primary);
            font-weight: 600;

            &::before {
              left: 8px;
              width: 2px;
              height: 16px;
            }
          }
        }
      }
    }

    // 折叠状态下的样式
    &.el-menu--collapse {
      .el-menu-item,
      .el-sub-menu .el-sub-menu__title {
        padding: 0;
        text-align: center;
        margin: 3px 8px;

        .el-icon {
          margin-right: 0;
          font-size: 22px;
        }

        span {
          display: none;
        }
      }

      .el-menu-item {
        &.is-active::before {
          left: 50%;
          transform: translate(-50%, -50%);
          width: 6px;
          height: 6px;
          border-radius: 50%;
          top: 10px;
        }
      }
    }
  }
}

.main-container {
  display: flex;
  flex-direction: column;
}

.header {
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color-light);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  height: 60px;

  .header-left {
    display: flex;
    align-items: center;
    gap: 16px;

    .sidebar-toggle {
      padding: 8px;
    }

    .breadcrumb {
      font-size: 14px;
    }
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 16px;

    .theme-toggle,
    .notification-btn {
      padding: 8px;
    }

    .auth-status-indicator {
      margin-right: 8px;
    }

    .user-dropdown {
      .user-info {
        display: flex;
        align-items: center;
        gap: 8px;
        cursor: pointer;
        padding: 4px 8px;
        border-radius: var(--el-border-radius-base);
        transition: background-color 0.3s;

        &:hover {
          background: var(--el-fill-color-light);
        }

        .username {
          font-size: 14px;
          color: var(--el-text-color-primary);
        }

        .dropdown-icon {
          font-size: 12px;
          color: var(--el-text-color-secondary);
        }
      }
    }
  }
}

.main-content {
  background: var(--el-bg-color-page);
  padding: 0;
  overflow: auto;
}

// 响应式设计
@media (max-width: 1024px) {
  .header {
    padding: 0 16px;
  }

  .header-left {
    gap: 12px;
  }

  .header-right {
    gap: 12px;

    .auth-status-indicator {
      display: none;
    }
  }
}

@media (max-width: 768px) {
  .main-layout {
    position: relative;
  }

  .sidebar {
    position: fixed;
    top: 0;
    left: 0;
    z-index: 1000;
    height: 100vh;
    width: 64px !important; // 移动端仅图标模式，与桌面端折叠宽度一致
    transform: translateX(-100%);
    transition: transform 0.3s ease;
    box-shadow: var(--el-box-shadow);

    &.mobile-open {
      transform: translateX(0);
    }

    .logo-container {
      padding: 0; // 移除内边距，logo居中
      height: 50px; // 与移动端头部高度保持一致

      .logo {
        justify-content: center; // logo居中
        padding: 8px; // 统一内边距
        
        .el-icon {
          font-size: 24px; // 增大logo图标以适应仅图标模式
        }

        .logo-text {
          display: none; // 移动端隐藏logo文字
        }
      }
    }

    .sidebar-menu {
      height: calc(100vh - 50px); // 调整为新的头部高度
      overflow-y: auto;
      -webkit-overflow-scrolling: touch; // 平滑滚动

      :deep(.el-menu-item),
      :deep(.el-sub-menu .el-sub-menu__title) {
        height: 48px;
        line-height: 48px;
        margin: 3px 8px; // 左右边距一致
        padding: 0; // 移除内边距，图标居中
        text-align: center; // 图标居中
        -webkit-tap-highlight-color: transparent; // 移除触摸高亮
        touch-action: manipulation; // 优化触摸响应

        .el-icon {
          font-size: 20px; // 增大图标以适应仅图标模式
          margin-right: 0; // 移除右边距
          width: 20px;
          text-align: center;
        }

        span {
          display: none; // 移动端隐藏文字，仅显示图标
        }

        // 移动端触摸反馈
        &:active {
          background: var(--el-color-primary-light-8);
          transform: scale(0.95);
          transition: all 0.1s ease;
        }
      }

      // 移动端仅图标模式，隐藏子菜单展开功能
      :deep(.el-sub-menu) {
        // 隐藏子菜单箭头
        .el-sub-menu__title {
          .el-sub-menu__icon-arrow {
            display: none;
          }
        }
        
        // 隐藏子菜单内容
        .el-menu {
          display: none;
        }
      }
    }
  }

  .main-container {
    margin-left: 0;
    width: 100%;
  }

  .header {
    padding: 0 12px;
    height: 50px; // 减少移动端头部高度

    .header-left {
      gap: 6px;

      .sidebar-toggle {
        -webkit-tap-highlight-color: transparent;
        touch-action: manipulation;
        min-width: 36px; // 减小触摸目标大小
        min-height: 36px;
        border-radius: 6px;
        padding: 4px;

        .el-icon {
          font-size: 16px !important; // 减小图标大小
          transition: all 0.2s ease;
        }

        &:hover {
          background: var(--el-color-primary-light-9);

          .el-icon {
            color: var(--el-color-primary);
          }
        }

        &:active {
          transform: scale(0.95);
          transition: transform 0.1s ease;
          background: var(--el-color-primary-light-8);
        }
      }

      .breadcrumb {
        display: none;
      }
    }

    .header-right {
      gap: 6px;

      .theme-toggle,
      .notification-btn {
        padding: 4px;
        min-width: 32px;
        min-height: 32px;
        border-radius: 6px;
        -webkit-tap-highlight-color: transparent;
        touch-action: manipulation;

        .el-icon {
          font-size: 16px !important; // 减小图标大小
          transition: all 0.2s ease;
        }

        &:hover {
          background: var(--el-color-primary-light-9);

          .el-icon {
            color: var(--el-color-primary);
          }
        }

        &:active {
          transform: scale(0.95);
          transition: transform 0.1s ease;
          background: var(--el-color-primary-light-8);
        }
      }

      .user-info {
        .username {
          display: none;
        }
      }
    }
  }

  .mobile-overlay {
    position: fixed;
    top: 0;
    left: 64px; // 从菜单右侧开始
    right: 0;
    bottom: 0;
    background: var(--el-overlay-color-lighter); // 使用主题变量
    z-index: 999;
    animation: fadeIn 0.3s ease;
    -webkit-tap-highlight-color: transparent; // 移除触摸高亮
    touch-action: manipulation; // 优化触摸响应
  }

  @keyframes fadeIn {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }
}

@media (max-width: 480px) {
  .main-layout {
    .sidebar {
      width: 64px !important; // 所有移动端都使用仅图标模式
    }

    .header {
      padding: 0 12px;

      .header-left {
        .sidebar-toggle {
          margin-right: 8px;
        }
      }

      .header-right {
        .user-info {
          .username {
            display: none;
          }
        }
      }
    }
  }

  .mobile-overlay {
    left: 64px; // 遮罩从菜单右侧开始
  }
}

@media (max-width: 360px) {
  .main-layout {
    .sidebar {
      width: 64px !important; // 极小屏幕也使用仅图标模式
    }

    .header {
      padding: 0 8px;

      .header-right {
        .notification-btn {
          display: none;
        }

        .theme-toggle {
          padding: 4px;
        }
      }
    }
  }

  .mobile-overlay {
    left: 64px; // 遮罩从菜单右侧开始
  }
}
</style>
