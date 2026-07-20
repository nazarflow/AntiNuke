import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database.db")

def get_connection():
    return sqlite3.connect(DB_PATH)

def setup_db():
    """Create necessary tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    # Admins table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            user_id INTEGER PRIMARY KEY
        )
    ''')

    # Tracked users table (voice move tracking)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tracked_users (
            user_id INTEGER PRIMARY KEY
        )
    ''')

    # Guild configs table (tuner channel, category, etc.)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS guild_configs (
            guild_id INTEGER PRIMARY KEY,
            tuner_category_id INTEGER,
            tuner_channel_id INTEGER
        )
    ''')

    # Guild Roles table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS guild_roles (
            guild_id INTEGER PRIMARY KEY,
            quarantine_id INTEGER,
            quarantine_alt_id INTEGER,
            server_booster_id INTEGER,
            ai_id INTEGER
        )
    ''')

    # Guild Log Channels table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS guild_log_channels (
            guild_id INTEGER PRIMARY KEY,
            channel_create_id INTEGER,
            channel_delete_id INTEGER,
            channel_update_id INTEGER,
            links_spam_id INTEGER,
            webhooks_id INTEGER,
            bot_joins_id INTEGER,
            message_edit_delete_id INTEGER,
            voice_move_id INTEGER,
            role_updates_id INTEGER,
            bans_id INTEGER
        )
    ''')

    # Guild Limits table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS guild_limits (
            guild_id INTEGER PRIMARY KEY,
            channel_create_count INTEGER,
            channel_create_time INTEGER,
            channel_delete_count INTEGER,
            channel_delete_time INTEGER
        )
    ''')

    # Custom Role Limits table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS custom_role_limits (
            role_id INTEGER PRIMARY KEY,
            guild_id INTEGER,
            channels_limit INTEGER DEFAULT 0,
            channels_time INTEGER DEFAULT 0,
            roles_limit INTEGER DEFAULT 0,
            roles_time INTEGER DEFAULT 0,
            links_limit INTEGER DEFAULT 0,
            links_time INTEGER DEFAULT 0,
            webhooks_limit INTEGER DEFAULT 0,
            webhooks_time INTEGER DEFAULT 0
        )
    ''')

    # Server Owners table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS server_owners (
            guild_id INTEGER,
            user_id INTEGER,
            PRIMARY KEY (guild_id, user_id)
        )
    ''')

    # Custom User Limits table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS custom_user_limits (
            user_id INTEGER PRIMARY KEY,
            guild_id INTEGER,
            channels_limit INTEGER DEFAULT 0,
            channels_time INTEGER DEFAULT 0,
            roles_limit INTEGER DEFAULT 0,
            roles_time INTEGER DEFAULT 0,
            links_limit INTEGER DEFAULT 0,
            links_time INTEGER DEFAULT 0,
            webhooks_limit INTEGER DEFAULT 0,
            webhooks_time INTEGER DEFAULT 0
        )
    ''')

    conn.commit()
    conn.close()

# ================================================================================================ #
# Admin Operations
# ================================================================================================ #

def get_all_admins():
    """Returns a list of all admin user IDs."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM admins')
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

def add_admin(user_id: int):
    """Adds an admin ID to the database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO admins (user_id) VALUES (?)', (user_id,))
    conn.commit()
    conn.close()

def remove_admin(user_id: int):
    """Removes an admin ID from the database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM admins WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

# ================================================================================================ #
# Tracked User Operations
# ================================================================================================ #

def get_all_tracked_users():
    """Returns a list of all tracked user IDs."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM tracked_users')
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

def add_tracked_user(user_id: int):
    """Adds a tracked user ID to the database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO tracked_users (user_id) VALUES (?)', (user_id,))
    conn.commit()
    conn.close()

def remove_tracked_user(user_id: int):
    """Removes a tracked user ID from the database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM tracked_users WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

# ================================================================================================ #
# Guild Config Operations (Tuner channel/category)
# ================================================================================================ #

def get_guild_config(guild_id: int):
    """Returns (tuner_category_id, tuner_channel_id) or None if not configured."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT tuner_category_id, tuner_channel_id FROM guild_configs WHERE guild_id = ?', (guild_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def save_guild_config(guild_id: int, category_id: int, channel_id: int):
    """Saves or updates the tuner channel and category for a guild."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO guild_configs (guild_id, tuner_category_id, tuner_channel_id)
        VALUES (?, ?, ?)
        ON CONFLICT(guild_id) DO UPDATE SET
            tuner_category_id = excluded.tuner_category_id,
            tuner_channel_id = excluded.tuner_channel_id
    ''', (guild_id, category_id, channel_id))
    conn.commit()
    conn.close()

def delete_guild_config(guild_id: int):
    """Removes the tuner configuration for a guild."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM guild_configs WHERE guild_id = ?', (guild_id,))
    conn.commit()
    conn.close()

# ================================================================================================ #
# Guild Roles Operations
# ================================================================================================ #

def get_guild_roles(guild_id: int):
    """Returns all role IDs for a guild."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM guild_roles WHERE guild_id = ?', (guild_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def get_role_id(guild_id: int, role_type: str):
    """Returns a specific role ID for a guild by column name (e.g., 'quarantine', 'ai')."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(f'SELECT {role_type}_id FROM guild_roles WHERE guild_id = ?', (guild_id,))
        row = cursor.fetchone()
    except Exception:
        row = None
    conn.close()
    return row[0] if row else None

def save_guild_roles(guild_id: int, **kwargs):
    """Updates role IDs for a guild. kwargs should match column names."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Ensure a row exists first
    cursor.execute('INSERT OR IGNORE INTO guild_roles (guild_id) VALUES (?)', (guild_id,))
    
    if kwargs:
        columns = ", ".join(f"{k} = ?" for k in kwargs.keys())
        values = tuple(kwargs.values()) + (guild_id,)
        cursor.execute(f'UPDATE guild_roles SET {columns} WHERE guild_id = ?', values)
        
    conn.commit()
    conn.close()

# ================================================================================================ #
# Guild Log Channels Operations
# ================================================================================================ #

def get_guild_log_channels(guild_id: int):
    """Returns all log channel IDs for a guild."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM guild_log_channels WHERE guild_id = ?', (guild_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def get_log_channel(guild_id: int, log_type: str):
    """Returns a specific log channel ID for a guild by column name (e.g., 'channel_create')."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(f'SELECT {log_type}_id FROM guild_log_channels WHERE guild_id = ?', (guild_id,))
        row = cursor.fetchone()
    except Exception:
        row = None
    conn.close()
    return row[0] if row else None

def save_guild_log_channels(guild_id: int, **kwargs):
    """Updates log channel IDs for a guild. kwargs should match column names."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Ensure a row exists first
    cursor.execute('INSERT OR IGNORE INTO guild_log_channels (guild_id) VALUES (?)', (guild_id,))
    
    if kwargs:
        columns = ", ".join(f"{k} = ?" for k in kwargs.keys())
        values = tuple(kwargs.values()) + (guild_id,)
        cursor.execute(f'UPDATE guild_log_channels SET {columns} WHERE guild_id = ?', values)
        
    conn.commit()
    conn.close()

# ================================================================================================ #
# Guild Limits Operations
# ================================================================================================ #

def get_guild_limits(guild_id: int):
    """Returns all limit configurations for a guild."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM guild_limits WHERE guild_id = ?', (guild_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def save_guild_limits(guild_id: int, **kwargs):
    """Updates limit values for a guild. kwargs should match column names."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Ensure a row exists first
    cursor.execute('INSERT OR IGNORE INTO guild_limits (guild_id) VALUES (?)', (guild_id,))
    
    if kwargs:
        columns = ", ".join(f"{k} = ?" for k in kwargs.keys())
        values = tuple(kwargs.values()) + (guild_id,)
        cursor.execute(f'UPDATE guild_limits SET {columns} WHERE guild_id = ?', values)
        
    conn.commit()
    conn.close()

# ================================================================================================ #
# Custom Role Limits Operations
# ================================================================================================ #

def save_custom_role_limits(role_id: int, guild_id: int, **kwargs):
    """Saves custom limits for an admin role."""
    conn = get_connection()
    cursor = conn.cursor()
    
    columns = ['channels_limit', 'channels_time', 'roles_limit', 'roles_time', 
               'links_limit', 'links_time', 'webhooks_limit', 'webhooks_time']
    
    values = [kwargs.get(col, 0) for col in columns]
    
    cursor.execute(f'''
        INSERT OR REPLACE INTO custom_role_limits 
        (role_id, guild_id, {", ".join(columns)}) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (role_id, guild_id, *values))
    
    conn.commit()
    conn.close()

def get_custom_role_limits(role_id: int):
    """Returns custom limits for a specific role."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM custom_role_limits WHERE role_id = ?', (role_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "channels_limit": row[2], "channels_time": row[3],
            "roles_limit": row[4], "roles_time": row[5],
            "links_limit": row[6], "links_time": row[7],
            "webhooks_limit": row[8], "webhooks_time": row[9],
        }
    return None

def get_all_custom_roles(guild_id: int):
    """Returns all custom admin role IDs for a guild."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT role_id FROM custom_role_limits WHERE guild_id = ?', (guild_id,))
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

# ================================================================================================ #
# Server Owners Operations
# ================================================================================================ #

def get_server_owners(guild_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM server_owners WHERE guild_id = ?', (guild_id,))
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

def add_server_owner(guild_id: int, user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO server_owners (guild_id, user_id) VALUES (?, ?)', (guild_id, user_id))
    conn.commit()
    conn.close()

def remove_server_owner(guild_id: int, user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM server_owners WHERE guild_id = ? AND user_id = ?', (guild_id, user_id))
    conn.commit()
    conn.close()

def is_server_owner(guild_id: int, user_id: int):
    return user_id in get_server_owners(guild_id)

# ================================================================================================ #
# Custom User Limits Operations
# ================================================================================================ #

def save_custom_user_limits(user_id: int, guild_id: int, **kwargs):
    """Saves custom limits for an individual user."""
    conn = get_connection()
    cursor = conn.cursor()
    
    columns = ['channels_limit', 'channels_time', 'roles_limit', 'roles_time', 
               'links_limit', 'links_time', 'webhooks_limit', 'webhooks_time']
    
    values = [kwargs.get(col, 0) for col in columns]
    
    cursor.execute(f'''
        INSERT OR REPLACE INTO custom_user_limits 
        (user_id, guild_id, {", ".join(columns)}) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, guild_id, *values))
    
    conn.commit()
    conn.close()

def get_custom_user_limits(user_id: int):
    """Returns custom limits for a specific user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM custom_user_limits WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "channels_limit": row[2], "channels_time": row[3],
            "roles_limit": row[4], "roles_time": row[5],
            "links_limit": row[6], "links_time": row[7],
            "webhooks_limit": row[8], "webhooks_time": row[9],
        }
    return None

def get_all_custom_users(guild_id: int):
    """Returns all custom admin user IDs for a guild."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM custom_user_limits WHERE guild_id = ?', (guild_id,))
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

def delete_custom_user_limits(user_id: int):
    """Deletes custom limits for a user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM custom_user_limits WHERE user_id = ?', (user_id,))
    changes = cursor.rowcount
    conn.commit()
    conn.close()
    return changes
