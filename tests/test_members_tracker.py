import pytest
import disnake
from unittest.mock import AsyncMock, MagicMock, patch
from src.events.members.members_tracker import MembersTracker

GUILD_ID = 123456
AUTHOR_ID = 654321

@pytest.fixture
def mock_bot():
    bot = MagicMock()
    bot.get_channel = MagicMock(return_value=AsyncMock())
    bot.user_ids = []
    return bot

@pytest.fixture
def mock_member():
    member = AsyncMock()
    member.guild.id = GUILD_ID
    member.id = 111111
    member.bot = True
    
    # Mock audit logs for bot add
    mock_entry = MagicMock()
    mock_entry.target.id = member.id
    
    mock_user = AsyncMock()
    mock_user.id = AUTHOR_ID
    mock_entry.user = mock_user
    
    # Async generator for audit logs
    async def mock_audit_logs(*args, **kwargs):
        yield mock_entry
    
    member.guild.audit_logs = mock_audit_logs
    
    return member


@pytest.mark.asyncio
async def test_on_member_join_unauthorized_bot(mock_bot, mock_member):
    tracker = MembersTracker(mock_bot)
    
    with patch("src.events.members.members_tracker.config_service") as mock_config_service, \
         patch("src.events.members.members_tracker.admin_service") as mock_admin_service:
        
        # Setup mocks
        mock_config_service.get_log_channel = AsyncMock(return_value=None)
        mock_config_service.get_role_id = AsyncMock(return_value=None)
        
        mock_admin_service.is_server_owner = AsyncMock(return_value=False)
        
        await tracker.on_member_join(mock_member)
        
        # Verify the bot was banned
        mock_member.ban.assert_called_once_with(reason="Unauthorized Bot")
