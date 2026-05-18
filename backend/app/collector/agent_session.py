"""AI Sub-Agent 会话管理 — spawn / resolve-captcha / cancel"""

import json
import logging
from datetime import datetime
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.models.collection_run import CollectionRun
from app.models.collection_progress import CollectionProgress
from app.models.topic import Topic
from app.collector.sub_agent_prompt import build_sub_agent_prompt

logger = logging.getLogger(__name__)

# 缓存活跃的 sub-agent session key: {run_id: session_key}
_active_sessions: dict[str, str] = {}


def _gateway_headers() -> dict[str, str]:
    """构造 Gateway API 请求头（含 Bearer 鉴权）"""
    settings = get_settings()
    headers = {"Content-Type": "application/json"}
    if settings.openclaw_gateway_token:
        headers["Authorization"] = f"Bearer {settings.openclaw_gateway_token}"
    return headers


def _gateway_url() -> str:
    """获取 Gateway base URL"""
    settings = get_settings()
    return settings.openclaw_gateway_url.rstrip("/")


async def spawn_collection(topic_id: str) -> tuple[str, str]:
    """为 topic 创建采集任务并 spawn sub-agent，返回 (run_id, session_key)"""
    import app.database as db

    async with db.async_session_factory() as session:
        result = await session.execute(
            select(Topic)
            .where(Topic.id == UUID(topic_id))
            .options(selectinload(Topic.search_sources))
        )
        topic = result.scalar_one_or_none()
        if topic is None:
            raise ValueError(f"Topic {topic_id} not found")

        # 创建 CollectionRun
        run = CollectionRun(
            topic_id=topic.id,
            status="queued",
            user_id=topic.user_id,
            started_at=datetime.now(),
        )
        session.add(run)
        await session.flush()

        # 准备 sub-agent prompt
        collected_urls = _get_collected_urls(session, topic)
        settings = get_settings()
        api_base = f"http://localhost:{settings.app_port}"
        cdp_info = {"host": settings.cdp_host, "port": settings.cdp_port}
        prompt = build_sub_agent_prompt(
            topic=topic,
            collected_urls=collected_urls,
            api_base=api_base,
            cdp_info=cdp_info,
            run_id=str(run.id),
        )

        # 通过 OpenClaw Gateway /tools/invoke API spawn sub-agent
        try:
            session_key = await _spawn_via_gateway(prompt, str(run.id))
            run.status = "in_progress"
            _active_sessions[str(run.id)] = session_key
            logger.info(
                "Spawned sub-agent for topic %s → run %s → session %s",
                topic_id, run.id, session_key,
            )
        except Exception as exc:
            logger.exception("Failed to spawn sub-agent for topic %s", topic_id)
            run.status = "failed"
            run.error_info = json.dumps({"error": f"spawn failed: {exc}"})
            raise

        await session.commit()
        return str(run.id), session_key


async def resolve_captcha(run_id: str) -> bool:
    """人工验证已解决 → 通知 sub-agent 继续"""
    session_key = _active_sessions.get(run_id)
    if not session_key:
        logger.warning("No active session for run %s", run_id)
        return False

    try:
        await _send_to_session(
            session_key=session_key,
            message="【系统通知】人工验证已被用户解决，请继续你的采集任务。",
        )
        logger.info("Sent resolve message to sub-agent session %s", session_key)
        return True
    except Exception as exc:
        logger.error("Failed to send resolve to session %s: %s", session_key, exc)
        return False


async def cancel_collection(run_id: str) -> bool:
    """取消采集任务 → kill sub-agent + 更新状态"""
    session_key = _active_sessions.pop(run_id, None)

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

    if session_key:
        try:
            await _kill_session(session_key)
            logger.info("Cancelled sub-agent session %s for run %s", session_key, run_id)
        except Exception as exc:
            logger.warning("Failed to kill session %s: %s", session_key, exc)

    return True


def _get_collected_urls(session, topic) -> list[str]:
    """获取 topic 已采集的 URL 列表用于去重"""
    try:
        from app.models.source import Source
        result = session.execute(
            select(Source.url).where(Source.collector == "sub-agent")
        )
        urls = [row[0] for row in result if row[0]]
        return urls
    except Exception:
        return []


async def _spawn_via_gateway(prompt: str, run_id: str) -> str:
    """通过 OpenClaw Gateway /tools/invoke 创建 sub-agent"""
    gw_url = _gateway_url()
    headers = _gateway_headers()

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{gw_url}/tools/invoke",
            headers=headers,
            json={
                "tool": "sessions_spawn",
                "args": {
                    "task": prompt,
                    "label": f"采集-{run_id[:8]}",
                    "mode": "run",
                    "run_timeout_seconds": 900,
                    "thinking": "low",
                },
            },
        )

        if resp.status_code != 200:
            raise RuntimeError(
                f"Gateway responded {resp.status_code}: {resp.text[:200]}"
            )

        data = resp.json()
        if not data.get("ok"):
            raise RuntimeError(f"Gateway returned error: {data.get('error', resp.text[:200])}")

        result = data.get("result", {})
        detail = result.get("details", {}) if isinstance(result, dict) else {}
        session_key = detail.get("childSessionKey", f"sub-agent-{run_id[:8]}")
        logger.info("Sub-agent spawned: session_key=%s", session_key)
        return session_key


async def _send_to_session(session_key: str, message: str) -> None:
    """通过 OpenClaw Gateway /tools/invoke 发送消息到 sub-agent session"""
    gw_url = _gateway_url()
    headers = _gateway_headers()

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            f"{gw_url}/tools/invoke",
            headers=headers,
            json={
                "tool": "sessions_send",
                "args": {
                    "session_key": session_key,
                    "message": message,
                },
            },
        )

        if resp.status_code != 200:
            logger.warning(
                "send_to_session failed: %s %s", resp.status_code, resp.text[:100]
            )


async def _kill_session(session_key: str) -> None:
    """通过 OpenClaw Gateway /tools/invoke 终止 sub-agent session"""
    gw_url = _gateway_url()
    headers = _gateway_headers()

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            f"{gw_url}/tools/invoke",
            headers=headers,
            json={
                "tool": "subagents",
                "args": {
                    "action": "kill",
                    "target": session_key,
                },
            },
        )

        if resp.status_code != 200:
            logger.warning(
                "kill_session failed: %s %s", resp.status_code, resp.text[:100]
            )
