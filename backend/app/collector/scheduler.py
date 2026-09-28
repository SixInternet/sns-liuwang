"""定时采集调度器 — 基于 APScheduler 管理 Topic 定时采集任务"""

import json
import logging
from datetime import datetime

from uuid import UUID

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.collector import agent_session
import app.database as db
from app.models.collection_run import CollectionRun
from app.models.topic import Topic

logger = logging.getLogger(__name__)


class SchedulerManager:
    """管理 APScheduler 定时采集任务"""

    def __init__(self):
        self._scheduler: AsyncIOScheduler | None = None
        self._topic_jobs: dict[str, list[str]] = {}

    async def start(self) -> None:
        """启动调度器，从数据库加载所有 enabled 的 Topic 定时任务"""
        self._scheduler = AsyncIOScheduler()
        await self.reload_all()
        self._scheduler.start()
        logger.info("调度器已启动，已加载 %d 个 Topic 的定时任务", len(self._topic_jobs))

    async def shutdown(self) -> None:
        """关闭调度器"""
        if self._scheduler is not None:
            self._scheduler.shutdown(wait=False)
            self._scheduler = None
            self._topic_jobs.clear()
            logger.info("调度器已关闭")

    async def sync_topic(self, topic_id: str) -> None:
        """重新同步某个 Topic 的定时任务（移除旧的，添加新的）"""
        self._remove_topic_jobs(topic_id)
        await self._add_topic_jobs(topic_id)
        logger.info("已重新同步 Topic %s 的定时任务", topic_id)

    async def remove_topic(self, topic_id: str) -> None:
        """移除某个 Topic 的所有定时任务"""
        self._remove_topic_jobs(topic_id)
        logger.info("已移除 Topic %s 的所有定时任务", topic_id)

    async def reload_all(self) -> None:
        """重新从数据库加载所有 enabled Topic 的定时任务"""
        if self._scheduler is not None:
            self._scheduler.remove_all_jobs()
        self._topic_jobs.clear()

        async with db.async_session_factory() as session:
            result = await session.execute(
                select(Topic)
                .where(Topic.enabled.is_(True))
                .options(selectinload(Topic.search_sources))
            )
            topics = result.scalars().all()

        for topic in topics:
            await self._add_topic_jobs(str(topic.id))

        logger.info("已重新加载所有定时任务，共 %d 个 Topic", len(self._topic_jobs))

    async def _add_topic_jobs(self, topic_id: str) -> None:
        """为指定 Topic 创建 CronTrigger 定时任务"""
        if self._scheduler is None:
            return

        async with db.async_session_factory() as session:
            result = await session.execute(
                select(Topic)
                .where(Topic.id == UUID(topic_id), Topic.enabled.is_(True))
                .options(selectinload(Topic.search_sources))
            )
            topic = result.scalar_one_or_none()

        if topic is None:
            logger.warning("Topic %s 不存在或已禁用，跳过创建定时任务", topic_id)
            return

        if not topic.schedule_times:
            logger.warning("Topic %s 没有配置 schedule_times，跳过", topic_id)
            return

        try:
            times = json.loads(topic.schedule_times)
        except (json.JSONDecodeError, TypeError):
            logger.warning("Topic %s 的 schedule_times 格式无效: %s", topic_id, topic.schedule_times)
            return

        job_ids: list[str] = []
        day_of_week = "mon-fri" if topic.schedule_type == "weekly" else None

        for time_str in times:
            parts = time_str.strip().split(":")
            if len(parts) != 2:
                logger.warning("Topic %s 的时间格式无效: %s", topic_id, time_str)
                continue
            hour, minute = int(parts[0]), int(parts[1])

            trigger = CronTrigger(hour=hour, minute=minute, day_of_week=day_of_week)
            job = self._scheduler.add_job(
                _run_collection,
                trigger=trigger,
                id=f"topic_{topic_id}_{hour:02d}{minute:02d}",
                args=[topic_id],
                replace_existing=True,
            )
            job_ids.append(job.id)

        if job_ids:
            self._topic_jobs[topic_id] = job_ids
            logger.info(
                "Topic %s 已创建 %d 个定时任务: %s",
                topic_id, len(job_ids), job_ids,
            )

    def _remove_topic_jobs(self, topic_id: str) -> None:
        """移除指定 Topic 的所有定时任务"""
        if self._scheduler is None:
            return

        job_ids = self._topic_jobs.pop(topic_id, [])
        for job_id in job_ids:
            try:
                self._scheduler.remove_job(job_id)
            except Exception:
                pass  # job 可能已不存在


async def _run_collection(topic_id: str) -> None:
    """执行一轮采集（由 APScheduler 定时触发）"""
    logger.info("开始执行 Topic %s 的定时采集", topic_id)

    try:
        async with db.async_session_factory() as session:
            result = await session.execute(
                select(Topic)
                .where(Topic.id == UUID(topic_id))
                .options(selectinload(Topic.search_sources))
            )
            topic = result.scalar_one_or_none()

            if topic is None:
                logger.warning("Topic %s 不存在，跳过采集", topic_id)
                return

            if not topic.search_sources:
                logger.warning("Topic %s 没有关联搜索源，跳过采集", topic_id)
                return

            # 通过 hook:liuwang-space 主会话采集
            try:
                run_id, _mode = await agent_session.spawn_collection(topic_id)
                topic.last_collected_at = datetime.now()
                await session.commit()
                logger.info(
                    "Topic %s CDP 采集完成 → run %s",
                    topic_id, run_id,
                )
            except Exception as exc:
                logger.exception("Topic %s 采集投递失败: %s", topic_id, exc)
                raise

    except Exception:
        logger.exception("Topic %s 定时采集过程中发生未预期的异常", topic_id)


# 全局单例
scheduler_manager = SchedulerManager()
