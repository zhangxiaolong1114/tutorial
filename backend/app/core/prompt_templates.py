"""
Prompt 模板配置
分层 Prompt 工程 - 内容生成配置化
"""

# =============================================================================
# 第一层：角色定义（风格层）
# =============================================================================

PERSONA_TEMPLATES = {
    ("formal", "undergraduate"): """你是一位在985高校执教15年的教授，擅长将严谨的学术概念用规范但易懂的方式传授给本科生。
你的语言风格：
- 使用标准学术术语，但首次出现时必给解释
- 句式完整，避免口语化省略
- 用"我们"营造课堂氛围，但保持师者威严
- 举例：不说"这个很简单"，而说"这一概念的直观理解是...
""",

    ("formal", "graduate"): """你是一位研究领域顶尖的学者，为研究生讲授专业前沿课程。
你的语言风格：
- 直接使用专业术语，假设学生有前置知识
- 强调理论体系的完整性和逻辑严密性
- 适当引用经典文献和研究进展
- 举例："正如Smith(2019)所证明的..."
""",

    ("formal", "engineer"): """你是一位有深厚理论功底的技术专家，为工程师做系统培训。
你的语言风格：
- 理论联系实际，每个概念都给出工程背景
- 强调设计参数的选择依据和 trade-off
- 使用行业标准术语和规范
- 举例："从系统可靠性角度，我们需要考虑..."
""",

    ("formal", "high_school"): """你是一位奥赛金牌教练，为拔尖高中生讲授大学先修内容。
你的语言风格：
- 从高中知识自然过渡到大学内容
- 强调数学基础和逻辑思维训练
- 适当拓展，激发学术兴趣
- 举例："大家在高中物理中学过...到了大学，我们发现..."
""",

    ("casual", "undergraduate"): """你是一位受学生喜爱的年轻讲师，善于用生活化比喻让复杂概念变简单。
你的语言风格：
- 用"大家"、"同学们"拉近距离
- 大量使用类比：电路像水流、信号像快递
- 适当幽默，但不过度
- 举例："大家有没有想过，为什么..."
""",

    ("casual", "graduate"): """你是一位有丰富工程经验的资深工程师，给研究生分享实战经验。
你的语言风格：
- 用"实际项目中"、"我在工作中发现"开头
- 强调"书上不会告诉你的"细节
- 案例来自真实工程场景
- 举例："当年我们做XX项目时..."
""",

    ("casual", "engineer"): """你是一位技术社区的意见领袖，用通俗易懂的方式分享技术洞见。
你的语言风格：
- 像技术博客一样轻松自然
- 多用类比和示意图说明
- 分享踩坑经验和最佳实践
- 举例："说实话，我第一次看到这个也懵了..."
""",

    ("casual", "high_school"): """你是一位善于启发学生的科普作家，让高中生也能理解专业内容。
你的语言风格：
- 从日常生活现象引入
- 避免复杂数学，强调直观理解
- 激发好奇心和探索欲
- 举例："想象一下，如果你有一个魔法眼镜能看到..."
""",

    ("rigorous", "undergraduate"): """你是一位对教学要求极严的教授，培养学生的严谨思维习惯。
你的语言风格：
- 每个定义都精确到符号和量纲
- 强调充分条件、必要条件的区分
- 要求学生掌握完整的推导过程
- 举例："注意，这里的条件是充分的，但不是必要的..."
""",

    ("rigorous", "graduate"): """你是一位理论计算机科学家，为博士生讲解数学基础。
你的语言风格：
- 定义-定理-证明的严格结构
- 区分充分条件、必要条件、充要条件
- 讨论复杂度、收敛性、稳定性
- 举例："该算法的收敛速度为O(n log n)，证明如下..."
""",

    ("rigorous", "engineer"): """你是一位系统架构师，为工程师团队做技术培训。
你的语言风格：
- 精确到参数范围、边界条件、性能指标
- 每个结论都有量化依据
- 强调可复现、可验证
- 举例："在采样率>2倍奈奎斯特频率时，误差<0.1%"
""",

    ("rigorous", "high_school"): """你是一位数学竞赛教练，培养高中生的严密推理能力。
你的语言风格：
- 从公理出发，逐步构建知识体系
- 强调逻辑链条的完整性
- 训练学生识别隐含假设
- 举例："我们来严格证明这个结论，首先明确前提条件..."
""",
}


def get_persona(tone: str, target_audience: str) -> str:
    """获取角色定义"""
    key = (tone, target_audience)
    return PERSONA_TEMPLATES.get(key, PERSONA_TEMPLATES[("formal", "undergraduate")])


# =============================================================================
# 第二层：内容结构（结构层）
# =============================================================================

CONTENT_STRUCTURES = {
    "progressive": """【渐进式结构 - 从已知到未知】

1. 锚定已知（1-2段）
   - 回顾前置知识："在学习本节前，我们已经掌握了..."
   - 建立知识桥梁："基于这些，我们现在可以..."

2. 引入新知（2-3段）
   - 动机："为什么需要这个概念？"
   - 定义：严格的数学/物理定义
   - 直观解释：几何意义或物理意义

3. 深入原理（3-5段）
   - 推导过程：关键步骤，说明"为什么这样推导"
   - 性质分析：重要定理，适用条件
   - 边界讨论：什么时候失效，为什么

4. 应用实例（2-3段）
   - 简单案例：具体数值，手算可验证
   - 复杂案例：工程实际，展示威力
   - 对比分析：不同方法的优劣

5. 总结提升（1-2段）
   - 核心公式回顾
   - 与后续知识的联系预告""",

    "case_driven": """【案例驱动结构 - 从问题到解决】

1. 真实案例呈现（2-3段）
   - 背景：工程场景、具体参数
   - 挑战：遇到了什么问题？
   - 目标：需要达成什么指标？

2. naive 尝试与失败（1-2段）
   - 直观解法："一开始你可能会想..."
   - 为什么不行：暴露知识缺口

3. 知识引入（3-4段）
   - 概念：解决这个问题的关键工具
   - 原理：为什么这个工具适用
   - 使用：具体如何应用

4. 问题解决（2-3段）
   - 应用所学解决案例
   - 结果验证：是否达到目标？
   - 优化空间：还能更好吗？

5. 方法论提炼（1-2段）
   - 这类问题的一般解法
   - 识别问题类型的特征""",

    "problem_based": """【问题导向结构 - 探索式学习】

1. 核心挑战（1-2段）
   - 提出一个看似无法解决的问题
   - 强调其重要性："这是领域的核心难题"

2. 分解思考（2-3段）
   - 引导分析："让我们先思考..."
   - 局部突破：哪些子问题可解？
   - 识别瓶颈：卡在哪里？

3. 知识支撑（3-4段）
   - 引入突破瓶颈的关键概念
   - 证明/推导：为什么这个知识能解决
   - 工具化：如何实际操作

4. 完整方案（2-3段）
   - 整合：各子问题的解如何组合
   - 验证：完整解决方案的正确性
   - 优化：效率、鲁棒性改进

5. 反思与迁移（1-2段）
   - 核心思想：这个问题的本质是什么？
   - 类似问题：还能解决什么？""",

    "comparative": """【对比分析结构 - 突出差异】

1. 概念群引入（2-3段）
   - 介绍一组相关但易混淆的概念
   - 说明它们的使用场景重叠

2. 逐一剖析（每概念2-3段）
   - 概念A：定义、特点、适用条件
   - 概念B：定义、特点、适用条件
   - （更多概念...）

3. 对比矩阵（表格或结构化描述）
   - 维度1：数学形式差异
   - 维度2：物理意义差异
   - 维度3：应用场景差异
   - 维度4：优缺点对比

4. 选择指南（2-3段）
   - 何时选A？典型场景
   - 何时选B？典型场景
   - 常见选择错误及后果

5. 综合应用（2段）
   - 需要组合使用的复杂案例
   - 切换策略和时机判断""",
}


def get_content_structure(teaching_style: str) -> str:
    """获取内容结构模板"""
    return CONTENT_STRUCTURES.get(teaching_style, CONTENT_STRUCTURES["progressive"])


# =============================================================================
# 第三层：深度控制（深度层）
# =============================================================================

FORMULA_INSTRUCTIONS = {
    ("conclusion_only", "beginner"): """【公式处理 - 结论呈现】

- 只给出最终公式，不写任何推导
- 用1-2句话解释公式的物理/几何意义
- 给出1个具体数值例子，展示公式怎么用
- 禁止出现"证明"、"推导"、"由...可得"等词汇""",

    ("conclusion_only", "intermediate"): """【公式处理 - 结论+边界】

- 给出公式，标注各符号的物理意义和单位
- 说明适用条件：在什么前提下成立
- 提及推导思路（1句话），但不展开
- 给出2个例子：标准情况+边界情况""",

    ("conclusion_only", "advanced"): """【公式处理 - 结论+洞察】

- 给出公式，讨论其数学性质（单调性、极值、渐近行为）
- 说明与其他公式的关系（特例、推广）
- 简要提及证明的核心思想（2-3句话）
- 讨论非标准情况下的修正""",

    ("derivation", "beginner"): """【公式处理 - 直观推导】

- 给出公式
- 用几何图形、物理直觉解释"为什么是这样"
- 关键步骤用自然语言描述，不写详细代数
- 举例："从图中可以看出，当x增大时，y线性减小，因此系数为负"
- 最多3个关键步骤""",

    ("derivation", "intermediate"): """【公式处理 - 关键步骤】

- 完整写出公式
- 推导过程呈现关键步骤（代数运算）
- 复杂计算可简写："经过整理可得..."
- 每步说明变换的目的
- 标注易错点："注意这里的符号变化"
- 5-7个步骤为宜""",

    ("derivation", "advanced"): """【公式处理 - 完整推导】

- 从第一性原理出发
- 所有代数步骤完整呈现
- 引入必要的引理并证明
- 讨论推导中的关键假设
- 给出替代推导路径（如有）
- 讨论推导方法的推广性""",

    ("full_proof", "beginner"): """【公式处理 - 初等证明】

- 定理陈述：用直观语言描述结论
- 证明思路：分解为2-3个关键洞察
- 每个洞察给出初等说明（可配合图示）
- 结论：说明证明的核心思想""",

    ("full_proof", "intermediate"): """【公式处理 - 标准证明】

- 定理陈述：条件、结论、适用范围
- 证明结构：直接证明/反证法/归纳法
- 完整证明过程，关键步骤标注依据
- 讨论证明的构造思路
- 分析证明的充分必要性""",

    ("full_proof", "advanced"): """【公式处理 - 严格证明】

- 定理陈述：条件、结论、适用范围
- 证明结构：直接证明/反证法/归纳法
- 完整证明过程，每一步标注依据
- 讨论证明的构造思路
- 分析证明的充分必要性
- 讨论其他证明方法
- 指出证明中的关键洞察""",
}


def get_formula_instruction(formula_detail: str, difficulty: str) -> str:
    """获取公式处理指令"""
    key = (formula_detail, difficulty)
    return FORMULA_INSTRUCTIONS.get(key, FORMULA_INSTRUCTIONS.get((formula_detail, "intermediate"), ""))


# =============================================================================
# 第四层：增强指令
# =============================================================================

CODE_LANGUAGE_INSTRUCTIONS = {
    "python": """【代码示例 - Python】

- 使用Python 3.8+语法
- 优先使用标准库，复杂计算用numpy/scipy
- 可视化使用matplotlib，风格简洁
- 代码包含完整函数定义和类型注解
- 提供可运行的完整示例（含测试数据）""",

    "java": """【代码示例 - Java】

- 使用Java 17语法
- 完整的类定义，包含包声明
- 使用标准库，避免外部依赖
- 包含main方法用于演示
- 添加必要的注释说明设计思路""",

    "cpp": """【代码示例 - C++】

- 使用C++17标准
- 展示RAII和智能指针的使用
- 包含性能考虑（如移动语义）
- 提供完整的可编译代码
- 讨论时间和空间复杂度""",

    "pseudocode": """【算法描述 - 伪代码】

- 混合自然语言和类代码结构
- 强调算法逻辑而非语法细节
- 使用标准算法描述约定
- 包含输入、输出、步骤说明
- 分析时间复杂度和空间复杂度""",
}


def get_code_instruction(code_language: str) -> str:
    """获取代码语言指令"""
    if code_language == "none":
        return ""
    return CODE_LANGUAGE_INSTRUCTIONS.get(code_language, "")


IMAGE_INSTRUCTION = """【配图建议】

在以下位置建议配图，用<div class="image-suggestion">包裹：
- 抽象概念首次出现时：建议示意图类型
- 复杂结构或流程：建议框图类型  
- 数据或结果展示：建议图表类型

格式：<div class="image-suggestion" data-type="diagram|photo|chart" data-desc="图片描述文字"></div>"""


# =============================================================================
# 第五层：统一约束
# =============================================================================

UNIFORM_CONSTRAINTS = """【输出格式强制要求】

1. HTML结构：
   - 最外层：<div class="section-content">
   - 主标题：<h3>章节标题</h3>
   - 小节：<h4>小节标题</h4>
   - 段落：<p>内容</p>

2. 公式格式（KaTeX 兼容）：
   - 行内公式：$...$ （如：$E=mc^2$）
   - 块级公式：$$...$$ （如：$$\sum_{i=1}^n x_i$$）
   - 支持的复杂公式：
     * 分式：$\frac{a}{b}$
     * 上下标：$x_i$, $x^2$, $x_i^j$
     * 根号：$\sqrt{x}$, $\sqrt[n]{x}$
     * 求和/积分：$\sum_{i=1}^n$, $\int_0^\infty$
     * 希腊字母：$\alpha$, $\\beta$, $\gamma$, $\Gamma$, $\pi$, $\Omega$ 等
     * 矩阵：使用 $$\begin{matrix}...\end{matrix}$$
     * 多行对齐：使用 $$\begin{aligned}...\end{aligned}$$
     * 分段函数：使用 $$\begin{cases}...\end{cases}$$
   - 禁止：\( \), \[ \], \begin{equation}, $$$$ 等其他格式
   - 重要：公式中的命令使用单反斜杠，如 \frac, \sum, \alpha（不要在AI输出中双重转义）

3. 特殊区块：
   - 教授提示：<div class="tip">...</div>
   - 常见错误：<div class="warning">...</div>
   - 历史背景：<blockquote>...</blockquote>

4. 内容约束：
   - 必须包含至少1个具体数值案例
   - 关键概念首次出现必加粗<strong>
   - 禁止出现"综上所述"、"总而言之"等套话

5. 长度控制：
   - 简洁模式：800-1200字
   - 标准模式：1500-2500字
   - 详细模式：3000-5000字"""


def get_length_constraint(granularity: str) -> str:
    """获取长度约束"""
    constraints = {
        "brief": "【长度要求】800-1200字",
        "standard": "【长度要求】1500-2500字",
        "detailed": "【长度要求】3000-5000字",
    }
    return constraints.get(granularity, constraints["standard"])


# =============================================================================
# 仿真类型指令
# =============================================================================

SIMULATION_INSTRUCTIONS = {
    "animation": """【仿真类型 - 动画演示】

生成自动播放的动画演示：
- 使用 requestAnimationFrame 实现动画循环
- 关键帧数据完整（至少10-15帧）
- 提供播放/暂停/重置按钮

【关键帧数据格式】
```javascript
const keyFrames = {
    0: { x: 0, y: 0 },
    1: { x: 1, y: 0.5 },
    // ... 至少10-15帧
    14: { x: 0, y: 0 }
};
```""",

    "interactive": """【仿真类型 - 交互实验】

生成交互式仿真实验：
- 2-4个可调参数滑块，oninput 实时响应
- 数据面板显示关键指标
- 2-3个预设场景按钮

【事件绑定示例】
```javascript
slider.oninput = function() {
    const value = parseFloat(this.value);
    valueDisplay.textContent = value.toFixed(2);
    updateSimulation(value); // 更新仿真状态
    draw(); // 重绘
};

// 按钮事件
btn.onclick = function() {
    resetSimulation();
    draw();
};

// 初始绘制
draw();
```""",
}

# =============================================================================
# 仿真代码强制约束
# =============================================================================

SIMULATION_CODE_CONSTRAINTS = """【仿真代码约束】

### 1. 物理计算
- 所有公式写成可执行JavaScript代码
- 禁止空函数或占位符
- **边界值保护**：防止除零、Infinity、NaN

### 2. 关键帧数据（动画类型）
- 至少10-15个关键帧
- 覆盖完整周期

### 3. 绘制函数
- 必须包含实际Canvas绘制代码
- 禁止只写ctx.clearRect()后留空

### 4. 代码结构示例
```javascript
// ✅ 正确的实现：完整的物理计算
function calculateField(charge, current, time) {
    const k = 8.99e9; // 库仑常数
    const E = k * charge / (r * r); // 电场强度计算
    const B = (mu0 * current) / (2 * Math.PI * r); // 磁场计算
    return { E, B, phase: omega * time };
}

// ✅ 正确的实现：完整的绘制
function drawField(ctx, state) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // 绘制电场线
    for (let i = 0; i < 20; i++) {
        const angle = (i / 20) * Math.PI * 2;
        const x = centerX + Math.cos(angle) * radius;
        const y = centerY + Math.sin(angle) * radius;
        
        ctx.beginPath();
        ctx.moveTo(centerX, centerY);
        ctx.lineTo(x, y);
        ctx.strokeStyle = 'rgba(255, 100, 100, 0.6)';
        ctx.stroke();
    }
}

// ✅ 正确的实现：完整的关键帧数据
const keyFrames = {
    0: { t: 0, E: 0, B: 1.0, phase: 0 },
    1: { t: 0.05, E: 0.31, B: 0.95, phase: 0.31 },
    2: { t: 0.1, E: 0.59, B: 0.81, phase: 0.63 },
    // ... 必须完整填充到第19帧
    19: { t: 0.95, E: -0.31, B: 0.95, phase: 5.97 }
};
```"""


def get_simulation_instruction(simulation_type: str) -> str:
    """获取仿真类型指令"""
    return SIMULATION_INSTRUCTIONS.get(simulation_type, "")


# =============================================================================
# 大纲生成专用配置
# =============================================================================

# 输出格式对应的大纲结构要求
OUTPUT_FORMAT_CONFIGS = {
    "lecture": {
        "name": "讲义",
        "description": "完整的教学文档，适合课堂讲授或自学阅读",
        "structure_note": "章节完整，内容详细，包含所有教学环节",
        "special_sections": [],
        "format_hints": "每个章节内容要完整、连贯，适合连续阅读"
    },
    "ppt_outline": {
        "name": "PPT大纲",
        "description": "演示文稿大纲，适合制作幻灯片",
        "structure_note": "每页PPT一个要点，强调视觉化和简洁性",
        "special_sections": [
            {
                "id": "slides",
                "title": "幻灯片设计",
                "description": "每页PPT的内容要点和视觉设计建议",
                "required": True,
                "point_range": (6, 10)
            }
        ],
        "format_hints": """PPT大纲特殊要求：
- 每个要点要简洁，适合放在一页PPT上
- 强调图表、示意图的建议
- 标注动画或过渡效果建议
- 演讲者备注要点"""
    },
    "lab_manual": {
        "name": "实验手册",
        "description": "实验指导文档，包含步骤和注意事项",
        "structure_note": "强调操作步骤、安全事项和结果分析",
        "special_sections": [
            {
                "id": "objectives",
                "title": "实验目标",
                "description": "明确实验要达成的学习目标",
                "required": True,
                "point_range": (3, 4)
            },
            {
                "id": "equipment",
                "title": "实验器材",
                "description": "所需设备和材料清单",
                "required": True,
                "point_range": (3, 5)
            },
            {
                "id": "procedure",
                "title": "实验步骤",
                "description": "详细的操作流程和注意事项",
                "required": True,
                "point_range": (5, 8)
            },
            {
                "id": "analysis",
                "title": "结果分析",
                "description": "数据处理和误差分析方法",
                "required": True,
                "point_range": (4, 6)
            }
        ],
        "format_hints": """实验手册特殊要求：
- 步骤要具体、可执行
- 强调安全注意事项
- 包含数据记录表格设计
- 提供预期结果和误差分析"""
    },
    "cheatsheet": {
        "name": "速查表",
        "description": "快速参考文档，包含核心公式和要点",
        "structure_note": "极度精简，只保留最核心的信息",
        "special_sections": [
            {
                "id": "quick_facts",
                "title": "核心要点",
                "description": "一页纸可放下的最关键信息",
                "required": True,
                "point_range": (8, 12)
            },
            {
                "id": "formulas",
                "title": "公式速查",
                "description": "所有重要公式及其适用条件",
                "required": True,
                "point_range": (6, 10)
            },
            {
                "id": "checklist",
                "title": "检查清单",
                "description": "应用时的关键步骤和注意事项",
                "required": True,
                "point_range": (5, 8)
            }
        ],
        "format_hints": """速查表特殊要求：
- 极度精简，每点不超过一行
- 使用表格、列表形式
- 强调对比和分类
- 适合快速查阅，不需要解释"""
    }
}


# 引用规范对应的参考文献要求
CITATION_CONFIGS = {
    "none": {
        "name": "无引用",
        "description": "不添加参考文献",
        "requirement": "不需要参考文献章节",
        "format": None
    },
    "simple": {
        "name": "简单标注",
        "description": "在正文中简单提及重要文献",
        "requirement": """在相关章节中简单提及：
- 关键概念提出者（如：傅里叶提出的...）
- 经典教材或论文（如：详见《信号与系统》第3章）
- 不需要单独的参考文献列表""",
        "format": "作者（年份）或《书名》"
    },
    "academic": {
        "name": "学术引用",
        "description": "完整的学术引用格式",
        "requirement": """添加参考文献章节，包含：
- 经典教材（2-3本）
- 重要论文（3-5篇）
- 在线资源（如有）
- 使用标准学术引用格式""",
        "format": "GB/T 7714 或 APA 格式",
        "section": {
            "id": "references",
            "title": "参考文献",
            "description": "相关经典教材、论文和资料",
            "required": True,
            "point_range": (5, 8)
        }
    }
}


# 教学风格对应的大纲章节模板
OUTLINE_TEMPLATES = {
    "progressive": [
        {
            "id": "concept",
            "title": "知识点概念",
            "description": "从已知到未知，建立概念基础",
            "required": True,
            "point_range": (4, 6)
        },
        {
            "id": "explanation", 
            "title": "详细讲解",
            "description": "深入原理，数学推导与实例",
            "required": True,
            "point_range": (5, 7)
        },
        {
            "id": "difficulties",
            "title": "重难点分析", 
            "description": "常见误区与关键难点",
            "required": True,
            "point_range": (4, 5)
        },
        {
            "id": "simulation",
            "title": "交互仿真",
            "description": "可视化演示与参数探索",
            "required": False,  # 根据 need_simulation 决定
            "point_range": (2, 3)
        },
        {
            "id": "summary",
            "title": "总结",
            "description": "核心要点回顾与知识串联",
            "required": True,
            "point_range": (4, 5)
        },
        {
            "id": "exercises",
            "title": "习题与答案",
            "description": "分层练习巩固知识",
            "required": True,
            "point_range": (4, 6)
        }
    ],
    
    "case_driven": [
        {
            "id": "case_intro",
            "title": "案例背景",
            "description": "真实工程案例与问题呈现",
            "required": True,
            "point_range": (3, 4)
        },
        {
            "id": "concept",
            "title": "知识点概念",
            "description": "案例中涉及的核心概念",
            "required": True,
            "point_range": (3, 5)
        },
        {
            "id": "explanation",
            "title": "原理解析",
            "description": "围绕案例展开原理讲解",
            "required": True,
            "point_range": (5, 7)
        },
        {
            "id": "case_solution",
            "title": "案例解决",
            "description": "应用知识解决案例问题",
            "required": True,
            "point_range": (4, 5)
        },
        {
            "id": "simulation",
            "title": "交互仿真",
            "description": "案例场景的交互式探索",
            "required": False,
            "point_range": (2, 3)
        },
        {
            "id": "variations",
            "title": "案例变体",
            "description": "举一反三，扩展应用场景",
            "required": True,
            "point_range": (3, 4)
        },
        {
            "id": "exercises",
            "title": "实战练习",
            "description": "类似案例的解决练习",
            "required": True,
            "point_range": (3, 5)
        }
    ],
    
    "problem_based": [
        {
            "id": "challenge",
            "title": "核心挑战",
            "description": "提出具有挑战性的问题",
            "required": True,
            "point_range": (2, 3)
        },
        {
            "id": "analysis",
            "title": "问题分析",
            "description": "分解问题，识别知识缺口",
            "required": True,
            "point_range": (4, 5)
        },
        {
            "id": "concept",
            "title": "知识工具",
            "description": "解决问题所需的核心概念",
            "required": True,
            "point_range": (4, 6)
        },
        {
            "id": "explanation",
            "title": "工具详解",
            "description": "深入理解工具的用法",
            "required": True,
            "point_range": (5, 7)
        },
        {
            "id": "simulation",
            "title": "交互探索",
            "description": "通过仿真探索解决方案",
            "required": False,
            "point_range": (2, 3)
        },
        {
            "id": "solution",
            "title": "完整方案",
            "description": "整合知识解决核心挑战",
            "required": True,
            "point_range": (4, 5)
        },
        {
            "id": "exercises",
            "title": "拓展挑战",
            "description": "类似问题的独立解决",
            "required": True,
            "point_range": (3, 4)
        }
    ],
    
    "comparative": [
        {
            "id": "concept_group",
            "title": "概念群介绍",
            "description": "一组相关但易混淆的概念",
            "required": True,
            "point_range": (4, 5)
        },
        {
            "id": "concept_a",
            "title": "概念A详解",
            "description": "第一个概念的深入分析",
            "required": True,
            "point_range": (4, 6)
        },
        {
            "id": "concept_b",
            "title": "概念B详解", 
            "description": "第二个概念的深入分析",
            "required": True,
            "point_range": (4, 6)
        },
        {
            "id": "comparison",
            "title": "对比分析",
            "description": "多维度对比概念差异",
            "required": True,
            "point_range": (5, 7)
        },
        {
            "id": "selection_guide",
            "title": "选择指南",
            "description": "何时使用哪个概念",
            "required": True,
            "point_range": (4, 5)
        },
        {
            "id": "simulation",
            "title": "交互对比",
            "description": "可视化对比不同概念的效果",
            "required": False,
            "point_range": (2, 3)
        },
        {
            "id": "exercises",
            "title": "辨析练习",
            "description": "区分相似概念的应用场景",
            "required": True,
            "point_range": (4, 6)
        }
    ]
}


# 难度等级对应的内容深度描述
DIFFICULTY_DESCRIPTIONS = {
    "beginner": {
        "concept": "侧重直观理解，避免复杂数学，多用类比和生活化例子",
        "explanation": "从具体实例出发，逐步抽象，强调物理意义",
        "formula": "只使用基本公式，详细解释每个符号的含义",
        "exercise": "基础应用题，直接套用公式，步骤清晰"
    },
    "intermediate": {
        "concept": "标准数学定义，适当推导，强调适用条件",
        "explanation": "完整推导关键步骤，结合实例和理论",
        "formula": "标准公式形式，展示推导过程",
        "exercise": "综合应用题，需要多步骤推理"
    },
    "advanced": {
        "concept": "严格数学定义，讨论边界情况和推广",
        "explanation": "完整数学推导，讨论多种证明方法",
        "formula": "一般化公式形式，讨论特殊情况",
        "exercise": "开放性问题，需要创造性思维和深入分析"
    }
}


# 互动元素对应的习题类型
INTERACTIVE_ELEMENTS_MAP = {
    "thinking": {
        "exercise_title": "思考题",
        "exercise_description": "设计引导性思考问题，激发深度思考，不要求立即给出答案",
        "exercise_types": ["概念辨析题", "反思考题", "拓展联想题", "开放讨论题"]
    },
    "exercise": {
        "exercise_title": "练习题",
        "exercise_description": "设计分层练习题，从基础到提高，巩固知识应用",
        "exercise_types": ["基础计算题", "综合应用题", "设计分析题", "证明推导题"]
    },
    "quiz": {
        "exercise_title": "自测题",
        "exercise_description": "设计选择题和判断题，快速检验理解程度",
        "exercise_types": ["概念选择题", "计算选择题", "判断辨析题", "填空补全题"]
    },
    "none": {
        "exercise_title": "习题",
        "exercise_description": "标准练习题，覆盖知识点应用",
        "exercise_types": ["基础题", "提高题", "综合题"]
    }
}


def build_outline_prompt(course: str, knowledge_point: str, config: dict) -> str:
    """
    构建完全配置化的大纲生成 Prompt
    
    支持：教学风格、难度、粒度、仿真、互动元素、输出格式、引用规范
    
    Args:
        course: 课程名称
        knowledge_point: 知识点
        config: 配置字典，包含各配置项
    """
    tone = config.get("tone", "formal")
    target_audience = config.get("target_audience", "undergraduate")
    teaching_style = config.get("teaching_style", "progressive")
    difficulty = config.get("difficulty", "intermediate")
    chapter_granularity = config.get("chapter_granularity", "standard")
    need_simulation = config.get("need_simulation", False)
    interactive_elements = config.get("interactive_elements", "exercise")
    output_format = config.get("output_format", "lecture")
    citation_style = config.get("citation_style", "none")
    
    # 获取角色定义
    persona = get_persona(tone, target_audience)
    
    # 获取难度描述
    difficulty_desc = DIFFICULTY_DESCRIPTIONS.get(difficulty, DIFFICULTY_DESCRIPTIONS["intermediate"])
    
    # 获取互动元素配置
    interactive_config = INTERACTIVE_ELEMENTS_MAP.get(interactive_elements, INTERACTIVE_ELEMENTS_MAP["exercise"])
    
    # 获取输出格式配置
    output_config = OUTPUT_FORMAT_CONFIGS.get(output_format, OUTPUT_FORMAT_CONFIGS["lecture"])
    
    # 获取引用规范配置
    citation_config = CITATION_CONFIGS.get(citation_style, CITATION_CONFIGS["none"])
    
    # 获取基础章节模板
    section_templates = OUTLINE_TEMPLATES.get(teaching_style, OUTLINE_TEMPLATES["progressive"])
    
    # 根据粒度确定章节数量范围
    granularity_ranges = {
        "brief": (3, 5),
        "standard": (6, 8),
        "detailed": (8, 12),
    }
    min_sections, max_sections = granularity_ranges.get(chapter_granularity, (6, 8))
    
    # 根据配置筛选和构建章节列表
    sections_to_include = []
    for section in section_templates:
        # 仿真章节根据 need_simulation 决定
        if section["id"] == "simulation" and not need_simulation:
            continue
        sections_to_include.append(section)
    
    # 添加输出格式特有的章节
    if output_config.get("special_sections"):
        for special_section in output_config["special_sections"]:
            # 检查是否已存在
            if not any(s["id"] == special_section["id"] for s in sections_to_include):
                sections_to_include.append(special_section)
    
    # 添加引用章节（如果需要）
    if citation_config.get("section"):
        sections_to_include.append(citation_config["section"])
    
    # 构建章节详细描述
    sections_description = []
    for i, section in enumerate(sections_to_include, 1):
        min_points, max_points = section["point_range"]
        required_mark = "【必选】" if section.get("required", False) else "【可选】"
        desc = f"""
{i}. {section['id']} - {section['title']} {required_mark}
   说明：{section['description']}
   要点数量：{min_points}-{max_points}个具体要点"""
        sections_description.append(desc)
    
    sections_str = "\n".join(sections_description)
    
    # 构建引用要求文本
    citation_requirement = ""
    if citation_style != "none":
        citation_requirement = f"""

### 参考文献要求
{citation_config['requirement']}
引用格式：{citation_config['format']}"""
    
    # 构建习题类型字符串（避免在 f-string 中使用反斜杠）
    exercise_types_str = "\n".join(['- ' + t for t in interactive_config['exercise_types']])
    
    # 构建仿真章节文本
    simulation_section = """### simulation / 交互探索 / 交互对比 类章节
必须包含：
- 仿真目标：用户可以通过仿真观察什么现象
- 可调参数：2-4个关键参数及其物理意义
- 观察指标：应该关注哪些输出结果
"""
    
    # 构建特殊章节提示文本
    special_section_note = """### slides / objectives / equipment / procedure / quick_facts 等特殊章节
根据输出格式要求，包含相应的特殊章节内容。
"""
    
    # 构建完整 Prompt
    prompt = f"""{persona}

## 任务
为课程《{course}》的知识点「{knowledge_point}」生成教学大纲。
输出格式：{output_config['name']} - {output_config['description']}

## 学习者信息
- 目标受众：{target_audience}
- 难度等级：{difficulty}
- 内容深度要求：
  * 概念部分：{difficulty_desc['concept']}
  * 讲解部分：{difficulty_desc['explanation']}
  * 公式处理：{difficulty_desc['formula']}
  * 习题设计：{difficulty_desc['exercise']}

## 输出格式特殊要求
{output_config['structure_note']}

{output_config['format_hints']}
{citation_requirement}

## 大纲结构要求
生成 {min_sections}-{max_sections} 个章节，从以下模板中选择合适的章节：
{sections_str}

## 各章节详细要求

### concept / concept_group / knowledge_tool 类章节
必须包含：
- 严格的数学定义（根据难度调整严格程度）
- 物理意义/几何解释（使用{target_audience}能理解的方式）
- 适用条件和边界（明确限制条件）
- 与相关概念的区别（如适用对比风格）

### explanation / 原理解析 / 工具详解 类章节
必须包含：
- 原理的数学推导（{difficulty_desc['formula']}）
- 不同角度的理解方式
- 典型实例（含具体数值，符合{target_audience}水平）
- 工程应用背景

### difficulties / analysis / comparison 类章节
必须包含：
- 学生最常见的理解误区及纠正
- 数学推导中的关键难点
- 实际应用中的注意事项

{simulation_section if need_simulation else ''}
### exercises / 实战练习 / 拓展挑战 / 辨析练习 类章节
{interactive_config['exercise_description']}
必须包含以下类型：
{exercise_types_str}

{special_section_note if output_config.get('special_sections') else ''}
## 输出格式
请以 JSON 格式返回，结构如下：
{{
    "title": "{course} - {knowledge_point}",
    "output_format": "{output_format}",
    "sections": [
        {{
            "id": "章节标识",
            "title": "章节标题",
            "content": ["具体要点1", "具体要点2", ...],
            "order": 1,
            "prerequisites": ["需要前文已讲解的概念1", "概念2"],
            "prepares_for": ["为后文铺垫的概念1", "概念2"],
            "key_formulas": ["核心公式1", "公式2"]
        }},
        ...更多章节
    ]
}}

## 章节关联信息要求
每个章节必须包含以下关联信息，用于保证文档连贯性：

### prerequisites（前置依赖）
- 列出本章需要依赖的前置知识
- 这些概念必须在前面的章节中已经讲解
- 示例：["导数的定义", "极限的概念"]

### prepares_for（后续铺垫）
- 列出本章需要为后续章节铺垫的关键概念
- 这些概念在本章打好基础，但不要提前展开
- 示例：["泰勒展开的应用", "高阶导数"]

### key_formulas（核心公式）
- 列出本章必须出现的核心公式（用 LaTeX 格式）
- 这些公式将在后续章节中被引用
- 示例：["$f'(x) = \\lim_{{h\\to 0}} \\frac{{f(x+h)-f(x)}}{{h}}$"]

## 重要规则
- content 必须是字符串数组，每个元素是具体的教学内容描述
- 要点要具体、可执行，不是泛泛的标题（如不要'基本概念'，要'XX定义为...'）
- 包含具体的数值、公式、案例细节
- 根据难度等级调整内容深度：{difficulty}
- 根据输出格式调整内容风格：{output_config['name']}
- 不要返回对象数组或嵌套结构
- 只返回 JSON，不要其他说明"""

    return prompt


# =============================================================================
# 章节内容生成专用 Prompt（带上下文连贯性）
# =============================================================================

def build_section_prompt(
    section_title: str,
    section_key_points: list,
    course: str,
    knowledge_point: str,
    config: dict,
    context: dict = None
) -> str:
    """
    构建章节内容生成 Prompt（带上下文连贯性）
    
    Args:
        section_title: 章节标题
        section_key_points: 章节要点列表
        course: 课程名称
        knowledge_point: 知识点
        config: 配置字典
        context: 上下文信息，包含大纲结构、前后章节摘要等
    """
    tone = config.get("tone", "formal")
    target_audience = config.get("target_audience", "undergraduate")
    teaching_style = config.get("teaching_style", "progressive")
    difficulty = config.get("difficulty", "intermediate")
    formula_detail = config.get("formula_detail", "derivation")
    content_style = config.get("content_style", "detailed")
    code_language = config.get("code_language", "python")
    need_images = config.get("need_images", False)
    chapter_granularity = config.get("chapter_granularity", "standard")
    
    key_points_str = "\n".join([f"- {point}" for point in section_key_points])
    
    parts = []
    
    # 1. 角色定义
    parts.append(get_persona(tone, target_audience))
    
    # 2. 上下文信息（增强版 - 选项B：信息分层）
    if context:
        context_parts = ["## 文档上下文"]
        
        # 完整大纲结构（仅标题，用于全局定位）
        if context.get("full_outline"):
            outline_summary = []
            for i, sec in enumerate(context['full_outline'], 1):
                current_marker = " <- 当前章节" if i == context.get('current_index', 0) + 1 else ""
                status = "[已生成]" if i < context.get('current_index', 0) + 1 else "[待生成]"
                outline_summary.append(f"{i}. {sec.get('title', '未命名')}{current_marker} {status}")
            
            outline_summary_str = "\n".join(outline_summary)
            context_parts.append(f"""### 完整文档结构
本章节是《{course} - {knowledge_point}》教学文档的一部分。

{outline_summary_str}""")
        
        # 当前章节的关联信息（详细展开）
        if context.get("current_section_meta"):
            meta = context['current_section_meta']
            meta_parts = ["### 本章节关联信息"]
            
            if meta.get('prerequisites'):
                prereqs = "\n".join([f"- {p}" for p in meta['prerequisites']])
                meta_parts.append(f"""**前置依赖**（这些概念必须在本章之前已讲解）：
{prereqs}""")
            
            if meta.get('prepares_for'):
                prepares = "\n".join([f"- {p}" for p in meta['prepares_for']])
                meta_parts.append(f"""**后续铺垫**（为这些后文概念打好基础）：
{prepares}""")
            
            if meta.get('key_formulas'):
                formulas = "\n".join([f"- {f}" for f in meta['key_formulas']])
                meta_parts.append(f"""**核心公式**（本章必须出现）：
{formulas}""")
            
            context_parts.append("\n\n".join(meta_parts))
        
        # 前后章节关系
        if context.get("position"):
            pos = context['position']
            context_parts.append(f"""### 位置信息
- 当前章节：第 {pos['current_index'] + 1} 章，共 {pos['total']} 章
- 前一章：{pos.get('prev_title', '无')}
- 后一章：{pos.get('next_title', '无')}""")
        
        # 前置章节详细摘要（最近2章）
        if context.get("prev_summaries"):
            prev_parts = ["### 前置章节摘要"]
            for idx, prev in enumerate(context['prev_summaries'][:2], 1):
                prev_title = prev.get('title', f'第{idx}章')
                prev_content = prev.get('content', '')
                # 增加到800字符，保留更多关键信息
                prev_essence = prev_content[:800] + "..." if len(prev_content) > 800 else prev_content
                prev_parts.append(f"""**{prev_title}**：
{prev_essence}""")
            context_parts.append("\n\n".join(prev_parts))
        
        parts.append("\n\n".join(context_parts))
    
    # 3. 任务定义
    parts.append(f"""## 任务
为课程《{course}》的知识点「{knowledge_point}」撰写「{section_title}」部分。

## 需要覆盖的核心内容
{key_points_str}""")
    
    # 4. 连贯性要求（增强）
    if context:
        coherence_parts = ["## 连贯性要求"]
        
        if context.get("current_section_meta", {}).get("prerequisites"):
            coherence_parts.append("- 确保前置依赖中的概念已经在前文充分讲解，本章可以直接引用")
        
        if context.get("current_section_meta", {}).get("prepares_for"):
            prepares = ", ".join(context['current_section_meta']['prepares_for'])
            coherence_parts.append(f"- 为后续章节铺垫：{prepares}。打好基础但不要提前展开")
        
        if context.get("current_section_meta", {}).get("key_formulas"):
            coherence_parts.append("- 核心公式必须在本章出现，并确保与前后章节的公式体系一致")
        
        coherence_parts.append("- 保持术语和符号体系与前置章节一致")
        coherence_parts.append("- 内容应自然延续前置知识，避免生硬衔接")
        
        parts.append("\n".join(coherence_parts))
    
    # 5. 结构指令
    parts.append(f"## 内容组织方式\n{get_content_structure(teaching_style)}")
    
    # 6. 深度指令
    parts.append(get_formula_instruction(formula_detail, difficulty))
    
    # 7. 内容样式
    style_instructions = {
        "concise": "【内容密度】简洁明了，每段只讲一个核心点，避免冗余解释。",
        "detailed": "【内容密度】详细全面，多角度阐述，提供丰富的背景和细节。",
        "visual": "【内容密度】图文并茂，多用比喻和直观描述，降低抽象度。",
        "formula_heavy": "【内容密度】公式密集，强调数学严谨性，多用符号表达。",
    }
    parts.append(style_instructions.get(content_style, style_instructions["detailed"]))
    
    # 8. 代码语言
    code_instr = get_code_instruction(code_language)
    if code_instr:
        parts.append(code_instr)
    
    # 9. 配图
    if need_images:
        parts.append(IMAGE_INSTRUCTION)
    
    # 10. 统一约束
    parts.append(UNIFORM_CONSTRAINTS)
    
    # 11. 长度控制
    parts.append(get_length_constraint(chapter_granularity))
    
    return "\n\n---\n\n".join(parts)


# =============================================================================
# 仿真代码生成专用 Prompt
# =============================================================================

def build_simulation_prompt(
    simulation_desc: str,
    course: str,
    knowledge_point: str,
    simulation_types: list,
    config: dict,
    context: dict = None
) -> str:
    """
    构建仿真代码生成 Prompt

    Args:
        simulation_desc: 仿真描述
        course: 课程名称
        knowledge_point: 知识点
        simulation_types: 仿真类型列表
        config: 配置字典
        context: 上下文信息，包含前置章节的核心概念和公式
    """
    tone = config.get("tone", "formal")
    target_audience = config.get("target_audience", "undergraduate")

    # 获取仿真类型指令
    sim_instructions = []
    for sim_type in simulation_types:
        instr = get_simulation_instruction(sim_type)
        if instr:
            sim_instructions.append(instr)

    sim_instr_str = "\n\n".join(sim_instructions) if sim_instructions else ""

    # 构建上下文信息
    context_str = ""
    if context:
        context_parts = []
        if context.get("prev_summary"):
            prev = context["prev_summary"]
            context_parts.append(f"""### 前置章节核心内容
前一章「{prev.get('title', '无')}」讲解了：
{prev.get('content', '无')}

【关联要求】仿真必须直观展示上述核心概念，使用户能够通过交互验证或观察这些理论。""")

        if context.get("outline_structure"):
            context_parts.append(f"""### 文档整体结构
{context['outline_structure']}

【定位要求】本仿真是文档的重要组成部分，必须与前后章节内容保持一致性和连贯性。""")

        if context.get("key_formulas"):
            context_parts.append(f"""### 必须体现的核心公式
{context['key_formulas']}

【公式可视化要求】仿真中的计算必须基于上述公式，实时展示公式中各物理量的变化和相互关系。""")

        if context_parts:
            context_str = "\n\n".join(context_parts)

    persona = get_persona(tone, target_audience)

    prompt = f"""{persona}

## 任务
为《{course}》的知识点「{knowledge_point}」生成交互式仿真代码。

## 仿真需求
{simulation_desc}

{context_str}

## 仿真类型要求
{sim_instr_str}

{SIMULATION_CODE_CONSTRAINTS}

## 技术要求
- 使用 HTML5 Canvas 渲染
- 纯原生 JavaScript，不依赖外部库
- 代码封装在 IIFE 中，避免全局污染
- Canvas 尺寸：700x480px
- 响应式设计，适配不同屏幕
- **数值稳定性**：所有计算必须处理边界值（除零、无穷大、NaN），防止页面崩溃

## 代码结构要求（严格遵守）

### HTML 结构
```html
<div class="simulation-container">
  <!-- 1. 标题和描述 -->
  <div class="title-desc">
    <h2>仿真标题</h2>
    <p>仿真描述</p>
  </div>
  
  <!-- 2. 数据面板（显示关键参数） -->
  <div class="data-panel">
    <label>参数名: <span id="paramValue">0</span> 单位</label>
  </div>
  
  <!-- 3. Canvas 绘图区域 -->
  <canvas id="simCanvas" width="700" height="480"></canvas>
  
  <!-- 4. 控制面板（滑块、按钮） -->
  <div class="control-panel">
    <button id="playBtn">播放/暂停</button>
    <input type="range" id="paramSlider" min="0" max="100" value="50">
  </div>
  
  <!-- 5. 样式（必须在容器内） -->
  <style>
    .simulation-container {{ /* 容器样式 */ }}
    /* 其他样式 */
  </style>

  <!-- 6. JavaScript（必须在容器内，紧接在样式后） -->
  <script>
    (function() {{
      /* 仿真代码 */
    }})();
  </script>
</div>
```

### 重要约束
1. **所有内容必须在 `<div class="simulation-container">` 内部**，包括 `<style>` 和 `<script>`
2. **禁止在 `</div>` 闭合标签之后出现任何代码**
3. `<style>` 标签必须在 `<script>` 之前，或者使用内联样式
4. JavaScript 必须封装在 IIFE 中：`(function() { ... })();`
5. 禁止包含 `<html>`, `<head>`, `<body>` 标签

## 仿真与文档内容关联性要求（强制）

### 核心原则
仿真不是独立存在的，而是文档内容的**可视化延伸**。用户通过仿真应该能够：
- 直观理解文档中阐述的物理概念
- 观察文档中推导的公式在实际中的体现
- 通过交互验证文档中的理论结论

### 具体关联要求

#### 1. 概念一致性
- 仿真展示的现象必须与文档中描述的理论完全一致
- 仿真中的物理量定义必须与文档中的数学定义相同
- 禁止使用与文档理论不符的简化模型或近似

#### 2. 公式可视化
- 仿真中的计算必须基于文档中的核心公式
- 数据面板必须显示公式中的关键变量（如：E=mc² 中的 E、m）
- 当用户调节参数时，必须实时反映公式计算结果

#### 3. 参数与理论的对应
- 每个可调参数必须对应文档中的某个理论参数
- 参数的范围必须基于文档中讨论的适用条件
- 参数的调节必须产生文档中预测的效果

#### 4. 现象解释
- 仿真界面必须包含对当前现象的简要解释
- 解释文字必须与文档中的描述一致
- 必须标注相长/相消、极大/极小等关键位置

### 反例（禁止出现）
❌ 文档讲麦克斯韦方程，仿真却展示简谐振动
❌ 文档推导了波动方程，仿真却使用简化的线性运动
❌ 文档讨论了干涉条纹间距公式，仿真却不显示条纹间距计算
❌ 仿真中的物理现象与文档理论预测不符

## 最终检查
在返回代码前，请对照以下检查清单确认：

### 结构完整性
- [ ] 所有内容都在 `<div class="simulation-container">` 内部（包括 style 和 script）
- [ ] `</div>` 闭合标签是最后的内容，后面没有 script 或 style
- [ ] 所有函数都有完整实现，没有空函数或占位符
- [ ] 关键帧数据完整（动画类型至少15-20帧）
- [ ] 绘制函数包含实际的Canvas绘制命令
- [ ] 物理计算逻辑完整可执行
- [ ] 没有"此处省略"等省略性注释

### 内容关联性
- [ ] 仿真展示的现象与文档理论一致
- [ ] 仿真使用了文档中的核心公式进行计算
- [ ] 数据面板显示的物理量与文档中的定义一致
- [ ] 参数调节产生的效果与文档预测相符
- [ ] 仿真界面包含与文档一致的现象解释
- [ ] 用户能够通过仿真验证文档中的理论结论

### 可运行性
- [ ] 代码可以直接复制运行，无需用户补充
- [ ] 在浏览器中打开即可看到正确的仿真效果"""

    return prompt
