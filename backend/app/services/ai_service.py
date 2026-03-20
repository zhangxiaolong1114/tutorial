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
        
        # 固定使用 moonshot-v1-8k 模型（用户要求不变）
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
        prompt = f"""你是一个专业的教育内容设计师。请为以下课程知识点生成详细的教学大纲。

课程：{course}
知识点：{knowledge_point}
难度：{difficulty}

请生成包含以下章节的大纲，每个章节的 content 必须是字符串数组（string[]），每个元素是一个要点：
1. concept - 知识点概念：核心定义和公式（3-5个要点）
2. explanation - 详细讲解：原理、推导、实例（3-4个要点）
3. difficulties - 重难点分析：常见难点和易错点（2-3个要点）
4. simulation - 交互仿真：描述需要模拟什么（1-2个要点）
5. summary - 总结：核心要点回顾（2-3个要点）
6. exercises - 习题与答案：练习题描述（2-3个要点，每个习题用字符串描述）

重要规则：
- content 必须是字符串数组，如：["要点1", "要点2"]
- 不要返回对象数组或嵌套结构
- 不要返回 [object Object] 这种无效内容
- 每个要点必须是纯文本字符串

请以 JSON 格式返回，结构如下：
{{
    "title": "{course} - {knowledge_point}",
    "sections": [
        {{
            "id": "concept",
            "title": "知识点概念",
            "content": ["要点1", "要点2", "要点3"],
            "order": 1
        }},
        {{
            "id": "explanation",
            "title": "详细讲解",
            "content": ["要点1", "要点2"],
            "order": 2
        }},
        {{
            "id": "difficulties",
            "title": "重难点分析",
            "content": ["要点1", "要点2"],
            "order": 3
        }},
        {{
            "id": "simulation",
            "title": "交互仿真",
            "content": ["仿真描述要点"],
            "order": 4
        }},
        {{
            "id": "summary",
            "title": "总结",
            "content": ["要点1", "要点2"],
            "order": 5
        }},
        {{
            "id": "exercises",
            "title": "习题与答案",
            "content": ["习题1描述", "习题2描述"],
            "order": 6
        }}
    ]
}}

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
        
        prompt = f"""请为以下章节生成详细的教学 HTML 内容。

课程：{course}
知识点：{knowledge_point}
章节：{section_title}
要点：
{key_points_str}

HTML 结构要求（必须严格遵守）：
1. 最外层使用 <div class="section-content">
2. 章节主标题使用 <h3>{section_title}</h3>（只使用一次）
3. 小节标题使用 <h4>（如需要）
4. 段落使用 <p>，重要概念用 <strong> 加粗
5. 列表使用 <ul><li> 或 <ol><li>
6. 公式使用 $...$ 行内或 $$...$$ 块级（不要用 \( \) 或 \[ \]）
7. 提示信息使用 <div class="tip">...</div>
8. 警告信息使用 <div class="warning">...</div>
9. 不要包含 html/head/body 标签
10. 不要嵌套 <main>、<section> 等结构性标签

示例结构：
<div class="section-content">
  <h3>{section_title}</h3>
  <p>段落内容...</p>
  <h4>小节标题</h4>
  <p>段落内容，<strong>重要概念</strong>...</p>
  <ul>
    <li>列表项1</li>
    <li>列表项2</li>
  </ul>
  <div class="tip">提示信息...</div>
</div>

请直接返回 HTML 内容。"""

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
        """规范化 HTML 结构，确保统一格式"""
        import re
        
        html = html.strip()
        
        # 如果已经有 section-content 包装，检查内部结构
        if html.startswith('<div class="section-content">'):
            # 检查是否有 h3 标题
            if f'<h3>{section_title}</h3>' not in html and f'<h3>' not in html:
                # 在开头添加 h3
                html = html.replace('<div class="section-content">', f'<div class="section-content">\n  <h3>{section_title}</h3>')
            return html
        
        # 如果没有 section-content 包装，添加包装
        # 移除可能存在的结构性标签
        html = re.sub(r'</?(main|section|article|aside|header|footer)[^>]*>', '', html, flags=re.IGNORECASE)
        
        # 检查是否已有 h3
        has_h3 = f'<h3>{section_title}</h3>' in html or '<h3>' in html
        
        if not has_h3:
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
        prompt = f"""请为以下知识点生成可交互的 HTML5 Canvas 仿真代码。

课程：{course}
知识点：{knowledge_point}
仿真需求：{simulation_desc}

要求：
1. 使用原生 HTML5 Canvas API（不使用外部库）
2. 提供可调节的参数（滑块或按钮），使用美观的样式
3. 实时显示计算结果，使用彩色图表
4. 包含动画效果，使用 requestAnimationFrame
5. 代码完整，可直接运行
6. 返回完整的 HTML 代码（包含 canvas 和 script）
7. 添加说明文字解释如何使用仿真

请返回完整的 HTML 代码。"""

        messages = [
            {"role": "system", "content": "你是一个专业的物理仿真开发者，擅长使用 HTML5 Canvas 创建交互式教学演示。"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self._call_kimi(messages, temperature=0.8)
            cleaned = self._clean_markdown_code_blocks(response)
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
