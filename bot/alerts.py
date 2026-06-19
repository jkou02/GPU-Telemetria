from telegram.ext import ContextTypes

from database.repository import get_hostnames, get_latest_entry
from config import TELEGRAM_CHAT_ID, ALERT_CPU_TEMP, ALERT_GPU_TEMP, ALERT_RAM_PCT, ALERT_VRAM_PCT


async def check_and_alert(context: ContextTypes.DEFAULT_TYPE):
    hostnames = get_hostnames()
    if not hostnames:
        return

    for hostname in hostnames:
        entry = get_latest_entry(hostname)
        if not entry:
            continue

        triggered = []

        cpu_temp = entry.get("cpu_temp")
        if cpu_temp is not None and cpu_temp > ALERT_CPU_TEMP:
            triggered.append(
                f"CPU temp: {cpu_temp:.1f} C (limite {ALERT_CPU_TEMP:.0f} C)"
            )

        gpu_temp = entry.get("gpu_temp")
        if gpu_temp is not None and gpu_temp > ALERT_GPU_TEMP:
            triggered.append(
                f"GPU temp: {gpu_temp} C (limite {ALERT_GPU_TEMP:.0f} C)"
            )

        vram_pct = entry.get("vram_percent")
        if vram_pct is not None and vram_pct > ALERT_VRAM_PCT:
            triggered.append(
                f"VRAM: {vram_pct:.1f}% (limite {ALERT_VRAM_PCT:.0f}%)"
            )

        ram_pct = entry.get("ram_percent")
        if ram_pct is not None and ram_pct > ALERT_RAM_PCT:
            triggered.append(
                f"RAM: {ram_pct:.1f}% (limite {ALERT_RAM_PCT:.0f}%)"
            )

        if triggered:
            msg = f"*ALERTA — {hostname}*\n\n" + "\n".join(f"- {t}" for t in triggered)
            await context.bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=msg,
                parse_mode="Markdown",
            )
