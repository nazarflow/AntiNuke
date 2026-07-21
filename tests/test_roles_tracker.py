import pytest
import disnake
from unittest.mock import AsyncMock, MagicMock, patch
from src.events.roles.roles_tracker import RolesTracker

GUILD_ID = 123456
AUTHOR_ID = 654321

@pytest.fixture
def mock_bot():
    bot = MagicMock()
    bot.get_channel = MagicMock(return_value=AsyncMock())
    return bot

@pytest.fixture
def mock_role():
    role = AsyncMock()
    role.guild.id = GUILD_ID
    role.id = 111111
    role.name = "test-role"
    
    # Mock audit logs for creation
    mock_entry = MagicMock()
    
    mock_member = AsyncMock()
    mock_member.roles = []
    mock_member.id = AUTHOR_ID
    mock_member.bot = False
    mock_entry.user = mock_member
    
    # Async flatten for audit logs
    mock_audit = AsyncMock()
    mock_audit.flatten = AsyncMock(return_value=[mock_entry])
    role.guild.audit_logs = MagicMock(return_value=mock_audit)
    
    return role


@pytest.mark.asyncio
async def test_on_role_create_limit_exceeded(mock_bot, mock_role):
    tracker = RolesTracker(mock_bot)
    
    with patch("src.events.roles.roles_tracker.config_service") as mock_config_service, \
         patch("src.events.roles.roles_tracker.admin_service") as mock_admin_service, \
         patch("src.events.roles.roles_tracker.limiter") as mock_limiter:
        
        # Setup mocks
        mock_config_service.get_log_channel = AsyncMock(return_value=None)
        mock_config_service.get_role_id = AsyncMock(return_value=None)
        
        mock_admin_service.is_server_owner = AsyncMock(return_value=False)
        mock_limiter.check_limit = AsyncMock(return_value=False) # Exceeds limit!
        
        await tracker.on_guild_role_create(mock_role)
        
        # Verify spam was detected and role was deleted
        mock_limiter.add_action.assert_called_once_with(GUILD_ID, AUTHOR_ID, "roles")
        mock_limiter.check_limit.assert_called_once()
        mock_role.delete.assert_called_once()
