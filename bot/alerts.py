from telegram.ext import ContextTypes

from collector.system import get_system_stats
from collector.gpu import get_gpu_stats
from database.repository import insert_telemetry
from config import TELEGRAM_CHAT_ID, ALERT_CPU_TEMP, ALERT_GPU_TEMP, ALERT_RAM_PCT, ALERT_VRAM_PCT


async def check_and_alert(context: ContextTypes.DEFAULT_TYPE):
    system = get_system_stats()
    gpu = get_gpu_stats()

    insert_telemetry(system, gpu)

    triggered = []

    cpu_temp = system.get("cpu_temp")
    if cpu_temp is not None and cpu_temp > ALERT_CPU_TEMP:
        triggered.append(f"CPU temp: {cpu_temp:.1f} C (limite {ALERT_CPU_TEMP:.0f} C)")

    if gpu:
        if gpu["temperature"] > ALERT_GPU_TEMP:
            triggered.append(f"GPU temp: {gpu['temperature']} C (limite {ALERT_GPU_TEMP:.0f} C)")
        if gpu["memory_percent"] > ALERT_VRAM_PCT:
            triggered.append(f"VRAM: {gpu['memory_percent']:.1f}% (limite {ALERT_VRAM_PCT:.0f}%)")

    if system["ram"]["percent"] > ALERT_RAM_PCT:
        triggered.append(f"RAM: {system['ram']['percent']:.1f}% (limite {ALERT_RAM_PCT:.0f}%)")

    if triggered:
        msg = "*ALERTA*\n\n" + "\n".join(f"- {t}" for t in triggered)
        await context.bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=msg,
            parse_mode="Markdown",
        )
