"""Central paths & constants for the Nanobot Platform control plane."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = Path(os.environ.get("NANOBOT_PLATFORM_DATA", BASE_DIR / "data"))
CONFIG_DIR = DATA_DIR / "config"          # nanobot-style config: nanobot.yaml + agents/*.md
AGENTS_DIR = CONFIG_DIR / "agents"
UPLOAD_DIR = DATA_DIR / "uploads"
LOG_DIR = DATA_DIR / "logs"
DB_PATH = DATA_DIR / "platform.db"
SECRET_FILE = DATA_DIR / "secret.key"
APP_LOG = LOG_DIR / "app.log"
STARTUP_LOG = LOG_DIR / "startup.log"

NANOBOT_YAML = CONFIG_DIR / "nanobot.yaml"

SESSION_TTL_DAYS = 30
MAX_UPLOAD_MB = 50
