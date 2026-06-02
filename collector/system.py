import time
import psutil


def get_cpu_temperature():
    temps = psutil.sensors_temperatures()
    for key in ("coretemp", "cpu_thermal", "acpitz", "k10temp", "zenpmp"):
        if key in temps:
            return temps[key][0].current
    return None


def get_ram_usage():
    mem = psutil.virtual_memory()
    return {
        "total": mem.total,
        "available": mem.available,
        "percent": mem.percent,
        "used": mem.used,
    }


def get_uptime_seconds():
    return time.time() - psutil.boot_time()


def get_system_stats():
    return {
        "cpu_temp": get_cpu_temperature(),
        "ram": get_ram_usage(),
        "uptime_seconds": get_uptime_seconds(),
    }
