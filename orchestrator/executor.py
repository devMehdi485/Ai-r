"""Exécute un plan : appelle les méthodes du drone une à une, monitore.

ÉVITEMENT D'OBSTACLES :
Avant chaque move qui inclut une avancée frontale (dx > 0), on consulte
VisionStream pour savoir si un objet bloque la bande centrale. Si oui :
- on annule le move
- on logge l'alerte
- on continue avec l'étape suivante du plan (le drone ne s'écrase pas)
"""
import asyncio
import logging
from datetime import datetime
from pathlib import Path

import cv2

from drone.base import BaseDrone
from drone.safety import SafetyMonitor
from vision.detector import YoloDetector
from vision.stream import VisionStream

log = logging.getLogger(__name__)


class Executor:
    def __init__(self, drone: BaseDrone, detector: YoloDetector):
        self.drone = drone
        self.detector = detector
        self.vision = VisionStream(drone, detector)
        self.safety = SafetyMonitor(drone)
        self._started = False
        self.on_obstacle = None  # callback(label_list) appelé par le serveur

    async def _ensure_started(self) -> None:
        if self._started:
            return
        await self.drone.connect()
        await self.vision.start()
        await self.safety.start()
        self._started = True

    async def shutdown(self) -> None:
        if not self._started:
            return
        await self.safety.stop()
        await self.vision.stop()
        await self.drone.disconnect()

    async def run(self, plan: list[dict]) -> None:
        await self._ensure_started()
        for step in plan:
            name = step["name"]
            args = step.get("arguments") or {}
            log.info("Step: %s(%s)", name, args)
            await self._dispatch(name, args)

    async def _dispatch(self, name: str, args: dict) -> None:
        if name == "takeoff":
            await self.drone.takeoff()
        elif name == "land":
            await self.drone.land()
        elif name == "move":
            await self._safe_move(args)
        elif name == "rotate":
            await self.drone.rotate(args["degrees"])
        elif name == "wait":
            await asyncio.sleep(args["seconds"])
        elif name == "detect":
            label = args["label"]
            frame = await self.drone.get_video_frame()
            found = self.detector.find(frame, label)
            log.info("[detect] '%s' → %s", label, found)
        elif name == "capture_photo":
            frame = await self.drone.get_video_frame()
            Path("captures").mkdir(exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            path = f"captures/photo_{ts}.png"
            cv2.imwrite(path, frame)
            log.info("[photo] sauvegardée: %s", path)
        else:
            log.warning("Tool inconnu: %s", name)

    async def _safe_move(self, args: dict) -> None:
        """Check obstacle avant un mouvement frontal."""
        dx = float(args.get("dx", 0))
        dy = float(args.get("dy", 0))
        dz = float(args.get("dz", 0))

        # On bloque seulement les avancées frontales (dx > 0)
        if dx > 0 and self.vision.is_path_blocked():
            labels = [d.label for d in self.vision.latest_detections]
            log.warning("[OBSTACLE] move avant annulé — détections: %s", labels)
            if self.on_obstacle:
                try:
                    await self.on_obstacle(labels)
                except Exception:
                    log.exception("on_obstacle callback failed")
            return

        await self.drone.move(dx, dy, dz)
