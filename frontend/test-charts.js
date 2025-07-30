#!/usr/bin/env node

/**
 * 图表组件功能测试脚本
 * 验证 ECharts 配置和组件是否正常工作
 */

const fs = require('fs')
const path = require('path')

console.log('🔍 开始测试图表组件功能...\n')

// 测试结果
const testResults = {
  passed: 0,
  failed: 0,
  errors: []
}

// 测试函数
function test(name, testFn) {
  try {
    console.log(`📋 测试: ${name}`)
    const result = testFn()
    if (result) {
      console.log(`✅ 通过: ${name}`)
      testResults.passed++
    } else {
      console.log(`❌ 失败: ${name}`)
      testResults.failed++
      testResults.errors.push(name)
    }
  } catch (error) {
    console.log(`❌ 错误: ${name} - ${error.message}`)
    testResults.failed++
    testResults.errors.push(`${name}: ${error.message}`)
  }
  console.log('')
}

// 1. 测试 ECharts 配置文件存在
test('ECharts 配置文件存在', () => {
  const echartsConfigPath = path.join(__dirname, 'src/utils/echarts.ts')
  return fs.existsSync(echartsConfigPath)
})

// 2. 测试 ECharts 配置内容
test('ECharts 配置内容正确', () => {
  const echartsConfigPath = path.join(__dirname, 'src/utils/echarts.ts')
  if (!fs.existsSync(echartsConfigPath)) return false
  
  const content = fs.readFileSync(echartsConfigPath, 'utf8')
  
  // 检查必要的导入
  const requiredImports = [
    'use',
    'CanvasRenderer',
    'LineChart',
    'PieChart',
    'BarChart',
    'TitleComponent',
    'TooltipComponent',
    'LegendComponent'
  ]
  
  return requiredImports.every(imp => content.includes(imp))
})

// 3. 测试 main.ts 中的 ECharts 导入
test('main.ts 中正确导入 ECharts', () => {
  const mainPath = path.join(__dirname, 'src/main.ts')
  if (!fs.existsSync(mainPath)) return false
  
  const content = fs.readFileSync(mainPath, 'utf8')
  return content.includes('./utils/echarts')
})

// 4. 测试 RealTimeChart 组件存在
test('RealTimeChart 组件存在', () => {
  const componentPath = path.join(__dirname, 'src/components/RealTimeChart.vue')
  return fs.existsSync(componentPath)
})

// 5. 测试 RealTimeChart 组件使用 vue-echarts
test('RealTimeChart 组件使用 vue-echarts', () => {
  const componentPath = path.join(__dirname, 'src/components/RealTimeChart.vue')
  if (!fs.existsSync(componentPath)) return false
  
  const content = fs.readFileSync(componentPath, 'utf8')
  return content.includes('vue-echarts') && content.includes('v-chart')
})

// 6. 测试 DashboardView 使用图表组件
test('DashboardView 使用图表组件', () => {
  const dashboardPath = path.join(__dirname, 'src/views/dashboard/DashboardView.vue')
  if (!fs.existsSync(dashboardPath)) return false
  
  const content = fs.readFileSync(dashboardPath, 'utf8')
  return content.includes('RealTimeChart') && content.includes('v-chart')
})

// 7. 测试 package.json 中的依赖
test('package.json 包含必要的图表依赖', () => {
  const packagePath = path.join(__dirname, 'package.json')
  if (!fs.existsSync(packagePath)) return false
  
  const packageJson = JSON.parse(fs.readFileSync(packagePath, 'utf8'))
  const deps = { ...packageJson.dependencies, ...packageJson.devDependencies }
  
  return deps.echarts && deps['vue-echarts']
})

// 8. 测试 vite 配置中的 ECharts 优化
test('vite 配置包含 ECharts 优化', () => {
  const viteConfigPath = path.join(__dirname, 'vite.config.ts')
  if (!fs.existsSync(viteConfigPath)) return false
  
  const content = fs.readFileSync(viteConfigPath, 'utf8')
  return content.includes('echarts') && content.includes('vue-echarts')
})

// 9. 测试简化 vite 配置
test('简化 vite 配置包含 ECharts', () => {
  const viteSimpleConfigPath = path.join(__dirname, 'vite.config.simple.ts')
  if (!fs.existsSync(viteSimpleConfigPath)) return false
  
  const content = fs.readFileSync(viteSimpleConfigPath, 'utf8')
  return content.includes('echarts') && content.includes('vue-echarts')
})

// 10. 测试图表组件文件完整性
test('所有图表组件文件存在', () => {
  const chartComponents = [
    'src/components/RealTimeChart.vue',
    'src/components/BacktestResultReport.vue',
    'src/components/StrategyPerformanceMonitor.vue',
    'src/components/BacktestTradeRecords.vue'
  ]
  
  return chartComponents.every(component => {
    const componentPath = path.join(__dirname, component)
    return fs.existsSync(componentPath)
  })
})

// 11. 测试 Dockerfile 优化
test('Dockerfile 包含必要的构建步骤', () => {
  const dockerfilePath = path.join(__dirname, 'Dockerfile')
  if (!fs.existsSync(dockerfilePath)) return false
  
  const content = fs.readFileSync(dockerfilePath, 'utf8')
  return content.includes('npm ci') && content.includes('sass-embedded')
})

// 12. 测试 .dockerignore 文件
test('.dockerignore 文件存在', () => {
  const dockerignorePath = path.join(__dirname, '.dockerignore')
  return fs.existsSync(dockerignorePath)
})

// 运行所有测试
console.log('🚀 开始执行测试...\n')

// 执行测试（这里只是模拟，实际测试在上面的 test 函数中）

// 输出测试结果
console.log('📊 测试结果汇总:')
console.log('=' * 50)
console.log(`✅ 通过: ${testResults.passed}`)
console.log(`❌ 失败: ${testResults.failed}`)
console.log(`📈 成功率: ${((testResults.passed / (testResults.passed + testResults.failed)) * 100).toFixed(1)}%`)

if (testResults.errors.length > 0) {
  console.log('\n❌ 失败的测试:')
  testResults.errors.forEach((error, index) => {
    console.log(`  ${index + 1}. ${error}`)
  })
}

console.log('\n' + '=' * 50)

if (testResults.failed === 0) {
  console.log('🎉 所有图表组件测试通过！')
  process.exit(0)
} else {
  console.log('⚠️  部分测试失败，请检查上述错误')
  process.exit(1)
}