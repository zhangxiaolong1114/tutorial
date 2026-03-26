"""
AI 服务封装（重构版）
基于模型路由系统，支持多模型配置和动态选择
"""
import json
import logging
import re
from typing import Dict, Any, Optional, Tuple

from app.core.config import get_settings
from app.core.model_router import (
    model_router, model_registry, GenerationTask, TaskModelConfig
)
from app.core.model_callers import init_model_api_keys
from app.core.prompt_templates import (
    build_outline_prompt,
    build_section_prompt,
    build_simulation_prompt,
)
from app.core.simulation_prompts import (
    build_simulation_prompt_lite,
    build_simulation_prompt_structure,
    build_simulation_prompt_logic,
)

logger = logging.getLogger(__name__)
settings = get_settings()


class ContentValidator:
    """内容完整性验证器（保持不变）"""
    
    @staticmethod
    def _normalize_text(text: str) -> str:
        """标准化文本用于比较（移除空白、转为小写）"""
        return re.sub(r'\s+', '', text.lower().strip())
    
    @staticmethod
    def calculate_similarity(text1: str, text2: str) -> float:
        """计算两段文本的相似度（0-1）"""
        if not text1 or not text2:
            return 0.0
        
        norm1 = ContentValidator._normalize_text(text1)
        norm2 = ContentValidator._normalize_text(text2)
        
        if not norm1 or not norm2:
            return 0.0
        
        len_ratio = min(len(norm1), len(norm2)) / max(len(norm1), len(norm2))
        if len_ratio < 0.5:
            return len_ratio
        
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
        
        tags_to_check = [
            ('<div class="section-content">', '</div>'),
            ('<script>', '</script>'),
        ]
        
        for open_tag, close_tag in tags_to_check:
            open_count = content.count(open_tag)
            close_count = content.count(close_tag)
            if open_count != close_count:
                return False, f"标签不匹配: {open_tag}"
        
        if "(function()" in content and not content.rstrip().endswith("})();"):
            if "<script>" in content:
                return False, "JavaScript IIFE 未正确闭合"
        
        return True, "HTML 结构完整"
    
    @staticmethod
    def check_section_complete(content: str) -> Tuple[bool, str]:
        """检查章节 HTML 是否完整"""
        if '<div class="section-content">' not in content:
            has_heading = '<h3>' in content or '<h4>' in content
            has_paragraph = '<p>' in content
            has_formula = '$' in content
            
            if not (has_heading or has_paragraph or has_formula):
                return False, "内容缺少基本结构"
        
        script_open = content.count('<script>')
        script_close = content.count('</script>')
        if script_open != script_close:
            return False, "script 标签不匹配"
        
        dollar_count = content.count('$')
        if dollar_count % 2 != 0:
            return False, "公式分隔符 $ 数量不匹配"
        
        return True, "章节内容结构完整"
    
    @staticmethod
    def check_simulation_complete(content: str) -> Tuple[bool, str]:
        """检查仿真代码是否完整"""
        import re
        
        # 检查 simulation-container
        open_count = len(re.findall(r'<div[^>]*class=["\'][^"\']*simulation-container[^"\']*["\'][^>]*>', content, re.IGNORECASE))
        if open_count == 0:
            return False, "缺少 simulation-container 容器"
        
        # 检查 script 标签
        script_open = content.lower().count('<script>')
        script_close = content.lower().count('</script>')
        if script_open != script_close:
            return False, f"script 标签不匹配"
        
        # 检查 IIFE 闭合
        if "(function()" in content or "(function ()" in content:
            if not re.search(r'\}\)\(\);\s*</script>', content, re.DOTALL):
                return False, "JavaScript IIFE 未正确闭合"
        
        # 检查 Canvas
        has_canvas = "<canvas" in content.lower()
        has_2d_context = "getContext('2d')" in content or 'getContext("2d")' in content
        if has_canvas and not has_2d_context:
            return False, "Canvas 初始化代码不完整"
        
        # 检查关键帧数据
        if "keyFrames" in content or "keyframes" in content.lower():
            keyframe_pattern = r'keyFrames\s*=\s*\{([^}]+)\}'
            match = re.search(keyframe_pattern, content, re.DOTALL)
            if match:
                keyframe_content = match.group(1)
                frame_count = len(re.findall(r'\d+\s*:', keyframe_content))
                if frame_count < 5:
                    return False, f"关键帧数据不完整：只定义了 {frame_count} 帧"
        
        # 检查省略性注释
        forbidden_patterns = [
            r'此处省略.*代码',
            r'根据实际.*实现',
            r'添加更多.*数据',
            r'//\s*\.\.\.',
            r'/\*\s*\.\.\.\s*\*/',
        ]
        for pattern in forbidden_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return False, f"发现省略性注释"
        
        return True, "仿真代码完整"


class AIService:
    """
    AI 服务统一封装（重构版）
    基于模型路由系统，支持用户自定义模型配置
    """
    
    def __init__(self):
        self.validator = ContentValidator()
        self._init_api_keys()
    
    def _init_api_keys(self):
        """从配置初始化 API Keys"""
        api_keys = {
            "kimi": settings.KIMI_API_KEY,
            "claude": getattr(settings, 'CLAUDE_API_KEY', ''),
        }
        
        # 从配置加载其他模型的 API Keys（如果有）
        for model_id in ["deepseek", "qwen", "glm", "openai"]:
            key = getattr(settings, f'{model_id.upper()}_API_KEY', '')
            if key:
                api_keys[model_id] = key
        
        # 加载自定义 Base URL
        for model_id in ["deepseek", "qwen", "glm", "claude"]:
            base_url = getattr(settings, f'{model_id.upper()}_BASE_URL', '')
            if base_url:
                model_registry.update_base_url(f"{model_id}-v3" if model_id == "deepseek" else f"{model_id}-coder", base_url)
        
        init_model_api_keys(api_keys)
        logger.info("[AIService] API Keys 初始化完成")
    
    # ============ 对外接口 ============
    
    def generate_outline(
        self,
        course: str,
        knowledge_point: str,
        config: dict,
        task_id: str = "unknown",
        model_id: Optional[str] = None,
        task_config: Optional[TaskModelConfig] = None,
    ) -> dict:
        """
        生成大纲
        
        Args:
            model_id: 指定模型ID（优先级最高）
            task_config: 任务级别的模型配置
        """
        logger.info(f"[AI Service] Task {task_id} - 开始生成大纲: {course} - {knowledge_point}")
        
        prompt = build_outline_prompt(course, knowledge_point, config)
        
        messages = [
            {"role": "system", "content": "你是一个专业的教育内容设计师，擅长生成结构化的教学大纲。严格遵守输出格式要求。"},
            {"role": "user", "content": prompt}
        ]
        
        logger.info(f"[AI Service] Task {task_id} - 调用模型生成大纲")
        content, log_file = model_router.route(
            task=GenerationTask.OUTLINE,
            messages=messages,
            model_id=model_id,
            task_config=task_config,
            task_id=task_id,
        )
        logger.info(f"[AI Service] Task {task_id} - 大纲生成完成，日志: {log_file}")
        
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
    
    def generate_section(
        self,
        section_title: str,
        section_key_points: list,
        course: str,
        knowledge_point: str,
        config: dict,
        task_id: str = "unknown",
        model_id: Optional[str] = None,
        task_config: Optional[TaskModelConfig] = None,
        context: dict = None,
    ) -> str:
        """生成章节内容"""
        logger.info(f"[AI Service] Task {task_id} - 开始生成章节: {section_title}")
        
        prompt = build_section_prompt(section_title, section_key_points, course, knowledge_point, config, context)
        
        messages = [
            {"role": "system", "content": "你是教育内容专家，生成统一结构的高质量HTML教学内容。注意与前后章节保持连贯性。"},
            {"role": "user", "content": prompt}
        ]
        
        logger.info(f"[AI Service] Task {task_id} - 调用模型生成章节")
        content, log_file = model_router.route(
            task=GenerationTask.SECTION,
            messages=messages,
            model_id=model_id,
            task_config=task_config,
            task_id=task_id,
        )
        logger.info(f"[AI Service] Task {task_id} - 章节生成完成，日志: {log_file}")
        
        # 后处理
        content = self._clean_markdown_code_blocks(content)
        content = self._normalize_html_structure(content, section_title)
        content = self._convert_math_delimiters(content)
        
        return content
    
    def generate_simulation(
        self,
        simulation_desc: str,
        course: str,
        knowledge_point: str,
        simulation_types: list,
        config: dict,
        task_id: str = "unknown",
        model_id: Optional[str] = None,
        task_config: Optional[TaskModelConfig] = None,
        context: dict = None,
        use_chunked: bool = True,
    ) -> str:
        """
        生成交互仿真代码
        
        Args:
            use_chunked: 是否使用分块生成（默认True，更快更稳定）
        """
        if use_chunked:
            return self._generate_simulation_chunked(
                simulation_desc, course, knowledge_point, 
                simulation_types, config, task_id, model_id, task_config, context
            )
        else:
            return self._generate_simulation_full(
                simulation_desc, course, knowledge_point,
                simulation_types, config, task_id, model_id, task_config, context
            )
    
    def _generate_simulation_chunked(
        self,
        simulation_desc: str,
        course: str,
        knowledge_point: str,
        simulation_types: list,
        config: dict,
        task_id: str,
        model_id: Optional[str],
        task_config: Optional[TaskModelConfig],
        context: dict,
    ) -> str:
        """
        分块生成仿真（两阶段）
        
        阶段1：生成结构和样式（JSON，轻量）
        阶段2：生成物理计算和渲染逻辑（JS，核心）
        
        优点：
        - 单次请求token少，响应快
        - 任一阶段失败可重试，不浪费之前结果
        - 总时间通常比单次长请求更短
        """
        logger.info(f"[Simulation] Task {task_id} - 使用分块生成模式")
        
        # ===== 阶段1：生成结构和样式 =====
        logger.info(f"[Simulation] Task {task_id} - 阶段1：生成结构")
        
        structure_prompt = build_simulation_prompt_structure(
            simulation_desc, course, knowledge_point, context
        )
        
        structure_messages = [
            {"role": "system", "content": "你是仿真界面设计师，输出简洁的JSON配置。"},
            {"role": "user", "content": structure_prompt}
        ]
        
        try:
            structure_content, _ = model_router.route(
                task=GenerationTask.SIMULATION,
                messages=structure_messages,
                model_id=model_id,
                task_config=task_config,
                task_id=f"{task_id}_struct",
            )
            
            # 解析 JSON
            structure_json = self._extract_json(structure_content)
            if not structure_json:
                raise ValueError("无法解析结构JSON")
            
            logger.info(f"[Simulation] Task {task_id} - 结构生成完成: {structure_json.get('title', 'unknown')}")
            
        except Exception as e:
            logger.error(f"[Simulation] Task {task_id} - 阶段1失败: {e}")
            # 降级为完整生成
            logger.info(f"[Simulation] Task {task_id} - 降级为完整生成")
            return self._generate_simulation_full(
                simulation_desc, course, knowledge_point,
                simulation_types, config, task_id, model_id, task_config, context
            )
        
        # ===== 阶段2：生成逻辑代码 =====
        logger.info(f"[Simulation] Task {task_id} - 阶段2：生成逻辑代码")
        logger.info(f"[Simulation] Task {task_id} - 使用模型: {model_id or 'default'}, task_config: {task_config}")
        
        try:
            logic_prompt = build_simulation_prompt_logic(
                simulation_desc, course, knowledge_point, 
                simulation_types, structure_json, context
            )
            logger.info(f"[Simulation] Task {task_id} - 逻辑Prompt生成完成，长度: {len(logic_prompt)}")
        except Exception as e:
            logger.error(f"[Simulation] Task {task_id} - 生成逻辑Prompt失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
        
        logic_messages = [
            {"role": "system", "content": "你是仿真代码专家，编写完整可运行的JavaScript。"},
            {"role": "user", "content": logic_prompt}
        ]
        
        try:
            logger.info(f"[Simulation] Task {task_id} - 调用模型生成逻辑代码")
            logger.info(f"[Simulation] Task {task_id} - 消息数: {len(logic_messages)}, 任务类型: SIMULATION")
            logic_content, logic_log_file = model_router.route(
                task=GenerationTask.SIMULATION,
                messages=logic_messages,
                model_id=model_id,
                task_config=task_config,
                task_id=f"{task_id}_logic",
            )
            logger.info(f"[Simulation] Task {task_id} - model_router.route 返回成功")
            
            logger.info(f"[Simulation] Task {task_id} - 逻辑代码生成成功，日志: {logic_log_file}")
            
            # 提取 JavaScript
            js_code = self._extract_javascript(logic_content)
            
            if not js_code or len(js_code) < 100:
                logger.warning(f"[Simulation] Task {task_id} - 提取的JS代码过短，可能不完整")
            else:
                logger.info(f"[Simulation] Task {task_id} - 逻辑生成完成，JS代码长度: {len(js_code)}")
            
        except Exception as e:
            logger.error(f"[Simulation] Task {task_id} - 阶段2失败: {e}")
            # 阶段2失败，阶段1结果可缓存复用
            raise
        
        # ===== 拼接完整仿真 =====
        try:
            simulation_html = self._assemble_simulation(structure_json, js_code)
            logger.info(f"[Simulation] Task {task_id} - 分块生成完成，HTML长度: {len(simulation_html)}")
            
            # 验证生成的HTML是否完整
            if '<div class="simulation-container">' not in simulation_html:
                logger.error(f"[Simulation] Task {task_id} - 生成的HTML缺少simulation-container")
                raise ValueError("生成的仿真HTML结构不完整")
            
            if '<script>' not in simulation_html or len(js_code) < 50:
                logger.error(f"[Simulation] Task {task_id} - 生成的HTML缺少脚本或脚本过短")
                raise ValueError("生成的仿真脚本不完整")
            
            return simulation_html
        except Exception as e:
            logger.error(f"[Simulation] Task {task_id} - 拼接仿真失败: {e}")
            raise
    
    def _generate_simulation_full(
        self,
        simulation_desc: str,
        course: str,
        knowledge_point: str,
        simulation_types: list,
        config: dict,
        task_id: str,
        model_id: Optional[str],
        task_config: Optional[TaskModelConfig],
        context: dict,
    ) -> str:
        """完整生成（备用方案）- 使用精简Prompt"""
        logger.info(f"[Simulation] Task {task_id} - 使用完整生成模式")
        
        prompt = build_simulation_prompt_lite(
            simulation_desc, course, knowledge_point, 
            simulation_types, config, context
        )
        
        messages = [
            {"role": "system", "content": "你是仿真代码专家，编写完整可运行的HTML5 Canvas仿真。"},
            {"role": "user", "content": prompt}
        ]
        
        content, _ = model_router.route(
            task=GenerationTask.SIMULATION,
            messages=messages,
            model_id=model_id,
            task_config=task_config,
            task_id=task_id,
        )
        
        # 后处理
        content = self._clean_markdown_code_blocks(content)
        content = self._extract_simulation_content(content)
        
        return content
    
    def _extract_json(self, text: str) -> Optional[dict]:
        """从文本中提取JSON"""
        import json
        
        # 尝试直接解析
        try:
            return json.loads(text.strip())
        except:
            pass
        
        # 查找代码块中的JSON
        import re
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
        if json_match:
            try:
                return json.loads(json_match.group(1).strip())
            except:
                pass
        
        # 查找花括号包裹的内容
        brace_match = re.search(r'\{[\s\S]*\}', text)
        if brace_match:
            try:
                return json.loads(brace_match.group(0))
            except:
                pass
        
        return None
    
    def _extract_javascript(self, text: str) -> str:
        """从文本中提取JavaScript代码"""
        import re
        
        # 查找代码块
        js_match = re.search(r'```(?:javascript|js)?\s*([\s\S]*?)\s*```', text)
        if js_match:
            return js_match.group(1).strip()
        
        # 如果没有代码块标记，返回清理后的文本
        return text.strip()
    
    def _assemble_simulation(self, structure: dict, js_code: str) -> str:
        """拼接结构和逻辑生成完整仿真"""
        
        # 构建数据面板HTML
        data_metrics_html = ""
        for metric in structure.get("data_metrics", []):
            unit = metric.get("unit", "")
            unit_html = f'<span class="unit">{unit}</span>' if unit else ""
            data_metrics_html += f'''
    <div class="metric">
      <span class="label">{metric.get("label", "")}:</span>
      <span class="value" id="{metric.get("id", "")}">0</span>{unit_html}
    </div>'''
        
        # 构建控件HTML
        controls_html = ""
        slider_ids = []
        button_ids = []
        for ctrl in structure.get("controls", []):
            ctrl_id = ctrl.get("id", "")
            if ctrl.get("type") == "slider":
                slider_ids.append(ctrl_id)
                display_id = ctrl_id.replace("Slider", "Display").replace("slider", "Display")
                controls_html += f'''
    <label>{ctrl.get("label", "")}: <span id="{display_id}">{ctrl.get("value", 0)}</span></label>
    <input type="range" id="{ctrl_id}" min="{ctrl.get("min", 0)}" max="{ctrl.get("max", 100)}" step="{ctrl.get("step", 1)}" value="{ctrl.get("value", 0)}">'''
            elif ctrl.get("type") == "button":
                button_ids.append(ctrl_id)
                controls_html += f'''
    <button id="{ctrl_id}">{ctrl.get("label", "")}</button>'''
        
        # 生成控件ID列表用于JS引用检查
        all_control_ids = slider_ids + button_ids
        control_ids_js = ", ".join([f'"{cid}"' for cid in all_control_ids])
        
        # 组装完整HTML，添加错误处理和控件引用
        html = f'''<div class="simulation-container">
  <div class="title-desc">
    <h2>{structure.get("title", "仿真")}</h2>
    <p>{structure.get("description", "")}</p>
  </div>
  
  <div class="data-panel">{data_metrics_html}
  </div>
  
  <canvas id="simCanvas" width="700" height="480"></canvas>
  
  <div class="control-panel">{controls_html}
  </div>
  
  <style>
{structure.get("css", "")}
  </style>
  
  <script>
(function() {{
  'use strict';
  
  // 错误处理
  window.onerror = function(msg, url, line) {{
    console.error('[Simulation Error]', msg, 'at line', line);
    return true;
  }};
  
  // 获取Canvas
  const canvas = document.getElementById('simCanvas');
  if (!canvas) {{
    console.error('Canvas not found');
    return;
  }}
  const ctx = canvas.getContext('2d');
  
  // 获取控件引用
  const controls = {{}};
  [{control_ids_js}].forEach(function(id) {{
    const el = document.getElementById(id);
    if (el) controls[id] = el;
    else console.warn('Control not found:', id);
  }});
  
  // 用户代码开始
{js_code}
  // 用户代码结束
}})();
  </script>
</div>'''
        
        return html
    
    def get_available_models(self, task_type: Optional[str] = None) -> list:
        """获取可用模型列表"""
        if task_type:
            task = GenerationTask(task_type)
            return model_router.get_available_models(task)
        return model_router.get_available_models()
    
    def get_model_recommendations(self, task_type: str) -> list:
        """获取模型推荐列表"""
        from app.core.model_callers import get_model_recommendations
        task = GenerationTask(task_type)
        return get_model_recommendations(task)
    
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
        
        start_match = re.search(r'<div class="simulation-container"[^>]*>', html, re.IGNORECASE)
        if start_match:
            start_pos = start_match.start()
            pos = start_match.end()
            depth = 1
            
            while pos < len(html) and depth > 0:
                next_open = html.find('<div', pos)
                next_close = html.find('</div>', pos)
                
                if next_open == -1 and next_close == -1:
                    break
                
                if next_open != -1 and (next_close == -1 or next_open < next_close):
                    tag_end = html.find('>', next_open)
                    if tag_end != -1:
                        tag_content = html[next_open:tag_end+1]
                        if not tag_content.rstrip().endswith('/>'):
                            depth += 1
                        pos = tag_end + 1
                    else:
                        break
                else:
                    depth -= 1
                    pos = next_close + 6
                    
                    if depth == 0:
                        container_content = html[start_pos:pos]
                        remaining = html[pos:].strip()
                        
                        script_match = re.search(r'<script>.*?</script>', remaining, re.DOTALL | re.IGNORECASE)
                        style_match = re.search(r'<style>.*?</style>', remaining, re.DOTALL | re.IGNORECASE)
                        
                        if script_match or style_match:
                            container_without_close = container_content[:-6]
                            additional_content = ""
                            if style_match:
                                additional_content += style_match.group(0)
                            if script_match:
                                additional_content += script_match.group(0)
                            return container_without_close + additional_content + "</div>"
                        
                        return container_content
        
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
        
        # 转换 \( ... \) 为 $ ... $
        html = re.sub(r'\\\((.*?)\\\)', r'$\1$', html, flags=re.DOTALL)
        # 转换 \[ ... \] 为 $$ ... $$
        html = re.sub(r'\\\[(.*?)\\\]', r'$$\1$$', html, flags=re.DOTALL)
        
        # 注意：不再自动替换双反斜杠，让 KaTeX 自己处理
        # 过度转义会导致 KaTeX 解析错误
        
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

    def _fix_math_formulas(self, html: str) -> str:
        """
        修复公式中的常见问题
        
        问题：
        1. AI 生成的公式可能包含未转义的特殊字符
        2. 某些 KaTeX 命令可能需要特殊处理
        """
        import re
        
        # 修复常见的公式问题
        fixes = [
            # 修复双反斜杠问题
            (r'\\\\(frac|dot|sum|int|alpha|beta|gamma|delta|theta|omega|pi|sigma|zeta)', r'\\\1'),
            # 修复连续的反斜杠
            (r'\\\\\\', r'\\\\'),
        ]
        
        for pattern, replacement in fixes:
            html = re.sub(pattern, replacement, html)
        
        return html
    
    def generate_complete_html(self, title: str, body_content: str) -> str:
        """生成完整的 HTML 文档（包含样式和 KaTeX）"""
        # 在生成最终 HTML 前修复公式
        body_content = self._fix_math_formulas(body_content)
        
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="https://cdn.bootcdn.net/ajax/libs/KaTeX/0.16.9/katex.min.css">
    <script defer src="https://cdn.bootcdn.net/ajax/libs/KaTeX/0.16.9/katex.min.js"></script>
    <script defer src="https://cdn.bootcdn.net/ajax/libs/KaTeX/0.16.9/contrib/auto-render.min.js"></script>
    <script>
        document.addEventListener("DOMContentLoaded", function() {{
            function renderMath() {{
                if (typeof renderMathInElement !== 'undefined') {{
                    try {{
                        renderMathInElement(document.body, {{
                            delimiters: [
                                {{left: '$$$$', right: '$$$$', display: true}},
                                {{left: '$$', right: '$$', display: true}},
                                {{left: '$', right: '$', display: false}},
                                {{left: '\\[', right: '\\]', display: true}},
                                {{left: '\\(', right: '\\)', display: false}}
                            ],
                            throwOnError: false,
                            strict: false,
                            trust: true,
                            errorColor: '#dc2626',
                            minRuleThickness: 0.05,
                            maxExpand: 1000,
                            macros: {{
                                "\\vec": "\\mathbf",
                                "\\R": "\\mathbb{{R}}",
                                "\\C": "\\mathbb{{C}}"
                            }},
                            // 添加错误处理
                            errorCallback: function(msg, err) {{
                                console.warn('[KaTeX] 渲染警告:', msg);
                            }}
                        }});
                        console.log('[KaTeX] 公式渲染完成');
                    }} catch (e) {{
                        console.error('[KaTeX] 渲染错误:', e);
                    }}
                }} else {{
                    console.error('[KaTeX] 库未加载');
                }}
            }}
            // 延迟渲染，确保库已加载
            if (document.readyState === 'loading') {{
                document.addEventListener('DOMContentLoaded', function() {{ setTimeout(renderMath, 500); }});
            }} else {{
                setTimeout(renderMath, 500);
            }}
        }});
    </script>
    <style>
        :root {{
            --primary-color: #3b82f6;
            --secondary-color: #8b5cf6;
            --bg-color: #f8fafc;
            --card-bg: #ffffff;
            --text-primary: #1e293b;
            --text-secondary: #64748b;
            --border-color: #e2e8f0;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
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
        .header h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
        .content {{ padding: 40px; }}
        section {{
            margin-bottom: 40px;
            padding: 30px;
            background: var(--bg-color);
            border-radius: 12px;
            border-left: 5px solid var(--primary-color);
        }}
        h2 {{ color: var(--text-primary); font-size: 1.8em; margin-bottom: 20px; }}
        h3 {{ color: var(--primary-color); font-size: 1.4em; margin: 25px 0 15px; }}
        p {{ color: var(--text-primary); margin-bottom: 15px; }}
        canvas {{
            display: block;
            max-width: 100%;
            margin: 20px auto;
            border: 3px solid var(--primary-color);
            border-radius: 12px;
            background: white;
        }}
        button {{
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1em;
            margin: 5px;
        }}
        .footer {{
            background: var(--bg-color);
            padding: 20px;
            text-align: center;
            color: var(--text-secondary);
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header"><h1>{title}</h1></div>
        <div class="content">{body_content}</div>
        <div class="footer">由 智教云 AI 教学平台生成</div>
    </div>
</body>
</html>"""


# 全局 AI 服务实例
ai_service = AIService()
