from config import ALERT_CPU_TEMP, ALERT_GPU_TEMP, ALERT_RAM_PCT, ALERT_VRAM_PCT


def _fmt_bytes(b):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} PB"


def _fmt_uptime(seconds):
    parts = []
    days, seconds = divmod(int(seconds), 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, _ = divmod(seconds, 60)
    if days:
        parts.append(f"{days}d")
    parts.append(f"{hours}h")
    parts.append(f"{minutes}m")
    return " ".join(parts)


def format_status(system, gpu):
    lines = ["*Estado del Sistema*", ""]
    lines.append("*CPU*")
    cpu_temp = system.get("cpu_temp")
    if cpu_temp is not None:
        lines.append(f"  Temp: {cpu_temp:.1f} C")
    else:
        lines.append("  Temp: N/A")
    ram = system["ram"]
    lines.append(f"  RAM: {ram['percent']:.1f}%  ({_fmt_bytes(ram['used'])} / {_fmt_bytes(ram['total'])})")
    lines.append("")

    if gpu:
        lines.append("*GPU*")
        lines.append(f"  Modelo: {gpu['name']}")
        lines.append(f"  Temp: {gpu['temperature']} C")
        lines.append(f"  VRAM: {gpu['memory_percent']:.1f}%  ({_fmt_bytes(gpu['memory_used'])} / {_fmt_bytes(gpu['memory_total'])})")
        lines.append(f"  Uso:   {gpu['gpu_util']}%")
        lines.append("")
    else:
        lines.append("*GPU*")
        lines.append("  No detectada")
        lines.append("")

    lines.append(f"*Uptime:* {_fmt_uptime(system['uptime_seconds'])}")
    return "\n".join(lines)


def format_history(entries):
    if not entries:
        return "No hay registros en la base de datos."

    lines = ["*Ultimos registros*", ""]
    for e in entries:
        lines.append(f"`{e['timestamp']}`")
        parts = []
        if e["cpu_temp"] is not None:
            parts.append(f"CPU {e['cpu_temp']:.0f}C")
        if e["gpu_temp"] is not None:
            parts.append(f"GPU {e['gpu_temp']}C")
        if e["ram_percent"] is not None:
            parts.append(f"RAM {e['ram_percent']:.0f}%")
        if e["vram_percent"] is not None:
            parts.append(f"VRAM {e['vram_percent']:.0f}%")
        lines.append("  " + " | ".join(parts))
    return "\n".join(lines)


def format_alertas():
    lines = [
        "*Umbrales configurados*",
        "",
        f"CPU temp: {ALERT_CPU_TEMP:.0f} C",
        f"GPU temp: {ALERT_GPU_TEMP:.0f} C",
        f"RAM:      {ALERT_RAM_PCT:.0f}%",
        f"VRAM:     {ALERT_VRAM_PCT:.0f}%",
    ]
    return "\n".join(lines)
