"""Serveur FastAPI : launcher + cockpit + WebSocket + flux MJPEG + YOLO."""
import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import config
import launcher_store
from drone.simulator import SimulatorDrone
from drone.tello import TelloDrone
from llm.groq_client import GroqClient
from orchestrator.executor import Executor
from orchestrator.planner import Planner
from vision.detector import YoloDetector

log = logging.getLogger(__name__)

FRONTEND_DIR = Path(__file__).parent / "frontend"


class CommandRequest(BaseModel):
    order: str


class LaunchRequest(BaseModel):
    mode: str  # "simulator" | "tello"
    drone_id: str | None = None


class TestConnectionRequest(BaseModel):
    ip: str


class App:
    def __init__(self):
        self.llm = GroqClient()
        self.detector = YoloDetector()
        self.planner = Planner(self.llm)
        self.drone = None
        self.executor: Executor | None = None
        self.clients: set[WebSocket] = set()
        self._broadcaster_task: asyncio.Task | None = None
        self._switch_lock = asyncio.Lock()

    def _build_drone(self, mode: str, ip: str | None):
        if mode == "tello":
            if ip:
                # Override config.TELLO_IP en mémoire pour cette instance
                config.TELLO_IP = ip
            return TelloDrone()
        return SimulatorDrone()

    async def switch_target(self, mode: str, drone_id: str | None) -> dict:
        """Recrée le drone et l'executor selon le mode choisi."""
        async with self._switch_lock:
            ip = None
            drone_info = None
            if mode == "tello":
                if not drone_id:
                    raise ValueError("drone_id requis pour mode=tello")
                drones = launcher_store.load_drones()
                drone_info = next((d for d in drones if d["id"] == drone_id), None)
                if not drone_info:
                    raise ValueError(f"drone {drone_id} introuvable")
                ip = drone_info["ip"]

            # Tear down old
            if self.executor and self.executor._started:
                try:
                    await self.executor.shutdown()
                except Exception:
                    log.exception("old executor shutdown failed")

            # Build new
            self.drone = self._build_drone(mode, ip)
            self.executor = Executor(self.drone, self.detector)
            self.executor.on_obstacle = self._on_obstacle

            launcher_store.save_active(mode, drone_id)
            log.info("[launch] mode=%s drone=%s ip=%s", mode, drone_id, ip)

            # autostart
            asyncio.create_task(_safe_autostart(self))
            return {"mode": mode, "drone": drone_info}

    async def _on_obstacle(self, labels: list[str]):
        await self.broadcast({"type": "obstacle", "labels": labels})

    async def broadcast(self, msg: dict) -> None:
        dead = set()
        for ws in self.clients:
            try:
                await ws.send_json(msg)
            except Exception:
                dead.add(ws)
        self.clients -= dead

    async def state_loop(self) -> None:
        while True:
            try:
                if self.drone is not None:
                    s = await self.drone.get_state()
                    dets, blocked = [], False
                    if self.executor and self.executor._started:
                        for d in self.executor.vision.latest_detections[:10]:
                            dets.append({"label": d.label, "confidence": round(d.confidence, 2)})
                        blocked = self.executor.vision.is_path_blocked()
                    await self.broadcast({
                        "type": "state",
                        "state": {
                            "x": s.x, "y": s.y, "z": s.z,
                            "yaw": s.yaw, "battery": s.battery,
                            "is_flying": s.is_flying,
                        },
                        "detections": dets,
                        "path_blocked": blocked,
                    })
            except Exception:
                log.exception("state loop error")
            await asyncio.sleep(0.1)


state: App | None = None


async def _safe_autostart(app_state: App):
    try:
        await app_state.executor._ensure_started()
        log.info("[autostart] drone + vision démarrés ✓")
    except Exception:
        log.exception("[autostart] échec — vidéo vide jusqu'à une commande réussie")


@asynccontextmanager
async def lifespan(_: FastAPI):
    global state
    logging.basicConfig(level=config.LOG_LEVEL)
    state = App()
    state._broadcaster_task = asyncio.create_task(state.state_loop())

    # Restaurer la dernière config active
    active = launcher_store.load_active()
    try:
        await state.switch_target(active["mode"], active.get("drone_id"))
    except Exception:
        log.exception("init switch failed — fallback simulator")
        await state.switch_target("simulator", None)

    yield

    if state._broadcaster_task:
        state._broadcaster_task.cancel()
    if state.executor:
        await state.executor.shutdown()


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


# ============ Pages ============
@app.get("/")
async def index():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/launcher")
async def launcher_page():
    return FileResponse(FRONTEND_DIR / "launcher.html")


# ============ API drones ============
@app.get("/api/drones")
async def list_drones():
    return {"drones": launcher_store.load_drones()}


@app.post("/api/drones")
async def create_drone(payload: dict):
    return launcher_store.add_drone(payload)


@app.put("/api/drones/{drone_id}")
async def update_drone(drone_id: str, payload: dict):
    drone = launcher_store.update_drone(drone_id, payload)
    if not drone:
        raise HTTPException(404, "drone not found")
    return drone


@app.delete("/api/drones/{drone_id}")
async def remove_drone(drone_id: str):
    if not launcher_store.delete_drone(drone_id):
        raise HTTPException(404, "drone not found")
    return {"ok": True}


@app.post("/api/test-connection")
async def test_connection(req: TestConnectionRequest):
    return await asyncio.to_thread(launcher_store.ping_tello, req.ip)


@app.post("/api/launch")
async def launch(req: LaunchRequest):
    try:
        return await state.switch_target(req.mode, req.drone_id)
    except ValueError as e:
        raise HTTPException(400, str(e))


# ============ Cockpit endpoints ============
@app.post("/command")
async def command(req: CommandRequest):
    if state.executor is None:
        raise HTTPException(503, "executor non initialisé")
    plan = await state.planner.plan(req.order)
    await state.broadcast({"type": "plan", "order": req.order, "plan": plan})
    asyncio.create_task(_run_plan(plan))
    return {"plan": plan}


async def _run_plan(plan):
    try:
        await state.executor.run(plan)
        await state.broadcast({"type": "done"})
    except Exception as e:
        log.exception("plan failed")
        await state.broadcast({"type": "error", "message": str(e)})


@app.get("/video")
async def video_feed():
    from vision.stream import get_placeholder_jpeg
    boundary = b"--frame"

    async def gen():
        try:
            while True:
                data = None
                if state and state.executor and state.executor._started:
                    data = state.executor.vision.get_jpeg()
                if not data:
                    data = get_placeholder_jpeg()
                yield boundary + b"\r\n"
                yield b"Content-Type: image/jpeg\r\n"
                yield f"Content-Length: {len(data)}\r\n\r\n".encode()
                yield data
                yield b"\r\n"
                await asyncio.sleep(1 / 15)
        except asyncio.CancelledError:
            return

    return StreamingResponse(gen(), media_type="multipart/x-mixed-replace; boundary=frame")


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    state.clients.add(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        state.clients.discard(ws)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=False)
