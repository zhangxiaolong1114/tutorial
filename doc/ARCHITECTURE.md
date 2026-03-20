# 智教云 - 项目技术说明文档

## 项目概述

**智教云**是一个为理工科教师提供 AI 生成课程知识点教学文档的平台。

- **核心功能**: 输入课程 + 知识点 → AI 生成完整教学 HTML 文档
- **技术架构**: Vue3 + FastAPI + PostgreSQL + Docker
- **AI 服务**: Kimi API (Moonshot)

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
            └─────────────┘
```

---

## 模块详细说明

### 1. 用户认证系统 (Phase 2 - 已完成)

#### 1.1 功能设计
- **注册**: 邮箱 + 密码 + 验证码
- **登录**: 支持多设备，新设备需邮箱验证
- **密码找回**: 邮箱验证码重置
- **JWT Token**: 120 分钟有效期

#### 1.2 核心文件

| 文件 | 说明 |
|------|------|
| `backend/app/models/user.py` | User 模型：id, username, email, hashed_password, is_verified |
| `backend/app/models/user_device.py` | UserDevice 模型：设备指纹、信任状态 |
| `backend/app/api/auth.py` | 认证路由：注册、登录、验证码、重置密码 |
| `backend/app/services/user_service.py` | 用户业务逻辑：创建、验证、设备管理 |
| `backend/app/services/email_service.py` | 邮件服务：Office 365 SMTP |
| `backend/app/core/security.py` | JWT 生成与验证 |
| `frontend/src/views/LoginView.vue` | 登录页面 |
| `frontend/src/views/RegisterView.vue` | 注册页面 |
| `frontend/src/stores/auth.ts` | Pinia 认证状态管理 |

#### 1.3 关键流程

**多设备登录流程:**
```
用户登录
    ↓
检查设备指纹
    ├── 已信任设备 → 直接登录
    └── 新设备 → 发送验证码 → 验证成功 → 加入信任列表 → 登录
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

### 3. AI 内容生成系统 (Phase 3 - 已完成)

#### 3.1 功能设计
- **大纲生成**: 6 个标准章节（概念、讲解、重难点、仿真、总结、习题）
- **文档生成**: 为每个章节生成详细 HTML 内容
- **仿真代码**: 生成可交互的 Canvas 仿真
- **Markdown 清理**: 自动去除 AI 返回的代码块标记

#### 3.2 核心文件

| 文件 | 说明 |
|------|------|
| `backend/app/services/ai_service.py` | AI 服务封装：Kimi API 调用、内容生成、代码清理 |
| `backend/app/models/outline.py` | Outline 模型：大纲结构、JSON 存储 |
| `backend/app/models/document.py` | Document 模型：HTML 内容、章节信息 |
| `backend/app/api/outline.py` | 大纲/文档 API 路由 |
| `frontend/src/views/GenerateView.vue` | 生成大纲页面 |
| `frontend/src/views/OutlineEditView.vue` | 编辑大纲、生成文档 |

#### 3.3 Prompt 设计

**大纲生成 Prompt:**
```
你是一个专业的教育内容设计师...
生成包含以下章节的大纲：
1. 知识点概念
2. 详细讲解
3. 重难点分析
4. 交互仿真
5. 总结
6. 习题与答案
返回 JSON 格式
```

**章节内容 Prompt:**
```
为以下章节生成详细的教学 HTML 内容...
使用丰富的 HTML 标签、CSS 类名
公式用 \( ... \) 或 \[ ... \]
```

---

### 4. 文档查看与下载系统 (Phase 3 - 已完成)

#### 4.1 功能设计
- **平台预览**: 直接显示原始 HTML
- **下载 HTML**: 包含完整样式、MathJax、响应式设计
- **公式渲染**: MathJax CDN 支持
- **中文文件名**: UTF-8 编码支持

#### 4.2 核心文件

| 文件 | 说明 |
|------|------|
| `backend/app/api/document.py` | 文档 API：获取详情、下载 HTML |
| `frontend/src/views/DocumentDetailView.vue` | 文档详情页（平台预览） |
| `frontend/src/views/DocumentsView.vue` | 文档列表页 |
| `frontend/src/styles/document.css` | 共享样式文件（已废弃） |

#### 4.3 下载 HTML 结构

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>文档标题</title>
    <!-- MathJax 公式渲染 -->
    <script src="https://cdn.jsdelivr.net/npm/mathjax@3/..."></script>
    <!-- 内嵌 CSS 样式 -->
    <style>
        /* 渐变背景、卡片布局、彩色章节 */
    </style>
</head>
<body>
    <div class="document-container">
        <div class="document-header">
            <h1>标题</h1>
        </div>
        <div class="document-body">
            <!-- AI 生成的章节内容 -->
        </div>
    </div>
</body>
</html>
```

---

### 5. 前端架构

#### 5.1 项目结构

```
frontend/src/
├── api/                    # API 客户端
│   ├── index.ts           # 基础请求封装（含 JWT、401 处理）
│   ├── auth.ts            # 认证相关 API
│   └── outline.ts         # 大纲/文档/任务 API
├── components/            # 公共组件
│   ├── Layout.vue         # 布局框架
│   ├── Header.vue         # 顶部导航
│   └── Sidebar.vue        # 侧边栏导航
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
└── types/                 # TypeScript 类型
    └── outline.ts         # 大纲/任务类型定义
```

#### 5.2 状态管理

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

### 6. 后端架构

#### 6.1 项目结构

```
backend/app/
├── api/                   # API 路由
│   ├── auth.py           # 认证路由
│   ├── outline.py        # 大纲/任务路由
│   ├── document.py       # 文档路由
│   └── deps.py           # 依赖注入（获取当前用户）
├── core/                  # 核心配置
│   ├── config.py         # 应用配置
│   ├── database.py       # 数据库连接
│   └── security.py       # JWT 工具
├── models/                # 数据模型
│   ├── user.py           # 用户模型
│   ├── user_device.py    # 设备模型
│   ├── outline.py        # 大纲模型
│   ├── document.py       # 文档模型
│   └── task_queue.py     # 任务队列模型
└── services/              # 业务服务
    ├── ai_service.py     # AI 生成服务
    ├── task_queue_service.py # 任务队列服务
    ├── user_service.py   # 用户服务
    └── email_service.py  # 邮件服务
```

#### 6.2 数据库模型关系

```
User (1)
 ├── UserDevice (N)      # 用户的多个设备
 ├── Outline (N)         # 用户的多个大纲
 │    └── Document (N)   # 大纲生成的多个文档
 └── TaskQueue (N)       # 用户的多个任务
```

---

## API 接口清单

### 认证接口 (`/auth`)

| 接口 | 方法 | 说明 | 文件 |
|------|------|------|------|
| `/auth/register` | POST | 用户注册 | `auth.py` |
| `/auth/login` | POST | 用户登录 | `auth.py` |
| `/auth/verify-login` | POST | 验证码登录 | `auth.py` |
| `/auth/send-verification-code` | POST | 发送验证码 | `auth.py` |
| `/auth/reset-password` | POST | 重置密码 | `auth.py` |
| `/auth/me` | GET | 获取当前用户 | `auth.py` |

### 大纲接口 (`/outlines`)

| 接口 | 方法 | 说明 | 文件 |
|------|------|------|------|
| `/outlines/generate` | POST | 异步生成大纲 | `outline.py` |
| `/outlines/` | GET | 大纲列表 | `outline.py` |
| `/outlines/{id}` | GET | 大纲详情 | `outline.py` |
| `/outlines/{id}` | PUT | 更新大纲 | `outline.py` |
| `/outlines/{id}` | DELETE | 删除大纲 | `outline.py` |
| `/outlines/{id}/generate-doc` | POST | 异步生成文档 | `outline.py` |
| `/outlines/tasks` | GET | 任务列表 | `outline.py` |
| `/outlines/tasks/{id}` | GET | 任务状态 | `outline.py` |

### 文档接口 (`/documents`)

| 接口 | 方法 | 说明 | 文件 |
|------|------|------|------|
| `/documents/` | GET | 文档列表 | `document.py` |
| `/documents/{id}` | GET | 文档详情 | `document.py` |
| `/documents/{id}/download` | GET | 下载 HTML | `document.py` |
| `/documents/{id}` | DELETE | 删除文档 | `document.py` |

---

## 关键技术决策

### 1. 异步任务队列

**选择**: PostgreSQL + Python asyncio

**原因**:
- 项目初期，避免引入 Redis/MQ 复杂度
- 数据库事务保证任务不丢失
- 足够支撑初期并发量

**未来扩展**: 可无缝迁移到 Celery + Redis

### 2. AI 模型选择

**选择**: Kimi (Moonshot)

**原因**:
- 中文理解能力强
- 成本较低
- 国内访问稳定

**备选**: Claude (复杂代码生成)、GPT-4 (高质量内容)

### 3. 公式渲染

**选择**: MathJax

**原因**:
- 支持 LaTeX 语法
- 浏览器直接渲染，无需后端处理
- 下载的 HTML 离线可用

### 4. 数据库

**开发**: SQLite (零配置)
**生产**: PostgreSQL (高性能、并发)

---

## 已知问题与 TODO

### 已修复
- ✅ 验证码过期后重新发送报错
- ✅ 异步任务 401 错误处理
- ✅ Markdown 代码块清理
- ✅ 中文文件名下载

### 待优化
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

*文档版本: v1.0*
*最后更新: 2026-03-20*
