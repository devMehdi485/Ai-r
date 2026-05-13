"""Configuration centralisée du projet."""
import os
from dotenv import load_dotenv

load_dotenv()

# --- LLM ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
LLM_PROVIDER = "groq"  # "groq" | "claude"
LLM_MODEL_GROQ = "llama-3.3-70b-versatile"
LLM_MODEL_CLAUDE = "claude-sonnet-4-6"
LLM_TEMPERATURE = 0.2

# --- Drone ---
DRONE_TYPE = os.getenv("DRONE_TYPE", "simulator")  # "simulator" | "tello"
TELLO_IP = os.getenv("TELLO_IP")  # défini = mode station ; vide = mode direct AP
MIN_BATTERY_PERCENT = 20
MAX_ALTITUDE_M = 5.0
MAX_SPEED_MS = 1.0
COMMAND_TIMEOUT_S = 45.0

# --- Vision ---
YOLO_MODEL = "yolov8n.pt"
YOLO_CONFIDENCE = 0.5
VIDEO_FPS = 30

# --- Logs ---
LOG_LEVEL = "INFO"
LOG_DIR = "logs"
