"""
数据库迁移脚本：添加 generation_configs 表

运行方式：
1. 进入 backend 目录
2. 激活虚拟环境
3. 运行: python migrations/add_generation_configs.py
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import get_settings

settings = get_settings()


def migrate():
    """执行迁移"""
    engine = create_engine(settings.DATABASE_URL)
    
    # 检测数据库类型
    is_sqlite = 'sqlite' in settings.DATABASE_URL.lower()
    
    with engine.connect() as conn:
        if is_sqlite:
            # SQLite 兼容语法
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS generation_configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    
                    -- 风格层配置
                    tone VARCHAR(20) NOT NULL DEFAULT 'formal',
                    
                    -- 结构层配置
                    teaching_style VARCHAR(30) NOT NULL DEFAULT 'progressive',
                    content_style VARCHAR(20) NOT NULL DEFAULT 'detailed',
                    
                    -- 深度层配置
                    difficulty VARCHAR(20) NOT NULL DEFAULT 'intermediate',
                    formula_detail VARCHAR(20) NOT NULL DEFAULT 'derivation',
                    
                    -- 受众与格式配置
                    target_audience VARCHAR(30) NOT NULL DEFAULT 'undergraduate',
                    output_format VARCHAR(20) NOT NULL DEFAULT 'lecture',
                    code_language VARCHAR(20) NOT NULL DEFAULT 'python',
                    
                    -- 内容细节配置
                    chapter_granularity VARCHAR(20) NOT NULL DEFAULT 'standard',
                    citation_style VARCHAR(20) NOT NULL DEFAULT 'none',
                    interactive_elements VARCHAR(30) NOT NULL DEFAULT 'exercise',
                    
                    -- 仿真配置
                    need_simulation BOOLEAN NOT NULL DEFAULT 0,
                    simulation_types VARCHAR(50) NOT NULL DEFAULT '',
                    
                    -- 其他配置
                    need_images BOOLEAN NOT NULL DEFAULT 0,
                    
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
        else:
            # PostgreSQL 语法
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS generation_configs (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    
                    -- 风格层配置
                    tone VARCHAR(20) NOT NULL DEFAULT 'formal',
                    
                    -- 结构层配置
                    teaching_style VARCHAR(30) NOT NULL DEFAULT 'progressive',
                    content_style VARCHAR(20) NOT NULL DEFAULT 'detailed',
                    
                    -- 深度层配置
                    difficulty VARCHAR(20) NOT NULL DEFAULT 'intermediate',
                    formula_detail VARCHAR(20) NOT NULL DEFAULT 'derivation',
                    
                    -- 受众与格式配置
                    target_audience VARCHAR(30) NOT NULL DEFAULT 'undergraduate',
                    output_format VARCHAR(20) NOT NULL DEFAULT 'lecture',
                    code_language VARCHAR(20) NOT NULL DEFAULT 'python',
                    
                    -- 内容细节配置
                    chapter_granularity VARCHAR(20) NOT NULL DEFAULT 'standard',
                    citation_style VARCHAR(20) NOT NULL DEFAULT 'none',
                    interactive_elements VARCHAR(30) NOT NULL DEFAULT 'exercise',
                    
                    -- 仿真配置
                    need_simulation BOOLEAN NOT NULL DEFAULT FALSE,
                    simulation_types VARCHAR(50) NOT NULL DEFAULT '',
                    
                    -- 其他配置
                    need_images BOOLEAN NOT NULL DEFAULT FALSE,
                    
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """))
        
        # 创建索引
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_gen_config_user_created 
            ON generation_configs(user_id, created_at)
        """))
        
        conn.commit()
        
    print("✅ 迁移完成：generation_configs 表已创建")


def rollback():
    """回滚迁移"""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        conn.execute(text("DROP INDEX IF EXISTS idx_gen_config_user_created"))
        conn.execute(text("DROP TABLE IF EXISTS generation_configs"))
        conn.commit()
        
    print("✅ 回滚完成：generation_configs 表已删除")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="数据库迁移脚本")
    parser.add_argument("--rollback", action="store_true", help="回滚迁移")
    args = parser.parse_args()
    
    if args.rollback:
        rollback()
    else:
        migrate()
