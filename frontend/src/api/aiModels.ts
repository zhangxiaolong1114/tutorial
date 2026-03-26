// AI 模型管理 API
import api from './index'

export interface ModelInfo {
  id: string
  name: string
  provider: string
  model_id: string
  supports_temperature: boolean
  default_temperature: number
  max_tokens: number
  input_price_per_1k: number
  output_price_per_1k: number
  speed_score: number
  quality_score: number
  is_default: boolean
  is_enabled: boolean
  is_premium: boolean
  supported_tasks: string[]
}

export interface ModelRecommendation extends ModelInfo {
  value_score: number
  reasons: string[]
}

export interface TaskModelConfig {
  task: 'outline' | 'section' | 'simulation'
  model_id: string
  temperature: number
  custom_prompt_suffix: string
}

export interface ModelConfig {
  outline_model_id?: string
  section_model_id?: string
  simulation_model_id?: string
}

export const aiModelsApi = {
  // 获取可用模型列表
  getModels: (taskType?: string) => {
    const params = taskType ? { task_type: taskType } : undefined
    return api.get<ModelInfo[]>('/api/ai-models/list', { params })
  },

  // 获取推荐模型
  getRecommendations: (taskType: string) => {
    return api.get<ModelRecommendation[]>(`/api/ai-models/recommendations/${taskType}`)
  },

  // 获取默认模型配置
  getDefaults: () => {
    return api.get<Record<string, ModelInfo>>('/api/ai-models/defaults')
  },

  // 保存任务模型配置
  saveTaskConfig: (config: TaskModelConfig) => {
    return api.post<TaskModelConfig>('/api/ai-models/task-config', config)
  },

  // 对比模型
  compareModels: (modelIds: string[]) => {
    return api.get<ModelInfo[]>('/api/ai-models/compare', {
      params: { model_ids: modelIds.join(',') }
    })
  },

  // 获取价格概览
  getPricing: () => {
    return api.get<Array<{
      id: string
      name: string
      provider: string
      input_price: number
      output_price: number
      cost_10k_tokens: number
    }>>('/api/ai-models/pricing')
  }
}

export default aiModelsApi
