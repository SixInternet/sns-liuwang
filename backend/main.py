"""FastAPI 应用入口"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import router as v1_router
from app.auth.router import router as auth_router
from app.collector.scheduler import scheduler_manager
from app.database import init_db, close_db, Base


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """应用生命周期管理：初始化数据库、建表、清理"""
    # 启动：初始化数据库连接
    await init_db()

    # 自动根据模型建表（延迟引用 app.database.engine，避免 import 时捕获 None）
    import app.database as db_mod

    async with db_mod.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await scheduler_manager.start()

    yield

    await scheduler_manager.shutdown()
    await close_db()


app = FastAPI(title="六网 SNS", lifespan=lifespan)

# 跨域配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 v1 路由
app.include_router(v1_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "ok"}
