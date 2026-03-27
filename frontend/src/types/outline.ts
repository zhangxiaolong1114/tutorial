// 大纲类型定义

export interface Section {
  id: string
  title: string
  content: string[] | string
  order: number
  children?: Section[]
  prerequisites?: string[] | string
  prepares_for?: string[] | string
  key_formulas?: string[] | string
}

export interface Outline {
  id: string
  course: string
  knowledge_point: string
  difficulty: 'easy' | 'medium' | 'hard'
  title: string
  sections: Section[]
  status: 'draft' | 'generating' | 'completed'
  created_at: string
}

import type { GenerationConfigCreate } from './generationConfig'
import type { ModelConfig } from '../api/aiModels'

export interface GenerateOutlineRequest {
  course: string
  knowledge_point: string
  difficulty: 'easy' | 'medium' | 'hard'
  config?: GenerationConfigCreate  // 可选的生成配置
  model_config?: ModelConfig  // 可选的模型配置
}

export interface UpdateOutlineRequest {
  sections: Section[]
}

// 任务相关类型
export interface TaskResponse {
  task_id: number
  status: string
  message: string
}

export interface ProgressDetail {
  phase?: string
  current_section?: string
  section_index?: number
  total_sections?: number
  message?: string
}

export interface ModelUsage {
  task: string
  model_id: string
  section?: string
}

export interface TaskStatusResponse {
  task_id: number
  status: 'pending' | 'processing' | 'completed' | 'failed'
  task_type: string
  created_at: string
  started_at?: string
  completed_at?: string
  result?: {
    outline_id?: number
    document_id?: number
    title?: string
    models_used?: ModelUsage[]
  }
  error_message?: string
  progress: number  // 0-100
  progress_detail?: ProgressDetail
  models_used?: ModelUsage[]
}
