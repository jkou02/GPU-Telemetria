from config import ALERT_CPU_TEMP, ALERT_GPU_TEMP, ALERT_RAM_PCT, ALERT_VRAM_PCT


def _fmt_bytes(b):
    if b is None:
        return "N/A"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} PB"


def _fmt_uptime(seconds):
    if seconds is None:
        return "N/A"
    parts = []
    days, seconds = divmod(int(seconds), 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, _ = divmod(seconds, 60)
    if days:
        parts.append(f"{days}d")
    parts.append(f"{hours}h")
    parts.append(f"{minutes}m")
    return " ".join(parts)


def format_status(system, gpu, hostname=None):
    lines = []
    if hostname:
        lines.append(f"*Estado del Sistema — {hostname}*")
    else:
        lines.append("*Estado del Sistema*")
    lines.append("")

    lines.append("*CPU*")
    cpu_temp = system.get("cpu_temp")
    if cpu_temp is not None:
        lines.append(f"  Temp: {cpu_temp:.1f} C")
    else:
        lines.append("  Temp: N/A")
    ram = system["ram"]
    lines.append(
        f"  RAM: {ram['percent']:.1f}%  ({_fmt_bytes(ram['used'])} / {_fmt_bytes(ram['total'])})"
    )
    lines.append("")

    if gpu:
        lines.append("*GPU*")
        lines.append(f"  Modelo: {gpu['name']}")
        lines.append(f"  Temp: {gpu['temperature']} C")
        lines.append(
            f"  VRAM: {gpu['memory_percent']:.1f}%  "
            f"({_fmt_bytes(gpu['memory_used'])} / {_fmt_bytes(gpu['memory_total'])})"
        )
        lines.append(f"  Uso:   {gpu['gpu_util']}%")
        lines.append("")
    else:
        lines.append("*GPU*")
        lines.append("  No detectada")
        lines.append("")

    lines.append(f"*Uptime:* {_fmt_uptime(system.get('uptime_seconds'))}")
    return "\n".join(lines)


def format_history(entries, hostname=None):
    if not entries:
        if hostname:
            return f"No hay registros para '{hostname}'."
        return "No hay registros en la base de datos."

    lines = ["*Ultimos registros*", ""]
    for e in entries:
        ts = e["timestamp"]
        # Formatear timestamp a string legible si es datetime
        if hasattr(ts, "strftime"):
            ts = ts.strftime("%Y-%m-%d %H:%M:%S")

        parts = []
        if e.get("hostname"):
            parts.append(e["hostname"])
        if e["cpu_temp"] is not None:
            parts.append(f"CPU {e['cpu_temp']:.0f}C")
        if e["gpu_temp"] is not None:
            parts.append(f"GPU {e['gpu_temp']}C")
        if e["ram_percent"] is not None:
            parts.append(f"RAM {e['ram_percent']:.0f}%")
        if e["vram_percent"] is not None:
            parts.append(f"VRAM {e['vram_percent']:.0f}%")

        lines.append(f"`{ts}`")
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


def format_gpu_info(gpu, hostname=None):
    lines = []
    if hostname:
        lines.append(f"*Información detallada de GPU — {hostname}*")
    else:
        lines.append("*Información detallada de GPU*")
    lines.append("")

    if not gpu:
        lines.append("No se detectó GPU activa.")
        return "\n".join(lines)

    lines.append(f"*Modelo:* {gpu['name']}")
    lines.append("")

    # Temperatura con indicador visual
    temp = gpu["temperature"]
    if temp >= 80:
        temp_icon = "🔴"
    elif temp >= 60:
        temp_icon = "🟡"
    else:
        temp_icon = "🟢"
    lines.append(f"*Temperatura:* {temp_icon} {temp:.1f} C")
    lines.append("")

    # VRAM
    vram_total = gpu["memory_total"]
    vram_used = gpu["memory_used"]
    vram_pct = gpu["memory_percent"]

    bar_len = 10
    filled = int(vram_pct / 100 * bar_len)
    bar = "█" * filled + "░" * (bar_len - filled)

    lines.append("*Memoria VRAM*")
    lines.append(f"  Uso: {bar} {vram_pct:.1f}%")
    lines.append(f"  {_fmt_bytes(vram_used)} / {_fmt_bytes(vram_total)}")
    lines.append("")

    # Utilización GPU con barra
    gpu_util = gpu["gpu_util"]
    filled_util = int(gpu_util / 100 * bar_len)
    bar_util = "█" * filled_util + "░" * (bar_len - filled_util)

    lines.append("*Utilización GPU*")
    lines.append(f"  Uso: {bar_util} {gpu_util:.1f}%")
    lines.append("")

    # Umbrales de alerta
    lines.append("*Umbrales de alerta*")
    lines.append(f"  GPU temp: {ALERT_GPU_TEMP:.0f} C")
    lines.append(f"  VRAM:     {ALERT_VRAM_PCT:.0f}%")

    return "\n".join(lines)


def format_pc_list(hostnames):
    if not hostnames:
        return "No hay PCs registradas."

    lines = ["*PCs registradas*", ""]
    for h in hostnames:
        lines.append(f"- `{h}`")
    lines.append("")
    lines.append("_Usa /status <pc>, /history <pc> o /gpu_info <pc>_")
    return "\n".join(lines)
