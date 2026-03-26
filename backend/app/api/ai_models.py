"""
AI 模型管理 API
提供模型列表、推荐、配置等功能
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.model_router import (
    model_router, model_registry, GenerationTask, TaskModelConfig
)
from app.core.model_callers import get_model_recommendations
from app.services.ai_service import ai_service

router = APIRouter(prefix="/api/ai-models", tags=["AI Models"])


# ============ 请求/响应模型 ============

class ModelInfoResponse(BaseModel):
    """模型信息响应"""
    model_config = {"protected_namespaces": ()}
    
    id: str
    name: str
    provider: str
    model_id: str
    supports_temperature: bool
    default_temperature: float
    max_tokens: int
    input_price_per_1k: float
    output_price_per_1k: float
    speed_score: int
    quality_score: int
    is_default: bool
    is_enabled: bool
    is_premium: bool
    supported_tasks: List[str]


class ModelRecommendationResponse(BaseModel):
    """模型推荐响应"""
    id: str
    name: str
    provider: str
    input_price_per_1k: float
    output_price_per_1k: float
    speed_score: int
    quality_score: int
    is_premium: bool
    value_score: float
    reasons: List[str]


class TaskModelConfigRequest(BaseModel):
    """任务模型配置请求"""
    model_config = {"protected_namespaces": ()}
    
    task: str  # outline, section, simulation
    model_id: str
    temperature: float = 0.7
    custom_prompt_suffix: str = ""


class TaskModelConfigResponse(BaseModel):
    """任务模型配置响应"""
    model_config = {"protected_namespaces": ()}
    
    task: str
    model_id: str
    temperature: float
    custom_prompt_suffix: str


class GenerationRequest(BaseModel):
    """生成请求（带模型选择）"""
    model_config = {"protected_namespaces": ()}
    
    course: str
    knowledge_point: str
    config: dict
    model_id: Optional[str] = None  # 指定模型
    temperature: Optional[float] = None


# ============ API 端点 ============

@router.get("/list", response_model=List[ModelInfoResponse])
async def list_models(task_type: Optional[str] = None):
    """
    获取可用模型列表
    
    Args:
        task_type: 可选，按任务类型过滤 (outline/section/simulation)
    """
    models = ai_service.get_available_models(task_type)
    return models


@router.get("/recommendations/{task_type}", response_model=List[ModelRecommendationResponse])
async def get_recommendations(task_type: str):
    """
    获取任务推荐的模型列表（按性价比排序）
    
    Args:
        task_type: 任务类型 (outline/section/simulation)
    """
    try:
        recommendations = ai_service.get_model_recommendations(task_type)
        return recommendations
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/defaults")
async def get_default_models():
    """获取各任务的默认模型配置"""
    defaults = {}
    for task in GenerationTask:
        model = model_registry.get_default(task)
        if model:
            defaults[task.value] = model.to_dict()
    return defaults


@router.post("/task-config", response_model=TaskModelConfigResponse)
async def save_task_config(config: TaskModelConfigRequest):
    """
    保存任务级别的模型配置（需要登录，暂存于内存，后续可存数据库）
    
    注意：这是示例实现，实际应关联用户ID存储到数据库
    """
    try:
        task = GenerationTask(config.task)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"无效的任务类型: {config.task}")
    
    # 验证模型是否存在且支持该任务
    model = model_registry.get(config.model_id)
    if not model:
        raise HTTPException(status_code=404, detail=f"模型不存在: {config.model_id}")
    
    if not model.is_enabled:
        raise HTTPException(status_code=400, detail=f"模型已禁用: {config.model_id}")
    
    if task not in model.supported_tasks:
        raise HTTPException(
            status_code=400, 
            detail=f"模型 {config.model_id} 不支持任务 {config.task}"
        )
    
    # 验证 temperature
    if config.temperature is not None:
        if not model.supports_temperature:
            raise HTTPException(
                status_code=400,
                detail=f"模型 {config.model_id} 不支持 temperature 参数"
            )
        if not 0 <= config.temperature <= 2:
            raise HTTPException(status_code=400, detail="temperature 必须在 0-2 之间")
    
    # TODO: 存储到数据库，关联当前用户
    # 目前仅返回验证后的配置
    return TaskModelConfigResponse(
        task=config.task,
        model_id=config.model_id,
        temperature=config.temperature,
        custom_prompt_suffix=config.custom_prompt_suffix,
    )


@router.get("/compare")
async def compare_models(model_ids: str):
    """
    对比多个模型
    
    Args:
        model_ids: 逗号分隔的模型ID，如 "kimi-k2.5,deepseek-v3,gpt-4o"
    """
    ids = [m.strip() for m in model_ids.split(",")]
    comparison = []
    
    for model_id in ids:
        model = model_registry.get(model_id)
        if model:
            comparison.append({
                **model.to_dict(),
                "cost_per_10k_output": round(model.output_price_per_1k * 10, 4),
            })
    
    return comparison


@router.get("/pricing")
async def get_pricing_overview():
    """获取所有模型的价格概览"""
    models = model_registry.list_all()
    
    pricing = []
    for m in models:
        pricing.append({
            "id": m.id,
            "name": m.name,
            "provider": m.provider.value,
            "input_price": m.input_price_per_1k,
            "output_price": m.output_price_per_1k,
            "cost_10k_tokens": round((m.input_price_per_1k + m.output_price_per_1k * 2) * 10, 4),
        })
    
    # 按价格排序
    pricing.sort(key=lambda x: x["cost_10k_tokens"])
    return pricing
