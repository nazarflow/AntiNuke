import pytest
import disnake
from unittest.mock import AsyncMock, MagicMock, patch
from src.events.channels.channels_tracker import ChannelsTracker

GUILD_ID = 123456
AUTHOR_ID = 654321
OWNER_ID = 999999

@pytest.fixture
def mock_bot():
    bot = MagicMock()
    bot.get_channel = MagicMock(return_value=AsyncMock())
    return bot

@pytest.fixture
def mock_channel():
    channel = AsyncMock()
    channel.guild.id = GUILD_ID
    channel.id = 111111
    import datetime
    dt = datetime.datetime.now()
    channel.created_at = dt
    
    # Mock audit logs for creation
    mock_entry = MagicMock()
    mock_entry.created_at = dt
    
    mock_user = AsyncMock()
    mock_user.id = AUTHOR_ID
    mock_user.bot = False
    mock_user.roles = []
    mock_entry.user = mock_user
    
    # Async generator for audit logs
    async def mock_audit_logs(*args, **kwargs):
        yield mock_entry
    
    channel.guild.audit_logs = mock_audit_logs
    
    # Mock member
    channel.guild.get_member = MagicMock(return_value=mock_user)
    
    return channel


@pytest.mark.asyncio
async def test_on_channel_create_limit_exceeded(mock_bot, mock_channel):
    tracker = ChannelsTracker(mock_bot)
    
    with patch("src.events.channels.channels_tracker.config_service") as mock_config_service, \
         patch("src.events.channels.channels_tracker.admin_service") as mock_admin_service, \
         patch("src.events.channels.channels_tracker.limiter") as mock_limiter:
        
        # Setup mocks
        mock_config_service.get_log_channel = AsyncMock(return_value=None)
        mock_config_service.get_role_id = AsyncMock(return_value=None)
        
        mock_admin_service.is_server_owner = AsyncMock(return_value=False)
        mock_limiter.check_limit = AsyncMock(return_value=False) # Exceeds limit!
        
        await tracker.on_guild_channel_create(mock_channel)
        
        # Verify spam was detected and channel was deleted
        mock_limiter.add_action.assert_called_once_with(GUILD_ID, AUTHOR_ID, "channels")
        mock_limiter.check_limit.assert_called_once()
        mock_channel.delete.assert_called_once()
