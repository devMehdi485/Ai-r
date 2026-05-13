"""Implémentation pour DJI Tello (et Tello EDU) via djitellopy."""
import asyncio
import logging
import math

import numpy as np

from drone.base import BaseDrone, DroneState

log = logging.getLogger(__name__)

MIN_MOVE_CM = 20
MAX_MOVE_CM = 500
MIN_ROT_DEG = 1
MAX_ROT_DEG = 360


class TelloDrone(BaseDrone):
    def __init__(self):
        from djitellopy import Tello
        import config
        if config.TELLO_IP:
            self._tello = Tello(host=config.TELLO_IP)
            self._mode = f"station ({config.TELLO_IP})"
        else:
            self._tello = Tello()
            self._mode = "direct (TELLO-XXXXXX)"
        self._frame_read = None
        self._connected = False
        self._telemetry_task: asyncio.Task | None = None
        self.state = DroneState()

    async def _run(self, fn, *args):
        return await asyncio.to_thread(fn, *args)

    async def connect(self) -> None:
        if self._connected:
            return
        log.info("[tello] connexion mode=%s", self._mode)
        await self._run(self._tello.connect)
        battery = await self._run(self._tello.get_battery)
        self.state.battery = float(battery)
        log.info("[tello] connecté, batterie=%d%%", battery)

        # Le flux vidéo (UDP 11111) échoue souvent en mode station sous Windows
        # (firewall, isolation client...). On le tente en best-effort.
        await self._try_start_video()

        self._connected = True
        self._telemetry_task = asyncio.create_task(self._telemetry_loop())

    async def _try_start_video(self) -> None:
        try:
            await self._run(self._tello.streamon)
            await asyncio.sleep(2.0)
            self._frame_read = await asyncio.to_thread(self._tello.get_frame_read)
            log.info("[tello] flux vidéo OK")
        except Exception as e:
            log.warning(
                "[tello] flux vidéo indisponible (%s) — on continue sans vidéo. "
                "Causes fréquentes : firewall Windows bloquant UDP 11111, "
                "isolation client du wifi.",
                type(e).__name__,
            )
            self._frame_read = None
            try:
                await self._run(self._tello.streamoff)
            except Exception:
                pass

    async def disconnect(self) -> None:
        if not self._connected:
            return
        if self._telemetry_task:
            self._telemetry_task.cancel()
        try:
            if self.state.is_flying:
                await self.land()
        finally:
            try:
                await self._run(self._tello.streamoff)
            except Exception:
                pass
            await self._run(self._tello.end)
            self._connected = False

    async def _telemetry_loop(self) -> None:
        while True:
            try:
                self.state.battery = float(await self._run(self._tello.get_battery))
                height_cm = await self._run(self._tello.get_height)
                self.state.z = height_cm / 100.0
                self.state.yaw = float(await self._run(self._tello.get_yaw)) % 360
            except Exception:
                log.debug("telemetry read failed", exc_info=True)
            await asyncio.sleep(0.5)

    async def takeoff(self) -> None:
        if self.state.is_flying:
            log.info("[tello] takeoff ignoré : déjà en vol")
            return
        log.info("[tello] takeoff")
        await self._run(self._tello.takeoff)
        self.state.is_flying = True
        self.state.z = 1.0

    async def land(self) -> None:
        if not self.state.is_flying:
            log.info("[tello] land ignoré : au sol")
            return
        log.info("[tello] land")
        await self._run(self._tello.land)
        self.state.is_flying = False
        self.state.z = 0.0

    async def move(self, dx: float, dy: float, dz: float) -> None:
        if not self.state.is_flying:
            log.warning("[tello] move ignoré : pas en vol")
            return
        await self._move_axis(dx, "forward", "back")
        await self._move_axis(dy, "right", "left")
        await self._move_axis(dz, "up", "down")

        yaw_rad = math.radians(self.state.yaw)
        wx = dx * math.cos(yaw_rad) - dy * math.sin(yaw_rad)
        wy = dx * math.sin(yaw_rad) + dy * math.cos(yaw_rad)
        self.state.x += wx
        self.state.y += wy

        log.info(
            "[tello] pos≈(%.2f, %.2f, %.2f) yaw=%.1f° batt=%.1f%%",
            self.state.x, self.state.y, self.state.z,
            self.state.yaw, self.state.battery,
        )

    async def _move_axis(self, meters: float, pos_dir: str, neg_dir: str) -> None:
        cm = int(round(meters * 100))
        if cm == 0:
            return
        direction = pos_dir if cm > 0 else neg_dir
        cm = abs(cm)
        if cm < MIN_MOVE_CM:
            log.warning(
                "[tello] move %s %dcm ignoré : minimum %dcm imposé par le SDK",
                direction, cm, MIN_MOVE_CM,
            )
            return
        cm = min(cm, MAX_MOVE_CM)
        method = getattr(self._tello, f"move_{direction}")
        await self._run(method, cm)

    async def rotate(self, degrees: float) -> None:
        if not self.state.is_flying:
            log.warning("[tello] rotate ignoré : pas en vol")
            return
        deg = int(round(degrees))
        if abs(deg) < MIN_ROT_DEG:
            return
        if deg > 0:
            await self._run(self._tello.rotate_clockwise, min(MAX_ROT_DEG, deg))
        else:
            await self._run(self._tello.rotate_counter_clockwise, min(MAX_ROT_DEG, abs(deg)))
        self.state.yaw = (self.state.yaw + degrees) % 360

    async def get_video_frame(self) -> np.ndarray:
        if self._frame_read is None:
            return np.zeros((720, 960, 3), dtype=np.uint8)
        frame = self._frame_read.frame
        if frame is None:
            return np.zeros((720, 960, 3), dtype=np.uint8)
        return frame

    async def get_state(self) -> DroneState:
        return self.state

    async def emergency_stop(self) -> None:
        log.warning("[tello] EMERGENCY STOP — coupure moteurs")
        await self._run(self._tello.emergency)
        self.state.is_flying = False
