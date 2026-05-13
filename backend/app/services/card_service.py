"""卡片业务逻辑服务"""

from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.info_card import InfoCard
from app.schemas.info_card import CardCreate, CardStatusUpdate, CardUpdate


async def create_card(db: AsyncSession, card_data: CardCreate) -> InfoCard:
    """创建新卡片"""
    card = InfoCard(**card_data.model_dump())
    db.add(card)
    await db.commit()
    await db.refresh(card)
    return card


async def list_cards(
    db: AsyncSession, skip: int = 0, limit: int = 20
) -> tuple[list[InfoCard], int]:
    """获取卡片列表，同时返回总数"""
    total_query = await db.execute(select(func.count()).select_from(InfoCard))
    total = total_query.scalar() or 0

    result = await db.execute(select(InfoCard).offset(skip).limit(limit))
    cards = list(result.scalars().all())
    return cards, total


async def get_card(db: AsyncSession, card_id: UUID) -> InfoCard | None:
    """根据 ID 获取单张卡片"""
    result = await db.execute(select(InfoCard).where(InfoCard.id == card_id))
    return result.scalar_one_or_none()


async def update_card_status(
    db: AsyncSession, card_id: UUID, body: CardStatusUpdate
) -> InfoCard | None:
    """更新卡片状态"""
    card = await get_card(db, card_id)
    if card is None:
        return None
    card.status = body.status
    await db.commit()
    await db.refresh(card)
    return card


async def update_card(
    db: AsyncSession, card_id: UUID, body: CardUpdate
) -> InfoCard | None:
    """更新卡片内容（title/summary/category）"""
    card = await get_card(db, card_id)
    if card is None:
        return None

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(card, field, value)

    await db.commit()
    await db.refresh(card)
    return card
