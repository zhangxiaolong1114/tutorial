"""
用户设备服务
管理多设备登录
"""
from sqlalchemy.orm import Session
from typing import Optional

from app.models.user_device import UserDevice


def get_user_device(db: Session, user_id: int, device_fingerprint: str) -> Optional[UserDevice]:
    """
    获取用户的指定设备
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        device_fingerprint: 设备指纹
    
    Returns:
        设备对象，如果不存在则返回 None
    """
    return db.query(UserDevice).filter(
        UserDevice.user_id == user_id,
        UserDevice.device_fingerprint == device_fingerprint
    ).first()


def is_trusted_device(db: Session, user_id: int, device_fingerprint: str) -> bool:
    """
    检查设备是否是已信任设备
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        device_fingerprint: 设备指纹
    
    Returns:
        如果是已信任且活跃的设备返回 True
    """
    device = get_user_device(db, user_id, device_fingerprint)
    return device is not None and device.is_active


def add_or_update_device(
    db: Session, 
    user_id: int, 
    device_fingerprint: str, 
    device_name: Optional[str] = None,
    ip_address: Optional[str] = None
) -> UserDevice:
    """
    添加或更新设备信息
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        device_fingerprint: 设备指纹
        device_name: 设备名称
        ip_address: IP地址
    
    Returns:
        设备对象
    """
    device = get_user_device(db, user_id, device_fingerprint)
    
    if device:
        # 更新现有设备
        device.is_active = True
        if ip_address:
            device.last_login_ip = ip_address
    else:
        # 创建新设备
        device = UserDevice(
            user_id=user_id,
            device_fingerprint=device_fingerprint,
            device_name=device_name,
            last_login_ip=ip_address
        )
        db.add(device)
    
    db.commit()
    db.refresh(device)
    return device


def deactivate_device(db: Session, user_id: int, device_fingerprint: str) -> bool:
    """
    停用指定设备
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        device_fingerprint: 设备指纹
    
    Returns:
        成功返回 True
    """
    device = get_user_device(db, user_id, device_fingerprint)
    if device:
        device.is_active = False
        db.commit()
        return True
    return False


def get_user_devices(db: Session, user_id: int):
    """
    获取用户的所有设备
    
    Args:
        db: 数据库会话
        user_id: 用户ID
    
    Returns:
        设备列表
    """
    return db.query(UserDevice).filter(UserDevice.user_id == user_id).all()
