import logging
import signal
import sys
import time

from collector.gpu import get_gpu_stats
from collector.system import get_system_stats
from config import CHECK_INTERVAL_MIN, HOSTNAME, setup_logging, validate_config
from database.repository import init_db, insert_telemetry

logger = logging.getLogger(__name__)

_running = True


def _shutdown(signum, frame):
    global _running
    _running = False
    logger.info(f"Señal {signum} recibida. Iniciando shutdown graceful...")


def main():
    setup_logging()
    validate_config(["DATABASE_URL"])
    init_db()
    logger.info(f"Agente iniciado en '{HOSTNAME}'. Intervalo: {CHECK_INTERVAL_MIN} min.")

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    while _running:
        try:
            system = get_system_stats()
            gpu = get_gpu_stats()
            insert_telemetry(system, gpu, HOSTNAME)
            logger.debug(f"[{HOSTNAME}] Datos recolectados.")
        except Exception as e:
            logger.error(f"[{HOSTNAME}] Error: {e}")

        for _ in range(int(CHECK_INTERVAL_MIN * 60)):
            if not _running:
                break
            time.sleep(1)

    logger.info("Agente detenido correctamente.")
    sys.exit(0)


if __name__ == "__main__":
    main()
