"""
大纲模型定义
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
import json

from app.core.database import Base, get_now


class Outline(Base):
    """大纲模型 - 存储 AI 生成的大纲 JSON"""
    __tablename__ = "outlines"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 大纲生成参数
    course = Column(String(100), nullable=False)  # 课程名称
    knowledge_point = Column(String(200), nullable=False)  # 知识点
    difficulty = Column(String(20), nullable=False)  # 难度等级: easy, medium, hard
    
    # 大纲内容（JSON 格式存储）
    outline_json = Column(Text, nullable=False)
    
    # 状态: pending, generated, error
    status = Column(String(20), default="pending", nullable=False)
    
    # 关联用户
    user = relationship("User", backref="outlines")
    
    # 关联文档（一对多）
    documents = relationship("Document", back_populates="outline", cascade="all, delete-orphan")
    
    created_at = Column(DateTime, default=get_now, nullable=False)
    updated_at = Column(DateTime, default=get_now, onupdate=get_now, nullable=False)
    
    def get_outline_data(self):
        """解析 outline_json 为 Python 对象"""
        try:
            return json.loads(self.outline_json)
        except json.JSONDecodeError:
            return {}
    
    def set_outline_data(self, data):
        """将 Python 对象序列化为 JSON 字符串"""
        self.outline_json = json.dumps(data, ensure_ascii=False, indent=2)
