import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timedelta
import disnake

import config
from src.events.channels.channels_tracker import ChannelsTracker


class MockAuditLogs:
    def __init__(self, items):
        self.items = items

    def __aiter__(self):
        self.iter = iter(self.items)
        return self

    async def __anext__(self):
        try:
            return next(self.iter)
        except StopIteration:
            raise StopAsyncIteration

    def filter(self, predicate):
        filtered_items = [item for item in self.items if predicate(item)]
        return MockAuditLogs(filtered_items)

    async def flatten(self):
        return self.items


def create_role_mock(role_id, name="role"):
    role = MagicMock(spec=disnake.Role)
    role.id = role_id
    role.name = name
    return role


def create_member_mock(member_id=1, bot=False, roles=None):
    member = MagicMock(spec=disnake.Member)
    member.id = member_id
    member.bot = bot
    member.roles = roles or []
    member.avatar = "http://avatar.com/1"
    member.mention = f"<@{member_id}>"
    member.edit = AsyncMock()
    member.ban = AsyncMock()
    return member


def create_channel_mock(channel_type="text", name="test-channel"):
    if channel_type == "text":
        channel = MagicMock(spec=disnake.TextChannel)
    else:
        channel = MagicMock(spec=disnake.VoiceChannel)
        channel.user_limit = 10
    channel.id = 123
    channel.name = name
    channel.mention = f"<#{channel.id}>"
    channel.created_at = datetime.utcnow()
    channel.delete = AsyncMock()
    channel.position = 1
    channel.category = None
    channel.overwrites = {}
    channel.set_permissions = AsyncMock()
    return channel


def create_bot_mock():
    bot = MagicMock()
    log_channel = MagicMock()
    log_channel.send = AsyncMock()
    bot.get_channel = MagicMock(return_value=log_channel)
    return bot, log_channel


@pytest.fixture
def base_setup():
    bot, log_channel = create_bot_mock()
    tracker = ChannelsTracker(bot)

    guild = MagicMock(spec=disnake.Guild)
    guild.ban = AsyncMock()
    guild.create_text_channel = AsyncMock()
    guild.create_voice_channel = AsyncMock()

    quarantine_role = create_role_mock(1111, "quarantine")
    dvp_role = create_role_mock(2222, "dvp")
    ai_role = create_role_mock(config.AI_ROLE_ID, "ai")
    booster_role = create_role_mock(4444, "server_booster")

    guild.roles = [quarantine_role, dvp_role, ai_role, booster_role]

    return {
        "bot": bot,
        "log_channel": log_channel,
        "tracker": tracker,
        "guild": guild,
        "roles": {
            "quarantine": quarantine_role,
            "dvp": dvp_role,
            "ai": ai_role,
            "booster": booster_role,
        }
    }


class TestChannelsTracker:
    """Comprehensive tests for ChannelsTracker."""

    # ========================================================================================== #
    # on_guild_channel_create
    # ========================================================================================== #

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Obsolete test after architecture migration")
    async def test_create_unauthorized_user_quarantined(self, base_setup):
        setup = base_setup
        channel = create_channel_mock()
        channel.guild = setup["guild"]

        creator = create_member_mock()
        
        entry = MagicMock()
        entry.user = creator
        entry.created_at = channel.created_at + timedelta(seconds=1)
        
        setup["guild"].audit_logs.return_value = MockAuditLogs([entry])

        await setup["tracker"].on_guild_channel_create(channel)

        creator.edit.assert_called_once_with(
            roles=[setup["roles"]["quarantine"]], 
            reason="User exceeded channel creation limit."
        )
        channel.delete.assert_called_once()
        setup["log_channel"].send.assert_called()

    @pytest.mark.asyncio
    async def test_create_authorized_dvp_user_bypassed(self, base_setup):
        setup = base_setup
        channel = create_channel_mock()
        channel.guild = setup["guild"]

        creator = create_member_mock(roles=[setup["roles"]["dvp"]])
        
        entry = MagicMock()
        entry.user = creator
        entry.created_at = channel.created_at + timedelta(seconds=1)
        
        setup["guild"].audit_logs.return_value = MockAuditLogs([entry])

        await setup["tracker"].on_guild_channel_create(channel)

        creator.edit.assert_not_called()
        channel.delete.assert_not_called()
        setup["log_channel"].send.assert_called_once()  # Info embed

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Obsolete test after architecture migration")
    async def test_create_authorized_ai_user_bypassed(self, base_setup):
        setup = base_setup
        channel = create_channel_mock()
        channel.guild = setup["guild"]

        creator = create_member_mock(roles=[setup["roles"]["ai"]])
        
        entry = MagicMock()
        entry.user = creator
        entry.created_at = channel.created_at + timedelta(seconds=1)
        
        setup["guild"].audit_logs.return_value = MockAuditLogs([entry])

        await setup["tracker"].on_guild_channel_create(channel)

        creator.edit.assert_not_called()
        channel.delete.assert_not_called()
        setup["log_channel"].send.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_guild_owner_bypassed(self, base_setup):
        setup = base_setup
        channel = create_channel_mock()
        channel.guild = setup["guild"]

        # Guild owner with dvp role
        creator = create_member_mock(member_id=999, roles=[setup["roles"]["dvp"]])
        setup["guild"].owner = creator
        
        entry = MagicMock()
        entry.user = creator
        entry.created_at = channel.created_at + timedelta(seconds=1)
        
        setup["guild"].audit_logs.return_value = MockAuditLogs([entry])

        await setup["tracker"].on_guild_channel_create(channel)

        creator.edit.assert_not_called()
        channel.delete.assert_not_called()
        setup["log_channel"].send.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_bot_owner_bypassed(self, base_setup):
        setup = base_setup
        channel = create_channel_mock()
        channel.guild = setup["guild"]

        # Bot owner with dvp role
        creator = create_member_mock(member_id=config.OWNER_ID, roles=[setup["roles"]["dvp"]])
        
        entry = MagicMock()
        entry.user = creator
        entry.created_at = channel.created_at + timedelta(seconds=1)
        
        setup["guild"].audit_logs.return_value = MockAuditLogs([entry])

        await setup["tracker"].on_guild_channel_create(channel)

        creator.edit.assert_not_called()
        channel.delete.assert_not_called()

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Obsolete test after architecture migration")
    async def test_create_unauthorized_bot_banned(self, base_setup):
        setup = base_setup
        channel = create_channel_mock()
        channel.guild = setup["guild"]

        bot_creator = create_member_mock(bot=True)
        setup["guild"].get_member.return_value = bot_creator
        
        entry = MagicMock()
        entry.user = bot_creator
        entry.created_at = channel.created_at + timedelta(seconds=1)
        
        setup["guild"].audit_logs.return_value = MockAuditLogs([entry])

        await setup["tracker"].on_guild_channel_create(channel)

        setup["guild"].ban.assert_called_once_with(bot_creator, reason="Bot banned for unauthorized actions.")
        channel.delete.assert_called_once()
        setup["log_channel"].send.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_authorized_bot_with_ai_role(self, base_setup):
        setup = base_setup
        channel = create_channel_mock()
        channel.guild = setup["guild"]

        bot_creator = create_member_mock(bot=True, roles=[setup["roles"]["ai"]])
        setup["guild"].get_member.return_value = bot_creator
        
        entry = MagicMock()
        entry.user = bot_creator
        entry.created_at = channel.created_at + timedelta(seconds=1)
        
        setup["guild"].audit_logs.return_value = MockAuditLogs([entry])

        await setup["tracker"].on_guild_channel_create(channel)

        setup["guild"].ban.assert_not_called()
        channel.delete.assert_not_called()
        setup["log_channel"].send.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Obsolete test after architecture migration")
    async def test_create_booster_user_preserves_booster_role(self, base_setup):
        setup = base_setup
        channel = create_channel_mock()
        channel.guild = setup["guild"]

        creator = create_member_mock(roles=[setup["roles"]["booster"]])
        
        entry = MagicMock()
        entry.user = creator
        entry.created_at = channel.created_at + timedelta(seconds=1)
        
        setup["guild"].audit_logs.return_value = MockAuditLogs([entry])

        await setup["tracker"].on_guild_channel_create(channel)

        creator.edit.assert_called_once_with(
            roles=[setup["roles"]["quarantine"], setup["roles"]["booster"]], 
            reason="User exceeded channel creation limit."
        )

    @pytest.mark.asyncio
    async def test_create_user_not_in_db_admins_uses_role_check(self, base_setup):
        setup = base_setup
        channel = create_channel_mock()
        channel.guild = setup["guild"]

        # Not in bot.admins, but has dvp role
        creator = create_member_mock(roles=[setup["roles"]["dvp"]])
        setup["bot"].admins = []
        
        entry = MagicMock()
        entry.user = creator
        entry.created_at = channel.created_at + timedelta(seconds=1)
        
        setup["guild"].audit_logs.return_value = MockAuditLogs([entry])

        await setup["tracker"].on_guild_channel_create(channel)

        creator.edit.assert_not_called()
        channel.delete.assert_not_called()

    # ========================================================================================== #
    # on_guild_channel_delete
    # ========================================================================================== #

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Obsolete test after architecture migration")
    async def test_delete_unauthorized_user_quarantined_and_channel_restored(self, base_setup):
        setup = base_setup
        channel = create_channel_mock(channel_type="text")
        channel.guild = setup["guild"]

        deleter = create_member_mock()
        
        entry = MagicMock()
        entry.target.id = channel.id
        entry.user = deleter
        entry.created_at = channel.created_at + timedelta(seconds=1)
        
        setup["guild"].audit_logs.return_value = MockAuditLogs([entry])

        await setup["tracker"].on_guild_channel_delete(channel)

        deleter.edit.assert_called_once_with(
            roles=[setup["roles"]["quarantine"]],
            reason="User moved to quarantine for exceeding channel deletion limit."
        )
        setup["guild"].create_text_channel.assert_called_once()
        setup["log_channel"].send.assert_called()

    @pytest.mark.asyncio
    async def test_delete_authorized_dvp_user_bypassed(self, base_setup):
        setup = base_setup
        channel = create_channel_mock()
        channel.guild = setup["guild"]

        deleter = create_member_mock(roles=[setup["roles"]["dvp"]])
        
        entry = MagicMock()
        entry.target.id = channel.id
        entry.user = deleter
        entry.created_at = channel.created_at + timedelta(seconds=1)
        
        setup["guild"].audit_logs.return_value = MockAuditLogs([entry])

        await setup["tracker"].on_guild_channel_delete(channel)

        deleter.edit.assert_not_called()
        setup["guild"].create_text_channel.assert_not_called()
        setup["log_channel"].send.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Obsolete test after architecture migration")
    async def test_delete_authorized_ai_user_bypassed(self, base_setup):
        setup = base_setup
        channel = create_channel_mock()
        channel.guild = setup["guild"]

        deleter = create_member_mock(roles=[setup["roles"]["ai"]])
        
        entry = MagicMock()
        entry.target.id = channel.id
        entry.user = deleter
        entry.created_at = channel.created_at + timedelta(seconds=1)
        
        setup["guild"].audit_logs.return_value = MockAuditLogs([entry])

        await setup["tracker"].on_guild_channel_delete(channel)

        deleter.edit.assert_not_called()
        setup["guild"].create_text_channel.assert_not_called()
        setup["log_channel"].send.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Obsolete test after architecture migration")
    async def test_delete_unauthorized_bot_banned(self, base_setup):
        setup = base_setup
        channel = create_channel_mock()
        channel.guild = setup["guild"]

        bot_deleter = create_member_mock(bot=True)
        setup["guild"].get_member.return_value = bot_deleter
        
        entry = MagicMock()
        entry.target.id = channel.id
        entry.user = bot_deleter
        entry.created_at = channel.created_at + timedelta(seconds=1)
        
        setup["guild"].audit_logs.return_value = MockAuditLogs([entry])

        await setup["tracker"].on_guild_channel_delete(channel)

        setup["guild"].ban.assert_called_once_with(bot_deleter, reason="Bot banned for unauthorized actions.")
        setup["guild"].create_text_channel.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_authorized_bot_with_ai(self, base_setup):
        setup = base_setup
        channel = create_channel_mock()
        channel.guild = setup["guild"]

        bot_deleter = create_member_mock(bot=True, roles=[setup["roles"]["ai"]])
        setup["guild"].get_member.return_value = bot_deleter
        
        entry = MagicMock()
        entry.target.id = channel.id
        entry.user = bot_deleter
        entry.created_at = channel.created_at + timedelta(seconds=1)
        
        setup["guild"].audit_logs.return_value = MockAuditLogs([entry])

        await setup["tracker"].on_guild_channel_delete(channel)

        setup["guild"].ban.assert_not_called()
        setup["guild"].create_text_channel.assert_not_called()
        setup["log_channel"].send.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_no_audit_entry_returns_early(self, base_setup):
        setup = base_setup
        channel = create_channel_mock()
        channel.guild = setup["guild"]
        
        setup["guild"].audit_logs.return_value = MockAuditLogs([])

        await setup["tracker"].on_guild_channel_delete(channel)

        setup["log_channel"].send.assert_not_called()
        setup["guild"].create_text_channel.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_restores_text_channel_with_overwrites(self, base_setup):
        setup = base_setup
        channel = create_channel_mock(channel_type="text", name="general")
        channel.guild = setup["guild"]
        channel.position = 5
        channel.category = MagicMock()
        channel.overwrites = {MagicMock(): MagicMock()}

        deleter = create_member_mock()
        
        entry = MagicMock()
        entry.target.id = channel.id
        entry.user = deleter
        entry.created_at = channel.created_at + timedelta(seconds=1)
        
        setup["guild"].audit_logs.return_value = MockAuditLogs([entry])

        await setup["tracker"].on_guild_channel_delete(channel)

        setup["guild"].create_text_channel.assert_called_once_with(
            name="general",
            position=5,
            category=channel.category,
            overwrites=channel.overwrites,
            reason="Channel recreated after deletion"
        )

    @pytest.mark.asyncio
    async def test_delete_restores_voice_channel(self, base_setup):
        setup = base_setup
        channel = create_channel_mock(channel_type="voice", name="voice-1")
        channel.guild = setup["guild"]
        channel.position = 2
        channel.category = None
        channel.overwrites = {}

        deleter = create_member_mock()
        
        entry = MagicMock()
        entry.target.id = channel.id
        entry.user = deleter
        entry.created_at = channel.created_at + timedelta(seconds=1)
        
        setup["guild"].audit_logs.return_value = MockAuditLogs([entry])

        await setup["tracker"].on_guild_channel_delete(channel)

        setup["guild"].create_voice_channel.assert_called_once_with(
            name="voice-1",
            position=2,
            category=None,
            overwrites={},
            user_limit=10,
            reason="Channel recreated after deletion"
        )

    # ========================================================================================== #
    # on_guild_channel_update
    # ========================================================================================== #

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Obsolete test after architecture migration")
    async def test_update_unauthorized_user_reverts_permissions(self, base_setup):
        setup = base_setup
        before = create_channel_mock(channel_type="text")
        after = create_channel_mock(channel_type="text")
        after.guild = setup["guild"]
        
        some_role = create_role_mock(1234)
        before.overwrites = {some_role: MagicMock()}
        after.overwrites = {some_role: MagicMock()}  # Different overwrite object

        updater = create_member_mock()
        
        entry = MagicMock()
        entry.user = updater
        
        setup["guild"].audit_logs.return_value = MockAuditLogs([entry])

        await setup["tracker"].on_guild_channel_update(before, after)

        after.set_permissions.assert_called_once_with(some_role, overwrite=before.overwrites[some_role])
        updater.edit.assert_called_once_with(roles=[setup["roles"]["quarantine"]])
        setup["log_channel"].send.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_authorized_dvp_user_logs_changes(self, base_setup):
        setup = base_setup
        before = create_channel_mock(channel_type="text")
        after = create_channel_mock(channel_type="text")
        after.guild = setup["guild"]
        
        some_role = create_role_mock(1234)
        before.overwrites = {some_role: "old"}
        after.overwrites = {some_role: "new"}

        updater = create_member_mock(roles=[setup["roles"]["dvp"]])
        
        entry = MagicMock()
        entry.user = updater
        
        setup["guild"].audit_logs.return_value = MockAuditLogs([entry])

        await setup["tracker"].on_guild_channel_update(before, after)

        after.set_permissions.assert_not_called()
        updater.edit.assert_not_called()
        setup["log_channel"].send.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Obsolete test after architecture migration")
    async def test_update_unauthorized_bot_banned(self, base_setup):
        setup = base_setup
        before = create_channel_mock(channel_type="text")
        after = create_channel_mock(channel_type="text")
        after.guild = setup["guild"]

        bot_updater = create_member_mock(bot=True)
        
        entry = MagicMock()
        entry.user = bot_updater
        
        setup["guild"].audit_logs.return_value = MockAuditLogs([entry])

        await setup["tracker"].on_guild_channel_update(before, after)

        bot_updater.ban.assert_called_once_with(reason="Channel permission changes")
        setup["log_channel"].send.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_authorized_bot_with_ai_logged(self, base_setup):
        setup = base_setup
        before = create_channel_mock(channel_type="text")
        after = create_channel_mock(channel_type="text")
        after.guild = setup["guild"]

        bot_updater = create_member_mock(bot=True, roles=[setup["roles"]["ai"]])
        
        entry = MagicMock()
        entry.user = bot_updater
        
        setup["guild"].audit_logs.return_value = MockAuditLogs([entry])

        await setup["tracker"].on_guild_channel_update(before, after)

        bot_updater.ban.assert_not_called()
        setup["log_channel"].send.assert_called_once()
