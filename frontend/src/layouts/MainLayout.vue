<template>
  <el-container class="main-layout">
    <!-- 侧边栏 -->
    <el-aside :width="sidebarCollapsed ? '64px' : '240px'" class="sidebar">
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
      >
        <template v-for="route in menuRoutes" :key="route.path">
          <el-menu-item
            v-if="!route.children"
            :index="route.path"
            :disabled="!hasPermission(route.meta?.roles)"
          >
            <el-icon v-if="route.meta?.icon">
              <component :is="route.meta.icon" />
            </el-icon>
            <template #title>{{ route.meta?.title }}</template>
          </el-menu-item>
          
          <el-sub-menu
            v-else
            :index="route.path"
            :disabled="!hasPermission(route.meta?.roles)"
          >
            <template #title>
              <el-icon v-if="route.meta?.icon">
                <component :is="route.meta.icon" />
              </el-icon>
              <span>{{ route.meta?.title }}</span>
            </template>
            
            <el-menu-item
              v-for="child in route.children"
              :key="child.path"
              :index="child.path"
              :disabled="!hasPermission(child.meta?.roles)"
            >
              <el-icon v-if="child.meta?.icon">
                <component :is="child.meta.icon" />
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
          <el-button
            text
            @click="toggleSidebar"
            class="sidebar-toggle"
          >
            <el-icon size="20">
              <Expand v-if="sidebarCollapsed" />
              <Fold v-else />
            </el-icon>
          </el-button>
          
          <el-breadcrumb separator="/" class="breadcrumb">
            <el-breadcrumb-item
              v-for="item in breadcrumbs"
              :key="item.path"
              :to="item.path"
            >
              {{ item.title }}
            </el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        
        <div class="header-right">
          <!-- 主题切换 -->
          <el-button
            text
            @click="themeStore.toggleTheme()"
            class="theme-toggle"
          >
            <el-icon size="18">
              <Sunny v-if="themeStore.isDark" />
              <Moon v-else />
            </el-icon>
          </el-button>
          
          <!-- 通知 -->
          <el-badge :value="notificationCount" :hidden="notificationCount === 0">
            <el-button text class="notification-btn">
              <el-icon size="18">
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
                :size="32"
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
import { computed, ref, watch } from 'vue'
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
  SwitchButton
} from '@element-plus/icons-vue'
import UserAvatar from '@/components/UserAvatar.vue'
import AuthStatus from '@/components/AuthStatus.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const themeStore = useThemeStore()

// 侧边栏状态
const sidebarCollapsed = ref(false)

// 通知数量
const notificationCount = ref(0)

// 缓存的视图
const cachedViews = ref<string[]>([])

// 当前激活的菜单
const activeMenu = computed(() => route.path)

// 面包屑导航
const breadcrumbs = computed(() => {
  const matched = route.matched.filter(item => item.meta?.title)
  return matched.map(item => ({
    title: item.meta?.title,
    path: item.path
  }))
})

// 菜单路由
const menuRoutes = computed(() => {
  return router.getRoutes()
    .filter(route => {
      // 过滤掉不需要在菜单中显示的路由
      return route.path.startsWith('/') && 
             route.path !== '/' && 
             !route.path.includes(':') &&
             route.meta?.title &&
             !route.meta?.hidden
    })
    .sort((a, b) => {
      // 简单的排序逻辑
      const order = {
        '/dashboard': 1,
        '/trading': 2,
        '/orders': 3,
        '/positions': 4,
        '/accounts': 5,
        '/strategies': 6,
        '/backtests': 7,
        '/risk': 8,
        '/market': 9,
        '/settings': 10
      }
      return (order[a.path] || 99) - (order[b.path] || 99)
    })
})

// 切换侧边栏
const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
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
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-bottom: 1px solid var(--el-border-color-lighter);
    
    .logo {
      display: flex;
      align-items: center;
      gap: 8px;
      color: var(--el-color-primary);
      font-weight: 600;
      font-size: 16px;
      
      .logo-text {
        white-space: nowrap;
      }
    }
  }
  
  .sidebar-menu {
    border: none;
    height: calc(100vh - 60px);
    overflow-y: auto;
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
@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    top: 0;
    left: 0;
    z-index: 1000;
    height: 100vh;
  }
  
  .main-container {
    margin-left: 0;
  }
  
  .header-left {
    .breadcrumb {
      display: none;
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
</style>