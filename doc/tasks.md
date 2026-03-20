# 智教云开发任务清单

## 项目概述
- **名称**: 智教云 - AI 课程知识点生成平台
- **目标用户**: 理工科教师
- **核心功能**: 输入课程+知识点 → AI生成互动教学文档

---

## 开发阶段

### ✅ Phase 1: 基础框架 (已完成)
| 任务 | 状态 | 备注 |
|------|------|------|
| 需求文档 | ✅ | requirements.md |
| 后端初始化 (FastAPI + SQLAlchemy) | ✅ | SQLite/PostgreSQL 双支持 |
| 前端初始化 (Vue3 + TS + Tailwind) | ✅ | 含路由、Pinia |
| Docker 配置 | ✅ | docker-compose.yml |
| 样式修复 (Tailwind v4) | ✅ | @tailwindcss/vite 插件 |
| 国际化 (i18n) | ✅ | 中文/英文切换 |

---

### ✅ Phase 2: 用户系统 (已完成)
| 任务 | 优先级 | 状态 | 备注 |
|------|--------|------|------|
| 2.1 用户模型 (User Model) | P0 | ✅ | `backend/app/models/user.py` |
| 2.2 注册/登录 API | P0 | ✅ | `backend/app/api/auth.py` |
| 2.3 JWT 认证中间件 | P0 | ✅ | `backend/app/core/security.py` |
| 2.4 前端登录/注册页面联调 | P0 | ✅ | `frontend/src/views/LoginView.vue` |
| 2.5 用户状态管理 (Pinia) | P1 | ✅ | `frontend/src/stores/auth.ts` |
| 2.6 邮箱验证码 | P0 | ✅ | `backend/app/services/email_service.py` |
| 2.7 多设备登录支持 | P1 | ✅ | `backend/app/models/user_device.py` |
| 2.8 忘记密码 | P1 | ✅ | `backend/app/api/auth.py` |

**技术决策:**
- 密码加密: bcrypt
- Token: JWT (HS256)
- Token 有效期: 120 分钟
- 邮箱服务: Office 365 (smtp.partner.outlook.cn)
- 设备指纹: 浏览器特征生成唯一标识

---

### ✅ Phase 3: 核心生成 (已完成)
| 任务 | 优先级 | 状态 | 文件 |
|------|--------|------|------|
| 3.1 AI 服务封装 | P0 | ✅ | `backend/app/services/ai_service.py` |
| 3.2 异步任务队列 | P0 | ✅ | `backend/app/services/task_queue_service.py` |
| 3.3 任务状态追踪 | P0 | ✅ | `backend/app/models/task_queue.py` |
| 3.4 大纲生成 API | P0 | ✅ | `backend/app/api/outline.py` |
| 3.5 文档生成 API | P0 | ✅ | `backend/app/api/outline.py` |
| 3.6 大纲模型 | P0 | ✅ | `backend/app/models/outline.py` |
| 3.7 文档模型 | P0 | ✅ | `backend/app/models/document.py` |
| 3.8 前端生成页面 | P0 | ✅ | `frontend/src/views/GenerateView.vue` |
| 3.9 前端大纲编辑 | P0 | ✅ | `frontend/src/views/OutlineEditView.vue` |
| 3.10 前端文档查看 | P0 | ✅ | `frontend/src/views/DocumentDetailView.vue` |
| 3.11 任务中心页面 | P1 | ✅ | `frontend/src/views/TasksView.vue` |
| 3.12 HTML 下载功能 | P1 | ✅ | `backend/app/api/document.py` |
| 3.13 完整 HTML 存储 | P1 | ✅ | `backend/app/services/ai_service.py` |
| 3.14 文件系统存储 | P1 | ✅ | `backend/app/services/file_storage_service.py` |
| 3.15 加载速度优化 | P1 | ✅ | KaTeX 替代 MathJax，国内 CDN |
| 3.16 文档生成并行化 | P1 | ✅ | 章节并行生成，速度提升 3-6 倍 |
| 3.17 Token 有效期延长 | P1 | ✅ | 7天有效期，减少频繁登录 |
| 3.18 时区显示修复 | P1 | ✅ | 后端统一返回 UTC 时间，前端自动转换 |
| 3.19 UI 细节优化 | P1 | ✅ | 任务中心边框、布局调整 |
| 3.20 时间格式统一 | P1 | ✅ | 所有 API 时间字段使用 format_datetime() |

**技术决策:**
- AI 模型: Kimi (Moonshot)
- 任务队列: PostgreSQL + asyncio (可扩展至 Redis)
- 公式渲染: KaTeX（比 MathJax 快 10 倍以上）
- CDN: BootCDN 国内节点
- 文档存储: 支持双模式（数据库/文件系统），通过 `STORAGE_TYPE` 配置切换
- 文档生成: 并行处理章节，理论速度提升 = 章节数 / 并发数

---

### 🔄 Phase 4: 仿真系统 (部分完成)
| 任务 | 优先级 | 状态 | 文件 |
|------|--------|------|------|
| 4.1 仿真代码生成 | P1 | ✅ | `backend/app/services/ai_service.py` |
| 4.2 仿真代码嵌入 | P1 | ✅ | `backend/app/services/task_queue_service.py` |
| 4.3 Canvas 渲染 | P1 | ✅ | 浏览器原生支持 |
| 4.4 仿真代码沙箱 | P2 | ⏳ | 待开发（安全考虑） |
| 4.5 更多学科仿真 | P2 | ⏳ | 物理、电路、数学等 |

---

### 🔄 Phase 5: 文档管理 (部分完成)
| 任务 | 优先级 | 状态 | 文件 |
|------|--------|------|------|
| 5.1 文档列表 API | P2 | ✅ | `backend/app/api/document.py` |
| 5.2 文档详情 API | P2 | ✅ | `backend/app/api/document.py` |
| 5.3 前端文档列表 | P2 | ✅ | `frontend/src/views/DocumentsView.vue` |
| 5.4 前端文档详情 | P2 | ✅ | `frontend/src/views/DocumentDetailView.vue` |
| 5.5 局部修改功能 | P2 | ⏳ | 待开发 |
| 5.6 导出 PDF | P3 | ⏳ | 待开发 |

---

### ⏳ Phase 6: 付费系统 (未开始)
| 任务 | 优先级 | 状态 | 预估时间 |
|------|--------|------|---------|
| 6.1 会员模型 | P2 | ⏳ | 2h |
| 6.2 生成次数限制 | P2 | ⏳ | 2h |
| 6.3 支付集成 | P3 | ⏳ | 4h |
| 6.4 前端会员页面 | P3 | ⏳ | 2h |

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
| AI | Kimi (Moonshot) |
| 部署 | Docker + Docker Compose |

---

## 项目结构

```
tutorial/
├── doc/                          # 文档
│   ├── requirements.md           # 需求文档
│   ├── ARCHITECTURE.md           # 技术架构说明
│   └── tasks.md                  # 任务清单 (本文件)
├── backend/                      # 后端
│   ├── app/
│   │   ├── api/                  # API 路由
│   │   │   ├── auth.py          # 认证接口
│   │   │   ├── outline.py       # 大纲/任务接口
│   │   │   └── document.py      # 文档接口
│   │   ├── core/                 # 核心配置
│   │   │   ├── config.py        # 应用配置
│   │   │   ├── database.py      # 数据库
│   │   │   └── security.py      # JWT 工具
│   │   ├── models/               # 数据模型
│   │   │   ├── user.py          # 用户
│   │   │   ├── user_device.py   # 设备
│   │   │   ├── outline.py       # 大纲
│   │   │   ├── document.py      # 文档
│   │   │   └── task_queue.py    # 任务队列
│   │   └── services/             # 业务服务
│   │       ├── ai_service.py    # AI 生成
│   │       ├── task_queue_service.py # 任务队列
│   │       ├── file_storage_service.py # 文件存储
│   │       ├── user_service.py  # 用户
│   │       └── email_service.py # 邮件
│   └── Dockerfile
├── frontend/                     # 前端
│   ├── src/
│   │   ├── api/                  # API 客户端
│   │   │   ├── index.ts         # 基础请求
│   │   │   ├── auth.ts          # 认证 API
│   │   │   └── outline.ts       # 大纲/任务 API
│   │   ├── components/           # 组件
│   │   │   ├── Layout.vue       # 布局
│   │   │   ├── Header.vue       # 头部
│   │   │   └── Sidebar.vue      # 侧边栏
│   │   ├── router/               # 路由
│   │   │   └── index.ts         # 路由配置
│   │   ├── stores/               # 状态管理
│   │   │   └── auth.ts          # 认证状态
│   │   ├── views/                # 页面
│   │   │   ├── LoginView.vue    # 登录
│   │   │   ├── RegisterView.vue # 注册
│   │   │   ├── GenerateView.vue # 生成大纲
│   │   │   ├── OutlineEditView.vue # 编辑大纲
│   │   │   ├── DocumentDetailView.vue # 文档详情
│   │   │   ├── DocumentsView.vue # 文档列表
│   │   │   └── TasksView.vue    # 任务中心
│   │   └── types/                # 类型定义
│   │       └── outline.ts       # 大纲类型
│   └── Dockerfile
└── docker-compose.yml            # Docker 编排
```

---

## 下一步计划

### 短期 (1-2 周)
1. **仿真系统完善**
   - 添加仿真代码沙箱（安全执行）
   - 支持更多学科仿真类型

2. **文档管理增强**
   - 实现局部修改功能
   - 添加导出 PDF 功能

### 中期 (1 个月)
3. **付费系统集成**
   - 会员模型设计
   - 微信支付集成
   - 生成次数限制

4. **性能优化**
   - 任务队列迁移至 Redis
   - 前端懒加载优化

### 长期 (3 个月)
5. **功能扩展**
   - 模板市场
   - 协作编辑
   - 学校/企业版

---

## 文档索引

| 文档 | 路径 | 说明 |
|------|------|------|
| 需求文档 | `doc/requirements.md` | 产品需求定义 |
| 架构说明 | `doc/ARCHITECTURE.md` | 技术架构详解 |
| 任务清单 | `doc/tasks.md` | 开发进度跟踪 |

---

*文档版本: v2.0*
*最后更新: 2026-03-20*
