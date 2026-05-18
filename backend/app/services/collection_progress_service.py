"""采集进度服务 — 管理 Sub-Agent 进度记录"""

import logging
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.collection_progress import CollectionProgress
from app.models.collection_run import CollectionRun

logger = logging.getLogger(__name__)


async def report_progress(
    db: AsyncSession,
    collection_run_id: UUID,
    step: str,
    progress_pct: int,
    estimated_remaining: int = 0,
    progress_type: str = "progress",
    detail: str | None = None,
) -> CollectionProgress:
    """Sub-agent 汇报进度，写入数据库"""
    entry = CollectionProgress(
        collection_run_id=collection_run_id,
        step=step,
        progress_pct=progress_pct,
        estimated_remaining=estimated_remaining,
        progress_type=progress_type,
        detail=detail,
    )
    db.add(entry)
    await db.flush()
    logger.info(
        "Progress [%s]: %s (%d%%) type=%s",
        collection_run_id, step, progress_pct, progress_type,
    )
    return entry


async def list_progress(
    db: AsyncSession,
    collection_run_id: UUID,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[CollectionProgress], int]:
    """获取某个采集任务的所有进度记录"""
    count_q = await db.execute(
        select(func.count())
        .select_from(CollectionProgress)
        .where(CollectionProgress.collection_run_id == collection_run_id)
    )
    total = count_q.scalar() or 0

    result = await db.execute(
        select(CollectionProgress)
        .where(CollectionProgress.collection_run_id == collection_run_id)
        .order_by(CollectionProgress.created_at.asc())
        .offset(skip)
        .limit(limit)
    )
    items = list(result.scalars().all())
    return items, total


async def create_source_from_ingest(
    db: AsyncSession,
    collection_run_id: UUID,
    title: str,
    url: str | None,
    content_raw: str | None,
) -> None:
    """Sub-agent 提交采集内容 → 创建 Source 记录并更新 CollectionRun 统计"""
    from app.models.source import Source as SourceModel
    from datetime import datetime

    # 查询 collection_run 获取 user_id
    result = await db.execute(
        select(CollectionRun).where(CollectionRun.id == collection_run_id)
    )
    run = result.scalar_one_or_none()
    if run is None:
        raise ValueError(f"CollectionRun {collection_run_id} not found")

    from app.preprocessor import preprocess_bytes

    raw_text = content_raw or ""
    # 如果 content_raw 是 HTML，用 MarkItDown 转成 markdown
    if raw_text.strip().startswith("<"):
        try:
            markdown = preprocess_bytes(raw_text.encode("utf-8"), filename="article.html")
        except Exception:
            logger.warning("MarkItDown 转换失败，使用原文作为 markdown")
            markdown = raw_text
    else:
        markdown = raw_text

    src = SourceModel(
        title=title,
        url=url or "",
        content_raw=raw_text,
        content_markdown=markdown,
        collector="sub-agent",
        status="pending",
        user_id=run.user_id,
        collected_at=datetime.now(),
    )
    db.add(src)
    await db.flush()

    run.urls_collected = (run.urls_collected or 0) + 1
    run.sources_created = (run.sources_created or 0) + 1

    logger.info("Ingested source '%s' → run %s", title[:50], collection_run_id)
