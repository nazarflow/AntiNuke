import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import disnake
import config
from src.cogs.setup_wizard import (
    SetupWizard,
    DashboardView,
    Step1View,
    Step2View,
    ResetConfirmView,
    ChannelInputModal
)

@pytest.mark.asyncio
async def test_cmd_pull_unauthorized(mock_inter):
    """Test /pull command fails if not owner."""
    mock_inter.author.id = 12345 # Not owner
    config.OWNER_ID = 999999
    
    wizard = SetupWizard(bot=MagicMock())
    await SetupWizard.cmd_pull.callback(wizard, mock_inter)
    
    mock_inter.response.send_message.assert_called_once_with("⛔ You don't have access to this command.", ephemeral=True)

@pytest.mark.asyncio
@patch("src.cogs.setup_wizard.config_service")
async def test_cmd_pull_authorized_fresh_setup(mock_config_service, mock_inter):
    """Test /pull command for authorized owner with no previous setup."""
    mock_inter.author.id = config.OWNER_ID = 999999
    mock_config_service.get_guild_config = AsyncMock(return_value=None)
    
    wizard = SetupWizard(bot=MagicMock())
    await SetupWizard.cmd_pull.callback(wizard, mock_inter)
    
    mock_inter.response.send_message.assert_called_once()
    args, kwargs = mock_inter.response.send_message.call_args
    content = args[0] if args else kwargs.get("content", "")
    assert "give me the AI role" in content
    assert isinstance(kwargs.get("view"), Step1View)

@pytest.mark.asyncio
@patch("src.cogs.setup_wizard.config_service")
async def test_cmd_pull_authorized_existing_setup(mock_config_service, mock_inter):
    """Test /pull command when config already exists."""
    mock_inter.author.id = config.OWNER_ID = 999999
    mock_config_service.get_guild_config = AsyncMock(return_value=(111, 222))
    mock_channel = MagicMock(spec=disnake.TextChannel)
    mock_inter.guild.get_channel.return_value = mock_channel
    
    wizard = SetupWizard(bot=MagicMock())
    await SetupWizard.cmd_pull.callback(wizard, mock_inter)
    
    mock_inter.response.send_message.assert_called_once()
    args, kwargs = mock_inter.response.send_message.call_args
    content = args[0] if args else kwargs.get("content", "")
    assert "Setup channel already exists" in content
    assert isinstance(kwargs.get("view"), ResetConfirmView)

@pytest.mark.asyncio
async def test_dashboard_view_dev_button(mock_inter):
    view = DashboardView()
    config.OWNER_ID = 999999
    mock_inter.author.id = 999999
    
    await DashboardView.btn_dev(view, view.btn_dev, mock_inter)
    mock_inter.response.send_message.assert_called_once()
    args, kwargs = mock_inter.response.send_message.call_args
    content = args[0] if args else kwargs.get("content", "")
    assert "Opening Dev Panel" in content

@pytest.mark.asyncio
@patch("src.cogs.setup_wizard.admin_service")
async def test_dashboard_view_adm_button(mock_admin_service, mock_inter):
    view = DashboardView()
    config.OWNER_ID = 999999
    mock_inter.author.id = 12345
    mock_admin_service.is_server_owner = AsyncMock(return_value=True)
    
    await DashboardView.btn_adm(view, view.btn_adm, mock_inter)
    mock_inter.response.send_message.assert_called_once()
    args, kwargs = mock_inter.response.send_message.call_args
    content = args[0] if args else kwargs.get("content", "")
    assert "Admin Panel" in content

@pytest.mark.asyncio
@patch("src.cogs.setup_wizard.config_service")
async def test_step2_view_yes_creates_channels(mock_config_service, mock_inter):
    original_msg = AsyncMock()
    view = Step2View(original_message=original_msg)
    
    mock_inter.author.id = config.OWNER_ID = 999999
    mock_category = MagicMock(spec=disnake.CategoryChannel)
    mock_category.id = 111
    mock_channel = MagicMock(spec=disnake.TextChannel)
    mock_channel.id = 222
    mock_inter.guild.create_category = AsyncMock(return_value=mock_category)
    mock_inter.guild.create_text_channel = AsyncMock(return_value=mock_channel)
    mock_config_service.save_guild_config = AsyncMock()
    
    await Step2View.btn_yes(view, view.btn_yes, mock_inter)
    
    mock_inter.response.defer.assert_called_once()
    mock_inter.guild.create_category.assert_called_once()
    mock_inter.guild.create_text_channel.assert_called_once_with(name="Tuner", category=mock_category)
    mock_config_service.save_guild_config.assert_called_once_with(mock_inter.guild.id, 111, 222)
    mock_channel.send.assert_called_once()

@pytest.mark.asyncio
@patch("src.cogs.setup_wizard.config_service")
async def test_channel_input_modal_success(mock_config_service, mock_modal_inter):
    modal = ChannelInputModal()
    mock_modal_inter.text_values = {
        "category_id_input": "11111111111111111",
        "channel_id_input": "22222222222222222"
    }
    mock_cat = MagicMock(spec=disnake.CategoryChannel)
    mock_ch = MagicMock(spec=disnake.TextChannel)
    mock_config_service.save_guild_config = AsyncMock()
    
    def mock_get_channel(ch_id):
        if ch_id == 11111111111111111: return mock_cat
        if ch_id == 22222222222222222: return mock_ch
        return None
    mock_modal_inter.guild.get_channel.side_effect = mock_get_channel
    
    await modal.callback(mock_modal_inter)
    
    mock_config_service.save_guild_config.assert_called_once_with(mock_modal_inter.guild.id, 11111111111111111, 22222222222222222)
    mock_modal_inter.response.send_message.assert_called_once()
    args, kwargs = mock_modal_inter.response.send_message.call_args
    content = args[0] if args else kwargs.get("content", "")
    assert "Settings saved" in content

@pytest.mark.asyncio
@patch("src.cogs.setup_wizard.config_service")
async def test_reset_confirm_view_resets(mock_config_service, mock_inter):
    view = ResetConfirmView()
    mock_inter.author.id = config.OWNER_ID = 999999
    mock_config_service.get_guild_config = AsyncMock(return_value=(111, 222))
    mock_config_service.delete_guild_config = AsyncMock()
    
    mock_cat = MagicMock(spec=disnake.CategoryChannel)
    mock_ch = MagicMock(spec=disnake.TextChannel)
    mock_cat.delete = AsyncMock()
    mock_ch.delete = AsyncMock()
    mock_cat.channels = [mock_ch]
    
    def mock_get_channel(ch_id):
        if ch_id == 111: return mock_cat
        if ch_id == 222: return mock_ch
        return None
    mock_inter.guild.get_channel.side_effect = mock_get_channel
    
    await ResetConfirmView.btn_reset(view, view.btn_reset, mock_inter)
    
    mock_inter.response.defer.assert_called_once()
    mock_inter.edit_original_response.assert_called_once()
    mock_ch.delete.assert_called()
    mock_cat.delete.assert_called()
    mock_config_service.delete_guild_config.assert_called_once_with(mock_inter.guild.id)
