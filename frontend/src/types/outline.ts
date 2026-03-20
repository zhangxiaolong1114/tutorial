// 大纲类型定义

export interface Section {
  id: string
  title: string
  content: string[] | string
  order: number
  children?: Section[]
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

export interface GenerateOutlineRequest {
  course: string
  knowledge_point: string
  difficulty: 'easy' | 'medium' | 'hard'
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
  }
  error_message?: string
}
