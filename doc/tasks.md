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

### 🔄 Phase 2: 用户系统
| 任务 | 优先级 | 预估时间 | 状态 |
|------|--------|---------|------|
| 2.1 用户模型 (User Model) | P0 | 1h | ⏳ |
| 2.2 注册/登录 API | P0 | 2h | ⏳ |
| 2.3 JWT 认证中间件 | P0 | 1h | ⏳ |
| 2.4 前端登录/注册页面联调 | P0 | 2h | ⏳ |
| 2.5 用户状态管理 (Pinia) | P1 | 1h | ⏳ |

**技术决策:**
- 密码加密: bcrypt
- Token: JWT (HS256)
- Token 有效期: 30 分钟

---

### 🔄 Phase 3: 核心生成
| 任务 | 优先级 | 预估时间 | 状态 |
|------|--------|---------|------|
| 3.1 AI 服务封装 (多模型) | P0 | 3h | ⏳ |
| 3.2 文档生成 API | P0 | 2h | ⏳ |
| 3.3 文档模型 (Document Model) | P0 | 1h | ⏳ |
| 3.4 前端生成页面联调 | P0 | 2h | ⏳ |
| 3.5 HTML 渲染组件 | P1 | 2h | ⏳ |

**技术决策:**
- AI 模型: Kimi (成本低) + Claude (复杂任务)
- 文档存储: PostgreSQL JSONB 字段
- 生成内容: 概念、讲解、重难点、仿真、总结、习题

---

### 🔄 Phase 4: 仿真系统
| 任务 | 优先级 | 预估时间 | 状态 |
|------|--------|---------|------|
| 4.1 仿真代码生成 (牛顿第二定律) | P1 | 4h | ⏳ |
| 4.2 仿真渲染组件 (Canvas) | P1 | 3h | ⏳ |
| 4.3 仿真代码嵌入 HTML | P1 | 2h | ⏳ |

**技术决策:**
- 物理仿真: Matter.js / Planck.js
- 电路仿真: CircuitJS
- 数学可视化: Chart.js / 自定义 Canvas
- AI 生成可交互的 JavaScript 代码

**测试用例:**
- 课程: 大学物理
- 知识点: 牛顿第二定律 F=ma
- 期望: 可调节 m 和 F，实时显示 a 和运动动画

---

### 🔄 Phase 5: 文档管理
| 任务 | 优先级 | 预估时间 | 状态 |
|------|--------|---------|------|
| 5.1 文档列表 API | P2 | 1h | ⏳ |
| 5.2 文档详情 API | P2 | 1h | ⏳ |
| 5.3 前端文档列表/详情联调 | P2 | 2h | ⏳ |
| 5.4 局部修改功能 (AI 编辑) | P2 | 4h | ⏳ |
| 5.5 导出 HTML/PDF | P3 | 2h | ⏳ |

---

### 🔄 Phase 6: 付费系统
| 任务 | 优先级 | 预估时间 | 状态 |
|------|--------|---------|------|
| 6.1 会员模型 (Subscription) | P2 | 2h | ⏳ |
| 6.2 生成次数限制中间件 | P2 | 2h | ⏳ |
| 6.3 支付集成 (微信支付) | P3 | 4h | ⏳ |
| 6.4 前端会员页面 | P3 | 2h | ⏳ |

**定价策略:**
| 类型 | 权益 | 价格 |
|------|------|------|
| 免费用户 | 每月 3 次生成 | 免费 |
| 会员 | 每月 50 次生成 | ¥68/月 |
| 超额 | 额外生成 | ¥2/次 |

**成本估算:**
- 单次生成成本: ~¥0.3-0.6 (Token 费用)
- 会员毛利: ~60%

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue3 + TypeScript + Vite + Tailwind CSS + Vue I18n |
| 后端 | Python + FastAPI + SQLAlchemy 2.0 |
| 数据库 | PostgreSQL (生产) / SQLite (开发) |
| AI | Kimi / Claude / GPT-4 |
| 部署 | Docker + Docker Compose |

---

## 项目结构

```
tutorial/
├── doc/                    # 文档
│   ├── requirements.md     # 需求文档
│   └── tasks.md           # 任务清单 (本文件)
├── backend/               # 后端
│   ├── app/
│   │   ├── api/          # API 路由
│   │   ├── core/         # 配置、数据库
│   │   ├── models/       # 数据模型
│   │   └── services/     # 业务逻辑
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/              # 前端
│   ├── src/
│   │   ├── api/          # API 客户端
│   │   ├── components/   # 组件
│   │   ├── i18n/         # 国际化
│   │   ├── router/       # 路由
│   │   ├── stores/       # Pinia Store
│   │   └── views/        # 页面
│   ├── Dockerfile
│   └── package.json
└── docker-compose.yml
```

---

## 下一步行动

**当前决策:**
1. 继续 Phase 2 用户系统
2. 跳过用户系统，先做 Phase 3 核心生成 (快速验证)
3. 先做仿真系统原型 (验证核心差异化功能)

**待确认:**
- AI 模型 API Key 配置
- 数据库使用 SQLite 还是 PostgreSQL
- 是否立即开始 Phase 2

---

*最后更新: 2026-03-19*
