from telegram.ext import Application
from .config_loader import BotConfig
from .database import engine, Base
from .handlers.user_handlers import user_handlers

async def setup_main_bot():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    app = Application.builder().token(BotConfig.MAIN_BOT_TOKEN).build()
    for handler in user_handlers:
        app.add_handler(handler)
    
    return app