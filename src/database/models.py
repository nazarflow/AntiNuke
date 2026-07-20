# src/database/models.py
# SQLAlchemy ORM models. Each class maps to a database table.
# Dialect-agnostic: works with both SQLite (dev) and PostgreSQL (prod).

from sqlalchemy import BigInteger, Column, ForeignKey, Integer
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# ================================================================================================ #
# Access Control
# ================================================================================================ #

class Admin(Base):
    """Legacy admin list (pre-Admin Panel era)."""
    __tablename__ = "admins"

    user_id = Column(BigInteger, primary_key=True)


class ServerOwner(Base):
    """Trusted server owners allowed to use the Owner Panel."""
    __tablename__ = "server_owners"

    guild_id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, primary_key=True)


# ================================================================================================ #
# Tracking
# ================================================================================================ #

class TrackedUser(Base):
    """Users being tracked for suspicious activity (e.g. voice-move abuse)."""
    __tablename__ = "tracked_users"

    user_id = Column(BigInteger, primary_key=True)


# ================================================================================================ #
# Guild Configuration
# ================================================================================================ #

class GuildConfig(Base):
    """Per-guild setup: tuner category and log channel."""
    __tablename__ = "guild_configs"

    guild_id = Column(BigInteger, primary_key=True)
    tuner_category_id = Column(BigInteger, nullable=True)
    tuner_channel_id = Column(BigInteger, nullable=True)


class GuildRole(Base):
    """Per-guild role IDs (quarantine, server booster, AI)."""
    __tablename__ = "guild_roles"

    guild_id = Column(BigInteger, primary_key=True)
    quarantine_id = Column(BigInteger, nullable=True)
    quarantine_alt_id = Column(BigInteger, nullable=True)
    server_booster_id = Column(BigInteger, nullable=True)
    ai_id = Column(BigInteger, nullable=True)


class GuildLogChannel(Base):
    """Per-guild mapping of event types to log channel IDs."""
    __tablename__ = "guild_log_channels"

    guild_id = Column(BigInteger, primary_key=True)
    channel_create_id = Column(BigInteger, nullable=True)
    channel_delete_id = Column(BigInteger, nullable=True)
    channel_update_id = Column(BigInteger, nullable=True)
    links_spam_id = Column(BigInteger, nullable=True)
    webhooks_id = Column(BigInteger, nullable=True)
    bot_joins_id = Column(BigInteger, nullable=True)
    message_edit_delete_id = Column(BigInteger, nullable=True)
    voice_move_id = Column(BigInteger, nullable=True)
    role_updates_id = Column(BigInteger, nullable=True)
    bans_id = Column(BigInteger, nullable=True)


class GuildLimit(Base):
    """Default per-guild anti-nuke action limits."""
    __tablename__ = "guild_limits"

    guild_id = Column(BigInteger, primary_key=True)
    channel_create_count = Column(Integer, nullable=True)
    channel_create_time = Column(Integer, nullable=True)
    channel_delete_count = Column(Integer, nullable=True)
    channel_delete_time = Column(Integer, nullable=True)


# ================================================================================================ #
# Custom Admin Limits
# ================================================================================================ #

class CustomRoleLimit(Base):
    """Custom per-role action limits assigned via the Admin Panel."""
    __tablename__ = "custom_role_limits"

    role_id = Column(BigInteger, primary_key=True)
    guild_id = Column(BigInteger, nullable=False)
    channels_limit = Column(Integer, default=0, nullable=False)
    channels_time = Column(Integer, default=0, nullable=False)
    roles_limit = Column(Integer, default=0, nullable=False)
    roles_time = Column(Integer, default=0, nullable=False)
    links_limit = Column(Integer, default=0, nullable=False)
    links_time = Column(Integer, default=0, nullable=False)
    webhooks_limit = Column(Integer, default=0, nullable=False)
    webhooks_time = Column(Integer, default=0, nullable=False)


class CustomUserLimit(Base):
    """Custom per-user action limits assigned via the Admin Panel."""
    __tablename__ = "custom_user_limits"

    user_id = Column(BigInteger, primary_key=True)
    guild_id = Column(BigInteger, nullable=False)
    channels_limit = Column(Integer, default=0, nullable=False)
    channels_time = Column(Integer, default=0, nullable=False)
    roles_limit = Column(Integer, default=0, nullable=False)
    roles_time = Column(Integer, default=0, nullable=False)
    links_limit = Column(Integer, default=0, nullable=False)
    links_time = Column(Integer, default=0, nullable=False)
    webhooks_limit = Column(Integer, default=0, nullable=False)
    webhooks_time = Column(Integer, default=0, nullable=False)
