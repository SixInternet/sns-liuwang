# AGENTS.md — SNS 六网空间

> 个人数字孪生认知系统 — 信息卡片收集与分类 PWA

## 项目概览

前后端分离的单人项目，无 monorepo 工具链，无 CI/CD，无测试套件。

```
sns/                    ← 根目录
├── backend/            ← Python FastAPI（入口: main.py）
├── frontend/           ← React + Vite（入口: src/main.tsx）
├── docs/               ← 技术栈文档
└── sns/                ← 旧版前端残留，勿用
```

**⚠️ `sns/sns/` 目录是历史残留，不要编辑。真正的前端在 `sns/frontend/`。**

## 开发启动

### 后端（需要 Python ≥ 3.11）

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
# 创建 .env（参考 .env.example），开发用 SQLite 最简单
uvicorn main:app --host 0.0.0.0 --port 8001
```

- API 文档：http://localhost:8001/docs（FastAPI 自动生成 Swagger）
- 首次启动会自动建表（`Base.metadata.create_all`），不需要手动迁移
- **Alembic 已引入依赖但未初始化**（无 `alembic.ini`），目前不需要跑迁移命令

### 前端

```bash
cd frontend
npm install
npm run dev          # → http://localhost:5173
npm run build        # tsc -b && vite build（类型检查 + 打包）
npm run lint         # ESLint
```

- 局域网访问：`npx vite --host`
- PWA 支持（vite-plugin-pwa），开发时不影响

## 环境配置

后端 `backend/.env` 必需：

```env
DATABASE_URL=sqlite+aiosqlite:///./sns.db   # 开发用 SQLite
# DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/sns_liuwang  # 生产用
APP_ENV=development
APP_PORT=8001
SECRET_KEY=your-secret-key-here              # JWT 签名密钥
```

前端可选 `VITE_API_BASE`；未配置时与同页面主机 `:8001` 通信。登录/注册用 `fetch`，卡片列表等用 ky，均已接后端；`/api/v1/cards/*` 需 Bearer JWT。

## 架构要点

### 后端

- **入口**: `backend/main.py` — FastAPI app，lifespan 管理 DB 初始化/关闭
- **配置**: `app/config.py` — pydantic-settings 从 `.env` 加载，`get_settings()` 单例
- **数据库**: `app/database.py` — 异步 SQLAlchemy 2.0，`get_session()` 依赖注入
- **路由结构**:
  - `app/auth/router.py` → `/api/v1/auth/*`（注册/登录/用户信息）
  - `app/api/v1/cards.py` → `/api/v1/cards/*`（卡片 CRUD，**依赖 `get_current_user`**）
  - `app/api/v1/__init__.py` 汇总 v1 路由
- **分层**: `models/`（SQLAlchemy ORM）→ `schemas/`（Pydantic 请求/响应）→ `services/`（业务逻辑）→ `api/`（路由）
- **认证**: JWT HS256，30 分钟过期，`python-jose` 签发，`passlib + bcrypt` 哈希
- **CORS**: 全开放（`allow_origins=["*"]`）

### 前端

- **React 19** + TypeScript + Vite 8 + Tailwind CSS 4
- **HTTP 客户端**: ky（卡片 API）；登录/认证端点使用 `fetch` + `apiUrl`
- **状态管理**: TanStack React Query（已安装，尚未使用）
- **动画**: framer-motion（已安装，计划用于卡片滑动）
- **类型定义**: `src/types/index.ts` — `InfoCard` 接口
- **主流程**：登录/注册页 + `CardListPage`（列表、新建、PATCH 状态），已接后端 API

## 数据模型

- **User**: UUID 主键，username（唯一），bcrypt 哈希密码
- **InfoCard**: UUID 主键，title/summary/source_url/category/status 等，status 枚举: `pending/liked/disliked/valuable/valueless`

## 注意事项

- 卡片路由未带有效 JWT 时将返回 **401**，需先登录后再请求 `/api/v1/cards`
- **信息采集**：OpenClaw `hook:liuwang-space` 主会话直接执行（禁止 spawn）；ingest 提交 `content_html`；单次最多 10 条；进度见 `/api/v1/collector/progress`
- 项目没有测试，没有 CI，没有 pre-commit hooks
- `sns.db`（SQLite 数据库文件）在 `.gitignore` 中但已存在于目录，不要提交
