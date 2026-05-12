"""信息卡片 API 路由 — 提供卡片的增删改查接口"""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas.info_card import (
    CardCreate,
    CardList,
    CardResponse,
    CardStatusUpdate,
)
from app.services import card_service

router = APIRouter()


@router.post("/", response_model=CardResponse, status_code=201)
async def create_card(
    body: CardCreate,
    session: AsyncSession = Depends(get_session),
) -> CardResponse:
    """创建新的信息卡片"""
    card = await card_service.create_card(session, body)
    return card


@router.get("/", response_model=CardList)
async def list_cards(
    session: AsyncSession = Depends(get_session),
) -> CardList:
    """获取信息卡片列表"""
    return await card_service.list_cards(session)


@router.get("/{card_id}", response_model=CardResponse)
async def get_card(
    card_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> CardResponse:
    """根据 ID 获取单张信息卡片"""
    return await card_service.get_card(session, card_id)


@router.patch("/{card_id}/status", response_model=CardResponse)
async def update_card_status(
    card_id: UUID,
    body: CardStatusUpdate,
    session: AsyncSession = Depends(get_session),
) -> CardResponse:
    """更新指定卡片的状态"""
    return await card_service.update_card_status(session, card_id, body)
