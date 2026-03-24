"""
生成配置 API 路由
提供配置管理和应用接口
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.generation_config import GenerationConfig
from app.schemas.generation_config import (
    GenerationConfigCreate,
    GenerationConfigResponse,
    GenerationConfigHistory,
)

router = APIRouter(prefix="/generation-configs", tags=["generation-configs"])
logger = logging.getLogger(__name__)


@router.post("", response_model=GenerationConfigResponse)
def create_config(
    config_data: GenerationConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建新的生成配置
    
    保存用户的生成偏好设置，用于后续内容生成
    """
    try:
        logger.info(f"创建配置请求: user_id={current_user.id}, data={config_data.dict()}")
        
        # 创建配置对象
        config = GenerationConfig(
            user_id=current_user.id,
            tone=config_data.tone,
            teaching_style=config_data.teaching_style,
            content_style=config_data.content_style,
            difficulty=config_data.difficulty,
            formula_detail=config_data.formula_detail,
            target_audience=config_data.target_audience,
            output_format=config_data.output_format,
            code_language=config_data.code_language,
            chapter_granularity=config_data.chapter_granularity,
            citation_style=config_data.citation_style,
            interactive_elements=config_data.interactive_elements,
            need_simulation=config_data.need_simulation,
            need_images=config_data.need_images,
        )
        
        # 设置仿真类型列表
        config.set_simulation_types_list(config_data.simulation_types)
        
        logger.info(f"配置对象创建成功: user_id={current_user.id}, simulation_types={config.simulation_types}")
        
        db.add(config)
        db.commit()
        db.refresh(config)
        
        logger.info(f"配置保存成功: config_id={config.id}, user_id={current_user.id}")
        
        return config
    except Exception as e:
        logger.error(f"创建配置失败: user_id={current_user.id}, error={str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"保存配置失败: {str(e)}"
        )


@router.get("", response_model=GenerationConfigHistory)
def get_config_history(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取用户的配置历史列表
    
    按时间倒序返回用户的生成配置记录
    """
    configs = db.query(GenerationConfig).filter(
        GenerationConfig.user_id == current_user.id
    ).order_by(desc(GenerationConfig.created_at)).limit(limit).all()
    
    total = db.query(GenerationConfig).filter(
        GenerationConfig.user_id == current_user.id
    ).count()
    
    return {
        "configs": configs,
        "total": total
    }


@router.get("/latest", response_model=Optional[GenerationConfigResponse])
def get_latest_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取用户最新的生成配置
    
    用于自动填充表单，恢复上次的配置
    """
    config = db.query(GenerationConfig).filter(
        GenerationConfig.user_id == current_user.id
    ).order_by(desc(GenerationConfig.created_at)).first()
    
    return config


@router.get("/{config_id}", response_model=GenerationConfigResponse)
def get_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取指定配置的详细信息
    """
    config = db.query(GenerationConfig).filter(
        GenerationConfig.id == config_id,
        GenerationConfig.user_id == current_user.id
    ).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置不存在"
        )
    
    return config


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除指定的生成配置
    """
    config = db.query(GenerationConfig).filter(
        GenerationConfig.id == config_id,
        GenerationConfig.user_id == current_user.id
    ).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置不存在"
        )
    
    db.delete(config)
    db.commit()
    
    return None
