<template>
  <div class="system-management">
    <div class="page-header">
      <h2>系统管理</h2>
      <p>系统监控、数据导出、日志管理和性能分析</p>
    </div>

    <el-tabs v-model="activeTab" type="card" class="system-tabs">
      <el-tab-pane label="系统监控" name="monitor">
        <SystemMonitor />
      </el-tab-pane>

      <el-tab-pane label="数据导出" name="export">
        <ExportTaskManager />
      </el-tab-pane>

      <el-tab-pane label="系统日志" name="logs">
        <SystemLogViewer />
      </el-tab-pane>

      <el-tab-pane label="数据完整性" name="integrity">
        <DataIntegrityChecker />
      </el-tab-pane>

      <el-tab-pane label="系统维护" name="maintenance">
        <SystemMaintenance />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import SystemMonitor from '@/components/system/SystemMonitor.vue'
import ExportTaskManager from '@/components/system/ExportTaskManager.vue'
import SystemLogViewer from '@/components/system/SystemLogViewer.vue'
import DataIntegrityChecker from '@/components/system/DataIntegrityChecker.vue'
import SystemMaintenance from '@/components/system/SystemMaintenance.vue'

// 响应式数据
const activeTab = ref('monitor')
</script>

<style scoped>
.system-management {
  padding: 20px;
  min-height: calc(100vh - 60px);
}

.page-header {
  margin-bottom: 30px;
}

.page-header h2 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 28px;
  font-weight: 600;
}

.page-header p {
  margin: 0;
  color: #606266;
  font-size: 16px;
}

.system-tabs {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

:deep(.el-tabs__header) {
  margin: 0;
  background: #f5f7fa;
  border-radius: 8px 8px 0 0;
}

:deep(.el-tabs__content) {
  padding: 0;
}

:deep(.el-tab-pane) {
  background: white;
  border-radius: 0 0 8px 8px;
}
</style>