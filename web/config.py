import os
from pathlib import Path

# === PATHS ===
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_URL = "sqlite:///./gruppenrun_bot.db"

# === SERVER ===
SERVER_HOST = os.getenv("WEB_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("WEB_PORT", 8000))

# === BOT ===
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
