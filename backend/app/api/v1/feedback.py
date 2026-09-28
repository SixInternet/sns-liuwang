"""反馈同步 API — 获取和标记已标记的 InfoCard 以便同步到记忆中"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.info_card import InfoCard
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()


class FeedbackItem(BaseModel):
    id: str
    title: str
    status: str
    category: str | None
    summary: str | None
    source_url: str | None
    collected_at: str


class PendingFeedbackList(BaseModel):
    items: list[FeedbackItem]
    total: int


@router.get("/pending", response_model=PendingFeedbackList)
async def list_pending_feedback(
    session: AsyncSession = Depends(get_session),
    limit: int = 50,
    skip: int = 0,
):
    """获取尚未同步到记忆的反馈（status != pending 且 memory_synced=False）"""
    stmt = (
        select(InfoCard)
        .where(InfoCard.status != "pending", InfoCard.memory_synced == False)
        .order_by(InfoCard.collected_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await session.execute(stmt)
    cards = result.scalars().all()

    # total count
    count_stmt = (
        select(InfoCard)
        .where(InfoCard.status != "pending", InfoCard.memory_synced == False)
    )
    count_result = await session.execute(count_stmt)
    total = len(count_result.scalars().all())

    items = [
        FeedbackItem(
            id=str(c.id),
            title=c.title,
            status=c.status,
            category=c.category,
            summary=c.summary,
            source_url=c.source_url,
            collected_at=c.collected_at.isoformat() if c.collected_at else "",
        )
        for c in cards
    ]
    return PendingFeedbackList(items=items, total=total)


@router.post("/{card_id}/synced")
async def mark_feedback_synced(
    card_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """将指定卡片的 memory_synced 标记为 True"""
    stmt = select(InfoCard).where(InfoCard.id == card_id)
    result = await session.execute(stmt)
    card = result.scalar_one_or_none()
    if card is None:
        raise HTTPException(status_code=404, detail="卡片不存在")
    card.memory_synced = True
    await session.commit()
    return {"ok": True}


@router.post("/sync-all")
async def sync_all_pending_feedback(
    session: AsyncSession = Depends(get_session),
):
    """[安全操作] 将所有未同步的卡片标记为已同步"""
    stmt = (
        select(InfoCard)
        .where(InfoCard.status != "pending", InfoCard.memory_synced == False)
    )
    result = await session.execute(stmt)
    cards = result.scalars().all()
    count = 0
    for card in cards:
        card.memory_synced = True
        count += 1
    await session.commit()
    return {"ok": True, "count": count}
