"""数据库引擎与会话管理 — 异步 SQLAlchemy 2.0 声明式"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass

from app.config import get_settings

# 全局异步引擎（延迟初始化，由 lifespan 调用 init_db 创建）
engine = None
async_session_factory: async_sessionmaker[AsyncSession] | None = None


class Base(DeclarativeBase):
    """SQLAlchemy 声明式基类，所有模型继承此类"""
    pass


async def init_db() -> None:
    """初始化数据库引擎与会话工厂，应用启动时调用一次"""
    global engine, async_session_factory

    settings = get_settings()
    is_sqlite = settings.database_url.startswith("sqlite")

    if is_sqlite:
        # SQLite 不支持连接池参数
        engine = create_async_engine(
            settings.database_url,
            echo=settings.is_dev,
        )
    else:
        engine = create_async_engine(
            settings.database_url,
            echo=settings.is_dev,
            pool_size=5,
            max_overflow=10,
        )

    async_session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def close_db() -> None:
    """关闭数据库引擎并释放资源，应用关闭时调用"""
    global engine, async_session_factory
    if engine is not None:
        await engine.dispose()
        engine = None
        async_session_factory = None


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 依赖注入：获取异步数据库会话"""
    if async_session_factory is None:
        raise RuntimeError("数据库未初始化，请先调用 init_db()")
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
