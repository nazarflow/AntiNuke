import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from typing import List, Optional, Any
import datetime
import sqlite3

OWNER_ID = 478260595687292961
GUILD_ID = 1365026453854359695

ROLE_IDS = {
    "quarantine": 1075125088627720213,
    "quarantine_alt": 1045060791717593175,
    "dvp": 1075119105847341116,
    "ai": 1524139770437959690,
    "server_booster": 1075142507224104981
}

class AsyncAuditLogIterator:
    def __init__(self, entries):
        self.entries = entries

    def __aiter__(self):
        self._iter = iter(self.entries)
        return self

    async def __anext__(self):
        try:
            return next(self._iter)
        except StopIteration:
            raise StopAsyncIteration

    def filter(self, **kwargs):
        # basic filter mockup if needed
        return self

    async def flatten(self):
        return self.entries

@pytest.fixture
def make_role():
    """Factory for creating mock roles."""
    def _make_role(id: int, name: str, permissions=None, managed=False, color=None, hoist=False, mentionable=False):
        role = MagicMock()
        role.id = id
        role.name = name
        role.permissions = permissions or MagicMock()
        role.managed = managed
        role.color = color
        role.hoist = hoist
        role.mentionable = mentionable
        return role
    return _make_role

@pytest.fixture
def make_channel():
    """Factory for creating mock channels."""
    def _make_channel(id: int, name: str, guild, type='text', category=None, overwrites=None, position=0):
        channel = MagicMock()
        channel.id = id
        channel.name = name
        channel.guild = guild
        channel.type = type
        channel.category = category
        channel.overwrites = overwrites or {}
        channel.position = position
        channel.send = AsyncMock()
        channel.delete = AsyncMock()
        channel.edit = AsyncMock()
        return channel
    return _make_channel

@pytest.fixture
def make_member():
    """Factory for creating mock members."""
    def _make_member(id: int, roles=None, bot=False, guild=None):
        member = MagicMock()
        member.id = id
        member.name = f"user_{id}"
        member.mention = f"<@{id}>"
        member.avatar = MagicMock(url=f"http://avatar.com/{id}")
        member.bot = bot
        member.roles = roles or []
        member.guild = guild
        member.edit = AsyncMock()
        member.ban = AsyncMock()
        member.add_roles = AsyncMock()
        member.remove_roles = AsyncMock()
        member.move_to = AsyncMock()
        return member
    return _make_member

@pytest.fixture
def make_audit_entry():
    """Factory for creating mock audit log entries."""
    def _make_audit_entry(user, target, action, created_at=None, reason=None, changes=None):
        entry = MagicMock()
        entry.user = user
        entry.target = target
        entry.action = action
        entry.created_at = created_at or datetime.datetime.now(datetime.timezone.utc)
        entry.reason = reason
        
        # Make changes accessible like entry.changes.before.roles
        entry_changes = MagicMock()
        if changes:
            if 'before' in changes:
                entry_changes.before = MagicMock(**changes['before'])
            if 'after' in changes:
                entry_changes.after = MagicMock(**changes['after'])
        entry.changes = entry_changes
        return entry
    return _make_audit_entry

@pytest_asyncio.fixture
async def mock_log_channel():
    """Fixture for a mock log channel."""
    channel = AsyncMock()
    channel.id = 1099726312744173598
    channel.send = AsyncMock()
    return channel

@pytest_asyncio.fixture
async def mock_bot(mock_log_channel):
    """Fixture for a mock bot instance."""
    bot = AsyncMock()
    bot.get_channel = MagicMock(return_value=mock_log_channel)
    bot.user = MagicMock()
    bot.user.id = 1234567890
    bot.admins = [OWNER_ID]
    bot.user_ids = []
    bot.kick_counter = {}
    return bot

@pytest_asyncio.fixture
async def mock_guild(make_role, make_member):
    """Fixture for a mock guild."""
    guild = MagicMock()
    guild.id = GUILD_ID
    guild.owner_id = OWNER_ID
    
    # Setup roles
    quarantine_role = make_role(ROLE_IDS['quarantine'], "Quarantine")
    dvp_role = make_role(ROLE_IDS['dvp'], "DVP")
    ai_role = make_role(ROLE_IDS['ai'], "AI")
    booster_role = make_role(ROLE_IDS['server_booster'], "Server Booster")
    
    guild.roles = [quarantine_role, dvp_role, ai_role, booster_role]
    
    def get_role(role_id):
        return next((r for r in guild.roles if r.id == role_id), None)
    guild.get_role = MagicMock(side_effect=get_role)
    
    def get_member(member_id):
        # We can return a generic member if not set explicitly by the test
        return make_member(member_id, guild=guild)
    guild.get_member = MagicMock(side_effect=get_member)
    
    guild.ban = AsyncMock()
    guild.unban = AsyncMock()
    guild.create_text_channel = AsyncMock()
    guild.create_voice_channel = AsyncMock()
    guild.create_role = AsyncMock()
    guild.default_role = make_role(123, "@everyone", permissions=MagicMock())
    
    guild.audit_logs = MagicMock(return_value=AsyncAuditLogIterator([]))
    
    return guild

@pytest.fixture
def temp_db(tmp_path):
    """Fixture to create a temporary database."""
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))
    # You can initialize schemas here if necessary
    yield conn
    conn.close()
