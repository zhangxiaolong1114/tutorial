"""
任务队列服务 - 增强版
添加结构化日志、异常追踪、任务超时处理
"""
import asyncio
import logging
import signal
import sys
import traceback
from datetime import datetime, timezone, timedelta
from typing import Optional, Callable, Dict, Any
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.config import get_settings
from app.core.cost_tracker import cost_tracker
from app.core.task_logger import get_task_logger, TaskLogContext
from app.models.task_queue import TaskQueue, TaskStatus, TaskType
from app.services.ai_service import ai_service
from app.services.file_storage_service import file_storage_service

settings = get_settings()

logger = logging.getLogger(__name__)


class TaskExecutionError(Exception):
    """任务执行错误"""
    def __init__(self, message: str, error_type: str = None, details: dict = None):
        super().__init__(message)
        self.error_type = error_type or "unknown"
        self.details = details or {}


class TaskTimeoutError(TaskExecutionError):
    """任务超时错误"""
    def __init__(self, timeout_seconds: int):
        super().__init__(
            f"任务执行超时（{timeout_seconds}秒）",
            error_type="timeout",
            details={"timeout_seconds": timeout_seconds}
        )


class TaskQueueService:
    """任务队列服务 - 增强版"""
    
    # 任务超时配置（秒）
    TASK_TIMEOUTS = {
        TaskType.GENERATE_OUTLINE: 300,      # 5分钟
        TaskType.GENERATE_DOCUMENT: 1800,    # 30分钟
    }
    
    def __init__(self):
        self._running = False
        self._workers = []
        self._handlers: Dict[TaskType, Callable] = {}
        self._shutdown_event = asyncio.Event()
        self._register_handlers()
        
        # 注册信号处理
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """处理系统信号"""
        logger.info(f"收到信号 {signum}，准备优雅关闭...")
        self._shutdown_event.set()
    
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
        """创建新任务"""
        task = TaskQueue(
            user_id=user_id,
            task_type=task_type,
            status=TaskStatus.PENDING
        )
        task.set_params(params)
        
        db.add(task)
        db.commit()
        db.refresh(task)
        
        logger.info(f"[Task] 创建任务 {task.id} (用户 {user_id}, 类型 {task_type}, 参数 {params})")
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
        """获取待处理的任务（包含卡住的任务）"""
        # 同时获取卡住的任务（处理中但超时）
        timeout_threshold = datetime.now() - timedelta(hours=1)
        
        return db.query(TaskQueue).filter(
            (TaskQueue.status == TaskStatus.PENDING) |
            ((TaskQueue.status == TaskStatus.PROCESSING) & 
             (TaskQueue.started_at < timeout_threshold))
        ).order_by(TaskQueue.created_at.asc()).limit(limit).all()
    
    async def process_task(self, task_id: int):
        """处理单个任务（带完整日志和异常处理）"""
        db = SessionLocal()
        task_logger = get_task_logger()
        log_context: Optional[TaskLogContext] = None
        
        try:
            task = db.query(TaskQueue).filter(TaskQueue.id == task_id).first()
            if not task:
                logger.warning(f"[Task] 任务 {task_id} 不存在")
                return
            
            if task.status == TaskStatus.PROCESSING:
                # 检查是否卡住（超时）
                if task.started_at and (datetime.now() - task.started_at).seconds > 3600:
                    logger.warning(f"[Task] 任务 {task_id} 卡住，重新执行")
                else:
                    logger.info(f"[Task] 任务 {task_id} 正在处理中，跳过")
                    return
            
            # 初始化任务日志
            log_context = task_logger.start_task(
                task_id=str(task_id),
                task_type=task.task_type.value if hasattr(task.task_type, 'value') else str(task.task_type),
                user_id=task.user_id
            )
            
            # 更新为处理中
            task.status = TaskStatus.PROCESSING
            task.started_at = datetime.now()
            task.error_message = None  # 清除之前的错误
            db.commit()
            
            log_context.info("任务开始处理", 
                           task_type=task.task_type.value if hasattr(task.task_type, 'value') else str(task.task_type),
                           params=task.get_params())
            
            logger.info(f"[Task] 开始处理任务 {task_id}, 类型: {task.task_type}")
            
            # 获取处理器
            task_type_enum = TaskType(task.task_type) if isinstance(task.task_type, str) else task.task_type
            handler = self._handlers.get(task_type_enum)
            if not handler:
                raise TaskExecutionError(f"未知任务类型: {task.task_type}", error_type="unknown_task_type")
            
            # 获取超时时间
            timeout = self.TASK_TIMEOUTS.get(task_type_enum, 600)
            
            # 执行任务（带超时）
            try:
                loop = asyncio.get_event_loop()
                result = await asyncio.wait_for(
                    loop.run_in_executor(None, lambda: self._execute_with_logging(handler, db, task, log_context)),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                raise TaskTimeoutError(timeout)
            
            # 更新为完成
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.set_result(result)
            task.progress = 100
            db.commit()
            
            log_context.info("任务完成", result=result)
            task_logger.end_task(str(task_id), status="completed", result=result)
            
            logger.info(f"[Task] 任务 {task_id} 完成，结果: {result}")
            
        except TaskExecutionError as e:
            logger.error(f"[Task] 任务 {task_id} 执行错误: {e}")
            self._handle_task_error(db, task, e, log_context)
            
        except Exception as e:
            logger.error(f"[Task] 任务 {task_id} 未预期错误: {e}")
            logger.error(traceback.format_exc())
            
            # 包装为 TaskExecutionError
            wrapped_error = TaskExecutionError(
                message=str(e),
                error_type=type(e).__name__,
                details={"traceback": traceback.format_exc()}
            )
            self._handle_task_error(db, task, wrapped_error, log_context)
            
        finally:
            db.close()
    
    def _execute_with_logging(self, handler: Callable, db: Session, task: TaskQueue, log_context: TaskLogContext):
        """执行任务并记录详细日志"""
        try:
            return handler(db, task, log_context)
        except Exception as e:
            # 记录详细异常信息
            log_context.exception(f"任务执行异常: {str(e)}")
            raise
    
    def _handle_task_error(self, db: Session, task: TaskQueue, error: TaskExecutionError, log_context: Optional[TaskLogContext]):
        """处理任务错误"""
        task.status = TaskStatus.FAILED
        task.completed_at = datetime.now()
        
        # 构建错误信息
        error_info = {
            "error_type": error.error_type,
            "message": str(error),
            "details": error.details
        }
        
        # 限制错误信息长度
        error_message = str(error)[:500]
        task.error_message = error_message
        task.set_result({"error": error_info})
        
        db.commit()
        
        if log_context:
            log_context.error("任务失败", error_type=error.error_type, details=error.details)
            get_task_logger().end_task(str(task.id), status="failed", result={"error": error_info})
    
    def _handle_generate_outline(self, db: Session, task: TaskQueue, log_context: TaskLogContext) -> Dict[str, Any]:
        """处理生成大纲任务"""
        from app.models.outline import Outline
        
        params = task.get_params()
        course = params.get("course")
        knowledge_point = params.get("knowledge_point")
        difficulty = params.get("difficulty", "medium")
        config = params.get("config")
        
        log_context.info("开始生成大纲",
                        course=course,
                        knowledge_point=knowledge_point,
                        difficulty=difficulty,
                        has_config=bool(config))
        
        # 更新进度
        task.update_progress(10, {"phase": "generating_outline", "message": "正在生成教学大纲..."})
        db.commit()
        
        # 获取模型配置
        model_config = params.get("model_config", {})
        log_context.warning(f"model_config: {model_config}")
        outline_model_id = model_config.get("outline_model_id")
        
        # 记录使用的模型
        models_used = []
        
        try:
            # 调用AI服务
            if config:
                log_context.info("使用配置化生成", 
                               teaching_style=config.get('teaching_style'),
                               difficulty=config.get('difficulty'),
                               model_id=outline_model_id or "default")
                outline_data = ai_service.generate_outline(
                    course=course,
                    knowledge_point=knowledge_point,
                    config=config,
                    task_id=str(task.id),
                    model_id=outline_model_id,
                )
            else:
                log_context.info("使用默认生成方法", model_id=outline_model_id or "default")
                outline_data = ai_service.generate_outline(
                    course=course,
                    knowledge_point=knowledge_point,
                    config={"difficulty": difficulty},
                    task_id=str(task.id),
                    model_id=outline_model_id,
                )
            
            # 记录使用的模型
            models_used.append({
                "task": "outline",
                "model_id": outline_model_id or "kimi-k2.5 (default)"
            })
            
            log_context.info("大纲生成完成", 
                           section_count=len(outline_data.get('sections', [])),
                           models_used=models_used)
            
        except Exception as e:
            log_context.exception("大纲生成失败")
            raise TaskExecutionError(f"大纲生成失败: {str(e)}", error_type="ai_generation_failed")
        
        # 创建大纲记录
        try:
            outline = Outline(
                user_id=task.user_id,
                course=course,
                knowledge_point=knowledge_point,
                difficulty=difficulty,
                outline_json="",
                status="generated"
            )
            
            if config:
                outline_data["config"] = config
            
            outline.set_outline_data(outline_data)
            db.add(outline)
            db.commit()
            db.refresh(outline)
            
            log_context.info("大纲记录创建成功", outline_id=outline.id)
            
        except Exception as e:
            log_context.exception("保存大纲失败")
            raise TaskExecutionError(f"保存大纲失败: {str(e)}", error_type="database_error")
        
        # 更新任务进度
        task.update_progress(100, {"phase": "completed", "message": "大纲生成完成"})
        task.resource_id = outline.id
        task.resource_type = "outline"
        db.commit()
        
        # 记录成本
        try:
            cost_tracker.record_cost_from_logs(
                db=db,
                task_id=str(task.id),
                user_id=task.user_id,
                outline_id=outline.id,
                course=course,
                knowledge_point=knowledge_point,
            )
        except Exception as e:
            log_context.warning(f"记录成本失败: {e}")
        
        return {
            "outline_id": outline.id,
            "title": outline_data.get("title", f"{course} - {knowledge_point}"),
            "models_used": models_used
        }
    
    def _handle_generate_document(self, db: Session, task: TaskQueue, log_context: TaskLogContext) -> Dict[str, Any]:
        """处理生成文档任务"""
        from app.models.outline import Outline
        from app.models.document import Document
        
        params = task.get_params()
        outline_id = params.get("outline_id")
        
        log_context.info("开始生成文档", outline_id=outline_id)
        
        # 获取大纲
        outline = db.query(Outline).filter(
            Outline.id == outline_id,
            Outline.user_id == task.user_id
        ).first()
        
        if not outline:
            raise TaskExecutionError(f"大纲 {outline_id} 不存在", error_type="outline_not_found")
        
        outline_data = outline.get_outline_data()
        sections = outline_data.get("sections", [])
        
        # 获取配置
        config = params.get("config") or outline_data.get("config")
        model_config = params.get("model_config", {})
        log_context.warning(f"model_config: {model_config}")
        logger.info(f"[Task {task.id}] 文档生成参数: params keys={list(params.keys())}, model_config={model_config}")
        
        # 获取模型配置
        section_model_id = model_config.get("section_model_id")
        simulation_model_id = model_config.get("simulation_model_id")
        
        log_context.info("文档生成配置",
                        section_count=len(sections),
                        has_config=bool(config),
                        model_config=model_config,
                        section_model_id=section_model_id or "default",
                        simulation_model_id=simulation_model_id or "default")
        
        # 记录使用的模型
        models_used = []
        
        # 初始化进度
        task.update_progress(5, {
            "phase": "initializing",
            "message": "开始生成文档...",
            "total_sections": len(sections)
        })
        db.commit()
        
        # 准备大纲结构信息
        outline_structure = "\n".join([
            f"{i+1}. {s.get('title', '未命名')}"
            for i, s in enumerate(sections)
        ])
        
        # 生成每个章节
        html_contents = []
        generated_sections = []
        prev_section_summary = None
        prev_summaries = []  # 存储最近2章的摘要
        
        for section_index, section in enumerate(sections):
            section_id = section.get("id", "")
            section_title = section.get("title", "")
            section_content = section.get("content", [])
            
            # 更新进度
            progress = 10 + int((section_index / len(sections)) * 80)
            task.update_progress(progress, {
                "phase": "generating_sections",
                "current_section": section_title,
                "section_index": section_index + 1,
                "total_sections": len(sections),
                "message": f"正在生成章节: {section_title}"
            })
            db.commit()
            
            log_context.info(f"生成章节 {section_index + 1}/{len(sections)}",
                           section_id=section_id,
                           section_title=section_title)
            
            # 构建上下文（增强版 - 支持完整大纲和章节关联信息）
            current_section = sections[section_index]
            context = {
                # 完整大纲结构（用于全局定位）
                "full_outline": sections,
                "current_index": section_index,
                "position": {
                    "current_index": section_index,
                    "total": len(sections),
                    "prev_title": sections[section_index - 1].get("title") if section_index > 0 else None,
                    "next_title": sections[section_index + 1].get("title") if section_index < len(sections) - 1 else None
                },
                # 当前章节的关联信息（从大纲中获取）
                "current_section_meta": {
                    "prerequisites": current_section.get("prerequisites", []),
                    "prepares_for": current_section.get("prepares_for", []),
                    "key_formulas": current_section.get("key_formulas", [])
                },
                # 前置章节摘要（最近2章，每章800字符）
                "prev_summaries": prev_summaries if 'prev_summaries' in locals() else ([prev_section_summary] if prev_section_summary else []),
                # 保留旧字段兼容性
                "outline_structure": outline_structure,
                "prev_summary": prev_section_summary,
                "generated_sections": "\n".join([
                    f"- {s.get('title')}" for s in sections[:section_index]
                ]) if section_index > 0 else "无"
            }
            
            # 生成章节
            try:
                section_result = self._generate_section_with_retry(
                    section=section,
                    section_index=section_index,
                    outline=outline,
                    config=config,
                    task_id=str(task.id),
                    context=context,
                    max_retries=2,
                    model_config=model_config,
                )
                
                html_contents.append(section_result['html'])
                generated_sections.append(section_result['meta'])
                
                # 记录使用的模型
                model_used = section_result['meta'].get('model_used', 'unknown')
                if model_used and model_used not in [m['model_id'] for m in models_used]:
                    models_used.append({
                        "task": "simulation" if section_result['meta'].get('type') == 'simulation' else 'section',
                        "model_id": model_used,
                        "section": section_title
                    })
                
                if section_result['meta']['generated']:
                    prev_section_summary = self._extract_section_summary(section_title, section_result['content'])
                    # 维护最近2章的摘要列表
                    prev_summaries.insert(0, prev_section_summary)
                    if len(prev_summaries) > 2:
                        prev_summaries.pop()
                    log_context.info(f"章节 {section_id} 生成成功", model_used=model_used)
                else:
                    prev_section_summary = {
                        "title": section_title,
                        "content": "章节生成失败，将在文档中显示错误提示。"
                    }
                    log_context.warning(f"章节 {section_id} 生成失败", error=section_result['meta'].get('error'), model_used=model_used)
                    
            except Exception as e:
                log_context.exception(f"章节 {section_id} 生成异常")
                # 添加错误占位
                error_html = f'<div class="warning"><strong>章节生成失败</strong><p>{section_title}</p><p>{str(e)[:200]}</p></div>'
                html_contents.append(f"<section id='{section_id}'>{error_html}</section>")
                generated_sections.append({
                    "id": section_id,
                    "title": section_title,
                    "generated": False,
                    "error": str(e),
                    "model_used": (simulation_model_id if is_simulation else section_model_id) or "kimi-k2.5 (default)"
                })
        
        # 合并内容
        body_content = "\n\n".join(html_contents)
        title = outline_data.get("title", f"{outline.course} - {outline.knowledge_point}")
        
        # 更新进度
        task.update_progress(90, {
            "phase": "finalizing",
            "message": "正在生成最终文档..."
        })
        db.commit()
        
        # 生成完整 HTML
        try:
            full_html = ai_service.generate_complete_html(title, body_content)
            log_context.info("HTML文档生成完成", content_length=len(full_html))
        except Exception as e:
            log_context.exception("生成HTML文档失败")
            raise TaskExecutionError(f"生成HTML文档失败: {str(e)}", error_type="html_generation_failed")
        
        # 保存文档
        try:
            document = self._save_document(
                db=db,
                task=task,
                outline=outline,
                title=title,
                full_html=full_html,
                generated_sections=generated_sections,
                log_context=log_context
            )
        except Exception as e:
            log_context.exception("保存文档失败")
            raise TaskExecutionError(f"保存文档失败: {str(e)}", error_type="save_failed")
        
        # 更新任务
        task.resource_id = document.id
        task.resource_type = "document"
        db.commit()
        
        # 记录成本
        try:
            cost_tracker.record_cost_from_logs(
                db=db,
                task_id=str(task.id),
                user_id=task.user_id,
                outline_id=outline.id,
                document_id=document.id,
                course=outline.course,
                knowledge_point=outline.knowledge_point,
            )
        except Exception as e:
            log_context.warning(f"记录成本失败: {e}")
        
        log_context.info("文档生成完成", document_id=document.id, models_used=models_used)
        
        return {
            "document_id": document.id,
            "title": title,
            "models_used": models_used
        }
    
    def _generate_section_with_retry(
        self,
        section: dict,
        section_index: int,
        outline,
        config: dict,
        task_id: str,
        context: dict,
        max_retries: int = 2,
        model_config: dict = None,
    ) -> dict:
        """带重试机制的章节生成"""
        section_id = section.get("id", "")
        section_title = section.get("title", "")
        section_content = section.get("content", [])
        is_simulation = section_id == "simulation" or "仿真" in section_title
        
        model_config = model_config or {}
        section_model_id = model_config.get("section_model_id")
        simulation_model_id = model_config.get("simulation_model_id")
        
        logger.info(f"[Task {task_id}] 生成章节 {section_id}, is_simulation={is_simulation}, model_config={model_config}")
        
        for attempt in range(max_retries + 1):
            try:
                if is_simulation:
                    # 仿真章节 - 使用完整的章节内容
                    # 合并所有要点作为完整的仿真需求
                    if isinstance(section_content, list) and len(section_content) > 0:
                        simulation_desc = "\n".join(section_content)
                    else:
                        simulation_desc = str(section_content)
                    
                    # 从当前章节获取关联信息（直接从section获取，确保完整）
                    key_formulas = section.get("key_formulas", []) if isinstance(section, dict) else []
                    prerequisites = section.get("prerequisites", []) if isinstance(section, dict) else []
                    prepares_for = section.get("prepares_for", []) if isinstance(section, dict) else []
                    
                    # 获取前后章节标题
                    prev_title = None
                    next_title = None
                    if context and context.get("full_outline"):
                        full_outline = context["full_outline"]
                        current_idx = context.get("current_index", 0)
                        if current_idx > 0:
                            prev_title = full_outline[current_idx - 1].get("title")
                        if current_idx < len(full_outline) - 1:
                            next_title = full_outline[current_idx + 1].get("title")
                    
                    # 构建V2版本的仿真上下文 - 包含完整的章节信息
                    simulation_context = {
                        "prev_summary": context.get("prev_summary") if context else None,
                        "prev_summaries": context.get("prev_summaries") if context else None,
                        "outline_structure": context.get("outline_structure") if context else None,
                        "full_outline": context.get("full_outline") if context else None,
                        "current_index": context.get("current_index") if context else 0,
                        "key_formulas": key_formulas,
                        "prerequisites": prerequisites,
                        "prepares_for": prepares_for,
                        "section_content": section_content if isinstance(section_content, list) else [str(section_content)],
                        "section_title": section_title,
                        "prev_section_title": prev_title,
                        "next_section_title": next_title,
                        # 添加完整的当前章节信息
                        "current_section_full": {
                            "id": section_id,
                            "title": section_title,
                            "content": section_content,
                            "prerequisites": prerequisites,
                            "prepares_for": prepares_for,
                            "key_formulas": key_formulas
                        }
                    }
                    
                    logger.info(f"[Task {task_id}] 开始生成仿真 (V2): {simulation_desc[:100]}")
                    
                    try:
                        simulation_html = ai_service.generate_simulation(
                            simulation_desc=simulation_desc,
                            course=outline.course,
                            knowledge_point=outline.knowledge_point,
                            simulation_types=config.get('simulation_types', ['animation']) if config else ['animation'],
                            config=config or {},
                            task_id=task_id,
                            context=simulation_context,
                            model_id=simulation_model_id,
                            use_v2=True,  # 使用V2版本
                        )
                        
                        logger.info(f"[Task {task_id}] 仿真生成完成, HTML长度: {len(simulation_html)}")
                        
                        has_error = '仿真代码生成失败' in simulation_html or '仿真生成失败' in simulation_html or len(simulation_html) < 500
                        
                    except Exception as sim_error:
                        logger.error(f"[Task {task_id}] 仿真生成异常: {sim_error}")
                        # 返回错误占位
                        error_html = f'<div class="warning"><strong>仿真生成失败</strong><p>错误：{str(sim_error)[:200]}</p></div>'
                        return {
                            'html': f"<section id='{section_id}'>{error_html}</section>",
                            'content': error_html,
                            'meta': {
                                "id": section_id,
                                "title": section_title,
                                "generated": False,
                                "error": str(sim_error),
                                "type": "simulation",
                                "retry_count": attempt
                            }
                        }
                    
                    if not has_error:
                        # 将仿真代码用 iframe 包裹，实现沙箱隔离
                        iframe_html = self._wrap_simulation_in_iframe(simulation_html, section_title)
                        wrapped_html = f'''<div class="section-content">
<h3>{section_title}</h3>
{iframe_html}
</div>'''
                        return {
                            'html': f"<section id='{section_id}'>\n{wrapped_html}\n</section>",
                            'content': wrapped_html,
                            'meta': {
                                "id": section_id,
                                "title": section_title,
                                "generated": True,
                                "error": None,
                                "type": "simulation",
                                "retry_count": attempt,
                                "model_used": simulation_model_id or "kimi-k2.5 (default)"
                            }
                        }
                    elif attempt < max_retries:
                        import time
                        time.sleep(2 ** attempt)
                    else:
                        return {
                            'html': f"<section id='{section_id}'>\n{simulation_html}\n</section>",
                            'content': simulation_html,
                            'meta': {
                                "id": section_id,
                                "title": section_title,
                                "generated": False,
                                "error": "仿真生成失败（重试耗尽）",
                                "type": "simulation",
                                "retry_count": attempt,
                                "model_used": simulation_model_id or "kimi-k2.5 (default)"
                            }
                        }
                
                else:
                    # 普通章节 - 传递完整的章节信息
                    # 构建包含完整章节信息的上下文
                    section_context = {
                        **context,
                        "current_section_full": {
                            "id": section_id,
                            "title": section_title,
                            "content": section_content,
                            "prerequisites": section.get("prerequisites", []),
                            "prepares_for": section.get("prepares_for", []),
                            "key_formulas": section.get("key_formulas", [])
                        }
                    }
                    
                    if config:
                        html_content = ai_service.generate_section(
                            section_title=section_title,
                            section_key_points=section_content if isinstance(section_content, list) else [str(section_content)],
                            course=outline.course,
                            knowledge_point=outline.knowledge_point,
                            config=config,
                            task_id=task_id,
                            model_id=section_model_id,
                            context=section_context,
                        )
                    else:
                        html_content = ai_service.generate_section(
                            section_title=section_title,
                            section_key_points=section_content if isinstance(section_content, list) else [str(section_content)],
                            course=outline.course,
                            knowledge_point=outline.knowledge_point,
                            config={},
                            task_id=task_id,
                            model_id=section_model_id,
                            context=section_context,
                        )
                    
                    has_error = '内容生成失败' in html_content
                    
                    if not has_error:
                        return {
                            'html': f"<section id='{section_id}'>\n{html_content}\n</section>",
                            'content': html_content,
                            'meta': {
                                "id": section_id,
                                "title": section_title,
                                "generated": True,
                                "error": None,
                                "type": "content",
                                "retry_count": attempt,
                                "model_used": section_model_id or "kimi-k2.5 (default)"
                            }
                        }
                    elif attempt < max_retries:
                        import time
                        time.sleep(2 ** attempt)
                    else:
                        return {
                            'html': f"<section id='{section_id}'>\n{html_content}\n</section>",
                            'content': html_content,
                            'meta': {
                                "id": section_id,
                                "title": section_title,
                                "generated": False,
                                "error": "AI生成返回失败内容（重试耗尽）",
                                "type": "content",
                                "retry_count": attempt,
                                "model_used": section_model_id or "kimi-k2.5 (default)"
                            }
                        }
                        
            except Exception as e:
                logger.error(f"[Retry {attempt}] 生成章节 {section_id} 失败: {e}")
                if attempt < max_retries:
                    import time
                    time.sleep(2 ** attempt)
                else:
                    error_content = f'<div class="warning"><strong>内容生成失败</strong><p>章节：{section_title}</p><p>错误：{str(e)[:200]}</p></div>'
                    return {
                        'html': f"<section id='{section_id}'>\n{error_content}\n</section>",
                        'content': error_content,
                        'meta': {
                            "id": section_id,
                            "title": section_title,
                            "generated": False,
                            "error": str(e),
                            "type": "simulation" if is_simulation else "content",
                            "retry_count": attempt,
                            "model_used": (simulation_model_id if is_simulation else section_model_id) or "kimi-k2.5 (default)"
                        }
                    }
    
    def _extract_section_summary(self, section_title: str, html_content: str) -> dict:
        """从章节 HTML 内容中提取摘要"""
        import re
        
        text = re.sub(r'<[^>]+>', ' ', html_content)
        text = re.sub(r'\s+', ' ', text).strip()
        
        summary_text = text[:300] if len(text) > 300 else text
        
        formulas = re.findall(r'\$\$(.*?)\$\$', html_content)
        formula_summary = f"核心公式: {'; '.join(formulas[:2])}" if formulas else ""
        
        return {
            "title": section_title,
            "content": summary_text,
            "formulas": formula_summary
        }
    
    def _wrap_simulation_in_iframe(self, simulation_html: str, section_title: str) -> str:
        """
        将仿真代码用 iframe 包裹，实现沙箱隔离
        
        Args:
            simulation_html: 仿真 HTML 代码
            section_title: 章节标题
            
        Returns:
            包含 iframe 的 HTML 代码
        """
        import base64
        
        # 构建完整的 iframe 内容
        iframe_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{section_title} - 仿真</title>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f7fa;
        }}
        .simulation-wrapper {{
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
    </style>
</head>
<body>
    <div class="simulation-wrapper">
        {simulation_html}
    </div>
</body>
</html>'''
        
        # Base64 编码
        encoded_content = base64.b64encode(iframe_content.encode('utf-8')).decode('utf-8')
        
        # 生成 iframe HTML
        iframe_html = f'''<div class="simulation-iframe-wrapper" style="margin: 20px 0; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
    <iframe 
        src="data:text/html;base64,{encoded_content}" 
        style="width: 100%; height: 600px; border: none; display: block;"
        sandbox="allow-scripts allow-same-origin"
        title="{section_title}"
        loading="lazy"
    ></iframe>
</div>'''
        
        return iframe_html
    
    def _save_document(self, db: Session, task: TaskQueue, outline, title: str, 
                       full_html: str, generated_sections: list, log_context: TaskLogContext) -> "Document":
        """保存文档到数据库或文件系统"""
        from app.models.document import Document
        
        if settings.STORAGE_TYPE == "filesystem":
            # 先创建记录
            document = Document(
                user_id=task.user_id,
                outline_id=outline.id,
                title=title,
                html_content=None,
                file_path=None,
                simulation_code=None
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
                document.file_path = file_path
                document.html_content = full_html[:500] + "..." if len(full_html) > 500 else full_html
                db.commit()
                log_context.info("文档保存到文件系统", file_path=file_path)
            else:
                document.html_content = full_html
                db.commit()
                log_context.warning("文件系统保存失败，回退到数据库")
        else:
            # 数据库存储
            document = Document(
                user_id=task.user_id,
                outline_id=outline.id,
                title=title,
                html_content=full_html,
                simulation_code=None
            )
            document.set_sections_data(generated_sections)
            db.add(document)
            db.commit()
            db.refresh(document)
            log_context.info("文档保存到数据库", document_id=document.id)
        
        return document
    
    async def start_worker(self, worker_id: int):
        """启动工作线程"""
        logger.info(f"[Worker] {worker_id} 启动")
        
        while self._running and not self._shutdown_event.is_set():
            try:
                db = SessionLocal()
                try:
                    pending_tasks = self.get_pending_tasks(db, limit=1)
                    
                    if pending_tasks:
                        task = pending_tasks[0]
                        logger.info(f"[Worker {worker_id}] 获取任务 {task.id}")
                        await self.process_task(task.id)
                    else:
                        await asyncio.wait_for(
                            self._shutdown_event.wait(),
                            timeout=1.0
                        )
                        
                except asyncio.TimeoutError:
                    pass
                finally:
                    db.close()
                    
            except Exception as e:
                logger.error(f"[Worker {worker_id}] 错误: {e}")
                logger.error(traceback.format_exc())
                await asyncio.sleep(5)
        
        logger.info(f"[Worker] {worker_id} 停止")
    
    async def start(self, num_workers: int = 2):
        """启动任务队列服务"""
        self._running = True
        self._workers = [
            asyncio.create_task(self.start_worker(i))
            for i in range(num_workers)
        ]
        logger.info(f"[Service] 任务队列服务启动，{num_workers} 个工作线程")
    
    async def stop(self):
        """停止任务队列服务"""
        logger.info("[Service] 正在停止任务队列服务...")
        self._running = False
        self._shutdown_event.set()
        
        if self._workers:
            await asyncio.gather(*self._workers, return_exceptions=True)
        
        logger.info("[Service] 任务队列服务已停止")


# 全局任务队列服务实例
task_queue_service = TaskQueueService()
