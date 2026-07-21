# src/services/config_service.py
# Business logic for guild configuration: tuner setup, roles, log channels, limits.
# Centralises all guild-level read/write operations behind a clean async API.

from __future__ import annotations

from typing import Optional

from src.database import repository as db
from src.database.models import GuildLogChannel, GuildRole, GuildLimit


# ================================================================================================ #
# Guild Config (Tuner Category / Channel)
# ================================================================================================ #

async def get_guild_config(guild_id: int) -> Optional[tuple[int, int]]:
    return await db.get_guild_config(guild_id)


async def save_guild_config(guild_id: int, category_id: int, channel_id: int) -> None:
    await db.save_guild_config(guild_id, category_id, channel_id)


async def delete_guild_config(guild_id: int) -> None:
    await db.delete_guild_config(guild_id)


# ================================================================================================ #
# Guild Roles
# ================================================================================================ #

async def get_guild_roles(guild_id: int) -> Optional[GuildRole]:
    return await db.get_guild_roles(guild_id)


async def get_role_id(guild_id: int, role_type: str) -> Optional[int]:
    """Convenience: returns a single role ID by type (e.g. 'quarantine')."""
    row = await db.get_guild_roles(guild_id)
    return getattr(row, f"{role_type}_id", None) if row else None


async def save_guild_roles(guild_id: int, **kwargs: int) -> None:
    await db.save_guild_roles(guild_id, **kwargs)


# ================================================================================================ #
# Guild Log Channels
# ================================================================================================ #

async def get_guild_log_channels(guild_id: int) -> Optional[GuildLogChannel]:
    return await db.get_guild_log_channels(guild_id)


async def get_log_channel(guild_id: int, log_type: str) -> Optional[int]:
    return await db.get_log_channel(guild_id, log_type)


async def save_guild_log_channels(guild_id: int, **kwargs: int) -> None:
    await db.save_guild_log_channels(guild_id, **kwargs)


# ================================================================================================ #
# Guild Limits
# ================================================================================================ #

async def get_guild_limits(guild_id: int) -> Optional[GuildLimit]:
    return await db.get_guild_limits(guild_id)


async def save_guild_limits(guild_id: int, **kwargs: int) -> None:
    await db.save_guild_limits(guild_id, **kwargs)
