from telegram import Update
from telegram.ext import ContextTypes

from collector.system import get_system_stats
from collector.gpu import get_gpu_stats
from database.repository import get_recent_entries
from bot.formatter import format_status, format_history, format_alertas


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    system = get_system_stats()
    gpu = get_gpu_stats()
    msg = format_status(system, gpu)
    await update.message.reply_text(msg, parse_mode="Markdown")


async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    entries = get_recent_entries(5)
    msg = format_history(entries)
    await update.message.reply_text(msg, parse_mode="Markdown")


async def alertas_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = format_alertas()
    await update.message.reply_text(msg, parse_mode="Markdown")
