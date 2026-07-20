# src/services/limits_service.py
# Async-compatible rate-limiting service.
# Wraps the in-memory RateLimiter with async DB lookups for custom role/user limits.

from __future__ import annotations

import time

from src.database import repository as db


class RateLimiter:
    """In-memory sliding-window rate limiter.

    Tracks action timestamps per guild/user/action_type and checks them against
    the custom limits stored in the database (via the repository).
    """

    def __init__(self):
        # {guild_id: {user_id: {action_type: [timestamp, ...]}}}
        self.tracker: dict[int, dict[int, dict[str, list[float]]]] = {}

    # ------------------------------------------------------------------ #
    # Recording
    # ------------------------------------------------------------------ #

    def add_action(self, guild_id: int, user_id: int, action_type: str) -> None:
        """Records an action timestamp for a user."""
        guild = self.tracker.setdefault(guild_id, {})
        user = guild.setdefault(user_id, {})
        user.setdefault(action_type, []).append(time.time())

    # ------------------------------------------------------------------ #
    # Limit checking (async — needs DB)
    # ------------------------------------------------------------------ #

    async def check_limit(
        self,
        guild_id: int,
        user_id: int,
        action_type: str,
        user_roles: list,
    ) -> bool:
        """Check if a user is within their rate limit for *action_type*.

        Returns ``True`` if the user is **allowed** (not rate-limited).
        Returns ``False`` if the user **exceeded** the limit.
        """
        # 1. Check per-user custom limits first
        user_limits = await db.get_custom_user_limits(user_id)
        if user_limits:
            best_limit = user_limits.get(f"{action_type}_limit", 0)
            best_time = user_limits.get(f"{action_type}_time", 0)
            if best_limit > 0:
                return self._within_window(guild_id, user_id, action_type, best_limit, best_time)
            return False  # Explicitly forbidden

        # 2. Fall back to per-role custom limits
        custom_role_ids = await db.get_all_custom_roles(guild_id)

        best_limit = 0
        best_time = 0
        has_custom_role = False

        for role in user_roles:
            if role.id in custom_role_ids:
                has_custom_role = True
                limits = await db.get_custom_role_limits(role.id)
                if limits:
                    r_limit = limits.get(f"{action_type}_limit", 0)
                    r_time = limits.get(f"{action_type}_time", 0)
                    if r_limit > best_limit:
                        best_limit = r_limit
                        best_time = r_time

        if not has_custom_role:
            return False  # No admin role → forbidden

        if best_limit == 0:
            return False  # Completely forbidden

        return self._within_window(guild_id, user_id, action_type, best_limit, best_time)

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _within_window(
        self,
        guild_id: int,
        user_id: int,
        action_type: str,
        limit: int,
        time_minutes: int,
    ) -> bool:
        """Return True if the user is still within the allowed action count."""
        actions = (
            self.tracker
            .get(guild_id, {})
            .get(user_id, {})
            .get(action_type, [])
        )
        if not actions:
            return True

        now = time.time()
        window = time_minutes * 60
        recent = [t for t in actions if now - t <= window]

        # Update tracker to keep only recent entries
        self.tracker.setdefault(guild_id, {}).setdefault(user_id, {})[action_type] = recent

        return len(recent) <= limit

    def clean_old_records(self) -> None:
        """Removes records older than 1 hour (house-keeping)."""
        now = time.time()
        max_age = 3600

        for guild_id, users in list(self.tracker.items()):
            for user_id, actions in list(users.items()):
                for action_type, timestamps in list(actions.items()):
                    actions[action_type] = [t for t in timestamps if now - t <= max_age]
                    if not actions[action_type]:
                        del actions[action_type]
                if not actions:
                    del users[user_id]
            if not users:
                del self.tracker[guild_id]


# Singleton instance
limiter = RateLimiter()
