#!/usr/bin/env python3
"""
恢复失败的文档生成任务
用于修复因 generate_complete_html 方法缺失而失败的任务
"""
import sys
sys.path.insert(0, '/home/iecube_xiaolong/project/tutorial/backend')

from app.core.database import SessionLocal
from app.models.task_queue import TaskQueue, TaskStatus
from app.models.document import Document
from app.models.outline import Outline
from app.services.ai_service import ai_service
from app.services.file_storage_service import file_storage_service
from app.core.config import get_settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
settings = get_settings()


def recover_failed_document_task(task_id: int):
    """恢复失败的文档生成任务"""
    db = SessionLocal()
    try:
        task = db.query(TaskQueue).filter(TaskQueue.id == task_id).first()
        if not task:
            logger.error(f"Task {task_id} not found")
            return False
        
        if task.status != TaskStatus.FAILED:
            logger.warning(f"Task {task_id} is not failed, status: {task.status}")
            return False
        
        if task.task_type != TaskType.GENERATE_DOCUMENT:
            logger.error(f"Task {task_id} is not a document generation task")
            return False
        
        params = task.get_params()
        outline_id = params.get("outline_id")
        
        # 获取大纲
        outline = db.query(Outline).filter(
            Outline.id == outline_id,
            Outline.user_id == task.user_id
        ).first()
        
        if not outline:
            logger.error(f"Outline {outline_id} not found")
            return False
        
        outline_data = outline.get_outline_data()
        sections = outline_data.get("sections", [])
        
        logger.info(f"Recovering task {task_id} for outline {outline_id} with {len(sections)} sections")
        
        # 检查是否已有部分生成的文档
        existing_doc = db.query(Document).filter(
            Document.outline_id == outline_id,
            Document.user_id == task.user_id
        ).order_by(Document.id.desc()).first()
        
        if existing_doc and existing_doc.html_content and len(existing_doc.html_content) > 1000:
            # 如果已有完整内容，直接重新生成 HTML 包装
            logger.info(f"Found existing document {existing_doc.id} with content, regenerating HTML wrapper")
            body_content = existing_doc.html_content
            # 去除可能已存在的包装
            if body_content.startswith('<!DOCTYPE html>'):
                # 提取 body 内容
                import re
                match = re.search(r'<div class="content">(.*?)</div>\s*<div class="footer">', body_content, re.DOTALL)
                if match:
                    body_content = match.group(1).strip()
        else:
            logger.error(f"No existing document content found for recovery")
            return False
        
        # 重新生成完整 HTML
        title = outline_data.get("title", f"{outline.course} - {outline.knowledge_point}")
        full_html = ai_service.generate_complete_html(title, body_content)
        
        # 更新或创建文档记录
        if existing_doc:
            document = existing_doc
        else:
            document = Document(
                user_id=task.user_id,
                outline_id=outline.id,
                title=title,
                html_content=None,
                file_path=None,
                simulation_code=None
            )
            db.add(document)
            db.commit()
            db.refresh(document)
        
        # 保存到文件系统或数据库
        file_path = None
        if settings.STORAGE_TYPE == "filesystem":
            file_path = file_storage_service.save_document(
                document_id=document.id,
                user_id=task.user_id,
                title=title,
                html_content=full_html
            )
            
            if file_path:
                document.file_path = file_path
                document.html_content = full_html[:500] + "..." if len(full_html) > 500 else full_html
            else:
                document.html_content = full_html
        else:
            document.html_content = full_html
        
        db.commit()
        
        # 更新任务状态
        task.status = TaskStatus.COMPLETED
        task.error_message = None
        task.set_result({"document_id": document.id, "title": title})
        db.commit()
        
        logger.info(f"Successfully recovered task {task_id}, document {document.id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to recover task {task_id}: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def retry_failed_task(task_id: int):
    """将失败任务重置为待处理状态，重新执行"""
    db = SessionLocal()
    try:
        task = db.query(TaskQueue).filter(TaskQueue.id == task_id).first()
        if not task:
            logger.error(f"Task {task_id} not found")
            return False
        
        if task.status != TaskStatus.FAILED:
            logger.warning(f"Task {task_id} is not failed, status: {task.status}")
            return False
        
        # 重置任务状态
        task.status = TaskStatus.PENDING
        task.error_message = None
        task.started_at = None
        task.completed_at = None
        db.commit()
        
        logger.info(f"Task {task_id} has been reset to PENDING status")
        return True
        
    except Exception as e:
        logger.error(f"Failed to retry task {task_id}: {e}")
        db.rollback()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="恢复失败的文档生成任务")
    parser.add_argument("task_id", type=int, help="任务ID")
    parser.add_argument("--retry", action="store_true", help="重置为待处理状态重新执行")
    
    args = parser.parse_args()
    
    if args.retry:
        success = retry_failed_task(args.task_id)
    else:
        success = recover_failed_document_task(args.task_id)
    
    sys.exit(0 if success else 1)
