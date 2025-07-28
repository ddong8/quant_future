<template>
  <div v-if="hasPermission">
    <slot />
  </div>
  <div v-else-if="showFallback" class="permission-denied">
    <slot name="fallback">
      <el-empty 
        description="权限不足" 
        :image-size="100"
      >
        <template #image>
          <el-icon size="100" color="var(--el-color-info)">
            <Lock />
          </el-icon>
        </template>
        <el-button type="primary" @click="goBack">返回</el-button>
      </el-empty>
    </slot>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { Lock } from '@element-plus/icons-vue'

interface Props {
  roles?: string | string[]
  permissions?: string | string[]
  requireAll?: boolean
  showFallback?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  requireAll: false,
  showFallback: true
})

const router = useRouter()
const authStore = useAuthStore()

// 检查权限
const hasPermission = computed(() => {
  if (!authStore.isAuthenticated) {
    return false
  }

  const user = authStore.user
  if (!user) {
    return false
  }

  // 检查角色权限
  if (props.roles) {
    const requiredRoles = Array.isArray(props.roles) ? props.roles : [props.roles]
    const userRole = user.role
    
    if (props.requireAll) {
      // 需要所有角色（通常不适用，因为用户只有一个角色）
      return requiredRoles.includes(userRole)
    } else {
      // 需要任一角色
      return requiredRoles.includes(userRole)
    }
  }

  // 检查具体权限（如果有权限系统的话）
  if (props.permissions) {
    const requiredPermissions = Array.isArray(props.permissions) ? props.permissions : [props.permissions]
    
    // 这里可以扩展具体的权限检查逻辑
    // 目前简化为基于角色的权限检查
    const rolePermissions: Record<string, string[]> = {
      admin: ['*'], // 管理员拥有所有权限
      trader: ['trading', 'orders', 'positions', 'accounts', 'strategies', 'backtests'],
      viewer: ['view_only']
    }
    
    const userPermissions = rolePermissions[user.role] || []
    
    if (userPermissions.includes('*')) {
      return true
    }
    
    if (props.requireAll) {
      return requiredPermissions.every(permission => userPermissions.includes(permission))
    } else {
      return requiredPermissions.some(permission => userPermissions.includes(permission))
    }
  }

  // 如果没有指定角色或权限要求，默认允许已认证用户访问
  return true
})

// 返回上一页
const goBack = () => {
  router.go(-1)
}
</script>

<style lang="scss" scoped>
.permission-denied {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  padding: 40px;
}
</style>