"""主题（Topic）业务逻辑服务"""

import json
from datetime import datetime
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.topic import Topic, topic_search_sources
from app.models.search_source import SearchSource
from app.models.collection_run import CollectionRun
from app.schemas.topic import TopicCreate, TopicUpdate


async def create_topic(
    db: AsyncSession, body: TopicCreate, user_id: UUID
) -> Topic:
    """创建主题，keywords 和 schedule_times 以 JSON 字符串存储"""
    keywords_json = json.dumps(body.keywords) if body.keywords else None
    schedule_json = json.dumps(body.schedule_times) if body.schedule_times else None

    topic = Topic(
        name=body.name,
        description=body.description,
        keywords=keywords_json,
        search_depth=body.search_depth,
        schedule_type=body.schedule_type,
        schedule_times=schedule_json,
        created_via=body.created_via,
        user_id=user_id,
    )

    if body.search_source_ids:
        result = await db.execute(
            select(SearchSource).where(SearchSource.id.in_(body.search_source_ids))
        )
        sources = list(result.scalars().all())
        topic.search_sources = sources

    db.add(topic)
    await db.commit()
    await db.refresh(topic)
    return topic


async def list_topics(
    db: AsyncSession, user_id: UUID, skip: int = 0, limit: int = 20
) -> tuple[list[Topic], int]:
    """获取当前用户的主题列表（不预加载 search_sources，按需加载）"""
    count_q = await db.execute(
        select(func.count()).select_from(Topic).where(Topic.user_id == user_id)
    )
    total = count_q.scalar() or 0

    result = await db.execute(
        select(Topic)
        .where(Topic.user_id == user_id)
        .offset(skip)
        .limit(limit)
    )
    topics = list(result.scalars().all())
    return topics, total


async def get_topic(db: AsyncSession, topic_id: UUID) -> Topic | None:
    """根据 ID 获取主题，关联加载 search_sources"""
    result = await db.execute(
        select(Topic)
        .options(selectinload(Topic.search_sources))
        .where(Topic.id == topic_id)
    )
    return result.scalar_one_or_none()


async def update_topic(
    db: AsyncSession, topic_id: UUID, body: TopicUpdate
) -> Topic | None:
    """更新主题，只更新传入的非 None 字段"""
    topic = await get_topic(db, topic_id)
    if topic is None:
        return None

    update_data = body.model_dump(exclude_unset=True)

    # JSON 字段单独处理
    if "keywords" in update_data:
        kw = update_data.pop("keywords")
        topic.keywords = json.dumps(kw) if kw is not None else None

    if "schedule_times" in update_data:
        st = update_data.pop("schedule_times")
        topic.schedule_times = json.dumps(st) if st is not None else None

    # 多对多关联单独处理
    source_ids = update_data.pop("search_source_ids", None)

    for field, value in update_data.items():
        setattr(topic, field, value)

    if source_ids is not None:
        result = await db.execute(
            select(SearchSource).where(SearchSource.id.in_(source_ids))
        )
        topic.search_sources = list(result.scalars().all())

    await db.commit()
    await db.refresh(topic)
    # 重新加载关联
    await db.refresh(topic, ["search_sources"])
    return topic


async def delete_topic(db: AsyncSession, topic_id: UUID) -> bool:
    """删除主题"""
    topic = await get_topic(db, topic_id)
    if topic is None:
        return False
    await db.delete(topic)
    await db.commit()
    return True


async def collect_now(db: AsyncSession, topic_id: UUID) -> CollectionRun | None:
    """立即触发采集（通过 hook:liuwang-space 主会话）"""
    topic = await get_topic(db, topic_id)
    if topic is None or not topic.search_sources:
        return None

    from app.collector.agent_session import spawn_collection

    run_id, session_key = await spawn_collection(str(topic_id))

    # 重新从 db 读取最新记录返回
    result = await db.execute(
        select(CollectionRun).where(CollectionRun.id == UUID(run_id))
    )
    run = result.scalar_one_or_none()
    return run


async def get_topic_search_sources(
    db: AsyncSession,
    topic_id: UUID,
    user_id: UUID,
    page: int = 1,
    page_size: int = 5,
    date_from: str | None = None,
    date_to: str | None = None,
    sort: str = "desc",
) -> tuple[list[dict], int]:
    topic_q = await db.execute(
        select(Topic).where(Topic.id == topic_id, Topic.user_id == user_id)
    )
    if topic_q.scalar_one_or_none() is None:
        return [], 0

    conditions = [topic_search_sources.c.topic_id == topic_id]
    if date_from:
        try:
            conditions.append(
                SearchSource.created_at >= datetime.fromisoformat(date_from)
            )
        except ValueError:
            pass
    if date_to:
        try:
            conditions.append(
                SearchSource.created_at <= datetime.fromisoformat(date_to)
            )
        except ValueError:
            pass

    where = and_(*conditions)

    count_q = await db.execute(
        select(func.count())
        .select_from(topic_search_sources.join(SearchSource, topic_search_sources.c.search_source_id == SearchSource.id))
        .where(where)
    )
    total = count_q.scalar() or 0

    order_col = SearchSource.created_at.desc() if sort == "desc" else SearchSource.created_at.asc()

    offset = (page - 1) * page_size
    result = await db.execute(
        select(
            SearchSource.id,
            SearchSource.title,
            SearchSource.base_url,
            SearchSource.domain,
            SearchSource.status,
            SearchSource.auth_status,
            SearchSource.auth_notes,
            SearchSource.last_verified_at,
            SearchSource.last_error,
            SearchSource.user_id,
            SearchSource.created_at,
            SearchSource.updated_at,
        )
        .select_from(topic_search_sources.join(SearchSource, topic_search_sources.c.search_source_id == SearchSource.id))
        .where(where)
        .order_by(order_col)
        .offset(offset)
        .limit(page_size)
    )
    rows = result.all()

    items = []
    for row in rows:
        items.append({
            "id": row.id,
            "title": row.title,
            "base_url": row.base_url,
            "domain": row.domain,
            "status": row.status,
            "auth_status": row.auth_status,
            "auth_notes": row.auth_notes,
            "last_verified_at": row.last_verified_at,
            "last_error": row.last_error,
            "user_id": row.user_id,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
            "topics_count": 0,
            "topic_id": topic_id,
        })

    return items, total
