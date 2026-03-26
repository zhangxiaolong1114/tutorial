"""
结构化日志系统
支持日志分级、自动轮转、异常追踪
"""
import json
import logging
import os
import sys
import traceback
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from pathlib import Path


class StructuredLogFormatter(logging.Formatter):
    """结构化日志格式化器"""
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化为结构化日志"""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
        }
        
        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # 添加额外字段
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)
        
        return json.dumps(log_data, ensure_ascii=False, default=str)


class TaskLogContext:
    """任务日志上下文管理器"""
    
    def __init__(self, task_id: str, task_type: str, user_id: int = None):
        self.task_id = task_id
        self.task_type = task_type
        self.user_id = user_id
        self.start_time = datetime.now()
        self.log_entries = []
        
    def log(self, level: str, message: str, **extra):
        """记录日志条目"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "task_id": self.task_id,
            "task_type": self.task_type,
            "user_id": self.user_id,
            "message": message,
            **extra
        }
        self.log_entries.append(entry)
        return entry
    
    def info(self, message: str, **extra):
        return self.log("INFO", message, **extra)
    
    def warning(self, message: str, **extra):
        return self.log("WARN", message, **extra)
    
    def error(self, message: str, **extra):
        return self.log("ERROR", message, **extra)
    
    def exception(self, message: str, exc_info=None, **extra):
        """记录异常"""
        if exc_info is None:
            exc_info = sys.exc_info()
        
        entry = self.log("ERROR", message, **extra)
        entry["exception"] = {
            "type": exc_info[0].__name__ if exc_info[0] else None,
            "message": str(exc_info[1]) if exc_info[1] else None,
            "traceback": traceback.format_exception(*exc_info)
        }
        return entry
    
    def get_summary(self) -> Dict[str, Any]:
        """获取任务日志摘要"""
        duration = (datetime.now() - self.start_time).total_seconds()
        
        error_count = sum(1 for e in self.log_entries if e["level"] == "ERROR")
        warning_count = sum(1 for e in self.log_entries if e["level"] == "WARN")
        
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "user_id": self.user_id,
            "start_time": self.start_time.isoformat(),
            "duration_seconds": duration,
            "total_logs": len(self.log_entries),
            "error_count": error_count,
            "warning_count": warning_count,
            "status": "failed" if error_count > 0 else "success"
        }


class TaskLogger:
    """任务专用日志记录器"""
    
    def __init__(self, log_dir: str = None):
        if log_dir is None:
            log_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'app', 'logs', 'tasks')
        
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 当前活跃的任务上下文
        self._active_contexts: Dict[str, TaskLogContext] = {}
    
    def start_task(self, task_id: str, task_type: str, user_id: int = None) -> TaskLogContext:
        """开始记录任务"""
        context = TaskLogContext(task_id, task_type, user_id)
        self._active_contexts[task_id] = context
        context.info("任务开始")
        return context
    
    def get_context(self, task_id: str) -> Optional[TaskLogContext]:
        """获取任务上下文"""
        return self._active_contexts.get(task_id)
    
    def end_task(self, task_id: str, status: str = "completed", result: Dict = None):
        """结束任务记录"""
        context = self._active_contexts.get(task_id)
        if not context:
            return
        
        context.info(f"任务结束", status=status, result=result)
        
        # 保存日志到文件
        self._save_task_log(context)
        
        # 清理上下文
        del self._active_contexts[task_id]
    
    def _save_task_log(self, context: TaskLogContext):
        """保存任务日志到文件"""
        # 按日期组织日志文件
        date_str = context.start_time.strftime('%Y%m%d')
        task_log_dir = self.log_dir / date_str
        task_log_dir.mkdir(exist_ok=True)
        
        filename = f"{context.task_type}_{context.task_id}.json"
        filepath = task_log_dir / filename
        
        log_data = {
            "summary": context.get_summary(),
            "logs": context.log_entries
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存任务日志失败: {e}")
    
    def cleanup_old_logs(self, days: int = 7):
        """清理旧日志"""
        cutoff = datetime.now() - timedelta(days=days)
        
        for date_dir in self.log_dir.iterdir():
            if not date_dir.is_dir():
                continue
            
            try:
                dir_date = datetime.strptime(date_dir.name, '%Y%m%d')
                if dir_date < cutoff:
                    import shutil
                    shutil.rmtree(date_dir)
                    print(f"已清理旧日志: {date_dir}")
            except ValueError:
                continue


# 全局任务日志记录器
task_logger = TaskLogger()


def get_task_logger() -> TaskLogger:
    """获取任务日志记录器"""
    return task_logger
