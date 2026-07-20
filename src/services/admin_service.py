# src/services/admin_service.py
# Business logic for admin, owner, and tracked-user management.
# This is the ONLY place that should decide "how" admin operations work.
# Cogs call these functions — they never touch the repository directly.

from __future__ import annotations

from src.database import repository as db


# ================================================================================================ #
# Admin Operations
# ================================================================================================ #

async def get_all_admins() -> list[int]:
    return await db.get_all_admins()


async def add_admin(user_id: int) -> None:
    await db.add_admin(user_id)


async def remove_admin(user_id: int) -> None:
    await db.remove_admin(user_id)


# ================================================================================================ #
# Server Owner Operations
# ================================================================================================ #

async def get_server_owners(guild_id: int) -> list[int]:
    return await db.get_server_owners(guild_id)


async def add_server_owner(guild_id: int, user_id: int) -> None:
    await db.add_server_owner(guild_id, user_id)


async def remove_server_owner(guild_id: int, user_id: int) -> None:
    await db.remove_server_owner(guild_id, user_id)


async def is_server_owner(guild_id: int, user_id: int) -> bool:
    return await db.is_server_owner(guild_id, user_id)


# ================================================================================================ #
# Tracked User Operations
# ================================================================================================ #

async def get_all_tracked_users() -> list[int]:
    return await db.get_all_tracked_users()


async def add_tracked_user(user_id: int) -> None:
    await db.add_tracked_user(user_id)


async def remove_tracked_user(user_id: int) -> None:
    await db.remove_tracked_user(user_id)


# ================================================================================================ #
# Custom Role Limits (Admin Panel CRUD)
# ================================================================================================ #

async def save_custom_role_limits(role_id: int, guild_id: int, **kwargs: int) -> None:
    await db.save_custom_role_limits(role_id, guild_id, **kwargs)


async def get_custom_role_limits(role_id: int) -> dict | None:
    return await db.get_custom_role_limits(role_id)


async def get_all_custom_roles(guild_id: int) -> list[int]:
    return await db.get_all_custom_roles(guild_id)


async def delete_custom_role_limits(role_id: int) -> int:
    return await db.delete_custom_role_limits(role_id)


# ================================================================================================ #
# Custom User Limits (Admin Panel CRUD)
# ================================================================================================ #

async def save_custom_user_limits(user_id: int, guild_id: int, **kwargs: int) -> None:
    await db.save_custom_user_limits(user_id, guild_id, **kwargs)


async def get_custom_user_limits(user_id: int) -> dict | None:
    return await db.get_custom_user_limits(user_id)


async def get_all_custom_users(guild_id: int) -> list[int]:
    return await db.get_all_custom_users(guild_id)


async def delete_custom_user_limits(user_id: int) -> int:
    return await db.delete_custom_user_limits(user_id)
