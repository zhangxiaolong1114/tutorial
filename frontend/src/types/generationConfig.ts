// 生成配置类型定义

// 语气风格
export type Tone = 'formal' | 'casual' | 'rigorous'

// 教学风格
export type TeachingStyle = 'progressive' | 'case_driven' | 'problem_based' | 'comparative'

// 内容样式
export type ContentStyle = 'concise' | 'detailed' | 'visual' | 'formula_heavy'

// 难度等级
export type Difficulty = 'beginner' | 'intermediate' | 'advanced'

// 公式详细度
export type FormulaDetail = 'conclusion_only' | 'derivation' | 'full_proof'

// 目标受众
export type TargetAudience = 'undergraduate' | 'graduate' | 'engineer' | 'high_school'

// 输出格式
export type OutputFormat = 'lecture' | 'ppt_outline' | 'lab_manual' | 'cheatsheet'

// 代码语言
export type CodeLanguage = 'python' | 'java' | 'cpp' | 'pseudocode' | 'none'

// 章节粒度
export type ChapterGranularity = 'brief' | 'standard' | 'detailed'

// 引用规范
export type CitationStyle = 'none' | 'simple' | 'academic'

// 互动元素
export type InteractiveElements = 'thinking' | 'exercise' | 'quiz' | 'none'

// 仿真类型
export type SimulationType = 'animation' | 'interactive'

// 生成配置接口
export interface GenerationConfig {
  id: number
  user_id: number
  
  // 风格层
  tone: Tone
  
  // 结构层
  teaching_style: TeachingStyle
  content_style: ContentStyle
  
  // 深度层
  difficulty: Difficulty
  formula_detail: FormulaDetail
  
  // 受众与格式
  target_audience: TargetAudience
  output_format: OutputFormat
  code_language: CodeLanguage
  
  // 内容细节
  chapter_granularity: ChapterGranularity
  citation_style: CitationStyle
  interactive_elements: InteractiveElements
  
  // 仿真配置
  need_simulation: boolean
  simulation_types: SimulationType[]
  
  // 其他
  need_images: boolean
  
  created_at: string
}

// 创建配置请求
export interface GenerationConfigCreate {
  tone: Tone
  teaching_style: TeachingStyle
  content_style: ContentStyle
  difficulty: Difficulty
  formula_detail: FormulaDetail
  target_audience: TargetAudience
  output_format: OutputFormat
  code_language: CodeLanguage
  chapter_granularity: ChapterGranularity
  citation_style: CitationStyle
  interactive_elements: InteractiveElements
  need_simulation: boolean
  simulation_types: SimulationType[]
  need_images: boolean
}

// 配置历史响应
export interface GenerationConfigHistory {
  configs: GenerationConfig[]
  total: number
}

// 配置选项标签映射
export const configLabels = {
  tone: {
    formal: '正式学术',
    casual: '轻松通俗',
    rigorous: '严谨专业'
  },
  teaching_style: {
    progressive: '循序渐进',
    case_driven: '案例驱动',
    problem_based: '问题导向',
    comparative: '对比分析'
  },
  content_style: {
    concise: '简洁明了',
    detailed: '详细全面',
    visual: '图文并茂',
    formula_heavy: '公式密集'
  },
  difficulty: {
    beginner: '入门',
    intermediate: '进阶',
    advanced: '高级'
  },
  formula_detail: {
    conclusion_only: '仅结论',
    derivation: '推导过程',
    full_proof: '完整证明'
  },
  target_audience: {
    undergraduate: '本科生',
    graduate: '研究生',
    engineer: '工程师',
    high_school: '高中生'
  },
  output_format: {
    lecture: '讲义',
    ppt_outline: 'PPT大纲',
    lab_manual: '实验手册',
    cheatsheet: '速查表'
  },
  code_language: {
    python: 'Python',
    java: 'Java',
    cpp: 'C++',
    pseudocode: '伪代码',
    none: '无代码'
  },
  chapter_granularity: {
    brief: '精简（3-5节）',
    standard: '标准（6-10节）',
    detailed: '详细（10+节）'
  },
  citation_style: {
    none: '无引用',
    simple: '简单标注',
    academic: '学术引用'
  },
  interactive_elements: {
    thinking: '思考题',
    exercise: '练习题',
    quiz: '小测验',
    none: '无互动'
  },
  simulation_types: {
    animation: '动画演示',
    interactive: '交互实验'
  }
}

// 默认配置
export const defaultConfig: GenerationConfigCreate = {
  tone: 'formal',
  teaching_style: 'progressive',
  content_style: 'detailed',
  difficulty: 'intermediate',
  formula_detail: 'derivation',
  target_audience: 'undergraduate',
  output_format: 'lecture',
  code_language: 'python',
  chapter_granularity: 'standard',
  citation_style: 'none',
  interactive_elements: 'exercise',
  need_simulation: false,
  simulation_types: [],
  need_images: false
}
