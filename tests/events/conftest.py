import pytest
import pytest_asyncio
from tests.conftest import ROLE_IDS, OWNER_ID

@pytest.fixture
def quarantine_role(mock_guild):
    """Fixture for the Quarantine role."""
    return mock_guild.get_role(ROLE_IDS['quarantine'])

@pytest.fixture
def dvp_role(mock_guild):
    """Fixture for the DVP role."""
    return mock_guild.get_role(ROLE_IDS['dvp'])

@pytest.fixture
def ai_role(mock_guild):
    """Fixture for the AI role."""
    return mock_guild.get_role(ROLE_IDS['ai'])

@pytest.fixture
def server_booster_role(mock_guild):
    """Fixture for the Server Booster role."""
    return mock_guild.get_role(ROLE_IDS['server_booster'])

@pytest.fixture
def roles_dict(quarantine_role, dvp_role, ai_role, server_booster_role):
    """Fixture for a dictionary of roles."""
    return {
        'quarantine': quarantine_role,
        'dvp': dvp_role,
        'ai': ai_role,
        'server_booster': server_booster_role
    }

@pytest.fixture
def owner_member(make_member, dvp_role, mock_guild):
    """Fixture for the owner member."""
    return make_member(OWNER_ID, roles=[dvp_role], guild=mock_guild)

@pytest.fixture
def dvp_member(make_member, dvp_role, mock_guild):
    """Fixture for a regular DVP member."""
    return make_member(222222, roles=[dvp_role], guild=mock_guild)

@pytest.fixture
def regular_member(make_member, mock_guild):
    """Fixture for a regular member with no special roles."""
    return make_member(333333, roles=[], guild=mock_guild)

@pytest.fixture
def booster_member(make_member, server_booster_role, mock_guild):
    """Fixture for a server booster member."""
    return make_member(444444, roles=[server_booster_role], guild=mock_guild)

@pytest.fixture
def ai_bot_member(make_member, ai_role, mock_guild):
    """Fixture for an authorized AI bot member."""
    return make_member(555555, roles=[ai_role], bot=True, guild=mock_guild)

@pytest.fixture
def unauthorized_bot_member(make_member, mock_guild):
    """Fixture for an unauthorized bot member."""
    return make_member(666666, roles=[], bot=True, guild=mock_guild)
