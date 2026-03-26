"""
添加任务进度字段和进度详情字段
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import Column, Integer, Text, inspect, text
from app.core.database import Base, engine


def upgrade():
    """添加 progress 和 progress_detail 字段"""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('task_queue')]
    
    # 添加 progress 字段
    if 'progress' not in columns:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE task_queue ADD COLUMN progress INTEGER DEFAULT 0"))
            conn.commit()
        print("Added column: progress")
    
    # 添加 progress_detail 字段（JSON格式存储进度详情）
    if 'progress_detail' not in columns:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE task_queue ADD COLUMN progress_detail TEXT"))
            conn.commit()
        print("Added column: progress_detail")
    
    print("Migration completed successfully!")


def downgrade():
    """移除字段（SQLite不支持DROP COLUMN，这里仅作记录）"""
    print("SQLite does not support DROP COLUMN. Manual migration required.")


if __name__ == "__main__":
    upgrade()
