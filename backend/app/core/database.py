"""
数据库连接配置
使用 SQLAlchemy 2.0 语法
"""
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings

settings = get_settings()


def get_now():
    """
    获取当前本地时间
    项目统一使用本地时间（Asia/Shanghai），不使用 UTC
    """
    return datetime.now()

# 创建数据库引擎
# 根据数据库类型配置不同参数
if settings.DATABASE_URL.startswith("sqlite"):
    # SQLite 配置
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=settings.DEBUG,
    )
else:
    # PostgreSQL 配置
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=settings.DEBUG,
    )

# 创建会话工厂
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# 声明基类
Base = declarative_base()


def ensure_schema_updates():
    """
    轻量迁移：为已存在库补充新增列（无 Alembic 时的兼容手段）。
    """
    from sqlalchemy import inspect, text

    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        if "documents" not in tables:
            return
        cols = [c["name"] for c in inspector.get_columns("documents")]
        if "pptx_path" in cols:
            return
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE documents ADD COLUMN pptx_path VARCHAR(500)"))
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("ensure_schema_updates skipped: %s", e)


def get_db():
    """
    获取数据库会话
    用于 FastAPI 依赖注入
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
