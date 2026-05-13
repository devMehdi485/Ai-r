"""Point d'entrée pour le binaire .exe.

- Démarre uvicorn dans un thread
- Ouvre une fenêtre native (PyWebView si dispo, sinon navigateur par défaut)
- Pointe vers /launcher en premier

Pour packager :
    pip install pyinstaller pywebview
    pyinstaller --onefile --windowed --name AI-R \
        --add-data "frontend;frontend" \
        --add-data "yolov8n.pt;." \
        app.py
"""
import os
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path

import uvicorn

HOST = "127.0.0.1"
PORT = 8000
LAUNCHER_URL = f"http://{HOST}:{PORT}/launcher"


def resource_path(rel: str) -> Path:
    """Résout un chemin compatible PyInstaller (frozen) et dev."""
    if getattr(sys, "frozen", False):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).parent
    return base / rel


def wait_for_port(host: str, port: int, timeout: float = 30.0) -> bool:
    """Attend que le port soit ouvert (le serveur est prêt)."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except (OSError, ConnectionRefusedError):
            time.sleep(0.2)
    return False


def run_server():
    # Forcer le cwd au dossier des assets pour que frontend/ soit trouvé
    os.chdir(resource_path(""))
    uvicorn.run(
        "server:app",
        host=HOST,
        port=PORT,
        log_level="info",
        access_log=False,
    )


def main():
    # Lancer uvicorn dans un thread (daemon = tué à la fermeture)
    t = threading.Thread(target=run_server, daemon=True)
    t.start()

    if not wait_for_port(HOST, PORT, timeout=20):
        print(f"❌ Le serveur n'a pas démarré sur {HOST}:{PORT}")
        sys.exit(1)

    # Préfère PyWebView pour un vrai look "app Windows"
    try:
        import webview
        win = webview.create_window(
            "AI-R",
            LAUNCHER_URL,
            width=1180,
            height=780,
            min_size=(960, 600),
            background_color="#ececef",
        )
        webview.start()
    except ImportError:
        # Fallback : navigateur par défaut
        webbrowser.open(LAUNCHER_URL)
        # Garder le process vivant
        try:
            while t.is_alive():
                t.join(1.0)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
