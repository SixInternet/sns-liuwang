"""采集进度服务 — 管理主会话采集进度记录"""

import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.collection_progress import CollectionProgress
from app.models.collection_run import CollectionRun

logger = logging.getLogger(__name__)

CONTENT_HTML_MAX_BYTES = 2 * 1024 * 1024  # 2MB


class CollectionLimitError(Exception):
    """已达采集上限"""


class ContentTooLargeError(Exception):
    """content_html 体积超限"""


async def _sync_run_status(
    run: CollectionRun,
    progress_type: str,
    detail: str | None = None,
) -> None:
    """根据 progress_type 同步 CollectionRun 状态"""
    if progress_type == "error":
        run.status = "failed"
        run.completed_at = datetime.now()
        if detail:
            run.error_info = detail
    elif progress_type == "done":
        run.status = "completed"
        run.completed_at = datetime.now()
    elif progress_type in ("progress", "captcha", "resolved"):
        run.status = "in_progress"


async def report_progress(
    db: AsyncSession,
    collection_run_id: UUID,
    step: str,
    progress_pct: int,
    estimated_remaining: int = 0,
    progress_type: str = "progress",
    detail: str | None = None,
    step_phase: str | None = None,
    sources_collected: int | None = None,
    max_sources: int | None = None,
) -> tuple[CollectionProgress, CollectionRun | None]:
    """主会话汇报进度，写入数据库并同步 Run 状态"""
    settings = get_settings()
    effective_max = max_sources if max_sources is not None else settings.collection_max_sources

    result = await db.execute(
        select(CollectionRun).where(CollectionRun.id == collection_run_id)
    )
    run = result.scalar_one_or_none()

    if run and sources_collected is None:
        sources_collected = run.sources_created or 0

    entry = CollectionProgress(
        collection_run_id=collection_run_id,
        step=step,
        progress_pct=progress_pct,
        estimated_remaining=estimated_remaining,
        progress_type=progress_type,
        detail=detail,
        step_phase=step_phase or "running",
        sources_collected=sources_collected,
        max_sources=effective_max,
    )
    db.add(entry)

    if run:
        await _sync_run_status(run, progress_type, detail)

    await db.flush()
    logger.info(
        "Progress [%s]: %s (%d%%) type=%s phase=%s",
        collection_run_id, step, progress_pct, progress_type, step_phase,
    )
    return entry, run


async def list_progress(
    db: AsyncSession,
    collection_run_id: UUID,
    skip: int = 0,
    limit: int = 100,
    latest: bool = False,
) -> tuple[list[CollectionProgress], int]:
    """获取某个采集任务的进度记录（latest=True 时返回最新一条）"""
    count_q = await db.execute(
        select(func.count())
        .select_from(CollectionProgress)
        .where(CollectionProgress.collection_run_id == collection_run_id)
    )
    total = count_q.scalar() or 0

    order = (
        CollectionProgress.created_at.desc()
        if latest
        else CollectionProgress.created_at.asc()
    )

    result = await db.execute(
        select(CollectionProgress)
        .where(CollectionProgress.collection_run_id == collection_run_id)
        .order_by(order)
        .offset(skip)
        .limit(limit)
    )
    items = list(result.scalars().all())
    return items, total


async def get_run_source_counts(
    db: AsyncSession,
    collection_run_id: UUID,
) -> tuple[int, int]:
    """返回 (sources_created, max_sources)"""
    settings = get_settings()
    result = await db.execute(
        select(CollectionRun).where(CollectionRun.id == collection_run_id)
    )
    run = result.scalar_one_or_none()
    if run is None:
        return 0, settings.collection_max_sources
    return run.sources_created or 0, settings.collection_max_sources


async def create_source_from_ingest(
    db: AsyncSession,
    collection_run_id: UUID,
    title: str,
    url: str | None,
    content_html: str,
) -> tuple[int, int]:
    """主会话提交 DOM HTML → 创建 Source 并更新 CollectionRun 统计

    返回 (sources_created, max_sources)
    """
    from app.models.source import Source as SourceModel
    from app.preprocessor import preprocess_bytes

    settings = get_settings()
    max_sources = settings.collection_max_sources

    html_bytes = content_html.encode("utf-8")
    if len(html_bytes) > CONTENT_HTML_MAX_BYTES:
        raise ContentTooLargeError(
            f"content_html 超过 {CONTENT_HTML_MAX_BYTES // (1024 * 1024)}MB 上限"
        )

    result = await db.execute(
        select(CollectionRun).where(CollectionRun.id == collection_run_id)
    )
    run = result.scalar_one_or_none()
    if run is None:
        raise ValueError(f"CollectionRun {collection_run_id} not found")

    if (run.sources_created or 0) >= max_sources:
        raise CollectionLimitError(
            f"已达本轮采集上限 {max_sources} 条"
        )

    raw_text = content_html
    try:
        markdown = preprocess_bytes(html_bytes, filename="article.html")
    except Exception:
        logger.warning("MarkItDown 转换失败，使用原文作为 markdown")
        markdown = raw_text

    src = SourceModel(
        title=title,
        url=url or "",
        content_raw=raw_text,
        content_markdown=markdown,
        collector="hook-agent",
        status="pending",
        user_id=run.user_id,
        collected_at=datetime.now(),
    )
    db.add(src)
    await db.flush()

    run.urls_collected = (run.urls_collected or 0) + 1
    run.sources_created = (run.sources_created or 0) + 1

    logger.info("Ingested source '%s' → run %s", title[:50], collection_run_id)
    return run.sources_created, max_sources
