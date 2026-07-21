import pytest
import disnake
from unittest.mock import AsyncMock, MagicMock, patch

from src.events.roles.roles_tracker import RolesTracker
import config


class AsyncIteratorMock:
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

    async def flatten(self):
        return self.items


def create_mock_member(is_bot=False, roles=None, user_id=111, name="User"):
    m = AsyncMock()
    m.bot = is_bot
    m.id = user_id
    m.roles = roles or []
    m.avatar = "http://avatar.url"
    m.mention = f"<@{user_id}>"
    m.name = name
    return m


@pytest.fixture
def bot():
    bot_mock = AsyncMock()
    bot_mock.user.id = 12345
    log_channel = MagicMock()
    log_channel.send = AsyncMock()
    bot_mock.get_channel = MagicMock(return_value=log_channel)
    return bot_mock


@pytest.fixture
def tracker(bot):
    return RolesTracker(bot)


@pytest.fixture
def guild():
    g = MagicMock()
    g.id = 999

    quarantine = MagicMock(id=config.ROLES["quarantine"], name="Quarantine")
    dvp = MagicMock(id=config.ROLES["dvp"], name="DVP")
    ai = MagicMock(id=config.ROLES["ai"], name="Ai")
    server_booster = MagicMock(id=config.ROLES["server_booster"], name="Booster")

    def get_role_mock(role_id):
        if role_id == config.ROLES["quarantine"]: return quarantine
        if role_id == config.ROLES["dvp"]: return dvp
        if role_id == config.ROLES["ai"]: return ai
        if role_id == config.ROLES["server_booster"]: return server_booster
        return None

    g.get_role.side_effect = get_role_mock
    g.default_role = MagicMock(
        permissions=MagicMock(administrator=False),
        color=disnake.Color.default(),
        hoist=False,
        mentionable=False
    )
    g.create_role = AsyncMock()
    return g


@pytest.fixture
def role(guild):
    r = AsyncMock()
    r.guild = guild
    r.name = "TestRole"
    r.managed = False
    r.permissions = MagicMock(administrator=False)
    r.color = disnake.Color.default()
    r.hoist = False
    r.mentionable = False
    r.mention = "<@&555>"
    return r


@pytest.mark.asyncio
class TestRolesTracker:
    # -------------------------------------------------------------------------------------- #
    # on_guild_role_create
    # -------------------------------------------------------------------------------------- #

    async def test_role_create_unauthorized_user_quarantined(self, tracker, guild, role, bot):
        member = create_mock_member(is_bot=False)
        entry = MagicMock(user=member)
        guild.audit_logs = MagicMock(return_value=AsyncIteratorMock([entry]))

        await tracker.on_guild_role_create(role)

        role.delete.assert_called_once()
        member.edit.assert_called_once_with(roles=[guild.get_role(config.ROLES["quarantine"])])
        bot.get_channel.assert_called_with(config.LOG_CHANNELS["role_updates"])
        bot.get_channel().send.assert_called_once()

    async def test_role_create_authorized_dvp_user(self, tracker, guild, role, bot):
        dvp_role = guild.get_role(config.ROLES["dvp"])
        member = create_mock_member(is_bot=False, roles=[dvp_role])
        entry = MagicMock(user=member)
        guild.audit_logs = MagicMock(return_value=AsyncIteratorMock([entry]))

        await tracker.on_guild_role_create(role)

        role.delete.assert_not_called()
        member.edit.assert_not_called()
        bot.get_channel.assert_called_with(config.LOG_CHANNELS["role_updates"])
        bot.get_channel().send.assert_called_once()

    async def test_role_create_bot_with_ai_role(self, tracker, guild, role, bot):
        ai_role = MagicMock()
        ai_role.name = "Ai"
        member = create_mock_member(is_bot=True, roles=[ai_role])
        entry = MagicMock(user=member)
        guild.audit_logs = MagicMock(return_value=AsyncIteratorMock([entry]))

        await tracker.on_guild_role_create(role)

        role.delete.assert_not_called()
        member.ban.assert_not_called()
        bot.get_channel().send.assert_called_once()

    async def test_role_create_bot_without_ai_role(self, tracker, guild, role, bot):
        member = create_mock_member(is_bot=True, roles=[])
        entry = MagicMock(user=member)
        guild.audit_logs = MagicMock(return_value=AsyncIteratorMock([entry]))

        await tracker.on_guild_role_create(role)

        role.delete.assert_called_once()
        member.ban.assert_called_once_with(reason="Role Created without AI")
        bot.get_channel().send.assert_called_once()

    async def test_role_create_owner_with_dvp_bypassed(self, tracker, guild, role, bot):
        dvp_role = guild.get_role(config.ROLES["dvp"])
        member = create_mock_member(is_bot=False, roles=[dvp_role], user_id=config.OWNER_ID)
        entry = MagicMock(user=member)
        guild.audit_logs = MagicMock(return_value=AsyncIteratorMock([entry]))

        await tracker.on_guild_role_create(role)

        role.delete.assert_not_called()
        bot.get_channel().send.assert_called_once()

    # -------------------------------------------------------------------------------------- #
    # on_guild_role_delete
    # -------------------------------------------------------------------------------------- #

    async def test_role_delete_unauthorized_user_quarantined_and_restored(self, tracker, guild, role, bot):
        member = create_mock_member(is_bot=False)
        entry = MagicMock(user=member)
        guild.audit_logs = MagicMock(return_value=AsyncIteratorMock([entry]))

        new_role_mock = MagicMock(mention="<@&556>")
        guild.create_role.return_value = new_role_mock

        await tracker.on_guild_role_delete(role)

        guild.create_role.assert_called_once_with(
            name=role.name, color=role.color,
            hoist=role.hoist, mentionable=role.mentionable,
            reason=f'Recreated role "{role.name}" after deletion by {member.name}'
        )
        member.edit.assert_called_once_with(roles=[guild.get_role(config.ROLES["quarantine"])])
        bot.get_channel().send.assert_called_once()

    async def test_role_delete_authorized_dvp_user(self, tracker, guild, role, bot):
        dvp_role = guild.get_role(config.ROLES["dvp"])
        member = create_mock_member(is_bot=False, roles=[dvp_role])
        entry = MagicMock(user=member)
        guild.audit_logs = MagicMock(return_value=AsyncIteratorMock([entry]))

        await tracker.on_guild_role_delete(role)

        guild.create_role.assert_not_called()
        member.edit.assert_not_called()
        bot.get_channel().send.assert_called_once()

    async def test_role_delete_managed_role_ignored(self, tracker, guild, role, bot):
        role.managed = True
        member = create_mock_member(is_bot=False)
        entry = MagicMock(user=member)
        guild.audit_logs = MagicMock(return_value=AsyncIteratorMock([entry]))

        await tracker.on_guild_role_delete(role)

        bot.get_channel.assert_not_called()

    async def test_role_delete_bot_with_ai(self, tracker, guild, role, bot):
        ai_role = MagicMock()
        ai_role.name = "Ai"
        member = create_mock_member(is_bot=True, roles=[ai_role])
        entry = MagicMock(user=member)
        guild.audit_logs = MagicMock(return_value=AsyncIteratorMock([entry]))

        await tracker.on_guild_role_delete(role)

        member.ban.assert_not_called()
        bot.get_channel().send.assert_called_once()

    async def test_role_delete_bot_without_ai_banned(self, tracker, guild, role, bot):
        member = create_mock_member(is_bot=True, roles=[])
        entry = MagicMock(user=member)
        guild.audit_logs = MagicMock(return_value=AsyncIteratorMock([entry]))

        await tracker.on_guild_role_delete(role)

        member.ban.assert_called_once_with(reason="Role Deleted without AI")
        bot.get_channel().send.assert_called_once()

    # -------------------------------------------------------------------------------------- #
    # on_guild_role_update
    # -------------------------------------------------------------------------------------- #

    async def test_role_update_admin_escalation_unauthorized(self, tracker, guild, role, bot):
        member = create_mock_member(is_bot=False)
        entry = MagicMock(user=member)
        guild.audit_logs = MagicMock(return_value=AsyncIteratorMock([entry]))

        before = MagicMock()
        before.permissions = MagicMock(administrator=False)
        before.guild = guild

        after = AsyncMock()
        after.guild = guild
        after.permissions = MagicMock(administrator=True)
        after.name = "TestRole"
        after.color = role.color

        await tracker.on_guild_role_update(before, after)

        after.edit.assert_called_once_with(
            name=after.name, permissions=guild.default_role.permissions,
            color=after.color, hoist=guild.default_role.hoist,
            mentionable=guild.default_role.mentionable
        )
        member.edit.assert_called_once_with(roles=[guild.get_role(config.ROLES["quarantine"])])
        assert bot.get_channel().send.call_count == 1

    async def test_role_update_admin_escalation_authorized(self, tracker, guild, role, bot):
        dvp_role = guild.get_role(config.ROLES["dvp"])
        member = create_mock_member(is_bot=False, roles=[dvp_role])
        entry = MagicMock(user=member)
        guild.audit_logs = MagicMock(return_value=AsyncIteratorMock([entry]))

        before = MagicMock()
        before.permissions = MagicMock(administrator=False)

        after = AsyncMock()
        after.guild = guild
        after.permissions = MagicMock(administrator=True)

        await tracker.on_guild_role_update(before, after)

        after.edit.assert_not_called()
        member.edit.assert_not_called()
        bot.get_channel().send.assert_called_once()

    async def test_role_update_non_admin_change_ignored(self, tracker, guild, role, bot):
        before = MagicMock()
        before.permissions = MagicMock(administrator=False)

        after = MagicMock()
        after.permissions = MagicMock(administrator=False)

        await tracker.on_guild_role_update(before, after)

        bot.get_channel.assert_not_called()

    # -------------------------------------------------------------------------------------- #
    # on_member_update (role assignment/removal)
    # -------------------------------------------------------------------------------------- #

    async def test_role_added_admin_role_by_non_dvp(self, tracker, guild, bot):
        target_member = create_mock_member()
        target_member.guild = guild

        admin_role = MagicMock()
        admin_role.permissions.administrator = True

        before = MagicMock()
        before.roles = []
        after = target_member
        after.roles = [admin_role]

        assigning_user = create_mock_member(roles=[])
        entry = MagicMock()
        entry.target.id = after.id
        entry.user = assigning_user
        entry.user.id = 999
        entry.changes.before.roles = []
        entry.changes.after.roles = [admin_role]

        guild.audit_logs = MagicMock(return_value=AsyncIteratorMock([entry]))

        await tracker.on_member_update(before, after)

        assigning_user.edit.assert_called_once_with(roles=[guild.get_role(config.ROLES["quarantine"])])
        after.remove_roles.assert_called_once_with(admin_role)
        bot.get_channel().send.assert_called_once()

    async def test_role_added_admin_role_by_dvp(self, tracker, guild, bot):
        target_member = create_mock_member()
        target_member.guild = guild

        admin_role = MagicMock()
        admin_role.permissions.administrator = True

        before = MagicMock()
        before.roles = []
        after = target_member
        after.roles = [admin_role]

        dvp_role = guild.get_role(config.ROLES["dvp"])
        assigning_user = create_mock_member(roles=[dvp_role])
        entry = MagicMock()
        entry.target.id = after.id
        entry.user = assigning_user
        entry.user.id = 999
        entry.changes.before.roles = []
        entry.changes.after.roles = [admin_role]

        guild.audit_logs = MagicMock(return_value=AsyncIteratorMock([entry]))

        await tracker.on_member_update(before, after)

        assigning_user.edit.assert_not_called()
        after.remove_roles.assert_not_called()
        bot.get_channel().send.assert_called_once()

    async def test_role_added_non_admin_role_logged(self, tracker, guild, bot):
        target_member = create_mock_member()
        target_member.guild = guild

        normal_role = MagicMock()
        normal_role.permissions.administrator = False

        before = MagicMock()
        before.roles = []
        after = target_member
        after.roles = [normal_role]

        assigning_user = create_mock_member()
        entry = MagicMock()
        entry.target.id = after.id
        entry.user = assigning_user
        entry.user.id = 999
        entry.changes.before.roles = []
        entry.changes.after.roles = [normal_role]

        guild.audit_logs = MagicMock(return_value=AsyncIteratorMock([entry]))

        await tracker.on_member_update(before, after)

        bot.get_channel().send.assert_called_once()

    async def test_role_removed_ai_by_non_dvp(self, tracker, guild, bot):
        target_member = create_mock_member()
        target_member.guild = guild

        ai_role = MagicMock()
        ai_role.name = "Ai"

        before = MagicMock()
        before.roles = [ai_role]
        after = target_member
        after.roles = []

        removing_user = create_mock_member(roles=[])
        entry = MagicMock()
        entry.target.id = after.id
        entry.user = removing_user
        entry.user.id = 999
        entry.changes.before.roles = [ai_role]
        entry.changes.after.roles = []

        guild.audit_logs = MagicMock(return_value=AsyncIteratorMock([entry]))

        await tracker.on_member_update(before, after)

        removing_user.edit.assert_called_once_with(roles=[guild.get_role(config.ROLES["quarantine"])])
        after.add_roles.assert_called_once_with(guild.get_role(config.ROLES["ai"]))
        bot.get_channel().send.assert_called_once()

    async def test_role_removed_ai_by_dvp(self, tracker, guild, bot):
        target_member = create_mock_member()
        target_member.guild = guild

        ai_role = MagicMock()
        ai_role.name = "Ai"

        before = MagicMock()
        before.roles = [ai_role]
        after = target_member
        after.roles = []

        dvp_role = guild.get_role(config.ROLES["dvp"])
        removing_user = create_mock_member(roles=[dvp_role])
        entry = MagicMock()
        entry.target.id = after.id
        entry.user = removing_user
        entry.user.id = 999
        entry.changes.before.roles = [ai_role]
        entry.changes.after.roles = []

        guild.audit_logs = MagicMock(return_value=AsyncIteratorMock([entry]))

        await tracker.on_member_update(before, after)

        removing_user.edit.assert_not_called()
        after.add_roles.assert_not_called()
        bot.get_channel().send.assert_called_once()

    async def test_role_removed_regular_role_logged(self, tracker, guild, bot):
        target_member = create_mock_member()
        target_member.guild = guild

        normal_role = MagicMock()
        normal_role.name = "Regular"

        before = MagicMock()
        before.roles = [normal_role]
        after = target_member
        after.roles = []

        removing_user = create_mock_member()
        entry = MagicMock()
        entry.target.id = after.id
        entry.user = removing_user
        entry.user.id = 999
        entry.changes.before.roles = [normal_role]
        entry.changes.after.roles = []

        guild.audit_logs = MagicMock(return_value=AsyncIteratorMock([entry]))

        await tracker.on_member_update(before, after)

        bot.get_channel().send.assert_called_once()

    async def test_role_update_by_bot_itself_ignored(self, tracker, guild, bot):
        target_member = create_mock_member()
        target_member.guild = guild

        normal_role = MagicMock()
        normal_role.name = "Regular"

        before = MagicMock()
        before.roles = []
        after = target_member
        after.roles = [normal_role]

        entry = MagicMock()
        entry.target.id = after.id
        entry.user.id = bot.user.id
        entry.changes.before.roles = []
        entry.changes.after.roles = [normal_role]

        guild.audit_logs = MagicMock(return_value=AsyncIteratorMock([entry]))

        await tracker.on_member_update(before, after)

        bot.get_channel.assert_not_called()
