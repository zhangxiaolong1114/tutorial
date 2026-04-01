"""
结构化仿真生成管线（架构级）：阶段一 JSON 界面 + 阶段二 JS 逻辑 + 模板组装。
不经过多轮续写与 _merge_contents，避免字符串拼接错误。

日志：backend/app/logs/structured_simulation.log（与各阶段模型原始输出摘要）。
失败：返回 build_structured_failure_placeholder(...) 嵌入文档，含大纲侧全部细节，不再自动回退分块生成。
"""
from __future__ import annotations

import html as html_module
import json
import logging
import os
import re
import traceback
from typing import Any, Dict, List, Optional, Union

from app.core.model_router import GenerationTask, TaskModelConfig, model_router
from app.core.simulation_prompts import (
    build_simulation_prompt_logic,
    build_simulation_prompt_structure,
)
from app.services.simulation_assembly import assemble_simulation_html
from app.services.simulation_js_utils import (
    extract_javascript_robust,
    looks_like_incomplete_logic_js,
)

# 专用文件日志（与 simulation_generator 并列）
_log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
os.makedirs(_log_dir, exist_ok=True)
_struct_log_path = os.path.join(_log_dir, "structured_simulation.log")

struct_file_logger = logging.getLogger("structured_simulation_pipeline.file")
struct_file_logger.setLevel(logging.DEBUG)
if not struct_file_logger.handlers:
    _fh = logging.FileHandler(_struct_log_path, mode="a", encoding="utf-8")
    _fh.setLevel(logging.DEBUG)
    _fh.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    struct_file_logger.addHandler(_fh)
    struct_file_logger.propagate = False

logger = logging.getLogger(__name__)


def _log_line(msg: str, *args: Any) -> None:
    """同时写入根日志与专用文件。"""
    line = msg % args if args else msg
    logger.info(line)
    struct_file_logger.info(line)


def _log_debug(msg: str, *args: Any) -> None:
    line = msg % args if args else msg
    logger.debug(line)
    struct_file_logger.debug(line)


def _log_warning(msg: str, *args: Any) -> None:
    line = msg % args if args else msg
    logger.warning(line)
    struct_file_logger.warning(line)


def _log_error(msg: str, *args: Any) -> None:
    line = msg % args if args else msg
    logger.error(line)
    struct_file_logger.error(line)


class StructuredSimulationFailed(Exception):
    """结构化管线无法产出可用 HTML。"""

    def __init__(self, reason: str, stage: str = "", detail: str = ""):
        super().__init__(reason)
        self.reason = reason
        self.stage = stage
        self.detail = detail


def _extract_json(text: str) -> Optional[dict]:
    if not text or not text.strip():
        return None
    s = text.strip()
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        pass
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            pass
    brace = re.search(r"\{[\s\S]*\}", text)
    if brace:
        try:
            return json.loads(brace.group(0))
        except json.JSONDecodeError:
            pass
    return None


def _num(val: Any, default: float = 0.0) -> float:
    try:
        if val is None:
            return default
        return float(val)
    except (TypeError, ValueError):
        return default


def _normalize_structure(raw: Dict[str, Any]) -> Dict[str, Any]:
    s = dict(raw)
    s.setdefault("title", "交互仿真")
    s.setdefault("description", "")
    s.setdefault("css", "")
    metrics = s.get("data_metrics")
    if not isinstance(metrics, list):
        metrics = []
    clean_m: list = []
    for i, m in enumerate(metrics):
        if not isinstance(m, dict):
            continue
        mid = m.get("id") or f"metricValue{i}"
        clean_m.append(
            {
                "id": str(mid),
                "label": str(m.get("label", f"量{i+1}")),
                "unit": str(m.get("unit", "")),
            }
        )
    s["data_metrics"] = clean_m

    ctrls = s.get("controls")
    if not isinstance(ctrls, list):
        ctrls = []
    clean_c: list = []
    for i, c in enumerate(ctrls):
        if not isinstance(c, dict):
            continue
        cid = c.get("id") or f"param{i}Slider"
        typ = c.get("type", "slider")
        if typ not in ("slider", "button"):
            typ = "slider"
        item = {
            "type": typ,
            "id": str(cid),
            "label": str(c.get("label", f"参数{i+1}")),
        }
        if typ == "slider":
            item["min"] = _num(c.get("min"), 0)
            item["max"] = _num(c.get("max"), 100)
            item["step"] = _num(c.get("step"), 1)
            item["value"] = _num(c.get("value"), 50)
        clean_c.append(item)
    if not clean_c:
        clean_c = [
            {
                "type": "slider",
                "id": "paramSlider",
                "label": "参数",
                "min": 0,
                "max": 100,
                "step": 1,
                "value": 50,
            }
        ]
    if not clean_m:
        clean_m = [{"id": "mainValue", "label": "结果", "unit": ""}]
    s["controls"] = clean_c
    s["data_metrics"] = clean_m
    return s


def _validate_output_html(html: str) -> bool:
    if not html or len(html) < 200:
        return False
    if '<div class="simulation-container"' not in html:
        return False
    if "<script>" not in html or "</script>" not in html:
        return False
    if "<canvas" not in html.lower():
        return False
    return True


def _preview_text(text: Optional[str], head: int = 400, tail: int = 200) -> str:
    if not text:
        return "(空)"
    t = text.strip()
    if len(t) <= head + tail + 20:
        return t
    return f"{t[:head]} ... [省略 {len(t) - head - tail} 字符] ... {t[-tail:]}"


def _escape_block(text: Union[str, List, Any]) -> str:
    if text is None:
        return ""
    if isinstance(text, list):
        return "\n".join(f"• {html_module.escape(str(x))}" for x in text)
    return html_module.escape(str(text))


def build_structured_failure_placeholder(
    simulation_desc: str,
    course: str,
    knowledge_point: str,
    context: Optional[dict],
    failure_reason: str,
    *,
    stage: str = "",
    detail: str = "",
    task_id: str = "",
) -> str:
    """
    结构化仿真失败时的占位块：包含大纲侧全部可用细节，便于人工实现或排错。
    """
    ctx = context or {}
    section_title = ctx.get("section_title") or "交互仿真"
    prereq = ctx.get("prerequisites") or []
    prepares = ctx.get("prepares_for") or []
    kf = ctx.get("key_formulas") or []
    if isinstance(kf, list):
        kf_lines = []
        for item in kf:
            if isinstance(item, dict):
                kf_lines.append(item.get("formula") or item.get("latex") or json.dumps(item, ensure_ascii=False))
            else:
                kf_lines.append(str(item))
        key_formulas_text = "\n".join(kf_lines)
    else:
        key_formulas_text = str(kf)

    sec_content = ctx.get("section_content")
    if isinstance(sec_content, list):
        section_content_text = "\n".join(str(x) for x in sec_content)
    else:
        section_content_text = str(sec_content or "")

    cfull = ctx.get("current_section_full")
    cfull_html = ""
    if isinstance(cfull, dict):
        cfull_html = (
            f"<pre style='white-space:pre-wrap;font-size:13px;margin:8px 0;'>{_escape_block(json.dumps(cfull, ensure_ascii=False, indent=2))}</pre>"
        )

    full_outline = ctx.get("full_outline") or []
    outline_blocks: List[str] = []
    if isinstance(full_outline, list):
        for i, sec in enumerate(full_outline, 1):
            if not isinstance(sec, dict):
                outline_blocks.append(html_module.escape(str(sec)))
                continue
            st = sec.get("title", f"第{i}节")
            sid = sec.get("id", "")
            sc = sec.get("content", [])
            if isinstance(sc, list):
                sc_text = "\n".join(f"  - {x}" for x in sc)
            else:
                sc_text = str(sc)
            sp = sec.get("prerequisites") or []
            sf = sec.get("prepares_for") or []
            sk = sec.get("key_formulas") or []
            outline_blocks.append(
                f"<div style='margin-bottom:12px;padding:8px;background:#f8fafc;border-radius:6px;border:1px solid #e2e8f0;'>"
                f"<strong>{html_module.escape(str(i))}. {html_module.escape(str(st))}</strong>"
                f"<span style='color:#64748b;font-size:12px;'> ({html_module.escape(str(sid))})</span>"
                f"<pre style='white-space:pre-wrap;margin:6px 0 0 0;font-size:12px;'>{html_module.escape(sc_text)}</pre>"
                f"<p style='margin:4px 0 0 0;font-size:12px;color:#475569;'><em>前置</em>：{html_module.escape(str(sp))}</p>"
                f"<p style='margin:4px 0 0 0;font-size:12px;color:#475569;'><em>铺垫</em>：{html_module.escape(str(sf))}</p>"
                f"<p style='margin:4px 0 0 0;font-size:12px;color:#475569;'><em>公式</em>：{html_module.escape(str(sk))}</p>"
                f"</div>"
            )
    outline_section = "".join(outline_blocks) if outline_blocks else "<p>（无 full_outline）</p>"

    prev_t = ctx.get("prev_section_title") or ""
    next_t = ctx.get("next_section_title") or ""
    idx = ctx.get("current_index")
    prev_summaries = ctx.get("prev_summaries")

    extra = ""
    if prev_summaries:
        extra += (
            "<h4 style='margin:12px 0 6px;'>前置章节摘要（节选）</h4>"
            f"<pre style='white-space:pre-wrap;font-size:12px;background:#fff;padding:8px;border-radius:6px;'>{html_module.escape(str(prev_summaries)[:8000])}</pre>"
        )

    reason_esc = html_module.escape(failure_reason)
    stage_esc = html_module.escape(stage or "未知阶段")
    detail_esc = html_module.escape(detail[:4000] if detail else "")
    tid_esc = html_module.escape(task_id or "-")

    _log_warning(
        "[StructuredSim] 生成失败占位 HTML task_id=%s stage=%s reason=%s",
        task_id or "-",
        stage or "-",
        (failure_reason or "")[:500],
    )

    return f'''<div class="simulation-placeholder simulation-container" style="border:2px solid #f59e0b;background:linear-gradient(180deg,#fffbeb 0%,#fff 100%);padding:20px;border-radius:12px;max-width:100%;">
  <h3 style="margin:0 0 8px;color:#b45309;">交互仿真 · 结构化生成未完成</h3>
  <p style="margin:0 0 12px;color:#92400e;font-size:14px;">以下为<strong>大纲中的全部可用细节</strong>，可据此手动实现或排查。任务 ID：<code>{tid_esc}</code></p>
  <p style="margin:0 0 8px;"><strong>失败阶段</strong>：{stage_esc}</p>
  <p style="margin:0 0 8px;"><strong>原因</strong>：{reason_esc}</p>
  {f"<pre style='white-space:pre-wrap;font-size:12px;background:#fff;padding:8px;border-radius:6px;border:1px solid #fcd34d;'>{detail_esc}</pre>" if detail else ""}

  <hr style="border:none;border-top:1px solid #fcd34d;margin:16px 0;" />

  <h4 style="margin:12px 0 6px;">课程与知识点</h4>
  <p style="margin:0;"><strong>课程</strong>：{html_module.escape(course)}</p>
  <p style="margin:4px 0 0;"><strong>知识点</strong>：{html_module.escape(knowledge_point)}</p>
  <p style="margin:4px 0 0;"><strong>章节标题</strong>：{html_module.escape(str(section_title))}</p>
  <p style="margin:4px 0 0;"><strong>在大纲中的序号</strong>：{html_module.escape(str(idx))}</p>
  <p style="margin:4px 0 0;"><strong>前一章</strong>：{html_module.escape(str(prev_t))}　<strong>后一章</strong>：{html_module.escape(str(next_t))}</p>

  <h4 style="margin:16px 0 6px;">仿真需求汇总（任务描述）</h4>
  <pre style="white-space:pre-wrap;font-size:13px;background:#fff;padding:12px;border-radius:8px;border:1px solid #e2e8f0;">{html_module.escape(simulation_desc)}</pre>

  <h4 style="margin:16px 0 6px;">本章大纲要点（section_content）</h4>
  <pre style="white-space:pre-wrap;font-size:13px;background:#fff;padding:12px;border-radius:8px;border:1px solid #e2e8f0;">{html_module.escape(section_content_text)}</pre>

  <h4 style="margin:16px 0 6px;">前置依赖</h4>
  <pre style="white-space:pre-wrap;font-size:13px;background:#fff;padding:12px;border-radius:8px;border:1px solid #e2e8f0;">{_escape_block(prereq if isinstance(prereq, list) else str(prereq))}</pre>

  <h4 style="margin:16px 0 6px;">后续铺垫</h4>
  <pre style="white-space:pre-wrap;font-size:13px;background:#fff;padding:12px;border-radius:8px;border:1px solid #e2e8f0;">{_escape_block(prepares if isinstance(prepares, list) else str(prepares))}</pre>

  <h4 style="margin:16px 0 6px;">核心公式</h4>
  <pre style="white-space:pre-wrap;font-size:13px;background:#fff;padding:12px;border-radius:8px;border:1px solid #e2e8f0;">{html_module.escape(key_formulas_text)}</pre>

  <h4 style="margin:16px 0 6px;">current_section_full（JSON）</h4>
  {cfull_html if cfull_html else "<p>（无）</p>"}

  <h4 style="margin:16px 0 6px;">完整大纲（full_outline，逐章）</h4>
  {outline_section}

  {extra}
</div>'''


def run_structured_simulation(
    simulation_desc: str,
    course: str,
    knowledge_point: str,
    simulation_types: list,
    task_id: str,
    model_id: Optional[str],
    task_config: Optional[TaskModelConfig],
    context: Optional[dict],
) -> str:
    """
    两阶段模型调用 + 模板组装，返回完整仿真 HTML。
    失败时抛出 StructuredSimulationFailed（含阶段与可选详情）。
    """
    ctx = context or {}
    _log_line(
        "[StructuredSim] ========== 开始 task_id=%s model_id=%s ==========",
        task_id,
        model_id or "(default)",
    )
    _log_line("[StructuredSim] course=%s knowledge=%s sim_types=%s", course, knowledge_point, simulation_types)
    _log_line("[StructuredSim] simulation_desc 长度=%s", len(simulation_desc or ""))
    _log_debug("[StructuredSim] simulation_desc 预览: %s", _preview_text(simulation_desc, 500, 200))

    # --- 阶段 1：结构 JSON ---
    struct_prompt = build_simulation_prompt_structure(
        simulation_desc, course, knowledge_point, ctx
    )
    struct_messages = [
        {"role": "system", "content": "你是仿真界面设计师，只输出合法 JSON，不要 Markdown 解释。"},
        {"role": "user", "content": struct_prompt},
    ]
    _log_line("[StructuredSim] 阶段1 Prompt 长度=%s 字符", len(struct_prompt))

    try:
        struct_content, struct_log, struct_finish = model_router.route(
            task=GenerationTask.SIMULATION,
            messages=struct_messages,
            model_id=model_id,
            task_config=task_config,
            task_id=f"{task_id}_struct",
        )
    except Exception as e:
        _log_error("[StructuredSim] 阶段1 模型调用异常: %s\n%s", e, traceback.format_exc())
        raise StructuredSimulationFailed(
            f"阶段1 模型调用失败: {e}", stage="structure_model", detail=traceback.format_exc()
        ) from e

    _log_line(
        "[StructuredSim] 阶段1 返回 len=%s finish_reason=%s log_file=%s",
        len(struct_content or ""),
        struct_finish,
        struct_log,
    )
    _log_debug("[StructuredSim] 阶段1 原文预览: %s", _preview_text(struct_content, 600, 300))

    structure = _extract_json(struct_content or "")
    if not structure or not isinstance(structure, dict):
        _log_error("[StructuredSim] 阶段1 JSON 解析失败，原文前 800 字: %s", (struct_content or "")[:800])
        raise StructuredSimulationFailed(
            "无法解析阶段1结构 JSON",
            stage="structure_parse",
            detail=(struct_content or "")[:4000],
        )

    structure = _normalize_structure(structure)
    _log_line(
        "[StructuredSim] 阶段1 归一化后 title=%s metrics=%s controls=%s",
        structure.get("title"),
        len(structure.get("data_metrics", [])),
        len(structure.get("controls", [])),
    )
    _log_debug("[StructuredSim] 阶段1 structure JSON: %s", json.dumps(structure, ensure_ascii=False)[:3000])

    # --- 阶段 2：逻辑 JS ---
    logic_prompt = build_simulation_prompt_logic(
        simulation_desc,
        course,
        knowledge_point,
        simulation_types,
        structure,
        ctx,
    )
    logic_messages = [
        {
            "role": "system",
            "content": (
                "你是仿真代码专家。只输出一个 ```javascript 代码块，块内为可嵌入宿主 IIFE 的完整脚本逻辑。"
                "禁止在同一回复中输出第二个代码块、```html、整页 HTML 或代码块后的中文说明。"
                "不要用 (function(){...})(); 包裹整段（宿主已提供外层 IIFE）；不要重复声明 const canvas / const ctx / controls。"
            ),
        },
        {"role": "user", "content": logic_prompt},
    ]
    _log_line("[StructuredSim] 阶段2 Prompt 长度=%s 字符", len(logic_prompt))

    try:
        logic_content, logic_log, logic_finish = model_router.route(
            task=GenerationTask.SIMULATION,
            messages=logic_messages,
            model_id=model_id,
            task_config=task_config,
            task_id=f"{task_id}_logic",
        )
    except Exception as e:
        _log_error("[StructuredSim] 阶段2 模型调用异常: %s\n%s", e, traceback.format_exc())
        raise StructuredSimulationFailed(
            f"阶段2 模型调用失败: {e}", stage="logic_model", detail=traceback.format_exc()
        ) from e

    _log_line(
        "[StructuredSim] 阶段2 返回 len=%s finish_reason=%s log_file=%s",
        len(logic_content or ""),
        logic_finish,
        logic_log,
    )
    _log_debug("[StructuredSim] 阶段2 原文预览: %s", _preview_text(logic_content, 600, 300))

    js_code = extract_javascript_robust(logic_content or "")
    if len(js_code.strip()) < 50:
        _log_error("[StructuredSim] 阶段2 JS 过短 len=%s", len(js_code))
        raise StructuredSimulationFailed(
            "阶段2 JS 过短或无法提取",
            stage="logic_parse",
            detail=(logic_content or "")[:4000],
        )
    if looks_like_incomplete_logic_js(js_code):
        _log_error("[StructuredSim] 阶段2 JS 疑似碎片（非完整逻辑） preview=%s", js_code[:400])
        raise StructuredSimulationFailed(
            "阶段2 提取的 JavaScript 疑似不完整（例如从函数体中间开始），请检查模型输出格式",
            stage="logic_parse",
            detail=(logic_content or "")[:4000],
        )

    html = assemble_simulation_html(structure, js_code)
    if not _validate_output_html(html):
        _log_error("[StructuredSim] 组装后校验失败 html_len=%s", len(html))
        raise StructuredSimulationFailed(
            "组装后 HTML 未通过基本校验", stage="assemble_validate", detail=html[:2000]
        )

    _log_line("[StructuredSim] 成功 task_id=%s 最终 HTML 长度=%s", task_id, len(html))
    _log_line("[StructuredSim] ========== 结束 task_id=%s ==========", task_id)
    return html
