import api from './index'
import type { Outline, GenerateOutlineRequest, UpdateOutlineRequest, TaskResponse, TaskStatusResponse } from '../types/outline'
import type { ModelConfig } from './aiModels'
import type { GenerationConfigCreate } from '../types/generationConfig'

// 生成大纲（异步）
export const generateOutline = async (data: GenerateOutlineRequest): Promise<TaskResponse> => {
  return api.post<TaskResponse>('/outlines/generate', data)
}

// 获取大纲
export const getOutline = async (id: string): Promise<Outline> => {
  return api.get<Outline>(`/outlines/${id}`)
}

// 更新大纲
export const updateOutline = async (id: string, data: UpdateOutlineRequest): Promise<Outline> => {
  return api.put<Outline>(`/outlines/${id}`, data)
}

// 生成文档（异步）
export const generateDocument = async (
  id: string,
  modelConfig?: ModelConfig,
  generationConfig?: Partial<GenerationConfigCreate>
): Promise<TaskResponse> => {
  const requestData: Record<string, unknown> = {}
  // 只有当 modelConfig 有实际内容时才添加
  if (modelConfig && (modelConfig.outline_model_id || modelConfig.section_model_id || modelConfig.simulation_model_id)) {
    requestData.ai_model_config = modelConfig
  }
  // 传入大纲保存的生成配置（含 output_format），与大纲一致
  if (generationConfig && Object.keys(generationConfig).length > 0) {
    requestData.config = generationConfig
  }
  return api.post<TaskResponse>(`/outlines/${id}/generate-doc`, requestData)
}

// 获取任务状态
export const getTaskStatus = async (taskId: number): Promise<TaskStatusResponse> => {
  return api.get<TaskStatusResponse>(`/outlines/tasks/${taskId}`)
}

// 获取任务列表
export const listTasks = async (status?: string): Promise<TaskStatusResponse[]> => {
  const params = status ? { status } : undefined
  return api.get<TaskStatusResponse[]>('/outlines/tasks', { params })
}
