"""主题 API 路由"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.router import get_current_user
from app.database import get_session
from app.models.user import User
from app.schemas.topic import TopicCreate, TopicResponse, TopicList, TopicUpdate
from app.schemas.collection_run import CollectionRunResponse
from app.services import topic_service

router = APIRouter()


@router.post("/", response_model=TopicResponse, status_code=201)
async def create_topic(
    body: TopicCreate,
    _user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    topic = await topic_service.create_topic(session, body, _user.id)
    return topic


@router.get("/", response_model=TopicList)
async def list_topics(
    _user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    topics, total = await topic_service.list_topics(session, _user.id)
    return TopicList(items=topics, total=total)


@router.get("/{topic_id}", response_model=TopicResponse)
async def get_topic(
    topic_id: UUID,
    _user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    topic = await topic_service.get_topic(session, topic_id)
    if topic is None:
        raise HTTPException(status_code=404, detail="主题不存在")
    return topic


@router.patch("/{topic_id}", response_model=TopicResponse)
async def update_topic(
    topic_id: UUID,
    body: TopicUpdate,
    _user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    topic = await topic_service.update_topic(session, topic_id, body)
    if topic is None:
        raise HTTPException(status_code=404, detail="主题不存在")
    return topic


@router.delete("/{topic_id}", status_code=204)
async def delete_topic(
    topic_id: UUID,
    _user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    deleted = await topic_service.delete_topic(session, topic_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="主题不存在")
    return Response(status_code=204)


@router.post("/{topic_id}/collect-now", response_model=CollectionRunResponse)
async def collect_now(
    topic_id: UUID,
    _user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    run = await topic_service.collect_now(session, topic_id)
    if run is None:
        raise HTTPException(status_code=404, detail="主题不存在")
    return run


@router.get("/{topic_id}/search-sources")
async def list_topic_search_sources(
    topic_id: UUID,
    page: int = 1,
    page_size: int = 5,
    date_from: str | None = None,
    date_to: str | None = None,
    sort: str = "desc",
    _user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    items, total = await topic_service.get_topic_search_sources(
        session, topic_id, _user.id,
        page=page, page_size=page_size,
        date_from=date_from, date_to=date_to,
        sort=sort,
    )
    return {"items": items, "total": total, "page": page, "page_size": page_size}
