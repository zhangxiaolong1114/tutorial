"""
大纲相关 API 路由
- 生成大纲（异步任务）
- 获取大纲
- 更新大纲
- 根据大纲生成文档（异步任务）
"""
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.outline import Outline
from app.models.document import Document
from app.models.task_queue import TaskQueue, TaskStatus, TaskType
from app.services.task_queue_service import task_queue_service
from app.services.ai_service import ai_service

import logging

router = APIRouter(prefix="/outlines", tags=["大纲"])
logger = logging.getLogger(__name__)

def format_datetime(dt: datetime) -> str:
    """统一格式化日期时间，添加 UTC 时区标识"""
    if not dt:
        return None
    # if dt.tzinfo is None:
    #     dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


# ============ 请求/响应模型 ============

class OutlineGenerateRequest(BaseModel):
    """生成大纲请求"""
    course: str = Field(..., min_length=1, max_length=100, description="课程名称")
    knowledge_point: str = Field(..., min_length=1, max_length=200, description="知识点")
    difficulty: str = Field(default="medium", description="难度等级: easy, medium, hard")
    
    # 生成配置（可选，不传则使用默认配置）
    config: Optional[dict] = Field(default=None, description="生成配置")
    
    # 模型配置（可选，指定各任务使用的AI模型）
    ai_model_config: Optional[dict] = Field(default=None, description="模型配置")


class SectionUpdate(BaseModel):
    """章节更新数据"""
    id: str
    title: str
    content: list | str
    order: int


class OutlineUpdateRequest(BaseModel):
    """更新大纲请求"""
    sections: list = Field(..., description="章节列表")


class OutlineResponse(BaseModel):
    """大纲响应"""
    id: int
    user_id: int
    course: str
    knowledge_point: str
    difficulty: str
    title: str
    sections: list
    status: str
    created_at: str

    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    """文档响应"""
    id: int
    user_id: int
    outline_id: int
    title: str
    html_content: str
    sections: Optional[list]
    created_at: str

    class Config:
        from_attributes = True


class GenerateDocRequest(BaseModel):
    """生成文档请求"""
    title: Optional[str] = Field(None, description="文档标题，默认使用大纲标题")
    config: Optional[dict] = Field(None, description="生成配置（可选，覆盖大纲保存的配置）")
    ai_model_config: Optional[dict] = Field(None, description="模型配置（可选，指定各任务使用的AI模型）")


class TaskResponse(BaseModel):
    """任务响应"""
    task_id: int
    status: str
    message: str

    class Config:
        from_attributes = True


class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    task_id: int
    status: str
    task_type: str
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[dict] = None
    error_message: Optional[str] = None
    progress: int = 0  # 进度百分比 0-100
    progress_detail: Optional[dict] = None  # 进度详情
    models_used: Optional[list] = None  # 使用的模型列表

    class Config:
        from_attributes = True


# ============ 任务相关路由（必须放在 /{outline_id} 之前）============

@router.get("/tasks", response_model=List[TaskStatusResponse])
def list_tasks(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 50
):
    """
    获取当前用户的任务列表

    - **status**: 按状态筛选 (pending, processing, completed, failed)
    - **skip**: 跳过数量
    - **limit**: 返回数量限制
    """
    tasks = task_queue_service.get_user_tasks(
        db=db,
        user_id=current_user.id,
        status=TaskStatus(status) if status else None,
        limit=limit
    )

    return [
        {
            "task_id": task.id,
            "status": task.status,
            "task_type": task.task_type,
            "created_at": format_datetime(task.created_at),
            "started_at": format_datetime(task.started_at),
            "completed_at": format_datetime(task.completed_at),
            "result": task.get_result(),
            "error_message": task.error_message,
            "progress": task.progress or 0,
            "progress_detail": task.get_progress_detail()
        }
        for task in tasks
    ]


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
def get_task_status(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取任务状态

    - **task_id**: 任务 ID

    用于轮询异步任务的执行状态
    """
    task = task_queue_service.get_task(db, task_id, current_user.id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )

    def format_datetime(dt):
        """格式化日期时间，添加 UTC 时区标识"""
        if not dt:
            return None
        return dt.isoformat()

    # 获取结果中的 models_used
    result = task.get_result() or {}
    models_used = result.get("models_used")
    
    return {
        "task_id": task.id,
        "status": task.status,
        "task_type": task.task_type,
        "created_at": format_datetime(task.created_at),
        "started_at": format_datetime(task.started_at),
        "completed_at": format_datetime(task.completed_at),
        "result": result,
        "error_message": task.error_message,
        "progress": task.progress or 0,
        "progress_detail": task.get_progress_detail(),
        "models_used": models_used
    }


# ============ 大纲生成路由 ============

@router.post("/generate", response_model=TaskResponse, status_code=status.HTTP_202_ACCEPTED)
def generate_outline(
    request: OutlineGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    异步生成教学大纲

    - **course**: 课程名称
    - **knowledge_point**: 知识点
    - **difficulty**: 难度等级 (easy, medium, hard)

    立即返回任务ID，后台异步处理AI生成
    使用 GET /tasks/{task_id} 查询任务状态
    """
    try:
        logger.info(f"请求生成outline: user_id={current_user.id}, request={request.dict()}")
        # 创建异步任务
        task_params = {
            "course": request.course,
            "knowledge_point": request.knowledge_point,
            "difficulty": request.difficulty,
            "config": request.config  # 传递配置
        }
        
        # 如果请求中包含模型配置，传递给任务
        if request.ai_model_config:
            task_params["model_config"] = request.ai_model_config
        
        task = task_queue_service.create_task(
            db=db,
            user_id=current_user.id,
            task_type=TaskType.GENERATE_OUTLINE,
            params=task_params
        )

        return {
            "task_id": task.id,
            "status": task.status,
            "message": "大纲生成任务已创建，正在后台处理"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建任务失败: {str(e)}"
        )


# ============ 大纲列表路由 ============

@router.get("/", response_model=List[OutlineResponse])
def list_outlines(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 100
):
    """
    获取当前用户的大纲列表

    - **skip**: 跳过数量（分页）
    - **limit**: 返回数量限制
    """
    outlines = db.query(Outline).filter(
        Outline.user_id == current_user.id
    ).order_by(Outline.created_at.desc()).offset(skip).limit(limit).all()

    return [
        {
            "id": o.id,
            "user_id": o.user_id,
            "course": o.course,
            "knowledge_point": o.knowledge_point,
            "difficulty": o.difficulty,
            "title": o.get_outline_data().get("title", f"{o.course} - {o.knowledge_point}"),
            "sections": o.get_outline_data().get("sections", []),
            "status": o.status,
            "created_at": format_datetime(o.created_at)
        }
        for o in outlines
    ]


# ============ 单个大纲路由（/{outline_id} 必须放在最后）============

@router.get("/{outline_id}", response_model=OutlineResponse)
def get_outline(
    outline_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取大纲详情

    - **outline_id**: 大纲 ID

    只能访问自己的大纲
    """
    outline = db.query(Outline).filter(
        Outline.id == outline_id,
        Outline.user_id == current_user.id
    ).first()

    if not outline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="大纲不存在"
        )

    outline_data = outline.get_outline_data()
    return {
        "id": outline.id,
        "user_id": outline.user_id,
        "course": outline.course,
        "knowledge_point": outline.knowledge_point,
        "difficulty": outline.difficulty,
        "title": outline_data.get("title", f"{outline.course} - {outline.knowledge_point}"),
        "sections": outline_data.get("sections", []),
        "status": outline.status,
        "created_at": format_datetime(outline.created_at)
    }


@router.put("/{outline_id}", response_model=OutlineResponse)
def update_outline(
    outline_id: int,
    request: OutlineUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    更新大纲

    - **outline_id**: 大纲 ID
    - **sections**: 新的章节列表

    只能更新自己的大纲
    """
    outline = db.query(Outline).filter(
        Outline.id == outline_id,
        Outline.user_id == current_user.id
    ).first()

    if not outline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="大纲不存在"
        )

    # 更新大纲数据 - 合并现有数据和新的 sections
    outline_data = outline.get_outline_data()
    outline_data["sections"] = request.sections
    outline.set_outline_data(outline_data)
    db.commit()
    db.refresh(outline)

    outline_data = outline.get_outline_data()
    return {
        "id": outline.id,
        "user_id": outline.user_id,
        "course": outline.course,
        "knowledge_point": outline.knowledge_point,
        "difficulty": outline.difficulty,
        "title": outline_data.get("title", f"{outline.course} - {outline.knowledge_point}"),
        "sections": outline_data.get("sections", []),
        "status": outline.status,
        "created_at": format_datetime(outline.created_at)
    }


@router.delete("/{outline_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_outline(
    outline_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    删除大纲

    - **outline_id**: 大纲 ID

    只能删除自己的大纲，关联的文档也会被删除
    """
    outline = db.query(Outline).filter(
        Outline.id == outline_id,
        Outline.user_id == current_user.id
    ).first()

    if not outline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="大纲不存在"
        )

    db.delete(outline)
    db.commit()

    return None


@router.post("/{outline_id}/generate-doc", response_model=TaskResponse, status_code=status.HTTP_202_ACCEPTED)
def generate_document(
    outline_id: int,
    request: GenerateDocRequest = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    异步根据大纲生成文档

    - **outline_id**: 大纲 ID
    - **title**: 文档标题（可选，默认使用大纲标题）

    立即返回任务ID，后台异步生成文档内容
    使用 GET /tasks/{task_id} 查询任务状态
    """
    logger.info(f"请求生成document: user_id={current_user.id}, outline_id={outline_id},  request={request.dict()}")
    outline = db.query(Outline).filter(
        Outline.id == outline_id,
        Outline.user_id == current_user.id
    ).first()

    if not outline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="大纲不存在"
        )

    if outline.status != "generated":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="大纲尚未生成完成，无法创建文档"
        )

    try:
        # 创建异步任务
        task_params = {
            "outline_id": outline_id,
            "title": request.title if request else None
        }

        # 如果请求中包含配置，传递给任务
        if request and request.config:
            task_params["config"] = request.config
        
        # 如果请求中包含模型配置，传递给任务
        if request and request.ai_model_config:
            task_params["model_config"] = request.ai_model_config
            import logging
            logging.getLogger(__name__).info(f"[API] 接收到模型配置: {request.ai_model_config}")

        task = task_queue_service.create_task(
            db=db,
            user_id=current_user.id,
            task_type=TaskType.GENERATE_DOCUMENT,
            params=task_params
        )

        return {
            "task_id": task.id,
            "status": task.status,
            "message": "文档生成任务已创建，正在后台处理"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建任务失败: {str(e)}"
        )


@router.get("/{outline_id}/documents", response_model=List[DocumentResponse])
def list_documents(
    outline_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取大纲关联的文档列表

    - **outline_id**: 大纲 ID
    """
    # 先检查大纲是否存在且属于当前用户
    outline = db.query(Outline).filter(
        Outline.id == outline_id,
        Outline.user_id == current_user.id
    ).first()

    if not outline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="大纲不存在"
        )

    documents = db.query(Document).filter(
        Document.outline_id == outline_id,
        Document.user_id == current_user.id
    ).order_by(Document.created_at.desc()).all()

    return [
        {
            "id": d.id,
            "user_id": d.user_id,
            "outline_id": d.outline_id,
            "title": d.title,
            "html_content": d.html_content,
            "sections": d.get_sections_data(),
            "created_at": d.created_at.isoformat()
        }
        for d in documents
    ]
