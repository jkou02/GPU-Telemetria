import os
import socket
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
