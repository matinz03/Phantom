import os
from dotenv import load_dotenv

load_dotenv()

class BotConfig:
    MAIN_BOT_TOKEN = os.getenv("MAIN_BOT_TOKEN")
    ADMIN_BOT_TOKEN = os.getenv("ADMIN_BOT_TOKEN")
    ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", 0))
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
    DB_URL = os.getenv("DB_URL", "sqlite+aiosqlite:///vpn_shop.db")