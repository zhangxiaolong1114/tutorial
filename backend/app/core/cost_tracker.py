"""
AI 生成成本追踪器
从 AI 响应日志中提取 token 使用情况并记录成本
"""
import json
import logging
import os
from typing import Optional, Dict, List
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.generation_cost import GenerationCost, DocumentCostSummary
from app.core.model_router import model_registry

logger = logging.getLogger(__name__)


class GenerationCostTracker:
    """生成成本追踪器"""
    
    def __init__(self):
        self.log_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'app', 'logs', 'ai_responses')
    
    def find_log_files(self, task_id: str, module: str = None) -> List[str]:
        """
        查找任务相关的日志文件
        
        Args:
            task_id: 任务ID
            module: 模块名称（可选，用于过滤）
        
        Returns:
            日志文件路径列表
        """
        if not os.path.exists(self.log_dir):
            return []
        
        files = []
        prefix = f"*_task{task_id}_" if task_id else ""
        
        for filename in os.listdir(self.log_dir):
            if task_id in filename:
                if module and module not in filename:
                    continue
                files.append(os.path.join(self.log_dir, filename))
        
        # 按修改时间排序
        files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        return files
    
    def parse_log_file(self, log_file: str) -> Optional[Dict]:
        """
        解析日志文件获取 token 使用情况
        
        Returns:
            {
                "model_id": str,
                "provider": str,
                "module": str,
                "input_tokens": int,
                "output_tokens": int,
                "total_tokens": int,
            }
        """
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            usage = data.get("usage", {})
            
            # 不同 API 的 usage 格式可能不同
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", input_tokens + output_tokens)
            
            return {
                "model_id": data.get("model_id", "unknown"),
                "provider": data.get("provider", "unknown"),
                "module": data.get("module", "unknown"),
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
            }
        except Exception as e:
            logger.warning(f"解析日志文件失败 {log_file}: {e}")
            return None
    
    def record_cost_from_logs(
        self,
        db: Session,
        task_id: str,
        user_id: int,
        outline_id: Optional[int] = None,
        document_id: Optional[int] = None,
        course: Optional[str] = None,
        knowledge_point: Optional[str] = None,
    ) -> List[GenerationCost]:
        """
        从日志文件中记录成本
        
        Args:
            db: 数据库会话
            task_id: 任务ID
            user_id: 用户ID
            outline_id: 大纲ID
            document_id: 文档ID
            course: 课程名称
            knowledge_point: 知识点
        
        Returns:
            创建的成本记录列表
        """
        log_files = self.find_log_files(task_id)
        costs = []
        
        for log_file in log_files:
            log_data = self.parse_log_file(log_file)
            if not log_data:
                continue
            
            model_id = log_data["model_id"]
            model_config = model_registry.get(model_id)
            
            if not model_config:
                logger.warning(f"未找到模型配置: {model_id}")
                continue
            
            # 计算成本
            input_cost = (log_data["input_tokens"] / 1000) * model_config.input_price_per_1k
            output_cost = (log_data["output_tokens"] / 1000) * model_config.output_price_per_1k
            total_cost = input_cost + output_cost
            
            # 创建成本记录
            cost_record = GenerationCost(
                user_id=user_id,
                task_id=int(task_id) if task_id.isdigit() else None,
                outline_id=outline_id,
                document_id=document_id,
                course=course,
                knowledge_point=knowledge_point,
                model_id=model_id,
                model_name=model_config.name,
                provider=model_config.provider.value,
                task_type=log_data["module"],  # outline/section/simulation
                input_tokens=log_data["input_tokens"],
                output_tokens=log_data["output_tokens"],
                total_tokens=log_data["total_tokens"],
                input_cost=input_cost,
                output_cost=output_cost,
                total_cost=total_cost,
            )
            
            db.add(cost_record)
            costs.append(cost_record)
            
            logger.info(f"[CostTracker] 记录成本: {model_id} {log_data['module']} "
                       f"tokens={log_data['input_tokens']}+{log_data['output_tokens']} "
                       f"cost=¥{total_cost:.6f}")
        
        if costs:
            db.commit()
            for cost in costs:
                db.refresh(cost)
        
        return costs
    
    def update_document_summary(
        self,
        db: Session,
        document_id: int,
        user_id: int,
        outline_id: Optional[int] = None,
        course: Optional[str] = None,
        knowledge_point: Optional[str] = None,
        section_count: int = 0,
    ) -> Optional[DocumentCostSummary]:
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
        
        if not costs:
            logger.warning(f"文档 {document_id} 没有成本记录")
            return None
        
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
        
        logger.info(f"[CostTracker] 更新文档 {document_id} 成本汇总: "
                   f"calls={total_calls}, tokens={total_tokens}, cost=¥{total_cost:.4f}")
        
        return summary


# 全局成本追踪器实例
cost_tracker = GenerationCostTracker()
