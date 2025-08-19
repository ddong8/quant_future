#!/usr/bin/env node

/**
 * 账户管理API测试脚本
 */

const API_BASE = 'http://localhost:8000/api/v1';

async function makeRequest(url, options = {}) {
  const fetch = (await import('node-fetch')).default;
  
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers
    },
    ...options
  });
  
  const data = await response.json();
  return { status: response.status, data };
}

async function testAccountAPI() {
  console.log('🧪 开始测试账户管理API...\n');
  
  try {
    // 1. 登录获取token
    console.log('1️⃣ 登录获取token...');
    const loginResponse = await makeRequest(`${API_BASE}/auth/login`, {
      method: 'POST',
      body: JSON.stringify({
        username: 'admin',
        password: 'admin123'
      })
    });
    
    if (loginResponse.status !== 200) {
      throw new Error(`登录失败: ${JSON.stringify(loginResponse.data)}`);
    }
    
    const token = loginResponse.data.data.access_token;
    console.log('✅ 登录成功，获取到token');
    
    // 2. 获取账户列表
    console.log('\n2️⃣ 获取账户列表...');
    const accountsResponse = await makeRequest(`${API_BASE}/accounts/`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    if (accountsResponse.status !== 200) {
      throw new Error(`获取账户列表失败: ${JSON.stringify(accountsResponse.data)}`);
    }
    
    console.log('✅ 账户列表获取成功:');
    console.log(JSON.stringify(accountsResponse.data, null, 2));
    
    // 3. 创建新账户
    console.log('\n3️⃣ 创建新账户...');
    const createResponse = await makeRequest(`${API_BASE}/accounts/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        account_name: '测试账户',
        broker: '测试券商',
        initial_balance: 100000
      })
    });
    
    if (createResponse.status !== 200) {
      throw new Error(`创建账户失败: ${JSON.stringify(createResponse.data)}`);
    }
    
    console.log('✅ 账户创建成功:');
    console.log(JSON.stringify(createResponse.data, null, 2));
    
    const newAccountId = createResponse.data.id;
    
    // 4. 获取单个账户详情
    console.log('\n4️⃣ 获取账户详情...');
    const accountResponse = await makeRequest(`${API_BASE}/accounts/${newAccountId}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    if (accountResponse.status !== 200) {
      throw new Error(`获取账户详情失败: ${JSON.stringify(accountResponse.data)}`);
    }
    
    console.log('✅ 账户详情获取成功:');
    console.log(JSON.stringify(accountResponse.data, null, 2));
    
    // 5. 再次获取账户列表验证
    console.log('\n5️⃣ 验证账户列表...');
    const finalAccountsResponse = await makeRequest(`${API_BASE}/accounts/`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    console.log('✅ 最终账户列表:');
    console.log(JSON.stringify(finalAccountsResponse.data, null, 2));
    
    console.log('\n🎉 所有测试通过！账户管理API工作正常');
    
  } catch (error) {
    console.error('❌ 测试失败:', error.message);
    process.exit(1);
  }
}

// 运行测试
testAccountAPI();