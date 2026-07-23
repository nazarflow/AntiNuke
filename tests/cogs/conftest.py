import pytest
import disnake
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_bot():
    bot = MagicMock()
    bot.user_ids = []
    bot.wait_for = AsyncMock()
    return bot

@pytest.fixture
def mock_guild():
    guild = MagicMock(spec=disnake.Guild)
    guild.id = 123456789
    guild.roles = []
    guild.me = MagicMock()
    guild.me.top_role.position = 10
    guild.create_category = AsyncMock()
    guild.create_text_channel = AsyncMock()
    guild.create_role = AsyncMock()
    guild.get_role = MagicMock(return_value=None)
    guild.get_channel = MagicMock(return_value=None)
    guild.get_member = MagicMock(return_value=None)
    return guild

@pytest.fixture
def mock_inter(mock_bot, mock_guild):
    inter = AsyncMock(spec=disnake.MessageInteraction)
    inter.bot = mock_bot
    inter.guild = mock_guild
    inter.author = MagicMock(spec=disnake.Member)
    inter.author.id = 999999
    
    inter.response = AsyncMock()
    inter.response.send_message = AsyncMock()
    inter.response.send_modal = AsyncMock()
    inter.response.edit_message = AsyncMock()
    inter.response.defer = AsyncMock()
    
    inter.edit_original_response = AsyncMock()
    inter.followup = AsyncMock()
    inter.followup.send = AsyncMock()
    
    inter.original_response = AsyncMock()
    return inter

@pytest.fixture
def mock_modal_inter(mock_bot, mock_guild):
    inter = AsyncMock(spec=disnake.ModalInteraction)
    inter.bot = mock_bot
    inter.guild = mock_guild
    inter.author = MagicMock(spec=disnake.Member)
    inter.author.id = 999999
    
    inter.text_values = {}
    
    inter.response = AsyncMock()
    inter.response.send_message = AsyncMock()
    inter.response.defer = AsyncMock()
    
    inter.edit_original_response = AsyncMock()
    return inter
