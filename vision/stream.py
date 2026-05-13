"""Boucle asynchrone : récupère les frames du drone, exécute YOLO, annote."""
import asyncio
import logging

import cv2
import numpy as np

from drone.base import BaseDrone
from vision.detector import Detection, YoloDetector

log = logging.getLogger(__name__)

COLOR_SAFE = (50, 200, 50)
COLOR_WARN = (0, 165, 255)
COLOR_DANGER = (0, 0, 255)

DANGER_LABELS = {"person", "dog", "cat", "bird", "horse"}
WARN_LABELS = {"chair", "couch", "potted plant", "tv", "laptop", "bottle", "cup"}


class VisionStream:
    """Lit le flux du drone, fait tourner YOLO, expose la dernière frame annotée."""

    def __init__(
        self,
        drone: BaseDrone,
        detector: YoloDetector,
        fps: int = 15,
        detect_every_n: int = 3,
    ):
        self.drone = drone
        self.detector = detector
        self.fps = fps
        self.detect_every_n = detect_every_n

        self.latest_frame: np.ndarray | None = None
        self.latest_annotated: np.ndarray | None = None
        self.latest_detections: list[Detection] = []

        self._frame_count = 0
        self._task: asyncio.Task | None = None
        self._stop = asyncio.Event()

    async def start(self) -> None:
        if self._task is not None:
            return
        self._stop.clear()
        self._task = asyncio.create_task(self._loop())
        log.info("[vision] boucle démarrée (fps=%d, YOLO 1 frame/%d)",
                 self.fps, self.detect_every_n)

    async def stop(self) -> None:
        self._stop.set()
        if self._task:
            try:
                await self._task
            except Exception:
                pass
            self._task = None

    async def _loop(self) -> None:
        period = 1.0 / max(1, self.fps)
        while not self._stop.is_set():
            t0 = asyncio.get_event_loop().time()
            try:
                frame = await self.drone.get_video_frame()
                if frame is not None and frame.size > 0:
                    self.latest_frame = frame
                    self._frame_count += 1
                    if self._frame_count % self.detect_every_n == 0:
                        self.latest_detections = await asyncio.to_thread(
                            self.detector.detect, frame
                        )
                    self.latest_annotated = self._annotate(frame, self.latest_detections)
            except Exception:
                log.exception("vision loop error")
            elapsed = asyncio.get_event_loop().time() - t0
            await asyncio.sleep(max(0.0, period - elapsed))

    def _annotate(self, frame: np.ndarray, detections: list[Detection]) -> np.ndarray:
        out = frame.copy()
        h, w = out.shape[:2]
        # bande centrale = zone "devant" le drone, où on cherche les obstacles
        cv2.rectangle(out, (int(w * 0.4), 0), (int(w * 0.6), h), (60, 60, 60), 1)

        for d in detections:
            color = self._color_for(d.label)
            x1, y1, x2, y2 = d.bbox
            cv2.rectangle(out, (x1, y1), (x2, y2), color, 2)
            label = f"{d.label} {d.confidence:.2f}"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(out, (x1, y1 - th - 6), (x1 + tw + 4, y1), color, -1)
            cv2.putText(out, label, (x1 + 2, y1 - 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

        hud = f"detections: {len(detections)}"
        cv2.putText(out, hud, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                    (255, 255, 255), 2, cv2.LINE_AA)

        if self.is_path_blocked():
            cv2.putText(out, "OBSTACLE !", (10, 55), cv2.FONT_HERSHEY_SIMPLEX,
                        0.8, COLOR_DANGER, 2, cv2.LINE_AA)
            cv2.rectangle(out, (2, 2), (w - 2, h - 2), COLOR_DANGER, 4)
        return out

    @staticmethod
    def _color_for(label: str) -> tuple[int, int, int]:
        if label in DANGER_LABELS:
            return COLOR_DANGER
        if label in WARN_LABELS:
            return COLOR_WARN
        return COLOR_SAFE

    def get_jpeg(self, quality: int = 70) -> bytes | None:
        frame = self.latest_annotated if self.latest_annotated is not None else self.latest_frame
        if frame is None:
            return None
        ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
        return buf.tobytes() if ok else None

    def is_path_blocked(self) -> bool:
        """True si un objet croise la bande centrale du champ de vision."""
        from vision.obstacles import is_path_blocked
        if self.latest_frame is None:
            return False
        h, w = self.latest_frame.shape[:2]
        return is_path_blocked(self.latest_detections, w, h)

    def suggest_avoidance(self) -> str:
        """Renvoie 'left', 'right' ou 'stop' pour contourner l'obstacle."""
        from vision.obstacles import avoidance_direction
        if self.latest_frame is None:
            return "stop"
        _, w = self.latest_frame.shape[:2], self.latest_frame.shape[1]
        return avoidance_direction(self.latest_detections, w)


_PLACEHOLDER: bytes | None = None


def get_placeholder_jpeg(message: str = "En attente du flux video...") -> bytes:
    """Image générique servie tant qu'aucune frame n'est dispo."""
    global _PLACEHOLDER
    if _PLACEHOLDER is None:
        img = np.zeros((360, 640, 3), dtype=np.uint8)
        cv2.putText(img, message, (40, 190), cv2.FONT_HERSHEY_SIMPLEX,
                    0.8, (200, 200, 200), 2, cv2.LINE_AA)
        ok, buf = cv2.imencode(".jpg", img)
        _PLACEHOLDER = buf.tobytes() if ok else b""
    return _PLACEHOLDER
