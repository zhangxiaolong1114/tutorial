"""
文档相关 API 路由
- 获取文档详情
- 获取文档 HTML 内容
- 删除文档
- 列出用户的所有文档
"""
import logging
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import get_settings
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.document import Document
from app.services.file_storage_service import file_storage_service

settings = get_settings()
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["文档"])


def format_datetime(dt: datetime) -> str:
    """统一格式化日期时间，添加 UTC 时区标识"""
    if not dt:
        return None
    # if dt.tzinfo is None:
    #     dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


# ============ 请求/响应模型 ============

class DocumentResponse(BaseModel):
    """文档响应"""
    id: int
    user_id: int
    outline_id: int
    title: str
    sections: Optional[list]
    created_at: str
    
    class Config:
        from_attributes = True


class DocumentDetailResponse(DocumentResponse):
    """文档详情响应（包含 HTML 内容）"""
    html_content: str


class DocumentUpdateRequest(BaseModel):
    """更新文档请求"""
    title: Optional[str] = Field(None, description="文档标题")


# ============ 辅助函数 ============

def _get_document_content(document: Document) -> str:
    """获取文档完整内容（支持文件系统和数据库）"""
    if document.file_path:
        # 从文件系统读取
        content = file_storage_service.read_document(document.file_path)
        if content:
            return content
        # 文件读取失败，回退到数据库
        logger.warning(f"Failed to read from filesystem, fallback to database for document {document.id}")
    return document.html_content or ""


# ============ API 路由 ============

@router.get("/", response_model=List[DocumentResponse])
def list_user_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 100
):
    """
    获取当前用户的所有文档列表
    
    - **skip**: 跳过数量（分页）
    - **limit**: 返回数量限制
    """
    documents = db.query(Document).filter(
        Document.user_id == current_user.id
    ).order_by(Document.created_at.desc()).offset(skip).limit(limit).all()
    
    return [
        {
            "id": d.id,
            "user_id": d.user_id,
            "outline_id": d.outline_id,
            "title": d.title,
            "sections": d.get_sections_data(),
            "created_at": format_datetime(d.created_at)
        }
        for d in documents
    ]


@router.get("/{document_id}", response_model=DocumentDetailResponse)
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取文档详情
    
    - **document_id**: 文档 ID
    
    只能访问自己的文档
    """
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档不存在"
        )
    
    # 获取完整内容（支持文件系统）
    html_content = _get_document_content(document)
    
    return {
        "id": document.id,
        "user_id": document.user_id,
        "outline_id": document.outline_id,
        "title": document.title,
        "html_content": html_content,
        "sections": document.get_sections_data(),
        "created_at": format_datetime(document.created_at),
    }


@router.get("/{document_id}/html")
def get_document_html(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取文档的 HTML 内容（纯 HTML，无包装）
    
    - **document_id**: 文档 ID
    
    返回纯 HTML 内容，可用于直接渲染或下载
    """
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档不存在"
        )
    
    # 获取完整内容（支持文件系统）
    html_content = _get_document_content(document)
    
    return Response(
        content=html_content,
        media_type="text/html"
    )


@router.get("/{document_id}/download")
def download_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    下载文档为 HTML 文件
    
    - **document_id**: 文档 ID
    
    返回完整的 HTML 文件，可直接在浏览器中打开
    """
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档不存在"
        )
    
    # 获取完整内容（支持文件系统）
    html_content = _get_document_content(document)
    
    # 生成安全的文件名
    safe_title = "".join(c for c in document.title if c.isascii() and (c.isalnum() or c in (' ', '-', '_'))).rstrip()
    filename = f"{safe_title or 'document'}.html"

    # 对中文文件名进行 URL 编码
    from urllib.parse import quote
    encoded_filename = quote(document.title + '.html', safe='')

    return Response(
        content=html_content,
        media_type="text/html",
        headers={
            "Content-Disposition": f"attachment; filename=\"{filename}\"; filename*=UTF-8''{encoded_filename}"
        }
    )


@router.put("/{document_id}", response_model=DocumentResponse)
def update_document(
    document_id: int,
    request: DocumentUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    更新文档信息
    
    - **document_id**: 文档 ID
    - **title**: 新标题（可选）
    
    只能更新自己的文档
    """
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档不存在"
        )
    
    # 更新字段
    if request.title is not None:
        document.title = request.title
    
    db.commit()
    db.refresh(document)
    
    return {
        "id": document.id,
        "user_id": document.user_id,
        "outline_id": document.outline_id,
        "title": document.title,
        "sections": document.get_sections_data(),
        "created_at": format_datetime(document.created_at)
    }


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    删除文档

    - **document_id**: 文档 ID

    只能删除自己的文档，同时删除文件系统中的文件（如果存在）
    """
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档不存在"
        )

    # 如果文件系统中有对应文件，先删除
    if document.file_path:
        file_storage_service.delete_document(document.file_path)
    if getattr(document, "pptx_path", None):
        file_storage_service.delete_document(document.pptx_path)

    db.delete(document)
    db.commit()

    return None
