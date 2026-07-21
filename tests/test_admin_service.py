# tests/test_admin_service.py
# Unit tests for src/services/admin_service.py
# Uses in-memory SQLite (see conftest.py) — no Discord bot required.

import pytest
import pytest_asyncio
from src.services import admin_service

GUILD_ID = 111111111111111111
OWNER_ID = 222222222222222222
ADMIN_ID = 333333333333333333
USER_ID  = 444444444444444444
ROLE_ID  = 555555555555555555


# ─── Admin Management ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_add_and_get_admin():
    await admin_service.add_admin(ADMIN_ID)
    admins = await admin_service.get_all_admins()
    assert ADMIN_ID in admins


@pytest.mark.asyncio
async def test_remove_admin():
    await admin_service.add_admin(ADMIN_ID)
    await admin_service.remove_admin(ADMIN_ID)
    admins = await admin_service.get_all_admins()
    assert ADMIN_ID not in admins


# ─── Server Owner Management ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_add_and_check_server_owner():
    await admin_service.add_server_owner(GUILD_ID, OWNER_ID)
    assert await admin_service.is_server_owner(GUILD_ID, OWNER_ID) is True


@pytest.mark.asyncio
async def test_remove_server_owner():
    await admin_service.add_server_owner(GUILD_ID, OWNER_ID)
    await admin_service.remove_server_owner(GUILD_ID, OWNER_ID)
    assert await admin_service.is_server_owner(GUILD_ID, OWNER_ID) is False


@pytest.mark.asyncio
async def test_unknown_user_is_not_owner():
    assert await admin_service.is_server_owner(GUILD_ID, 999999999999999999) is False


# ─── Tracked Users ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_add_and_get_tracked_user():
    await admin_service.add_tracked_user(USER_ID)
    users = await admin_service.get_all_tracked_users()
    assert USER_ID in users


@pytest.mark.asyncio
async def test_remove_tracked_user():
    await admin_service.add_tracked_user(USER_ID)
    await admin_service.remove_tracked_user(USER_ID)
    users = await admin_service.get_all_tracked_users()
    assert USER_ID not in users


# ─── Custom Role Limits ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_save_and_get_custom_role_limits():
    await admin_service.save_custom_role_limits(
        ROLE_ID, GUILD_ID,
        channels_limit=5, channels_time=10,
        roles_limit=3,    roles_time=60,
        links_limit=10,   links_time=5,
        webhooks_limit=2, webhooks_time=60,
    )
    limits = await admin_service.get_custom_role_limits(ROLE_ID)
    assert limits is not None
    assert limits["channels_limit"] == 5
    assert limits["roles_limit"] == 3


@pytest.mark.asyncio
async def test_delete_custom_role_limits():
    await admin_service.save_custom_role_limits(
        ROLE_ID, GUILD_ID,
        channels_limit=1, channels_time=1,
        roles_limit=1,    roles_time=1,
        links_limit=1,    links_time=1,
        webhooks_limit=1, webhooks_time=1,
    )
    deleted = await admin_service.delete_custom_role_limits(ROLE_ID)
    assert deleted > 0
    assert await admin_service.get_custom_role_limits(ROLE_ID) is None


@pytest.mark.asyncio
async def test_get_all_custom_roles():
    await admin_service.save_custom_role_limits(
        ROLE_ID, GUILD_ID,
        channels_limit=5, channels_time=10,
        roles_limit=3,    roles_time=60,
        links_limit=10,   links_time=5,
        webhooks_limit=2, webhooks_time=60,
    )
    roles = await admin_service.get_all_custom_roles(GUILD_ID)
    assert ROLE_ID in roles


# ─── Custom User Limits ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_save_and_get_custom_user_limits():
    await admin_service.save_custom_user_limits(
        USER_ID, GUILD_ID,
        channels_limit=5, channels_time=10,
        roles_limit=3,    roles_time=60,
        links_limit=10,   links_time=5,
        webhooks_limit=2, webhooks_time=60,
    )
    limits = await admin_service.get_custom_user_limits(USER_ID)
    assert limits is not None
    assert limits["webhooks_limit"] == 2


@pytest.mark.asyncio
async def test_delete_custom_user_limits():
    await admin_service.save_custom_user_limits(
        USER_ID, GUILD_ID,
        channels_limit=1, channels_time=1,
        roles_limit=1,    roles_time=1,
        links_limit=1,    links_time=1,
        webhooks_limit=1, webhooks_time=1,
    )
    deleted = await admin_service.delete_custom_user_limits(USER_ID)
    assert deleted > 0
    assert await admin_service.get_custom_user_limits(USER_ID) is None
