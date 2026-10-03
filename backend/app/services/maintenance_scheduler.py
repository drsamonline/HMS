"""Lightweight background scheduler for safe HHMS maintenance."""
from __future__ import annotations
import asyncio
import logging
from app.config.settings import get_settings
from app.services.maintenance import maintenance_service
logger=logging.getLogger("hhms.maintenance.scheduler")
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
        while self._stop and not self._stop.is_set():
            try:
                await asyncio.wait_for(self._stop.wait(),timeout=interval)
            except asyncio.TimeoutError:
                try: await maintenance_service.run_safe_maintenance()
                except Exception: logger.exception("Automatic HHMS maintenance failed")
maintenance_scheduler=MaintenanceScheduler()
__all__=["MaintenanceScheduler","maintenance_scheduler"]
