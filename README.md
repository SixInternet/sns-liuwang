# SNS 六网空间

> Six Internet's Space — 个人数字孪生认知系统

## 技术栈

| 层 | 技术 |
|------|------|
| 后端 | Python FastAPI + SQLAlchemy 2.0 |
| 数据库 | PostgreSQL（开发环境可用 SQLite 替代） |
| 前端 | React 18 + TypeScript + Vite + Tailwind CSS |
| 认证 | JWT（HS256）+ bcrypt |

## 启动方式

### 后端

```bash
cd sns/backend

# 创建虚拟环境（首次）
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 启动 API 服务
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8001
```

API 文档：http://localhost:8001/docs

### 前端

```bash
cd sns/frontend

# 安装依赖（首次）
npm install

# 启动开发服务器
npm run dev
# 如需局域网访问，加 --host：
npx vite --host
```

前端地址：http://localhost:5173

### 数据库配置

创建 `sns/backend/.env`：

```env
DATABASE_URL=sqlite+aiosqlite:///./sns.db     # SQLite（开发用）
# DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/sns_liuwang   # PostgreSQL
APP_ENV=development
APP_PORT=8001
SECRET_KEY=your-secret-key-here
```

SQLite 无需额外安装，PostgreSQL 需自行安装并创建数据库 `sns_liuwang`。

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| POST | `/api/v1/auth/register` | 注册 |
| POST | `/api/v1/auth/login` | 登录 |
| GET | `/api/v1/auth/me?user_id=xxx` | 获取用户信息 |
| POST | `/api/v1/cards` | 创建卡片 |
| GET | `/api/v1/cards` | 卡片列表 |
| GET | `/api/v1/cards/{id}` | 卡片详情 |
| PATCH | `/api/v1/cards/{id}/status` | 更新卡片状态 |
