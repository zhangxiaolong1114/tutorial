"""
FastAPI 应用入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.api import auth
from app.core.database import engine, Base

settings = get_settings()

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 创建 FastAPI 应用实例
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应配置具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router)


@app.get("/")
async def root():
    """根路由 - 健康检查"""
    return {
        "message": "Welcome to FastAPI Tutorial",
        "version": settings.APP_VERSION,
        "debug": settings.DEBUG
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy"}
