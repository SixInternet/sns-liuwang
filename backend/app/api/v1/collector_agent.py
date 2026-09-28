"""主会话采集 API — 进度汇报/内容提交/人工验证处理"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.router import get_current_user
from app.config import get_settings
from app.database import get_session
from app.models.user import User
from app.schemas.collection_progress import (
    ProgressReport,
    ProgressResponse,
    ProgressTimelineResponse,
    ProgressReportResponse,
    IngestRequest,
)
from app.services import collection_progress_service
from app.services.collection_progress_service import (
    CollectionLimitError,
    ContentTooLargeError,
)
from app.collector import agent_session

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/ingest", status_code=201)
async def ingest_content(
    req: IngestRequest,
    session: AsyncSession = Depends(get_session),
):
    """主会话提交采集内容（content_html）"""
    content_html = req.content_html or req.content_raw
    if not content_html:
        raise HTTPException(status_code=422, detail="content_html 必填")

    try:
        sources_created, max_sources = await collection_progress_service.create_source_from_ingest(
            db=session,
            collection_run_id=req.collection_run_id,
            title=req.title,
            url=req.url,
            content_html=content_html,
        )
        await session.commit()
        return {
            "ok": True,
            "sources_created": sources_created,
            "max_sources": max_sources,
        }
    except CollectionLimitError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ContentTooLargeError as e:
        raise HTTPException(status_code=413, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("Ingest failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/progress", status_code=201, response_model=ProgressReportResponse)
async def report_progress(
    req: ProgressReport,
    session: AsyncSession = Depends(get_session),
):
    """主会话汇报进度"""
    entry, run = await collection_progress_service.report_progress(
        db=session,
        collection_run_id=req.collection_run_id,
        step=req.step,
        progress_pct=req.progress_pct,
        estimated_remaining=req.estimated_remaining,
        progress_type=req.progress_type,
        detail=req.detail,
        step_phase=req.step_phase,
        sources_collected=req.sources_collected,
        max_sources=req.max_sources,
    )
    await session.commit()

    settings = get_settings()
    sources_created = (run.sources_created if run else 0) or 0
    max_sources = req.max_sources or settings.collection_max_sources

    return ProgressReportResponse(
        ok=True,
        id=str(entry.id),
        sources_created=sources_created,
        max_sources=max_sources,
    )


@router.get("/progress/{run_id}")
async def get_progress(
    run_id: UUID,
    latest: bool = False,
    session: AsyncSession = Depends(get_session),
):
    """获取采集进度（默认完整时间线；?latest=1 仅最新一条）"""
    items, total = await collection_progress_service.list_progress(
        session, run_id, limit=100 if not latest else 1, latest=latest,
    )
    responses = [ProgressResponse.model_validate(i) for i in items]

    if latest:
        return responses[0] if responses else None

    sources_created, max_sources = await collection_progress_service.get_run_source_counts(
        session, run_id,
    )
    return ProgressTimelineResponse(
        items=responses,
        total=total,
        sources_created=sources_created,
        max_sources=max_sources,
    )


@router.post("/progress/{run_id}/resolve")
async def resolve_captcha(
    run_id: UUID,
    _user: User = Depends(get_current_user),
):
    """用户确认人工验证已解决"""
    ok = await agent_session.resolve_captcha(str(run_id))
    if not ok:
        raise HTTPException(status_code=404, detail="No active session found")
    return {"ok": True}


@router.post("/progress/{run_id}/cancel")
async def cancel_collection(
    run_id: UUID,
    _user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """取消采集任务"""
    ok = await agent_session.cancel_collection(str(run_id))
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to cancel")
    return {"ok": True}
