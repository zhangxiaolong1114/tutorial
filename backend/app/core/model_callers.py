"""
AI 模型调用器实现
支持 Moonshot/Kimi、DeepSeek、Claude、Qwen、GLM 等
"""
import json
import logging
import os
import re
import requests
import time
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

from app.core.model_router import (
    ModelConfig, ModelProvider, GenerationTask, model_router, model_registry
)
from app.core.rate_limiter import token_rate_limiter

logger = logging.getLogger(__name__)


class AIResponseLogger:
    """AI 响应日志记录器 - 按日期和任务组织"""
    
    def __init__(self):
        self.base_log_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'app', 'logs')
        self.responses_dir = os.path.join(self.base_log_dir, 'ai_responses')
        self.prompts_dir = os.path.join(self.base_log_dir, 'prompts')
        
        # 创建基础目录
        os.makedirs(self.responses_dir, exist_ok=True)
        os.makedirs(self.prompts_dir, exist_ok=True)
    
    def _get_date_dir(self, base_dir: str) -> str:
        """获取按日期组织的目录"""
        date_str = datetime.now().strftime('%Y%m%d')
        date_dir = os.path.join(base_dir, date_str)
        os.makedirs(date_dir, exist_ok=True)
        return date_dir
    
    def _get_task_dir(self, base_dir: str, task_id: str) -> str:
        """获取按任务组织的目录"""
        date_dir = self._get_date_dir(base_dir)
        task_dir = os.path.join(date_dir, f"task_{task_id}")
        os.makedirs(task_dir, exist_ok=True)
        return task_dir
    
    def log_response(
        self, 
        task_id: str, 
        module: str, 
        model_id: str, 
        provider: str,
        result: dict, 
        content: str
    ) -> str:
        """
        记录 AI 响应到日志文件（按日期和任务组织）
        
        目录结构: ai_responses/YYYYMMDD/task_{task_id}/{provider}_{model}_{module}_{timestamp}.json
        
        Returns:
            日志文件路径
        """
        timestamp = datetime.now().strftime('%H%M%S')
        filename = f"{provider}_{model_id}_{module}_{timestamp}.json"
        
        # 按任务组织目录
        task_dir = self._get_task_dir(self.responses_dir, task_id)
        filepath = os.path.join(task_dir, filename)
        
        # 提取 finish_reason（不同 API 格式不同）
        finish_reason = self._extract_finish_reason(result, provider)
        
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "task_id": task_id,
            "module": module,
            "model_id": model_id,
            "provider": provider,
            "finish_reason": finish_reason,
            "usage": result.get("usage", {}),
            "content_length": len(content),
            "content_preview": content[:500] if content else "",
            "full_response": result
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, ensure_ascii=False, indent=2)
            logger.debug(f"[AI Logger] 响应已记录: {filepath}")
        except Exception as e:
            logger.warning(f"[AI Logger] 保存日志失败: {e}")
        
        return filepath
    
    def _extract_finish_reason(self, result: dict, provider: str) -> str:
        """提取 finish_reason（适配不同 API 格式）"""
        # OpenAI 兼容格式
        if "choices" in result:
            return result["choices"][0].get("finish_reason", "unknown")
        
        # Claude 格式
        if "stop_reason" in result:
            return result["stop_reason"]
        
        return "unknown"
    
    def log_prompt(self, task_id: str, module: str, model_id: str, messages: list):
        """
        记录完整 Prompt（按日期和任务组织）
        
        目录结构: prompts/YYYYMMDD/task_{task_id}/{module}_{model}_{timestamp}.txt
        """
        timestamp = datetime.now().strftime('%H%M%S')
        filename = f"{module}_{model_id}_{timestamp}.txt"
        
        # 按任务组织目录
        task_dir = self._get_task_dir(self.prompts_dir, task_id)
        filepath = os.path.join(task_dir, filename)
        
        # 构建 prompt 内容
        prompt_lines = [
            f"Task ID: {task_id}",
            f"Module: {module}",
            f"Model: {model_id}",
            f"Timestamp: {datetime.now().isoformat()}",
            f"{'='*80}"
        ]
        
        for i, msg in enumerate(messages):
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            prompt_lines.append(f"\n--- Message {i+1} [{role}] ---")
            prompt_lines.append(content)
        
        prompt_lines.append(f"\n{'='*80}\n")
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write('\n'.join(prompt_lines))
            logger.debug(f"[AI Logger] Prompt 已记录: {filepath}")
        except Exception as e:
            logger.warning(f"[AI Logger] 保存 prompt 失败: {e}")
    
    def cleanup_old_logs(self, days: int = 7):
        """清理旧日志"""
        cutoff = datetime.now() - timedelta(days=days)
        
        for base_dir in [self.responses_dir, self.prompts_dir]:
            for date_dir in os.listdir(base_dir):
                date_path = os.path.join(base_dir, date_dir)
                if not os.path.isdir(date_path):
                    continue
                
                try:
                    dir_date = datetime.strptime(date_dir, '%Y%m%d')
                    if dir_date < cutoff:
                        import shutil
                        shutil.rmtree(date_path)
                        logger.info(f"已清理旧日志: {date_path}")
                except ValueError:
                    continue


# 全局日志记录器
response_logger = AIResponseLogger()


class BaseModelCaller:
    """模型调用器基类"""
    
    def __init__(self, provider: ModelProvider):
        self.provider = provider
    
    def __call__(
        self,
        config: ModelConfig,
        messages: List[Dict[str, str]],
        temperature: Optional[float],
        task: GenerationTask,
        task_id: str = "unknown",
        max_retries: int = 3,
        max_continuation: int = 5,
        **kwargs
    ) -> Tuple[str, str]:
        """
        调用模型（支持自动续生成）
        
        Returns:
            (content, log_file_path)
        """
        raise NotImplementedError
    
    def _check_duplicate(
        self, 
        prev_content: str, 
        new_content: str, 
        threshold: float = 0.85
    ) -> bool:
        """检查内容是否重复"""
        if not prev_content or not new_content:
            return False
        
        # 简单的相似度计算
        norm1 = re.sub(r'\s+', '', prev_content.lower().strip())
        norm2 = re.sub(r'\s+', '', new_content.lower().strip())
        
        if not norm1 or not norm2:
            return False
        
        # Jaccard 相似度
        def get_ngrams(text, n=4):
            return set(text[i:i+n] for i in range(len(text) - n + 1))
        
        ngrams1 = get_ngrams(norm1)
        ngrams2 = get_ngrams(norm2)
        
        if not ngrams1 or not ngrams2:
            return False
        
        intersection = len(ngrams1 & ngrams2)
        union = len(ngrams1 | ngrams2)
        
        similarity = intersection / union if union > 0 else 0.0
        return similarity > threshold


class OpenAICompatibleCaller(BaseModelCaller):
    """
    OpenAI 兼容格式调用器
    适用于：Moonshot/Kimi、DeepSeek、Qwen、GLM 等
    """
    
    def __init__(self, provider: ModelProvider):
        super().__init__(provider)
        self.provider_base_urls = {
            ModelProvider.MOONSHOT: "https://api.moonshot.cn/v1",
            ModelProvider.DEEPSEEK: "https://api.deepseek.com/v1",
            ModelProvider.QWEN: "https://dashscope.aliyuncs.com/compatible-mode/v1",
            ModelProvider.GLM: "https://open.bigmodel.cn/api/paas/v4",
            ModelProvider.OPENAI: "https://api.openai.com/v1",
        }
    
    def __call__(
        self,
        config: ModelConfig,
        messages: List[Dict[str, str]],
        temperature: Optional[float],
        task: GenerationTask,
        task_id: str = "unknown",
        max_retries: int = 3,
        max_continuation: int = 5,
        **kwargs
    ) -> Tuple[str, str]:
        
        if not config.api_key:
            raise ValueError(f"{config.id} 未配置 API Key")
        
        # 确定 base_url
        base_url = config.base_url or self.provider_base_urls.get(self.provider, "")
        if not base_url:
            raise ValueError(f"{config.id} 未配置 Base URL")
        
        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }
        
        all_content = []
        current_messages = messages.copy()
        total_tokens = 0
        
        # 记录 Prompt
        response_logger.log_prompt(task_id, task.value, config.id, messages)
        
        # 估算 token 并等待速率限制
        prompt_text = "\n".join([m.get("content", "") for m in messages])
        prompt_length = len(prompt_text)
        
        # 根据任务类型预估输出长度
        estimated_output = {
            GenerationTask.OUTLINE: 8000,
            GenerationTask.SECTION: 8000,
            GenerationTask.SIMULATION: 12000,
        }.get(task, 8000)
        
        estimated_input = prompt_length // 4
        estimated_total = max(estimated_input + estimated_output, 4000)
        
        logger.info(f"[Token Limiter] Task {task_id}/{task.value} - 预估 {estimated_total} tokens")
        
        if not token_rate_limiter.acquire(estimated_total, timeout=120):
            raise Exception("Token rate limit: 等待超时")
        
        for attempt in range(max_continuation):
            data = {
                "model": config.model_id,
                "messages": current_messages,
                "max_tokens": min(config.max_tokens, 24000),
            }
            
            if temperature is not None and config.supports_temperature:
                data["temperature"] = temperature
            
            logger.info(f"[{self.provider.value}] Task {task_id}/{task.value} - 调用 #{attempt + 1}")
            
            try:
                response = requests.post(
                    f"{base_url}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=600
                )
                
                if response.status_code != 200:
                    error_msg = f"HTTP {response.status_code}: {response.text[:500]}"
                    logger.error(f"[{self.provider.value}] 错误: {error_msg}")
                    raise Exception(error_msg)
                
                result = response.json()
                choice = result["choices"][0]
                content = choice["message"]["content"]
                finish_reason = choice.get("finish_reason", "unknown")
                usage = result.get("usage", {})
                
                all_content.append(content)
                total_tokens += usage.get("total_tokens", 0)
                
                logger.info(f"[{self.provider.value}] Task {task_id}/{task.value} - "
                          f"finish_reason={finish_reason}, tokens={usage.get('total_tokens', 0)}")
                
                # 保存响应日志
                log_file = response_logger.log_response(
                    task_id, task.value, config.id, self.provider.value, result, content
                )
                
                # 检查是否完成
                if finish_reason != "length":
                    token_rate_limiter.record_actual_usage(total_tokens)
                    return "".join(all_content), log_file
                
                # 需要续生成
                logger.info(f"[{self.provider.value}] 内容不完整，继续生成...")
                
                # 检查重复
                if len(all_content) > 1 and self._check_duplicate(all_content[-2], content):
                    logger.warning(f"[{self.provider.value}] 检测到重复内容，停止续生成")
                    break
                
                # 添加续生成提示
                current_messages.append({"role": "assistant", "content": content})
                current_messages.append({
                    "role": "user",
                    "content": "请继续生成剩余内容，保持格式一致。从上次中断的地方继续，不要重复已生成的内容。"
                })
                
            except Exception as e:
                logger.error(f"[{self.provider.value}] Task {task_id}/{task.value} - 调用失败: {e}")
                raise
        
        # 达到最大续生成次数
        logger.warning(f"[{self.provider.value}] 达到最大续生成次数，返回已生成内容")
        return "".join(all_content), log_file if 'log_file' in locals() else ""


class ClaudeCaller(BaseModelCaller):
    """Claude API 调用器（非 OpenAI 兼容格式）"""
    
    def __init__(self):
        super().__init__(ModelProvider.ANTHROPIC)
    
    def __call__(
        self,
        config: ModelConfig,
        messages: List[Dict[str, str]],
        temperature: Optional[float],
        task: GenerationTask,
        task_id: str = "unknown",
        max_retries: int = 3,
        max_continuation: int = 5,
        **kwargs
    ) -> Tuple[str, str]:
        
        if not config.api_key:
            raise ValueError(f"{config.id} 未配置 API Key")
        
        # Claude 使用 messages 格式，但 API 端点不同
        base_url = config.base_url or "https://api.anthropic.com/v1"
        
        headers = {
            "x-api-key": config.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        all_content = []
        current_messages = messages.copy()
        
        # 分离 system 和 user 消息
        system_msg = ""
        user_messages = []
        for msg in current_messages:
            if msg.get("role") == "system":
                system_msg = msg.get("content", "")
            else:
                user_messages.append(msg)
        
        # 记录 Prompt
        response_logger.log_prompt(task_id, task.value, config.id, messages)
        
        for attempt in range(max_continuation):
            data = {
                "model": config.model_id,
                "max_tokens": min(config.max_tokens, 8192),
                "messages": user_messages,
            }
            
            if system_msg:
                data["system"] = system_msg
            
            if temperature is not None:
                data["temperature"] = temperature
            
            logger.info(f"[claude] Task {task_id}/{task.value} - 调用 #{attempt + 1}")
            
            try:
                response = requests.post(
                    f"{base_url}/messages",
                    headers=headers,
                    json=data,
                    timeout=360
                )
                
                if response.status_code != 200:
                    error_msg = f"HTTP {response.status_code}: {response.text[:500]}"
                    logger.error(f"[claude] 错误: {error_msg}")
                    raise Exception(error_msg)
                
                result = response.json()
                content = result["content"][0]["text"]
                stop_reason = result.get("stop_reason", "unknown")
                usage = result.get("usage", {})
                
                all_content.append(content)
                
                logger.info(f"[claude] Task {task_id}/{task.value} - "
                          f"stop_reason={stop_reason}, tokens={usage.get('output_tokens', 0)}")
                
                # 保存响应日志
                log_file = response_logger.log_response(
                    task_id, task.value, config.id, "anthropic", result, content
                )
                
                # 检查是否完成
                if stop_reason != "max_tokens":
                    return "".join(all_content), log_file
                
                # 需要续生成
                logger.info(f"[claude] 内容不完整，继续生成...")
                
                # 检查重复
                if len(all_content) > 1 and self._check_duplicate(all_content[-2], content):
                    logger.warning(f"[claude] 检测到重复内容，停止续生成")
                    break
                
                # 添加续生成提示
                user_messages.append({"role": "assistant", "content": content})
                user_messages.append({
                    "role": "user",
                    "content": "请继续生成剩余内容，保持代码格式一致。从上次中断的地方继续，不要重复已生成的代码。"
                })
                
            except Exception as e:
                logger.error(f"[claude] Task {task_id}/{task.value} - 调用失败: {e}")
                raise
        
        return "".join(all_content), log_file if 'log_file' in locals() else ""


# ============ 注册调用器 ============

# OpenAI 兼容格式调用器
openai_caller = OpenAICompatibleCaller(ModelProvider.MOONSHOT)
model_router.register_caller(ModelProvider.MOONSHOT, openai_caller)

deepseek_caller = OpenAICompatibleCaller(ModelProvider.DEEPSEEK)
model_router.register_caller(ModelProvider.DEEPSEEK, deepseek_caller)

qwen_caller = OpenAICompatibleCaller(ModelProvider.QWEN)
model_router.register_caller(ModelProvider.QWEN, qwen_caller)

glm_caller = OpenAICompatibleCaller(ModelProvider.GLM)
model_router.register_caller(ModelProvider.GLM, glm_caller)




# ============ 便捷函数 ============

def init_model_api_keys(settings_dict: dict):
    """
    从配置初始化模型 API Keys
    
    Args:
        settings_dict: 包含 API Keys 的字典，如：
            {
                "kimi": "sk-xxx",
                "deepseek": "sk-xxx",
                "claude": "sk-xxx",
                ...
            }
    """
    # Kimi
    if settings_dict.get("kimi"):
        model_registry.update_api_key("kimi-k2.5", settings_dict["kimi"])
        model_registry.update_api_key("kimi-k1.5", settings_dict["kimi"])
    
    # DeepSeek
    if settings_dict.get("deepseek"):
        model_registry.update_api_key("deepseek-v3", settings_dict["deepseek"])
        model_registry.update_api_key("deepseek-r1", settings_dict["deepseek"])
    
    # Qwen
    if settings_dict.get("qwen"):
        model_registry.update_api_key("qwen-coder", settings_dict["qwen"])
        model_registry.update_api_key("qwen-plus", settings_dict["qwen"])
    
    # GLM
    if settings_dict.get("glm"):
        model_registry.update_api_key("glm-4", settings_dict["glm"])
    
    # OpenAI
    if settings_dict.get("openai"):
        model_registry.update_api_key("gpt-4o", settings_dict["openai"])
    
    logger.info("[Model Init] API Keys 已加载")


def get_model_recommendations(task: GenerationTask) -> List[dict]:
    """
    获取任务推荐的模型列表（按性价比排序）
    
    Returns:
        推荐模型列表，包含推荐理由
    """
    models = model_registry.list_by_task(task)
    
    # 计算性价比分数
    recommendations = []
    for m in models:
        # 性价比 = (质量 * 速度) / (输入价格 + 输出价格 * 2)
        price = m.input_price_per_1k + m.output_price_per_1k * 2
        value_score = (m.quality_score * m.speed_score) / (price + 0.001)
        
        reasons = []
        if m.is_default:
            reasons.append("默认推荐")
        if m.speed_score >= 4:
            reasons.append("生成速度快")
        if m.quality_score >= 4:
            reasons.append("生成质量高")
        if price < 0.01:
            reasons.append("性价比高")
        if m.is_premium:
            reasons.append("会员专属")
        
        recommendations.append({
            **m.to_dict(),
            "value_score": round(value_score, 2),
            "reasons": reasons,
        })
    
    # 按性价比排序
    recommendations.sort(key=lambda x: x["value_score"], reverse=True)
    return recommendations
