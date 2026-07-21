import pytest
from unittest.mock import AsyncMock

@pytest.fixture(autouse=True)
def mock_tracker_services(monkeypatch):
    """Mock the new services specifically for the event trackers."""
    ROLES = {
        "quarantine": 1111,
        "dvp": 2222,
        "server_booster": 4444,
        "ai": 1524139770437959690
    }
    LOG_CHANNELS = {
        "channel_create": 5555,
        "channel_delete": 5556,
        "channel_update": 5557,
        "bot_joins": 5558,
        "member_join": 5559,
        "bans": 5560,
        "role_updates": 5561,
        "webhooks": 5562,
        "voice_move": 5563,
        "message_edit_delete": 5564,
        "links_spam": 5565
    }

    async def get_role_id_side_effect(guild_id, role_type):
        return ROLES.get(role_type)

    async def get_log_channel_side_effect(guild_id, log_type):
        return LOG_CHANNELS.get(log_type)

    async def check_limit_side_effect(guild_id, user_id, action_type, user_roles):
        if hasattr(user_roles, "__iter__"):
            for r in user_roles:
                if getattr(r, "id", None) == 2222:  # DVP
                    return True
        return False

    get_role_mock = AsyncMock(side_effect=get_role_id_side_effect)
    get_log_mock = AsyncMock(side_effect=get_log_channel_side_effect)
    is_server_owner_mock = AsyncMock(return_value=False)
    check_limit_mock = AsyncMock(side_effect=check_limit_side_effect)

    # Patch channels tracker
    monkeypatch.setattr("src.events.channels.channels_tracker.config_service.get_role_id", get_role_mock)
    monkeypatch.setattr("src.events.channels.channels_tracker.config_service.get_log_channel", get_log_mock)
    monkeypatch.setattr("src.events.channels.channels_tracker.admin_service.is_server_owner", is_server_owner_mock)
    monkeypatch.setattr("src.events.channels.channels_tracker.limiter.check_limit", check_limit_mock)
    monkeypatch.setattr("src.events.channels.channels_tracker.limiter.add_action", lambda *a: None)

    # Patch members tracker
    monkeypatch.setattr("src.events.members.members_tracker.config_service.get_role_id", get_role_mock)
    monkeypatch.setattr("src.events.members.members_tracker.config_service.get_log_channel", get_log_mock)
    monkeypatch.setattr("src.events.members.members_tracker.admin_service.is_server_owner", is_server_owner_mock)
    monkeypatch.setattr("src.events.members.members_tracker.limiter.check_limit", check_limit_mock)
    monkeypatch.setattr("src.events.members.members_tracker.limiter.add_action", lambda *a: None)

    # Patch roles tracker
    monkeypatch.setattr("src.events.roles.roles_tracker.config_service.get_role_id", get_role_mock)
    monkeypatch.setattr("src.events.roles.roles_tracker.config_service.get_log_channel", get_log_mock)
    monkeypatch.setattr("src.events.roles.roles_tracker.admin_service.is_server_owner", is_server_owner_mock)
    monkeypatch.setattr("src.events.roles.roles_tracker.limiter.check_limit", check_limit_mock)
    monkeypatch.setattr("src.events.roles.roles_tracker.limiter.add_action", lambda *a: None)

    # Patch webhooks tracker
    monkeypatch.setattr("src.events.webhooks.webhooks_tracker.config_service.get_role_id", get_role_mock)
    monkeypatch.setattr("src.events.webhooks.webhooks_tracker.config_service.get_log_channel", get_log_mock)
    monkeypatch.setattr("src.events.webhooks.webhooks_tracker.admin_service.is_server_owner", is_server_owner_mock)
    monkeypatch.setattr("src.events.webhooks.webhooks_tracker.limiter.check_limit", check_limit_mock)
    monkeypatch.setattr("src.events.webhooks.webhooks_tracker.limiter.add_action", lambda *a: None)
