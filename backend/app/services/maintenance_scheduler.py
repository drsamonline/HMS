"""Lightweight background scheduler for safe HHMS maintenance.

Batch 116: the loop now ticks at ``REPORT_SCHEDULER_INTERVAL_MINUTES`` and
fires due scheduled report jobs on every tick; the heavy maintenance pass
still runs only once per ``MAINTENANCE_INTERVAL_HOURS``.
"""
from __future__ import annotations
import asyncio
import logging
from contextlib import asynccontextmanager
from app.config.settings import get_settings
from app.db.session import get_session_factory
from app.services.maintenance import maintenance_service
from app.services.report_scheduler import report_scheduler_service
logger=logging.getLogger("hhms.maintenance.scheduler")

@asynccontextmanager
async def _db_scope():
    session = get_session_factory()()
    try:
        yield session
    finally:
        await session.close()

class MaintenanceScheduler:
    def __init__(self): self._task=None; self._stop=None
    async def start(self):
        if self._task and not self._task.done(): return
        if not get_settings().AUTO_MAINTENANCE_ENABLED: return
        self._stop=asyncio.Event(); self._task=asyncio.create_task(self._loop())
    async def stop(self):
        if not self._task: return
        if self._stop: self._stop.set()
        try: await self._task
        finally: self._task=None
    async def _loop(self):
        interval=get_settings().MAINTENANCE_INTERVAL_HOURS*3600
        tick=get_settings().REPORT_SCHEDULER_INTERVAL_MINUTES*60
        loop=asyncio.get_running_loop()
        next_maint=loop.time()+interval
        while self._stop and not self._stop.is_set():
            try:
                await asyncio.wait_for(self._stop.wait(),timeout=tick)
            except asyncio.TimeoutError:
                pass
            if self._stop.is_set(): break
            try:
                async with _db_scope() as db:
                    await report_scheduler_service.run_due_jobs(db)
            except Exception: logger.exception("Scheduled report run failed")
            if loop.time()>=next_maint:
                next_maint=loop.time()+interval
                try: await maintenance_service.run_safe_maintenance()
                except Exception: logger.exception("Automatic HHMS maintenance failed")
maintenance_scheduler=MaintenanceScheduler()
__all__=["MaintenanceScheduler","maintenance_scheduler"]
