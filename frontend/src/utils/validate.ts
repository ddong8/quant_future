/**
 * 表单验证工具函数
 */

/**
 * 验证邮箱格式
 */
export function validateEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

/**
 * 验证手机号格式
 */
export function validatePhone(phone: string): boolean {
  const phoneRegex = /^1[3-9]\d{9}$/
  return phoneRegex.test(phone)
}

/**
 * 验证密码强度
 * @param password 密码
 * @param minLength 最小长度
 * @param requireSpecial 是否需要特殊字符
 */
export function validatePassword(
  password: string,
  minLength = 6,
  requireSpecial = false
): { valid: boolean; message: string } {
  if (password.length < minLength) {
    return {
      valid: false,
      message: `密码长度不能少于${minLength}位`
    }
  }
  
  if (requireSpecial) {
    const hasLetter = /[a-zA-Z]/.test(password)
    const hasNumber = /\d/.test(password)
    const hasSpecial = /[!@#$%^&*(),.?\":{}|<>]/.test(password)
    
    if (!hasLetter || !hasNumber || !hasSpecial) {
      return {
        valid: false,
        message: '密码必须包含字母、数字和特殊字符'
      }
    }
  }
  
  return { valid: true, message: '' }
}

/**
 * 验证数字范围
 */
export function validateNumberRange(
  value: number,
  min?: number,
  max?: number
): { valid: boolean; message: string } {
  if (min !== undefined && value < min) {
    return {
      valid: false,
      message: `数值不能小于${min}`
    }
  }
  
  if (max !== undefined && value > max) {
    return {
      valid: false,
      message: `数值不能大于${max}`
    }
  }
  
  return { valid: true, message: '' }
}

/**
 * 验证必填字段
 */
export function validateRequired(value: any): { valid: boolean; message: string } {
  if (value === null || value === undefined || value === '') {
    return {
      valid: false,
      message: '此字段为必填项'
    }
  }
  
  if (Array.isArray(value) && value.length === 0) {
    return {
      valid: false,
      message: '请至少选择一项'
    }
  }
  
  return { valid: true, message: '' }
}

/**
 * 验证字符串长度
 */
export function validateLength(
  value: string,
  min?: number,
  max?: number
): { valid: boolean; message: string } {
  const length = value ? value.length : 0
  
  if (min !== undefined && length < min) {
    return {
      valid: false,
      message: `长度不能少于${min}个字符`
    }
  }
  
  if (max !== undefined && length > max) {
    return {
      valid: false,
      message: `长度不能超过${max}个字符`
    }
  }
  
  return { valid: true, message: '' }
}

/**
 * 验证URL格式
 */
export function validateUrl(url: string): boolean {
  try {
    new URL(url)
    return true
  } catch {
    return false
  }
}

/**
 * 验证IP地址格式
 */
export function validateIP(ip: string): boolean {
  const ipRegex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/
  return ipRegex.test(ip)
}

/**
 * 验证身份证号格式
 */
export function validateIdCard(idCard: string): boolean {
  const idCardRegex = /(^\d{15}$)|(^\d{18}$)|(^\d{17}(\d|X|x)$)/
  return idCardRegex.test(idCard)
}

/**
 * 验证银行卡号格式
 */
export function validateBankCard(cardNumber: string): boolean {
  const bankCardRegex = /^\d{16,19}$/
  return bankCardRegex.test(cardNumber)
}

/**
 * 验证中文姓名
 */
export function validateChineseName(name: string): boolean {
  const chineseNameRegex = /^[\u4e00-\u9fa5]{2,4}$/
  return chineseNameRegex.test(name)
}

/**
 * 验证数字精度
 */
export function validatePrecision(
  value: number,
  precision: number
): { valid: boolean; message: string } {
  const valueStr = value.toString()
  const decimalIndex = valueStr.indexOf('.')
  
  if (decimalIndex !== -1) {
    const decimalPlaces = valueStr.length - decimalIndex - 1
    if (decimalPlaces > precision) {
      return {
        valid: false,
        message: `小数位数不能超过${precision}位`
      }
    }
  }
  
  return { valid: true, message: '' }
}

/**
 * 创建表单验证规则
 */
export function createValidationRules(config: {
  required?: boolean
  type?: 'email' | 'phone' | 'url' | 'number'
  min?: number
  max?: number
  minLength?: number
  maxLength?: number
  precision?: number
  pattern?: RegExp
  validator?: (value: any) => boolean | string
  message?: string
}) {
  const rules: any[] = []
  
  // 必填验证
  if (config.required) {
    rules.push({
      required: true,
      message: config.message || '此字段为必填项',
      trigger: 'blur'
    })
  }
  
  // 类型验证
  if (config.type) {
    let validator: (rule: any, value: any, callback: any) => void
    
    switch (config.type) {
      case 'email':
        validator = (rule, value, callback) => {
          if (value && !validateEmail(value)) {
            callback(new Error('请输入正确的邮箱格式'))
          } else {
            callback()
          }
        }
        break
      case 'phone':
        validator = (rule, value, callback) => {
          if (value && !validatePhone(value)) {
            callback(new Error('请输入正确的手机号格式'))
          } else {
            callback()
          }
        }
        break
      case 'url':
        validator = (rule, value, callback) => {
          if (value && !validateUrl(value)) {
            callback(new Error('请输入正确的URL格式'))
          } else {
            callback()
          }
        }
        break
      case 'number':
        validator = (rule, value, callback) => {
          if (value && isNaN(Number(value))) {
            callback(new Error('请输入有效的数字'))
          } else {
            callback()
          }
        }
        break
      default:
        validator = (rule, value, callback) => callback()
    }
    
    rules.push({ validator, trigger: 'blur' })
  }
  
  // 数值范围验证
  if (config.min !== undefined || config.max !== undefined) {
    rules.push({
      validator: (rule: any, value: any, callback: any) => {
        if (value !== null && value !== undefined && value !== '') {
          const result = validateNumberRange(Number(value), config.min, config.max)
          if (!result.valid) {
            callback(new Error(result.message))
          } else {
            callback()
          }
        } else {
          callback()
        }
      },
      trigger: 'blur'
    })
  }
  
  // 字符串长度验证
  if (config.minLength !== undefined || config.maxLength !== undefined) {
    rules.push({
      validator: (rule: any, value: any, callback: any) => {
        if (value) {
          const result = validateLength(value, config.minLength, config.maxLength)
          if (!result.valid) {
            callback(new Error(result.message))
          } else {
            callback()
          }
        } else {
          callback()
        }
      },
      trigger: 'blur'
    })
  }
  
  // 精度验证
  if (config.precision !== undefined) {
    rules.push({
      validator: (rule: any, value: any, callback: any) => {
        if (value !== null && value !== undefined && value !== '') {
          const result = validatePrecision(Number(value), config.precision!)
          if (!result.valid) {
            callback(new Error(result.message))
          } else {
            callback()
          }
        } else {
          callback()
        }
      },
      trigger: 'blur'
    })
  }
  
  // 正则验证
  if (config.pattern) {
    rules.push({
      pattern: config.pattern,
      message: config.message || '格式不正确',
      trigger: 'blur'
    })
  }
  
  // 自定义验证
  if (config.validator) {
    rules.push({
      validator: (rule: any, value: any, callback: any) => {
        const result = config.validator!(value)
        if (result === true) {
          callback()
        } else if (typeof result === 'string') {
          callback(new Error(result))
        } else {
          callback(new Error(config.message || '验证失败'))
        }
      },
      trigger: 'blur'
    })
  }
  
  return rules
}