# 🤖 AI-R: Autonomous Intelligent Reconnaissance Drone

A sophisticated autonomous drone control system powered by AI and computer vision. Control DJI Tello drones (or simulator) using natural language commands, with real-time YOLO object detection and LLM-based planning.

[🇫🇷 Français](#français) | [🇬🇧 English](#english)

---

## 🇬🇧 English

### Overview

**AI-R** is an intelligent drone control platform that combines:
- **Natural Language Processing**: Give commands in plain English/French to the drone
- **LLM-Powered Planning**: Uses Groq or Anthropic Claude to convert natural language into executable drone actions
- **Real-time Vision**: YOLOv8 object detection for autonomous obstacle avoidance and target tracking
- **Web Dashboard**: Modern web interface for control and monitoring
- **Hardware Support**: Works with DJI Tello drones or simulation mode

### Key Features

✅ **Natural Language Commands** - "Fly forward 2 meters", "Detect objects", "Return home"
✅ **Vision-Guided Autonomy** - Real-time YOLO detection and obstacle avoidance
✅ **Multi-LLM Support** - Groq (fast/free) or Anthropic Claude (advanced)
✅ **Live Video Stream** - MJPEG streaming from drone camera
✅ **Web-Based Control** - Responsive HTML/CSS/JS dashboard
✅ **Simulator Mode** - Test without hardware
✅ **Battery Management** - Automatic safety thresholds
✅ **Comprehensive Logging** - Full execution traces

### Requirements

- **Python 3.10+**
- **DJI Tello drone** (or use simulator mode)
- **API Keys**: Groq and/or Anthropic
- **WiFi**: For drone connectivity

### Installation

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd Ai-r
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # or: source .venv/bin/activate  # macOS/Linux
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables** (create `.env`)
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ANTHROPIC_API_KEY=your_anthropic_key_here
   DRONE_TYPE=simulator        # or "tello"
   TELLO_IP=192.168.1.100      # optional, for Tello in station mode
   ```

### Quick Start

#### Option 1: Web Dashboard (Recommended)
```bash
python app.py
```
- Automatically opens the web dashboard on `http://localhost:8000/launcher`
- Use the UI to select drone type and send commands

#### Option 2: Direct Command Line
```bash
python server.py &  # Start backend
# Then in another terminal:
# Send curl requests or WebSocket commands to http://localhost:8000/api/command
```

### Project Structure

```
.
├── app.py                    # Standalone executable entry point (PyInstaller)
├── server.py                 # FastAPI server with WebSocket & MJPEG streaming
├── config.py                 # Centralized configuration (env vars)
├── launcher_store.py         # Session/launch state management
│
├── frontend/                 # Web UI
│   ├── launcher.html/js      # Drone type selection & launch
│   ├── index.html/js         # Main cockpit dashboard
│   └── style.css
│
├── drone/                    # Drone abstraction layer
│   ├── base.py               # DroneBase abstract class
│   ├── simulator.py          # Virtual drone for testing
│   ├── tello.py              # DJI Tello implementation
│   ├── safety.py             # Battery, altitude, speed checks
│   └── __init__.py
│
├── vision/                   # Computer vision
│   ├── detector.py           # YOLOv8 integration
│   ├── stream.py             # MJPEG streaming
│   ├── obstacles.py          # Obstacle detection logic
│   └── __init__.py
│
├── llm/                      # LLM integrations
│   ├── base.py               # LLMBase abstract class
│   ├── groq_client.py        # Groq API client
│   ├── prompts.py            # System prompts for planning
│   └── __init__.py
│
├── orchestrator/             # Command orchestration
│   ├── planner.py            # Natural language → action plan
│   ├── executor.py           # Execute planned actions
│   ├── tools.py              # Available drone tools/actions
│   └── __init__.py
│
├── scripts/                  # Utilities
│   ├── setup_tello_wifi.py   # WiFi configuration helper
│   └── diag_tello_video.py   # Video stream diagnostics
│
├── requirements.txt          # Python dependencies
├── yolov8n.pt                # YOLOv8 nano model (pre-downloaded)
└── README.md
```

### Configuration

Edit `config.py` or set environment variables:

```python
# LLM Configuration
LLM_PROVIDER = "groq"           # "groq" | "claude"
LLM_MODEL_GROQ = "llama-3.3-70b-versatile"
LLM_MODEL_CLAUDE = "claude-sonnet-4-6"
LLM_TEMPERATURE = 0.2           # Lower = more deterministic

# Drone Configuration
DRONE_TYPE = "simulator"        # "simulator" | "tello"
TELLO_IP = "192.168.1.100"      # Optional, for station mode
MIN_BATTERY_PERCENT = 20        # Min battery before auto-landing
MAX_ALTITUDE_M = 5.0            # Safety ceiling
MAX_SPEED_MS = 1.0              # Movement speed limiter

# Vision
YOLO_CONFIDENCE = 0.5           # Detection confidence threshold
VIDEO_FPS = 30                  # Stream frame rate
```

### API Endpoints

#### Web Dashboard
- `GET /launcher` - Drone type selection page
- `GET /` - Main control dashboard
- `GET /stream` - MJPEG video stream

#### WebSocket (Real-time)
- `WS /ws` - Bidirectional command/response channel

#### REST API
- `POST /api/command` - Send natural language command
  ```json
  {"order": "Fly forward 2 meters"}
  ```
- `GET /api/status` - Get drone/system status
- `POST /api/launch` - Initialize drone session

### Usage Examples

**Web UI**:
1. Visit `http://localhost:8000/launcher`
2. Select drone type (Simulator or Tello)
3. Use dashboard to send commands:
   - "Fly forward"
   - "Detect objects in front"
   - "Take off and hover"

**Command Examples**:
- "Décolle et monte de 1 mètre" (French)
- "Take a picture and analyze it"
- "Avoid obstacles and fly around the room"
- "Return to starting position"

### Drone Setup

#### Simulator Mode
No setup needed! Just set `DRONE_TYPE=simulator` in config.

#### DJI Tello (WiFi)
1. Power on the Tello drone
2. Connect to its WiFi SSID (e.g., `TELLO-12345`)
3. Set `DRONE_TYPE=tello` and optionally `TELLO_IP` in config
4. Or run: `python scripts/setup_tello_wifi.py`

### Testing

```bash
# Run unit tests
pytest

# Run async tests
pytest -v --asyncio-mode=auto

# Specific module tests
pytest tests/ -k "vision" -v
```

### Packaging as Executable

Create a standalone `.exe` (Windows) with PyInstaller:

```bash
pip install pyinstaller pywebview

pyinstaller --onefile --windowed --name AI-R \
    --add-data "frontend;frontend" \
    --add-data "yolov8n.pt;." \
    app.py
```

Output: `dist/AI-R.exe`

### Troubleshooting

| Issue | Solution |
|-------|----------|
| "No module named 'groq'" | Run `pip install -r requirements.txt` |
| Drone not connecting | Check WiFi SSID, IP config, battery level |
| YOLO detection slow | Reduce `VIDEO_FPS` or use CPU inference |
| "API key invalid" | Verify `GROQ_API_KEY`/`ANTHROPIC_API_KEY` in `.env` |
| Web dashboard won't open | Check port 8000 is free: `netstat -ano \| findstr :8000` |

### Performance Tips

- **Simulator Mode**: Use for testing logic without hardware
- **Groq vs Claude**: Groq is ~10x faster and free, Claude is more capable
- **Vision**: YOLOv8 nano (current) is fast; swap for medium/large for better accuracy
- **Streaming**: Reduce FPS if network bandwidth is limited

### Contributing

1. Create a branch: `git checkout -b feature/your-feature`
2. Make changes and test
3. Submit a pull request

### License

MIT License - See LICENSE file

### Author

Developed for autonomous drone research and experimentation.

---

## 🇫🇷 Français

### Aperçu

**AI-R** est une plateforme de contrôle de drone intelligent qui combine:
- **Traitement du Langage Naturel**: Donnez des commandes en français/anglais au drone
- **Planification basée LLM**: Utilise Groq ou Anthropic Claude pour convertir le langage naturel en actions exécutables
- **Vision en Temps Réel**: Détection YOLO v8 pour l'évitement d'obstacles autonome et le suivi de cibles
- **Tableau de Bord Web**: Interface web moderne pour le contrôle et la surveillance
- **Support Matériel**: Fonctionne avec les drones DJI Tello ou en mode simulation

### Caractéristiques Principales

✅ **Commandes en Langage Naturel** - "Vole en avant de 2 mètres", "Détecte les objets"
✅ **Autonomie Guidée par la Vision** - Détection et évitement d'obstacles en temps réel
✅ **Support Multi-LLM** - Groq (rapide/gratuit) ou Anthropic Claude (avancé)
✅ **Flux Vidéo en Direct** - Streaming MJPEG depuis la caméra du drone
✅ **Contrôle Web** - Tableau de bord HTML/CSS/JS réactif
✅ **Mode Simulateur** - Testez sans matériel
✅ **Gestion de la Batterie** - Seuils de sécurité automatiques
✅ **Journalisation Complète** - Traces d'exécution complètes

### Prérequis

- **Python 3.10+**
- **Drone DJI Tello** (ou utilisez le mode simulateur)
- **Clés API**: Groq et/ou Anthropic
- **WiFi**: Pour la connectivité du drone

### Installation

1. **Clonez le dépôt**
   ```bash
   git clone <url-repo>
   cd Ai-r
   ```

2. **Créez un environnement virtuel**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   ```

3. **Installez les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurez les variables d'environnement** (créer `.env`)
   ```env
   GROQ_API_KEY=votre_clé_groq
   ANTHROPIC_API_KEY=votre_clé_anthropic
   DRONE_TYPE=simulator
   TELLO_IP=192.168.1.100
   ```

### Démarrage Rapide

#### Option 1: Tableau de Bord Web (Recommandé)
```bash
python app.py
```
- Ouvre automatiquement le tableau de bord web sur `http://localhost:8000/launcher`

#### Option 2: Ligne de Commande
```bash
python server.py &
# Puis envoyez des commandes curl ou WebSocket
```

### Configuration

Éditez `config.py` ou définissez des variables d'environnement:

```python
# LLM
LLM_PROVIDER = "groq"           # "groq" | "claude"
LLM_MODEL_GROQ = "llama-3.3-70b-versatile"

# Drone
DRONE_TYPE = "simulator"        # "simulator" | "tello"
MIN_BATTERY_PERCENT = 20
MAX_ALTITUDE_M = 5.0
MAX_SPEED_MS = 1.0

# Vision
YOLO_CONFIDENCE = 0.5
VIDEO_FPS = 30
```

### Exemples de Commandes

- "Décolle et monte de 1 mètre"
- "Détecte les objets devant"
- "Vole en avant"
- "Retour à la maison"
- "Prends une photo et analyse-la"

### Configuration du Drone

#### Mode Simulateur
Aucune configuration requise! Définissez simplement `DRONE_TYPE=simulator`

#### DJI Tello (WiFi)
1. Allumez le drone Tello
2. Connectez-vous à son WiFi (ex: `TELLO-12345`)
3. Définissez `DRONE_TYPE=tello` dans la configuration
4. Ou exécutez: `python scripts/setup_tello_wifi.py`

### Packaging en Exécutable

Créez un `.exe` autonome (Windows):

```bash
pip install pyinstaller pywebview

pyinstaller --onefile --windowed --name AI-R \
    --add-data "frontend;frontend" \
    --add-data "yolov8n.pt;." \
    app.py
```

Résultat: `dist/AI-R.exe`

### Dépannage

| Problème | Solution |
|----------|----------|
| "Aucun module nommé 'groq'" | Exécutez `pip install -r requirements.txt` |
| Le drone ne se connecte pas | Vérifiez SSID WiFi, configuration IP, niveau batterie |
| Détection YOLO lente | Réduisez `VIDEO_FPS` ou utilisez l'inférence CPU |
| Clé API invalide | Vérifiez `GROQ_API_KEY`/`ANTHROPIC_API_KEY` dans `.env` |
| Le tableau de bord web ne s'ouvre pas | Vérifiez que le port 8000 est libre |

### Astuces de Performance

- **Mode Simulateur**: Utilisez pour tester la logique sans matériel
- **Groq vs Claude**: Groq est ~10x plus rapide et gratuit, Claude est plus capable
- **Vision**: YOLOv8 nano (actuel) est rapide; basculez pour une meilleure précision
- **Streaming**: Réduisez FPS si la bande passante est limitée

### Licence

Licence MIT - Voir le fichier LICENSE

---

**Made with ❤️ for autonomous drone research**
