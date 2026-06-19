import time

from config import CHECK_INTERVAL_MIN, HOSTNAME
from database.repository import init_db, insert_telemetry
from collector.system import get_system_stats
from collector.gpu import get_gpu_stats


def main():
    init_db()
    print(f"Agente iniciado en '{HOSTNAME}'. Intervalo: {CHECK_INTERVAL_MIN} min.")

    while True:
        try:
            system = get_system_stats()
            gpu = get_gpu_stats()
            insert_telemetry(system, gpu, HOSTNAME)
            print(f"[{HOSTNAME}] Datos recolectados.")
        except Exception as e:
            print(f"[{HOSTNAME}] Error: {e}")

        time.sleep(CHECK_INTERVAL_MIN * 60)


if __name__ == "__main__":
    main()
