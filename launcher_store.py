"""Persistance des drones Tello (liste, IPs, credentials wifi).

Stocké dans %APPDATA%/AI-R/drones.json (Windows) ou ~/.config/ai-r/drones.json.
"""
import json
import os
import socket
import time
import uuid
from pathlib import Path


def _config_dir() -> Path:
    if os.name == "nt":
        base = Path(os.getenv("APPDATA", str(Path.home() / "AppData/Roaming")))
    else:
        base = Path(os.getenv("XDG_CONFIG_HOME", str(Path.home() / ".config")))
    d = base / "AI-R"
    d.mkdir(parents=True, exist_ok=True)
    return d


STORE_PATH = _config_dir() / "drones.json"
ACTIVE_PATH = _config_dir() / "active.json"


def load_drones() -> list[dict]:
    if not STORE_PATH.exists():
        return []
    try:
        return json.loads(STORE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_drones(drones: list[dict]) -> None:
    STORE_PATH.write_text(json.dumps(drones, indent=2), encoding="utf-8")


def add_drone(payload: dict) -> dict:
    drones = load_drones()
    drone = {
        "id": uuid.uuid4().hex[:10],
        "name": payload.get("name", "Tello"),
        "ssid": payload.get("ssid", ""),
        "pw": payload.get("pw", ""),
        "ip": payload.get("ip", ""),
        "battery": payload.get("battery", 100),
        "status": payload.get("status", "new"),
        "last_seen": payload.get("last_seen", "à l'instant"),
    }
    drones.append(drone)
    save_drones(drones)
    return drone


def update_drone(drone_id: str, payload: dict) -> dict | None:
    drones = load_drones()
    for d in drones:
        if d["id"] == drone_id:
            d.update({k: v for k, v in payload.items() if k != "id"})
            save_drones(drones)
            return d
    return None


def delete_drone(drone_id: str) -> bool:
    drones = load_drones()
    new = [d for d in drones if d["id"] != drone_id]
    if len(new) == len(drones):
        return False
    save_drones(new)
    return True


def load_active() -> dict:
    if not ACTIVE_PATH.exists():
        return {"mode": "simulator", "drone_id": None}
    try:
        return json.loads(ACTIVE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"mode": "simulator", "drone_id": None}


def save_active(mode: str, drone_id: str | None) -> None:
    ACTIVE_PATH.write_text(
        json.dumps({"mode": mode, "drone_id": drone_id}, indent=2),
        encoding="utf-8",
    )


def ping_tello(ip: str, timeout: float = 3.0) -> dict:
    """Envoie 'command' puis 'battery?' au Tello. Renvoie {ok, battery, message}."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("", 0))
        sock.settimeout(timeout)
        sock.sendto(b"command", (ip, 8889))
        data, _ = sock.recvfrom(1024)
        if data.decode(errors="ignore").strip().lower() != "ok":
            return {"ok": False, "message": "réponse 'command' inattendue"}
        sock.sendto(b"battery?", (ip, 8889))
        data, _ = sock.recvfrom(1024)
        battery = int(data.decode(errors="ignore").strip())
        sock.close()
        return {"ok": True, "battery": battery, "message": "OK"}
    except socket.timeout:
        return {"ok": False, "message": "timeout — vérifier wifi/firewall"}
    except Exception as e:
        return {"ok": False, "message": f"{type(e).__name__}: {e}"}
