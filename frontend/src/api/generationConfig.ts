// 生成配置 API
import api from './index'
import type { 
  GenerationConfig, 
  GenerationConfigCreate, 
  GenerationConfigHistory 
} from '@/types/generationConfig'

export const generationConfigApi = {
  // 创建配置
  create: (data: GenerationConfigCreate): Promise<GenerationConfig> =>
    api.post<GenerationConfig>('/generation-configs', data),

  // 获取配置历史
  getHistory: (limit?: number): Promise<GenerationConfigHistory> =>
    api.get<GenerationConfigHistory>('/generation-configs', { params: limit ? { limit: String(limit) } : undefined }),

  // 获取最新配置
  getLatest: (): Promise<GenerationConfig | null> =>
    api.get<GenerationConfig | null>('/generation-configs/latest'),

  // 获取指定配置
  getById: (id: number): Promise<GenerationConfig> =>
    api.get<GenerationConfig>(`/generation-configs/${id}`),

  // 删除配置
  delete: (id: number): Promise<void> =>
    api.delete<void>(`/generation-configs/${id}`),
}

export default generationConfigApi
