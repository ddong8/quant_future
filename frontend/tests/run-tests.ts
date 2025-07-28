#!/usr/bin/env node

/**
 * 前端测试运行脚本
 */
import { spawn } from 'child_process'
import { existsSync, mkdirSync } from 'fs'
import { resolve } from 'path'

interface TestOptions {
  type?: 'unit' | 'integration' | 'e2e' | 'cross-browser' | 'all'
  watch?: boolean
  coverage?: boolean
  reporter?: 'verbose' | 'json' | 'html'
  browser?: 'chrome' | 'firefox' | 'safari' | 'edge'
  viewport?: 'mobile' | 'tablet' | 'desktop'
  parallel?: boolean
  bail?: boolean
}

class TestRunner {
  private options: TestOptions

  constructor(options: TestOptions = {}) {
    this.options = {
      type: 'all',
      watch: false,
      coverage: false,
      reporter: 'verbose',
      parallel: true,
      bail: false,
      ...options
    }
  }

  async run(): Promise<void> {
    console.log('🧪 启动前端测试...')
    
    // 创建必要的目录
    this.ensureDirectories()
    
    // 根据测试类型运行不同的测试
    switch (this.options.type) {
      case 'unit':
        await this.runUnitTests()
        break
      case 'integration':
        await this.runIntegrationTests()
        break
      case 'e2e':
        await this.runE2ETests()
        break
      case 'cross-browser':
        await this.runCrossBrowserTests()
        break
      case 'all':
        await this.runAllTests()
        break
      default:
        throw new Error(`未知的测试类型: ${this.options.type}`)
    }
  }

  private ensureDirectories(): void {
    const dirs = [
      'test-results',
      'coverage',
      'screenshots',
      'videos'
    ]

    dirs.forEach(dir => {
      const fullPath = resolve(process.cwd(), dir)
      if (!existsSync(fullPath)) {
        mkdirSync(fullPath, { recursive: true })
      }
    })
  }

  private async runUnitTests(): Promise<void> {
    console.log('📦 运行单元测试...')
    
    const args = [
      'vitest',
      'run',
      '--config', 'vitest.config.ts',
      'src/**/*.{test,spec}.{js,ts}'
    ]

    if (this.options.coverage) {
      args.push('--coverage')
    }

    if (this.options.watch) {
      args.splice(1, 1, 'watch')
    }

    await this.executeCommand('npx', args)
  }

  private async runIntegrationTests(): Promise<void> {
    console.log('🔗 运行集成测试...')
    
    const args = [
      'vitest',
      'run',
      '--config', 'vitest.config.ts',
      'tests/integration/**/*.test.{js,ts}'
    ]

    if (this.options.coverage) {
      args.push('--coverage')
    }

    if (this.options.watch) {
      args.splice(1, 1, 'watch')
    }

    await this.executeCommand('npx', args)
  }

  private async runE2ETests(): Promise<void> {
    console.log('🎭 运行E2E测试...')
    
    const args = [
      'vitest',
      'run',
      '--config', 'vitest.config.ts',
      'tests/e2e/**/*.test.{js,ts}'
    ]

    if (this.options.coverage) {
      args.push('--coverage')
    }

    if (this.options.watch) {
      args.splice(1, 1, 'watch')
    }

    await this.executeCommand('npx', args)
  }

  private async runCrossBrowserTests(): Promise<void> {
    console.log('🌐 运行跨浏览器兼容性测试...')
    
    const browsers = this.options.browser ? [this.options.browser] : ['chrome', 'firefox', 'safari', 'edge']
    
    for (const browser of browsers) {
      console.log(`🔍 测试浏览器: ${browser}`)
      
      const args = [
        'vitest',
        'run',
        '--config', 'vitest.config.ts',
        'tests/cross-browser/**/*.test.{js,ts}'
      ]

      // 设置浏览器环境变量
      const env = {
        ...process.env,
        TEST_BROWSER: browser,
        TEST_VIEWPORT: this.options.viewport || 'desktop'
      }

      await this.executeCommand('npx', args, { env })
    }
  }

  private async runAllTests(): Promise<void> {
    console.log('🚀 运行所有测试...')
    
    try {
      await this.runUnitTests()
      console.log('✅ 单元测试通过')
      
      await this.runIntegrationTests()
      console.log('✅ 集成测试通过')
      
      await this.runE2ETests()
      console.log('✅ E2E测试通过')
      
      await this.runCrossBrowserTests()
      console.log('✅ 跨浏览器测试通过')
      
      console.log('🎉 所有测试通过!')
    } catch (error) {
      console.error('❌ 测试失败:', error)
      process.exit(1)
    }
  }

  private executeCommand(command: string, args: string[], options: any = {}): Promise<void> {
    return new Promise((resolve, reject) => {
      const child = spawn(command, args, {
        stdio: 'inherit',
        shell: true,
        ...options
      })

      child.on('close', (code) => {
        if (code === 0) {
          resolve()
        } else {
          reject(new Error(`命令执行失败，退出码: ${code}`))
        }
      })

      child.on('error', (error) => {
        reject(error)
      })
    })
  }
}

// 解析命令行参数
function parseArgs(): TestOptions {
  const args = process.argv.slice(2)
  const options: TestOptions = {}

  for (let i = 0; i < args.length; i++) {
    const arg = args[i]
    
    switch (arg) {
      case '--type':
      case '-t':
        options.type = args[++i] as TestOptions['type']
        break
      case '--watch':
      case '-w':
        options.watch = true
        break
      case '--coverage':
      case '-c':
        options.coverage = true
        break
      case '--reporter':
      case '-r':
        options.reporter = args[++i] as TestOptions['reporter']
        break
      case '--browser':
      case '-b':
        options.browser = args[++i] as TestOptions['browser']
        break
      case '--viewport':
      case '-v':
        options.viewport = args[++i] as TestOptions['viewport']
        break
      case '--parallel':
      case '-p':
        options.parallel = true
        break
      case '--bail':
        options.bail = true
        break
      case '--help':
      case '-h':
        showHelp()
        process.exit(0)
        break
      default:
        console.warn(`未知参数: ${arg}`)
    }
  }

  return options
}

function showHelp(): void {
  console.log(`
前端测试运行器

用法: npm run test [选项]

选项:
  -t, --type <type>        测试类型 (unit|integration|e2e|cross-browser|all) [默认: all]
  -w, --watch             监听模式
  -c, --coverage          生成覆盖率报告
  -r, --reporter <type>   报告器类型 (verbose|json|html) [默认: verbose]
  -b, --browser <name>    指定浏览器 (chrome|firefox|safari|edge)
  -v, --viewport <size>   视口尺寸 (mobile|tablet|desktop) [默认: desktop]
  -p, --parallel          并行运行测试
  --bail                  遇到失败时立即停止
  -h, --help              显示帮助信息

示例:
  npm run test                           # 运行所有测试
  npm run test -- --type unit           # 只运行单元测试
  npm run test -- --type integration -c # 运行集成测试并生成覆盖率
  npm run test -- --type cross-browser -b chrome # 在Chrome中运行跨浏览器测试
  npm run test -- --watch               # 监听模式运行测试
`)
}

// 主函数
async function main(): Promise<void> {
  try {
    const options = parseArgs()
    const runner = new TestRunner(options)
    await runner.run()
  } catch (error) {
    console.error('❌ 测试运行失败:', error)
    process.exit(1)
  }
}

// 如果直接运行此脚本
if (require.main === module) {
  main()
}

export { TestRunner, TestOptions }