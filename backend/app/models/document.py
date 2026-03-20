"""
文档模型定义
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import json

from app.core.database import Base


class Document(Base):
    """文档模型 - 存储生成的 HTML 内容"""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    outline_id = Column(Integer, ForeignKey("outlines.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 文档标题
    title = Column(String(200), nullable=False)
    
    # HTML 内容（当使用文件系统存储时，此字段可能为空或存储摘要）
    html_content = Column(Text, nullable=True)
    
    # 文件系统路径（当 STORAGE_TYPE=filesystem 时使用）
    file_path = Column(String(500), nullable=True, index=True)
    
    # 章节信息（JSON 格式，存储章节结构）
    sections = Column(Text, nullable=True)
    
    # 关联大纲
    outline = relationship("Outline", back_populates="documents")
    
    # 关联用户
    user = relationship("User", backref="documents")
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    def get_sections_data(self):
        """解析 sections 为 Python 对象"""
        if not self.sections:
            return []
        try:
            return json.loads(self.sections)
        except json.JSONDecodeError:
            return []
    
    def set_sections_data(self, data):
        """将 Python 对象序列化为 JSON 字符串"""
        self.sections = json.dumps(data, ensure_ascii=False, indent=2)
