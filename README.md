# Tutorial 项目

## 快速开始

使用 Docker Compose 一键启动整个项目：

```bash
docker-compose up -d
```

## 服务说明

| 服务 | 端口 | 说明 |
|------|------|------|
| PostgreSQL | 5432 | 数据库服务，数据持久化到 Docker 卷 |
| 后端服务 | 8000 | API 服务，依赖数据库 |
| 前端服务 | 5173 | Vue 开发服务器，热重载 |

## 环境变量

### 后端环境变量
- `DATABASE_URL` - 完整数据库连接字符串
- `DB_HOST` - 数据库主机名 (db)
- `DB_PORT` - 数据库端口 (5432)
- `DB_NAME` - 数据库名 (tutorial_db)
- `DB_USER` - 数据库用户名
- `DB_PASSWORD` - 数据库密码

### 前端环境变量
- `VITE_API_URL` - 后端 API 地址

## 常用命令

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 停止并删除数据卷（谨慎使用）
docker-compose down -v

# 重建服务
docker-compose up -d --build
```

## 项目结构

```
tutorial/
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   └── ...
├── frontend/
│   ├── Dockerfile.dev
│   └── ...
└── README.md
```
