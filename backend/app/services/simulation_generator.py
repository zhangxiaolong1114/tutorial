"""
仿真代码生成 - 新版实现（流式接收 + 续生成 + 需求优先）
"""
import json
import logging
import os
import re
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

from app.core.model_router import (
    model_router, GenerationTask, TaskModelConfig
)
from app.core.model_callers import response_logger
from app.core.rate_limiter import token_rate_limiter

# 配置独立的仿真生成日志
sim_logger = logging.getLogger("simulation_generator")
sim_logger.setLevel(logging.DEBUG)

# 创建文件处理器
log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'simulation_generator.log')

# 使用追加模式，每天一个文件
file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
file_handler.setLevel(logging.DEBUG)

# 设置日志格式
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(formatter)

# 添加处理器到日志器
if not sim_logger.handlers:
    sim_logger.addHandler(file_handler)

# 保持原有的 logger 用于兼容
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
    构建仿真生成Prompt（V3版本 - 与普通章节生成保持一致）
    
    核心理念：
    1. 参照完整大纲上下文，保证连贯性
    2. 严格实现大纲中提及的所有仿真需求
    3. 生成可在iframe中直接运行的完整HTML+CSS+JS
    """
    course = context.get('course', '')
    knowledge_point = context.get('knowledge_point', '')
    section_title = context.get('section_title', '交互仿真')
    
    # 仿真需求（来自大纲）
    description = context.get('description', '')
    
    # 核心公式
    core_formulas = context.get('core_formulas', [])
    if isinstance(core_formulas, list) and core_formulas:
        # 处理可能是对象或字符串的情况
        formula_list = []
        for f in core_formulas:
            if isinstance(f, dict):
                formula_list.append(f.get('formula', str(f)))
            else:
                formula_list.append(str(f))
        formulas_str = "\n".join([f"- {f}" for f in formula_list])
    else:
        formulas_str = "根据物理原理自行推导"
    
    # 前置依赖
    prerequisites = context.get('prerequisites', [])
    prereq_str = "\n".join([f"- {p}" for p in prerequisites]) if prerequisites else "无特殊要求"
    
    # 后续铺垫
    prepares_for = context.get('prepares_for', [])
    prepares_str = "\n".join([f"- {p}" for p in prepares_for]) if prepares_for else "无"
    
    # 完整大纲信息
    full_outline = context.get('full_outline', [])
    current_index = context.get('current_index', 0)
    
    # 构建大纲结构描述
    outline_summary = []
    if full_outline:
        for i, sec in enumerate(full_outline, 1):
            marker = " <- 当前仿真章节" if i == current_index + 1 else ""
            outline_summary.append(f"{i}. {sec.get('title', '未命名')}{marker}")
    outline_summary_str = "\n".join(outline_summary) if outline_summary else "无大纲信息"
    
    # 前置章节内容（用于上下文连贯性）
    prev_sections_content = []
    if full_outline and current_index > 0:
        for idx in range(max(0, current_index - 2), current_index):
            sec = full_outline[idx]
            sec_title = sec.get('title', f'第{idx+1}章')
            sec_content = sec.get('content', [])
            if isinstance(sec_content, list) and sec_content:
                content_preview = sec_content[0][:100] + "..." if len(sec_content[0]) > 100 else sec_content[0]
                prev_sections_content.append(f"**{sec_title}**：{content_preview}")
    prev_sections_str = "\n".join(prev_sections_content) if prev_sections_content else "无前序章节"
    
    return f"""【任务】为《{course}》的「{knowledge_point}」生成交互式仿真代码

## 仿真需求（来自大纲，必须严格实现）
{description}

**重要**：以上仿真需求必须全部实现，不得遗漏或简化。

## 文档上下文（保证连贯性）

### 完整文档结构
{outline_summary_str}

### 前置章节内容（已讲解的理论基础）
{prev_sections_str}

### 本章关联信息
- **前置知识**（仿真基于这些已讲解的概念）：
{prereq_str}

- **为后文铺垫**（通过仿真加深对这些概念的理解）：
{prepares_str}

- **核心公式**（仿真中必须正确实现的公式）：
{formulas_str}

## 连贯性要求
- 仿真必须验证前置章节中讲解的理论
- 仿真中观察的现象必须与前述理论对应
- 保持术语和符号体系与前置章节完全一致
- 仿真参数调节的目的必须明确（验证什么理论）

## 输出要求
生成可在iframe中直接运行的完整HTML代码：

### 必需结构
```html
<div class="simulation-container">
  <!-- 1. 标题和描述 -->
  <div class="sim-header">
    <h3>仿真标题</h3>
    <p>简短描述仿真目的和验证的理论</p>
  </div>
  
  <!-- 2. 数据面板：实时显示关键物理量 -->
  <div class="data-panel">
    <span>物理量1: <span id="value1">0.00</span> 单位</span>
    <span>物理量2: <span id="value2">0.00</span> 单位</span>
  </div>
  
  <!-- 3. Canvas画布：700x480px -->
  <canvas id="simCanvas" width="700" height="480"></canvas>
  
  <!-- 4. 控制面板：2-4个可调参数 -->
  <div class="control-panel">
    <label>参数1: <input type="range" id="param1Slider" min="0" max="100" value="50"></label>
    <label>参数2: <input type="range" id="param2Slider" min="0" max="100" value="50"></label>
  </div>
  
  <!-- 5. CSS样式 -->
  <style>
    .simulation-container {{ border: 2px solid #333; padding: 15px; background: #f9f9f9; }}
    .sim-header h3 {{ margin: 0 0 10px 0; }}
    .data-panel {{ margin: 10px 0; padding: 10px; background: #e0f2fe; }}
    .control-panel {{ margin: 10px 0; }}
    canvas {{ display: block; margin: 10px auto; }}
  </style>
  
  <!-- 6. JavaScript逻辑 -->
  <script>
    (function() {{
      'use strict';
      
      // 获取元素引用
      const canvas = document.getElementById('simCanvas');
      const ctx = canvas.getContext('2d');
      const param1Slider = document.getElementById('param1Slider');
      const param2Slider = document.getElementById('param2Slider');
      const value1Display = document.getElementById('value1');
      const value2Display = document.getElementById('value2');
      
      // 物理计算函数（必须基于核心公式实现）
      function calculatePhysics(param1, param2) {{
        // 实现物理计算，返回状态对象
        return {{ value1: 0, value2: 0 }};
      }}
      
      // 绘制函数
      function draw(state) {{
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        // 绘制物理现象
      }}
      
      // 更新函数（实时响应）
      function update() {{
        const param1 = parseFloat(param1Slider.value);
        const param2 = parseFloat(param2Slider.value);
        const state = calculatePhysics(param1, param2);
        
        // 更新数据显示
        value1Display.textContent = state.value1.toFixed(2);
        value2Display.textContent = state.value2.toFixed(2);
        
        // 绘制
        draw(state);
      }}
      
      // 事件绑定：使用oninput实现实时响应
      param1Slider.oninput = update;
      param2Slider.oninput = update;
      
      // 初始化
      update();
    }})();
  </script>
</div>
```

## 公式格式要求
- 行内公式使用 $...$ 格式
- 确保公式在HTML中可正常渲染（使用单反斜杠，如 \\frac, \\sum）

## JavaScript 代码质量要求（重要）
1. **函数返回值一致性**：所有函数必须始终返回预期类型的值，特别是：
   - 返回对象的函数（如 calculatePerformance()）在条件分支中也要返回相同结构的对象，不能返回 undefined
   - 错误示例：`if (history.y.length < 10) return;` ❌
   - 正确示例：`if (history.y.length < 10) return {{ Mp: 0, tr: 0, ts: 0, PM: 0, u_max: 0, y_ss: 0 }};` ✅

2. **严格模式变量声明**：代码使用 `'use strict'` 严格模式，所有变量必须用 `let`/`const`/`var` 声明后才能使用
   - 错误示例：`y_ss = 1.0;` ❌（未声明变量）
   - 正确示例：`const y_ss = 1.0;` ✅ 或 `let y_ss = 1.0;` ✅
   - 特别注意：函数内部的所有局部变量都必须声明，不能依赖隐式全局变量

3. **变量初始化**：所有变量使用前必须初始化，避免 undefined 错误

4. **防御性编程**：访问对象属性前检查对象是否存在，如：
   ```javascript
   const perf = calculatePerformance();
   if (perf && perf.Mp !== undefined) {{
     mpValue.textContent = perf.Mp;
   }}
   ```

5. **代码完整性**：确保所有 if/for/while 语句都有匹配的闭合括号，所有函数都有 return 语句

## 自检清单
生成完成后请确认：
- [ ] 仿真功能完全符合【仿真需求】的描述，无遗漏
- [ ] 仿真验证了前置章节的理论（如适用）
- [ ] 所有滑块使用 oninput 事件实现实时响应
- [ ] 数据面板正确显示物理量的实时数值
- [ ] 物理计算准确实现了核心公式
- [ ] Canvas尺寸为700x480px
- [ ] 代码完整可运行，无占位符，无"省略"注释
- [ ] 所有内容都在 simulation-container 内
- [ ] 代码可直接嵌入iframe运行
- [ ] **所有函数返回值一致，无 undefined 错误**
- [ ] **所有变量已初始化，无未定义错误**
- [ ] **严格模式下所有变量都已声明（let/const/var），无隐式全局变量**

请直接输出完整HTML代码（包含所有CSS和JS），不要其他说明。"""


def build_continue_prompt(existing_content: str) -> str:
    """构建续生成Prompt（优化版）"""
    # 取最后200字符作为上下文，确保AI理解上下文
    last_part = existing_content[-200:] if len(existing_content) > 200 else existing_content
    
    # 找到最后一行的开头，确保从完整的一行继续
    last_newline = last_part.rfind('\n')
    if last_newline > 0:
        # 取最后一行及之前的一些内容
        context = last_part[max(0, last_newline-100):]
    else:
        context = last_part
    
    prompt = f"""【续写任务】继续生成HTML代码

当前代码最后部分：
```
...{context}
```

【重要指令】
1. 从上述代码的断点处**继续写**，不要重复已生成的内容
2. 保持代码格式、缩进、变量名完全一致
3. **禁止**添加任何说明文字、注释、总结
4. **禁止**输出 ```html 或 ``` 标记
5. **禁止**输出"继续生成"、"代码如下"等提示语
6. 一直写到 `</div>` 标签完整闭合
7. 确保所有函数、条件语句、循环都正确闭合

【示例】
如果当前代码结尾是：
  if (i === 0) {{
    ctx.moveTo(x, y);
  }} else {{
    ctx.

你应该继续写：
  lineTo(x, y);
  }}
  // 继续后续代码...

请直接继续写代码："""
    
    return prompt


def simple_validate_simulation(html: str) -> Tuple[bool, List[str]]:
    """
    简单验证仿真代码完整性（放宽版）
    
    Returns:
        (是否通过, 错误列表)
    """
    errors = []
    warnings = []
    
    # 基本结构检查（必需）
    if '<div class="simulation-container"' not in html:
        errors.append("缺少 simulation-container")
    
    if '<canvas' not in html:
        errors.append("缺少 canvas 元素")
    
    if '<script>' not in html:
        errors.append("缺少 script 标签")
    
    # 标签平衡检查（必需）
    script_open = html.count('<script')
    script_close = html.count('</script>')
    if script_open != script_close:
        # 如果只差一个闭合标签，尝试自动修复
        if script_open == script_close + 1:
            warnings.append(f"script 标签可能缺少闭合 (开:{script_open}, 闭:{script_close})")
        else:
            errors.append(f"script 标签严重不平衡 (开:{script_open}, 闭:{script_close})")
    
    div_open = html.count('<div')
    div_close = html.count('</div>')
    if div_open != div_close:
        # 如果只差一个闭合标签，尝试自动修复
        if div_open == div_close + 1:
            warnings.append(f"div 标签可能缺少闭合 (开:{div_open}, 闭:{div_close})")
        else:
            errors.append(f"div 标签严重不平衡 (开:{div_open}, 闭:{div_close})")
    
    # 检查是否有省略性内容（警告级别）
    if '...' in html[-500:] or '此处省略' in html or '省略' in html[-500:]:
        warnings.append("内容可能包含省略标记")
    
    # 检查关键元素（警告级别，非必需）
    if 'oninput' not in html and 'onchange' not in html and 'addEventListener' not in html:
        warnings.append("缺少事件绑定（可能影响交互）")

    if 'getElementById' not in html:
        warnings.append("缺少 DOM 元素获取（可能影响功能）")

    if 'getContext' not in html:
        warnings.append("缺少 Canvas 上下文获取（无法绘制）")

    # JavaScript 代码质量检查
    # 1. 检查函数返回值一致性（查找可能的 undefined 返回）
    import re

    # 查找函数定义
    func_pattern = r'function\s+(\w+)\s*\([^)]*\)\s*\{'
    functions = re.findall(func_pattern, html)

    for func_name in functions:
        # 查找函数体
        func_start = html.find(f'function {func_name}(')
        if func_start == -1:
            continue

        # 找到函数体的结束位置（简单匹配大括号）
        brace_count = 0
        func_end = func_start
        in_func = False
        for i in range(func_start, min(len(html), func_start + 5000)):
            if html[i] == '{':
                brace_count += 1
                in_func = True
            elif html[i] == '}':
                brace_count -= 1
                if in_func and brace_count == 0:
                    func_end = i
                    break

        func_body = html[func_start:func_end+1]

        # 检查是否有返回对象的函数存在裸 return
        if 'return {' in func_body:
            # 查找所有 return 语句
            return_pattern = r'return\s*;'
            bare_returns = re.findall(return_pattern, func_body)
            if bare_returns:
                warnings.append(f"函数 {func_name}() 返回对象的函数中存在裸 return，可能导致 undefined 错误")

    # 2. 检查常见的 JavaScript 错误模式
    # 检查访问对象属性前是否有检查
    if '.Mp' in html or '.tr' in html or '.ts' in html:
        # 查找是否有防御性检查
        if 'if (perf' not in html and 'if(perf' not in html:
            warnings.append("访问性能指标对象属性前缺少存在性检查（可能导致 Cannot read properties of undefined）")

    # 3. 检查严格模式下的变量声明
    if "'use strict'" in html or '"use strict"' in html:
        # 提取 script 内容
        script_pattern = r'<script>(.*?)</script>'
        scripts = re.findall(script_pattern, html, re.DOTALL)
        for script in scripts:
            if "'use strict'" in script or '"use strict"' in script:
                # 查找函数定义
                func_pattern = r'function\s+(\w+)\s*\([^)]*\)\s*\{'
                for func_match in re.finditer(func_pattern, script):
                    func_name = func_match.group(1)
                    func_start = func_match.end() - 1
                    # 找到函数结束位置
                    brace_count = 1
                    func_end = func_start + 1
                    for i in range(func_start + 1, min(len(script), func_start + 10000)):
                        if script[i] == '{':
                            brace_count += 1
                        elif script[i] == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                func_end = i
                                break

                    func_body = script[func_start:func_end]

                    # 获取函数内声明的变量
                    declared_vars = set()
                    for decl_match in re.finditer(r'\b(let|const|var)\s+(\w+)', func_body):
                        declared_vars.add(decl_match.group(2))

                    # 查找赋值语句（排除对象属性赋值）
                    assign_pattern = r'(?<!\.)\b([a-zA-Z_]\w*)\s*=\s*(?![=])'
                    for assign_match in re.finditer(assign_pattern, func_body):
                        var_name = assign_match.group(1)
                        # 排除关键字和已知全局对象
                        if var_name not in ['if', 'while', 'for', 'return', 'switch', 'case', 'catch', 'this', 'true', 'false', 'null', 'undefined']:
                            if var_name not in declared_vars:
                                # 检查是否是函数参数
                                func_def_start = func_body.find('(')
                                func_def_end = func_body.find(')')
                                if func_def_start != -1 and func_def_end != -1:
                                    params = func_body[func_def_start+1:func_def_end]
                                    if var_name not in [p.strip() for p in params.split(',') if p.strip()]:
                                        warnings.append(f"函数 {func_name}() 中变量 '{var_name}' 未声明就使用（严格模式会报错）")

    # 检查代码完整性（放宽）
    # 只要以 </div> 结尾且没有严重错误，就认为通过
    if not html.rstrip().endswith('</div>'):
        # 如果不以 </div> 结尾，但标签基本平衡，也接受
        if abs(div_open - div_close) <= 1 and abs(script_open - script_close) <= 1:
            warnings.append("不以</div>结尾，但标签基本平衡")
        else:
            errors.append("代码未完整闭合（不以</div>结尾）")
    
    # 记录警告
    if warnings:
        sim_logger.warning(f"[Simulation Validation] 警告: {warnings}")
    
    # 放宽通过条件：没有严重错误即可
    # 即使有警告，只要核心结构存在，也认为是成功的
    is_valid = len(errors) == 0
    
    if is_valid and warnings:
        sim_logger.info(f"[Simulation Validation] 验证通过，但有 {len(warnings)} 个警告")
    
    return is_valid, errors


def clean_simulation_code(html: str) -> str:
    """
    清理仿真代码中的 markdown 标记和说明文字
    
    移除 ```html, ``` 等代码块标记，以及说明文字
    """
    import re
    
    # 移除开头的 ```html 或 ```
    html = re.sub(r'^\s*```html\s*', '', html, flags=re.IGNORECASE)
    html = re.sub(r'^\s*```\s*', '', html)
    
    # 移除结尾的 ```
    html = re.sub(r'\s*```\s*$', '', html)
    
    # 移除说明文字（以特定关键词开头的行）
    lines = html.split('\n')
    cleaned_lines = []
    for line in lines:
        # 跳过说明性文字（以特定关键词开头的整行）
        if re.match(r'^\s*(继续生成|代码如下|以下是|请继续|注意|提示|备注|总结|代码可直接嵌入)', line):
            continue
        # 跳过纯中文说明行（不包含任何代码特征）
        # 代码特征包括：<> {} () ; = // /* */ var let const function
        if (re.match(r'^[^<>{}();=\-/]*[\u4e00-\u9fff]+[^<>{}();=\-/]*$', line) and 
            len(line) < 50 and 
            not line.strip().startswith('//') and  # 保留代码注释
            not line.strip().startswith('/*')):     # 保留代码注释
            continue
        cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines).strip()


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
                sim_logger.info(f"[Simulation] Task {task_id} - 第{attempt+1}次尝试生成")
                
                result = self._generate_single_attempt(
                    context=context,
                    model_id=model_id,
                    task_config=task_config,
                    task_id=f"{task_id}_attempt{attempt+1}"
                )
                
                content = result["content"]
                continues = result["continues"]
                
                # 清理 markdown 代码块标记
                content = clean_simulation_code(content)
                
                # 验证
                is_valid, errors = simple_validate_simulation(content)
                
                if is_valid:
                    sim_logger.info(f"[Simulation] Task {task_id} - 生成成功，续生成{continues}次")
                    sim_logger.info(f"[Simulation] Task {task_id} - 最终内容长度: {len(content)}")
                    return {
                        "success": True,
                        "content": content,
                        "attempts": attempt + 1,
                        "continues": continues
                    }
                else:
                    sim_logger.error(f"[Simulation] Task {task_id} - 验证失败: {errors}")
                    sim_logger.error(f"[Simulation] Task {task_id} - 失败内容长度: {len(content)}")
                    sim_logger.error(f"[Simulation] Task {task_id} - 失败内容开头: {content[:200]}...")
                    sim_logger.error(f"[Simulation] Task {task_id} - 失败内容结尾: ...{content[-200:]}")
                    
                    if attempt < self.max_retries - 1:
                        sim_logger.info(f"[Simulation] Task {task_id} - 准备重试 (attempt {attempt+2}/{self.max_retries})")
                        continue
                    else:
                        # 最后一次尝试，返回失败
                        sim_logger.error(f"[Simulation] Task {task_id} - 所有重试耗尽，返回失败")
                        raise SimulationGenerationError(
                            message=f"验证失败: {', '.join(errors)}",
                            outline_requirement=description,
                            course=course,
                            knowledge_point=knowledge_point,
                            section_title=section_title
                        )
                
            except Exception as e:
                sim_logger.error(f"[Simulation] Task {task_id} - 生成异常: {e}")
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
                sim_logger.info(f"[Simulation] Task {task_id} - 开始第一次生成")
            else:
                # 续生成
                existing = "".join(all_content)
                continue_prompt = build_continue_prompt(existing)
                
                sim_logger.info(f"[Simulation] Task {task_id} - 开始第{continue_attempt+1}次续生成")
                sim_logger.info(f"[Simulation] Task {task_id} - 已有内容长度: {len(existing)}")
                sim_logger.info(f"[Simulation] Task {task_id} - 已有内容结尾: ...{existing[-100:]}")
                
                # 记录续生成 prompt 到日志
                try:
                    from app.core.model_callers import response_logger
                    response_logger.log_prompt(
                        task_id=f"{task_id}_continue{continue_attempt}",
                        module="simulation_continue",
                        model_id=model_id or "unknown",
                        messages=[
                            {"role": "system", "content": "续生成模式"},
                            {"role": "user", "content": continue_prompt}
                        ]
                    )
                    sim_logger.info(f"[Simulation] Task {task_id} - 续生成prompt已记录到日志")
                except Exception as e:
                    sim_logger.warning(f"[Simulation] Task {task_id} - 记录续生成prompt失败: {e}")
                
                current_messages = [
                    {"role": "system", "content": "你是交互式物理仿真专家，继续生成代码。"},
                    {"role": "user", "content": build_simulation_prompt_v2(context)},
                    {"role": "assistant", "content": existing},
                    {"role": "user", "content": continue_prompt}
                ]
                is_continuation = True
                total_continues += 1
            
            # 调用模型
            sim_logger.info(f"[Simulation] Task {task_id} - 调用模型 (continuation={is_continuation}, attempt={continue_attempt+1})")
            
            try:
                content, log_file, finish_reason = model_router.route(
                    task=GenerationTask.SIMULATION,
                    messages=current_messages,
                    model_id=model_id,
                    task_config=task_config,
                    task_id=task_id,
                )
                
                # 检查空内容
                if not content or len(content.strip()) == 0:
                    sim_logger.error(f"[Simulation] Task {task_id} - 续生成返回空内容，停止")
                    break
                
                # 记录详细信息
                sim_logger.info(f"[Simulation] Task {task_id} - 第{continue_attempt+1}次调用完成")
                sim_logger.info(f"[Simulation] Task {task_id} - finish_reason={finish_reason}")
                sim_logger.info(f"[Simulation] Task {task_id} - 本次生成长度: {len(content)}")
                sim_logger.info(f"[Simulation] Task {task_id} - 本次生成开头: {content[:80]}...")
                sim_logger.info(f"[Simulation] Task {task_id} - 本次生成结尾: ...{content[-80:]}")
                
                # 清理本次生成的内容（移除markdown代码块标记）
                cleaned_content = clean_simulation_code(content)

                # 只在非续生成时检测重复（第一次生成时）
                if continue_attempt == 0:
                    # 第一次生成，直接添加清理后的内容
                    all_content.append(cleaned_content)
                    sim_logger.info(f"[Simulation] Task {task_id} - 第一次生成，直接添加")
                else:
                    # 续生成，尝试合并（检测重复）
                    if all_content:
                        sim_logger.info(f"[Simulation] Task {task_id} - 续生成，尝试合并")
                        sim_logger.info(f"[Simulation] Task {task_id} - 已有内容长度: {len(''.join(all_content))}")
                        merged_content = self._merge_contents("".join(all_content), cleaned_content)
                        all_content = [merged_content]
                        sim_logger.info(f"[Simulation] Task {task_id} - 合并后长度: {len(merged_content)}")
                    else:
                        all_content.append(cleaned_content)

                full_content = "".join(all_content)

                # 检查合并后的内容（使用清理后的内容）
                sim_logger.info(f"[Simulation] Task {task_id} - 当前总长度: {len(full_content)}")
                sim_logger.info(f"[Simulation] Task {task_id} - 是否以</div>结尾: {full_content.rstrip().endswith('</div>')}")
                sim_logger.info(f"[Simulation] Task {task_id} - script标签: {full_content.count('<script')} / {full_content.count('</script>')}")
                sim_logger.info(f"[Simulation] Task {task_id} - div标签: {full_content.count('<div')} / {full_content.count('</div>')}")

                # 根据 finish_reason 判断是否需要续生成
                normalized_reason = self._normalize_finish_reason(finish_reason)

                if normalized_reason == "stop":
                    # 正常结束
                    if continue_attempt == 0:
                        # 第一次生成就 stop，检查是否完整（使用清理后的内容）
                        if has_basic_structure(full_content) and full_content.rstrip().endswith('</div>'):
                            sim_logger.info(f"[Simulation] Task {task_id} - 第一次生成正常结束且完整，停止")
                            break
                        else:
                            # 第一次生成就 stop 但不完整，可能是模型认为完成了，但实际上不完整
                            # 尝试一次续生成
                            sim_logger.warning(f"[Simulation] Task {task_id} - 第一次生成 stop 但不完整，尝试续生成")
                    else:
                        # 续生成后 stop，说明完成了
                        sim_logger.info(f"[Simulation] Task {task_id} - 续生成后正常结束，停止")
                        break
                        
                elif normalized_reason == "length":
                    # 长度截断，需要续生成
                    sim_logger.info(f"[Simulation] Task {task_id} - 长度截断，继续生成...")
                    # 继续下一次循环
                    
                else:
                    # 其他情况，根据内容判断
                    if has_basic_structure(full_content) and full_content.rstrip().endswith('</div>'):
                        sim_logger.info(f"[Simulation] Task {task_id} - 内容完整，停止生成")
                        break
                    elif len(content) < 500:
                        sim_logger.warning(f"[Simulation] Task {task_id} - 生成内容过短({len(content)}字符)，停止")
                        break
                
            except Exception as e:
                sim_logger.error(f"[Simulation] Task {task_id} - 调用失败: {e}")
                raise
        
        return {
            "content": "".join(all_content),
            "continues": total_continues
        }
    
    def _merge_contents(self, old_content: str, new_content: str) -> str:
        """
        合并两次生成的内容，检测并移除重叠部分
        
        改进的重叠检测算法：
        1. 从 old_content 结尾取不同长度的后缀（从长到短）
        2. 在 new_content 开头查找匹配
        3. 找到匹配后，只取 new_content 的不重复部分
        """
        # 尝试不同长度的后缀（从长到短）
        max_suffix_len = min(200, len(old_content), len(new_content))
        min_suffix_len = 10  # 最小匹配长度
        
        for suffix_len in range(max_suffix_len, min_suffix_len - 1, -5):
            suffix = old_content[-suffix_len:]
            # 在 new_content 开头查找
            if new_content.startswith(suffix):
                # 找到重叠，只取不重复的部分
                merged = old_content + new_content[suffix_len:]
                sim_logger.info(f"[Simulation] 检测到 {suffix_len} 字符重叠，已移除重复")
                return merged
            
            # 也尝试在 new_content 的较前位置查找（处理可能的前导空格/换行差异）
            # 取 new_content 的前 300 字符进行查找
            search_range = new_content[:min(300, len(new_content))]
            if suffix in search_range:
                overlap_idx = search_range.index(suffix) + suffix_len
                merged = old_content + new_content[overlap_idx:]
                sim_logger.info(f"[Simulation] 检测到 {suffix_len} 字符重叠（偏移位置），已移除重复")
                return merged
        
        # 没有找到重叠，尝试查找行级别的重叠
        # 获取 old_content 的最后几行
        old_lines = old_content.split('\n')
        if len(old_lines) > 1:
            # 尝试最后 1-3 行
            for num_lines in range(3, 0, -1):
                if len(old_lines) >= num_lines:
                    suffix_lines = '\n'.join(old_lines[-num_lines:])
                    if new_content.startswith(suffix_lines):
                        merged = old_content + new_content[len(suffix_lines):]
                        sim_logger.info(f"[Simulation] 检测到 {num_lines} 行重叠，已移除重复")
                        return merged
        
        # 没有找到重叠，直接拼接
        sim_logger.warning(f"[Simulation] 未检测到重叠，直接拼接（可能导致重复内容）")
        sim_logger.debug(f"[Simulation] old_content 结尾: ...{old_content[-50:]}")
        sim_logger.debug(f"[Simulation] new_content 开头: {new_content[:50]}...")
        return old_content + new_content
    
    def _normalize_finish_reason(self, raw_reason: str) -> str:
        """
        将各模型的 finish_reason 统一为标准格式
        
        Returns: "stop" | "length" | "other"
        """
        if not raw_reason:
            return "other"
        
        reason = raw_reason.lower()
        
        # 正常结束
        if reason in ["stop", "stop_sequence", "end_turn", "eos"]:
            return "stop"
        
        # 长度截断
        if reason in ["length", "max_tokens"]:
            return "length"
        
        # 其他
        return "other"


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
