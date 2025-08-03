/**
 * 策略管理API服务
 */

import { request } from '@/utils/request'
import type { ApiResponse, PaginatedResponse } from '@/types/api'

/**
 * 策略API服务类
 */
export class StrategyApi {
  /**
   * 创建策略
   */
  static async createStrategy(data: any): Promise<ApiResponse<any>> {
    return request.post('/strategies', data)
  }

  /**
   * 获取策略列表
   */
  static async getStrategies(params?: any): Promise<ApiResponse<PaginatedResponse<any>>> {
    return request.get('/strategies', { params })
  }

  /**
   * 获取我的策略
   */
  static async getMyStrategies(status?: string): Promise<ApiResponse<any[]>> {
    const params = status ? { status } : undefined
    return request.get('/strategies/my', { params })
  }

  /**
   * 获取策略统计
   */
  static async getStrategyStats(): Promise<ApiResponse<any>> {
    return request.get('/strategies/stats')
  }

  /**
   * 获取策略详情
   */
  static async getStrategy(id: string): Promise<ApiResponse<any>> {
    return request.get(`/strategies/${id}`)
  }

  /**
   * 根据UUID获取策略
   */
  static async getStrategyByUuid(uuid: string): Promise<ApiResponse<any>> {
    return request.get(`/strategies/uuid/${uuid}`)
  }

  /**
   * 更新策略
   */
  static async updateStrategy(id: string, data: any): Promise<ApiResponse<any>> {
    return request.put(`/strategies/${id}`, data)
  }

  /**
   * 删除策略
   */
  static async deleteStrategy(id: string): Promise<ApiResponse<any>> {
    return request.delete(`/strategies/${id}`)
  }

  /**
   * 复制策略
   */
  static async copyStrategy(id: string, data: any): Promise<ApiResponse<any>> {
    return request.post(`/strategies/${id}/copy`, data)
  }

  /**
   * 执行策略
   */
  static async executeStrategy(id: string, data: any): Promise<ApiResponse<any>> {
    return request.post(`/strategies/${id}/execute`, data)
  }

  /**
   * 获取策略版本列表
   */
  static async getStrategyVersions(id: string): Promise<ApiResponse<any[]>> {
    return request.get(`/strategies/${id}/versions`)
  }

  /**
   * 获取策略版本详情
   */
  static async getStrategyVersion(id: string, versionId: string): Promise<ApiResponse<any>> {
    return request.get(`/strategies/${id}/versions/${versionId}`)
  }

  /**
   * 恢复策略版本
   */
  static async restoreStrategyVersion(id: string, versionId: string): Promise<ApiResponse<any>> {
    return request.post(`/strategies/${id}/versions/${versionId}/restore`)
  }

  /**
   * 获取策略模板列表
   */
  static async getStrategyTemplates(): Promise<ApiResponse<any[]>> {
    return request.get('/strategies/templates')
  }

  /**
   * 获取策略模板详情
   */
  static async getStrategyTemplate(id: string): Promise<ApiResponse<any>> {
    return request.get(`/strategies/templates/${id}`)
  }

  /**
   * 从模板创建策略
   */
  static async createStrategyFromTemplate(templateId: string, data: any): Promise<ApiResponse<any>> {
    return request.post(`/strategies/templates/${templateId}/create`, data)
  }
}

// 导出便捷方法
export const {
  createStrategy,
  getStrategies,
  getMyStrategies,
  getStrategyStats,
  getStrategy,
  getStrategyByUuid,
  updateStrategy,
  deleteStrategy,
  copyStrategy,
  executeStrategy,
  getStrategyVersions,
  getStrategyVersion,
  restoreStrategyVersion,
  getStrategyTemplates,
  getStrategyTemplate,
  createStrategyFromTemplate
} = StrategyApi

// 创建策略API实例
export const strategyApi = StrategyApi