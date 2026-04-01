"""
仿真代码生成专用 Prompt（优化版 - 支持分块生成）
"""

# 精简版仿真约束（用于减少 Prompt 长度）
SIMULATION_CONSTRAINTS_LITE = """【代码约束】
- 使用 HTML5 Canvas，纯原生 JavaScript
- 所有代码在 simulation-container 内，包括 style 和 script
- script 用 IIFE 包裹：(function(){{...}})();
- 处理边界值（除零、Infinity、NaN）
- Canvas 逻辑像素固定为 700×480（即 canvas.width=700、canvas.height=480）
- 【布局】所有绘制必须落在 [0, canvas.width]×[0, canvas.height] 内。多子图纵向堆叠时**禁止**使用多行固定像素高度（如每行 150px）导致总高度超过 480；必须用 pad/gap 与行数动态计算行高：rowH = max(36, floor((canvas.height - padT - padB - gap*(rows-1)) / rows))，并保证最后一行 y+rowH ≤ canvas.height - padB"""


def build_simulation_prompt_lite(
    simulation_desc: str,
    course: str,
    knowledge_point: str,
    simulation_types: list,
    config: dict,
    context: dict = None
) -> str:
    """
    构建精简版仿真 Prompt（降低 token 消耗，提高响应速度）
    
    相比完整版，精简版：
    - 移除角色定义（节省 ~500 tokens）
    - 简化上下文信息（节省 ~300 tokens）
    - 合并重复约束（节省 ~200 tokens）
    - 总体减少约 40% 的 prompt 长度
    """
    # 获取仿真类型指令
    sim_type_str = simulation_types[0] if simulation_types else "interactive"
    
    # 构建上下文（极简）
    key_formulas = ""
    if context and context.get("key_formulas"):
        key_formulas = f"【公式】{context['key_formulas'][:200]}"
    
    return f"""为《{course}》的「{knowledge_point}」生成{sim_type_str}仿真代码。

【需求】{simulation_desc}
{key_formulas}

{SIMULATION_CONSTRAINTS_LITE}

【结构】
<div class="simulation-container">
  <div class="title-desc"><h2>标题</h2><p>描述</p></div>
  <div class="data-panel"><!-- 2-4个参数显示 --></div>
  <canvas id="simCanvas" width="700" height="480"></canvas>
  <div class="control-panel"><!-- 滑块/按钮 --></div>
  <style>/* 美观样式 */</style>
  <script>(function(){{
    // 1. 物理计算函数（处理边界值）
    // 2. 绘制函数（坐标轴+曲线+标注）
    // 3. 事件绑定+初始化
  }})();</script>
</div>

【要求】
- 2-4个可调参数，实时响应
- 数据面板显示关键物理量
- 物理计算基于核心公式
- 代码完整可运行"""


def build_simulation_prompt_structure(
    simulation_desc: str,
    course: str,
    knowledge_point: str,
    context: dict = None
) -> str:
    """
    第一阶段：生成仿真结构和样式
    
    输出 JSON，包含：
    - title, description
    - data_metrics（参数显示配置）
    - controls（控件配置）
    - css（样式）
    """
    key_formulas = ""
    if context and context.get("key_formulas"):
        key_formulas = f"【公式】{context['key_formulas'][:150]}"
    
    return f"""为《{course}》的「{knowledge_point}」设计仿真界面结构和样式。

【需求】{simulation_desc}
{key_formulas}

【输出 JSON】
{{
  "title": "仿真标题（5-10字）",
  "description": "简短描述（20-30字）",
  "data_metrics": [
    {{"id": "param1Value", "label": "参数1", "unit": "单位"}}
  ],
  "controls": [
    {{"type": "slider", "id": "param1Slider", "label": "参数1", "min": 0, "max": 100, "step": 1, "value": 50}}
  ],
  "css": ".simulation-container{{...}} .title-desc{{...}} ..."
}}

【要求】
- 2-4个参数，对应公式中的变量
- 样式美观专业，深色边框浅色背景
- css 选择器须与宿主 DOM 一致：`.simulation-container`、`.title-desc`、`.data-panel`、`.metric`、`.control-panel`（勿使用与宿主不一致的 class 名，否则样式不生效）
- 只返回 JSON，不要其他内容"""


def build_simulation_prompt_logic(
    simulation_desc: str,
    course: str,
    knowledge_point: str,
    simulation_types: list,
    structure_json: dict,
    context: dict = None
) -> str:
    """
    第二阶段：生成物理计算和渲染逻辑
    
    基于第一阶段生成的结构，生成 JavaScript 代码
    """
    sim_type_str = simulation_types[0] if simulation_types else "interactive"
    
    # 提取结构信息
    param_ids = [m["id"] for m in structure_json.get("data_metrics", [])]
    control_ids = [c["id"] for c in structure_json.get("controls", []) if c.get("type") == "slider"]
    
    key_formulas = ""
    if context and context.get("key_formulas"):
        key_formulas = f"【核心公式】{context['key_formulas']}"
    
    return f"""为《{course}》的「{knowledge_point}」生成仿真JavaScript代码。

【需求】{simulation_desc}
{key_formulas}

【界面元素】
- 数据面板元素ID: {param_ids}
- 滑块元素ID: {control_ids}
- Canvas ID: simCanvas（逻辑尺寸 700×480，与 canvas.width / canvas.height 一致）

【画布布局（必须遵守，避免子图被裁切）】
- 仅用 `canvas.width`、`canvas.height` 计算布局，勿写死超出 700×480 的累计高度。
- 若有多行子图（波形/频谱上下排列）：设 `padT`/`padB`/`gap` 与行数 `rows`，令
  `rowH = Math.max(36, Math.floor((canvas.height - padT - padB - gap * (rows - 1)) / rows))`，
  第 r 行顶边 `y = padT + r * (rowH + gap)`，且必须满足 `y + rowH <= canvas.height - padB`。
- 多列子图同理：各列 `x + w <= canvas.width`（预留左右边距）。
- 标题与坐标轴文字画在各行子图矩形**内部**或紧挨上方，避免 `fillText` 的 y 使用负值超出画布上缘（可用 `Math.max(12, y - 2)` 等形式约束）。

【输出格式（必须严格遵守）】
1. 回复中只包含**一个** Markdown 代码块，且第一行必须是：```javascript（其后换行再写代码）。
2. 代码块内从第一行起就是合法的可执行语句或函数声明；**禁止**从某函数体中间开始（例如禁止以 `ctx.fillText` 单独开头而无外层函数）。
3. **禁止**在代码块后再输出 ```html、第二段 ```、或任何中文说明/列举/总结（代码即全部有效内容）。
4. 宿主页面已用 IIFE 包裹并**已定义** `const canvas`、`const ctx`、`const controls` —— **不要**再写 `(function(){{...}})();` 包裹全文，**不要**重复 `const canvas` / `const ctx` / `const controls`。
5. 字符串中若需字面量写出 `</script>`，请写成 `\\u003c/script\\u003e` 或 `'<\\\\/script>'`，避免打断 HTML 中的 script 标签。

【输出代码】
```javascript
// 注意：canvas 和 ctx 已在外部定义，直接使用即可
// 控件引用在 controls 对象中，如 controls['kdSlider']

// 物理计算：基于核心公式
function calculatePhysics(kd) {{
  // kd 是参数值（从滑块读取）
  // 返回状态对象，包含所有计算结果
  // 处理边界值（除零保护、NaN检查）
  return {{ result1: 0, result2: 0 }};
}}

// 绘制函数
function draw(state) {{
  // 清空画布
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  // 绘制坐标轴、网格
  // 绘制曲线/图形
  // 标注关键点
}}

// 更新显示面板
function updateMetrics(state) {{
  // 更新 data_metrics 显示
  // 使用 document.getElementById('metricId') 获取元素
}}

// 主更新函数
function update() {{
  // 从 controls 对象获取滑块值
  const kd = parseFloat(controls['kdSlider'] ? controls['kdSlider'].value : 0);
  const state = calculatePhysics(kd);
  updateMetrics(state);
  draw(state);
}}

// 事件绑定
if (controls['kdSlider']) {{
  controls['kdSlider'].addEventListener('input', update);
}}

// 初始化
try {{
  update();
}} catch (e) {{
  console.error('Initialization error:', e);
}}
```

{SIMULATION_CONSTRAINTS_LITE}

【要求】
- 所有函数完整实现，无占位符
- 滑块调节实时响应
- 数据面板显示计算结果
- 代码可直接运行"""
