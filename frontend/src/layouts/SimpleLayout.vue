<template>
  <div class="simple-layout">
    <!-- 侧边栏 -->
    <div class="sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="logo-container">
        <div class="logo">
          <span class="logo-icon">📈</span>
          <span v-if="!sidebarCollapsed" class="logo-text">量化交易平台 [SimpleLayout]</span>
        </div>
      </div>
      
      <nav class="sidebar-menu">
        <!-- 调试信息 -->
        <div style="padding: 8px; font-size: 12px; color: #999; border-bottom: 1px solid #eee;">
          菜单数量: {{ menuRoutes.length }}<br>
          展开菜单: {{ expandedMenus.join(', ') }}<br>
          当前路径: {{ route.path }}
        </div>
        <div v-for="menuItem in menuRoutes" :key="menuItem.path" class="menu-group">
          <!-- 没有子菜单的路由 -->
          <router-link
            v-if="!menuItem.children"
            :to="menuItem.path"
            class="menu-item"
            :class="{ active: isActive(menuItem.path) }"
          >
            <span class="menu-icon">{{ menuItem.meta?.icon || '📄' }}</span>
            <span v-if="!sidebarCollapsed" class="menu-title">{{ menuItem.meta?.title }}</span>
          </router-link>
          
          <!-- 有子菜单的路由 -->
          <div v-else class="menu-item-group">
            <div 
              class="menu-item parent"
              :class="{ active: isParentActive(menuItem.path.substring(1)), expanded: expandedMenus.includes(menuItem.path) }"
              @click="toggleMenu(menuItem.path)"
            >
              <span class="menu-icon">{{ menuItem.meta?.icon || '📁' }}</span>
              <span v-if="!sidebarCollapsed" class="menu-title">{{ menuItem.meta?.title }}</span>
              <span v-if="!sidebarCollapsed" class="expand-icon" :class="{ rotated: expandedMenus.includes(menuItem.path) }">
                ▼
              </span>
            </div>
            
            <div v-if="!sidebarCollapsed && expandedMenus.includes(menuItem.path)" class="submenu">
              <router-link
                v-for="child in menuItem.children"
                :key="child.path"
                :to="child.path"
                class="submenu-item"
                :class="{ active: isActive(child.path) }"
              >
                <span class="submenu-icon">{{ child.meta?.icon || '•' }}</span>
                <span class="submenu-title">{{ child.meta?.title }}</span>
              </router-link>
            </div>
          </div>
        </div>
      </nav>
    </div>

    <!-- 主内容区 -->
    <div class="main-container">
      <!-- 顶部导航 -->
      <header class="header">
        <div class="header-left">
          <button class="sidebar-toggle" @click="toggleSidebar">
            <span>{{ sidebarCollapsed ? '☰' : '✕' }}</span>
          </button>
          
          <div class="breadcrumb">
            <span v-for="(item, index) in breadcrumbs" :key="item.path">
              <router-link v-if="index < breadcrumbs.length - 1" :to="item.path">
                {{ item.title }}
              </router-link>
              <span v-else class="current">{{ item.title }}</span>
              <span v-if="index < breadcrumbs.length - 1" class="separator"> / </span>
            </span>
          </div>
        </div>
        
        <div class="header-right">
          <div class="user-info">
            <span class="username">{{ authStore.userName || 'admin' }}</span>
            <button class="logout-btn" @click="logout">退出</button>
          </div>
        </div>
      </header>

      <!-- 主内容 -->
      <main class="main-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

// 侧边栏状态
const sidebarCollapsed = ref(false)
const expandedMenus = ref<string[]>([])

// 菜单路由配置 - 简化版本，直接定义
const menuRoutes = ref([
  {
    path: '/',
    meta: { title: '仪表板', icon: '🏠' }
  },
  {
    path: '/trading',
    meta: { title: '交易中心', icon: '📈' },
    children: [
      { path: '/trading', meta: { title: '交易面板', icon: '💹' } },
      { path: '/trading/manual', meta: { title: '手动交易', icon: '✏️' } },
      { path: '/trading/quick', meta: { title: '快速交易', icon: '⚡' } }
    ]
  },
  {
    path: '/orders',
    meta: { title: '订单管理', icon: '📋' },
    children: [
      { path: '/orders', meta: { title: '订单列表', icon: '📄' } },
      { path: '/orders/history', meta: { title: '历史订单', icon: '🕒' } },
      { path: '/orders/templates', meta: { title: '订单模板', icon: '📝' } }
    ]
  },
  {
    path: '/positions',
    meta: { title: '持仓管理', icon: '📊' },
    children: [
      { path: '/positions', meta: { title: '当前持仓', icon: '💼' } },
      { path: '/positions/history', meta: { title: '持仓历史', icon: '🕒' } },
      { path: '/positions/analysis', meta: { title: '持仓分析', icon: '📈' } }
    ]
  },
  {
    path: '/strategies',
    meta: { title: '策略管理', icon: '🎯' },
    children: [
      { path: '/strategies', meta: { title: '策略列表', icon: '📋' } },
      { path: '/strategies/create', meta: { title: '创建策略', icon: '➕' } },
      { path: '/strategies/templates', meta: { title: '策略模板', icon: '📝' } },
      { path: '/strategies/performance', meta: { title: '策略绩效', icon: '📊' } }
    ]
  },
  {
    path: '/settings',
    meta: { title: '系统设置', icon: '⚙️' },
    children: [
      { path: '/settings', meta: { title: '通用设置', icon: '🔧' } },
      { path: '/settings/account', meta: { title: '账户设置', icon: '👤' } },
      { path: '/settings/trading', meta: { title: '交易设置', icon: '📈' } },
      { path: '/settings/notifications', meta: { title: '通知设置', icon: '🔔' } }
    ]
  }
])

// 面包屑导航
const breadcrumbs = computed(() => {
  const matched = route.matched.filter(item => item.meta?.title)
  return matched.map(item => ({
    title: item.meta?.title,
    path: item.path
  }))
})

// 判断菜单是否激活
const isActive = (path: string) => {
  return route.path === path
}

const isParentActive = (parentKey: string) => {
  // 检查当前路由是否属于某个父级菜单
  return route.meta?.parent === parentKey || route.path.startsWith(`/${parentKey}`)
}

// 切换侧边栏
const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

// 切换菜单展开状态
const toggleMenu = (path: string) => {
  console.log('🔄 切换菜单:', path)
  console.log('📋 当前展开的菜单:', expandedMenus.value)
  console.log('📱 侧边栏是否收起:', sidebarCollapsed.value)
  
  if (sidebarCollapsed.value) return
  
  const index = expandedMenus.value.indexOf(path)
  if (index > -1) {
    expandedMenus.value.splice(index, 1)
    console.log('📤 收起菜单:', path)
  } else {
    expandedMenus.value.push(path)
    console.log('📥 展开菜单:', path)
  }
  
  console.log('📋 更新后展开的菜单:', expandedMenus.value)
}

// 退出登录
const logout = async () => {
  await authStore.logout()
  router.push('/login')
}

// 监听路由变化，自动展开相关菜单
watch(() => route.path, (newPath) => {
  // 根据当前路径确定应该展开哪个菜单
  const parentKey = route.meta?.parent
  if (parentKey) {
    const parentPath = `/${parentKey}`
    if (!expandedMenus.value.includes(parentPath)) {
      expandedMenus.value.push(parentPath)
    }
  }
  
  // 也检查路径匹配
  menuRoutes.value.forEach(menuRoute => {
    if (menuRoute.children && newPath.startsWith(menuRoute.path)) {
      if (!expandedMenus.value.includes(menuRoute.path)) {
        expandedMenus.value.push(menuRoute.path)
      }
    }
  })
}, { immediate: true })

// 组件挂载时的调试信息
onMounted(() => {
  console.log('🎯 SimpleLayout 组件已挂载')
  console.log('📋 菜单配置:', menuRoutes.value)
  console.log('📱 当前路由:', route.path)
})
</script>

<style scoped>
.simple-layout {
  display: flex;
  height: 100vh;
  background: #f8f9fa;
}

/* 侧边栏 */
.sidebar {
  width: 260px;
  background: white;
  border-right: 1px solid #e9ecef;
  transition: width 0.3s ease;
  overflow: hidden;
}

.sidebar.collapsed {
  width: 70px;
}

.logo-container {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid #e9ecef;
  padding: 0 16px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #667eea;
  font-weight: 600;
}

.logo-icon {
  font-size: 24px;
}

.logo-text {
  font-size: 16px;
  white-space: nowrap;
}

.sidebar-menu {
  padding: 16px 0;
  height: calc(100vh - 60px);
  overflow-y: auto;
}

.menu-item, .menu-item.parent {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  color: #2c3e50;
  text-decoration: none;
  transition: all 0.3s ease;
  cursor: pointer;
  border: none;
  background: none;
  width: 100%;
}

.menu-item:hover, .menu-item.parent:hover {
  background: #f8f9fa;
  color: #667eea;
}

.menu-item.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.menu-icon {
  font-size: 18px;
  width: 24px;
  text-align: center;
  margin-right: 12px;
}

.menu-title {
  flex: 1;
  font-weight: 500;
  white-space: nowrap;
}

.expand-icon {
  font-size: 12px;
  transition: transform 0.3s ease;
}

.expand-icon.rotated {
  transform: rotate(180deg);
}

.submenu {
  background: #f8f9fa;
  border-left: 3px solid #667eea;
}

.submenu-item {
  display: flex;
  align-items: center;
  padding: 8px 16px 8px 40px;
  color: #6c757d;
  text-decoration: none;
  transition: all 0.3s ease;
  font-size: 14px;
}

.submenu-item:hover {
  background: #e9ecef;
  color: #667eea;
}

.submenu-item.active {
  background: #667eea;
  color: white;
}

.submenu-icon {
  margin-right: 8px;
  font-size: 14px;
}

.submenu-title {
  font-weight: 500;
}

/* 主内容区 */
.main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.header {
  height: 60px;
  background: white;
  border-bottom: 1px solid #e9ecef;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.sidebar-toggle {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  padding: 8px;
  border-radius: 4px;
  transition: background 0.3s ease;
}

.sidebar-toggle:hover {
  background: #f8f9fa;
}

.breadcrumb {
  font-size: 14px;
  color: #6c757d;
}

.breadcrumb a {
  color: #667eea;
  text-decoration: none;
}

.breadcrumb a:hover {
  text-decoration: underline;
}

.breadcrumb .current {
  color: #2c3e50;
  font-weight: 500;
}

.separator {
  margin: 0 8px;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.username {
  font-weight: 500;
  color: #2c3e50;
}

.logout-btn {
  background: #dc3545;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: background 0.3s ease;
}

.logout-btn:hover {
  background: #c82333;
}

.main-content {
  flex: 1;
  overflow: auto;
  background: #f8f9fa;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    top: 0;
    left: 0;
    z-index: 1000;
    height: 100vh;
    transform: translateX(-100%);
    transition: transform 0.3s ease;
  }
  
  .sidebar:not(.collapsed) {
    transform: translateX(0);
  }
  
  .main-container {
    width: 100%;
  }
  
  .breadcrumb {
    display: none;
  }
}
</style>