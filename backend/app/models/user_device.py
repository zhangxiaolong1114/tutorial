"""
用户设备模型
支持多设备登录管理
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class UserDevice(Base):
    """用户设备模型"""
    __tablename__ = "user_devices"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    device_fingerprint = Column(String(255), nullable=False)
    device_name = Column(String(100), nullable=True)  # 设备名称（如：Chrome on Windows）
    last_login_ip = Column(String(45), nullable=True)
    last_login_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)  # 是否允许该设备登录
    
    # 关联用户
    user = relationship("User", back_populates="devices")
    
    # 联合唯一索引：一个用户的同一设备只存一条记录
    __table_args__ = (
        Index('ix_user_device_unique', 'user_id', 'device_fingerprint', unique=True),
    )
