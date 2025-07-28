<template>
  <el-dialog
    v-model="visible"
    title="策略部署"
    width="600px"
    :before-close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="120px"
      @submit.prevent
    >
      <!-- 部署配置 -->
      <el-divider content-position="left">部署配置</el-divider>
      
      <el-form-item label="部署名称" prop="name">
        <el-input
          v-model="form.name"
          placeholder="请输入部署名称"
          maxlength="100"
          show-word-limit
        />
      </el-form-item>

      <el-form-item label="部署环境" prop="environment">
        <el-select v-model="form.environment" placeholder="请选择部署环境">
          <el-option label="开发环境" value="development" />
          <el-option label="测试环境" value="testing" />
          <el-option label="预生产环境" value="staging" />
          <el-option label="生产环境" value="production" />
        </el-select>
      </el-form-item>

      <el-form-item label="实例数量" prop="instances">
        <el-input-number
          v-model="form.instances"
          :min="1"
          :max="10"
          style="width: 100%"
        />
        <div class="form-tip">
          建议根据策略复杂度和资源需求设置实例数量
        </div>
      </el-form-item>

      <el-form-item label="自动启动" prop="auto_start">
        <el-switch
          v-model="form.auto_start"
          active-text="启用"
          inactive-text="禁用"
        />
        <div class="form-tip">
          部署完成后是否自动启动策略
        </div>
      </el-form-item>

      <!-- 资源配置 -->
      <el-divider content-position="left">资源配置</el-divider>

      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="CPU限制" prop="cpu_limit">
            <el-input-number
              v-model="form.cpu_limit"
              :min="0.1"
              :max="8"
              :step="0.1"
              :precision="1"
              style="width: 100%"
            />
            <div class="form-tip">单位: 核心数</div>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="内存限制" prop="memory_limit">
            <el-input-number
              v-model="form.memory_limit"
              :min="128"
              :max="8192"
              :step="128"
              style="width: 100%"
            />
            <div class="form-tip">单位: MB</div>
          </el-form-item>
        </el-col>
      </el-row>

      <!-- 网络配置 -->
      <el-divider content-position="left">网络配置</el-divider>

      <el-form-item label="端口映射" prop="port_mapping">
        <el-input
          v-model="form.port_mapping"
          placeholder="例如: 8080:80,8443:443"
        />
        <div class="form-tip">
          格式: 主机端口:容器端口，多个端口用逗号分隔
        </div>
      </el-form-item>

      <el-form-item label="网络模式" prop="network_mode">
        <el-select v-model="form.network_mode">
          <el-option label="桥接模式" value="bridge" />
          <el-option label="主机模式" value="host" />
          <el-option label="自定义网络" value="custom" />
        </el-select>
      </el-form-item>

      <!-- 存储配置 -->
      <el-divider content-position="left">存储配置</el-divider>

      <el-form-item label="数据卷" prop="volumes">
        <el-input
          v-model="form.volumes"
          type="textarea"
          :rows="3"
          placeholder="例如: /host/data:/container/data,/host/logs:/container/logs"
        />
        <div class="form-tip">
          格式: 主机路径:容器路径，多个卷用逗号分隔
        </div>
      </el-form-item>

      <el-form-item label="持久化存储" prop="persistent_storage">
        <el-switch
          v-model="form.persistent_storage"
          active-text="启用"
          inactive-text="禁用"
        />
        <div class="form-tip">
          启用后数据将持久化保存
        </div>
      </el-form-item>

      <!-- 环境变量 -->
      <el-divider content-position="left">环境变量</el-divider>

      <el-form-item label="环境变量">
        <div class="env-vars">
          <div
            v-for="(env, index) in form.environment_variables"
            :key="index"
            class="env-var-item"
          >
            <el-input
              v-model="env.key"
              placeholder="变量名"
              style="width: 40%"
            />
            <span class="env-separator">=</span>
            <el-input
              v-model="env.value"
              placeholder="变量值"
              style="width: 40%"
            />
            <el-button
              text
              type="danger"
              @click="removeEnvVar(index)"
            >
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
          <el-button
            text
            type="primary"
            @click="addEnvVar"
          >
            <el-icon><Plus /></el-icon>
            添加环境变量
          </el-button>
        </div>
      </el-form-item>

      <!-- 健康检查 -->
      <el-divider content-position="left">健康检查</el-divider>

      <el-form-item label="启用健康检查" prop="health_check_enabled">
        <el-switch
          v-model="form.health_check_enabled"
          active-text="启用"
          inactive-text="禁用"
        />
      </el-form-item>

      <template v-if="form.health_check_enabled">
        <el-form-item label="检查路径" prop="health_check_path">
          <el-input
            v-model="form.health_check_path"
            placeholder="/health"
          />
        </el-form-item>

        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="检查间隔(秒)" prop="health_check_interval">
              <el-input-number
                v-model="form.health_check_interval"
                :min="5"
                :max="300"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="超时时间(秒)" prop="health_check_timeout">
              <el-input-number
                v-model="form.health_check_timeout"
                :min="1"
                :max="60"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="重试次数" prop="health_check_retries">
              <el-input-number
                v-model="form.health_check_retries"
                :min="1"
                :max="10"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </template>

      <!-- 日志配置 -->
      <el-divider content-position="left">日志配置</el-divider>

      <el-form-item label="日志级别" prop="log_level">
        <el-select v-model="form.log_level">
          <el-option label="DEBUG" value="DEBUG" />
          <el-option label="INFO" value="INFO" />
          <el-option label="WARNING" value="WARNING" />
          <el-option label="ERROR" value="ERROR" />
        </el-select>
      </el-form-item>

      <el-form-item label="日志驱动" prop="log_driver">
        <el-select v-model="form.log_driver">
          <el-option label="JSON文件" value="json-file" />
          <el-option label="Syslog" value="syslog" />
          <el-option label="Journald" value="journald" />
          <el-option label="Fluentd" value="fluentd" />
        </el-select>
      </el-form-item>

      <el-form-item label="日志轮转" prop="log_rotation">
        <el-switch
          v-model="form.log_rotation"
          active-text="启用"
          inactive-text="禁用"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" :loading="loading" @click="handleSubmit">
          开始部署
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Delete } from '@element-plus/icons-vue'

interface Props {
  modelValue: boolean
  strategyId?: number
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'success', deploymentId: number): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const formRef = ref<FormInstance>()
const loading = ref(false)

// 表单数据
const form = ref({
  name: '',
  environment: 'testing',
  instances: 1,
  auto_start: true,
  cpu_limit: 1.0,
  memory_limit: 512,
  port_mapping: '',
  network_mode: 'bridge',
  volumes: '',
  persistent_storage: true,
  environment_variables: [
    { key: '', value: '' }
  ],
  health_check_enabled: true,
  health_check_path: '/health',
  health_check_interval: 30,
  health_check_timeout: 10,
  health_check_retries: 3,
  log_level: 'INFO',
  log_driver: 'json-file',
  log_rotation: true
})

// 表单验证规则
const rules: FormRules = {
  name: [
    { required: true, message: '请输入部署名称', trigger: 'blur' },
    { min: 2, max: 100, message: '部署名称长度在 2 到 100 个字符', trigger: 'blur' }
  ],
  environment: [
    { required: true, message: '请选择部署环境', trigger: 'change' }
  ],
  instances: [
    { required: true, message: '请设置实例数量', trigger: 'blur' }
  ],
  cpu_limit: [
    { required: true, message: '请设置CPU限制', trigger: 'blur' }
  ],
  memory_limit: [
    { required: true, message: '请设置内存限制', trigger: 'blur' }
  ]
}

// 计算属性
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// 方法
const addEnvVar = () => {
  form.value.environment_variables.push({ key: '', value: '' })
}

const removeEnvVar = (index: number) => {
  if (form.value.environment_variables.length > 1) {
    form.value.environment_variables.splice(index, 1)
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    loading.value = true
    
    // 构建部署配置
    const deployConfig = {
      strategy_id: props.strategyId,
      name: form.value.name,
      environment: form.value.environment,
      config: {
        instances: form.value.instances,
        auto_start: form.value.auto_start,
        resources: {
          cpu_limit: form.value.cpu_limit,
          memory_limit: form.value.memory_limit
        },
        network: {
          port_mapping: form.value.port_mapping,
          network_mode: form.value.network_mode
        },
        storage: {
          volumes: form.value.volumes,
          persistent_storage: form.value.persistent_storage
        },
        environment_variables: form.value.environment_variables
          .filter(env => env.key && env.value)
          .reduce((acc, env) => {
            acc[env.key] = env.value
            return acc
          }, {} as Record<string, string>),
        health_check: form.value.health_check_enabled ? {
          path: form.value.health_check_path,
          interval: form.value.health_check_interval,
          timeout: form.value.health_check_timeout,
          retries: form.value.health_check_retries
        } : null,
        logging: {
          level: form.value.log_level,
          driver: form.value.log_driver,
          rotation: form.value.log_rotation
        }
      }
    }
    
    // 调用部署API
    // const response = await strategyApi.deployStrategy(deployConfig)
    // if (response.success) {
    //   emit('success', response.data.deployment_id)
    //   ElMessage.success('部署已开始')
    //   handleClose()
    // }
    
    // 模拟成功
    setTimeout(() => {
      emit('success', Math.floor(Math.random() * 1000))
      ElMessage.success('部署已开始')
      handleClose()
    }, 1000)
    
  } catch (error) {
    ElMessage.error('部署配置验证失败')
  } finally {
    loading.value = false
  }
}

const handleClose = () => {
  visible.value = false
  resetForm()
}

const resetForm = () => {
  if (formRef.value) {
    formRef.value.resetFields()
  }
  
  form.value = {
    name: '',
    environment: 'testing',
    instances: 1,
    auto_start: true,
    cpu_limit: 1.0,
    memory_limit: 512,
    port_mapping: '',
    network_mode: 'bridge',
    volumes: '',
    persistent_storage: true,
    environment_variables: [
      { key: '', value: '' }
    ],
    health_check_enabled: true,
    health_check_path: '/health',
    health_check_interval: 30,
    health_check_timeout: 10,
    health_check_retries: 3,
    log_level: 'INFO',
    log_driver: 'json-file',
    log_rotation: true
  }
}
</script>

<style scoped lang="scss">
.dialog-footer {
  text-align: right;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.env-vars {
  .env-var-item {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
    
    .env-separator {
      font-weight: bold;
      color: #606266;
    }
  }
}

:deep(.el-divider__text) {
  font-weight: 600;
  color: #303133;
}
</style>