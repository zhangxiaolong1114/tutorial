"""
验证码服务
处理验证码生成、存储和验证
"""
import random
import string
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.user import User
from app.core.config import get_settings


class VerificationError(Exception):
    """验证码异常基类"""
    pass


class CodeExpiredError(VerificationError):
    """验证码已过期"""
    pass


class InvalidCodeError(VerificationError):
    """验证码无效"""
    pass


class TooManyRequestsError(VerificationError):
    """请求过于频繁"""
    pass


def generate_code(email: str, db: Session, create_if_not_exists: bool = True) -> str:
    """
    生成6位数字验证码并保存到数据库
    
    Args:
        email: 用户邮箱
        db: 数据库会话
        create_if_not_exists: 如果用户不存在是否创建临时用户（用于注册场景）
    
    Returns:
        生成的6位数字验证码
    """
    settings = get_settings()
    
    # 查找用户
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        if not create_if_not_exists:
            from app.services.user_service import UserNotFoundError
            raise UserNotFoundError(f"用户 {email} 不存在")
        # 创建临时用户（用于注册场景）
        temp_username = email.split('@')[0]
        user = User(
            username=temp_username,
            email=email,
            hashed_password="",  # 临时密码，注册时会更新
            is_active=False,  # 未验证
            is_verified=False
        )
        db.add(user)
        db.flush()  # 获取 ID，但不提交
    
    # 检查是否频繁请求（如果上次验证码还未过期，且剩余时间超过 4 分钟）
    if user.verification_code and user.verification_code_expires:
        remaining_time = user.verification_code_expires - datetime.utcnow()
        if remaining_time.total_seconds() > 240:  # 剩余时间超过 4 分钟
            raise TooManyRequestsError("验证码请求过于频繁，请稍后再试")
    
    # 生成6位数字验证码
    code = ''.join(random.choices(string.digits, k=6))
    
    # 设置过期时间
    expires_at = datetime.utcnow() + timedelta(minutes=settings.VERIFICATION_CODE_EXPIRE_MINUTES)
    
    # 保存到数据库
    user.verification_code = code
    user.verification_code_expires = expires_at
    db.commit()
    
    return code


def verify_code(email: str, code: str, db: Session, clear_after_verify: bool = True) -> bool:
    """
    验证验证码
    
    Args:
        email: 用户邮箱
        code: 用户输入的验证码
        db: 数据库会话
        clear_after_verify: 验证成功后是否清除验证码
    
    Returns:
        验证成功返回 True
    
    Raises:
        UserNotFoundError: 如果用户不存在
        CodeExpiredError: 如果验证码已过期
        InvalidCodeError: 如果验证码无效
    """
    # 查找用户
    user = db.query(User).filter(User.email == email).first()
    if not user:
        from app.services.user_service import UserNotFoundError
        raise UserNotFoundError(f"用户 {email} 不存在")
    
    # 检查是否有验证码
    if not user.verification_code or not user.verification_code_expires:
        raise InvalidCodeError("验证码不存在，请先获取验证码")
    
    # 检查是否过期
    if datetime.utcnow() > user.verification_code_expires:
        raise CodeExpiredError("验证码已过期，请重新获取")
    
    # 验证验证码（不区分大小写，但数字验证码本来就没有大小写）
    if user.verification_code != code.strip():
        raise InvalidCodeError("验证码错误")
    
    # 验证成功，清除验证码
    if clear_after_verify:
        user.verification_code = None
        user.verification_code_expires = None
        db.commit()
    
    return True


def clear_verification_code(email: str, db: Session) -> None:
    """
    清除用户的验证码
    
    Args:
        email: 用户邮箱
        db: 数据库会话
    """
    user = db.query(User).filter(User.email == email).first()
    if user:
        user.verification_code = None
        user.verification_code_expires = None
        db.commit()
