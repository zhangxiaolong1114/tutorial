"""
应用日志配置
统一配置所有模块的日志输出
"""
import logging
import os
import sys
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path


def setup_logging(
    log_dir: str = None,
    app_level: int = logging.INFO,
    console_level: int = logging.INFO,
    enable_structured: bool = False
):
    """
    配置应用日志
    
    Args:
        log_dir: 日志目录
        app_level: 应用日志级别
        console_level: 控制台日志级别
        enable_structured: 是否启用结构化日志（JSON格式）
    """
    if log_dir is None:
        log_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'app', 'logs')
    
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # 根日志配置
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # 根级别设为DEBUG，让handler控制实际级别
    
    # 清除现有处理器
    root_logger.handlers = []
    
    # 日志格式
    standard_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    detailed_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)-30s | %(funcName)-20s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 1. 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(standard_formatter)
    root_logger.addHandler(console_handler)
    
    # 2. 应用主日志（轮转）
    app_handler = RotatingFileHandler(
        log_path / 'app.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=10,
        encoding='utf-8'
    )
    app_handler.setLevel(app_level)
    app_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(app_handler)
    
    # 3. 错误日志（单独文件）
    error_handler = RotatingFileHandler(
        log_path / 'error.log',
        maxBytes=10*1024*1024,
        backupCount=10,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(error_handler)
    
    # 4. AI 服务日志（按天轮转）
    ai_handler = TimedRotatingFileHandler(
        log_path / 'ai_service.log',
        when='midnight',
        interval=1,
        backupCount=30,
        encoding='utf-8'
    )
    ai_handler.setLevel(logging.DEBUG)
    ai_handler.setFormatter(detailed_formatter)
    
    # 记录 AI 相关日志（包括 ai_service 和 model_callers）
    ai_logger = logging.getLogger('app.services.ai_service')
    ai_logger.setLevel(logging.DEBUG)  # 确保日志级别正确设置
    ai_logger.addHandler(ai_handler)
    ai_logger.propagate = True  # 允许向根日志传播，确保不丢失
    
    # model_callers 的日志也记录到 ai_service.log
    model_logger = logging.getLogger('app.core.model_callers')
    model_logger.setLevel(logging.DEBUG)
    model_logger.addHandler(ai_handler)
    model_logger.propagate = True
    
    # 5. 任务队列日志
    task_handler = TimedRotatingFileHandler(
        log_path / 'task_queue.log',
        when='midnight',
        interval=1,
        backupCount=30,
        encoding='utf-8'
    )
    task_handler.setLevel(logging.DEBUG)
    task_handler.setFormatter(detailed_formatter)
    
    task_logger = logging.getLogger('app.services.task_queue_service')
    task_logger.addHandler(task_handler)
    task_logger.propagate = False
    
    # 6. 数据库日志（SQL语句）
    db_handler = RotatingFileHandler(
        log_path / 'database.log',
        maxBytes=50*1024*1024,  # 50MB
        backupCount=5,
        encoding='utf-8'
    )
    db_handler.setLevel(logging.DEBUG)
    db_handler.setFormatter(detailed_formatter)
    
    db_logger = logging.getLogger('sqlalchemy.engine')
    db_logger.addHandler(db_handler)
    db_logger.setLevel(logging.WARNING)  # 默认只记录警告以上
    
    # 7. 访问日志（API请求）
    access_handler = TimedRotatingFileHandler(
        log_path / 'access.log',
        when='midnight',
        interval=1,
        backupCount=30,
        encoding='utf-8'
    )
    access_handler.setLevel(logging.INFO)
    access_handler.setFormatter(standard_formatter)
    
    access_logger = logging.getLogger('app.api')
    access_logger.addHandler(access_handler)
    access_logger.propagate = False
    
    # 设置第三方库日志级别
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    
    logging.info(f"日志系统初始化完成，日志目录: {log_dir}")
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """获取命名日志记录器"""
    return logging.getLogger(name)
