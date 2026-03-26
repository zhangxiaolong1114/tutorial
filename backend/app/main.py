"""
FastAPI 应用入口
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging_config import setup_logging
from app.api import auth, outline, document, generation_config, ai_models, costs
from app.core.database import engine, Base
from app.services.task_queue_service import task_queue_service

# 首先配置日志
setup_logging()

settings = get_settings()

# 创建数据库表
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时启动任务队列
    await task_queue_service.start(num_workers=2)
    yield
    # 关闭时停止任务队列
    await task_queue_service.stop()


# 创建 FastAPI 应用实例
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
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
app.include_router(outline.router)
app.include_router(document.router)
app.include_router(generation_config.router)
app.include_router(ai_models.router)
app.include_router(costs.router)


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
