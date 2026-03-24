"""
AI 服务封装
支持 Kimi API 调用，带完整日志记录和自动续生成功能
"""
import json
import logging
import os
import re
import requests
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

from app.core.config import get_settings
from app.core.prompt_templates import (
    build_outline_prompt,
    build_section_prompt,
    build_simulation_prompt,
)

logger = logging.getLogger(__name__)
settings = get_settings()


class AIResponseLogger:
    """AI 响应日志记录器"""
    
    def __init__(self):
        self.log_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'app', 'logs', 'ai_responses')
        os.makedirs(self.log_dir, exist_ok=True)
    
    def log_response(self, task_id: str, module: str, model: str, result: dict, content: str):
        """
        记录 AI 响应到日志文件
        
        Args:
            task_id: 任务ID
            module: 模块名称 (outline/section/simulation)
            model: 模型名称 (kimi/claude)
            result: API 原始响应
            content: 提取的内容
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{model}_{module}_task{task_id}_{timestamp}.json"
        filepath = os.path.join(self.log_dir, filename)
        
        log_data = {
            "timestamp": timestamp,
            "task_id": task_id,
            "module": module,
            "model": model,
            "stop_reason": result.get("stop_reason") or result.get("choices", [{}])[0].get("finish_reason"),
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


class ContentValidator:
    """内容完整性验证器"""
    
    @staticmethod
    def _normalize_text(text: str) -> str:
        """标准化文本用于比较（移除空白、转为小写）"""
        return re.sub(r'\s+', '', text.lower().strip())
    
    @staticmethod
    def calculate_similarity(text1: str, text2: str) -> float:
        """
        计算两段文本的相似度（0-1）
        使用简单的高效算法：基于字符 n-gram 的 Jaccard 相似度
        """
        if not text1 or not text2:
            return 0.0
        
        # 标准化
        norm1 = ContentValidator._normalize_text(text1)
        norm2 = ContentValidator._normalize_text(text2)
        
        if not norm1 or not norm2:
            return 0.0
        
        # 如果长度差异过大，直接返回低相似度
        len_ratio = min(len(norm1), len(norm2)) / max(len(norm1), len(norm2))
        if len_ratio < 0.5:
            return len_ratio
        
        # 使用 4-gram 计算 Jaccard 相似度
        def get_ngrams(text, n=4):
            return set(text[i:i+n] for i in range(len(text) - n + 1))
        
        ngrams1 = get_ngrams(norm1)
        ngrams2 = get_ngrams(norm2)
        
        if not ngrams1 or not ngrams2:
            return 0.0
        
        intersection = len(ngrams1 & ngrams2)
        union = len(ngrams1 | ngrams2)
        
        return intersection / union if union > 0 else 0.0
    
    @staticmethod
    def check_json_complete(content: str) -> Tuple[bool, str]:
        """检查 JSON 内容是否完整"""
        content = content.strip()
        
        # 移除 markdown 代码块标记
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        try:
            json.loads(content)
            return True, "JSON 完整"
        except json.JSONDecodeError as e:
            return False, f"JSON 不完整: {str(e)}"
    
    @staticmethod
    def check_html_complete(content: str) -> Tuple[bool, str]:
        """检查 HTML 内容是否完整"""
        content = content.strip()
        
        # 检查关键标签是否闭合
        tags_to_check = [
            ('<div class="section-content">', '</div>'),
            ('<script>', '</script>'),
        ]
        
        for open_tag, close_tag in tags_to_check:
            open_count = content.count(open_tag)
            close_count = content.count(close_tag)
            if open_count != close_count:
                return False, f"标签不匹配: {open_tag} 出现 {open_count} 次, {close_tag} 出现 {close_count} 次"
        
        # 检查是否有未闭合的 IIFE
        if "(function()" in content and not content.rstrip().endswith("})();"):
            if "<script>" in content:
                return False, "JavaScript IIFE 未正确闭合"
        
        return True, "HTML 结构完整"
    
    @staticmethod
    def check_outline_complete(content: str) -> Tuple[bool, str]:
        """检查大纲 JSON 是否完整"""
        return ContentValidator.check_json_complete(content)
    
    @staticmethod
    def check_section_complete(content: str) -> Tuple[bool, str]:
        """检查章节 HTML 是否完整"""
        # 章节内容只需要检查基本结构完整性
        # 不要求严格的标签数量匹配，因为内容中可能有很多嵌套 div
        
        # 检查是否有 section-content 容器
        if '<div class="section-content">' not in content:
            # 如果没有 section-content，检查是否有其他有效的内容结构
            has_heading = '<h3>' in content or '<h4>' in content
            has_paragraph = '<p>' in content
            has_formula = '$' in content
            
            if not (has_heading or has_paragraph or has_formula):
                return False, "内容缺少基本结构（标题、段落或公式）"
        
        # 检查 script 标签是否匹配（如果存在）
        script_open = content.count('<script>')
        script_close = content.count('</script>')
        if script_open != script_close:
            return False, f"script 标签不匹配"
        
        # 检查是否有未闭合的公式（行内公式 $...$ 应该成对出现）
        # 注意：这只是一个简单的检查，可能不完全准确
        dollar_count = content.count('$')
        if dollar_count % 2 != 0:
            return False, "公式分隔符 $ 数量不匹配"
        
        return True, "章节内容结构完整"
    
    @staticmethod
    def check_simulation_complete(content: str) -> Tuple[bool, str]:
        """检查仿真代码是否完整"""
        import re
        
        # 检查 simulation-container 标签是否闭合
        open_count = len(re.findall(r'<div[^>]*class=["\'][^"\']*simulation-container[^"\']*["\'][^>]*>', content, re.IGNORECASE))
        close_count = content.lower().count('</div>')
        
        # 对于仿真代码，我们只检查是否有 simulation-container 和对应的闭合
        # 不严格要求数量匹配，因为内部可能有很多嵌套 div
        if open_count == 0:
            return False, "缺少 simulation-container 容器"
        
        # 检查 script 标签是否闭合
        script_open = content.lower().count('<script>')
        script_close = content.lower().count('</script>')
        if script_open != script_close:
            return False, f"script 标签不匹配: 开启 {script_open} 次, 闭合 {script_close} 次"
        
        # 检查 IIFE 是否正确闭合
        if "(function()" in content or "(function ()" in content:
            if not re.search(r'\}\)\(\);\s*</script>', content, re.DOTALL):
                return False, "JavaScript IIFE 未正确闭合或 script 标签未闭合"
        
        # 额外检查仿真特有的结构
        has_canvas = "<canvas" in content.lower()
        has_2d_context = "getContext('2d')" in content or 'getContext("2d")' in content
        if has_canvas and not has_2d_context:
            return False, "Canvas 初始化代码不完整"
        
        # 检查关键帧数据完整性（动画类型仿真）
        if "keyFrames" in content or "keyframes" in content.lower():
            # 检查关键帧数据是否完整（不能只定义第0帧）
            import re
            keyframe_pattern = r'keyFrames\s*=\s*\{([^}]+)\}'
            match = re.search(keyframe_pattern, content, re.DOTALL)
            if match:
                keyframe_content = match.group(1)
                # 计算定义了多少个关键帧
                frame_count = len(re.findall(r'\d+\s*:', keyframe_content))
                if frame_count < 5:
                    return False, f"关键帧数据不完整：只定义了 {frame_count} 帧，至少需要 5 帧"
        
        # 检查是否有省略性注释
        forbidden_patterns = [
            r'此处省略.*代码',
            r'根据实际.*实现',
            r'添加更多.*数据',
            r'根据.*模型实现',
            r'//\s*\.\.\.',
            r'/\*\s*\.\.\.\s*\*/',
            r'//\s*TODO',
            r'//\s*FIXME',
        ]
        for pattern in forbidden_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return False, f"发现省略性注释或未完成标记: {pattern}"
        
        # 检查绘制函数是否完整实现
        draw_functions = re.findall(r'function\s+(draw\w*|render\w*|animate)\s*\([^)]*\)\s*\{([^}]*)\}', content, re.DOTALL)
        
        # 统计所有绘制函数中的 ctx. 调用总数
        total_ctx_calls = 0
        for func_name, func_body in draw_functions:
            clean_body = re.sub(r'/\*.*?\*/', '', func_body, flags=re.DOTALL)
            clean_body = re.sub(r'//.*?\n', '\n', clean_body)
            clean_body = clean_body.strip()
            total_ctx_calls += clean_body.count('ctx.')
            # 单个函数至少要有一些代码
            if len(clean_body) < 10:
                return False, f"绘制函数 '{func_name}' 实现不完整"
        
        # 所有绘制函数加起来至少要有一些 Canvas 调用
        if total_ctx_calls < 3:
            return False, "绘制函数缺少 Canvas 绘制代码"
        
        return True, "仿真代码完整"


class AIService:
    """AI 服务统一封装"""
    
    def __init__(self):
        self.kimi_api_key = settings.KIMI_API_KEY
        self.kimi_base_url = "https://api.moonshot.cn/v1"
        
        # Claude 配置（从配置文件读取）
        self.claude_api_key = settings.CLAUDE_API_KEY
        self.claude_base_url = getattr(settings, 'CLAUDE_BASE_URL', 'https://xiaoai.plus/v1')
        self.claude_model = getattr(settings, 'CLAUDE_MODEL', 'claude-opus-4-5-20251101')
        
        self.response_logger = AIResponseLogger()
        self.validator = ContentValidator()
    
    def _save_kimi_response(self, task_id: str, module: str, result: dict, content: str):
        """保存 Kimi 响应到日志"""
        return self.response_logger.log_response(task_id, module, "kimi", result, content)
    
    def _save_claude_response(self, task_id: str, module: str, result: dict, content: str):
        """保存 Claude 响应到日志"""
        return self.response_logger.log_response(task_id, module, "claude", result, content)
    
    def _log_full_prompt(self, task_id: str, module: str, model: str, messages: list):
        """
        记录完整 Prompt 到 ai_server.log
        
        Args:
            task_id: 任务ID
            module: 模块名称
            model: 模型名称
            messages: 完整的对话消息列表
        """
        import os
        
        log_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'app', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, 'ai_server.log')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 构建完整的 prompt 文本
        prompt_lines = [f"\n{'='*80}", f"[{timestamp}] Task {task_id}/{module} - {model.upper()} FULL PROMPT", f"{'='*80}"]
        
        for i, msg in enumerate(messages):
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            prompt_lines.append(f"\n--- Message {i+1} [{role}] ---")
            prompt_lines.append(content)
        
        prompt_lines.append(f"\n{'='*80}\n")
        
        # 追加写入日志文件
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write('\n'.join(prompt_lines))
        except Exception as e:
            logger.warning(f"[AI Logger] 保存完整 prompt 失败: {e}")
    
    def _is_duplicate_content(self, prev_content: str, new_content: str, threshold: float = 0.85) -> bool:
        """
        检测新内容是否与之前的内容重复
        
        Args:
            prev_content: 之前生成的内容
            new_content: 新返回的内容
            threshold: 相似度阈值，超过则认为重复
        
        Returns:
            True 如果内容重复
        """
        if not prev_content or not new_content:
            return False
        
        similarity = self.validator.calculate_similarity(prev_content, new_content)
        logger.debug(f"[Content Check] 内容相似度: {similarity:.2%}")
        
        return similarity > threshold
    
    def _call_kimi_with_continuation(
        self, 
        messages: list, 
        task_id: str,
        module: str,
        temperature: float = 0.7,
        max_retries: int = 3
    ) -> Tuple[str, str]:
        """
        调用 Kimi API，支持自动续生成
        
        Returns:
            (content, log_file_path)
        """
        import time
        
        if not self.kimi_api_key:
            raise ValueError("KIMI_API_KEY not configured")
        
        headers = {
            "Authorization": f"Bearer {self.kimi_api_key}",
            "Content-Type": "application/json"
        }
        
        # model = "kimi-k2-0905-preview"  # 使用长上下文模型
        model = "kimi-k2.5"  # 使用长上下文模型
        
        # kimi-k2.5 只支持 temperature=1
        if model == "kimi-k2.5":
            temperature = 1.0
        
        all_content = []
        current_messages = messages.copy()
        total_tokens = 0
        max_continuation = 5  # 最大续生成次数
        
        # 记录完整 Prompt 到 ai_server.log
        self._log_full_prompt(task_id, module, "kimi", messages)
        
        for attempt in range(max_continuation):
            data = {
                "model": model,
                "messages": current_messages,
                "temperature": temperature,
                "max_tokens": 24000  # kimi-k2.5 支持最大 65535 tokens，设置为 24000 确保复杂仿真代码能够完整生成
            }
            
            logger.info(f"[Kimi API] Task {task_id}/{module} - 调用 #{attempt + 1}")
            
            try:
                response = requests.post(
                    f"{self.kimi_base_url}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=300
                )
                
                if response.status_code != 200:
                    error_msg = f"HTTP {response.status_code}: {response.text[:500]}"
                    logger.error(f"[Kimi API] 错误: {error_msg}")
                    raise Exception(error_msg)
                
                result = response.json()
                choice = result["choices"][0]
                content = choice["message"]["content"]
                finish_reason = choice.get("finish_reason", "unknown")
                usage = result.get("usage", {})
                
                all_content.append(content)
                total_tokens += usage.get("total_tokens", 0)
                
                logger.info(f"[Kimi API] Task {task_id}/{module} - 收到响应, finish_reason={finish_reason}, tokens={usage.get('total_tokens', 0)}")
                
                # 保存响应日志
                log_file = self._save_kimi_response(task_id, module, result, content)
                
                # 检查内容完整性
                if module == "outline":
                    is_complete, check_msg = self.validator.check_outline_complete("".join(all_content))
                elif module == "section":
                    is_complete, check_msg = self.validator.check_section_complete("".join(all_content))
                elif module == "simulation":
                    is_complete, check_msg = self.validator.check_simulation_complete("".join(all_content))
                else:
                    is_complete, check_msg = True, "无需检查"
                
                logger.info(f"[Kimi API] Task {task_id}/{module} - 完整性检查: {check_msg}")
                
                # 如果内容完整或不是因为长度截断，结束生成
                if is_complete or finish_reason != "length":
                    if not is_complete:
                        logger.warning(f"[Kimi API] Task {task_id}/{module} - 内容可能不完整，但非长度原因: {check_msg}")
                    return "".join(all_content), log_file
                
                # 需要续生成
                logger.info(f"[Kimi API] Task {task_id}/{module} - 内容不完整，继续生成...")
                
                # 检查是否返回了重复内容（避免浪费 token）
                if all_content and self._is_duplicate_content(all_content[-1], content):
                    logger.warning(f"[Kimi API] Task {task_id}/{module} - 检测到重复内容，停止续生成")
                    break
                
                # 添加已生成的内容到上下文，请求继续
                current_messages.append({
                    "role": "assistant",
                    "content": content
                })
                current_messages.append({
                    "role": "user", 
                    "content": "请继续生成剩余内容，保持格式一致。从上次中断的地方继续，不要重复已生成的内容。"
                })
                
            except Exception as e:
                logger.error(f"[Kimi API] Task {task_id}/{module} - 调用失败: {e}")
                raise
        
        # 达到最大续生成次数
        logger.warning(f"[Kimi API] Task {task_id}/{module} - 达到最大续生成次数({max_continuation})，返回已生成内容")
        return "".join(all_content), log_file if 'log_file' in locals() else ""
    
    def _call_claude_with_continuation(
        self,
        messages: list,
        task_id: str,
        module: str,
        temperature: float = 0.7,
        max_retries: int = 3
    ) -> Tuple[str, str]:
        """
        调用 Claude API，支持自动续生成
        
        Returns:
            (content, log_file_path)
        """
        import time
        
        if not self.claude_api_key:
            raise ValueError("CLAUDE_API_KEY not configured")
        
        headers = {
            "Authorization": f"Bearer {self.claude_api_key}",
            "Content-Type": "application/json",
            "Anthropic-Version": "2023-06-01"
        }
        
        model = self.claude_model
        all_content = []
        current_messages = messages.copy()
        max_continuation = 5
        
        # 分离 system 和 user 消息
        system_msg = ""
        user_messages = []
        for msg in current_messages:
            if msg.get("role") == "system":
                system_msg = msg.get("content", "")
            else:
                user_messages.append(msg)
        
        # 记录完整 Prompt 到 ai_server.log
        self._log_full_prompt(task_id, module, "claude", messages)
        
        for attempt in range(max_continuation):
            data = {
                "model": model,
                "max_tokens": 8192,
                "temperature": temperature,
                "messages": user_messages
            }
            if system_msg:
                data["system"] = system_msg
            
            logger.info(f"[Claude API] Task {task_id}/{module} - 调用 #{attempt + 1}")
            
            try:
                response = requests.post(
                    f"{self.claude_base_url}/messages",
                    headers=headers,
                    json=data,
                    timeout=360
                )
                
                if response.status_code != 200:
                    error_msg = f"HTTP {response.status_code}: {response.text[:500]}"
                    logger.error(f"[Claude API] 错误: {error_msg}")
                    raise Exception(error_msg)
                
                result = response.json()
                content = result["content"][0]["text"]
                stop_reason = result.get("stop_reason", "unknown")
                usage = result.get("usage", {})
                
                all_content.append(content)
                
                logger.info(f"[Claude API] Task {task_id}/{module} - 收到响应, stop_reason={stop_reason}, tokens={usage.get('output_tokens', 0)}")
                
                # 保存响应日志
                log_file = self._save_claude_response(task_id, module, result, content)
                
                # 检查内容完整性
                is_complete, check_msg = self.validator.check_simulation_complete("".join(all_content))
                logger.info(f"[Claude API] Task {task_id}/{module} - 完整性检查: {check_msg}")
                
                # 如果内容完整或不是因为长度截断，结束生成
                if is_complete or stop_reason != "max_tokens":
                    if not is_complete:
                        logger.warning(f"[Claude API] Task {task_id}/{module} - 内容可能不完整，但非长度原因: {check_msg}")
                    return "".join(all_content), log_file
                
                # 需要续生成
                logger.info(f"[Claude API] Task {task_id}/{module} - 内容不完整，继续生成...")
                
                # 检查是否返回了重复内容（避免浪费 token）
                if all_content and self._is_duplicate_content(all_content[-1], content):
                    logger.warning(f"[Claude API] Task {task_id}/{module} - 检测到重复内容，停止续生成")
                    break
                
                # 添加已生成的内容到上下文
                user_messages.append({
                    "role": "assistant",
                    "content": content
                })
                user_messages.append({
                    "role": "user",
                    "content": "请继续生成剩余内容，保持代码格式一致，完成未闭合的函数和标签。从上次中断的地方继续，不要重复已生成的代码。"
                })
                
            except Exception as e:
                logger.error(f"[Claude API] Task {task_id}/{module} - 调用失败: {e}")
                raise
        
        # 达到最大续生成次数
        logger.warning(f"[Claude API] Task {task_id}/{module} - 达到最大续生成次数({max_continuation})，返回已生成内容")
        return "".join(all_content), log_file if 'log_file' in locals() else ""
    
    # ============ 对外接口 ============
    
    def generate_outline_with_config(
        self,
        course: str,
        knowledge_point: str,
        config: dict,
        task_id: str = "unknown"
    ) -> dict:
        """使用配置生成大纲"""
        prompt = build_outline_prompt(course, knowledge_point, config)
        
        messages = [
            {"role": "system", "content": "你是一个专业的教育内容设计师，擅长生成结构化的教学大纲。严格遵守输出格式要求。"},
            {"role": "user", "content": prompt}
        ]
        
        content, log_file = self._call_kimi_with_continuation(
            messages=messages,
            task_id=task_id,
            module="outline",
            temperature=0.7
        )
        
        # 解析 JSON
        try:
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            outline = json.loads(content)
            outline = self._validate_and_clean_outline(outline)
            return outline
        except json.JSONDecodeError as e:
            logger.error(f"[AI Service] Task {task_id} - 大纲 JSON 解析失败: {e}")
            return self._get_default_outline(course, knowledge_point)
    
    def generate_section_content_with_config(
        self,
        section_title: str,
        section_key_points: list,
        course: str,
        knowledge_point: str,
        config: dict,
        task_id: str = "unknown",
        context: dict = None
    ) -> str:
        """使用配置生成章节内容（支持上下文连贯性）"""
        prompt = build_section_prompt(section_title, section_key_points, course, knowledge_point, config, context)

        messages = [
            {"role": "system", "content": "你是教育内容专家，生成统一结构的高质量HTML教学内容。注意与前后章节保持连贯性。"},
            {"role": "user", "content": prompt}
        ]

        content, log_file = self._call_kimi_with_continuation(
            messages=messages,
            task_id=task_id,
            module="section",
            temperature=0.7
        )

        # 后处理
        content = self._clean_markdown_code_blocks(content)
        content = self._normalize_html_structure(content, section_title)
        content = self._convert_math_delimiters(content)

        return content
    
    def generate_simulation_code_with_config(
        self,
        simulation_desc: str,
        course: str,
        knowledge_point: str,
        simulation_types: list,
        config: dict,
        task_id: str = "unknown",
        context: dict = None
    ) -> str:
        """
        使用配置生成交互仿真代码

        支持通过 SIMULATION_PROVIDER 配置选择使用 Kimi 或 Claude
        
        Args:
            simulation_desc: 仿真描述
            course: 课程名称
            knowledge_point: 知识点
            simulation_types: 仿真类型列表
            config: 配置字典
            task_id: 任务ID
            context: 上下文信息，包含前置章节的核心概念和公式
        """
        prompt = build_simulation_prompt(simulation_desc, course, knowledge_point, simulation_types, config, context)
        
        # 获取仿真生成 provider 配置
        provider = getattr(settings, 'SIMULATION_PROVIDER', 'kimi').lower()
        
        if provider == 'claude':
            # 使用 Claude 生成仿真
            logger.info(f"[Simulation] Task {task_id} - 使用 Claude 生成仿真")
            messages = [
                {"role": "system", "content": "You are an expert in creating interactive HTML5 Canvas simulations for education. Write clean, complete, runnable code with proper HTML structure."},
                {"role": "user", "content": prompt}
            ]
            
            content, log_file = self._call_claude_with_continuation(
                messages=messages,
                task_id=task_id,
                module="simulation",
                temperature=0.7
            )
        else:
            # 默认使用 Kimi 生成仿真
            logger.info(f"[Simulation] Task {task_id} - 使用 Kimi 生成仿真")
            messages = [
                {"role": "system", "content": "你是交互式 HTML5 Canvas 仿真代码专家。编写干净、完整、可运行的教育仿真代码，使用中文注释和界面标签。"},
                {"role": "user", "content": prompt}
            ]
            
            content, log_file = self._call_kimi_with_continuation(
                messages=messages,
                task_id=task_id,
                module="simulation",
                temperature=0.7
            )
        
        # 后处理
        content = self._clean_markdown_code_blocks(content)
        content = self._extract_simulation_content(content)
        
        return content
    
    # ============ 工具方法 ============
    
    def _clean_markdown_code_blocks(self, text: str) -> str:
        """清理 markdown 代码块标记"""
        text = text.strip()
        if text.startswith("```html"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()
    
    def _extract_simulation_content(self, html: str) -> str:
        """提取仿真内容"""
        import re
        
        # 查找 simulation-container div - 使用计数方式匹配最外层标签
        start_match = re.search(r'<div class="simulation-container"[^>]*>', html, re.IGNORECASE)
        if start_match:
            start_pos = start_match.start()
            pos = start_match.end()
            depth = 1
            
            while pos < len(html) and depth > 0:
                # 查找下一个 div 标签（开启或闭合）
                next_open = html.find('<div', pos)
                next_close = html.find('</div>', pos)
                
                # 如果没有更多标签，跳出
                if next_open == -1 and next_close == -1:
                    break
                
                # 确定下一个标签是什么
                if next_open != -1 and (next_close == -1 or next_open < next_close):
                    # 找到开启标签，检查是否是自闭合
                    tag_end = html.find('>', next_open)
                    if tag_end != -1:
                        tag_content = html[next_open:tag_end+1]
                        # 不是自闭合标签（没有 / 结尾）
                        if not tag_content.rstrip().endswith('/>'):
                            depth += 1
                        pos = tag_end + 1
                    else:
                        break
                else:
                    # 找到闭合标签
                    depth -= 1
                    pos = next_close + 6  # len('</div>') = 6
                    
                    if depth == 0:
                        # 找到最外层闭合标签
                        container_content = html[start_pos:pos]
                        
                        # 检查后面是否有 <script> 或 <style> 标签（Kimi 有时会放在外面）
                        remaining = html[pos:].strip()
                        
                        # 提取 script 和 style 标签
                        script_match = re.search(r'<script>.*?</script>', remaining, re.DOTALL | re.IGNORECASE)
                        style_match = re.search(r'<style>.*?</style>', remaining, re.DOTALL | re.IGNORECASE)
                        
                        # 如果 script/style 在容器外面，需要把它们移到容器内
                        if script_match or style_match:
                            # 移除容器闭合标签
                            container_without_close = container_content[:-6]  # 移除 </div>
                            
                            # 按正确顺序添加 style 和 script
                            additional_content = ""
                            if style_match:
                                additional_content += style_match.group(0)
                            if script_match:
                                additional_content += script_match.group(0)
                            
                            # 重新组装
                            return container_without_close + additional_content + "</div>"
                        
                        return container_content
        
        # 如果没有找到，返回原始内容
        return html
    
    def _normalize_html_structure(self, html: str, section_title: str) -> str:
        """规范化 HTML 结构"""
        import re
        
        html = html.strip()
        html = re.sub(r'</?(main|section|article|aside|header|footer)[^>]*>', '', html, flags=re.IGNORECASE)
        
        if html.startswith('<div class="section-content">'):
            open_count = html.count('<div class="section-content">')
            if open_count > 1:
                html = re.sub(r'<div class="section-content">', '', html, count=open_count-1)
                html = re.sub(r'</div>(?=\s*</div>\s*$)', '', html, count=open_count-1)
            
            h3_match = re.search(r'<h3>(.*?)</h3>', html)
            if not h3_match:
                html = html.replace('<div class="section-content">', f'<div class="section-content">\n<h3>{section_title}</h3>', 1)
            return html
        
        h3_match = re.search(r'<h3>(.*?)</h3>', html)
        if not h3_match:
            html = f'<h3>{section_title}</h3>\n{html}'
        
        return f'<div class="section-content">\n{html}\n</div>'
    
    def _convert_math_delimiters(self, html: str) -> str:
        """转换数学公式分隔符"""
        import re
        html = re.sub(r'\\\((.*?)\\\)', r'$\1$', html, flags=re.DOTALL)
        html = re.sub(r'\\\[(.*?)\\\]', r'$$\1$$', html, flags=re.DOTALL)
        return html
    
    def _validate_and_clean_outline(self, outline: dict) -> dict:
        """验证并清理大纲数据"""
        if not outline.get("sections"):
            outline["sections"] = []
        
        for i, section in enumerate(outline["sections"]):
            section["order"] = i + 1
            if not section.get("id"):
                section["id"] = f"section_{i}"
            if not section.get("title"):
                section["title"] = f"章节 {i + 1}"
            if not section.get("content"):
                section["content"] = []
        
        return outline
    
    def _get_default_outline(self, course: str, knowledge_point: str) -> dict:
        """获取默认大纲"""
        return {
            "title": f"{course} - {knowledge_point}",
            "sections": [
                {"id": "concept", "title": "知识点概念", "content": ["核心定义", "基本公式", "物理意义"], "order": 1},
                {"id": "explanation", "title": "详细讲解", "content": ["原理分析", "数学推导", "实例说明"], "order": 2},
                {"id": "difficulties", "title": "重难点分析", "content": ["常见难点", "易错点", "解题技巧"], "order": 3},
                {"id": "simulation", "title": "交互仿真", "content": ["参数调节演示", "动态模拟"], "order": 4},
                {"id": "summary", "title": "总结", "content": ["核心要点", "适用条件", "常见误区"], "order": 5},
                {"id": "exercises", "title": "习题与答案", "content": ["基础练习", "进阶练习", "详细解答"], "order": 6}
            ]
        }

    def generate_complete_html(self, title: str, body_content: str) -> str:
        """
        生成完整的 HTML 文档（包含样式和 KaTeX）
        
        Args:
            title: 文档标题
            body_content: body 内的 HTML 内容
        
        Returns:
            完整的 HTML 文档字符串
        """
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <!-- KaTeX 用于渲染数学公式 - 比 MathJax 更轻量更快 -->
    <link rel="stylesheet" href="https://cdn.bootcdn.net/ajax/libs/KaTeX/0.16.9/katex.min.css">
    <script defer src="https://cdn.bootcdn.net/ajax/libs/KaTeX/0.16.9/katex.min.js"></script>
    <script defer src="https://cdn.bootcdn.net/ajax/libs/KaTeX/0.16.9/contrib/auto-render.min.js"></script>
    <script>
        document.addEventListener("DOMContentLoaded", function() {{
            if (typeof renderMathInElement !== 'undefined') {{
                renderMathInElement(document.body, {{
                    delimiters: [
                        {{left: '$$', right: '$$', display: true}},
                        {{left: '$', right: '$', display: false}}
                    ],
                    throwOnError: false
                }});
            }}
        }});
    </script>
    <style>
        :root {{
            --primary-color: #3b82f6;
            --secondary-color: #8b5cf6;
            --success-color: #10b981;
            --warning-color: #f59e0b;
            --danger-color: #ef4444;
            --bg-color: #f8fafc;
            --card-bg: #ffffff;
            --text-primary: #1e293b;
            --text-secondary: #64748b;
            --border-color: #e2e8f0;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.8;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: var(--card-bg);
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}
        
        .header .subtitle {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        
        .content {{
            padding: 40px;
        }}
        
        section {{
            margin-bottom: 40px;
            padding: 30px;
            background: var(--bg-color);
            border-radius: 12px;
            border-left: 5px solid var(--primary-color);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        
        section:hover {{
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }}
        
        section:nth-child(2) {{ border-left-color: var(--secondary-color); }}
        section:nth-child(3) {{ border-left-color: var(--success-color); }}
        section:nth-child(4) {{ border-left-color: var(--warning-color); }}
        section:nth-child(5) {{ border-left-color: var(--danger-color); }}
        
        h2 {{
            color: var(--text-primary);
            font-size: 1.8em;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid var(--border-color);
        }}
        
        h3 {{
            color: var(--primary-color);
            font-size: 1.4em;
            margin: 25px 0 15px;
        }}
        
        h4 {{
            color: var(--text-secondary);
            font-size: 1.2em;
            margin: 20px 0 10px;
        }}
        
        p {{
            color: var(--text-primary);
            margin-bottom: 15px;
            text-align: justify;
        }}
        
        ul, ol {{
            margin: 15px 0;
            padding-left: 30px;
        }}
        
        li {{
            margin-bottom: 10px;
            color: var(--text-primary);
        }}
        
        strong {{
            color: var(--primary-color);
            font-weight: 600;
        }}
        
        code {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 3px 8px;
            border-radius: 4px;
            font-family: "Consolas", "Monaco", monospace;
            font-size: 0.9em;
        }}
        
        pre {{
            background: #1e293b;
            color: #e2e8f0;
            padding: 20px;
            border-radius: 8px;
            overflow-x: auto;
            margin: 20px 0;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.3);
        }}
        
        pre code {{
            background: none;
            padding: 0;
            color: inherit;
        }}
        
        blockquote {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            font-style: italic;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        th {{
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }}
        
        td {{
            padding: 12px 15px;
            border-bottom: 1px solid var(--border-color);
        }}
        
        tr:nth-child(even) {{
            background: var(--bg-color);
        }}
        
        tr:hover {{
            background: #e0e7ff;
        }}
        
        /* 仿真区域样式 */
        canvas {{
            display: block;
            max-width: 100%;
            margin: 20px auto;
            border: 3px solid var(--primary-color);
            border-radius: 12px;
            background: white;
            box-shadow: 0 10px 30px rgba(0,0,0,0.15);
        }}
        
        .simulation-controls {{
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 20px;
            border-radius: 12px;
            margin: 20px 0;
        }}
        
        input[type="range"] {{
            width: 100%;
            margin: 10px 0;
            height: 8px;
            border-radius: 4px;
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            outline: none;
            -webkit-appearance: none;
        }}
        
        input[type="range"]::-webkit-slider-thumb {{
            -webkit-appearance: none;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: white;
            cursor: pointer;
            box-shadow: 0 2px 6px rgba(0,0,0,0.3);
        }}
        
        button {{
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1em;
            font-weight: 600;
            margin: 5px;
            transition: transform 0.2s, box-shadow 0.2s;
            box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4);
        }}
        
        button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(59, 130, 246, 0.6);
        }}
        
        /* 公式样式 */
        .math-display {{
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 20px;
            border-radius: 12px;
            margin: 20px 0;
            text-align: center;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        /* 提示框 */
        .tip {{
            background: linear-gradient(135deg, #d4fc79 0%, #96e6a1 100%);
            color: #166534;
            padding: 15px 20px;
            border-radius: 8px;
            margin: 20px 0;
            border-left: 5px solid var(--success-color);
        }}
        
        .warning {{
            background: linear-gradient(135deg, #ffeaa7 0%, #fdcb6e 100%);
            color: #92400e;
            padding: 15px 20px;
            border-radius: 8px;
            margin: 20px 0;
            border-left: 5px solid var(--warning-color);
        }}
        
        .footer {{
            background: var(--bg-color);
            padding: 20px;
            text-align: center;
            color: var(--text-secondary);
            font-size: 0.9em;
        }}
        
        /* 章节内容统一包装 */
        .section-content {{
            width: 100%;
        }}
        
        .section-content h3 {{
            color: var(--primary-color);
            font-size: 1.5em;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid var(--border-color);
        }}
        
        .section-content h4 {{
            color: var(--text-secondary);
            font-size: 1.2em;
            margin: 20px 0 10px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{title}</h1>
        </div>
        <div class="content">
            {body_content}
        </div>
        <div class="footer">
            由 智教云 AI 教学平台生成
        </div>
    </div>
</body>
</html>"""


# 全局 AI 服务实例
ai_service = AIService()
