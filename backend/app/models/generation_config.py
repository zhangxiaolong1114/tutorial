"""
生成配置模型
存储用户的内容生成偏好配置和历史记录
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index, Text
from sqlalchemy.orm import relationship

from app.core.database import Base, get_now


class GenerationConfig(Base):
    """生成配置模型 - 存储用户的内容生成偏好"""
    __tablename__ = "generation_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # === 风格层配置 ===
    # 语气: formal(正式学术), casual(轻松通俗), rigorous(严谨专业)
    tone = Column(String(20), nullable=False, default="formal")
    
    # === 结构层配置 ===
    # 教学风格: progressive(循序渐进), case_driven(案例驱动), problem_based(问题导向), comparative(对比分析)
    teaching_style = Column(String(30), nullable=False, default="progressive")
    # 内容样式: concise(简洁), detailed(详细), visual(图文并茂), formula_heavy(公式密集)
    content_style = Column(String(20), nullable=False, default="detailed")
    
    # === 深度层配置 ===
    # 难度: beginner(入门), intermediate(进阶), advanced(高级)
    difficulty = Column(String(20), nullable=False, default="intermediate")
    # 公式详细度: conclusion_only(仅结论), derivation(推导过程), full_proof(完整证明)
    formula_detail = Column(String(20), nullable=False, default="derivation")
    
    # === 受众与格式配置 ===
    # 目标受众: undergraduate(本科生), graduate(研究生), engineer(工程师), high_school(高中生)
    target_audience = Column(String(30), nullable=False, default="undergraduate")
    # 输出格式: lecture(讲义), lab_manual(实验手册), cheatsheet(速查表)
    output_format = Column(String(20), nullable=False, default="lecture")
    # 代码语言: python, java, cpp, pseudocode(伪代码), none(无代码)
    code_language = Column(String(20), nullable=False, default="python")
    
    # === 内容细节配置 ===
    # 章节粒度: brief(精简3-5节), standard(标准6-10节), detailed(详细10+节)
    chapter_granularity = Column(String(20), nullable=False, default="standard")
    # 引用规范: none(无), simple(简单标注), academic(标准学术引用)
    citation_style = Column(String(20), nullable=False, default="none")
    # 互动元素: thinking(思考题), exercise(练习题), quiz(小测验), none(无)
    interactive_elements = Column(String(30), nullable=False, default="exercise")
    
    # === 仿真配置 ===
    # 是否需要仿真
    need_simulation = Column(Boolean, nullable=False, default=False)
    # 仿真类型: animation(动画演示), interactive(交互实验), 逗号分隔多选
    simulation_types = Column(String(50), nullable=False, default="")
    
    # === 其他配置 ===
    # 是否需要配图建议
    need_images = Column(Boolean, nullable=False, default=False)
    
    # 关联用户
    user = relationship("User", backref="generation_configs")
    
    created_at = Column(DateTime, default=get_now, nullable=False)
    
    # 索引
    __table_args__ = (
        Index('idx_gen_config_user_created', 'user_id', 'created_at'),
    )
    
    def get_simulation_types_list(self) -> list:
        """将仿真类型字符串转换为列表"""
        if not self.simulation_types:
            return []
        return [t.strip() for t in self.simulation_types.split(',') if t.strip()]
    
    def set_simulation_types_list(self, types: list):
        """将仿真类型列表转换为字符串"""
        self.simulation_types = ','.join(types) if types else ""
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "tone": self.tone,
            "teaching_style": self.teaching_style,
            "content_style": self.content_style,
            "difficulty": self.difficulty,
            "formula_detail": self.formula_detail,
            "target_audience": self.target_audience,
            "output_format": self.output_format,
            "code_language": self.code_language,
            "chapter_granularity": self.chapter_granularity,
            "citation_style": self.citation_style,
            "interactive_elements": self.interactive_elements,
            "need_simulation": self.need_simulation,
            "simulation_types": self.get_simulation_types_list(),
            "need_images": self.need_images,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
