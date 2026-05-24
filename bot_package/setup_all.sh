#!/bin/bash

echo "🚀 شروع ساخت پروژه..."

# ساخت پوشه‌ها
mkdir -p bot_package/handlers bot_package/services bot_package/utils

# فایل‌های __init__.py
echo "" > bot_package/__init__.py
echo "" > bot_package/handlers/__init__.py
echo "" > bot_package/services/__init__.py
echo "" > bot_package/utils/__init__.py

# ============ .env ============
cat > .env << 'EOFENV'
MAIN_BOT_TOKEN=توکن_ربات_فروش_رو_بذار_اینجا
ADMIN_BOT_TOKEN=توکن_ربات_ادمین_رو_بذار_اینجا
ADMIN_USER_ID=آیدی_عددی_خودت_از_userinfobot
ADMIN_PASSWORD=رمز_دلخواه_برای_پنل
DB_URL=sqlite+aiosqlite:///vpn_shop.db
EOFENV

# ============ config_loader.py ============
cat > bot_package/config_loader.py << 'EOFPY'
import os
from dotenv import load_dotenv

load_dotenv()

class BotConfig:
    MAIN_BOT_TOKEN = os.getenv("MAIN_BOT_TOKEN")
    ADMIN_BOT_TOKEN = os.getenv("ADMIN_BOT_TOKEN")
    ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", 0))
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
    DB_URL = os.getenv("DB_URL", "sqlite+aiosqlite:///vpn_shop.db")
EOFPY

# ============ database.py ============
cat > bot_package/database.py << 'EOFPY'
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from .config_loader import BotConfig

engine = create_async_engine(BotConfig.DB_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with async_session() as session:
        yield session
EOFPY

# ============ models.py ============
cat > bot_package/models.py << 'EOFPY'
from sqlalchemy import Column, Integer, BigInteger, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import DeclarativeBase, relationship
from datetime import datetime, timezone

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=False)
    wallet_balance = Column(Integer, default=0)
    is_blocked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    purchases = relationship("Purchase", back_populates="user")

class Config(Base):
    __tablename__ = "configs"
    id = Column(Integer, primary_key=True)
    volume_gb = Column(Integer, nullable=False)
    sub_link = Column(String, nullable=False, unique=True)
    is_sold = Column(Boolean, default=False)
    sold_to_user_id = Column(BigInteger, nullable=True)
    sold_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Purchase(Base):
    __tablename__ = "purchases"
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    config_id = Column(Integer, ForeignKey("configs.id"), nullable=False)
    volume_gb = Column(Integer, nullable=False)
    price = Column(Integer, nullable=False)
    purchased_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    user = relationship("User", back_populates="purchases")

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    amount = Column(Integer, nullable=False)
    type = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Price(Base):
    __tablename__ = "prices"
    id = Column(Integer, primary_key=True)
    volume_gb = Column(Integer, unique=True, nullable=False)
    price = Column(Integer, nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
EOFPY

# ============ auth.py ============
cat > bot_package/auth.py << 'EOFPY'
from datetime import datetime, timedelta, timezone
from typing import Dict

class AuthManager:
    _sessions: Dict[int, datetime] = {}
    SESSION_TIMEOUT_MINUTES = 30
    
    @classmethod
    def is_authenticated(cls, admin_id: int) -> bool:
        if admin_id not in cls._sessions:
            return False
        if datetime.now(timezone.utc) - cls._sessions[admin_id] > timedelta(minutes=cls.SESSION_TIMEOUT_MINUTES):
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
EOFPY

echo "✅ فایل‌های پایه ساخته شدند!"
echo "📝 حالا ادامه اسکریپت رو اجرا کن..."
