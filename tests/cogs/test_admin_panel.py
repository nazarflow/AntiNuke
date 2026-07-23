import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import disnake
from src.cogs.admin_panel import (
    AdminPanelView,
    CreateAdminRoleModal,
    RemoveAdminRoleModal,
    EditAdminRoleLimitsModal,
    CreateAdminUserModal,
    RemoveAdminUserModal,
    EditAdminUserLimitsModal,
    AddTrustedUserModal,
    RemoveTrustedUserModal
)
import config

@pytest.mark.asyncio
@patch("src.cogs.admin_panel.admin_service")
async def test_admin_panel_view_access(mock_admin_service, mock_inter):
    view = AdminPanelView()
    
    # Not owner, not server owner
    mock_inter.author.id = 12345
    config.OWNER_ID = 999999
    mock_admin_service.is_server_owner = AsyncMock(return_value=False)
    
    result = await view.interaction_check(mock_inter)
    assert result is False
    mock_inter.response.send_message.assert_called_once_with("⛔ Only owners can use this panel.", ephemeral=True)
    
    # Server owner
    mock_inter.response.send_message.reset_mock()
    mock_admin_service.is_server_owner = AsyncMock(return_value=True)
    result = await view.interaction_check(mock_inter)
    assert result is True
    mock_inter.response.send_message.assert_not_called()

@pytest.mark.asyncio
@patch("src.cogs.admin_panel.admin_service")
async def test_create_admin_role_modal(mock_admin_service, mock_modal_inter):
    modal = CreateAdminRoleModal()
    mock_modal_inter.text_values = {
        "role_name": "TestDVP",
        "channels_limits": "5 10",
        "roles_limits": "3 60",
        "links_limits": "10", # Implicit 60
        "webhooks_limits": "invalid" # Implicit 0, 0
    }
    
    mock_role = MagicMock(spec=disnake.Role)
    mock_role.id = 777
    mock_role.mention = "<@&777>"
    mock_modal_inter.guild.create_role = AsyncMock(return_value=mock_role)
    mock_admin_service.save_custom_role_limits = AsyncMock()
    
    await modal.callback(mock_modal_inter)
    
    mock_modal_inter.response.defer.assert_called_once()
    mock_modal_inter.guild.create_role.assert_called_once_with(name="TestDVP", reason="Created via Admin Panel")
    mock_admin_service.save_custom_role_limits.assert_called_once_with(
        777, mock_modal_inter.guild.id,
        channels_limit=5, channels_time=10,
        roles_limit=3, roles_time=60,
        links_limit=10, links_time=60,
        webhooks_limit=0, webhooks_time=0
    )

@pytest.mark.asyncio
@patch("src.cogs.admin_panel.admin_service")
async def test_remove_admin_role_modal(mock_admin_service, mock_modal_inter):
    modal = RemoveAdminRoleModal()
    mock_modal_inter.text_values = {"role_id": "777"}
    
    mock_role = MagicMock(spec=disnake.Role)
    mock_role.delete = AsyncMock()
    mock_modal_inter.guild.get_role.return_value = mock_role
    mock_admin_service.delete_custom_role_limits = AsyncMock(return_value=1)
    
    await modal.callback(mock_modal_inter)
    
    mock_admin_service.delete_custom_role_limits.assert_called_once_with(777)
    mock_role.delete.assert_called_once()
    mock_modal_inter.response.send_message.assert_called_once()
    args, kwargs = mock_modal_inter.response.send_message.call_args
    content = args[0] if args else kwargs.get("content", "")
    assert "removed from DB" in content

@pytest.mark.asyncio
@patch("src.cogs.admin_panel.admin_service")
async def test_create_admin_user_modal(mock_admin_service, mock_modal_inter):
    modal = CreateAdminUserModal()
    mock_modal_inter.text_values = {
        "user_id": "888",
        "channels_limits": "1 2",
        "roles_limits": "3 4",
        "links_limits": "5 6",
        "webhooks_limits": "7 8"
    }
    mock_admin_service.save_custom_user_limits = AsyncMock()
    
    await modal.callback(mock_modal_inter)
    
    mock_admin_service.save_custom_user_limits.assert_called_once_with(
        888, mock_modal_inter.guild.id,
        channels_limit=1, channels_time=2,
        roles_limit=3, roles_time=4,
        links_limit=5, links_time=6,
        webhooks_limit=7, webhooks_time=8
    )
    mock_modal_inter.response.send_message.assert_called_once()

@pytest.mark.asyncio
@patch("src.cogs.admin_panel.admin_service")
async def test_add_trusted_user_modal(mock_admin_service, mock_modal_inter):
    modal = AddTrustedUserModal()
    mock_modal_inter.text_values = {"user_id": "12345"}
    mock_modal_inter.bot.user_ids = []
    mock_admin_service.add_tracked_user = AsyncMock()
    
    await modal.callback(mock_modal_inter)
    
    assert 12345 in mock_modal_inter.bot.user_ids
    mock_admin_service.add_tracked_user.assert_called_once_with(12345)
    mock_modal_inter.response.send_message.assert_called_once()
    args, kwargs = mock_modal_inter.response.send_message.call_args
    content = args[0] if args else kwargs.get("content", "")
    assert "added to trusted list" in content

@pytest.mark.asyncio
@patch("src.cogs.admin_panel.admin_service")
async def test_remove_trusted_user_modal(mock_admin_service, mock_modal_inter):
    modal = RemoveTrustedUserModal()
    mock_modal_inter.text_values = {"user_id": "12345"}
    mock_modal_inter.bot.user_ids = [12345]
    mock_admin_service.remove_tracked_user = AsyncMock()
    
    await modal.callback(mock_modal_inter)
    
    assert 12345 not in mock_modal_inter.bot.user_ids
    mock_admin_service.remove_tracked_user.assert_called_once_with(12345)
    mock_modal_inter.response.send_message.assert_called_once()
    args, kwargs = mock_modal_inter.response.send_message.call_args
    content = args[0] if args else kwargs.get("content", "")
    assert "removed from trusted list" in content
