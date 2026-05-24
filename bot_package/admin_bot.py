import logging

from telegram.ext import Application
from .config_loader import BotConfig
from .handlers.admin_handlers import admin_handlers

logger = logging.getLogger(__name__)


async def log_error(update, context):
    error = context.error
    logger.error("Admin bot update failed", exc_info=(type(error), error, error.__traceback__))


async def setup_admin_bot():
    app = Application.builder().token(BotConfig.ADMIN_BOT_TOKEN).build()
    for handler in admin_handlers:
        app.add_handler(handler)
    app.add_error_handler(log_error)
    return app
