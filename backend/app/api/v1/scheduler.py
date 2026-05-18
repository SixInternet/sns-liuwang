"""调度 API 路由 — 手动触发定时任务同步与重载"""

from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException

from app.auth.router import get_current_user
from app.collector.scheduler import scheduler_manager
from app.models.user import User

router = APIRouter()


class SyncRequest(BaseModel):
    topic_id: str


@router.post("/sync")
async def sync_topic_schedule(
    body: SyncRequest,
    _user: User = Depends(get_current_user),
):
    """手动触发同步指定 topic 的定时任务"""
    try:
        await scheduler_manager.sync_topic(body.topic_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"同步失败: {e}")
    return {"message": f"已同步 topic {body.topic_id} 的定时任务"}


@router.post("/reload")
async def reload_all_schedules(
    _user: User = Depends(get_current_user),
):
    """重新加载所有 topic 的定时任务"""
    try:
        await scheduler_manager.reload_all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重载失败: {e}")
    return {"message": "已重新加载所有定时任务"}
