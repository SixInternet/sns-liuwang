"""AI Sub-Agent 采集 API — 进度汇报/内容提交/人工验证处理"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.router import get_current_user
from app.database import get_session
from app.models.user import User
from app.schemas.collection_progress import (
    ProgressReport,
    ProgressResponse,
    ProgressList,
    IngestRequest,
)
from app.services import collection_progress_service
from app.collector import agent_session

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/ingest", status_code=201)
async def ingest_content(
    req: IngestRequest,
    session: AsyncSession = Depends(get_session),
):
    """Sub-agent 提交采集内容"""
    try:
        await collection_progress_service.create_source_from_ingest(
            db=session,
            collection_run_id=req.collection_run_id,
            title=req.title,
            url=req.url,
            content_raw=req.content_raw,
        )
        await session.commit()
        return {"ok": True}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("Ingest failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/progress", status_code=201)
async def report_progress(
    req: ProgressReport,
    session: AsyncSession = Depends(get_session),
):
    """Sub-agent 汇报进度"""
    entry = await collection_progress_service.report_progress(
        db=session,
        collection_run_id=req.collection_run_id,
        step=req.step,
        progress_pct=req.progress_pct,
        estimated_remaining=req.estimated_remaining,
        progress_type=req.progress_type,
        detail=req.detail,
    )
    await session.commit()
    return {"ok": True, "id": str(entry.id)}


@router.get("/progress/{run_id}", response_model=list[ProgressResponse])
async def get_progress(
    run_id: UUID,
    latest: bool = False,
    session: AsyncSession = Depends(get_session),
):
    """获取采集进度记录（含 CAPTCHA 状态）"""
    if latest:
        # 只返回最新一条
        items, total = await collection_progress_service.list_progress(
            session, run_id, limit=1,
        )
    else:
        items, total = await collection_progress_service.list_progress(
            session, run_id, limit=100,
        )
    return [ProgressResponse.model_validate(i) for i in items]


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
