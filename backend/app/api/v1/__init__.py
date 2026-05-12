"""API v1 路由汇总"""

from fastapi import APIRouter

from app.api.v1.cards import router as cards_router

router = APIRouter(prefix="/cards", tags=["卡片"])
router.include_router(cards_router)
