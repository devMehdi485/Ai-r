"""Drone virtuel.

En mode simulateur, si une webcam est disponible elle sert de "caméra du drone"
— très pratique pour tester YOLO et l'évitement d'obstacles sans matériel.
"""
import asyncio
import logging
import math

import numpy as np

from drone.base import BaseDrone, DroneState

log = logging.getLogger(__name__)

SPEED_MS = 1.0
ROTATION_DEG_S = 90.0
BATTERY_DRAIN_PER_MOVE = 0.5


class SimulatorDrone(BaseDrone):
    def __init__(self):
        self.state = DroneState()
        self._cap = None

    async def connect(self) -> None:
        log.info("[sim] connect")
        try:
            import cv2
            cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if cap.isOpened():
                self._cap = cap
                log.info("[sim] webcam ouverte — utilisée comme caméra du drone")
            else:
                cap.release()
                log.info("[sim] pas de webcam — frames noires renvoyées")
        except Exception:
            log.warning("[sim] échec init webcam", exc_info=True)

    async def disconnect(self) -> None:
        log.info("[sim] disconnect")
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    async def _interpolate(self, duration: float, apply):
        steps = max(1, int(duration / 0.03))
        for i in range(1, steps + 1):
            apply(i / steps)
            await asyncio.sleep(duration / steps)

    async def takeoff(self) -> None:
        if self.state.is_flying:
            return
        log.info("[sim] takeoff")
        self.state.is_flying = True
        await self._interpolate(1.0, lambda t: setattr(self.state, "z", t * 1.0))

    async def land(self) -> None:
        if not self.state.is_flying:
            return
        log.info("[sim] land depuis z=%.2f", self.state.z)
        z0 = self.state.z
        duration = max(0.3, z0 / SPEED_MS)
        await self._interpolate(duration, lambda t: setattr(self.state, "z", z0 * (1 - t)))
        self.state.z = 0.0
        self.state.is_flying = False

    async def move(self, dx: float, dy: float, dz: float) -> None:
        if not self.state.is_flying:
            log.warning("[sim] move ignoré : pas en vol")
            return
        yaw_rad = math.radians(self.state.yaw)
        wx = dx * math.cos(yaw_rad) - dy * math.sin(yaw_rad)
        wy = dx * math.sin(yaw_rad) + dy * math.cos(yaw_rad)
        distance = math.sqrt(dx * dx + dy * dy + dz * dz)
        duration = max(0.1, distance / SPEED_MS)
        x0, y0, z0 = self.state.x, self.state.y, self.state.z
        target_z = max(0.0, z0 + dz)

        def step(t):
            self.state.x = x0 + wx * t
            self.state.y = y0 + wy * t
            self.state.z = z0 + (target_z - z0) * t

        await self._interpolate(duration, step)
        self.state.battery = max(0.0, self.state.battery - BATTERY_DRAIN_PER_MOVE)

    async def rotate(self, degrees: float) -> None:
        if not self.state.is_flying:
            return
        duration = max(0.1, abs(degrees) / ROTATION_DEG_S)
        yaw0 = self.state.yaw
        await self._interpolate(
            duration,
            lambda t: setattr(self.state, "yaw", (yaw0 + degrees * t) % 360),
        )

    async def get_video_frame(self) -> np.ndarray:
        if self._cap is not None:
            ok, frame = await asyncio.to_thread(self._cap.read)
            if ok and frame is not None:
                return frame
        return np.zeros((480, 640, 3), dtype=np.uint8)

    async def get_state(self) -> DroneState:
        return self.state

    async def emergency_stop(self) -> None:
        log.warning("[sim] EMERGENCY STOP")
        self.state.is_flying = False
        self.state.z = 0.0
