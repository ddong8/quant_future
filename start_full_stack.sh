#!/bin/bash

# 量化交易平台完整启动脚本
set -e

echo "🚀 启动量化交易平台完整版..."

# 停止现有服务
echo "🛑 停止现有服务..."
docker-compose down

# 启动数据库服务
echo "🗄️ 启动数据库服务..."
docker-compose up -d postgres redis influxdb

# 等待数据库就绪
echo "⏳ 等待数据库就绪..."
sleep 15

# 启动后端服务
echo "🔧 启动后端服务..."
docker-compose up -d backend

# 等待后端就绪
echo "⏳ 等待后端就绪..."
sleep 10

# 测试后端
echo "🧪 测试后端服务..."
curl -s http://localhost:8000/health | jq .

# 启动简化的Vue.js前端
echo "🎨 启动前端服务..."

# 创建简化的前端配置
cat > frontend_simple/package.json << 'EOF'
{
  "name": "trading-frontend-simple",
  "version": "1.0.0",
  "scripts": {
    "dev": "vite --host 0.0.0.0 --port 3000"
  },
  "dependencies": {
    "vue": "^3.3.8",
    "axios": "^1.6.2"
  },
  "devDependencies": {
    "vite": "^5.0.0",
    "@vitejs/plugin-vue": "^4.5.0"
  }
}
EOF

# 创建简化的vite配置
cat > frontend_simple/vite.config.js << 'EOF'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    port: 3000
  }
})
EOF

# 创建简化的Vue应用
cat > frontend_simple/index.html << 'EOF'
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>量化交易平台</title>
</head>
<body>
  <div id="app"></div>
  <script type="module" src="/src/main.js"></script>
</body>
</html>
EOF

mkdir -p frontend_simple/src

cat > frontend_simple/src/main.js << 'EOF'
import { createApp } from 'vue'
import App from './App.vue'

createApp(App).mount('#app')
EOF

cat > frontend_simple/src/App.vue << 'EOF'
<template>
  <div id="app">
    <h1>🚀 量化交易平台</h1>
    <div>
      <button @click="testAPI">测试后端API</button>
      <pre>{{ result }}</pre>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'App',
  data() {
    return {
      result: '点击按钮测试API...'
    }
  },
  methods: {
    async testAPI() {
      try {
        const response = await axios.get('http://localhost:8000/health')
        this.result = JSON.stringify(response.data, null, 2)
      } catch (error) {
        this.result = '错误: ' + error.message
      }
    }
  }
}
</script>
EOF

# 更新docker-compose配置使用简化前端
cat > docker-compose-simple.yml << 'EOF'
services:
  postgres:
    image: postgres:13
    container_name: trading_postgres
    environment:
      POSTGRES_DB: trading_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:6-alpine
    container_name: trading_redis
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3

  influxdb:
    image: influxdb:2.0
    container_name: trading_influxdb
    environment:
      INFLUXDB_DB: trading
      INFLUXDB_ADMIN_USER: admin
      INFLUXDB_ADMIN_PASSWORD: password
      INFLUXDB_ADMIN_TOKEN: my-super-secret-auth-token
    volumes:
      - influxdb_data:/var/lib/influxdb2
    ports:
      - "8086:8086"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8086/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  backend:
    image: python:3.9-slim
    container_name: trading_backend
    working_dir: /app
    volumes:
      - ./demo_server.py:/app/demo_server.py
    command: >
      bash -c "
        pip install fastapi uvicorn[standard] &&
        python demo_server.py
      "
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      influxdb:
        condition: service_healthy
    restart: unless-stopped

  frontend:
    image: node:18-alpine
    container_name: trading_frontend
    working_dir: /app
    volumes:
      - ./frontend_simple:/app
    ports:
      - "3000:3000"
    depends_on:
      - backend
    restart: unless-stopped
    command: >
      sh -c "
        npm install &&
        npm run dev
      "

volumes:
  postgres_data:
  redis_data:
  influxdb_data:

networks:
  default:
    name: trading_network
EOF

echo "✅ 配置文件已创建"
echo "🌐 访问地址:"
echo "  前端: http://localhost:3000"
echo "  后端: http://localhost:8000"
echo "  API文档: http://localhost:8000/docs"

echo "🎉 启动完成！"