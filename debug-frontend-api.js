#!/usr/bin/env node

/**
 * 前端API调试脚本
 * 用于诊断首页请求参数错误问题
 */

const axios = require('axios');

// 配置
const BASE_URL = 'http://localhost:8000';
const TEST_USER = {
  username: 'admin',
  password: 'admin123'
};

let authToken = null;

// 创建axios实例
const api = axios.create({
  baseURL: BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// 请求拦截器
api.interceptors.request.use(config => {
  if (authToken) {
    config.headers.Authorization = `Bearer ${authToken}`;
  }
  console.log(`🔍 请求: ${config.method?.toUpperCase()} ${config.url}`);
  if (config.params) {
    console.log(`   参数:`, config.params);
  }
  if (config.data) {
    console.log(`   数据:`, config.data);
  }
  return config;
});

// 响应拦截器
api.interceptors.response.use(
  response => {
    console.log(`✅ 响应: ${response.status} ${response.config.url}`);
    return response;
  },
  error => {
    console.error(`❌ 错误: ${error.response?.status || 'NETWORK'} ${error.config?.url}`);
    if (error.response?.status === 422) {
      console.error(`   422错误详情:`, error.response.data);
    }
    return Promise.reject(error);
  }
);

// 认证函数
async function authenticate() {
  try {
    console.log('🔐 开始用户认证...');
    const response = await api.post('/api/v1/auth/login', TEST_USER);
    
    if (response.data.success && response.data.data) {
      authToken = response.data.data.access_token;
      console.log('✅ 认证成功');
      return true;
    } else {
      console.error('❌ 认证失败：响应格式不正确');
      return false;
    }
  } catch (err) {
    console.error('❌ 认证失败:', err.message);
    return false;
  }
}

// 测试首页相关API
async function testDashboardAPIs() {
  console.log('\n🏠 测试首页相关API...\n');
  
  const tests = [
    {
      name: '获取仪表板摘要',
      method: 'GET',
      url: '/api/v1/dashboard/summary'
    },
    {
      name: '获取用户资料',
      method: 'GET',
      url: '/api/v1/user/profile'
    },
    {
      name: '获取用户设置资料',
      method: 'GET',
      url: '/api/v1/user-settings/profile'
    },
    {
      name: '获取当前用户信息',
      method: 'GET',
      url: '/api/v1/auth/me'
    }
  ];
  
  for (const test of tests) {
    try {
      console.log(`\n📋 测试: ${test.name}`);
      const response = await api({
        method: test.method,
        url: test.url,
        params: test.params
      });
      
      console.log(`✅ ${test.name} - 成功`);
      console.log(`   响应数据类型: ${typeof response.data}`);
      if (response.data.success !== undefined) {
        console.log(`   成功标志: ${response.data.success}`);
      }
      if (response.data.data) {
        console.log(`   数据字段: ${Object.keys(response.data.data).join(', ')}`);
      }
    } catch (err) {
      console.error(`❌ ${test.name} - 失败`);
      if (err.response?.status === 422) {
        console.error(`   422错误详情:`, err.response.data);
        if (err.response.data.detail) {
          console.error(`   详细信息:`, err.response.data.detail);
        }
      } else {
        console.error(`   错误信息:`, err.message);
      }
    }
  }
}

// 主函数
async function main() {
  console.log('🚀 开始前端API调试\n');
  
  // 1. 认证
  const authSuccess = await authenticate();
  if (!authSuccess) {
    console.log('\n❌ 认证失败，无法继续测试');
    process.exit(1);
  }
  
  // 2. 测试首页相关API
  await testDashboardAPIs();
  
  console.log('\n✅ API调试完成');
}

// 运行调试
if (require.main === module) {
  main().catch(err => {
    console.error('\n💥 调试运行失败:', err);
    process.exit(1);
  });
}