"""
AI 生成成本统计服务
"""
import logging
from typing import Optional, Dict, List
from sqlalchemy.orm import Session

from app.models.generation_cost import GenerationCost, DocumentCostSummary
from app.core.model_router import model_registry

logger = logging.getLogger(__name__)


class CostService:
    """成本统计服务"""
    
    @staticmethod
    def record_generation_cost(
        db: Session,
        user_id: int,
        model_id: str,
        task_type: str,
        input_tokens: int,
        output_tokens: int,
        task_id: Optional[int] = None,
        outline_id: Optional[int] = None,
        document_id: Optional[int] = None,
        course: Optional[str] = None,
        knowledge_point: Optional[str] = None,
    ) -> GenerationCost:
        """
        记录一次 AI 生成的成本
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            model_id: 模型ID
            task_type: 任务类型 (outline/section/simulation)
            input_tokens: 输入 tokens
            output_tokens: 输出 tokens
            task_id: 关联的任务ID
            outline_id: 关联的大纲ID
            document_id: 关联的文档ID
            course: 课程名称
            knowledge_point: 知识点
        
        Returns:
            创建的成本记录
        """
        # 获取模型配置
        model_config = model_registry.get(model_id)
        if not model_config:
            logger.warning(f"未找到模型配置: {model_id}，使用默认价格 0")
            input_price = 0
            output_price = 0
            model_name = model_id
            provider = "unknown"
        else:
            input_price = model_config.input_price_per_1k
            output_price = model_config.output_price_per_1k
            model_name = model_config.name
            provider = model_config.provider.value
        
        # 计算成本
        input_cost = (input_tokens / 1000) * input_price
        output_cost = (output_tokens / 1000) * output_price
        total_cost = input_cost + output_cost
        
        # 创建成本记录
        cost_record = GenerationCost(
            user_id=user_id,
            task_id=task_id,
            outline_id=outline_id,
            document_id=document_id,
            course=course,
            knowledge_point=knowledge_point,
            model_id=model_id,
            model_name=model_name,
            provider=provider,
            task_type=task_type,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=total_cost,
        )
        
        db.add(cost_record)
        db.commit()
        db.refresh(cost_record)
        
        logger.info(f"[Cost] 记录成本: {model_id} {task_type} "
                   f"tokens={input_tokens}+{output_tokens} "
                   f"cost=¥{total_cost:.6f}")
        
        return cost_record
    
    @staticmethod
    def update_document_cost_summary(
        db: Session,
        document_id: int,
        user_id: int,
        outline_id: Optional[int] = None,
        course: Optional[str] = None,
        knowledge_point: Optional[str] = None,
        section_count: int = 0,
    ) -> DocumentCostSummary:
        """
        更新文档成本汇总
        
        Args:
            db: 数据库会话
            document_id: 文档ID
            user_id: 用户ID
            outline_id: 大纲ID
            course: 课程名称
            knowledge_point: 知识点
            section_count: 章节数
        
        Returns:
            更新的汇总记录
        """
        # 查找或创建汇总记录
        summary = db.query(DocumentCostSummary).filter(
            DocumentCostSummary.document_id == document_id
        ).first()
        
        if not summary:
            summary = DocumentCostSummary(
                user_id=user_id,
                document_id=document_id,
                outline_id=outline_id,
                course=course,
                knowledge_point=knowledge_point,
                section_count=section_count,
            )
            db.add(summary)
        
        # 重新计算汇总数据
        costs = db.query(GenerationCost).filter(
            GenerationCost.document_id == document_id
        ).all()
        
        total_calls = len(costs)
        total_input_tokens = sum(c.input_tokens for c in costs)
        total_output_tokens = sum(c.output_tokens for c in costs)
        total_tokens = total_input_tokens + total_output_tokens
        total_cost = sum(c.total_cost for c in costs)
        
        # 按模型统计成本
        cost_breakdown: Dict[str, float] = {}
        for cost in costs:
            if cost.model_id not in cost_breakdown:
                cost_breakdown[cost.model_id] = 0
            cost_breakdown[cost.model_id] += cost.total_cost
        
        # 更新汇总
        summary.total_calls = total_calls
        summary.total_input_tokens = total_input_tokens
        summary.total_output_tokens = total_output_tokens
        summary.total_tokens = total_tokens
        summary.total_cost = total_cost
        summary.set_cost_breakdown(cost_breakdown)
        
        if section_count > 0:
            summary.section_count = section_count
        
        db.commit()
        db.refresh(summary)
        
        logger.info(f"[Cost] 更新文档 {document_id} 成本汇总: "
                   f"calls={total_calls}, tokens={total_tokens}, cost=¥{total_cost:.4f}")
        
        return summary
    
    @staticmethod
    def get_document_cost_summary(
        db: Session,
        document_id: int,
        user_id: int
    ) -> Optional[DocumentCostSummary]:
        """获取文档成本汇总"""
        return db.query(DocumentCostSummary).filter(
            DocumentCostSummary.document_id == document_id,
            DocumentCostSummary.user_id == user_id
        ).first()
    
    @staticmethod
    def get_user_cost_stats(
        db: Session,
        user_id: int,
        days: int = 30
    ) -> Dict:
        """
        获取用户成本统计
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            days: 统计天数
        
        Returns:
            统计数据字典
        """
        from datetime import datetime, timedelta
        from app.core.database import get_now
        
        start_date = get_now() - timedelta(days=days)
        
        # 查询指定时间范围内的成本记录
        costs = db.query(GenerationCost).filter(
            GenerationCost.user_id == user_id,
            GenerationCost.created_at >= start_date
        ).all()
        
        if not costs:
            return {
                "total_calls": 0,
                "total_tokens": 0,
                "total_cost": 0,
                "by_model": {},
                "by_task_type": {},
            }
        
        # 统计
        total_calls = len(costs)
        total_tokens = sum(c.total_tokens for c in costs)
        total_cost = sum(c.total_cost for c in costs)
        
        by_model: Dict[str, Dict] = {}
        by_task_type: Dict[str, Dict] = {}
        
        for cost in costs:
            # 按模型统计
            if cost.model_id not in by_model:
                by_model[cost.model_id] = {
                    "name": cost.model_name,
                    "calls": 0,
                    "tokens": 0,
                    "cost": 0,
                }
            by_model[cost.model_id]["calls"] += 1
            by_model[cost.model_id]["tokens"] += cost.total_tokens
            by_model[cost.model_id]["cost"] += cost.total_cost
            
            # 按任务类型统计
            if cost.task_type not in by_task_type:
                by_task_type[cost.task_type] = {
                    "calls": 0,
                    "tokens": 0,
                    "cost": 0,
                }
            by_task_type[cost.task_type]["calls"] += 1
            by_task_type[cost.task_type]["tokens"] += cost.total_tokens
            by_task_type[cost.task_type]["cost"] += cost.total_cost
        
        # 四舍五入
        for model_data in by_model.values():
            model_data["cost"] = round(model_data["cost"], 4)
        for task_data in by_task_type.values():
            task_data["cost"] = round(task_data["cost"], 4)
        
        return {
            "period_days": days,
            "total_calls": total_calls,
            "total_tokens": total_tokens,
            "total_cost": round(total_cost, 4),
            "by_model": by_model,
            "by_task_type": by_task_type,
        }


# 全局成本服务实例
cost_service = CostService()
