# tests/test_config_service.py
# Unit tests for src/services/config_service.py

import pytest
from src.services import config_service

GUILD_ID  = 666666666666666666
CAT_ID    = 777777777777777777
CH_ID     = 888888888888888888


# ─── Guild Config ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_save_and_get_guild_config():
    await config_service.save_guild_config(GUILD_ID, CAT_ID, CH_ID)
    result = await config_service.get_guild_config(GUILD_ID)
    assert result is not None
    cat, ch = result
    assert cat == CAT_ID
    assert ch == CH_ID


@pytest.mark.asyncio
async def test_delete_guild_config():
    await config_service.save_guild_config(GUILD_ID, CAT_ID, CH_ID)
    await config_service.delete_guild_config(GUILD_ID)
    result = await config_service.get_guild_config(GUILD_ID)
    assert result is None


# ─── Guild Roles ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_save_and_get_role_id():
    await config_service.save_guild_roles(GUILD_ID, quarantine_id=123456789012345678)
    role_id = await config_service.get_role_id(GUILD_ID, "quarantine")
    assert role_id == 123456789012345678


@pytest.mark.asyncio
async def test_get_role_id_unknown_guild():
    role_id = await config_service.get_role_id(999999999999999999, "quarantine")
    assert role_id is None


# ─── Guild Log Channels ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_save_and_get_log_channel():
    await config_service.save_guild_log_channels(GUILD_ID, channel_create_id=CH_ID)
    ch = await config_service.get_log_channel(GUILD_ID, "channel_create")
    assert ch == CH_ID


@pytest.mark.asyncio
async def test_get_log_channel_unknown_guild():
    ch = await config_service.get_log_channel(999999999999999999, "bans")
    assert ch is None
