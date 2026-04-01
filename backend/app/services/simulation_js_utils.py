"""
仿真阶段二：从模型原文中稳健提取 JavaScript，并做嵌入 HTML 前的必要清理。

典型问题（如 task_131）：
- 未以 ```javascript 开头，仅输出代码片段；
- 在第一个 ``` 之后追加 ```html、整页 HTML、中文说明；
- 非贪婪正则只匹配到极短的第一段 fenced 块；
- 重复包裹 (function(){...})(); 与模板外层 IIFE 嵌套。
"""
from __future__ import annotations

import re
from typing import List, Optional


def extract_javascript_robust(text: Optional[str]) -> str:
    """
    优先提取最长的 ```javascript / ```js 代码块；若无 fence，则截断 ```html / 中文说明等尾部垃圾。
    """
    if not text:
        return ""
    t = text.strip()

    # 1) 去掉明显不属于 JS 的尾部（第二段 fence、说明文）
    t = _truncate_trailing_non_js(t)

    # 2) 所有 fenced JS 块，取最长（避免非贪婪只命中极短的第一段）
    blocks = re.findall(
        r"```(?:javascript|js)\s*([\s\S]*?)\s*```",
        t,
        re.IGNORECASE,
    )
    if blocks:
        best = max(blocks, key=lambda b: len(b.strip()))
        best = best.strip()
        best = _unwrap_outer_iife(best)
        return _sanitize_js_embedded(best)
    # 无 js 语言标记时，仅当全文只有一个 ``` 代码块且像 JS 时才采用（避免误抓 ```html）
    generic_blocks = re.findall(r"```\s*([\s\S]*?)\s*```", t)
    if generic_blocks and not re.search(r"```(?:javascript|js)\b", t, re.I):
        candidates = [b for b in generic_blocks if _looks_like_javascript(b)]
        if len(candidates) == 1:
            best = _unwrap_outer_iife(candidates[0].strip())
            return _sanitize_js_embedded(best)

    # 3) 无闭合 fence：从 ```javascript 起到文末或下一个 ``` 前
    m = re.search(r"```(?:javascript|js)\s*\n([\s\S]*)", t, re.IGNORECASE)
    if m:
        rest = m.group(1)
        if "```" in rest:
            rest = rest.split("```", 1)[0]
        rest = rest.strip()
        rest = _unwrap_outer_iife(rest)
        return _sanitize_js_embedded(rest)

    # 4) 纯文本：去掉从「第二个代码段 / 说明」起的内容
    t = _truncate_trailing_non_js(t)
    t = _unwrap_outer_iife(t.strip())
    return _sanitize_js_embedded(t)


def _truncate_trailing_non_js(s: str) -> str:
    """截断 ```html、重复 fence、中文说明段落等（取最早出现的截断点）。"""
    markers: List[str] = [
        "\n```html",
        "\n```\n```html",
        "\n```\n\n```",
        "\n\n这个完整的仿真代码",
        "\n\n这个完整",
        "\n\n以下是",
        "\n\n## ",
        "\n\n---\n",
        "\n\n1. **",
        "\n\n代码采用模块化",
    ]
    out = s
    cut_at = len(out)
    for mk in markers:
        i = out.find(mk)
        if i != -1:
            cut_at = min(cut_at, i)
    if cut_at < len(out):
        out = out[:cut_at]
    # 去掉行首为中文说明的段落（模型爱用的「本仿真实现了…」）
    lines = out.split("\n")
    cut = len(lines)
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("这个") and "仿真" in stripped and idx > 20:
            cut = idx
            break
        if re.match(r"^\d+\.\s+\*\*[^*]+\*\*", stripped) and idx > 30:
            cut = idx
            break
    out = "\n".join(lines[:cut])
    return out.strip()


def _looks_like_javascript(s: str) -> bool:
    t = s.strip()[:800]
    if not t:
        return False
    hints = (
        "function ",
        "const ",
        "let ",
        "var ",
        "ctx.",
        "canvas",
        "addEventListener",
        "getElementById",
        "=>",
    )
    return any(h in t for h in hints)


def _unwrap_outer_iife(js: str) -> str:
    """
    若整段为 (function(...){ ... })(); 则去掉最外层，避免与 simulation_assembly 内层 IIFE 双套。
    花括号匹配为启发式（不解析字符串内的括号）。
    """
    s = js.strip()
    m = re.match(r"^\(function\s*\([^)]*\)\s*\{", s)
    if not m:
        return s
    start_brace = m.end() - 1
    depth = 0
    for i in range(start_brace, len(s)):
        if s[i] == "{":
            depth += 1
        elif s[i] == "}":
            depth -= 1
            if depth == 0:
                tail = s[i + 1 :].strip()
                if re.match(r"^\)\s*\(\s*\)\s*;?\s*$", tail):
                    return s[start_brace + 1 : i].strip()
                return s
    return s


def _sanitize_js_embedded(js: str) -> str:
    """
    降低嵌入 <script> 时提前闭合的风险：将裸字符串中的 </script> 拆写（简单替换）。
    仅处理常见模板字面量/引号串中的字面量（启发式，非完备 JS 解析）。
    """
    if "</script>" not in js.lower():
        return js
    # 将不在反斜杠转义下的 </script> 替换为拼接或 unicode（模板字符串内常用）
    return re.sub(
        r"</script>",
        r"<\\/script>",
        js,
        flags=re.IGNORECASE,
    )


def extract_javascript_simple(text: str) -> str:
    """兼容旧逻辑：单段 ```javascript ``` 非贪婪匹配。"""
    if not text:
        return ""
    m = re.search(r"```(?:javascript|js)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return text.strip()


def looks_like_incomplete_logic_js(js: str) -> bool:
    """
    启发式：阶段二应产出可嵌入 IIFE 的完整语句，而非 draw 函数体内的碎片。
    用于拒绝「从 ctx.fillText 开始」等明显截断输出。
    """
    s = js.strip()
    if len(s) < 30:
        return True
    first = ""
    for line in s.split("\n"):
        t = line.strip()
        if t:
            first = t
            break
    if not first:
        return True
    if first.startswith("ctx.") or first.startswith("canvas."):
        return True
    if first.startswith("})") or first.startswith(");") or first.startswith("},"):
        return True
    return False
