"""Logique d'évitement d'obstacles à partir des détections YOLO."""
from vision.detector import Detection

# Si une bbox couvre plus que ce ratio de la bande centrale → obstacle proche
BLOCK_RATIO = 0.15


def is_path_blocked(
    detections: list[Detection],
    frame_width: int,
    frame_height: int,
    center_band: tuple[float, float] = (0.4, 0.6),
) -> bool:
    """True si un objet occupe le centre vertical de l'image (zone droit devant)."""
    if not detections:
        return False
    band_left = frame_width * center_band[0]
    band_right = frame_width * center_band[1]
    band_area = (band_right - band_left) * frame_height

    for d in detections:
        x1, y1, x2, y2 = d.bbox
        # intersection avec la bande centrale
        ix1 = max(x1, band_left)
        ix2 = min(x2, band_right)
        if ix2 <= ix1:
            continue
        iw = ix2 - ix1
        ih = y2 - y1
        if (iw * ih) / band_area >= BLOCK_RATIO:
            return True
    return False


def avoidance_direction(
    detections: list[Detection],
    frame_width: int,
) -> str:
    """Renvoie 'left', 'right' ou 'stop' selon la zone la plus libre."""
    if not detections:
        return "stop"
    half = frame_width / 2
    left_area = right_area = 0
    for d in detections:
        x1, y1, x2, y2 = d.bbox
        h = y2 - y1
        if x2 <= half:
            left_area += (x2 - x1) * h
        elif x1 >= half:
            right_area += (x2 - x1) * h
        else:
            # à cheval
            left_area += (half - x1) * h
            right_area += (x2 - half) * h
    if left_area < right_area:
        return "left"
    if right_area < left_area:
        return "right"
    return "stop"
