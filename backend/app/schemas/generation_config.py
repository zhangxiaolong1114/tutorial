"""
生成配置 Schema
Pydantic 模型用于请求/响应验证
"""
from typing import List, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime


class GenerationConfigBase(BaseModel):
    """生成配置基础模型"""
    
    # 风格层
    tone: str = Field(default="formal", description="语气风格")
    
    # 结构层
    teaching_style: str = Field(default="progressive", description="教学风格")
    content_style: str = Field(default="detailed", description="内容样式")
    
    # 深度层
    difficulty: str = Field(default="intermediate", description="难度等级")
    formula_detail: str = Field(default="derivation", description="公式详细度")
    
    # 受众与格式
    target_audience: str = Field(default="undergraduate", description="目标受众")
    output_format: str = Field(default="lecture", description="输出格式")
    code_language: str = Field(default="python", description="代码语言")
    
    # 内容细节
    chapter_granularity: str = Field(default="standard", description="章节粒度")
    citation_style: str = Field(default="none", description="引用规范")
    interactive_elements: str = Field(default="exercise", description="互动元素")
    
    # 仿真配置
    need_simulation: bool = Field(default=False, description="是否需要仿真")
    simulation_types: List[str] = Field(default_factory=list, description="仿真类型列表")
    
    # 其他
    need_images: bool = Field(default=False, description="是否需要配图")
    
    # 有效值验证
    @validator('tone')
    def validate_tone(cls, v):
        valid = ['formal', 'casual', 'rigorous']
        if v not in valid:
            raise ValueError(f'tone must be one of {valid}')
        return v
    
    @validator('teaching_style')
    def validate_teaching_style(cls, v):
        valid = ['progressive', 'case_driven', 'problem_based', 'comparative']
        if v not in valid:
            raise ValueError(f'teaching_style must be one of {valid}')
        return v
    
    @validator('content_style')
    def validate_content_style(cls, v):
        valid = ['concise', 'detailed', 'visual', 'formula_heavy']
        if v not in valid:
            raise ValueError(f'content_style must be one of {valid}')
        return v
    
    @validator('difficulty')
    def validate_difficulty(cls, v):
        valid = ['beginner', 'intermediate', 'advanced']
        if v not in valid:
            raise ValueError(f'difficulty must be one of {valid}')
        return v
    
    @validator('formula_detail')
    def validate_formula_detail(cls, v):
        valid = ['conclusion_only', 'derivation', 'full_proof']
        if v not in valid:
            raise ValueError(f'formula_detail must be one of {valid}')
        return v
    
    @validator('target_audience')
    def validate_target_audience(cls, v):
        valid = ['undergraduate', 'graduate', 'engineer', 'high_school']
        if v not in valid:
            raise ValueError(f'target_audience must be one of {valid}')
        return v
    
    @validator('output_format')
    def validate_output_format(cls, v):
        valid = ['lecture', 'ppt_outline', 'lab_manual', 'cheatsheet']
        if v not in valid:
            raise ValueError(f'output_format must be one of {valid}')
        return v
    
    @validator('code_language')
    def validate_code_language(cls, v):
        valid = ['python', 'java', 'cpp', 'pseudocode', 'none']
        if v not in valid:
            raise ValueError(f'code_language must be one of {valid}')
        return v
    
    @validator('chapter_granularity')
    def validate_chapter_granularity(cls, v):
        valid = ['brief', 'standard', 'detailed']
        if v not in valid:
            raise ValueError(f'chapter_granularity must be one of {valid}')
        return v
    
    @validator('citation_style')
    def validate_citation_style(cls, v):
        valid = ['none', 'simple', 'academic']
        if v not in valid:
            raise ValueError(f'citation_style must be one of {valid}')
        return v
    
    @validator('interactive_elements')
    def validate_interactive_elements(cls, v):
        valid = ['thinking', 'exercise', 'quiz', 'none']
        if v not in valid:
            raise ValueError(f'interactive_elements must be one of {valid}')
        return v
    
    @validator('simulation_types', each_item=True)
    def validate_simulation_types(cls, v):
        valid = ['animation', 'interactive']
        if v not in valid:
            raise ValueError(f'simulation_types items must be one of {valid}')
        return v


class GenerationConfigCreate(GenerationConfigBase):
    """创建配置请求模型"""
    pass


class GenerationConfigResponse(GenerationConfigBase):
    """配置响应模型"""
    id: int
    user_id: int
    created_at: str  # 返回格式化后的字符串

    class Config:
        from_attributes = True

    @validator('simulation_types', pre=True)
    def parse_simulation_types(cls, v):
        """将数据库字符串转换为列表"""
        if isinstance(v, str):
            if not v:
                return []
            return [t.strip() for t in v.split(',') if t.strip()]
        return v if v else []

    @validator('created_at', pre=True)
    def format_created_at(cls, v):
        """格式化时间为本地时间字符串"""
        if isinstance(v, datetime):
            return v.strftime('%Y-%m-%d %H:%M:%S')
        return v


class GenerationConfigHistory(BaseModel):
    """配置历史列表响应"""
    configs: List[GenerationConfigResponse]
    total: int


class GenerationConfigApply(BaseModel):
    """应用配置到生成任务"""
    config_id: Optional[int] = Field(default=None, description="要应用的配置ID，None表示使用默认")
    course: str = Field(..., description="课程名称")
    knowledge_point: str = Field(..., description="知识点")
