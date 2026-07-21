import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import disnake
import config
from src.events.members.members_tracker import MembersTracker


def create_mock_role(role_id, name="role"):
    role = MagicMock(spec=disnake.Role)
    role.id = role_id
    role.name = name
    role.mention = f"<@&{role_id}>"
    return role


class MockAuditLogEntry:
    def __init__(self, user, target, reason=None):
        self.user = user
        self.target = target
        self.reason = reason


async def mock_audit_logs_gen(entries):
    for entry in entries:
        yield entry


class MockAuditLogs:
    def __init__(self, entries):
        self.entries = entries

    def __aiter__(self):
        return mock_audit_logs_gen(self.entries)

    async def flatten(self):
        return self.entries


@pytest.fixture
def bot():
    b = MagicMock()
    b.user_ids = [111, 222]
    # For bot.get_channel().send()
    b.get_channel = MagicMock()
    b.get_channel.return_value.send = AsyncMock()
    return b


@pytest.fixture
def tracker(bot):
    return MembersTracker(bot)


@pytest.mark.asyncio
class TestMembersTracker:
    # ========================================================================================== #
    # on_member_join tests
    # ========================================================================================== #

    async def test_join_non_bot_member_ignored(self, tracker):
        member = MagicMock()
        member.bot = False
        member.guild.audit_logs = MagicMock()

        await tracker.on_member_join(member)

        member.guild.audit_logs.assert_not_called()

    async def test_join_bot_added_by_owner(self, tracker):
        member = MagicMock()
        member.bot = True
        member.id = 999
        member.mention = "<@999>"

        added_by = MagicMock()
        added_by.id = config.OWNER_ID

        entry = MockAuditLogEntry(user=added_by, target=member)
        member.guild.audit_logs.return_value = MockAuditLogs([entry])

        await tracker.on_member_join(member)

        tracker.bot.get_channel.assert_called_with(config.LOG_CHANNELS["bot_joins"])
        send_mock = tracker.bot.get_channel.return_value.send
        send_mock.assert_called_once()
        assert "Authorized developer" in send_mock.call_args[0][0]

        member.ban.assert_not_called()

    async def test_join_bot_added_by_non_owner(self, tracker):
        member = MagicMock()
        member.bot = True
        member.id = 999
        guild = member.guild

        added_by = MagicMock()
        added_by.id = 12345
        added_by.roles = []
        added_by.edit = AsyncMock()
        member.ban = AsyncMock()

        entry = MockAuditLogEntry(user=added_by, target=member)
        guild.audit_logs.return_value = MockAuditLogs([entry])

        quarantine_role = create_mock_role(config.ROLES["quarantine"])
        guild.get_role.side_effect = lambda role_id: quarantine_role if role_id == config.ROLES["quarantine"] else None

        dvp_role = create_mock_role(config.ROLES["dvp"])
        guild.roles = [dvp_role]

        with patch('src.events.members.members_tracker.embeds.bot_joined_unauthorized', return_value="mock_embed"):
            await tracker.on_member_join(member)

        member.ban.assert_called_once_with(reason="Unauthorized Bot")
        added_by.edit.assert_called_once_with(roles=[quarantine_role], reason="Adding bot to server")

        send_mock = tracker.bot.get_channel.return_value.send
        assert send_mock.call_count == 2
        send_mock.assert_any_call(embed="mock_embed")
        send_mock.assert_any_call(f"{dvp_role.mention} - Please investigate")

    async def test_join_bot_inviter_with_booster_preserves_booster(self, tracker):
        member = MagicMock()
        member.bot = True
        member.id = 999
        guild = member.guild

        added_by = MagicMock()
        added_by.id = 12345
        added_by.edit = AsyncMock()
        member.ban = AsyncMock()

        booster_role = create_mock_role(config.ROLES["server_booster"])
        added_by.roles = [booster_role]

        entry = MockAuditLogEntry(user=added_by, target=member)
        guild.audit_logs.return_value = MockAuditLogs([entry])

        quarantine_role = create_mock_role(config.ROLES["quarantine"])
        guild.get_role.side_effect = lambda r_id: quarantine_role if r_id == config.ROLES["quarantine"] else (booster_role if r_id == config.ROLES["server_booster"] else None)

        dvp_role = create_mock_role(config.ROLES["dvp"])
        guild.roles = [dvp_role]

        with patch('src.events.members.members_tracker.embeds.bot_joined_unauthorized', return_value="mock_embed"):
            await tracker.on_member_join(member)

        member.ban.assert_called_once_with(reason="Unauthorized Bot")
        added_by.edit.assert_called_once_with(roles=[quarantine_role, booster_role], reason="Adding bot to server")

    async def test_join_bot_added_by_user_not_in_db(self, tracker):
        member = MagicMock()
        member.bot = True
        member.id = 999
        guild = member.guild

        added_by = MagicMock()
        added_by.id = 8888  # Not owner
        added_by.roles = []
        added_by.edit = AsyncMock()
        member.ban = AsyncMock()

        entry = MockAuditLogEntry(user=added_by, target=member)
        guild.audit_logs.return_value = MockAuditLogs([entry])

        quarantine_role = create_mock_role(config.ROLES["quarantine"])
        guild.get_role.side_effect = lambda r_id: quarantine_role if r_id == config.ROLES["quarantine"] else None

        dvp_role = create_mock_role(config.ROLES["dvp"])
        guild.roles = [dvp_role]

        with patch('src.events.members.members_tracker.embeds.bot_joined_unauthorized', return_value="mock_embed"):
            await tracker.on_member_join(member)

        member.ban.assert_called_once_with(reason="Unauthorized Bot")

    # ========================================================================================== #
    # on_member_ban tests
    # ========================================================================================== #

    async def test_ban_by_unauthorized_user(self, tracker):
        guild = MagicMock()
        user = MagicMock()  # The victim
        guild.unban = AsyncMock()

        dvp_role = create_mock_role(config.ROLES["dvp"])
        quarantine_role = create_mock_role(config.ROLES["quarantine"])
        guild.get_role.side_effect = lambda r_id: dvp_role if r_id == config.ROLES["dvp"] else (quarantine_role if r_id == config.ROLES["quarantine"] else None)

        member = MagicMock()  # The banner
        member.roles = []  # No dvp role
        member.edit = AsyncMock()

        entry = MockAuditLogEntry(user=member, target=user, reason="Some reason")
        guild.audit_logs.return_value = MockAuditLogs([entry])

        with patch('src.events.members.members_tracker.embeds.ban_unauthorized', return_value="mock_embed_unauth"):
            await tracker.on_member_ban(guild, user)

        member.edit.assert_called_once_with(roles=[quarantine_role])
        guild.unban.assert_called_once_with(user, reason="Banned by mistake")

        tracker.bot.get_channel.assert_called_with(config.LOG_CHANNELS["bans"])
        tracker.bot.get_channel.return_value.send.assert_called_once_with(embed="mock_embed_unauth")

    async def test_ban_by_authorized_dvp_user(self, tracker):
        guild = MagicMock()
        user = MagicMock()
        guild.unban = AsyncMock()

        dvp_role = create_mock_role(config.ROLES["dvp"])
        guild.get_role.return_value = dvp_role

        member = MagicMock()  # The banner
        member.roles = [dvp_role]  # Has dvp
        member.edit = AsyncMock()

        entry = MockAuditLogEntry(user=member, target=user, reason="Bad behavior")
        guild.audit_logs.return_value = MockAuditLogs([entry])

        with patch('src.events.members.members_tracker.embeds.ban_authorized', return_value="mock_embed_auth"):
            await tracker.on_member_ban(guild, user)

        member.edit.assert_not_called()
        guild.unban.assert_not_called()

        tracker.bot.get_channel.assert_called_with(config.LOG_CHANNELS["bans"])
        tracker.bot.get_channel.return_value.send.assert_called_once_with(embed="mock_embed_auth")

    async def test_ban_no_reason_defaults_to_message(self, tracker):
        guild = MagicMock()
        user = MagicMock()

        dvp_role = create_mock_role(config.ROLES["dvp"])
        guild.get_role.return_value = dvp_role

        member = MagicMock()
        member.roles = [dvp_role]

        entry = MockAuditLogEntry(user=member, target=user, reason=None)
        guild.audit_logs.return_value = MockAuditLogs([entry])

        with patch('src.events.members.members_tracker.embeds.ban_authorized') as mock_ban_auth:
            mock_ban_auth.return_value = "mock_embed_auth"
            await tracker.on_member_ban(guild, user)

        mock_ban_auth.assert_called_once_with(member, user, "Reason not provided")

    async def test_ban_by_guild_owner_with_dvp(self, tracker):
        guild = MagicMock()
        user = MagicMock()

        dvp_role = create_mock_role(config.ROLES["dvp"])
        guild.get_role.return_value = dvp_role

        member = MagicMock()
        member.roles = [dvp_role]

        entry = MockAuditLogEntry(user=member, target=user, reason="Owner ban")
        guild.audit_logs.return_value = MockAuditLogs([entry])

        with patch('src.events.members.members_tracker.embeds.ban_authorized', return_value="mock_embed_auth"):
            await tracker.on_member_ban(guild, user)

        tracker.bot.get_channel.return_value.send.assert_called_once_with(embed="mock_embed_auth")
        guild.unban.assert_not_called()

    async def test_ban_unauthorized_preserves_booster(self, tracker):
        guild = MagicMock()
        user = MagicMock()
        guild.unban = AsyncMock()

        dvp_role = create_mock_role(config.ROLES["dvp"])
        quarantine_role = create_mock_role(config.ROLES["quarantine"])
        booster_role = create_mock_role(config.ROLES["server_booster"])

        def get_role_mock(r_id):
            if r_id == config.ROLES["dvp"]: return dvp_role
            if r_id == config.ROLES["quarantine"]: return quarantine_role
            if r_id == config.ROLES["server_booster"]: return booster_role
            return None

        guild.get_role.side_effect = get_role_mock

        member = MagicMock()
        member.roles = [booster_role]  # No dvp, but has booster
        member.edit = AsyncMock()

        entry = MockAuditLogEntry(user=member, target=user, reason="Bad")
        guild.audit_logs.return_value = MockAuditLogs([entry])

        with patch('src.events.members.members_tracker.embeds.ban_unauthorized', return_value="mock_embed_unauth"):
            await tracker.on_member_ban(guild, user)

        member.edit.assert_called_once_with(roles=[quarantine_role, booster_role])
        guild.unban.assert_called_once_with(user, reason="Banned by mistake")

    # ========================================================================================== #
    # on_voice_state_update tests
    # ========================================================================================== #

    async def test_voice_tracked_user_moved(self, tracker):
        member = MagicMock()
        member.id = 111  # tracked in bot.user_ids
        member.move_to = AsyncMock()

        before = MagicMock()
        before.channel = MagicMock()

        after = MagicMock()
        after.channel = MagicMock()

        mock_log_channel = MagicMock()
        tracker.bot.get_channel.return_value = mock_log_channel

        await tracker.on_voice_state_update(member, before, after)

        tracker.bot.get_channel.assert_called_once_with(config.LOG_CHANNELS["voice_move"])
        member.move_to.assert_called_once_with(mock_log_channel)

    async def test_voice_untracked_user_ignored(self, tracker):
        member = MagicMock()
        member.id = 999  # not tracked
        member.move_to = AsyncMock()

        before = MagicMock()
        before.channel = MagicMock()
        after = MagicMock()
        after.channel = MagicMock()

        await tracker.on_voice_state_update(member, before, after)

        member.move_to.assert_not_called()

    async def test_voice_tracked_user_same_channel_ignored(self, tracker):
        member = MagicMock()
        member.id = 111
        member.move_to = AsyncMock()

        channel = MagicMock()
        before = MagicMock()
        before.channel = channel
        after = MagicMock()
        after.channel = channel

        await tracker.on_voice_state_update(member, before, after)

        member.move_to.assert_not_called()

    async def test_voice_tracked_user_disconnects_ignored(self, tracker):
        member = MagicMock()
        member.id = 111
        member.move_to = AsyncMock()

        before = MagicMock()
        before.channel = MagicMock()
        after = MagicMock()
        after.channel = None

        await tracker.on_voice_state_update(member, before, after)

        member.move_to.assert_not_called()
