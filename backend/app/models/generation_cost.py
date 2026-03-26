"""
AI 生成成本统计模型
记录每次 AI 调用的 token 消耗和成本
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index, Text
from sqlalchemy.orm import relationship
import json

from app.core.database import Base, get_now


class GenerationCost(Base):
    """AI 生成成本记录"""
    __tablename__ = "generation_costs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id = Column(Integer, ForeignKey("task_queue.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # 关联的文档/大纲
    outline_id = Column(Integer, nullable=True, index=True)
    document_id = Column(Integer, nullable=True, index=True)
    
    # 生成内容信息
    course = Column(String(100), nullable=True)
    knowledge_point = Column(String(200), nullable=True)
    
    # 调用信息
    model_id = Column(String(50), nullable=False)  # 使用的模型ID
    model_name = Column(String(100), nullable=False)  # 模型显示名称
    provider = Column(String(50), nullable=False)  # 提供商
    task_type = Column(String(50), nullable=False)  # outline/section/simulation
    
    # Token 消耗
    input_tokens = Column(Integer, default=0)  # 输入 tokens
    output_tokens = Column(Integer, default=0)  # 输出 tokens
    total_tokens = Column(Integer, default=0)  # 总 tokens
    
    # 成本（元）
    input_cost = Column(Float, default=0.0)  # 输入成本
    output_cost = Column(Float, default=0.0)  # 输出成本
    total_cost = Column(Float, default=0.0)  # 总成本
    
    # 时间戳
    created_at = Column(DateTime, default=get_now, nullable=False)
    
    # 关联
    user = relationship("User", backref="generation_costs")
    task = relationship("TaskQueue", backref="costs")
    
    # 索引
    __table_args__ = (
        Index('ix_cost_user_created', 'user_id', 'created_at'),
        Index('ix_cost_task', 'task_id'),
        Index('ix_cost_outline', 'outline_id'),
        Index('ix_cost_document', 'document_id'),
    )
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "model_id": self.model_id,
            "model_name": self.model_name,
            "provider": self.provider,
            "task_type": self.task_type,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "input_cost": round(self.input_cost, 6),
            "output_cost": round(self.output_cost, 6),
            "total_cost": round(self.total_cost, 6),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class DocumentCostSummary(Base):
    """文档生成成本汇总"""
    __tablename__ = "document_cost_summaries"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(Integer, nullable=False, unique=True, index=True)
    outline_id = Column(Integer, nullable=True, index=True)
    
    # 文档信息
    course = Column(String(100), nullable=True)
    knowledge_point = Column(String(200), nullable=True)
    section_count = Column(Integer, default=0)  # 章节数
    
    # 成本统计
    total_calls = Column(Integer, default=0)  # 总调用次数
    total_input_tokens = Column(Integer, default=0)
    total_output_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)  # 总成本（元）
    
    # 详细成本（JSON格式，记录每个模型的花费）
    cost_breakdown = Column(Text, nullable=True)  # {"kimi-k2.5": 1.23, "deepseek-v3": 0.45}
    
    # 时间戳
    created_at = Column(DateTime, default=get_now, nullable=False)
    updated_at = Column(DateTime, default=get_now, onupdate=get_now, nullable=False)
    
    # 关联
    user = relationship("User", backref="document_cost_summaries")
    
    def get_cost_breakdown(self):
        """解析成本明细"""
        if not self.cost_breakdown:
            return {}
        try:
            return json.loads(self.cost_breakdown)
        except json.JSONDecodeError:
            return {}
    
    def set_cost_breakdown(self, data):
        """设置成本明细"""
        if data is None:
            self.cost_breakdown = None
        else:
            self.cost_breakdown = json.dumps(data, ensure_ascii=False)
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "course": self.course,
            "knowledge_point": self.knowledge_point,
            "section_count": self.section_count,
            "total_calls": self.total_calls,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_tokens,
            "total_cost": round(self.total_cost, 4),
            "cost_breakdown": self.get_cost_breakdown(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
