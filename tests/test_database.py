import pytest
import pytest_asyncio
from contextlib import asynccontextmanager
from unittest.mock import patch
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from src.database.models import Base
from src.database import repository

# 1. Module-level fixture for SQLite in-memory engine
test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

@pytest_asyncio.fixture(autouse=True)
async def setup_test_db():
    # Setup tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    yield
    
    # Teardown tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(autouse=True)
def override_get_session():
    @asynccontextmanager
    async def get_test_session():
        async with TestSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    with patch("src.database.repository.get_session", get_test_session):
        yield

class TestDatabaseAdmins:
    @pytest.mark.asyncio
    async def test_add_admin(self):
        await repository.add_admin(12345)
        admins = await repository.get_all_admins()
        assert 12345 in admins
        assert len(admins) == 1

    @pytest.mark.asyncio
    async def test_add_admin_duplicate_ignored(self):
        await repository.add_admin(12345)
        await repository.add_admin(12345)
        admins = await repository.get_all_admins()
        assert len(admins) == 1
        assert admins[0] == 12345

    @pytest.mark.asyncio
    async def test_remove_admin(self):
        await repository.add_admin(12345)
        await repository.remove_admin(12345)
        admins = await repository.get_all_admins()
        assert 12345 not in admins
        assert len(admins) == 0

    @pytest.mark.asyncio
    async def test_get_all_admins_empty(self):
        admins = await repository.get_all_admins()
        assert admins == []

class TestDatabaseTrackedUsers:
    @pytest.mark.asyncio
    async def test_add_tracked_user(self):
        await repository.add_tracked_user(54321)
        users = await repository.get_all_tracked_users()
        assert 54321 in users
        assert len(users) == 1

    @pytest.mark.asyncio
    async def test_add_tracked_user_duplicate_ignored(self):
        await repository.add_tracked_user(54321)
        await repository.add_tracked_user(54321)
        users = await repository.get_all_tracked_users()
        assert len(users) == 1
        assert users[0] == 54321

    @pytest.mark.asyncio
    async def test_remove_tracked_user(self):
        await repository.add_tracked_user(54321)
        await repository.remove_tracked_user(54321)
        users = await repository.get_all_tracked_users()
        assert 54321 not in users
        assert len(users) == 0

    @pytest.mark.asyncio
    async def test_get_all_tracked_users_empty(self):
        users = await repository.get_all_tracked_users()
        assert users == []

class TestDatabaseGuildConfigs:
    @pytest.mark.asyncio
    async def test_save_and_get_guild_config(self):
        await repository.save_guild_config(111, 222, 333)
        config = await repository.get_guild_config(111)
        assert config is not None
        assert config[0] == 222
        assert config[1] == 333

    @pytest.mark.asyncio
    async def test_update_guild_config(self):
        await repository.save_guild_config(111, 222, 333)
        await repository.save_guild_config(111, 444, 555)
        config = await repository.get_guild_config(111)
        assert config is not None
        assert config[0] == 444
        assert config[1] == 555

    @pytest.mark.asyncio
    async def test_delete_guild_config(self):
        await repository.save_guild_config(111, 222, 333)
        await repository.delete_guild_config(111)
        config = await repository.get_guild_config(111)
        assert config is None

class TestDatabaseRoles:
    @pytest.mark.asyncio
    async def test_save_and_get_guild_roles(self):
        await repository.save_guild_roles(111, quarantine_id=10, quarantine_alt_id=20)
        roles = await repository.get_guild_roles(111)
        assert roles is not None
        assert roles.quarantine_id == 10
        assert roles.quarantine_alt_id == 20
        assert roles.ai_id is None

    @pytest.mark.asyncio
    async def test_update_guild_roles(self):
        await repository.save_guild_roles(111, quarantine_id=10)
        await repository.save_guild_roles(111, quarantine_id=50, ai_id=60)
        roles = await repository.get_guild_roles(111)
        assert roles is not None
        assert roles.quarantine_id == 50
        assert roles.ai_id == 60

class TestDatabaseLimits:
    @pytest.mark.asyncio
    async def test_save_and_get_guild_limits(self):
        await repository.save_guild_limits(111, channel_create_count=5, channel_create_time=60)
        limits = await repository.get_guild_limits(111)
        assert limits is not None
        assert limits.channel_create_count == 5
        assert limits.channel_create_time == 60
        assert limits.channel_delete_count is None

    @pytest.mark.asyncio
    async def test_update_guild_limits(self):
        await repository.save_guild_limits(111, channel_create_count=5)
        await repository.save_guild_limits(111, channel_create_count=10, channel_delete_count=2)
        limits = await repository.get_guild_limits(111)
        assert limits is not None
        assert limits.channel_create_count == 10
        assert limits.channel_delete_count == 2
