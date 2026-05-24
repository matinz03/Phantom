import importlib

import pytest
import pytest_asyncio


@pytest_asyncio.fixture()
async def db(tmp_path, monkeypatch):
    monkeypatch.setenv("MAIN_BOT_TOKEN", "123:abc")
    monkeypatch.setenv("ADMIN_BOT_TOKEN", "456:def")
    monkeypatch.setenv("OWNER_USER_IDS", "1001")
    monkeypatch.setenv("ADMIN_USER_IDS", "2002")
    monkeypatch.setenv("ADMIN_PASSWORD", "strong-password")
    monkeypatch.setenv("DB_URL", f"sqlite+aiosqlite:///{tmp_path / 'test.db'}")

    import bot_package.config_loader as config_loader
    import bot_package.database as database
    import bot_package.services.admin_service as admin_service
    from bot_package.models import Base

    importlib.reload(config_loader)
    database = importlib.reload(database)
    admin_service = importlib.reload(admin_service)

    async with database.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    try:
        yield database, admin_service
    finally:
        await database.engine.dispose()


@pytest.mark.asyncio
async def test_sync_configured_admins_seeds_owner_and_admin(db):
    database, admin_service = db

    async with database.async_session() as session:
        await admin_service.AdminService.sync_configured_admins(session)
        owner = await admin_service.AdminService.get_admin(session, 1001)
        admin = await admin_service.AdminService.get_admin(session, 2002)

    assert owner.is_owner is True
    assert admin.is_owner is False
    assert await _can_access(database, admin_service, 2002, "inventory") is True


@pytest.mark.asyncio
async def test_add_admin_with_scoped_permissions(db):
    database, admin_service = db

    async with database.async_session() as session:
        await admin_service.AdminService.add_or_update_admin(
            session,
            telegram_id=3003,
            permissions="inventory reports invalid",
            created_by=1001,
        )
        await session.commit()

    assert await _can_access(database, admin_service, 3003, "inventory") is True
    assert await _can_access(database, admin_service, 3003, "reports") is True
    assert await _can_access(database, admin_service, 3003, "prices") is False


@pytest.mark.asyncio
async def test_remove_admin_deactivates_non_owner_but_not_owner(db):
    database, admin_service = db

    async with database.async_session() as session:
        await admin_service.AdminService.sync_configured_admins(session)
        removed_admin = await admin_service.AdminService.remove_admin(session, 2002)
        removed_owner = await admin_service.AdminService.remove_admin(session, 1001)
        await session.commit()

    assert removed_admin is True
    assert removed_owner is False
    assert await _can_access(database, admin_service, 2002, "inventory") is False
    assert await _can_access(database, admin_service, 1001, "prices") is True


async def _can_access(database, admin_service, telegram_id: int, permission: str) -> bool:
    async with database.async_session() as session:
        return await admin_service.AdminService.can_access(session, telegram_id, permission)
