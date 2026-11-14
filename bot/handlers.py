from telegram import Update
from telegram.ext import ContextTypes

from bot.formatter import (
    format_alertas,
    format_gpu_info,
    format_history,
    format_pc_list,
    format_status,
)
from config import HOSTNAME
from database.repository import get_hostnames, get_latest_entry, get_recent_entries, row_to_stats


def _resolve_hostname(args):
    """Devuelve el hostname a consultar a partir de los argumentos del comando."""
    if args:
        return args[0]
    return HOSTNAME


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    hostname = _resolve_hostname(context.args)
    entry = get_latest_entry(hostname)

    if not entry:
        await update.message.reply_text(f"No hay datos para '{hostname}'.")
        return

    system, gpu = row_to_stats(entry)
    msg = format_status(system, gpu, hostname)
    await update.message.reply_text(msg, parse_mode="Markdown")


async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    hostname = _resolve_hostname(context.args)
    entries = get_recent_entries(5, hostname=hostname)
    msg = format_history(entries, hostname)
    await update.message.reply_text(msg, parse_mode="Markdown")


async def alertas_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = format_alertas()
    await update.message.reply_text(msg, parse_mode="Markdown")


async def gpu_info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    hostname = _resolve_hostname(context.args)
    entry = get_latest_entry(hostname)

    if not entry:
        await update.message.reply_text(f"No hay datos para '{hostname}'.")
        return

    system, gpu = row_to_stats(entry)
    msg = format_gpu_info(gpu, hostname)
    await update.message.reply_text(msg, parse_mode="Markdown")


async def pcs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    hostnames = get_hostnames()
    msg = format_pc_list(hostnames)
    await update.message.reply_text(msg, parse_mode="Markdown")
