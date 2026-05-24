from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models import Price
from typing import Dict, Optional
from datetime import datetime, timezone

class PriceService:
    @staticmethod
    async def init_default_prices(session: AsyncSession):
        defaults = {1: 15000, 2: 28000, 3: 40000, 5: 65000, 10: 120000, 20: 220000}
        for vol, price in defaults.items():
            stmt = select(Price).where(Price.volume_gb == vol)
            result = await session.execute(stmt)
            if not result.scalar_one_or_none():
                session.add(Price(volume_gb=vol, price=price))
        await session.commit()
    
    @staticmethod
    async def get_all_prices(session: AsyncSession) -> Dict[int, int]:
        stmt = select(Price).order_by(Price.volume_gb)
        result = await session.execute(stmt)
        prices = result.scalars().all()
        return {p.volume_gb: p.price for p in prices}
    
    @staticmethod
    async def get_price(session: AsyncSession, volume_gb: int) -> Optional[int]:
        stmt = select(Price).where(Price.volume_gb == volume_gb)
        result = await session.execute(stmt)
        price_obj = result.scalar_one_or_none()
        return price_obj.price if price_obj else None
    
    @staticmethod
    async def update_price(session: AsyncSession, volume_gb: int, new_price: int) -> bool:
        stmt = select(Price).where(Price.volume_gb == volume_gb)
        result = await session.execute(stmt)
        price_obj = result.scalar_one_or_none()
        if price_obj:
            price_obj.price = new_price
            price_obj.updated_at = datetime.now(timezone.utc)
            await session.commit()
            return True
        return False