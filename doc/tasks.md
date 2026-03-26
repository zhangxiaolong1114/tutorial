# 智教云开发任务清单

## 项目概述

- **名称**: 智教云 - AI 课程知识点生成平台
- **目标用户**: 理工科教师
- **核心功能**: 输入课程+知识点 → AI生成互动教学文档

---

## 开发阶段

### ✅ Phase 1: 基础框架 (已完成)

| 任务                           | 状态  | 备注                    |
| ---------------------------- | --- | --------------------- |
| 需求文档                         | ✅   | requirements.md       |
| 后端初始化 (FastAPI + SQLAlchemy) | ✅   | SQLite/PostgreSQL 双支持 |
| 前端初始化 (Vue3 + TS + Tailwind) | ✅   | 含路由、Pinia             |
| Docker 配置                    | ✅   | docker-compose.yml    |
| 样式修复 (Tailwind v4)           | ✅   | @tailwindcss/vite 插件  |
| 国际化 (i18n)                   | ✅   | 中文/英文切换               |

---

### ✅ Phase 2: 用户系统 (已完成)

| 任务                    | 优先级 | 状态  | 备注                                      |
| --------------------- | --- | --- | --------------------------------------- |
| 2.1 用户模型 (User Model) | P0  | ✅   | `backend/app/models/user.py`            |
| 2.2 注册/登录 API         | P0  | ✅   | `backend/app/api/auth.py`               |
| 2.3 JWT 认证中间件         | P0  | ✅   | `backend/app/core/security.py`          |
| 2.4 前端登录/注册页面联调       | P0  | ✅   | `frontend/src/views/LoginView.vue`      |
| 2.5 用户状态管理 (Pinia)    | P1  | ✅   | `frontend/src/stores/auth.ts`           |
| 2.6 邮箱验证码             | P0  | ✅   | `backend/app/services/email_service.py` |
| 2.7 多设备登录支持           | P1  | ✅   | `backend/app/models/user_device.py`     |
| 2.8 忘记密码              | P1  | ✅   | `backend/app/api/auth.py`               |
| 2.9 Token 刷新机制        | P1  | ✅   | 双 Token 架构，自动静默刷新                       |

**技术决策:**

- 密码加密: bcrypt
- Token: JWT (HS256)
- **双 Token 架构**:
  - Access Token: 30 分钟短期有效
  - Refresh Token: 7 天长期有效
- 自动刷新: axios/fetch 响应拦截器实现
- 并发处理: 刷新队列机制，避免重复刷新
- 邮箱服务: Office 365 (smtp.partner.outlook.cn)
- 设备指纹: 浏览器特征生成唯一标识

---

### ✅ Phase 3: 核心生成 (已完成)

| 任务               | 优先级 | 状态  | 文件                                             |
| ---------------- | --- | --- | ---------------------------------------------- |
| 3.1 AI 服务封装      | P0  | ✅   | `backend/app/services/ai_service.py`           |
| 3.2 异步任务队列       | P0  | ✅   | `backend/app/services/task_queue_service.py`   |
| 3.3 任务状态追踪       | P0  | ✅   | `backend/app/models/task_queue.py`             |
| 3.4 大纲生成 API     | P0  | ✅   | `backend/app/api/outline.py`                   |
| 3.5 文档生成 API     | P0  | ✅   | `backend/app/api/outline.py`                   |
| 3.6 大纲模型         | P0  | ✅   | `backend/app/models/outline.py`                |
| 3.7 文档模型         | P0  | ✅   | `backend/app/models/document.py`               |
| 3.8 前端生成页面       | P0  | ✅   | `frontend/src/views/GenerateView.vue`          |
| 3.9 前端大纲编辑       | P0  | ✅   | `frontend/src/views/OutlineEditView.vue`       |
| 3.10 前端文档查看      | P0  | ✅   | `frontend/src/views/DocumentDetailView.vue`    |
| 3.11 任务中心页面      | P1  | ✅   | `frontend/src/views/TasksView.vue`             |
| 3.12 HTML 下载功能   | P1  | ✅   | `backend/app/api/document.py`                  |
| 3.13 完整 HTML 存储  | P1  | ✅   | `backend/app/services/ai_service.py`           |
| 3.14 文件系统存储      | P1  | ✅   | `backend/app/services/file_storage_service.py` |
| 3.15 加载速度优化      | P1  | ✅   | KaTeX 替代 MathJax，国内 CDN                        |
| 3.16 文档生成并行化     | P1  | ✅   | 章节并行生成，速度提升 3-6 倍                              |
| 3.17 Token 有效期延长 | P1  | ✅   | 7天有效期，减少频繁登录                                   |
| 3.18 时区显示修复      | P1  | ✅   | 后端统一返回 UTC 时间，前端自动转换                           |
| 3.19 UI 细节优化     | P1  | ✅   | 任务中心边框、布局调整                                    |
| 3.20 时间格式统一      | P1  | ✅   | 所有 API 时间字段使用 format_datetime()                |
| 3.21 Token 刷新机制  | P1  | ✅   | 解决生成文档后点击查看触发重新登录问题                            |
| 3.22 API 超时优化    | P1  | ✅   | 6分钟超时 + 3次重试 + 指数退避                            |
| 3.23 详细日志配置      | P1  | ✅   | ai_service.log / task_queue.log / error.log    |
| 3.24 HTML 结构统一   | P1  | ✅   | section-content 统一包装，规范层级                      |
| 3.25 大纲数据清理      | P1  | ✅   | 自动过滤 [object Object] 等无效内容                     |
| 3.26 公式渲染修复      | P1  | ✅   | 转换为 $ $$，KaTeX 配置修复                            |
| 3.27 时区统一        | P1  | ✅   | 所有模型时间字段统一使用 UTC                               |

**技术决策:**

- AI 模型: Kimi (Moonshot)
- 任务队列: PostgreSQL + asyncio (可扩展至 Redis)
- 公式渲染: KaTeX（比 MathJax 快 10 倍以上）
- CDN: BootCDN 国内节点
- 文档存储: 支持双模式（数据库/文件系统），通过 `STORAGE_TYPE` 配置切换
- 文档生成: 并行处理章节，理论速度提升 = 章节数 / 并发数

---

### ✅ Phase 4: 配置化生成系统 (已完成)

| 任务 | 优先级 | 状态 | 文件 | 说明 |
|------|--------|------|------|------|
| 4.1 配置化生成设计 | P0 | ✅ | `doc/design/configurable-generation.md` | 13个配置字段设计 |
| 4.2 分层 Prompt 工程 | P0 | ✅ | `app/core/prompt_templates.py` | 5层架构：角色/结构/深度/增强/约束 |
| 4.3 配置模型设计 | P0 | ✅ | `app/models/generation_config.py` | 配置数据模型 |
| 4.4 配置 API 开发 | P0 | ✅ | `app/api/generation_config.py` | CRUD 接口 |
| 4.5 配置化大纲生成 | P0 | ✅ | `app/services/ai_service.py` | `generate_outline_with_config` |
| 4.6 配置化章节生成 | P0 | ✅ | `app/services/ai_service.py` | `generate_section_content_with_config` |
| 4.7 上下文连贯性 | P0 | ✅ | `app/services/task_queue_service.py` | 串行生成，传递前一章摘要 |
| 4.8 自动续生成 | P0 | ✅ | `app/services/ai_service.py` | 检测截断，保持上下文连续 |
| 4.9 内容完整性验证 | P0 | ✅ | `app/services/ai_service.py` | JSON/HTML/仿真代码结构检查 |
| 4.10 前端配置界面 | P1 | ✅ | `frontend/src/views/GenerateView.vue` | 配置表单集成 |

**技术亮点:**

- **13个配置字段**:
  - 语气风格: formal/casual/rigorous
  - 目标受众: undergraduate/graduate/engineer/high_school
  - 教学风格: progressive/case_driven/problem_based/comparative
  - 难度等级: beginner/intermediate/advanced
  - 内容粒度: brief/standard/detailed
  - 公式详细度: conclusion_only/derivation/full_proof
  - 仿真类型: animation/interactive
  - 代码语言: python/java/cpp/pseudocode/none
  - 配图需求: true/false
  - 输出格式: lecture/ppt_outline/lab_manual/cheatsheet
  - 引用规范: none/simple/academic
  - 互动元素: thinking/exercise/quiz/none

- **分层 Prompt 架构**:
  ```
  第一层: 角色定义（风格层）- 12种角色组合
  第二层: 内容结构（结构层）- 4种教学结构
  第三层: 深度控制（深度层）- 9种公式处理组合
  第四层: 增强指令（增强层）- 代码/配图
  第五层: 统一约束（约束层）- 格式/长度/公式分隔符
  ```

- **上下文传递机制**:
  ```python
  context = {
      "outline_structure": "大纲结构",
      "position": {"current_index": i, "total": n, "prev_title": "", "next_title": ""},
      "prev_summary": {"title": "", "content": ""},
      "generated_sections": "已生成章节列表"
  }
  ```

---

### 🔄 Phase 4.5: 仿真系统优化 (进行中)

| 任务 | 优先级 | 状态 | 文件 | 说明 |
|------|--------|------|------|------|
| 4.5.1 仿真代码生成 | P1 | ✅ | `app/services/ai_service.py` | `generate_simulation_code_with_config` |
| 4.5.2 仿真代码嵌入 | P1 | ✅ | `app/services/task_queue_service.py` | 嵌入 HTML 文档 |
| 4.5.3 仿真代码完整性修复 | P0 | ✅ | `app/services/ai_service.py` | max_tokens 24000 + 续生成机制 |
| 4.5.4 仿真代码提取修复 | P0 | ✅ | `app/services/ai_service.py` | 处理外部 script/style |
| 4.5.5 仿真与文档关联性 | P0 | ✅ | `app/core/prompt_templates.py` | 传递上下文，强制公式一致 |
| 4.5.6 章节衔接优化 | P1 | ✅ | `app/core/prompt_templates.py` | 移除生硬衔接要求 |
| 4.5.7 标签验证修复 | P1 | ✅ | `app/services/ai_service.py` | 放宽 section 标签检查 |
| 4.5.8 交互事件绑定 | P1 | ✅ | `app/core/prompt_templates.py` | 明确 oninput 要求 |
| 4.5.9 k2.5 模型兼容 | P0 | ✅ | `app/services/ai_service.py` | temperature=1.0 自动设置 |
| 4.5.10 仿真交互稳定性 | P1 | 🔄 | `app/core/prompt_templates.py` | 持续优化中 |
| 4.5.11 更多学科仿真 | P2 | ⏳ | - | 物理、电路、数学等 |
| 4.5.12 仿真代码沙箱 | P2 | ⏳ | - | 安全执行环境 |

**已修复问题:**

1. ✅ **代码截断问题**: max_tokens 8192 → 24000，启用续生成机制
2. ✅ **提取失败问题**: 自动将外部 script/style 移到容器内
3. ✅ **关联性不足**: Prompt 添加上下文信息，强制使用文档公式
4. ✅ **衔接生硬**: 移除"正如我们在XX章讲到的"等刻意引用
5. ✅ **标签不匹配**: 放宽验证，只检查基本结构
6. ✅ **交互不工作**: 明确要求 oninput 事件，提供示例代码
7. ✅ **k2.5 兼容**: 自动设置 temperature=1.0

**待解决问题:**

1. 🔄 仿真交互能力不稳定（需要继续优化 Prompt）
2. 🔄 公式渲染偶发问题
3. ⏳ 仿真代码沙箱（安全）

---

### 🔄 Phase 5: 文档管理增强 (部分完成)

| 任务 | 优先级 | 状态 | 文件 |
|------|--------|------|------|
| 5.1 文档列表 API | P2 | ✅ | `backend/app/api/document.py` |
| 5.2 文档详情 API | P2 | ✅ | `backend/app/api/document.py` |
| 5.3 前端文档列表 | P2 | ✅ | `frontend/src/views/DocumentsView.vue` |
| 5.4 前端文档详情 | P2 | ✅ | `frontend/src/views/DocumentDetailView.vue` |
| 5.5 局部修改功能 | P2 | ⏳ | 待开发 |
| 5.6 导出 PDF | P3 | ⏳ | 待开发 |
| 5.7 文档版本历史 | P3 | ⏳ | 待开发 |

---

### ⏳ Phase 6: 付费系统 (未开始)

| 任务 | 优先级 | 状态 | 预估时间 |
|------|--------|------|----------|
| 6.1 会员模型 | P2 | ⏳ | 2h |
| 6.2 生成次数限制 | P2 | ⏳ | 2h |
| 6.3 支付集成（微信） | P3 | ⏳ | 4h |
| 6.4 前端会员页面 | P3 | ⏳ | 2h |

---

### ✅ Phase 4.5: AI 模型路由系统 (2026-03-26 完成)

| 任务 | 优先级 | 状态 | 备注 |
|------|--------|------|------|
| 4.5.1 模型注册中心 | P1 | ✅ | `backend/app/core/model_router.py` |
| 4.5.2 多模型调用器 | P1 | ✅ | 支持 Moonshot/DeepSeek/Qwen/GLM |
| 4.5.3 前端模型选择器 | P1 | ✅ | `frontend/src/components/ModelSelector.vue` |
| 4.5.4 成本统计系统 | P1 | ✅ | 后端自动记录每次调用成本 |
| 4.5.5 移除海外模型 | P1 | ✅ | 移除 Claude/OpenAI，仅保留国内模型 |

**支持的模型:**

| 模型 | 提供商 | 价格(输入/输出) | 特点 |
|------|--------|-----------------|------|
| Kimi K2.5 | Moonshot | ¥0.02/¥0.02 | 默认全能 |
| DeepSeek V3 | DeepSeek | ¥0.002/¥0.008 | 性价比首选 |
| Qwen Coder | 阿里云 | ¥0.004/¥0.012 | 代码生成 |
| GLM-4 | 智谱 | ¥0.005/¥0.005 | 中文优化 |

**快速配置预设:**
- ⚡ 极速模式: 全部 DeepSeek V3
- ⭐ 均衡模式: DeepSeek + Kimi 组合
- 🎯 质量优先: 全部 Kimi K2.5
- 🔬 仿真专用: DeepSeek + Kimi + Qwen

**成本统计:**
- 每次 AI 调用自动记录 token 消耗
- 按模型价格计算实际成本
- 文档生成完成后汇总总成本
- API: `GET /api/costs/document/{id}`

**待优化:**
- ⏳ 默认模型策略优化（当前全部使用 Kimi K2.5）
  - 方案A: 全部默认 DeepSeek V3（成本最低 ¥0.63）
  - 方案B: 按任务类型智能选择（大纲→DeepSeek, 章节→Kimi, 仿真→Qwen）
  - 需测试验证质量差异后再决定

**技术决策:**
- 模型配置使用 Pydantic 数据类
- 调用器支持 OpenAI 兼容格式
- 成本从 AI 响应日志解析 token 使用量
- 仅支持中国大陆可访问的模型

**定价策略:**

| 类型 | 权益 | 价格 |
|------|------|------|
| 免费用户 | 每月 3 次生成 | 免费 |
| 会员 | 每月 50 次生成 | ¥68/月 |
| 超额 | 额外生成 | ¥2/次 |

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue3 + TypeScript + Vite + Tailwind CSS |
| 后端 | Python + FastAPI + SQLAlchemy 2.0 |
| 数据库 | PostgreSQL (生产) / SQLite (开发) |
| AI | Kimi k2.5 (Moonshot) |
| 部署 | Docker + Docker Compose |

**AI 配置:**
```python
model = "kimi-k2.5"
max_tokens = 24000  # 支持最大 65535
temperature = 1.0   # k2.5 只支持 temperature=1
context_window = 256000
```

---

## 项目结构

```
tutorial/
├── doc/                          # 文档
│   ├── requirements.md           # 需求文档
│   ├── ARCHITECTURE.md           # 技术架构说明
│   ├── tasks.md                  # 任务清单 (本文件)
│   └── progress.md               # 项目进度文档
├── backend/                      # 后端
│   ├── app/
│   │   ├── api/                  # API 路由
│   │   ├── core/                 # 核心配置
│   │   │   ├── prompt_templates.py  # 分层 Prompt 配置
│   │   │   └── ...
│   │   ├── models/               # 数据模型
│   │   │   ├── generation_config.py # 配置模型
│   │   │   └── ...
│   │   └── services/             # 业务服务
│   │       ├── ai_service.py     # AI 生成（含配置化方法）
│   │       └── task_queue_service.py # 任务队列（含上下文传递）
│   └── ...
├── frontend/                     # 前端
│   └── ...
└── docker-compose.yml            # Docker 编排
```

---

## 下一步计划

### 本周 (3月24日-3月30日)
1. 继续优化仿真 Prompt，提高交互稳定性
2. 测试更多学科仿真效果
3. 开始 Phase 5 局部修改功能设计

### 下周 (3月31日-4月6日)
1. 实现局部修改功能
2. 测试付费系统流程
3. 准备 Phase 6 开发

---

## 文档索引

| 文档 | 路径 | 说明 |
|------|------|------|
| 需求文档 | `doc/requirements.md` | 产品需求定义 |
| 架构说明 | `doc/ARCHITECTURE.md` | 技术架构详解 |
| 任务清单 | `doc/tasks.md` | 开发进度跟踪 |
| 进度文档 | `doc/progress.md` | 最新进度汇总 |

---

*文档版本: v3.1*
*最后更新: 2026-03-26*
