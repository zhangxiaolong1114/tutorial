"""
日志配置
配置详细的日志记录，用于排查 AI 生成失败问题
"""
import logging
import logging.handlers
import os
from pathlib import Path

# 日志目录
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# 日志格式
DETAILED_FORMAT = logging.Formatter(
    '%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

SIMPLE_FORMAT = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


def setup_logging():
    """配置日志系统"""
    
    # 根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # 清除现有处理器
    root_logger.handlers = []
    
    # 1. 控制台输出（简化格式）
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(SIMPLE_FORMAT)
    root_logger.addHandler(console_handler)
    
    # 2. 应用日志文件（轮转，每天一个文件，保留7天）
    app_handler = logging.handlers.TimedRotatingFileHandler(
        filename=LOG_DIR / "app.log",
        when="midnight",
        interval=1,
        backupCount=7,
        encoding="utf-8"
    )
    app_handler.setLevel(logging.INFO)
    app_handler.setFormatter(DETAILED_FORMAT)
    root_logger.addHandler(app_handler)
    
    # 3. AI 服务详细日志（专门记录 AI 调用）
    ai_handler = logging.handlers.TimedRotatingFileHandler(
        filename=LOG_DIR / "ai_service.log",
        when="midnight",
        interval=1,
        backupCount=7,
        encoding="utf-8"
    )
    ai_handler.setLevel(logging.DEBUG)
    ai_handler.setFormatter(DETAILED_FORMAT)
    
    # 专门给 ai_service 配置更详细的日志
    ai_logger = logging.getLogger("app.services.ai_service")
    ai_logger.setLevel(logging.DEBUG)
    ai_logger.addHandler(ai_handler)
    
    # 4. 错误日志（单独记录错误）
    error_handler = logging.handlers.RotatingFileHandler(
        filename=LOG_DIR / "error.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(DETAILED_FORMAT)
    root_logger.addHandler(error_handler)
    
    # 5. 任务队列日志
    task_handler = logging.handlers.TimedRotatingFileHandler(
        filename=LOG_DIR / "task_queue.log",
        when="midnight",
        interval=1,
        backupCount=7,
        encoding="utf-8"
    )
    task_handler.setLevel(logging.DEBUG)
    task_handler.setFormatter(DETAILED_FORMAT)
    
    task_logger = logging.getLogger("app.services.task_queue_service")
    task_logger.setLevel(logging.DEBUG)
    task_logger.addHandler(task_handler)
    
    # 记录启动信息
    root_logger.info(f"日志系统初始化完成")
    root_logger.info(f"日志目录: {LOG_DIR}")
    root_logger.info(f"AI 服务日志: {LOG_DIR / 'ai_service.log'}")
    root_logger.info(f"任务队列日志: {LOG_DIR / 'task_queue.log'}")
    root_logger.info(f"错误日志: {LOG_DIR / 'error.log'}")
    
    return root_logger
