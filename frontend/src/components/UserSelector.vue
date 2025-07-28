<template>
  <el-select
    v-model="selectedValue"
    :placeholder="placeholder"
    :multiple="multiple"
    :clearable="clearable"
    :filterable="filterable"
    :remote="remote"
    :remote-method="handleRemoteSearch"
    :loading="loading"
    @change="handleChange"
    @clear="handleClear"
  >
    <el-option
      v-for="user in userOptions"
      :key="user.id"
      :label="getUserLabel(user)"
      :value="user.id"
    >
      <div class="user-option">
        <UserAvatar
          :avatar-url="user.avatar_url"
          :display-name="user.full_name || user.username"
          :size="24"
        />
        <div class="user-info">
          <div class="user-name">{{ user.full_name || user.username }}</div>
          <div class="user-email">{{ user.email }}</div>
        </div>
        <el-tag v-if="showRole" :type="getRoleType(user.role)" size="small">
          {{ getRoleText(user.role) }}
        </el-tag>
      </div>
    </el-option>
  </el-select>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import type { User } from '@/types/auth'
import UserAvatar from './UserAvatar.vue'

interface Props {
  modelValue?: number | number[]
  placeholder?: string
  multiple?: boolean
  clearable?: boolean
  filterable?: boolean
  remote?: boolean
  showRole?: boolean
  roleFilter?: string[]
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: '请选择用户',
  multiple: false,
  clearable: true,
  filterable: true,
  remote: false,
  showRole: true
})

const emit = defineEmits<{
  'update:modelValue': [value: number | number[] | undefined]
  change: [value: number | number[], users: User | User[]]
  clear: []
}>()

// 响应式数据
const loading = ref(false)
const userOptions = ref<User[]>([])
const searchKeyword = ref('')

// 计算属性
const selectedValue = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// 获取用户显示标签
const getUserLabel = (user: User) => {
  return user.full_name || user.username
}

// 获取角色类型
const getRoleType = (role: string) => {
  const roleTypeMap: Record<string, string> = {
    admin: 'danger',
    trader: 'primary',
    viewer: 'info'
  }
  return roleTypeMap[role] || 'info'
}

// 获取角色文本
const getRoleText = (role: string) => {
  const roleTextMap: Record<string, string> = {
    admin: '管理员',
    trader: '交易员',
    viewer: '观察者'
  }
  return roleTextMap[role] || role
}

// 处理选择变化
const handleChange = (value: number | number[]) => {
  if (props.multiple && Array.isArray(value)) {
    const selectedUsers = userOptions.value.filter(user => value.includes(user.id))
    emit('change', value, selectedUsers)
  } else if (!props.multiple && typeof value === 'number') {
    const selectedUser = userOptions.value.find(user => user.id === value)
    if (selectedUser) {
      emit('change', value, selectedUser)
    }
  }
}

// 处理清空
const handleClear = () => {
  emit('clear')
}

// 处理远程搜索
const handleRemoteSearch = async (query: string) => {
  if (!query) {
    userOptions.value = []
    return
  }

  searchKeyword.value = query
  await loadUsers(query)
}

// 加载用户列表
const loadUsers = async (keyword?: string) => {
  try {
    loading.value = true

    // 这里调用API加载用户列表
    // const params = {
    //   keyword,
    //   roles: props.roleFilter,
    //   page_size: 20
    // }
    // const response = await userApi.getUsers(params)
    // userOptions.value = response.data.users

    // 模拟数据
    const mockUsers: User[] = [
      {
        id: 1,
        username: 'admin',
        email: 'admin@example.com',
        full_name: '系统管理员',
        role: 'admin',
        avatar_url: '',
        is_active: true,
        is_verified: true,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z'
      },
      {
        id: 2,
        username: 'trader1',
        email: 'trader1@example.com',
        full_name: '交易员一号',
        role: 'trader',
        avatar_url: '',
        is_active: true,
        is_verified: true,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z'
      },
      {
        id: 3,
        username: 'viewer1',
        email: 'viewer1@example.com',
        full_name: '观察员一号',
        role: 'viewer',
        avatar_url: '',
        is_active: true,
        is_verified: true,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z'
      }
    ]

    // 过滤用户
    let filteredUsers = mockUsers
    
    if (keyword) {
      filteredUsers = mockUsers.filter(user => 
        user.username.toLowerCase().includes(keyword.toLowerCase()) ||
        user.email.toLowerCase().includes(keyword.toLowerCase()) ||
        (user.full_name && user.full_name.toLowerCase().includes(keyword.toLowerCase()))
      )
    }

    if (props.roleFilter && props.roleFilter.length > 0) {
      filteredUsers = filteredUsers.filter(user => props.roleFilter!.includes(user.role))
    }

    userOptions.value = filteredUsers
  } catch (error) {
    console.error('加载用户列表失败:', error)
    userOptions.value = []
  } finally {
    loading.value = false
  }
}

// 监听角色过滤变化
watch(() => props.roleFilter, () => {
  if (!props.remote) {
    loadUsers(searchKeyword.value)
  }
}, { deep: true })

// 生命周期
onMounted(() => {
  if (!props.remote) {
    loadUsers()
  }
})
</script>

<style lang="scss" scoped>
.user-option {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 4px 0;
  
  .user-info {
    flex: 1;
    min-width: 0;
    
    .user-name {
      font-size: 14px;
      color: var(--el-text-color-primary);
      font-weight: 500;
    }
    
    .user-email {
      font-size: 12px;
      color: var(--el-text-color-secondary);
      margin-top: 2px;
    }
  }
}
</style>