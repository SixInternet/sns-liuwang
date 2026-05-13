"""信息卡片 API 路由 — 提供卡片的增删改查接口"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.router import get_current_user
from app.database import get_session
from app.models.user import User
from app.schemas.info_card import (
    CardCreate,
    CardList,
    CardResponse,
    CardStatusUpdate,
    CardUpdate,
)
from app.services import card_service

router = APIRouter()


@router.post('/', response_model=CardResponse, status_code=201)
async def create_card(
    body: CardCreate,
    _user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> CardResponse:
    """创建新的信息卡片（需登录）"""
    card = await card_service.create_card(session, body)
    return card


@router.get('/', response_model=CardList)
async def list_cards(
    _user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> CardList:
    """获取信息卡片列表（需登录）"""
    cards, total = await card_service.list_cards(session)
    return CardList(items=cards, total=total)


@router.get('/{card_id}', response_model=CardResponse)
async def get_card(
    card_id: UUID,
    _user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> CardResponse:
    """根据 ID 获取单张信息卡片（需登录）"""
    card = await card_service.get_card(session, card_id)
    if card is None:
        raise HTTPException(status_code=404, detail='卡片不存在')
    return card


@router.patch('/{card_id}/status', response_model=CardResponse)
async def update_card_status(
    card_id: UUID,
    body: CardStatusUpdate,
    _user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> CardResponse:
    """更新指定卡片的状态（需登录）"""
    card = await card_service.update_card_status(session, card_id, body)
    if card is None:
        raise HTTPException(status_code=404, detail='卡片不存在')
    return card


@router.patch('/{card_id}', response_model=CardResponse)
async def update_card(
    card_id: UUID,
    body: CardUpdate,
    _user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> CardResponse:
    """更新指定卡片的内容（标题/摘要/分类）（需登录）"""
    card = await card_service.update_card(session, card_id, body)
    if card is None:
        raise HTTPException(status_code=404, detail='卡片不存在')
    return card
