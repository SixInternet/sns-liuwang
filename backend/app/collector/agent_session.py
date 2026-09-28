"""采集任务会话管理 — 通过 OpenClaw Gateway hooks 触发 hook:liuwang-space 主会话采集"""

import json
import logging
from datetime import datetime
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.collector.collection_prompt import build_collection_prompt
from app.config import get_settings
from app.models.collection_run import CollectionRun
from app.models.topic import Topic

logger = logging.getLogger(__name__)


async def spawn_collection(topic_id: str) -> tuple[str, str]:
    """
    为 topic 创建采集任务并通过 OpenClaw /hooks/agent 投递到 hook:liuwang-space 主会话
    返回 (run_id, "hook-agent")
    """
    import app.database as db

    settings = get_settings()
    gateway_url = settings.openclaw_gateway_url.rstrip("/")
    gateway_token = settings.openclaw_gateway_token

    async with db.async_session_factory() as session:
        result = await session.execute(
            select(Topic)
            .where(Topic.id == UUID(topic_id))
            .options(selectinload(Topic.search_sources))
        )
        topic = result.scalar_one_or_none()
        if topic is None:
            raise ValueError(f"Topic {topic_id} not found")

        sources_to_collect = list(topic.search_sources or [])
        if not sources_to_collect:
            raise ValueError(f"Topic {topic_id} 没有关联搜索源")

        # 1. 创建 CollectionRun，立即设为 in_progress
        run = CollectionRun(
            topic_id=topic.id,
            status="in_progress",
            user_id=topic.user_id,
            started_at=datetime.now(),
        )
        session.add(run)
        await session.flush()
        run_id = str(run.id)

        # 2. 构建主会话采集 prompt
        prompt = build_collection_prompt(
            topic=topic,
            collected_urls=[],
            api_base=f"http://localhost:{settings.app_port}",
            browseros_info={
                "mcp_url": settings.browseros_mcp_url,
            },
            run_id=run_id,
        )

        # 3. 通过 /hooks/agent 投递到 hook:liuwang-space 主会话
        hook_url = f"{gateway_url}/hooks/agent"
        payload = {
            "message": f"[COLLECTION_TASK]\nRun ID: {run_id}\nTopic: {topic.name}\n\n{prompt}",
            "name": "信息采集",
            "wakeMode": "now",
            "deliver": False,
            "sessionKey": "hook:liuwang-space",
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {gateway_token}",
        }

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
                resp = await client.post(hook_url, json=payload, headers=headers)
                if resp.status_code < 200 or resp.status_code >= 300:
                    logger.error(
                        "OpenClaw hook 返回非成功状态: %s body=%s",
                        resp.status_code, (resp.text or "")[:200],
                    )
                    run.status = "failed"
                    run.error_info = json.dumps({
                        "error": f"hook 失败: HTTP {resp.status_code}",
                    })
                else:
                    logger.info(
                        "采集任务已投递到 hook:liuwang-space: run=%s topic=%s hook_status=%s",
                        run_id, topic.name, resp.status_code,
                    )
        except httpx.RequestError as exc:
            logger.exception("OpenClaw hook 请求异常: %s", exc)
            run.status = "failed"
            run.error_info = json.dumps({"error": f"hook 请求异常: {exc}"})

        run.completed_at = datetime.now() if run.status == "failed" else None
        await session.commit()

        if run.status == "failed":
            raise RuntimeError(f"采集任务投递失败: {run.error_info}")

        return run_id, "hook-agent"


async def resolve_captcha(run_id: str) -> bool:
    """用户确认人工验证已解决 → 创建 resolved 进度记录"""
    from app.models.collection_progress import CollectionProgress
    import app.database as db

    async with db.async_session_factory() as session:
        entry = CollectionProgress(
            collection_run_id=UUID(run_id),
            step="人工验证已解决",
            progress_pct=50,
            estimated_remaining=0,
            progress_type="resolved",
            detail="用户确认验证已通过",
            step_phase="done",
        )
        session.add(entry)
        await session.commit()
        return True


async def cancel_collection(run_id: str) -> bool:
    """取消采集任务 → 更新状态"""
    import app.database as db

    async with db.async_session_factory() as session:
        result = await session.execute(
            select(CollectionRun).where(CollectionRun.id == UUID(run_id))
        )
        run = result.scalar_one_or_none()
        if run:
            run.status = "cancelled"
            run.completed_at = datetime.now()
            await session.commit()
            return True
        return False
