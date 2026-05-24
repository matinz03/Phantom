from datetime import datetime, timedelta, timezone
from typing import Dict

class AuthManager:
    """مدیریت نشست‌های احراز هویت ادمین"""
    
    _sessions: Dict[int, datetime] = {}
    SESSION_TIMEOUT_MINUTES = 30  # بعد از ۳۰ دقیقه دوباره رمز بخواد
    
    @classmethod
    def is_authenticated(cls, admin_id: int) -> bool:
        """چک می‌کنه ادمین احراز هویت شده یا نه"""
        if admin_id not in cls._sessions:
            return False
        
        session_time = cls._sessions[admin_id]
        if datetime.now(timezone.utc) - session_time > timedelta(minutes=cls.SESSION_TIMEOUT_MINUTES):
            del cls._sessions[admin_id]
            return False
        
        return True
    
    @classmethod
    def authenticate(cls, admin_id: int):
        """ادمین رو احراز هویت می‌کنه"""
        cls._sessions[admin_id] = datetime.now(timezone.utc)
    
    @classmethod
    def logout(cls, admin_id: int):
        """خروج ادمین"""
        if admin_id in cls._sessions:
            del cls._sessions[admin_id]
    
    @classmethod
    def refresh_session(cls, admin_id: int):
        """تمدید نشست"""
        if admin_id in cls._sessions:
            cls._sessions[admin_id] = datetime.now(timezone.utc)