"""信息来源（Source）API 路由 — 提供增量采集的增删改查接口"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.router import get_current_user
from app.database import get_session
from app.models.user import User
from app.schemas.source import (
    SourceCreate,
    SourceList,
    SourceResponse,
    SourceUpdateStatus,
)
from app.services import source_service

router = APIRouter()


@router.post('/', response_model=SourceResponse, status_code=201)
async def create_source(
    body: SourceCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> SourceResponse:
    """创建新的信息来源（需登录）。支持提交原始内容或 URL 自动抓取。"""
    source = await source_service.create_source(session, body, user.id)
    return source


@router.get('/', response_model=SourceList)
async def list_sources(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    skip: int = 0,
    limit: int = 20,
) -> SourceList:
    """获取当前用户的信息来源列表（需登录）。包含关联卡片数量。"""
    sources, total = await source_service.list_sources(session, user.id, skip, limit)
    return SourceList(items=sources, total=total)


@router.get('/grouped')
async def list_sources_grouped(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    page: int = 1,
    page_size: int = 5,
    date_from: str | None = None,
    date_to: str | None = None,
    sort: str = 'desc',
) -> dict:
    """按搜索源分组返回信息来源列表（需登录）。"""
    return await source_service.list_sources_grouped(
        session, user.id, page=page, page_size=page_size,
        date_from=date_from, date_to=date_to, sort=sort,
    )


@router.get('/{source_id}', response_model=SourceResponse)
async def get_source(
    source_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> SourceResponse:
    """根据 ID 获取信息来源详情（需登录）。包含关联卡片数量。"""
    source = await source_service.get_source(session, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail='信息来源不存在')
    return source


@router.patch('/{source_id}/status', response_model=SourceResponse)
async def update_source_status(
    source_id: UUID,
    body: SourceUpdateStatus,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> SourceResponse:
    """更新指定信息来源的状态（pending/refined/failed）。"""
    source = await source_service.update_source_status(session, source_id, body.status)
    if source is None:
        raise HTTPException(status_code=404, detail='信息来源不存在')
    return source


@router.delete('/{source_id}', status_code=204)
async def delete_source(
    source_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    """删除指定信息来源（级联删除关联的卡片和附件）。"""
    deleted = await source_service.delete_source(session, source_id)
    if not deleted:
        raise HTTPException(status_code=404, detail='信息来源不存在')
    return None
