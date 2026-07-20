# src/api/schemas.py
from pydantic import BaseModel
from typing import Optional

# ─── Admins & Owners ──────────────────────────────────────────────────────────

class AdminResponse(BaseModel):
    user_id: int

class ServerOwnerResponse(BaseModel):
    guild_id: int
    user_id: int

class TrackedUserResponse(BaseModel):
    user_id: int

# ─── Configuration ─────────────────────────────────────────────────────────────

class GuildConfigResponse(BaseModel):
    guild_id: int
    tuner_category_id: Optional[int]
    tuner_channel_id: Optional[int]

class GuildConfigUpdate(BaseModel):
    tuner_category_id: Optional[int] = None
    tuner_channel_id: Optional[int] = None

class GuildRolesResponse(BaseModel):
    guild_id: int
    quarantine_id: Optional[int]
    quarantine_alt_id: Optional[int]
    ai_id: Optional[int]
    server_booster_id: Optional[int]

class GuildRolesUpdate(BaseModel):
    quarantine_id: Optional[int] = None
    quarantine_alt_id: Optional[int] = None
    ai_id: Optional[int] = None
    server_booster_id: Optional[int] = None

class GuildLogChannelsResponse(BaseModel):
    guild_id: int
    channel_create_id: Optional[int]
    channel_delete_id: Optional[int]
    channel_update_id: Optional[int]
    links_spam_id: Optional[int]
    webhooks_id: Optional[int]
    bot_joins_id: Optional[int]
    message_edit_delete_id: Optional[int]
    voice_move_id: Optional[int]
    role_updates_id: Optional[int]
    bans_id: Optional[int]

class GuildLogChannelsUpdate(BaseModel):
    channel_create_id: Optional[int] = None
    channel_delete_id: Optional[int] = None
    channel_update_id: Optional[int] = None
    links_spam_id: Optional[int] = None
    webhooks_id: Optional[int] = None
    bot_joins_id: Optional[int] = None
    message_edit_delete_id: Optional[int] = None
    voice_move_id: Optional[int] = None
    role_updates_id: Optional[int] = None
    bans_id: Optional[int] = None

# ─── Limits ────────────────────────────────────────────────────────────────────

class GuildLimitsResponse(BaseModel):
    guild_id: int
    channels_limit: int
    channels_time: int
    roles_limit: int
    roles_time: int
    links_limit: int
    links_time: int
    webhooks_limit: int
    webhooks_time: int

class GuildLimitsUpdate(BaseModel):
    channels_limit: Optional[int] = None
    channels_time: Optional[int] = None
    roles_limit: Optional[int] = None
    roles_time: Optional[int] = None
    links_limit: Optional[int] = None
    links_time: Optional[int] = None
    webhooks_limit: Optional[int] = None
    webhooks_time: Optional[int] = None

class CustomRoleLimitsResponse(BaseModel):
    role_id: int
    guild_id: int
    channels_limit: int
    channels_time: int
    roles_limit: int
    roles_time: int
    links_limit: int
    links_time: int
    webhooks_limit: int
    webhooks_time: int

class CustomRoleLimitsUpdate(BaseModel):
    channels_limit: Optional[int] = None
    channels_time: Optional[int] = None
    roles_limit: Optional[int] = None
    roles_time: Optional[int] = None
    links_limit: Optional[int] = None
    links_time: Optional[int] = None
    webhooks_limit: Optional[int] = None
    webhooks_time: Optional[int] = None

class CustomUserLimitsResponse(BaseModel):
    user_id: int
    guild_id: int
    channels_limit: int
    channels_time: int
    roles_limit: int
    roles_time: int
    links_limit: int
    links_time: int
    webhooks_limit: int
    webhooks_time: int

class CustomUserLimitsUpdate(BaseModel):
    channels_limit: Optional[int] = None
    channels_time: Optional[int] = None
    roles_limit: Optional[int] = None
    roles_time: Optional[int] = None
    links_limit: Optional[int] = None
    links_time: Optional[int] = None
    webhooks_limit: Optional[int] = None
    webhooks_time: Optional[int] = None
