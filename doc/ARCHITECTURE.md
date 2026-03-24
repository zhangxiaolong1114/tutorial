# 智教云 - 项目技术说明文档

## 项目概述

**智教云**是一个为理工科教师提供 AI 生成课程知识点教学文档的平台。

- **核心功能**: 输入课程 + 知识点 → AI 生成完整教学 HTML 文档
- **技术架构**: Vue3 + FastAPI + PostgreSQL + Docker + Kimi AI
- **AI 服务**: Kimi k2.5 (Moonshot)
- **当前状态**: Phase 4 配置化生成已完成，Phase 5-6 开发中

---

## 系统架构

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   前端 (Vue3)    │────→│  后端 (FastAPI)  │────→│   AI (Kimi)     │
│  - 用户界面      │     │  - 业务逻辑      │     │  - 内容生成      │
│  - 状态管理      │     │  - 任务队列      │     │  - 仿真代码      │
│  - 路由导航      │     │  - 数据持久化    │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                       │
         └───────────────────────┘
                   │
            ┌─────────────┐
            │  PostgreSQL │
            │  - 用户数据  │
            │  - 大纲数据  │
            │  - 文档数据  │
            │  - 任务队列  │
            │  - 生成配置  │
            └─────────────┘
```

---

## 模块详细说明

### 1. 用户认证系统 (Phase 2 - 已完成)

#### 1.1 功能设计
- **注册**: 邮箱 + 密码 + 验证码
- **登录**: 支持多设备，新设备需邮箱验证
- **密码找回**: 邮箱验证码重置
- **JWT Token**: 双 Token 架构
  - Access Token: 30 分钟短期有效
  - Refresh Token: 7 天长期有效
  - 自动静默刷新，用户无感知

#### 1.2 核心文件

| 文件 | 说明 |
|------|------|
| `backend/app/models/user.py` | User 模型：id, username, email, hashed_password, is_verified |
| `backend/app/models/user_device.py` | UserDevice 模型：设备指纹、信任状态 |
| `backend/app/api/auth.py` | 认证路由：注册、登录、验证码、重置密码 |
| `backend/app/services/user_service.py` | 用户业务逻辑：创建、验证、设备管理 |
| `backend/app/services/email_service.py` | 邮件服务：Office 365 SMTP |
| `backend/app/core/security.py` | JWT 生成与验证（含 Refresh Token） |
| `backend/app/api/auth.py` | 新增 `/auth/refresh` 刷新接口 |
| `frontend/src/api/auth.ts` | axios 响应拦截器自动刷新 |
| `frontend/src/api/index.ts` | fetch 封装支持自动刷新 |
| `frontend/src/views/LoginView.vue` | 登录页面 |
| `frontend/src/views/RegisterView.vue` | 注册页面 |
| `frontend/src/stores/auth.ts` | Pinia 认证状态管理 |

#### 1.3 关键流程

**多设备登录流程:**
```
用户登录
    ↓
检查设备指纹
    ├── 已信任设备 → 直接登录 → 返回 Access Token + Refresh Token
    └── 新设备 → 发送验证码 → 验证成功 → 加入信任列表 → 登录
```

**Token 刷新流程:**
```
API 请求
    ↓
Access Token 过期 (401)
    ↓
自动调用 /auth/refresh
    ↓
使用 Refresh Token 获取新 Access Token
    ↓
重试原请求（用户无感知）
    ↓
Refresh Token 也过期 → 跳转登录页
```

**并发请求处理:**
```
请求 A → 发现 401 → 开始刷新
请求 B → 发现 401 → 加入等待队列
请求 C → 发现 401 → 加入等待队列
    ↓
刷新完成 → 新 Token 通知所有等待请求
    ↓
A/B/C 使用新 Token 重试
```

---

### 2. 任务队列系统 (Phase 3 - 已完成)

#### 2.1 功能设计
- **异步处理**: AI 生成大纲/文档不阻塞接口
- **高并发**: 支持多 Worker 并行处理
- **状态追踪**: pending → processing → completed/failed
- **生命周期管理**: 任务中心可查看所有任务状态

#### 2.2 核心文件

| 文件 | 说明 |
|------|------|
| `backend/app/models/task_queue.py` | TaskQueue 模型：任务状态、参数、结果 |
| `backend/app/services/task_queue_service.py` | 任务队列服务：创建、执行、查询 |
| `backend/app/api/outline.py` | 异步接口：/outlines/generate, /outlines/{id}/generate-doc |
| `backend/app/main.py` | 启动/停止任务队列 Worker |
| `frontend/src/views/TasksView.vue` | 任务中心页面 |
| `frontend/src/views/GenerateView.vue` | 生成大纲页面（含轮询） |
| `frontend/src/views/OutlineEditView.vue` | 大纲编辑页面（含生成文档任务） |

#### 2.3 关键流程

**异步生成流程:**
```
用户请求生成
    ↓
立即返回任务ID (< 100ms)
    ↓
后台 Worker 处理 AI 生成
    ↓
轮询查询任务状态
    ↓
完成 → 显示结果
```

---

### 3. AI 内容生成系统 (Phase 3-4 - 已完成)

#### 3.1 功能设计
- **大纲生成**: 6 个标准章节（概念、讲解、重难点、仿真、总结、习题）
- **文档生成**: 为每个章节生成详细 HTML 内容
- **仿真代码**: 生成可交互的 Canvas 仿真
- **配置化生成**: 13个配置字段自定义生成风格
- **Markdown 清理**: 自动去除 AI 返回的代码块标记

#### 3.2 核心文件

| 文件 | 说明 |
|------|------|
| `backend/app/services/ai_service.py` | AI 服务封装：Kimi API 调用、内容生成、代码清理 |
| `backend/app/core/prompt_templates.py` | 分层 Prompt 工程：5层架构配置化生成 |
| `backend/app/models/outline.py` | Outline 模型：大纲结构、JSON 存储 |
| `backend/app/models/document.py` | Document 模型：HTML 内容、章节信息 |
| `backend/app/models/generation_config.py` | GenerationConfig 模型：13个配置字段 |
| `backend/app/api/outline.py` | 大纲/文档 API 路由 |
| `backend/app/api/generation_config.py` | 生成配置 API 路由 |
| `frontend/src/views/GenerateView.vue` | 生成大纲页面 |
| `frontend/src/views/OutlineEditView.vue` | 编辑大纲、生成文档 |
| `frontend/src/components/GenerationConfigPanel.vue` | 生成配置面板组件 |

#### 3.3 分层 Prompt 工程

**5层架构设计:**
```
第一层: 角色定义（风格层）- 12种角色组合
├── tone: formal/casual/rigorous
├── target_audience: undergraduate/graduate/engineer/high_school
└── 组合出 12 种不同角色

第二层: 内容结构（结构层）- 4种教学结构
├── teaching_style: progressive/case_driven/problem_based/comparative
└── 决定内容组织方式

第三层: 深度控制（深度层）- 9种公式处理组合
├── difficulty: beginner/intermediate/advanced
├── formula_detail: conclusion_only/derivation/full_proof
└── 组合出 9 种深度配置

第四层: 增强指令（增强层）- 代码/配图
├── code_language: python/java/cpp/pseudocode/none
├── need_images: true/false
└── 控制额外内容

第五层: 统一约束（约束层）- 格式/长度
├── output_format: lecture/ppt_outline/lab_manual/cheatsheet
├── chapter_granularity: brief/standard/detailed
├── citation_style: none/simple/academic
└── 控制输出格式
```

**13个配置字段:**
| 字段 | 说明 | 选项 |
|------|------|------|
| tone | 语气风格 | formal/casual/rigorous |
| target_audience | 目标受众 | undergraduate/graduate/engineer/high_school |
| teaching_style | 教学风格 | progressive/case_driven/problem_based/comparative |
| content_style | 内容样式 | concise/detailed/visual/formula_heavy |
| difficulty | 难度等级 | beginner/intermediate/advanced |
| formula_detail | 公式详细度 | conclusion_only/derivation/full_proof |
| output_format | 输出格式 | lecture/ppt_outline/lab_manual/cheatsheet |
| code_language | 代码语言 | python/java/cpp/pseudocode/none |
| chapter_granularity | 章节粒度 | brief/standard/detailed |
| citation_style | 引用规范 | none/simple/academic |
| interactive_elements | 互动元素 | thinking/exercise/quiz/none |
| need_simulation | 需要仿真 | true/false |
| simulation_types | 仿真类型 | animation/interactive |

#### 3.4 上下文连贯性生成

**设计目标**: 确保文档各章节之间内容连贯、术语一致

**实现方式**:
```python
context = {
    "outline_structure": "大纲结构",
    "position": {
        "current_index": i,
        "total": n,
        "prev_title": "前一章标题",
        "next_title": "后一章标题"
    },
    "prev_summary": {
        "title": "前一章标题",
        "content": "前一章内容摘要（前500字符）"
    },
    "generated_sections": "已生成章节列表"
}
```

**生成策略**:
- 串行生成章节（非并行），确保上下文传递
- 前一章摘要自动提取，用于下一章上下文
- Prompt 中提供"前置知识"提示，但不强制生硬衔接

#### 3.5 自动续生成机制

**问题**: 复杂仿真代码可能超出 max_tokens 限制被截断

**解决方案**:
```python
# 检测截断
if finish_reason == "length" and not is_complete:
    # 自动发送续生成请求
    current_messages.append({
        "role": "assistant",
        "content": content
    })
    current_messages.append({
        "role": "user",
        "content": "请继续生成剩余内容，保持格式一致。从上次中断的地方继续，不要重复已生成的内容。"
    })
```

**配置**:
- max_tokens: 24000（kimi-k2.5 支持最大 65535）
- 最大续生成次数: 5 次
- 重复内容检测: 避免浪费 token

---

### 4. 配置化生成系统 (Phase 4 - 新增)

#### 4.1 功能设计
- **配置管理**: 保存用户的生成偏好配置
- **配置历史**: 查看和复用历史配置
- **最新配置**: 自动恢复上次使用的配置
- **前端配置面板**: 可视化配置表单

#### 4.2 核心文件

| 文件 | 说明 |
|------|------|
| `backend/app/models/generation_config.py` | GenerationConfig 模型：13个配置字段 |
| `backend/app/schemas/generation_config.py` | Pydantic  schemas |
| `backend/app/api/generation_config.py` | 配置 API：CRUD 接口 |
| `frontend/src/types/generationConfig.ts` | TypeScript 类型定义 |
| `frontend/src/api/generationConfig.ts` | 配置 API 客户端 |
| `frontend/src/components/GenerationConfigPanel.vue` | 配置面板组件 |

#### 4.3 API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/generation-configs` | POST | 创建配置 |
| `/generation-configs` | GET | 获取配置历史列表 |
| `/generation-configs/latest` | GET | 获取最新配置 |
| `/generation-configs/{id}` | GET | 获取配置详情 |
| `/generation-configs/{id}` | DELETE | 删除配置 |

#### 4.4 前端配置面板

**组件**: `GenerationConfigPanel.vue`

**功能**:
- 分组展示配置项（风格/难度/结构/深度/仿真）
- 难度等级可视化选择（卡片式）
- 配置说明和提示
- 与生成表单集成

---

### 5. 仿真系统 (Phase 4.5 - 优化中)

#### 5.1 功能设计
- **仿真代码生成**: AI 生成 Canvas 交互仿真
- **代码提取**: 自动提取和清理仿真代码
- **代码完整性**: 自动续生成确保代码完整
- **关联性保证**: 仿真内容与文档理论一致

#### 5.2 核心文件

| 文件 | 说明 |
|------|------|
| `backend/app/services/ai_service.py` | `_extract_simulation_content()` 提取仿真代码 |
| `backend/app/services/task_queue_service.py` | 传递上下文到仿真生成 |
| `backend/app/core/prompt_templates.py` | 仿真 Prompt 和约束 |

#### 5.3 仿真代码提取

**问题**: Kimi 有时将 `<script>` 和 `<style>` 放在 `</div>` 外部

**解决方案**:
```python
def _extract_simulation_content(self, html: str) -> str:
    # 查找 simulation-container div
    # 如果 script/style 在容器外部，自动移到容器内
    # 保持正确顺序：HTML → Style → Script → </div>
```

#### 5.4 仿真代码完整性验证

**检查项**:
- `simulation-container` 标签存在
- `script` 标签匹配（开启=闭合）
- IIFE 正确闭合 `})();`
- Canvas 2d context 初始化
- 关键帧数据完整（动画类型）
- 无省略性注释

#### 5.5 交互事件绑定

**要求**:
- 滑块使用 `oninput` 事件（不是 `onchange`）
- 按钮使用 `onclick` 事件
- 实时响应，无延迟

**Prompt 示例**:
```javascript
// 滑块事件 - 使用 oninput 实现实时响应
slider.oninput = function() {
    const value = parseFloat(this.value);
    valueDisplay.textContent = value.toFixed(2);
    updateSimulation(value);
    draw();
};
```

---

### 6. 文档查看与下载系统 (Phase 3 - 已完成)

#### 6.1 功能设计
- **平台预览**: 直接显示原始 HTML
- **下载 HTML**: 包含完整样式、KaTeX、响应式设计
- **公式渲染**: KaTeX CDN 支持
- **中文文件名**: UTF-8 编码支持

#### 6.2 核心文件

| 文件 | 说明 |
|------|------|
| `backend/app/api/document.py` | 文档 API：获取详情、下载 HTML |
| `frontend/src/views/DocumentDetailView.vue` | 文档详情页（平台预览） |
| `frontend/src/views/DocumentsView.vue` | 文档列表页 |

#### 6.3 下载 HTML 结构

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>文档标题</title>
    <!-- KaTeX 公式渲染 -->
    <link rel="stylesheet" href="https://cdn.bootcdn.net/ajax/libs/KaTeX/0.16.9/katex.min.css">
    <script defer src="https://cdn.bootcdn.net/ajax/libs/KaTeX/0.16.9/katex.min.js"></script>
    <script defer src="https://cdn.bootcdn.net/ajax/libs/KaTeX/0.16.9/contrib/auto-render.min.js"></script>
    <script>
        document.addEventListener("DOMContentLoaded", function() {
            if (typeof renderMathInElement !== 'undefined') {
                renderMathInElement(document.body, {
                    delimiters: [
                        {left: '$$', right: '$$', display: true},
                        {left: '$', right: '$', display: false}
                    ],
                    throwOnError: false
                });
            }
        });
    </script>
    <!-- 内嵌 CSS 样式 -->
    <style>...</style>
</head>
<body>...</body>
</html>
```

---

### 7. 前端架构

#### 7.1 项目结构

```
frontend/src/
├── api/                    # API 客户端
│   ├── index.ts           # 基础请求封装（含 JWT、401 处理）
│   ├── auth.ts            # 认证相关 API
│   ├── outline.ts         # 大纲/文档/任务 API
│   └── generationConfig.ts # 生成配置 API
├── components/            # 公共组件
│   ├── Layout.vue         # 布局框架
│   ├── Header.vue         # 顶部导航
│   ├── Sidebar.vue        # 侧边栏导航
│   └── GenerationConfigPanel.vue # 生成配置面板
├── router/                # 路由配置
│   └── index.ts           # 路由定义 + 导航守卫
├── stores/                # Pinia 状态管理
│   └── auth.ts            # 认证状态
├── views/                 # 页面视图
│   ├── LoginView.vue      # 登录
│   ├── RegisterView.vue   # 注册
│   ├── GenerateView.vue   # 生成大纲
│   ├── OutlineEditView.vue # 编辑大纲
│   ├── DocumentDetailView.vue # 文档详情
│   ├── DocumentsView.vue  # 文档列表
│   └── TasksView.vue      # 任务中心
├── types/                 # TypeScript 类型
│   ├── outline.ts         # 大纲/任务类型
│   └── generationConfig.ts # 生成配置类型
└── ...
```

#### 7.2 状态管理

**认证状态 (Pinia):**
```typescript
const authStore = useAuthStore()
authStore.token      // JWT Token
authStore.user       // 当前用户信息
authStore.isAuthenticated  // 是否登录
authStore.login()    // 登录方法
authStore.logout()   // 登出方法
```

---

### 8. 后端架构

#### 8.1 项目结构

```
backend/app/
├── api/                   # API 路由
│   ├── auth.py           # 认证路由
│   ├── outline.py        # 大纲/任务路由
│   ├── document.py       # 文档路由
│   ├── generation_config.py # 生成配置路由
│   └── deps.py           # 依赖注入（获取当前用户）
├── core/                  # 核心配置
│   ├── config.py         # 应用配置
│   ├── database.py       # 数据库连接
│   ├── security.py       # JWT 工具
│   └── prompt_templates.py # 分层 Prompt 配置
├── models/                # 数据模型
│   ├── user.py           # 用户模型
│   ├── user_device.py    # 设备模型
│   ├── outline.py        # 大纲模型
│   ├── document.py       # 文档模型
│   ├── task_queue.py     # 任务队列模型
│   └── generation_config.py # 生成配置模型
└── services/              # 业务服务
    ├── ai_service.py     # AI 生成服务
    ├── task_queue_service.py # 任务队列服务
    ├── file_storage_service.py # 文件存储服务
    ├── user_service.py   # 用户服务
    └── email_service.py  # 邮件服务
```

#### 8.2 数据库模型关系

```
User (1)
 ├── UserDevice (N)           # 用户的多个设备
 ├── Outline (N)              # 用户的多个大纲
 │    └── Document (N)        # 大纲生成的多个文档
 ├── TaskQueue (N)            # 用户的多个任务
 └── GenerationConfig (N)     # 用户的多个生成配置
```

---

## API 接口清单

### 认证接口 (`/auth`)

| 接口 | 方法 | 说明 | 文件 |
|------|------|------|------|
| `/auth/register` | POST | 用户注册 | `auth.py` |
| `/auth/login` | POST | 用户登录（返回双 Token） | `auth.py` |
| `/auth/verify-login` | POST | 验证码登录（返回双 Token） | `auth.py` |
| `/auth/refresh` | POST | 刷新 Access Token | `auth.py` |
| `/auth/send-verification-code` | POST | 发送验证码 | `auth.py` |
| `/auth/reset-password` | POST | 重置密码 | `auth.py` |
| `/auth/me` | GET | 获取当前用户 | `auth.py` |

### 大纲接口 (`/outlines`)

| 接口 | 方法 | 说明 | 文件 |
|------|------|------|------|
| `/outlines/generate` | POST | 异步生成大纲（支持配置） | `outline.py` |
| `/outlines/` | GET | 大纲列表 | `outline.py` |
| `/outlines/{id}` | GET | 大纲详情 | `outline.py` |
| `/outlines/{id}` | PUT | 更新大纲 | `outline.py` |
| `/outlines/{id}` | DELETE | 删除大纲 | `outline.py` |
| `/outlines/{id}/generate-doc` | POST | 异步生成文档（支持配置） | `outline.py` |
| `/outlines/tasks` | GET | 任务列表 | `outline.py` |
| `/outlines/tasks/{id}` | GET | 任务状态 | `outline.py` |

### 文档接口 (`/documents`)

| 接口 | 方法 | 说明 | 文件 |
|------|------|------|------|
| `/documents/` | GET | 文档列表 | `document.py` |
| `/documents/{id}` | GET | 文档详情 | `document.py` |
| `/documents/{id}/download` | GET | 下载 HTML | `document.py` |
| `/documents/{id}` | DELETE | 删除文档 | `document.py` |

### 生成配置接口 (`/generation-configs`)

| 接口 | 方法 | 说明 | 文件 |
|------|------|------|------|
| `/generation-configs` | POST | 创建配置 | `generation_config.py` |
| `/generation-configs` | GET | 配置历史列表 | `generation_config.py` |
| `/generation-configs/latest` | GET | 获取最新配置 | `generation_config.py` |
| `/generation-configs/{id}` | GET | 配置详情 | `generation_config.py` |
| `/generation-configs/{id}` | DELETE | 删除配置 | `generation_config.py` |

---

## 关键技术决策

### 1. 异步任务队列

**选择**: PostgreSQL + Python asyncio

**原因**:
- 项目初期，避免引入 Redis/MQ 复杂度
- 数据库事务保证任务不丢失
- 足够支撑初期并发量

**未来扩展**: 可无缝迁移到 Celery + Redis

### 2. AI 模型策略

**当前配置**:
```python
model = "kimi-k2.5"
max_tokens = 24000      # 支持最大 65535
temperature = 1.0       # k2.5 只支持 temperature=1
context_window = 256000 # 256k 上下文
```

**选择原因**:
- 中文理解能力强
- 上下文长度 256k，适合长文档
- 成本较低
- 国内访问稳定

**备选**: Claude (复杂代码生成)、GPT-4 (高质量内容)

### 3. 公式渲染

**选择**: KaTeX

**原因**:
- 比 MathJax 快 10 倍以上
- 国内 CDN 支持 (BootCDN)
- 浏览器直接渲染，无需后端处理
- 下载的 HTML 离线可用

### 4. 数据库

**开发**: SQLite (零配置)
**生产**: PostgreSQL (高性能、并发)

### 5. 配置化生成设计

**设计原则**:
- 分层配置：风格/结构/深度/增强/约束
- 组合爆炸：12种角色 × 4种结构 × 9种深度 = 432种组合
- 灵活扩展：新增配置字段不影响现有逻辑

---

## 已知问题与 TODO

### 已修复 ✅
- ✅ 验证码过期后重新发送报错
- ✅ 异步任务 401 错误处理
- ✅ Markdown 代码块清理
- ✅ 中文文件名下载
- ✅ Token 刷新机制（双 Token 架构）
- ✅ API 超时与重试机制（6分钟超时 + 3次重试）
- ✅ 详细日志配置（按模块分离日志文件）
- ✅ HTML 结构统一（section-content 包装）
- ✅ 大纲数据验证（自动清理无效内容）
- ✅ 公式渲染修复（统一使用 $ 分隔符）
- ✅ 时区统一（所有时间字段使用 UTC）
- ✅ 仿真代码完整性（max_tokens 24000 + 续生成）
- ✅ 仿真代码提取（自动处理外部 script/style）
- ✅ 仿真与文档关联性（上下文传递）
- ✅ 章节衔接优化（移除生硬衔接要求）
- ✅ 标签验证修复（放宽 section 标签检查）
- ✅ k2.5 模型兼容（temperature=1.0 自动设置）

### 待优化 ⏳
- ⏳ 仿真交互稳定性（持续优化 Prompt）
- ⏳ 仿真代码执行沙箱（安全）
- ⏳ 文档局部编辑功能
- ⏳ 更多学科仿真类型
- ⏳ 付费系统集成

---

## 部署说明

### 开发环境
```bash
cd tutorial
docker-compose up -d
```

### 环境变量
```bash
# backend/.env
DATABASE_URL=sqlite:///./test.db
SECRET_KEY=your-secret-key
KIMI_API_KEY=sk-...
SMTP_USER=...
SMTP_PASSWORD=...
```

---

## 文档索引

| 文档 | 路径 | 说明 |
|------|------|------|
| 需求文档 | `doc/requirements.md` | 产品需求定义 |
| 架构说明 | `doc/ARCHITECTURE.md` | 技术架构详解（本文件） |
| 任务清单 | `doc/tasks.md` | 开发进度跟踪 |
| 进度文档 | `doc/progress.md` | 最新进度汇总 |

---

*文档版本: v2.0*
*最后更新: 2026-03-24*
