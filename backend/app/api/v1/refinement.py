"""精炼 API 路由 — 触发 DeepSeek 精炼"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.router import get_current_user
from app.database import get_session
from app.models.user import User
from app.services.refinement import refine_source

router = APIRouter()


@router.post("/{source_id}/refine")
async def trigger_refinement(
    source_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """触发对指定 Source 的 DeepSeek 精炼"""
    try:
        cards = await refine_source(session, source_id)
        return {
            "success": True,
            "card_count": len(cards),
            "cards": [{"id": str(c.id), "title": c.title} for c in cards],
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"精炼失败: {str(e)}")
