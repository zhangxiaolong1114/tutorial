"""
仿真 HTML 组装：由结构化 JSON + 内联 JS 生成完整片段（无多段字符串拼接）。
供分块生成与结构化管线共用。
"""
from __future__ import annotations

from typing import Any, Dict

# 宿主注入：保证画布在文档/iframe 内按比例缩放且不被父级意外裁切；不改变位图分辨率（仍为 700×480）。
_DEFAULT_SIMULATION_CANVAS_CSS = """
  .simulation-container { overflow-x: auto; box-sizing: border-box; }
  .simulation-container canvas#simCanvas {
    display: block;
    max-width: min(100%, 700px);
    width: 700px;
    height: auto;
    aspect-ratio: 700 / 480;
    box-sizing: border-box;
    vertical-align: top;
  }
"""


def assemble_simulation_html(structure: Dict[str, Any], js_code: str) -> str:
    """
    将阶段一 JSON 与阶段二 JS 拼成可嵌入文档的完整仿真 HTML。

    structure 需含：title, description, data_metrics[], controls[], css（可为空字符串）。
    js_code 为 IIFE 内「用户代码」主体（不含外层 (function(){...})() 包裹）。
    """
    data_metrics_html = ""
    for metric in structure.get("data_metrics", []) or []:
        unit = metric.get("unit", "")
        unit_html = f'<span class="unit">{unit}</span>' if unit else ""
        data_metrics_html += f"""
    <div class="metric">
      <span class="label">{metric.get("label", "")}:</span>
      <span class="value" id="{metric.get("id", "")}">0</span>{unit_html}
    </div>"""

    controls_html = ""
    slider_ids: list[str] = []
    button_ids: list[str] = []
    for ctrl in structure.get("controls", []) or []:
        ctrl_id = ctrl.get("id", "")
        if ctrl.get("type") == "slider":
            slider_ids.append(ctrl_id)
            display_id = ctrl_id.replace("Slider", "Display").replace("slider", "Display")
            controls_html += f"""
    <label>{ctrl.get("label", "")}: <span id="{display_id}">{ctrl.get("value", 0)}</span></label>
    <input type="range" id="{ctrl_id}" min="{ctrl.get("min", 0)}" max="{ctrl.get("max", 100)}" step="{ctrl.get("step", 1)}" value="{ctrl.get("value", 0)}">"""
        elif ctrl.get("type") == "button":
            button_ids.append(ctrl_id)
            controls_html += f"""
    <button id="{ctrl_id}">{ctrl.get("label", "")}</button>"""

    all_control_ids = slider_ids + button_ids
    control_ids_js = ", ".join([f'"{cid}"' for cid in all_control_ids])

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
{_DEFAULT_SIMULATION_CANVAS_CSS}
{structure.get("css", "")}
  </style>

  <script>
(function() {{
  'use strict';

  window.onerror = function(msg, url, line) {{
    console.error('[Simulation Error]', msg, 'at line', line);
    return true;
  }};

  const canvas = document.getElementById('simCanvas');
  if (!canvas) {{
    console.error('Canvas not found');
    return;
  }}
  const ctx = canvas.getContext('2d');

  const controls = {{}};
  [{control_ids_js}].forEach(function(id) {{
    const el = document.getElementById(id);
    if (el) controls[id] = el;
    else console.warn('Control not found:', id);
  }});

{js_code}
}})();
  </script>
</div>'''

    return html
