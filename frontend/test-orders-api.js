#!/usr/bin/env node

/**
 * 订单管理API测试脚本
 * 测试前端订单管理功能与后端API的集成
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
  return config;
});

// 响应拦截器
api.interceptors.response.use(
  response => response,
  error => {
    console.error(`❌ API请求失败: ${error.config?.method?.toUpperCase()} ${error.config?.url}`);
    console.error(`   状态码: ${error.response?.status}`);
    console.error(`   错误信息: ${error.response?.data?.detail || error.message}`);
    return Promise.reject(error);
  }
);

// 工具函数
const log = (message, data = null) => {
  console.log(`📋 ${message}`);
  if (data) {
    console.log('   数据:', JSON.stringify(data, null, 2));
  }
};

const success = (message, data = null) => {
  console.log(`✅ ${message}`);
  if (data) {
    console.log('   结果:', JSON.stringify(data, null, 2));
  }
};

const error = (message, err = null) => {
  console.error(`❌ ${message}`);
  if (err) {
    console.error('   错误:', err.message || err);
  }
};

// 认证函数
async function authenticate() {
  try {
    log('开始用户认证...');
    const response = await api.post('/api/v1/auth/login', TEST_USER);
    
    if (response.data.success && response.data.data) {
      authToken = response.data.data.access_token;
      success('用户认证成功', { token: authToken.substring(0, 20) + '...' });
      return true;
    } else {
      error('认证失败：响应格式不正确', response.data);
      return false;
    }
  } catch (err) {
    error('认证失败', err);
    return false;
  }
}

// 测试订单管理API
async function testOrdersAPI() {
  console.log('\n🔍 测试订单管理API...\n');
  
  const tests = [
    {
      name: '获取我的订单列表',
      method: 'GET',
      url: '/api/v1/orders/my',
      params: { limit: 10 }
    },
    {
      name: '获取订单统计',
      method: 'GET',
      url: '/api/v1/orders/stats'
    },
    {
      name: '获取活跃订单',
      method: 'GET',
      url: '/api/v1/orders/active'
    }
  ];
  
  for (const test of tests) {
    try {
      log(`测试: ${test.name}`);
      const response = await api({
        method: test.method,
        url: test.url,
        params: test.params
      });
      
      if (response.data.success) {
        success(`${test.name} - 成功`, {
          dataType: Array.isArray(response.data.data) ? 'array' : typeof response.data.data,
          count: Array.isArray(response.data.data) ? response.data.data.length : 'N/A'
        });
      } else {
        error(`${test.name} - 失败`, response.data.message);
      }
    } catch (err) {
      error(`${test.name} - 异常`, err);
    }
    console.log('');
  }
}

// 测试简单交易API
async function testSimpleTradingAPI() {
  console.log('\n🔍 测试简单交易API...\n');
  
  const tests = [
    {
      name: '获取账户信息',
      method: 'GET',
      url: '/api/v1/simple-trading/account'
    },
    {
      name: '获取订单列表',
      method: 'GET',
      url: '/api/v1/simple-trading/orders'
    },
    {
      name: '获取持仓列表',
      method: 'GET',
      url: '/api/v1/simple-trading/positions'
    },
    {
      name: '获取交易状态',
      method: 'GET',
      url: '/api/v1/simple-trading/trading-status'
    }
  ];
  
  for (const test of tests) {
    try {
      log(`测试: ${test.name}`);
      const response = await api({
        method: test.method,
        url: test.url
      });
      
      if (response.data.success) {
        success(`${test.name} - 成功`, {
          dataType: Array.isArray(response.data.data) ? 'array' : typeof response.data.data,
          count: Array.isArray(response.data.data) ? response.data.data.length : 'N/A'
        });
      } else {
        error(`${test.name} - 失败`, response.data.message);
      }
    } catch (err) {
      error(`${test.name} - 异常`, err);
    }
    console.log('');
  }
}

// 测试算法交易API
async function testAlgoTradingAPI() {
  console.log('\n🔍 测试算法交易API...\n');
  
  const tests = [
    {
      name: '获取引擎状态',
      method: 'GET',
      url: '/api/v1/algo-trading/status'
    },
    {
      name: '获取活跃策略',
      method: 'GET',
      url: '/api/v1/algo-trading/strategies'
    },
    {
      name: '获取订单历史',
      method: 'GET',
      url: '/api/v1/algo-trading/orders',
      params: { limit: 10 }
    },
    {
      name: '获取信号历史',
      method: 'GET',
      url: '/api/v1/algo-trading/signals',
      params: { limit: 10 }
    }
  ];
  
  for (const test of tests) {
    try {
      log(`测试: ${test.name}`);
      const response = await api({
        method: test.method,
        url: test.url,
        params: test.params
      });
      
      if (response.data.success) {
        success(`${test.name} - 成功`, {
          dataType: Array.isArray(response.data.data) ? 'array' : typeof response.data.data,
          count: Array.isArray(response.data.data) ? response.data.data.length : 'N/A'
        });
      } else {
        error(`${test.name} - 失败`, response.data.message);
      }
    } catch (err) {
      error(`${test.name} - 异常`, err);
    }
    console.log('');
  }
}

// 测试下单功能
async function testOrderPlacement() {
  console.log('\n🔍 测试下单功能...\n');
  
  const testOrder = {
    symbol: 'SHFE.cu2601',
    direction: 'BUY',
    volume: 1,
    price: 71000,
    order_type: 'LIMIT'
  };
  
  try {
    log('测试简单交易下单');
    const response = await api.post('/api/v1/simple-trading/orders', testOrder);
    
    if (response.data.success) {
      success('下单测试成功', response.data.data);
      
      // 如果下单成功，尝试撤单
      const orderId = response.data.data?.order_id;
      if (orderId) {
        try {
          log(`尝试撤销订单: ${orderId}`);
          const cancelResponse = await api.delete(`/api/v1/simple-trading/orders/${orderId}`);
          
          if (cancelResponse.data.success) {
            success('撤单测试成功');
          } else {
            error('撤单测试失败', cancelResponse.data.message);
          }
        } catch (err) {
          error('撤单测试异常', err);
        }
      }
    } else {
      error('下单测试失败', response.data.message);
    }
  } catch (err) {
    error('下单测试异常', err);
  }
}

// 主测试函数
async function runTests() {
  console.log('🚀 开始订单管理API集成测试\n');
  console.log('=' * 50);
  
  // 1. 认证
  const authSuccess = await authenticate();
  if (!authSuccess) {
    console.log('\n❌ 认证失败，终止测试');
    process.exit(1);
  }
  
  // 2. 测试各个API
  await testOrdersAPI();
  await testSimpleTradingAPI();
  await testAlgoTradingAPI();
  
  // 3. 测试下单功能（可选，会产生实际订单）
  const shouldTestOrders = process.argv.includes('--test-orders');
  if (shouldTestOrders) {
    await testOrderPlacement();
  } else {
    console.log('\n💡 提示: 使用 --test-orders 参数来测试实际下单功能');
  }
  
  console.log('\n✅ 订单管理API集成测试完成');
  console.log('=' * 50);
}

// 运行测试
if (require.main === module) {
  runTests().catch(err => {
    console.error('\n💥 测试运行失败:', err);
    process.exit(1);
  });
}

module.exports = {
  runTests,
  authenticate,
  testOrdersAPI,
  testSimpleTradingAPI,
  testAlgoTradingAPI
};