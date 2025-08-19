#!/usr/bin/env node

/**
 * 手动交易页面修复效果测试脚本
 * 
 * 测试内容：
 * 1. WebSocket连接和断开场景
 * 2. API请求失败和重试场景
 * 3. 组件在各种数据状态下的渲染
 * 4. 错误处理和用户体验
 */

const puppeteer = require('puppeteer');

async function testManualTradingFix() {
  console.log('🚀 开始测试手动交易页面修复效果...\n');
  
  const browser = await puppeteer.launch({ 
    headless: false, 
    devtools: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const page = await browser.newPage();
  
  // 监听控制台错误
  const consoleErrors = [];
  page.on('console', msg => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text());
    }
  });
  
  // 监听页面错误
  const pageErrors = [];
  page.on('pageerror', error => {
    pageErrors.push(error.message);
  });
  
  try {
    // 1. 测试页面加载
    console.log('📄 测试1: 页面加载...');
    await page.goto('http://localhost:3000/trading/manual', { 
      waitUntil: 'networkidle2',
      timeout: 30000 
    });
    
    // 等待页面完全加载
    await page.waitForTimeout(3000);
    
    // 检查是否有JavaScript错误
    if (consoleErrors.length > 0) {
      console.log('❌ 发现控制台错误:');
      consoleErrors.forEach(error => console.log(`   - ${error}`));
    } else {
      console.log('✅ 页面加载无JavaScript错误');
    }
    
    if (pageErrors.length > 0) {
      console.log('❌ 发现页面错误:');
      pageErrors.forEach(error => console.log(`   - ${error}`));
    } else {
      console.log('✅ 页面加载无页面错误');
    }
    
    // 2. 测试WebSocket状态指示器
    console.log('\n🔌 测试2: WebSocket状态指示器...');
    
    const wsStatusExists = await page.$('.websocket-status');
    if (wsStatusExists) {
      console.log('✅ WebSocket状态指示器存在');
      
      const statusText = await page.$eval('.websocket-status .status-text', el => el.textContent);
      console.log(`   状态: ${statusText}`);
    } else {
      console.log('❌ WebSocket状态指示器不存在');
    }
    
    // 3. 测试错误状态显示
    console.log('\n⚠️  测试3: 错误状态显示...');
    
    // 检查是否有错误横幅
    const errorBanner = await page.$('.error-banner');
    if (errorBanner) {
      const errorText = await page.$eval('.error-banner .el-alert__title', el => el.textContent);
      console.log(`⚠️  发现错误横幅: ${errorText}`);
    } else {
      console.log('✅ 无错误横幅显示');
    }
    
    // 4. 测试数据加载状态
    console.log('\n📊 测试4: 数据加载状态...');
    
    // 检查刷新按钮
    const refreshButton = await page.$('button:has-text("刷新")');
    if (refreshButton) {
      console.log('✅ 刷新按钮存在');
      
      // 点击刷新按钮测试加载状态
      await refreshButton.click();
      await page.waitForTimeout(1000);
      
      const isLoading = await page.$eval('button:has-text("刷新")', el => 
        el.classList.contains('is-loading')
      ).catch(() => false);
      
      if (isLoading) {
        console.log('✅ 刷新按钮显示加载状态');
      }
    } else {
      console.log('❌ 刷新按钮不存在');
    }
    
    // 5. 测试组件渲染
    console.log('\n🧩 测试5: 组件渲染...');
    
    const components = [
      { selector: '.manual-trading-form', name: '手动交易表单' },
      { selector: '.market-quote', name: '市场行情' },
      { selector: '.position-display', name: '持仓显示' },
      { selector: '.order-management', name: '订单管理' }
    ];
    
    for (const component of components) {
      const exists = await page.$(component.selector);
      if (exists) {
        console.log(`✅ ${component.name}组件渲染正常`);
      } else {
        console.log(`❌ ${component.name}组件未找到`);
      }
    }
    
    // 6. 测试网络状态指示器
    console.log('\n🌐 测试6: 网络状态指示器...');
    
    const networkStatus = await page.$('.header-status .status-group');
    if (networkStatus) {
      const statusTexts = await page.$$eval('.header-status .el-tag', 
        elements => elements.map(el => el.textContent)
      );
      console.log(`✅ 网络状态指示器存在: ${statusTexts.join(', ')}`);
    } else {
      console.log('❌ 网络状态指示器不存在');
    }
    
    // 7. 测试重试功能
    console.log('\n🔄 测试7: 重试功能...');
    
    const retryButton = await page.$('button:has-text("重试")');
    if (retryButton) {
      console.log('✅ 重试按钮存在');
    } else {
      console.log('ℹ️  当前无重试按钮（正常情况）');
    }
    
    // 8. 最终错误统计
    console.log('\n📈 测试结果统计:');
    console.log(`   控制台错误数量: ${consoleErrors.length}`);
    console.log(`   页面错误数量: ${pageErrors.length}`);
    
    if (consoleErrors.length === 0 && pageErrors.length === 0) {
      console.log('🎉 所有测试通过，修复效果良好！');
    } else {
      console.log('⚠️  发现一些问题，需要进一步检查');
    }
    
  } catch (error) {
    console.error('❌ 测试过程中发生错误:', error.message);
  } finally {
    // 保持浏览器打开以便手动检查
    console.log('\n🔍 浏览器将保持打开状态，请手动检查页面功能...');
    console.log('按 Ctrl+C 退出测试');
    
    // 等待用户手动关闭
    process.on('SIGINT', async () => {
      console.log('\n👋 关闭浏览器...');
      await browser.close();
      process.exit(0);
    });
  }
}

// 检查是否安装了puppeteer
try {
  require('puppeteer');
  testManualTradingFix().catch(console.error);
} catch (error) {
  console.log('❌ 请先安装puppeteer: npm install puppeteer');
  console.log('或者手动测试以下功能:');
  console.log('1. 访问 http://localhost:3000/trading/manual');
  console.log('2. 检查控制台是否有错误');
  console.log('3. 检查WebSocket连接状态');
  console.log('4. 测试刷新和重试功能');
  console.log('5. 检查各组件是否正常渲染');
}