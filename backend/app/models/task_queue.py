"""
任务队列模型
用于异步处理AI生成任务
"""
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import json

from app.core.database import Base


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"      # 等待处理
    PROCESSING = "processing" # 处理中
    COMPLETED = "completed"  # 完成
    FAILED = "failed"        # 失败


class TaskType(str, Enum):
    """任务类型"""
    GENERATE_OUTLINE = "generate_outline"    # 生成大纲
    GENERATE_DOCUMENT = "generate_document"  # 生成文档


class TaskQueue(Base):
    """任务队列模型"""
    __tablename__ = "task_queue"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 任务信息
    task_type = Column(String(50), nullable=False, index=True)  # generate_outline / generate_document
    status = Column(String(20), default=TaskStatus.PENDING, nullable=False, index=True)
    
    # 任务参数（JSON格式）
    params = Column(Text, nullable=False, default="{}")
    
    # 任务结果
    result = Column(Text, nullable=True)  # 成功时存储结果ID等
    error_message = Column(Text, nullable=True)  # 失败时存储错误信息
    
    # 关联资源ID（如生成的大纲ID）
    resource_id = Column(Integer, nullable=True)
    resource_type = Column(String(50), nullable=True)  # outline / document
    
    # 时间戳
    created_at = Column(DateTime, default=func.now(), nullable=False)
    started_at = Column(DateTime, nullable=True)  # 开始处理时间
    completed_at = Column(DateTime, nullable=True)  # 完成时间
    
    # 关联用户
    user = relationship("User", backref="tasks")
    
    # 索引优化查询
    __table_args__ = (
        Index('ix_task_queue_user_status', 'user_id', 'status'),
        Index('ix_task_queue_status_created', 'status', 'created_at'),
    )
    
    def get_params(self):
        """解析参数"""
        try:
            return json.loads(self.params)
        except json.JSONDecodeError:
            return {}
    
    def set_params(self, data):
        """设置参数"""
        self.params = json.dumps(data, ensure_ascii=False)
    
    def get_result(self):
        """解析结果"""
        if not self.result:
            return None
        try:
            return json.loads(self.result)
        except json.JSONDecodeError:
            return self.result
    
    def set_result(self, data):
        """设置结果"""
        if data is None:
            self.result = None
        elif isinstance(data, dict):
            self.result = json.dumps(data, ensure_ascii=False)
        else:
            self.result = str(data)
    
    @property
    def duration_seconds(self):
        """计算任务耗时"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        if self.started_at:
            return (datetime.now() - self.started_at).total_seconds()
        return None
