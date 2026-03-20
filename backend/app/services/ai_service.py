"""
AI 服务封装
支持 Kimi API 调用
"""
import json
import logging
import requests
from typing import Dict, Any, Optional

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AIService:
    """AI 服务统一封装"""
    
    def __init__(self):
        self.kimi_api_key = settings.KIMI_API_KEY
        self.kimi_base_url = "https://api.moonshot.cn/v1"
        self.claude_api_key = settings.CLAUDE_API_KEY
    
    def _call_kimi(self, messages: list, temperature: float = 0.7, max_retries: int = 3) -> str:
        """
        调用 Kimi API（带重试机制）
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_retries: 最大重试次数
        
        Returns:
            AI 回复内容
        """
        import time
        
        if not self.kimi_api_key:
            raise ValueError("KIMI_API_KEY not configured")
        
        headers = {
            "Authorization": f"Bearer {self.kimi_api_key}",
            "Content-Type": "application/json"
        }
        
        # 使用 moonshot-v1-8k 模型（默认）
        model = "moonshot-v1-8k"
        
        # 估算 token 数量并记录
        total_chars = sum(len(m["content"]) for m in messages)
        prompt_preview = messages[-1]["content"][:200] if messages else ""
        logger.info(f"[Kimi API] 开始调用 | 模型: {model} | 字符数: {total_chars} | 消息数: {len(messages)}")
        logger.debug(f"[Kimi API] Prompt 预览: {prompt_preview}...")
        
        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature
        }
        
        last_error = None
        start_time = time.time()
        
        for attempt in range(max_retries):
            attempt_start = time.time()
            logger.info(f"[Kimi API] 尝试 {attempt + 1}/{max_retries}")
            
            try:
                response = requests.post(
                    f"{self.kimi_base_url}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=360  # 6 分钟超时
                )
                
                elapsed = time.time() - attempt_start
                logger.info(f"[Kimi API] 响应状态: {response.status_code} | 耗时: {elapsed:.2f}s")
                
                # 处理限流错误
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 5))
                    logger.warning(f"[Kimi API] 触发限流 (429)，等待 {retry_after}s 后重试")
                    time.sleep(retry_after)
                    continue
                
                # 处理其他 HTTP 错误
                if response.status_code != 200:
                    error_body = response.text[:500]
                    logger.error(f"[Kimi API] HTTP 错误: {response.status_code} | 响应: {error_body}")
                    last_error = f"HTTP {response.status_code}: {error_body}"
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        logger.info(f"[Kimi API] 等待 {wait_time}s 后重试...")
                        time.sleep(wait_time)
                    continue
                
                result = response.json()
                
                # 检查响应结构
                if "choices" not in result or not result["choices"]:
                    logger.error(f"[Kimi API] 响应结构异常: {json.dumps(result, ensure_ascii=False)[:500]}")
                    raise ValueError("Invalid API response structure: missing 'choices'")
                
                content = result["choices"][0]["message"]["content"]
                total_elapsed = time.time() - start_time
                
                # 记录成功信息
                logger.info(f"[Kimi API] 调用成功 | 总耗时: {total_elapsed:.2f}s | 响应长度: {len(content)} 字符")
                logger.debug(f"[Kimi API] 响应预览: {content[:200]}...")
                
                return content
                
            except requests.exceptions.Timeout as e:
                elapsed = time.time() - attempt_start
                last_error = f"请求超时 ({elapsed:.1f}s): {str(e)}"
                logger.error(f"[Kimi API] 超时错误 (attempt {attempt + 1}): {last_error}")
                if attempt < max_retries - 1:
                    wait_time = min(2 ** attempt * 2, 30)  # 最大等待30秒
                    logger.info(f"[Kimi API] 等待 {wait_time}s 后重试...")
                    time.sleep(wait_time)
                    
            except requests.exceptions.RequestException as e:
                elapsed = time.time() - attempt_start
                last_error = f"请求异常 ({elapsed:.1f}s): {str(e)}"
                logger.error(f"[Kimi API] 请求异常 (attempt {attempt + 1}): {last_error}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                    
            except Exception as e:
                elapsed = time.time() - attempt_start
                last_error = f"未知错误 ({elapsed:.1f}s): {str(e)}"
                logger.error(f"[Kimi API] 未知错误 (attempt {attempt + 1}): {last_error}", exc_info=True)
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
        
        # 所有重试都失败
        total_elapsed = time.time() - start_time
        final_error = f"[Kimi API] 调用失败（{max_retries} 次尝试后放弃）| 总耗时: {total_elapsed:.2f}s | 最后错误: {last_error}"
        logger.error(final_error)
        raise Exception(final_error)
    
    def _call_claude(self, messages: list, temperature: float = 0.7, max_retries: int = 3) -> str:
        """
        调用 Claude API（用于生成仿真代码，支持更长输出）
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_retries: 最大重试次数
        
        Returns:
            AI 回复内容
        """
        import time
        
        if not self.claude_api_key:
            raise ValueError("CLAUDE_API_KEY not configured")
        
        headers = {
            "Authorization": f"Bearer {self.claude_api_key}",
            "Content-Type": "application/json",
            "Anthropic-Version": "2023-06-01"
        }
        
        # 从环境变量读取模型名称，默认使用 claude-3-5-sonnet 
        model = getattr(settings, 'CLAUDE_MODEL', 'claude-opus-4-5-20251101') # 不要更改
        
        # 转换消息格式为 Claude 格式
        system_msg = ""
        user_messages = []
        for msg in messages:
            if msg.get("role") == "system":
                system_msg = msg.get("content", "")
            else:
                user_messages.append(msg)
        
        # 构建请求体
        data = {
            "model": model,
            "max_tokens": 8192,  # Claude 支持 8k 输出
            "temperature": temperature,
            "messages": user_messages
        }
        if system_msg:
            data["system"] = system_msg
        
        last_error = None
        start_time = time.time()
        
        for attempt in range(max_retries):
            attempt_start = time.time()
            logger.info(f"[Claude API] 尝试 {attempt + 1}/{max_retries}")
            
            try:
                response = requests.post(
                    # "https://api.anthropic.com/v1/messages",
                    "https://xiaoai.plus/v1/messages",
                    headers=headers,
                    json=data,
                    timeout=360
                )
                
                elapsed = time.time() - attempt_start
                logger.info(f"[Claude API] 响应状态: {response.status_code} | 耗时: {elapsed:.2f}s")
                
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 5))
                    logger.warning(f"[Claude API] 触发限流 (429)，等待 {retry_after}s 后重试")
                    time.sleep(retry_after)
                    continue
                
                if response.status_code != 200:
                    error_body = response.text[:500]
                    logger.error(f"[Claude API] HTTP 错误: {response.status_code} | 响应: {error_body}")
                    last_error = f"HTTP {response.status_code}: {error_body}"
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        time.sleep(wait_time)
                    continue
                
                result = response.json()
                
                # 保存原始响应到日志文件以便调试
                import os
                from datetime import datetime
                log_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'app', 'logs', 'claude_responses')
                os.makedirs(log_dir, exist_ok=True)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
                log_file = os.path.join(log_dir, f'claude_response_{timestamp}.json')
                try:
                    with open(log_file, 'w', encoding='utf-8') as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)
                    logger.debug(f"[Claude API] 原始响应已保存到: {log_file}")
                except Exception as e:
                    logger.warning(f"[Claude API] 保存响应日志失败: {e}")
                
                # 处理不同的响应格式
                content = None
                extracted_format = None
                
                # 尝试标准 Claude 格式
                if "content" in result and result["content"]:
                    if isinstance(result["content"], list) and len(result["content"]) > 0:
                        if "text" in result["content"][0]:
                            content = result["content"][0]["text"]
                            extracted_format = "claude_standard"
                        elif "value" in result["content"][0]:
                            content = result["content"][0]["value"]
                            extracted_format = "claude_value"
                
                # 尝试 OpenAI 兼容格式
                if not content and "choices" in result and result["choices"]:
                    choice = result["choices"][0]
                    if "message" in choice and "content" in choice["message"]:
                        content = choice["message"]["content"]
                        extracted_format = "openai_compatible"
                    elif "text" in choice:
                        content = choice["text"]
                        extracted_format = "openai_text"
                
                # 尝试直接 content 字段
                if not content and "content" in result and isinstance(result["content"], str):
                    content = result["content"]
                    extracted_format = "direct_content"
                
                # 尝试 data.choices 格式
                if not content and "data" in result and "choices" in result["data"]:
                    content = result["data"]["choices"][0].get("message", {}).get("content", "")
                    extracted_format = "data_choices"
                
                # 尝试嵌套在 data 中的 content
                if not content and "data" in result and isinstance(result["data"], dict):
                    if "content" in result["data"]:
                        data_content = result["data"]["content"]
                        if isinstance(data_content, list) and len(data_content) > 0:
                            content = data_content[0].get("text", "")
                            extracted_format = "data_content_list"
                        elif isinstance(data_content, str):
                            content = data_content
                            extracted_format = "data_content_string"
                
                if not content:
                    logger.error(f"[Claude API] 响应结构异常，无法解析。原始响应已保存到: {log_file}")
                    logger.error(f"[Claude API] 响应内容: {json.dumps(result, ensure_ascii=False)[:1000]}")
                    raise ValueError(f"Invalid API response structure: cannot extract content. Log saved to: {log_file}")
                
                logger.info(f"[Claude API] 响应格式: {extracted_format}")
                
                total_elapsed = time.time() - start_time
                
                logger.info(f"[Claude API] 调用成功 | 总耗时: {total_elapsed:.2f}s | 响应长度: {len(content)} 字符")
                logger.debug(f"[Claude API] 响应预览: {content[:200]}...")
                
                return content
                
            except requests.exceptions.Timeout as e:
                elapsed = time.time() - attempt_start
                last_error = f"请求超时 ({elapsed:.1f}s): {str(e)}"
                logger.error(f"[Claude API] 超时错误 (attempt {attempt + 1}): {last_error}")
                if attempt < max_retries - 1:
                    wait_time = min(2 ** attempt * 2, 30)
                    time.sleep(wait_time)
                    
            except requests.exceptions.RequestException as e:
                elapsed = time.time() - attempt_start
                last_error = f"请求异常 ({elapsed:.1f}s): {str(e)}"
                logger.error(f"[Claude API] 请求异常 (attempt {attempt + 1}): {last_error}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                    
            except Exception as e:
                elapsed = time.time() - attempt_start
                last_error = f"未知错误 ({elapsed:.1f}s): {str(e)}"
                logger.error(f"[Claude API] 未知错误 (attempt {attempt + 1}): {last_error}", exc_info=True)
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
        
        # 所有重试都失败
        total_elapsed = time.time() - start_time
        final_error = f"[Claude API] 调用失败（{max_retries} 次尝试后放弃）| 总耗时: {total_elapsed:.2f}s | 最后错误: {last_error}"
        logger.error(final_error)
        raise Exception(final_error)
    
    def generate_outline(self, course: str, knowledge_point: str, difficulty: str = "medium") -> Dict[str, Any]:
        """
        生成教学大纲
        
        Args:
            course: 课程名称
            knowledge_point: 知识点
            difficulty: 难度等级 (easy, medium, hard)
        
        Returns:
            大纲 JSON 数据
        """
        prompt = f"""你是一位资深教授，为本科生设计专业、深入的教学大纲。请为以下课程知识点生成结构化的教学大纲。

## 课程信息
- 课程：{course}
- 知识点：{knowledge_point}
- 难度：{difficulty}

## 大纲结构要求
每个章节的 content 必须是字符串数组，每个元素是一个具体的教学要点（不是标题，而是需要讲解的具体内容）。

### 1. concept - 知识点概念（4-6个要点）
必须包含：
- 严格的数学定义（含公式）
- 物理意义/几何解释
- 定理/定律的完整表述
- 适用条件和边界
- 与相关概念的区别

### 2. explanation - 详细讲解（5-7个要点）
必须包含：
- 原理的数学推导（关键步骤）
- 不同角度的理解方式
- 典型实例1：简单情况（含具体数值）
- 典型实例2：复杂情况（含具体数值）
- 工程应用背景
- 参数对结果的影响分析

### 3. difficulties - 重难点分析（4-5个要点）
必须包含：
- 学生最常见的理解误区及纠正
- 数学推导中的关键难点
- 实际应用中的注意事项
- 与其他知识点的混淆点对比
- 进阶思考/拓展问题

### 4. simulation - 交互仿真（2-3个要点，暂不实现，仅描述）
- 仿真目标和观察指标
- 可调参数及其物理意义

### 5. summary - 总结（4-5个要点）
必须包含：
- 核心公式回顾
- 关键概念梳理
- 适用场景总结
- 与后续知识点的联系

### 6. exercises - 习题与答案（4-5个要点）
必须包含：
- 基础题：直接应用公式（含具体数值）
- 提高题：综合应用（含具体数值）
- 设计题：实际工程问题
- 证明题：重要定理的证明

## 输出格式
请以 JSON 格式返回，结构如下：
{{
    "title": "{course} - {knowledge_point}",
    "sections": [
        {{
            "id": "concept",
            "title": "知识点概念",
            "content": ["严格数学定义：...", "物理意义：...", "定理表述：...", "适用条件：..."],
            "order": 1
        }},
        {{
            "id": "explanation",
            "title": "详细讲解",
            "content": ["数学推导：...", "实例1：...", "实例2：...", "工程应用：..."],
            "order": 2
        }},
        {{
            "id": "difficulties",
            "title": "重难点分析",
            "content": ["常见误区：...", "推导难点：...", "应用注意：..."],
            "order": 3
        }},
        {{
            "id": "simulation",
            "title": "交互仿真",
            "content": ["仿真目标：...", "可调参数：..."],
            "order": 4
        }},
        {{
            "id": "summary",
            "title": "总结",
            "content": ["核心公式：...", "关键概念：...", "适用场景：..."],
            "order": 5
        }},
        {{
            "id": "exercises",
            "title": "习题与答案",
            "content": ["基础题：...", "提高题：...", "设计题：..."],
            "order": 6
        }}
    ]
}}

## 重要规则
- content 必须是字符串数组，每个元素是具体的教学内容描述
- 要点要具体、可执行，不是泛泛的标题
- 包含具体的数值、公式、案例细节
- 不要返回对象数组或嵌套结构
- 不要返回 [object Object] 这种无效内容

只返回 JSON，不要其他说明。"""

        messages = [
            {"role": "system", "content": "你是一个专业的教育内容设计师，擅长生成结构化的教学大纲。严格遵守输出格式要求。"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self._call_kimi(messages, temperature=0.7)
            # 解析 JSON
            # 清理可能的 markdown 代码块
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()
            
            outline = json.loads(response)
            
            # 验证并清理大纲数据
            outline = self._validate_and_clean_outline(outline)
            
            logger.info(f"Generated outline for {course} - {knowledge_point}")
            return outline
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse outline JSON: {e}")
            # 返回默认大纲结构
            return self._get_default_outline(course, knowledge_point)
        except Exception as e:
            logger.error(f"Failed to generate outline: {e}")
            return self._get_default_outline(course, knowledge_point)
    
    def _validate_and_clean_outline(self, outline: Dict[str, Any]) -> Dict[str, Any]:
        """验证并清理大纲数据，修复常见问题"""
        sections = outline.get("sections", [])
        
        for section in sections:
            content = section.get("content", [])
            
            # 确保 content 是列表
            if not isinstance(content, list):
                content = [str(content)] if content else []
            
            # 清理列表中的无效内容
            cleaned_content = []
            for item in content:
                item_str = str(item)
                # 跳过 [object Object] 等无效内容
                if item_str == "[object Object]" or not item_str.strip():
                    continue
                cleaned_content.append(item_str)
            
            # 如果清理后为空，添加默认内容
            if not cleaned_content:
                section_title = section.get("title", "")
                cleaned_content = [f"{section_title}内容待补充"]
            
            section["content"] = cleaned_content
        
        return outline

    def _clean_markdown_code_blocks(self, text: str) -> str:
        """清理 Markdown 代码块标记"""
        text = text.strip()
        # 处理 ```html 开头的代码块
        if text.startswith("```html"):
            text = text[7:]
        elif text.startswith("```HTML"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        # 处理结尾的 ```
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()

    def generate_section_content(self, section_title: str, section_key_points: list, course: str, knowledge_point: str) -> str:
        """
        生成章节详细内容
        
        Args:
            section_title: 章节标题
            section_key_points: 章节要点
            course: 课程名称
            knowledge_point: 知识点
        
        Returns:
            HTML 格式的内容
        """
        key_points_str = "\n".join([f"- {point}" for point in section_key_points])
        
        prompt = f"""你是一位在高校执教20年的资深教授，擅长把复杂的工程概念用生动的语言讲清楚。请为以下章节撰写教学内容，像在课堂上讲课一样自然流畅。

## 课程信息
- 课程：{course}
- 知识点：{knowledge_point}
- 章节：{section_title}
- 学生水平：本科工科生，有一定数学基础但缺乏工程直觉

## 需要覆盖的核心内容
{key_points_str}

## 教学风格要求（非常重要）
1. **像讲课一样写作**：
   - 用"我们"、"大家"、"同学们"等称呼，营造课堂氛围
   - 适当使用设问："那么问题来了..."、"大家有没有想过..."
   - 加入教授的思考和经验："我在工程实践中发现..."、"很多同学在这里会犯一个错误..."

2. **从直观到抽象**：
   - 先用生活化例子或物理直觉引入（如开车、调音量、温度控制等）
   - 再逐步过渡到数学定义和公式
   - 最后回到工程应用，形成闭环

3. **内容组织灵活多样**：
   - 不要机械地1.2.3.4编号，根据内容特点选择最适合的结构
   - 可以用"故事线"、"问题驱动"、"对比分析"、"案例研究"等多种形式
   - 允许有"知识卡片"、"思考题"、"延伸阅读"等灵活板块

4. **真实教学场景**：
   - 包含"常见错误"：指出学生容易混淆的地方
   - 包含"教授提示"：分享考试重点、记忆技巧、工程经验
   - 包含"互动思考"：提出让学生暂停思考的问题
   - 包含"历史背景"：知识点的发展历史、重要人物

5. **公式讲解生动**：
   - 每个公式都要解释"为什么长这样"
   - 用物理意义解释每一项的作用
   - 通过量纲分析验证合理性

## HTML 格式要求
1. 最外层使用 <div class="section-content">
2. 章节主标题使用 <h3>{section_title}</h3>
3. 小节标题用 <h4>，但标题要生动（如"为什么需要微分项？"而不是"3. 微分控制"）
4. 段落使用 <p>，重要概念用 <strong> 加粗
5. 公式使用 $...$ 行内或 $$...$$ 块级
6. 使用 <div class="tip"> 放置教授提示、记忆技巧
7. 使用 <div class="warning"> 放置常见错误、易混淆点
8. 可以使用 <blockquote> 放置名言、历史背景
9. 不要包含 html/head/body 标签
10. **结构要求**：div 嵌套要清晰，section-content 内直接是 h3 + 多个段落/小节，不要过多嵌套

## 优秀教学内容的例子

❌ 死板的写法：
"1. 数学定义：PD控制器的输出为 u(t) = Kp*e(t) + Kd*de/dt"

✅ 生动的写法：
"我们先从一个生活场景说起。想象你在开车，目标是保持车速在60km/h。这时候你会怎么做？

首先，你会看仪表盘，发现实际速度是55km/h——这就是'偏差'。你心里想：'慢了5公里，得踩油门'。踩多少呢？如果你是个急性子，可能会猛踩；如果比较谨慎，就轻踩。这种'根据偏差大小决定动作强弱'的直觉，就是比例控制的思想。

但等等，如果前面是个上坡呢？你刚踩完油门，发现车速还在往下掉。这时候老司机都知道：'坡度在变大，得提前多踩点'。这种'根据变化趋势提前动作'的智慧，就是微分控制的精髓。

把这两种直觉写成数学语言，就得到了PD控制器的核心公式：$$u(t) = K_p e(t) + K_d \\frac{{de(t)}}{{dt}}$$"

请生成像上面这样生动、有温度、有故事的教学 HTML 内容。"""

        messages = [
            {"role": "system", "content": "你是教育内容专家，生成统一结构的高质量HTML教学内容。严格遵守HTML结构要求。"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self._call_kimi(messages, temperature=0.7)
            cleaned = self._clean_markdown_code_blocks(response)
            
            # 统一包装结构
            cleaned = self._normalize_html_structure(cleaned, section_title)
            
            # 转换公式格式 \( \) -> $, \[ \] -> $$
            cleaned = self._convert_math_delimiters(cleaned)
            
            logger.info(f"Generated section '{section_title}', length: {len(cleaned)}")
            return cleaned
        except Exception as e:
            logger.error(f"Failed to generate section content for '{section_title}': {e}")
            # 返回更详细的错误信息
            error_html = f'''<div class="section-content">
<div class="warning">
    <strong>内容生成失败</strong>
    <p>章节：{section_title}</p>
    <p>错误：{str(e)[:200]}</p>
    <p>请稍后重试或联系管理员</p>
</div>
</div>'''
            return error_html
    
    def _normalize_html_structure(self, html: str, section_title: str) -> str:
        """规范化 HTML 结构，确保统一格式和清晰的 div 嵌套"""
        import re
        
        html = html.strip()
        
        # 移除可能存在的结构性标签（避免嵌套混乱）
        html = re.sub(r'</?(main|section|article|aside|header|footer)[^>]*>', '', html, flags=re.IGNORECASE)
        
        # 如果已经有 section-content 包装
        if html.startswith('<div class="section-content">'):
            # 检查内部是否有多余的 section-content 嵌套
            # 统计 section-content 的数量
            open_count = html.count('<div class="section-content">')
            if open_count > 1:
                # 移除内部的 section-content 包装，只保留最外层
                html = re.sub(r'<div class="section-content">', '', html, count=open_count-1)
                html = re.sub(r'</div>(?=\s*</div>\s*$)', '', html, count=open_count-1)
            
            # 检查是否有 h3 标题
            h3_match = re.search(r'<h3>(.*?)</h3>', html)
            if not h3_match:
                # 在 section-content 开始后添加 h3
                html = html.replace('<div class="section-content">', f'<div class="section-content">\n<h3>{section_title}</h3>', 1)
            return html
        
        # 如果没有 section-content 包装，添加包装
        # 检查是否已有 h3
        h3_match = re.search(r'<h3>(.*?)</h3>', html)
        if not h3_match:
            html = f'<h3>{section_title}</h3>\n{html}'
        
        # 包装在 section-content 中
        return f'<div class="section-content">\n{html}\n</div>'
    
    def _convert_math_delimiters(self, html: str) -> str:
        """转换数学公式分隔符 \( \) -> $, \[ \] -> $$"""
        import re
        
        # 转换行内公式 \( ... \) -> $ ... $
        # 使用非贪婪匹配，处理多行内容
        html = re.sub(r'\\\((.*?)\\\)', r'$\1$', html, flags=re.DOTALL)
        
        # 转换块级公式 \[ ... \] -> $$ ... $$
        html = re.sub(r'\\\[(.*?)\\\]', r'$$\1$$', html, flags=re.DOTALL)
        
        return html

    def generate_simulation_code(self, simulation_desc: str, course: str, knowledge_point: str) -> str:
        """
        生成交互仿真代码
        
        Args:
            simulation_desc: 仿真描述
            course: 课程名称
            knowledge_point: 知识点
        
        Returns:
            JavaScript 代码字符串
        """
        prompt = f"""Generate interactive HTML5 Canvas simulation for {knowledge_point} ({course}).

Requirements: {simulation_desc}

STRICT OUTPUT RULES:
1. Return ONLY content inside <div class="simulation-container">, NO html/head/body tags
2. Wrap ALL JS in (function(){{...}})(); IIFE, NO global variables
3. Use canvas ID: sim-canvas-abc123
4. Canvas: 700x480px, border-radius:12px, box-shadow

REQUIRED ELEMENTS:
- Centered <h4> title (color:#3b82f6) and <p> description
- Data panel: gradient div with 2-3 large number displays
- Canvas with grid, axes, and curve legend
- Controls: 2-4 sliders with live values, Start/Pause/Reset buttons, 2-3 preset buttons

JS REQUIREMENTS:
- Use requestAnimationFrame for animation
- Redraw immediately on parameter change
- Multiple curves with different colors
- COMPLETE, RUNNABLE code only"""

        messages = [
            {"role": "system", "content": "You are an expert in creating interactive HTML5 Canvas simulations for education. Write clean, complete, runnable code with proper HTML structure."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            # 使用 Claude 生成仿真代码（支持更长输出）
            if self.claude_api_key:
                logger.info("Using Claude API for simulation generation")
                response = self._call_claude(messages, temperature=0.7)
            else:
                logger.info("Claude API key not set, falling back to Kimi")
                response = self._call_kimi(messages, temperature=0.8)
            
            cleaned = self._clean_markdown_code_blocks(response)
            
            # Post-process to extract simulation content
            cleaned = self._extract_simulation_content(cleaned)
            
            logger.info(f"Generated simulation code, length: {len(cleaned)}")
            return cleaned
        except Exception as e:
            logger.error(f"Failed to generate simulation code: {e}")
            error_html = f'''<div class="section-content">
<div class="warning">
    <strong>仿真代码生成失败</strong>
    <p>错误：{str(e)[:200]}</p>
    <p>请稍后重试或联系管理员</p>
</div>
</div>'''
            return error_html
    
    def _extract_simulation_content(self, html: str) -> str:
        """Extract simulation content and remove extra HTML structure tags."""
        import re
        
        html = html.strip()
        
        # If already correct format, return directly
        if html.startswith('<div class="simulation-container">') or html.startswith("<div class='simulation-container'>"):
            return html
        
        # Try to extract body content from full HTML document
        body_match = re.search(r'<body[^>]*>(.*?)</body>', html, re.DOTALL | re.IGNORECASE)
        if body_match:
            body_content = body_match.group(1).strip()
            # If simulation-container exists in body, extract it
            sim_match = re.search(r'(<div class=["\']simulation-container["\']>.*?</div>)', body_content, re.DOTALL | re.IGNORECASE)
            if sim_match:
                return sim_match.group(1)
            # Otherwise wrap entire body content
            return f'<div class="simulation-container">\n{body_content}\n</div>'
        
        # Try to find simulation-container directly
        sim_match = re.search(r'(<div class=["\']simulation-container["\']>.*?</div>)', html, re.DOTALL | re.IGNORECASE)
        if sim_match:
            return sim_match.group(1)
        
        # Remove html/head/body tags and wrap
        html = re.sub(r'<!DOCTYPE[^>]*>', '', html, flags=re.IGNORECASE)
        html = re.sub(r'</?html[^>]*>', '', html, flags=re.IGNORECASE)
        html = re.sub(r'<head[^>]*>.*?</head>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'</?body[^>]*>', '', html, flags=re.IGNORECASE)
        
        html = html.strip()
        
        if not html.startswith('<'):
            html = f'<p>{html}</p>'
        
        return f'<div class="simulation-container">\n{html}\n</div>'
    
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

    def _get_default_outline(self, course: str, knowledge_point: str) -> Dict[str, Any]:
        """获取默认大纲结构"""
        return {
            "title": f"{course} - {knowledge_point}",
            "sections": [
                {
                    "id": "concept",
                    "title": "知识点概念",
                    "content": ["核心定义", "基本公式", "物理意义"],
                    "order": 1
                },
                {
                    "id": "explanation",
                    "title": "详细讲解",
                    "content": ["原理分析", "数学推导", "实例说明"],
                    "order": 2
                },
                {
                    "id": "difficulties",
                    "title": "重难点分析",
                    "content": ["常见难点", "易错点", "解题技巧"],
                    "order": 3
                },
                {
                    "id": "simulation",
                    "title": "交互仿真",
                    "content": ["参数调节演示", "动态模拟"],
                    "order": 4
                },
                {
                    "id": "summary",
                    "title": "总结",
                    "content": ["核心要点", "适用条件", "常见误区"],
                    "order": 5
                },
                {
                    "id": "exercises",
                    "title": "习题与答案",
                    "content": ["基础练习", "进阶练习", "详细解答"],
                    "order": 6
                }
            ]
        }


# 全局 AI 服务实例
ai_service = AIService()
