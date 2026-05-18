"""采集器模块 — 协调浏览器适配器与截图筛选器完成信息采集"""

from app.collector.scheduler import SchedulerManager, scheduler_manager

__all__ = ["SchedulerManager", "scheduler_manager"]
