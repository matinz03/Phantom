import logging

from telegram.ext import Application
from .config_loader import BotConfig
from .database import engine
from .models import Base
from .handlers.user_handlers import user_handlers

logger = logging.getLogger(__name__)


async def log_error(update, context):
    error = context.error
    logger.error("Main bot update failed", exc_info=(type(error), error, error.__traceback__))


async def setup_main_bot():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    app = Application.builder().token(BotConfig.MAIN_BOT_TOKEN).build()
    for handler in user_handlers:
        app.add_handler(handler)
    app.add_error_handler(log_error)
    
    return app
