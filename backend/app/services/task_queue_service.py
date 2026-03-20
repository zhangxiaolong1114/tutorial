"""
任务队列服务
管理异步任务的创建、执行和状态查询
"""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, Callable, Dict, Any
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.config import get_settings
from app.models.task_queue import TaskQueue, TaskStatus, TaskType
from app.services.ai_service import ai_service
from app.services.file_storage_service import file_storage_service

settings = get_settings()

logger = logging.getLogger(__name__)


class TaskQueueService:
    """任务队列服务"""
    
    def __init__(self):
        self._running = False
        self._workers = []
        self._handlers: Dict[TaskType, Callable] = {}
        self._register_handlers()
    
    def _register_handlers(self):
        """注册任务处理器"""
        self._handlers[TaskType.GENERATE_OUTLINE] = self._handle_generate_outline
        self._handlers[TaskType.GENERATE_DOCUMENT] = self._handle_generate_document
    
    def create_task(
        self,
        db: Session,
        user_id: int,
        task_type: TaskType,
        params: Dict[str, Any]
    ) -> TaskQueue:
        """
        创建新任务
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            task_type: 任务类型
            params: 任务参数
        
        Returns:
            创建的任务对象
        """
        task = TaskQueue(
            user_id=user_id,
            task_type=task_type,
            status=TaskStatus.PENDING
        )
        task.set_params(params)
        
        db.add(task)
        db.commit()
        db.refresh(task)
        
        logger.info(f"Created task {task.id} for user {user_id}, type: {task_type}")
        return task
    
    def get_task(self, db: Session, task_id: int, user_id: int) -> Optional[TaskQueue]:
        """获取任务详情"""
        return db.query(TaskQueue).filter(
            TaskQueue.id == task_id,
            TaskQueue.user_id == user_id
        ).first()
    
    def get_user_tasks(
        self,
        db: Session,
        user_id: int,
        status: Optional[TaskStatus] = None,
        limit: int = 50
    ):
        """获取用户的任务列表"""
        query = db.query(TaskQueue).filter(TaskQueue.user_id == user_id)
        
        if status:
            query = query.filter(TaskQueue.status == status)
        
        return query.order_by(TaskQueue.created_at.desc()).limit(limit).all()
    
    def get_pending_tasks(self, db: Session, limit: int = 10):
        """获取待处理的任务（用于工作线程）"""
        return db.query(TaskQueue).filter(
            TaskQueue.status == TaskStatus.PENDING
        ).order_by(TaskQueue.created_at.asc()).limit(limit).all()
    
    def _handle_generate_outline(self, db: Session, task: TaskQueue) -> Dict[str, Any]:
        """处理生成大纲任务"""
        from app.models.outline import Outline
        
        params = task.get_params()
        course = params.get("course")
        knowledge_point = params.get("knowledge_point")
        difficulty = params.get("difficulty", "medium")
        
        # 调用AI服务生成大纲
        outline_data = ai_service.generate_outline(
            course=course,
            knowledge_point=knowledge_point,
            difficulty=difficulty
        )
        
        # 创建大纲记录
        outline = Outline(
            user_id=task.user_id,
            course=course,
            knowledge_point=knowledge_point,
            difficulty=difficulty,
            outline_json="",
            status="generated"
        )
        outline.set_outline_data(outline_data)
        
        db.add(outline)
        db.commit()
        db.refresh(outline)
        
        # 更新任务关联资源
        task.resource_id = outline.id
        task.resource_type = "outline"
        db.commit()
        
        return {
            "outline_id": outline.id,
            "title": outline_data.get("title", f"{course} - {knowledge_point}")
        }
    
    def _generate_section_sync(self, section: dict, course: str, knowledge_point: str) -> tuple:
        """同步生成单个章节内容"""
        section_id = section.get("id", "")
        section_title = section.get("title", "")
        section_content = section.get("content", [])
        
        try:
            if section_id == "simulation" or "仿真" in section_title:
                simulation_desc = section_content[0] if isinstance(section_content, list) and section_content else str(section_content)
                html_content = ai_service.generate_simulation_code(
                    simulation_desc=simulation_desc,
                    course=course,
                    knowledge_point=knowledge_point
                )
            else:
                html_content = ai_service.generate_section_content(
                    section_title=section_title,
                    section_key_points=section_content if isinstance(section_content, list) else [str(section_content)],
                    course=course,
                    knowledge_point=knowledge_point
                )
            return (section_id, section_title, html_content, None)
        except Exception as e:
            logger.error(f"Failed to generate section {section_id}: {e}")
            return (section_id, section_title, f"<p>内容生成失败: {str(e)}</p>", str(e))
    
    async def _generate_section_async(self, section: dict, course: str, knowledge_point: str) -> tuple:
        """异步生成单个章节内容"""
        section_id = section.get("id", "")
        section_title = section.get("title", "")
        section_content = section.get("content", [])
        
        try:
            # 仿真章节生成仿真代码
            if section_id == "simulation" or "仿真" in section_title:
                simulation_desc = section_content[0] if isinstance(section_content, list) and section_content else str(section_content)
                # 在线程池中执行同步的 AI 调用
                loop = asyncio.get_event_loop()
                html_content = await loop.run_in_executor(
                    None,
                    lambda: ai_service.generate_simulation_code(
                        simulation_desc=simulation_desc,
                        course=course,
                        knowledge_point=knowledge_point
                    )
                )
            else:
                # 普通章节生成HTML
                loop = asyncio.get_event_loop()
                html_content = await loop.run_in_executor(
                    None,
                    lambda: ai_service.generate_section_content(
                        section_title=section_title,
                        section_key_points=section_content if isinstance(section_content, list) else [str(section_content)],
                        course=course,
                        knowledge_point=knowledge_point
                    )
                )
            
            return (section_id, section_title, html_content, None)
        except Exception as e:
            logger.error(f"Failed to generate section {section_id}: {e}")
            return (section_id, section_title, f"<p>内容生成失败: {str(e)}</p>", str(e))

    def _handle_generate_document(self, db: Session, task: TaskQueue) -> Dict[str, Any]:
        """处理生成文档任务"""
        from app.models.outline import Outline
        from app.models.document import Document
        
        params = task.get_params()
        outline_id = params.get("outline_id")
        
        # 获取大纲
        outline = db.query(Outline).filter(
            Outline.id == outline_id,
            Outline.user_id == task.user_id
        ).first()
        
        if not outline:
            raise ValueError(f"Outline {outline_id} not found")
        
        outline_data = outline.get_outline_data()
        sections = outline_data.get("sections", [])
        
        logger.info(f"Starting generation of {len(sections)} sections for document")
        
        # 生成每个章节的HTML内容
        html_contents = []
        generated_sections = []
        
        for section in sections:
            section_id = section.get("id", "")
            section_title = section.get("title", "")
            section_content = section.get("content", [])
            
            try:
                # 仿真章节生成仿真代码
                if section_id == "simulation" or "仿真" in section_title:
                    simulation_desc = section_content[0] if isinstance(section_content, list) and section_content else str(section_content)
                    html_content = ai_service.generate_simulation_code(
                        simulation_desc=simulation_desc,
                        course=outline.course,
                        knowledge_point=outline.knowledge_point
                    )
                else:
                    # 普通章节生成HTML
                    html_content = ai_service.generate_section_content(
                        section_title=section_title,
                        section_key_points=section_content if isinstance(section_content, list) else [str(section_content)],
                        course=outline.course,
                        knowledge_point=outline.knowledge_point
                    )
                
                # 检查返回的内容是否包含失败标记
                has_error = '内容生成失败' in html_content or '仿真代码生成失败' in html_content
                
                html_contents.append(f"<section id='{section_id}'>\n{html_content}\n</section>")
                generated_sections.append({
                    "id": section_id,
                    "title": section_title,
                    "generated": not has_error,
                    "error": "AI生成返回失败内容" if has_error else None
                })
                
                if has_error:
                    logger.warning(f"Section {section_id} returned error content")
                    
            except Exception as e:
                logger.error(f"Failed to generate section {section_id}: {e}")
                # 即使异常也要添加失败内容到 html_contents
                error_content = f'<div class="warning"><strong>内容生成失败</strong><p>章节：{section_title}</p><p>错误：{str(e)[:200]}</p></div>'
                html_contents.append(f"<section id='{section_id}'>\n{error_content}\n</section>")
                generated_sections.append({
                    "id": section_id,
                    "title": section_title,
                    "generated": False,
                    "error": str(e)
                })
        
        # 合并 body 内容
        body_content = "\n\n".join(html_contents)
        title = outline_data.get("title", f"{outline.course} - {outline.knowledge_point}")
        
        # 生成完整 HTML 文档
        full_html = ai_service.generate_complete_html(title, body_content)
        
        # 根据存储类型决定保存方式
        file_path = None
        
        if settings.STORAGE_TYPE == "filesystem":
            # 先创建文档记录获取 ID
            document = Document(
                user_id=task.user_id,
                outline_id=outline.id,
                title=title,
                html_content=None,  # 暂时为空
                file_path=None
            )
            document.set_sections_data(generated_sections)
            db.add(document)
            db.commit()
            db.refresh(document)
            
            # 保存到文件系统
            file_path = file_storage_service.save_document(
                document_id=document.id,
                user_id=task.user_id,
                title=title,
                html_content=full_html
            )
            
            if file_path:
                # 更新文件路径，数据库只存摘要（前500字符）
                document.file_path = file_path
                document.html_content = full_html[:500] + "..." if len(full_html) > 500 else full_html
                db.commit()
                logger.info(f"Document {document.id} saved to filesystem: {file_path}")
            else:
                # 文件系统保存失败，回退到数据库存储
                document.html_content = full_html
                db.commit()
                logger.warning(f"Failed to save to filesystem, fallback to database for document {document.id}")
        else:
            # 数据库存储模式
            document = Document(
                user_id=task.user_id,
                outline_id=outline.id,
                title=title,
                html_content=full_html
            )
            document.set_sections_data(generated_sections)
            db.add(document)
            db.commit()
            db.refresh(document)
        
        # 更新任务关联资源
        task.resource_id = document.id
        task.resource_type = "document"
        db.commit()
        
        logger.info(f"Document {document.id} generated successfully for task {task.id}")
        
        return {
            "document_id": document.id,
            "title": title
        }
    
    async def process_task(self, task_id: int):
        """处理单个任务（在线程池中运行）"""
        db = SessionLocal()
        try:
            task = db.query(TaskQueue).filter(TaskQueue.id == task_id).first()
            if not task or task.status != TaskStatus.PENDING:
                return
            
            # 更新为处理中
            task.status = TaskStatus.PROCESSING
            task.started_at = datetime.now(timezone.utc)
            db.commit()
            
            logger.info(f"Processing task {task_id}, type: {task.task_type}")
            
            # 获取处理器
            handler = self._handlers.get(TaskType(task.task_type))
            if not handler:
                raise ValueError(f"Unknown task type: {task.task_type}")
            
            # 执行任务（在线程池中运行阻塞操作）
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, lambda: handler(db, task))
            
            # 更新为完成
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now(timezone.utc)
            task.set_result(result)
            db.commit()
            
            logger.info(f"Task {task_id} completed successfully with result: {result}")
            
        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            task.completed_at = datetime.now(timezone.utc)
            db.commit()
        finally:
            db.close()
    
    async def start_worker(self, worker_id: int):
        """启动工作线程"""
        logger.info(f"Worker {worker_id} started")
        while self._running:
            try:
                db = SessionLocal()
                try:
                    # 获取待处理任务
                    pending_tasks = self.get_pending_tasks(db, limit=1)
                    
                    if pending_tasks:
                        task = pending_tasks[0]
                        await self.process_task(task.id)
                    else:
                        # 没有任务，等待一段时间
                        await asyncio.sleep(1)
                finally:
                    db.close()
                    
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                await asyncio.sleep(5)
    
    async def start(self, num_workers: int = 2):
        """启动任务队列服务"""
        self._running = True
        self._workers = [
            asyncio.create_task(self.start_worker(i))
            for i in range(num_workers)
        ]
        logger.info(f"Task queue service started with {num_workers} workers")
    
    async def stop(self):
        """停止任务队列服务"""
        self._running = False
        if self._workers:
            await asyncio.gather(*self._workers, return_exceptions=True)
        logger.info("Task queue service stopped")


# 全局任务队列服务实例
task_queue_service = TaskQueueService()
