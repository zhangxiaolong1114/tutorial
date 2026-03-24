"""
应用配置管理
使用 pydantic-settings 管理环境变量
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置类"""
    
    # 应用信息
    APP_NAME: str = "FastAPI Tutorial"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # 数据库配置
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/fastapi_db"
    
    # JWT 配置
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # Access Token 30分钟有效期
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 10080  # Refresh Token 7天有效期
    
    # SMTP 配置
    # Office 365 中国版 (由世纪互联运营)
    SMTP_HOST: str = "smtp.partner.outlook.cn"
    SMTP_PORT: int = 587
    SMTP_USER: str = "iecubetutorial@iecube.com.cn"
    SMTP_PASSWORD: str = "Tutorial@903020275615ub"
    SMTP_FROM_EMAIL: str = "iecubetutorial@iecube.com.cn"
    SMTP_FROM_NAME: str = "智教云"
    SMTP_USE_TLS: bool = False  # 587端口使用 STARTTLS
    
    # 验证码配置
    VERIFICATION_CODE_EXPIRE_MINUTES: int = 5
    
    # AI API 配置
    KIMI_API_KEY: str = ""
    
    # Claude API 配置（可选，用于仿真生成）
    CLAUDE_API_KEY: str = ""
    CLAUDE_BASE_URL: str = "https://xiaoai.plus/v1"  # Claude API 基础地址
    CLAUDE_MODEL: str = "claude-opus-4-5-20251101"  # 默认模型
    
    # 仿真生成配置
    SIMULATION_PROVIDER: str = "kimi"  # 可选: "kimi" 或 "claude"
    SIMULATION_MODEL: str = "moonshot-v1-128k"  # Kimi 模型（当 provider=kimi 时使用）
    
    # 文件存储配置
    STORAGE_TYPE: str = "database"  # database 或 filesystem
    STORAGE_PATH: str = "./storage/documents"  # 文件系统存储路径
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """获取配置实例（缓存）"""
    return Settings()
