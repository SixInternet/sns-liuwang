"""搜索源（SearchSource）业务逻辑服务"""

from urllib.parse import urlparse
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.search_source import SearchSource
from app.models.topic import topic_search_sources
from app.schemas.search_source import SearchSourceCreate


async def create_search_source(
    db: AsyncSession, body: SearchSourceCreate, user_id: UUID
) -> SearchSource:
    """创建搜索源，自动从 base_url 提取 domain"""
    parsed = urlparse(body.base_url)
    domain = parsed.hostname or body.base_url

    source = SearchSource(
        title=body.title,
        base_url=body.base_url,
        domain=domain,
        auth_notes=body.auth_notes,
        user_id=user_id,
    )
    db.add(source)
    await db.commit()
    await db.refresh(source)
    return source


async def list_search_sources(
    db: AsyncSession, user_id: UUID, skip: int = 0, limit: int = 20
) -> tuple[list[SearchSource], int]:
    """获取当前用户的搜索源列表，含关联 topics 数量"""
    count_q = await db.execute(
        select(func.count())
        .select_from(SearchSource)
        .where(SearchSource.user_id == user_id)
    )
    total = count_q.scalar() or 0

    result = await db.execute(
        select(SearchSource)
        .where(SearchSource.user_id == user_id)
        .order_by(SearchSource.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    sources = list(result.scalars().all())

    # 为每个 source 计算 topics_count
    for s in sources:
        cnt_q = await db.execute(
            select(func.count())
            .select_from(topic_search_sources)
            .where(topic_search_sources.c.search_source_id == s.id)
        )
        s.topics_count = cnt_q.scalar() or 0

    return sources, total


async def get_search_source(
    db: AsyncSession, source_id: UUID
) -> SearchSource | None:
    """根据 ID 获取搜索源"""
    result = await db.execute(
        select(SearchSource).where(SearchSource.id == source_id)
    )
    return result.scalar_one_or_none()


async def update_search_source_status(
    db: AsyncSession, source_id: UUID, status: str
) -> SearchSource | None:
    """更新搜索源状态"""
    source = await get_search_source(db, source_id)
    if source is None:
        return None
    source.status = status
    await db.commit()
    await db.refresh(source)
    return source


async def verify_search_source(
    db: AsyncSession, source_id: UUID
) -> dict | None:
    """验证搜索源 — 简单验证，设置为 active"""
    source = await get_search_source(db, source_id)
    if source is None:
        return None
    source.status = "active"
    source.auth_status = "session_ok"
    await db.commit()
    await db.refresh(source)
    return {
        "id": str(source.id),
        "title": source.title,
        "domain": source.domain,
        "status": source.status,
        "auth_status": source.auth_status,
    }


async def delete_search_source(db: AsyncSession, source_id: UUID) -> bool:
    """删除搜索源"""
    source = await get_search_source(db, source_id)
    if source is None:
        return False
    await db.delete(source)
    await db.commit()
    return True
