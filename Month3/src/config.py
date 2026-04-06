# ============================================================
#  src/config.py
#  Loads every setting from config/settings.env and makes
#  them available to all other modules via simple imports.
#  Also sets up the shared logging system.
# ============================================================

import os
import logging
from pathlib import Path

# ----------------------------------------------------------
# Locate the project root no matter where Python is run from
# ----------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent   # …/weather_project/

ENV_FILE = ROOT / "config" / "settings.env"

# ----------------------------------------------------------
# Read the .env file into os.environ
# ----------------------------------------------------------
def _load_env(path: Path) -> None:
    if not path.exists():
        return
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())

_load_env(ENV_FILE)

# ----------------------------------------------------------
# API
# ----------------------------------------------------------
API_KEY  = os.environ.get("API_KEY", "")
BASE_URL = "https://api.openweathermap.org/data/2.5"

# ----------------------------------------------------------
# Cities
# ----------------------------------------------------------
CITIES = [c.strip() for c in
          os.environ.get("CITIES", "Mumbai,Delhi,Bangalore").split(",")]

# ----------------------------------------------------------
# Alert thresholds
# ----------------------------------------------------------
TEMP_HIGH  = float(os.environ.get("TEMP_HIGH_THRESHOLD",  "35"))
TEMP_LOW   = float(os.environ.get("TEMP_LOW_THRESHOLD",   "5"))
HUM_HIGH   = float(os.environ.get("HUMIDITY_HIGH_THRESHOLD", "80"))
WIND_HIGH  = float(os.environ.get("WIND_SPEED_THRESHOLD", "50"))

# ----------------------------------------------------------
# Scheduler
# ----------------------------------------------------------
COLLECT_INTERVAL = int(os.environ.get("COLLECT_INTERVAL_MINUTES", "60"))

# ----------------------------------------------------------
# Paths
# ----------------------------------------------------------
DB_PATH     = ROOT / "database" / "weather_data.db"
LOGS_DIR    = ROOT / "logs"
REPORTS_DIR = ROOT / "reports"

# Make sure folders exist
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------
# Logging — one shared setup for the whole project
# ----------------------------------------------------------
LOG_FILE = LOGS_DIR / "pipeline.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(),                            # terminal
        logging.FileHandler(LOG_FILE, encoding="utf-8"),   # file
    ],
)

def get_logger(name: str) -> logging.Logger:
    """Call this in every module:  logger = get_logger(__name__)"""
    return logging.getLogger(name)
