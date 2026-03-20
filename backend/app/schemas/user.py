"""
Pydantic 模型定义 - 用户相关
"""
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """用户基础模型"""
    email: EmailStr


class UserCreate(UserBase):
    """用户注册模型"""
    username: str = Field(..., min_length=2, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=100)
    verification_code: str = Field(..., min_length=6, max_length=6, description="邮箱验证码", alias="verificationCode")
    
    class Config:
        populate_by_name = True


class UserLogin(BaseModel):
    """用户登录模型"""
    email: EmailStr
    password: str


class UserResponse(UserBase):
    """用户响应模型"""
    id: int
    username: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """Token 响应模型"""
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Token 载荷模型"""
    sub: int | None = None


class VerificationCodeRequest(BaseModel):
    """发送验证码请求模型"""
    email: EmailStr


class VerificationCodeResponse(BaseModel):
    """发送验证码响应模型"""
    message: str


class LoginWithVerificationCode(BaseModel):
    """验证码登录模型（异常设备登录）"""
    email: EmailStr
    password: str
    verification_code: str = Field(..., min_length=6, max_length=6, description="邮箱验证码", alias="verificationCode")
    device_fingerprint: str | None = Field(None, description="设备指纹")
    
    class Config:
        populate_by_name = True


class LoginResponse(BaseModel):
    """登录响应模型"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """刷新 Token 请求模型"""
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    """刷新 Token 响应模型"""
    access_token: str
    token_type: str = "bearer"


class VerificationRequiredResponse(BaseModel):
    """需要验证码的登录响应"""
    require_verification: bool = True
    message: str = "检测到异常登录，需要验证码"
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """重置密码请求模型"""
    email: EmailStr
    verification_code: str = Field(..., min_length=6, max_length=6, description="邮箱验证码", alias="verificationCode")
    new_password: str = Field(..., min_length=6, max_length=100, description="新密码", alias="newPassword")
    
    class Config:
        populate_by_name = True
