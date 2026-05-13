"""API v1 路由汇总"""

from fastapi import APIRouter

from app.api.v1.cards import router as cards_router
from app.api.v1.sources import router as sources_router
from app.api.v1.refinement import router as refinement_router

router = APIRouter()

router.include_router(cards_router, prefix="/cards", tags=["卡片"])
router.include_router(sources_router, prefix="/sources", tags=["信息来源"])
router.include_router(refinement_router, prefix="/sources", tags=["精炼"])
