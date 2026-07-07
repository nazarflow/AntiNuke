# config.py
# Універсальний конфігураційний файл для AntiNuke бота

# Основні налаштування бота
TEST_GUILDS = [1075118944656052336]
OWNER_ID = 478260595687292961
ADMIN_IDS = []

# ID Ролей (Roles)
ROLES = {
    "quarantine": 1075125088627720213,
    "quarantine_alt": 1045060791717593175,  # Альтернативна роль карантину (використовується в back)
    "dvp": 1075119105847341116,
    "ai": 1075124786314870946,
    "server_booster": 1075142507224104981,
}

# ID Каналів для логів (Channels)
LOG_CHANNELS = {
    "channel_create": 1099726312744173598,
    "channel_delete": 109972631274417312598, # Original string had this long ID, maybe a typo but preserved
    "channel_update": 1099726312744173598,
    "links_spam": 1079020311246295120,
    "webhooks": 1079020282704044062,
    "bot_joins": 1079020254711251004,
    "message_edit_delete": 1079020399129526382,
    "voice_move": 1079029484512096286,
    "role_updates": 1083177679848734750,
    "bans": 1083338100807307304
}

# Ліміти Anti-Nuke системи
LIMITS = {
    "channel_create": {"count": 1, "time_minutes": 30},
    "channel_delete": {"count": 1, "time_minutes": 30}
}
