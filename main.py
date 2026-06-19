from telegram.ext import ApplicationBuilder, CommandHandler

from config import TELEGRAM_BOT_TOKEN, CHECK_INTERVAL_MIN
from database.repository import init_db
from bot.handlers import (
    status_command,
    history_command,
    alertas_command,
    gpu_info_command,
    pcs_command,
)
from bot.alerts import check_and_alert


async def post_init(application):
    jq = application.job_queue
    interval = CHECK_INTERVAL_MIN * 60
    jq.run_repeating(check_and_alert, interval=interval, first=10)


def main():
    init_db()
    app = (
        ApplicationBuilder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .build()
    )
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("history", history_command))
    app.add_handler(CommandHandler("alertas", alertas_command))
    app.add_handler(CommandHandler("gpu_info", gpu_info_command))
    app.add_handler(CommandHandler("pcs", pcs_command))
    app.run_polling()


if __name__ == "__main__":
    main()
