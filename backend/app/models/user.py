"""
用户模型定义
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Index
from sqlalchemy.orm import relationship

from app.core.database import Base, get_now


class User(Base):
    """用户模型"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # 邮箱验证码字段
    verification_code = Column(String(10), nullable=True)
    verification_code_expires = Column(DateTime, nullable=True)
    
    # 关联设备（多设备登录）
    devices = relationship("UserDevice", back_populates="user", cascade="all, delete-orphan")
    
    created_at = Column(DateTime, default=get_now, nullable=False)
    updated_at = Column(DateTime, default=get_now, onupdate=get_now, nullable=False)
    
    # 显式创建 email 唯一索引
    __table_args__ = (
        Index('ix_users_email_unique', 'email', unique=True),
    )
