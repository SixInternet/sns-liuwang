"""采集记录（CollectionRun）业务逻辑服务"""

from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.collection_run import CollectionRun


def _run_to_dict(run: CollectionRun) -> dict:
    """将 CollectionRun ORM 对象转为包含 topic_name 的 dict"""
    return {
        "id": run.id,
        "topic_id": run.topic_id,
        "topic_name": run.topic.name if run.topic else None,
        "search_source_id": run.search_source_id,
        "status": run.status,
        "urls_scanned": run.urls_scanned,
        "urls_collected": run.urls_collected,
        "sources_created": run.sources_created,
        "cards_created": run.cards_created,
        "error_info": run.error_info,
        "user_id": run.user_id,
        "started_at": run.started_at,
        "completed_at": run.completed_at,
    }


async def list_collection_runs(
    db: AsyncSession, user_id: UUID, skip: int = 0, limit: int = 20
) -> tuple[list[dict], int]:
    """获取当前用户的采集记录列表，按 started_at 倒序"""
    count_q = await db.execute(
        select(func.count())
        .select_from(CollectionRun)
        .where(CollectionRun.user_id == user_id)
    )
    total = count_q.scalar() or 0

    result = await db.execute(
        select(CollectionRun)
        .options(joinedload(CollectionRun.topic))
        .where(CollectionRun.user_id == user_id)
        .order_by(CollectionRun.started_at.desc())
        .offset(skip)
        .limit(limit)
    )
    runs = list(result.unique().scalars().all())
    return [_run_to_dict(run) for run in runs], total


async def get_collection_run(
    db: AsyncSession, run_id: UUID
) -> dict | None:
    """根据 ID 获取采集记录"""
    result = await db.execute(
        select(CollectionRun)
        .options(joinedload(CollectionRun.topic))
        .where(CollectionRun.id == run_id)
    )
    run = result.unique().scalar_one_or_none()
    if run is None:
        return None
    return _run_to_dict(run)
