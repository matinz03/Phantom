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


def _parse_int_env(name: str, default: int) -> int:
    raw_value = os.getenv(name, str(default)).strip()
    try:
        return int(raw_value)
    except ValueError:
        return default


class BotConfig:
    MAIN_BOT_TOKEN = os.getenv("MAIN_BOT_TOKEN", "").strip()
    ADMIN_BOT_TOKEN = os.getenv("ADMIN_BOT_TOKEN", "").strip()
    ADMIN_USER_ID = _parse_admin_user_id()
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "").strip()
    DB_URL = os.getenv("DB_URL", "sqlite+aiosqlite:///vpn_shop.db").strip()
    SUPPORT_URL = os.getenv("SUPPORT_URL", "https://t.me/YourSupport").strip()
    SUPPORT_HANDLE = os.getenv("SUPPORT_HANDLE", "@YourSupport").strip()
    CHANNEL_HANDLE = os.getenv("CHANNEL_HANDLE", "@YourChannel").strip()
    SESSION_TIMEOUT_MINUTES = _parse_int_env("SESSION_TIMEOUT_MINUTES", 30)
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").strip().upper()

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
        if not cls.SUPPORT_URL.startswith(("https://t.me/", "http://", "https://")):
            errors.append("SUPPORT_URL must be a valid URL")
        if cls.SESSION_TIMEOUT_MINUTES <= 0:
            errors.append("SESSION_TIMEOUT_MINUTES must be positive")
        if cls.LOG_LEVEL not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            errors.append("LOG_LEVEL must be DEBUG, INFO, WARNING, ERROR, or CRITICAL")
        if errors:
            raise RuntimeError("Invalid bot configuration: " + "; ".join(errors))
