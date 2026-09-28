"""API v1 路由汇总"""

from fastapi import APIRouter

from app.api.v1.cards import router as cards_router
from app.api.v1.sources import router as sources_router
from app.api.v1.refinement import router as refinement_router
from app.api.v1.search_sources import router as search_sources_router
from app.api.v1.topics import router as topics_router
from app.api.v1.collection_runs import router as collection_runs_router
from app.api.v1.scheduler import router as scheduler_router
from app.api.v1.collector_agent import router as collector_agent_router
from app.api.v1.feedback import router as feedback_router

router = APIRouter()

router.include_router(cards_router, prefix="/cards", tags=["卡片"])
router.include_router(sources_router, prefix="/sources", tags=["信息来源"])
router.include_router(refinement_router, prefix="/sources", tags=["精炼"])
router.include_router(search_sources_router, prefix="/search-sources", tags=["搜索源"])
router.include_router(topics_router, prefix="/topics", tags=["主题"])
router.include_router(collection_runs_router, prefix="/collection-runs", tags=["采集记录"])
router.include_router(scheduler_router, prefix="/scheduler", tags=["调度"])
router.include_router(collector_agent_router, prefix="/collector", tags=["AI采集"])
router.include_router(feedback_router, prefix="/feedback", tags=["反馈同步"])
