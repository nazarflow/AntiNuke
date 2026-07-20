# tests/test_events.py
import pytest
import disnake
from unittest.mock import AsyncMock, MagicMock, patch
from src.events.messages.messages_tracker import MessagesTracker

GUILD_ID = 123456
AUTHOR_ID = 654321

@pytest.fixture
def mock_bot():
    bot = MagicMock()
    bot.get_channel = MagicMock(return_value=AsyncMock())
    bot.process_commands = AsyncMock()
    return bot

@pytest.fixture
def mock_message():
    msg = AsyncMock()
    msg.content = "Hello @everyone"
    msg.author.id = AUTHOR_ID
    msg.guild.id = GUILD_ID
    msg.webhook_id = None
    
    # Mock member and roles
    mock_member = MagicMock()
    mock_member.roles = []
    msg.guild.get_member = MagicMock(return_value=mock_member)
    
    return msg

@pytest.mark.asyncio
async def test_on_message_spam_detection(mock_bot, mock_message):
    tracker = MessagesTracker(mock_bot)
    
    with patch("src.events.messages.messages_tracker.config_service") as mock_config_service, \
         patch("src.events.messages.messages_tracker.admin_service") as mock_admin_service, \
         patch("src.events.messages.messages_tracker.limiter") as mock_limiter:
        
        # Setup mocks
        mock_config_service.get_log_channel = AsyncMock(return_value=None)
        mock_config_service.get_role_id = AsyncMock(return_value=None)
        mock_admin_service.is_server_owner = AsyncMock(return_value=False)
        mock_limiter.check_limit = AsyncMock(return_value=False) # Exceeds limit!
        
        await tracker.on_message(mock_message)
        
        # Verify spam was detected and limiter was called
        mock_limiter.add_action.assert_called_once_with(GUILD_ID, AUTHOR_ID, "links")
        mock_limiter.check_limit.assert_called_once()
        mock_message.delete.assert_called_once()

@pytest.mark.asyncio
async def test_on_message_edit_logging(mock_bot):
    tracker = MessagesTracker(mock_bot)
    
    before = MagicMock()
    before.content = "Old"
    before.guild.id = GUILD_ID
    
    after = MagicMock()
    after.content = "New"
    
    with patch("src.events.messages.messages_tracker.config_service") as mock_config_service:
        mock_config_service.get_log_channel = AsyncMock(return_value=999)
        mock_channel = AsyncMock()
        mock_bot.get_channel.return_value = mock_channel
        
        await tracker.on_message_edit(before, after)
        
        # Verify log channel was fetched and message was sent
        mock_config_service.get_log_channel.assert_called_once_with(GUILD_ID, "message_edit_delete")
        mock_bot.get_channel.assert_called_once_with(999)
        mock_channel.send.assert_called_once()
