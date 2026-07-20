import pytest
import disnake
from unittest.mock import AsyncMock, MagicMock, patch
from src.events.webhooks.webhooks_tracker import WebhooksTracker

GUILD_ID = 123456
AUTHOR_ID = 654321

@pytest.fixture
def mock_bot():
    bot = MagicMock()
    bot.get_channel = MagicMock(return_value=AsyncMock())
    return bot

@pytest.fixture
def mock_channel():
    channel = AsyncMock()
    channel.guild.id = GUILD_ID
    
    # Mock webhook
    mock_webhook = AsyncMock()
    mock_webhook.user.id = AUTHOR_ID
    mock_webhook.user.bot = False
    
    channel.webhooks = AsyncMock(return_value=[mock_webhook])
    
    # Mock member
    mock_member = AsyncMock()
    mock_member.roles = []
    mock_member.id = AUTHOR_ID
    channel.guild.get_member = MagicMock(return_value=mock_member)
    
    return channel


@pytest.mark.asyncio
async def test_on_webhooks_update_limit_exceeded(mock_bot, mock_channel):
    tracker = WebhooksTracker(mock_bot)
    
    with patch("src.events.webhooks.webhooks_tracker.config_service") as mock_config_service, \
         patch("src.events.webhooks.webhooks_tracker.admin_service") as mock_admin_service, \
         patch("src.events.webhooks.webhooks_tracker.limiter") as mock_limiter:
        
        # Setup mocks
        mock_config_service.get_log_channel = AsyncMock(return_value=None)
        mock_config_service.get_role_id = AsyncMock(return_value=None)
        
        mock_admin_service.is_server_owner = AsyncMock(return_value=False)
        mock_limiter.check_limit = AsyncMock(return_value=False) # Exceeds limit!
        
        await tracker.on_webhooks_update(mock_channel)
        
        # Verify spam was detected and webhook was deleted
        mock_limiter.add_action.assert_called_once_with(GUILD_ID, AUTHOR_ID, "webhooks")
        mock_limiter.check_limit.assert_called_once()
        
        webhooks = await mock_channel.webhooks()
        webhooks[0].delete.assert_called()
