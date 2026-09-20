import logging
import time

from collector.gpu import get_gpu_stats
from collector.system import get_system_stats
from config import CHECK_INTERVAL_MIN, HOSTNAME, setup_logging, validate_config
from database.repository import init_db, insert_telemetry

logger = logging.getLogger(__name__)


def main():
    setup_logging()
    validate_config(["DATABASE_URL"])
    init_db()
    logger.info(f"Agente iniciado en '{HOSTNAME}'. Intervalo: {CHECK_INTERVAL_MIN} min.")

    while True:
        try:
            system = get_system_stats()
            gpu = get_gpu_stats()
            insert_telemetry(system, gpu, HOSTNAME)
            logger.debug(f"[{HOSTNAME}] Datos recolectados.")
        except Exception as e:
            logger.error(f"[{HOSTNAME}] Error: {e}")

        time.sleep(CHECK_INTERVAL_MIN * 60)


if __name__ == "__main__":
    main()
