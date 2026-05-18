"""搜索源 API 路由"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.router import get_current_user
from app.database import get_session
from app.models.user import User
from app.schemas.search_source import (
    SearchSourceCreate,
    SearchSourceResponse,
    SearchSourceList,
    SearchSourceStatusUpdate,
)
from app.services import search_source_service

router = APIRouter()


@router.post("/", response_model=SearchSourceResponse, status_code=201)
async def create_search_source(
    body: SearchSourceCreate,
    _user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    if body.title == body.base_url:
        raise HTTPException(status_code=400, detail='标题和 Base URL 不能相同')
    source = await search_source_service.create_search_source(session, body, _user.id)
    return source


@router.get("/", response_model=SearchSourceList)
async def list_search_sources(
    _user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    sources, total = await search_source_service.list_search_sources(session, _user.id)
    return SearchSourceList(items=sources, total=total)


@router.get("/{source_id}", response_model=SearchSourceResponse)
async def get_search_source(
    source_id: UUID,
    _user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    source = await search_source_service.get_search_source(session, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="搜索源不存在")
    return source


@router.patch("/{source_id}/status", response_model=SearchSourceResponse)
async def update_search_source_status(
    source_id: UUID,
    body: SearchSourceStatusUpdate,
    _user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    source = await search_source_service.update_search_source_status(
        session, source_id, body.status
    )
    if source is None:
        raise HTTPException(status_code=404, detail="搜索源不存在")
    return source


@router.post("/{source_id}/verify")
async def verify_search_source(
    source_id: UUID,
    _user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await search_source_service.verify_search_source(session, source_id)
    if result is None:
        raise HTTPException(status_code=404, detail="搜索源不存在")
    return result


@router.delete("/{source_id}", status_code=204)
async def delete_search_source(
    source_id: UUID,
    _user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    deleted = await search_source_service.delete_search_source(session, source_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="搜索源不存在")
    return Response(status_code=204)
