from datetime import datetime, timedelta, timezone
from typing import Dict

from .config_loader import BotConfig


class AuthManager:
    _sessions: Dict[int, datetime] = {}
    SESSION_TIMEOUT_MINUTES = BotConfig.SESSION_TIMEOUT_MINUTES

    @classmethod
    def is_authenticated(cls, admin_id: int) -> bool:
        if admin_id not in cls._sessions:
            return False

        session_time = cls._sessions[admin_id]
        if datetime.now(timezone.utc) - session_time > timedelta(minutes=cls.SESSION_TIMEOUT_MINUTES):
            del cls._sessions[admin_id]
            return False

        return True

    @classmethod
    def authenticate(cls, admin_id: int):
        cls._sessions[admin_id] = datetime.now(timezone.utc)

    @classmethod
    def logout(cls, admin_id: int):
        if admin_id in cls._sessions:
            del cls._sessions[admin_id]

    @classmethod
    def refresh_session(cls, admin_id: int):
        if admin_id in cls._sessions:
            cls._sessions[admin_id] = datetime.now(timezone.utc)
