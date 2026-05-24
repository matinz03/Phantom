import os

from dotenv import load_dotenv

load_dotenv()


def _parse_admin_user_id() -> int:
    raw_value = os.getenv("ADMIN_USER_ID", "").strip()
    if not raw_value:
        return 0
    try:
        return int(raw_value)
    except ValueError:
        return 0


class BotConfig:
    MAIN_BOT_TOKEN = os.getenv("MAIN_BOT_TOKEN", "").strip()
    ADMIN_BOT_TOKEN = os.getenv("ADMIN_BOT_TOKEN", "").strip()
    ADMIN_USER_ID = _parse_admin_user_id()
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "").strip()
    DB_URL = os.getenv("DB_URL", "sqlite+aiosqlite:///vpn_shop.db").strip()

    @classmethod
    def validate(cls) -> None:
        errors = []
        if not cls.MAIN_BOT_TOKEN:
            errors.append("MAIN_BOT_TOKEN is required")
        if not cls.ADMIN_BOT_TOKEN:
            errors.append("ADMIN_BOT_TOKEN is required")
        if cls.ADMIN_USER_ID <= 0:
            errors.append("ADMIN_USER_ID must be a positive numeric Telegram user ID")
        if not cls.ADMIN_PASSWORD:
            errors.append("ADMIN_PASSWORD is required")
        if cls.ADMIN_PASSWORD == "admin123":
            errors.append("ADMIN_PASSWORD must not use the unsafe default 'admin123'")
        if not cls.DB_URL:
            errors.append("DB_URL is required")
        if errors:
            raise RuntimeError("Invalid bot configuration: " + "; ".join(errors))
