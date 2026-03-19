"""
认证相关 API 路由
- 用户注册
- 用户登录
- 获取当前用户信息
- 发送验证码
- 验证码登录（异常设备）
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token
from app.schemas.user import (
    UserCreate, UserResponse, Token,
    VerificationCodeRequest, VerificationCodeResponse,
    LoginWithVerificationCode, LoginResponse, VerificationRequiredResponse,
    ResetPasswordRequest
)
from app.services import user_service
from app.services.user_service import (
    UserAlreadyExistsError,
    UserNotFoundError,
    InvalidCredentialsError
)
from app.services.email_service import send_verification_code
from app.services.verification_service import (
    generate_code, verify_code, 
    VerificationError, CodeExpiredError, InvalidCodeError, TooManyRequestsError
)
from app.api.deps import get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["认证"])


class SendCodeRequest(BaseModel):
    """发送验证码请求"""
    email: EmailStr
    purpose: str = "register"  # register, login, reset


@router.post("/send-verification-code", response_model=VerificationCodeResponse)
async def send_verification_code_endpoint(
    request: SendCodeRequest,
    db: Session = Depends(get_db)
):
    """
    发送邮箱验证码
    
    - **email**: 用户邮箱
    - **purpose**: 用途（register-注册, login-登录, reset-重置密码）
    
    验证码将在 5 分钟后过期
    """
    try:
        # 根据不同用途检查用户是否存在
        user = user_service.get_user_by_email(db, request.email)
        
        if request.purpose == "register" and user:
            # 注册时用户已存在
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该邮箱已注册"
            )
        elif request.purpose in ["login", "reset"] and not user:
            # 登录或重置密码时用户不存在
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 生成验证码
        code = generate_code(request.email, db)
        
        # 发送邮件
        success = await send_verification_code(request.email, code)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="邮件发送失败，请稍后重试"
            )
        
        return VerificationCodeResponse(message="验证码已发送至您的邮箱")
    
    except TooManyRequestsError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"发送验证码失败: {str(e)}"
        )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_create: UserCreate, db: Session = Depends(get_db)):
    """
    用户注册
    
    - **email**: 用户邮箱（必须唯一）
    - **password**: 密码（至少6位）
    - **verification_code**: 邮箱验证码（6位数字）
    """
    try:
        # 先验证验证码
        verify_code(user_create.email, user_create.verification_code, db)
        
        # 创建用户
        user = user_service.create_user(
            db=db,
            email=user_create.email,
            password=user_create.password,
            username=user_create.username
        )
        
        # 标记邮箱已验证
        user.is_verified = True
        db.commit()
        
        return user
    
    except UserAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except (CodeExpiredError, InvalidCodeError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"注册失败: {str(e)}"
        )


@router.post("/login", response_model=LoginResponse)
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    用户登录
    
    - **username**: 用户邮箱
    - **password**: 密码
    
    如果是新设备登录，会返回需要验证码的错误
    已信任设备直接登录成功
    """
    from app.services import device_service
    
    try:
        # 验证用户凭据
        user = user_service.authenticate_user(
            db=db,
            email=form_data.username,
            password=form_data.password
        )
    except (UserNotFoundError, InvalidCredentialsError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 获取客户端信息
    client_ip = request.client.host if request.client else None
    device_fingerprint = request.headers.get("X-Device-Fingerprint")
    
    # 检查是否是已信任设备
    is_trusted_device = False
    if device_fingerprint:
        is_trusted_device = device_service.is_trusted_device(
            db=db,
            user_id=user.id,
            device_fingerprint=device_fingerprint
        )
    
    # 新设备需要验证码
    if not is_trusted_device:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "VERIFICATION_REQUIRED",
                "message": "检测到新设备登录，需要验证码",
                "email": user.email
            }
        )
    
    # 更新设备登录信息
    if device_fingerprint:
        device_service.add_or_update_device(
            db=db,
            user_id=user.id,
            device_fingerprint=device_fingerprint,
            ip_address=client_ip
        )
    
    # 生成访问令牌
    access_token = create_access_token(subject=user.id)
    
    return LoginResponse(access_token=access_token, token_type="bearer")


@router.post("/verify-login", response_model=LoginResponse)
async def verify_login(
    request: Request,
    login_data: LoginWithVerificationCode,
    db: Session = Depends(get_db)
):
    """
    验证码登录（新设备登录）
    
    - **email**: 用户邮箱
    - **password**: 密码
    - **verification_code**: 邮箱验证码
    - **device_fingerprint**: 设备指纹（可选）
    
    用于在新设备登录时的验证，验证成功后设备会被添加到信任列表
    """
    from app.services import device_service
    
    try:
        # 验证用户凭据
        user = user_service.authenticate_user(
            db=db,
            email=login_data.email,
            password=login_data.password
        )
    except (UserNotFoundError, InvalidCredentialsError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 验证验证码
    try:
        verify_code(login_data.email, login_data.verification_code, db, clear_after_verify=False)
    except (CodeExpiredError, InvalidCodeError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # 获取客户端信息
    client_ip = request.client.host if request.client else None
    device_fingerprint = request.headers.get("X-Device-Fingerprint")
    
    # 添加设备到信任列表
    if device_fingerprint:
        device_service.add_or_update_device(
            db=db,
            user_id=user.id,
            device_fingerprint=device_fingerprint,
            ip_address=client_ip
        )
    
    # 清除验证码
    user.verification_code = None
    user.verification_code_expires = None
    db.commit()
    
    # 生成访问令牌
    access_token = create_access_token(subject=user.id)
    
    return LoginResponse(access_token=access_token, token_type="bearer")


@router.post("/send-login-verification-code", response_model=VerificationCodeResponse)
async def send_login_verification_code(
    request: VerificationCodeRequest,
    db: Session = Depends(get_db)
):
    """
    发送登录验证码（用于异常设备登录）
    
    - **email**: 用户邮箱
    
    验证码将在 5 分钟后过期
    """
    try:
        # 检查用户是否存在
        user = user_service.get_user_by_email(db, request.email)
        if not user:
            # 用户不存在时，为了安全考虑，返回相同的消息
            return VerificationCodeResponse(message="验证码已发送至您的邮箱")
        
        # 生成验证码
        code = generate_code(request.email, db)
        
        # 发送邮件
        success = await send_verification_code(request.email, code)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="邮件发送失败，请稍后重试"
            )
        
        return VerificationCodeResponse(message="验证码已发送至您的邮箱")
    
    except TooManyRequestsError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"发送验证码失败: {str(e)}"
        )


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """
    获取当前登录用户信息
    
    需要有效的 JWT 令牌
    """
    return current_user


@router.post("/reset-password")
def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    重置密码
    
    - **email**: 用户邮箱
    - **verification_code**: 邮箱验证码
    - **new_password**: 新密码
    """
    try:
        # 验证验证码
        verify_code(request.email, request.verification_code, db)
        
        # 重置密码
        user_service.reset_password(db, request.email, request.new_password)
        
        return {"message": "密码重置成功"}
    
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    except (CodeExpiredError, InvalidCodeError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"重置密码失败: {str(e)}"
        )
