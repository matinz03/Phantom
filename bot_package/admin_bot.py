from telegram.ext import Application
from .config_loader import BotConfig
from .handlers.admin_handlers import admin_handlers

async def setup_admin_bot():
    app = Application.builder().token(BotConfig.ADMIN_BOT_TOKEN).build()
    for handler in admin_handlers:
        app.add_handler(handler)
    return app