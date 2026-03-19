# FastAPI Project

## 项目结构

```
app/
├── api/          # API 路由
├── core/         # 核心配置和数据库
├── models/       # SQLAlchemy 模型
├── services/     # 业务逻辑
└── main.py       # FastAPI 入口
```

## 环境配置

1. 复制 `.env.example` 为 `.env` 并配置环境变量
2. 安装依赖：`pip install -r requirements.txt`
3. 运行：`uvicorn app.main:app --reload`

## Docker 运行

```bash
docker build -t fastapi-app .
docker run -p 8000:8000 --env-file .env fastapi-app
```
