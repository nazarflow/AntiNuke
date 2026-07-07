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

