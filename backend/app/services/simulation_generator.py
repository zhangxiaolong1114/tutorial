"""
仿真代码生成 - 新版实现（流式接收 + 续生成 + 需求优先）
"""
import json
import logging
import re
import time
from typing import Dict, List, Optional, Tuple, Any

from app.core.model_router import (
    model_router, GenerationTask, TaskModelConfig
)
from app.core.model_callers import response_logger
from app.core.rate_limiter import token_rate_limiter

logger = logging.getLogger(__name__)


class SimulationGenerationError(Exception):
    """仿真生成错误"""
    def __init__(self, message: str, outline_requirement: str = None, 
                 course: str = None, knowledge_point: str = None,
                 section_title: str = None):
        super().__init__(message)
        self.outline_requirement = outline_requirement
        self.course = course
        self.knowledge_point = knowledge_point
        self.section_title = section_title
    
    def to_dict(self) -> dict:
        return {
            "error": str(self),
            "outline_requirement": self.outline_requirement,
            "course": self.course,
            "knowledge_point": self.knowledge_point,
            "section_title": self.section_title
        }


def build_simulation_prompt_v2(context: dict) -> str:
    """
    构建仿真生成Prompt（V2版本 - 需求优先）
    
    优先级：仿真需求 > 核心公式
    """
    course = context.get('course', '')
    knowledge_point = context.get('knowledge_point', '')
    description = context.get('description', '')
    core_formulas = context.get('core_formulas', [])
    prerequisites = context.get('prerequisites', [])
    prepares_for = context.get('prepares_for', [])
    prev_section = context.get('prev_section_title', '')
    next_section = context.get('next_section_title', '')
    
    # 格式化公式
    formulas_str = "\n".join([f"- {f}" for f in core_formulas]) if core_formulas else "根据物理原理自行推导"
    
    # 格式化前置依赖
    prereq_str = "\n".join([f"- {p}" for p in prerequisites]) if prerequisites else "无特殊要求"
    
    # 格式化后续铺垫
    prepares_str = "\n".join([f"- {p}" for p in prepares_for]) if prepares_for else "无"
    
    return f"""【任务】为《{course}》的「{knowledge_point}」生成交互式仿真代码

【仿真需求】（用户确认，必须严格实现）
{description}

【前置知识】（仿真基于这些概念）
{prereq_str}

【为后文铺垫】（这些概念将在后续章节展开）
{prepares_str}

【核心公式】（参考实现，如与需求冲突以需求为准）
{formulas_str}

【章节位置】
- 前一章：{prev_section or "无"}
- 后一章：{next_section or "无"}

【输出要求】
1. 完整HTML代码，所有内容包含在 `<div class="simulation-container">` 内
2. 使用原生Canvas，尺寸 700x480px
3. 2-4个可调参数（滑块），使用 oninput 事件实现实时响应
4. 数据面板显示关键物理量的实时数值
5. 物理计算必须准确实现【仿真需求】中的描述
6. 代码完整可运行，无占位符，无"省略"注释

【代码结构模板】
```html
<div class="simulation-container">
  <!-- 标题和描述 -->
  <div class="sim-header">
    <h3>仿真标题</h3>
    <p>简短描述仿真目的</p>
  </div>
  
  <!-- 数据面板：显示关键物理量 -->
  <div class="data-panel">
    <span>物理量1: <span id="value1">0.00</span> 单位</span>
    <span>物理量2: <span id="value2">0.00</span> 单位</span>
  </div>
  
  <!-- Canvas画布 -->
  <canvas id="simCanvas" width="700" height="480"></canvas>
  
  <!-- 控制面板：滑块和按钮 -->
  <div class="control-panel">
    <label>参数1: <input type="range" id="param1Slider" min="0" max="100" value="50"></label>
    <label>参数2: <input type="range" id="param2Slider" min="0" max="100" value="50"></label>
  </div>
  
  <style>
    /* 简洁美观的样式 */
    .simulation-container {{
      border: 2px solid #333;
      padding: 15px;
      background: #f9f9f9;
    }}
    /* 其他样式... */
  </style>
  
  <script>
    (function() {{
      'use strict';
      
      // 获取Canvas和上下文
      const canvas = document.getElementById('simCanvas');
      const ctx = canvas.getContext('2d');
      
      // 获取控件引用
      const param1Slider = document.getElementById('param1Slider');
      const param2Slider = document.getElementById('param2Slider');
      const value1Display = document.getElementById('value1');
      const value2Display = document.getElementById('value2');
      
      // 物理计算函数（基于核心公式）
      function calculatePhysics(param1, param2) {{
        // 实现物理计算
        // 返回计算结果对象
      }}
      
      // 绘制函数
      function draw(state) {{
        // 清空画布
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        // 绘制坐标轴、网格
        // 绘制物理现象
        // 标注关键点
      }}
      
      // 更新显示
      function update() {{
        const param1 = parseFloat(param1Slider.value);
        const param2 = parseFloat(param2Slider.value);
        const state = calculatePhysics(param1, param2);
        
        // 更新数据面板
        value1Display.textContent = state.value1.toFixed(2);
        value2Display.textContent = state.value2.toFixed(2);
        
        // 绘制
        draw(state);
      }}
      
      // 事件绑定（使用oninput实现实时响应）
      param1Slider.oninput = update;
      param2Slider.oninput = update;
      
      // 初始化
      update();
    }})();
  </script>
</div>
```

【自检清单】
生成完成后请确认：
- [ ] 仿真功能完全符合【仿真需求】的描述
- [ ] 所有滑块使用 oninput 事件实现实时响应
- [ ] 数据面板正确显示物理量的实时数值
- [ ] 物理计算准确（如有公式，必须正确实现）
- [ ] Canvas尺寸为700x480px
- [ ] 代码完整可运行，无占位符
- [ ] 所有内容都在 simulation-container 内

请直接输出完整HTML代码，不要其他说明。"""


def build_continue_prompt(existing_content: str) -> str:
    """构建续生成Prompt"""
    # 取最后1000字符作为上下文
    last_part = existing_content[-1000:] if len(existing_content) > 1000 else existing_content
    
    return f"""请继续生成仿真代码，从以下位置继续（不要重复已生成内容）：

...{last_part}

【续写要求】
- 从上次中断处继续生成
- 保持代码格式和变量名一致
- 不要重复已生成的内容
- 直接输出代码，不要解释
- 确保代码最终完整闭合（所有标签、括号、函数都正确结束）

请继续："""


def simple_validate_simulation(html: str) -> Tuple[bool, List[str]]:
    """
    简单验证仿真代码完整性
    
    Returns:
        (是否通过, 错误列表)
    """
    errors = []
    
    # 基本结构检查
    if '<div class="simulation-container"' not in html:
        errors.append("缺少 simulation-container")
    
    if '<canvas' not in html:
        errors.append("缺少 canvas 元素")
    
    if '<script>' not in html:
        errors.append("缺少 script 标签")
    
    # 标签平衡检查
    if html.count('<script') != html.count('</script>'):
        errors.append("script 标签不平衡")
    
    if html.count('<div') != html.count('</div>'):
        errors.append("div 标签不平衡")
    
    # 检查是否有省略性内容
    if '...' in html[-200:] or '此处省略' in html or '省略' in html[-200:]:
        errors.append("内容可能被截断或省略")
    
    # 检查关键元素
    if 'oninput' not in html and 'onchange' not in html:
        errors.append("缺少事件绑定（oninput/onchange）")
    
    if 'getElementById' not in html:
        errors.append("缺少 DOM 元素获取")
    
    if 'getContext' not in html:
        errors.append("缺少 Canvas 上下文获取")
    
    return len(errors) == 0, errors


def has_basic_structure(html: str) -> bool:
    """检查是否已生成基本可用结构（用于流式接收时判断）"""
    return (
        '<div class="simulation-container"' in html and
        '<canvas' in html and
        '<script>' in html and
        html.count('<script') == html.count('</script>')
    )


class SimulationGenerator:
    """仿真代码生成器（流式接收 + 续生成）"""
    
    def __init__(self):
        self.max_retries = 3  # 失败重试次数
        self.max_continues = 5  # max_tokens导致的续生成次数
        self.timeout = 180  # 单次请求超时时间
    
    def generate(
        self,
        context: dict,
        model_id: Optional[str] = None,
        task_config: Optional[TaskModelConfig] = None,
        task_id: str = "unknown"
    ) -> dict:
        """
        生成仿真代码
        
        Returns:
            {
                "success": True/False,
                "content": "生成的HTML代码",  # success=True时
                "error": "错误信息",  # success=False时
                "outline_requirement": "...",  # success=False时
                "attempts": 3,  # 尝试次数
                "continues": 2  # 续生成次数
            }
        """
        course = context.get('course', '')
        knowledge_point = context.get('knowledge_point', '')
        section_title = context.get('section_title', '')
        description = context.get('description', '')
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"[Simulation] Task {task_id} - 第{attempt+1}次尝试生成")
                
                result = self._generate_single_attempt(
                    context=context,
                    model_id=model_id,
                    task_config=task_config,
                    task_id=f"{task_id}_attempt{attempt+1}"
                )
                
                content = result["content"]
                continues = result["continues"]
                
                # 验证
                is_valid, errors = simple_validate_simulation(content)
                
                if is_valid:
                    logger.info(f"[Simulation] Task {task_id} - 生成成功，续生成{continues}次")
                    return {
                        "success": True,
                        "content": content,
                        "attempts": attempt + 1,
                        "continues": continues
                    }
                else:
                    logger.warning(f"[Simulation] Task {task_id} - 验证失败: {errors}")
                    if attempt < self.max_retries - 1:
                        logger.info(f"[Simulation] Task {task_id} - 准备重试")
                        continue
                    else:
                        # 最后一次尝试，返回失败
                        raise SimulationGenerationError(
                            message=f"验证失败: {', '.join(errors)}",
                            outline_requirement=description,
                            course=course,
                            knowledge_point=knowledge_point,
                            section_title=section_title
                        )
                
            except Exception as e:
                logger.error(f"[Simulation] Task {task_id} - 生成异常: {e}")
                if attempt < self.max_retries - 1:
                    continue
                else:
                    # 所有重试失败
                    if isinstance(e, SimulationGenerationError):
                        raise
                    else:
                        raise SimulationGenerationError(
                            message=f"生成失败: {str(e)}",
                            outline_requirement=description,
                            course=course,
                            knowledge_point=knowledge_point,
                            section_title=section_title
                        )
        
        # 不应该到达这里
        raise SimulationGenerationError(
            message="未知错误",
            outline_requirement=description,
            course=course,
            knowledge_point=knowledge_point,
            section_title=section_title
        )
    
    def _generate_single_attempt(
        self,
        context: dict,
        model_id: Optional[str],
        task_config: Optional[TaskModelConfig],
        task_id: str
    ) -> dict:
        """单次生成尝试（支持续生成）"""
        prompt = build_simulation_prompt_v2(context)
        
        messages = [
            {"role": "system", "content": "你是交互式物理仿真专家，编写完整、准确、可运行的HTML5 Canvas仿真代码。"},
            {"role": "user", "content": prompt}
        ]
        
        all_content = []
        total_continues = 0
        
        for continue_attempt in range(self.max_continues):
            if continue_attempt == 0:
                # 第一次生成
                current_messages = messages
                is_continuation = False
            else:
                # 续生成
                existing = "".join(all_content)
                current_messages = [
                    {"role": "system", "content": "你是交互式物理仿真专家，继续生成代码。"},
                    {"role": "user", "content": build_simulation_prompt_v2(context)},
                    {"role": "assistant", "content": existing},
                    {"role": "user", "content": build_continue_prompt(existing)}
                ]
                is_continuation = True
                total_continues += 1
            
            # 调用模型
            logger.info(f"[Simulation] Task {task_id} - 调用模型 (continuation={is_continuation})")
            
            try:
                content, log_file = model_router.route(
                    task=GenerationTask.SIMULATION,
                    messages=current_messages,
                    model_id=model_id,
                    task_config=task_config,
                    task_id=task_id,
                )
                
                all_content.append(content)
                
                # 检查 finish_reason（从日志或返回信息中获取）
                # 注意：当前 model_router 不返回 finish_reason，需要修改
                # 这里假设如果内容看起来完整就停止
                full_content = "".join(all_content)
                
                # 如果已经生成基本结构且看起来完整，停止
                if has_basic_structure(full_content):
                    # 进一步检查是否完整（有闭合标签）
                    if full_content.rstrip().endswith('</div>'):
                        logger.info(f"[Simulation] Task {task_id} - 内容完整，停止生成")
                        break
                
                # 如果内容很短，可能出错了，停止
                if len(content) < 100:
                    logger.warning(f"[Simulation] Task {task_id} - 生成内容过短，停止")
                    break
                
            except Exception as e:
                logger.error(f"[Simulation] Task {task_id} - 调用失败: {e}")
                raise
        
        return {
            "content": "".join(all_content),
            "continues": total_continues
        }


# 便捷函数
def generate_simulation_v2(
    context: dict,
    model_id: Optional[str] = None,
    task_config: Optional[TaskModelConfig] = None,
    task_id: str = "unknown"
) -> dict:
    """
    生成仿真代码（V2版本）
    
    Args:
        context: 包含仿真需求的上下文
        model_id: 指定模型ID
        task_config: 任务配置
        task_id: 任务ID
    
    Returns:
        {
            "success": True/False,
            "content": "生成的HTML代码" or None,
            "error": "错误信息" or None,
            "outline_requirement": "大纲需求" or None,
            "course": "课程" or None,
            "knowledge_point": "知识点" or None,
            "section_title": "章节标题" or None,
            "attempts": 尝试次数,
            "continues": 续生成次数
        }
    """
    generator = SimulationGenerator()
    
    try:
        result = generator.generate(
            context=context,
            model_id=model_id,
            task_config=task_config,
            task_id=task_id
        )
        return result
    except SimulationGenerationError as e:
        return {
            "success": False,
            "content": None,
            "error": str(e),
            **e.to_dict(),
            "attempts": generator.max_retries,
            "continues": 0
        }
