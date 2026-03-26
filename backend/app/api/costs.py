"""
成本统计 API
提供成本查询和统计功能
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.generation_cost import GenerationCost, DocumentCostSummary
from app.core.cost_tracker import cost_tracker

router = APIRouter(prefix="/api/costs", tags=["成本统计"])


# ============ 响应模型 ============

class GenerationCostResponse(BaseModel):
    """生成成本响应"""
    model_config = {"protected_namespaces": ()}
    
    id: int
    model_id: str
    model_name: str
    provider: str
    task_type: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    input_cost: float
    output_cost: float
    total_cost: float
    created_at: str


class DocumentCostSummaryResponse(BaseModel):
    """文档成本汇总响应"""
    id: int
    document_id: int
    course: Optional[str]
    knowledge_point: Optional[str]
    section_count: int
    total_calls: int
    total_input_tokens: int
    total_output_tokens: int
    total_tokens: int
    total_cost: float
    cost_breakdown: dict
    created_at: str


class UserCostStatsResponse(BaseModel):
    """用户成本统计响应"""
    period_days: int
    total_calls: int
    total_tokens: int
    total_cost: float
    by_model: dict
    by_task_type: dict


# ============ API 端点 ============

@router.get("/document/{document_id}", response_model=DocumentCostSummaryResponse)
async def get_document_cost(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取文档生成成本汇总
    
    Args:
        document_id: 文档ID
    """
    summary = db.query(DocumentCostSummary).filter(
        DocumentCostSummary.document_id == document_id,
        DocumentCostSummary.user_id == current_user.id
    ).first()
    
    if not summary:
        raise HTTPException(status_code=404, detail="文档成本记录不存在")
    
    return summary.to_dict()


@router.get("/document/{document_id}/details", response_model=list)
async def get_document_cost_details(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取文档生成的详细成本记录
    
    Args:
        document_id: 文档ID
    """
    # 验证文档所有权
    summary = db.query(DocumentCostSummary).filter(
        DocumentCostSummary.document_id == document_id,
        DocumentCostSummary.user_id == current_user.id
    ).first()
    
    if not summary:
        raise HTTPException(status_code=404, detail="文档成本记录不存在")
    
    costs = db.query(GenerationCost).filter(
        GenerationCost.document_id == document_id,
        GenerationCost.user_id == current_user.id
    ).order_by(GenerationCost.created_at.asc()).all()
    
    return [cost.to_dict() for cost in costs]


@router.get("/stats", response_model=UserCostStatsResponse)
async def get_user_cost_stats(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取用户成本统计
    
    Args:
        days: 统计天数，默认30天
    """
    stats = cost_tracker.get_user_cost_stats(db, current_user.id, days)
    return stats


@router.get("/history", response_model=list)
async def get_cost_history(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取成本历史记录
    
    Args:
        limit: 返回记录数量，默认50条
    """
    costs = db.query(GenerationCost).filter(
        GenerationCost.user_id == current_user.id
    ).order_by(GenerationCost.created_at.desc()).limit(limit).all()
    
    return [cost.to_dict() for cost in costs]


@router.get("/documents", response_model=list)
async def get_document_costs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取所有文档的成本汇总列表
    """
    summaries = db.query(DocumentCostSummary).filter(
        DocumentCostSummary.user_id == current_user.id
    ).order_by(DocumentCostSummary.created_at.desc()).all()
    
    return [summary.to_dict() for summary in summaries]
