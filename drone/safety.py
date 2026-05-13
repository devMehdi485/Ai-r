"""Garde-fous : batterie faible, altitude max, kill switch."""
import asyncio
import logging

import config
from drone.base import BaseDrone

log = logging.getLogger(__name__)


class SafetyMonitor:
    """Tourne en tâche de fond, force land() si une limite est franchie."""

    def __init__(self, drone: BaseDrone):
        self.drone = drone
        self._task: asyncio.Task | None = None
        self._stop = asyncio.Event()

    async def start(self) -> None:
        log.info("[safety] start (no-op pour l'instant — watchdog branché plus tard)")

    async def stop(self) -> None:
        self._stop.set()
        if self._task:
            await self._task

    async def _loop(self) -> None:
        # TODO: surveille batterie + altitude, déclenche land() si dépassement
        raise NotImplementedError
