# src/database/repository.py
# All async database operations.
# This is the ONLY place in the codebase that may import and use SQLAlchemy sessions.
# Cogs, Services, and Events must call these functions — never touch the session directly.

from __future__ import annotations

from typing import Optional

from sqlalchemy import delete, select, update
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from .engine import get_session
from .models import (
    Admin,
    CustomRoleLimit,
    CustomUserLimit,
    GuildConfig,
    GuildLimit,
    GuildLogChannel,
    GuildRole,
    ServerOwner,
    TrackedUser,
)

# ================================================================================================ #
# Admin Operations
# ================================================================================================ #

async def get_all_admins() -> list[int]:
    """Returns all admin user IDs."""
    async with get_session() as session:
        result = await session.execute(select(Admin.user_id))
        return [row[0] for row in result.all()]


async def add_admin(user_id: int) -> None:
    """Adds a user as an admin (ignores duplicates)."""
    async with get_session() as session:
        stmt = sqlite_insert(Admin).values(user_id=user_id).on_conflict_do_nothing()
        await session.execute(stmt)


async def remove_admin(user_id: int) -> None:
    """Removes a user from the admin list."""
    async with get_session() as session:
        await session.execute(delete(Admin).where(Admin.user_id == user_id))


# ================================================================================================ #
# Tracked User Operations
# ================================================================================================ #

async def get_all_tracked_users() -> list[int]:
    """Returns all tracked user IDs."""
    async with get_session() as session:
        result = await session.execute(select(TrackedUser.user_id))
        return [row[0] for row in result.all()]


async def add_tracked_user(user_id: int) -> None:
    """Adds a user to the tracked list (ignores duplicates)."""
    async with get_session() as session:
        stmt = sqlite_insert(TrackedUser).values(user_id=user_id).on_conflict_do_nothing()
        await session.execute(stmt)


async def remove_tracked_user(user_id: int) -> None:
    """Removes a user from the tracked list."""
    async with get_session() as session:
        await session.execute(delete(TrackedUser).where(TrackedUser.user_id == user_id))


# ================================================================================================ #
# Guild Config Operations
# ================================================================================================ #

async def get_guild_config(guild_id: int) -> Optional[tuple[int, int]]:
    """Returns (tuner_category_id, tuner_channel_id) or None if not configured."""
    async with get_session() as session:
        result = await session.execute(
            select(GuildConfig.tuner_category_id, GuildConfig.tuner_channel_id)
            .where(GuildConfig.guild_id == guild_id)
        )
        return result.one_or_none()


async def save_guild_config(guild_id: int, category_id: int, channel_id: int) -> None:
    """Saves or updates the tuner channel and category for a guild."""
    async with get_session() as session:
        stmt = (
            sqlite_insert(GuildConfig)
            .values(guild_id=guild_id, tuner_category_id=category_id, tuner_channel_id=channel_id)
            .on_conflict_do_update(
                index_elements=["guild_id"],
                set_={"tuner_category_id": category_id, "tuner_channel_id": channel_id},
            )
        )
        await session.execute(stmt)


async def delete_guild_config(guild_id: int) -> None:
    """Removes the tuner configuration for a guild."""
    async with get_session() as session:
        await session.execute(delete(GuildConfig).where(GuildConfig.guild_id == guild_id))


# ================================================================================================ #
# Guild Roles Operations
# ================================================================================================ #

async def get_guild_roles(guild_id: int) -> Optional[GuildRole]:
    """Returns the GuildRole row for a guild, or None."""
    async with get_session() as session:
        result = await session.execute(select(GuildRole).where(GuildRole.guild_id == guild_id))
        return result.scalar_one_or_none()


async def save_guild_roles(guild_id: int, **kwargs: int) -> None:
    """Upserts role IDs for a guild. kwargs should match GuildRole column names."""
    async with get_session() as session:
        stmt = (
            sqlite_insert(GuildRole)
            .values(guild_id=guild_id, **kwargs)
            .on_conflict_do_update(index_elements=["guild_id"], set_=kwargs)
        )
        await session.execute(stmt)


# ================================================================================================ #
# Guild Log Channels Operations
# ================================================================================================ #

async def get_guild_log_channels(guild_id: int) -> Optional[GuildLogChannel]:
    """Returns the GuildLogChannel row for a guild, or None."""
    async with get_session() as session:
        result = await session.execute(
            select(GuildLogChannel).where(GuildLogChannel.guild_id == guild_id)
        )
        return result.scalar_one_or_none()


async def get_log_channel(guild_id: int, log_type: str) -> Optional[int]:
    """Returns a specific log channel ID by column name (e.g. 'channel_create')."""
    row = await get_guild_log_channels(guild_id)
    return getattr(row, f"{log_type}_id", None) if row else None


async def save_guild_log_channels(guild_id: int, **kwargs: int) -> None:
    """Upserts log channel IDs for a guild. kwargs should match column names."""
    async with get_session() as session:
        stmt = (
            sqlite_insert(GuildLogChannel)
            .values(guild_id=guild_id, **kwargs)
            .on_conflict_do_update(index_elements=["guild_id"], set_=kwargs)
        )
        await session.execute(stmt)


# ================================================================================================ #
# Guild Limits Operations
# ================================================================================================ #

async def get_guild_limits(guild_id: int) -> Optional[GuildLimit]:
    """Returns the GuildLimit row for a guild, or None."""
    async with get_session() as session:
        result = await session.execute(
            select(GuildLimit).where(GuildLimit.guild_id == guild_id)
        )
        return result.scalar_one_or_none()


async def save_guild_limits(guild_id: int, **kwargs: int) -> None:
    """Upserts limit values for a guild."""
    async with get_session() as session:
        stmt = (
            sqlite_insert(GuildLimit)
            .values(guild_id=guild_id, **kwargs)
            .on_conflict_do_update(index_elements=["guild_id"], set_=kwargs)
        )
        await session.execute(stmt)


# ================================================================================================ #
# Custom Role Limits Operations
# ================================================================================================ #

async def save_custom_role_limits(role_id: int, guild_id: int, **kwargs: int) -> None:
    """Saves or replaces custom limits for an admin role."""
    cols = [
        "channels_limit", "channels_time", "roles_limit", "roles_time",
        "links_limit", "links_time", "webhooks_limit", "webhooks_time",
    ]
    values = {col: kwargs.get(col, 0) for col in cols}
    async with get_session() as session:
        stmt = (
            sqlite_insert(CustomRoleLimit)
            .values(role_id=role_id, guild_id=guild_id, **values)
            .on_conflict_do_update(index_elements=["role_id"], set_=values)
        )
        await session.execute(stmt)


async def get_custom_role_limits(role_id: int) -> Optional[dict]:
    """Returns a dict of limit values for a role, or None."""
    async with get_session() as session:
        result = await session.execute(
            select(CustomRoleLimit).where(CustomRoleLimit.role_id == role_id)
        )
        row = result.scalar_one_or_none()

    if not row:
        return None
    return {
        "channels_limit": row.channels_limit, "channels_time": row.channels_time,
        "roles_limit": row.roles_limit,       "roles_time": row.roles_time,
        "links_limit": row.links_limit,       "links_time": row.links_time,
        "webhooks_limit": row.webhooks_limit, "webhooks_time": row.webhooks_time,
    }


async def get_all_custom_roles(guild_id: int) -> list[int]:
    """Returns all custom admin role IDs for a guild."""
    async with get_session() as session:
        result = await session.execute(
            select(CustomRoleLimit.role_id).where(CustomRoleLimit.guild_id == guild_id)
        )
        return [row[0] for row in result.all()]


async def delete_custom_role_limits(role_id: int) -> int:
    """Deletes custom limits for a role. Returns number of rows deleted."""
    async with get_session() as session:
        result = await session.execute(
            delete(CustomRoleLimit).where(CustomRoleLimit.role_id == role_id)
        )
        return result.rowcount


# ================================================================================================ #
# Server Owners Operations
# ================================================================================================ #

async def get_server_owners(guild_id: int) -> list[int]:
    """Returns all trusted owner IDs for a guild."""
    async with get_session() as session:
        result = await session.execute(
            select(ServerOwner.user_id).where(ServerOwner.guild_id == guild_id)
        )
        return [row[0] for row in result.all()]


async def add_server_owner(guild_id: int, user_id: int) -> None:
    """Adds a trusted owner (ignores duplicates)."""
    async with get_session() as session:
        stmt = (
            sqlite_insert(ServerOwner)
            .values(guild_id=guild_id, user_id=user_id)
            .on_conflict_do_nothing()
        )
        await session.execute(stmt)


async def remove_server_owner(guild_id: int, user_id: int) -> None:
    """Removes a trusted owner."""
    async with get_session() as session:
        await session.execute(
            delete(ServerOwner).where(
                ServerOwner.guild_id == guild_id, ServerOwner.user_id == user_id
            )
        )


async def is_server_owner(guild_id: int, user_id: int) -> bool:
    """Returns True if the user is a registered trusted owner for the guild."""
    return user_id in await get_server_owners(guild_id)


# ================================================================================================ #
# Custom User Limits Operations
# ================================================================================================ #

async def save_custom_user_limits(user_id: int, guild_id: int, **kwargs: int) -> None:
    """Saves or replaces custom limits for an individual user."""
    cols = [
        "channels_limit", "channels_time", "roles_limit", "roles_time",
        "links_limit", "links_time", "webhooks_limit", "webhooks_time",
    ]
    values = {col: kwargs.get(col, 0) for col in cols}
    async with get_session() as session:
        stmt = (
            sqlite_insert(CustomUserLimit)
            .values(user_id=user_id, guild_id=guild_id, **values)
            .on_conflict_do_update(index_elements=["user_id"], set_=values)
        )
        await session.execute(stmt)


async def get_custom_user_limits(user_id: int) -> Optional[dict]:
    """Returns a dict of limit values for a user, or None."""
    async with get_session() as session:
        result = await session.execute(
            select(CustomUserLimit).where(CustomUserLimit.user_id == user_id)
        )
        row = result.scalar_one_or_none()

    if not row:
        return None
    return {
        "channels_limit": row.channels_limit, "channels_time": row.channels_time,
        "roles_limit": row.roles_limit,       "roles_time": row.roles_time,
        "links_limit": row.links_limit,       "links_time": row.links_time,
        "webhooks_limit": row.webhooks_limit, "webhooks_time": row.webhooks_time,
    }


async def get_all_custom_users(guild_id: int) -> list[int]:
    """Returns all custom admin user IDs for a guild."""
    async with get_session() as session:
        result = await session.execute(
            select(CustomUserLimit.user_id).where(CustomUserLimit.guild_id == guild_id)
        )
        return [row[0] for row in result.all()]


async def delete_custom_user_limits(user_id: int) -> int:
    """Deletes custom limits for a user. Returns number of rows deleted."""
    async with get_session() as session:
        result = await session.execute(
            delete(CustomUserLimit).where(CustomUserLimit.user_id == user_id)
        )
        return result.rowcount
