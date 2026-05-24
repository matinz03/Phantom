import asyncio
from bot_package.main_bot import setup_main_bot
from bot_package.admin_bot import setup_admin_bot
from bot_package.database import async_session, engine, Base
from bot_package.services.price_service import PriceService

async def main():
    # ساخت جداول
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # مقداردهی اولیه قیمت‌ها
    async with async_session() as session:
        await PriceService.init_default_prices(session)
    
    main_app = await setup_main_bot()
    admin_app = await setup_admin_bot()
    
    print("✅ بات‌ها آماده اجرا هستند...")
    
    async with main_app, admin_app:
        await asyncio.gather(
            main_app.run_polling(),
            admin_app.run_polling()
        )

if __name__ == "__main__":
    asyncio.run(main())