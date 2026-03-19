"""
用户服务层
处理用户相关的业务逻辑
"""
from sqlalchemy.orm import Session

from app.models.user import User
from app.core.security import get_password_hash, verify_password


class UserServiceError(Exception):
    """用户服务异常基类"""
    pass


class UserAlreadyExistsError(UserServiceError):
    """用户已存在异常"""
    pass


class UserNotFoundError(UserServiceError):
    """用户不存在异常"""
    pass


class InvalidCredentialsError(UserServiceError):
    """凭据无效异常"""
    pass


def get_user_by_email(db: Session, email: str) -> User | None:
    """
    通过邮箱获取用户
    
    Args:
        db: 数据库会话
        email: 用户邮箱
    
    Returns:
        用户对象，如果不存在则返回 None
    """
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    """
    通过ID获取用户
    
    Args:
        db: 数据库会话
        user_id: 用户ID
    
    Returns:
        用户对象，如果不存在则返回 None
    """
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, email: str, password: str, username: str = "") -> User:
    """
    创建新用户
    
    Args:
        db: 数据库会话
        email: 用户邮箱
        password: 明文密码
        username: 用户名
    
    Returns:
        创建的用户对象
    
    Raises:
        UserAlreadyExistsError: 如果邮箱已被注册且已激活
    """
    # 检查邮箱是否已存在
    existing_user = get_user_by_email(db, email)
    if existing_user:
        # 如果是临时用户（is_active=False），则更新为正式用户
        if not existing_user.is_active:
            if not username:
                username = email.split('@')[0]
            existing_user.username = username
            existing_user.hashed_password = get_password_hash(password)
            existing_user.is_active = True
            db.commit()
            db.refresh(existing_user)
            return existing_user
        else:
            raise UserAlreadyExistsError(f"邮箱 {email} 已被注册")
    
    # 如果没有提供用户名，使用邮箱前缀
    if not username:
        username = email.split('@')[0]
    
    # 创建新用户
    hashed_password = get_password_hash(password)
    db_user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        is_active=True,
        is_verified=False
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


def authenticate_user(db: Session, email: str, password: str) -> User:
    """
    验证用户凭据
    
    Args:
        db: 数据库会话
        email: 用户邮箱
        password: 明文密码
    
    Returns:
        验证通过的用户对象
    
    Raises:
        InvalidCredentialsError: 如果邮箱或密码不正确
        UserNotFoundError: 如果用户不存在
    """
    user = get_user_by_email(db, email)
    if not user:
        raise UserNotFoundError("用户不存在")
    
    if not verify_password(password, user.hashed_password):
        raise InvalidCredentialsError("密码错误")
    
    return user


def reset_password(db: Session, email: str, new_password: str) -> User:
    """
    重置用户密码
    
    Args:
        db: 数据库会话
        email: 用户邮箱
        new_password: 新密码
    
    Returns:
        用户对象
    
    Raises:
        UserNotFoundError: 如果用户不存在
    """
    user = get_user_by_email(db, email)
    if not user:
        raise UserNotFoundError("用户不存在")
    
    # 更新密码
    user.hashed_password = get_password_hash(new_password)
    db.commit()
    db.refresh(user)
    
    return user
