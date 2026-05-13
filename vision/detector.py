"""Wrapper YOLOv8 pour la détection d'objets."""
from dataclasses import dataclass

import numpy as np

import config


@dataclass
class Detection:
    label: str
    confidence: float
    bbox: tuple[int, int, int, int]  # x1, y1, x2, y2


class YoloDetector:
    def __init__(self, model_path: str = config.YOLO_MODEL):
        self.model_path = model_path
        self.confidence = config.YOLO_CONFIDENCE
        self._model = None

    @property
    def model(self):
        # Lazy load : le téléchargement de yolov8n.pt (~6 Mo) ne se fait
        # qu'à la première détection, pas à l'import.
        if self._model is None:
            from ultralytics import YOLO
            self._model = YOLO(self.model_path)
        return self._model

    def detect(self, frame: np.ndarray) -> list[Detection]:
        if frame is None or frame.size == 0:
            return []
        results = self.model.predict(frame, conf=self.confidence, verbose=False)
        if not results:
            return []
        r = results[0]
        names = r.names
        out: list[Detection] = []
        for box in r.boxes:
            cls_id = int(box.cls)
            conf = float(box.conf)
            x1, y1, x2, y2 = (int(v) for v in box.xyxy[0].tolist())
            out.append(Detection(label=names[cls_id], confidence=conf, bbox=(x1, y1, x2, y2)))
        return out

    def find(self, frame: np.ndarray, label: str) -> Detection | None:
        matches = [d for d in self.detect(frame) if d.label.lower() == label.lower()]
        if not matches:
            return None
        return max(matches, key=lambda d: d.confidence)
