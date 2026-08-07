"""Bot worker entry point — SPEC §2.1. Long-polling, not webhooks (no public
endpoint needed for self-hosting). Runs as its own process alongside the
FastAPI api process (see docker-compose.yml)."""
import logging

from telegram.ext import Application, CallbackQueryHandler, CommandHandler, MessageHandler, filters

from app.bot.handlers import handle_callback, handle_message, help_command, start
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def build_application() -> Application:
    app = Application.builder().token(settings.telegram_bot_token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))
    return app


def main() -> None:
    if not settings.telegram_bot_token:
        raise SystemExit("TELEGRAM_BOT_TOKEN not set — refusing to start the bot worker.")
    if not settings.telegram_allowed_user_id:
        raise SystemExit("TELEGRAM_ALLOWED_USER_ID not set — refusing to start the bot worker.")

    logger.info("Compass bot worker starting (long-polling)...")
    app = build_application()
    app.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
