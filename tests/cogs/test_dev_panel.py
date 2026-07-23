import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import disnake
from src.cogs.dev_panel import (
    DevPanelView,
    AddOwnerModal,
    DelOwnerModal,
    CompareModal,
    FixSkipView
)
import config

@pytest.mark.asyncio
async def test_dev_panel_view_access(mock_inter):
    view = DevPanelView()
    
    # Not owner
    mock_inter.author.id = 12345
    config.OWNER_ID = 999999
    
    result = await view.interaction_check(mock_inter)
    assert result is False
    mock_inter.response.send_message.assert_called_once_with("❌ Only the main bot owner can use this panel.", ephemeral=True)
    
    # Is owner
    mock_inter.response.send_message.reset_mock()
    mock_inter.author.id = 999999
    result = await view.interaction_check(mock_inter)
    assert result is True
    mock_inter.response.send_message.assert_not_called()

@pytest.mark.asyncio
@patch("src.cogs.dev_panel.config_service")
async def test_dev_pull_creates_channels_and_roles(mock_config_service, mock_inter):
    view = DevPanelView()
    mock_inter.author.id = config.OWNER_ID = 999999
    
    # Setup config
    mock_config_service.get_guild_config = AsyncMock(return_value=(111, 222))
    mock_config_service.save_guild_log_channels = AsyncMock()
    mock_config_service.save_guild_roles = AsyncMock()
    
    mock_category = MagicMock(spec=disnake.CategoryChannel)
    mock_inter.guild.get_channel.return_value = mock_category
    
    # Mocks for created channels and roles
    mock_ch = MagicMock(spec=disnake.TextChannel)
    mock_ch.id = 1010
    mock_inter.guild.create_text_channel = AsyncMock(return_value=mock_ch)
    
    mock_role = MagicMock(spec=disnake.Role)
    mock_role.id = 2020
    mock_role.edit = AsyncMock()
    mock_inter.guild.create_role = AsyncMock(return_value=mock_role)
    
    await DevPanelView.btn_pull(view, view.btn_pull, mock_inter)
    
    # 10 channels + 2 roles created
    assert mock_inter.guild.create_text_channel.call_count == 10
    assert mock_inter.guild.create_role.call_count == 2
    
    # Verify save calls
    mock_config_service.save_guild_log_channels.assert_called_once()
    mock_config_service.save_guild_roles.assert_called_once()

@pytest.mark.asyncio
@patch("src.cogs.dev_panel.admin_service")
async def test_add_owner_modal(mock_admin_service, mock_modal_inter):
    modal = AddOwnerModal()
    mock_modal_inter.text_values = {"owner_id": "444555"}
    mock_admin_service.add_server_owner = AsyncMock()
    
    await modal.callback(mock_modal_inter)
    
    mock_admin_service.add_server_owner.assert_called_once_with(mock_modal_inter.guild.id, 444555)
    mock_modal_inter.response.send_message.assert_called_once()
    args, kwargs = mock_modal_inter.response.send_message.call_args
    content = args[0] if args else kwargs.get("content", "")
    assert "successfully added" in content

@pytest.mark.asyncio
@patch("src.cogs.dev_panel.admin_service")
async def test_del_owner_modal(mock_admin_service, mock_modal_inter):
    modal = DelOwnerModal()
    mock_modal_inter.text_values = {"owner_id": "444555"}
    mock_admin_service.remove_server_owner = AsyncMock()
    
    await modal.callback(mock_modal_inter)
    
    mock_admin_service.remove_server_owner.assert_called_once_with(mock_modal_inter.guild.id, 444555)
    mock_modal_inter.response.send_message.assert_called_once()
    args, kwargs = mock_modal_inter.response.send_message.call_args
    content = args[0] if args else kwargs.get("content", "")
    assert "successfully removed" in content

@pytest.mark.asyncio
@patch("src.cogs.dev_panel.config_service")
async def test_compare_modal(mock_config_service, mock_modal_inter):
    modal = CompareModal()
    mock_modal_inter.text_values = {"server_booster_id": "999888"}
    mock_config_service.save_guild_roles = AsyncMock()
    
    await modal.callback(mock_modal_inter)
    
    mock_config_service.save_guild_roles.assert_called_once_with(mock_modal_inter.guild.id, server_booster_id=999888)
    mock_modal_inter.response.send_message.assert_called_once()
    args, kwargs = mock_modal_inter.response.send_message.call_args
    content = args[0] if args else kwargs.get("content", "")
    assert "successfully saved" in content

@pytest.mark.asyncio
@patch("src.cogs.dev_panel.config_service")
@patch("src.cogs.dev_panel.admin_service")
async def test_dev_doctor_fix_skip_view(mock_admin_service, mock_config_service, mock_inter):
    view = FixSkipView(
        missing_channels=["bans"], 
        missing_roles=["quarantine"], 
        missing_custom_roles=[123], 
        missing_custom_users=[456]
    )
    
    # Provide a category so channels can be created
    mock_config_service.get_guild_config = AsyncMock(return_value=(111, 222))
    mock_config_service.save_guild_log_channels = AsyncMock()
    mock_config_service.save_guild_roles = AsyncMock()
    mock_admin_service.delete_custom_role_limits = AsyncMock()
    mock_admin_service.delete_custom_user_limits = AsyncMock()
    
    mock_category = MagicMock(spec=disnake.CategoryChannel)
    mock_inter.guild.get_channel.return_value = mock_category
    
    mock_ch = MagicMock()
    mock_ch.id = 555
    mock_inter.guild.create_text_channel = AsyncMock(return_value=mock_ch)
    
    mock_role = MagicMock()
    mock_role.id = 666
    mock_role.edit = AsyncMock()
    mock_inter.guild.create_role = AsyncMock(return_value=mock_role)
    
    await FixSkipView.btn_fix(view, view.btn_fix, mock_inter)
    
    mock_inter.guild.create_text_channel.assert_called_once_with(name="bans", category=mock_category)
    mock_inter.guild.create_role.assert_called_once_with(name="quarantine", reason="AntiNuke Doctor Fix")
    mock_admin_service.delete_custom_role_limits.assert_called_once_with(123)
    mock_admin_service.delete_custom_user_limits.assert_called_once_with(456)
    
    mock_config_service.save_guild_log_channels.assert_called_once_with(mock_inter.guild.id, bans_id=555)
    mock_config_service.save_guild_roles.assert_called_once_with(mock_inter.guild.id, quarantine_id=666)
    mock_inter.edit_original_response.assert_called_once()
