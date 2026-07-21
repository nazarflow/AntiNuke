import pytest
import disnake
from unittest.mock import AsyncMock, MagicMock, patch
from src.events.webhooks.webhooks_tracker import WebhooksTracker
import config


@pytest.fixture
def bot():
    bot_mock = AsyncMock()
    log_channel = MagicMock()
    log_channel.send = AsyncMock()
    bot_mock.get_channel = MagicMock(return_value=log_channel)
    return bot_mock


@pytest.fixture
def tracker(bot):
    return WebhooksTracker(bot)


@pytest.fixture
def mock_channel():
    channel = AsyncMock()
    channel.guild = MagicMock()
    channel.guild.ban = AsyncMock()
    channel.mention = "#test-channel"

    quarantine_role = MagicMock(id=config.ROLES["quarantine"])
    server_booster_role = MagicMock(id=config.ROLES["server_booster"])

    def get_role_side_effect(role_id):
        if role_id == config.ROLES["quarantine"]:
            return quarantine_role
        if role_id == config.ROLES["server_booster"]:
            return server_booster_role
        return None

    channel.guild.get_role.side_effect = get_role_side_effect
    return channel


class TestWebhooksTracker:
    """Tests for WebhooksTracker event handler.

    NOTE: The production code in webhooks_tracker.py has a specific flow:
    - If webhook.user exists AND member is found AND member has no dvp role:
      -> quarantine + delete webhook, then FALLS THROUGH to lines 46-56 (second delete attempt)
    - If webhook.user exists AND (member not found OR member has dvp):
      -> sends authorized embed + returns from loop iteration
    - After the if/else block, checks webhook.user.bot for ban logic
    """

    @pytest.mark.asyncio
    @patch("src.embeds.webhooks.webhook_created_punish")
    async def test_webhook_non_dvp_member_quarantined(self, mock_embed, tracker, mock_channel, bot):
        """Non-DVP member creates webhook -> quarantined, webhook deleted (twice due to fall-through)."""
        webhook = AsyncMock()
        webhook.user = MagicMock(id=123, bot=False)
        mock_channel.webhooks.return_value = [webhook]

        member = AsyncMock()
        member.roles = []
        member.mention = "<@123>"
        member.avatar = "http://avatar.url"
        mock_channel.guild.get_member.return_value = member

        log_channel = bot.get_channel.return_value

        await tracker.on_webhooks_update(mock_channel)

        member.edit.assert_awaited_once()
        log_channel.send.assert_awaited_once()
        # webhook.delete() is called twice in prod code: once in quarantine block, once in fallthrough else
        assert webhook.delete.await_count == 2

    @pytest.mark.asyncio
    @patch("src.embeds.webhooks.webhook_created_authorized")
    async def test_webhook_dvp_member_authorized(self, mock_embed, tracker, mock_channel, bot):
        """DVP member creates webhook -> authorized embed sent, returns early."""
        webhook = AsyncMock()
        webhook.user = MagicMock(id=123, bot=False)
        mock_channel.webhooks.return_value = [webhook]

        member = AsyncMock()
        dvp_role = MagicMock(id=config.ROLES["dvp"])
        member.roles = [dvp_role]
        member.mention = "<@123>"
        mock_channel.guild.get_member.return_value = member

        log_channel = bot.get_channel.return_value

        await tracker.on_webhooks_update(mock_channel)

        member.edit.assert_not_awaited()
        log_channel.send.assert_awaited_once()
        webhook.delete.assert_not_awaited()

    @pytest.mark.asyncio
    @patch("src.embeds.webhooks.webhook_created_punish")
    async def test_webhook_booster_preserves_role(self, mock_embed, tracker, mock_channel, bot):
        """Non-DVP member with server_booster -> quarantined with booster preserved."""
        webhook = AsyncMock()
        webhook.user = MagicMock(id=123, bot=False)
        mock_channel.webhooks.return_value = [webhook]

        member = AsyncMock()
        booster_role = MagicMock(id=config.ROLES["server_booster"])
        member.roles = [booster_role]
        member.mention = "<@123>"
        member.avatar = "http://avatar.url"
        mock_channel.guild.get_member.return_value = member

        quarantine_role = mock_channel.guild.get_role(config.ROLES["quarantine"])
        server_booster_role = mock_channel.guild.get_role(config.ROLES["server_booster"])

        await tracker.on_webhooks_update(mock_channel)

        member.edit.assert_awaited_once_with(
            roles=[quarantine_role, server_booster_role],
            reason="User moved to quarantine."
        )

    @pytest.mark.asyncio
    async def test_webhook_bot_creator_banned(self, tracker, mock_channel, bot):
        """Bot creates webhook, member not found -> falls to else block (authorized embed).

        NOTE: In production code, when member is None and webhook.user.bot is True,
        the code first hits the else branch (line 42) calling webhook_created_authorized(None, channel)
        which would crash. This test documents this edge case in the actual source code behavior.
        The bot ban logic on line 46 is only reachable AFTER the if/else block on line 27.
        When member is None, the `if member and ...` is False, so it goes to else on line 42.
        """
        webhook = AsyncMock()
        webhook.user = MagicMock(id=123, bot=True)
        webhook.user.mention = "<@123>"
        mock_channel.webhooks.return_value = [webhook]

        # When member is found and is bot, no dvp -> quarantine block handles it
        # But the ban path on line 46 is also reachable after quarantine block
        # Let's test the path where member IS found (as a non-dvp bot member)
        member = AsyncMock()
        member.roles = []
        member.mention = "<@123>"
        member.avatar = "http://avatar.url"
        mock_channel.guild.get_member.return_value = member

        with patch("src.embeds.webhooks.webhook_created_punish"):
            await tracker.on_webhooks_update(mock_channel)

        # Bot gets banned via line 47 (after falling through from quarantine block)
        mock_channel.guild.ban.assert_awaited_once_with(webhook.user, reason="Webhook created by a bot")

    @pytest.mark.asyncio
    @patch("src.embeds.webhooks.webhook_created_punish")
    async def test_webhook_delete_not_found_handled(self, mock_embed, tracker, mock_channel, bot):
        """webhook.delete() raises NotFound -> handled gracefully without crash."""
        webhook = AsyncMock()
        webhook.user = MagicMock(id=123, bot=False)
        webhook.delete.side_effect = disnake.errors.NotFound(MagicMock(), MagicMock())
        mock_channel.webhooks.return_value = [webhook]

        member = AsyncMock()
        member.roles = []
        member.mention = "<@123>"
        member.avatar = "http://avatar.url"
        mock_channel.guild.get_member.return_value = member

        # Should not raise despite NotFound
        await tracker.on_webhooks_update(mock_channel)
        assert webhook.delete.await_count >= 1

    @pytest.mark.asyncio
    async def test_webhook_no_user_attribute(self, tracker, mock_channel):
        """webhook.user is None -> skips user block, falls to else -> deletes webhook."""
        webhook = AsyncMock()
        webhook.user = None
        mock_channel.webhooks.return_value = [webhook]

        await tracker.on_webhooks_update(mock_channel)

        # webhook.user is None -> line 24 is False, line 46 is False -> else on line 52 -> delete
        webhook.delete.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("src.embeds.webhooks.webhook_created_authorized")
    async def test_webhook_member_not_in_guild(self, mock_embed, tracker, mock_channel, bot):
        """guild.get_member returns None -> else branch calls webhook_created_authorized(None, channel) and returns.

        NOTE: In unpatched production code, this would crash because member is None
        and webhook_created_authorized() tries to access member.mention.
        This test documents the bug by verifying the else branch is reached with member=None.
        """
        webhook = AsyncMock()
        webhook.user = MagicMock(id=123, bot=False)
        mock_channel.webhooks.return_value = [webhook]
        mock_channel.guild.get_member.return_value = None

        log_channel = bot.get_channel.return_value

        await tracker.on_webhooks_update(mock_channel)

        # The else branch on line 42 was taken because `if member and ...` is False when member is None
        mock_embed.assert_called_once_with(None, mock_channel)
        log_channel.send.assert_awaited_once()
        # Returns early from the loop due to `return` on line 44
        webhook.delete.assert_not_awaited()

    @pytest.mark.asyncio
    @patch("src.embeds.webhooks.webhook_created_authorized")
    async def test_webhook_owner_with_dvp_authorized(self, mock_embed, tracker, mock_channel, bot):
        """OWNER_ID with DVP role -> authorized embed, no quarantine."""
        webhook = AsyncMock()
        webhook.user = MagicMock(id=config.OWNER_ID, bot=False)
        mock_channel.webhooks.return_value = [webhook]

        member = AsyncMock()
        dvp_role = MagicMock(id=config.ROLES["dvp"])
        member.roles = [dvp_role]
        member.mention = f"<@{config.OWNER_ID}>"
        mock_channel.guild.get_member.return_value = member

        await tracker.on_webhooks_update(mock_channel)

        member.edit.assert_not_awaited()
        webhook.delete.assert_not_awaited()
