import logging
import os
import socket
import sys
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ALERT_CPU_TEMP = float(os.getenv("ALERT_CPU_TEMP", "75"))
ALERT_GPU_TEMP = float(os.getenv("ALERT_GPU_TEMP", "80"))
ALERT_RAM_PCT = float(os.getenv("ALERT_RAM_PCT", "90"))
ALERT_VRAM_PCT = float(os.getenv("ALERT_VRAM_PCT", "90"))
CHECK_INTERVAL_MIN = int(os.getenv("CHECK_INTERVAL_MIN", "5"))
DATABASE_URL = os.getenv("DATABASE_URL")
HOSTNAME = os.getenv("HOSTNAME", socket.gethostname())
GPU_BACKEND = os.getenv("GPU_BACKEND", "")  # nvidia, amd, intel o vacío para auto-detect
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


def setup_logging():
    logging.basicConfig(
        level=LOG_LEVEL,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )


logger = logging.getLogger(__name__)


def validate_config(required_vars: list[str]) -> None:
    missing = [v for v in required_vars if not os.getenv(v)]
    if missing:
        logger.error(f"faltan variables de entorno requeridas: {', '.join(missing)}")
        sys.exit(1)

    db_url = os.getenv("DATABASE_URL")
    if db_url and not db_url.startswith("postgresql://"):
        logger.error("DATABASE_URL debe empezar con 'postgresql://'")
        sys.exit(1)

    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if chat_id and not chat_id.isdigit():
        logger.error("TELEGRAM_CHAT_ID debe ser numérico")
        sys.exit(1)
