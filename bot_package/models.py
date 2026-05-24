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