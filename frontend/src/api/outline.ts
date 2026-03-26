import api from './index'
import type { Outline, GenerateOutlineRequest, UpdateOutlineRequest, TaskResponse, TaskStatusResponse } from '../types/outline'
import type { ModelConfig } from './aiModels'

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
export const generateDocument = async (id: string, modelConfig?: ModelConfig): Promise<TaskResponse> => {
  return api.post<TaskResponse>(`/outlines/${id}/generate-doc`, { model_config: modelConfig })
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
