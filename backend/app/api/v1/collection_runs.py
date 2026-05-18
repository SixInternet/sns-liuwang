"""采集记录 API 路由"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.router import get_current_user
from app.database import get_session
from app.models.user import User
from app.schemas.collection_run import CollectionRunResponse, CollectionRunList
from app.services import collection_run_service

router = APIRouter()


@router.get("/", response_model=CollectionRunList)
async def list_collection_runs(
    _user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    runs, total = await collection_run_service.list_collection_runs(session, _user.id)
    items = [CollectionRunResponse(**run) for run in runs]
    return CollectionRunList(items=items, total=total)


@router.get("/{run_id}", response_model=CollectionRunResponse)
async def get_collection_run(
    run_id: UUID,
    _user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await collection_run_service.get_collection_run(session, run_id)
    if result is None:
        raise HTTPException(status_code=404, detail="采集记录不存在")
    return CollectionRunResponse(**result)
